from django.urls import path
from .api import SRSTraditionalServerView, SRSDockerServerView

urlpatterns = [
    # path('api/srs/traditional/', SRSTraditionalServerView.as_view(), name='srs_traditional_api'),
    path('api/srs/docker/', SRSDockerServerView.as_view(), name='srs_docker_api'),
]
