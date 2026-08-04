from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
import sys

from app.core.database import get_db
from app.core.config import settings
from app.core.logging import app_logger

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    \"\"\"
    Health check endpoint.
    Checks database connectivity and returns system status.
    \"\"\"
    status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Check database
    try:
        result = db.execute(text("SELECT 1"))
        status["database"] = "connected"
        app_logger.debug("Database health check passed")
    except Exception as e:
        status["status"] = "unhealthy"
        status["database"] = f"error: {str(e)}"
        app_logger.error(f"Database health check failed: {e}")
        return status
    
    # Check Python version
    status["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Check if in debug mode
    status["debug"] = settings.DEBUG
    
    return status


@router.get("/health/ready")
async def readiness_check():
    \"\"\"
    Readiness probe for container orchestration.
    \"\"\"
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
async def liveness_check():
    \"\"\"
    Liveness probe for container orchestration.
    \"\"\"
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
