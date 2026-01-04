#!/usr/bin/env python3
"""
InfluxDB Schema Setup Script
InfluxDB 架構設置腳本
Phase 1.2 - 時序數據庫配置

This script sets up the InfluxDB database schema for the CBSC quant strategy
management system, including buckets, retention policies, and downsampling tasks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from influxdb_client import InfluxDBClient, BucketRetentionRules, Task, Permission
from influxdb_client.client.exceptions import InfluxDBError
import yaml
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InfluxDBSchemaSetup:
    """
    Sets up InfluxDB schema with buckets, retention policies, and downsampling tasks.
    設置 InfluxDB 架構，包括存儲桶、保留策略和下採樣任務。
    """

    def __init__(self, url: str, token: str, org: str):
        self.url = url
        self.token = token
        self.org = org
        self.client: Optional[InfluxDBClient] = None
        self.buckets_api = None
        self.tasks_api = None
        self.authorizations_api = None

    async def connect(self):
        """Connect to InfluxDB"""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                timeout=60000  # 60 seconds timeout for operations
            )

            # Initialize APIs
            self.buckets_api = self.client.buckets_api()
            self.tasks_api = self.client.tasks_api()
            self.authorizations_api = self.client.authorizations_api()

            # Test connection
            health = self.client.health()
            if health.status == "pass":
                logger.info("✅ Successfully connected to InfluxDB")
                return True
            else:
                logger.error(f"❌ InfluxDB health check failed: {health.message}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to InfluxDB: {e}")
            return False

    async def create_buckets(self) -> bool:
        """
        Create all required buckets with proper retention policies.
        創建所有需要的存儲桶並配置適當的保留策略。
        """
        logger.info("Setting up buckets...")

        # Define buckets with their configurations
        buckets_config = [
            {
                "name": "market_data_raw",
                "description": "Raw market data with minute-level granularity",
                "retention": "90d",
                "shard_group_duration": "1d"
            },
            {
                "name": "market_data_hourly",
                "description": "Hourly aggregated market data",
                "retention": "2y",
                "shard_group_duration": "7d"
            },
            {
                "name": "market_data_daily",
                "description": "Daily aggregated market data",
                "retention": "10y",
                "shard_group_duration": "30d"
            },
            {
                "name": "strategy_performance",
                "description": "Strategy performance metrics and analytics",
                "retention": "5y",
                "shard_group_duration": "7d"
            },
            {
                "name": "risk_metrics",
                "description": "Risk calculation results and VaR/ES metrics",
                "retention": "5y",
                "shard_group_duration": "7d"
            },
            {
                "name": "trading_signals",
                "description": "Trading signals, orders, and execution data",
                "retention": "2y",
                "shard_group_duration": "1d"
            },
            {
                "name": "system_metrics",
                "description": "System performance and monitoring metrics",
                "retention": "30d",
                "shard_group_duration": "1h"
            }
        ]

        success = True

        for bucket_config in buckets_config:
            try:
                # Check if bucket already exists
                existing_buckets = self.buckets_api.find_buckets()
                bucket_exists = any(
                    b.name == bucket_config["name"]
                    for b in existing_buckets
                )

                if bucket_exists:
                    logger.info(f"⏭️  Bucket '{bucket_config['name']}' already exists")
                    continue

                # Create retention rule
                retention_rule = self._create_retention_rule(
                    bucket_config["retention"]
                )

                # Create bucket
                bucket = self.buckets_api.create_bucket(
                    bucket_name=bucket_config["name"],
                    org=self.org,
                    retention_rules=[retention_rule],
                    description=bucket_config["description"]
                )

                logger.info(f"✅ Created bucket: {bucket.name}")

            except Exception as e:
                logger.error(f"❌ Failed to create bucket {bucket_config['name']}: {e}")
                success = False

        return success

    def _create_retention_rule(self, duration: str) -> BucketRetentionRules:
        """
        Create a retention rule from duration string.
        從持續時間字符串創建保留規則。
        """
        # Map duration strings to seconds
        duration_map = {
            "30d": 2592000,      # 30 days
            "90d": 7776000,      # 90 days
            "180d": 15552000,    # 180 days
            "1y": 31536000,      # 1 year
            "2y": 63072000,      # 2 years
            "5y": 157680000,     # 5 years
            "10y": 315360000,    # 10 years
            "inf": 0,            # Infinite
        }

        seconds = duration_map.get(duration, 7776000)  # Default to 90 days

        return BucketRetentionRules(
            type="expire",
            every_seconds=seconds
        )

    async def create_downsampling_tasks(self) -> bool:
        """
        Create downsampling tasks for data aggregation.
        創建數據聚合的下採樣任務。
        """
        logger.info("Setting up downsampling tasks...")

        tasks_config = [
            {
                "name": "Hourly Market Data Aggregation",
                "description": "Aggregate raw market data to hourly",
                "every": "1h",
                "source_bucket": "market_data_raw",
                "target_bucket": "market_data_hourly",
                "offset": "5m",
                "flux": """
from(bucket: "market_data_raw")
  |> range(start: task.every)
  |> filter(fn: (r) => r._measurement == "stock_price")
  |> aggregateWindow(
      every: 1h,
      fn: (tables=<-, column="_value") =>
        tables
          |> group(columns: ["symbol", "exchange", "_measurement", "_field"])
          |> first(column: "_value")
          |> set(key: "_field", value: "open")
          |> yield(name: "first")
      ,
      createEmpty: false
    )
  |> duplicate(column: "_stop", as: "_time")
  |> set(key: "_field", value: "close")
  |> last(column: "_value")
  |> group(columns: ["symbol", "exchange", "_measurement", "_field"])
  |> to(bucket: "market_data_hourly", org: "cbsc")
                """
            },
            {
                "name": "Daily Market Data Aggregation",
                "description": "Aggregate hourly market data to daily",
                "every": "1d",
                "source_bucket": "market_data_hourly",
                "target_bucket": "market_data_daily",
                "offset": "1h",
                "flux": """
from(bucket: "market_data_hourly")
  |> range(start: task.every)
  |> filter(fn: (r) => r._measurement == "stock_price")
  |> aggregateWindow(
      every: 1d,
      fn: (tables=<-, column="_value") =>
        tables
          |> group(columns: ["symbol", "exchange", "_measurement", "_field"])
          |> first(column: "_value")
          |> set(key: "_field", value: "open")
          |> yield(name: "first")
      ,
      createEmpty: false
    )
  |> aggregateWindow(every: 1d, fn: max, column: "_value")
  |> set(key: "_field", value: "high")
  |> to(bucket: "market_data_daily", org: "cbsc")
                """
            },
            {
                "name": "Strategy Performance Daily Summary",
                "description": "Daily summary of strategy performance",
                "every": "1d",
                "source_bucket": "strategy_performance",
                "target_bucket": "strategy_performance",
                "offset": "2h",
                "flux": """
from(bucket: "strategy_performance")
  |> range(start: task.every)
  |> filter(fn: (r) => r._measurement == "strategy_returns")
  |> filter(fn: (r) => r.frequency == "daily")
  |> group(columns: ["strategy_id"])
  |> aggregateWindow(
      every: 1d,
      fn: (tables=<-, column="_value") =>
        tables
          |> mean(column: "_value")
          |> set(key: "_field", value: "daily_return_avg")
          |> yield(name: "mean")
      ,
      createEmpty: false
    )
  |> to(bucket: "strategy_performance", org: "cbsc", tagColumns: ["strategy_id"])
                """
            }
        ]

        success = True

        for task_config in tasks_config:
            try:
                # Check if task already exists
                existing_tasks = self.tasks_api.find_tasks()
                task_exists = any(
                    t.name == task_config["name"]
                    for t in existing_tasks
                )

                if task_exists:
                    logger.info(f"⏭️  Task '{task_config['name']}' already exists")
                    continue

                # Create task
                task = Task(
                    name=task_config["name"],
                    description=task_config["description"],
                    every=task_config["every"],
                    offset=task_config.get("offset"),
                    flux=task_config["flux"],
                    org_id=self.client.org().id
                )

                created_task = self.tasks_api.create_task(task)
                logger.info(f"✅ Created task: {created_task.name}")

            except Exception as e:
                logger.error(f"❌ Failed to create task {task_config['name']}: {e}")
                success = False

        return success

    async def setup_monitoring(self) -> bool:
        """
        Set up monitoring queries and alerts.
        設置監控查詢和警報。
        """
        logger.info("Setting up monitoring...")

        try:
            # Create a monitoring bucket for alerts
            existing_buckets = self.buckets_api.find_buckets()
            monitoring_bucket_exists = any(
                b.name == "monitoring" for b in existing_buckets
            )

            if not monitoring_bucket_exists:
                retention_rule = self._create_retention_rule("30d")
                bucket = self.buckets_api.create_bucket(
                    bucket_name="monitoring",
                    org=self.org,
                    retention_rules=[retention_rule],
                    description="System monitoring and alerts"
                )
                logger.info(f"✅ Created monitoring bucket: {bucket.name}")

            # Create sample monitoring check task
            monitoring_task = Task(
                name="System Health Check",
                description="Check system health and performance metrics",
                every="5m",
                flux="""
from(bucket: "system_metrics")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "api_performance")
  |> group()
  |> mean(column: "response_time")
  |> map(fn: (r) => ({
      r with
      _measurement: "system_health",
      _field: "avg_response_time",
      _value: r._value,
      healthy: r._value < 1000.0
    }))
  |> to(bucket: "monitoring", org: "cbsc")
                """,
                org_id=self.client.org().id
            )

            # Check if monitoring task exists
            existing_tasks = self.tasks_api.find_tasks()
            monitoring_task_exists = any(
                t.name == "System Health Check" for t in existing_tasks
            )

            if not monitoring_task_exists:
                created_task = self.tasks_api.create_task(monitoring_task)
                logger.info(f"✅ Created monitoring task: {created_task.name}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup monitoring: {e}")
            return False

    async def create_readonly_user(self) -> bool:
        """
        Create a readonly user for dashboard queries.
        為儀表板查詢創建只讀用戶。
        """
        logger.info("Setting up readonly user...")

        try:
            # Note: InfluxDB 2.x uses tokens instead of users
            # This would create an authorization token with read permissions

            # Create read-only permission for all buckets
            read_permission = Permission(
                type="read",
                resource={
                    "type": "buckets",
                    "orgID": self.client.org().id
                }
            )

            # This is a placeholder - actual token creation would depend on
            # your organization's security policies
            logger.info("⚠️  Read-only user setup skipped - requires org admin privileges")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create readonly user: {e}")
            return False

    async def verify_setup(self) -> bool:
        """
        Verify that all components are set up correctly.
        驗證所有組件都已正確設置。
        """
        logger.info("Verifying setup...")

        try:
            # Check buckets
            buckets = self.buckets_api.find_buckets()
            bucket_names = [b.name for b in buckets]

            required_buckets = [
                "market_data_raw",
                "market_data_hourly",
                "market_data_daily",
                "strategy_performance",
                "risk_metrics",
                "trading_signals",
                "system_metrics"
            ]

            missing_buckets = set(required_buckets) - set(bucket_names)
            if missing_buckets:
                logger.error(f"❌ Missing buckets: {missing_buckets}")
                return False

            # Check tasks
            tasks = self.tasks_api.find_tasks()
            task_names = [t.name for t in tasks]

            required_tasks = [
                "Hourly Market Data Aggregation",
                "Daily Market Data Aggregation",
                "Strategy Performance Daily Summary"
            ]

            missing_tasks = set(required_tasks) - set(task_names)
            if missing_tasks:
                logger.error(f"❌ Missing tasks: {missing_tasks}")
                return False

            logger.info("✅ All components verified successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False

    async def run_setup(self) -> bool:
        """
        Run the complete setup process.
        運行完整的設置過程。
        """
        logger.info("Starting InfluxDB schema setup...")

        # Connect to InfluxDB
        if not await self.connect():
            return False

        # Setup components
        success = True
        success &= await self.create_buckets()
        success &= await self.create_downsampling_tasks()
        success &= await self.setup_monitoring()
        success &= await self.create_readonly_user()

        # Verify setup
        if success:
            success = await self.verify_setup()

        if success:
            logger.info("✅ InfluxDB schema setup completed successfully!")
        else:
            logger.error("❌ InfluxDB schema setup failed!")

        return success

    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()
            logger.info("InfluxDB connection closed")


async def main():
    """Main setup function"""
    # Load environment variables
    load_dotenv()

    # Get configuration from environment or use defaults
    influxdb_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    influxdb_token = os.getenv("INFLUXDB_TOKEN", "")
    influxdb_org = os.getenv("INFLUXDB_ORG", "cbsc")

    if not influxdb_token:
        logger.error("❌ INFLUXDB_TOKEN environment variable is required")
        return False

    # Create and run setup
    setup = InfluxDBSchemaSetup(
        url=influxdb_url,
        token=influxdb_token,
        org=influxdb_org
    )

    try:
        success = await setup.run_setup()
        return success
    finally:
        setup.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)