from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.post import BlogPost
from app.models.image import Image
from app.services.matching_service import matching_service
from app.schemas.matching import MatchResponse, MatchCandidate

router = APIRouter()


@router.post("/posts/{post_id}/match")
async def find_matches(
    post_id: int,
    top_k: int = 5,
    min_similarity: float = 0.0,
    db: Session = Depends(get_db)
):
    # Find matching images for a blog post
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog post with ID {post_id} not found"
        )
    
    if not post.embedding_vector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Blog post {post_id} has no embedding. Please generate embedding first."
        )
    
    result = matching_service.get_post_recommendations(
        post_id, db, top_k, min_similarity
    )
    
    # Convert to response format
    matches = []
    for m in result["matches"]:
        matches.append(MatchCandidate(
            image_id=m["image_id"],
            filename=m["filename"],
            similarity_score=m["similarity_score"],
            subject=m["subject"],
            category=m["category"],
            caption=m["caption"]
        ))
    
    return {
        "post_id": result["post_id"],
        "post_title": result["post_title"],
        "matches": matches,
        "top_match": matches[0] if matches else None,
        "total_candidates": result["total_candidates"]
    }


@router.get("/posts/{post_id}/matches")
async def get_matches(
    post_id: int,
    top_k: int = 5,
    min_similarity: float = 0.0,
    db: Session = Depends(get_db)
):
    # Get matching images for a blog post (GET version)
    return await find_matches(post_id, top_k, min_similarity, db)


@router.post("/images/{image_id}/similar")
async def find_similar_images(
    image_id: int,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    # Find similar images based on embedding similarity
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    if not image.embedding or not image.embedding.embedding_vector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image {image_id} has no embedding"
        )
    
    # Get all other images with embeddings
    images = db.query(Image).join(ImageEmbedding).filter(
        Image.id != image_id,
        Image.processing_status == "completed"
    ).all()
    
    matches = []
    for img in images:
        if not img.embedding or not img.embedding.embedding_vector:
            continue
        
        similarity = matching_service.cosine_similarity(
            image.embedding.embedding_vector,
            img.embedding.embedding_vector
        )
        
        matches.append({
            "image_id": img.id,
            "filename": img.filename,
            "similarity_score": similarity,
            "subject": img.image_metadata.subject if img.image_metadata else None,
            "category": img.image_metadata.category if img.image_metadata else None
        })
    
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    top_matches = matches[:top_k]
    
    return {
        "source_image_id": image_id,
        "source_filename": image.filename,
        "matches": top_matches,
        "total_similar": len(matches)
    }


@router.get("/stats")
async def get_matching_stats(db: Session = Depends(get_db)):
    # Get statistics about matching
    total_posts = db.query(BlogPost).count()
    posts_with_embeddings = db.query(BlogPost).filter(BlogPost.embedding_vector.isnot(None)).count()
    
    total_images = db.query(Image).count()
    images_with_embeddings = db.query(Image).join(ImageEmbedding).count()
    images_processed = db.query(Image).filter(Image.processing_status == "completed").count()
    
    return {
        "total_posts": total_posts,
        "posts_with_embeddings": posts_with_embeddings,
        "total_images": total_images,
        "images_with_embeddings": images_with_embeddings,
        "images_processed": images_processed,
        "ready_for_matching": posts_with_embeddings > 0 and images_with_embeddings > 0
    }
