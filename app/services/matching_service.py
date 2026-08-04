import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.image import Image, ImageEmbedding
from app.models.post import BlogPost


class SemanticMatchingService:
    # Service for semantic matching between blog posts and images
    
    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        # Calculate cosine similarity between two vectors
        if not vec_a or not vec_b:
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        
        # Calculate magnitudes
        mag_a = math.sqrt(sum(a * a for a in vec_a))
        mag_b = math.sqrt(sum(b * b for b in vec_b))
        
        if mag_a == 0 or mag_b == 0:
            return 0.0
        
        return dot_product / (mag_a * mag_b)
    
    def find_matches(
        self,
        post_id: int,
        db: Session,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> Tuple[List[Dict[str, Any]], int]:
        # Find matching images for a blog post
        try:
            # Get the blog post with embedding
            post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
            if not post:
                print(f'Blog post {post_id} not found')
                return [], 0
            
            if not post.embedding_vector:
                print(f'Blog post {post_id} has no embedding')
                return [], 0
            
            # Get all images with embeddings and metadata
            images = db.query(Image).join(ImageEmbedding).filter(
                Image.processing_status == "completed"
            ).all()
            
            if not images:
                print('No images with embeddings found')
                return [], 0
            
            # Calculate similarity scores
            matches = []
            for image in images:
                if not image.embedding or not image.embedding.embedding_vector:
                    continue
                
                similarity = self.cosine_similarity(
                    post.embedding_vector,
                    image.embedding.embedding_vector
                )
                
                # Get image metadata
                subject = None
                category = None
                caption = None
                if image.image_metadata:
                    subject = image.image_metadata.subject
                    category = image.image_metadata.category
                    caption = image.image_metadata.caption
                
                matches.append({
                    "image_id": image.id,
                    "filename": image.filename,
                    "similarity_score": similarity,
                    "subject": subject,
                    "category": category,
                    "caption": caption,
                    "image": image
                })
            
            # Sort by similarity (highest first)
            matches.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Filter by minimum similarity
            matches = [m for m in matches if m["similarity_score"] >= min_similarity]
            
            # Return top K
            total = len(matches)
            top_matches = matches[:top_k]
            
            return top_matches, total
            
        except Exception as e:
            print(f'Error finding matches: {e}')
            return [], 0
    
    def get_post_recommendations(
        self,
        post_id: int,
        db: Session,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> Dict[str, Any]:
        # Get recommendations with full details
        matches, total = self.find_matches(post_id, db, top_k, min_similarity)
        
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        
        return {
            "post_id": post_id,
            "post_title": post.title if post else "Unknown",
            "matches": matches,
            "top_match": matches[0] if matches else None,
            "total_candidates": total
        }


# Create singleton instance
matching_service = SemanticMatchingService()
