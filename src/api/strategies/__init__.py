"""
策略管理API模块 - 统一路由入口
Strategy Management API Module - Unified Router Entry
"""

from fastapi import APIRouter
from .base import router as base_router
from .execution import router as execution_router
from .personal import router as personal_router
from .websocket import router as websocket_router

# 创建主路由器
router = APIRouter(prefix="/api/strategies", tags=["策略管理"])

# 注册子路由
router.include_router(base_router, tags=["基础操作"])
router.include_router(execution_router, tags=["策略执行"])
router.include_router(personal_router, prefix="/personal", tags=["个性化功能"])
router.include_router(websocket_router, prefix="/ws", tags=["实时通信"])

__all__ = ["router"]