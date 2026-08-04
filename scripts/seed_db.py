import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models import Image, ImageMetadata, ImageEmbedding, BlogPost, Suggestion, Review, CostLog


def seed_database():
    print("Seeding database...")
    
    db = SessionLocal()
    
    try:
        # Create sample images
        sample_images = [
            {
                "filename": "red_fox.jpg",
                "file_path": "./uploads/red_fox.jpg",
                "file_size": 1024000,
                "mime_type": "image/jpeg",
                "processing_status": "completed"
            },
            {
                "filename": "wolf.jpg", 
                "file_path": "./uploads/wolf.jpg",
                "file_size": 980000,
                "mime_type": "image/jpeg",
                "processing_status": "completed"
            },
            {
                "filename": "dog.jpg",
                "file_path": "./uploads/dog.jpg", 
                "file_size": 850000,
                "mime_type": "image/jpeg",
                "processing_status": "completed"
            }
        ]
        
        images_created = []
        for img_data in sample_images:
            image = Image(**img_data)
            db.add(image)
            db.flush()
            images_created.append(image)
            
            # Create metadata for each image
            subject = img_data["filename"].replace(".jpg", "").replace("_", " ").title()
            metadata_data = {
                "image_id": image.id,
                "subject": subject,
                "category": "animal",
                "caption": f"A {subject} in its natural habitat",
                "tags": ["wild", "animal", "nature"],
                "confidence": 0.95
            }
            metadata = ImageMetadata(**metadata_data)
            db.add(metadata)
            
            # Create embedding for each image
            embedding_data = {
                "image_id": image.id,
                "embedding_vector": [0.1] * 384,
                "model": "text-embedding-004"
            }
            embedding = ImageEmbedding(**embedding_data)
            db.add(embedding)
        
        db.commit()
        print(f"Created {len(images_created)} sample images with metadata and embeddings")
        
        # Create a sample blog post
        post = BlogPost(
            title="Understanding Red Foxes",
            content="Red foxes are intelligent wild animals found in various habitats...",
            embedding_vector=[0.1] * 384,
            embedding_model="text-embedding-004"
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        print(f"Created sample blog post: {post.title}")
        
        # Create sample suggestions
        for i, image in enumerate(images_created, 1):
            suggestion = Suggestion(
                post_id=post.id,
                image_id=image.id,
                similarity_score=0.95 - (i-1) * 0.1,
                guard_passed="passed" if i == 1 else "rejected",
                guard_reason=None if i == 1 else f"Subject mismatch: expected fox, got {image.image_metadata.subject}",
                rank=i
            )
            db.add(suggestion)
        
        db.commit()
        print("Created sample suggestions")
        
        # Create sample reviews
        for suggestion in db.query(Suggestion).all():
            if suggestion.rank == 1:
                review = Review(
                    suggestion_id=suggestion.id,
                    decision="approved",
                    reviewer_notes="Good match!",
                    reviewer="admin"
                )
                db.add(review)
        
        db.commit()
        print("Created sample reviews")
        
        print("Database seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
