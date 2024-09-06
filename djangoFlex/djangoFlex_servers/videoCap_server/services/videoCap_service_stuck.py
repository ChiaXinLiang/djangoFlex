import cv2
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import transaction
from django.utils import timezone
from ..models import VideoCapConfig, CurrentFrame
from django.conf import settings
import redis
import atexit
from django.core.signals import request_finished
from django.dispatch import receiver

logger = logging.getLogger(__name__)

class VideoCapService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VideoCapService, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        with self._lock:
            if not self._initialized:
                self._initialized = True
                self.configs = {}
                self.caps = {}
                self.running = {}
                self.capture_threads = {}
                self.executor = ThreadPoolExecutor(max_workers=10)
                self.max_reconnect_attempts = 5
                self.reconnect_timeout = 5 
                self.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
                self.termination_event = threading.Event()
                self._load_configs()
                logger.info("VideoCapService initialized")

    def _load_configs(self):
        try:
            with transaction.atomic():
                for config in VideoCapConfig.objects.filter(is_active=True):
                    self.configs[config.rtmp_url] = config
                    self.running[config.rtmp_url] = False
                    self._initialize_capture(config.rtmp_url)
            logger.info("Configurations loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")

    def start_capture(self, rtmp_url):
        with self._lock:
            if rtmp_url in self.running and self.running[rtmp_url]:
                logger.info(f"Capture for {rtmp_url} is already running")
                return False, "Capture already running"

            if rtmp_url not in self.configs:
                logger.error(f"No configuration found for {rtmp_url}")
                return False, "No configuration found"

            self.running[rtmp_url] = True
            self.capture_threads[rtmp_url] = self.executor.submit(self._capture_loop, rtmp_url)

            logger.info(f"Capture started for {rtmp_url}")
            return True, "Capture started successfully"

    def stop_server(self, rtmp_url):
        with self._lock:
            if rtmp_url not in self.running or not self.running[rtmp_url]:
                logger.warning(f"Server for {rtmp_url} is not running")
                return False, "Server not running"

            self.running[rtmp_url] = False
            if rtmp_url in self.capture_threads:
                future = self.capture_threads[rtmp_url]
                future.cancel()
                try:
                    future.result(timeout=5)
                except Exception as e:
                    logger.error(f"Error stopping capture thread for {rtmp_url}: {str(e)}")
                del self.capture_threads[rtmp_url]
                logger.info(f"Capture thread for {rtmp_url} stopped")

            if rtmp_url in self.caps:
                self.caps[rtmp_url].release()
                del self.caps[rtmp_url]
                logger.info(f"Video capture for {rtmp_url} released")

            with transaction.atomic():
                config = self.configs[rtmp_url]
                config.is_active = False
                config.save()
                CurrentFrame.objects.filter(config=config).delete()
                logger.info(f"Configuration for {rtmp_url} deactivated and current frames deleted")

            self.redis_client.delete(f"video_cap_service:current_image:{rtmp_url}")
            logger.info(f"Server stopped for {rtmp_url}")
            return True, "Server stopped successfully"

    def check_server_status(self, rtmp_url):
        with self._lock:
            status = self.running.get(rtmp_url, False)
        logger.info(f"Server status for {rtmp_url}: {'Running' if status else 'Not running'}")
        return status

    def _initialize_capture(self, rtmp_url):
        with self._lock:
            if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
                self.caps[rtmp_url].release()
                logger.info(f"Existing capture for {rtmp_url} released")
            
            cap_source = 0 if rtmp_url == '0' else rtmp_url
            try:
                self.caps[rtmp_url] = cv2.VideoCapture(cap_source)
                self.caps[rtmp_url].set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not self.caps[rtmp_url].isOpened():
                    raise Exception("Failed to open video capture")
                logger.info(f"Video capture initialized for {rtmp_url}")
            except Exception as e:
                logger.error(f"Failed to initialize video capture for {rtmp_url}: {str(e)}")
                self.caps[rtmp_url] = None

    def _capture_loop(self, rtmp_url):
        config = self.configs[rtmp_url]
        reconnect_start_time = None
        reconnect_attempts = 0
        logger.info(f"Capture loop started for {rtmp_url}")
        while self.running[rtmp_url] and not self.termination_event.is_set():
            try:
                with self._lock:
                    if rtmp_url in self.caps and self.caps[rtmp_url] is not None and self.caps[rtmp_url].isOpened():
                        if self._process_frame(rtmp_url):
                            reconnect_start_time = None
                            reconnect_attempts = 0
                        else:
                            if reconnect_start_time is None:
                                reconnect_start_time = time.time()
                                reconnect_attempts += 1
                    else:
                        if reconnect_start_time is None:
                            reconnect_start_time = time.time()
                            reconnect_attempts += 1
                            logger.warning(f"Connection lost for {rtmp_url}, attempting to reconnect")
                
                if reconnect_start_time is not None:
                    elapsed_time = time.time() - reconnect_start_time
                    if elapsed_time > self.reconnect_timeout or reconnect_attempts > self.max_reconnect_attempts:
                        logger.error(f"Failed to reconnect to {rtmp_url} after {elapsed_time:.2f} seconds and {reconnect_attempts} attempts. Setting server to inactive.")
                        self._set_inactive(rtmp_url)
                        break
                    else:
                        self._reconnect(rtmp_url)
                
                time.sleep(config.frame_interval)
            except Exception as e:
                logger.error(f"Error in capture loop for {rtmp_url}: {str(e)}")
                time.sleep(1)  # Prevent rapid-fire logging in case of persistent errors
        logger.info(f"Capture loop ended for {rtmp_url}")

    def _process_frame(self, rtmp_url):
        if rtmp_url not in self.caps or self.caps[rtmp_url] is None or not self.caps[rtmp_url].isOpened():
            logger.warning(f"VideoCapture is not initialized or opened for {rtmp_url}")
            return False

        try:
            ret, frame = self.caps[rtmp_url].read()
            if not ret:
                raise Exception("Failed to capture frame")
            
            self.update_frame(rtmp_url, frame)
            self.configs[rtmp_url].consecutive_errors = 0
            return True
        except Exception as e:
            logger.warning(f"Error processing frame for {rtmp_url}: {str(e)}")
            self.configs[rtmp_url].consecutive_errors += 1
            return False

    def _reconnect(self, rtmp_url):
        logger.info(f"Attempting to reconnect to video source for {rtmp_url}")
        with self._lock:
            if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
                self.caps[rtmp_url].release()
            self.caps[rtmp_url] = None
        time.sleep(1)
        self._initialize_capture(rtmp_url)
        with self._lock:
            if self.caps[rtmp_url] is None or not self.caps[rtmp_url].isOpened():
                logger.error(f"Failed to reconnect to video source for {rtmp_url}")
                return False
            else:
                logger.info(f"Successfully reconnected to video source for {rtmp_url}")
                self.configs[rtmp_url].consecutive_errors = 0
                return True

    def _set_inactive(self, rtmp_url):
        logger.info(f"Setting server to inactive for {rtmp_url}")
        with transaction.atomic():
            config = self.configs[rtmp_url]
            config.is_active = False
            config.save()
            CurrentFrame.objects.filter(config=config).delete()
            logger.info(f"Configuration for {rtmp_url} set to inactive and current frames deleted")

        with self._lock:
            self.running[rtmp_url] = False
            if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
                self.caps[rtmp_url].release()
            self.caps[rtmp_url] = None
            logger.info(f"Video capture for {rtmp_url} released")

            if rtmp_url in self.capture_threads:
                del self.capture_threads[rtmp_url]
                logger.info(f"Capture thread for {rtmp_url} removed")

        self.redis_client.delete(f"video_cap_service:current_image:{rtmp_url}")
        logger.info(f"Server set to inactive for {rtmp_url}")

    def update_frame(self, rtmp_url, frame):
        if frame is None:
            logger.warning(f"Received None frame for {rtmp_url}, skipping update")
            return
        
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        with transaction.atomic():
            config = self.configs[rtmp_url]
            current_frame, created = CurrentFrame.objects.get_or_create(config=config)
            current_frame.frame_data = frame_bytes
            current_frame.timestamp = timezone.now()
            current_frame.save()
            self.redis_client.set(f"video_cap_service:current_image:{rtmp_url}", frame_bytes)

    def stop_all_servers(self):
        self.termination_event.set()
        with self._lock:
            for rtmp_url in list(self.running.keys()):
                self.stop_server(rtmp_url)

    def shutdown(self):
        logger.info("VideoCapService shutdown initiated")
        self.stop_all_servers()
        self.executor.shutdown(wait=True)
        logger.info("ThreadPoolExecutor shut down")

        with transaction.atomic():
            CurrentFrame.objects.filter(config__in=self.configs.values()).delete()
            logger.info("All current frames deleted")

        for rtmp_url in self.configs.keys():
            self.redis_client.delete(f"video_cap_service:current_image:{rtmp_url}")
        logger.info("All redis_client keys deleted")

        logger.info("VideoCapService shutdown completed")

    def __del__(self):
        self.shutdown()

    def list_running_threads(self):
        with self._lock:
            running_threads = []
            for rtmp_url, future in self.capture_threads.items():
                running_threads.append({
                    'rtmp_url': rtmp_url,
                    'is_running': self.running[rtmp_url],
                    'is_done': future.done()
                })
        return running_threads

    def check_all_threads(self):
        with self._lock:
            for rtmp_url, future in list(self.capture_threads.items()):
                if future.done():
                    try:
                        exception = future.exception(timeout=1)
                        if exception:
                            logger.error(f"Thread for {rtmp_url} raised an exception: {exception}")
                            self.stop_server(rtmp_url)
                    except Exception as e:
                        logger.error(f"Error checking thread for {rtmp_url}: {str(e)}")

video_cap_service = VideoCapService()

@receiver(request_finished)
def on_request_finished(sender, **kwargs):
    video_cap_service.shutdown()

def cleanup():
    video_cap_service.shutdown()

atexit.register(cleanup)