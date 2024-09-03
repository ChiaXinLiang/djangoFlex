from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from .services.videoCap_service import VideoCapService
from .models import VideoCapConfig

video_cap_service = VideoCapService()

@method_decorator(name='post', decorator=swagger_auto_schema(
    operation_description="""
    Perform various actions on the Video Capture server. The available actions are:
    - 'start': Initiate the Video Capture server for a given RTMP URL.
    - 'stop': Halt the Video Capture server for a given RTMP URL.
    - 'status': Check the current status of the Video Capture server for a given RTMP URL.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'status'], description="The action to be performed on the Video Capture server."),
            'rtmp_url': openapi.Schema(type=openapi.TYPE_STRING, description="The RTMP URL to be used for the action."),
        },
        required=['action', 'rtmp_url']
    ),
    responses={
        200: openapi.Response(description="The action was performed successfully on the Video Capture server."),
        400: openapi.Response(description="The action is invalid or missing required parameters."),
        500: openapi.Response(description="The action failed to be performed on the Video Capture server due to an internal error.")
    }
))
class VideoCapServerView(APIView):
    def post(self, request):
        action = request.data.get('action')
        rtmp_url = request.data.get('rtmp_url')

        if not rtmp_url:
            return Response({'error': 'RTMP URL is required'}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'start':
            success, message = video_cap_service.start_server(rtmp_url)
            return self.create_response(message, success)
        elif action == 'stop':
            success, message = video_cap_service.stop_server(rtmp_url)
            return self.create_response(message, success)
        elif action == 'status':
            is_running = video_cap_service.check_server_status(rtmp_url)
            message = f"Video capture server for {rtmp_url} is {'running' if is_running else 'not running'}"
            return Response({'status': message}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def create_response(message, success):
        return Response(
            {'message': message},
            status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # @swagger_auto_schema(
    #     method='get',
    #     operation_description="Get the status of all Video Capture servers.",
    #     responses={
    #         200: openapi.Response(
    #             description="Successfully retrieved the status of all servers.",
    #             schema=openapi.Schema(
    #                 type=openapi.TYPE_OBJECT,
    #                 properties={
    #                     'servers': openapi.Schema(
    #                         type=openapi.TYPE_ARRAY,
    #                         items=openapi.Schema(
    #                             type=openapi.TYPE_OBJECT,
    #                             properties={
    #                                 'rtmp_url': openapi.Schema(type=openapi.TYPE_STRING),
    #                                 'is_running': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    #                             }
    #                         )
    #                     )
    #                 }
    #             )
    #         )
    #     }
    # )
    # def get(self, request):
    #     servers_status = []
    #     for config in VideoCapConfig.objects.all():
    #         is_running = video_cap_service.check_server_status(config.rtmp_url)
    #         servers_status.append({
    #             'rtmp_url': config.rtmp_url,
    #             'is_running': is_running
    #         })
    #     return Response({'servers': servers_status}, status=status.HTTP_200_OK)