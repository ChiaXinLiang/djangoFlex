from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from .services.srs_docker_service import SRSDockerService
from .services.srs_service import SRSService

@method_decorator(name='post', decorator=swagger_auto_schema(
    operation_description="""
    Perform various actions on the SRS server. The available actions are:
    - 'start': Initiate the SRS server.
    - 'stop': Halt the SRS server.
    - 'status': Check the current status of the SRS server.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'status'], description="The action to be performed on the SRS server."),
        },
        required=['action']
    ),
    responses={
        200: openapi.Response(description="The action was performed successfully on the SRS server."),
        400: openapi.Response(description="The action is invalid."),
        500: openapi.Response(description="The action failed to be performed on the SRS server due to an internal error.")
    }
))
class SRSServerView(APIView):
    def post(self, request):
        action = request.data.get('action')
        if action == 'start':
            success, message = self.srs_service.start_server()
            return self.create_response(message, success)
        elif action == 'stop':
            success, message = self.srs_service.stop_server()
            return self.create_response(message, success)
        elif action == 'status':
            is_running, message = self.srs_service.check_server_status()
            return Response({'status': message}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def create_response(message, success):
        return Response(
            {'message': message},
            status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class SRSTraditionalServerView(SRSServerView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.srs_service = SRSService()

class SRSDockerServerView(SRSServerView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.srs_service = SRSDockerService()
