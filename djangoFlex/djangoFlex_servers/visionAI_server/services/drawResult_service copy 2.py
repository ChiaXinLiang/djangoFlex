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
    """
    負責處理視頻流的繪圖服務，包括物體檢測和結果繪製。
    """

    def __init__(self):
        """
        初始化 DrawResultService 類的實例。
        設置繪圖參數，加載配置和模型。
        """
        try:
            self.configs = {}  # 存儲視頻流配置
            self.running = {}  # 追踪每個 RTMP URL 的運行狀態
            self.draw_threads = {}  # 存儲每個 RTMP URL 的繪圖線程
            self.ffmpeg_processes = {}  # 存儲每個 RTMP URL 的 FFmpeg 進程
            self.ffmpeg_checkers = {}  # 存儲每個 RTMP URL 的 FFmpeg 進程檢查器

            # 設置繪圖參數
            self.font = cv2.FONT_HERSHEY_SIMPLEX
            self.font_scale = 0.5
            self.thickness = 2
            self.text_color = (255, 255, 255)  # 文字顏色：白色
            self.box_color = (0, 255, 0)  # 邊界框顏色：藍色
            self.predicted_box_color = (0, 255, 255)  # 預測框顏色：黃色
            self.frame_size = (1280, 720)  # 設置幀大小
            self.fps = 15  # 設置幀率

            self._load_configs()  # 加載配置
            utils.download_model_if_not_exists("360_1280_person_yolov8m", "1")  # 下載模型（如果不存在）
            self.detection_model = utils.load_detection_model("models/360_1280_person_yolov8m/1/model/best.pt")  # 加載檢測模型
            self.last_processed_clip = {}  # 存儲每個 RTMP URL 的最後處理的片段
        except Exception as e:
            pass  # 初始化過程中的錯誤被忽略，可能需要添加日誌記錄

    def _load_configs(self):
        """
        從數據庫加載活動的視頻流配置。
        """
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = {
                    'rtmp_url': config.rtmp_url,
                    'output_url': f"rtmp://localhost/live/result_demo",
                    'is_active': True
                }
                self.running[config.rtmp_url] = False
        except Exception as e:
            pass  # 加載配置過程中的錯誤被忽略，可能需要添加日誌記錄

    def start_draw_service(self, rtmp_url):
        """
        啟動指定 RTMP URL 的繪圖服務。

        Args:
            rtmp_url (str): 要啟動服務的 RTMP URL。

        Returns:
            tuple: (成功狀態, 消息)
        """
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
        """
        停止指定 RTMP URL 的繪圖服務。

        Args:
            rtmp_url (str): 要停止服務的 RTMP URL。

        Returns:
            tuple: (成功狀態, 消息)
        """
        try:
            if rtmp_url not in self.running or not self.running[rtmp_url]:
                return False, "Draw service not running"

            self.running[rtmp_url] = False
            if rtmp_url in self.draw_threads:
                self.draw_threads[rtmp_url].join(timeout=10)
                if self.draw_threads[rtmp_url].is_alive():
                    pass  # 線程未能在超時內結束，可能需要額外處理
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
        """
        繪圖服務的主循環。
        從視頻流中提取幀，進行物體檢測，並將結果繪製在幀上。

        Args:
            rtmp_url (str): 要處理的 RTMP URL。
        """
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
                            if frame_data and len(frame_data) > 0:
                                for frame in frame_data:
                                    if frame is not None and frame.size > 0:
                                        self.ffmpeg_processes[rtmp_url].stdin.write(frame.tobytes())
                                    else:
                                        print("跳過無效幀")
                            else:
                                print("沒有有效的幀數據")
                        else:
                            time.sleep(1 / self.fps)

                    break  # 如果到達這裡，循環成功運行
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        break  # 達到最大重試次數，退出循環
        except Exception as e:
            print(f"繪圖循環中發生錯誤：{str(e)}")
        finally:
            self._stop_ffmpeg_process(rtmp_url)

    def _start_ffmpeg_process(self, rtmp_url):
        """
        為指定的 RTMP URL 啟動 FFmpeg 進程。

        Args:
            rtmp_url (str): 要啟動 FFmpeg 進程的 RTMP URL。

        Raises:
            Exception: 如果啟動 FFmpeg 進程時發生錯誤。
        """
        config = self.configs[rtmp_url]
        try:
            self.ffmpeg_processes[rtmp_url], self.ffmpeg_checkers[rtmp_url] = utils.create_ffmpeg_process(config['output_url'], self.fps, self.frame_size)
        except Exception as e:
            raise  # 重新拋出異常，可能需要在調用處進行處理

    def _stop_ffmpeg_process(self, rtmp_url):
        """
        停止指定 RTMP URL 的 FFmpeg 進程。

        Args:
            rtmp_url (str): 要停止 FFmpeg 進程的 RTMP URL。
        """
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
        """
        從數據庫獲取當前視頻片段，提取幀並進行物體檢測，然後將結果繪製在幀上。

        Args:
            rtmp_url (str): 要處理的 RTMP URL。

        Returns:
            tuple or None: 包含處理後的幀數據和持續時間的元組，如果處理失敗則返回 None。
        """
        try:
            with transaction.atomic():
                config = self.configs[rtmp_url]
                current_video_clip = CurrentVideoClip.objects.filter(config__rtmp_url=rtmp_url).order_by('-start_time').first()

                if current_video_clip is None:
                    return None

                clip_path = current_video_clip.clip_path

                if not clip_path or not os.path.exists(clip_path) or not clip_path.endswith('.ts'):
                    return None

                # 比較當前視頻片段與上次處理的片段
                last_processed_clip = self.last_processed_clip.get(rtmp_url)
                if last_processed_clip and last_processed_clip.id == current_video_clip.id:
                    return None

                # 更新最後處理的片段
                self.last_processed_clip[rtmp_url] = current_video_clip

                cap = cv2.VideoCapture(clip_path)
                if not cap.isOpened():
                    print(f"無法打開視頻文件：{clip_path}")
                    return None

                frames = []
                duration = 0

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames.append(frame)
                    duration += 1 / cap.get(cv2.CAP_PROP_FPS)

                cap.release()

                if len(frames) == 0:
                    print(f"無法從視頻中讀取幀：{clip_path}")
                    return None

                if len(frames) > 0:
                    first_frame = frames[0]
                    last_frame = frames[-1]
                    first_result = self.detection_model(first_frame, classes=[0], verbose=False, imgsz=1280)
                    last_result = self.detection_model(last_frame, classes=[0], verbose=False, imgsz=1280)

                    # 使用 utils.py 中的 draw_all_results
                    frames = utils.draw_all_results(frames, first_result, last_result)
                    return frames, duration
                else:
                    return None
        except Exception as e:
            print(f"處理視頻時發生錯誤：{str(e)}")
            return None

    def __del__(self):
        """
        析構函數，確保所有運行中的繪圖服務在對象被銷毀時停止。
        """
        try:
            for rtmp_url in list(self.running.keys()):
                if self.running[rtmp_url]:
                    self.stop_draw_service(rtmp_url)
        except Exception as e:
            pass  # 析構過程中的錯誤被忽略，可能需要添加日誌記錄

    def list_running_threads(self):
        """
        列出當前運行中的所有繪圖線程。

        Returns:
            list: 包含運行中線程信息的字典列表。
        """
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
            return []  # 如果發生錯誤，返回空列表

