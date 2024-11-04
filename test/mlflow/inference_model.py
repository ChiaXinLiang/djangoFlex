from pathlib import Path
import time
import cv2
from ultralytics.utils.files import increment_path
from ultralytics import YOLO

def crop_center_image(image, crop_height):
    # 讀取圖像
    height, width, _  = image.shape

    # 計算裁剪區域
    top = (height - crop_height) // 2
    bottom = top + crop_height

    left = 0
    right = width

    # 裁剪圖像
    cropped_image = image[top:bottom, left:right]

    return cropped_image

def run(person_weights="yolov8n.pt", source="test.mp4", save_img=False, exist_ok=False):
    """
    Run object detection on a video using YOLOv8 and SAHI.

    Args:
        weights (str): Model weights path.
        source (str): Video file path.
        view_img (bool): Show results.
        save_img (bool): Save results.
        exist_ok (bool): Overwrite existing files.
    """

    # Check source path
    if not Path(source).exists():
        raise FileNotFoundError(f"Source path '{source}' does not exist.")

    detection_model = YOLO(person_weights)

    # Video setup
    videocapture = cv2.VideoCapture(source)
    frame_width, frame_height = int(videocapture.get(3)), int(videocapture.get(4))
    fps, fourcc = int(videocapture.get(5)), cv2.VideoWriter_fourcc(*"mp4v")

    # Output setup
    save_dir = increment_path(Path("ultralytics_results") / "exp", exist_ok)
    save_dir.mkdir(parents=True, exist_ok=True)
    video_writer = cv2.VideoWriter(str(save_dir / f"{Path(source).stem}.mp4"), fourcc, fps, (frame_width, 920))

    frame_count = 0

    while videocapture.isOpened():
        print(f"Frame: {frame_count}")

        success, frame = videocapture.read()
        if not success:
            break

        croped_frame = crop_center_image(frame, 920)

        results = detection_model(croped_frame, classes=[0], verbose=False, imgsz=1280)
        print(results[0].boxes.xyxy)
        croped_frame = results[0].plot()

        if save_img:
            if croped_frame is not None:
                video_writer.write(croped_frame)
            else:
                print("Warning: trying to write an empty frame")

        frame_count += 1

    video_writer.release()
    videocapture.release()
    cv2.destroyAllWindows()

person_weights = "models/360_1280_person_yolov8m/model/best.pt"

source="../video/outpu9.mp4"

save_img=True
exist_ok=False

start_time = time.time()

if __name__ == "__main__":
    run(person_weights, source, save_img, exist_ok)

print("--- %s seconds ---" % (time.time() - start_time))