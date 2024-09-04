from django.conf import settings
import redis
from djangoFlex_servers.BaseService.BaseDockerService import BaseDockerService
import subprocess
import os

class RedisDockerService(BaseDockerService):
    def __init__(self):
        super().__init__()
        self.load_config()

    def load_config(self):
        config = settings.SERVERS_CONFIG
        self.container_name = config['REDIS_DOCKER_CONTAINER_NAME']
        self.image_name = config['REDIS_DOCKER_IMAGE']
        self.host = config['REDIS_SERVER_HOST']
        self.port = config['REDIS_SERVER_PORT']
        self.data_dir = config['REDIS_DATA_DIR']

    def start_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"
        
        try:
            container_exists = subprocess.run(['docker', 'ps', '-a', '-q', '-f', f'name={self.container_name}'], capture_output=True, text=True)
            
            if container_exists.stdout.strip():
                status, message = self.get_container_status()
                if status != 'running':
                    subprocess.run(['docker', 'start', self.container_name], check=True)
                    print(f"Starting existing Redis container: {self.container_name}")
                else:
                    print(f"Redis container {self.container_name} is already running")
                return True, f"Starting existing Redis container: {self.container_name}"
            else:
                command = [
                    "docker", "run",
                    "-d",
                    "--name", self.container_name,
                    "-h", self.host,
                    "-p", f"{self.port}:6379",
                    "-v", f"{self.data_dir}:/data",
                    self.image_name
                ]
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
                print(f"Created and started new Redis container: {self.container_name}")
                return True, f"Created and started new Redis container: {self.container_name}"

        except subprocess.CalledProcessError as e:
            error_message = f"Error starting Redis Docker container: {e}\nCommand: {e.cmd}\nOutput: {e.stdout}\nError: {e.stderr}"
            print(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Unexpected error starting Redis Docker container: {str(e)}"
            print(error_message)
            return False, error_message

    def stop_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"

        try:
            subprocess.run(["docker", "stop", self.container_name], check=True, capture_output=True, text=True)
            subprocess.run(["docker", "rm", self.container_name], check=True, capture_output=True, text=True)
            return True, "Redis Docker server stopped successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to stop Redis Docker server: {e.stderr}"

    def check_server_status(self):
        return super().check_server_status()

    def list_keys(self):
        try:
            client = redis.Redis(host=self.host, port=self.port, db=0)
            keys = client.keys()
            return True, keys
        except Exception as e:
            return False, f"Failed to list keys: {str(e)}"

    def set_key(self, key, value):
        try:
            client = redis.Redis(host=self.host, port=self.port, db=0)
            client.set(key, value)
            return True, f"Key '{key}' set successfully"
        except Exception as e:
            return False, f"Failed to set key: {str(e)}"

    def delete_key(self, key):
        try:
            client = redis.Redis(host=self.host, port=self.port, db=0)
            client.delete(key)
            return True, f"Key '{key}' deleted successfully"
        except Exception as e:
            return False, f"Failed to delete key: {str(e)}"