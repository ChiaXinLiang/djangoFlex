import os
import mlflow
from pathlib import Path
import cv2
import subprocess
from ultralytics import YOLO
import numpy as np
from django.conf import settings
import time
import random
from functools import wraps

def check_path(path):
    """
    檢查給定的路徑是否存在，如果不存在則創建新的資料夾。

    Args:
        path (str): 要檢查的路徑。

    Returns:
        None
    """
    if not os.path.exists(path=path):
        os.mkdir(path=path)

def download_model_if_not_exists(model_name, model_version):
    """
    如果指定的模型不存在，則從 MLflow 下載模型。

    Args:
        model_name (str): 模型名稱。
        model_version (str): 模型版本。

    Raises:
        Exception: 如果下載過程中發生錯誤。
    """
    try:
        model_download_path = f'models/{model_name}/{model_version}'

        if not os.path.exists(model_download_path):
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            client = mlflow.tracking.MlflowClient()
            model_version_details = client.get_model_version(name=model_name, version=model_version)

            run_id = model_version_details.run_id
            mlflow_model_path = os.path.basename(model_version_details.source)

            os.makedirs(model_download_path, exist_ok=True)
            client.download_artifacts(run_id, mlflow_model_path, dst_path=model_download_path)
    except Exception as e:
        raise

def load_detection_model(model_path):
    """
    加載指定路徑的 YOLO 模型。

    Args:
        model_path (str): 模型文件的路徑。

    Returns:
        YOLO: 加載的 YOLO 模型。

    Raises:
        FileNotFoundError: 如果模型文件不存在。
        Exception: 如果加載過程中發生其他錯誤。
    """
    try:
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model path '{model_path}' does not exist.")
        return YOLO(model_path)
    except Exception as e:
        raise

def create_ffmpeg_process(output_url, fps, frame_size):
    """
    創建 FFmpeg 進程用於視頻流處理。

    Args:
        output_url (str): 輸出視頻流的 URL。
        fps (int): 幀率。
        frame_size (tuple): 幀大小，格式為 (width, height)。

    Returns:
        tuple: 包含 FFmpeg 進程對象和檢查進程狀態的函數。

    Raises:
        Exception: 如果創建進程時發生錯誤。
    """
    print(f"output_url: {output_url}")
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
            '-err_detect', 'ignore_err',
            output_url
        ]
        # ffmpeg_command = [
        #     'ffmpeg',
        #     '-f', 'rawvideo',
        #     '-vcodec', 'rawvideo',
        #     '-pix_fmt', 'bgr24',
        #     '-s', f'{frame_size[0]}x{frame_size[1]}',
        #     '-r', str(fps),
        #     '-i', '-',
        #     '-c:v', 'libx264',
        #     '-pix_fmt', 'yuv420p',
        #     '-preset', 'superfast',  # 改為 veryfast，在速度和質量間取得平衡
        #     '-tune', 'zerolatency',
        #     '-profile:v', 'baseline',
        #     '-level', '3.1',  # 提高到 3.1，支持更高的比特率
        #     '-f', 'flv',
        #     '-max_muxing_queue_size', '1024',
        #     '-g', str(fps*2),  # 將 GOP 設置為幀率的 2 倍
        #     '-keyint_min', str(fps),  # 最小關鍵幀間隔設為幀率
        #     '-sc_threshold', '0',
        #     '-b:v', '3000k',  # 略微提高比特率以改善質量
        #     '-maxrate', '3000k',
        #     '-bufsize', '6000k',
        #     '-x264-params', 'nal-hrd=cbr',  # 強制 CBR 模式
        #     '-threads', '4',  # 使用多線程編碼
        #     output_url
        # ]
        process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

        def check_process():
            return process.poll() is None

        return process, check_process
    except Exception as e:
        raise

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

