from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from .services.mysqp_docker_service import MySQLDockerService

@method_decorator(name='post', decorator=swagger_auto_schema(
    operation_description="""
    Perform various actions on the MySQL server. The available actions are:
    - 'start': Initiate the MySQL server.
    - 'stop': Halt the MySQL server.
    - 'status': Check the current status of the MySQL server.
    - 'list_databases': Retrieve a list of all databases currently present on the MySQL server.
    - 'create_database': Create a new database on the MySQL server.
    - 'delete_database': Remove an existing database from the MySQL server.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['start', 'stop', 'status', 'list_databases', 'create_database', 'delete_database'], description="The action to be performed on the MySQL server."),
            'database_name': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the database to be created or deleted. This parameter is required for the actions create_database and delete_database.', nullable=True),
        },
        required=['action']
    ),
    responses={
        200: openapi.Response(description="The action was performed successfully on the MySQL server."),
        400: openapi.Response(description="The action is invalid or required parameters are missing."),
        500: openapi.Response(description="The action failed to be performed on the MySQL server due to an internal error.")
    }
))
class MySQLServerView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mysql_service = MySQLDockerService()

    def post(self, request):
        action = request.data.get('action')
        if action == 'start':
            success, message = self.mysql_service.start_server()
            return self.create_response(message, success)
        elif action == 'stop':
            success, message = self.mysql_service.stop_server()
            return self.create_response(message, success)
        elif action == 'status':
            success, message = self.mysql_service.check_server_status()
            return Response({'status': message}, status=status.HTTP_200_OK)
        elif action == 'list_databases':
            success, databases = self.mysql_service.list_databases()
            if success:
                return Response({'databases': databases}, status=status.HTTP_200_OK)
            else:
                return Response({'error': databases}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif action == 'create_database':
            database_name = request.data.get('database_name')
            if not database_name:
                return Response({'error': 'Database name is required'}, status=status.HTTP_400_BAD_REQUEST)
            success, message = self.mysql_service.create_database(database_name)
            return self.create_response(message, success)
        elif action == 'delete_database':
            database_name = request.data.get('database_name')
            if not database_name:
                return Response({'error': 'Database name is required'}, status=status.HTTP_400_BAD_REQUEST)
            success, message = self.mysql_service.delete_database(database_name)
            return self.create_response(message, success)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def create_response(message, success):
        return Response(
            {'message': message},
            status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR
        )
