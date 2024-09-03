from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path
from clients import rabbitmq_websocket_urlpatterns

# Redefine websocket_application by including the imported patterns and Socket.IO
websocket_urlpatterns = URLRouter(
    path("rabbitmq_io/", rabbitmq_websocket_urlpatterns)
)
