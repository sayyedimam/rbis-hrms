from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
settings = get_settings()
from app.api.router import api_router
from app.core.database import engine
from app.models import models #, notice

# Sync Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RBIS HR Management System API", version="2.0.0")

# CORS Configuration - Use allowed origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include Central Routerz
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to RBIS HRMS API", "status": "Online"}

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings
    settings = get_settings()
    # Disable reload in production for better performance
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=(settings.ENVIRONMENT == "development"), log_level=settings.LOG_LEVEL.lower())
