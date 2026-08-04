import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings


def setup_logging():
    \"\"\"Configure Loguru for the application.\"\"\"
    
    # Remove default handler
    logger.remove()
    
    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    
    # File logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Rotating file handler
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
    )
    
    # Error file handler
    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
    )
    
    logger.info(f"Logging configured. Log level: {settings.LOG_LEVEL}")
    
    return logger


# Create a global logger instance
app_logger = setup_logging()
