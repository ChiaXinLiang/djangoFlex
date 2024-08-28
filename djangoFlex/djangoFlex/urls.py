"""
URL configuration for djangoFlex project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.views.generic.base import RedirectView


schema_view = get_schema_view(
   openapi.Info(
      title="API Documentation",
      default_version='v1',
      description="API documentation for all available endpoints",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@myproject.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/', admin.site.urls),
    path('servers/', include('servers.urls')),  # Update this line
    path('servers/rabbitmq_dashboard/', RedirectView.as_view(url=f'http://{settings.SERVERS_CONFIG["RABBITMQ_HOST"]}:{settings.SERVERS_CONFIG["RABBITMQ_DASHBOARD_PORT"]}/', permanent=False), name='rabbitmq_management'),
    path('servers/mlflow_dashboard/', RedirectView.as_view(url=f'http://{settings.SERVERS_CONFIG["MLFLOW_SERVER_HOST"]}:{settings.SERVERS_CONFIG["MLFLOW_SERVER_PORT"]}/', permanent=False), name='mlflow_ui'),
    # path('api/rabbitmq_client/', include('rabbitmq_client_app.urls')),
]
