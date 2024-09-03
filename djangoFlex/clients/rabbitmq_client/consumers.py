import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .RabbitMQConsumers import MessageConsumer
from .RabbitMQProducers import MessageProducer

class RabbitMQConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')

        if action == 'send_message':
            producer = MessageProducer()
            producer.send_message_to_queue(
                text_data_json['exchange'],
                text_data_json['exchange_type'],
                text_data_json['queue_name'],
                text_data_json['routing_key'],
                text_data_json['message']
            )
            await self.send(text_data=json.dumps({
                'action': 'message_sent',
                'status': 'Message sent successfully'
            }))
        elif action == 'receive_message':
            consumer = MessageConsumer()
            message = consumer.receive_single_message(
                text_data_json['exchange'],
                text_data_json['exchange_type'],
                text_data_json['queue_name'],
                text_data_json['routing_key']
            )
            await self.send(text_data=json.dumps({
                'action': 'message_received',
                'message': message if message else 'No messages in queue'
            }))