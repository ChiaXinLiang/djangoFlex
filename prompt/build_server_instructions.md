# Project overview

This project, named djangoFlex, is a comprehensive Django-based application that integrates various services and servers. It includes functionality for video capture, vision AI, database management, message queuing, and more.

# Feature requirements

1. Video capture and processing
2. Object detection and scene analysis
3. Violation detection based on predefined rules
4. Integration with RabbitMQ for message queuing
5. Support for multiple database systems (PostgreSQL, MySQL, Redis)
6. MLflow integration for machine learning model management
7. SRS (Simple RTMP Server) integration for streaming
8. Celery integration for task management

# Relevant docs

- Django documentation: https://docs.djangoproject.com/
- RabbitMQ documentation: https://www.rabbitmq.com/documentation.html
- PostgreSQL documentation: https://www.postgresql.org/docs/
- Redis documentation: https://redis.io/documentation
- MLflow documentation: https://www.mlflow.org/docs/latest/index.html
- Celery documentation: https://docs.celeryproject.org/

# Current File Structure
djangoFlex/
├── .env
├── clear_all_migrate_and_db.py
├── clear_pyc.py
├── db.sqlite3
├── manage.py
├── LICENSE
├── README.md
├── clients/
│   ├── routing.py
│   ├── urls.py
│   ├── __init__.py
│   └── rabbitmq_client/
│       ├── admin.py
│       ├── apps.py
│       ├── consumers.py
│       ├── models.py
│       ├── RabbitMQClient.py
│       ├── RabbitMQConsumers.py
│       ├── RabbitMQProducers.py
│       ├── routing.py
│       ├── socketio_server.py
│       ├── tests.py
│       ├── urls.py
│       ├── views.py
│       ├── __init__.py
│       ├── migrations/
│       │   └── __init__.py
│       └── templates/
│           └── rabbitmq_client/
│               └── index.html
├── djangoFlex/
│   ├── asgi.py
│   ├── celery.py
│   ├── routing.py
│   ├── settings/
│   │   └── base.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── __init__.py
│   └── config/
│       ├── load_config_from_yaml.py
│       ├── servers.yaml
│       ├── test.yaml
│       └── __init__.py
├── djangoFlex_servers/
│   ├── urls.py
│   ├── __init__.py
│   ├── BaseService/
│   │   ├── BaseDockerService.py
│   │   └── BaseService.py
│   ├── mlflow_server/
│   │   ├── api.py
│   │   ├── apps.py
│   │   ├── urls.py
│   │   ├── __init__.py
│   │   └── services/
│   │       ├── mlflow_docker_service.py
│   │       ├── mlflow_service.py
│   │       └── __init__.py
│   ├── mysqp_server/
│   │   ├── admin.py
│   │   ├── api.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── __init__.py
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   └── services/
│   │       └── mysqp_docker_service.py
│   ├── postgres_server/
│   │   ├── admin.py
│   │   ├── api.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── __init__.py
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   └── services/
│   │       └── postgres_docker_service.py
│   ├── rabbitmq_server/
│   │   ├── api.py
│   │   ├── apps.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── __init__.py
│   │   └── services/
│   │       ├── rabbitmq_docker_service.py
│   │       ├── rabbitmq_service.py
│   │       └── __init__.py
│   ├── redis_server/
│   │   ├── admin.py
│   │   ├── api.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── __init__.py
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   └── services/
│   │       └── redis_service.py
│   ├── srs_server/
│   │   ├── admin.py
│   │   ├── api.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── __init__.py
│   │   ├── migrations/
│   │   │   ├── 0001_initial.py
│   │   │   └── __init__.py
│   │   └── services/
│   │       ├── srs_docker_service.py
│   │       └── srs_service.py
│   ├── videoCap_server/
│   │   ├── admin.py
│   │   ├── admin_frame.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── models_no_batch.py
│   │   ├── tasks.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── __init__.py
│   │   ├── Commands/
│   │   │   └── check_thread.py
│   │   ├── migrations/
│   │   │   ├── 0001_initial.py
│   │   │   ├── 0002_videocapconfig_redis_client_and_more.py
│   │   │   ├── 0003_alter_currentframe_options_alter_currentframe_config_and_more.py
│   │   │   ├── 0004_currentvideoclip_aiinferenceresult.py
│   │   │   ├── 0005_cameralist.py
│   │   │   ├── 0006_alter_cameralist_options_and_more.py
│   │   │   ├── 0007_alter_cameralist_options_cameralist_camera_status.py
│   │   │   ├── 0008_cameralist_stream_upload_video_path.py
│   │   │   └── __init__.py
│   │   └── services/
│   │       ├── drawResult_service.py
│   │       ├── videoCap_service.py
│   │       └── videoCap_service_no_batch.py
│   └── visionAI_server/
│       ├── admin.py
│       ├── api.py
│       ├── api_db.py
│       ├── api_object.py
│       ├── apps.py
│       ├── models.py
│       ├── tests.py
│       ├── type_initial_config.rar
│       ├── urls.py
│       ├── views.py
│       ├── __init__.py
│       ├── API/
│       ├── migrations/
│       │   ├── 0001_initial.py
│       │   ├── 0002_visionaiconfig_delete_config.py
│       │   ├── 0003_remove_visionaiconfig_violation_threshold.py
│       │   ├── 0004_alter_detectedobject_entity_type_and_more.py
│       │   ├── 0005_keyframe_rtmp_url.py
│       │   └── __init__.py
│       ├── serializers/
│       │   └── serializer.py
│       ├── services/
│       │   ├── objectDetect_service.py
│       │   ├── violationDetect_service copy.py
│       │   ├── violationDetect_service.py
│       │   ├── violationDetect_service_full.py
│       │   ├── visionAI_db_service.py
│       │   └── utils.py
│       └── type_initial_config/
│           ├── entity_type.yaml
│           ├── role.yaml
│           ├── rule.yaml
│           └── scene_type.yaml
├── drawResult_server/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   ├── __init__.py
│   └── migrations/
│       └── __init__.py
├── extensions/
└── init_docker.sh
