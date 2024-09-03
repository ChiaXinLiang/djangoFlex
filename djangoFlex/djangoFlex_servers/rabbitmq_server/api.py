from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .services.rabbitmq_docker_service import RabbitMQDockerService
from .services.rabbitmq_service import RabbitMQService
from django.utils.decorators import method_decorator


@method_decorator(name='post', decorator=swagger_auto_schema(
    operation_description="""
    Perform various actions on the RabbitMQ server. The available actions are:
    - 'start': Initiate the RabbitMQ server.
    - 'stop': Halt the RabbitMQ server.
    - 'status': Check the current status of the RabbitMQ server.
    - 'create_queue': Create a new message queue on the RabbitMQ server.
    - 'delete_queue': Remove an existing message queue from the RabbitMQ server.
    - 'list_queues': Retrieve a list of all message queues currently present on the RabbitMQ server.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'status', 'create_queue', 'delete_queue', 'list_queues'], description="The action to be performed on the RabbitMQ server. Possible values are: 'start', 'stop', 'status', 'create_queue', 'delete_queue', and 'list_queues'."),
            'queue_name': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the queue to be created or deleted. This parameter is required for the actions create_queue and delete_queue.', nullable=True),
        },
        required=['action']
    ),
    responses={
        200: openapi.Response(description="The action was performed successfully on the RabbitMQ server."),
        400: openapi.Response(description="The action is invalid or required parameters are missing."),
        500: openapi.Response(description="The action failed to be performed on the RabbitMQ server due to an internal error.")
    }
))
class RabbitMQServerView(APIView):
    def post(self, request):
        action = request.data.get('action')
        if action == 'start':
            success, message = self.rabbitmq_service.start_server()
            return self.create_response(message, success)
        elif action == 'stop':
            success, message = self.rabbitmq_service.stop_server()
            return self.create_response(message, success)
        elif action == 'status':
            is_running, message = self.rabbitmq_service.check_server_status()
            return Response({'status': message}, status=status.HTTP_200_OK)
        elif action == 'create_queue':
            queue_name = request.data.get('queue_name')
            if not queue_name:
                return Response({'error': 'Queue name is required'}, status=status.HTTP_400_BAD_REQUEST)
            success, message = self.rabbitmq_service.create_queue(queue_name)
            return self.create_response(message, success)
        elif action == 'delete_queue':
            queue_name = request.data.get('queue_name')
            if not queue_name:
                return Response({'error': 'Queue name is required'}, status=status.HTTP_400_BAD_REQUEST)
            success, message = self.rabbitmq_service.delete_queue(queue_name)
            return self.create_response(message, success)
        elif action == 'list_queues':
            queues = self.rabbitmq_service.list_queues()
            return Response({'queues': queues}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def create_response(message, success):
        return Response(
            {'message': message},
            status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class RabbitMQTraditionalServerView(RabbitMQServerView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rabbitmq_service = RabbitMQService()

class RabbitMQDockerServerView(RabbitMQServerView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rabbitmq_service = RabbitMQDockerService()