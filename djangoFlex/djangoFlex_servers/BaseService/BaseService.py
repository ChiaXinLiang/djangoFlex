import subprocess
from abc import ABC, abstractmethod
from django.conf import settings

class BaseService(ABC):
    def __init__(self):
        self.service_name = None
    
    # @abstractmethod
    # def get_config(self):
    #     pass 

    @abstractmethod
    def start_server(self):
        
        pass

    @abstractmethod
    def stop_server(self):
        pass

    @abstractmethod
    def check_server_status(self):
        pass

    def check_service_availability(self):
        try:
            result = subprocess.run(['systemctl', 'is-active', self.service_name], capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                print(f"Service {self.service_name} is not available. Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error checking service availability: {e}")
            return False

    def get_service_status(self):
        result = subprocess.run(['systemctl', 'status', self.service_name], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None

