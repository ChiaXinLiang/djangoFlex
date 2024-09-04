from django.urls import path
from .views import ViolationDetectView

urlpatterns = [
    path('violations_detect_service/', ViolationDetectView.as_view(), name='violation-detect'),
]

