import pika
import json
import yaml

def publish_message(message):
    # Load RabbitMQ configuration from YAML file
    with open('rabbitmq_config.yaml', 'r') as f:
        config = yaml.safe_load(f)['rabbitmq']

    credentials = pika.PlainCredentials(config['username'], config['password'])
    parameters = pika.ConnectionParameters(
        host=config['host'],
        port=config['port'],
        virtual_host=config['vhost'],
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue=config['queue_name'])

    # Publish the message
    channel.basic_publish(exchange='',
                          routing_key=config['queue_name'],
                          body=json.dumps(message))
    print(f"Sent message: {message}")

    connection.close()

if __name__ == "__main__":
    message = {
        'type': 'queue',
        'data': 'This is a message sent directly to a queue'
    }
    publish_message(message)