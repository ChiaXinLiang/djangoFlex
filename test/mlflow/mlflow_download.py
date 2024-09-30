import mlflow
import os

mlflow.set_tracking_uri("http://192.168.1.77:5000")

model_name = "360_1280_person_yolov8m"
model_version = "1"

model_download_path = f'models/{model_name}'

# Load a specific model version
client = mlflow.tracking.MlflowClient()
model_version_details = client.get_model_version(name=model_name, version=model_version)

run_id = model_version_details.run_id
# artifact_path = model_version_details.source
mlflow_model_path = os.path.basename(model_version_details.source)

os.makedirs(model_download_path, exist_ok=True)
# Download the model artifacts
client.download_artifacts(run_id, mlflow_model_path, dst_path=model_download_path)