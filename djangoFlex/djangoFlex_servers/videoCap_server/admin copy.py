from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.urls import path, reverse
import base64
from django.contrib import messages

from .services.videoCap_service import VideoCapService

from .models import CurrentFrame, VideoCapConfig, CurrentVideoClip, AIInferenceResult, CameraList

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

    def frame_time(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    frame_time.short_description = 'Frame Time'

    list_display = ('frame_preview', 'rtmp_url', 'frame_time')
    readonly_fields = ('frame_preview', 'rtmp_url', 'frame_time')

@admin.register(VideoCapConfig)
class VideoCapConfigAdmin(admin.ModelAdmin):
    list_display = ('rtmp_url', 'frame_interval', 'max_consecutive_errors', 'is_active')

@admin.register(CurrentVideoClip)
class CurrentVideoClipAdmin(admin.ModelAdmin):
    list_display = ('config', 'clip_path', 'start_time', 'end_time', 'duration', 'processed')
    readonly_fields = ('duration',)

@admin.register(AIInferenceResult)
class AIInferenceResultAdmin(admin.ModelAdmin):
    list_display = ('video_clip', 'timestamp')
    readonly_fields = ('result_data',)

@admin.register(CameraList)
class CameraListAdmin(admin.ModelAdmin):
    list_display = ('camera_name', 'camera_url', 'camera_status_display', 'start_stop_button')
    list_editable = ('camera_url',)
    search_fields = ('camera_name', 'camera_url')
    list_filter = ('camera_name', 'camera_status')

    def camera_status_display(self, obj):
        video_cap_service = VideoCapService()
        is_running = video_cap_service.check_server_status(obj.camera_url)
        return format_html('<span style="color: {};">{}</span>',
                           'green' if is_running else 'red',
                           '運行中' if is_running else '已停止')
    camera_status_display.short_description = '錄影狀態'

    def start_stop_button(self, obj):
        video_cap_service = VideoCapService()
        is_running = video_cap_service.check_server_status(obj.camera_url)
        if is_running:
            return format_html('<a class="button" href="{}">停止</a>',
                               reverse('admin:stop_camera', args=[obj.camera_url]))
        else:
            return format_html('<a class="button" href="{}">啟動</a>',
                               reverse('admin:start_camera', args=[obj.camera_url]))
    start_stop_button.short_description = '錄影操作'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:camera_url>/start/', self.admin_site.admin_view(self.start_camera), name='start_camera'),
            path('<path:camera_url>/stop/', self.admin_site.admin_view(self.stop_camera), name='stop_camera'),
        ]
        return custom_urls + urls

    def start_camera(self, request, camera_url):
        video_cap_service = VideoCapService()
        success, message = video_cap_service.start_server(camera_url)
        if success:
            self.message_user(request, f"成功啟動攝像機 {camera_url}", level=messages.SUCCESS)
        else:
            self.message_user(request, f"啟動攝像機 {camera_url} 失敗: {message}", level=messages.ERROR)
        return HttpResponseRedirect(reverse('admin:videoCap_server_cameralist_changelist'))

    def stop_camera(self, request, camera_url):
        video_cap_service = VideoCapService()
        success, message = video_cap_service.stop_server(camera_url)
        if success:
            self.message_user(request, f"成功停止攝像機 {camera_url}", level=messages.SUCCESS)
        else:
            self.message_user(request, f"停止攝像機 {camera_url} 失敗: {message}", level=messages.ERROR)
        return HttpResponseRedirect(reverse('admin:videoCap_server_cameralist_changelist'))

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        VideoCapConfig.objects.update_or_create(
            rtmp_url=obj.camera_url,
            defaults={'name': obj.camera_name, 'is_active': obj.camera_status}
        )
