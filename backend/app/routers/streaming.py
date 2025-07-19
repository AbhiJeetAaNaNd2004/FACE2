"""
Live streaming router for camera feed
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Generator
import cv2
import time

from app.schemas import CurrentUser
from app.security import require_admin_or_above

router = APIRouter(prefix="/stream", tags=["Live Streaming"])

def generate_mock_mjpeg_stream() -> Generator[bytes, None, None]:
    """
    Generate a mock MJPEG stream for demonstration
    In a real implementation, this would connect to actual cameras
    """
    # Create a simple test image
    import numpy as np
    
    while True:
        # Create a simple test frame with timestamp
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some color and text
        frame[:, :] = [50, 100, 150]  # Blue background
        
        # Add timestamp text
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Live Feed - {timestamp}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Mock Camera Feed", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        # Yield frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Sleep to control frame rate
        time.sleep(1/30)  # 30 FPS

@router.get("/live-feed")
async def get_live_feed(
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get live camera feed (Admin+ only)
    Returns an MJPEG stream
    """
    return StreamingResponse(
        generate_mock_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/camera-status")
async def get_camera_status(
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get camera status information (Admin+ only)
    """
    return {
        "cameras": [
            {
                "id": 1,
                "name": "Main Entrance",
                "status": "active",
                "resolution": "1920x1080",
                "fps": 30,
                "last_seen": "2024-01-01T12:00:00Z"
            },
            {
                "id": 2,
                "name": "Exit Door",
                "status": "active",
                "resolution": "1280x720",
                "fps": 25,
                "last_seen": "2024-01-01T12:00:00Z"
            }
        ],
        "total_cameras": 2,
        "active_cameras": 2,
        "inactive_cameras": 0
    }

@router.get("/health")
async def streaming_health_check(
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Health check for streaming service (Admin+ only)
    """
    return {
        "status": "healthy",
        "service": "streaming",
        "timestamp": time.time(),
        "message": "Streaming service is operational"
    }
