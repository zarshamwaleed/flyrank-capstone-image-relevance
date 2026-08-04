import os
import shutil
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.image import Image
from app.core.config import settings
from app.services.ollama_service import vision_service
from app.services.embedding_service import embedding_service

router = APIRouter()


# Helper function to validate image
def validate_image_file(file: UploadFile):
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/jpg"]
    max_size = settings.MAX_IMAGE_SIZE
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed: {', '.join(allowed_types)}"
        )
    
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size {size} bytes exceeds maximum {max_size} bytes"
        )
    
    return True


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Upload a single image file with auto-processing and auto-embedding
    validate_image_file(file)
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    file_size = os.path.getsize(file_path)
    
    # Create database record with status 'pending'
    db_image = Image(
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        processing_status="pending"
    )
    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    metadata = None
    embedding = None
    processing_success = False
    
    # Step 1: Auto-process the image (Vision)
    try:
        print(f"🔄 Auto-processing image {db_image.id}: {db_image.filename}")
        result = vision_service.process_image(db_image, db)
        if result:
            processing_success = True
            metadata = {
                "subject": result.subject,
                "category": result.category,
                "caption": result.caption,
                "tags": result.tags,
                "confidence": result.confidence
            }
            db.refresh(db_image)
            print(f"✅ Vision processing completed for image {db_image.id}")
            
            # Step 2: Auto-generate embedding after vision processing
            try:
                print(f"🔄 Auto-generating embedding for image {db_image.id}")
                embedding_result = embedding_service.embed_image_caption(db_image.id, db)
                if embedding_result:
                    embedding = {
                        "dimensions": len(embedding_result.embedding_vector),
                        "model": embedding_result.model
                    }
                    db.refresh(db_image)
                    print(f"✅ Embedding generated for image {db_image.id}")
            except Exception as e:
                print(f"❌ Auto-embedding failed for image {db_image.id}: {e}")
                
    except Exception as e:
        print(f"❌ Auto-processing failed for image {db_image.id}: {e}")
        db_image.processing_status = "failed"
        db_image.processing_error = str(e)
        db.commit()
    
    return {
        "id": db_image.id,
        "filename": db_image.filename,
        "file_path": db_image.file_path,
        "file_size": db_image.file_size,
        "mime_type": db_image.mime_type,
        "processing_status": db_image.processing_status,
        "created_at": db_image.created_at,
        "auto_processed": processing_success,
        "metadata": metadata,
        "embedding": embedding,
        "message": "✅ Image uploaded, processed, and embedded successfully!" if (processing_success and embedding) else "⚠️ Image uploaded but processing incomplete. Please check status."
    }


@router.post("/upload-multiple", status_code=status.HTTP_201_CREATED)
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    # Upload multiple image files with auto-processing and auto-embedding
    uploaded = []
    failed = []
    
    for file in files:
        try:
            validate_image_file(file)
            
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
            file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = os.path.getsize(file_path)
            
            db_image = Image(
                filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type,
                processing_status="pending"
            )
            
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            
            # Auto-process and auto-embed
            try:
                # Vision processing
                result = vision_service.process_image(db_image, db)
                if result:
                    db.refresh(db_image)
                    
                    # Embedding generation
                    try:
                        embedding_result = embedding_service.embed_image_caption(db_image.id, db)
                        if embedding_result:
                            db.refresh(db_image)
                            uploaded.append({
                                "id": db_image.id,
                                "filename": db_image.filename,
                                "status": "success",
                                "message": "✅ Uploaded, processed, and embedded",
                                "metadata": {
                                    "subject": result.subject,
                                    "category": result.category
                                },
                                "embedding": {
                                    "dimensions": len(embedding_result.embedding_vector),
                                    "model": embedding_result.model
                                }
                            })
                        else:
                            uploaded.append({
                                "id": db_image.id,
                                "filename": db_image.filename,
                                "status": "partial",
                                "message": "⚠️ Uploaded and processed but embedding failed"
                            })
                    except Exception as e:
                        uploaded.append({
                            "id": db_image.id,
                            "filename": db_image.filename,
                            "status": "partial",
                            "message": f"⚠️ Uploaded and processed but embedding failed: {str(e)}"
                        })
                else:
                    uploaded.append({
                        "id": db_image.id,
                        "filename": db_image.filename,
                        "status": "partial",
                        "message": "⚠️ Uploaded but processing failed"
                    })
            except Exception as e:
                db_image.processing_status = "failed"
                db_image.processing_error = str(e)
                db.commit()
                uploaded.append({
                    "id": db_image.id,
                    "filename": db_image.filename,
                    "status": "partial",
                    "message": f"⚠️ Uploaded but processing failed: {str(e)}"
                })
            
        except HTTPException as e:
            failed.append({
                "filename": file.filename,
                "status": "failed",
                "error": e.detail
            })
        except Exception as e:
            failed.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "total": len(files),
        "successful": len(uploaded),
        "failed": len(failed),
        "uploaded": uploaded,
        "failed_list": failed
    }


@router.get("/")
async def list_images(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Image)
    
    if status_filter:
        query = query.filter(Image.processing_status == status_filter)
    
    images = query.order_by(desc(Image.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for image in images:
        result.append({
            "id": image.id,
            "filename": image.filename,
            "file_path": image.file_path,
            "file_size": image.file_size,
            "mime_type": image.mime_type,
            "processing_status": image.processing_status,
            "processing_error": image.processing_error,
            "created_at": image.created_at,
            "updated_at": image.updated_at,
            "has_metadata": image.image_metadata is not None,
            "has_embedding": image.embedding is not None
        })
    
    return result


@router.get("/{image_id}")
async def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    include_metadata: bool = False
):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    response = {
        "id": image.id,
        "filename": image.filename,
        "file_path": image.file_path,
        "file_size": image.file_size,
        "mime_type": image.mime_type,
        "processing_status": image.processing_status,
        "processing_error": image.processing_error,
        "created_at": image.created_at,
        "updated_at": image.updated_at
    }
    
    if include_metadata and image.image_metadata:
        response["metadata"] = {
            "subject": image.image_metadata.subject,
            "category": image.image_metadata.category,
            "caption": image.image_metadata.caption,
            "tags": image.image_metadata.tags,
            "confidence": image.image_metadata.confidence,
            "created_at": image.image_metadata.created_at
        }
    
    if image.embedding:
        response["has_embedding"] = True
    
    return response


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    delete_file: bool = True
):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    if delete_file and os.path.exists(image.file_path):
        try:
            os.remove(image.file_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    db.delete(image)
    db.commit()
    
    return {
        "message": f"Image {image_id} ({image.filename}) deleted successfully",
        "id": image_id,
        "filename": image.filename,
        "file_deleted": delete_file
    }


@router.get("/stats/count")
async def get_image_stats(db: Session = Depends(get_db)):
    total = db.query(Image).count()
    pending = db.query(Image).filter(Image.processing_status == "pending").count()
    processing = db.query(Image).filter(Image.processing_status == "processing").count()
    completed = db.query(Image).filter(Image.processing_status == "completed").count()
    failed = db.query(Image).filter(Image.processing_status == "failed").count()
    
    return {
        "total": total,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed
    }
