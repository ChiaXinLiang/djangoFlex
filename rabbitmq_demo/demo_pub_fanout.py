import pika
import json
import yaml

def send_fanout_message(message):
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
    channel.basic_publish(exchange='demo_fanout',
                          routing_key='',
                          body=json.dumps(message))
    print(f"Sent fanout message: {message}")

    connection.close()

if __name__ == "__main__":
    message = {
        'type': 'fanout',
        'data': 'This is a fanout message'
    }
    send_fanout_message(message)