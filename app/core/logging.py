import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    logger.remove()
    logger.add(sys.stdout, level=settings.LOG_LEVEL)
