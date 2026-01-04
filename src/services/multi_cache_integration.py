"""
Multi-Level Cache Integration
===========================

Redis-InfluxDB multi-level caching system with intelligent data management
for optimal performance in strategy management and real-time data processing.
"""

import asyncio
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import zlib
from collections import defaultdict, deque
import time as time_module

import aioredis
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class CacheTier(str, Enum):
    """Cache tiers with different characteristics"""
    L1_REALTIME = "l1_realtime"     # Hot data - seconds TTL
    L2_QUERIES = "l2_queries"       # Query results - minutes TTL
    L3_SESSION = "l3_session"       # Session data - hours TTL
    L4_ARCHIVE = "l4_archive"       # Cold data - days TTL


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    tier: CacheTier
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: int = 0
    tags: Dict[str, str] = None
    compressed: bool = False

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.size_bytes == 0:
            self.size_bytes = len(pickle.dumps(self.value))

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl_seconds <= 0:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    def access(self):
        """Update access statistics"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheConfig:
    """Configuration for a cache tier"""
    tier: CacheTier
    max_size_mb: int
    max_entries: int
    default_ttl: int
    compression_threshold: int = 1024  # bytes
    eviction_policy: str = "lru"  # lru, lfu, fifo
    write_through: bool = False
    write_behind: bool = False
    write_behind_delay: float = 5.0  # seconds


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    tier: CacheTier
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    promotions: int = 0
    demotions: int = 0
    size_bytes: int = 0
    entries_count: int = 0
    avg_response_time_ms: float = 0.0
    compression_ratio: float = 0.0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate


class InfluxDBQueryCache:
    """Advanced InfluxDB query result caching"""

    def __init__(
        self,
        influx_client: InfluxDBClient,
        redis_client: aioredis.Redis,
        bucket: str = "strategy_data",
        org: str = "default"
    ):
        self.influx_client = influx_client
        self.redis_client = redis_client
        self.bucket = bucket
        self.org = org
        self.query_signatures = {}  # Cache of query signatures
        self._lock = asyncio.Lock()

    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent hashing"""
        # Remove extra whitespace
        query = ' '.join(query.split())
        # Convert to lowercase for case-insensitive comparison
        return query.lower()

    def _query_signature(
        self,
        query: str,
        params: Dict = None,
        time_range: Tuple[datetime, datetime] = None
    ) -> str:
        """Generate deterministic signature for query"""
        normalized = self._normalize_query(query)

        signature_data = {
            'query': normalized,
            'params': params or {},
            'time_range': None
        }

        if time_range:
            signature_data['time_range'] = {
                'start': time_range[0].isoformat(),
                'end': time_range[1].isoformat()
            }

        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.sha256(signature_str.encode()).hexdigest()

    async def cached_query(
        self,
        query: str,
        params: Dict = None,
        time_range: Tuple[datetime, datetime] = None,
        ttl_seconds: int = 3600
    ) -> pd.DataFrame:
        """
        Execute query with intelligent caching

        Args:
            query: FluxQL query
            params: Query parameters
            time_range: Time range for query
            ttl_seconds: Cache TTL

        Returns:
            Query result DataFrame
        """
        signature = self._query_signature(query, params, time_range)
        cache_key = f"influx:query:{signature}"

        # Check cache
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            try:
                # Deserialize cached result
                if isinstance(cached_data, bytes):
                    decompressed = zlib.decompress(cached_data)
                    df = pickle.loads(decompressed)
                    logger.debug(f"Query cache hit: {signature[:16]}")
                    return df
            except Exception as e:
                logger.warning(f"Failed to deserialize cached query: {e}")

        # Cache miss - execute query
        logger.debug(f"Query cache miss: {signature[:16]}")

        # Build query with time range
        if time_range:
            start, end = time_range
            if 'range' not in query.lower():
                range_clause = f'|> range(start: {start.isoformat()}, stop: {end.isoformat()})'
                query = f'from(bucket: "{self.bucket}") {range_clause} {query}'

        # Execute query
        query_api = self.influx_client.query_api()
        result_df = query_api.query_data_frame(query, params=params)

        # Cache the result
        if not result_df.empty:
            try:
                serialized = pickle.dumps(result_df)
                compressed = zlib.compress(serialized, level=6)

                await self.redis_client.setex(
                    cache_key,
                    ttl_seconds,
                    compressed
                )

                # Store metadata
                metadata = {
                    'signature': signature,
                    'query': query,
                    'params': params or {},
                    'created_at': datetime.now().isoformat(),
                    'rows_count': len(result_df),
                    'size_compressed': len(compressed),
                    'size_uncompressed': len(serialized)
                }

                await self.redis_client.hset(
                    f"{cache_key}:meta",
                    mapping=metadata
                )

            except Exception as e:
                logger.warning(f"Failed to cache query result: {e}")

        return result_df

    async def invalidate_queries_by_pattern(self, pattern: str) -> int:
        """Invalidate cached queries matching pattern"""
        pattern = f"influx:query:*"
        cursor = 0
        invalidated = 0

        async with self._lock:
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    # Check metadata for pattern match
                    for key in keys:
                        if key.endswith(":meta"):
                            continue

                        meta_key = f"{key}:meta"
                        if await self.redis_client.exists(meta_key):
                            query = await self.redis_client.hget(meta_key, 'query')
                            if query and pattern in query.decode():
                                await self.redis_client.delete(key, meta_key)
                                invalidated += 1

                if cursor == 0:
                    break

        logger.info(f"Invalidated {invalidated} query cache entries")
        return invalidated


