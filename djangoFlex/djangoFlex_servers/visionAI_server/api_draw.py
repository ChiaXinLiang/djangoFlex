from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from .services.drawResult_service import DrawResultService
from ..videoCap_server.models import VideoCapConfig

class DrawView(APIView):
    draw_result_service = None

    @classmethod
    def get_draw_result_service(cls):
        if cls.draw_result_service is None:
            cls.draw_result_service = DrawResultService()
        return cls.draw_result_service

    @method_decorator(name='post', decorator=swagger_auto_schema(
        operation_description="Start or stop the draw service for active RTMP URLs.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop'], description="The action to be performed."),
            },
            required=['action']
        ),
        responses={
            200: openapi.Response(
                description="Successful operation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Operation success status"),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Service control message"),
                        'affected_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of affected draw services"),
                    }
                )
            ),
            400: "Bad Request",
            500: "Internal Server Error"
        }
    ))
    def post(self, request):
        action = request.data.get('action')
        draw_result_service = self.get_draw_result_service()

        if action not in ['start', 'stop']:
            return Response({"success": False, "message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        active_configs = VideoCapConfig.objects.filter(is_active=True)
        affected_count = 0

        if action == 'start':
            for config in active_configs:
                rtmp_url = config.rtmp_url
                success, message = draw_result_service.start_draw_service(rtmp_url)
                if success:
                    affected_count += 1
            action_verb = "Started"
        else:  # stop
            for config in active_configs:
                rtmp_url = config.rtmp_url
                success, message = draw_result_service.stop_draw_service(rtmp_url)
                if success:
                    affected_count += 1
            action_verb = "Stopped"

        total_count = active_configs.count()
        message = f"{action_verb} {affected_count} out of {total_count} draw services"
        success = affected_count > 0

        return Response({
            "success": success,
            "message": message,
            "affected_count": affected_count
        }, status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR)

    @method_decorator(name='get', decorator=swagger_auto_schema(
        operation_description="Retrieve the list of currently running draw service threads.",
        responses={
            200: openapi.Response(
                description="Successful operation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'running_threads': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'rtmp_url': openapi.Schema(type=openapi.TYPE_STRING),
                                    'thread_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'thread_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'is_alive': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                                }
                            )
                        )
                    }
                )
            )
        }
    ))
    def get(self, request):
        draw_result_service = self.get_draw_result_service()
        running_threads = draw_result_service.list_running_threads()
        return Response({"running_threads": running_threads}, status=status.HTTP_200_OK)