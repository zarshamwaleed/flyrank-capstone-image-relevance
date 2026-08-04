import time
from typing import List
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.image import Image
from app.services.ollama_service import vision_service


def process_pending_images():
    # Process all pending images in the queue
    db = SessionLocal()
    try:
        pending_images = db.query(Image).filter(Image.processing_status == "pending").all()
        
        if not pending_images:
            print("No pending images to process")
            return
        
        print(f"Found {len(pending_images)} pending images to process")
        
        for image in pending_images:
            print(f"Processing image {image.id}: {image.filename}")
            if vision_service:
                vision_service.process_image(image, db)
            else:
                print("Vision service not initialized")
            
    except Exception as e:
        print(f"Error processing images: {str(e)}")
    finally:
        db.close()


def process_image_by_id(image_id: int):
    # Process a specific image by ID
    db = SessionLocal()
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            print(f"Image {image_id} not found")
            return False
        
        if image.processing_status != "pending":
            print(f"Image {image_id} is not pending (status: {image.processing_status})")
            return False
        
        if not vision_service:
            print("Vision service not initialized")
            return False
        
        result = vision_service.process_image(image, db)
        return result is not None
        
    except Exception as e:
        print(f"Error processing image {image_id}: {str(e)}")
        return False
    finally:
        db.close()
