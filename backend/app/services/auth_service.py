"""
Authentication Service
Business logic for user authentication and authorization
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from app.repositories.employee_repository import EmployeeRepository
from app.core.security import get_password_hash, verify_password, create_access_token
from app.utils.email_service import generate_otp, send_otp_email
from app.models.models import Employee, UserRole, get_ist_now

class AuthService:
    """Handles authentication business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.employee_repo = EmployeeRepository(db)
    
    def signup(self, email: str, password: str) -> dict:
        """
        Register new user and send OTP
        
        Args:
            email: User email
            password: User password
            
        Returns:
            dict: Success message
            
        Raises:
            HTTPException: If email already exists and verified
        """
        # Check if user already exists
        existing_user = self.employee_repo.get_by_email(email)
        
        if existing_user:
            if existing_user.is_verified:
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered and verified"
                )
            # Resend OTP for unverified user
            return self._resend_signup_otp(existing_user, password)
        
        # Determine role (first user is admin)
        role = self._determine_initial_role()
        emp_id = self._generate_initial_emp_id()
        
        # Generate OTP
        otp = generate_otp()
        
        # Create new user
        employee_data = {
            "email": email,
            "password_hash": get_password_hash(password),
            "role": role,
            "emp_id": emp_id,
            "is_verified": False,
            "otp_code": otp,
            "otp_created_at": get_ist_now(),
            "otp_purpose": "SIGNUP"
        }
        
        employee = self.employee_repo.create(employee_data)
        
        # Send OTP email
        send_otp_email(email, otp, "SIGNUP")
        
        return {"message": "Signup successful! OTP sent to your email. Please verify to activate your account."}
    
    def verify_otp(self, email: str, otp: str) -> dict:
        """
        Verify OTP for signup or password reset
        
        Args:
            email: User email
            otp: OTP code
            
        Returns:
            dict: Success message
            
        Raises:
            HTTPException: If OTP is invalid or expired
        """
        user = self.employee_repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.otp_code:
            raise HTTPException(
                status_code=400,
                detail="No OTP found. Please request a new one."
            )
        
        # Check OTP expiration (10 minutes)
        if user.otp_created_at:
            otp_age = datetime.now(user.otp_created_at.tzinfo) - user.otp_created_at
            if otp_age > timedelta(minutes=10):
                raise HTTPException(
                    status_code=400,
                    detail="OTP expired. Please request a new one."
                )
        
        # Verify OTP
        if otp != user.otp_code:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # OTP is valid - activate account if signup
        if user.otp_purpose == "SIGNUP":
            user.is_verified = True
        
        # Clear OTP after successful verification
        user.otp_code = None
        user.otp_created_at = None
        user.otp_purpose = None
        user.verification_code = None
        
        self.employee_repo.update(user)
        
        return {"message": "OTP verified successfully"}
    
    def login(self, email: str, password: str) -> dict:
        """
        Authenticate user and return JWT token
        
        Args:
            email: User email
            password: User password
            
        Returns:
            dict: Access token and user info
            
        Raises:
            HTTPException: If credentials are invalid or account not verified
        """
        user = self.employee_repo.get_by_email(email)
        
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=400,
                detail="Invalid email or password"
            )
        
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
    
    def forgot_password(self, email: str) -> dict:
        """
        Send password reset OTP to user's email
        
        Args:
            email: User email
            
        Returns:
            dict: Success message
        """
        user = self.employee_repo.get_by_email(email)
        if not user:
            # Don't reveal if email exists for security
            return {"message": "If the email exists, a password reset OTP has been sent."}
        
        if not user.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Account not verified. Please complete signup first."
            )
        
        # Generate OTP
        otp = generate_otp()
        user.otp_code = otp
        user.otp_created_at = get_ist_now()
        user.otp_purpose = "PASSWORD_RESET"
        
        self.employee_repo.update(user)
        
        # Send OTP email
        send_otp_email(email, otp, "PASSWORD_RESET")
        
        return {"message": "Password reset OTP sent to your email."}
    
    def reset_password(self, email: str, otp: str, new_password: str) -> dict:
        """
        Reset password using OTP
        
        Args:
            email: User email
            otp: OTP code
            new_password: New password
            
        Returns:
            dict: Success message
            
        Raises:
            HTTPException: If OTP is invalid or expired
        """
        user = self.employee_repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.otp_code or user.otp_purpose != "PASSWORD_RESET":
            raise HTTPException(
                status_code=400,
                detail="No password reset request found"
            )
        
        # Check OTP expiration (10 minutes)
        if user.otp_created_at:
            otp_age = datetime.now(user.otp_created_at.tzinfo) - user.otp_created_at
            if otp_age > timedelta(minutes=10):
                raise HTTPException(
                    status_code=400,
                    detail="OTP expired. Please request a new one."
                )
        
        # Verify OTP
        if otp != user.otp_code:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        user.otp_code = None
        user.otp_created_at = None
        user.otp_purpose = None
        
        self.employee_repo.update(user)
        
        return {"message": "Password reset successfully. You can now login with your new password."}
    
    def _determine_initial_role(self) -> str:
        """Determine role for new user (first user is admin)"""
        count = self.employee_repo.count()
        return UserRole.SUPER_ADMIN if count == 0 else UserRole.EMPLOYEE
    
    def _generate_initial_emp_id(self) -> str:
        """Generate employee ID (first user gets ADMIN001, others get None)"""
        count = self.employee_repo.count()
        return "ADMIN001" if count == 0 else None
    
    def _resend_signup_otp(self, user: Employee, password: str) -> dict:
        """Resend OTP for unverified user"""
        otp = generate_otp()
        user.otp_code = otp
        user.otp_created_at = get_ist_now()
        user.otp_purpose = "SIGNUP"
        user.password_hash = get_password_hash(password)
        
        self.employee_repo.update(user)
        send_otp_email(user.email, otp, "SIGNUP")
        
        return {"message": "OTP resent to your email. Please verify to complete signup."}
