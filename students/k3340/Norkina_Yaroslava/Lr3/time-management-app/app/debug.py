# app/debug.py
import logging
import traceback

logger = logging.getLogger(__name__)


def log_error(message: str, exc_info: bool = False):
    """Логирует ошибку с опциональным трейсбеком."""
    logger.error(message, exc_info=exc_info)
    if exc_info:
        traceback.print_exc()