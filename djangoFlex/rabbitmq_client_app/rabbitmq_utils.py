import pika

def send_message(exchange, exchange_type, queue_name, routing_key, message):
    """
    Send a message to the specified RabbitMQ queue.

    Parameters:
    exchange (str): The name of the exchange.
    exchange_type (str): The type of the exchange (e.g., 'direct', 'fanout', 'topic', 'headers').
    queue_name (str): The name of the queue to which the message will be sent.
    routing_key (str): The routing key for the message.
    message (str): The message to be sent to the queue.

    Returns:
    None
    """
    # Establish a connection to the RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the exchange
    channel.exchange_declare(exchange=exchange, exchange_type=exchange_type)

    # Declare the queue to ensure it exists
    channel.queue_declare(queue=queue_name)

    # Bind the queue to the exchange with the routing key
    channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=routing_key)

    # Publish the message to the exchange with the routing key
    channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message)

    # Close the connection
    connection.close()

def receive_message(exchange, exchange_type, queue_name, routing_key):
    """
    Receive a message from the specified RabbitMQ queue.

    Parameters:
    exchange (str): The name of the exchange.
    exchange_type (str): The type of the exchange (e.g., 'direct', 'fanout', 'topic', 'headers').
    queue_name (str): The name of the queue from which the message will be received.
    routing_key (str): The routing key for the message.

    Returns:
    str: The message received from the queue, or None if the queue is empty.
    """
    # Establish a connection to the RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the exchange
    channel.exchange_declare(exchange=exchange, exchange_type=exchange_type)

    # Declare the queue to ensure it exists
    channel.queue_declare(queue=queue_name)

    # Bind the queue to the exchange with the routing key
    channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=routing_key)

    # Attempt to get a message from the queue
    method_frame, header_frame, body = channel.basic_get(queue=queue_name)
    if method_frame:
        # Acknowledge the message if received
        channel.basic_ack(method_frame.delivery_tag)
        connection.close()
        return body.decode()
    else:
        # Close the connection if no message is received
        connection.close()
        return None