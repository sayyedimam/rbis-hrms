from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
settings = get_settings()
from contextlib import asynccontextmanager
from app.api.router import api_router
from app.core.database import engine
from app.models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events (startup/shutdown)"""
    # Sync Database Tables on startup
    try:
        # In production, use migrations (alembic). In dev, create_all is convenient.
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        import sys
        print(f"ERROR: Database connection failed: {e}", file=sys.stderr)
        # We don't exit(1) here to allow the app to start even if DB is down,
        # which can be useful for debugging or health checks.
    
    yield
    # Shutdown logic (if any) here

app = FastAPI(
    title="RBIS HR Management System API", 
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration - Use allowed origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include Central Router
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to RBIS HRMS API", "status": "Online"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings
    settings = get_settings()
    # Disable reload in production for better performance
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=(settings.ENVIRONMENT == "development"), log_level=settings.LOG_LEVEL.lower())
