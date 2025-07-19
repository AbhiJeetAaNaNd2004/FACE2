"""
Camera Management API Router
Provides endpoints for camera discovery, configuration, and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.schemas import (
    CurrentUser, MessageResponse,
    CameraDiscoveryRequest, CameraDiscoveryResponse, CameraDiscoveryResult,
    CameraConfigurationRequest, CameraActivationRequest,
    CameraInfo, CameraListResponse, CameraStatusResponse,
    CameraCreate, CameraUpdate, TripwireCreate, TripwireUpdate, Tripwire
)
from app.security import require_admin_or_above, require_super_admin
from db.db_manager import DatabaseManager
from utils.camera_discovery import discover_cameras_on_network, CameraInfo as DiscoveredCameraInfo
from utils.logging import get_logger

router = APIRouter(prefix="/cameras", tags=["Camera Management"])
logger = get_logger(__name__)

# Background task storage for discovery operations
discovery_tasks = {}

@router.post("/discover", response_model=CameraDiscoveryResponse)
async def discover_cameras(
    request: CameraDiscoveryRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Discover cameras on the network using ONVIF and port scanning
    (Super Admin only)
    """
    try:
        start_time = time.time()
        
        # Perform camera discovery
        discovered_cameras = await discover_cameras_on_network(
            network_range=request.network_range,
            timeout=request.timeout
        )
        
        discovery_time = time.time() - start_time
        
        # Convert to response format
        camera_results = []
        for camera in discovered_cameras:
            camera_results.append(CameraDiscoveryResult(
                ip_address=camera.ip_address,
                port=camera.port,
                manufacturer=camera.manufacturer,
                model=camera.model,
                firmware_version=camera.firmware_version,
                stream_urls=camera.stream_urls,
                onvif_supported=camera.onvif_supported,
                device_service_url=camera.device_service_url,
                media_service_url=camera.media_service_url
            ))
        
        # Store discovered cameras in database
        if camera_results:
            background_tasks.add_task(
                _store_discovered_cameras,
                [camera.__dict__ for camera in discovered_cameras]
            )
        
        logger.info(f"Discovered {len(camera_results)} cameras in {discovery_time:.2f}s")
        
        return CameraDiscoveryResponse(
            discovered_cameras=camera_results,
            total_discovered=len(camera_results),
            discovery_time=discovery_time,
            network_range=request.network_range
        )
        
    except Exception as e:
        logger.error(f"Camera discovery failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Camera discovery failed: {str(e)}"
        )

