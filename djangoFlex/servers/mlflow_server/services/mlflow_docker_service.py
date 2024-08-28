from django.conf import settings
import mlflow
from servers.BaseService.BaseDockerService import BaseDockerService
import subprocess
import os

class MLflowDockerService(BaseDockerService):
    def __init__(self):
        super().__init__()
        self.container_name = settings.SERVERS_CONFIG['MLFLOW_DOCKER_CONTAINER_NAME']
        self.image_name = settings.SERVERS_CONFIG['MLFLOW_DOCKER_IMAGE']

    def start_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"
        
        try:
            # Check if the container already exists
            container_exists = subprocess.run(['docker', 'ps', '-a', '-q', '-f', f'name={self.container_name}'], capture_output=True, text=True)
            
            if container_exists.stdout.strip():
                # Container exists, start it if it's not running
                status, message = self.get_container_status()
                if status != 'running':
                    subprocess.run(['docker', 'start', self.container_name], check=True)
                    print(f"Starting existing MLflow container: {self.container_name}")
                else:
                    print(f"MLflow container {self.container_name} is already running")
                return True, f"Starting existing MLflow container: {self.container_name}"
            else:
                # Container doesn't exist, create a new one
                command = [
                    "docker", "run",
                    "-d",
                    "--name", self.container_name,
                    "-h", settings.SERVERS_CONFIG['MLFLOW_SERVER_HOST'],
                    "-p", f"{settings.SERVERS_CONFIG['MLFLOW_SERVER_PORT']}:{settings.SERVERS_CONFIG['MLFLOW_SERVER_PORT']}",
                    "-v", f"{settings.SERVERS_CONFIG['MLFLOW_BACKEND_STORE']}:/mlflow/mlruns",
                    "-w", "/mlflow",
                    self.image_name,
                    "mlflow", "server",
                    "--backend-store-uri", "mlruns",
                    "--host", "0.0.0.0",
                    "--port", str(settings.SERVERS_CONFIG['MLFLOW_SERVER_PORT'])
                ]
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
                print(f"Created and started new MLflow container: {self.container_name}")
                return True, f"Created and started new MLflow container: {self.container_name}"

        except subprocess.CalledProcessError as e:
            error_message = f"Error starting MLflow Docker container: {e}\nCommand: {e.cmd}\nOutput: {e.stdout}\nError: {e.stderr}"
            print(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Unexpected error starting MLflow Docker container: {str(e)}"
            print(error_message)
            return False, error_message

    def stop_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"

        try:
            subprocess.run(["docker", "stop", self.container_name], check=True, capture_output=True, text=True)
            subprocess.run(["docker", "rm", self.container_name], check=True, capture_output=True, text=True)
            return True, "MLflow Docker server stopped successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to stop MLflow Docker server: {e.stderr}"

    def check_server_status(self):
        return super().check_server_status()

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