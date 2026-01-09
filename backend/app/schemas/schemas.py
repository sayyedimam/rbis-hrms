from pydantic import BaseModel
from typing import List, Optional
import datetime

class SignupRequest(BaseModel):
    email: str
    password: str

class OnboardRequest(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    phone_number: str
    email: str
    designation: str
    emp_id: str

class VerifyRequest(BaseModel):
    email: str
    code: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    emp_id: str
    email: str
    role: str
    full_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
