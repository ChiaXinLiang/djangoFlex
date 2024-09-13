from django.conf import settings
import psycopg2
from djangoFlex_servers.BaseService.BaseDockerService import BaseDockerService
import subprocess
import os

class PostgresDockerService(BaseDockerService):
    def __init__(self):
        super().__init__()
        self.load_config()

    def load_config(self):
        config = settings.SERVERS_CONFIG
        self.container_name = config['POSTGRES_DOCKER_CONTAINER_NAME']
        self.image_name = config['POSTGRES_DOCKER_IMAGE']
        self.host = config['POSTGRES_SERVER_HOST']
        self.port = config['POSTGRES_SERVER_PORT']
        self.root_user = config['POSTGRES_ROOT_USER']
        self.root_password = config['POSTGRES_ROOT_PASSWORD']
        self.database = config['POSTGRES_DATABASE']
        self.data_dir = config['POSTGRES_DATA_DIR']

    def start_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"
        
        try:
            container_exists = subprocess.run(['docker', 'ps', '-a', '-q', '-f', f'name={self.container_name}'], capture_output=True, text=True)
            
            if container_exists.stdout.strip():
                status, message = self.get_container_status()
                if status != 'running':
                    subprocess.run(['docker', 'start', self.container_name], check=True)
                    print(f"Starting existing PostgreSQL container: {self.container_name}")
                else:
                    print(f"PostgreSQL container {self.container_name} is already running")
                return True, f"Starting existing PostgreSQL container: {self.container_name}"
            else:
                command = [
                    "docker", "run",
                    "-d",
                    "--name", self.container_name,
                    "-h", self.host,
                    "-p", f"{self.port}:5432",
                    "-e", f"POSTGRES_PASSWORD={self.root_password}",
                    "-e", f"POSTGRES_DB={self.database}",
                    "-v", f"{self.data_dir}:/var/lib/postgresql/data",
                    self.image_name
                ]
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
                print(f"Created and started new PostgreSQL container: {self.container_name}")
                return True, f"Created and started new PostgreSQL container: {self.container_name}"

        except subprocess.CalledProcessError as e:
            error_message = f"Error starting PostgreSQL Docker container: {e}\nCommand: {e.cmd}\nOutput: {e.stdout}\nError: {e.stderr}"
            print(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Unexpected error starting PostgreSQL Docker container: {str(e)}"
            print(error_message)
            return False, error_message

    def stop_server(self):
        if not self.check_docker_availability():
            return False, "Docker is not available"

        try:
            subprocess.run(["docker", "stop", self.container_name], check=True, capture_output=True, text=True)
            subprocess.run(["docker", "rm", self.container_name], check=True, capture_output=True, text=True)
            return True, "PostgreSQL Docker server stopped successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to stop PostgreSQL Docker server: {e.stderr}"

    def check_server_status(self):
        return super().check_server_status()

    def list_databases(self):
        try:
            connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.root_user,
                password=self.root_password,
                database="postgres"
            )
            cursor = connection.cursor()
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            databases = [db[0] for db in cursor.fetchall()]
            cursor.close()
            connection.close()
            return True, databases
        except Exception as e:
            return False, f"Failed to list databases: {str(e)}"

    def create_database(self, database_name):
        try:
            connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.root_user,
                password=self.root_password,
                database="postgres"
            )
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE {database_name}")
            cursor.close()
            connection.close()
            return True, f"Database '{database_name}' created successfully"
        except Exception as e:
            return False, f"Failed to create database: {str(e)}"

    def delete_database(self, database_name):
        try:
            connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.root_user,
                password=self.root_password,
                database="postgres"
            )
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE {database_name}")
            cursor.close()
            connection.close()
            return True, f"Database '{database_name}' deleted successfully"
        except Exception as e:
            return False, f"Failed to delete database: {str(e)}"