from django.conf import settings
import mysql.connector
from djangoFlex_servers.BaseService.BaseDockerService import BaseDockerService
import subprocess
import os

class MySQLDockerService(BaseDockerService):
    def __init__(self):
        super().__init__()
        self.load_config()

    def load_config(self):
        config = settings.SERVERS_CONFIG
        self.container_name = config['MYSQL_DOCKER_CONTAINER_NAME']
        self.image_name = config['MYSQL_DOCKER_IMAGE']
        self.host = config['MYSQL_SERVER_HOST']
        self.port = config['MYSQL_SERVER_PORT']
        self.root_user = config['MYSQL_ROOT_USER']
        self.root_password = config['MYSQL_ROOT_PASSWORD']
        self.database = config['MYSQL_DATABASE']
        self.data_dir = config['MYSQL_DATA_DIR']

    def start_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"
        
        try:
            container_exists = subprocess.run(['docker', 'ps', '-a', '-q', '-f', f'name={self.container_name}'], capture_output=True, text=True)
            
            if container_exists.stdout.strip():
                status, message = self.get_container_status()
                if status != 'running':
                    subprocess.run(['docker', 'start', self.container_name], check=True)
                    print(f"Starting existing MySQL container: {self.container_name}")
                else:
                    print(f"MySQL container {self.container_name} is already running")
                return True, f"Starting existing MySQL container: {self.container_name}"
            else:
                command = [
                    "docker", "run",
                    "-d",
                    "--name", self.container_name,
                    "-h", self.host,
                    "-p", f"{self.port}:3306",
                    "-e", f"MYSQL_ROOT_PASSWORD={self.root_password}",
                    "-e", f"MYSQL_DATABASE={self.database}",
                    "-v", f"{self.data_dir}:/var/lib/mysql",
                    self.image_name
                ]
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
                print(f"Created and started new MySQL container: {self.container_name}")
                return True, f"Created and started new MySQL container: {self.container_name}"

        except subprocess.CalledProcessError as e:
            error_message = f"Error starting MySQL Docker container: {e}\nCommand: {e.cmd}\nOutput: {e.stdout}\nError: {e.stderr}"
            print(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Unexpected error starting MySQL Docker container: {str(e)}"
            print(error_message)
            return False, error_message

    def stop_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"

        try:
            subprocess.run(["docker", "stop", self.container_name], check=True, capture_output=True, text=True)
            subprocess.run(["docker", "rm", self.container_name], check=True, capture_output=True, text=True)
            return True, "MySQL Docker server stopped successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to stop MySQL Docker server: {e.stderr}"

    def check_server_status(self):
        return super().check_server_status()

    def list_databases(self):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.root_user,
                password=self.root_password
            )
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            cursor.close()
            connection.close()
            return True, databases
        except Exception as e:
            return False, f"Failed to list databases: {str(e)}"

    def create_database(self, database_name):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.root_user,
                password=self.root_password
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE {database_name}")
            connection.commit()
            cursor.close()
            connection.close()
            return True, f"Database '{database_name}' created successfully"
        except Exception as e:
            return False, f"Failed to create database: {str(e)}"

    def delete_database(self, database_name):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.root_user,
                password=self.root_password
            )
            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE {database_name}")
            connection.commit()
            cursor.close()
            connection.close()
            return True, f"Database '{database_name}' deleted successfully"
        except Exception as e:
            return False, f"Failed to delete database: {str(e)}"