import asyncio
import socketio
import aio_pika
from django.conf import settings

logger = logging.getLogger(__name__)

rabbitmq_manager = socketio.AsyncAioPikaManager(
    url=f"amqp://{settings.SERVERS_CONFIG['RABBITMQ']['USER']}:{settings.SERVERS_CONFIG['RABBITMQ']['PASSWORD']}@{settings.SERVERS_CONFIG['RABBITMQ']['HOST']}:{settings.SERVERS_CONFIG['RABBITMQ']['PORT']}/{settings.SERVERS_CONFIG['RABBITMQ']['VIRTUAL_HOST']}"
)

sio = socketio.AsyncServer(async_mode='asgi', client_manager=rabbitmq_manager)

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            f"amqp://{settings.SERVERS_CONFIG['RABBITMQ']['USER']}:{settings.SERVERS_CONFIG['RABBITMQ']['PASSWORD']}@{settings.SERVERS_CONFIG['RABBITMQ']['HOST']}:{settings.SERVERS_CONFIG['RABBITMQ']['PORT']}/{settings.SERVERS_CONFIG['RABBITMQ']['VIRTUAL_HOST']}"
        )
        self.channel = await self.connection.channel()

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def send_message(self, exchange, exchange_type, queue_name, routing_key, message):
        if not self.connection or self.connection.is_closed:
            await self.connect()

        exchange_obj = await self.channel.declare_exchange(exchange, exchange_type)
        queue = await self.channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange_obj, routing_key)

        await exchange_obj.publish(
            aio_pika.Message(body=message.encode()),
            routing_key=routing_key
        )

    async def receive_message(self, exchange, exchange_type, queue_name, routing_key):
        if not self.connection or self.connection.is_closed:
            await self.connect()

        exchange_obj = await self.channel.declare_exchange(exchange, exchange_type)
        queue = await self.channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange_obj, routing_key)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    return message.body.decode()

    async def start_consuming(self, queue_name, callback):
        if not self.connection or self.connection.is_closed:
            await self.connect()

        queue = await self.channel.declare_queue(queue_name, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await callback(self.channel, message.delivery_tag, None, message.body)

def rabbitmq_client(func):
    async def wrapper(*args, **kwargs):
        client = args[0].client
        try:
            return await func(*args, **kwargs)
        finally:
            await client.close()
    return wrapper