"""
Camera Configuration Loader
Loads camera configurations from the database for the FTS system
"""

from typing import List, Optional
from dataclasses import dataclass
import logging

from db.db_manager import DatabaseManager
from db.db_models import CameraConfig as DBCameraConfig, Tripwire as DBTripwire

logger = logging.getLogger(__name__)

@dataclass
class TripwireConfig:
    """Tripwire configuration for FTS system"""
    position: float
    spacing: float
    direction: str
    name: str
    detection_type: str = "entry"
    is_active: bool = True

@dataclass
class CameraConfig:
    """Camera configuration for FTS system"""
    camera_id: int
    gpu_id: int
    camera_type: str
    camera_name: str
    ip_address: str
    stream_url: str
    username: Optional[str]
    password: Optional[str]
    tripwires: List[TripwireConfig]
    resolution: tuple
    fps: int
    is_active: bool = True

class CameraConfigLoader:
    """
    Loads camera configurations from the database for the FTS system
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def load_active_cameras(self) -> List[CameraConfig]:
        """
        Load all active camera configurations from the database
        
        Returns:
            List of active camera configurations
        """
        try:
            # Get all active cameras from database
            db_cameras = self.db_manager.get_active_cameras()
            
            camera_configs = []
            for db_camera in db_cameras:
                # Convert database camera to FTS camera config
                camera_config = self._convert_db_camera_to_fts_config(db_camera)
                if camera_config:
                    camera_configs.append(camera_config)
            
            logger.info(f"Loaded {len(camera_configs)} active camera configurations")
            return camera_configs
            
        except Exception as e:
            logger.error(f"Error loading active cameras: {e}")
            return []
    
    def load_all_cameras(self) -> List[CameraConfig]:
        """
        Load all camera configurations from the database
        
        Returns:
            List of all camera configurations
        """
        try:
            # Get all cameras from database
            db_cameras = self.db_manager.get_all_cameras()
            
            camera_configs = []
            for db_camera in db_cameras:
                # Convert database camera to FTS camera config
                camera_config = self._convert_db_camera_to_fts_config(db_camera)
                if camera_config:
                    camera_configs.append(camera_config)
            
            logger.info(f"Loaded {len(camera_configs)} camera configurations")
            return camera_configs
            
        except Exception as e:
            logger.error(f"Error loading all cameras: {e}")
            return []
    
    def load_camera_by_id(self, camera_id: int) -> Optional[CameraConfig]:
        """
        Load a specific camera configuration by ID
        
        Args:
            camera_id: Camera ID to load
            
        Returns:
            Camera configuration or None if not found
        """
        try:
            db_camera = self.db_manager.get_camera(camera_id)
            if not db_camera:
                return None
            
            return self._convert_db_camera_to_fts_config(db_camera)
            
        except Exception as e:
            logger.error(f"Error loading camera {camera_id}: {e}")
            return None
    
    def _convert_db_camera_to_fts_config(self, db_camera: DBCameraConfig) -> Optional[CameraConfig]:
        """
        Convert database camera model to FTS camera configuration
        
        Args:
            db_camera: Database camera model
            
        Returns:
            FTS camera configuration or None if conversion fails
        """
        try:
            # Get tripwires for this camera
            db_tripwires = self.db_manager.get_camera_tripwires(db_camera.camera_id)
            
            # Convert tripwires
            tripwires = []
            for db_tripwire in db_tripwires:
                if db_tripwire.is_active:  # Only include active tripwires
                    tripwire = TripwireConfig(
                        position=db_tripwire.position,
                        spacing=db_tripwire.spacing,
                        direction=db_tripwire.direction,
                        name=db_tripwire.name,
                        detection_type=db_tripwire.detection_type,
                        is_active=db_tripwire.is_active
                    )
                    tripwires.append(tripwire)
            
            # Build stream URL if not provided
            stream_url = db_camera.stream_url
            if not stream_url and db_camera.ip_address:
                # Default RTSP stream URL
                stream_url = f"rtsp://{db_camera.ip_address}:554/stream1"
            
            # Create FTS camera configuration
            camera_config = CameraConfig(
                camera_id=db_camera.camera_id,
                gpu_id=db_camera.gpu_id,
                camera_type=db_camera.camera_type,
                camera_name=db_camera.camera_name,
                ip_address=db_camera.ip_address,
                stream_url=stream_url,
                username=db_camera.username,
                password=db_camera.password,
                tripwires=tripwires,
                resolution=(db_camera.resolution_width, db_camera.resolution_height),
                fps=db_camera.fps,
                is_active=db_camera.is_active
            )
            
            return camera_config
            
        except Exception as e:
            logger.error(f"Error converting database camera {db_camera.camera_id}: {e}")
            return None
    
    def get_camera_stream_url(self, camera_id: int) -> Optional[str]:
        """
        Get the stream URL for a specific camera
        
        Args:
            camera_id: Camera ID
            
        Returns:
            Stream URL or None if not found
        """
        try:
            db_camera = self.db_manager.get_camera(camera_id)
            if not db_camera:
                return None
            
            if db_camera.stream_url:
                return db_camera.stream_url
            elif db_camera.ip_address:
                # Default RTSP stream URL
                return f"rtsp://{db_camera.ip_address}:554/stream1"
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting stream URL for camera {camera_id}: {e}")
            return None
    
    def refresh_camera_configs(self) -> List[CameraConfig]:
        """
        Refresh and reload all active camera configurations
        
        Returns:
            List of refreshed active camera configurations
        """
        logger.info("Refreshing camera configurations from database")
        return self.load_active_cameras()
    
    def validate_camera_config(self, camera_config: CameraConfig) -> bool:
        """
        Validate a camera configuration
        
        Args:
            camera_config: Camera configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not camera_config.camera_id:
                logger.error(f"Camera config missing camera_id")
                return False
            
            if not camera_config.camera_name:
                logger.error(f"Camera {camera_config.camera_id} missing camera_name")
                return False
            
            if not camera_config.stream_url and not camera_config.ip_address:
                logger.error(f"Camera {camera_config.camera_id} missing stream_url and ip_address")
                return False
            
            # Validate resolution
            if not camera_config.resolution or len(camera_config.resolution) != 2:
                logger.error(f"Camera {camera_config.camera_id} has invalid resolution")
                return False
            
            # Validate FPS
            if camera_config.fps <= 0:
                logger.error(f"Camera {camera_config.camera_id} has invalid fps: {camera_config.fps}")
                return False
            
            # Validate tripwires
            for tripwire in camera_config.tripwires:
                if not (0.0 <= tripwire.position <= 1.0):
                    logger.error(f"Camera {camera_config.camera_id} tripwire {tripwire.name} has invalid position: {tripwire.position}")
                    return False
                
                if tripwire.direction not in ['horizontal', 'vertical']:
                    logger.error(f"Camera {camera_config.camera_id} tripwire {tripwire.name} has invalid direction: {tripwire.direction}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating camera config {camera_config.camera_id}: {e}")
            return False

# Convenience functions
def load_active_camera_configs() -> List[CameraConfig]:
    """
    Convenience function to load active camera configurations
    
    Returns:
        List of active camera configurations
    """
    loader = CameraConfigLoader()
    return loader.load_active_cameras()

def load_all_camera_configs() -> List[CameraConfig]:
    """
    Convenience function to load all camera configurations
    
    Returns:
        List of all camera configurations
    """
    loader = CameraConfigLoader()
    return loader.load_all_cameras()

def load_camera_config_by_id(camera_id: int) -> Optional[CameraConfig]:
    """
    Convenience function to load a specific camera configuration
    
    Args:
        camera_id: Camera ID to load
        
    Returns:
        Camera configuration or None if not found
    """
    loader = CameraConfigLoader()
    return loader.load_camera_by_id(camera_id)