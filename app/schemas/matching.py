from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MatchCandidate(BaseModel):
    image_id: int
    filename: str
    similarity_score: float
    subject: Optional[str] = None
    category: Optional[str] = None
    caption: Optional[str] = None


class MatchResponse(BaseModel):
    post_id: int
    post_title: str
    matches: List[MatchCandidate]
    top_match: Optional[MatchCandidate] = None
    total_candidates: int
