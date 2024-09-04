from django.urls import path
from .api import MySQLServerView

urlpatterns = [
    path('mysql/', MySQLServerView.as_view(), name='mysql_server'),
]
