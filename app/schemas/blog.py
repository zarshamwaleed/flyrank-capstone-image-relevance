from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BlogPostBase(BaseModel):
    title: str
    content: str


class BlogPostCreate(BlogPostBase):
    pass


class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class BlogPostResponse(BlogPostBase):
    id: int
    embedding_model: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BlogPostWithEmbedding(BlogPostResponse):
    embedding_vector: Optional[List[float]] = None
