from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.core.database import get_db
from app.models.image import Image
from app.models.post import BlogPost
from app.models.suggestion import Suggestion
from app.models.review import Review
from app.services.evaluation_service import evaluation_engine

router = APIRouter()

# Set up templates with absolute path
templates = Jinja2Templates(directory="/app/app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "active_page": "dashboard",
        "now": datetime.now()
    })


@router.get("/images", response_class=HTMLResponse)
async def images_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("images.html", {
        "request": request, 
        "active_page": "images",
        "now": datetime.now()
    })


@router.get("/blogs", response_class=HTMLResponse)
async def blogs_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("blogs.html", {
        "request": request, 
        "active_page": "blogs",
        "now": datetime.now()
    })


@router.get("/suggestions", response_class=HTMLResponse)
async def suggestions_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("suggestions.html", {
        "request": request, 
        "active_page": "suggestions",
        "now": datetime.now()
    })


@router.get("/reviews", response_class=HTMLResponse)
async def reviews_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("reviews.html", {
        "request": request, 
        "active_page": "reviews",
        "now": datetime.now()
    })


@router.get("/costs", response_class=HTMLResponse)
async def costs_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("costs.html", {
        "request": request, 
        "active_page": "costs",
        "now": datetime.now()
    })


@router.get("/evaluation", response_class=HTMLResponse)
async def evaluation_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("evaluation.html", {
        "request": request, 
        "active_page": "evaluation",
        "now": datetime.now()
    })


# API endpoints for dashboard data
@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    try:
        total_images = db.query(Image).count()
        total_posts = db.query(BlogPost).count()
        total_suggestions = db.query(Suggestion).count()
        total_reviews = db.query(Review).count()
        
        eval_result = evaluation_engine.run_evaluation(db)
        top1_precision = eval_result.get("top1_precision", 0)
        
        return {
            "total_images": total_images,
            "total_posts": total_posts,
            "total_suggestions": total_suggestions,
            "total_reviews": total_reviews,
            "top1_precision": top1_precision
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    try:
        pending = db.query(Image).filter(Image.processing_status == "pending").count()
        processing = db.query(Image).filter(Image.processing_status == "processing").count()
        completed = db.query(Image).filter(Image.processing_status == "completed").count()
        failed = db.query(Image).filter(Image.processing_status == "failed").count()
        
        return {
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/activity")
async def get_activity(db: Session = Depends(get_db)):
    try:
        recent = []
        
        images = db.query(Image).order_by(Image.created_at.desc()).limit(5).all()
        for img in images:
            recent.append({
                "message": f"📸 Image uploaded: {img.filename}",
                "time": img.created_at.strftime("%H:%M")
            })
        
        reviews = db.query(Review).order_by(Review.reviewed_at.desc()).limit(3).all()
        for rev in reviews:
            status = "✅ Approved" if rev.decision == "approved" else "❌ Rejected"
            recent.append({
                "message": f"📝 Suggestion {status}",
                "time": rev.reviewed_at.strftime("%H:%M")
            })
        
        return recent[:10]
    except Exception as e:
        return []
