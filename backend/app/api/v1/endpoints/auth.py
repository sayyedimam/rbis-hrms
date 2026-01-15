"""
Authentication Endpoints (API v1)
Handles user signup, login, OTP verification, and password reset
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.services.auth_service import AuthService
from app.schemas.schemas import SignupRequest, LoginRequest, VerifyRequest, TokenResponse

router = APIRouter()

@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    """
    Register new user
    
    - Creates user account
    - Sends OTP to email for verification
    - First user becomes SUPER_ADMIN
    - Returns success message
    """
    service = AuthService(db)
    return service.signup(req.email, req.password)

@router.post("/verify-otp")
def verify_otp(req: VerifyRequest, db: Session = Depends(get_db)):
    """
    Verify OTP for signup or password reset
    
    - Validates OTP code
    - Checks expiration (10 minutes)
    - Activates account if signup OTP
    - Clears OTP after verification
    """
    service = AuthService(db)
    return service.verify_otp(req.email, req.code)

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    """
    Send password reset OTP to user's email
    
    - Generates reset OTP
    - Sends OTP via email
    - Returns generic success message (security)
    """
    service = AuthService(db)
    return service.forgot_password(email)

@router.post("/reset-password")
def reset_password(email: str, otp: str, new_password: str, db: Session = Depends(get_db)):
    """
    Reset password using OTP
    
    - Validates OTP
    - Updates password
    - Clears OTP
    - Returns success message
    """
    service = AuthService(db)
    return service.reset_password(email, otp, new_password)

@router.post("/verify")
def verify(req: VerifyRequest, db: Session = Depends(get_db)):
    """
    Legacy verification endpoint - redirects to verify-otp
    
    Maintained for backward compatibility
    """
    service = AuthService(db)
    return service.verify_otp(req.email, req.code)

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and get JWT token
    
    - Validates credentials
    - Checks if account is verified
    - Returns access token and user info
    """
    service = AuthService(db)
    return service.login(req.email, req.password)
