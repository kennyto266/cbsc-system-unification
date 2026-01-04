"""
缓存服务
Cache Service

Task #002: API接口集成和數據獲取
提供Redis缓存服务，优化API性能和实时数据管理
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import asyncio
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import pickle

logger = logging.getLogger(__name__)

class CacheService:
    """Redis缓存服务 with in-memory fallback"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 20
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections

        self.redis_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self._is_connected = False

        # In-memory fallback cache
        self._memory_cache: Dict[str, tuple[Any, Optional[float]]] = {}  # key -> (value, expiry_time)
        self._use_memory_fallback = False

    async def initialize(self) -> bool:
        """初始化缓存服务"""
        try:
            # 创建连接池
            self.redis_pool = ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.max_connections,
                decode_responses=False  # 使用二进制模式支持pickle
            )

            # 创建Redis客户端
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)

            # 测试连接
            await self.redis_client.ping()

            self._is_connected = True
            logger.info(f"缓存服务初始化成功: {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.warning(f"Redis連接失敗，啟用內存緩存回退: {e}")
            self._is_connected = False
            self._use_memory_fallback = True
            logger.info("✅ 內存緩存回退已啟用 - 緩存功能將使用進程內存")
            return True  # Return True since we have fallback

    async def is_connected(self) -> bool:
        """检查连接状态"""
        if not self._is_connected or not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except:
            self._is_connected = False
            return False

    # ============================================================================
    # Memory Fallback Cache Helpers
    # ============================================================================

    def _memory_cache_set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        try:
            expiry_time = None
            if expire:
                expiry_time = datetime.now().timestamp() + expire
            self._memory_cache[key] = (value, expiry_time)
            return True
        except Exception as e:
            logger.error(f"Memory cache set failed: {e}")
            return False

    def _memory_cache_get(self, key: str, default: Any = None) -> Any:
        """Get value from memory cache"""
        try:
            if key not in self._memory_cache:
                return default

            value, expiry_time = self._memory_cache[key]

            # Check if expired
            if expiry_time and datetime.now().timestamp() > expiry_time:
                del self._memory_cache[key]
                return default

            return value
        except Exception as e:
            logger.error(f"Memory cache get failed: {e}")
            return default

    def _memory_cache_delete(self, key: str) -> bool:
        """Delete value from memory cache"""
        try:
            if key in self._memory_cache:
                del self._memory_cache[key]
                return True
            return False
        except Exception as e:
            logger.error(f"Memory cache delete failed: {e}")
            return False

    async def _memory_cache_cleanup(self) -> int:
        """Clean expired entries from memory cache"""
        try:
            current_time = datetime.now().timestamp()
            expired_keys = [
                key for key, (_, expiry) in self._memory_cache.items()
                if expiry and current_time > expiry
            ]
            for key in expired_keys:
                del self._memory_cache[key]
            return len(expired_keys)
        except Exception as e:
            logger.error(f"Memory cache cleanup failed: {e}")
            return 0

    # ============================================================================
    # Public Cache Operations with Memory Fallback
    # ============================================================================

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        use_pickle: bool = True
    ) -> bool:
        """设置缓存"""
        try:
            # Try Redis first if connected
            if await self.is_connected():
                if use_pickle:
                    serialized_value = pickle.dumps(value)
                else:
                    serialized_value = json.dumps(value, default=str).encode('utf-8')

                if expire:
                    await self.redis_client.setex(key, expire, serialized_value)
                else:
                    await self.redis_client.set(key, serialized_value)

                return True

            # Fall back to memory cache
            elif self._use_memory_fallback:
                return self._memory_cache_set(key, value, expire)

            return False

        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            # Try memory fallback on error
            if self._use_memory_fallback:
                return self._memory_cache_set(key, value, expire)
            return False

    async def get(
        self,
        key: str,
        use_pickle: bool = True,
        default: Any = None
    ) -> Any:
        """获取缓存"""
        try:
            # Try Redis first if connected
            if await self.is_connected():
                value = await self.redis_client.get(key)

                if value is None:
                    return default

                if use_pickle:
                    return pickle.loads(value)
                else:
                    return json.loads(value.decode('utf-8'))

            # Fall back to memory cache
            elif self._use_memory_fallback:
                return self._memory_cache_get(key, default)

            return default

        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            # Try memory fallback on error
            if self._use_memory_fallback:
                return self._memory_cache_get(key, default)
            return default

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            # Try Redis first if connected
            if await self.is_connected():
                result = await self.redis_client.delete(key)
                return result > 0

            # Fall back to memory cache
            elif self._use_memory_fallback:
                return self._memory_cache_delete(key)

            return False

        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            # Try memory fallback on error
            if self._use_memory_fallback:
                return self._memory_cache_delete(key)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存"""
        try:
            if not await self.is_connected():
                return 0

            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0

        except Exception as e:
            logger.error(f"批量删除缓存失败 {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            if not await self.is_connected():
                return False

            result = await self.redis_client.exists(key)
            return result > 0

        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置缓存过期时间"""
        try:
            if not await self.is_connected():
                return False

            result = await self.redis_client.expire(key, seconds)
            return result > 0

        except Exception as e:
            logger.error(f"设置缓存过期时间失败 {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """获取缓存剩余过期时间"""
        try:
            if not await self.is_connected():
                return -1

            return await self.redis_client.ttl(key)

        except Exception as e:
            logger.error(f"获取缓存TTL失败 {key}: {e}")
            return -1

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增缓存值"""
        try:
            # 使用内存回退模式
            if self._use_memory_fallback:
                current_value = self._memory_cache_get(key, default=0)
                new_value = (current_value or 0) + amount
                self._memory_cache_set(key, new_value)
                return new_value

            if not await self.is_connected():
                return None

            return await self.redis_client.incrby(key, amount)

        except Exception as e:
            # 如果Redis失敗，回退到內存緩存
            if not self._use_memory_fallback:
                logger.warning(f"Redis increment failed, using memory fallback: {e}")
                self._use_memory_fallback = True
                current_value = self._memory_cache_get(key, default=0)
                new_value = (current_value or 0) + amount
                self._memory_cache_set(key, new_value)
                return new_value
            logger.error(f"Memory increment failed {key}: {e}")
            return None

    async def list_push(self, key: str, *values: Any, maxlen: Optional[int] = None) -> Optional[int]:
        """推入列表"""
        try:
            if not await self.is_connected():
                return None

            serialized_values = [pickle.dumps(v) for v in values]

            if maxlen:
                return await self.redis_client.lpush(key, *serialized_values[:maxlen])
            else:
                return await self.redis_client.lpush(key, *serialized_values)

        except Exception as e:
            logger.error(f"列表推入失败 {key}: {e}")
            return None

    async def list_pop(self, key: str, count: int = 1) -> List[Any]:
        """弹出列表元素"""
        try:
            if not await self.is_connected():
                return []

            values = await self.redis_client.lpop(key, count)

            if not values:
                return []

            return [pickle.loads(v) for v in values]

        except Exception as e:
            logger.error(f"列表弹出失败 {key}: {e}")
            return []

    async def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表范围"""
        try:
            if not await self.is_connected():
                return []

            values = await self.redis_client.lrange(key, start, end)

            if not values:
                return []

            return [pickle.loads(v) for v in values]

        except Exception as e:
            logger.error(f"获取列表范围失败 {key}: {e}")
            return []

    async def hash_set(self, key: str, field: str, value: Any) -> bool:
        """设置哈希字段"""
        try:
            if not await self.is_connected():
                return False

            serialized_value = pickle.dumps(value)
            await self.redis_client.hset(key, field, serialized_value)
            return True

        except Exception as e:
            logger.error(f"设置哈希字段失败 {key}.{field}: {e}")
            return False

    async def hash_get(self, key: str, field: str, default: Any = None) -> Any:
        """获取哈希字段"""
        try:
            if not await self.is_connected():
                return default

            value = await self.redis_client.hget(key, field)

            if value is None:
                return default

            return pickle.loads(value)

        except Exception as e:
            logger.error(f"获取哈希字段失败 {key}.{field}: {e}")
            return default

    async def hash_get_all(self, key: str) -> Dict[str, Any]:
        """获取所有哈希字段"""
        try:
            if not await self.is_connected():
                return {}

            hash_data = await self.redis_client.hgetall(key)

            if not hash_data:
                return {}

            return {
                field.decode('utf-8'): pickle.loads(value)
                for field, value in hash_data.items()
            }

        except Exception as e:
            logger.error(f"获取所有哈希字段失败 {key}: {e}")
            return {}

    async def hash_delete(self, key: str, *fields: str) -> int:
        """删除哈希字段"""
        try:
            if not await self.is_connected():
                return 0

            return await self.redis_client.hdel(key, *fields)

        except Exception as e:
            logger.error(f"删除哈希字段失败 {key}: {e}")
            return 0

    # ============================================================================
    # 策略相关缓存操作 (Strategy-related Cache Operations)
    # ============================================================================

    async def cache_user_strategies(self, user_id: int, strategies: List[Any], expire: int = 300) -> bool:
        """缓存用户策略"""
        key = f"user_strategies:{user_id}"
        return await self.set(key, strategies, expire=expire)

    async def get_user_strategies(self, user_id: int) -> Optional[List[Any]]:
        """获取缓存的用户策略"""
        key = f"user_strategies:{user_id}"
        return await self.get(key)

    async def cache_strategy_performance(self, strategy_id: str, performance: Any, expire: int = 300) -> bool:
        """缓存策略性能"""
        key = f"strategy_performance:{strategy_id}"
        return await self.set(key, performance, expire=expire)

    async def get_strategy_performance(self, strategy_id: str) -> Optional[Any]:
        """获取缓存的策略性能"""
        key = f"strategy_performance:{strategy_id}"
        return await self.get(key)

    async def cache_user_dashboard(self, user_id: int, dashboard_data: Any, expire: int = 60) -> bool:
        """缓存用户仪表板数据"""
        key = f"user_dashboard:{user_id}"
        return await self.set(key, dashboard_data, expire=expire)

    async def get_user_dashboard(self, user_id: int) -> Optional[Any]:
        """获取缓存的用户仪表板数据"""
        key = f"user_dashboard:{user_id}"
        return await self.get(key)

    async def add_realtime_signal(self, signal: Any, max_signals: int = 1000) -> bool:
        """添加实时信号到缓存队列"""
        key = "realtime_signals"
        return await self.list_push(key, signal, maxlen=max_signals) is not None

    async def get_recent_signals(self, count: int = 50) -> List[Any]:
        """获取最近的实时信号"""
        key = "realtime_signals"
        return await self.list_range(key, 0, count - 1)

    async def cache_market_data(self, symbol: str, market_data: Any, expire: int = 30) -> bool:
        """缓存市场数据"""
        key = f"market_data:{symbol}"
        return await self.set(key, market_data, expire=expire)

    async def get_market_data(self, symbol: str) -> Optional[Any]:
        """获取缓存的市场数据"""
        key = f"market_data:{symbol}"
        return await self.get(key)

    async def cache_user_preferences(self, user_id: int, preferences: Any, expire: int = 3600) -> bool:
        """缓存用户偏好设置"""
        key = f"user_preferences:{user_id}"
        return await self.set(key, preferences, expire=expire)

    async def get_user_preferences(self, user_id: int) -> Optional[Any]:
        """获取缓存的用户偏好设置"""
        key = f"user_preferences:{user_id}"
        return await self.get(key)

    async def record_api_call(self, endpoint: str, user_id: int, response_time: float) -> bool:
        """记录API调用统计"""
        try:
            key = f"api_stats:{endpoint}"

            # 使用内存回退模式
            if self._use_memory_fallback:
                # 从内存获取现有统计
                stats_key = f"{key}_stats"
                stats = self._memory_cache_get(stats_key) or {"call_count": 0, "avg_response_time": 0, "total_time": 0}

                # 更新统计
                stats["call_count"] += 1
                stats["total_time"] += response_time
                stats["avg_response_time"] = stats["total_time"] / stats["call_count"]

                # 保存回内存（24小时过期）
                self._memory_cache_set(stats_key, stats, expire=86400)
                return True

            # 使用Redis存储
            if not await self.is_connected():
                return False

            # 更新调用次数
            await self.redis_client.hincrby(key, "call_count", 1)

            # 更新平均响应时间
            current_avg = float(await self.redis_client.hget(key, "avg_response_time") or 0)
            call_count = int(await self.redis_client.hget(key, "call_count") or 1)
            new_avg = ((current_avg * (call_count - 1)) + response_time) / call_count
            await self.redis_client.hset(key, "avg_response_time", str(new_avg))

            # 设置过期时间（24小时）
            await self.redis_client.expire(key, 86400)

            return True

        except Exception as e:
            # 如果Redis失敗，回退到內存緩存
            if not self._use_memory_fallback:
                logger.warning(f"Redis record_api_call failed, using memory fallback: {e}")
                self._use_memory_fallback = True
                # 重试使用内存模式
                return await self.record_api_call(endpoint, user_id, response_time)
            logger.error(f"Memory record_api_call failed: {e}")
            return False

    async def get_api_stats(self, endpoint: str) -> Dict[str, Any]:
        """获取API调用统计"""
        try:
            key = f"api_stats:{endpoint}"
            stats = await self.redis_client.hgetall(key)

            if not stats:
                return {}

            return {
                field.decode('utf-8'): value.decode('utf-8')
                for field, value in stats.items()
            }

        except Exception as e:
            logger.error(f"获取API调用统计失败: {e}")
            return {}

    async def cleanup_expired_cache(self) -> int:
        """清理过期的缓存"""
        try:
            if not await self.is_connected():
                return 0

            # 获取所有键
            keys = await self.redis_client.keys("*")

            expired_count = 0
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl == -2:  # 已过期但未被删除
                    await self.redis_client.delete(key)
                    expired_count += 1

            logger.info(f"清理了 {expired_count} 个过期缓存")
            return expired_count

        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0

    async def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        try:
            if await self.is_connected():
                info = await self.redis_client.info()

                return {
                    "type": "redis",
                    "connected": True,
                    "used_memory": info.get("used_memory_human"),
                    "total_commands_processed": info.get("total_commands_processed"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                    "connected_clients": info.get("connected_clients"),
                    "uptime_in_seconds": info.get("uptime_in_seconds")
                }

            elif self._use_memory_fallback:
                # Count expired entries
                await self._memory_cache_cleanup()

                return {
                    "type": "memory",
                    "connected": True,
                    "cache_entries": len(self._memory_cache),
                    "fallback_mode": True,
                    "note": "Using in-memory cache fallback"
                }

            return {"connected": False}

        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {"connected": False, "error": str(e)}

    # ============================================================================
    # 统一数据缓存操作 (Unified Data Cache Operations)
    # ============================================================================

    async def cache_unified_data_point(
        self,
        data_point: Dict[str, Any],
        source: str,
        expire: Optional[int] = None
    ) -> bool:
        """缓存统一数据点"""
        try:
            # Generate cache key based on timestamp and symbol
            symbol = data_point.get('symbol', 'unknown')
            timestamp = data_point.get('timestamp', datetime.now().isoformat())
            cache_key = f"unified_data:{source}:{symbol}:{timestamp}"

            # Set default expiration based on source type
            if expire is None:
                expire = self._get_default_ttl_for_source(source)

            return await self.set(cache_key, data_point, expire=expire, use_pickle=True)

        except Exception as e:
            logger.error(f"缓存统一数据点失败: {e}")
            return False

    async def get_unified_data_point(
        self,
        symbol: str,
        source: str,
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """获取缓存的统一数据点"""
        try:
            cache_key = f"unified_data:{source}:{symbol}:{timestamp}"
            return await self.get(cache_key, use_pickle=True)

        except Exception as e:
            logger.error(f"获取统一数据点失败: {e}")
            return None

    async def cache_unified_data_series(
        self,
        symbol: str,
        source: str,
        data_series: List[Dict[str, Any]],
        expire: Optional[int] = None
    ) -> bool:
        """缓存统一数据序列"""
        try:
            cache_key = f"unified_series:{source}:{symbol}"

            # Set default expiration based on source type
            if expire is None:
                expire = self._get_default_ttl_for_source(source)

            # Sort data by timestamp for efficient querying
            sorted_data = sorted(data_series, key=lambda x: x.get('timestamp', ''))

            return await self.set(cache_key, sorted_data, expire=expire, use_pickle=True)

        except Exception as e:
            logger.error(f"缓存统一数据序列失败: {e}")
            return False

    async def get_unified_data_series(
        self,
        symbol: str,
        source: str
    ) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的统一数据序列"""
        try:
            cache_key = f"unified_series:{source}:{symbol}"
            return await self.get(cache_key, use_pickle=True)

        except Exception as e:
            logger.error(f"获取统一数据序列失败: {e}")
            return None

    async def cache_hkma_data(
        self,
        indicator: str,
        data: Dict[str, Any],
        expire: int = 3600
    ) -> bool:
        """缓存HKMA数据"""
        cache_key = f"hkma_data:{indicator}"
        return await self.set(cache_key, data, expire=expire, use_pickle=True)

    async def get_hkma_data(self, indicator: str) -> Optional[Dict[str, Any]]:
        """获取缓存的HKMA数据"""
        cache_key = f"hkma_data:{indicator}"
        return await self.get(cache_key, use_pickle=True)

    async def cache_sentiment_data(
        self,
        symbol: str,
        sentiment_data: Dict[str, Any],
        expire: int = 900
    ) -> bool:
        """缓存情绪数据"""
        cache_key = f"sentiment_data:{symbol}"
        return await self.set(cache_key, sentiment_data, expire=expire, use_pickle=True)

    async def get_sentiment_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取缓存的情绪数据"""
        cache_key = f"sentiment_data:{symbol}"
        return await self.get(cache_key, use_pickle=True)

    async def cache_quality_score(
        self,
        data_type: str,
        symbol: str,
        quality_result: Dict[str, Any],
        expire: int = 300
    ) -> bool:
        """缓存数据质量评分"""
        cache_key = f"quality_score:{data_type}:{symbol}"
        return await self.set(cache_key, quality_result, expire=expire, use_pickle=True)

    async def get_quality_score(
        self,
        data_type: str,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """获取缓存的数据质量评分"""
        cache_key = f"quality_score:{data_type}:{symbol}"
        return await self.get(cache_key, use_pickle=True)

    async def cache_backtest_result(
        self,
        strategy_id: str,
        backtest_data: Dict[str, Any],
        expire: int = 86400
    ) -> bool:
        """缓存回测结果"""
        cache_key = f"backtest_result:{strategy_id}"
        return await self.set(cache_key, backtest_data, expire=expire, use_pickle=True)

    async def get_backtest_result(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的回测结果"""
        cache_key = f"backtest_result:{strategy_id}"
        return await self.get(cache_key, use_pickle=True)

    async def invalidate_symbol_cache(self, symbol: str) -> int:
        """清除指定股票代码的所有缓存"""
        patterns = [
            f"unified_data:*:{symbol}:*",
            f"unified_series:*:{symbol}",
            f"market_data:{symbol}",
            f"sentiment_data:{symbol}"
        ]

        deleted_count = 0
        for pattern in patterns:
            deleted_count += await self.delete_pattern(pattern)

        return deleted_count

    async def invalidate_source_cache(self, source: str) -> int:
        """清除指定数据源的所有缓存"""
        patterns = [
            f"unified_data:{source}:*",
            f"unified_series:{source}:*",
            f"quality_score:{source}:*"
        ]

        deleted_count = 0
        for pattern in patterns:
            deleted_count += await self.delete_pattern(pattern)

        return deleted_count

    def _get_default_ttl_for_source(self, source: str) -> int:
        """根据数据源类型获取默认TTL"""
        ttl_mapping = {
            'price': 30,         # 30 seconds for price data
            'hkma': 3600,        # 1 hour for HKMA data
            'sentiment': 900,    # 15 minutes for sentiment data
            'alternative': 1800, # 30 minutes for alternative data
            'backtest': 86400    # 24 hours for backtest results
        }
        return ttl_mapping.get(source, 300)  # Default 5 minutes

    async def close(self):
        """关闭连接"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self.redis_pool:
                await self.redis_pool.disconnect()

            self._is_connected = False
            logger.info("缓存服务连接已关闭")

        except Exception as e:
            logger.error(f"关闭缓存服务连接失败: {e}")

# 创建全局缓存服务实例
cache_service = CacheService()

# 缓存键前缀常量
CACHE_KEYS = {
    "USER_STRATEGIES": "user_strategies",
    "STRATEGY_PERFORMANCE": "strategy_performance",
    "USER_DASHBOARD": "user_dashboard",
    "REALTIME_SIGNALS": "realtime_signals",
    "MARKET_DATA": "market_data",
    "USER_PREFERENCES": "user_preferences",
    "API_STATS": "api_stats"
}

# 缓存过期时间常量（秒）
CACHE_TTL = {
    "SHORT": 60,      # 1分钟
    "MEDIUM": 300,    # 5分钟
    "LONG": 3600,     # 1小时
    "DAILY": 86400    # 24小时
}

__all__ = [
    "CacheService",
    "cache_service",
    "CACHE_KEYS",
    "CACHE_TTL"
]