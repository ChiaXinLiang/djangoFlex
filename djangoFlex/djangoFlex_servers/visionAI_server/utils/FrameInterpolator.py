import cv2
import numpy as np
import os

class FrameInterpolator:
    def __init__(self, frame_interval=5):
        self.frame_interval = frame_interval
        self.prev_detections = {}
        self.prev_frame_count = 0
        self.last_keyframe_detections = {}
        self.next_keyframe_detections = {}
        self.last_keyframe_number = 0
        self.next_keyframe_number = 0
        # Add buffer for smooth interpolation
        self.detection_buffer = {}  # track_id -> list of (frame_num, bbox, conf)
        self.buffer_size = 4  # Store 4 keyframes for better interpolation
        self.smoothing_factor = 0.8  # Adjustable smoothing factor

    def setup_video_io(self, input_path, width, height, fps):
        """Setup video writer"""
        output_path = f'result_{os.path.basename(input_path)}.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        return cv2.VideoWriter(output_path, fourcc, fps, (width, height)), output_path

    def process_keyframe(self, frame, frame_count, detection_service):
        """處理關鍵幀並進行物件偵測"""
        try:
            results = detection_service.detect_objects(frame)
            if results is None or len(results) == 0:
                print("未檢測到任何物件")
                return frame

            if results[0].boxes is None or len(results[0].boxes) == 0:
                print("未檢測到任何邊界框")
                return frame

            current_detections = {}

            for box in results[0].boxes:
                track_id = int(box.id[0]) if box.id is not None else None
                if track_id is not None:
                    x1, y1, x2, y2 = box.xyxy[0]
                    detection = {
                        'bbox': (x1, y1, x2, y2),
                        'conf': float(box.conf)
                    }
                    current_detections[track_id] = detection

                    # Update detection buffer
                    if track_id not in self.detection_buffer:
                        self.detection_buffer[track_id] = []
                    self.detection_buffer[track_id].append((frame_count, detection['bbox'], detection['conf']))

                    # Keep only recent detections
                    if len(self.detection_buffer[track_id]) > self.buffer_size:
                        self.detection_buffer[track_id].pop(0)

                    # 確保繪製檢測結果
                    self._draw_detection(frame, track_id, (x1, y1, x2, y2), float(box.conf))

            # 更新關鍵幀資訊
            self.last_keyframe_detections = self.next_keyframe_detections
            self.next_keyframe_detections = current_detections
            self.last_keyframe_number = self.next_keyframe_number
            self.next_keyframe_number = frame_count

        except Exception as e:
            print(f"處理關鍵幀時發生錯誤：{str(e)}")

        return frame

    def _cubic_interpolation(self, p0, p1, p2, p3, t):
        """Cubic interpolation between points"""
        t2 = t * t
        t3 = t2 * t

        a = -0.5 * p0 + 1.5 * p1 - 1.5 * p2 + 0.5 * p3
        b = p0 - 2.5 * p1 + 2 * p2 - 0.5 * p3
        c = -0.5 * p0 + 0.5 * p2
        d = p1

        return a * t3 + b * t2 + c * t + d

    def _predict_velocity(self, track_history):
        """Calculate velocity based on recent detections"""
        if len(track_history) < 2:
            return [0, 0, 0, 0]

        recent_points = track_history[-2:]
        velocities = []
        for i in range(4):  # For each coordinate (x1, y1, x2, y2)
            v = (recent_points[-1][1][i] - recent_points[-2][1][i]) / \
                (recent_points[-1][0] - recent_points[-2][0])
            velocities.append(v)
        return velocities

    def process_interpolated_frame(self, frame, frame_count):
        """Process interpolated frames using cubic spline interpolation with velocity prediction"""
        # Get the surrounding keyframe numbers
        prev_keyframe = self.last_keyframe_number
        next_keyframe = self.next_keyframe_number

        # For each track_id that exists in both keyframes
        for track_id in set(self.last_keyframe_detections.keys()) & set(self.next_keyframe_detections.keys()):
            prev_bbox = self.last_keyframe_detections[track_id]['bbox']
            next_bbox = self.next_keyframe_detections[track_id]['bbox']
            prev_conf = self.last_keyframe_detections[track_id]['conf']
            next_conf = self.next_keyframe_detections[track_id]['conf']

            # Calculate interpolation factor (0 to 1)
            if next_keyframe == prev_keyframe:
                continue
            t = (frame_count - prev_keyframe) / (next_keyframe - prev_keyframe)

            # Interpolate bbox coordinates
            current_bbox = []
            for i in range(4):  # For each coordinate (x1, y1, x2, y2)
                coord = prev_bbox[i] + (next_bbox[i] - prev_bbox[i]) * t
                current_bbox.append(coord)

            # Interpolate confidence
            current_conf = prev_conf + (next_conf - prev_conf) * t

            # Draw the interpolated detection
            self._draw_detection(frame, track_id, tuple(current_bbox), current_conf, is_interpolated=True)

        return frame

    def _draw_detection(self, frame, track_id, bbox, conf, is_interpolated=False):
        """Draw detection boxes and labels with improved visibility"""
        x1, y1, x2, y2 = [int(coord) for coord in bbox]  # Convert to integers

        # Generate unique color for each track_id
        # color = ((track_id * 50) % 255, (track_id * 100) % 255, (track_id * 150) % 255)
        color = (255, 0, 0)

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Draw background for text
        # label = f'ID: {track_id} {"(I)" if is_interpolated else ""} {conf:.2f}'
        label = "person"
        (text_width, text_height), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)

        cv2.rectangle(frame,
                    (x1, y1 - text_height - 10),
                    (x1 + text_width + 10, y1),
                    color, -1)

        # Draw text
        cv2.putText(frame, label, (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def draw_info_overlay(self, frame, info_dict):
        """Draw information overlay on frame"""
        text_lines = [
            (f'Frame: {info_dict["frame_count"]}', (10, 60)),
            (f'FPS: {info_dict["fps"]:.1f}', (10, 90)),
            (f'{"Key Frame" if info_dict["is_keyframe"] else "Tracked"}', (10, 120)),
            (f'Queue Size: {info_dict["queue_size"]}', (10, 150))
        ]

        for text, (x, y) in text_lines:
            self._draw_text_with_background(frame, text, (x, y))

    def _draw_text_with_background(self, frame, text, pos,
                                font=cv2.FONT_HERSHEY_SIMPLEX,
                                font_scale=0.7,
                                font_thickness=2):
        """Draw text with semi-transparent background"""
        x, y = pos
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, font_thickness)

        padding = 5
        overlay = frame.copy()
        cv2.rectangle(overlay,
                    (x - padding, y - text_height - padding),
                    (x + text_width + padding, y + padding),
                    (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, text, (x, y), font, font_scale, (255, 255, 255), font_thickness)