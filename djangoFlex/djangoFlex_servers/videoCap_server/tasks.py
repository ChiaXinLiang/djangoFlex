from celery import shared_task
import cv2
import time
from django.db import transaction
from django.utils import timezone
from .models import VideoCapConfig, CurrentFrame
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def capture_loop(self, rtmp_url):
    retries = 0
    config = VideoCapConfig.objects.get(rtmp_url=rtmp_url)
    cap = cv2.VideoCapture(rtmp_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    max_retries = 3
    retry_delay = 1

    try:
        while config.is_active:
            ret, frame = cap.read()
            if not ret:
                retries += 1
                if retries > max_retries:
                    raise Exception("Loading frame failed")
                logger.warning(f"Loading frame failed, retry {retries}/{max_retries}")
                time.sleep(retry_delay)
                continue

            # retries = 0

            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            with transaction.atomic():
                current_frame, created = CurrentFrame.objects.get_or_create(config=config)
                current_frame.frame_data = frame_bytes
                current_frame.timestamp = timezone.now()
                current_frame.save()
            
            time.sleep(config.frame_interval)
            config.refresh_from_db()

    except Exception as e:
        logger.error(f"Error in capture_loop: {str(e)}")
        raise self.retry(exc=e)
    finally:
        cap.release()
