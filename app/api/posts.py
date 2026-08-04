from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.post import BlogPost
from app.models.suggestion import Suggestion
from app.schemas.blog import BlogPostCreate, BlogPostUpdate, BlogPostResponse, BlogPostWithEmbedding
from app.services.embedding_service import embedding_service
from app.services.matching_service import matching_service

router = APIRouter()


@router.post("/", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
async def create_blog_post(
    post: BlogPostCreate,
    db: Session = Depends(get_db)
):
    # Create blog post
    db_post = BlogPost(
        title=post.title,
        content=post.content
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    # Generate embedding
    try:
        updated = embedding_service.embed_blog_post(db_post.id, db)
        if updated:
            db.refresh(db_post)
            print(f'✅ Embedding generated for blog post {db_post.id}')
    except Exception as e:
        print(f'⚠️ Warning: Failed to generate embedding: {e}')
    
    # AUTO-SAVE SUGGESTIONS WITH AUTO-REJECT FOR LOW SCORES
    try:
        matches, total = matching_service.find_matches(db_post.id, db, 5, 0)
        if matches:
            print(f'🔄 Auto-saving {len(matches)} suggestions for post {db_post.id}')
            for i, match in enumerate(matches, 1):
                similarity = match['similarity_score']
                
                # AUTO-REJECT if similarity is below 25%
                if similarity < 0.25:
                    guard_passed = 'rejected'
                    guard_reason = f'Auto-rejected: Similarity {similarity:.1%} below 25% threshold'
                else:
                    guard_passed = 'pending'
                    guard_reason = None
                
                suggestion = Suggestion(
                    post_id=db_post.id,
                    image_id=match['image_id'],
                    similarity_score=similarity,
                    guard_passed=guard_passed,
                    guard_reason=guard_reason,
                    rank=i
                )
                db.add(suggestion)
            db.commit()
            print(f'✅ Auto-saved {len(matches)} suggestions for post {db_post.id} to Reviews')
    except Exception as e:
        print(f'⚠️ Warning: Failed to auto-save suggestions: {e}')
    
    return db_post


@router.get("/", response_model=List[BlogPostResponse])
async def list_blog_posts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).offset(skip).limit(limit).all()
    return posts


@router.get("/{post_id}", response_model=BlogPostWithEmbedding)
async def get_blog_post(
    post_id: int,
    include_embedding: bool = False,
    db: Session = Depends(get_db)
):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog post with ID {post_id} not found"
        )
    return post


@router.put("/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: int,
    post_update: BlogPostUpdate,
    db: Session = Depends(get_db)
):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog post with ID {post_id} not found"
        )
    
    if post_update.title is not None:
        post.title = post_update.title
    if post_update.content is not None:
        post.content = post_update.content
    
    post.embedding_vector = None
    post.embedding_model = None
    
    db.commit()
    db.refresh(post)
    
    try:
        updated = embedding_service.embed_blog_post(post_id, db)
        if updated:
            db.refresh(post)
            print(f'✅ Embedding regenerated for blog post {post_id}')
    except Exception as e:
        print(f'⚠️ Warning: Failed to regenerate embedding: {e}')
    
    return post


@router.delete("/{post_id}")
async def delete_blog_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog post with ID {post_id} not found"
        )
    
    db.delete(post)
    db.commit()
    
    return {
        "message": f"Blog post {post_id} deleted successfully",
        "post_id": post_id,
        "title": post.title
    }


@router.post("/{post_id}/regenerate-embedding")
async def regenerate_post_embedding(
    post_id: int,
    db: Session = Depends(get_db)
):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog post with ID {post_id} not found"
        )
    
    updated = embedding_service.embed_blog_post(post_id, db)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embedding for blog post {post_id}"
        )
    
    return {
        "message": f"Embedding regenerated for blog post {post_id}",
        "post_id": post_id,
        "dimensions": len(updated.embedding_vector) if updated.embedding_vector else 0,
        "model": updated.embedding_model
    }


@router.get("/stats/count")
async def get_blog_stats(db: Session = Depends(get_db)):
    total = db.query(BlogPost).count()
    with_embeddings = db.query(BlogPost).filter(BlogPost.embedding_vector.isnot(None)).count()
    
    return {
        "total_posts": total,
        "with_embeddings": with_embeddings,
        "without_embeddings": total - with_embeddings
    }
