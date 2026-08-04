from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


class ReviewBase(BaseModel):
    suggestion_id: int
    decision: ReviewDecision
    reviewer_notes: Optional[str] = None
    reviewer: Optional[str] = "admin"


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    id: int
    reviewed_at: datetime
    
    class Config:
        from_attributes = True


class SuggestionWithReview(BaseModel):
    id: int
    post_id: int
    image_id: int
    similarity_score: float
    guard_passed: str
    guard_reason: Optional[str] = None
    rank: Optional[int] = None
    created_at: datetime
    review: Optional[ReviewResponse] = None
    
    # Additional info
    post_title: Optional[str] = None
    image_filename: Optional[str] = None
    image_subject: Optional[str] = None
    image_category: Optional[str] = None


class ReviewStats(BaseModel):
    total_suggestions: int
    pending: int
    approved: int
    rejected: int
    approval_rate: float
