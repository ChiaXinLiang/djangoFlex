from django.urls import path
from . import api


# URL patterns
urlpatterns = [
    path('local/server/', api.RabbitMQTraditionalServerView.as_view(), name='rabbitmq-traditional-server'),
    path('docker/server/', api.RabbitMQDockerServerView.as_view(), name='rabbitmq-docker-server'),
 
]
