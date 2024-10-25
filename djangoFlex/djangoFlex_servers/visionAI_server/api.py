from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
# from .services.violationDetect_service import ViolationDetectService
# from .services.objectDetect_service import ObjectDetectService

class ViolationDetectView(APIView):
    violation_detect_service = None

    @classmethod
    # def get_violation_detect_service(cls):
        # if cls.violation_detect_service is None:
            # cls.violation_detect_service = ViolationDetectService()
        # return cls.violation_detect_service

    @method_decorator(name='post', decorator=swagger_auto_schema(
        operation_description="Detect violations or control the violation detection service",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['detect', 'start', 'stop', 'status'], description="The action to be performed."),
                'rtmp_url': openapi.Schema(type=openapi.TYPE_STRING, description="Optional RTMP URL for specific detection"),
            },
            required=['action']
        ),
        responses={
            200: openapi.Response(
                description="Successful operation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'violations': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'rule_code': openapi.Schema(type=openapi.TYPE_STRING),
                                    'description': openapi.Schema(type=openapi.TYPE_STRING),
                                    'severity_level': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Service control message"),
                        'is_running': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Service status"),
                    }
                )
            ),
            400: "Bad Request",
            500: "Internal Server Error"
        }
    ))
    def post(self, request):
        action = request.data.get('action')
        rtmp_url = request.data.get('rtmp_url')
        violation_detect_service = self.get_violation_detect_service()

        if action == 'detect':
            if not violation_detect_service.is_running:
                return Response({"error": "Violation detection service is not running"}, status=status.HTTP_400_BAD_REQUEST)
            detected_violations = violation_detect_service.detect_violations(rtmp_url)

            if detected_violations is None:
                return Response({"error": "No current frame found for the given RTMP URL"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"violations": detected_violations}, status=status.HTTP_200_OK)
        elif action == 'start':
            message = violation_detect_service.start_service()
            running = violation_detect_service.running
            return Response({"message": message, "running": running}, status=status.HTTP_200_OK)
        elif action == 'stop':
            violation_detect_service.stop_service()
            return Response({"message": "Violation detection service stopped", "running": False}, status=status.HTTP_200_OK)
        elif action == 'status':
            running = violation_detect_service.running
            return Response({"running": running}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

