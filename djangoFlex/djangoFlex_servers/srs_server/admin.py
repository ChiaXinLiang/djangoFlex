from django.contrib import admin
from .models import SRSServerConfig

# Register your models here.

@admin.register(SRSServerConfig)
class SRSServerConfigAdmin(admin.ModelAdmin):
    list_display = ('container_name', 'docker_image', 'rtmp_port', 'http_api_port', 'http_server_port')
