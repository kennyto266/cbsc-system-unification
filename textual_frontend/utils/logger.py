"""
TUI 日志记录工具
======================================

Author: CBSC Quant Team
Version: 1.0.0
"""

import logging
from typing import Optional


class TUILogger:
    """
    Textual TUI 日志记录器

    功能：
    - 记录应用操作
    - 输出到控制台
    - 可扩展为写入文件
    """

    def __init__(self, name: str = "TUI", level: int = logging.INFO):
        """
        初始化日志记录器

        Args:
            name: 日志记录器名称
            level: 日志级别
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 创建控制台处理器
        handler = logging.StreamHandler()
        handler.setLevel(level)

        # 创建格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(handler)

    def info(self, message: str):
        """记录 INFO 级别日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录 WARNING 级别日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录 ERROR 级别日志"""
        self.logger.error(message)

    def debug(self, message: str):
        """记录 DEBUG 级别日志"""
        self.logger.debug(message)
