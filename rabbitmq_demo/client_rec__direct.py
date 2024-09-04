import pika
import yaml

def receive_message(routing_key):
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

    # Declare the exchange
    channel.exchange_declare(exchange=config['exchange'], 
                             exchange_type="direct")
    
    # Declare a queue
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    
    # Bind the queue to the exchange with the specified routing key
    channel.queue_bind(exchange=config['exchange'], queue=queue_name, routing_key=routing_key)
    
    print(f" [*] Waiting for messages with routing key '{routing_key}'. To exit press CTRL+C")
    
    # Define a callback function to handle messages
    def callback(ch, method, properties, body):
        print(f" [x] Received '{body.decode()}'")

    # Tell RabbitMQ that this callback will receive messages from the specified queue
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    
    channel.start_consuming()

if __name__ == "__main__":
    routing_key = 'camera-live-1'
    receive_message(routing_key)