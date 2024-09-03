from clients.rabbitmq_client.RabbitMQClient import RabbitMQClient, rabbitmq_client, sio

class MessageProducer:
    def __init__(self):
        self.client = RabbitMQClient()

    @rabbitmq_client
    async def send_message_to_queue(self, exchange, exchange_type, queue_name, routing_key, message):
        await self.client.send_message(exchange, exchange_type, queue_name, routing_key, message)
        await sio.emit('message_sent', {'status': 'Message sent successfully'})