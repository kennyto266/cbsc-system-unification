"""
缓存配置
Cache Configuration

职责：
- 缓存相关配置管理
- 环境变量处理
- 缓存策略配置
"""

import os
from typing import Optional
from dataclasses import dataclass

from ..services.cache_strategy import DEFAULT_STRATEGIES
from ..services.cache_manager import CacheManager


@dataclass
class CacheConfig:
    """缓存配置"""
    redis_url: Optional[str] = None
    max_memory_items: int = 1000
    default_ttl: int = 300  # 5分钟

    @classmethod
    def from_env(cls) -> "CacheConfig":
        """从环境变量创建配置"""
        redis_url = os.getenv("REDIS_URL")
        max_items = int(os.getenv("CACHE_MAX_ITEMS", "1000"))
        default_ttl = int(os.getenv("CACHE_DEFAULT_TTL", "300"))

        return cls(
            redis_url=redis_url if redis_url else None,
            max_memory_items=max_items,
            default_ttl=default_ttl
        )


# 全局CacheManager实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    获取全局CacheManager实例（单例模式）
    """
    global _cache_manager

    if _cache_manager is None:
        config = CacheConfig.from_env()
        _cache_manager = CacheManager(
            redis_url=config.redis_url,
            max_memory_items=config.max_memory_items,
            default_ttl=config.default_ttl,
            strategies=DEFAULT_STRATEGIES
        )

    return _cache_manager


def get_cache_stats() -> dict:
    """获取缓存统计信息"""
    if _cache_manager:
        return _cache_manager.get_stats()
    return {"error": "CacheManager未初始化"}


async def close_cache_manager() -> None:
    """关闭缓存管理器"""
    global _cache_manager
    if _cache_manager:
        await _cache_manager.close()
        _cache_manager = None