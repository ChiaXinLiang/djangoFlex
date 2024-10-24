from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
# from .services.objectDetect_service import ObjectDetectService


class ObjectDetectView(APIView):
    object_detect_service = None

    # @classmethod
    # def get_object_detect_service(cls):
    #     if cls.object_detect_service is None:
    #         cls.object_detect_service = ObjectDetectService()
    #     return cls.object_detect_service

    @method_decorator(name='post', decorator=swagger_auto_schema(
        operation_description="Control the object detection service",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'status'], description="The action to be performed."),
                'rtmp_url': openapi.Schema(type=openapi.TYPE_STRING, description="Optional RTMP URL for specific detection"),
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
    def post(self, request):
        action = request.data.get('action')
        rtmp_url = request.data.get('rtmp_url')
        object_detect_service = self.get_object_detect_service()

        if action == 'start':
            if rtmp_url:
                success, message = object_detect_service.start_detection(rtmp_url)
            else:
                object_detect_service.start_service()
                success, message = True, "Object detection service started"
            return Response({"message": message, "is_running": success}, status=status.HTTP_200_OK)
        elif action == 'stop':
            if rtmp_url:
                success, message = object_detect_service.stop_detection(rtmp_url)
            else:
                object_detect_service.stop_service()
                success, message = True, "Object detection service stopped"
            return Response({"message": message, "is_running": not success}, status=status.HTTP_200_OK)
        elif action == 'status':
            running_threads = object_detect_service.list_running_threads()
            return Response({"running_threads": running_threads}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
