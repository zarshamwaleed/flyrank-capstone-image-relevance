from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.image import Image
from app.services.image_processor import process_image_by_id, process_pending_images

# Use Ollama service
try:
    from app.services.ollama_service import vision_service
    print('✅ Ollama vision service loaded successfully')
except ImportError as e:
    print(f'❌ Error loading Ollama service: {e}')
    vision_service = None

router = APIRouter()


@router.post("/process/{image_id}")
async def process_image_endpoint(
    image_id: int,
    db: Session = Depends(get_db)
):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    if not vision_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vision service not initialized. Please check your Ollama setup."
        )
    
    result = vision_service.process_image(image, db)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image {image_id}"
        )
    
    return {
        "message": f"Image {image_id} processed successfully",
        "image_id": image_id,
        "metadata": {
            "subject": result.subject,
            "category": result.category,
            "caption": result.caption,
            "tags": result.tags,
            "confidence": result.confidence
        }
    }


@router.post("/process-pending")
async def process_pending_images_endpoint():
    from app.core.database import SessionLocal
    from app.models.image import Image
    
    if not vision_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vision service not initialized. Please check your Ollama setup."
        )
    
    db = SessionLocal()
    try:
        pending_count = db.query(Image).filter(Image.processing_status == "pending").count()
        
        if pending_count == 0:
            return {
                "message": "No pending images to process",
                "total_processed": 0,
                "pending_count": 0
            }
        
        process_pending_images()
        
        remaining = db.query(Image).filter(Image.processing_status == "pending").count()
        
        return {
            "message": "Processed pending images",
            "total_processed": pending_count - remaining,
            "pending_count": remaining
        }
    finally:
        db.close()
