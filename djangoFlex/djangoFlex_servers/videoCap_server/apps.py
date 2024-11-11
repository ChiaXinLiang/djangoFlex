import os
from django.apps import AppConfig
from django.db.utils import ProgrammingError

class VideoCapServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djangoFlex_servers.videoCap_server"

    def ready(self):
        try:
            from .repositories.video_cap_repository import VideoCapRepository
            VideoCapRepository.reset_video_cap_system()
        except ProgrammingError:
            pass