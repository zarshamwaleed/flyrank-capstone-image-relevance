from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Suggestion(Base):
    __tablename__ = "suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    
    similarity_score = Column(Float, nullable=False)
    guard_passed = Column(String(20), default="pending")  # pending, passed, rejected
    guard_reason = Column(Text, nullable=True)
    rank = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    post = relationship("BlogPost", back_populates="suggestions")
    image = relationship("Image", back_populates="suggestions")
    review = relationship("Review", back_populates="suggestion", uselist=False, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_suggestions_post", "post_id"),
        Index("idx_suggestions_image", "image_id"),
        Index("idx_suggestions_score", "similarity_score"),
        Index("idx_suggestions_guard", "guard_passed"),
        Index("idx_suggestions_post_rank", "post_id", "rank"),  # Composite index for ranking queries
    )
