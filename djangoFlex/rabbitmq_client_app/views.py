# rabbitmq_server_app/views.py

from django.http import JsonResponse
from .rabbitmq_utils import send_message, receive_message
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view


# Define the request body schema
send_message_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='The message to be sent to the queue', default='Hello, World!'),
        'exchange': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the exchange', default='default_exchange'),
        'exchange_type': openapi.Schema(type=openapi.TYPE_STRING, description='The type of the exchange (e.g., direct, fanout, topic, headers)', default='direct'),
        'queue_name': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the queue to which the message will be sent', default='default_queue'),
        'routing_key': openapi.Schema(type=openapi.TYPE_STRING, description='The routing key for the message', default='default_routing_key')
    },
    required=['message', 'exchange', 'exchange_type', 'queue_name', 'routing_key']
)

@swagger_auto_schema(
    method='post',
    operation_description="Send a message to the RabbitMQ queue",
    request_body=send_message_request_body,
    responses={
        200: openapi.Response(description="Message sent successfully", examples={
            'application/json': {
                'status': 'Message sent successfully'
            }
        }),
        400: openapi.Response(description="Invalid request method", examples={
            'application/json': {
                'status': 'Invalid request method'
            }
        })
    }
)
@api_view(['POST'])
def send_message_view(request):
    if request.method == 'POST':
        message = request.data.get('message', 'Hello, World!')
        exchange = request.data.get('exchange', 'default_exchange')
        exchange_type = request.data.get('exchange_type', 'direct')
        queue_name = request.data.get('queue_name', 'default_queue')
        routing_key = request.data.get('routing_key', 'default_routing_key')
        send_message(exchange, exchange_type, queue_name, routing_key, message)
        return JsonResponse({'status': 'Message sent successfully'})
    return JsonResponse({'status': 'Invalid request method'}, status=400)

receive_message_schema = swagger_auto_schema(
    method='get',
    operation_description="Receive a message from the RabbitMQ queue",
    manual_parameters=[
        openapi.Parameter('exchange', openapi.IN_QUERY, description="The name of the exchange", type=openapi.TYPE_STRING, default='default_exchange'),
        openapi.Parameter('exchange_type', openapi.IN_QUERY, description="The type of the exchange (e.g., direct, fanout, topic, headers)", type=openapi.TYPE_STRING, default='direct'),
        openapi.Parameter('queue_name', openapi.IN_QUERY, description="The name of the queue to receive the message from", type=openapi.TYPE_STRING, default='default_queue'),
        openapi.Parameter('routing_key', openapi.IN_QUERY, description="The routing key for the message", type=openapi.TYPE_STRING, default='default_routing_key')
    ],
    responses={
        200: openapi.Response(description="Message received successfully", examples={
            'application/json': {
                'message': 'The content of the received message'
            }
        }),
        204: openapi.Response(description="No messages in queue", examples={
            'application/json': {
                'message': 'No messages in queue'
            }
        }),
        400: openapi.Response(description="Queue name not provided", examples={
            'application/json': {
                'message': 'Queue name not provided'
            }
        })
    }
)

@receive_message_schema
@api_view(['GET'])
def receive_message_view(request):
    exchange = request.GET.get('exchange', 'default_exchange')
    exchange_type = request.GET.get('exchange_type', 'direct')
    queue_name = request.GET.get('queue_name', 'default_queue')
    routing_key = request.GET.get('routing_key', 'default_routing_key')
    if not queue_name:
        return JsonResponse({'message': 'Queue name not provided'}, status=400)
    message = receive_message(exchange, exchange_type, queue_name, routing_key)
    if message:
        return JsonResponse({'message': message})
    return JsonResponse({'message': 'No messages in queue'}, status=204)