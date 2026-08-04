from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    processing_status = Column(String(50), default="pending")
    processing_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Renamed from 'metadata' to 'image_metadata' to avoid conflict
    image_metadata = relationship("ImageMetadata", back_populates="image", uselist=False, cascade="all, delete-orphan")
    embedding = relationship("ImageEmbedding", back_populates="image", uselist=False, cascade="all, delete-orphan")
    suggestions = relationship("Suggestion", back_populates="image", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_images_status", "processing_status"),
        Index("idx_images_created", "created_at"),
    )


class ImageMetadata(Base):
    __tablename__ = "image_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    subject = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    caption = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    confidence = Column(Float, nullable=False)
    
    raw_response = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    image = relationship("Image", back_populates="image_metadata")
    
    __table_args__ = (
        Index("idx_metadata_subject", "subject"),
        Index("idx_metadata_category", "category"),
        Index("idx_metadata_confidence", "confidence"),
    )


class ImageEmbedding(Base):
    __tablename__ = "image_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    embedding_vector = Column(JSON, nullable=False)
    model = Column(String(100), default="text-embedding-004")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    image = relationship("Image", back_populates="embedding")
    
    __table_args__ = (
        Index("idx_embedding_model", "model"),
    )
