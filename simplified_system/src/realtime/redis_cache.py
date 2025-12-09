#!/usr/bin/env python3
"""
Redis高性能緩存層 - High-Performance Redis Caching Layer
提供亞毫秒級數據訪問能力
Sub-millisecond data access capabilities
"""

import asyncio
import json
import logging
import time
import zlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aioredis
from aioredis import Redis
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import hashlib
import numpy as np
import pandas as pd
from .safe_serialization import SafeDataSerializer, SerializationError, DeserializationError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheKeyPattern(Enum):
    """緩存鍵模式"""
    REALTIME_PRICE = "rt:price:{symbol}"
    HISTORICAL_PRICE = "hist:price:{symbol}:{timestamp}"
    MARKET_DATA = "market:{key}"
    SIGNAL_DATA = "signal:{symbol}:{signal_type}"
    USER_SESSION = "session:{user_id}"
    CALCULATION_RESULT = "calc:{calc_hash}"
    PERFORMANCE_METRICS = "metrics:{name}"
    RATE_LIMIT = "ratelimit:{key}:{window}"

@dataclass
class CacheConfig:
    """緩存配置"""
    default_ttl: int = 300  # 5分鐘
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True
    health_check_interval: int = 30
    retry_on_timeout: bool = True
    encoding: str = "utf-8"

class CacheMetrics:
    """緩存指標"""

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_hit_rate": 0.0,
            "avg_response_time_ms": 0.0,
            "total_response_time_ms": 0.0,
            "max_response_time_ms": 0.0,
            "min_response_time_ms": float('inf'),
            "connection_errors": 0,
            "serialization_errors": 0,
            "memory_usage_mb": 0.0,
            "keys_cached": 0,
            "cache_size_mb": 0.0,
            "last_update": datetime.now()
        }
        self.response_times = deque(maxlen=1000)

    def record_request(self, response_time: float, is_hit: bool):
        """記錄請求"""
        self.metrics["total_requests"] += 1
        self.metrics["total_response_time_ms"] += response_time
        self.response_times.append(response_time)

        self.metrics["max_response_time_ms"] = max(
            self.metrics["max_response_time_ms"], response_time
        )
        self.metrics["min_response_time_ms"] = min(
            self.metrics["min_response_time_ms"], response_time
        )

        if is_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

        # 更新統計指標
        total = self.metrics["total_requests"]
        if total > 0:
            self.metrics["cache_hit_rate"] = self.metrics["cache_hits"] / total
            self.metrics["avg_response_time_ms"] = self.metrics["total_response_time_ms"] / total

class DataSerializer:
    """安全數據序列化器 - 使用SafeDataSerializer避免pickle安全漏洞"""

    @staticmethod
    def serialize(data: Any) -> bytes:
        """安全序列化數據"""
        try:
            # 使用SafeDataSerializer進行安全序列化
            serialized = SafeDataSerializer.serialize(data)

            # 對大型數據進行壓縮
            if len(serialized) > 1024:
                return zlib.compress(serialized)
            return serialized

        except (SerializationError, ValueError, TypeError) as e:
            logger.error(f"Safe serialization error: {e}")
            # 記錄序列化錯誤指標
            if hasattr(DataSerializer, '_metrics'):
                DataSerializer._metrics["serialization_errors"] += 1
            raise SerializationError(f"Cannot safely serialize data: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected serialization error: {e}")
            if hasattr(DataSerializer, '_metrics'):
                DataSerializer._metrics["serialization_errors"] += 1
            raise SerializationError(f"Unexpected serialization error: {e}") from e

    @staticmethod
    def deserialize(data: bytes, data_type: str = "auto") -> Any:
        """安全反序列化數據"""
        try:
            # 首先嘗試解壓縮（如果適用）
            if data_type == "compressed" or data_type == "auto":
                try:
                    # 檢查是否為壓縮數據
                    decompressed = zlib.decompress(data)
                    data_to_deserialize = decompressed
                except:
                    # 不是壓縮數據，使用原始數據
                    data_to_deserialize = data
            else:
                data_to_deserialize = data

            # 使用SafeDataSerializer進行安全反序列化
            return SafeDataSerializer.deserialize(data_to_deserialize)

        except (DeserializationError, ValueError, UnicodeDecodeError) as e:
            logger.error(f"Safe deserialization error: {e}")
            # 記錄反序列化錯誤指標
            if hasattr(DataSerializer, '_metrics'):
                DataSerializer._metrics["serialization_errors"] += 1
            raise DeserializationError(f"Cannot safely deserialize data: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected deserialization error: {e}")
            if hasattr(DataSerializer, '_metrics'):
                DataSerializer._metrics["serialization_errors"] += 1
            raise DeserializationError(f"Unexpected deserialization error: {e}") from e

