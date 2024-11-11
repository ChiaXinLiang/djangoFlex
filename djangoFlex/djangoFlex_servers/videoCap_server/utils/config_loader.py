from django.conf import settings
from dataclasses import dataclass

@dataclass
class VideoCapConfig:
    fps: int
    resolution: tuple
    gop_length: int
    hls_time: int
    video_clip_dir: str
    check_interval: float
    reconnect_timeout: int
    max_reconnect_attempts: int

class ConfigLoader:
    @staticmethod
    def load_config():
        return VideoCapConfig(
            fps=getattr(settings, 'VIDEO_CAP_FPS', 15),
            resolution=getattr(settings, 'VIDEO_CAP_RESOLUTION', (1280, 720)),
            gop_length=getattr(settings, 'VIDEO_CAP_GOP_LENGTH', 15),
            hls_time=getattr(settings, 'VIDEO_CAP_HLS_TIME', 2),
            video_clip_dir=getattr(settings, 'VIDEO_CAP_CLIP_DIR', 'tmp/video_clip'),
            check_interval=getattr(settings, 'VIDEO_CAP_CHECK_INTERVAL', 0.1),
            reconnect_timeout=getattr(settings, 'VIDEO_CAP_RECONNECT_TIMEOUT', 5),
            max_reconnect_attempts=getattr(settings, 'VIDEO_CAP_MAX_RECONNECT_ATTEMPTS', 5)
        )
