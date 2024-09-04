import pika
import json
import yaml

def send_test_message(routing_key, message):
    # Load RabbitMQ configuration from YAML file
    with open('rabbitmq_config.yaml', 'r') as f:
        config = yaml.safe_load(f)['rabbitmq']

    # Create a connection to RabbitMQ
    credentials = pika.PlainCredentials(config['username'], config['password'])
    parameters = pika.ConnectionParameters(
        host=config['host'],
        port=config['port'],
        virtual_host=config['vhost'],
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Send the message to RabbitMQ
    channel.exchange_declare(exchange=config['exchange'],
                             exchange_type="direct")
    channel.basic_publish(exchange=config['exchange'],
                          routing_key=routing_key,
                          body=json.dumps(message))
    print(f"Sent message to {routing_key}: {message}")

    # Close the connection
    connection.close()

if __name__ == "__main__":
    routing_key = "camera-live-1"
    message = {
        'camera_id': 1,
        'frame_data': 'Test frame data'
    }
    send_test_message(routing_key, message)