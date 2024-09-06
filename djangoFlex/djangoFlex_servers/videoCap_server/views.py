from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from .services.videoCap_service import VideoCapService
from .models import VideoCapConfig

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
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'status'], description="The action to be performed."),
                'rtmp_url': openapi.Schema(type=openapi.TYPE_STRING, description="RTMP URL for the video capture"),
            },
            required=['action', 'rtmp_url']
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
    def post(self, request):
        action = request.data.get('action')
        rtmp_url = request.data.get('rtmp_url')
        video_cap_service = self.get_video_cap_service()

        if not rtmp_url:
            return Response({"error": "RTMP URL is required"}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'start':
            success, message = video_cap_service.start_server(rtmp_url)
            is_running = success
        elif action == 'stop':
            success, message = video_cap_service.stop_server(rtmp_url)
            is_running = not success
        elif action == 'status':
            is_running = video_cap_service.check_server_status(rtmp_url)
            message = f"Video capture server for {rtmp_url} is {'running' if is_running else 'not running'}"
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": message, "is_running": is_running}, 
                        status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)
