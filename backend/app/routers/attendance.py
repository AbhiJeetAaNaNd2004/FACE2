"""
Attendance management router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, date

from app.schemas import (
    AttendanceLog, AttendanceLogCreate, AttendanceResponse, 
    MessageResponse, CurrentUser, Employee
)
from app.security import (
    require_admin_or_above, require_employee_or_above, 
    get_current_active_user, check_employee_access
)
from db.db_config import get_db
from db.db_models import AttendanceLog as AttendanceLogModel, Employee as EmployeeModel

router = APIRouter(prefix="/attendance", tags=["Attendance Management"])

@router.get("/me", response_model=AttendanceResponse)
async def get_my_attendance(
    start_date: Optional[date] = Query(None, description="Start date for attendance records"),
    end_date: Optional[date] = Query(None, description="End date for attendance records"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get own attendance records (Employee+ role)
    """
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an employee record"
        )
    
    # Get employee details
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == current_user.employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    # Build query for attendance logs
    query = db.query(AttendanceLogModel).filter(
        AttendanceLogModel.employee_id == current_user.employee_id
    )
    
    # Apply date filters if provided
    if start_date:
        query = query.filter(AttendanceLogModel.timestamp >= start_date)
    if end_date:
        from datetime import datetime, time
        end_datetime = datetime.combine(end_date, time.max)
        query = query.filter(AttendanceLogModel.timestamp <= end_datetime)
    
    # Order by timestamp descending
    attendance_logs = query.order_by(desc(AttendanceLogModel.timestamp)).all()
    
    return AttendanceResponse(
        employee_id=employee.employee_id,
        employee_name=employee.name,
        attendance_logs=attendance_logs
    )

