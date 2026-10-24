"""
缓存策略定义
Cache Strategy Definition

职责：
- 定义不同数据类型的缓存策略
- 配置TTL和缓存级别
- 管理缓存行为
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class CacheLevel(str, Enum):
    """缓存级别"""
    L1 = "L1"          # 内存缓存
    L2 = "L2"          # Redis缓存
    L1_L2 = "L1+L2"     # 内存+Redis


class SerializationType(str, Enum):
    """序列化类型"""
    JSON = "json"
    PICKLE = "pickle"
    NONE = "none"


@dataclass
class CacheStrategy:
    """缓存策略配置"""
    ttl: int                           # TTL（秒）
    level: CacheLevel                  # 缓存级别
    serializer: SerializationType      # 序列化方式
    max_size: Optional[int] = None    # 最大缓存条目数
    cleanup_factor: float = 0.75       # 清理因子（LRU缓存）

    def __post_init__(self):
        """验证配置"""
        if self.ttl <= 0:
            raise ValueError("TTL必须大于0")
        if self.cleanup_factor <= 0 or self.cleanup_factor >= 1:
            raise ValueError("清理因子必须在0-1之间")


# 预定义的缓存策略
DEFAULT_STRATEGIES: Dict[str, CacheStrategy] = {
    # 策略数据：5分钟，存储在Redis（持久化）
    "strategy:*": CacheStrategy(
        ttl=300,
        level=CacheLevel.L2,
        serializer=SerializationType.JSON
    ),

    # 性能数据：30秒，仅内存（频繁变化）
    "performance:*": CacheStrategy(
        ttl=30,
        level=CacheLevel.L1,
        serializer=SerializationType.JSON,
        max_size=1000
    ),

    # 用户数据：1分钟，内存+Redis（快速访问+持久化）
    "user:*": CacheStrategy(
        ttl=60,
        level=CacheLevel.L1_L2,
        serializer=SerializationType.JSON,
        max_size=500
    ),

    # 配置数据：10分钟，Redis（持久化）
    "config:*": CacheStrategy(
        ttl=600,
        level=CacheLevel.L2,
        serializer=SerializationType.JSON
    ),

    # 信号数据：10秒，仅内存（实时性要求高）
    "signals:*": CacheStrategy(
        ttl=10,
        level=CacheLevel.L1,
        serializer=SerializationType.JSON,
        max_size=2000
    ),

    # 执行状态：5分钟，Redis（持久化）
    "execution:*": CacheStrategy(
        ttl=300,
        level=CacheLevel.L2,
        serializer=SerializationType.JSON
    ),

    # 会话数据：24小时，Redis（持久化）
    "session:*": CacheStrategy(
        ttl=86400,  # 24小时
        level=CacheLevel.L2,
        serializer=SerializationType.JSON
    )
}


def get_strategy_for_key(key: str, strategies: Optional[Dict[str, CacheStrategy]] = None) -> CacheStrategy:
    """
    根据键获取缓存策略

    Args:
        key: 缓存键
        strategies: 自定义策略字典（可选）

    Returns:
        匹配的缓存策略
    """
    # 使用提供的策略或默认策略
    all_strategies = strategies or DEFAULT_STRATEGIES

    # 尝试精确匹配
    if key in all_strategies:
        return all_strategies[key]

    # 尝试模式匹配
    for pattern, strategy in all_strategies.items():
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            if key.startswith(prefix):
                return strategy

    # 默认策略：1分钟，仅内存
    return CacheStrategy(
        ttl=60,
        level=CacheLevel.L1,
        serializer=SerializationType.JSON,
        max_size=500
    )