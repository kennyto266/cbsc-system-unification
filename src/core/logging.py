"""
CBSC Strategy Management System Logging Configuration
CBSC 策略管理系統日誌配置

Logging setup and configuration
日誌設置和配置
"""

import logging
import logging.config
import sys
from pathlib import Path

from .config import settings


def setup_logging():
    """
    Setup application logging
    設置應用程序日誌
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Define logging configuration
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "detailed",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.log_level,
                "formatter": "detailed",
                "filename": log_dir / "cbsc.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            }
        }
    }

    # Apply logging configuration
    logging.config.dictConfig(log_config)

    # Create logger
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")

    return logger


# Create global logger instance
logger = setup_logging()