class RedisCacheManager:
    """Redis緩存管理器"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.redis_client: Optional[Redis] = None
        self.metrics = CacheMetrics()
        self.connection_pool = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._local_cache = {}  # 本地緩存用於熱點數據
        self._local_cache_max_size = 1000

    async def connect(self) -> bool:
        """連接到Redis"""
        try:
            self.redis_client = Redis(
                host='localhost',
                port=6379,
                db=0,
                encoding=self.config.encoding,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                socket_keepalive=self.config.socket_keepalive,
                health_check_interval=self.config.health_check_interval,
                retry_on_timeout=self.config.retry_on_timeout,
                max_connections=self.config.max_connections
            )

            # 測試連接
            await self.redis_client.ping()

            logger.info("Redis connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False

    async def disconnect(self):
        """斷開Redis連接"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

        if self.connection_pool:
            self.connection_pool.close()
            self.connection_pool = None

    def _get_cache_key(self, pattern: CacheKeyPattern, **kwargs) -> str:
        """生成緩存鍵"""
        return pattern.value.format(**kwargs)

    def _generate_hash(self, data: Dict[str, Any]) -> str:
        """生成數據哈希值"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """設置緩存值"""
        if not self.redis_client:
            return False

        start_time = time.perf_counter()
        cache_hit = False

        try:
            # 序列化數據
            serialized_value = DataSerializer.serialize(value)
            compressed_value = zlib.compress(serialized_value) if len(serialized_value) > 1024 else serialized_value

            # 設置TTL
            if ttl is None:
                ttl = self.config.default_ttl

            # 使用管道提高性能
            pipe = self.redis_client.pipeline()
            await pipe.setex(key, ttl, compressed_value)
            await pipe.expire(key, ttl + 60)  # 確保不過早過期
            await pipe.execute()

            cache_hit = True
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.metrics["connection_errors"] += 1
            return False

        finally:
            response_time = (time.perf_counter() - start_time) * 1000
            self.metrics.record_request(response_time, cache_hit)

    async def get(self, key: str, default: Any = None) -> Any:
        """獲取緩存值"""
        if not self.redis_client:
            return default

        start_time = time.perf_counter()
        cache_hit = False

        try:
            # 首先檢查本地緩存
            if key in self._local_cache:
                cache_hit = True
                return self._local_cache[key]

            # 從Redis獲取
            compressed_value = await self.redis_client.get(key)

            if compressed_value:
                # 嘗試解壓縮
                try:
                    decompressed = zlib.decompress(compressed_value)
                    value = DataSerializer.deserialize(decompressed, "compressed")
                except:
                    # 可能未壓縮，直接反序列化
                    value = DataSerializer.deserialize(compressed_value)

                # 更新本地緩存
                self._update_local_cache(key, value)
                cache_hit = True
                return value
            else:
                return default

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.metrics["connection_errors"] += 1
            return default

        finally:
            response_time = (time.perf_counter() - start_time) * 1000
            self.metrics.record_request(response_time, cache_hit)

    def _update_local_cache(self, key: str, value: Any):
        """更新本地緩存"""
        if len(self._local_cache) >= self._local_cache_max_size:
            # 移除最舊的條目
            oldest_key = next(iter(self._local_cache))
            del self._local_cache[oldest_key]

        self._local_cache[key] = value

    async def delete(self, key: str) -> bool:
        """刪除緩存鍵"""
        if not self.redis_client:
            return False

        try:
            # 從Redis和本地緩存中刪除
            await self.redis_client.delete(key)
            if key in self._local_cache:
                del self._local_cache[key]
            return True

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self.metrics["connection_errors"] += 1
            return False

    async def exists(self, key: str) -> bool:
        """檢查緩存鍵是否存在"""
        if not self.redis_client:
            return False

        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists check error for key {key}: {e}")
            return False

    async def set_json(self, key: str, data: Dict[str, Any], ttl: int = None) -> bool:
        """設置JSON緩存"""
        return await self.set(key, data, ttl)

    async def get_json(self, key: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """獲取JSON緩存"""
        result = await self.get(key, default)
        return result if isinstance(result, dict) else default

    async def set_price_data(self, symbol: str, price_data: Dict[str, Any], ttl: int = 60) -> bool:
        """設置實時價格數據（短TTL）"""
        key = self._get_cache_key(CacheKeyPattern.REALTIME_PRICE, symbol=symbol)
        return await self.set_json(key, price_data, ttl)

    async def get_price_data(self, symbol: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """獲取實時價格數據"""
        key = self._get_cache_key(CacheKeyPattern.REALTIME_PRICE, symbol=symbol)
        return await self.get_json(key, default)

    async def set_signal_data(self, symbol: str, signal_type: str, signal_data: Dict[str, Any], ttl: int = 300) -> bool:
        """設置信號數據"""
        key = self._get_cache_key(CacheKeyPattern.SIGNAL_DATA, symbol=symbol, signal_type=signal_type)
        return await self.set_json(key, signal_data, ttl)

    async def get_signal_data(self, symbol: str, signal_type: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """獲置信號數據"""
        key = self._get_cache_key(CacheKeyPattern.SIGNAL_DATA, symbol=symbol, signal_type=signal_type)
        return await self.get_json(key, default)

    async def set_calculation_result(self, calculation: Callable, params: Dict[str, Any], result: Any, ttl: int = 600) -> str:
        """設置計算結果緩存"""
        # 生成計算哈希
        calc_hash = self._generate_hash({
            "function": calculation.__name__,
            "params": params
        })

        key = self._get_cache_key(CacheKeyPattern.CALCULATION_RESULT, calc_hash=calc_hash)
        success = await self.set(key, result, ttl)

        if success:
            return calc_hash
        return None

    async def get_calculation_result(self, calculation: Callable, params: Dict[str, Any], default: Any = None) -> Any:
        """獲取計算結果緩存"""
        calc_hash = self._generate_hash({
            "function": calculation.__name__,
            "params": params
        })

        key = self._get_cache_key(CacheKeyPattern.CALCULATION_RESULT, calc_hash=calc_hash)
        return await self.get(key, default)

    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量獲取緩存值"""
        if not self.redis_client:
            return {key: None for key in keys}

        start_time = time.perf_counter()
        results = {}
        cache_hits = 0

        try:
            # 使用pipeline批量獲取
            pipe = self.redis_client.pipeline()
            for key in keys:
                pipe.get(key)
            redis_results = await pipe.execute()

            for key, result in zip(keys, redis_results):
                if result:
                    try:
                        # 嘗試解壓縮
                        try:
                            decompressed = zlib.decompress(result)
                            value = DataSerializer.deserialize(decompressed, "compressed")
                        except:
                            value = DataSerializer.deserialize(result)
                        results[key] = value
                        cache_hits += 1
                    except Exception as e:
                        logger.error(f"Error deserializing batch result for key {key}: {e}")
                        results[key] = None
                else:
                    results[key] = None

        except Exception as e:
            logger.error(f"Batch get error: {e}")
            self.metrics["connection_errors"] += 1
            return {key: None for key in keys}

        # 更新本地緩存
        for key, value in results.items():
            if value is not None:
                self._update_local_cache(key, value)

        response_time = (time.perf_counter() - start_time) * 1000
        avg_time = response_time / len(keys)

        for _ in range(len(keys)):
            self.metrics.record_request(avg_time, cache_hits > 0)

        return results

    async def batch_set(self, key_value_pairs: Dict[str, Any], ttl: int = None) -> Dict[str, bool]:
        """批量設置緩存值"""
        if not self.redis_client:
            return {key: False for key in key_value_pairs.keys()}

        start_time = time.perf_counter()
        results = {}

        try:
            # 序列化所有值
            serialized_pairs = {}
            for key, value in key_value_pairs.items():
                try:
                    serialized = DataSerializer.serialize(value)
                    compressed = zlib.compress(serialized) if len(serialized) > 1024 else serialized
                    serialized_pairs[key] = compressed
                except Exception as e:
                    logger.error(f"Error serializing {key}: {e}")
                    serialized_pairs[key] = None

            # 使用pipeline批量設置
            pipe = self.redis_client.pipeline()
            for key, value in serialized_pairs.items():
                if value is not None:
                    final_ttl = ttl if ttl is not None else self.config.default_ttl
                    pipe.setex(key, final_ttl, value)
            await pipe.execute()

            # 更新本地緩存
            for key, value in key_value_pairs.items():
                if value is not None:
                    self._update_local_cache(key, value)
                    results[key] = True
                else:
                    results[key] = False

        except Exception as e:
            logger.error(f"Batch set error: {e}")
            self.metrics["connection_errors"] += 1
            return {key: False for key in key_value_pairs.keys()}

        response_time = (time.perf_counter() - start_time) * 1000
        avg_time = response_time / len(key_value_pairs)

        for _ in range(len(key_value_pairs)):
            self.metrics.record_request(avg_time, True)

        return results

    async def get_cache_info(self) -> Dict[str, Any]:
        """獲取緩存信息"""
        if not self.redis_client:
            return {"error": "Redis not connected"}

        try:
            info = await self.redis_client.info()

            # 解析Redis信息
            cache_info = {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "max_memory": info.get("maxmemory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "cache_hit_rate": 0.0,
                "cache_info": info
            }

            # 計算緩存命中率
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            if hits + misses > 0:
                cache_info["cache_hit_rate"] = hits / (hits + misses)

            # 添加我們的指標
            cache_info["performance_metrics"] = self.metrics.metrics
            cache_info["local_cache_size"] = len(self._local_cache)

            return cache_info

        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {"error": str(e)}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return self.metrics.metrics

    async def clear_cache(self, pattern: str = "*") -> int:
        """清除緩存"""
        if not self.redis_client:
            return 0

        try:
            # 使用SCAN命令找到匹配的鍵
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis_client.delete(*keys)
                # 同時清理本地緩存中匹配的鍵
                keys_to_remove = [k for k in self._local_cache.keys() if pattern.replace("*", "") in k]
                for key in keys_to_remove:
                    del self._local_cache[key]

            return len(keys)

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    async def warm_up_cache(self, warmup_data: Dict[str, Any]):
        """預熱緩存"""
        logger.info(f"Warming up cache with {len(warmup_data)} items")

        start_time = time.perf_counter()
        results = await self.batch_set(warmup_data, ttl=self.config.default_ttl)

        success_count = sum(1 for success in results.values() if success)
        total_time = time.perf_counter() - start_time

        logger.info(f"Cache warm-up completed: {success_count}/{len(warmup_data)} items in {total_time:.3f}s")

# 使用示例
async def demo_redis_cache():
    """演示Redis緩存"""
    cache_manager = RedisCacheManager()

    try:
        # 連接Redis
        connected = await cache_manager.connect()
        print(f"Redis connected: {connected}")

        if connected:
            # 設置一些測試數據
            price_data = {
                "symbol": "0700.HK",
                "price": 300.50,
                "change": 1.2,
                "change_percent": 0.4,
                "volume": 15000,
                "timestamp": datetime.now().isoformat()
            }

            # 測試設置和獲取
            print("Testing set/get operations...")
            success = await cache_manager.set_price_data("0700.HK", price_data, ttl=60)
            print(f"Set operation successful: {success}")

            retrieved_data = await cache_manager.get_price_data("0700.HK")
            print(f"Retrieved data: {retrieved_data}")

            # 測試批量操作
            batch_data = {
                "0700.HK": {"price": 300.50, "volume": 15000},
                "0941.HK": {"price": 55.20, "volume": 8000},
                "1299.HK": {"price": 42.80, "volume": 12000}
            }

            print("Testing batch operations...")
            batch_results = await cache_manager.batch_set({
                f"price:{symbol}": data
                for symbol, data in batch_data.items()
            })

            print(f"Batch set results: {batch_results}")

            # 獲取緩存信息
            cache_info = await cache_manager.get_cache_info()
            print(f"Cache info: {json.dumps(cache_info, indent=2, default=str)}")

            # 獲取性能指標
            metrics = cache_manager.get_performance_metrics()
            print(f"Performance metrics: {json.dumps(metrics, indent=2, default=str)}")

    finally:
        await cache_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(demo_redis_cache())