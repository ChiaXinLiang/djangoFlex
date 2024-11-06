import os
from django.apps import AppConfig

class VideoCapServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djangoFlex_servers.videoCap_server"

    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            from .repositories.video_cap_repository import VideoCapRepository
            VideoCapRepository.reset_video_cap_system()
            print("视频捕获服务器已准备就绪！")