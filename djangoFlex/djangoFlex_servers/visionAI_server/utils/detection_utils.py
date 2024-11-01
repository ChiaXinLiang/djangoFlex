from pathlib import Path
from ultralytics import YOLO

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