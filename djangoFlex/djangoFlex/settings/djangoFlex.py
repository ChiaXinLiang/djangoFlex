from djangoFlex.settings.base import *  # noqa

from dotenv import load_dotenv
from djangoFlex.config.load_config_from_yaml import load_config_from_yaml

# Django Configuration
# DJANGO_SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "your-secret-key-here")
# DEBUG = os.getenv("DEBUG", "False") == "True"
# ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# MLflow Configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_BACKEND_STORE = os.getenv("MLFLOW_BACKEND_STORE", "mlruns")
MLFLOW_SERVER_PORT = int(os.getenv("MLFLOW_SERVER_PORT", "5000"))
MLFLOW_SERVER_HOST = os.getenv("MLFLOW_SERVER_HOST", "localhost")

# RabbitMQ Configuration
# RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
# RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5675"))
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")  # 改為容器名稱
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))  # 改為容器內部端口
RABBITMQ_DASHBOARD_PORT = int(os.getenv("RABBITMQ_DASHBOARD_PORT", "15676"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672/")
# CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")  # 改為容器名稱

# SRS (Simple RTMP Server) Configuration
# SRS_SERVER_HOST = os.getenv("SRS_SERVER_HOST", "localhost")
SRS_SERVER_HOST = os.getenv("SRS_SERVER_HOST", "srs")  # 改為容器名稱
SRS_SERVER_PORT = int(os.getenv("SRS_SERVER_PORT", "1935"))
SRS_HTTP_SERVER_PORT = int(os.getenv("SRS_HTTP_SERVER_PORT", "8080"))

# VisionAI Configuration
VISIONAI_RULE_CONFIG_PATH = os.getenv("VISIONAI_RULE_CONFIG_PATH", "djangoFlex_servers/visionAI_server/type_initial_config/rule.yaml")
VISIONAI_ROLE_CONFIG_PATH = os.getenv("VISIONAI_ROLE_CONFIG_PATH", "djangoFlex_servers/visionAI_server/type_initial_config/role.yaml")
VISIONAI_ENTITY_TYPE_CONFIG_PATH = os.getenv("VISIONAI_ENTITY_TYPE_CONFIG_PATH", "djangoFlex_servers/visionAI_server/type_initial_config/entity_type.yaml")
VISIONAI_SCENE_TYPE_CONFIG_PATH = os.getenv("VISIONAI_SCENE_TYPE_CONFIG_PATH", "djangoFlex_servers/visionAI_server/type_initial_config/scene_type.yaml")

# PostgreSQL Configuration
# POSTGRES_SERVER_HOST = os.getenv("POSTGRES_SERVER_HOST", "localhost")
# POSTGRES_SERVER_PORT = int(os.getenv("POSTGRES_SERVER_PORT", "5435"))
POSTGRES_SERVER_HOST = os.getenv("POSTGRES_SERVER_HOST", "postgres")
POSTGRES_SERVER_PORT = int(os.getenv("POSTGRES_SERVER_PORT", "5432"))
POSTGRES_ROOT_USER = os.getenv("POSTGRES_ROOT_USER", "postgres")
POSTGRES_ROOT_PASSWORD = os.getenv("POSTGRES_ROOT_PASSWORD", "your_postgres_password")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "your_postgres_database")


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': POSTGRES_DATABASE,
        'USER': POSTGRES_ROOT_USER,
        'PASSWORD': POSTGRES_ROOT_PASSWORD,
        'HOST': POSTGRES_SERVER_HOST,
        'PORT': POSTGRES_SERVER_PORT,
    }
}




