import mlflow
import os

EXPERIMENT_NAME = "<模型名稱+版本>"
RUN_NAME = 'exp1' #  隨意指定
MODEL_NAME = '<模型名稱>'
TRAINED_MODEL_PATH = '<模型路徑>.pt'
ARTIFACT_MODEL_PATH = None # 可隨意指定資料夾路徑如 'model'。None 代表保存在最上層目錄
MLRUNS_PATH = 'http://localhost:5000'

mlflow.set_tracking_uri(MLRUNS_PATH )
os.environ['MLFLOW_TRACKING_URI'] = MLRUNS_PATH

# 獲取 experiment_id
try:
    experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
except:
    experiment_id = mlflow.get_experiment_by_name(EXPERIMENT_NAME).experiment_id

# 打開指定 <run_id> 的 MLflow run
with mlflow.start_run(experiment_id=experiment_id, run_name=RUN_NAME) as run:

    # 取得 run_id
    run_id = run.info.run_id

    # 將模型登記在 artifact 中
    mlflow.log_artifact(TRAINED_MODEL_PATH, ARTIFACT_MODEL_PATH)

    # 注冊模型
    mlflow.register_model(  model_uri = f"runs:/{run_id}/model",
                            name = MODEL_NAME, # 當模型名稱重複，版本會往上叠加
                            )

    mlflow.end_run()