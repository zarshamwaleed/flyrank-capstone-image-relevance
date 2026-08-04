from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.sql import func

from app.core.database import Base


class CostLog(Base):
    __tablename__ = "cost_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    service = Column(String(50), nullable=False)  # vision, embedding
    model = Column(String(100), nullable=False)
    
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    estimated_cost = Column(Float, default=0.0)
    
    request_id = Column(String(100), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    status = Column(String(20), default="success")  # success, failed, retry
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_cost_service", "service"),
        Index("idx_cost_model", "model"),
        Index("idx_cost_status", "status"),
        Index("idx_cost_created", "created_at"),
        Index("idx_cost_service_created", "service", "created_at"),  # Composite for analytics
    )
