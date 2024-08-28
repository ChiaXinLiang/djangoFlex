import subprocess
import time
from django.conf import settings
from .BaseService import BaseService

class BaseDockerService(BaseService):
    def __init__(self):
        super().__init__()
        self.container_name = None
        self.image_name = None

    def check_server_status(self):
        status, message = self.check_container_status()
        possible_statuses = {
            'new': 'The initial state of a container.',
            'allocated': 'Resources have been allocated for the container.',
            'pending': 'The container is waiting for resources to become available.',
            'assigned': 'The container has been assigned to a node.',
            'accepted': 'The container has been accepted by a node.',
            'preparing': 'The container is being prepared to run.',
            'ready': 'The container is ready to start.',
            'starting': 'The container is starting.',
            'running': 'The container is currently running.',
            'complete': 'The container has completed its task.',
            'shutdown': 'The container is shutting down.',
            'failed': 'The container has failed.',
            'rejected': 'The container was rejected by a node.',
            'remove': 'The container is being removed.',
            'orphaned': 'The container has been orphaned.'
        }
        if status is not None:
            if status in possible_statuses:
                return status == 'running', f"Container {self.container_name} status: {status} - {possible_statuses[status]}"
            else:
                return False, f"Container {self.container_name} has an unknown status: {status}"
        else:
            return False, message
        
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

    def get_container_status(self):
        try:
            result = subprocess.run(['docker', 'inspect', '-f', '{{.State.Status}}', self.container_name], capture_output=True, text=True)
            if result.returncode == 0:
                status = result.stdout.strip()
                return status, f"Container {self.container_name} is {status}."
            else:
                return None, f"Error retrieving status for container {self.container_name}: {result.stderr}"
        except Exception as e:
            return None, f"Error checking container status: {e}"
