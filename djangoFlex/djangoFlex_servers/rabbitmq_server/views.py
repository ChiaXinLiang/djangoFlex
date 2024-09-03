# rabbitmq_server_app/views.py

from django.http import JsonResponse
from ..rabbitmq_client_app.rabbitmq_utils import send_message, receive_message
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view

@swagger_auto_schema(
    method='post',
    operation_description="Send a message to the RabbitMQ queue",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING, description='The message to be sent to the queue')
        },
        required=['message']
    ),
    responses={
        200: openapi.Response(description="Message sent successfully"),
        400: openapi.Response(description="Invalid request method")
    }
)
@api_view(['POST'])
def send_message_view(request):
    if request.method == 'POST':
        message = request.data.get('message', '')
        queue_name = 'test_queue'
        send_message(queue_name, message)
        return JsonResponse({'status': 'Message sent successfully'})
    return JsonResponse({'status': 'Invalid request method'}, status=400)

@swagger_auto_schema(
    method='get',
    operation_description="Receive a message from the RabbitMQ queue",
    responses={
        200: openapi.Response(description="Message received successfully"),
        204: openapi.Response(description="No messages in queue")
    }
)
@api_view(['GET'])
def receive_message_view(request):
    queue_name = 'test_queue'
    message = receive_message(queue_name)
    if message:
        return JsonResponse({'message': message})
    return JsonResponse({'message': 'No messages in queue'}, status=204)