"""
配置模块初始化文件
"""

from .database import get_db_connection, init_database

__all__ = ['get_db_connection', 'init_database']