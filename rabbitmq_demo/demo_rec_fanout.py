import pika
import yaml
import json

def receive_fanout_messages():
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

    channel.exchange_declare(exchange="demo_fanout", exchange_type='fanout')
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange="demo_fanout", queue=queue_name)

    def callback(ch, method, properties, body):
        print(f"Received fanout message: {json.loads(body)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    print("Waiting for fanout messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    receive_fanout_messages()