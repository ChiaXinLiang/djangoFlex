from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from .services.redis_service import RedisDockerService

@method_decorator(name='post', decorator=swagger_auto_schema(
    operation_description="""
    Perform various actions on the Redis server. The available actions are:
    - 'start': Initiate the Redis server.
    - 'stop': Halt the Redis server.
    - 'status': Check the current status of the Redis server.
    - 'list_keys': Retrieve a list of all keys currently present on the Redis server.
    - 'set_key': Set a new key-value pair on the Redis server.
    - 'delete_key': Remove an existing key from the Redis server.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'status', 'list_keys', 'set_key', 'delete_key'], description="The action to be performed on the Redis server."),
            'key': openapi.Schema(type=openapi.TYPE_STRING, description='The key to be set or deleted. This parameter is required for the actions set_key and delete_key.', nullable=True),
            'value': openapi.Schema(type=openapi.TYPE_STRING, description='The value to be set for the key. This parameter is required for the action set_key.', nullable=True),
        },
        required=['action']
    ),
    responses={
        200: openapi.Response(description="The action was performed successfully on the Redis server."),
        400: openapi.Response(description="The action is invalid or required parameters are missing."),
        500: openapi.Response(description="The action failed to be performed on the Redis server due to an internal error.")
    }
))
class RedisServerView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.redis_service = RedisDockerService()

    def post(self, request):
        action = request.data.get('action')
        if action == 'start':
            success, message = self.redis_service.start_server()
            return self.create_response(message, success)
        elif action == 'stop':
            success, message = self.redis_service.stop_server()
            return self.create_response(message, success)
        elif action == 'status':
            success, message = self.redis_service.check_server_status()
            return Response({'status': message}, status=status.HTTP_200_OK)
        elif action == 'list_keys':
            success, keys = self.redis_service.list_keys()
            if success:
                return Response({'keys': keys}, status=status.HTTP_200_OK)
            else:
                return Response({'error': keys}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif action == 'set_key':
            key = request.data.get('key')
            value = request.data.get('value')
            if not key or not value:
                return Response({'error': 'Both key and value are required'}, status=status.HTTP_400_BAD_REQUEST)
            success, message = self.redis_service.set_key(key, value)
            return self.create_response(message, success)
        elif action == 'delete_key':
            key = request.data.get('key')
            if not key:
                return Response({'error': 'Key is required'}, status=status.HTTP_400_BAD_REQUEST)
            success, message = self.redis_service.delete_key(key)
            return self.create_response(message, success)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def create_response(message, success):
        return Response(
            {'message': message},
            status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR
        )
