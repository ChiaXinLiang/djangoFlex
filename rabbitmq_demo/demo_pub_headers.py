import pika
import json
import yaml

def send_headers_message(headers, message):
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
    channel.basic_publish(exchange="demo_headers",
                          routing_key='',
                          body=json.dumps(message),
                          properties=pika.BasicProperties(headers=headers))
    print(f"Sent headers message with headers {headers}: {message}")

    connection.close()

if __name__ == "__main__":
    headers = {'category': 'electronics', 'priority': 'high'}
    message = {
        'type': 'headers',
        'data': 'This is a headers message about high-priority electronics'
    }
    send_headers_message(headers, message)