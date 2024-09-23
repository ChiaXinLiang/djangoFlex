import cv2
import numpy as np
import threading
import logging
import subprocess
import time
from ...videoCap_server.models import VideoCapConfig, CurrentVideoClip
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import os

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
        self.fps = 15  # Set FPS to 15
        self._load_configs()
        logger.info("DrawResultService initialized")

    def _load_configs(self):
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = {
                    'rtmp_url': config.rtmp_url,
                    'output_url': f"rtmp://localhost/live/annotation_result_{config.rtmp_url.split('/')[-1]}",
                    'frame_interval': 1 / self.fps,  # Set frame interval based on FPS
                    'is_active': True
                }
                self.running[config.rtmp_url] = False
            logger.info("Configurations loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")

    def start_draw_service(self, rtmp_url):
        logger.info(f"Attempting to start draw service for {rtmp_url}")
        if rtmp_url in self.running and self.running[rtmp_url]:
            return False, "Draw service already running"

        config = self.configs.get(rtmp_url)
        if not config:
            self.configs[rtmp_url] = {
                'rtmp_url': rtmp_url,
                'output_url': f"rtmp://localhost/live/annotation_result_{rtmp_url.split('/')[-1]}",
                'frame_interval': 1 / self.fps,  # Set frame interval based on FPS
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
            ffmpeg_command = [
                'ffmpeg',
                '-re',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', '1280x720',  # Adjust to your frame size
                '-r', str(self.fps),
                '-i', '-',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'ultrafast',
                '-r', str(self.fps),
                '-f', 'flv',
                config['output_url']
            ]

            logger.info(f"Starting ffmpeg process for {rtmp_url}")
            self.ffmpeg_processes[rtmp_url] = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

        try:
            while self.running[rtmp_url]:
                frame_data = self._draw_results(rtmp_url)
                if frame_data is not None:
                    logger.info(f"Received frame data for {rtmp_url}, length: {len(frame_data)}")
                    for frame in frame_data:
                        self.ffmpeg_processes[rtmp_url].stdin.write(frame)
                    logger.info(f"Wrote {len(frame_data)} frames to ffmpeg for {rtmp_url}")
                else:
                    logger.warning(f"No frame data received for {rtmp_url}")
                time.sleep(config['frame_interval'])

        except Exception as e:
            logger.error(f"Error in draw loop for {rtmp_url}: {str(e)}")
        finally:
            if rtmp_url in self.ffmpeg_processes:
                logger.info(f"Closing ffmpeg process for {rtmp_url}")
                self.ffmpeg_processes[rtmp_url].stdin.close()
                self.ffmpeg_processes[rtmp_url].wait()
                del self.ffmpeg_processes[rtmp_url]

    def _draw_results(self, rtmp_url):
        try:
            with transaction.atomic():
                config = self.configs[rtmp_url]
                current_video_clip = CurrentVideoClip.objects.filter(config__rtmp_url=rtmp_url).latest('start_time')
                
                clip_path = current_video_clip.clip_path
                
                if not clip_path or not os.path.exists(clip_path) or not clip_path.endswith('.ts'):
                    logger.error(f"Invalid clip path for {rtmp_url}: {clip_path}")
                    return None

                cap = cv2.VideoCapture(clip_path)
                frames = []

                frame_count = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    bbox = self._generate_random_bbox(frame.shape[1], frame.shape[0])
                    
                    cv2.rectangle(frame, (bbox['x'], bbox['y']), 
                                  (bbox['x'] + bbox['width'], bbox['y'] + bbox['height']), 
                                  self.box_color, self.thickness)
                    
                    label = "Object"
                    cv2.putText(frame, label, (bbox['x'], bbox['y'] - 10), self.font, self.font_scale, self.text_color, self.thickness)

                    cv2.putText(frame, f"Clip: {current_video_clip.start_time}", (10, 30), 
                                self.font, self.font_scale, self.text_color, self.thickness)

                    frames.append(frame.tobytes())
                    frame_count += 1

                cap.release()
                logger.info(f"Processed {frame_count} frames for {rtmp_url}")
                return frames
        except Exception as e:
            logger.error(f"Error in _draw_results for {rtmp_url}: {str(e)}")
            return None

    def _generate_random_bbox(self, max_width, max_height):
        x = np.random.randint(0, max_width - 100)
        y = np.random.randint(0, max_height - 100)
        width = np.random.randint(50, 100)
        height = np.random.randint(50, 100)
        return {'x': x, 'y': y, 'width': width, 'height': height}

    def __del__(self):
        logger.info("Destroying DrawResultService")
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                self.stop_draw_service(rtmp_url)
        logger.info("DrawResultService destroyed")

    def list_running_threads(self):
        running_threads = []
        for rtmp_url, thread in self.draw_threads.items():
            running_threads.append({
                'rtmp_url': rtmp_url,
                'thread_id': thread.ident,
                'thread_name': thread.name,
                'is_alive': thread.is_alive()
            })
        return running_threads
