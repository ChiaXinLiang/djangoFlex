from django.db import models

# Create your models here.

class SRSServerConfig(models.Model):
    docker_image = models.CharField(max_length=255, default='registry.cn-hangzhou.aliyuncs.com/ossrs/srs:4')
    container_name = models.CharField(max_length=100, default='srs_server')
    rtmp_port = models.IntegerField(default=1935)
    http_api_port = models.IntegerField(default=1985)
    http_server_port = models.IntegerField(default=8080)
    config_file = models.CharField(max_length=100, default='conf/docker.conf')

    class Meta:
        verbose_name = 'SRS Server Configuration'
        verbose_name_plural = 'SRS Server Configurations'

    def __str__(self):
        return f"SRS Server Config ({self.container_name})"
