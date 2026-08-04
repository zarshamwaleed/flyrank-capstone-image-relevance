from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.post import BlogPost
from app.models.image import Image
from app.models.suggestion import Suggestion
from app.services.guard_service import guard

router = APIRouter()


@router.get("/check")
async def check_match(
    post_id: int = Query(...),
    image_id: int = Query(...),
    min_similarity: float = Query(0.4, ge=0.0, le=1.0),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0),
    require_subject_match: bool = Query(True),
    db: Session = Depends(get_db)
):
    result = guard.guard_match(
        post_id, image_id, db,
        min_similarity, min_confidence,
        require_subject_match
    )
    return result


@router.get("/recommend/{post_id}")
async def get_safe_recommendations(
    post_id: int,
    top_k: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.4, ge=0.0, le=1.0),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0),
    require_subject_match: bool = Query(True),
    db: Session = Depends(get_db)
):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog post with ID {post_id} not found"
        )
    
    if not post.embedding_vector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Blog post {post_id} has no embedding"
        )
    
    result = guard.get_safe_recommendations(
        post_id, db, top_k,
        min_similarity, min_confidence,
        require_subject_match
    )
    
    return result


@router.get("/stats")
async def get_guard_stats(db: Session = Depends(get_db)):
    total_suggestions = db.query(Suggestion).count()
    passed = db.query(Suggestion).filter(Suggestion.guard_passed == "passed").count()
    rejected = db.query(Suggestion).filter(Suggestion.guard_passed == "rejected").count()
    pending = db.query(Suggestion).filter(Suggestion.guard_passed == "pending").count()
    
    return {
        "total_suggestions": total_suggestions,
        "passed": passed,
        "rejected": rejected,
        "pending": pending,
        "pass_rate": passed / total_suggestions if total_suggestions > 0 else 0
    }


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db)
):
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion with ID {suggestion_id} not found"
        )
    
    suggestion.guard_passed = "passed"
    db.commit()
    
    return {
        "message": f"Suggestion {suggestion_id} approved",
        "suggestion_id": suggestion_id,
        "status": "passed"
    }


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db)
):
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion with ID {suggestion_id} not found"
        )
    
    suggestion.guard_passed = "rejected"
    db.commit()
    
    return {
        "message": f"Suggestion {suggestion_id} rejected",
        "suggestion_id": suggestion_id,
        "status": "rejected"
    }
