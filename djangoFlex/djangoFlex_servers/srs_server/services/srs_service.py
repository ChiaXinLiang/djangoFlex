import subprocess
import time
from django.conf import settings

class SRSService:
    @staticmethod
    def start_server():
        try:
            subprocess.Popen([settings.SERVERS_CONFIG['SRS_SERVER_PATH'], '-c', settings.SERVERS_CONFIG['SRS_CONFIG_PATH']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Starting SRS server...")
            time.sleep(5)  # Wait for the server to start
            print("SRS server started successfully.")
            return True
        except Exception as e:
            print(f"Error starting SRS server: {e}")
            return False

    @staticmethod
    def stop_server():
        try:
            subprocess.run(["killall", "srs"], check=True)
            print("SRS server stopped successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error stopping SRS server: {e}")
            return False

    @staticmethod
    def check_server_status():
        try:
            result = subprocess.run(["pgrep", "srs"], capture_output=True, text=True)
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def get_server_version():
        try:
            result = subprocess.run([settings.SERVERS_CONFIG['SRS_SERVER_PATH'], '-v'], capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error getting SRS server version: {e}")
            return None

    @staticmethod
    def reload_config():
        try:
            subprocess.run(["kill", "-1", "$(pgrep srs)"], shell=True, check=True)
            print("SRS server configuration reloaded successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error reloading SRS server configuration: {e}")
            return False