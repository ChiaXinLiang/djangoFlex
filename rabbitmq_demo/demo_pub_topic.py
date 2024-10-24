import pika
import json
import yaml

def send_topic_message(routing_key, message):
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
    channel.basic_publish(exchange="demo_topic",
                          routing_key=routing_key,
                          body=json.dumps(message))
    print(f"Sent topic message to {routing_key}: {message}")

    connection.close()

if __name__ == "__main__":
    routing_key = "animals.mammals.dogs"
    message = {
        'type': 'topic',
        'data': 'This is a topic message about dogs'
    }
    send_topic_message(routing_key, message)