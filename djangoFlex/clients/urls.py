from django.urls import path, include

urlpatterns = [
    path('rabbitmq_app/', include('app.rabbitmq_client_app.urls')),
]