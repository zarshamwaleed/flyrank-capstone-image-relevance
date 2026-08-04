from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.usage_service import usage_tracker
from app.models.usage import AIUsageLog

router = APIRouter()


@router.get("/stats")
async def get_usage_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    return usage_tracker.get_usage_stats(db, days)


@router.get("/models")
async def get_model_usage(db: Session = Depends(get_db)):
    return usage_tracker.get_model_usage(db)


@router.get("/logs")
async def get_usage_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    logs = db.query(AIUsageLog).order_by(AIUsageLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": db.query(AIUsageLog).count(),
        "logs": [
            {
                "id": log.id,
                "service": log.service,
                "model": log.model,
                "status": log.status,
                "response_time_ms": log.response_time_ms,
                "cost_savings_usd": log.cost_savings_usd,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }
