from django.urls import re_path
from . import consumers

rabbitmq_websocket_urlpatterns = [
    re_path(r'ws/rabbitmq/$', consumers.RabbitMQConsumer.as_asgi()),
]