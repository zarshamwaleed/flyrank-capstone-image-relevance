from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os


class Settings(BaseSettings):
    APP_NAME: str = "AI Image Understanding & Content Matching Engine"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/image_relevance"
    
    # Ollama settings
    OLLAMA_URL: str = "http://resyn-ollama:11434"
    VISION_MODEL: str = "llava:7b"
    EMBEDDING_MODEL: str = "all-minilm"
    USE_OLLAMA: bool = True
    
    UPLOAD_DIR: str = "./uploads"
    MAX_IMAGE_SIZE: int = 10485760
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
