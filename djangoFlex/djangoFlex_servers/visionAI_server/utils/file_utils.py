import os
from django.conf import settings
import mlflow

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

# Add other file-related utility functions here
