from ..utils.detection_utils import load_detection_model

class DetectionService:
    def __init__(self):
        self.detection_model = load_detection_model("models/360_1280_person_yolov8m/1/model/best.pt")

    def detect_objects(self, frame):
        return self.detection_model(frame, classes=[0], verbose=False, imgsz=1280)
