from django.urls import path
from . import api


# URL patterns
urlpatterns = [
    # path('rabbitmq/local/server/', api.RabbitMQTraditionalServerView.as_view(), name='rabbitmq-traditional-server'),
    path('rabbitmq/docker/server/', api.RabbitMQDockerServerView.as_view(), name='rabbitmq-docker-server'),
 
]
