from django.urls import path
from . import api

urlpatterns = [
    # path('local/server/', api.MLflowTraditionalServerView.as_view(), name='mlflow-traditional-server'),
    path('mlflow_server/docker/server/', api.MLflowDockerServerView.as_view(), name='mlflow-docker-server'),
]