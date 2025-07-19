from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the face detection task
face_detection_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    global face_detection_task
    
    # Startup
    logger.info("Starting Face Recognition Attendance System...")
    try:
        # Import here to avoid circular imports
        from backend.core.fts_system import FaceTrackingSystem
        
        # Initialize and start the face tracking system
        fts = FaceTrackingSystem()
        face_detection_task = asyncio.create_task(fts.run())
        logger.info("Face detection system started successfully")
    except Exception as e:
        logger.error(f"Failed to start face detection system: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Face Recognition Attendance System...")
    if face_detection_task:
        face_detection_task.cancel()
        try:
            await face_detection_task
        except asyncio.CancelledError:
            logger.info("Face detection system stopped")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Face Recognition Attendance System",
    description="A comprehensive attendance management system using face recognition",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Face Recognition Attendance System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Face Recognition Attendance System"}

# System endpoints
@app.get("/system/status")
async def get_system_status():
    global face_detection_task
    is_running = face_detection_task is not None and not face_detection_task.done()
    return {
        "status": "running" if is_running else "stopped",
        "face_detection_active": is_running
    }

@app.post("/system/start")
async def start_system():
    global face_detection_task
    
    if face_detection_task and not face_detection_task.done():
        return {"message": "System is already running"}
    
    try:
        from backend.core.fts_system import FaceTrackingSystem
        fts = FaceTrackingSystem()
        face_detection_task = asyncio.create_task(fts.run())
        return {"message": "System started successfully"}
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        return {"error": f"Failed to start system: {str(e)}"}

@app.post("/system/stop")
async def stop_system():
    global face_detection_task
    
    if not face_detection_task or face_detection_task.done():
        return {"message": "System is not running"}
    
    face_detection_task.cancel()
    try:
        await face_detection_task
    except asyncio.CancelledError:
        pass
    
    return {"message": "System stopped successfully"}

# Auth endpoints (mock implementation)
@app.post("/auth/login")
async def login():
    return {
        "access_token": "mock_token_123",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "username": "admin",
            "role": "super_admin"
        }
    }

@app.get("/auth/me")
async def get_current_user():
    return {
        "id": 1,
        "username": "admin",
        "role": "super_admin",
        "email": "admin@company.com"
    }

# Employee endpoints (mock implementation)
@app.get("/employees/")
async def get_employees():
    return [
        {
            "id": 1,
            "name": "John Doe",
            "department": "Engineering",
            "email": "john@company.com",
            "status": "active"
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "department": "HR",
            "email": "jane@company.com",
            "status": "active"
        }
    ]

@app.get("/employees/present/current")
async def get_present_employees():
    return [
        {
            "id": 1,
            "name": "John Doe",
            "department": "Engineering",
            "check_in_time": "2024-01-15T09:00:00Z"
        }
    ]

# Attendance endpoints (mock implementation)
@app.get("/attendance/all")
async def get_all_attendance():
    return [
        {
            "id": 1,
            "employee_id": 1,
            "employee_name": "John Doe",
            "date": "2024-01-15",
            "check_in": "09:00:00",
            "check_out": "17:30:00",
            "status": "present"
        }
    ]

@app.get("/attendance/me")
async def get_my_attendance():
    return [
        {
            "id": 1,
            "date": "2024-01-15",
            "check_in": "09:00:00",
            "check_out": "17:30:00",
            "status": "present",
            "hours_worked": 8.5
        }
    ]

# Camera endpoints (mock implementation)
@app.get("/cameras")
async def get_cameras():
    return [
        {
            "id": 1,
            "name": "Main Entrance",
            "location": "Building A - Entrance",
            "status": "active",
            "ip_address": "192.168.1.100"
        }
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)