@router.get("/all", response_model=List[AttendanceResponse])
async def get_all_attendance(
    start_date: Optional[date] = Query(None, description="Start date for attendance records"),
    end_date: Optional[date] = Query(None, description="End date for attendance records"),
    employee_id: Optional[str] = Query(None, description="Filter by specific employee ID"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get all attendance records (Admin+ only)
    """
    # Build base query
    query = db.query(AttendanceLogModel)
    
    # Apply employee filter if provided
    if employee_id:
        query = query.filter(AttendanceLogModel.employee_id == employee_id)
    
    # Apply date filters if provided
    if start_date:
        query = query.filter(AttendanceLogModel.timestamp >= start_date)
    if end_date:
        from datetime import datetime, time
        end_datetime = datetime.combine(end_date, time.max)
        query = query.filter(AttendanceLogModel.timestamp <= end_datetime)
    
    # Get all matching attendance logs
    attendance_logs = query.order_by(desc(AttendanceLogModel.timestamp)).all()
    
    # Group by employee
    employee_attendance = {}
    for log in attendance_logs:
        if log.employee_id not in employee_attendance:
            employee_attendance[log.employee_id] = []
        employee_attendance[log.employee_id].append(log)
    
    # Build response
    responses = []
    for emp_id, logs in employee_attendance.items():
        employee = db.query(EmployeeModel).filter(
            EmployeeModel.employee_id == emp_id
        ).first()
        
        if employee:
            responses.append(AttendanceResponse(
                employee_id=emp_id,
                employee_name=employee.name,
                attendance_logs=logs
            ))
    
    return responses

@router.get("/{employee_id}", response_model=AttendanceResponse)
async def get_employee_attendance(
    employee_id: str,
    start_date: Optional[date] = Query(None, description="Start date for attendance records"),
    end_date: Optional[date] = Query(None, description="End date for attendance records"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get specific employee's attendance records
    """
    # Check access permissions
    check_employee_access(employee_id, current_user)
    
    # Get employee details
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Build query for attendance logs
    query = db.query(AttendanceLogModel).filter(
        AttendanceLogModel.employee_id == employee_id
    )
    
    # Apply date filters if provided
    if start_date:
        query = query.filter(AttendanceLogModel.timestamp >= start_date)
    if end_date:
        from datetime import datetime, time
        end_datetime = datetime.combine(end_date, time.max)
        query = query.filter(AttendanceLogModel.timestamp <= end_datetime)
    
    # Order by timestamp descending
    attendance_logs = query.order_by(desc(AttendanceLogModel.timestamp)).all()
    
    return AttendanceResponse(
        employee_id=employee.employee_id,
        employee_name=employee.name,
        attendance_logs=attendance_logs
    )

@router.post("/mark", response_model=MessageResponse)
async def mark_attendance(
    attendance_data: AttendanceLogCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Mark attendance for an employee (Admin+ only)
    """
    # Check if employee exists
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == attendance_data.employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Create attendance log
    new_attendance = AttendanceLogModel(
        employee_id=attendance_data.employee_id,
        status=attendance_data.status,
        confidence_score=attendance_data.confidence_score,
        notes=attendance_data.notes,
        timestamp=datetime.utcnow()
    )
    
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    
    return MessageResponse(
        message=f"Attendance marked as '{attendance_data.status}' for employee '{employee.name}'"
    )

@router.get("/summary/daily")
async def get_daily_attendance_summary(
    target_date: date = Query(..., description="Date for attendance summary"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Get daily attendance summary (Admin+ only)
    """
    from datetime import datetime, time
    
    # Define the date range for the target date
    start_datetime = datetime.combine(target_date, time.min)
    end_datetime = datetime.combine(target_date, time.max)
    
    # Get all attendance logs for the target date
    attendance_logs = db.query(AttendanceLogModel).filter(
        and_(
            AttendanceLogModel.timestamp >= start_datetime,
            AttendanceLogModel.timestamp <= end_datetime
        )
    ).all()
    
    # Get total active employees
    total_employees = db.query(EmployeeModel).filter(
        EmployeeModel.is_active == True
    ).count()
    
    # Count present and absent employees
    present_employees = set()
    absent_employees = set()
    
    for log in attendance_logs:
        if log.status == 'present':
            present_employees.add(log.employee_id)
        elif log.status == 'absent':
            absent_employees.add(log.employee_id)
    
    # Remove employees who are both present and absent (present takes precedence)
    absent_employees = absent_employees - present_employees
    
    # Count employees with no attendance record
    employees_with_logs = present_employees.union(absent_employees)
    employees_without_logs = total_employees - len(employees_with_logs)
    
    return {
        "date": target_date,
        "total_employees": total_employees,
        "present_count": len(present_employees),
        "absent_count": len(absent_employees),
        "no_record_count": employees_without_logs,
        "attendance_logs_count": len(attendance_logs)
    }

@router.delete("/{log_id}", response_model=MessageResponse)
async def delete_attendance_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin_or_above)
):
    """
    Delete an attendance log (Admin+ only)
    """
    attendance_log = db.query(AttendanceLogModel).filter(
        AttendanceLogModel.id == log_id
    ).first()
    
    if not attendance_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance log not found"
        )
    
    db.delete(attendance_log)
    db.commit()
    
    return MessageResponse(
        message=f"Attendance log deleted successfully"
    )

@router.get("/employee/{employee_id}/latest")
async def get_latest_attendance(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get the latest attendance record for an employee
    """
    # Check access permissions
    check_employee_access(employee_id, current_user)
    
    # Get employee details
    employee = db.query(EmployeeModel).filter(
        EmployeeModel.employee_id == employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get latest attendance log
    latest_log = db.query(AttendanceLogModel).filter(
        AttendanceLogModel.employee_id == employee_id
    ).order_by(desc(AttendanceLogModel.timestamp)).first()
    
    return {
        "employee_id": employee.employee_id,
        "employee_name": employee.name,
        "latest_attendance": latest_log,
        "current_status": latest_log.status if latest_log else "unknown"
    }
