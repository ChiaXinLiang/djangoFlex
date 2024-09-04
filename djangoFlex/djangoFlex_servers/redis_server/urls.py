
from django.urls import path
from .api import RedisServerView

urlpatterns = [
    path('redis/', RedisServerView.as_view(), name='mysql_server'),
]
