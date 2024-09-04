import cv2
import numpy as np
from ..models import CurrentFrame
from django.utils import timezone
import threading

class ObjectDetectService:
    def __init__(self):
        self.mock_algorithm = MockAlgorithm()
        self.running = {}
        self.detect_threads = {}

    def start_server(self, rtmp_url):
        if rtmp_url in self.running and self.running[rtmp_url]:
            return False, "Server already running"

        self.running[rtmp_url] = True
        self.detect_threads[rtmp_url] = threading.Thread(target=self._detect_loop, args=(rtmp_url,))
        self.detect_threads[rtmp_url].start()

        return True, "Server started successfully"

    def stop_server(self, rtmp_url):
        if rtmp_url not in self.running or not self.running[rtmp_url]:
            return False, "Server not running"

        self.running[rtmp_url] = False
        if rtmp_url in self.detect_threads:
            self.detect_threads[rtmp_url].join()
            del self.detect_threads[rtmp_url]

        return True, "Server stopped successfully"

    def _detect_loop(self, rtmp_url):
        while self.running[rtmp_url]:
            detected_objects = self.detect_objects(rtmp_url)
            # Here you can process or store the detected objects as needed
            # For example, you might want to save them to a database or send them to another service

    def detect_objects(self, rtmp_url):
        """
        Detects objects in the current frame from videoCap_service using a mock algorithm.
        """
        # Get the most recent frame from the database for the specific rtmp_url
        current_frame = CurrentFrame.objects.filter(config__rtmp_url=rtmp_url).order_by('-timestamp').first()
        
        if current_frame is None:
            return None

        # Convert the frame data to a numpy array
        nparr = np.frombuffer(current_frame.frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Apply the mock algorithm to detect objects
        detected_objects = self.mock_algorithm.detect(frame)
        
        return detected_objects

class MockAlgorithm:
    def detect(self, frame):
        """
        Mock algorithm to simulate object detection.
        """
        # Simulate object detection by adding rectangles to the frame
        # This is a placeholder for actual object detection logic
        detected_objects = []
        for _ in range(5):  # Simulate detection of 5 objects
            x, y = np.random.randint(0, frame.shape[1]), np.random.randint(0, frame.shape[0])
            w, h = np.random.randint(50, 100), np.random.randint(50, 100)
            confidence = np.random.uniform(0.5, 1.0)
            class_id = np.random.randint(0, 10)  # Assuming 10 different classes
            detected_objects.append({
                'bbox': (x, y, w, h),
                'confidence': confidence,
                'class_id': class_id
            })
        return detected_objects
