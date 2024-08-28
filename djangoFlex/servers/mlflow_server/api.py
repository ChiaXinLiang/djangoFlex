from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from .services.mlflow_docker_service import MLflowDockerService
from .services.mlflow_service import MLflowService

@method_decorator(name='post', decorator=swagger_auto_schema(
    operation_description="""
    Perform various actions on the MLflow server. The available actions are:
    - 'start': Initiate the MLflow server.
    - 'stop': Halt the MLflow server.
    - 'status': Check the current status of the MLflow server.
    - 'list_experiments': Retrieve a list of all experiments currently present on the MLflow server.
    - 'create_experiment': Create a new experiment on the MLflow server.
    - 'delete_experiment': Remove an existing experiment from the MLflow server.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'status', 'list_experiments', 'create_experiment', 'delete_experiment'], description="The action to be performed on the MLflow server."),
            'experiment_name': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the experiment to be created or deleted. This parameter is required for the actions create_experiment and delete_experiment.', nullable=True),
        },
        required=['action']
    ),
    responses={
        200: openapi.Response(description="The action was performed successfully on the MLflow server."),
        400: openapi.Response(description="The action is invalid or required parameters are missing."),
        500: openapi.Response(description="The action failed to be performed on the MLflow server due to an internal error.")
    }
))
class MLflowServerView(APIView):
    def post(self, request):
        action = request.data.get('action')
        if action == 'start':
            success, message = self.mlflow_service.start_server()
            return self.create_response(message, success)
        elif action == 'stop':
            success, message = self.mlflow_service.stop_server()
            return self.create_response(message, success)
        elif action == 'status':
            is_running, message = self.mlflow_service.check_server_status()
            return Response({'status': message}, status=status.HTTP_200_OK)
        elif action == 'list_experiments':
            experiments = self.mlflow_service.list_experiments()
            return Response({'experiments': experiments}, status=status.HTTP_200_OK)
        elif action == 'create_experiment':
            experiment_name = request.data.get('experiment_name')
            if not experiment_name:
                return Response({'error': 'Experiment name is required'}, status=status.HTTP_400_BAD_REQUEST)
            success, message = self.mlflow_service.create_experiment(experiment_name)
            return self.create_response(message, success)
        elif action == 'delete_experiment':
            experiment_name = request.data.get('experiment_name')
            if not experiment_name:
                return Response({'error': 'Experiment name is required'}, status=status.HTTP_400_BAD_REQUEST)
            success, message = self.mlflow_service.delete_experiment(experiment_name)
            return self.create_response(message, success)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def create_response(message, success):
        return Response(
            {'message': message},
            status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class MLflowTraditionalServerView(MLflowServerView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mlflow_service = MLflowService()

class MLflowDockerServerView(MLflowServerView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mlflow_service = MLflowDockerService()
