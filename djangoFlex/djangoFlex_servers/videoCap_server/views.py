from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from .services.videoCap_service import VideoCapService
from .services.cameraList_service import CameraListService
from .models import VideoCapConfig, CameraList
import time
from django.http import HttpRequest

class VideoCapServerView(APIView):
    video_cap_service = None

    @classmethod
    def get_video_cap_service(cls):
        if cls.video_cap_service is None:
            cls.video_cap_service = VideoCapService()
        return cls.video_cap_service

    @method_decorator(name='post', decorator=swagger_auto_schema(
        operation_description="Control the video capture service",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'status', 'start_all', 'stop_all', 'add_camera', 'delete_camera'], description="The action to be performed."),
                'rtmp_url': openapi.Schema(type=openapi.TYPE_STRING, description="RTMP URL for the video capture"),
                'camera_name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the camera (for add_camera action)"),
            },
            required=['action']
        ),
        responses={
            200: openapi.Response(
                description="Successful operation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Service control message"),
                        'is_running': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Service status"),
                    }
                )
            ),
            400: "Bad Request",
            500: "Internal Server Error"
        }
    ))
    def post(self, request, action=None, rtmp_url=None):
        if isinstance(request, HttpRequest):
            # 如果是從 admin 調用，action 和 rtmp_url 會作為參數傳入
            data = {'action': action, 'rtmp_url': rtmp_url}
        else:
            # 如果是 API 調用，從 request.data 中獲取數據
            data = request.data

        action = data.get('action')
        rtmp_url = data.get('rtmp_url')
        camera_name = data.get('camera_name')
        video_cap_service = self.get_video_cap_service()

        if action not in ['start', 'stop', 'status', 'start_all', 'stop_all', 'add_camera', 'delete_camera']:
            return Response({"error": "無效的操作"}, status=status.HTTP_400_BAD_REQUEST)

        if action in ['start', 'stop', 'status'] and not rtmp_url:
            return Response({"error": "此操作需要 RTMP URL"}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'start':
            success, message = video_cap_service.start_server(rtmp_url)
            is_running = success

        elif action == 'stop':
            success, message = video_cap_service.stop_server(rtmp_url)
            CameraList.objects.filter(camera_url=rtmp_url).update(camera_status=False)
            is_running = video_cap_service.check_server_status(rtmp_url)

        elif action == 'status':
            is_running = video_cap_service.check_server_status(rtmp_url)
            message = f"Video capture server for {rtmp_url} is {'running' if is_running else 'not running'}"
        elif action == 'start_all':
            started_count, total_count = video_cap_service.start_all_cameras()
            message = f"Started {started_count} out of {total_count} video capture servers"
            is_running = started_count > 0
            success = True
        elif action == 'stop_all':
            stopped_count = video_cap_service.stop_all_servers()
            message = f"Stopped {stopped_count} video capture servers"
            is_running = False
            success = True
        elif action == 'add_camera':
            if not camera_name or not rtmp_url:
                return Response({"error": "Camera name and RTMP URL are required for adding a camera"}, status=status.HTTP_400_BAD_REQUEST)
            success, message = CameraListService.add_camera(camera_name, rtmp_url)
            is_running = False
        elif action == 'delete_camera':
            if not rtmp_url:
                return Response({"error": "RTMP URL is required for deleting a camera"}, status=status.HTTP_400_BAD_REQUEST)
            success, message = CameraListService.delete_camera(rtmp_url)
            is_running = False

        return Response({"message": message, "is_running": is_running},
                        status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)
