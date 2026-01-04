"""
Data Synchronization Manager
==========================

Manages synchronization between Redis and InfluxDB with intelligent
data routing, transformation, and consistency guarantees.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import pickle
import time
from collections import defaultdict, deque

import aioredis
import aiofiles
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS, SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SyncDirection(str, Enum):
    """Data synchronization direction"""
    REDIS_TO_INFLUX = "redis_to_influx"
    INFLUX_TO_REDIS = "influx_to_redis"
    BIDIRECTIONAL = "bidirectional"


class SyncMode(str, Enum):
    """Synchronization mode"""
    REALTIME = "realtime"      # Immediate sync
    BATCH = "batch"           # Batch processing
    SCHEDULED = "scheduled"    # Scheduled intervals
    ON_DEMAND = "on_demand"   # Manual trigger


class ConflictResolution(str, Enum):
    """Conflict resolution strategy"""
    REDIS_WINS = "redis_wins"
    INFLUX_WINS = "influx_wins"
    TIMESTAMP_WINS = "timestamp_wins"
    MERGE = "merge"
    CUSTOM = "custom"


@dataclass
class SyncRule:
    """Data synchronization rule"""
    name: str
    source_pattern: str      # Redis key pattern or InfluxDB measurement
    target_pattern: str      # Target pattern
    direction: SyncDirection
    mode: SyncMode
    interval_seconds: int = 60
    batch_size: int = 1000
    ttl_seconds: Optional[int] = None
    conflict_resolution: ConflictResolution = ConflictResolution.TIMESTAMP_WINS
    transform_function: Optional[Callable] = None
    filter_function: Optional[Callable] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncTask:
    """Synchronization task"""
    id: str
    rule: SyncRule
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items_processed: int = 0
    items_total: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncMetrics:
    """Synchronization metrics"""
    total_synced: int = 0
    total_errors: int = 0
    avg_sync_time_ms: float = 0.0
    last_sync: Optional[datetime] = None
    sync_history: deque = field(default_factory=lambda: deque(maxlen=1000))


class DataTransformer:
    """
    Transforms data between Redis and InfluxDB formats
    """

    @staticmethod
    def redis_to_influx(
        redis_data: Dict[str, Any],
        measurement: str,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Point]:
        """
        Transform Redis data to InfluxDB points

        Args:
            redis_data: Data from Redis
            measurement: InfluxDB measurement name
            tags: Additional tags

        Returns:
            List of InfluxDB points
        """
        points = []

        # Handle different data types
        if 'timestamp' in redis_data:
            timestamp = pd.to_datetime(redis_data['timestamp'])
        else:
            timestamp = datetime.now()

        # Create base point
        point = Point(measurement).time(timestamp)

        # Add tags
        if tags:
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, str(tag_value))

        # Extract fields (exclude metadata)
        field_keys = {
            'value', 'price', 'volume', 'open', 'high', 'low', 'close',
            'bid', 'ask', 'bid_size', 'ask_size', 'spread'
        }

        for key, value in redis_data.items():
            if key in field_keys or not key.startswith('_'):
                # Skip timestamp and other metadata
                if key == 'timestamp':
                    continue

                # Convert value to appropriate type
                if isinstance(value, (int, float)):
                    point = point.field(key, value)
                elif isinstance(value, str):
                    # Try to parse as number
                    try:
                        if '.' in value:
                            point = point.field(key, float(value))
                        else:
                            point = point.field(key, int(value))
                    except ValueError:
                        # Keep as string field
                        point = point.field(key + "_str", value)
                elif isinstance(value, bool):
                    point = point.field(key, int(value))
                elif value is not None:
                    # Serialize complex objects
                    point = point.field(key + "_json", json.dumps(value, default=str))

        points.append(point)
        return points

    @staticmethod
    def influx_to_redis(
        influx_data: pd.DataFrame,
        key_pattern: str,
        ttl_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transform InfluxDB data to Redis format

        Args:
            influx_data: DataFrame from InfluxDB
            key_pattern: Redis key pattern
            ttl_seconds: TTL for Redis keys

        Returns:
            Dictionary of Redis key-value pairs
        """
        redis_data = {}

        if influx_data.empty:
            return redis_data

        # Process each row
        for _, row in influx_data.iterrows():
            # Build Redis key
            tags = row.get('_tags', {})
            key = key_pattern.format(**tags)

            # Build value dictionary
            value = {
                'timestamp': row.get('_time', datetime.now()).isoformat(),
                'measurement': row.get('_measurement', 'unknown')
            }

            # Add fields
            for col in influx_data.columns:
                if not col.startswith('_'):
                    value[col] = row[col]

            # Add tags
            if tags:
                value['tags'] = tags

            redis_data[key] = {
                'value': value,
                'ttl': ttl_seconds
            }

        return redis_data

    @staticmethod
    def merge_redis_influx(
        redis_data: Dict[str, Any],
        influx_data: Dict[str, Any],
        strategy: str = "latest"
    ) -> Dict[str, Any]:
        """
        Merge data from Redis and InfluxDB

        Args:
            redis_data: Data from Redis
            influx_data: Data from InfluxDB
            strategy: Merge strategy

        Returns:
            Merged data
        """
        if strategy == "latest":
            # Use latest timestamp
            redis_time = pd.to_datetime(redis_data.get('timestamp', '1970-01-01'))
            influx_time = pd.to_datetime(influx_data.get('timestamp', '1970-01-01'))

            if redis_time >= influx_time:
                return redis_data
            else:
                return influx_data

        elif strategy == "union":
            # Union of all fields
            merged = {}
            merged.update(redis_data)
            merged.update(influx_data)
            return merged

        elif strategy == "intersection":
            # Only common fields
            merged = {}
            for key in set(redis_data.keys()) & set(influx_data.keys()):
                merged[key] = influx_data[key]  # Prefer InfluxDB
            return merged

        return redis_data  # Default to Redis


