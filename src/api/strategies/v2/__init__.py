"""
Strategy API v2
策略管理 API v2 版本

提供新的 RESTful API 端點，支持更好的資源管理和版本控制
"""

from .routes import router as v2_router

__all__ = ["v2_router"]