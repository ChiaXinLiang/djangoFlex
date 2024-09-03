from django.db import models
from django.utils import timezone

class VideoCapConfig(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rtmp_url = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False)
    frame_interval = models.FloatField(default=0.033)  # Capture at approximately 30 fps
    max_consecutive_errors = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"VideoCapConfig: {self.name}, RTMP URL={self.rtmp_url}, Active={self.is_active}"

class CurrentFrame(models.Model):
    config = models.OneToOneField(VideoCapConfig, on_delete=models.CASCADE, related_name='current_frame')
    frame_data = models.BinaryField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Current Frame"
        verbose_name_plural = "Current Frames"

    def __str__(self):
        return f"Current frame for {self.config.name} at {self.timestamp}"

    def save(self, *args, **kwargs):
        self.timestamp = timezone.now()  # Update timestamp manually
        super().save(*args, **kwargs)