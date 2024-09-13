from django.urls import path
from .api import PostgresServerView

urlpatterns = [
    path('postgres/', PostgresServerView.as_view(), name='postgres_server'),
]
