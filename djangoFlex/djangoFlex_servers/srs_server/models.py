from django.db import models
from django.conf import settings

# Create your models here.

class SRSServerConfig(models.Model):
    docker_image = models.CharField(max_length=255, default=settings.SERVERS_CONFIG.get('SRS_DOCKER_IMAGE', 'ossrs/srs:5'))
    container_name = models.CharField(max_length=100, default=settings.SERVERS_CONFIG.get('SRS_DOCKER_CONTAINER_NAME', 'srs_container'))
    rtmp_port = models.IntegerField(default=settings.SERVERS_CONFIG.get('SRS_SERVER_PORT', 1935))
    http_api_port = models.IntegerField(default=1985)  # Keeping default as it's not in settings
    http_server_port = models.IntegerField(default=settings.SERVERS_CONFIG.get('SRS_HTTP_SERVER_PORT', 8080))
    config_file = models.CharField(max_length=100, default='conf/docker.conf')

    class Meta:
        verbose_name = 'SRS Server Configuration'
        verbose_name_plural = 'SRS Server Configurations'

    def __str__(self):
        return f"SRS Server Config ({self.container_name})"
