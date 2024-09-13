import cv2
import yaml
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from django.db import transaction
from django.utils import timezone
from djangoFlex_servers.videoCap_server.models import VideoCapConfig    
from ..models import Rule, Violation, DetectedObject, Scene, KeyFrame, EntityType, SceneType, Role, PersonRole
from django.conf import settings
import redis
import random
import numpy as np
import time
import json
import pika
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings

logger = logging.getLogger(__name__)

class ViolationDetectService:
    def __init__(self):
        self.configs = {}
        self.rules = {}
        self.running = {}
        self.detect_threads = {}
        self.executor = None
        self.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        self._load_configs()
        self._load_rules()
        self._load_entity_types()
        self._load_scene_types()
        self._load_roles()
        logger.info("ViolationDetectService initialized")

    def _load_configs(self):
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = config
                self.running[config.rtmp_url] = False
            logger.info("Configurations loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")

    def _load_rules(self):
        try:
            self.rules = {rule.rule_code: rule for rule in Rule.objects.all()}
            logger.info("Rules loaded successfully")
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")

    def _load_entity_types(self):
        try:
            self.entity_types = {et.type_name: et for et in EntityType.objects.all()}
            logger.info("Entity types loaded successfully")
        except Exception as e:
            logger.error(f"Error loading entity types: {str(e)}")

    def _load_scene_types(self):
        try:
            self.scene_types = {st.type_name: st for st in SceneType.objects.all()}
            logger.info("Scene types loaded successfully")
        except Exception as e:
            logger.error(f"Error loading scene types: {str(e)}")

    def _load_roles(self):
        try:
            self.roles = {r.role_name: r for r in Role.objects.all()}
            logger.info("Roles loaded successfully")
        except Exception as e:
            logger.error(f"Error loading roles: {str(e)}")

    def start_service(self):
        logger.info("Starting ViolationDetectService")
        self.executor = ThreadPoolExecutor(max_workers=10)
        for rtmp_url in self.configs.keys():
            self.start_detection(rtmp_url)
        logger.info("ViolationDetectService started successfully")

    def stop_service(self):
        logger.info("Stopping ViolationDetectService")
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                self.stop_detection(rtmp_url)
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        logger.info("ThreadPoolExecutor shut down")
        logger.info("ViolationDetectService stopped successfully")

    def start_detection(self, rtmp_url):
        if rtmp_url in self.running and self.running[rtmp_url]:
            logger.info(f"Detection for {rtmp_url} is already running")
            return False, "Detection already running"

        config = self.configs.get(rtmp_url)
        if not config:
            logger.error(f"No configuration found for {rtmp_url}")
            return False, "No configuration found"

        self.running[rtmp_url] = True
        if self.executor is None or self.executor._shutdown:
            self.executor = ThreadPoolExecutor(max_workers=10)
        self.detect_threads[rtmp_url] = self.executor.submit(self._detect_loop, rtmp_url)

        logger.info(f"Detection started for {rtmp_url}")
        return True, "Detection started successfully"

    def stop_detection(self, rtmp_url):
        if rtmp_url not in self.running or not self.running[rtmp_url]:
            logger.warning(f"Detection for {rtmp_url} is not running")
            return False, "Detection not running"

        self.running[rtmp_url] = False
        if rtmp_url in self.detect_threads:
            self.detect_threads[rtmp_url].result()
            del self.detect_threads[rtmp_url]
            logger.info(f"Detection thread for {rtmp_url} stopped")

        logger.info(f"Detection stopped for {rtmp_url}")
        return True, "Detection stopped successfully"

    def _detect_loop(self, rtmp_url):
        logger.info(f"Detection loop started for {rtmp_url}")
        while self.running[rtmp_url]:
            frame_bytes = self.redis_client.get(f"video_cap_service:current_image:{rtmp_url}")
            if frame_bytes:
                frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
                self._process_frame(rtmp_url, frame)
            time.sleep(self.configs[rtmp_url].frame_interval)
        logger.info(f"Detection loop ended for {rtmp_url}")

    def _process_frame(self, rtmp_url, frame):
        time.sleep(2)
        config = self.configs[rtmp_url]
        time_now = timezone.now()

        # Create a KeyFrame
        key_frame = KeyFrame.objects.create(
            rtmp_url=rtmp_url,
            frame_time=time_now,
            frame_index=0  # Implement a frame counter
        )

        # Perform object detection (simulated for this example)
        detected_objects = self._detect_objects(frame, key_frame)

        # Perform scene analysis (simulated)
        scene = self._analyze_scene(frame, key_frame)

        # Check for violations
        self._check_violations(detected_objects, scene, key_frame)

        # Generate the JSON message
        message = {
            "key_frame_id": key_frame.frame_id,
            "frame_time": key_frame.frame_time.isoformat(),
            "frame_index": key_frame.frame_index,
            "scenes": [
                {
                    "class": scene.scene_type.type_name,
                    "description": scene.description
                }
            ],
            "object_detected": self._format_detected_objects(key_frame),
            "violations": self._format_violations(key_frame)
        }

        # Publish the message to RabbitMQ
        # Check if any violation has severity > 3
        high_severity_violations = [v for v in key_frame.violation_set.all() if v.rule.severity_level < 3]
        
        if high_severity_violations:
            self._publish_to_rabbitmq(message)
        else:
            logger.info("No high severity violations detected, skipping RabbitMQ publish")

        logger.info(f"Processed frame for {rtmp_url} and published to RabbitMQ")

    def _format_detected_objects(self, key_frame):
        formatted_objects = {}
        for obj in key_frame.detectedobject_set.all():
            if obj.entity_type.type_name not in formatted_objects:
                formatted_objects[obj.entity_type.type_name] = {
                    "entity_type": obj.entity_type.type_name,
                    "object_details": []
                }
            formatted_objects[obj.entity_type.type_name]["object_details"].append({
                "object_id": obj.detected_object_id,
                "object_class": obj.specific_type,
                "confidence_score": obj.confidence_score,
                "bounding_box": obj.bounding_box,
                "segmentation": obj.segmentation,
                "re_id": obj.re_id
            })
        return list(formatted_objects.values())

    def _format_violations(self, key_frame):
        return [
            {
                "violation_id": v.violation_id,
                "violation_type": {
                    "violation_code": v.rule.rule_code,
                    "violation_description": v.rule.description,
                    "severity_level": v.rule.severity_level
                },
                "entity_type": v.detected_object.entity_type.type_name if v.detected_object else "Scene",
                "entity_id": v.detected_object.detected_object_id if v.detected_object else v.scene.scene_id,
                "occurrence_time": v.occurrence_time.isoformat()
            }
            for v in key_frame.violation_set.all()
        ]

    def _publish_to_rabbitmq(self, message):
        try:
            credentials = pika.PlainCredentials(settings.SERVERS_CONFIG['RABBITMQ_USER'], settings.SERVERS_CONFIG['RABBITMQ_PASSWORD'])
            parameters = pika.ConnectionParameters(
                host=settings.SERVERS_CONFIG['RABBITMQ_HOST'],
                port=settings.SERVERS_CONFIG['RABBITMQ_PORT'],
                virtual_host=settings.SERVERS_CONFIG['RABBITMQ_VHOST'],
                credentials=credentials
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue='vision_ai_results')
            channel.basic_publish(
                exchange='',
                routing_key='vision_ai_results',
                body=json.dumps(message)
            )
            connection.close()
            logger.info("Message published to RabbitMQ successfully")
        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {str(e)}")

    def _detect_objects(self, frame, key_frame):
        # Simulate object detection
        # In a real implementation, you would use a pre-trained model or API
        detected_objects = []
        for _ in range(random.randint(1, 5)):
            object_type = random.choice(list(self.entity_types.values()))
            detected_objects.append(DetectedObject.objects.create(
                frame=key_frame,
                entity_type=object_type,
                specific_type=object_type.type_name,
                confidence_score=random.uniform(0.7, 1.0),
                bounding_box={'x': random.randint(0, 100), 'y': random.randint(0, 100), 'width': random.randint(10, 50), 'height': random.randint(10, 50)},
                segmentation=[],  # Add segmentation data if available
                re_id=random.randint(1, 1000)
            ))
        return detected_objects

    def _analyze_scene(self, frame, key_frame):
        # Simulate scene analysis
        scene_type = random.choice(list(self.scene_types.values()))
        return Scene.objects.create(
            frame=key_frame,
            scene_type=scene_type,
            description=f"Detected {scene_type.type_name}"
        )

    def _check_violations(self, detected_objects, scene, key_frame):
        for rule in self.rules.values():
            # Simplified violation detection logic
            if random.random() < 0.1:  # 10% chance of violation for demonstration
                violated_object = random.choice(detected_objects) if detected_objects else None
                Violation.objects.create(
                    rule=rule,
                    frame=key_frame,
                    detected_object=violated_object,
                    scene=scene,
                    occurrence_time=timezone.now()
                )
                logger.info(f"Violation detected for rule: {rule.rule_code}")

                # Assign roles to detected objects (if applicable)
                if violated_object:
                    role = random.choice(list(self.roles.values()))
                    PersonRole.objects.create(
                        detected_object=violated_object,
                        role=role
                    )
                    logger.info(f"Assigned role {role.role_name} to detected object")

    def update_rules(self):
        self._load_rules()
        for rtmp_url in self.running.keys():
            if self.running[rtmp_url]:
                self.stop_detection(rtmp_url)
                self.start_detection(rtmp_url)
        logger.info("Rules updated and all detection threads restarted")

    def update_config(self, rtmp_url):
        if rtmp_url in self.configs:
            self.configs[rtmp_url] = VideoCapConfig.objects.get(rtmp_url=rtmp_url)
            if self.running[rtmp_url]:
                self.stop_detection(rtmp_url)
                self.start_detection(rtmp_url)
            logger.info(f"Configuration updated for {rtmp_url}")
        else:
            logger.warning(f"No configuration found for {rtmp_url}")

    def __del__(self):
        logger.info("ViolationDetectService destructor called")
        self.stop_service()
        logger.info("ViolationDetectService destroyed")

    def list_running_threads(self):
        running_threads = []
        for rtmp_url, future in self.detect_threads.items():
            running_threads.append({
                'rtmp_url': rtmp_url,
                'is_running': self.running[rtmp_url],
                'is_done': future.done() if future else True
            })
        return running_threads
    
