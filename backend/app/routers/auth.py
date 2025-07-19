"""
Authentication router for JWT-based authentication
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas import (
    Token, LoginRequest, MessageResponse, UserAccountCreate, 
    UserAccount, CurrentUser, UserRole, RoleAssignmentRequest
)
from app.security import (
    authenticate_user, create_access_token, get_current_active_user,
    require_super_admin, get_password_hash
)
from db.db_config import get_db
from db.db_models import UserAccount as UserAccountModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint using OAuth2PasswordRequestForm for JWT token generation
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/json", response_model=Token)
async def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Alternative login endpoint accepting JSON data
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=CurrentUser)
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return current_user

@router.post("/users/create", response_model=MessageResponse)
async def create_user(
    user_data: UserAccountCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Create a new user account (Super Admin only)
    """
    # Check if username already exists
    existing_user = db.query(UserAccountModel).filter(
        UserAccountModel.username == user_data.username
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Validate employee_id if provided
    if user_data.employee_id:
        from db.db_models import Employee
        employee = db.query(Employee).filter(
            Employee.employee_id == user_data.employee_id
        ).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID not found"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = UserAccountModel(
        username=user_data.username,
        hashed_password=hashed_password,
        role=user_data.role,
        employee_id=user_data.employee_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return MessageResponse(message=f"User '{user_data.username}' created successfully")

@router.patch("/users/{user_id}/role", response_model=MessageResponse)
async def assign_role(
    user_id: int,
    role_data: RoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Assign role to user (Super Admin only)
    """
    user = db.query(UserAccountModel).filter(UserAccountModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = role_data.role
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return MessageResponse(message=f"Role updated to '{role_data.role}' for user '{user.username}'")

@router.get("/users", response_model=list[UserAccount])
async def list_users(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    List all users (Super Admin only)
    """
    users = db.query(UserAccountModel).all()
    return users

@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_super_admin)
):
    """
    Delete a user account (Super Admin only)
    """
    user = db.query(UserAccountModel).filter(UserAccountModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    
    return MessageResponse(message=f"User '{user.username}' deleted successfully")
