from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    service = Column(String(50), nullable=False)  # vision, embedding
    model = Column(String(100), nullable=False)
    
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    
    response_time_ms = Column(Integer, nullable=True)
    
    image_id = Column(Integer, nullable=True)
    post_id = Column(Integer, nullable=True)
    
    estimated_cost_usd = Column(Float, default=0.0)
    cost_savings_usd = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
