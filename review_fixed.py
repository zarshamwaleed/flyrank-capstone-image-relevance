from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.suggestion import Suggestion
from app.models.review import Review
from app.models.image import Image
from app.models.post import BlogPost
from app.services.review_service import review_service

router = APIRouter()


@router.get("/stats")
async def get_review_stats(db: Session = Depends(get_db)):
    total = db.query(Suggestion).count()
    
    # Count pending suggestions (no review yet)
    pending = db.query(Suggestion).filter(
        Suggestion.review == None
    ).count()
    
    approved = db.query(Suggestion).join(Review).filter(Review.decision == "approved").count()
    rejected = db.query(Suggestion).join(Review).filter(Review.decision == "rejected").count()
    reviewed = approved + rejected
    
    return {
        "total_suggestions": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "reviewed": reviewed,
        "approval_rate": approved / reviewed if reviewed > 0 else 0
    }


@router.get("/suggestions")
async def get_suggestions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str = Query(None, pattern="^(pending|approved|rejected)$"),
    db: Session = Depends(get_db)
):
    query = db.query(Suggestion)
    
    if status == "pending":
        query = query.filter(Suggestion.review == None)
    elif status == "approved":
        query = query.join(Review).filter(Review.decision == "approved")
    elif status == "rejected":
        query = query.join(Review).filter(Review.decision == "rejected")
    
    suggestions = query.order_by(desc(Suggestion.created_at)).offset(skip).limit(limit).all()
    
    results = []
    for s in suggestions:
        post = db.query(BlogPost).filter(BlogPost.id == s.post_id).first()
        image = db.query(Image).filter(Image.id == s.image_id).first()
        
        result = {
            "id": s.id,
            "post_id": s.post_id,
            "image_id": s.image_id,
            "similarity_score": s.similarity_score,
            "guard_passed": s.guard_passed,
            "guard_reason": s.guard_reason,
            "rank": s.rank,
            "created_at": s.created_at,
            "post_title": post.title if post else "Unknown",
            "image_filename": image.filename if image else "Unknown",
        }
        
        if s.review:
            result["review"] = {
                "id": s.review.id,
                "decision": s.review.decision,
                "reviewer_notes": s.review.reviewer_notes,
                "reviewer": s.review.reviewer,
                "reviewed_at": s.review.reviewed_at
            }
        
        results.append(result)
    
    return {
        "total": len(results),
        "suggestions": results
    }


@router.get("/suggestions/pending")
async def get_pending_suggestions(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    suggestions = db.query(Suggestion).filter(
        Suggestion.review == None
    ).order_by(desc(Suggestion.created_at)).limit(limit).all()
    
    results = []
    for s in suggestions:
        post = db.query(BlogPost).filter(BlogPost.id == s.post_id).first()
        image = db.query(Image).filter(Image.id == s.image_id).first()
        
        results.append({
            "id": s.id,
            "post_id": s.post_id,
            "image_id": s.image_id,
            "similarity_score": s.similarity_score,
            "guard_passed": s.guard_passed,
            "guard_reason": s.guard_reason,
            "rank": s.rank,
            "created_at": s.created_at,
            "post_title": post.title if post else "Unknown",
            "image_filename": image.filename if image else "Unknown",
        })
    
    return {
        "total": len(results),
        "suggestions": results
    }


@router.get("/suggestions/{suggestion_id}")
async def get_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db)
):
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion with ID {suggestion_id} not found"
        )
    
    post = db.query(BlogPost).filter(BlogPost.id == suggestion.post_id).first()
    image = db.query(Image).filter(Image.id == suggestion.image_id).first()
    
    result = {
        "id": suggestion.id,
        "post_id": suggestion.post_id,
        "image_id": suggestion.image_id,
        "similarity_score": suggestion.similarity_score,
        "guard_passed": suggestion.guard_passed,
        "guard_reason": suggestion.guard_reason,
        "rank": suggestion.rank,
        "created_at": suggestion.created_at,
        "post_title": post.title if post else "Unknown",
        "image_filename": image.filename if image else "Unknown",
    }
    
    if suggestion.review:
        result["review"] = {
            "id": suggestion.review.id,
            "decision": suggestion.review.decision,
            "reviewer_notes": suggestion.review.reviewer_notes,
            "reviewer": suggestion.review.reviewer,
            "reviewed_at": suggestion.review.reviewed_at
        }
    
    return result


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(
    suggestion_id: int,
    reviewer: str = Query("admin"),
    notes: str = Query(None),
    db: Session = Depends(get_db)
):
    result = review_service.approve_suggestion(suggestion_id, db, reviewer, notes)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: int,
    reviewer: str = Query("admin"),
    notes: str = Query(None),
    db: Session = Depends(get_db)
):
    result = review_service.reject_suggestion(suggestion_id, db, reviewer, notes)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result


@router.get("/history")
async def get_review_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    suggestions = db.query(Suggestion).join(Review).order_by(desc(Review.reviewed_at)).offset(skip).limit(limit).all()
    results = []
    for s in suggestions:
        post = db.query(BlogPost).filter(BlogPost.id == s.post_id).first()
        image = db.query(Image).filter(Image.id == s.image_id).first()
        results.append({
            "id": s.id,
            "post_id": s.post_id,
            "image_id": s.image_id,
            "similarity_score": s.similarity_score,
            "guard_passed": s.guard_passed,
            "rank": s.rank,
            "created_at": s.created_at,
            "post_title": post.title if post else "Unknown",
            "image_filename": image.filename if image else "Unknown",
            "review": {
                "decision": s.review.decision if s.review else None,
                "reviewer_notes": s.review.reviewer_notes if s.review else None,
                "reviewer": s.review.reviewer if s.review else None,
                "reviewed_at": s.review.reviewed_at if s.review else None
            } if s.review else None
        })
    
    return {
        "total": len(results),
        "history": results
    }
