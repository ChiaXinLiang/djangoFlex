from django.urls import path
from .views import VideoCapServerView

urlpatterns = [
    path('api/videocap/', VideoCapServerView.as_view(), name='videocap_api'),
]
