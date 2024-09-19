import cv2
import numpy as np
import threading
import logging
import subprocess
import time
from ...videoCap_server.models import VideoCapConfig, CurrentFrame
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class DrawResultService:
    def __init__(self):
        self.configs = {}
        self.running = {}
        self.draw_threads = {}
        self.ffmpeg_processes = {}
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.thickness = 2
        self.text_color = (255, 255, 255)  # White color for text
        self.box_color = (0, 255, 0)  # Green color for bounding boxes
        self.predicted_box_color = (0, 255, 255)  # Yellow color for predicted boxes
        self._load_configs()
        logger.info("DrawResultService initialized")

    def _load_configs(self):
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = {
                    'rtmp_url': config.rtmp_url,
                    'output_url': f"rtmp://localhost/live/annotation_result_{config.rtmp_url.split('/')[-1]}",
                    'frame_interval': 0.1,  # Default frame interval
                    'is_active': True
                }
                self.running[config.rtmp_url] = False
                logger.info(f"Loaded configuration for {config.rtmp_url}")
            logger.info("Configurations loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")

    def start_draw_service(self, rtmp_url):
        logger.info(f"Attempting to start draw service for {rtmp_url}")
        if rtmp_url in self.running and self.running[rtmp_url]:
            logger.warning(f"Draw service already running for {rtmp_url}")
            return False, "Draw service already running"

        config = self.configs.get(rtmp_url)
        if not config:
            logger.info(f"Creating new config for {rtmp_url}")
            self.configs[rtmp_url] = {
                'rtmp_url': rtmp_url,
                'output_url': f"rtmp://localhost/live/annotation_result_{rtmp_url.split('/')[-1]}",
                'frame_interval': 0.1,  # Default frame interval
                'is_active': True
            }

        self.running[rtmp_url] = True
        self.draw_threads[rtmp_url] = threading.Thread(target=self._draw_loop, args=(rtmp_url,))
        self.draw_threads[rtmp_url].start()

        logger.info(f"Draw service started for {rtmp_url}")
        return True, "Draw service started successfully"

    def stop_draw_service(self, rtmp_url):
        logger.info(f"Attempting to stop draw service for {rtmp_url}")
        if rtmp_url not in self.running or not self.running[rtmp_url]:
            logger.warning(f"Draw service not running for {rtmp_url}")
            return False, "Draw service not running"

        self.running[rtmp_url] = False
        if rtmp_url in self.draw_threads:
            self.draw_threads[rtmp_url].join()
            del self.draw_threads[rtmp_url]

        if rtmp_url in self.ffmpeg_processes:
            logger.info(f"Closing ffmpeg process for {rtmp_url}")
            self.ffmpeg_processes[rtmp_url].stdin.close()
            self.ffmpeg_processes[rtmp_url].wait()
            del self.ffmpeg_processes[rtmp_url]

        logger.info(f"Draw service stopped for {rtmp_url}")
        return True, "Draw service stopped successfully"

    @classmethod
    def stop_all_services(cls):
        logger.info("Stopping all draw services")
        instance = cls()
        for rtmp_url in list(instance.running.keys()):
            if instance.running[rtmp_url]:
                instance.stop_draw_service(rtmp_url)
        logger.info("All draw services stopped")

    def _draw_loop(self, rtmp_url):
        logger.info(f"Starting draw loop for {rtmp_url}")
        config = self.configs[rtmp_url]
        
        if rtmp_url not in self.ffmpeg_processes:
            fps = int(1 / config['frame_interval'])
            ffmpeg_command = [
                'ffmpeg',
                '-re',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', '1280x720',  # Adjust to your frame size
                '-r', str(fps),
                '-i', '-',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'ultrafast',
                '-r', str(fps),
                '-f', 'flv',
                config['output_url']
            ]

            logger.info(f"Starting ffmpeg process for {rtmp_url}")
            self.ffmpeg_processes[rtmp_url] = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

        last_bbox = None
        last_timestamp = None

        try:
            while self.running[rtmp_url]:
                logger.debug(f"Processing frame for {rtmp_url}")
                frame_data = self._draw_results(rtmp_url, last_bbox, last_timestamp)
                if frame_data is not None:
                    self.ffmpeg_processes[rtmp_url].stdin.write(frame_data)
                time.sleep(config['frame_interval'])

        except Exception as e:
            logger.error(f"Error in draw loop for {rtmp_url}: {str(e)}")
        finally:
            if rtmp_url in self.ffmpeg_processes:
                logger.info(f"Closing ffmpeg process for {rtmp_url}")
                self.ffmpeg_processes[rtmp_url].stdin.close()
                self.ffmpeg_processes[rtmp_url].wait()
                del self.ffmpeg_processes[rtmp_url]

    def _draw_results(self, rtmp_url, last_bbox, last_timestamp):
        try:
            with transaction.atomic():
                logger.debug(f"Drawing results for {rtmp_url}")
                config = self.configs[rtmp_url]
                current_frame = CurrentFrame.objects.filter(config__rtmp_url=rtmp_url).latest('timestamp')
                
                frame = cv2.imdecode(np.frombuffer(current_frame.frame_data, np.uint8), cv2.IMREAD_COLOR)

                if last_bbox is None:
                    logger.debug(f"Generating initial bounding box for {rtmp_url}")
                    last_bbox = self._generate_random_bbox(frame.shape[1], frame.shape[0])
                    last_timestamp = current_frame.timestamp

                time_diff = current_frame.timestamp - last_timestamp
                predicted_bbox = self._predict_bbox_movement(last_bbox, time_diff)
                
                logger.debug(f"Drawing bounding boxes for {rtmp_url}")
                cv2.rectangle(frame, (predicted_bbox['x'], predicted_bbox['y']), 
                              (predicted_bbox['x'] + predicted_bbox['width'], predicted_bbox['y'] + predicted_bbox['height']), 
                              self.predicted_box_color, self.thickness)
                
                cv2.rectangle(frame, (last_bbox['x'], last_bbox['y']), 
                              (last_bbox['x'] + last_bbox['width'], last_bbox['y'] + last_bbox['height']), 
                              self.box_color, self.thickness)
                
                label = "Object"
                cv2.putText(frame, label, (last_bbox['x'], last_bbox['y'] - 10), self.font, self.font_scale, self.text_color, self.thickness)

                cv2.putText(frame, f"Frame: {current_frame.timestamp}", (10, 30), 
                            self.font, self.font_scale, self.text_color, self.thickness)

                last_bbox = predicted_bbox
                last_timestamp = current_frame.timestamp

                logger.debug(f"Frame processed for {rtmp_url}")
                return frame.tobytes()
        except Exception as e:
            logger.error(f"Error in _draw_results for {rtmp_url}: {str(e)}")
            return None

    def _generate_random_bbox(self, max_width, max_height):
        logger.debug("Generating random bounding box")
        x = np.random.randint(0, max_width - 100)
        y = np.random.randint(0, max_height - 100)
        width = np.random.randint(50, 100)
        height = np.random.randint(50, 100)
        return {'x': x, 'y': y, 'width': width, 'height': height}

    def _predict_bbox_movement(self, old_bbox, time_diff):
        logger.debug("Predicting bounding box movement")
        predicted_bbox = old_bbox.copy()
        
        speed = 5  # pixels per second
        movement = speed * time_diff.total_seconds()
        
        predicted_bbox['x'] += int(movement)
        predicted_bbox['y'] += int(movement)
        
        return predicted_bbox

    def __del__(self):
        logger.info("Destroying DrawResultService")
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                self.stop_draw_service(rtmp_url)
        logger.info("DrawResultService destroyed")

    def list_running_threads(self):
        logger.info("Listing running threads")
        running_threads = []
        for rtmp_url, thread in self.draw_threads.items():
            running_threads.append({
                'rtmp_url': rtmp_url,
                'thread_id': thread.ident,
                'thread_name': thread.name,
                'is_alive': thread.is_alive()
            })
        return running_threads
