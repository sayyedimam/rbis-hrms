"""
Authentication Endpoints (API v1)
Handles user signup, login, OTP verification, and password reset
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.services.auth_service import AuthService
from app.schemas.schemas import (
    SignupRequest, 
    LoginRequest, 
    VerifyOTPRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    TokenResponse,
    MessageResponse,
    ErrorResponse
)

router = APIRouter()

@router.post("/signup", response_model=MessageResponse, status_code=201)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    """
    Register new user with email validation
    
    Request body:
    - **email**: Valid email address
    - **password**: Minimum 8 chars with uppercase, lowercase, and number
    
    Returns:
    - Success message with instructions to verify OTP
    
    Status Codes:
    - 201: User created successfully
    - 400: Invalid input or email already exists
    """
    try:
        service = AuthService(db)
        result = service.signup(req.email, req.password)
        return MessageResponse(message=result["message"])
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verify OTP for signup or password reset
    
    - Validates 6-digit OTP code
    - Checks expiration (10 minutes)
    - Activates account if signup OTP
    - Returns JWT token on success
    
    Status Codes:
    - 200: OTP verified successfully
    - 400: Invalid or expired OTP
    - 404: User not found
    """
    try:
        service = AuthService(db)
        return service.verify_otp(req.email, req.otp_code)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(req: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Request password reset OTP
    
    - Sends OTP to user's registered email
    - OTP valid for 10 minutes
    - Returns generic message for security
    
    Status Codes:
    - 200: OTP sent (even if email doesn't exist - security practice)
    - 400: Invalid email format
    """
    try:
        service = AuthService(db)
        result = service.forgot_password(req.email)
        return MessageResponse(message=result["message"])
    except Exception:
        # Return generic response for security (don't reveal if user exists)
        return MessageResponse(
            message="If the email exists in our system, you will receive a password reset code"
        )

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Reset password with OTP verification
    
    - Validates OTP code
    - Updates password with strength requirements
    - Clears OTP token
    
    Status Codes:
    - 200: Password reset successfully
    - 400: Invalid OTP or password requirements not met
    - 404: User not found
    """
    try:
        service = AuthService(db)
        result = service.reset_password(req.email, req.otp_code, req.new_password)
        return MessageResponse(message=result["message"])
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify", response_model=TokenResponse, deprecated=True)
def verify(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Legacy verification endpoint
    
    ⚠️ DEPRECATED: Use `/verify-otp` instead
    
    Maintained for backward compatibility only.
    """
    try:
        service = AuthService(db)
        return service.verify_otp(req.email, req.otp_code)
    except HTTPException as e:
        raise e

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and get JWT token
    
    - Validates email and password
    - Checks if account is verified
    - Returns JWT token valid for 7 days
    
    Status Codes:
    - 200: Login successful
    - 400: Invalid credentials or account not verified
    - 401: Unauthorized
    - 404: User not found
    - Returns access token and user info
    """
    service = AuthService(db)
    return service.login(req.email, req.password)
