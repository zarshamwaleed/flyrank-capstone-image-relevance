from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class GuardDecision(str, Enum):
    PASSED = "passed"
    REJECTED = "rejected"
    PENDING = "pending"


class GuardCheck(BaseModel):
    check_name: str
    passed: bool
    reason: Optional[str] = None
    details: Optional[str] = None


class GuardResult(BaseModel):
    decision: GuardDecision
    overall_passed: bool
    checks: List[GuardCheck]
    explanation: str
    recommendation: Optional[dict] = None
    recommended_image_id: Optional[int] = None


class MatchRequest(BaseModel):
    post_id: int
    image_id: Optional[int] = None
    top_k: int = 5
    min_similarity: float = 0.4
    require_subject_match: bool = True
    require_category_match: bool = False
    min_confidence: float = 0.7
