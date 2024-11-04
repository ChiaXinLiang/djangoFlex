import pika
import json
import yaml

def receive_messages():
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

    def callback(ch, method, properties, body):
        message = json.loads(body)
        print(f"Received message: {message}")

    # Consume messages from the queue
    channel.basic_consume(queue=config['queue_name'],
                          on_message_callback=callback,
                          auto_ack=True)

    print(f"Waiting for messages on queue '{config['queue_name']}'. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    receive_messages()