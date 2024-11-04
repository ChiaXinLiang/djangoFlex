from django.urls import path, include

urlpatterns = [
    # path('mlflow_server/', include('djangoFlex_servers.mlflow_server.urls')),
    path('videoCap_server/', include('djangoFlex_servers.videoCap_server.urls')),
    path('visionAI_server/', include('djangoFlex_servers.visionAI_server.urls')),
    # path('postgres_server/', include('djangoFlex_servers.postgres_server.urls')),
]