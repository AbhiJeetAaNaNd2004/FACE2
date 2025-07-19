# Face Detection System Startup Guide

## Overview

The Face Recognition Attendance System consists of two main components:
1. **FastAPI Web Server** - Handles API requests, authentication, and database operations
2. **Face Detection System (FTS)** - Performs real-time face detection, recognition, and attendance tracking

## Current Status

When you run `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`, only the **FastAPI Web Server** starts. The **Face Detection System** needs to be started separately.

## How to Start the Face Detection System

### Method 1: Using the Web API (Recommended)

1. **Start the FastAPI server** (if not already running):
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the API documentation**:
   - Open your browser and go to: `http://localhost:8000/docs`
   - You'll see the new "System Management" section with endpoints

3. **Authenticate**:
   - Use the `/auth/login` endpoint to get an authentication token
   - You'll need admin credentials to access system management endpoints

4. **Start the Face Detection System**:
   - Use the `POST /system/start` endpoint to start the face detection system
   - Or use the provided script (see Method 2)

### Method 2: Using the Startup Script

1. **Update credentials** in `start_face_detection.py`:
   ```python
   login_data = {
       "username": "your_admin_username",
       "password": "your_admin_password"
   }
   ```

2. **Start the face detection system**:
   ```bash
   python start_face_detection.py start
   ```

3. **Check system status**:
   ```bash
   python start_face_detection.py status
   ```

### Method 3: Direct Python Integration

If you want to start the system programmatically:

```python
from core.fts_system import start_tracking_service, is_tracking_running

# Start the face detection system
if not is_tracking_running:
    start_tracking_service()
    print("Face detection system started!")
else:
    print("Face detection system is already running")
```

## Available System Management Endpoints

Once the FastAPI server is running, you have access to these endpoints (Admin+ only):

### Core Management
- `POST /system/start` - Start the face detection system
- `POST /system/stop` - Stop the face detection system
- `GET /system/status` - Get system status and statistics

### Monitoring
- `GET /system/live-faces` - Get currently detected faces
- `GET /system/attendance-data` - Get recent attendance records
- `GET /system/logs` - Get system logs
- `GET /system/camera-feed/{camera_id}` - Get live camera feed with face detection overlay

## System Status Information

The system status endpoint provides:
- **is_running**: Whether the face detection system is active
- **uptime**: How long the system has been running (seconds)
- **cam_count**: Number of active cameras
- **faces_detected**: Total faces detected since startup
- **attendance_count**: Total attendance records created
- **load**: Current system load

## Prerequisites

Before starting the face detection system, ensure:

1. **Database is initialized**: The FastAPI server creates necessary tables
2. **Camera configurations**: Cameras should be configured in the database
3. **Employee records**: Employee face embeddings should be enrolled
4. **Dependencies installed**: All required packages (OpenCV, InsightFace, etc.)

## Troubleshooting

### Common Issues

1. **Authentication Failed**:
   - Check your admin credentials in the startup script
   - Ensure you have admin privileges

2. **System Won't Start**:
   - Check that cameras are properly configured
   - Verify database connection
   - Check system logs for error messages

3. **No Face Detection**:
   - Ensure cameras are connected and accessible
   - Check camera permissions
   - Verify face recognition models are loaded

### Checking Logs

You can monitor system logs in several ways:

1. **Via API**: `GET /system/logs`
2. **FastAPI server logs**: Check the uvicorn console output
3. **System logs**: Check the FTS system internal logs

## Camera Setup

Before starting face detection, ensure your cameras are configured:

1. **Discover cameras**: Use `POST /cameras/discover` to find available cameras
2. **Configure cameras**: Set up camera parameters and tripwires
3. **Activate cameras**: Enable cameras for face detection

## Performance Considerations

- **GPU Usage**: The system can utilize GPU for faster face detection
- **Multiple Cameras**: Each camera runs in a separate thread
- **Resource Monitoring**: Monitor CPU and memory usage
- **Frame Rate**: Adjust camera frame rates based on system capacity

## Security Notes

- System management endpoints require admin authentication
- Camera feeds are protected by role-based access control
- All API calls should use HTTPS in production
- Regularly rotate authentication tokens

## Next Steps

After starting the face detection system:

1. **Monitor system status** regularly
2. **Check camera feeds** for proper operation
3. **Review attendance logs** for accuracy
4. **Adjust camera settings** as needed
5. **Monitor system performance** and resource usage

## Support

If you encounter issues:
1. Check the system logs first
2. Verify camera and database connections
3. Ensure all dependencies are properly installed
4. Check the API documentation for proper endpoint usage