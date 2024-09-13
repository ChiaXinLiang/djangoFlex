import cv2
import time
import threading
import logging
from ..models import VideoCapConfig, CurrentFrame
from django.db import transaction
from django.utils import timezone
import redis

logger = logging.getLogger(__name__)

class VideoCapService:
    def __init__(self):
        
        self.configs = {}
        self.caps = {}
        self.running = {}
        self.capture_threads = {}
        self.max_reconnect_attempts = 5
        self.reconnect_timeout = 5 
        self.redis_client = redis.StrictRedis(host='localhost', port='6379', db=0)
        self._load_configs()
        logger.info("VideoCapService initialized")

    @staticmethod
    @transaction.atomic
    def reset_video_cap_system():
        from ..models import VideoCapConfig, CurrentFrame
        try:
            CurrentFrame.objects.all().delete()
            VideoCapConfig.objects.update(is_active=False)
            redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
            for key in redis_client.keys("video_cap_service:current_image:*"):
                redis_client.delete(key)
            logger.info("Video capture system reset completed")
        except Exception as e:
            logger.error(f"Error resetting video capture system: {str(e)}")


    def _load_configs(self):
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = config
                self.running[config.rtmp_url] = False
            logger.info("Configurations loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")

    def start_server(self, rtmp_url):
        if rtmp_url in self.running and self.running[rtmp_url]:
            return False, "Server already running"

        config, created = VideoCapConfig.objects.get_or_create(rtmp_url=rtmp_url)
        if created:
            config.name = f"Config_{config.id}"
            config.save()

        self.configs[rtmp_url] = config
        self.running[rtmp_url] = True
        config.is_active = True
        config.save()

        self._initialize_capture(rtmp_url)
        self.capture_threads[rtmp_url] = threading.Thread(target=self._capture_loop, args=(rtmp_url,))
        self.capture_threads[rtmp_url].start()

        logger.info(f"Server started for {rtmp_url}")
        return True, "Server started successfully"

    def stop_server(self, rtmp_url):
        if rtmp_url not in self.running or not self.running[rtmp_url]:
            return False, "Server not running"

        self.running[rtmp_url] = False
        if rtmp_url in self.capture_threads:
            self.capture_threads[rtmp_url].join()
            del self.capture_threads[rtmp_url]

        if rtmp_url in self.caps:
            self.caps[rtmp_url].release()
            del self.caps[rtmp_url]

        with transaction.atomic():
            config = self.configs[rtmp_url]
            config.is_active = False
            config.save()
            CurrentFrame.objects.filter(config=config).delete()

        self.redis_client.delete(f"video_cap_service:current_image:{rtmp_url}")
        logger.info(f"Server stopped for {rtmp_url}")
        return True, "Server stopped successfully"

    def check_server_status(self, rtmp_url):
        status = self.running.get(rtmp_url, False)
        return status

    def _initialize_capture(self, rtmp_url):
        if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
            self.caps[rtmp_url].release()
        
        cap_source = 0 if rtmp_url == '0' else rtmp_url
        try:
            self.caps[rtmp_url] = cv2.VideoCapture(cap_source)
            self.caps[rtmp_url].set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not self.caps[rtmp_url].isOpened():
                raise Exception("Failed to open video capture")
        except Exception as e:
            logger.error(f"Failed to initialize video capture for {rtmp_url}: {str(e)}")
            self.caps[rtmp_url] = None

    def _capture_loop(self, rtmp_url):
        config = self.configs[rtmp_url]
        reconnect_start_time = None
        reconnect_attempts = 0
        while self.running[rtmp_url]:
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
            
            if reconnect_start_time is not None:
                elapsed_time = time.time() - reconnect_start_time
                if elapsed_time > self.reconnect_timeout or reconnect_attempts > self.max_reconnect_attempts:
                    self._set_inactive(rtmp_url)
                    break
                else:
                    self._reconnect(rtmp_url)
            
            time.sleep(config.frame_interval)

    def _process_frame(self, rtmp_url):
        if rtmp_url not in self.caps or self.caps[rtmp_url] is None or not self.caps[rtmp_url].isOpened():
            return False

        try:
            ret, frame = self.caps[rtmp_url].read()
            if not ret:
                raise Exception("Failed to capture frame")
            
            self.update_frame(rtmp_url, frame)
            self.configs[rtmp_url].max_consecutive_errors = 0
            return True
        except Exception as e:
            self.configs[rtmp_url].max_consecutive_errors += 1
            return False

    def _reconnect(self, rtmp_url):
        if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
            self.caps[rtmp_url].release()
        self.caps[rtmp_url] = None
        time.sleep(1)
        if self.caps[rtmp_url] is None or not self.caps[rtmp_url].isOpened():
            return False
        else:
            self.configs[rtmp_url].max_consecutive_errors = 0
            return True

    def _set_inactive(self, rtmp_url):
        with transaction.atomic():
            config = self.configs[rtmp_url]
            config.is_active = False
            config.save()
            CurrentFrame.objects.filter(config=config).delete()

        self.running[rtmp_url] = False
        if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
            self.caps[rtmp_url].release()
        self.caps[rtmp_url] = None

        if rtmp_url in self.capture_threads:
            del self.capture_threads[rtmp_url]

        self.redis_client.delete(f"video_cap_service:current_image:{rtmp_url}")

    def update_frame(self, rtmp_url, frame):
        if frame is None:
            return
        
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        with transaction.atomic():
            current_frame, created = CurrentFrame.objects.get_or_create(config=self.configs[rtmp_url])
            current_frame.frame_data = frame_bytes
            current_frame.timestamp = timezone.now()
            current_frame.save()
            self.redis_client.set(f"video_cap_service:current_image:{rtmp_url}", frame_bytes)

    def __del__(self):
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                self.stop_server(rtmp_url)

        with transaction.atomic():
            CurrentFrame.objects.filter(config__in=self.configs.values()).delete()

        for rtmp_url in self.configs.keys():
            self.redis_client.delete(f"video_cap_service:current_image:{rtmp_url}")

        logger.info("VideoCapService destroyed")

    def list_running_threads(self):
        running_threads = []
        for rtmp_url, thread in self.capture_threads.items():
            running_threads.append({
                'rtmp_url': rtmp_url,
                'thread_id': thread.ident,
                'thread_name': thread.name,
                'is_alive': thread.is_alive()
            })
        return running_threads
