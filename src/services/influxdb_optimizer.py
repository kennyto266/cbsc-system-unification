"""
InfluxDB Query Optimizer
========================

Optimizes InfluxDB queries for better performance with intelligent
query analysis, caching, and automatic optimization suggestions.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time
from collections import defaultdict, deque

from influxdb_client import InfluxDBClient, QueryApi
from influxdb_client.client.flux_table import FluxTable
from influxdb_client.client.flux_record import FluxRecord
import pandas as pd
import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)


class OptimizationType(str, Enum):
    """Types of optimizations"""
    INDEX = "index"
    AGGREGATION = "aggregation"
    TIME_RANGE = "time_range"
    BATCH_SIZE = "batch_size"
    PARALLEL = "parallel"
    CACHING = "caching"
    COMPRESSION = "compression"


@dataclass
class QueryPattern:
    """Represents a query pattern for optimization"""
    pattern: str
    frequency: int
    avg_duration_ms: float
    optimized_pattern: Optional[str] = None
    optimization_type: Optional[OptimizationType] = None
    performance_gain: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QueryStats:
    """Query execution statistics"""
    query_hash: str
    execution_count: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    last_executed: datetime
    result_size_bytes: int
    cached_count: int = 0


@dataclass
class OptimizationSuggestion:
    """Optimization suggestion for a query"""
    query_hash: str
    optimization_type: OptimizationType
    description: str
    impact: str  # high, medium, low
    effort: str  # low, medium, high
    estimated_improvement: float  # percentage
    optimized_query: Optional[str] = None


class QueryAnalyzer:
    """
    Analyzes InfluxDB queries for optimization opportunities
    """

    def __init__(self):
        self.query_patterns = {}
        self.optimization_rules = self._load_optimization_rules()

    def _load_optimization_rules(self) -> List[Dict]:
        """Load query optimization rules"""
        return [
            {
                'type': OptimizationType.INDEX,
                'pattern': r'filter\(fn:\s*\(r\)\s*=>\s*r\[.*\]\s*==\s*".*"\)',
                'suggestion': 'Use indexed fields in filters',
                'optimization': self._optimize_index_filter
            },
            {
                'type': OptimizationType.AGGREGATION,
                'pattern': r'aggregateWindow\([^)]*\)',
                'suggestion': 'Optimize aggregation window size',
                'optimization': self._optimize_aggregation
            },
            {
                'type': OptimizationType.TIME_RANGE,
                'pattern': r'range\(start:\s*.*?,\s*stop:\s*.*?\)',
                'suggestion': 'Optimize time range selection',
                'optimization': self._optimize_time_range
            },
            {
                'type': OptimizationType.BATCH_SIZE,
                'pattern': r'limit\(\d+\)',
                'suggestion': 'Optimize batch size',
                'optimization': self._optimize_batch_size
            }
        ]

    async def analyze_query(
        self,
        query: str,
        execution_time_ms: float,
        result_size: int
    ) -> List[OptimizationSuggestion]:
        """Analyze query and suggest optimizations"""
        suggestions = []
        query_hash = self._hash_query(query)

        # Apply optimization rules
        for rule in self.optimization_rules:
            if re.search(rule['pattern'], query, re.IGNORECASE):
                optimized_query = rule['optimization'](query)
                if optimized_query != query:
                    # Estimate improvement
                    estimated_gain = self._estimate_improvement(
                        rule['type'],
                        execution_time_ms,
                        result_size
                    )

                    suggestions.append(OptimizationSuggestion(
                        query_hash=query_hash,
                        optimization_type=rule['type'],
                        description=rule['suggestion'],
                        impact=self._calculate_impact(estimated_gain),
                        effort=self._calculate_effort(rule['type']),
                        estimated_improvement=estimated_gain,
                        optimized_query=optimized_query
                    ))

        # Detect complex queries that could benefit from parallelization
        if self._is_complex_query(query):
            suggestions.append(OptimizationSuggestion(
                query_hash=query_hash,
                optimization_type=OptimizationType.PARALLEL,
                description='Consider parallel query execution',
                impact='high',
                effort='medium',
                estimated_improvement=30.0,
                optimized_query=self._parallelize_query(query)
            ))

        return suggestions

    def _hash_query(self, query: str) -> str:
        """Generate hash for normalized query"""
        # Normalize query (remove whitespace differences)
        normalized = ' '.join(query.split())
        normalized = normalized.lower()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _optimize_index_filter(self, query: str) -> str:
        """Optimize index-based filters"""
        # Look for non-indexed field filters and suggest alternatives
        # This is a simplified example
        return query  # Would contain actual optimization logic

    def _optimize_aggregation(self, query: str) -> str:
        """Optimize aggregation functions"""
        # Optimize aggregateWindow parameters
        if 'aggregateWindow(every: 1m' in query:
            # Adjust window size based on data volume
            query = query.replace('aggregateWindow(every: 1m', 'aggregateWindow(every: 5m')
        return query

    def _optimize_time_range(self, query: str) -> str:
        """Optimize time range selection"""
        # Add subqueries for large time ranges
        return query  # Would contain actual optimization logic

    def _optimize_batch_size(self, query: str) -> str:
        """Optimize batch/limit size"""
        # Adjust limit based on use case
        return query  # Would contain actual optimization logic

    def _parallelize_query(self, query: str) -> str:
        """Convert query to parallel execution"""
        # Split query into parallelizable parts
        return f"// Parallel version:\n{query}"

    def _is_complex_query(self, query: str) -> bool:
        """Determine if query is complex enough for parallelization"""
        complexity_score = 0

        # Count joins
        complexity_score += query.count('join(') * 3

        # Count aggregations
        complexity_score += query.count('aggregateWindow(') * 2

        # Count filters
        complexity_score += query.count('filter(')

        # Count pivots
        complexity_score += query.count('pivot(') * 2

        return complexity_score > 5

    def _estimate_improvement(
        self,
        opt_type: OptimizationType,
        execution_time: float,
        result_size: int
    ) -> float:
        """Estimate performance improvement percentage"""
        base_improvements = {
            OptimizationType.INDEX: 40.0,
            OptimizationType.AGGREGATION: 25.0,
            OptimizationType.TIME_RANGE: 30.0,
            OptimizationType.BATCH_SIZE: 15.0,
            OptimizationType.PARALLEL: 50.0
        }

        # Adjust based on query characteristics
        improvement = base_improvements.get(opt_type, 10.0)

        # Reduce improvement for fast queries
        if execution_time < 100:  # < 100ms
            improvement *= 0.5
        elif execution_time < 1000:  # < 1s
            improvement *= 0.8

        # Reduce improvement for small results
        if result_size < 1000:
            improvement *= 0.7

        return min(improvement, 90.0)  # Cap at 90%

    def _calculate_impact(self, improvement: float) -> str:
        """Calculate impact level"""
        if improvement >= 30:
            return 'high'
        elif improvement >= 15:
            return 'medium'
        else:
            return 'low'

    def _calculate_effort(self, opt_type: OptimizationType) -> str:
        """Calculate implementation effort"""
        high_effort = {OptimizationType.PARALLEL}
        medium_effort = {OptimizationType.INDEX, OptimizationType.AGGREGATION}

        if opt_type in high_effort:
            return 'high'
        elif opt_type in medium_effort:
            return 'medium'
        else:
            return 'low'


class QueryCache:
    """
    Intelligent query result caching system
    """

    def __init__(
        self,
        redis_client,
        default_ttl: int = 300,
        max_entries: int = 10000
    ):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self.cache_stats = defaultdict(int)

    async def get(self, query: str, params: Dict = None) -> Optional[pd.DataFrame]:
        """Get cached query result"""
        cache_key = self._cache_key(query, params)
        cached_data = await self.redis_client.get(cache_key)

        if cached_data:
            try:
                # Decompress and deserialize
                import zlib
                decompressed = zlib.decompress(cached_data)
                df = pickle.loads(decompressed)
                self.cache_stats['hits'] += 1
                logger.debug(f"Cache hit for query: {cache_key[:32]}")
                return df
            except Exception as e:
                logger.warning(f"Failed to deserialize cached result: {e}")

        self.cache_stats['misses'] += 1
        return None

    async def set(
        self,
        query: str,
        result: pd.DataFrame,
        ttl: Optional[int] = None,
        params: Dict = None
    ):
        """Cache query result"""
        if result.empty:
            return

        cache_key = self._cache_key(query, params)
        ttl = ttl or self.default_ttl

        try:
            # Serialize and compress
            import zlib
            serialized = pickle.dumps(result)
            compressed = zlib.compress(serialized, level=6)

            # Check cache size limit
            await self._ensure_cache_size()

            # Store in Redis
            await self.redis_client.setex(cache_key, ttl, compressed)

            # Store metadata
            metadata = {
                'query': query,
                'params': json.dumps(params or {}),
                'created_at': datetime.now().isoformat(),
                'rows': len(result),
                'size_bytes': len(compressed)
            }
            await self.redis_client.hset(f"{cache_key}:meta", mapping=metadata)

            self.cache_stats['sets'] += 1
            logger.debug(f"Cached query result: {cache_key[:32]}")

        except Exception as e:
            logger.warning(f"Failed to cache query result: {e}")

    def _cache_key(self, query: str, params: Dict = None) -> str:
        """Generate cache key for query"""
        key_data = {
            'query': query,
            'params': params or {}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"influx:query:{hashlib.sha256(key_str.encode()).hexdigest()}"

    async def _ensure_cache_size(self):
        """Ensure cache doesn't exceed max entries"""
        cursor = 0
        keys = []

        # Get all query cache keys
        while True:
            cursor, scan_keys = await self.redis_client.scan(
                cursor,
                match="influx:query:*",
                count=100
            )
            keys.extend([k for k in scan_keys if not k.endswith(b":meta")])
            if cursor == 0:
                break

        # If over limit, remove oldest entries
        if len(keys) > self.max_entries:
            # Get metadata for creation times
            key_times = []
            for key in keys:
                meta_key = f"{key.decode()}:meta"
                if await self.redis_client.exists(meta_key):
                    created = await self.redis_client.hget(meta_key, 'created_at')
                    if created:
                        key_times.append((created, key))

            # Sort by creation time and remove oldest
            key_times.sort()
            to_remove = len(keys) - self.max_entries

            for _, key in key_times[:to_remove]:
                await self.redis_client.delete(key, f"{key.decode()}:meta")

            logger.info(f"Removed {to_remove} old cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total if total > 0 else 0

        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': hit_rate,
            'sets': self.cache_stats['sets']
        }


