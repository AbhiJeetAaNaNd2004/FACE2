"""
System Management Router
Provides endpoints for managing the face detection system
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Dict, Any

from app.schemas import CurrentUser, MessageResponse
from app.security import require_admin_or_above
from core.fts_system import (
    start_tracking_service, 
    shutdown_tracking_service, 
    get_system_status,
    get_live_faces,
    get_attendance_data,
    get_logs,
    is_tracking_running,
    generate_mjpeg
)
from utils.logging import get_logger

router = APIRouter(prefix="/system", tags=["System Management"])
logger = get_logger(__name__)

@router.post("/start", response_model=MessageResponse)
async def start_face_detection_system(
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Start the face detection and tracking system (Admin+ only)
    """
    try:
        if is_tracking_running:
            return MessageResponse(
                success=False,
                message="Face detection system is already running"
            )
        
        start_tracking_service()
        logger.info(f"Face detection system started by user {current_user.username}")
        
        return MessageResponse(
            success=True,
            message="Face detection system started successfully"
        )
    except Exception as e:
        logger.error(f"Failed to start face detection system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start face detection system: {str(e)}"
        )

@router.post("/stop", response_model=MessageResponse)
async def stop_face_detection_system(
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Stop the face detection and tracking system (Admin+ only)
    """
    try:
        if not is_tracking_running:
            return MessageResponse(
                success=False,
                message="Face detection system is not running"
            )
        
        shutdown_tracking_service()
        logger.info(f"Face detection system stopped by user {current_user.username}")
        
        return MessageResponse(
            success=True,
            message="Face detection system stopped successfully"
        )
    except Exception as e:
        logger.error(f"Failed to stop face detection system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop face detection system: {str(e)}"
        )

@router.get("/status")
async def get_face_detection_status(
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get face detection system status and statistics (Admin+ only)
    """
    try:
        status_data = get_system_status()
        status_data["is_running"] = is_tracking_running
        
        return {
            "success": True,
            "data": status_data
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )

@router.get("/live-faces")
async def get_detected_faces(
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get currently detected faces (Admin+ only)
    """
    try:
        faces = get_live_faces()
        return {
            "success": True,
            "data": faces
        }
    except Exception as e:
        logger.error(f"Failed to get live faces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get live faces: {str(e)}"
        )

@router.get("/attendance-data")
async def get_recent_attendance(
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get recent attendance records (Admin+ only)
    """
    try:
        attendance = get_attendance_data()
        return {
            "success": True,
            "data": attendance
        }
    except Exception as e:
        logger.error(f"Failed to get attendance data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance data: {str(e)}"
        )

@router.get("/logs")
async def get_system_logs(
    limit: int = 100,
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get recent system logs (Admin+ only)
    """
    try:
        logs = get_logs(limit)
        return {
            "success": True,
            "data": logs
        }
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system logs: {str(e)}"
        )

@router.get("/camera-feed/{camera_id}")
async def get_camera_feed(
    camera_id: int,
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get live camera feed with face detection overlay (Admin+ only)
    """
    try:
        if not is_tracking_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Face detection system is not running"
            )
        
        return StreamingResponse(
            generate_mjpeg(camera_id),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except Exception as e:
        logger.error(f"Failed to get camera feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get camera feed: {str(e)}"
        )