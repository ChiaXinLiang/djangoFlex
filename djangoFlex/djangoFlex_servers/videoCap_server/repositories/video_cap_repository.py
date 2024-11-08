from django.db import transaction
from ..models import VideoCapConfig, CurrentVideoClip

class VideoCapRepository:
    @staticmethod
    def get_or_create_config(rtmp_url):
        config, created = VideoCapConfig.objects.get_or_create(rtmp_url=rtmp_url)
        if created:
            config.name = f"Config_{config.id}"
            config.save()
        return config

    @staticmethod
    def get_config(rtmp_url):
        return VideoCapConfig.objects.get(rtmp_url=rtmp_url)

    @staticmethod
    def set_config_active(config, is_active):
        config.is_active = is_active
        config.save()

    @staticmethod
    def set_config_inactive(rtmp_url):
        VideoCapConfig.objects.filter(rtmp_url=rtmp_url).update(is_active=False)

    @staticmethod
    @transaction.atomic
    def reset_video_cap_system():
        CurrentVideoClip.objects.all().delete()
        VideoCapConfig.objects.update(is_active=False)

    @staticmethod
    def create_current_video_clip(config, clip_path, start_time, end_time, duration):
        return CurrentVideoClip.objects.create(
            config=config,
            clip_path=clip_path,
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )

    @staticmethod
    def delete_current_video_clips(config):
        CurrentVideoClip.objects.filter(config=config).delete()
