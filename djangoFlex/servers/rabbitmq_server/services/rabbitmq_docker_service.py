import subprocess
import time
from django.conf import settings
from .rabbitmq_service import RabbitMQService
from servers.BaseService.BaseDockerService import BaseDockerService

class RabbitMQDockerService(BaseDockerService):
    def __init__(self):
        super().__init__()
        self.container_name = settings.SERVERS_CONFIG['RABBITMQ_DOCKER_CONTAINER_NAME']
        self.image_name = settings.SERVERS_CONFIG['RABBITMQ_DOCKER_IMAGE']

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
                    print(f"Starting existing RabbitMQ container: {self.container_name}")
                else:
                    print(f"RabbitMQ container {self.container_name} is already running")
                return True, f"Starting existing RabbitMQ container: {self.container_name}"
            else:
                # Container doesn't exist, create a new one
                subprocess.run([
                    'docker', 'run', '-d', '--name', self.container_name,
                    '-p', f"{settings.SERVERS_CONFIG['RABBITMQ_PORT']}:5672",
                    '-p', f"{settings.SERVERS_CONFIG['RABBITMQ_DASHBOARD_PORT']}:15672",
                    '-e', f"RABBITMQ_DEFAULT_USER={settings.SERVERS_CONFIG['RABBITMQ_USER']}",
                    '-e', f"RABBITMQ_DEFAULT_PASS={settings.SERVERS_CONFIG['RABBITMQ_PASSWORD']}",
                    '-e', f"RABBITMQ_DEFAULT_VHOST={settings.SERVERS_CONFIG['RABBITMQ_VHOST']}",
                    self.image_name
                ], check=True)
                print(f"Created and started new RabbitMQ container: {self.container_name}")
                return True, f"Created and started new RabbitMQ container: {self.container_name}"

        except subprocess.CalledProcessError as e:
            print(f"Error starting RabbitMQ Docker container: {e}")
            return False, f"Error starting RabbitMQ Docker container: {e}"
        except Exception as e:
            print(f"Unexpected error starting RabbitMQ Docker container: {e}")
            return False, f"Unexpected error starting RabbitMQ Docker container: {e}"

    def stop_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"
        
        try:
            status, message = self.get_container_status()
            if status == 'running':
                subprocess.run(['docker', 'stop', self.container_name], check=True)
                subprocess.run(['docker', 'rm', self.container_name], check=True)
                return True, f"Docker RabbitMQ server '{self.container_name}' stopped and removed"
            elif status == 'exited':
                subprocess.run(['docker', 'rm', self.container_name], check=True)
                return True, f"Docker RabbitMQ server '{self.container_name}' was already stopped, container removed"
            elif status is None:
                return False, message
            else:
                return False, f"Docker RabbitMQ server '{self.container_name}' is in an unexpected state: {status}"
        except subprocess.CalledProcessError as e:
            return False, f"Error stopping Docker RabbitMQ server: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error stopping Docker RabbitMQ server: {str(e)}"

    def check_server_status(self):
        return super().check_server_status()