import cv2
from ..utils.drawing_utils import draw_bounding_boxes, draw_all_results
from ..utils.video_utils import fps_controller_adjustment
import os

class DrawingService:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.thickness = 2
        self.text_color = (255, 255, 255)  # White color for text
        self.box_color = (0, 255, 0)  # Green color for bounding boxes
        self.predicted_box_color = (0, 255, 255)  # Yellow color for predicted boxes

    def draw_all_results(self, frames, first_result, last_result):
        return draw_all_results(frames, first_result, last_result)

    def adjust_fps(self, frame_data, duration, fps):
        return fps_controller_adjustment(frame_data, duration, fps)

    def is_valid_clip(self, clip_path):
        return clip_path and os.path.exists(clip_path) and clip_path.endswith('.ts')

    def read_video_frames(self, clip_path):
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
        return frames, duration
