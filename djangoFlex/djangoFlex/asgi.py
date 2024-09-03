import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from djangoFlex.routing import websocket_application
from django.urls import path


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoFlex.settings')

django_asgi_app = get_asgi_application()

application = socketio.ASGIApp(sio, django_asgi_app)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter([
        path("socket.io/", websocket_application),
        # other WebSocket routes...
    ]),
})