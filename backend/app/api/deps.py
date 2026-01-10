from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.models import Employee, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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

def check_admin(user: Employee = Depends(get_current_user)):
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.HR, UserRole.CEO]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return user

def check_hr(user: Employee = Depends(get_current_user)):
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.HR]:
        raise HTTPException(status_code=403, detail="Only HR or Admin can perform this action")
    return user

def check_ceo(user: Employee = Depends(get_current_user)):
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.CEO]:
        raise HTTPException(status_code=403, detail="Only CEO can perform this action")
    return user
