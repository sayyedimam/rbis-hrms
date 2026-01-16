from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.database import engine
from app.models import models, notice

# Sync Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RBIS HR Management System API", version="2.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Central Router
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to RBIS HRMS API", "status": "Online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
