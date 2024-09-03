from clients.rabbitmq_client.RabbitMQClient import sio
from clients.rabbitmq_client.RabbitMQProducers import MessageProducer
from clients.rabbitmq_client.RabbitMQConsumers import MessageConsumer

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def send_message(sid, data):
    producer = MessageProducer()
    await producer.send_message_to_queue(
        data['exchange'],
        data['exchange_type'],
        data['queue_name'],
        data['routing_key'],
        data['message']
    )

@sio.event
async def receive_message(sid, data):
    consumer = MessageConsumer()
    await consumer.receive_single_message(
        data['exchange'],
        data['exchange_type'],
        data['queue_name'],
        data['routing_key']
    )