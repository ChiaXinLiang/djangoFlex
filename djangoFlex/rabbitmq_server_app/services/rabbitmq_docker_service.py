import subprocess
import time
from django.conf import settings
from .rabbitmq_service import RabbitMQService

class RabbitMQDockerService(RabbitMQService):
    def __init__(self):
        super().__init__()
        self.container_name = settings.RABBITMQ_DOCKER_CONTAINER_NAME
        self.image_name = settings.RABBITMQ_DOCKER_IMAGE

    def check_docker_availability(self):
        try:
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                print(f"Docker is not available. Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error checking Docker availability: {e}")
            return False

    def check_rabbitmq_availability(self):
        if self.check_docker_availability():
            container_status = self.get_container_status()
            if container_status == 'running':
                print(f"RabbitMQ container '{self.container_name}' is running. Status: {container_status}")
                return True
            else:
                print(f"RabbitMQ container '{self.container_name}' is not running. Status: {container_status}")
                return False
        else:
            return False

    def get_container_status(self):
        result = subprocess.run(['docker', 'inspect', '-f', '{{.State.Status}}', self.container_name], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def start_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"
        
        try:
            # Check if the container already exists
            container_exists = subprocess.run(['docker', 'ps', '-a', '-q', '-f', f'name={self.container_name}'], capture_output=True, text=True)
            
            if container_exists.stdout.strip():
                # Container exists, start it if it's not running
                container_status = self.get_container_status()
                if container_status != 'running':
                    subprocess.run(['docker', 'start', self.container_name], check=True)
                    print(f"Starting existing RabbitMQ container: {self.container_name}")
                else:
                    print(f"RabbitMQ container {self.container_name} is already running")
                return True, f"Starting existing RabbitMQ container: {self.container_name}"
            else:
                # Container doesn't exist, create a new one
                subprocess.run([
                    'docker', 'run', '-d', '--name', self.container_name,
                    '-p', f"{settings.RABBITMQ_PORT}:5672",
                    '-p', '15672:15672',
                    '-e', f"RABBITMQ_DEFAULT_USER={settings.RABBITMQ_USER}",
                    '-e', f"RABBITMQ_DEFAULT_PASS={settings.RABBITMQ_PASSWORD}",
                    '-e', f"RABBITMQ_DEFAULT_VHOST={settings.RABBITMQ_VHOST}",
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
            container_status = self.get_container_status()
            if container_status == 'running':
                subprocess.run(['docker', 'stop', self.container_name], check=True)
                subprocess.run(['docker', 'rm', self.container_name], check=True)
                return True, f"Docker RabbitMQ server '{self.container_name}' stopped and removed"
            elif container_status == 'exited':
                subprocess.run(['docker', 'rm', self.container_name], check=True)
                return True, f"Docker RabbitMQ server '{self.container_name}' was already stopped, container removed"
            elif container_status is None:
                return False, f"Docker RabbitMQ server '{self.container_name}' not found"
            else:
                return False, f"Docker RabbitMQ server '{self.container_name}' is in an unexpected state: {container_status}"
        except subprocess.CalledProcessError as e:
            return False, f"Error stopping Docker RabbitMQ server: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error stopping Docker RabbitMQ server: {str(e)}"

    def check_server_status(self):
        if not self.check_rabbitmq_availability():
            return False, "Docker or RabbitMQ container is not available"
        
        try:
            status = self.get_container_status()
            
            if status == 'running':
                return True, "Docker RabbitMQ server is running"
            elif status == 'exited':
                return False, "Docker RabbitMQ server has exited"
            elif status == 'paused':
                return False, "Docker RabbitMQ server is paused"
            elif status is None:
                return False, "Docker RabbitMQ container not found"
            else:
                return False, f"Docker RabbitMQ server status: {status}"
        except Exception as e:
            return False, f"Error checking Docker RabbitMQ server status: {str(e)}"

    # Implement other methods (create_queue, delete_queue, list_queues) similarly