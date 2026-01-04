"""
缓存集成示例
Cache Integration Examples

展示如何在现有系统中集成和使用新的缓存功能。
"""

from .cached_strategy_manager import (
    CachedStrategyManager,
    get_global_config,
    get_api_statistics
)

__all__ = [
    "CachedStrategyManager",
    "get_global_config",
    "get_api_statistics"
]