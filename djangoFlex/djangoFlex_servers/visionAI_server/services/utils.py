import os
import mlflow
from pathlib import Path
import cv2
import subprocess
from ultralytics import YOLO
import numpy as np

def check_path(path):
    """
    偵測給定的 path 路徑，若沒有會自動創建新的資料夾
    """
    if not os.path.exists(path=path):
        os.mkdir(path=path)

def download_model_if_not_exists(model_name, model_version):
    try:
        model_download_path = f'models/{model_name}/{model_version}'

        if not os.path.exists(model_download_path):
            mlflow.set_tracking_uri("http://192.168.1.77:5000")
            client = mlflow.tracking.MlflowClient()
            model_version_details = client.get_model_version(name=model_name, version=model_version)

            run_id = model_version_details.run_id
            mlflow_model_path = os.path.basename(model_version_details.source)

            os.makedirs(model_download_path, exist_ok=True)
            client.download_artifacts(run_id, mlflow_model_path, dst_path=model_download_path)
    except Exception as e:
        raise

def load_detection_model(model_path):
    try:
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model path '{model_path}' does not exist.")
        return YOLO(model_path)
    except Exception as e:
        raise

def create_ffmpeg_process(output_url, fps, frame_size):
    try:
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f'{frame_size[0]}x{frame_size[1]}',
            '-r', str(fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-profile:v', 'baseline',
            '-level', '3.0',
            '-f', 'flv',
            '-max_muxing_queue_size', '1024',
            '-g', '30',
            '-keyint_min', '30',
            '-sc_threshold', '0',
            '-b:v', '2500k',
            '-maxrate', '2500k',
            '-bufsize', '5000k',
            output_url
        ]
        process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
        
        def check_process():
            return process.poll() is None
        
        return process, check_process
    except Exception as e:
        raise

def draw_bounding_boxes(frame, results, box_color, text_color, thickness, font, font_scale):
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

def add_timestamp(frame, timestamp, font, font_scale, text_color, thickness):
    cv2.putText(frame, f"Clip: {timestamp}", (10, 30), font, font_scale, text_color, thickness)
    return frame

def run(weights, source, view_img=False, save_img=False):
    if not Path(source).exists():
        raise FileNotFoundError(f"Source path '{source}' does not exist.")

    model = YOLO(weights)
    image = cv2.imread(source)
    if image is None:
        raise ValueError(f"Unable to read image from {source}")

    save_dir = "ultralytics_results"
    check_path(save_dir)

    results = model.predict(image, conf=0.5, verbose=False, imgsz=640, classes=[0])

    processed_image = draw_bounding_boxes(image, results, (0, 255, 0), (255, 255, 255), 2, cv2.FONT_HERSHEY_SIMPLEX, 0.6)

    if view_img:
        cv2.imshow(Path(source).stem, processed_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if save_img:
        output_path = os.path.join(save_dir, f"{Path(source).stem}_result.jpg")
        cv2.imwrite(output_path, processed_image)

    return processed_image

def draw_all_results(frames, first_result, last_result):
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

def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0

def calculate_distance(box1, box2):
    center1 = np.array([(box1[0] + box1[2]) / 2, (box1[1] + box1[3]) / 2])
    center2 = np.array([(box2[0] + box2[2]) / 2, (box2[1] + box2[3]) / 2])
    return np.linalg.norm(center1 - center2)

def match_detections(first_detections, last_detections):
    if not first_detections or not last_detections:
        return [], []
    
    distances = [[calculate_distance(first, last) for last in last_detections] for first in first_detections]
    matched_pairs = []
    unmatched_first = list(range(len(first_detections)))
    unmatched_last = list(range(len(last_detections)))
    
    while unmatched_first and unmatched_last:
        i, j = min(((i, j) for i in unmatched_first for j in unmatched_last), key=lambda x: distances[x[0]][x[1]])
        matched_pairs.append((i, j))
        unmatched_first.remove(i)
        unmatched_last.remove(j)
    
    return matched_pairs, unmatched_last

def interpolate_detections(first_detections, last_detections, interval):
    matched_pairs, unmatched_last = match_detections(first_detections, last_detections)
    
    interpolated = [[] for _ in range(interval)]
    
    for i, j in matched_pairs:
        first = first_detections[i]
        last = last_detections[j]
        for k in range(interval):
            weight = (k + 1) / (interval + 1)
            x1 = int(first[0] * (1 - weight) + last[0] * weight)
            y1 = int(first[1] * (1 - weight) + last[1] * weight)
            x2 = int(first[2] * (1 - weight) + last[2] * weight)
            y2 = int(first[3] * (1 - weight) + last[3] * weight)
            interpolated[k].append((x1, y1, x2, y2))
    
    for j in unmatched_last:
        for k in range(interval):
            interpolated[k].append(last_detections[j])
    
    return interpolated

def fps_controller(frames, duration, fps):
    target_frame_count = int(duration * fps)
    current_frame_count = len(frames)
    
    if current_frame_count == target_frame_count:
        return frames
    elif current_frame_count > target_frame_count:
        # Reduce frames
        step = current_frame_count / target_frame_count
        return [frames[int(i * step)] for i in range(target_frame_count)]
    elif current_frame_count < target_frame_count:
        # Duplicate frames
        duplicated_frames = []
        for i in range(target_frame_count):
            index = min(int(i * current_frame_count / target_frame_count), current_frame_count - 1)
            duplicated_frames.append(frames[index])
        return duplicated_frames
    else:
        return frames  # This case should never happen, but included for completeness

def fps_controller_sleep_time(frames, duration, fps):
    target_frame_count = int(duration * fps)
    current_frame_count = len(frames)
    print(f"current_frame_count: {current_frame_count}", f"target_frame_count: {target_frame_count}")
    if current_frame_count == target_frame_count:
        return 0  # No sleep needed
    elif current_frame_count > target_frame_count:
        # Calculate sleep time to slow down frame rate
        total_sleep_time = duration - (current_frame_count / fps)
        return max(0, total_sleep_time / current_frame_count)
    elif current_frame_count < target_frame_count:
        # Calculate negative sleep time (indicating frames need to be duplicated)
        return (target_frame_count - current_frame_count) / fps / current_frame_count
    else:
        return 0  # This case should never happen, but included for completeness

def fps_controller_adjustment(frames, duration, fps):
    target_frame_count = int(2 * fps)
    current_frame_count = len(frames)
    print(f"current_frame_count: {current_frame_count}", f"target_frame_count: {target_frame_count}")
    
    if current_frame_count == target_frame_count:
        return frames  # No adjustment needed
    
    adjustment_factor = target_frame_count / current_frame_count
    
    if adjustment_factor > 1:
        # Duplicate frames
        new_frames = []
        for i in range(target_frame_count):
            index = int(i / adjustment_factor)
            new_frames.append(frames[index])
        frames = new_frames
    elif adjustment_factor < 1:
        # Remove frames
        step = 1 / adjustment_factor
        frames = [frames[int(i * step)] for i in range(target_frame_count)]
    
    return frames