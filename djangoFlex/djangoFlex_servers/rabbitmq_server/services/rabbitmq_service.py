import subprocess
import time
import pika
from django.conf import settings

class RabbitMQService:
    @staticmethod
    def start_server():
        try:
            subprocess.Popen([settings.SERVERS_CONFIG['RABBITMQ_SERVER_PATH']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Starting RabbitMQ server...")
            time.sleep(10)  # Wait for the server to start
            print("RabbitMQ server started successfully.")
            return True
        except Exception as e:
            print(f"Error starting RabbitMQ server: {e}")
            return False

    @staticmethod
    def stop_server():
        try:
            subprocess.run(["rabbitmqctl", "stop"], check=True)
            print("RabbitMQ server stopped successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error stopping RabbitMQ server: {e}")
            return False

    @staticmethod
    def check_server_status():
        try:
            result = subprocess.run(["rabbitmqctl", "status"], capture_output=True, text=True)
            return "RabbitMQ running" in result.stdout
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def create_queue(queue_name):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.SERVERS_CONFIG['RABBITMQ_HOST']))
            channel = connection.channel()
            channel.queue_declare(queue=queue_name)
            connection.close()
            print(f"Queue '{queue_name}' created successfully.")
            return True
        except Exception as e:
            print(f"Error creating queue: {e}")
            return False

    @staticmethod
    def delete_queue(queue_name):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.SERVERS_CONFIG['RABBITMQ_HOST']))
            channel = connection.channel()
            channel.queue_delete(queue=queue_name)
            connection.close()
            print(f"Queue '{queue_name}' deleted successfully.")
            return True
        except Exception as e:
            print(f"Error deleting queue: {e}")
            return False

    @staticmethod
    def list_queues():
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.SERVERS_CONFIG['RABBITMQ_HOST']))
            channel = connection.channel()
            queues = channel.queue_declare(queue='', exclusive=True).method.queue
            connection.close()
            return queues
        except Exception as e:
            print(f"Error listing queues: {e}")
            return []