def add_timestamp(frame, timestamp, font, font_scale, text_color, thickness):
    """
    在幀上添加時間戳。

    Args:
        frame (numpy.ndarray): 要添加時間戳的幀。
        timestamp (str): 時間戳字符串。
        font: 字體。
        font_scale (float): 字體大小。
        text_color (tuple): 文字顏色。
        thickness (int): 文字粗細。

    Returns:
        numpy.ndarray: 添加了時間戳的幀。
    """
    cv2.putText(frame, f"Clip: {timestamp}", (10, 30), font, font_scale, text_color, thickness)
    return frame

def run(weights, source, view_img=False, save_img=False):
    """
    運行 YOLO 模型進行物體檢測。

    Args:
        weights (str): 模型權重文件路徑。
        source (str): 輸入圖像路徑。
        view_img (bool): 是否顯示處理後的圖像。
        save_img (bool): 是否保存處理後的圖像。

    Returns:
        numpy.ndarray: 處理後的圖像。

    Raises:
        FileNotFoundError: 如果源圖像文件不存在。
        ValueError: 如果無法讀取源圖像。
    """
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

def calculate_iou(box1, box2):
    """
    計算兩個邊界框的交並比（IoU）。

    Args:
        box1 (tuple): 第一個邊界框的坐標 (x1, y1, x2, y2)。
        box2 (tuple): 第二個邊界框的坐標 (x1, y1, x2, y2)。

    Returns:
        float: 兩個邊界框的 IoU 值。
    """
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
    """
    計算兩個邊界框中心點之間的歐氏距離。

    Args:
        box1 (tuple): 第一個邊界框的坐標 (x1, y1, x2, y2)。
        box2 (tuple): 第二個邊界框的坐標 (x1, y1, x2, y2)。

    Returns:
        float: 兩個邊界框中心點之間的距離。
    """
    center1 = np.array([(box1[0] + box1[2]) / 2, (box1[1] + box1[3]) / 2])
    center2 = np.array([(box2[0] + box2[2]) / 2, (box2[1] + box2[3]) / 2])
    return np.linalg.norm(center1 - center2)

def match_detections(first_detections, last_detections):
    """
    匹配第一幀和最後一幀的檢測結果。

    Args:
        first_detections (list): 第一幀的檢測結果。
        last_detections (list): 最後一幀的檢測結果。

    Returns:
        tuple: 包含匹配對和未匹配的最後檢測結果的列表。
    """
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
    """
    在第一幀和最後一幀的檢測結果之間進行插值。

    Args:
        first_detections (list): 第一幀的檢測結果。
        last_detections (list): 最後一幀的檢測結果。
        interval (int): 插值的間隔數。

    Returns:
        list: 插值後的檢測結果列表。
    """
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
    """
    控制幀數以匹配目標 FPS。

    Args:
        frames (list): 原始幀列表。
        duration (float): 視頻持續時間（秒）。
        fps (int): 目標幀率。

    Returns:
        list: 調整後的幀列表。
    """
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
    """
    計算每幀之間需要的睡眠時間以達到目標 FPS。

    Args:
        frames (list): 幀列表。
        duration (float): 視頻持續時間（秒）。
        fps (int): 目標幀率。

    Returns:
        float: 每幀之間的睡眠時間（秒）。
    """
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
    """
    調整幀數以匹配目標 FPS，主要用於 2 秒的視頻片段。

    Args:
        frames (list): 原始幀列表。
        duration (float): 視頻持續時間（秒）。
        fps (int): 目標幀率。

    Returns:
        list: 調整後的幀列表。
    """
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

def retry_with_backoff(retries=5, backoff_in_seconds=1):
    """
    裝飾器：使用指數退避策略重試失敗的函數。

    Args:
        retries (int): 最大重試次數。
        backoff_in_seconds (int): 初始退避時間（秒）。

    Returns:
        function: 裝飾器函數。
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise
                    sleep = backoff_in_seconds * 2 ** x + random.uniform(0, 1)
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator
