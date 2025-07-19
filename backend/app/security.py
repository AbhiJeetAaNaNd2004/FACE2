"""
Security utilities for JWT authentication and role-based access control
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas import TokenData, CurrentUser, UserRole
from db.db_config import get_db
from db.db_models import UserAccount

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, role=role)
        return token_data
    except JWTError:
        raise credentials_exception

def authenticate_user(db: Session, username: str, password: str) -> Optional[UserAccount]:
    """Authenticate a user with username and password"""
    user = db.query(UserAccount).filter(UserAccount.username == username).first()
    
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
        
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> CurrentUser:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(token, credentials_exception)
    user = db.query(UserAccount).filter(UserAccount.username == token_data.username).first()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return CurrentUser(
        id=user.id,
        username=user.username,
        role=user.role,
        employee_id=user.employee_id,
        is_active=user.is_active
    )

def get_current_active_user(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role-based access control dependencies
def require_admin_or_above(current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
    """Require admin or super_admin role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

def require_super_admin(current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
    """Require super_admin role"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return current_user

def require_employee_or_above(current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
    """Require at least employee role (basically any authenticated user)"""
    return current_user

def check_employee_access(employee_id: str, current_user: CurrentUser = Depends(get_current_active_user)) -> bool:
    """Check if user can access employee data (own data or admin+)"""
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return True
    
    if current_user.employee_id == employee_id:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You can only access your own data"
    )

# Utility functions for role checking
def has_admin_privileges(user_role: str) -> bool:
    """Check if user has admin privileges"""
    return user_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

def has_super_admin_privileges(user_role: str) -> bool:
    """Check if user has super admin privileges"""
    return user_role == UserRole.SUPER_ADMIN

def can_access_employee_data(user_role: str, user_employee_id: str, target_employee_id: str) -> bool:
    """Check if user can access specific employee data"""
    if has_admin_privileges(user_role):
        return True
    return user_employee_id == target_employee_id