@router.get("/", response_model=CameraListResponse)
async def get_cameras(
    status_filter: Optional[str] = None,
    active_only: bool = False,
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get list of all cameras with optional filtering
    (Admin+ only)
    """
    try:
        db_manager = DatabaseManager()
        
        if active_only:
            cameras = db_manager.get_active_cameras()
        elif status_filter:
            cameras = db_manager.get_cameras_by_status(status_filter)
        else:
            cameras = db_manager.get_all_cameras()
        
        # Convert to response format
        camera_infos = []
        for camera in cameras:
            tripwires = db_manager.get_camera_tripwires(camera.camera_id)
            camera_info = CameraInfo(
                id=camera.id,
                camera_id=camera.camera_id,
                camera_name=camera.camera_name,
                camera_type=camera.camera_type,
                ip_address=camera.ip_address,
                stream_url=camera.stream_url,
                location_description=camera.location_description,
                resolution_width=camera.resolution_width,
                resolution_height=camera.resolution_height,
                fps=camera.fps,
                gpu_id=camera.gpu_id,
                manufacturer=camera.manufacturer,
                model=camera.model,
                firmware_version=camera.firmware_version,
                onvif_supported=camera.onvif_supported,
                status=camera.status,
                is_active=camera.is_active,
                created_at=camera.created_at,
                updated_at=camera.updated_at,
                tripwires=[Tripwire(
                    id=t.id,
                    camera_id=t.camera_id,
                    name=t.name,
                    position=t.position,
                    spacing=t.spacing,
                    direction=t.direction,
                    detection_type=t.detection_type,
                    is_active=t.is_active,
                    created_at=t.created_at,
                    updated_at=t.updated_at
                ) for t in tripwires]
            )
            camera_infos.append(camera_info)
        
        active_count = len([c for c in cameras if c.is_active])
        inactive_count = len(cameras) - active_count
        
        return CameraListResponse(
            cameras=camera_infos,
            total_count=len(cameras),
            active_count=active_count,
            inactive_count=inactive_count
        )
        
    except Exception as e:
        logger.error(f"Error getting cameras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cameras: {str(e)}"
        )

@router.get("/{camera_id}", response_model=CameraInfo)
async def get_camera(
    camera_id: int,
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get detailed information about a specific camera
    (Admin+ only)
    """
    try:
        db_manager = DatabaseManager()
        camera = db_manager.get_camera(camera_id)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        
        tripwires = db_manager.get_camera_tripwires(camera_id)
        
        return CameraInfo(
            id=camera.id,
            camera_id=camera.camera_id,
            camera_name=camera.camera_name,
            camera_type=camera.camera_type,
            ip_address=camera.ip_address,
            stream_url=camera.stream_url,
            location_description=camera.location_description,
            resolution_width=camera.resolution_width,
            resolution_height=camera.resolution_height,
            fps=camera.fps,
            gpu_id=camera.gpu_id,
            manufacturer=camera.manufacturer,
            model=camera.model,
            firmware_version=camera.firmware_version,
            onvif_supported=camera.onvif_supported,
            status=camera.status,
            is_active=camera.is_active,
            created_at=camera.created_at,
            updated_at=camera.updated_at,
            tripwires=[Tripwire(
                id=t.id,
                camera_id=t.camera_id,
                name=t.name,
                position=t.position,
                spacing=t.spacing,
                direction=t.direction,
                detection_type=t.detection_type,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at
            ) for t in tripwires]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving camera: {str(e)}"
        )

@router.post("/", response_model=CameraInfo)
async def create_camera(
    camera_data: CameraCreate,
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Create a new camera configuration
    (Super Admin only)
    """
    try:
        db_manager = DatabaseManager()
        
        # Convert to dict for database manager
        camera_dict = camera_data.dict()
        
        camera = db_manager.create_camera(camera_dict)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create camera"
            )
        
        return CameraInfo(
            id=camera.id,
            camera_id=camera.camera_id,
            camera_name=camera.camera_name,
            camera_type=camera.camera_type,
            ip_address=camera.ip_address,
            stream_url=camera.stream_url,
            location_description=camera.location_description,
            resolution_width=camera.resolution_width,
            resolution_height=camera.resolution_height,
            fps=camera.fps,
            gpu_id=camera.gpu_id,
            manufacturer=camera.manufacturer,
            model=camera.model,
            firmware_version=camera.firmware_version,
            onvif_supported=camera.onvif_supported,
            status=camera.status,
            is_active=camera.is_active,
            created_at=camera.created_at,
            updated_at=camera.updated_at,
            tripwires=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating camera: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating camera: {str(e)}"
        )

@router.put("/{camera_id}", response_model=CameraInfo)
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Update camera configuration
    (Super Admin only)
    """
    try:
        db_manager = DatabaseManager()
        
        # Convert to dict, excluding None values
        update_dict = {k: v for k, v in camera_data.dict().items() if v is not None}
        
        camera = db_manager.update_camera(camera_id, update_dict)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        
        tripwires = db_manager.get_camera_tripwires(camera_id)
        
        return CameraInfo(
            id=camera.id,
            camera_id=camera.camera_id,
            camera_name=camera.camera_name,
            camera_type=camera.camera_type,
            ip_address=camera.ip_address,
            stream_url=camera.stream_url,
            location_description=camera.location_description,
            resolution_width=camera.resolution_width,
            resolution_height=camera.resolution_height,
            fps=camera.fps,
            gpu_id=camera.gpu_id,
            manufacturer=camera.manufacturer,
            model=camera.model,
            firmware_version=camera.firmware_version,
            onvif_supported=camera.onvif_supported,
            status=camera.status,
            is_active=camera.is_active,
            created_at=camera.created_at,
            updated_at=camera.updated_at,
            tripwires=[Tripwire(
                id=t.id,
                camera_id=t.camera_id,
                name=t.name,
                position=t.position,
                spacing=t.spacing,
                direction=t.direction,
                detection_type=t.detection_type,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at
            ) for t in tripwires]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating camera: {str(e)}"
        )

@router.post("/{camera_id}/configure", response_model=CameraInfo)
async def configure_camera(
    camera_id: int,
    config_data: CameraConfigurationRequest,
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Configure a discovered camera with tripwires and settings
    (Super Admin only)
    """
    try:
        db_manager = DatabaseManager()
        
        # Update camera configuration
        camera_update = {
            'camera_name': config_data.camera_name,
            'camera_type': config_data.camera_type,
            'location_description': config_data.location_description,
            'stream_url': config_data.stream_url,
            'username': config_data.username,
            'password': config_data.password,
            'resolution_width': config_data.resolution_width,
            'resolution_height': config_data.resolution_height,
            'fps': config_data.fps,
            'gpu_id': config_data.gpu_id,
            'status': 'configured'
        }
        
        camera = db_manager.update_camera(camera_id, camera_update)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        
        # Create tripwires
        tripwires = []
        for tripwire_data in config_data.tripwires:
            tripwire = db_manager.create_tripwire(camera_id, tripwire_data.dict())
            if tripwire:
                tripwires.append(tripwire)
        
        return CameraInfo(
            id=camera.id,
            camera_id=camera.camera_id,
            camera_name=camera.camera_name,
            camera_type=camera.camera_type,
            ip_address=camera.ip_address,
            stream_url=camera.stream_url,
            location_description=camera.location_description,
            resolution_width=camera.resolution_width,
            resolution_height=camera.resolution_height,
            fps=camera.fps,
            gpu_id=camera.gpu_id,
            manufacturer=camera.manufacturer,
            model=camera.model,
            firmware_version=camera.firmware_version,
            onvif_supported=camera.onvif_supported,
            status=camera.status,
            is_active=camera.is_active,
            created_at=camera.created_at,
            updated_at=camera.updated_at,
            tripwires=[Tripwire(
                id=t.id,
                camera_id=t.camera_id,
                name=t.name,
                position=t.position,
                spacing=t.spacing,
                direction=t.direction,
                detection_type=t.detection_type,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at
            ) for t in tripwires]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error configuring camera: {str(e)}"
        )

@router.post("/{camera_id}/activate", response_model=MessageResponse)
async def activate_camera(
    camera_id: int,
    activation_data: CameraActivationRequest,
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Activate or deactivate a camera
    (Super Admin only)
    """
    try:
        db_manager = DatabaseManager()
        
        success = db_manager.activate_camera(camera_id, activation_data.is_active)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        
        action = "activated" if activation_data.is_active else "deactivated"
        
        return MessageResponse(
            message=f"Camera {camera_id} {action} successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating camera: {str(e)}"
        )

@router.delete("/{camera_id}", response_model=MessageResponse)
async def delete_camera(
    camera_id: int,
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Delete a camera configuration
    (Super Admin only)
    """
    try:
        db_manager = DatabaseManager()
        
        success = db_manager.delete_camera(camera_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        
        return MessageResponse(
            message=f"Camera {camera_id} deleted successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting camera: {str(e)}"
        )

@router.get("/{camera_id}/status", response_model=CameraStatusResponse)
async def get_camera_status(
    camera_id: int,
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get real-time status of a camera
    (Admin+ only)
    """
    try:
        db_manager = DatabaseManager()
        camera = db_manager.get_camera(camera_id)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        
        # In a real implementation, this would check actual camera stream health
        # For now, we'll return mock status
        return CameraStatusResponse(
            camera_id=camera.camera_id,
            camera_name=camera.camera_name,
            status=camera.status,
            is_active=camera.is_active,
            last_seen=camera.updated_at,
            stream_health="healthy" if camera.is_active else "offline",
            processing_load=0.3 if camera.is_active else 0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting camera status {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting camera status: {str(e)}"
        )

# Tripwire management endpoints
@router.post("/{camera_id}/tripwires", response_model=Tripwire)
async def create_tripwire(
    camera_id: int,
    tripwire_data: TripwireCreate,
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Create a new tripwire for a camera
    (Super Admin only)
    """
    try:
        db_manager = DatabaseManager()
        
        tripwire = db_manager.create_tripwire(camera_id, tripwire_data.dict())
        
        if not tripwire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera {camera_id} not found"
            )
        
        return Tripwire(
            id=tripwire.id,
            camera_id=tripwire.camera_id,
            name=tripwire.name,
            position=tripwire.position,
            spacing=tripwire.spacing,
            direction=tripwire.direction,
            detection_type=tripwire.detection_type,
            is_active=tripwire.is_active,
            created_at=tripwire.created_at,
            updated_at=tripwire.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tripwire for camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tripwire: {str(e)}"
        )

@router.get("/{camera_id}/tripwires", response_model=List[Tripwire])
async def get_camera_tripwires(
    camera_id: int,
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get all tripwires for a camera
    (Admin+ only)
    """
    try:
        db_manager = DatabaseManager()
        tripwires = db_manager.get_camera_tripwires(camera_id)
        
        return [Tripwire(
            id=t.id,
            camera_id=t.camera_id,
            name=t.name,
            position=t.position,
            spacing=t.spacing,
            direction=t.direction,
            detection_type=t.detection_type,
            is_active=t.is_active,
            created_at=t.created_at,
            updated_at=t.updated_at
        ) for t in tripwires]
        
    except Exception as e:
        logger.error(f"Error getting tripwires for camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tripwires: {str(e)}"
        )

@router.put("/tripwires/{tripwire_id}", response_model=Tripwire)
async def update_tripwire(
    tripwire_id: int,
    tripwire_data: TripwireUpdate,
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Update a tripwire configuration
    (Super Admin only)
    """
    try:
        db_manager = DatabaseManager()
        
        # Convert to dict, excluding None values
        update_dict = {k: v for k, v in tripwire_data.dict().items() if v is not None}
        
        tripwire = db_manager.update_tripwire(tripwire_id, update_dict)
        
        if not tripwire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tripwire {tripwire_id} not found"
            )
        
        return Tripwire(
            id=tripwire.id,
            camera_id=tripwire.camera_id,
            name=tripwire.name,
            position=tripwire.position,
            spacing=tripwire.spacing,
            direction=tripwire.direction,
            detection_type=tripwire.detection_type,
            is_active=tripwire.is_active,
            created_at=tripwire.created_at,
            updated_at=tripwire.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tripwire {tripwire_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tripwire: {str(e)}"
        )

@router.delete("/tripwires/{tripwire_id}", response_model=MessageResponse)
async def delete_tripwire(
    tripwire_id: int,
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Delete a tripwire
    (Super Admin only)
    """
    try:
        db_manager = DatabaseManager()
        
        success = db_manager.delete_tripwire(tripwire_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tripwire {tripwire_id} not found"
            )
        
        return MessageResponse(
            message=f"Tripwire {tripwire_id} deleted successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tripwire {tripwire_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tripwire: {str(e)}"
        )

# Background task function
async def _store_discovered_cameras(camera_data_list: List[dict]):
    """Background task to store discovered cameras in database"""
    try:
        db_manager = DatabaseManager()
        created_cameras = db_manager.bulk_create_cameras_from_discovery(camera_data_list)
        logger.info(f"Stored {len(created_cameras)} discovered cameras in database")
    except Exception as e:
        logger.error(f"Error storing discovered cameras: {e}")

@router.post("/reload-configurations", response_model=MessageResponse)
async def reload_camera_configurations(
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Reload camera configurations from database in the FTS system
    (Super Admin only)
    """
    try:
        # Import here to avoid circular imports
        from core.fts_system import system_instance
        
        if system_instance:
            system_instance.reload_camera_configurations()
            logger.info("Camera configurations reloaded in FTS system")
            return MessageResponse(
                message="Camera configurations reloaded successfully",
                success=True
            )
        else:
            logger.warning("FTS system not running, configurations will be loaded on next start")
            return MessageResponse(
                message="FTS system not running, configurations will be loaded on next start",
                success=True
            )
        
    except Exception as e:
        logger.error(f"Error reloading camera configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reloading camera configurations: {str(e)}"
        )