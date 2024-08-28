from django.urls import path, include

urlpatterns = [
    path('rabbitmq_server/', include('servers.rabbitmq_server.urls')),
    path('mlflow_server/', include('servers.mlflow_server.urls')),
]