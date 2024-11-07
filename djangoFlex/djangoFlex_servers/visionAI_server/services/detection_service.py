from ..utils.detection_utils import load_detection_model
from ..utils.file_utils import download_model_if_not_exists, get_model_base_path
import os

class DetectionService:
    def __init__(self):
        model_name = "360_1280_person_yolov8m"
        model_version = "1"

        try:
            # 確保模型文件存在並獲取完整路徑
            model_path = download_model_if_not_exists(model_name, model_version)
            print(f"使用模型路徑: {model_path}")

            # 載入模型
            self.detection_model = load_detection_model(model_path)
        except Exception as e:
            print(f"初始化 DetectionService 時發生錯誤: {str(e)}")
            raise

    def detect_objects(self, frame):
        return self.detection_model(frame, classes=[0], verbose=False, imgsz=1280)
