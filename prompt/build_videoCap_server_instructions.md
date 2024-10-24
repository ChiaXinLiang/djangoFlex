# Server Overview
This server, named `video_cap_server`, is part of the `djangoFlex` project. It specializes in multi-camera video capture and processing. The server comprises two primary services:
1. **video_capture_service**: Captures frames from multiple cameras concurrently. The frame should save in the 
2. **draw_result_service**: This service obtain the frame from 
Together, these services form a robust video processing pipeline, enabling real-time capture and visualization of multiple video streams.


# Models
## VideoCapConfig Model
### Fields
- `rtmp_url`: The URL of the RTMP stream.
- `is_active`: A boolean indicating whether the stream is active.
- `redis_client`: The Redis client instance.

## CurrentFrame Model
### Fields
- `rtmp_url`: The URL of the RTMP stream.
- `frame`: The current frame of the video stream.
- `timestamp`: The timestamp of the current frame.

## KeyFrame Model
### Fields
- `rtmp_url`: The URL of the RTMP stream.
- `frame_time`: The timestamp of the key frame.
- `frame_index`: The index of the key frame.

## DetectedObject Model
### Fields
- `frame`: The key frame that the object was detected in.
- `entity_type`: The type of entity detected (e.g. person, car, etc.).
- `specific_type`: The specific type of entity detected (e.g. pedestrian, vehicle, etc.).
- `confidence_score`: The confidence score of the detection.
- `bounding_box`: The bounding box coordinates of the detected object.
- `segmentation`: The segmentation data of the detected object.
- `re_id`: The re-identification ID of the detected object.

## Scene Model
### Fields
- `frame`: The key frame that the scene was detected in.
- `scene_type`: The type of scene detected (e.g. indoor, outdoor, etc.).
- `description`: A description of the scene.

## Violation Model
### Fields
- `rule`: The rule that was violated.
- `frame`: The key frame that the violation occurred in.
- `detected_object`: The detected object that caused the violation.
- `scene`: The scene that the violation occurred in.
- `occurrence_time`: The timestamp of the violation.


# Feature Requirements

1. Multi-camera video capture and real-time processing
2. Frame annotation and overlay capabilities
3. Efficient handling of various video stream sources
```


# Relevant docs

- Django documentation: https://docs.djangoproject.com/
- RabbitMQ documentation: https://www.rabbitmq.com/documentation.html
- PostgreSQL documentation: https://www.postgresql.org/docs/
- Redis documentation: https://redis.io/documentation
- MLflow documentation: https://www.mlflow.org/docs/latest/index.html
- Celery documentation: https://docs.celeryproject.org/

# Current File Structure
djangoFlex/
├── djangoFlex_servers/
│   └── videoCap_server/
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── models_no_batch.py
│       ├── tasks.py
│       ├── tests.py
│       ├── urls.py
│       ├── views.py
│       ├── __init__.py
│       ├── Commands/
│       │   └── check_thread.py
│       └── services/
│           ├── drawResult_service.py
│           ├── videoCap_service.py
│           └── videoCap_service_no_batch.py
