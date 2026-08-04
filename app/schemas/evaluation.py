from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class EvaluationSample(BaseModel):
    post_id: int
    post_title: str
    correct_image_id: int
    correct_image_filename: Optional[str] = None
    correct_subject: Optional[str] = None


class EvaluationResult(BaseModel):
    total_samples: int
    correct_predictions: int
    top1_precision: float
    top3_precision: float
    top5_precision: float
    mean_reciprocal_rank: float
    results: List[Dict[str, Any]]
    recommendations: str


class EvaluationReport(BaseModel):
    timestamp: datetime
    samples_count: int
    top1_precision: float
    top3_precision: float
    top5_precision: float
    mean_reciprocal_rank: float
    summary: str
    details: List[Dict[str, Any]]