class RealTimeDataStream:
    """Manages real-time data streaming with caching"""

    def __init__(
        self,
        redis_client: aioredis.Redis,
        influx_client: InfluxDBClient,
        buffer_size: int = 1000,
        flush_interval: float = 1.0
    ):
        self.redis_client = redis_client
        self.influx_client = influx_client
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        self.data_buffers = defaultdict(deque)
        self._flush_tasks = {}
        self._lock = asyncio.Lock()

    async def ingest_data_point(
        self,
        measurement: str,
        tags: Dict[str, str],
        fields: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """
        Ingest a single data point

        Args:
            measurement: InfluxDB measurement name
            tags: Tag key-value pairs
            fields: Field key-value pairs
            timestamp: Data point timestamp
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Create data point
        data_point = {
            'measurement': measurement,
            'tags': tags,
            'fields': fields,
            'timestamp': timestamp
        }

        # Cache in Redis for immediate access
        symbol = tags.get('symbol', 'unknown')
        cache_key = f"rt:{measurement}:{symbol}"

        await self.redis_client.setex(
            cache_key,
            60,  # 1 minute TTL for real-time data
            json.dumps(data_point, default=str)
        )

        # Add to buffer for InfluxDB write
        buffer_key = f"{measurement}:{symbol}"
        async with self._lock:
            buffer = self.data_buffers[buffer_key]
            buffer.append(data_point)

            # Start flush task if not running
            if buffer_key not in self._flush_tasks:
                self._flush_tasks[buffer_key] = asyncio.create_task(
                    self._flush_buffer(buffer_key)
                )

            # Trigger flush if buffer is full
            if len(buffer) >= self.buffer_size:
                task = self._flush_tasks.get(buffer_key)
                if task and not task.done():
                    task.cancel()
                self._flush_tasks[buffer_key] = asyncio.create_task(
                    self._flush_buffer(buffer_key, immediate=True)
                )

    async def get_latest_data(
        self,
        measurement: str,
        symbol: str,
        fields: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """Get latest data point from cache"""
        cache_key = f"rt:{measurement}:{symbol}"
        cached_data = await self.redis_client.get(cache_key)

        if cached_data:
            try:
                data = json.loads(cached_data)
                if fields:
                    data['fields'] = {
                        k: v for k, v in data['fields'].items()
                        if k in fields
                    }
                return data
            except Exception as e:
                logger.warning(f"Failed to parse cached data: {e}")

        return None

    async def _flush_buffer(self, buffer_key: str, immediate: bool = False):
        """Flush data buffer to InfluxDB"""
        try:
            # Wait for flush interval or immediate flush
            if not immediate:
                await asyncio.sleep(self.flush_interval)

            async with self._lock:
                buffer = self.data_buffers[buffer_key]
                if not buffer:
                    return

                # Extract data points
                data_points = list(buffer)
                buffer.clear()

                # Remove flush task reference
                self._flush_tasks.pop(buffer_key, None)

            # Convert to InfluxDB points
            points = []
            for dp in data_points:
                point = Point(dp['measurement'])

                # Add tags
                for tag_key, tag_value in dp['tags'].items():
                    point = point.tag(tag_key, str(tag_value))

                # Add fields
                for field_key, field_value in dp['fields'].items():
                    point = point.field(field_key, field_value)

                # Set timestamp
                point = point.time(dp['timestamp'])
                points.append(point)

            # Write to InfluxDB
            if points:
                write_api = self.influx_client.write_api(
                    write_options=ASYNCHRONOUS
                )
                write_api.write(
                    bucket="realtime_data",
                    record=points
                )
                logger.debug(f"Flushed {len(points)} points to InfluxDB")

        except asyncio.CancelledError:
            # Task was cancelled for immediate flush
            return
        except Exception as e:
            logger.error(f"Failed to flush buffer {buffer_key}: {e}")


class MultiLevelCacheManager:
    """
    Advanced multi-level cache manager with Redis-InfluxDB integration
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        influx_url: str = "http://localhost:8086",
        influx_token: str = "",
        influx_org: str = "default",
        config: Optional[Dict[CacheTier, CacheConfig]] = None
    ):
        # Default configuration
        self.tier_configs = config or {
            CacheTier.L1_REALTIME: CacheConfig(
                tier=CacheTier.L1_REALTIME,
                max_size_mb=64,
                max_entries=10000,
                default_ttl=60,
                eviction_policy="lru"
            ),
            CacheTier.L2_QUERIES: CacheConfig(
                tier=CacheTier.L2_QUERIES,
                max_size_mb=256,
                max_entries=50000,
                default_ttl=300,
                compression_threshold=512,
                eviction_policy="lfu"
            ),
            CacheTier.L3_SESSION: CacheConfig(
                tier=CacheTier.L3_SESSION,
                max_size_mb=512,
                max_entries=100000,
                default_ttl=3600,
                compression_threshold=256,
                eviction_policy="lru"
            ),
            CacheTier.L4_ARCHIVE: CacheConfig(
                tier=CacheTier.L4_ARCHIVE,
                max_size_mb=1024,
                max_entries=500000,
                default_ttl=86400,
                compression_threshold=128,
                eviction_policy="fifo"
            )
        }

        # Connection parameters
        self.redis_url = redis_url
        self.influx_url = influx_url
        self.influx_token = influx_token
        self.influx_org = influx_org

        # Initialize clients
        self.redis_client: Optional[aioredis.Redis] = None
        self.influx_client: Optional[InfluxDBClient] = None

        # Specialized components
        self.query_cache: Optional[InfluxDBQueryCache] = None
        self.realtime_stream: Optional[RealTimeDataStream] = None

        # In-memory tracking
        self.memory_stores = {}  # L1 cache
        self.metrics = {
            tier: CacheMetrics(tier=tier)
            for tier in CacheTier
        }

        # Response time tracking
        self._response_times = defaultdict(lambda: deque(maxlen=100))

        # Background tasks
        self._background_tasks = set()
        self._shutdown = False

    async def initialize(self):
        """Initialize cache manager and connections"""
        # Initialize Redis
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                decode_responses=False
            )
            await self.redis_client.ping()
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

        # Initialize InfluxDB
        try:
            self.influx_client = InfluxDBClient(
                url=self.influx_url,
                token=self.influx_token,
                org=self.influx_org
            )
            health = self.influx_client.health()
            if health.status == "pass":
                logger.info("InfluxDB client initialized")
            else:
                logger.warning(f"InfluxDB health: {health.message}")
        except Exception as e:
            logger.warning(f"Failed to initialize InfluxDB: {e}")

        # Initialize specialized components
        if self.redis_client and self.influx_client:
            self.query_cache = InfluxDBQueryCache(
                self.influx_client,
                self.redis_client
            )

            self.realtime_stream = RealTimeDataStream(
                self.redis_client,
                self.influx_client
            )

        # Initialize memory stores
        for tier in [CacheTier.L1_REALTIME]:
            self.memory_stores[tier] = {}

        # Start background tasks
        self._start_background_tasks()

        logger.info("Multi-level cache manager initialized")

    async def get(
        self,
        key: str,
        tier: Optional[CacheTier] = None,
        fallback: bool = True,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[Any]:
        """
        Get value from cache with intelligent tier selection

        Args:
            key: Cache key
            tier: Specific tier to check (None for auto-select)
            fallback: Whether to fallback to other tiers
            tags: Tags for metrics

        Returns:
            Cached value or None
        """
        start_time = time_module.time()

        # Determine search order
        if tier:
            search_tiers = [tier]
        else:
            search_tiers = [
                CacheTier.L1_REALTIME,
                CacheTier.L2_QUERIES,
                CacheTier.L3_SESSION,
                CacheTier.L4_ARCHIVE
            ]

        # Search through tiers
        for current_tier in search_tiers:
            value = await self._get_from_tier(key, current_tier)

            if value is not None:
                # Update metrics
                self.metrics[current_tier].hits += 1
                self._track_response_time(current_tier, start_time)

                # Promote to higher tier if needed
                if fallback and current_tier != CacheTier.L1_REALTIME:
                    await self._promote_key(key, value, current_tier)

                return value

            # Track miss for this tier
            self.metrics[current_tier].misses += 1

        self._track_response_time(tier or CacheTier.L4_ARCHIVE, start_time)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        tier: CacheTier = CacheTier.L3_SESSION,
        ttl_seconds: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
        compress: Optional[bool] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            tier: Target tier
            ttl_seconds: Custom TTL
            tags: Metadata tags
            compress: Force compression

        Returns:
            True if successful
        """
        try:
            config = self.tier_configs[tier]
            ttl = ttl_seconds or config.default_ttl

            # Determine if compression is needed
            should_compress = (
                compress or
                (compress is None and len(pickle.dumps(value)) > config.compression_threshold)
            )

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                tier=tier,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl_seconds=ttl,
                tags=tags or {},
                compressed=should_compress
            )

            # Store in appropriate tier
            success = await self._store_in_tier(entry)

            if success:
                self.metrics[tier].sets += 1
                self.metrics[tier].size_bytes += entry.size_bytes
                self.metrics[tier].entries_count += 1

                # Update compression ratio
                if should_compress:
                    original_size = len(pickle.dumps(value))
                    compressed_size = entry.size_bytes
                    ratio = compressed_size / original_size if original_size > 0 else 1.0
                    self.metrics[tier].compression_ratio = (
                        self.metrics[tier].compression_ratio * 0.9 + ratio * 0.1
                    )

            return success

        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False

    async def delete(self, key: str, tier: Optional[CacheTier] = None) -> bool:
        """Delete key from cache"""
        deleted = False

        if tier:
            deleted = await self._delete_from_tier(key, tier)
        else:
            # Delete from all tiers
            for t in CacheTier:
                if await self._delete_from_tier(key, t):
                    deleted = True
                    self.metrics[t].deletes += 1

        return deleted

    async def invalidate_by_tags(self, tags: Dict[str, str]) -> int:
        """Invalidate all entries matching tags"""
        invalidated = 0

        # This is expensive - in production, maintain tag indexes
        for tier in CacheTier:
            if tier == CacheTier.L1_REALTIME:
                # Search memory store
                to_delete = []
                for key, entry in self.memory_stores[tier].items():
                    if all(entry.tags.get(k) == v for k, v in tags.items()):
                        to_delete.append(key)

                for key in to_delete:
                    del self.memory_stores[tier][key]
                    invalidated += 1
            else:
                # Search Redis
                pattern = f"{tier.value}:*"
                cursor = 0

                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor,
                        match=pattern,
                        count=100
                    )

                    for key in keys:
                        if key.endswith(":meta"):
                            continue

                        # Check metadata
                        meta_key = f"{key}:meta"
                        if await self.redis_client.exists(meta_key):
                            stored_tags = await self.redis_client.hgetall(meta_key)
                            if all(stored_tags.get(f"tag_{k}") == v for k, v in tags.items()):
                                await self.redis_client.delete(key, meta_key)
                                invalidated += 1

                    if cursor == 0:
                        break

        logger.info(f"Invalidated {invalidated} entries by tags")
        return invalidated

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        metrics = {}
        total_size = 0
        total_entries = 0

        for tier in CacheTier:
            tier_metrics = self.metrics[tier]

            # Update current stats
            if tier == CacheTier.L1_REALTIME:
                tier_metrics.entries_count = len(self.memory_stores.get(tier, {}))
                tier_metrics.size_bytes = sum(
                    e.size_bytes for e in self.memory_stores.get(tier, {}).values()
                )

            total_size += tier_metrics.size_bytes
            total_entries += tier_metrics.entries_count

            metrics[tier.value] = {
                'hits': tier_metrics.hits,
                'misses': tier_metrics.misses,
                'hit_rate': tier_metrics.hit_rate,
                'sets': tier_metrics.sets,
                'deletes': tier_metrics.deletes,
                'evictions': tier_metrics.evictions,
                'promotions': tier_metrics.promotions,
                'demotions': tier_metrics.demotions,
                'size_mb': tier_metrics.size_bytes / (1024 * 1024),
                'entries_count': tier_metrics.entries_count,
                'avg_response_time_ms': tier_metrics.avg_response_time_ms,
                'compression_ratio': tier_metrics.compression_ratio
            }

        # Overall metrics
        total_hits = sum(m.hits for m in self.metrics.values())
        total_misses = sum(m.misses for m in self.metrics.values())

        metrics['overall'] = {
            'total_hits': total_hits,
            'total_misses': total_misses,
            'overall_hit_rate': total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0,
            'total_size_mb': total_size / (1024 * 1024),
            'total_entries': total_entries
        }

        return metrics

    async def optimize_performance(self):
        """Run performance optimization routines"""
        logger.info("Starting cache performance optimization")

        # 1. Evict expired entries
        await self._evict_expired()

        # 2. Rebalance tiers
        await self._rebalance_tiers()

        # 3. Optimize compression
        await self._optimize_compression()

        # 4. Compact Redis memory
        await self._compact_memory()

        logger.info("Cache optimization completed")

    async def shutdown(self):
        """Graceful shutdown"""
        self._shutdown = True

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Flush any remaining buffers
        if self.realtime_stream:
            # Flush all buffers
            for buffer_key in list(self.realtime_stream.data_buffers.keys()):
                await self.realtime_stream._flush_buffer(buffer_key, immediate=True)

        # Close connections
        if self.redis_client:
            await self.redis_client.close()

        if self.influx_client:
            self.influx_client.close()

        logger.info("Cache manager shutdown complete")

    async def _get_from_tier(self, key: str, tier: CacheTier) -> Optional[Any]:
        """Get value from specific tier"""
        if tier == CacheTier.L1_REALTIME:
            # Memory store
            entry = self.memory_stores.get(tier, {}).get(key)
            if entry:
                if not entry.is_expired():
                    entry.access()
                    return entry.value
                else:
                    # Remove expired entry
                    del self.memory_stores[tier][key]
            return None

        # Redis tiers
        tier_key = f"{tier.value}:{key}"
        value = await self.redis_client.get(tier_key)

        if value:
            # Update access time
            meta_key = f"{tier_key}:meta"
            await self.redis_client.hset(
                meta_key,
                'last_accessed',
                datetime.now().isoformat()
            )

            # Decompress if needed
            meta = await self.redis_client.hgetall(meta_key)
            if meta.get(b'compressed', b'false').decode() == 'true':
                value = pickle.loads(zlib.decompress(value))
            else:
                value = pickle.loads(value)

            return value

        return None

    async def _store_in_tier(self, entry: CacheEntry) -> bool:
        """Store entry in specific tier"""
        if entry.tier == CacheTier.L1_REALTIME:
            # Memory store
            store = self.memory_stores.setdefault(entry.tier, {})

            # Check space constraints
            config = self.tier_configs[entry.tier]
            current_size = sum(e.size_bytes for e in store.values())

            if current_size + entry.size_bytes > config.max_size_mb * 1024 * 1024:
                await self._evict_from_tier(entry.tier, entry.size_bytes)

            store[entry.key] = entry
            return True

        # Redis tiers
        tier_key = f"{entry.tier.value}:{entry.key}"

        # Prepare value
        value = entry.value
        if entry.compressed:
            value = zlib.compress(pickle.dumps(value))
        else:
            value = pickle.dumps(value)

        # Store value with TTL
        await self.redis_client.setex(
            tier_key,
            entry.ttl_seconds,
            value
        )

        # Store metadata
        metadata = {
            'created_at': entry.created_at.isoformat(),
            'last_accessed': entry.last_accessed.isoformat(),
            'access_count': str(entry.access_count),
            'size_bytes': str(entry.size_bytes),
            'compressed': str(entry.compressed),
            'tags': json.dumps(entry.tags)
        }

        await self.redis_client.hset(f"{tier_key}:meta", mapping=metadata)

        return True

    async def _delete_from_tier(self, key: str, tier: CacheTier) -> bool:
        """Delete key from specific tier"""
        if tier == CacheTier.L1_REALTIME:
            store = self.memory_stores.get(tier, {})
            if key in store:
                del store[key]
                self.metrics[tier].entries_count = max(0, self.metrics[tier].entries_count - 1)
                return True
            return False

        # Redis tiers
        tier_key = f"{tier.value}:{key}"
        deleted = await self.redis_client.delete(tier_key)
        await self.redis_client.delete(f"{tier_key}:meta")

        if deleted:
            self.metrics[tier].entries_count = max(0, self.metrics[tier].entries_count - 1)

        return deleted > 0

    async def _promote_key(self, key: str, value: Any, from_tier: CacheTier):
        """Promote key to higher priority tier"""
        # Find promotion target
        tiers = [
            CacheTier.L1_REALTIME,
            CacheTier.L2_QUERIES,
            CacheTier.L3_SESSION,
            CacheTier.L4_ARCHIVE
        ]

        current_index = tiers.index(from_tier)
        if current_index > 0:
            target_tier = tiers[current_index - 1]

            # Store in higher tier
            await self.set(key, value, target_tier)
            self.metrics[target_tier].promotions += 1
            self.metrics[from_tier].demotions += 1

    async def _evict_from_tier(self, tier: CacheTier, required_space: int):
        """Evict entries from tier to free space"""
        if tier == CacheTier.L1_REALTIME:
            store = self.memory_stores.get(tier, {})
            config = self.tier_configs[tier]

            # Sort by eviction policy
            if config.eviction_policy == "lru":
                sorted_entries = sorted(
                    store.items(),
                    key=lambda x: x[1].last_accessed
                )
            elif config.eviction_policy == "lfu":
                sorted_entries = sorted(
                    store.items(),
                    key=lambda x: x[1].access_count
                )
            else:  # fifo
                sorted_entries = sorted(
                    store.items(),
                    key=lambda x: x[1].created_at
                )

            # Evict until enough space
            freed = 0
            for key, entry in sorted_entries:
                del store[key]
                freed += entry.size_bytes
                self.metrics[tier].evictions += 1

                if freed >= required_space:
                    break

    async def _evict_expired(self):
        """Remove expired entries from all tiers"""
        # Check memory store
        for tier in [CacheTier.L1_REALTIME]:
            store = self.memory_stores.get(tier, {})
            expired_keys = []

            for key, entry in store.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del store[key]
                self.metrics[tier].evictions += 1

        # Redis handles TTL automatically

    async def _rebalance_tiers(self):
        """Rebalance data across tiers based on access patterns"""
        # Identify hot/cold data
        hot_keys = set()
        cold_keys = set()

        for tier in [CacheTier.L1_REALTIME, CacheTier.L2_QUERIES]:
            store = self.memory_stores.get(tier, {})
            for key, entry in store.items():
                # Calculate access rate
                age_hours = (datetime.now() - entry.created_at).total_seconds() / 3600
                access_rate = entry.access_count / age_hours if age_hours > 0 else 0

                if access_rate > 10:  # High access rate
                    hot_keys.add(key)
                elif access_rate < 0.1 and age_hours > 24:  # Low access rate and old
                    cold_keys.add(key)

        # Move hot data to higher tiers
        for key in hot_keys:
            value = await self.get(key, fallback=False)
            if value:
                await self.set(key, value, CacheTier.L1_REALTIME)

        # Move cold data to lower tiers
        for key in cold_keys:
            value = await self.get(key, fallback=False)
            if value:
                await self.set(key, value, CacheTier.L4_ARCHIVE)

    async def _optimize_compression(self):
        """Optimize compression settings"""
        for tier in [CacheTier.L3_SESSION, CacheTier.L4_ARCHIVE]:
            # Find uncompressed large entries
            pattern = f"{tier.value}:*"
            cursor = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match=pattern,
                    count=50
                )

                for key in keys:
                    if key.endswith(":meta"):
                        continue

                    # Check size
                    size = await self.redis_client.memory_usage(key)
                    if size > 10 * 1024:  # 10KB
                        # Check if compressed
                        meta = await self.redis_client.hgetall(f"{key}:meta")
                        if meta.get(b'compressed', b'false').decode() == 'false':
                            # Compress the entry
                            value = await self.redis_client.get(key)
                            if value:
                                compressed = zlib.compress(value)
                                await self.redis_client.set(key, compressed)
                                await self.redis_client.hset(
                                    f"{key}:meta",
                                    'compressed',
                                    'true'
                                )

                if cursor == 0:
                    break

    async def _compact_memory(self):
        """Compact Redis memory usage"""
        if self.redis_client:
            try:
                # Trigger Redis memory defragmentation
                await self.redis_client.execute_command('MEMORY', 'PURGE')
                logger.debug("Redis memory purged")
            except Exception as e:
                logger.warning(f"Failed to purge Redis memory: {e}")

    def _track_response_time(self, tier: CacheTier, start_time: float):
        """Track response time for metrics"""
        response_time = (time_module.time() - start_time) * 1000
        self._response_times[tier].append(response_time)

        # Update average
        if self._response_times[tier]:
            self.metrics[tier].avg_response_time_ms = np.mean(self._response_times[tier])

    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        # Metrics collection
        self._background_tasks.add(
            asyncio.create_task(self._metrics_collection_loop())
        )

        # Performance optimization
        self._background_tasks.add(
            asyncio.create_task(self._optimization_loop())
        )

    async def _metrics_collection_loop(self):
        """Collect and report metrics periodically"""
        while not self._shutdown:
            try:
                # Collect detailed metrics
                metrics = await self.get_metrics()

                # Log summary
                logger.info(
                    f"Cache metrics - Hit rate: {metrics['overall']['overall_hit_rate']:.2%}, "
                    f"Size: {metrics['overall']['total_size_mb']:.1f}MB, "
                    f"Entries: {metrics['overall']['total_entries']}"
                )

                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)

    async def _optimization_loop(self):
        """Run optimization periodically"""
        while not self._shutdown:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self.optimize_performance()
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")


# Global cache manager instance
_cache_manager: Optional[MultiLevelCacheManager] = None


async def get_cache_manager() -> MultiLevelCacheManager:
    """Get or create global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = MultiLevelCacheManager()
        await _cache_manager.initialize()
    return _cache_manager


# Utility functions for common operations
async def cache_strategy_result(
    strategy_id: str,
    result_data: Dict,
    ttl_hours: int = 24
):
    """Cache strategy backtest result"""
    cache = await get_cache_manager()
    key = f"strategy_result:{strategy_id}"
    return await cache.set(
        key,
        result_data,
        CacheTier.L3_SESSION,
        ttl_seconds=ttl_hours * 3600,
        tags={'strategy_id': strategy_id, 'type': 'backtest_result'}
    )


async def get_cached_strategy_result(strategy_id: str) -> Optional[Dict]:
    """Get cached strategy result"""
    cache = await get_cache_manager()
    key = f"strategy_result:{strategy_id}"
    return await cache.get(key, tags={'strategy_id': strategy_id})


async def cache_market_data(
    symbol: str,
    timeframe: str,
    data: pd.DataFrame,
    ttl_minutes: int = 5
):
    """Cache market data with intelligent tier selection"""
    cache = await get_cache_manager()
    key = f"market_data:{symbol}:{timeframe}"

    # Determine tier based on timeframe
    if timeframe in ['1m', '5m']:
        tier = CacheTier.L1_REALTIME
        ttl = 60  # 1 minute
    elif timeframe in ['15m', '30m', '1h']:
        tier = CacheTier.L2_QUERIES
        ttl = 300  # 5 minutes
    else:
        tier = CacheTier.L3_SESSION
        ttl = ttl_minutes * 60

    return await cache.set(
        key,
        data,
        tier,
        ttl_seconds=ttl,
        tags={'symbol': symbol, 'timeframe': timeframe, 'type': 'market_data'}
    )


async def get_cached_market_data(symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    """Get cached market data"""
    cache = await get_cache_manager()
    key = f"market_data:{symbol}:{timeframe}"
    return await cache.get(key, tags={'symbol': symbol, 'timeframe': timeframe})


__all__ = [
    'MultiLevelCacheManager',
    'get_cache_manager',
    'cache_strategy_result',
    'get_cached_strategy_result',
    'cache_market_data',
    'get_cached_market_data'
]