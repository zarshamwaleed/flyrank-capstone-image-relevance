from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.api.images import router as images_router
from app.api.vision import router as vision_router
from app.api.embeddings import router as embeddings_router
from app.api.posts import router as posts_router
from app.api.matching import router as matching_router
from app.api.guard import router as guard_router
from app.api.review import router as review_router
from app.api.usage import router as usage_router
from app.api.evaluation import router as evaluation_router
from app.api.dashboard import router as dashboard_router
from app.models import Image, ImageMetadata, ImageEmbedding, BlogPost, Suggestion, Review, CostLog


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.APP_NAME}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE_URL}")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
    yield
    print(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description="Automatically understand images and match them to blog posts using AI",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (images)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(images_router, prefix="/api/images", tags=["Images"])
app.include_router(vision_router, prefix="/api/vision", tags=["Vision"])
app.include_router(embeddings_router, prefix="/api/embeddings", tags=["Embeddings"])
app.include_router(posts_router, prefix="/api/posts", tags=["Blog Posts"])
app.include_router(matching_router, prefix="/api/matching", tags=["Matching"])
app.include_router(guard_router, prefix="/api/guard", tags=["Mismatch Guard"])
app.include_router(review_router, prefix="/api/review", tags=["Review"])
app.include_router(usage_router, prefix="/api/usage", tags=["Usage Tracking"])
app.include_router(evaluation_router, prefix="/api/evaluation", tags=["Evaluation"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "debug": settings.DEBUG
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
