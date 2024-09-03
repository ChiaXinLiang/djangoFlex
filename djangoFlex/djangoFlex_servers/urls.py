from django.urls import path, include

urlpatterns = [
    path('rabbitmq_server/', include('djangoFlex_servers.rabbitmq_server.urls')),
    path('mlflow_server/', include('djangoFlex_servers.mlflow_server.urls')),
    path('srs_server/', include('djangoFlex_servers.srs_server.urls')),
    path('videoCap_server/', include('djangoFlex_servers.videoCap_server.urls')),
]