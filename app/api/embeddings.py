from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.image import Image
from app.models.post import BlogPost
from app.services.embedding_service import embedding_service

router = APIRouter()


@router.post("/images/{image_id}/embed")
async def embed_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    # Generate embedding for an image
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    # Check if image has metadata
    if not image.image_metadata:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image {image_id} has no metadata. Please process the image first."
        )
    
    embedding = embedding_service.embed_image_caption(image_id, db)
    
    if not embedding:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embedding for image {image_id}"
        )
    
    return {
        "message": f"Embedding generated for image {image_id}",
        "image_id": image_id,
        "dimensions": len(embedding.embedding_vector),
        "model": embedding.model
    }


@router.post("/posts/{post_id}/embed")
async def embed_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    # Generate embedding for a blog post
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
        "message": f"Embedding generated for blog post {post_id}",
        "post_id": post_id,
        "dimensions": len(updated.embedding_vector),
        "model": updated.embedding_model
    }


@router.post("/embed-all")
async def embed_all(db: Session = Depends(get_db)):
    # Generate embeddings for all images and blog posts
    results = {
        "images": embedding_service.embed_all_images(db),
        "posts": embedding_service.embed_all_posts(db)
    }
    
    total_images = results["images"]["total"]
    success_images = results["images"]["success"]
    total_posts = results["posts"]["total"]
    success_posts = results["posts"]["success"]
    
    return {
        "message": f"Generated embeddings: {success_images}/{total_images} images, {success_posts}/{total_posts} posts",
        "results": results
    }


@router.get("/images/{image_id}/embedding")
async def get_image_embedding(
    image_id: int,
    db: Session = Depends(get_db)
):
    # Get the embedding for an image
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    if not image.embedding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No embedding found for image {image_id}"
        )
    
    return {
        "image_id": image_id,
        "filename": image.filename,
        "dimensions": len(image.embedding.embedding_vector),
        "model": image.embedding.model,
        "embedding": image.embedding.embedding_vector[:10],  # Show first 10 values
        "full_embedding": image.embedding.embedding_vector
    }


@router.get("/posts/{post_id}/embedding")
async def get_post_embedding(
    post_id: int,
    db: Session = Depends(get_db)
):
    # Get the embedding for a blog post
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog post with ID {post_id} not found"
        )
    
    if not post.embedding_vector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No embedding found for blog post {post_id}"
        )
    
    return {
        "post_id": post_id,
        "title": post.title,
        "dimensions": len(post.embedding_vector),
        "model": post.embedding_model,
        "embedding": post.embedding_vector[:10],  # Show first 10 values
        "full_embedding": post.embedding_vector
    }
