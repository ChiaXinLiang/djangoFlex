from django.contrib import admin
from django.utils.html import format_html
import base64

from .models import CurrentFrame, VideoCapConfig

@admin.register(CurrentFrame)
class CurrentFrameAdmin(admin.ModelAdmin):
    def frame_preview(self, obj):
        if obj.frame_data:
            # Convert binary image data to a base64 encoded string
            image_base64 = base64.b64encode(obj.frame_data).decode('ascii')
            # Render the image in the admin list display
            return format_html('<img src="data:image/jpeg;base64,{}" width="300" height="auto" />', image_base64)
        return "No image"
    frame_preview.short_description = 'Frame Preview'

    def rtmp_url(self, obj):
        if obj.config:
            return obj.config.rtmp_url
        return "No config"

    list_display = ('frame_preview', 'rtmp_url')
    readonly_fields = ('frame_preview', 'rtmp_url')

@admin.register(VideoCapConfig)
class VideoCapConfigAdmin(admin.ModelAdmin):
    list_display = ('rtmp_url', 'frame_interval', 'max_consecutive_errors', 'is_active')