from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.urls import path, reverse
import base64

# from .services.videoCap_service import VideoCapService
from .services.video_cap_manager import VideoCapManager

from .models import VideoCapConfig, CurrentVideoClip, CameraList
from ..visionAI_server.models import CameraDrawingStatus
from ..visionAI_server.api_draw import DrawView
from .views import VideoCapServerView


@admin.register(VideoCapConfig)
class VideoCapConfigAdmin(admin.ModelAdmin):
    list_display = ('rtmp_url', 'frame_interval', 'max_consecutive_errors', 'is_active')

@admin.register(CurrentVideoClip)
class CurrentVideoClipAdmin(admin.ModelAdmin):
    list_display = ('config', 'clip_path', 'start_time', 'end_time', 'duration', 'processed')
    readonly_fields = ('duration',)

@admin.register(CameraList)
class CameraListAdmin(admin.ModelAdmin):
    list_display = ('camera_name', 'camera_url', 'camera_online_status', 'camera_status_display', 'start_stop_button', 'drawing_status_display', 'drawing_control_button')
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
                               reverse('admin:stop_capture', args=[obj.camera_url]))
        else:
            return format_html('<a class="button" href="{}" onclick="return confirm(\'確定要啟動錄影嗎？\')">啟動</a>',
                               reverse('admin:start_capture', args=[obj.camera_url]))
    start_stop_button.short_description = '錄影操作'

    def camera_online_status(self, obj):
        is_online = VideoCapManager().check_camera_online(rtmp_url=obj.camera_url)
        print('is_online:', is_online)
        return format_html('<span style="color: {};">{}</span>',
                           'green' if is_online else 'red',
                           '在線' if is_online else '離線')
    camera_online_status.short_description = '串流狀態'

    def drawing_status_display(self, obj):
        status, _ = CameraDrawingStatus.objects.get_or_create(camera_url=obj.camera_url)
        return format_html('<span style="color: {};">{}</span>',
                           'green' if status.is_drawing else 'red',
                           '畫圖中' if status.is_drawing else '未畫圖')
    drawing_status_display.short_description = '畫圖狀態'

    def drawing_control_button(self, obj):
        status, _ = CameraDrawingStatus.objects.get_or_create(camera_url=obj.camera_url)
        if status.is_drawing:
            return format_html('<a class="button" href="{}" onclick="return confirm(\'確定要停止畫圖嗎？\')">停止</a>',
                               reverse('admin:stop_drawing', args=[obj.camera_url]))
        else:
            return format_html('<a class="button" href="{}" onclick="return confirm(\'確定要開始畫圖嗎？\')">開始</a>',
                               reverse('admin:start_drawing', args=[obj.camera_url]))
    drawing_control_button.short_description = '畫圖操作'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:camera_url>/start_capture/', self.admin_site.admin_view(self.start_video_cap), name='start_capture'),
            path('<path:camera_url>/stop_capture/', self.admin_site.admin_view(self.stop_video_cap), name='stop_capture'),
            path('<path:camera_url>/start_drawing/', self.admin_site.admin_view(self.start_drawing), name='start_drawing'),
            path('<path:camera_url>/stop_drawing/', self.admin_site.admin_view(self.stop_drawing), name='stop_drawing'),
        ]
        return custom_urls + urls

    def start_video_cap(self, request, camera_url):
        view = VideoCapServerView()
        response = view.post(request, action='start', rtmp_url=camera_url)
        self.message_user(request, response.data['message'])
        return HttpResponseRedirect(reverse('admin:videoCap_server_cameralist_changelist'))

    def stop_video_cap(self, request, camera_url):
        view = VideoCapServerView()
        response = view.post(request, action='stop', rtmp_url=camera_url)
        self.message_user(request, response.data['message'])
        return HttpResponseRedirect(reverse('admin:videoCap_server_cameralist_changelist'))

    def start_drawing(self, request, camera_url):
        view = DrawView()  # 實例化 DrawView
        response = view.post(request, action='start', rtmp_url=camera_url)
        self.message_user(request, response.data['message'])
        return HttpResponseRedirect(reverse('admin:videoCap_server_cameralist_changelist'))

    def stop_drawing(self, request, camera_url):
        view = DrawView()  # 實例化 DrawView
        response = view.post(request, action='stop', rtmp_url=camera_url)
        self.message_user(request, response.data['message'])
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
