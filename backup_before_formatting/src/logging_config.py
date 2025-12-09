import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging():
    """设置结构化日志记录"""
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())
    log_file = Path("logs / quant_system.log")

    # 确保日志目录存在
    log_file.parent.mkdir(exist_ok=True)

    # 创建logger
    logger = logging.getLogger("quant_system")
    logger.setLevel(log_level)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # 文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(log_level)

    # 格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
