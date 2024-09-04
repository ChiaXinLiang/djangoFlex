from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from .services.visionAI_db_service import VisionAIDBService
from .serializers.serializer import RuleSerializer, RoleSerializer, EntityTypeSerializer, SceneTypeSerializer

class VisionAIDBAPI(APIView):
    @method_decorator(name='post', decorator=swagger_auto_schema(
        operation_description="Load data, get data, or delete all data from the VisionAI database",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, description="Action to perform: 'load_all', 'get', or 'delete_all'"),
                'type': openapi.Schema(type=openapi.TYPE_STRING, description="Type of data to get: 'rules', 'roles', 'entity_types', or 'scene_types'"),
            },
            required=['action']
        ),
        responses={
            200: openapi.Response(
                description="Successful operation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Success message"),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description="Requested data"),
                    }
                )
            ),
            400: "Bad Request",
            500: "Internal Server Error"
        }
    ))
    def post(self, request):
        action = request.data.get('action')
        if action == 'load_all':
            try:
                VisionAIDBService.load_all_from_yaml()
                return Response({'message': 'All data loaded successfully from YAML files'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif action == 'get':
            data_type = request.data.get('type')
            try:
                if data_type == 'rules':
                    data = VisionAIDBService.get_all_rules()
                    serializer = RuleSerializer(data.values(), many=True)
                elif data_type == 'roles':
                    data = VisionAIDBService.get_all_roles()
                    serializer = RoleSerializer(data.values(), many=True)
                elif data_type == 'entity_types':
                    data = VisionAIDBService.get_all_entity_types()
                    serializer = EntityTypeSerializer(data.values(), many=True)
                elif data_type == 'scene_types':
                    data = VisionAIDBService.get_all_scene_types()
                    serializer = SceneTypeSerializer(data.values(), many=True)
                else:
                    return Response({'error': 'Invalid data type'}, status=status.HTTP_400_BAD_REQUEST)
                return Response({'message': f'Successfully retrieved {data_type}', 'data': serializer.data}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif action == 'delete_all':
            try:
                VisionAIDBService.delete_all()
                return Response({'message': 'All data deleted successfully'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(name='get', decorator=swagger_auto_schema(
        operation_description="Get all rules from the VisionAI database",
        responses={
            200: openapi.Response(
                description="Successful operation",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            ),
            500: "Internal Server Error"
        }
    ))
    def get(self, request):
        try:
            rules = VisionAIDBService.get_all_rules()
            serializer = RuleSerializer(rules.values(), many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
