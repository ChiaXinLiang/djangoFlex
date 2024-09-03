import subprocess
import psutil
from django.conf import settings
import mlflow

class MLflowService:
    def start_server(self):
        try:
            command = [
                "mlflow", "server",
                "--host", settings.SERVERS_CONFIG['MLFLOW_SERVER_HOST'],
                "--port", str(settings.SERVERS_CONFIG['MLFLOW_SERVER_PORT']),
                "--backend-store-uri", f"sqlite:///{settings.SERVERS_CONFIG['MLFLOW_BACKEND_STORE']}/mlflow.db",
                "--default-artifact-root", settings.SERVERS_CONFIG['MLFLOW_BACKEND_STORE']
            ]
            subprocess.Popen(command)
            return True, "MLflow server started successfully"
        except Exception as e:
            return False, f"Failed to start MLflow server: {str(e)}"

    def stop_server(self):
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'mlflow' in proc.info['name']:
                    proc.terminate()
            return True, "MLflow server stopped successfully"
        except Exception as e:
            return False, f"Failed to stop MLflow server: {str(e)}"

    def check_server_status(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if 'mlflow' in proc.info['name']:
                return True, "MLflow server is running"
        return False, "MLflow server is not running"

    def list_experiments(self):
        mlflow.set_tracking_uri(settings.SERVERS_CONFIG['MLFLOW_TRACKING_URI'])
        return mlflow.list_experiments()

    def create_experiment(self, experiment_name):
        mlflow.set_tracking_uri(settings.SERVERS_CONFIG['MLFLOW_TRACKING_URI'])
        try:
            experiment_id = mlflow.create_experiment(experiment_name)
            return True, f"Experiment '{experiment_name}' created with ID: {experiment_id}"
        except Exception as e:
            return False, f"Failed to create experiment: {str(e)}"

    def delete_experiment(self, experiment_name):
        mlflow.set_tracking_uri(settings.SERVERS_CONFIG['MLFLOW_TRACKING_URI'])
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment:
                mlflow.delete_experiment(experiment.experiment_id)
                return True, f"Experiment '{experiment_name}' deleted successfully"
            else:
                return False, f"Experiment '{experiment_name}' not found"
        except Exception as e:
            return False, f"Failed to delete experiment: {str(e)}"