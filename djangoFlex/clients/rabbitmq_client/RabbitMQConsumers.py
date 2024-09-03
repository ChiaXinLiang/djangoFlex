from clients.rabbitmq_client.RabbitMQClient import RabbitMQClient, rabbitmq_client, sio
import logging
import asyncio

logger = logging.getLogger(__name__)

class MessageConsumer:
    def __init__(self):
        self.client = RabbitMQClient()

    @rabbitmq_client
    async def start_consumer(self, queue_name):
        async def callback(ch, delivery_tag, properties, body):
            logger.info(f"Received message: {body.decode()}")
            await ch.basic_ack(delivery_tag)
            await sio.emit('message_received', {'message': body.decode()})

        await self.client.start_consuming(queue_name, callback)

    @rabbitmq_client
    async def receive_single_message(self, exchange, exchange_type, queue_name, routing_key):
        message = await self.client.receive_message(exchange, exchange_type, queue_name, routing_key)
        if message:
            await sio.emit('message_received', {'message': message})
        return message