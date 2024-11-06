import cv2
import time
import threading
import os
import shutil
from datetime import datetime, timedelta
import pytz
from django.conf import settings
from django.db import transaction
from ..utils.config_loader import ConfigLoader
from ..utils.video_cap_utils import VideoCapUtils
from ..repositories.video_cap_repository import VideoCapRepository
from ..exceptions.video_cap_exceptions import VideoCapException
from ..logs.log_manager import LogManager
from .hls_stream_service import HLSStreamService
from .camera_status_service import CameraStatusService
from ..models import CameraList, CurrentVideoClip

class VideoCapManager:
    def __init__(self):
        self.config = ConfigLoader.load_config()
        self.logger = LogManager.get_logger(__name__)
        self.repository = VideoCapRepository()
        self.hls_service = HLSStreamService()
        self.camera_status_service = CameraStatusService()
        self.running = {}
        self.capture_threads = {}
        self.caps = {}

    def start_video_cap_service(self, rtmp_url):
        try:
            if self.running.get(rtmp_url):
                return False, "伺服器已在運行中"

            config = self.repository.get_or_create_config(rtmp_url)
            self.running[rtmp_url] = True
            self.repository.set_config_active(config, True)

            self._initialize_capture(rtmp_url)
            self.capture_threads[rtmp_url] = threading.Thread(
                target=self._capture_loop,
                args=(rtmp_url,)
            )
            self.capture_threads[rtmp_url].start()

            self.camera_status_service.update_camera_status(rtmp_url, True)
            return True, "錄影開始，伺服器成功啟動。"
        except VideoCapException as e:
            self.logger.error(f"啟動視頻捕獲服務時發生錯誤: {str(e)}")
            return False, str(e)

    def stop_video_cap_service(self, rtmp_url):
        try:
            if rtmp_url not in self.running:
                self.logger.warning(f"嘗試停止未運行的服務: {rtmp_url}")
                return False, "伺服器未找到或未運行"

            self.running[rtmp_url] = False
            self._stop_capture_thread(rtmp_url)
            self._release_capture_object(rtmp_url)
            self.repository.set_config_inactive(rtmp_url)
            self.hls_service.cleanup_hls_output(rtmp_url)
            self.camera_status_service.update_camera_status(rtmp_url, False)

            return True, "伺服器已成功停止"
        except VideoCapException as e:
            self.logger.error(f"停止視頻捕獲服務時發生錯誤: {str(e)}")
            return False, str(e)
        except Exception as e:
            self.logger.error(f"停止視頻捕獲服務時發生未預期的錯誤: {str(e)}")
            return False, "發生未預期的錯誤"

    def get_service_running_status(self, rtmp_url):
        is_running = self.running.get(rtmp_url, False)
        self.logger.info(f"伺服器狀態 {rtmp_url}: {'運行中' if is_running else '未運行'}")
        return is_running

    def _initialize_capture(self, rtmp_url):
        try:
            if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
                self.caps[rtmp_url].release()

            cap_source = 0 if rtmp_url == '0' else rtmp_url
            self.caps[rtmp_url] = cv2.VideoCapture(cap_source)
            self.caps[rtmp_url].set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.caps[rtmp_url].set(cv2.CAP_PROP_FPS, self.config.fps)
            self.caps[rtmp_url].set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
            self.caps[rtmp_url].set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])

            if not self.caps[rtmp_url].isOpened():
                raise VideoCapException("無法開啟視頻捕獲")
        except Exception as e:
            self.logger.error(f"初始化捕獲 {rtmp_url} 時發生錯誤: {str(e)}")
            self.caps[rtmp_url] = None
            raise VideoCapException(f"初始化捕獲失敗: {str(e)}")

    def _capture_loop(self, rtmp_url):
        config = self.repository.get_config(rtmp_url)
        reconnect_start_time = None
        reconnect_attempts = 0
        last_frame_time = time.time()
        last_check_time = time.time()

        hls_output_dir = self.hls_service.start_hls_stream(rtmp_url, self.config.video_clip_dir)

        try:
            while self.running[rtmp_url]:
                if self.caps[rtmp_url] and self.caps[rtmp_url].isOpened():
                    ret, frame = self.caps[rtmp_url].read()
                    current_time = time.time()

                    if ret:
                        last_frame_time = current_time
                        reconnect_start_time = None
                        reconnect_attempts = 0

                        if current_time - last_check_time >= self.config.check_interval:
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
                    if elapsed_time > self.config.reconnect_timeout or reconnect_attempts > self.config.max_reconnect_attempts:
                        self._set_inactive(rtmp_url)
                        break

        except Exception as e:
            self.logger.error(f"捕獲循環中發生錯誤 {rtmp_url}: {str(e)}")
        finally:
            self.hls_service.stop_hls_stream(rtmp_url)
            self._cleanup_resources(rtmp_url)

    def _stop_capture_thread(self, rtmp_url):
        if rtmp_url in self.capture_threads:
            try:
                self.capture_threads[rtmp_url].join(timeout=10)
                if self.capture_threads[rtmp_url].is_alive():
                    self.logger.warning(f"線程 {rtmp_url} 未在指定時間內停止")
            except Exception as e:
                self.logger.error(f"停止線程 {rtmp_url} 時發生錯誤: {str(e)}")
            finally:
                self.capture_threads.pop(rtmp_url, None)
        else:
            self.logger.warning(f"嘗試停止不存在的捕獲線程: {rtmp_url}")

    def _release_capture_object(self, rtmp_url):
        if rtmp_url in self.caps and self.caps[rtmp_url] is not None:
            try:
                self.caps[rtmp_url].release()
            except Exception as e:
                self.logger.error(f"釋放捕獲對象 {rtmp_url} 時發生錯誤: {str(e)}")
            finally:
                del self.caps[rtmp_url]

    def _reconnect(self, rtmp_url):
        self._release_capture_object(rtmp_url)
        time.sleep(1)
        try:
            self._initialize_capture(rtmp_url)
            return self.caps[rtmp_url] is not None and self.caps[rtmp_url].isOpened()
        except VideoCapException:
            return False

    def _set_inactive(self, rtmp_url):
        self.repository.set_config_inactive(rtmp_url)
        self.running[rtmp_url] = False
        self._release_capture_object(rtmp_url)
        self.camera_status_service.update_camera_status(rtmp_url, False)

    def _cleanup_resources(self, rtmp_url):
        self._release_capture_object(rtmp_url)
        if rtmp_url in self.running:
            del self.running[rtmp_url]
        if rtmp_url in self.capture_threads:
            del self.capture_threads[rtmp_url]
        self.camera_status_service.update_camera_status(rtmp_url, False)
        self.logger.info(f"已清理 {rtmp_url} 的資源")

    def _check_and_update_video_clip(self, rtmp_url, hls_output_dir):
        config = self.repository.get_config(rtmp_url)
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
                            self.repository.create_current_video_clip(
                                config,
                                ts_file_path,
                                ts_file_timestamp,
                                ts_file_timestamp + timedelta(seconds=self.config.hls_time),
                                self.config.hls_time
                            )
        except Exception as e:
            self.logger.error(f"Error checking and updating video clip for {rtmp_url}: {str(e)}")

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

    def start_all_video_cap_service(self):
        cameras = CameraList.objects.all()
        started_count = 0
        for camera in cameras:
            success, _ = self.start_video_cap_service(camera.camera_url)
            if success:
                started_count += 1
                self.camera_status_service.update_camera_status(camera.camera_url, True)
        return started_count, cameras.count()

    def stop_all_video_cap_service(self):
        stopped_count = 0
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                success, _ = self.stop_video_cap_service(rtmp_url)
                if success:
                    stopped_count += 1
                    self.repository.set_config_inactive(rtmp_url)
        return stopped_count

    @staticmethod
    def check_camera_online(rtmp_url, timeout=4):
        return VideoCapUtils.check_camera_online(rtmp_url, timeout)

    def __del__(self):
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                self.stop_video_cap_service(rtmp_url)
