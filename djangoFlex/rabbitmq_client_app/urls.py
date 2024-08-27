from django.urls import path
from .views import send_message_view, receive_message_view

# URL patterns
urlpatterns = [
    path('send_message/', send_message_view, name='send_message'),
    path('receive_message/', receive_message_view, name='receive_message'),
]
