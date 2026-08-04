from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.suggestion import Suggestion
from app.services.review_service import review_service
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewStats

router = APIRouter()


@router.get("/suggestions")
async def get_suggestions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(pending|approved|rejected)$"),
    db: Session = Depends(get_db)
):
    # Get all suggestions with optional status filter
    suggestions = review_service.get_all_suggestions(db, skip, limit, status)
    return {
        "total": len(suggestions),
        "suggestions": suggestions
    }


@router.get("/suggestions/pending")
async def get_pending_suggestions(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Get all pending suggestions
    suggestions = review_service.get_pending_suggestions(db, limit)
    return {
        "total": len(suggestions),
        "suggestions": suggestions
    }


@router.get("/suggestions/{suggestion_id}")
async def get_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db)
):
    # Get a specific suggestion with details
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion with ID {suggestion_id} not found"
        )
    
    return review_service.get_suggestion_with_details(suggestion, db)


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(
    suggestion_id: int,
    reviewer: str = Query("admin"),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Approve a suggestion
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
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Reject a suggestion
    result = review_service.reject_suggestion(suggestion_id, db, reviewer, notes)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.get("/stats")
async def get_review_stats(
    db: Session = Depends(get_db)
):
    # Get review statistics
    return review_service.get_review_stats(db)


@router.get("/history")
async def get_review_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Get reviewed suggestions (approved or rejected)
    suggestions = review_service.get_all_suggestions(db, skip, limit, "reviewed")
    return {
        "total": len(suggestions),
        "history": suggestions
    }
