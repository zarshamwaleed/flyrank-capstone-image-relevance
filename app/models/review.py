from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    suggestion_id = Column(Integer, ForeignKey("suggestions.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    decision = Column(String(20), nullable=False)  # approved, rejected
    reviewer_notes = Column(Text, nullable=True)
    reviewer = Column(String(100), default="admin")
    
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    suggestion = relationship("Suggestion", back_populates="review")
    
    # Indexes
    __table_args__ = (
        Index("idx_reviews_decision", "decision"),
        Index("idx_reviews_reviewer", "reviewer"),
        Index("idx_reviews_reviewed", "reviewed_at"),
    )
