import pika
import yaml
import json

def receive_topic_messages(binding_key):
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

    channel.exchange_declare(exchange="demo_topic", exchange_type='topic')
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange="demo_topic", queue=queue_name, routing_key=binding_key)

    def callback(ch, method, properties, body):
        print(f"Received topic message with routing key {method.routing_key}: {json.loads(body)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    print(f"Waiting for topic messages with binding key {binding_key}. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    binding_key = "animals.mammals.*"
    receive_topic_messages(binding_key)