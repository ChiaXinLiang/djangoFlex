from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.urls import path, reverse
import base64

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
    list_display = ('camera_name', 'camera_url', 'camera_online_status', 'camera_status_display', 'start_stop_button')
    list_editable = ('camera_url',)
    search_fields = ('camera_name', 'camera_url')
    list_filter = ('camera_name',)
    actions = ['start_all_cameras', 'stop_all_cameras']

    def camera_status_display(self, obj):
        status = VideoCapConfig.objects.filter(rtmp_url=obj.camera_url, is_active=True).exists()
        return format_html('<span style="color: {};">{}</span>',
                           'green' if status else 'red',
                           '儲存中' if status else '已停止')
    camera_status_display.short_description = '錄影狀態'

    def start_stop_button(self, obj):
        status = VideoCapConfig.objects.filter(rtmp_url=obj.camera_url, is_active=True).exists()
        if status:
            return format_html('<a class="button" href="{}" onclick="return confirm(\'確定要停止錄影嗎？\')">停止</a>',
                               reverse('admin:stop_camera', args=[obj.camera_url]))
        else:
            return format_html('<a class="button" href="{}" onclick="return confirm(\'確定要啟動錄影嗎？\')">啟動</a>',
                               reverse('admin:start_camera', args=[obj.camera_url]))
    start_stop_button.short_description = '錄影操作'

    def camera_online_status(self, obj):
        is_online = VideoCapService().check_camera_online(rtmp_url=obj.camera_url)
        print('is_online:', is_online)
        return format_html('<span style="color: {};">{}</span>',
                           'green' if is_online else 'red',
                           '在線' if is_online else '離線')
    camera_online_status.short_description = '串流狀態'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:camera_url>/start/', self.admin_site.admin_view(self.start_camera), name='start_camera'),
            path('<path:camera_url>/stop/', self.admin_site.admin_view(self.stop_camera), name='stop_camera'),
        ]
        return custom_urls + urls

    def start_camera(self, request, camera_url):
        from .views import VideoCapServerView
        view = VideoCapServerView()
        response = view.post(request, action='start', rtmp_url=camera_url)
        self.message_user(request, response.data['message'])
        # 確保更新 VideoCapConfig 的狀態
        VideoCapConfig.objects.filter(rtmp_url=camera_url).update(is_active=True)
        return HttpResponseRedirect(reverse('admin:videoCap_server_cameralist_changelist'))

    def stop_camera(self, request, camera_url):
        from .views import VideoCapServerView
        view = VideoCapServerView()
        response = view.post(request, action='stop', rtmp_url=camera_url)
        self.message_user(request, response.data['message'])
        # 確保更新 VideoCapConfig 的狀態
        VideoCapConfig.objects.filter(rtmp_url=camera_url).update(is_active=False)
        return HttpResponseRedirect(reverse('admin:videoCap_server_cameralist_changelist'))

    @admin.action(description="啟動所有錄影")
    def start_all_cameras(self, request, queryset):
        from .views import VideoCapServerView
        view = VideoCapServerView()
        response = view.post(request, action='start_all')
        message = response.data['message']
        if response.status_code == 200:
            self.message_user(request, message, messages.SUCCESS)
        else:
            self.message_user(request, f"失敗：無法啟動所有錄影：{message}", messages.ERROR)

    @admin.action(description="停止所有錄影")
    def stop_all_cameras(self, request, queryset):
        from .views import VideoCapServerView
        view = VideoCapServerView()
        response = view.post(request, action='stop_all')
        message = response.data['message']
        if response.status_code == 200:
            self.message_user(request, message, messages.SUCCESS)
        else:
            self.message_user(request, f"失敗：無法停止所有錄影：{message}", messages.ERROR)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        VideoCapConfig.objects.update_or_create(
            rtmp_url=obj.camera_url,
            defaults={'name': obj.camera_name, 'is_active': False}
        )
