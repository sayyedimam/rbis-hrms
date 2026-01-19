"""
Application Settings and Configuration Management

This module loads and validates environment variables.
Never hardcode secrets - always use environment variables!
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    
    Security Rules:
    1. Never hardcode secrets
    2. Always use environment variables
    3. Validate secrets on startup
    4. Use .env.example as template
    5. Never commit .env to git
    """
    
    # ========================================================================
    # DATABASE
    # ========================================================================
    DATABASE_URL: str = Field(
        ..., 
        description="MS SQL Server connection string"
    )
    
    # ========================================================================
    # SECURITY - JWT & SECRETS
    # ========================================================================
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT encoding (min 32 chars). Generate: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
    
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm (HS256 recommended)"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=480,  # 8 hours
        ge=1,
        le=1440,  # Max 24 hours
        description="JWT token expiration in minutes"
    )
    
    # ========================================================================
    # CORS
    # ========================================================================
    ALLOWED_ORIGINS_STR: str = Field(
        default="http://localhost:4200",
        description="Comma-separated list of allowed origins (or JSON array)"
    )
    
    # Parsed list of allowed origins (set after parsing ALLOWED_ORIGINS_STR)
    allowed_origins: List[str] = Field(
        default=["http://localhost:4200"],
        exclude=True,  # Don't include in validation
        description="Parsed list of CORS origins"
    )
    
    # ========================================================================
    # AZURE
    # ========================================================================
    AZURE_STORAGE_CONNECTION_STRING: str = Field(
        ...,
        description="Azure Blob Storage connection string"
    )
    
    AZURE_CONTAINER_NAME: str = Field(
        default="attendance-records",
        description="Azure container name for file uploads"
    )
    
    # ========================================================================
    # EMAIL (SMTP)
    # ========================================================================
    SMTP_HOST: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname"
    )
    
    SMTP_PORT: int = Field(
        default=587,
        description="SMTP server port"
    )
    
    SMTP_USER: str = Field(
        ...,
        description="SMTP username/email"
    )
    
    SMTP_PASSWORD: str = Field(
        ...,
        description="SMTP password or app-specific password"
    )
    
    SMTP_FROM: str = Field(
        default="noreply@rbistech.com",
        description="Email sender address"
    )
    
    # ========================================================================
    # APPLICATION ENVIRONMENT
    # ========================================================================
    DEBUG: bool = Field(
        default=False,
        description="Debug mode (set to False in production)"
    )
    
    ENVIRONMENT: str = Field(
        default="development",
        description="Application environment: development, staging, production"
    )
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    # ========================================================================
    # OTP SETTINGS
    # ========================================================================
    ENABLE_OTP_EMAIL: bool = Field(
        default=True,
        description="Enable email OTP verification"
    )
    
    OTP_EXPIRY_MINUTES: int = Field(
        default=10,
        ge=1,
        le=60,
        description="OTP validity period in minutes"
    )
    
    MAX_OTP_ATTEMPTS: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum failed OTP attempts before lockout"
    )
    
    # ========================================================================
    # RATE LIMITING
    # ========================================================================
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    
    RATE_LIMIT_REQUESTS: int = Field(
        default=10,
        ge=1,
        description="Number of requests allowed per period"
    )
    
    RATE_LIMIT_PERIOD: int = Field(
        default=60,
        ge=1,
        description="Rate limit period in seconds"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore unknown fields
    
    def __init__(self, **data):
        """Initialize settings and validate"""
        super().__init__(**data)
        # Parse ALLOWED_ORIGINS from string
        self._parse_allowed_origins()
        self._validate_settings()
    
    def _parse_allowed_origins(self):
        """Parse ALLOWED_ORIGINS_STR into list"""
        try:
            import json
            # Try to parse as JSON first
            if self.ALLOWED_ORIGINS_STR.strip().startswith('['):
                self.allowed_origins = json.loads(self.ALLOWED_ORIGINS_STR)
            else:
                # Parse as comma-separated string
                origins = [o.strip() for o in self.ALLOWED_ORIGINS_STR.split(',') if o.strip()]
                self.allowed_origins = origins if origins else ["http://localhost:4200"]
        except Exception:
            # Fallback to default
            self.allowed_origins = ["http://localhost:4200"]
    
    def _validate_settings(self):
        """Validate critical settings on startup"""
        # Warn if using default/weak secret in non-production
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        # Warn if debug is enabled in production
        if self.DEBUG and self.ENVIRONMENT == "production":
            raise ValueError("DEBUG cannot be True in production environment")
        
        # Ensure CORS origins are specified for production
        if self.ENVIRONMENT == "production" and "localhost" in str(self.allowed_origins):
            raise ValueError("Localhost not allowed in production CORS origins")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"
    
    def get_database_url(self) -> str:
        """Get database connection string"""
        return self.DATABASE_URL
    
    def get_jwt_settings(self) -> dict:
        """Get JWT configuration"""
        return {
            "secret_key": self.SECRET_KEY,
            "algorithm": self.ALGORITHM,
            "expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================
# Load settings once at application startup
try:
    settings = Settings()
except Exception as e:
    print(f"❌ Failed to load settings: {e}")
    print("Make sure .env file is configured. Use .env.example as template.")
    raise


def get_settings() -> Settings:
    """
    Get the global settings instance.
    Used for dependency injection in FastAPI.
    """
    return settings


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
"""
# In your FastAPI application:

from app.core.config import settings

# Use settings anywhere in your app
app = FastAPI(debug=settings.DEBUG)

# For JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

# For CORS
ALLOWED_ORIGINS = settings.ALLOWED_ORIGINS

# For Email
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT

# Check environment
if settings.is_production:
    print("Running in production mode")
"""
