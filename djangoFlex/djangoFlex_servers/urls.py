from django.urls import path, include

urlpatterns = [
    path('rabbitmq_server/', include('djangoFlex_servers.rabbitmq_server.urls')),
    path('mlflow_server/', include('djangoFlex_servers.mlflow_server.urls')),
    path('srs_server/', include('djangoFlex_servers.srs_server.urls')),
    path('videoCap_server/', include('djangoFlex_servers.videoCap_server.urls')),
    path('mysqp_server/', include('djangoFlex_servers.mysqp_server.urls')),
    path('redis_server/', include('djangoFlex_servers.redis_server.urls')),
    path('visionAI_server/', include('djangoFlex_servers.visionAI_server.urls')),
    path('postgres_server/', include('djangoFlex_servers.postgres_server.urls')),
]