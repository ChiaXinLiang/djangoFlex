from django.db import models
from django.utils import timezone
import redis

# Create a single Redis client instance

class VideoCapConfig(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rtmp_url = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False)
    frame_interval = models.FloatField(default=0.1)  # Capture at approximately 30 fps
    max_consecutive_errors = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    redis_host = models.CharField(max_length=255, default='localhost')
    redis_client = models.CharField(max_length=255, default='default')

    def __str__(self):
        return f"VideoCapConfig: {self.name}, RTMP URL={self.rtmp_url}, Active={self.is_active}"

class CurrentFrame(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.ForeignKey(VideoCapConfig, on_delete=models.CASCADE, related_name='frames')
    frame_data = models.BinaryField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Frame"
        verbose_name_plural = "Frames"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Frame for {self.config.rtmp_url} at {self.timestamp}"

    def save(self, *args, **kwargs):
        self.timestamp = timezone.now()
        super().save(*args, **kwargs)
        # Save the frame data to Redis server

class CurrentVideoClip(models.Model):
    config = models.ForeignKey(VideoCapConfig, on_delete=models.CASCADE, related_name='video_clips')
    clip_path = models.CharField(max_length=255)  # Path to the stored video clip
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)  # Duration in seconds
    processed = models.BooleanField(default=False)  # Flag to indicate if AI processing is done

    class Meta:
        verbose_name = "Video Clip"
        verbose_name_plural = "Video Clips"
        ordering = ['-start_time']

    def __str__(self):
        return f"Video Clip for {self.config.rtmp_url} from {self.start_time} to {self.end_time}"

    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        super().save(*args, **kwargs)

class AIInferenceResult(models.Model):
    video_clip = models.ForeignKey(CurrentVideoClip, on_delete=models.CASCADE, related_name='ai_results')
    result_data = models.JSONField()  # Store AI results as JSON
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Inference Result"
        verbose_name_plural = "AI Inference Results"
        ordering = ['-timestamp']

    def __str__(self):
        return f"AI Result for {self.video_clip} at {self.timestamp}"

class CameraList(models.Model):
    camera_name = models.CharField(max_length=100, unique=True)
    camera_url = models.CharField(max_length=255, unique=True)
    camera_status = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Camera"
        verbose_name_plural = "Camera List"

    def __str__(self):
        return f"Camera: {self.camera_name}, URL={self.camera_url}, Status={self.camera_status}"
