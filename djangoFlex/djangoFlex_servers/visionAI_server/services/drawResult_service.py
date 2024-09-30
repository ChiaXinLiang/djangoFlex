import cv2
import numpy as np
import threading
import logging
import time
from ...videoCap_server.models import VideoCapConfig, CurrentVideoClip
from django.db import transaction
import os
from . import utils
import time

logger = logging.getLogger(__name__)

class DrawResultService:
    def __init__(self):
        try:
            self.configs = {}
            self.running = {}
            self.draw_threads = {}
            self.ffmpeg_processes = {}
            self.ffmpeg_checkers = {}
            self.font = cv2.FONT_HERSHEY_SIMPLEX
            self.font_scale = 0.5
            self.thickness = 2
            self.text_color = (255, 255, 255)  # White color for text
            self.box_color = (0, 255, 0)  # Green color for bounding boxes
            self.predicted_box_color = (0, 255, 255)  # Yellow color for predicted boxes
            self.frame_size = (1280, 720)  # Set frame size
            self.fps = 15  # Set fps to 15
            self._load_configs()
            utils.download_model_if_not_exists("360_1280_person_yolov8m", "1")
            self.detection_model = utils.load_detection_model("models/360_1280_person_yolov8m/1/model/best.pt")
            self.last_processed_clip = {}  # Store the last processed clip for each rtmp_url
            logger.debug("DrawResultService initialized")
        except Exception as e:
            logger.debug(f"Error in DrawResultService initialization: {str(e)}")

    def _load_configs(self):
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = {
                    'rtmp_url': config.rtmp_url,
                    'output_url': f"rtmp://localhost/live/annotation_result_{config.rtmp_url.split('/')[-1]}",
                    'is_active': True
                }
                self.running[config.rtmp_url] = False
            logger.debug("Configurations loaded successfully")
        except Exception as e:
            logger.debug(f"Error loading configurations: {str(e)}")

    def start_draw_service(self, rtmp_url):
        try:
            logger.debug(f"Attempting to start draw service for {rtmp_url}")
            if rtmp_url in self.running and self.running[rtmp_url]:
                return False, "Draw service already running"

            config = self.configs.get(rtmp_url)
            if not config:
                self.configs[rtmp_url] = {
                    'rtmp_url': rtmp_url,
                    'output_url': f"rtmp://localhost/live/annotation_result_{rtmp_url.split('/')[-1]}",
                    'is_active': True
                }

            self.running[rtmp_url] = True
            self.draw_threads[rtmp_url] = threading.Thread(target=self._draw_loop, args=(rtmp_url,))
            self.draw_threads[rtmp_url].start()

            logger.debug(f"Draw service started for {rtmp_url}")
            return True, "Draw service started successfully"
        except Exception as e:
            logger.debug(f"Error starting draw service for {rtmp_url}: {str(e)}")
            return False, f"Error starting draw service: {str(e)}"

    def stop_draw_service(self, rtmp_url):
        try:
            logger.debug(f"Attempting to stop draw service for {rtmp_url}")
            if rtmp_url not in self.running or not self.running[rtmp_url]:
                return False, "Draw service not running"

            self.running[rtmp_url] = False
            if rtmp_url in self.draw_threads:
                self.draw_threads[rtmp_url].join(timeout=10)
                if self.draw_threads[rtmp_url].is_alive():
                    logger.debug(f"Thread for {rtmp_url} did not stop within timeout. Forcing termination.")
                del self.draw_threads[rtmp_url]

            if rtmp_url in self.ffmpeg_processes:
                logger.debug(f"Closing ffmpeg process for {rtmp_url}")
                try:
                    self.ffmpeg_processes[rtmp_url].stdin.close()
                    self.ffmpeg_processes[rtmp_url].terminate()
                    self.ffmpeg_processes[rtmp_url].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.debug(f"FFmpeg process for {rtmp_url} did not terminate. Killing it.")
                    self.ffmpeg_processes[rtmp_url].kill()
                del self.ffmpeg_processes[rtmp_url]

            logger.debug(f"Draw service stopped for {rtmp_url}")
            return True, "Draw service stopped successfully"
        except Exception as e:
            logger.debug(f"Error stopping draw service for {rtmp_url}: {str(e)}")
            return False, f"Error stopping draw service: {str(e)}"

    def _draw_loop(self, rtmp_url):
        try:
            logger.debug(f"Starting draw loop for {rtmp_url}")
            config = self.configs[rtmp_url]
            
            if rtmp_url not in self.ffmpeg_processes:
                self._start_ffmpeg_process(rtmp_url)

            consecutive_empty_frames = 0
            max_empty_frames = 30  # Increased from 10 to 30
            restart_attempts = 0
            max_restart_attempts = 5

            while self.running[rtmp_url]:
                # Check if FFmpeg process is still running
                if not self.ffmpeg_checkers[rtmp_url]():
                    logger.warning(f"FFmpeg process for {rtmp_url} has stopped. Waiting 10 seconds to reconnect...")
                    time.sleep(10)
                    self._start_ffmpeg_process(rtmp_url)

                frame_data = self._draw_results(rtmp_url)
                logger.debug(f"Frame data received for {rtmp_url}: {len(frame_data) if frame_data else 0} frames")
                if frame_data is not None and len(frame_data) > 0:
                    logger.debug(f"Received frame data for {rtmp_url}, length: {len(frame_data)}")
                    consecutive_empty_frames = 0  # Reset the counter
                    restart_attempts = 0  # Reset restart attempts
                    for frame in frame_data:
                        if self.running[rtmp_url]:  # Check again to ensure we should continue
                            try:
                                self.ffmpeg_processes[rtmp_url].stdin.write(frame)
                            except Exception as e:
                                logger.debug(f"Error writing frame to ffmpeg for {rtmp_url}: {str(e)}")
                                logger.warning(f"FFmpeg process for {rtmp_url} has encountered an error. Waiting 10 seconds to reconnect...")
                                time.sleep(10)
                                self._start_ffmpeg_process(rtmp_url)  # Restart FFmpeg process
                        else:
                            break
                    logger.debug(f"Wrote {len(frame_data)} frames to ffmpeg for {rtmp_url}")
                else:
                    consecutive_empty_frames += 1
                    logger.debug(f"No frame data received for {rtmp_url}. Consecutive empty frames: {consecutive_empty_frames}")
                    
                    if consecutive_empty_frames >= max_empty_frames:
                        logger.warning(f"Too many consecutive empty frames for {rtmp_url}. Attempting to restart...")
                        restart_attempts += 1
                        if restart_attempts > max_restart_attempts:
                            logger.error(f"Max restart attempts reached for {rtmp_url}. Stopping draw loop.")
                            break
                        self._stop_ffmpeg_process(rtmp_url)
                        time.sleep(10)  # Wait before restarting
                        self._start_ffmpeg_process(rtmp_url)
                        consecutive_empty_frames = 0  # Reset counter after restart attempt

                time.sleep(0.1)  # Small delay to prevent excessive CPU usage

        except Exception as e:
            logger.error(f"Error in draw loop for {rtmp_url}: {str(e)}")
        finally:
            self._stop_ffmpeg_process(rtmp_url)

    def _start_ffmpeg_process(self, rtmp_url):
        config = self.configs[rtmp_url]
        self.ffmpeg_processes[rtmp_url], self.ffmpeg_checkers[rtmp_url] = utils.create_ffmpeg_process(config['output_url'], self.fps, self.frame_size)
        logger.debug(f"Started new FFmpeg process for {rtmp_url}")

    def _stop_ffmpeg_process(self, rtmp_url):
        if rtmp_url in self.ffmpeg_processes:
            logger.debug(f"Closing ffmpeg process for {rtmp_url}")
            try:
                self.ffmpeg_processes[rtmp_url].stdin.close()
                self.ffmpeg_processes[rtmp_url].terminate()
                self.ffmpeg_processes[rtmp_url].wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.debug(f"FFmpeg process for {rtmp_url} did not terminate. Killing it.")
                self.ffmpeg_processes[rtmp_url].kill()
            del self.ffmpeg_processes[rtmp_url]
            del self.ffmpeg_checkers[rtmp_url]

    def _draw_results(self, rtmp_url):
        try:
            with transaction.atomic():
                config = self.configs[rtmp_url]
                current_video_clip = CurrentVideoClip.objects.filter(config__rtmp_url=rtmp_url).order_by('-start_time').first()
                
                if current_video_clip is None:
                    logger.debug(f"No current video clip found for {rtmp_url}")
                    return None

                clip_path = current_video_clip.clip_path
                
                if not clip_path or not os.path.exists(clip_path) or not clip_path.endswith('.ts'):
                    logger.debug(f"Invalid clip path for {rtmp_url}: {clip_path}")
                    return None

                # Compare current_video_clip with last_processed_clip
                last_processed_clip = self.last_processed_clip.get(rtmp_url)
                if last_processed_clip and last_processed_clip.id == current_video_clip.id:
                    logger.debug(f"Clip {clip_path} for {rtmp_url} is the same as the last processed. Waiting for the next.")
                    return None

                # Update the last processed clip
                self.last_processed_clip[rtmp_url] = current_video_clip

                cap = cv2.VideoCapture(clip_path)
                frames = []

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames.append(frame)

                cap.release()
                logger.debug(f"Total frames processed for {rtmp_url}: {len(frames)}")

                if len(frames) > 0:
                    first_frame = frames[0]
                    last_frame = frames[-1]
                    first_result = self.detection_model(first_frame, classes=[0], verbose=False, imgsz=1280)
                    last_result = self.detection_model(last_frame, classes=[0], verbose=False, imgsz=1280)
                    logger.debug(f"Processed first and last frames for {rtmp_url}")
                    
                    # Use draw_all_results from utils.py
                    frames = utils.draw_all_results(frames, first_result, last_result)
                    return frames
                else:
                    logger.debug(f"No frames to process for {rtmp_url}")
                    return None
        except Exception as e:
            logger.debug(f"Error in _draw_results for {rtmp_url}: {str(e)}")
            return None

    def __del__(self):
        try:
            logger.debug("Destroying DrawResultService")
            for rtmp_url in list(self.running.keys()):
                if self.running[rtmp_url]:
                    self.stop_draw_service(rtmp_url)
            logger.debug("DrawResultService destroyed")
        except Exception as e:
            logger.debug(f"Error destroying DrawResultService: {str(e)}")

    def list_running_threads(self):
        try:
            running_threads = []
            for rtmp_url, thread in self.draw_threads.items():
                running_threads.append({
                    'rtmp_url': rtmp_url,
                    'thread_id': thread.ident,
                    'thread_name': thread.name,
                    'is_alive': thread.is_alive()
                })
            return running_threads
        except Exception as e:
            logger.debug(f"Error listing running threads: {str(e)}")
            return []
