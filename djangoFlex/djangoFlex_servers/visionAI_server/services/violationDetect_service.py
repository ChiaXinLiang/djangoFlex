import cv2
import yaml
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from django.db import transaction
from django.utils import timezone
from djangoFlex_servers.videoCap_server.models import VideoCapConfig    
from ..models import  Rule, Violation, DetectedObject, Scene, KeyFrame
from django.conf import settings
import redis
import random
import numpy as np

logger = logging.getLogger(__name__)

class ViolationDetectService:
    def __init__(self):
        self.configs = {}
        self.rules = {}
        self.running = {}
        self.detect_threads = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        self._load_configs()
        self._load_rules()
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
            db_rules = Rule.objects.all()
            if db_rules.exists():
                for rule in db_rules:
                    self.rules[rule.rule_code] = rule
            else:
                with open(settings.BASE_DIR / 'rule.yaml', 'r') as file:
                    yaml_rules = yaml.safe_load(file)
                    for rule_data in yaml_rules:
                        rule = Rule.objects.create(**rule_data)
                        self.rules[rule.rule_code] = rule
            logger.info("Rules loaded successfully")
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")

    def start_service(self):
        logger.info("Starting ViolationDetectService")
        for rtmp_url in self.configs.keys():
            self.start_detection(rtmp_url)
        logger.info("ViolationDetectService started successfully")

    def stop_service(self):
        logger.info("Stopping ViolationDetectService")
        for rtmp_url in list(self.running.keys()):
            if self.running[rtmp_url]:
                self.stop_detection(rtmp_url)
        self.executor.shutdown(wait=True)
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
        # Here we implement a simplified violation detection logic
        # that randomly selects a rule and creates a violation
        config = self.configs[rtmp_url]
        
        # Create a KeyFrame
        key_frame = KeyFrame.objects.create(
            frame_time=timezone.now(),
            frame_index=0  # You might want to implement a frame counter
        )

        # Randomly select a rule
        if self.rules:
            random_rule = random.choice(list(self.rules.values()))

            # Create a violation with the random rule
            Violation.objects.create(
                rule=random_rule,
                frame=key_frame,
                detected_object=None,  # We're not detecting objects in this simplified version
                scene=None  # We're not detecting scenes in this simplified version
            )

            logger.info(f"Created violation for rule: {random_rule.rule_code}")
        else:
            logger.warning("No rules available to create violations")

    def _detect_objects(self, frame):
        # Placeholder for object detection
        return []

    def _detect_scene(self, frame):
        # Placeholder for scene detection
        return None

    def _check_violation(self, rule, detected_objects, scene):
        # Placeholder for violation checking
        return False

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
        self.stop_server()
        logger.info("ViolationDetectService destroyed")

    def list_running_threads(self):
        running_threads = []
        for rtmp_url, future in self.detect_threads.items():
            running_threads.append({
                'rtmp_url': rtmp_url,
                'is_running': self.running[rtmp_url],
                'is_done': future.done()
            })
        return running_threads