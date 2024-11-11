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
        os.makedirs(path, exist_ok=True)

def get_model_base_path():
    """
    獲取模型的基礎路徑。

    Returns:
        str: 模型的基礎路徑
    """
    # 檢查是否在容器環境中
    if os.getenv('IS_DOCKER', 'False') == 'True':
        # 容器內的路徑
        return '/app/djangoFlex/models'
    else:
        # 本地開發環境的路徑
        return os.path.join(settings.BASE_DIR.parent, 'models')

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
        base_path = get_model_base_path()
        model_download_path = os.path.join(base_path, model_name, model_version)
        model_file_path = os.path.join(model_download_path, 'model', 'best.pt')

        if not os.path.exists(model_file_path):
            print(f"模型文件不存在，嘗試從 MLflow 下載: {model_file_path}")
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            client = mlflow.tracking.MlflowClient()
            model_version_details = client.get_model_version(name=model_name, version=model_version)

            run_id = model_version_details.run_id
            mlflow_model_path = os.path.basename(model_version_details.source)

            model_dir = os.path.join(model_download_path, 'model')
            os.makedirs(model_dir, exist_ok=True)
            client.download_artifacts(run_id, mlflow_model_path, dst_path=model_dir)
            print(f"模型下載完成: {model_file_path}")
        else:
            print(f"模型文件已存在: {model_file_path}")

        return model_file_path
    except Exception as e:
        print(f"下載模型時發生錯誤: {str(e)}")
        raise Exception(f"Error downloading model: {str(e)}")

# Add other file-related utility functions here
