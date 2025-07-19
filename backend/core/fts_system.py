"""
Face Tracking System (FTS) - Core Module
Handles face detection, recognition, and attendance tracking
"""

import cv2
import numpy as np
import threading
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import queue

from db.db_manager import DatabaseManager
from utils.camera_config_loader import load_active_camera_configs, CameraConfig, TripwireConfig
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DetectedFace:
    """Detected face information"""
    employee_id: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    timestamp: datetime

@dataclass
class SystemStatus:
    """System status information"""
    is_running: bool
    uptime: float
    cam_count: int
    faces_detected: int
    attendance_count: int
    load: float

class FaceTrackingPipeline:
    """
    Main face tracking pipeline for real-time face detection and recognition
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.is_running = False
        self.start_time = None
        self.camera_threads = {}
        self.detected_faces = queue.Queue(maxsize=100)
        self.system_stats = {
            'faces_detected': 0,
            'attendance_count': 0,
            'cameras_active': 0
        }
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._stop_event = threading.Event()
        
    def start(self):
        """Start the face tracking system"""
        if self.is_running:
            logger.warning("Face tracking system is already running")
            return False
        
        try:
            logger.info("Starting Face Tracking System...")
            
            # Load camera configurations from database
            cameras = load_active_camera_configs()
            if not cameras:
                logger.warning("No active cameras found in database")
                return False
            
            self.is_running = True
            self.start_time = time.time()
            self._stop_event.clear()
            
            # Start camera threads
            for camera in cameras:
                if self._start_camera_thread(camera):
                    self.system_stats['cameras_active'] += 1
            
            logger.info(f"Face tracking system started with {self.system_stats['cameras_active']} cameras")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start face tracking system: {e}")
            self.is_running = False
            return False
    
    def stop(self):
        """Stop the face tracking system"""
        if not self.is_running:
            logger.warning("Face tracking system is not running")
            return False
        
        try:
            logger.info("Stopping Face Tracking System...")
            
            # Signal all threads to stop
            self._stop_event.set()
            self.is_running = False
            
            # Wait for camera threads to finish
            for camera_id, thread in self.camera_threads.items():
                thread.join(timeout=5.0)
                logger.info(f"Stopped camera thread {camera_id}")
            
            self.camera_threads.clear()
            self.system_stats['cameras_active'] = 0
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            logger.info("Face tracking system stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping face tracking system: {e}")
            return False
    
    def _start_camera_thread(self, camera: CameraConfig) -> bool:
        """Start a camera processing thread"""
        try:
            thread = threading.Thread(
                target=self._camera_worker,
                args=(camera,),
                daemon=True,
                name=f"camera_{camera.camera_id}"
            )
            
            self.camera_threads[camera.camera_id] = thread
            thread.start()
            
            logger.info(f"Started camera thread for camera {camera.camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start camera thread for camera {camera.camera_id}: {e}")
            return False
    
    def _camera_worker(self, camera: CameraConfig):
        """Worker function for camera processing"""
        logger.info(f"Camera worker started for camera {camera.camera_id}")
        
        cap = None
        frame_count = 0
        
        try:
            # Initialize camera
            if camera.stream_url:
                cap = cv2.VideoCapture(camera.stream_url)
            else:
                cap = cv2.VideoCapture(camera.camera_id)
            
            if not cap.isOpened():
                logger.error(f"Failed to open camera {camera.camera_id}")
                return
            
            # Set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera.resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera.resolution[1])
            cap.set(cv2.CAP_PROP_FPS, camera.fps)
            
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from camera {camera.camera_id}")
                    time.sleep(0.1)
                    continue
                
                frame_count += 1
                
                # Process every 10th frame to reduce CPU load
                if frame_count % 10 == 0:
                    self._process_frame(frame, camera)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            logger.error(f"Error in camera worker for camera {camera.camera_id}: {e}")
        
        finally:
            if cap:
                cap.release()
            logger.info(f"Camera worker stopped for camera {camera.camera_id}")
    
    def _process_frame(self, frame: np.ndarray, camera: CameraConfig):
        """Process a single frame for face detection"""
        try:
            # Mock face detection (replace with actual face recognition)
            # In a real implementation, this would use InsightFace or similar
            faces = self._mock_face_detection(frame, camera)
            
            for face in faces:
                # Add to detected faces queue
                if not self.detected_faces.full():
                    self.detected_faces.put(face)
                
                # Record attendance
                self._record_attendance(face, camera)
                
                self.system_stats['faces_detected'] += 1
                
        except Exception as e:
            logger.error(f"Error processing frame from camera {camera.camera_id}: {e}")
    
    def _mock_face_detection(self, frame: np.ndarray, camera: CameraConfig) -> List[DetectedFace]:
        """Mock face detection for demonstration"""
        # This is a placeholder - replace with actual face recognition
        # For now, randomly detect faces for testing
        import random
        
        if random.random() < 0.1:  # 10% chance of detecting a face
            # Mock detected face
            face = DetectedFace(
                employee_id=f"EMP{random.randint(1, 3):03d}",
                confidence=random.uniform(0.7, 0.95),
                bbox=(100, 100, 200, 200),
                timestamp=datetime.now()
            )
            return [face]
        
        return []
    
    def _record_attendance(self, face: DetectedFace, camera: CameraConfig):
        """Record attendance for detected face"""
        try:
            # Check if this employee already has recent attendance
            recent_attendance = self.db_manager.get_latest_attendance_by_employee(
                face.employee_id, hours_back=1
            )
            
            if recent_attendance:
                # Don't record duplicate attendance within 1 hour
                return
            
            # Record new attendance
            success = self.db_manager.log_attendance(
                employee_id=face.employee_id,
                camera_id=camera.camera_id,
                event_type='entry',
                confidence_score=face.confidence,
                work_status='working',
                notes=f"Auto-detected via camera {camera.camera_id}"
            )
            
            if success:
                self.system_stats['attendance_count'] += 1
                logger.info(f"Recorded attendance for {face.employee_id} with confidence {face.confidence:.3f}")
            
        except Exception as e:
            logger.error(f"Error recording attendance for {face.employee_id}: {e}")
    
    def get_status(self) -> SystemStatus:
        """Get current system status"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return SystemStatus(
            is_running=self.is_running,
            uptime=uptime,
            cam_count=self.system_stats['cameras_active'],
            faces_detected=self.system_stats['faces_detected'],
            attendance_count=self.system_stats['attendance_count'],
            load=0.3  # Mock load value
        )
    
    def get_live_faces(self) -> List[Dict]:
        """Get currently detected faces"""
        faces = []
        
        # Get all faces from queue without blocking
        while not self.detected_faces.empty():
            try:
                face = self.detected_faces.get_nowait()
                faces.append({
                    'employee_id': face.employee_id,
                    'confidence': face.confidence,
                    'bbox': face.bbox,
                    'timestamp': face.timestamp.isoformat()
                })
            except queue.Empty:
                break
        
        return faces
    
    def reload_camera_configurations(self):
        """Reload camera configurations from database"""
        if not self.is_running:
            logger.info("System not running, configurations will be loaded on next start")
            return
        
        logger.info("Reloading camera configurations...")
        
        # Stop current cameras
        self._stop_event.set()
        for thread in self.camera_threads.values():
            thread.join(timeout=5.0)
        
        self.camera_threads.clear()
        self.system_stats['cameras_active'] = 0
        
        # Restart with new configurations
        self._stop_event.clear()
        cameras = load_active_camera_configs()
        
        for camera in cameras:
            if self._start_camera_thread(camera):
                self.system_stats['cameras_active'] += 1
        
        logger.info(f"Reloaded {self.system_stats['cameras_active']} camera configurations")

