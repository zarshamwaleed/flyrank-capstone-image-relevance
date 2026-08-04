import json
import requests
import numpy as np
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.image import Image, ImageMetadata, ImageEmbedding
from app.models.post import BlogPost


class OllamaEmbeddingService:
    # Service for generating embeddings using Ollama
    
    def __init__(self):
        self.base_url = settings.OLLAMA_URL or "http://resyn-ollama:11434"
        self.model = settings.EMBEDDING_MODEL or "all-minilm"
        print(f'Embedding service initialized with model: {self.model}')
        print(f'Ollama URL: {self.base_url}')
        
    def generate_embedding(self, text: str) -> List[float]:
        # Generate embedding for a text string
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            embedding = result.get("embedding", [])
            
            if not embedding:
                raise Exception("No embedding returned from Ollama")
            
            return embedding
            
        except Exception as e:
            print(f'Error generating embedding: {e}')
            return []
    
    def embed_image_caption(self, image_id: int, db: Session) -> Optional[ImageEmbedding]:
        # Generate embedding for an image's caption and store it
        try:
            # Get image metadata
            metadata = db.query(ImageMetadata).filter(ImageMetadata.image_id == image_id).first()
            if not metadata:
                print(f'No metadata found for image {image_id}')
                return None
            
            # Generate embedding from caption
            text = metadata.caption
            print(f'Generating embedding for image {image_id}: {text[:50]}...')
            
            embedding_vector = self.generate_embedding(text)
            
            if not embedding_vector:
                print(f'Failed to generate embedding for image {image_id}')
                return None
            
            # Check if embedding already exists
            existing = db.query(ImageEmbedding).filter(ImageEmbedding.image_id == image_id).first()
            if existing:
                existing.embedding_vector = embedding_vector
                existing.model = self.model
                db.commit()
                print(f'Updated embedding for image {image_id}')
                return existing
            
            # Create new embedding
            embedding = ImageEmbedding(
                image_id=image_id,
                embedding_vector=embedding_vector,
                model=self.model
            )
            
            db.add(embedding)
            db.commit()
            db.refresh(embedding)
            
            print(f'Generated embedding for image {image_id} (dimensions: {len(embedding_vector)})')
            return embedding
            
        except Exception as e:
            print(f'Error embedding image {image_id}: {e}')
            db.rollback()
            return None
    
    def embed_blog_post(self, post_id: int, db: Session) -> Optional[BlogPost]:
        # Generate embedding for a blog post and store it
        try:
            post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
            if not post:
                print(f'Blog post {post_id} not found')
                return None
            
            # Combine title and content for embedding
            text = f"{post.title}\n\n{post.content}"
            print(f'Generating embedding for blog post {post_id}: {post.title[:30]}...')
            
            embedding_vector = self.generate_embedding(text)
            
            if not embedding_vector:
                print(f'Failed to generate embedding for blog post {post_id}')
                return None
            
            # Update the post with embedding
            post.embedding_vector = embedding_vector
            post.embedding_model = self.model
            db.commit()
            db.refresh(post)
            
            print(f'Generated embedding for blog post {post_id} (dimensions: {len(embedding_vector)})')
            return post
            
        except Exception as e:
            print(f'Error embedding blog post {post_id}: {e}')
            db.rollback()
            return None
    
    def embed_all_images(self, db: Session) -> dict:
        # Generate embeddings for all images with metadata
        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        try:
            # Get all images with metadata
            images = db.query(Image).join(ImageMetadata).all()
            results["total"] = len(images)
            
            for image in images:
                try:
                    embedding = self.embed_image_caption(image.id, db)
                    if embedding:
                        results["success"] += 1
                        results["details"].append({
                            "image_id": image.id,
                            "filename": image.filename,
                            "status": "success"
                        })
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "image_id": image.id,
                            "filename": image.filename,
                            "status": "failed",
                            "error": "Embedding generation failed"
                        })
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "image_id": image.id,
                        "filename": image.filename,
                        "status": "failed",
                        "error": str(e)
                    })
            
            print(f'Embedded {results["success"]}/{results["total"]} images')
            return results
            
        except Exception as e:
            print(f'Error embedding all images: {e}')
            return results
    
    def embed_all_posts(self, db: Session) -> dict:
        # Generate embeddings for all blog posts
        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        try:
            posts = db.query(BlogPost).all()
            results["total"] = len(posts)
            
            for post in posts:
                try:
                    updated = self.embed_blog_post(post.id, db)
                    if updated:
                        results["success"] += 1
                        results["details"].append({
                            "post_id": post.id,
                            "title": post.title,
                            "status": "success"
                        })
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "post_id": post.id,
                            "title": post.title,
                            "status": "failed",
                            "error": "Embedding generation failed"
                        })
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "post_id": post.id,
                        "title": post.title,
                        "status": "failed",
                        "error": str(e)
                    })
            
            print(f'Embedded {results["success"]}/{results["total"]} blog posts')
            return results
            
        except Exception as e:
            print(f'Error embedding all posts: {e}')
            return results


# Create singleton instance
embedding_service = OllamaEmbeddingService()
