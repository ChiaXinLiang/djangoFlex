import os
import logging
import mlflow
from pathlib import Path
import cv2
import subprocess
from ultralytics import YOLO
import numpy as np

logger = logging.getLogger(__name__)

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
            logger.info(f"Model not found. Downloading model {model_name} version {model_version}")
            mlflow.set_tracking_uri("http://192.168.1.77:5000")
            client = mlflow.tracking.MlflowClient()
            model_version_details = client.get_model_version(name=model_name, version=model_version)

            run_id = model_version_details.run_id
            mlflow_model_path = os.path.basename(model_version_details.source)

            os.makedirs(model_download_path, exist_ok=True)
            client.download_artifacts(run_id, mlflow_model_path, dst_path=model_download_path)
            logger.info(f"Model downloaded successfully to {model_download_path}")
        else:
            logger.info(f"Model already exists at {model_download_path}")
    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        raise

def load_detection_model(model_path):
    try:
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model path '{model_path}' does not exist.")
        return YOLO(model_path)
    except Exception as e:
        logger.error(f"Error loading detection model: {str(e)}")
        raise

def create_ffmpeg_process(output_url, fps, frame_size):
    try:
        ffmpeg_command = [
            'ffmpeg',
            '-re',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f'{frame_size[0]}x{frame_size[1]}',
            '-r', str(fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',
            '-r', str(fps),
            '-f', 'flv',
            output_url
        ]
        process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
        
        def check_process():
            return process.poll() is None
        
        return process, check_process
    except Exception as e:
        logger.error(f"Error creating ffmpeg process: {str(e)}")
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
        logger.info(f"Result saved to {output_path}")

    return processed_image

def draw_all_results(frames, first_result, last_result):
    logger.info("Starting draw_all_results function")
    if not frames or not first_result or not last_result:
        logger.warning("Empty input: frames, first_result, or last_result is missing")
        return frames

    num_frames = len(frames)
    logger.info(f"Number of frames: {num_frames}")
    
    # Extract detections from first and last results
    first_detections = [(int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])) 
                        for r in first_result for box in r.boxes]
    last_detections = [(int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])) 
                       for r in last_result for box in r.boxes]

    logger.info(f"Number of detections in first frame: {len(first_detections)}")
    logger.info(f"Number of detections in last frame: {len(last_detections)}")

    interpolated_detections = interpolate_detections(last_detections, first_detections, num_frames - 2)

    for i, frame in enumerate(frames):
        logger.debug(f"Processing frame {i+1}/{num_frames}")
        if frame is None or frame.size == 0:
            logger.error(f"Error decoding frame {i+1}: Empty or invalid frame")
            continue

        detections = first_detections if i == 0 else (last_detections if i == num_frames - 1 else interpolated_detections[i-1])
        
        # Draw bounding boxes using draw_bounding_boxes function
        dummy_results = [type('DummyResult', (), {'boxes': type('DummyBoxes', (), {'xyxy': np.array([[x1, y1, x2, y2]]), 'cls': np.array([0])})()})() for x1, y1, x2, y2 in detections]
        frame = draw_bounding_boxes(frame, dummy_results, (0, 255, 0), (255, 255, 255), 2, cv2.FONT_HERSHEY_SIMPLEX, 0.6)
        logger.debug(f"Drew {len(detections)} boxes on frame {i+1}")

        frames[i] = frame
    
    logger.info("Finished processing all frames")
    return frames

def calculate_iou(box1, box2):
    # Calculate the Intersection over Union (IoU) of two bounding boxes
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

def match_detections(last_detections, current_detections):
    if not last_detections or not current_detections:
        return [], []
    
    distances = [[calculate_distance(last, current) for current in current_detections] for last in last_detections]
    matched_pairs = []
    unmatched_last = list(range(len(last_detections)))
    unmatched_current = list(range(len(current_detections)))
    
    while unmatched_last and unmatched_current:
        i, j = min(((i, j) for i in unmatched_last for j in unmatched_current), key=lambda x: distances[x[0]][x[1]])
        matched_pairs.append((i, j))
        unmatched_last.remove(i)
        unmatched_current.remove(j)
    
    return matched_pairs, unmatched_current

def interpolate_detections(last_detections, current_detections, interval):
    matched_pairs, unmatched_current = match_detections(last_detections, current_detections)
    
    interpolated = [[] for _ in range(interval)]
    
    for i, j in matched_pairs:
        last = last_detections[i]
        current = current_detections[j]
        for k in range(interval):
            # 使用加權平均進行平滑插值
            weight = (k + 1) / (interval + 1)  # 權重從 1/(interval+1) 到 interval/(interval+1)
            x1 = int(last[0] * (1 - weight) + current[0] * weight)
            y1 = int(last[1] * (1 - weight) + current[1] * weight)
            x2 = int(last[2] * (1 - weight) + current[2] * weight)
            y2 = int(last[3] * (1 - weight) + current[3] * weight)
            interpolated[k].append((x1, y1, x2, y2))
    
    # 處理新出現的物體
    for j in unmatched_current:
        for k in range(interval):
            interpolated[k].append(current_detections[j])
    
    return interpolated
