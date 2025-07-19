from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

# Enums for better type safety
class UserRole(str, Enum):
    EMPLOYEE = "employee"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"

# Base schemas
class EmployeeBase(BaseModel):
    employee_id: str = Field(..., description="Unique employee identifier")
    name: str = Field(..., description="Employee full name")
    department: str = Field(..., description="Department name")
    role: str = Field(..., description="Job role/position")
    date_joined: date = Field(..., description="Date when employee joined")
    email: Optional[str] = Field(None, description="Employee email address")
    phone: Optional[str] = Field(None, description="Employee phone number")

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class Employee(EmployeeBase):
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Face Embedding schemas
class FaceEmbeddingBase(BaseModel):
    employee_id: str
    image_path: str
    quality_score: Optional[float] = None

class FaceEmbeddingCreate(FaceEmbeddingBase):
    embedding_vector: bytes

class FaceEmbedding(FaceEmbeddingBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Attendance Log schemas
class AttendanceLogBase(BaseModel):
    employee_id: str
    status: AttendanceStatus
    confidence_score: Optional[float] = None
    notes: Optional[str] = None

class AttendanceLogCreate(AttendanceLogBase):
    pass

class AttendanceLog(AttendanceLogBase):
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# User Account schemas
class UserAccountBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: UserRole
    employee_id: Optional[str] = None

class UserAccountCreate(UserAccountBase):
    password: str = Field(..., min_length=6)

class UserAccountUpdate(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    employee_id: Optional[str] = None

class UserAccount(UserAccountBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class CurrentUser(BaseModel):
    id: int
    username: str
    role: UserRole
    employee_id: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

# Employee enrollment schema
class EmployeeEnrollmentRequest(BaseModel):
    employee: EmployeeCreate
    image_data: str = Field(..., description="Base64 encoded image data")

# Response schemas
class MessageResponse(BaseModel):
    message: str
    success: bool = True

class AttendanceResponse(BaseModel):
    employee_id: str
    employee_name: str
    attendance_logs: List[AttendanceLog]

class PresentEmployeesResponse(BaseModel):
    present_employees: List[Employee]
    total_count: int

# Role assignment schema
class RoleAssignmentRequest(BaseModel):
    role: UserRole

# Camera Management schemas
class CameraStatus(str, Enum):
    DISCOVERED = "discovered"
    CONFIGURED = "configured"
    ACTIVE = "active"
    INACTIVE = "inactive"

class CameraType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    GENERAL = "general"

class TripwireDirection(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

class TripwireDetectionType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    COUNTING = "counting"

# Tripwire schemas
class TripwireBase(BaseModel):
    name: str = Field(..., description="Tripwire name/identifier")
    position: float = Field(..., ge=0.0, le=1.0, description="Position (0.0 to 1.0)")
    spacing: float = Field(default=0.01, ge=0.001, le=0.1, description="Spacing for detection")
    direction: TripwireDirection = Field(..., description="Tripwire direction")
    detection_type: TripwireDetectionType = Field(default=TripwireDetectionType.ENTRY, description="Detection type")
    is_active: bool = Field(default=True, description="Whether tripwire is active")

class TripwireCreate(TripwireBase):
    pass

class TripwireUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[float] = Field(None, ge=0.0, le=1.0)
    spacing: Optional[float] = Field(None, ge=0.001, le=0.1)
    direction: Optional[TripwireDirection] = None
    detection_type: Optional[TripwireDetectionType] = None
    is_active: Optional[bool] = None

class Tripwire(TripwireBase):
    id: int
    camera_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Camera schemas
class CameraBase(BaseModel):
    camera_name: str = Field(..., description="Human-readable camera name")
    camera_type: CameraType = Field(default=CameraType.GENERAL, description="Camera type")
    location_description: Optional[str] = Field(None, description="Human-readable location description")
    resolution_width: int = Field(default=1920, ge=320, le=4096, description="Camera resolution width")
    resolution_height: int = Field(default=1080, ge=240, le=2160, description="Camera resolution height")
    fps: int = Field(default=30, ge=1, le=60, description="Frames per second")
    gpu_id: int = Field(default=0, ge=0, description="GPU ID for processing")

class CameraCreate(CameraBase):
    ip_address: str = Field(..., description="Camera IP address")
    stream_url: Optional[str] = Field(None, description="Primary stream URL")
    username: Optional[str] = Field(None, description="Camera authentication username")
    password: Optional[str] = Field(None, description="Camera authentication password")

class CameraUpdate(BaseModel):
    camera_name: Optional[str] = None
    camera_type: Optional[CameraType] = None
    location_description: Optional[str] = None
    resolution_width: Optional[int] = Field(None, ge=320, le=4096)
    resolution_height: Optional[int] = Field(None, ge=240, le=2160)
    fps: Optional[int] = Field(None, ge=1, le=60)
    gpu_id: Optional[int] = Field(None, ge=0)
    stream_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    status: Optional[CameraStatus] = None
    is_active: Optional[bool] = None

class CameraInfo(CameraBase):
    id: int
    camera_id: int
    ip_address: str
    stream_url: Optional[str]
    manufacturer: Optional[str]
    model: Optional[str]
    firmware_version: Optional[str]
    onvif_supported: bool
    status: CameraStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tripwires: List[Tripwire] = []

    class Config:
        from_attributes = True

class CameraDiscoveryResult(BaseModel):
    ip_address: str
    port: int
    manufacturer: str
    model: str
    firmware_version: str
    stream_urls: List[str]
    onvif_supported: bool
    device_service_url: str
    media_service_url: str

class CameraDiscoveryRequest(BaseModel):
    network_range: str = Field(default="192.168.1.0/24", description="Network range to scan (CIDR notation)")
    timeout: int = Field(default=10, ge=5, le=60, description="Discovery timeout in seconds")

class CameraDiscoveryResponse(BaseModel):
    discovered_cameras: List[CameraDiscoveryResult]
    total_discovered: int
    discovery_time: float
    network_range: str

class CameraConfigurationRequest(BaseModel):
    camera_name: str = Field(..., description="Human-readable camera name")
    camera_type: CameraType = Field(..., description="Camera type")
    location_description: Optional[str] = Field(None, description="Location description")
    stream_url: Optional[str] = Field(None, description="Primary stream URL")
    username: Optional[str] = Field(None, description="Camera username")
    password: Optional[str] = Field(None, description="Camera password")
    resolution_width: int = Field(default=1920, ge=320, le=4096)
    resolution_height: int = Field(default=1080, ge=240, le=2160)
    fps: int = Field(default=30, ge=1, le=60)
    gpu_id: int = Field(default=0, ge=0)
    tripwires: List[TripwireCreate] = Field(default=[], description="Tripwire configurations")

class CameraActivationRequest(BaseModel):
    is_active: bool = Field(..., description="Whether to activate or deactivate the camera")

class CameraListResponse(BaseModel):
    cameras: List[CameraInfo]
    total_count: int
    active_count: int
    inactive_count: int

class CameraStatusResponse(BaseModel):
    camera_id: int
    camera_name: str
    status: CameraStatus
    is_active: bool
    last_seen: Optional[datetime]
    stream_health: str  # 'healthy', 'degraded', 'offline'
    processing_load: float  # 0.0 to 1.0

# Validation
class EmployeeCreate(EmployeeBase):
    @validator('employee_id')
    def validate_employee_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Employee ID cannot be empty')
        return v.strip()

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('department')
    def validate_department(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Department cannot be empty')
        return v.strip()

    @validator('role')
    def validate_role(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Role cannot be empty')
        return v.strip()