from django.urls import path
from clients.rabbitmq_client import views

# URL patterns
urlpatterns = [
    path('', views.RabbitMQClientView.as_view(), name='rabbitmq_client_index'),
]
