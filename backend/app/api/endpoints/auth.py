from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.models import Employee, UserRole, get_ist_now
from app.schemas.schemas import SignupRequest, LoginRequest, VerifyRequest, TokenResponse, UserResponse
from app.utils.email_service import generate_otp, send_otp_email
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    """
    Signup endpoint - Creates user account and sends OTP via email
    """
    existing_user = db.query(Employee).filter(Employee.email == req.email).first()
    
    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered and verified")
        else:
            # Re-generate OTP for unverified user
            otp = generate_otp()
            existing_user.otp_code = otp
            existing_user.otp_created_at = get_ist_now()
            existing_user.otp_purpose = "SIGNUP"
            existing_user.password_hash = get_password_hash(req.password)
            db.commit()
            
            # Send OTP email
            send_otp_email(req.email, otp, "SIGNUP")
            return {"message": "OTP resent to your email. Please verify to complete signup."}
    
    # First user becomes SUPER_ADMIN
    count = db.query(Employee).count()
    if count == 0:
        role = UserRole.SUPER_ADMIN
        emp_id = "ADMIN001"
    else:
        role = UserRole.EMPLOYEE
        emp_id = None  # Will be assigned by HR during onboarding
    
    # Generate OTP
    otp = generate_otp()
    
    new_user = Employee(
        email=req.email,
        emp_id=emp_id,
        password_hash=get_password_hash(req.password),
        role=role,
        is_verified=False,
        otp_code=otp,
        otp_created_at=get_ist_now(),
        otp_purpose="SIGNUP"
    )
    db.add(new_user)
    db.commit()
    
    # Send OTP email
    send_otp_email(req.email, otp, "SIGNUP")
    
    return {"message": "Signup successful! OTP sent to your email. Please verify to activate your account."}

@router.post("/verify-otp")
def verify_otp(req: VerifyRequest, db: Session = Depends(get_db)):
    """
    Verify OTP for signup or password reset
    """
    user = db.query(Employee).filter(Employee.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.otp_code:
        raise HTTPException(status_code=400, detail="No OTP found. Please request a new one.")
    
    # Check OTP expiration (10 minutes)
    if user.otp_created_at:
        otp_age = datetime.now(user.otp_created_at.tzinfo) - user.otp_created_at
        if otp_age > timedelta(minutes=10):
            raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")
    
    # Verify OTP
    if req.code != user.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # OTP is valid - activate account if signup
    if user.otp_purpose == "SIGNUP":
        user.is_verified = True
    
    # Clear OTP after successful verification
    user.otp_code = None
    user.otp_created_at = None
    user.otp_purpose = None
    user.verification_code = None
    db.commit()
    
    return {"message": "OTP verified successfully"}

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    """
    Send password reset OTP to user's email
    """
    user = db.query(Employee).filter(Employee.email == email).first()
    if not user:
        # Don't reveal if email exists for security
        return {"message": "If the email exists, a password reset OTP has been sent."}
    
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Account not verified. Please complete signup first.")
    
    # Generate OTP
    otp = generate_otp()
    user.otp_code = otp
    user.otp_created_at = get_ist_now()
    user.otp_purpose = "PASSWORD_RESET"
    db.commit()
    
    # Send OTP email
    send_otp_email(email, otp, "PASSWORD_RESET")
    
    return {"message": "Password reset OTP sent to your email."}

@router.post("/reset-password")
def reset_password(email: str, otp: str, new_password: str, db: Session = Depends(get_db)):
    """
    Reset password using OTP
    """
    user = db.query(Employee).filter(Employee.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.otp_code or user.otp_purpose != "PASSWORD_RESET":
        raise HTTPException(status_code=400, detail="No password reset request found")
    
    # Check OTP expiration (10 minutes)
    if user.otp_created_at:
        otp_age = datetime.now(user.otp_created_at.tzinfo) - user.otp_created_at
        if otp_age > timedelta(minutes=10):
            raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")
    
    # Verify OTP
    if otp != user.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Update password
    user.password_hash = get_password_hash(new_password)
    user.otp_code = None
    user.otp_created_at = None
    user.otp_purpose = None
    db.commit()
    
    return {"message": "Password reset successfully. You can now login with your new password."}

@router.post("/verify")
def verify(req: VerifyRequest, db: Session = Depends(get_db)):
    """
    Legacy verification endpoint - redirects to verify-otp
    """
    return verify_otp(req, db)

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
            "emp_id": user.emp_id or "PENDING",
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }
