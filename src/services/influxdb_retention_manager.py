#!/usr/bin/env python3
"""
InfluxDB Retention Policy Manager
InfluxDB 保留策略管理器
Phase 1.2 - 時序數據庫配置

Manages data retention policies, downsampling tasks, and data archiving for InfluxDB.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from influxdb_client import InfluxDBClient, BucketRetentionRules, Task, TaskRepeat
from influxdb_client.client.exceptions import InfluxDBError

from ..config.influxdb_config import get_config, BucketType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DownsampleFrequency(Enum):
    """Downsampling frequency options"""
    MINUTELY = "1m"
    HOURLY = "1h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "30d"


class AggregationFunction(Enum):
    """Aggregation functions for downsampling"""
    FIRST = "first"
    LAST = "last"
    MEAN = "mean"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    MEDIAN = "median"


@dataclass
class DownsampleRule:
    """Rule for downsampling data"""
    source_bucket: str
    target_bucket: str
    measurement: str
    frequency: DownsampleFrequency
    aggregations: Dict[str, AggregationFunction]  # field -> function mapping
    offset: Optional[str] = None
    filters: Dict[str, str] = field(default_factory=dict)  # Additional filters


@dataclass
class RetentionPolicy:
    """Data retention policy"""
    bucket: str
    duration: str  # e.g., "30d", "90d", "1y", "inf"
    shard_group_duration: Optional[str] = None
    downsample_rules: List[DownsampleRule] = field(default_factory=list)
    default: bool = False
    description: Optional[str] = None


class InfluxDBRetentionManager:
    """
    Manages InfluxDB retention policies and downsampling.
    管理 InfluxDB 保留策略和下採樣。
    """

    def __init__(self, client: InfluxDBClient, org: str):
        self.client = client
        self.org = org
        self.buckets_api = client.buckets_api()
        self.tasks_api = client.tasks_api()
        self.config = get_config()

        # Initialize retention policies
        self.retention_policies = self._init_retention_policies()

        logger.info("InfluxDB retention manager initialized")

    def _init_retention_policies(self) -> List[RetentionPolicy]:
        """Initialize default retention policies"""
        policies = []

        # Raw market data - 90 days
        policies.append(RetentionPolicy(
            bucket="market_data_raw",
            duration="90d",
            shard_group_duration="1d",
            description="Raw market data with minute-level granularity",
            downsample_rules=[
                DownsampleRule(
                    source_bucket="market_data_raw",
                    target_bucket="market_data_hourly",
                    measurement="stock_price",
                    frequency=DownsampleFrequency.HOURLY,
                    aggregations={
                        "open": AggregationFunction.FIRST,
                        "high": AggregationFunction.MAX,
                        "low": AggregationFunction.MIN,
                        "close": AggregationFunction.LAST,
                        "volume": AggregationFunction.SUM,
                        "vwap": AggregationFunction.MEAN,
                        "num_trades": AggregationFunction.SUM
                    },
                    offset="5m"
                ),
                DownsampleRule(
                    source_bucket="market_data_raw",
                    target_bucket="market_data_hourly",
                    measurement="technical_indicators",
                    frequency=DownsampleFrequency.HOURLY,
                    aggregations={
                        "value": AggregationFunction.MEAN,
                        "signal": AggregationFunction.LAST,
                        "confidence": AggregationFunction.MEAN
                    },
                    offset="5m"
                )
            ]
        ))

        # Hourly market data - 2 years
        policies.append(RetentionPolicy(
            bucket="market_data_hourly",
            duration="2y",
            shard_group_duration="7d",
            description="Hourly aggregated market data",
            downsample_rules=[
                DownsampleRule(
                    source_bucket="market_data_hourly",
                    target_bucket="market_data_daily",
                    measurement="stock_price",
                    frequency=DownsampleFrequency.DAILY,
                    aggregations={
                        "open": AggregationFunction.FIRST,
                        "high": AggregationFunction.MAX,
                        "low": AggregationFunction.MIN,
                        "close": AggregationFunction.LAST,
                        "volume": AggregationFunction.SUM,
                        "vwap": AggregationFunction.MEAN,
                        "num_trades": AggregationFunction.SUM
                    },
                    offset="1h"
                )
            ]
        ))

        # Daily market data - 10 years (default)
        policies.append(RetentionPolicy(
            bucket="market_data_daily",
            duration="10y",
            shard_group_duration="30d",
            description="Daily aggregated market data",
            default=True
        ))

        # Strategy performance - 5 years
        policies.append(RetentionPolicy(
            bucket="strategy_performance",
            duration="5y",
            shard_group_duration="7d",
            description="Strategy performance metrics",
            downsample_rules=[
                DownsampleRule(
                    source_bucket="strategy_performance",
                    target_bucket="strategy_performance",
                    measurement="strategy_returns",
                    frequency=DownsampleFrequency.WEEKLY,
                    aggregations={
                        "total_return": AggregationFunction.LAST,
                        "daily_return": AggregationFunction.MEAN,
                        "volatility": AggregationFunction.MEAN,
                        "sharpe_ratio": AggregationFunction.MEAN
                    },
                    offset="2h"
                )
            ]
        ))

        # Risk metrics - 5 years
        policies.append(RetentionPolicy(
            bucket="risk_metrics",
            duration="5y",
            shard_group_duration="7d",
            description="Risk calculation results and VaR/ES metrics"
        ))

        # Trading signals - 2 years
        policies.append(RetentionPolicy(
            bucket="trading_signals",
            duration="2y",
            shard_group_duration="1d",
            description="Trading signals and execution data"
        ))

        # System metrics - 30 days
        policies.append(RetentionPolicy(
            bucket="system_metrics",
            duration="30d",
            shard_group_duration="1h",
            description="System performance and monitoring metrics",
            downsample_rules=[
                DownsampleRule(
                    source_bucket="system_metrics",
                    target_bucket="system_metrics",
                    measurement="api_performance",
                    frequency=DownsampleFrequency.HOURLY,
                    aggregations={
                        "response_time": AggregationFunction.MEAN,
                        "error_rate": AggregationFunction.MEAN,
                        "request_count": AggregationFunction.SUM
                    },
                    offset="10m"
                )
            ]
        ))

        return policies

    async def apply_retention_policies(self) -> bool:
        """
        Apply all retention policies to InfluxDB.
        將所有保留策略應用到 InfluxDB。
        """
        logger.info("Applying retention policies...")

        success = True

        for policy in self.retention_policies:
            try:
                # Get or create bucket with retention
                bucket = await self._ensure_bucket_with_retention(policy)
                if not bucket:
                    success = False
                    continue

                # Create downsampling tasks
                for rule in policy.downsample_rules:
                    task_success = await self._create_downsample_task(policy, rule)
                    if not task_success:
                        success = False

                logger.info(f"✅ Applied retention policy for bucket: {policy.bucket}")

            except Exception as e:
                logger.error(f"❌ Failed to apply retention policy for {policy.bucket}: {e}")
                success = False

        return success

    async def _ensure_bucket_with_retention(self, policy: RetentionPolicy) -> Optional[Any]:
        """Ensure bucket exists with correct retention policy"""
        try:
            # Check if bucket exists
            buckets = self.buckets_api.find_buckets()
            bucket = next((b for b in buckets if b.name == policy.bucket), None)

            if bucket:
                # Check retention rules
                if bucket.retention_rules:
                    current_rule = bucket.retention_rules[0]
                    expected_seconds = self._duration_to_seconds(policy.duration)

                    # Skip if retention is already correct
                    if current_rule.type == "expire" and current_rule.every_seconds == expected_seconds:
                        logger.debug(f"Bucket {policy.bucket} already has correct retention")
                        return bucket

                # Delete and recreate with correct retention
                logger.info(f"Recreating bucket {policy.bucket} with updated retention")
                self.buckets_api.delete_bucket(bucket)

            # Create bucket with retention
            retention_rule = BucketRetentionRules(
                type="expire",
                every_seconds=self._duration_to_seconds(policy.duration)
            )

            bucket = self.buckets_api.create_bucket(
                bucket_name=policy.bucket,
                org=self.org,
                retention_rules=[retention_rule],
                description=policy.description
            )

            logger.info(f"Created bucket {policy.bucket} with retention {policy.duration}")
            return bucket

        except Exception as e:
            logger.error(f"Failed to ensure bucket {policy.bucket}: {e}")
            return None

    def _duration_to_seconds(self, duration: str) -> int:
        """Convert duration string to seconds"""
        if duration == "inf":
            return 0

        unit = duration[-1]
        value = int(duration[:-1])

        multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800,
            'y': 31536000
        }

        return value * multipliers.get(unit, 86400)  # Default to days

    async def _create_downsample_task(self, policy: RetentionPolicy, rule: DownsampleRule) -> bool:
        """Create a downsampling task"""
        try:
            task_name = f"Downsample {rule.source_bucket} to {rule.target_bucket} - {rule.measurement}"

            # Check if task already exists
            existing_tasks = self.tasks_api.find_tasks()
            if any(t.name == task_name for t in existing_tasks):
                logger.info(f"Downsample task already exists: {task_name}")
                return True

            # Build Flux query for downsampling
            flux_query = self._build_downsample_flux(rule)

            # Create task
            task = Task(
                name=task_name,
                description=f"Downsample {rule.measurement} from {rule.source_bucket} to {rule.target_bucket}",
                every=rule.frequency.value,
                offset=rule.offset,
                flux=flux_query,
                org_id=self.client.org().id
            )

            created_task = self.tasks_api.create_task(task)
            logger.info(f"✅ Created downsampling task: {task_name}")

            return True

        except Exception as e:
            logger.error(f"Failed to create downsampling task: {e}")
            return False

    def _build_downsample_flux(self, rule: DownsampleRule) -> str:
        """Build Flux query for downsampling"""
        # Start with from and range
        flux_parts = [
            f'from(bucket: "{rule.source_bucket}")',
            f'|> range(start: task.every)'
        ]

        # Add measurement filter
        flux_parts.append(f'|> filter(fn: (r) => r._measurement == "{rule.measurement}")')

        # Add custom filters
        for key, value in rule.filters.items():
            flux_parts.append(f'|> filter(fn: (r) => r.{key} == "{value}")')

        # Group by tags (symbol, strategy_id, etc.)
        flux_parts.append('|> group(columns: ["_measurement"])')

        # For each aggregation function, create a separate aggregation
        aggregation_queries = []
        for field, agg_func in rule.aggregations.items():
            # Create aggregation for this field
            field_flux = flux_parts.copy()
            field_flux.append(f'|> filter(fn: (r) => r._field == "{field}")')
            field_flux.append(f'|> aggregateWindow(every: {rule.frequency.value}, fn: {agg_func.value}, createEmpty: false)')
            field_flux.append(f'|> set(key: "_field", value: "{field}")')
            field_flux.append(f'|> yield(name: "{field}_{agg_func.value}")')
            aggregation_queries.append("  \n".join(field_flux))

        # Join all aggregation queries
        return "\n\n".join(aggregation_queries)

    async def create_archive_task(self, bucket: str, archive_bucket: str = "archive") -> bool:
        """
        Create a task to archive old data before deletion.
        創建在刪除前歸檔舊數據的任務。
        """
        try:
            task_name = f"Archive {bucket} before deletion"

            # Check if task already exists
            existing_tasks = self.tasks_api.find_tasks()
            if any(t.name == task_name for t in existing_tasks):
                logger.info(f"Archive task already exists: {task_name}")
                return True

            # Build Flux query for archiving
            flux_query = f'''
from(bucket: "{bucket}")
  |> range(start: -30d, stop: now())
  |> filter(fn: (r) => r._measurement == "stock_price")
  |> to(bucket: "{archive_bucket}", org: "{self.org}")
            '''

            # Create task that runs daily
            task = Task(
                name=task_name,
                description=f"Archive old data from {bucket}",
                every="1d",
                offset="2h",
                flux=flux_query,
                org_id=self.client.org().id
            )

            created_task = self.tasks_api.create_task(task)
            logger.info(f"✅ Created archive task: {task_name}")

            return True

        except Exception as e:
            logger.error(f"Failed to create archive task: {e}")
            return False

    async def get_retention_status(self) -> Dict[str, Any]:
        """
        Get current status of retention policies and data sizes.
        獲取保留策略和數據大小的當前狀態。
        """
        status = {
            "buckets": {},
            "tasks": {
                "total": 0,
                "downsample": 0,
                "archive": 0,
                "failed": 0
            },
            "policies": []
        }

        try:
            # Get bucket information
            buckets = self.buckets_api.find_buckets()
            for bucket in buckets:
                retention_info = "No retention" if not bucket.retention_rules else f"{bucket.retention_rules[0].every_seconds}s"
                status["buckets"][bucket.name] = {
                    "retention": retention_info,
                    "created": bucket.created.isoformat() if bucket.created else None,
                    "description": bucket.description or ""
                }

            # Get task information
            tasks = self.tasks_api.find_tasks()
            status["tasks"]["total"] = len(tasks)

            for task in tasks:
                if "Downsample" in task.name:
                    status["tasks"]["downsample"] += 1
                elif "Archive" in task.name:
                    status["tasks"]["archive"] += 1

                if not task.status == "active":
                    status["tasks"]["failed"] += 1

            # Add policy information
            for policy in self.retention_policies:
                policy_info = {
                    "bucket": policy.bucket,
                    "duration": policy.duration,
                    "default": policy.default,
                    "downsample_rules": len(policy.downsample_rules)
                }
                status["policies"].append(policy_info)

        except Exception as e:
            logger.error(f"Failed to get retention status: {e}")

        return status

    async def cleanup_old_data(self, bucket: str, days_to_keep: int) -> int:
        """
        Manually delete data older than specified days.
        手動刪除早於指定天數的數據。
        """
        try:
            # Build delete query
            delete_api = self.client.delete_api()

            start = datetime(1970, 1, 1)
            stop = datetime.utcnow() - timedelta(days=days_to_keep)

            # Delete old data
            delete_api.delete(
                start=start,
                stop=stop,
                bucket=bucket,
                org=self.org,
                predicate='_measurement="stock_price"'  # Example predicate
            )

            logger.info(f"Deleted data older than {days_to_keep} days from bucket {bucket}")
            return 0

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 1

    async def export_retention_config(self, filename: str) -> bool:
        """
        Export current retention configuration to file.
        將當前保留配置導出到文件。
        """
        try:
            config = {
                "policies": [],
                "timestamp": datetime.utcnow().isoformat()
            }

            for policy in self.retention_policies:
                policy_data = {
                    "bucket": policy.bucket,
                    "duration": policy.duration,
                    "shard_group_duration": policy.shard_group_duration,
                    "default": policy.default,
                    "description": policy.description,
                    "downsample_rules": []
                }

                for rule in policy.downsample_rules:
                    rule_data = {
                        "source_bucket": rule.source_bucket,
                        "target_bucket": rule.target_bucket,
                        "measurement": rule.measurement,
                        "frequency": rule.frequency.value,
                        "offset": rule.offset,
                        "aggregations": {
                            field: func.value for field, func in rule.aggregations.items()
                        },
                        "filters": rule.filters
                    }
                    policy_data["downsample_rules"].append(rule_data)

                config["policies"].append(policy_data)

            # Write to file
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"Exported retention configuration to {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to export retention config: {e}")
            return False


# Example usage and testing
async def test_retention_manager():
    """Test the retention manager functionality"""
    import os
    from dotenv import load_dotenv

    # Load environment
    load_dotenv()

    # Create client and retention manager
    token = os.getenv("INFLUXDB_TOKEN")
    if not token:
        print("INFLUXDB_TOKEN not set")
        return

    client = InfluxDBClient(
        url="http://localhost:8086",
        token=token,
        org="cbsc"
    )

    manager = InfluxDBRetentionManager(client, "cbsc")

    try:
        # Apply retention policies
        success = await manager.apply_retention_policies()
        print(f"Retention policies applied: {success}")

        # Get status
        status = await manager.get_retention_status()
        print("\nRetention Status:")
        print(json.dumps(status, indent=2))

        # Export configuration
        await manager.export_retention_config("retention_config.json")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(test_retention_manager())