# Global system instance
system_instance: Optional[FaceTrackingPipeline] = None

def get_system_instance() -> FaceTrackingPipeline:
    """Get or create the global system instance"""
    global system_instance
    if system_instance is None:
        system_instance = FaceTrackingPipeline()
    return system_instance

def start_tracking_service() -> bool:
    """Start the face tracking service"""
    system = get_system_instance()
    return system.start()

def shutdown_tracking_service() -> bool:
    """Shutdown the face tracking service"""
    system = get_system_instance()
    return system.stop()

def get_system_status() -> Dict[str, Any]:
    """Get system status"""
    system = get_system_instance()
    status = system.get_status()
    
    return {
        'is_running': status.is_running,
        'uptime': status.uptime,
        'cam_count': status.cam_count,
        'faces_detected': status.faces_detected,
        'attendance_count': status.attendance_count,
        'load': status.load
    }

def get_live_faces() -> List[Dict]:
    """Get live detected faces"""
    system = get_system_instance()
    return system.get_live_faces()

def get_attendance_data() -> List[Dict]:
    """Get recent attendance data"""
    try:
        db_manager = DatabaseManager()
        records = db_manager.get_attendance_records(limit=50)
        
        return [{
            'id': record.id,
            'employee_id': record.employee_id,
            'timestamp': record.timestamp.isoformat(),
            'event_type': getattr(record, 'event_type', 'entry'),
            'confidence_score': record.confidence_score
        } for record in records]
        
    except Exception as e:
        logger.error(f"Error getting attendance data: {e}")
        return []

def get_logs(limit: int = 100) -> List[Dict]:
    """Get system logs"""
    # Mock logs for now
    return [
        {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': 'System running normally',
            'component': 'FTS'
        }
    ]

def generate_mjpeg(camera_id: int):
    """Generate MJPEG stream for camera"""
    # Mock MJPEG stream
    import time
    
    while True:
        # Create a simple test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :] = [50, 100, 150]  # Blue background
        
        # Add timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Camera {camera_id} - {timestamp}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Encode frame
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(1/30)  # 30 FPS

@property
def is_tracking_running() -> bool:
    """Check if tracking system is running"""
    system = get_system_instance()
    return system.is_running

def reload_embeddings_and_rebuild_index():
    """Reload embeddings and rebuild index"""
    logger.info("Reloading embeddings and rebuilding index")
    # Implementation for reloading embeddings
    pass