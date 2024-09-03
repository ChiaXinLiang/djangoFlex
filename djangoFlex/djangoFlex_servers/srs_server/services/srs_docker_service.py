import subprocess
import time
from django.conf import settings
from djangoFlex_servers.BaseService.BaseDockerService import BaseDockerService
from ..models import SRSServerConfig

class SRSDockerService(BaseDockerService):
    def __init__(self):
        super().__init__()
        self.config = self.get_config()

    def get_config(self):
        config, created = SRSServerConfig.objects.get_or_create(pk=1)
        return config

    def start_server(self):
        # Use self.config to access configuration parameters
        command = [
            "docker", "run", "--rm", "-d",
            "--name", self.config.container_name,
            "-p", f"{self.config.rtmp_port}:1935",
            "-p", f"{self.config.http_api_port}:1985",
            "-p", f"{self.config.http_server_port}:8080",
            self.config.docker_image,
            "./objs/srs",
            "-c", self.config.config_file
        ]
        if not self.check_docker_availability():
            return False, "Docker is not available"
        
        try:
            # Check if the container already exists
            container_exists = subprocess.run(['docker', 'ps', '-a', '-q', '-f', f'name={self.config.container_name}'], capture_output=True, text=True)
            
            if container_exists.stdout.strip():
                # Container exists, start it if it's not running
                status, message = self.get_container_status()
                if status != 'running':
                    subprocess.run(['docker', 'start', self.config.container_name], check=True)
                    print(f"Starting existing SRS container: {self.config.container_name}")
                else:
                    print(f"SRS container {self.config.container_name} is already running")
                return True, f"Starting existing SRS container: {self.config.container_name}"
            else:
                # Container doesn't exist, create a new one
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
                print(f"Created and started new SRS container: {self.config.container_name}")
                return True, f"Created and started new SRS container: {self.config.container_name}"

        except subprocess.CalledProcessError as e:
            error_message = f"Error starting SRS Docker container: {e}\nCommand: {e.cmd}\nOutput: {e.stdout}\nError: {e.stderr}"
            print(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Unexpected error starting SRS Docker container: {str(e)}"
            print(error_message)
            return False, error_message

    def stop_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"
        
        if self.config.container_name is None:
            return False, "Container name is not set in the configuration"
        
        try:
            status, message = self.get_container_status()
            if status == 'running':
                subprocess.run(['docker', 'stop', self.config.container_name], check=True)
                subprocess.run(['docker', 'rm', self.config.container_name], check=True)
                return True, f"Docker SRS server '{self.config.container_name}' stopped and removed"
            elif status == 'exited':
                subprocess.run(['docker', 'rm', self.config.container_name], check=True)
                return True, f"Docker SRS server '{self.config.container_name}' was already stopped, container removed"
            elif status is None:
                return False, message
            else:
                return False, f"Docker SRS server '{self.config.container_name}' is in an unexpected state: {status}"
        except subprocess.CalledProcessError as e:
            return False, f"Error stopping Docker SRS server: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error stopping Docker SRS server: {str(e)}"

    def check_server_status(self):
        return super().check_server_status()