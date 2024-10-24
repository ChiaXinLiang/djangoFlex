import cv2
import numpy as np
import threading
import logging
import time
from ...videoCap_server.models import VideoCapConfig, CurrentVideoClip
from django.conf import settings
from django.db import transaction
import os
from . import utils
import time
import subprocess


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
        except Exception as e:
            pass

    def _load_configs(self):
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = {
                    'rtmp_url': config.rtmp_url,
                    # 'output_url': f"rtmp://192.168.1.77/live/result_demo",
                    'output_url': f"rtmp://localhost/live/result_{config.rtmp_url.split('/')[-1]}",
                    'is_active': True
                }
                self.running[config.rtmp_url] = False
        except Exception as e:
            pass

    def start_draw_service(self, rtmp_url):
        try:
            if rtmp_url in self.running and self.running[rtmp_url]:
                return False, "Draw service already running"

            config = self.configs.get(rtmp_url)

            self.running[rtmp_url] = True
            self.draw_threads[rtmp_url] = threading.Thread(target=self._draw_loop, args=(rtmp_url,))
            self.draw_threads[rtmp_url].start()

            return True, "Draw service started successfully"
        except Exception as e:
            return False, f"Error starting draw service: {str(e)}"

    def stop_draw_service(self, rtmp_url):
        try:
            if rtmp_url not in self.running or not self.running[rtmp_url]:
                return False, "Draw service not running"

            self.running[rtmp_url] = False
            if rtmp_url in self.draw_threads:
                self.draw_threads[rtmp_url].join(timeout=10)
                if self.draw_threads[rtmp_url].is_alive():
                    pass
                del self.draw_threads[rtmp_url]

            if rtmp_url in self.ffmpeg_processes:
                try:
                    self.ffmpeg_processes[rtmp_url].stdin.close()
                    self.ffmpeg_processes[rtmp_url].terminate()
                    self.ffmpeg_processes[rtmp_url].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.ffmpeg_processes[rtmp_url].kill()
                del self.ffmpeg_processes[rtmp_url]

            return True, "Draw service stopped successfully"
        except Exception as e:
            return False, f"Error stopping draw service: {str(e)}"

    def _draw_loop(self, rtmp_url):
        try:
            config = self.configs[rtmp_url]
            max_retries = 5
            retry_delay = 10  # seconds

            for attempt in range(max_retries):

                try:
                    if rtmp_url not in self.ffmpeg_processes:
                        self._start_ffmpeg_process(rtmp_url)

                    while self.running[rtmp_url]:
                        if not self.ffmpeg_checkers[rtmp_url]():
                            raise Exception("FFmpeg process is not running")

                        start_time = time.time()
                        result = self._draw_results(rtmp_url)
                        if result is not None:
                            frame_data, duration = result
                            frame_data = utils.fps_controller_adjustment(frame_data, duration, self.fps)
                            end_time = time.time()
                            time_diff = end_time - start_time
                            if frame_data is not None and len(frame_data) > 0:
                                for frame in frame_data:
                                    if self.running[rtmp_url]:
                                        self.ffmpeg_processes[rtmp_url].stdin.write(frame)
                                        # print(f"sleep_time: {sleep_time}", f"duration: {duration}", f"fps: {self.fps}")
                                        sleep_time = max(0, ((1- time_diff) / self.fps) )
                                        time.sleep(sleep_time)

                        else:
                            time.sleep(1 / self.fps)


                    break  # If we get here, the loop ran successfully
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        break
        except Exception as e:
            pass
        finally:
            self._stop_ffmpeg_process(rtmp_url)

    def _start_ffmpeg_process(self, rtmp_url):
        config = self.configs[rtmp_url]
        try:
            self.ffmpeg_processes[rtmp_url], self.ffmpeg_checkers[rtmp_url] = utils.create_ffmpeg_process(config['output_url'], self.fps, self.frame_size)
        except Exception as e:
            raise

    def _stop_ffmpeg_process(self, rtmp_url):
        if rtmp_url in self.ffmpeg_processes:
            try:
                self.ffmpeg_processes[rtmp_url].stdin.close()
                self.ffmpeg_processes[rtmp_url].terminate()
                self.ffmpeg_processes[rtmp_url].wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_processes[rtmp_url].kill()
            del self.ffmpeg_processes[rtmp_url]
            del self.ffmpeg_checkers[rtmp_url]

    def _draw_results(self, rtmp_url):
        try:
            with transaction.atomic():
                config = self.configs[rtmp_url]
                current_video_clip = CurrentVideoClip.objects.filter(config__rtmp_url=rtmp_url).order_by('-start_time').first()

                if current_video_clip is None:
                    return None

                clip_path = current_video_clip.clip_path

                if not clip_path or not os.path.exists(clip_path) or not clip_path.endswith('.ts'):
                    return None

                # Compare current_video_clip with last_processed_clip
                last_processed_clip = self.last_processed_clip.get(rtmp_url)
                if last_processed_clip and last_processed_clip.id == current_video_clip.id:
                    return None

                # Update the last processed clip
                self.last_processed_clip[rtmp_url] = current_video_clip

                cap = cv2.VideoCapture(clip_path)
                frames = []
                duration = 0

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames.append(frame)
                    duration += 1 / cap.get(cv2.CAP_PROP_FPS)

                cap.release()

                if len(frames) > 0:
                    first_frame = frames[0]
                    last_frame = frames[-1]
                    first_result = self.detection_model(first_frame, classes=[0], verbose=False, imgsz=1280)
                    last_result = self.detection_model(last_frame, classes=[0], verbose=False, imgsz=1280)

                    # Use draw_all_results from utils.py
                    frames = utils.draw_all_results(frames, first_result, last_result)
                    return frames, duration
                else:
                    return None
        except Exception as e:
            return None

    def __del__(self):
        try:
            for rtmp_url in list(self.running.keys()):
                if self.running[rtmp_url]:
                    self.stop_draw_service(rtmp_url)
        except Exception as e:
            pass

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
            return []