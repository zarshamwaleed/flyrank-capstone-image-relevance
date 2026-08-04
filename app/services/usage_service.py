from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.usage import AIUsageLog


class UsageTrackingService:
    # Service for tracking AI usage
    
    def get_usage_stats(self, db: Session, days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        total = db.query(AIUsageLog).filter(AIUsageLog.created_at >= cutoff).count()
        vision = db.query(AIUsageLog).filter(
            AIUsageLog.service == "vision",
            AIUsageLog.created_at >= cutoff
        ).count()
        embedding = db.query(AIUsageLog).filter(
            AIUsageLog.service == "embedding",
            AIUsageLog.created_at >= cutoff
        ).count()
        success = db.query(AIUsageLog).filter(
            AIUsageLog.status == "success",
            AIUsageLog.created_at >= cutoff
        ).count()
        failed = db.query(AIUsageLog).filter(
            AIUsageLog.status == "failed",
            AIUsageLog.created_at >= cutoff
        ).count()
        
        total_savings = db.query(func.sum(AIUsageLog.cost_savings_usd)).filter(
            AIUsageLog.created_at >= cutoff
        ).scalar() or 0.0
        
        avg_time = db.query(func.avg(AIUsageLog.response_time_ms)).filter(
            AIUsageLog.created_at >= cutoff,
            AIUsageLog.response_time_ms.isnot(None)
        ).scalar() or 0.0
        
        return {
            "period_days": days,
            "total_requests": total,
            "vision_requests": vision,
            "embedding_requests": embedding,
            "success_rate": success / total if total > 0 else 0,
            "failed_requests": failed,
            "total_cost_savings_usd": total_savings,
            "avg_response_time_ms": avg_time,
            "savings_estimate": {
                "monthly": total_savings * (30 / days) if days > 0 else 0,
                "yearly": total_savings * (365 / days) if days > 0 else 0
            }
        }
    
    def get_model_usage(self, db: Session) -> Dict[str, Any]:
        models = db.query(
            AIUsageLog.model,
            func.count().label('count')
        ).group_by(AIUsageLog.model).all()
        
        return {"models": [{"model": m.model, "count": m.count} for m in models]}


usage_tracker = UsageTrackingService()