class DataSyncManager:
    """
    Manages data synchronization between Redis and InfluxDB
    """

    def __init__(
        self,
        redis_client: aioredis.Redis,
        influx_client: InfluxDBClient,
        bucket: str = "sync_data",
        org: str = "default"
    ):
        self.redis_client = redis_client
        self.influx_client = influx_client
        self.bucket = bucket
        self.org = org

        # Sync rules and tasks
        self.sync_rules: Dict[str, SyncRule] = {}
        self.active_tasks: Dict[str, SyncTask] = {}
        self.completed_tasks: deque = deque(maxlen=1000)

        # Transformer
        self.transformer = DataTransformer()

        # Metrics
        self.metrics = SyncMetrics()

        # Background processing
        self._running = False
        self._background_tasks = set()
        self._sync_queue = asyncio.Queue()

        # Write API for batch operations
        self._write_api = None

    async def initialize(self):
        """Initialize sync manager"""
        # Initialize write API
        self._write_api = self.influx_client.write_api(write_options=ASYNCHRONOUS)

        # Start background tasks
        self._running = True
        self._background_tasks.add(
            asyncio.create_task(self._sync_processor_loop())
        )
        self._background_tasks.add(
            asyncio.create_task(self._scheduled_sync_loop())
        )

        logger.info("Data sync manager initialized")

    async def shutdown(self):
        """Shutdown sync manager"""
        self._running = False

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close write API
        if self._write_api:
            self._write_api.close()

        logger.info("Data sync manager shutdown")

    def add_sync_rule(self, rule: SyncRule):
        """Add a synchronization rule"""
        self.sync_rules[rule.name] = rule
        logger.info(f"Added sync rule: {rule.name}")

    def remove_sync_rule(self, rule_name: str):
        """Remove a synchronization rule"""
        if rule_name in self.sync_rules:
            del self.sync_rules[rule_name]
            logger.info(f"Removed sync rule: {rule_name}")

    async def trigger_sync(self, rule_name: str, force: bool = False) -> str:
        """
        Trigger manual synchronization

        Args:
            rule_name: Name of the sync rule
            force: Force sync even if not scheduled

        Returns:
            Task ID
        """
        if rule_name not in self.sync_rules:
            raise ValueError(f"Sync rule not found: {rule_name}")

        rule = self.sync_rules[rule_name]

        # Create sync task
        task_id = f"{rule_name}_{int(datetime.now().timestamp())}"
        task = SyncTask(
            id=task_id,
            rule=rule,
            status="pending",
            created_at=datetime.now()
        )

        self.active_tasks[task_id] = task

        # Queue for processing
        await self._sync_queue.put((rule_name, task_id, force))

        logger.info(f"Triggered sync: {task_id}")
        return task_id

    async def get_sync_status(self, task_id: str) -> Optional[SyncTask]:
        """Get synchronization task status"""
        return self.active_tasks.get(task_id)

    async def list_active_tasks(self) -> List[SyncTask]:
        """List all active sync tasks"""
        return list(self.active_tasks.values())

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a sync task"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = "cancelled"
            task.completed_at = datetime.now()

            # Move to completed
            self.completed_tasks.append(task)
            del self.active_tasks[task_id]

            logger.info(f"Cancelled sync task: {task_id}")
            return True
        return False

    async def get_sync_metrics(self) -> Dict[str, Any]:
        """Get synchronization metrics"""
        return {
            'total_synced': self.metrics.total_synced,
            'total_errors': self.metrics.total_errors,
            'avg_sync_time_ms': self.metrics.avg_sync_time_ms,
            'last_sync': self.metrics.last_sync.isoformat() if self.metrics.last_sync else None,
            'active_rules': len([r for r in self.sync_rules.values() if r.enabled]),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks)
        }

    async def _sync_processor_loop(self):
        """Process sync tasks from queue"""
        while self._running:
            try:
                # Get next task
                rule_name, task_id, force = await asyncio.wait_for(
                    self._sync_queue.get(),
                    timeout=1.0
                )

                # Process the sync
                await self._execute_sync(rule_name, task_id, force)

            except asyncio.TimeoutError:
                # No task in queue
                continue
            except Exception as e:
                logger.error(f"Error in sync processor: {e}")

    async def _scheduled_sync_loop(self):
        """Execute scheduled syncs"""
        while self._running:
            try:
                current_time = datetime.now()

                # Check each rule for scheduled syncs
                for rule_name, rule in self.sync_rules.items():
                    if (rule.enabled and
                        rule.mode == SyncMode.SCHEDULED and
                        not self._is_rule_running(rule_name)):

                        # Check if it's time to sync
                        if self._should_sync_now(rule, current_time):
                            await self.trigger_sync(rule_name)

                # Sleep for a while
                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in scheduled sync loop: {e}")
                await asyncio.sleep(60)

    async def _execute_sync(self, rule_name: str, task_id: str, force: bool = False):
        """Execute a sync task"""
        rule = self.sync_rules[rule_name]
        task = self.active_tasks[task_id]

        try:
            # Update task status
            task.status = "running"
            task.started_at = datetime.now()

            logger.info(f"Executing sync: {task_id}")

            # Execute based on direction
            if rule.direction in [SyncDirection.REDIS_TO_INFLUX, SyncDirection.BIDIRECTIONAL]:
                await self._sync_redis_to_influx(rule, task)

            if rule.direction in [SyncDirection.INFLUX_TO_REDIS, SyncDirection.BIDIRECTIONAL]:
                await self._sync_influx_to_redis(rule, task)

            # Update metrics
            self.metrics.total_synced += task.items_processed
            if task.started_at:
                sync_time = (datetime.now() - task.started_at).total_seconds() * 1000
                self.metrics.avg_sync_time_ms = (
                    self.metrics.avg_sync_time_ms * 0.9 + sync_time * 0.1
                )
            self.metrics.last_sync = datetime.now()

            # Update task
            task.status = "completed"
            task.completed_at = datetime.now()

            logger.info(f"Sync completed: {task_id} ({task.items_processed} items)")

        except Exception as e:
            # Handle error
            task.status = "failed"
            task.completed_at = datetime.now()
            task.errors.append(str(e))
            self.metrics.total_errors += 1

            logger.error(f"Sync failed: {task_id} - {e}")

        finally:
            # Move to completed
            self.completed_tasks.append(task)
            self.active_tasks.pop(task_id, None)

    async def _sync_redis_to_influx(self, rule: SyncRule, task: SyncTask):
        """Sync data from Redis to InfluxDB"""
        # Scan for matching keys
        cursor = 0
        batch_points = []
        items_processed = 0

        while True:
            cursor, keys = await self.redis_client.scan(
                cursor,
                match=rule.source_pattern,
                count=rule.batch_size
            )

            if not keys:
                break

            # Process batch
            for key in keys:
                try:
                    # Get data from Redis
                    data = await self.redis_client.get(key)
                    if not data:
                        continue

                    # Deserialize
                    if isinstance(data, bytes):
                        try:
                            data = pickle.loads(data)
                        except:
                            data = json.loads(data)

                    # Apply filter
                    if rule.filter_function and not rule.filter_function(data):
                        continue

                    # Transform data
                    if rule.transform_function:
                        data = rule.transform_function(data)

                    # Convert to InfluxDB points
                    measurement = rule.target_pattern
                    tags = self._extract_tags_from_key(key, rule)

                    points = self.transformer.redis_to_influx(
                        data,
                        measurement,
                        tags
                    )

                    batch_points.extend(points)
                    items_processed += 1

                    # Write batch if full
                    if len(batch_points) >= rule.batch_size:
                        await self._write_points(batch_points)
                        batch_points = []
                        task.items_processed = items_processed

                except Exception as e:
                    task.errors.append(f"Error processing key {key}: {e}")

            # Update progress
            task.items_processed = items_processed

            # Check if we should continue
            if cursor == 0:
                break

        # Write remaining points
        if batch_points:
            await self._write_points(batch_points)

    async def _sync_influx_to_redis(self, rule: SyncRule, task: SyncTask):
        """Sync data from InfluxDB to Redis"""
        # Build query
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{rule.interval_seconds}s)
            |> filter(fn: (r) => r["_measurement"] == "{rule.source_pattern}")
        '''

        # Add tag filters if any
        if 'tags' in rule.metadata:
            for tag_key, tag_value in rule.metadata['tags'].items():
                query += f'|> filter(fn: (r) => r["{tag_key}"] == "{tag_value}")\n'

        # Execute query
        query_api = self.influx_client.query_api()
        result_df = query_api.query_data_frame(query)

        if result_df.empty:
            return

        # Transform and store in Redis
        redis_data = self.transformer.influx_to_redis(
            result_df,
            rule.target_pattern,
            rule.ttl_seconds
        )

        items_processed = 0
        for key, data in redis_data.items():
            try:
                # Apply filter
                if rule.filter_function and not rule.filter_function(data['value']):
                    continue

                # Transform data
                if rule.transform_function:
                    data['value'] = rule.transform_function(data['value'])

                # Check for conflicts
                existing = await self.redis_client.get(key)
                if existing:
                    existing_data = pickle.loads(existing) if isinstance(existing, bytes) else existing

                    # Resolve conflict
                    if rule.conflict_resolution == ConflictResolution.REDIS_WINS:
                        continue  # Keep existing
                    elif rule.conflict_resolution == ConflictResolution.INFLUX_WINS:
                        pass  # Use new data
                    elif rule.conflict_resolution == ConflictResolution.TIMESTAMP_WINS:
                        # Compare timestamps
                        existing_time = pd.to_datetime(existing_data.get('timestamp', '1970-01-01'))
                        new_time = pd.to_datetime(data['value'].get('timestamp', '1970-01-01'))

                        if existing_time >= new_time:
                            continue
                    elif rule.conflict_resolution == ConflictResolution.MERGE:
                        # Merge data
                        data['value'] = self.transformer.merge_redis_influx(
                            existing_data,
                            data['value']
                        )

                # Store in Redis
                serialized = pickle.dumps(data['value'])
                if data['ttl']:
                    await self.redis_client.setex(key, data['ttl'], serialized)
                else:
                    await self.redis_client.set(key, serialized)

                items_processed += 1

            except Exception as e:
                task.errors.append(f"Error storing key {key}: {e}")

        task.items_processed = items_processed

    async def _write_points(self, points: List[Point]):
        """Write points to InfluxDB"""
        try:
            self._write_api.write(
                bucket=self.bucket,
                record=points
            )
        except InfluxDBError as e:
            logger.error(f"InfluxDB write error: {e}")
            raise

    def _extract_tags_from_key(self, key: str, rule: SyncRule) -> Dict[str, str]:
        """Extract tags from Redis key pattern"""
        tags = {}

        # Simple pattern matching
        # Could be enhanced with regex for complex patterns
        parts = key.split(':')

        if len(parts) >= 2:
            # Assume format: type:symbol:extra
            tags['type'] = parts[0]
            tags['symbol'] = parts[1]
            if len(parts) > 2:
                tags['extra'] = ':'.join(parts[2:])

        # Add metadata tags
        if 'tags' in rule.metadata:
            tags.update(rule.metadata['tags'])

        return tags

    def _is_rule_running(self, rule_name: str) -> bool:
        """Check if a rule is currently running"""
        for task in self.active_tasks.values():
            if task.rule.name == rule_name and task.status == "running":
                return True
        return False

    def _should_sync_now(self, rule: SyncRule, current_time: datetime) -> bool:
        """Check if rule should sync now"""
        # For demonstration, sync every interval_seconds
        # Could be enhanced with cron-like scheduling
        if not hasattr(rule, '_last_sync'):
            rule._last_sync = None

        if rule._last_sync is None:
            rule._last_sync = current_time
            return True

        elapsed = (current_time - rule._last_sync).total_seconds()
        if elapsed >= rule.interval_seconds:
            rule._last_sync = current_time
            return True

        return False


# Utility functions for common sync patterns
async def setup_market_data_sync(
    sync_manager: DataSyncManager,
    symbols: List[str],
    intervals: List[str] = ["1m", "5m", "1h"]
):
    """
    Setup market data synchronization rules

    Args:
        sync_manager: Data sync manager instance
        symbols: List of symbols to sync
        intervals: List of intervals
    """
    for symbol in symbols:
        for interval in intervals:
            # Redis to InfluxDB rule
            rule = SyncRule(
                name=f"market_data_{symbol}_{interval}",
                source_pattern=f"rt:market_data:{symbol}:{interval}",
                target_pattern=f"market_data_{interval}",
                direction=SyncDirection.REDIS_TO_INFLUX,
                mode=SyncMode.REALTIME,
                interval_seconds=60,
                ttl_seconds=3600,
                metadata={
                    'tags': {
                        'symbol': symbol,
                        'interval': interval
                    }
                }
            )
            sync_manager.add_sync_rule(rule)

    logger.info(f"Setup market data sync for {len(symbols)} symbols")


async def setup_strategy_result_sync(
    sync_manager: DataSyncManager,
    ttl_hours: int = 24
):
    """
    Setup strategy result synchronization

    Args:
        sync_manager: Data sync manager instance
        ttl_hours: TTL for cached results
    """
    rule = SyncRule(
        name="strategy_results",
        source_pattern="strategy_result:*",
        target_pattern="strategy_results",
        direction=SyncDirection.BIDIRECTIONAL,
        mode=SyncMode.BATCH,
        interval_seconds=300,  # 5 minutes
        batch_size=100,
        ttl_seconds=ttl_hours * 3600,
        conflict_resolution=ConflictResolution.TIMESTAMP_WINS
    )
    sync_manager.add_sync_rule(rule)

    logger.info("Setup strategy result sync")


# Global sync manager instance
_sync_manager: Optional[DataSyncManager] = None


async def get_sync_manager(
    redis_client: Optional[aioredis.Redis] = None,
    influx_client: Optional[InfluxDBClient] = None,
    config: Optional[Dict] = None
) -> DataSyncManager:
    """Get or create global sync manager"""
    global _sync_manager
    if _sync_manager is None:
        if not redis_client or not influx_client:
            raise ValueError("Redis and InfluxDB clients required")

        _sync_manager = DataSyncManager(
            redis_client,
            influx_client,
            bucket=config.get('bucket', 'sync_data') if config else 'sync_data',
            org=config.get('org', 'default') if config else 'default'
        )
        await _sync_manager.initialize()

        # Setup default rules if config provided
        if config and 'default_rules' in config:
            for rule_config in config['default_rules']:
                rule = SyncRule(**rule_config)
                _sync_manager.add_sync_rule(rule)

    return _sync_manager


async def setup_data_synchronization(
    redis_client: aioredis.Redis,
    influx_client: InfluxDBClient,
    config: Optional[Dict] = None
) -> DataSyncManager:
    """
    Setup data synchronization between Redis and InfluxDB

    Args:
        redis_client: Redis client
        influx_client: InfluxDB client
        config: Configuration dictionary

    Returns:
        Configured sync manager
    """
    sync_manager = DataSyncManager(
        redis_client,
        influx_client,
        bucket=config.get('bucket', 'sync_data') if config else 'sync_data',
        org=config.get('org', 'default') if config else 'default'
    )
    await sync_manager.initialize()

    # Setup default sync rules
    if config and 'market_data' in config:
        await setup_market_data_sync(
            sync_manager,
            config['market_data'].get('symbols', []),
            config['market_data'].get('intervals', ['1m', '5m', '1h'])
        )

    if config and 'strategy_results' in config:
        await setup_strategy_result_sync(
            sync_manager,
            config['strategy_results'].get('ttl_hours', 24)
        )

    logger.info("Data synchronization configured")
    return sync_manager


__all__ = [
    'DataSyncManager',
    'SyncRule',
    'SyncTask',
    'SyncDirection',
    'SyncMode',
    'ConflictResolution',
    'get_sync_manager',
    'setup_data_synchronization',
    'setup_market_data_sync',
    'setup_strategy_result_sync'
]