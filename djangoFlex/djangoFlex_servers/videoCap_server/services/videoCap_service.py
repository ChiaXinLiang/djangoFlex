import cv2
import time
import threading
from ..models import VideoCapConfig, CurrentVideoClip
from django.db import transaction
from django.utils import timezone
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import timedelta, datetime
import subprocess
import shutil
import pytz
import re

class VideoCapService:
    def __init__(self):
        self.configs = {}
        self.caps = {}
        self.running = {}
        self.capture_threads = {}
        self.max_reconnect_attempts = 5
        self.reconnect_timeout = 5 
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.fps = 15
        self.frame_interval = 1 / self.fps
        self.video_clip_duration = 1
        self.check_interval = 0.1
        self.video_clip_dir = os.path.join('tmp', 'video_clip')
        self.resolution = (1280, 720)
        self.gop_length = 30
        self.hls_time = 1
        os.makedirs(self.video_clip_dir, exist_ok=True)
        self._load_configs()

    @staticmethod
    @transaction.atomic
    def reset_video_cap_system():
        from ..models import VideoCapConfig, CurrentVideoClip
        try:
            CurrentVideoClip.objects.all().delete()
            VideoCapConfig.objects.update(is_active=False)
        except Exception:
            pass

    def _load_configs(self):
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = config
                self.running[config.rtmp_url] = False
        except Exception:
            pass

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

            CurrentVideoClip.objects.filter(config=config).delete()

        hls_output_dir = os.path.join(self.video_clip_dir, f"{rtmp_url.split('/')[-1]}_hls")
        if os.path.exists(hls_output_dir):
            shutil.rmtree(hls_output_dir)

        if os.path.exists(self.video_clip_dir):
            shutil.rmtree(self.video_clip_dir)

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
            self.caps[rtmp_url].set(cv2.CAP_PROP_FPS, self.fps)
            self.caps[rtmp_url].set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.caps[rtmp_url].set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            if not self.caps[rtmp_url].isOpened():
                raise Exception("Failed to open video capture")
        except Exception:
            self.caps[rtmp_url] = None

    def _capture_loop(self, rtmp_url):
        config = self.configs[rtmp_url]
        reconnect_start_time = None
        reconnect_attempts = 0
        last_frame_time = time.time()
        last_check_time = time.time()

        hls_output_dir = os.path.join(self.video_clip_dir, f"{rtmp_url.split('/')[-1]}_hls")
        os.makedirs(hls_output_dir, exist_ok=True)
        hls_output = os.path.join(hls_output_dir, 'index.m3u8')

        ffmpeg_command = [
            'ffmpeg',
            '-y',
            '-i', rtmp_url,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-r', str(self.fps),
            '-g', str(self.gop_length),
            '-keyint_min', str(self.gop_length),
            '-force_key_frames', f"expr:if(isnan(prev_forced_n),1,eq(n,prev_forced_n+{self.gop_length}))",
            '-s', f'{self.resolution[0]}x{self.resolution[1]}',
            '-f', 'hls',
            '-hls_time', str(self.hls_time),
            '-hls_segment_type', 'mpegts',
            '-hls_flags', 'independent_segments',
            '-strftime', '1',
            '-strftime_mkdir', '1',
            '-hls_segment_filename', os.path.join(hls_output_dir, f'%Y%m%d%H%M_%s.ts'),
            hls_output
        ]

        ffmpeg_process = None
        try:
            ffmpeg_process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE)

            def log_stderr(stderr):
                for line in iter(stderr.readline, b''):
                    pass

            threading.Thread(target=log_stderr, args=(ffmpeg_process.stderr,), daemon=True).start()

            while self.running[rtmp_url]:
                if rtmp_url in self.caps and self.caps[rtmp_url] is not None and self.caps[rtmp_url].isOpened():
                    ret, frame = self.caps[rtmp_url].read()
                    current_time = time.time()

                    if ret:
                        last_frame_time = current_time
                        reconnect_start_time = None
                        reconnect_attempts = 0

                        if current_time - last_check_time >= self.check_interval:
                            self._check_and_update_video_clip(rtmp_url, hls_output_dir)
                            last_check_time = current_time

                    elif current_time - last_frame_time > 1:
                        if reconnect_start_time is None:
                            reconnect_start_time = current_time
                            reconnect_attempts += 1
                        self._reconnect(rtmp_url)
                else:
                    if reconnect_start_time is None:
                        reconnect_start_time = time.time()
                        reconnect_attempts += 1
                    self._reconnect(rtmp_url)
                
                if reconnect_start_time is not None:
                    elapsed_time = time.time() - reconnect_start_time
                    if elapsed_time > self.reconnect_timeout or reconnect_attempts > self.max_reconnect_attempts:
                        self._set_inactive(rtmp_url)
                        break

        except Exception:
            pass
        finally:
            if ffmpeg_process:
                ffmpeg_process.terminate()
                ffmpeg_process.wait()

    def _get_frame_size(self, rtmp_url):
        return self.resolution

    def _reconnect(self, rtmp_url):
        if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
            self.caps[rtmp_url].release()
        self.caps[rtmp_url] = None
        time.sleep(1)
        self._initialize_capture(rtmp_url)
        return self.caps[rtmp_url] is not None and self.caps[rtmp_url].isOpened()

    def _set_inactive(self, rtmp_url):
        with transaction.atomic():
            config = self.configs[rtmp_url]
            config.is_active = False
            config.save()

            CurrentVideoClip.objects.filter(config=config).delete()

        self.running[rtmp_url] = False
        if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
            self.caps[rtmp_url].release()
        self.caps[rtmp_url] = None

        if rtmp_url in self.capture_threads:
            del self.capture_threads[rtmp_url]

        hls_output_dir = os.path.join(self.video_clip_dir, f"{rtmp_url.split('/')[-1]}_hls")
        if os.path.exists(hls_output_dir):
            shutil.rmtree(hls_output_dir)

    async def update_frame(self, rtmp_url, frame):
        if frame is None:
            return
        
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        await asyncio.to_thread(self.redis_client.set, f"video_cap_service:current_image:{rtmp_url}", frame_bytes)

    def _check_and_update_video_clip(self, rtmp_url, hls_output_dir):
        config = self.configs[rtmp_url]

        try:
            ts_files = [f for f in os.listdir(hls_output_dir) if f.endswith('.ts')]
            if ts_files:
                latest_ts_file = max(ts_files, key=lambda f: os.path.getmtime(os.path.join(hls_output_dir, f)))
                ts_file_path = os.path.join(hls_output_dir, latest_ts_file)
                
                existing_clip = CurrentVideoClip.objects.filter(config=config, clip_path=ts_file_path).first()
                if not existing_clip:
                    if os.path.exists(ts_file_path):
                        ts_file_timestamp = datetime.fromtimestamp(os.path.getmtime(ts_file_path))
                        ts_file_timestamp = pytz.timezone('UTC').localize(ts_file_timestamp)

                        with transaction.atomic():
                            CurrentVideoClip.objects.create(
                                config=config,
                                clip_path=ts_file_path,
                                start_time=ts_file_timestamp,
                                end_time=ts_file_timestamp + timedelta(seconds=self.video_clip_duration),
                                duration=self.video_clip_duration
                            )
        except Exception:
            pass

    def __del__(self):
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                self.stop_server(rtmp_url)

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
