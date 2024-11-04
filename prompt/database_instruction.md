# Models Outline

The following models are used in the `video_cap_server` to manage video capture and processing:

**VideoCapConfig Model**

- `rtmp_url`: The URL of the RTMP stream.
- `is_active`: A boolean indicating whether the stream is active.
- `redis_client`: The Redis client instance.

**CurrentFrame Model**

- `rtmp_url`: The URL of the RTMP stream.
- `frame`: The current frame of the video stream.
- `timestamp`: The timestamp of the current frame.

**KeyFrame Model**

- `rtmp_url`: The URL of the RTMP stream.
- `frame_time`: The timestamp of the key frame.
- `frame_index`: The index of the key frame.

**DetectedObject Model**

- `frame`: The key frame that the object was detected in.
- `entity_type`: The type of entity detected (e.g. person, car, etc.).
- `specific_type`: The specific type of entity detected (e.g. pedestrian, vehicle, etc.).
- `confidence_score`: The confidence score of the detection.
- `bounding_box`: The bounding box coordinates of the detected object.
- `segmentation`: The segmentation data of the detected object.
- `re_id`: The re-identification ID of the detected object.

