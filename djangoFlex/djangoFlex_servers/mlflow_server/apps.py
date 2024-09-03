from django.apps import AppConfig

class MLflowServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'djangoFlex_servers.mlflow_server'  # Changed from 'djangoFlex.server.mlflow_server'