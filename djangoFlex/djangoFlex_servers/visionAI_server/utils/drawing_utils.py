import cv2
import numpy as np

from .math_utils import interpolate_detections, calculate_distance

def draw_bounding_boxes(frame, results, box_color, text_color, thickness, font, font_scale):
    """
    在幀上繪製邊界框和標籤。

    Args:
        frame (numpy.ndarray): 要繪製的幀。
        results (list): 檢測結果列表。
        box_color (tuple): 邊界框的顏色。
        text_color (tuple): 文字的顏色。
        thickness (int): 線條粗細。
        font: 字體。
        font_scale (float): 字體大小。

    Returns:
        numpy.ndarray: 繪製了邊界框和標籤的幀。
    """
    label_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
                    (255, 255, 0), (0, 255, 255), (255, 0, 255),
                    (192, 192, 192), (128, 0, 0), (128, 128, 0),
                    (0, 128, 0), (128, 0, 128), (0, 128, 128),
                    (0, 0, 128), (72, 61, 139), (47, 79, 79),
                    (0, 206, 209), (148, 0, 211), (255, 20, 147),
                    (255, 165, 0)]

    for result in results:
        boxes = result.boxes.xyxy
        classes = result.boxes.cls

        for box, cls in zip(boxes, classes):
            x1, y1, x2, y2 = box.tolist()
            cls_num = int(cls.item())
            color = label_colors[cls_num % len(label_colors)]

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)

            label = "Person"
            t_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
            cv2.rectangle(frame, (int(x1), int(y1) - t_size[1] - 3), (int(x1) + t_size[0], int(y1) + 3), color, -1)
            cv2.putText(frame, label, (int(x1), int(y1) - 2), font, font_scale, text_color, thickness, lineType=cv2.LINE_AA)

    return frame


def draw_all_results(frames, first_result, last_result):
    """
    在所有幀上繪製檢測結果，包括插值的結果。

    Args:
        frames (list): 幀列表。
        first_result (list): 第一幀的檢測結果。
        last_result (list): 最後一幀的檢測結果。

    Returns:
        list: 繪製了檢測結果的幀列表。
    """
    if not frames or not first_result or not last_result:
        return frames

    num_frames = len(frames)

    first_detections = [(int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3]))
                        for r in first_result for box in r.boxes]
    last_detections = [(int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3]))
                       for r in last_result for box in r.boxes]

    interpolated_detections = interpolate_detections(first_detections, last_detections, num_frames - 2)

    for i, frame in enumerate(frames):
        if frame is None or frame.size == 0:
            continue

        detections = first_detections if i == 0 else (last_detections if i == num_frames - 1 else interpolated_detections[i-1])

        dummy_results = [type('DummyResult', (), {'boxes': type('DummyBoxes', (), {'xyxy': np.array([[x1, y1, x2, y2]]), 'cls': np.array([0])})()})() for x1, y1, x2, y2 in detections]
        frame = draw_bounding_boxes(frame, dummy_results, (0, 255, 0), (255, 255, 255), 2, cv2.FONT_HERSHEY_SIMPLEX, 0.6)

        frames[i] = frame

    return frames



# Add other drawing-related utility functions here
