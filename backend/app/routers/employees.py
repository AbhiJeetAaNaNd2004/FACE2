"""
Employee management router
"""

import base64
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import settings
from app.schemas import (
    Employee, EmployeeCreate, EmployeeUpdate, MessageResponse,
    EmployeeEnrollmentRequest, PresentEmployeesResponse, CurrentUser
)
from app.security import (
    require_admin_or_above, require_employee_or_above, 
    get_current_active_user, check_employee_access
)
from db.db_config import get_db
from db.db_models import Employee as EmployeeModel, FaceEmbedding, AttendanceLog

router = APIRouter(prefix="/employees", tags=["Employee Management"])

@router.post("/enroll", response_model=MessageResponse)
async def enroll_employee(
    enrollment_data: EmployeeEnrollmentRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Enroll employee with face data (Admin+ only)
    """
    # Check if employee already exists
    existing_employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == enrollment_data.employee.employee_id
    ).first()
    
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee already exists"
        )
    
    # Create employee record
    new_employee = EmployeeModel(
        employee_id=enrollment_data.employee.employee_id,
        name=enrollment_data.employee.name,
        department=enrollment_data.employee.department,
        role=enrollment_data.employee.role,
        date_joined=enrollment_data.employee.date_joined,
        email=enrollment_data.employee.email,
        phone=enrollment_data.employee.phone
    )
    
    db.add(new_employee)
    db.flush()  # Flush to get the employee in the session
    
    # Process face image and create embedding
    try:
        # Create directories if they don't exist
        face_images_dir = os.path.join(settings.UPLOAD_DIR, settings.FACE_IMAGES_DIR)
        os.makedirs(face_images_dir, exist_ok=True)
        
        # Decode base64 image
        image_data = base64.b64decode(enrollment_data.image_data)
        
        # Save image file
        image_filename = f"{enrollment_data.employee.employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = os.path.join(face_images_dir, image_filename)
        
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        # For now, create a mock embedding (in real implementation, use face_recognition library)
        mock_embedding = b"mock_embedding_data_" + enrollment_data.employee.employee_id.encode()
        
        # Create face embedding record
        face_embedding = FaceEmbedding(
            employee_id=enrollment_data.employee.employee_id,
            image_path=image_path,
            embedding_vector=mock_embedding,
            quality_score=0.95  # Mock quality score
        )
        
        db.add(face_embedding)
        db.commit()
        
        return MessageResponse(
            message=f"Employee '{enrollment_data.employee.name}' enrolled successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process face data: {str(e)}"
        )

@router.get("/", response_model=List[Employee])
async def list_employees(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_employee_or_above)
):
    """
    List all employees (any authenticated user)
    """
    employees = db.query(EmployeeModel).filter(EmployeeModel.is_active == True).all()
    return employees

@router.get("/{employee_id}", response_model=Employee)
async def get_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get specific employee details
    """
    # Check access permissions
    check_employee_access(employee_id, current_user)
    
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee

@router.put("/{employee_id}", response_model=MessageResponse)
async def update_employee(
    employee_id: str,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Update employee information (Admin+ only)
    """
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update fields
    update_data = employee_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    employee.updated_at = datetime.utcnow()
    db.commit()
    
    return MessageResponse(message=f"Employee '{employee.name}' updated successfully")

@router.delete("/{employee_id}", response_model=MessageResponse)
async def delete_employee(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Delete employee (Admin+ only)
    """
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Soft delete
    employee.is_active = False
    employee.updated_at = datetime.utcnow()
    db.commit()
    
    return MessageResponse(message=f"Employee '{employee.name}' deleted successfully")

@router.get("/present/current", response_model=PresentEmployeesResponse)
async def get_present_employees(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_employee_or_above)
):
    """
    Get currently present employees (any authenticated user)
    """
    # Get employees who have a 'present' status in their latest attendance log
    from sqlalchemy import func, and_
    
    # Subquery to get the latest attendance log for each employee
    latest_attendance_subquery = db.query(
        AttendanceLog.employee_id,
        func.max(AttendanceLog.timestamp).label('latest_timestamp')
    ).group_by(AttendanceLog.employee_id).subquery()
    
    # Query to get employees with 'present' status in their latest log
    present_employees = db.query(EmployeeModel).join(
        AttendanceLog,
        EmployeeModel.employee_id == AttendanceLog.employee_id
    ).join(
        latest_attendance_subquery,
        and_(
            AttendanceLog.employee_id == latest_attendance_subquery.c.employee_id,
            AttendanceLog.timestamp == latest_attendance_subquery.c.latest_timestamp
        )
    ).filter(
        and_(
            AttendanceLog.status == 'present',
            EmployeeModel.is_active == True
        )
    ).all()
    
    return PresentEmployeesResponse(
        present_employees=present_employees,
        total_count=len(present_employees)
    )

@router.post("/{employee_id}/face-image", response_model=MessageResponse)
async def upload_face_image(
    employee_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Upload additional face image for employee (Admin+ only)
    """
    # Check if employee exists
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Check file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
        )
    
    try:
        # Create directories if they don't exist
        face_images_dir = os.path.join(settings.UPLOAD_DIR, settings.FACE_IMAGES_DIR)
        os.makedirs(face_images_dir, exist_ok=True)
        
        # Save uploaded file
        image_filename = f"{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        image_path = os.path.join(face_images_dir, image_filename)
        
        with open(image_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create mock embedding (in real implementation, use face_recognition library)
        mock_embedding = b"mock_embedding_data_" + employee_id.encode() + b"_" + str(datetime.now().timestamp()).encode()
        
        # Create face embedding record
        face_embedding = FaceEmbedding(
            employee_id=employee_id,
            image_path=image_path,
            embedding_vector=mock_embedding,
            quality_score=0.90  # Mock quality score
        )
        
        db.add(face_embedding)
        db.commit()
        
        return MessageResponse(
            message=f"Face image uploaded successfully for employee '{employee.name}'"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload face image: {str(e)}"
        )