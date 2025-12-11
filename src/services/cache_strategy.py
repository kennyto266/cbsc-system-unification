"""
缓存策略定义
Cache Strategy Definitions

This module defines cache strategies for different types of data.
Each strategy specifies TTL, cache levels, and eviction policies.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import time


class CacheLevel(Enum):
    """缓存级别枚举"""
    L1_ONLY = "L1_ONLY"           # 仅内存缓存
    L2_ONLY = "L2_ONLY"           # 仅Redis缓存
    L1_L2 = "L1_L2"               # 内存+Redis缓存


class EvictionPolicy(Enum):
    """缓存淘汰策略"""
    LRU = "LRU"                   # 最近最少使用
    LFU = "LFU"                   # 最少使用频率
    FIFO = "FIFO"                 # 先进先出
    TTL = "TTL"                   # 仅基于TTL


@dataclass
class CacheStrategy:
    """缓存策略配置"""

    # 基础配置
    name: str                     # 策略名称
    ttl_seconds: int              # 生存时间（秒）
    cache_level: CacheLevel       # 缓存级别

    # 高级配置
    max_memory_items: Optional[int] = None        # 内存缓存最大条目数
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU  # 淘汰策略

    # 性能优化
    enable_compression: bool = False              # 是否启用压缩
    compression_threshold: int = 1024             # 压缩阈值（字节）

    # 一致性配置
    enable_sync: bool = True                      # 是否启用L1-L2同步
    sync_delay: float = 0.1                       # 同步延迟（秒）

    # 统计配置
    enable_metrics: bool = True                   # 是否启用指标统计

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "ttl_seconds": self.ttl_seconds,
            "cache_level": self.cache_level.value,
            "max_memory_items": self.max_memory_items,
            "eviction_policy": self.eviction_policy.value,
            "enable_compression": self.enable_compression,
            "compression_threshold": self.compression_threshold,
            "enable_sync": self.enable_sync,
            "sync_delay": self.sync_delay,
            "enable_metrics": self.enable_metrics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheStrategy":
        """从字典创建策略"""
        return cls(
            name=data["name"],
            ttl_seconds=data["ttl_seconds"],
            cache_level=CacheLevel(data["cache_level"]),
            max_memory_items=data.get("max_memory_items"),
            eviction_policy=EvictionPolicy(data.get("eviction_policy", "LRU")),
            enable_compression=data.get("enable_compression", False),
            compression_threshold=data.get("compression_threshold", 1024),
            enable_sync=data.get("enable_sync", True),
            sync_delay=data.get("sync_delay", 0.1),
            enable_metrics=data.get("enable_metrics", True)
        )


class CacheStrategies:
    """预定义的缓存策略集合"""

    # 策略数据：5分钟，L2缓存（数据较大，不需要内存缓存）
    STRATEGY = CacheStrategy(
        name="strategy",
        ttl_seconds=300,                     # 5分钟
        cache_level=CacheLevel.L2_ONLY,
        max_memory_items=None,
        eviction_policy=EvictionPolicy.TTL,
        enable_compression=True,
        compression_threshold=512,
        enable_sync=False,
        enable_metrics=True
    )

    # 性能数据：30秒，L1缓存（访问频繁，数据较小）
    PERFORMANCE = CacheStrategy(
        name="performance",
        ttl_seconds=30,                      # 30秒
        cache_level=CacheLevel.L1_ONLY,
        max_memory_items=1000,
        eviction_policy=EvictionPolicy.LRU,
        enable_compression=False,
        enable_sync=False,
        enable_metrics=True
    )

    # 用户数据：1分钟，L1+L2缓存（需要持久化和快速访问）
    USER = CacheStrategy(
        name="user",
        ttl_seconds=60,                      # 1分钟
        cache_level=CacheLevel.L1_L2,
        max_memory_items=500,
        eviction_policy=EvictionPolicy.LRU,
        enable_compression=True,
        compression_threshold=256,
        enable_sync=True,
        sync_delay=0.05,
        enable_metrics=True
    )

    # 配置数据：10分钟，L2缓存（相对静态）
    CONFIG = CacheStrategy(
        name="config",
        ttl_seconds=600,                     # 10分钟
        cache_level=CacheLevel.L2_ONLY,
        max_memory_items=None,
        eviction_policy=EvictionPolicy.TTL,
        enable_compression=True,
        compression_threshold=128,
        enable_sync=False,
        enable_metrics=True
    )

    # 市场数据：5秒，L1缓存（高频更新）
    MARKET_DATA = CacheStrategy(
        name="market_data",
        ttl_seconds=5,                       # 5秒
        cache_level=CacheLevel.L1_ONLY,
        max_memory_items=2000,
        eviction_policy=EvictionPolicy.LRU,
        enable_compression=False,
        enable_sync=False,
        enable_metrics=True
    )

    # 会话数据：30分钟，L1+L2缓存（需要持久化）
    SESSION = CacheStrategy(
        name="session",
        ttl_seconds=1800,                    # 30分钟
        cache_level=CacheLevel.L1_L2,
        max_memory_items=100,
        eviction_policy=EvictionPolicy.LRU,
        enable_compression=True,
        compression_threshold=512,
        enable_sync=True,
        sync_delay=0.1,
        enable_metrics=True
    )

    # 实时信号：1秒，L1缓存（极高频）
    REALTIME_SIGNALS = CacheStrategy(
        name="realtime_signals",
        ttl_seconds=1,                       # 1秒
        cache_level=CacheLevel.L1_ONLY,
        max_memory_items=5000,
        eviction_policy=EvictionPolicy.FIFO,
        enable_compression=False,
        enable_sync=False,
        enable_metrics=True
    )

    # API统计：1小时，L2缓存（不需要内存缓存）
    API_STATS = CacheStrategy(
        name="api_stats",
        ttl_seconds=3600,                    # 1小时
        cache_level=CacheLevel.L2_ONLY,
        max_memory_items=None,
        eviction_policy=EvictionPolicy.TTL,
        enable_compression=True,
        compression_threshold=1024,
        enable_sync=False,
        enable_metrics=True
    )

    @classmethod
    def get_strategy(cls, name: str) -> Optional[CacheStrategy]:
        """根据名称获取策略"""
        strategy_map = {
            "strategy": cls.STRATEGY,
            "performance": cls.PERFORMANCE,
            "user": cls.USER,
            "config": cls.CONFIG,
            "market_data": cls.MARKET_DATA,
            "session": cls.SESSION,
            "realtime_signals": cls.REALTIME_SIGNALS,
            "api_stats": cls.API_STATS
        }
        return strategy_map.get(name)

    @classmethod
    def all_strategies(cls) -> Dict[str, CacheStrategy]:
        """获取所有策略"""
        return {
            "strategy": cls.STRATEGY,
            "performance": cls.PERFORMANCE,
            "user": cls.USER,
            "config": cls.CONFIG,
            "market_data": cls.MARKET_DATA,
            "session": cls.SESSION,
            "realtime_signals": cls.REALTIME_SIGNALS,
            "api_stats": cls.API_STATS
        }

    @classmethod
    def register_strategy(cls, name: str, strategy: CacheStrategy):
        """注册自定义策略"""
        setattr(cls, name.upper(), strategy)

    @classmethod
    def validate_strategy(cls, strategy: CacheStrategy) -> bool:
        """验证策略配置"""
        if strategy.ttl_seconds <= 0:
            return False

        if strategy.cache_level == CacheLevel.L1_ONLY and strategy.max_memory_items is None:
            # L1缓存必须设置最大条目数
            return False

        if strategy.sync_delay < 0:
            return False

        if strategy.compression_threshold <= 0:
            return False

        return True


# 缓存键命名规范
class CacheKeys:
    """缓存键命名规范"""

    # 基础格式
    PREFIX = "cbsc"
    SEPARATOR = ":"

    @classmethod
    def build_key(cls, *parts: str) -> str:
        """构建缓存键"""
        return cls.SEPARATOR.join([cls.PREFIX] + [str(p) for p in parts])

    @classmethod
    def strategy_key(cls, strategy_id: str) -> str:
        """策略键"""
        return cls.build_key("strategy", strategy_id)

    @classmethod
    def user_strategy_key(cls, user_id: int) -> str:
        """用户策略列表键"""
        return cls.build_key("user", user_id, "strategies")

    @classmethod
    def strategy_performance_key(cls, strategy_id: str) -> str:
        """策略性能键"""
        return cls.build_key("strategy", strategy_id, "performance")

    @classmethod
    def user_key(cls, user_id: int) -> str:
        """用户键"""
        return cls.build_key("user", user_id)

    @classmethod
    def user_dashboard_key(cls, user_id: int) -> str:
        """用户仪表板键"""
        return cls.build_key("user", user_id, "dashboard")

    @classmethod
    def market_data_key(cls, symbol: str) -> str:
        """市场数据键"""
        return cls.build_key("market", symbol)

    @classmethod
    def config_key(cls, config_name: str) -> str:
        """配置键"""
        return cls.build_key("config", config_name)

    @classmethod
    def session_key(cls, session_id: str) -> str:
        """会话键"""
        return cls.build_key("session", session_id)

    @classmethod
    def realtime_signals_key(cls) -> str:
        """实时信号键"""
        return cls.build_key("signals", "realtime")

    @classmethod
    def api_stats_key(cls, endpoint: str) -> str:
        """API统计键"""
        return cls.build_key("api", "stats", endpoint)

    @classmethod
    def pattern_match(cls, pattern: str) -> str:
        """模式匹配键"""
        return cls.build_key(pattern.replace("*", "*"))


# 缓存指标
@dataclass
class CacheMetrics:
    """缓存指标"""

    # 基础指标
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0

    # 时间指标
    total_get_time: float = 0.0
    total_set_time: float = 0.0

    # 大小指标
    memory_size: int = 0
    redis_size: int = 0

    # 错误指标
    get_errors: int = 0
    set_errors: int = 0

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def avg_get_time(self) -> float:
        """平均获取时间"""
        return self.total_get_time / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0.0

    @property
    def avg_set_time(self) -> float:
        """平均设置时间"""
        return self.total_set_time / self.sets if self.sets > 0 else 0.0

    def reset(self):
        """重置指标"""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0
        self.total_get_time = 0.0
        self.total_set_time = 0.0
        self.memory_size = 0
        self.redis_size = 0
        self.get_errors = 0
        self.set_errors = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "hit_rate": self.hit_rate,
            "avg_get_time": self.avg_get_time,
            "avg_set_time": self.avg_set_time,
            "memory_size": self.memory_size,
            "redis_size": self.redis_size,
            "get_errors": self.get_errors,
            "set_errors": self.set_errors
        }


__all__ = [
    "CacheLevel",
    "EvictionPolicy",
    "CacheStrategy",
    "CacheStrategies",
    "CacheKeys",
    "CacheMetrics"
]