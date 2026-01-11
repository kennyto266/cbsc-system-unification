"""
CacheManager核心实现
Cache Manager Core Implementation

统一的多级缓存管理系统，支持L1（内存）和L2（Redis）缓存。
提供TTL自动过期、批量清理、策略管理等功能。
"""

import json
import pickle
import gzip
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from collections import OrderedDict
import re
import weakref

# L1缓存相关
from cachetools import TTLCache, LRUCache

# L2缓存相关 - Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# 本地模块
from .cache_strategy import (
    CacheStrategy, CacheStrategies, CacheKeys, CacheMetrics,
    CacheLevel, EvictionPolicy
)

logger = logging.getLogger(__name__)


class MemoryCache:
    """内存缓存实现"""

    def __init__(self, max_size: int, ttl: Optional[int] = None):
        self.max_size = max_size
        self.ttl = ttl

        if ttl:
            # 基于TTL的缓存
            self._cache = TTLCache(maxsize=max_size, ttl=ttl)
        else:
            # 基于LRU的缓存
            self._cache = LRUCache(maxsize=max_size)

        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            try:
                return self._cache[key]
            except KeyError:
                return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        with self._lock:
            try:
                self._cache[key] = value
                return True
            except Exception as e:
                logger.error(f"Memory cache set error: {e}")
                return False

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            try:
                del self._cache[key]
                return True
            except KeyError:
                return False

    def clear(self) -> bool:
        """清空缓存"""
        with self._lock:
            try:
                self._cache.clear()
                return True
            except Exception as e:
                logger.error(f"Memory cache clear error: {e}")
                return False

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)

    def keys(self) -> List[str]:
        """获取所有键"""
        with self._lock:
            return list(self._cache.keys())

    def items(self) -> List[Tuple[str, Any]]:
        """获取所有键值对"""
        with self._lock:
            return list(self._cache.items())