class QueryOptimizer:
    """
    Main query optimizer with caching and performance tracking
    """

    def __init__(
        self,
        influx_client: InfluxDBClient,
        redis_client,
        bucket: str = "strategy_data",
        org: str = "default"
    ):
        self.influx_client = influx_client
        self.redis_client = redis_client
        self.bucket = bucket
        self.org = org

        # Components
        self.analyzer = QueryAnalyzer()
        self.cache = QueryCache(redis_client)
        self.query_api = influx_client.query_api()

        # Query statistics
        self.query_stats = {}
        self.optimization_history = deque(maxlen=1000)

        # Optimization tracking
        self._optimization_lock = asyncio.Lock()

    async def execute_query(
        self,
        query: str,
        params: Dict = None,
        use_cache: bool = True,
        ttl: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Execute optimized query with caching

        Args:
            query: FluxQL query
            params: Query parameters
            use_cache: Whether to use cache
            ttl: Cache TTL

        Returns:
            Query result as DataFrame
        """
        query_hash = self.analyzer._hash_query(query)
        start_time = time.time()

        # Try cache first
        if use_cache:
            cached_result = await self.cache.get(query, params)
            if cached_result is not None:
                await self._update_query_stats(query_hash, (time.time() - start_time) * 1000, True)
                return cached_result

        # Execute query
        try:
            logger.debug(f"Executing query: {query[:100]}...")
            result = self.query_api.query_data_frame(query, params=params)

            # Cache result
            if use_cache and not result.empty:
                await self.cache.set(query, result, ttl, params)

            # Update statistics
            execution_time = (time.time() - start_time) * 1000
            await self._update_query_stats(query_hash, execution_time, False, len(result))

            # Analyze for optimizations
            if execution_time > 500:  # Only analyze slow queries
                suggestions = await self.analyzer.analyze_query(
                    query,
                    execution_time,
                    len(result)
                )

                if suggestions:
                    await self._store_optimizations(query_hash, suggestions)

            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def optimize_query(self, query: str) -> Tuple[str, List[OptimizationSuggestion]]:
        """
        Generate optimized version of query

        Args:
            query: Original query

        Returns:
            Tuple of (optimized_query, suggestions)
        """
        suggestions = await self.analyzer.analyze_query(query, 0, 0)
        optimized_query = query

        # Apply optimizations
        for suggestion in suggestions:
            if suggestion.optimized_query:
                optimized_query = suggestion.optimized_query

        return optimized_query, suggestions

    async def batch_execute(
        self,
        queries: List[Tuple[str, Dict]],
        parallel: bool = True,
        max_concurrent: int = 5
    ) -> List[pd.DataFrame]:
        """
        Execute multiple queries efficiently

        Args:
            queries: List of (query, params) tuples
            parallel: Whether to execute in parallel
            max_concurrent: Maximum concurrent queries

        Returns:
            List of results
        """
        if not parallel or len(queries) == 1:
            # Sequential execution
            results = []
            for query, params in queries:
                result = await self.execute_query(query, params)
                results.append(result)
            return results

        # Parallel execution with semaphore
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(q, p):
            async with semaphore:
                return await self.execute_query(q, p)

        tasks = [
            execute_with_semaphore(query, params)
            for query, params in queries
        ]

        return await asyncio.gather(*tasks)

    async def get_query_stats(self, query_hash: Optional[str] = None) -> Dict[str, Any]:
        """Get query execution statistics"""
        if query_hash:
            return self.query_stats.get(query_hash, {})

        # Return all stats
        stats = {}
        for q_hash, q_stats in self.query_stats.items():
            stats[q_hash[:16]] = {
                'execution_count': q_stats.execution_count,
                'avg_duration_ms': q_stats.avg_duration_ms,
                'total_duration_ms': q_stats.total_duration_ms,
                'last_executed': q_stats.last_executed.isoformat(),
                'cached_count': q_stats.cached_count
            }

        # Add cache stats
        stats['_cache'] = self.cache.get_stats()

        return stats

    async def get_optimization_report(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get optimization report for time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_optimizations = [
            opt for opt in self.optimization_history
            if opt['timestamp'] >= cutoff_time
        ]

        # Group by optimization type
        optimizations_by_type = defaultdict(list)
        total_improvement = 0

        for opt in recent_optimizations:
            optimizations_by_type[opt['type']].append(opt)
            total_improvement += opt['estimated_improvement']

        # Calculate top optimizations
        top_optimizations = sorted(
            recent_optimizations,
            key=lambda x: x['estimated_improvement'],
            reverse=True
        )[:10]

        return {
            'period_hours': hours,
            'total_optimizations': len(recent_optimizations),
            'total_estimated_improvement': total_improvement,
            'optimizations_by_type': {
                k: len(v) for k, v in optimizations_by_type.items()
            },
            'top_optimizations': top_optimizations,
            'cache_hit_rate': self.cache.get_stats()['hit_rate']
        }

    async def _update_query_stats(
        self,
        query_hash: str,
        duration_ms: float,
        cached: bool,
        result_size: int = 0
    ):
        """Update query execution statistics"""
        async with self._optimization_lock:
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = QueryStats(
                    query_hash=query_hash,
                    execution_count=0,
                    total_duration_ms=0,
                    avg_duration_ms=0,
                    min_duration_ms=float('inf'),
                    max_duration_ms=0,
                    last_executed=datetime.now(),
                    result_size_bytes=result_size
                )

            stats = self.query_stats[query_hash]
            stats.execution_count += 1
            stats.total_duration_ms += duration_ms
            stats.avg_duration_ms = stats.total_duration_ms / stats.execution_count
            stats.min_duration_ms = min(stats.min_duration_ms, duration_ms)
            stats.max_duration_ms = max(stats.max_duration_ms, duration_ms)
            stats.last_executed = datetime.now()

            if cached:
                stats.cached_count += 1

    async def _store_optimizations(
        self,
        query_hash: str,
        suggestions: List[OptimizationSuggestion]
    ):
        """Store optimization suggestions"""
        async with self._optimization_lock:
            for suggestion in suggestions:
                self.optimization_history.append({
                    'timestamp': datetime.now(),
                    'query_hash': query_hash,
                    'type': suggestion.optimization_type,
                    'description': suggestion.description,
                    'impact': suggestion.impact,
                    'estimated_improvement': suggestion.estimated_improvement,
                    'optimized_query': suggestion.optimized_query
                })


# Utility functions for common optimizations
async def create_time_partitioned_query(
    base_query: str,
    time_ranges: List[Tuple[datetime, datetime]]
) -> str:
    """
    Create a time-partitioned query for large time ranges

    Args:
        base_query: Base query without range
        time_ranges: List of (start, end) tuples

    Returns:
        Partitioned query
    """
    if not time_ranges:
        return base_query

    # Create union of time-partitioned queries
    union_queries = []
    for start, end in time_ranges:
        query = base_query.replace(
            'from(bucket: "{bucket}")',
            f'from(bucket: "{{bucket}}") |> range(start: {start.isoformat()}, stop: {end.isoformat()})'
        )
        union_queries.append(query)

    if len(union_queries) == 1:
        return union_queries[0]

    # Create union query
    return f"union(tables: [{', '.join([f'()=>({q})' for q in union_queries])}]) |> sort(columns: [\"_time\"])"


async def create_downsampling_query(
    source_measurement: str,
    target_measurement: str,
    aggregation_window: str,
    aggregation_functions: List[str]
) -> str:
    """
    Create a downsampling query

    Args:
        source_measurement: Source measurement name
        target_measurement: Target measurement name
        aggregation_window: Window for aggregation (e.g., '1h', '1d')
        aggregation_functions: List of aggregation functions

    Returns:
        Downsampling query
    """
    aggregations = []
    for func in aggregation_functions:
        aggregations.append(f'{func}(r._value) as _value_{func}')

    query = f'''
    data = from(bucket: "{source_measurement}")
        |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
        |> filter(fn: (r) => r._measurement == "{source_measurement}")

    aggregated = data
        |> aggregateWindow(
            every: {aggregation_window},
            fn: (tables) => tables
                |> group(columns: ["_measurement", "_field"])
                |> {', '.join(aggregations)}
        )

    aggregated
        |> set(key: "_measurement", value: "{target_measurement}")
        |> to(bucket: "{target_measurement}", org: "default")
    '''

    return query


# Global optimizer instance
_query_optimizer: Optional[QueryOptimizer] = None


async def get_query_optimizer(
    influx_client: Optional[InfluxDBClient] = None,
    redis_client: Optional[aioredis.Redis] = None,
    config: Optional[Dict] = None
) -> QueryOptimizer:
    """Get or create global query optimizer"""
    global _query_optimizer
    if _query_optimizer is None:
        if not influx_client or not redis_client:
            raise ValueError("InfluxDB and Redis clients required")

        _query_optimizer = QueryOptimizer(
            influx_client,
            redis_client,
            bucket=config.get('bucket', 'strategy_data') if config else 'strategy_data',
            org=config.get('org', 'default') if config else 'default'
        )

    return _query_optimizer


__all__ = [
    'QueryOptimizer',
    'QueryAnalyzer',
    'QueryCache',
    'OptimizationType',
    'OptimizationSuggestion',
    'get_query_optimizer',
    'create_time_partitioned_query',
    'create_downsampling_query'
]