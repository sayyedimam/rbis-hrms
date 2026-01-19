"""
Authentication Dependencies
Handles JWT token validation and role-based access control
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.models import Employee, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Employee:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        Employee: Authenticated employee object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(Employee).filter(Employee.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def check_admin(user: Employee = Depends(get_current_user)) -> Employee:
    """
    Dependency to check if user has admin privileges
    
    Args:
        user: Current authenticated user
        
    Returns:
        Employee: User with admin privileges
        
    Raises:
        HTTPException: If user doesn't have admin role
    """
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.HR, UserRole.CEO]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return user

def check_hr(user: Employee = Depends(get_current_user)) -> Employee:
    """
    Dependency to check if user has HR privileges
    
    Args:
        user: Current authenticated user
        
    Returns:
        Employee: User with HR privileges
        
    Raises:
        HTTPException: If user doesn't have HR role
    """
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.HR]:
        raise HTTPException(status_code=403, detail="Only HR or Admin can perform this action")
    return user

def check_ceo(user: Employee = Depends(get_current_user)) -> Employee:
    """
    Dependency to check if user has CEO privileges
    
    Args:
        user: Current authenticated user
        
    Returns:
        Employee: User with CEO privileges
        
    Raises:
        HTTPException: If user doesn't have CEO role
    """
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.CEO]:
        raise HTTPException(status_code=403, detail="Only CEO can perform this action")
    return user
