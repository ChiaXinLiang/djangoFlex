import pika
import yaml
import json

def receive_headers_messages(bind_headers):
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

    channel.exchange_declare(exchange="demo_headers", exchange_type='headers')
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    bind_arguments = {}
    for key, value in bind_headers.items():
        bind_arguments[key] = value
    bind_arguments['x-match'] = 'all'  # Change to 'any' for OR matching

    channel.queue_bind(exchange="demo_headers", queue=queue_name, arguments=bind_arguments)

    def callback(ch, method, properties, body):
        print(f"Received headers message: {json.loads(body)}")
        print(f"Message headers: {properties.headers}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    print(f"Waiting for headers messages with binding {bind_headers}. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    bind_headers = {'category': 'electronics', 'priority': 'high'}
    receive_headers_messages(bind_headers)