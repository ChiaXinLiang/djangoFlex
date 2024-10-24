import cv2
import time
import threading
from ..models import VideoCapConfig, CurrentVideoClip, CameraList
from django.db import transaction
from django.utils import timezone
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import timedelta, datetime
import subprocess
import json
import shutil
import pytz
import re
import logging
import ssl
import socket
from urllib.parse import urlparse
from .cameraStream_service import stream_to_rtmp

class VideoCapService:
    def __init__(self):
        """
        初始化 VideoCapService 類。
        設置各種配置參數，創建必要的目錄，並加載配置。
        """
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
        self.gop_length = 15
        self.hls_time = 2
        os.makedirs(self.video_clip_dir, exist_ok=True)
        self._load_configs()
        self.logger = logging.getLogger(__name__)
        self.stream_processes = {}
        self.stream_threads = {}
        self._stream_to_rtmp = stream_to_rtmp

    @staticmethod
    @transaction.atomic
    def reset_video_cap_system():
        """
        重置視頻捕獲系統。
        刪除所有當前視頻片段並將所有配置設置為非活動狀態。
        """
        from ..models import VideoCapConfig, CurrentVideoClip
        try:
            CurrentVideoClip.objects.all().delete()
            VideoCapConfig.objects.update(is_active=False)
        except Exception as e:
            logging.error(f"Error resetting video cap system: {str(e)}")

    def _load_configs(self):
        """
        從數據庫加載活動的視頻捕獲配置。
        """
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = config
                self.running[config.rtmp_url] = False
        except Exception as e:
            self.logger.error(f"Error loading configs: {str(e)}")

    def start_server(self, rtmp_url):
        """
        啟動指定 RTMP URL 的視頻捕獲服務。
        """
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

        # 更新 CameraList 狀態
        CameraList.objects.filter(camera_url=rtmp_url).update(camera_status=True)

        return True, "錄影開始 Server started successfully."

    def stop_server(self, rtmp_url):
        """
        停止指定 RTMP URL 的視頻捕獲服務。
        """
        if rtmp_url not in self.running:
            return False, "伺服器未找到"

        self.running[rtmp_url] = False

        # 等待捕獲線程結束
        if rtmp_url in self.capture_threads:
            try:
                self.capture_threads[rtmp_url].join(timeout=10)
                if self.capture_threads[rtmp_url].is_alive():
                    self.logger.warning(f"線程 {rtmp_url} 未在指定時間內停止")
            except Exception as e:
                self.logger.error(f"停止線程 {rtmp_url} 時發生錯誤: {str(e)}")
            finally:
                del self.capture_threads[rtmp_url]

        # 檢查並釋放捕獲對象
        if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
            try:
                self.caps[rtmp_url].release()
            except Exception as e:
                self.logger.error(f"釋放捕獲對象 {rtmp_url} 時發生錯誤: {str(e)}")
            finally:
                del self.caps[rtmp_url]

        with transaction.atomic():
            config = self.configs.get(rtmp_url)
            if config:
                config.is_active = False
                config.save()
                CurrentVideoClip.objects.filter(config=config).delete()

        hls_output_dir = os.path.join(self.video_clip_dir, f"{rtmp_url.split('/')[-1]}_hls")
        if os.path.exists(hls_output_dir):
            try:
                shutil.rmtree(hls_output_dir)
            except Exception as e:
                self.logger.error(f"刪除目錄 {hls_output_dir} 時發生錯誤: {str(e)}")

        if rtmp_url in self.configs:
            del self.configs[rtmp_url]

        # 更新 CameraList 狀態
        CameraList.objects.filter(camera_url=rtmp_url).update(camera_status=False)

        return True, "伺服器已成功停止"

    def check_server_status(self, rtmp_url):
        """
        檢查指定 RTMP URL 的服務運行狀態。
        """
        is_running = self.running.get(rtmp_url, False)
        is_active = VideoCapConfig.objects.filter(rtmp_url=rtmp_url, is_active=True).exists()
        camera_status = CameraList.objects.filter(camera_url=rtmp_url, camera_status=True).exists()
        return is_running and is_active and camera_status

    def _initialize_capture(self, rtmp_url):
        """
        初始化視頻捕獲對象。
        設置捕獲參數如幀率、分辨率等，並檢查捕獲對象是否成功打開。
        """
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
        except Exception as e:
            self.logger.error(f"Error initializing capture for {rtmp_url}: {str(e)}")
            self.caps[rtmp_url] = None

    def _capture_loop(self, rtmp_url):
        """
        視頻捕獲的主循環。
        持續從視頻流中讀取幀，處理重連邏輯，並更新視頻片段。
        同時啟動 FFmpeg 進程來處理 HLS 輸出。
        """
        # 檢查 rtmp_url 是否在 self.configs 中
        if rtmp_url not in self.configs:
            self.logger.error(f"配置未找到：{rtmp_url}")
            return

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
            '-preset', 'ultrafast', #'ultrafast',
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
            '-loglevel', 'warning',  # Set log level to warning
            '-err_detect', 'ignore_err',  # Ignore decoding errors
            hls_output
        ]


        ffmpeg_process = None
        try:
            ffmpeg_process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, universal_newlines=True)

            def log_stderr(stderr):
                for line in iter(stderr.readline, ''):
                    if line.strip():
                        self.logger.warning(f"FFmpeg: {line.strip()}")

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

        except Exception as e:
            self.logger.error(f"捕獲循環中發生錯誤 {rtmp_url}: {str(e)}")
        finally:
            if ffmpeg_process:
                ffmpeg_process.terminate()
                ffmpeg_process.wait()

        # 在循環結束後清理資源
        self._cleanup_resources(rtmp_url)

    def _get_frame_size(self, rtmp_url):
        """
        獲取指定 RTMP URL 的幀大小（分辨率）。
        """
        return self.resolution

    def _reconnect(self, rtmp_url):
        """
        嘗試重新連接視頻捕獲對象。
        釋放當前捕獲對象並重新初始化。
        """
        if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
            self.caps[rtmp_url].release()
        self.caps[rtmp_url] = None
        time.sleep(1)
        self._initialize_capture(rtmp_url)
        return self.caps[rtmp_url] is not None and self.caps[rtmp_url].isOpened()

    def _set_inactive(self, rtmp_url):
        """
        將指定的 RTMP URL 配置設置為非活動狀態。
        清理相關資源和數據庫記錄。
        """
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

    # async def update_frame(self, rtmp_url, frame):
    #     """
    #     異步更新當前幀。
    #     將幀編碼為 JPEG 並存儲在 Redis 中。
    #     """
    #     if frame is None:
    #         return

    #     _, buffer = cv2.imencode('.jpg', frame)
    #     frame_bytes = buffer.tobytes()

    #     await asyncio.to_thread(self.redis_client.set, f"video_cap_service:current_image:{rtmp_url}", frame_bytes)

    def _check_and_update_video_clip(self, rtmp_url, hls_output_dir):
        """
        檢查並更新視頻片段。
        查找最新的 TS 文件並在數據庫中創建相應的 CurrentVideoClip 記錄。
        """
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
        except Exception as e:
            self.logger.error(f"Error checking and updating video clip for {rtmp_url}: {str(e)}")

    def __del__(self):
        """
        析構函數。
        確保所有運行中的服務在對象被銷毀時停止。
        """
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                self.stop_server(rtmp_url)
        for rtmp_url in list(self.stream_processes.keys()):
            self._stop_stream(rtmp_url)

    def list_running_threads(self):
        """
        列出所有正在運行的捕獲線程的信息。
        """
        running_threads = []
        for rtmp_url, thread in self.capture_threads.items():
            running_threads.append({
                'rtmp_url': rtmp_url,
                'thread_id': thread.ident,
                'thread_name': thread.name,
                'is_alive': thread.is_alive()
            })
        return running_threads

    def start_all_cameras(self):
        """
        啟動 CameraList 中所有的攝像頭
        """
        cameras = CameraList.objects.all()
        started_count = 0
        for camera in cameras:
            success, _ = self.start_server(camera.camera_url)
            if success:
                started_count += 1
                camera.camera_status = True
                camera.save()
        return started_count, cameras.count()

    def stop_all_servers(self):
        """
        停止所有正在運行的視頻捕獲服務。
        """
        stopped_count = 0
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                success, _ = self.stop_server(rtmp_url)
                if success:
                    stopped_count += 1
                    camera = CameraList.objects.filter(camera_url=rtmp_url).first()
                    if camera:
                        camera.camera_status = False
                        camera.save()
        return stopped_count

    def start_camera(self, rtmp_url):
        """
        啟動指定 RTMP URL 的攝像機並開始串流。
        """
        try:
            camera = CameraList.objects.filter(camera_url=rtmp_url).first()

            # 啟動串流
            stream_thread = threading.Thread(
                target=self._stream_to_rtmp,
                args=(camera.camera_url, camera.stream_upload_video_path)
            )
            stream_thread.start()
            self.stream_threads[camera.camera_url] = stream_thread

            return True, "攝像機啟動並開始串流成功。"

        except CameraList.DoesNotExist:
            return False, f"未找到 ID 為 {camera.camera_name} 的攝像機"
        except Exception as e:
            return False, f"啟動攝像機時發生錯誤：{str(e)}"

    def stop_camera(self, rtmp_url):
        """
        停止指定 RTMP URL 的攝像機並結束串流。
        """
        try:
            camera = CameraList.objects.filter(camera_url=rtmp_url).first()
            if not camera:
                return False, f"未找到 URL 為 {rtmp_url} 的攝像機"

            # 停止串流
            if rtmp_url in self.stream_threads:
                self._stop_stream(rtmp_url)

            # 更新攝像機狀態
            camera.camera_status = False
            camera.save()

            return True, "攝像機停止並結束串流成功"
        except Exception as e:
            self.logger.error(f"停止攝像機時發生錯誤：{str(e)}")
            return False, f"停止攝像機時發生錯誤：{str(e)}"

    # def _stop_stream(self, rtmp_url):
    #     """
    #     停止指定 RTMP URL 的串流。
    #     """
    #     if rtmp_url in self.stream_stop_events:
    #         self.logger.info(f"正在停止 {rtmp_url} 的串流")
    #         self.stream_stop_events[rtmp_url].set()  # 設置停止事件

    #     if rtmp_url in self.stream_threads:
    #         thread = self.stream_threads[rtmp_url]
    #         thread.join(timeout=10)  # 等待線程結束，最多等待10秒
    #         if thread.is_alive():
    #             self.logger.warning(f"{rtmp_url} 的串流線程未能在指定時間內停止")
    #         else:
    #             self.logger.info(f"{rtmp_url} 的串流已成功停止")
    #         del self.stream_threads[rtmp_url]

    #     if rtmp_url in self.stream_stop_events:
    #         del self.stream_stop_events[rtmp_url]


    # def _stream_to_rtmp(rtmp_url: str, source_video: str) -> None:
    #     """
    #     將源影片檔案流式傳輸到指定的RTMP URL。

    #     此函數使用FFmpeg將影片檔案以流的形式傳輸到RTMP服務器。
    #     它會無限循環播放影片，直到用戶中斷或發生錯誤。

    #     參數:
    #     rtmp_url (str): 目標RTMP服務器的URL。
    #     source_video (str): 源影片檔案的路徑。

    #     返回:
    #     None
    #     """
    #     if not os.path.exists(source_video):
    #         print(f"錯誤：源影片檔案 '{source_video}' 不存在。")
    #         return

    #     ffmpeg_command = [
    #         "ffmpeg",
    #         "-re",
    #         "-stream_loop", "-1",  # 這將無限循環重複影片
    #         "-i", source_video,
    #         # "-c", "copy",
    #         "-vcodec", "libx264",
    #         "-preset:v", "ultrafast",
    #         "-f", "flv",
    #         rtmp_url
    #     ]

    #     try:
    #         print(f"開始從 {source_video} 向 {rtmp_url} 傳輸流")
    #         ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    #         while True:
    #             output = ffmpeg_process.stderr.readline().decode().strip()
    #             if output:
    #                 print(output)

    #             if ffmpeg_process.poll() is not None:
    #                 print("流傳輸進程已結束")
    #                 break

    #     except KeyboardInterrupt:
    #         print("用戶中斷了流傳輸")
    #     except Exception as e:
    #         print(f"發生錯誤：{str(e)}")
    #     finally:
    #         if ffmpeg_process.poll() is None:
    #             print("正在停止流傳輸進程")
    #             ffmpeg_process.terminate()
    #             ffmpeg_process.wait()

    # def check_camera_online(self, rtmp_url):
    #     """
    #     檢查攝像機是否在線（偵測到串流內容）
    #     """
    #     try:
    #         cap = cv2.VideoCapture(rtmp_url)
    #         if not cap.isOpened():
    #             return False
    #         ret, frame = cap.read()
    #         cap.release()
    #         return ret and frame is not None
    #     except Exception as e:
    #         self.logger.error(f"檢查攝像機 {rtmp_url} 在線狀態時發生錯誤：{str(e)}")
    #         return False

    # @staticmethod
    # def check_camera_online(rtmp_url, timeout = 1.0):
    #     """
    #     使用 Socket 測試 RTMP 主機連通性以加速離線檢測。
    #     """
    #     try:
    #         parsed_url = urlparse(rtmp_url)
    #         host, port = parsed_url.hostname, parsed_url.port or 1935  # 預設 RTMP 端口
    #         with socket.create_connection((host, port), timeout=timeout):
    #             return True
    #     except (socket.timeout, OSError):
    #         return False

    @staticmethod
    def check_camera_online(rtmp_url, timeout = 4):
        """
        使用 FFmpeg 測試 RTMP 串流是否在線。
        """
        try:
            # 呼叫 ffmpeg 並限制在 timeout 時間內返回
            command = [
                "ffmpeg", "-i", rtmp_url,
                "-t", "2",  # 最多讀取 2 秒
                "-f", "null", "-"  # 不輸出結果
            ]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
            return result.returncode == 0  # returncode 為 0 表示串流有效
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            print(f"FFmpeg 檢測錯誤：{e}")
            return False



    def _cleanup_resources(self, rtmp_url):
        """
        清理與特定 RTMP URL 相關的資源
        """
        if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
            self.caps[rtmp_url].release()
            del self.caps[rtmp_url]

        if rtmp_url in self.running:
            del self.running[rtmp_url]

        if rtmp_url in self.configs:
            del self.configs[rtmp_url]

        # 更新 CameraList 狀態
        CameraList.objects.filter(camera_url=rtmp_url).update(camera_status=False)

        self.logger.info(f"已清理 {rtmp_url} 的資源")