class RedisCache:
    """Redis缓存实现"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 10,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout

        self._client: Optional[redis.Redis] = None
        self._pool: Optional[redis.ConnectionPool] = None
        self._connected = False
        self._lock = threading.RLock()

    def connect(self) -> bool:
        """连接Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, running in memory-only mode")
            return False

        with self._lock:
            try:
                # 创建连接池
                self._pool = redis.ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    max_connections=self.max_connections,
                    socket_timeout=self.socket_timeout,
                    socket_connect_timeout=self.socket_connect_timeout,
                    retry_on_timeout=self.retry_on_timeout,
                    decode_responses=False  # 保持二进制格式
                )

                # 创建客户端
                self._client = redis.Redis(connection_pool=self._pool)

                # 测试连接
                self._client.ping()

                self._connected = True
                logger.info(f"Connected to Redis: {self.host}:{self.port}/{self.db}")
                return True

            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._connected = False
                return False

    def disconnect(self):
        """断开连接"""
        with self._lock:
            try:
                if self._client:
                    self._client.close()
                if self._pool:
                    self._pool.disconnect()
                self._connected = False
                logger.info("Disconnected from Redis")
            except Exception as e:
                logger.error(f"Error disconnecting from Redis: {e}")

    def is_connected(self) -> bool:
        """检查连接状态"""
        if not REDIS_AVAILABLE or not self._client or not self._connected:
            return False

        try:
            self._client.ping()
            return True
        except:
            self._connected = False
            return False

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.is_connected():
            return None

        try:
            value = self._client.get(key)
            if value is None:
                return None

            # 尝试反序列化
            try:
                return pickle.loads(value)
            except (pickle.PickleError, EOFError):
                # 如果pickle失败，尝试JSON
                try:
                    return json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # 直接返回原始值
                    return value

        except Exception as e:
            logger.error(f"Redis get error for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self.is_connected():
            return False

        try:
            # 序列化值
            serialized = pickle.dumps(value)

            # 设置值
            if ttl:
                return self._client.setex(key, ttl, serialized)
            else:
                return self._client.set(key, serialized)

        except Exception as e:
            logger.error(f"Redis set error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self.is_connected():
            return False

        try:
            return self._client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error for key '{key}': {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的键"""
        if not self.is_connected():
            return 0

        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis delete pattern error for '{pattern}': {e}")
            return 0

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.is_connected():
            return False

        try:
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key '{key}': {e}")
            return False

    def ttl(self, key: str) -> int:
        """获取键的TTL"""
        if not self.is_connected():
            return -1

        try:
            return self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            return -1

    def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的键"""
        if not self.is_connected():
            return []

        try:
            keys = self._client.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"Redis keys error for pattern '{pattern}': {e}")
            return []

    def info(self) -> Dict[str, Any]:
        """获取Redis信息"""
        if not self.is_connected():
            return {"connected": False}

        try:
            info = self._client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human"),
                "used_memory_bytes": info.get("used_memory"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "connected_clients": info.get("connected_clients"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
        except Exception as e:
            logger.error(f"Redis info error: {e}")
            return {"connected": False, "error": str(e)}


class CacheManager:
    """
    统一缓存管理器

    支持多级缓存：
    - L1: 内存缓存（快速访问）
    - L2: Redis缓存（持久化和共享）

    特性：
    - 自动TTL过期
    - 模式匹配批量清理
    - 缓存策略管理
    - Redis降级支持
    - 性能指标统计
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        enable_redis: bool = True,
        default_memory_size: int = 1000
    ):
        # 基础配置
        self.enable_redis = enable_redis and REDIS_AVAILABLE
        self.default_memory_size = default_memory_size

        # L1缓存（内存）
        self._memory_caches: Dict[str, MemoryCache] = {}
        self._memory_lock = threading.RLock()

        # L2缓存（Redis）
        self._redis_cache = RedisCache(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password
        ) if self.enable_redis else None

        # 缓存策略
        self._strategies: Dict[str, CacheStrategy] = CacheStrategies.all_strategies()
        self._strategy_lock = threading.RLock()

        # 性能指标
        self._metrics: Dict[str, CacheMetrics] = {}
        self._metrics_lock = threading.RLock()

        # 后台任务
        self._cleanup_thread: Optional[threading.Thread] = None
        self._sync_thread: Optional[threading.Thread] = None
        self._running = False

        # 初始化
        self._initialize()

    def _initialize(self):
        """初始化缓存管理器"""
        # 连接Redis
        if self._redis_cache:
            self._redis_cache.connect()

        # 启动后台任务
        self._start_background_tasks()

        logger.info("CacheManager initialized successfully")

    def _start_background_tasks(self):
        """启动后台任务"""
        self._running = True

        # 启动清理任务
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            name="CacheCleanupWorker",
            daemon=True
        )
        self._cleanup_thread.start()

        # 启动同步任务
        self._sync_thread = threading.Thread(
            target=self._sync_worker,
            name="CacheSyncWorker",
            daemon=True
        )
        self._sync_thread.start()

    def _cleanup_worker(self):
        """清理任务工作线程"""
        while self._running:
            try:
                self._cleanup_expired_entries()
                time.sleep(60)  # 每分钟清理一次
            except Exception as e:
                logger.error(f"Cache cleanup worker error: {e}")
                time.sleep(60)

    def _sync_worker(self):
        """同步任务工作线程"""
        while self._running:
            try:
                self._sync_cache_entries()
                time.sleep(5)  # 每5秒同步一次
            except Exception as e:
                logger.error(f"Cache sync worker error: {e}")
                time.sleep(5)

    def _cleanup_expired_entries(self):
        """清理过期条目"""
        current_time = time.time()

        with self._memory_lock:
            for strategy_name, cache in self._memory_caches.items():
                strategy = self._strategies.get(strategy_name)
                if not strategy or strategy.cache_level in [CacheLevel.L1_ONLY, CacheLevel.L1_L2]:
                    # 清理内存缓存中的过期条目
                    expired_keys = []
                    for key in cache.keys():
                        # 这里需要检查实际过期时间，因为TTLCache可能不会立即清理
                        # 简化实现，依赖TTLCache的自动清理
                        pass

    def _sync_cache_entries(self):
        """同步缓存条目"""
        if not self._redis_cache or not self._redis_cache.is_connected():
            return

        with self._memory_lock:
            for strategy_name, cache in self._memory_caches.items():
                strategy = self._strategies.get(strategy_name)
                if strategy and strategy.enable_sync and strategy.cache_level == CacheLevel.L1_L2:
                    # 同步L1到L2
                    self._sync_to_redis(strategy_name, cache, strategy)

    def _sync_to_redis(self, strategy_name: str, cache: MemoryCache, strategy: CacheStrategy):
        """同步内存缓存到Redis"""
        for key, value in cache.items():
            redis_key = CacheKeys.build_key(strategy_name, key)
            # 检查Redis中是否存在，如果不存在则同步
            if not self._redis_cache.exists(redis_key):
                self._redis_cache.set(redis_key, value, strategy.ttl_seconds)

    def _get_memory_cache(self, strategy_name: str, strategy: CacheStrategy) -> MemoryCache:
        """获取或创建内存缓存"""
        if strategy_name not in self._memory_caches:
            max_size = strategy.max_memory_items or self.default_memory_size
            ttl = strategy.ttl_seconds if strategy.cache_level == CacheLevel.L1_ONLY else None

            self._memory_caches[strategy_name] = MemoryCache(max_size=max_size, ttl=ttl)

        return self._memory_caches[strategy_name]

    def _get_metrics(self, strategy_name: str) -> CacheMetrics:
        """获取或创建指标对象"""
        if strategy_name not in self._metrics:
            self._metrics[strategy_name] = CacheMetrics()
        return self._metrics[strategy_name]

    def _compress_if_needed(self, data: Any, strategy: CacheStrategy) -> Any:
        """根据策略压缩数据"""
        if not strategy.enable_compression:
            return data

        try:
            serialized = pickle.dumps(data)
            if len(serialized) >= strategy.compression_threshold:
                # 压缩数据
                compressed = gzip.compress(serialized)
                if len(compressed) < len(serialized):
                    return {"__compressed__": True, "__data__": compressed}
        except Exception as e:
            logger.error(f"Compression error: {e}")

        return data

    def _decompress_if_needed(self, data: Any) -> Any:
        """解压缩数据"""
        if isinstance(data, dict) and data.get("__compressed__"):
            try:
                return pickle.loads(gzip.decompress(data["__data__"]))
            except Exception as e:
                logger.error(f"Decompression error: {e}")
        return data

    def _build_cache_key(self, strategy_name: str, key: str) -> str:
        """构建缓存键"""
        return CacheKeys.build_key(strategy_name, key)

    def _extract_strategy_from_key(self, cache_key: str) -> Optional[str]:
        """从缓存键提取策略名称"""
        parts = cache_key.split(CacheKeys.SEPARATOR)
        if len(parts) >= 2 and parts[0] == CacheKeys.PREFIX:
            return parts[1]
        return None

    # ========================================================================
    # 公共接口 (Public Interface)
    # ========================================================================

    def get(self, strategy_name: str, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        Args:
            strategy_name: 策略名称
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        start_time = time.time()
        strategy = self._strategies.get(strategy_name)

        if not strategy:
            logger.warning(f"Unknown cache strategy: {strategy_name}")
            return default

        metrics = self._get_metrics(strategy_name)
        memory_key = self._build_cache_key(strategy_name, key)

        try:
            # L1缓存查找
            if strategy.cache_level in [CacheLevel.L1_ONLY, CacheLevel.L1_L2]:
                memory_cache = self._get_memory_cache(strategy_name, strategy)
                value = memory_cache.get(key)
                if value is not None:
                    metrics.hits += 1
                    metrics.total_get_time += time.time() - start_time
                    return self._decompress_if_needed(value)

            # L2缓存查找
            if strategy.cache_level in [CacheLevel.L2_ONLY, CacheLevel.L1_L2] and self._redis_cache:
                redis_key = memory_key  # 使用相同的键格式
                value = self._redis_cache.get(redis_key)
                if value is not None:
                    metrics.hits += 1
                    # 如果是L1_L2策略，回填到L1
                    if strategy.cache_level == CacheLevel.L1_L2:
                        memory_cache = self._get_memory_cache(strategy_name, strategy)
                        memory_cache.set(key, value)

                    metrics.total_get_time += time.time() - start_time
                    return self._decompress_if_needed(value)

            # 未找到
            metrics.misses += 1
            metrics.total_get_time += time.time() - start_time
            return default

        except Exception as e:
            metrics.get_errors += 1
            logger.error(f"Cache get error for '{strategy_name}:{key}': {e}")
            return default

    def set(self, strategy_name: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值

        Args:
            strategy_name: 策略名称
            key: 缓存键
            value: 缓存值
            ttl: 自定义TTL（秒）

        Returns:
            是否成功
        """
        start_time = time.time()
        strategy = self._strategies.get(strategy_name)

        if not strategy:
            logger.warning(f"Unknown cache strategy: {strategy_name}")
            return False

        metrics = self._get_metrics(strategy_name)
        actual_ttl = ttl or strategy.ttl_seconds

        try:
            # 压缩数据
            processed_value = self._compress_if_needed(value, strategy)

            success = True

            # L1缓存设置
            if strategy.cache_level in [CacheLevel.L1_ONLY, CacheLevel.L1_L2]:
                memory_cache = self._get_memory_cache(strategy_name, strategy)
                if not memory_cache.set(key, processed_value, actual_ttl):
                    success = False

            # L2缓存设置
            if strategy.cache_level in [CacheLevel.L2_ONLY, CacheLevel.L1_L2] and self._redis_cache:
                redis_key = self._build_cache_key(strategy_name, key)
                if not self._redis_cache.set(redis_key, processed_value, actual_ttl):
                    success = False

            if success:
                metrics.sets += 1
            else:
                metrics.set_errors += 1

            metrics.total_set_time += time.time() - start_time
            return success

        except Exception as e:
            metrics.set_errors += 1
            logger.error(f"Cache set error for '{strategy_name}:{key}': {e}")
            return False

    def delete(self, strategy_name: str, key: str) -> bool:
        """
        删除缓存值

        Args:
            strategy_name: 策略名称
            key: 缓存键

        Returns:
            是否成功
        """
        strategy = self._strategies.get(strategy_name)

        if not strategy:
            logger.warning(f"Unknown cache strategy: {strategy_name}")
            return False

        metrics = self._get_metrics(strategy_name)
        success = True

        try:
            # L1缓存删除
            if strategy.cache_level in [CacheLevel.L1_ONLY, CacheLevel.L1_L2]:
                if strategy_name in self._memory_caches:
                    if not self._memory_caches[strategy_name].delete(key):
                        success = False

            # L2缓存删除
            if strategy.cache_level in [CacheLevel.L2_ONLY, CacheLevel.L1_L2] and self._redis_cache:
                redis_key = self._build_cache_key(strategy_name, key)
                if not self._redis_cache.delete(redis_key):
                    success = False

            if success:
                metrics.deletes += 1

            return success

        except Exception as e:
            logger.error(f"Cache delete error for '{strategy_name}:{key}': {e}")
            return False

    def clear_pattern(self, strategy_name: str, pattern: str) -> int:
        """
        清除匹配模式的缓存

        Args:
            strategy_name: 策略名称
            pattern: 匹配模式（支持通配符*）

        Returns:
            删除的条目数
        """
        strategy = self._strategies.get(strategy_name)

        if not strategy:
            logger.warning(f"Unknown cache strategy: {strategy_name}")
            return 0

        deleted_count = 0

        try:
            # L1缓存清理
            if strategy.cache_level in [CacheLevel.L1_ONLY, CacheLevel.L1_L2]:
                if strategy_name in self._memory_caches:
                    cache = self._memory_caches[strategy_name]
                    # 简化的模式匹配（仅支持*通配符）
                    regex_pattern = pattern.replace('*', '.*')
                    compiled_pattern = re.compile(regex_pattern)

                    keys_to_delete = [
                        key for key in cache.keys()
                        if compiled_pattern.match(key)
                    ]

                    for key in keys_to_delete:
                        if cache.delete(key):
                            deleted_count += 1

            # L2缓存清理
            if strategy.cache_level in [CacheLevel.L2_ONLY, CacheLevel.L1_L2] and self._redis_cache:
                redis_pattern = self._build_cache_key(strategy_name, pattern)
                redis_deleted = self._redis_cache.delete_pattern(redis_pattern)
                deleted_count += redis_deleted

            return deleted_count

        except Exception as e:
            logger.error(f"Cache clear pattern error for '{strategy_name}:{pattern}': {e}")
            return 0

    def exists(self, strategy_name: str, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            strategy_name: 策略名称
            key: 缓存键

        Returns:
            是否存在
        """
        strategy = self._strategies.get(strategy_name)

        if not strategy:
            return False

        try:
            # L1缓存检查
            if strategy.cache_level in [CacheLevel.L1_ONLY, CacheLevel.L1_L2]:
                if strategy_name in self._memory_caches:
                    if self._memory_caches[strategy_name].get(key) is not None:
                        return True

            # L2缓存检查
            if strategy.cache_level in [CacheLevel.L2_ONLY, CacheLevel.L1_L2] and self._redis_cache:
                redis_key = self._build_cache_key(strategy_name, key)
                return self._redis_cache.exists(redis_key)

            return False

        except Exception as e:
            logger.error(f"Cache exists error for '{strategy_name}:{key}': {e}")
            return False

    def get_ttl(self, strategy_name: str, key: str) -> int:
        """
        获取缓存剩余TTL

        Args:
            strategy_name: 策略名称
            key: 缓存键

        Returns:
            剩余TTL（秒），-1表示不存在或无TTL
        """
        strategy = self._strategies.get(strategy_name)

        if not strategy:
            return -1

        try:
            # L2缓存TTL查询
            if strategy.cache_level in [CacheLevel.L2_ONLY, CacheLevel.L1_L2] and self._redis_cache:
                redis_key = self._build_cache_key(strategy_name, key)
                return self._redis_cache.ttl(redis_key)

            # L1缓存TTL查询（简化实现）
            return strategy.ttl_seconds

        except Exception as e:
            logger.error(f"Cache TTL error for '{strategy_name}:{key}': {e}")
            return -1

    # ========================================================================
    # 策略管理 (Strategy Management)
    # ========================================================================

    def register_strategy(self, strategy: CacheStrategy) -> bool:
        """
        注册缓存策略

        Args:
            strategy: 缓存策略

        Returns:
            是否成功
        """
        if not CacheStrategies.validate_strategy(strategy):
            logger.error(f"Invalid cache strategy: {strategy.name}")
            return False

        with self._strategy_lock:
            self._strategies[strategy.name] = strategy
            logger.info(f"Registered cache strategy: {strategy.name}")
            return True

    def get_strategy(self, strategy_name: str) -> Optional[CacheStrategy]:
        """获取缓存策略"""
        return self._strategies.get(strategy_name)

    def list_strategies(self) -> Dict[str, CacheStrategy]:
        """列出所有策略"""
        return self._strategies.copy()

    def update_strategy(self, strategy_name: str, **kwargs) -> bool:
        """
        更新缓存策略

        Args:
            strategy_name: 策略名称
            **kwargs: 要更新的字段

        Returns:
            是否成功
        """
        strategy = self._strategies.get(strategy_name)
        if not strategy:
            logger.error(f"Strategy not found: {strategy_name}")
            return False

        try:
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)

            # 验证更新后的策略
            if not CacheStrategies.validate_strategy(strategy):
                logger.error(f"Invalid updated strategy: {strategy_name}")
                return False

            logger.info(f"Updated cache strategy: {strategy_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating strategy {strategy_name}: {e}")
            return False

    # ========================================================================
    # 指标和统计 (Metrics and Statistics)
    # ========================================================================

    def get_metrics(self, strategy_name: Optional[str] = None) -> Union[CacheMetrics, Dict[str, CacheMetrics]]:
        """
        获取缓存指标

        Args:
            strategy_name: 策略名称，None表示获取所有策略的指标

        Returns:
            指标对象或指标字典
        """
        with self._metrics_lock:
            if strategy_name:
                return self._metrics.get(strategy_name, CacheMetrics())
            else:
                return self._metrics.copy()

    def reset_metrics(self, strategy_name: Optional[str] = None):
        """
        重置缓存指标

        Args:
            strategy_name: 策略名称，None表示重置所有策略的指标
        """
        with self._metrics_lock:
            if strategy_name:
                if strategy_name in self._metrics:
                    self._metrics[strategy_name].reset()
            else:
                for metrics in self._metrics.values():
                    metrics.reset()

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存系统信息

        Returns:
            缓存系统信息
        """
        info = {
            "redis_enabled": self.enable_redis,
            "redis_connected": self._redis_cache.is_connected() if self._redis_cache else False,
            "memory_caches": {
                name: {
                    "size": cache.size(),
                    "max_size": cache.max_size
                }
                for name, cache in self._memory_caches.items()
            },
            "strategies_count": len(self._strategies),
            "total_metrics": {
                "total_hits": sum(m.hits for m in self._metrics.values()),
                "total_misses": sum(m.misses for m in self._metrics.values()),
                "total_sets": sum(m.sets for m in self._metrics.values()),
                "total_deletes": sum(m.deletes for m in self._metrics.values()),
                "overall_hit_rate": self._calculate_overall_hit_rate()
            }
        }

        # 添加Redis信息
        if self._redis_cache:
            info["redis_info"] = self._redis_cache.info()

        return info

    def _calculate_overall_hit_rate(self) -> float:
        """计算整体命中率"""
        total_hits = sum(m.hits for m in self._metrics.values())
        total_misses = sum(m.misses for m in self._metrics.values())
        total = total_hits + total_misses
        return total_hits / total if total > 0 else 0.0

    # ========================================================================
    # 高级功能 (Advanced Features)
    # ========================================================================

    def warm_up(self, strategy_name: str, data_loader: Callable[[List[str]], Dict[str, Any]], keys: List[str]) -> int:
        """
        缓存预热

        Args:
            strategy_name: 策略名称
            data_loader: 数据加载函数
            keys: 要预热的键列表

        Returns:
            成功预热的条目数
        """
        strategy = self._strategies.get(strategy_name)
        if not strategy:
            logger.error(f"Unknown strategy for warm-up: {strategy_name}")
            return 0

        try:
            # 加载数据
            data_dict = data_loader(keys)

            success_count = 0
            for key, value in data_dict.items():
                if self.set(strategy_name, key, value):
                    success_count += 1

            logger.info(f"Cache warm-up completed: {success_count}/{len(keys)} for {strategy_name}")
            return success_count

        except Exception as e:
            logger.error(f"Cache warm-up error for {strategy_name}: {e}")
            return 0

    def export_cache(self, strategy_name: str, filename: str) -> bool:
        """
        导出缓存数据

        Args:
            strategy_name: 策略名称
            filename: 导出文件名

        Returns:
            是否成功
        """
        try:
            cache_data = {}

            # 导出L1缓存
            if strategy_name in self._memory_caches:
                cache_data["L1"] = self._memory_caches[strategy_name].items()

            # 导出L2缓存（简化实现）
            cache_data["L2"] = {}  # 实际实现需要从Redis批量获取

            with open(filename, 'wb') as f:
                pickle.dump(cache_data, f)

            logger.info(f"Cache exported: {strategy_name} -> {filename}")
            return True

        except Exception as e:
            logger.error(f"Cache export error: {e}")
            return False

    def import_cache(self, strategy_name: str, filename: str) -> bool:
        """
        导入缓存数据

        Args:
            strategy_name: 策略名称
            filename: 导入文件名

        Returns:
            是否成功
        """
        try:
            with open(filename, 'rb') as f:
                cache_data = pickle.load(f)

            success_count = 0

            # 导入L1缓存
            if "L1" in cache_data:
                for key, value in cache_data["L1"]:
                    if self.set(strategy_name, key, value):
                        success_count += 1

            logger.info(f"Cache imported: {filename} -> {strategy_name} ({success_count} items)")
            return True

        except Exception as e:
            logger.error(f"Cache import error: {e}")
            return False

    # ========================================================================
    # 生命周期管理 (Lifecycle Management)
    # ========================================================================

    def shutdown(self):
        """关闭缓存管理器"""
        logger.info("Shutting down CacheManager...")

        self._running = False

        # 等待后台线程结束
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)

        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5)

        # 断开Redis连接
        if self._redis_cache:
            self._redis_cache.disconnect()

        # 清理内存缓存
        with self._memory_lock:
            self._memory_caches.clear()

        logger.info("CacheManager shutdown complete")

    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass


# 创建全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None
_cache_lock = threading.Lock()


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager

    if _cache_manager is None:
        with _cache_lock:
            if _cache_manager is None:
                _cache_manager = CacheManager()

    return _cache_manager


def initialize_cache_manager(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_db: int = 0,
    redis_password: Optional[str] = None,
    enable_redis: bool = True,
    default_memory_size: int = 1000
) -> CacheManager:
    """
    初始化全局缓存管理器

    Args:
        redis_host: Redis主机
        redis_port: Redis端口
        redis_db: Redis数据库
        redis_password: Redis密码
        enable_redis: 是否启用Redis
        default_memory_size: 默认内存缓存大小

    Returns:
        缓存管理器实例
    """
    global _cache_manager

    with _cache_lock:
        if _cache_manager is not None:
            _cache_manager.shutdown()

        _cache_manager = CacheManager(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_db=redis_db,
            redis_password=redis_password,
            enable_redis=enable_redis,
            default_memory_size=default_memory_size
        )

    return _cache_manager


# 便捷函数
def cache_get(strategy_name: str, key: str, default: Any = None) -> Any:
    """便捷获取函数"""
    return get_cache_manager().get(strategy_name, key, default)


def cache_set(strategy_name: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """便捷设置函数"""
    return get_cache_manager().set(strategy_name, key, value, ttl)


def cache_delete(strategy_name: str, key: str) -> bool:
    """便捷删除函数"""
    return get_cache_manager().delete(strategy_name, key)


def cache_exists(strategy_name: str, key: str) -> bool:
    """便捷存在检查函数"""
    return get_cache_manager().exists(strategy_name, key)


__all__ = [
    "CacheManager",
    "MemoryCache",
    "RedisCache",
    "get_cache_manager",
    "initialize_cache_manager",
    "cache_get",
    "cache_set",
    "cache_delete",
    "cache_exists"
]