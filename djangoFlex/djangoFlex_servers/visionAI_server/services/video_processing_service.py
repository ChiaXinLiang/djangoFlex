import os
import threading
from .configuration_service import ConfigurationService
from .detection_service import DetectionService
from .drawing_service import DrawingService
from .ffmpeg_service import FFmpegService
from ..models import CameraDrawingStatus
from ...videoCap_server.models import CurrentVideoClip
from ..utils.FrameInterpolator import FrameInterpolator
from django.db import transaction
import time
import cv2

class VideoProcessingService:
    def __init__(self):
        self.drawing_service = DrawingService()
        self.ffmpeg_service = FFmpegService()
        self.rtmp_interpolator = {}
        self.rtmp_detection_service = {}
        self.running = {}
        self.draw_threads = {}
        self.last_processed_clip = {}

    def start_draw_service(self, rtmp_url):
        self.config_service = ConfigurationService()
        try:
            if rtmp_url in self.running and self.running[rtmp_url]:
                CameraDrawingStatus.objects.update_or_create(camera_url=rtmp_url, defaults={'is_drawing': True})
                return False, "Draw service already running"

            config = self.config_service.get_config(rtmp_url)
            if not config:
                return False, "Configuration not found"

            self.running[rtmp_url] = True
            self.rtmp_interpolator[rtmp_url] = FrameInterpolator()
            self.rtmp_detection_service[rtmp_url] = DetectionService()

            self.draw_threads[rtmp_url] = threading.Thread(target=self._draw_loop, args=(rtmp_url,))
            self.draw_threads[rtmp_url].start()

            CameraDrawingStatus.objects.update_or_create(camera_url=rtmp_url, defaults={'is_drawing': True})

            return True, "Draw service started successfully"
        except Exception as e:
            return False, f"Error starting draw service: {str(e)}"

    def stop_draw_service(self, rtmp_url):
        self.config_service = ConfigurationService()
        try:
            if rtmp_url not in self.running or not self.running[rtmp_url]:
                CameraDrawingStatus.objects.update_or_create(camera_url=rtmp_url, defaults={'is_drawing': False})
                return False, "Draw service not running"

            self.running[rtmp_url] = False
            if rtmp_url in self.draw_threads:
                self.draw_threads[rtmp_url].join(timeout=10)
                if self.draw_threads[rtmp_url].is_alive():
                    pass
                del self.draw_threads[rtmp_url]

            self.ffmpeg_service.stop_ffmpeg_process(rtmp_url)

            CameraDrawingStatus.objects.update_or_create(camera_url=rtmp_url, defaults={'is_drawing': False})

            return True, "Draw service stopped successfully"
        except Exception as e:
            return False, f"Error stopping draw service: {str(e)}"

    def _draw_loop(self, rtmp_url):
        """
        管理給定 RTMP URL 的視頻處理循環。

        此方法嘗試啟動並維護一個 FFmpeg 過程以進行視頻處理。
        如果失敗，它會重試指定次數。在每次嘗試期間，
        它處理視頻剪輯，調整幀率，並將幀寫入 FFmpeg 過程。

        參數:
            rtmp_url (str): 視頻流的 RTMP URL。

        引發:
            Exception: 如果 FFmpeg 過程未運行或視頻處理在最大重試次數後失敗。

        注意:
            當循環不再運行時，此方法將停止 FFmpeg 過程。
        """
        try:
            config = self.config_service.get_config(rtmp_url)
            max_retries = 5 # 最大重試次數
            retry_delay = 10  # 每次重試之間的延遲，seconds

            for attempt in range(max_retries):
                try:
                    if not self.ffmpeg_service.is_ffmpeg_running(rtmp_url):
                        self.ffmpeg_service.start_ffmpeg_process(rtmp_url, config['output_url'])

                    while self.running[rtmp_url]:
                        if not self.ffmpeg_service.is_ffmpeg_running(rtmp_url):
                            raise Exception("FFmpeg process is not running")

                        start_time = time.time()
                        # print("開始進行interpolation處理")
                        result = self._process_video_clip(rtmp_url)
                        if result is not None:
                            # print("接收到interpolation處理結果")
                            frame_data, duration = result
                            frame_data = self.drawing_service.adjust_fps(frame_data, duration, config['fps'])
                            end_time = time.time()
                            time_diff = end_time - start_time
                            if frame_data is not None and len(frame_data) > 0:
                                for frame in frame_data:
                                    if self.running[rtmp_url]:
                                        # print("開始打出interpolation處理結果rtmp")
                                        self.ffmpeg_service.write_frame(rtmp_url, frame)
                                        sleep_time = max(0, ((1 - time_diff) / config['fps']))
                                        time.sleep(sleep_time)
                        else:
                            time.sleep(1 / config['fps'])

                    break  # If we get here, the loop ran successfully
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        break
        except Exception as e:
            pass
        finally:
            self.ffmpeg_service.stop_ffmpeg_process(rtmp_url)

    def _process_video_clip(self, rtmp_url):
        try:
            with transaction.atomic():
                config = self.config_service.get_config(rtmp_url)

                current_video_clip = CurrentVideoClip.objects.filter(config__rtmp_url=rtmp_url).order_by('-start_time').first()

                if current_video_clip is None:
                    return None

                # 先取得所有要刪除的舊記錄
                old_clips = CurrentVideoClip.objects.filter(
                    config__rtmp_url=rtmp_url,
                    start_time__lt=current_video_clip.start_time
                )

                # 刪除每個舊記錄對應的實體檔案
                for clip in old_clips:
                    try:
                        if os.path.exists(clip.clip_path):
                            os.remove(clip.clip_path)
                    except Exception as e:
                        # 記錄錯誤但不中斷處理流程
                        print(f"Error deleting file {clip.clip_path}: {str(e)}")

                # 刪除資料庫記錄
                old_clips.delete()

                clip_path = current_video_clip.clip_path

                if not self.drawing_service.is_valid_clip(clip_path):
                    return None

                if self._is_clip_already_processed(rtmp_url, current_video_clip):
                    return None

                # print("找到指定的路徑")
                self.last_processed_clip[rtmp_url] = current_video_clip

                # print("開始讀取視頻幀")
                org_frame_list, duration = self.drawing_service.read_video_frames(clip_path)

                if len(org_frame_list) > 0:
                    # print("開始進行interpolation處理")
                    processed_frame_list = []
                    total_frame_number = len(org_frame_list) - 1
                    middle_frame_number = int(total_frame_number/2)
                    frame_count = 0
                    for frame in org_frame_list:
                        process_frame = frame.copy()
                        # Process frame
                        if frame_count == 0 or frame_count == middle_frame_number or frame_count == total_frame_number:
                            process_frame = self.rtmp_interpolator[rtmp_url].process_keyframe(process_frame, frame_count, self.rtmp_detection_service[rtmp_url])
                            self.rtmp_interpolator[rtmp_url].prev_frame_count = frame_count
                            # print(f"Processed Keyframe: {frame_count}")
                        else:
                            process_frame = self.rtmp_interpolator[rtmp_url].process_interpolated_frame(process_frame, frame_count)
                            # print(f"Processed Interpolated Frame: {frame_count}")
                        frame_count += 1
                        processed_frame_list.append(process_frame)

                    current_video_clip.delete()
                    os.remove(clip_path)

                    return processed_frame_list, duration
                else:
                    return None
        except Exception as e:
            return None

    def _is_clip_already_processed(self, rtmp_url, current_video_clip):
        last_processed_clip = self.last_processed_clip.get(rtmp_url)
        return last_processed_clip and last_processed_clip.id == current_video_clip.id

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

    def __del__(self):
        try:
            for rtmp_url in list(self.running.keys()):
                if self.running[rtmp_url]:
                    self.stop_draw_service(rtmp_url)
        except Exception as e:
            pass
