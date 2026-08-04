from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.suggestion import Suggestion
from app.models.review import Review
from app.models.image import Image
from app.models.post import BlogPost


class ReviewService:
    # Service for managing reviews
    
    def get_suggestion_with_details(self, suggestion: Suggestion, db: Session) -> Dict[str, Any]:
        # Get suggestion with post and image details
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
            "post_title": post.title if post else None,
            "image_filename": image.filename if image else None,
            "image_subject": image.image_metadata.subject if image and image.image_metadata else None,
            "image_category": image.image_metadata.category if image and image.image_metadata else None,
        }
        
        # Add review if exists
        if suggestion.review:
            result["review"] = {
                "id": suggestion.review.id,
                "decision": suggestion.review.decision,
                "reviewer_notes": suggestion.review.reviewer_notes,
                "reviewer": suggestion.review.reviewer,
                "reviewed_at": suggestion.review.reviewed_at
            }
        
        return result
    
    def get_pending_suggestions(self, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        # Get all pending suggestions
        suggestions = db.query(Suggestion).filter(
            Suggestion.guard_passed == "pending"
        ).order_by(desc(Suggestion.created_at)).limit(limit).all()
        
        return [self.get_suggestion_with_details(s, db) for s in suggestions]
    
    def get_all_suggestions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # Get all suggestions with optional status filter
        query = db.query(Suggestion)
        
        if status:
            if status == "pending":
                query = query.filter(Suggestion.guard_passed == "pending")
            elif status == "approved":
                query = query.join(Review).filter(Review.decision == "approved")
            elif status == "rejected":
                query = query.join(Review).filter(Review.decision == "rejected")
        
        suggestions = query.order_by(desc(Suggestion.created_at)).offset(skip).limit(limit).all()
        return [self.get_suggestion_with_details(s, db) for s in suggestions]
    
    def approve_suggestion(
        self,
        suggestion_id: int,
        db: Session,
        reviewer: str = "admin",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        # Approve a suggestion
        suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
        if not suggestion:
            return {"error": f"Suggestion {suggestion_id} not found"}
        
        # Check if already reviewed
        if suggestion.review:
            return {"error": f"Suggestion {suggestion_id} already reviewed"}
        
        # Create review
        review = Review(
            suggestion_id=suggestion_id,
            decision="approved",
            reviewer_notes=notes,
            reviewer=reviewer
        )
        
        db.add(review)
        suggestion.guard_passed = "passed"
        db.commit()
        db.refresh(review)
        
        return {
            "message": f"Suggestion {suggestion_id} approved",
            "suggestion_id": suggestion_id,
            "review": {
                "id": review.id,
                "decision": review.decision,
                "reviewer": review.reviewer,
                "reviewed_at": review.reviewed_at
            }
        }
    
    def reject_suggestion(
        self,
        suggestion_id: int,
        db: Session,
        reviewer: str = "admin",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        # Reject a suggestion
        suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
        if not suggestion:
            return {"error": f"Suggestion {suggestion_id} not found"}
        
        # Check if already reviewed
        if suggestion.review:
            return {"error": f"Suggestion {suggestion_id} already reviewed"}
        
        # Create review
        review = Review(
            suggestion_id=suggestion_id,
            decision="rejected",
            reviewer_notes=notes,
            reviewer=reviewer
        )
        
        db.add(review)
        suggestion.guard_passed = "rejected"
        db.commit()
        db.refresh(review)
        
        return {
            "message": f"Suggestion {suggestion_id} rejected",
            "suggestion_id": suggestion_id,
            "review": {
                "id": review.id,
                "decision": review.decision,
                "reviewer": review.reviewer,
                "reviewed_at": review.reviewed_at
            }
        }
    
    def get_review_stats(self, db: Session) -> Dict[str, Any]:
        # Get review statistics
        total = db.query(Suggestion).count()
        pending = db.query(Suggestion).filter(Suggestion.guard_passed == "pending").count()
        
        approved = db.query(Suggestion).join(Review).filter(Review.decision == "approved").count()
        rejected = db.query(Suggestion).join(Review).filter(Review.decision == "rejected").count()
        
        reviewed = approved + rejected
        approval_rate = approved / reviewed if reviewed > 0 else 0
        
        return {
            "total_suggestions": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "reviewed": reviewed,
            "approval_rate": approval_rate
        }


# Create singleton instance
review_service = ReviewService()
