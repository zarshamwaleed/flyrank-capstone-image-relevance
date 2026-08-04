from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    
    embedding_vector = Column(JSON, nullable=True)  # List of floats
    embedding_model = Column(String(100), default="text-embedding-004")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    suggestions = relationship("Suggestion", back_populates="post", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_posts_created", "created_at"),
    )
