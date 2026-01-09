from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.models import Employee, UserRole
from app.schemas.schemas import SignupRequest, LoginRequest, VerifyRequest, TokenResponse, UserResponse
import random

router = APIRouter()

@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    existing_user = db.query(Employee).filter(Employee.email == req.email).first()
    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered and verified")
        else:
            # Re-generate code for unverified user
            v_code = str(random.randint(100000, 999999))
            existing_user.verification_code = v_code
            existing_user.password_hash = get_password_hash(req.password) # Update password if they changed it
            db.commit()
            return {"message": f"Verification code resent: {v_code}"}
    
    # First user becomes SUPER_ADMIN
    count = db.query(Employee).count()
    if count == 0:
        role = UserRole.SUPER_ADMIN
        emp_id = "ADMIN001"
    else:
        role = UserRole.EMPLOYEE
        emp_id = f"TEMP_{random.randint(1000, 9999)}"
    
    # Generate 6-digit verification code
    v_code = str(random.randint(100000, 999999))
    
    new_user = Employee(
        email=req.email,
        emp_id=emp_id,
        password_hash=get_password_hash(req.password),
        role=role,
        is_verified=False,
        verification_code=v_code
    )
    db.add(new_user)
    db.commit()
    # In a real app, send email here. For now, we return it in response for dev ease.
    return {"message": f"Signup successful. Verification code: {v_code}"}

@router.post("/verify")
def verify(req: VerifyRequest, db: Session = Depends(get_db)):
    user = db.query(Employee).filter(Employee.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if req.code != user.verification_code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
        
    user.is_verified = True
    user.verification_code = None  # Clear code after successful verification
    db.commit()
    return {"message": "Email verified successfully"}

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Employee).filter(Employee.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Account not verified. Please verify your email first."
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "emp_id": user.emp_id or "TEMP_ID",
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }
