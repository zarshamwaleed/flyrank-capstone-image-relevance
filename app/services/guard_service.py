from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.image import Image, ImageMetadata
from app.models.post import BlogPost
from app.models.suggestion import Suggestion
from app.services.matching_service import matching_service


class MismatchGuard:
    # Mismatch Guard - Safety layer for AI recommendations
    
    def __init__(self):
        self.default_min_similarity = 0.3
        self.default_min_confidence = 0.7
        self.default_require_subject_match = False  # Disabled by default for better results
    
    def extract_post_subject(self, title: str) -> str:
        # Extract main subject from post title
        # Remove common stop words and get the main noun
        stop_words = ['the', 'a', 'an', 'understanding', 'about', 'of', 'in', 'at', 'on']
        words = title.lower().split()
        
        # Remove stop words
        meaningful_words = [w for w in words if w not in stop_words]
        
        if meaningful_words:
            # Return the first meaningful word
            return meaningful_words[0].capitalize()
        
        return title
    
    def check_similarity(self, similarity: float, threshold: float) -> Tuple[bool, str]:
        if similarity >= threshold:
            return True, f"Similarity score {similarity:.3f} meets threshold {threshold}"
        else:
            return False, f"Similarity score {similarity:.3f} is below threshold {threshold}"
    
    def check_subject_match(self, post_subject: str, image_subject: str) -> Tuple[bool, str]:
        if not post_subject or not image_subject:
            return True, "No subject information available"
        
        post_subject_lower = post_subject.lower()
        image_subject_lower = image_subject.lower()
        
        # Check for exact match
        if post_subject_lower == image_subject_lower:
            return True, f"Subject '{post_subject}' matches exactly"
        
        # Check for partial match (e.g., "red fox" vs "fox")
        post_words = set(post_subject_lower.split())
        image_words = set(image_subject_lower.split())
        
        if post_words.intersection(image_words):
            return True, f"Subjects share common words: {post_words.intersection(image_words)}"
        
        return False, f"Subject mismatch: expected '{post_subject}', got '{image_subject}'"
    
    def check_category_match(self, post_category: str, image_category: str) -> Tuple[bool, str]:
        if not post_category or not image_category:
            return True, "No category information available"
        
        if post_category.lower() == image_category.lower():
            return True, f"Category '{post_category}' matches"
        
        return False, f"Category mismatch: expected '{post_category}', got '{image_category}'"
    
    def check_confidence(self, confidence: float, min_confidence: float) -> Tuple[bool, str]:
        if confidence >= min_confidence:
            return True, f"Confidence {confidence:.2f} meets minimum {min_confidence}"
        else:
            return False, f"Confidence {confidence:.2f} is below minimum {min_confidence}"
    
    def guard_match(
        self,
        post_id: int,
        image_id: int,
        db: Session,
        min_similarity: Optional[float] = None,
        min_confidence: Optional[float] = None,
        require_subject_match: bool = False
    ) -> Dict[str, Any]:
        # Get post
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if not post:
            return {
                "decision": "rejected",
                "overall_passed": False,
                "checks": [],
                "explanation": "Post not found"
            }
        
        # Get image with metadata
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            return {
                "decision": "rejected",
                "overall_passed": False,
                "checks": [],
                "explanation": "Image not found"
            }
        
        metadata = image.image_metadata
        if not metadata:
            return {
                "decision": "rejected",
                "overall_passed": False,
                "checks": [],
                "explanation": "Image has no metadata"
            }
        
        if not image.embedding or not image.embedding.embedding_vector or not post.embedding_vector:
            return {
                "decision": "rejected",
                "overall_passed": False,
                "checks": [],
                "explanation": "Missing embeddings"
            }
        
        similarity = matching_service.cosine_similarity(
            post.embedding_vector,
            image.embedding.embedding_vector
        )
        
        min_similarity = min_similarity or self.default_min_similarity
        min_confidence = min_confidence or self.default_min_confidence
        
        # Extract post subject
        post_subject = self.extract_post_subject(post.title)
        
        checks = []
        all_passed = True
        
        # Check 1: Similarity
        sim_passed, sim_reason = self.check_similarity(similarity, min_similarity)
        checks.append({
            "check_name": "similarity",
            "passed": sim_passed,
            "reason": sim_reason,
            "details": f"Score: {similarity:.3f}, Threshold: {min_similarity}"
        })
        if not sim_passed:
            all_passed = False
        
        # Check 2: Subject match (optional)
        if require_subject_match:
            subject_passed, subject_reason = self.check_subject_match(
                post_subject,
                metadata.subject
            )
            checks.append({
                "check_name": "subject_match",
                "passed": subject_passed,
                "reason": subject_reason,
                "details": f"Post: '{post_subject}', Image: '{metadata.subject}'"
            })
            if not subject_passed:
                all_passed = False
        
        # Check 3: Confidence
        conf_passed, conf_reason = self.check_confidence(metadata.confidence, min_confidence)
        checks.append({
            "check_name": "confidence",
            "passed": conf_passed,
            "reason": conf_reason,
            "details": f"Confidence: {metadata.confidence:.2f}, Minimum: {min_confidence}"
        })
        if not conf_passed:
            all_passed = False
        
        passed_checks = [c for c in checks if c["passed"]]
        failed_checks = [c for c in checks if not c["passed"]]
        
        if all_passed:
            explanation = f"✅ All checks passed! Image '{image.filename}' is recommended."
        else:
            explanation = f"❌ Guard rejected: {len(failed_checks)} check(s) failed. "
            explanation += "; ".join([c["reason"] for c in failed_checks])
        
        return {
            "decision": "passed" if all_passed else "rejected",
            "overall_passed": all_passed,
            "checks": checks,
            "explanation": explanation,
            "similarity_score": similarity,
            "image_id": image_id,
            "filename": image.filename,
            "subject": metadata.subject,
            "category": metadata.category,
            "confidence": metadata.confidence
        }
    
    def get_safe_recommendations(
        self,
        post_id: int,
        db: Session,
        top_k: int = 5,
        min_similarity: Optional[float] = None,
        min_confidence: Optional[float] = None,
        require_subject_match: bool = False
    ) -> Dict[str, Any]:
        min_similarity = min_similarity or self.default_min_similarity
        
        matches, total = matching_service.find_matches(
            post_id, db, top_k, min_similarity
        )
        
        guarded_matches = []
        for match in matches:
            guard_result = self.guard_match(
                post_id,
                match["image_id"],
                db,
                min_similarity,
                min_confidence,
                require_subject_match
            )
            
            guarded_matches.append({
                "image_id": match["image_id"],
                "filename": match["filename"],
                "similarity_score": match["similarity_score"],
                "subject": match.get("subject"),
                "category": match.get("category"),
                "guard_decision": guard_result["decision"],
                "guard_explanation": guard_result["explanation"],
                "checks": guard_result["checks"]
            })
        
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        
        top_match = None
        for match in guarded_matches:
            if match["guard_decision"] == "passed":
                top_match = match
                break
        
        return {
            "post_id": post_id,
            "post_title": post.title if post else "Unknown",
            "all_matches": guarded_matches,
            "safe_matches": [m for m in guarded_matches if m["guard_decision"] == "passed"],
            "rejected_matches": [m for m in guarded_matches if m["guard_decision"] == "rejected"],
            "top_safe_match": top_match,
            "total_candidates": total,
            "safe_count": len([m for m in guarded_matches if m["guard_decision"] == "passed"]),
            "rejected_count": len([m for m in guarded_matches if m["guard_decision"] == "rejected"])
        }


guard = MismatchGuard()
