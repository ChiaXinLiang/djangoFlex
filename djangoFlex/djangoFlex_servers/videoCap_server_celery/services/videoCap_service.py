from celery import shared_task
from django.db import transaction
from .models import VideoCapConfig, CurrentFrame

@shared_task
def capture_loop(rtmp_url):
    import cv2
    from django.db import transaction
    from .models import VideoCapConfig, CurrentFrame
    import time

    config = VideoCapConfig.objects.get(rtmp_url=rtmp_url)
    cap = cv2.VideoCapture(rtmp_url)
    consecutive_errors = 0

    while config.is_active:
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = buffer.tobytes()

            with transaction.atomic():
                current_frame, created = CurrentFrame.objects.get_or_create(config=config)
                current_frame.frame_data = frame_data
                current_frame.save()

            consecutive_errors = 0
        else:
            consecutive_errors += 1
            if consecutive_errors >= config.max_consecutive_errors:
                break

        time.sleep(config.frame_interval)
        config.refresh_from_db()

    cap.release()
    with transaction.atomic():
        config.is_active = False
        config.save()
        CurrentFrame.objects.filter(config=config).delete()

class VideoCapService:
    def start_server(self, rtmp_url):
        config, created = VideoCapConfig.objects.get_or_create(rtmp_url=rtmp_url)
        if not created and config.is_active:
            return False, "Server already running"

        with transaction.atomic():
            config.is_active = True
            config.save()

        capture_loop.delay(rtmp_url)
        return True, "Server started successfully"

    def stop_server(self, rtmp_url):
        try:
            config = VideoCapConfig.objects.get(rtmp_url=rtmp_url)
        except VideoCapConfig.DoesNotExist:
            return False, "Server not running"

        with transaction.atomic():
            config.is_active = False
            config.save()
            CurrentFrame.objects.filter(config=config).delete()

        # Note: Celery task will check is_active and stop itself
        return True, "Server stopped successfully"

    def check_server_status(self, rtmp_url):
        try:
            config = VideoCapConfig.objects.get(rtmp_url=rtmp_url)
            return config.is_active
        except VideoCapConfig.DoesNotExist:
            return False