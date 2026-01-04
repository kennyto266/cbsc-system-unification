#!/usr/bin/env python3
"""
InfluxDB Setup Script
Setup InfluxDB buckets, retention policies, and initial configuration
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yaml

# InfluxDB client
try:
    from influxdb_client import InfluxDBClient, Bucket, RetentionRule
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:
    print("Error: influxdb-client not installed. Run: pip install influxdb-client")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InfluxDBSetup:
    """Setup InfluxDB for CBSC Strategy Management System"""

    def __init__(self, url: str, token: str, org: str):
        """Initialize InfluxDB client"""
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.buckets_api = self.client.buckets_api()
        self.organizations_api = self.client.organizations_api()
        self.org = org

    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def create_buckets(self, bucket_configs: Dict) -> None:
        """Create buckets with retention policies"""
        logger.info("Creating buckets...")

        for bucket_name, bucket_config in bucket_configs.items():
            try:
                # Check if bucket already exists
                existing_bucket = self.buckets_api.find_bucket_by_name(bucket_config['name'])

                if existing_bucket:
                    logger.info(f"Bucket '{bucket_config['name']}' already exists")
                    continue

                # Parse retention duration
                retention_duration = self._parse_duration(bucket_config['retention'])
                shard_group_duration = self._parse_duration(bucket_config['shard_group_duration'])

                # Create retention rules
                retention_rules = [
                    RetentionRule(
                        type="expire",
                        every_seconds=retention_duration
                    )
                ]

                # Create bucket
                bucket = Bucket(
                    name=bucket_config['name'],
                    description=bucket_config['description'],
                    org_id=self.organizations_api.find_organizations(org=self.org)[0].id,
                    retention_rules=retention_rules,
                    shard_group_duration_seconds=shard_group_duration
                )

                created_bucket = self.buckets_api.create_bucket(bucket)
                logger.info(f"✅ Created bucket: {bucket_config['name']}")

            except Exception as e:
                logger.error(f"❌ Failed to create bucket '{bucket_config['name']}': {e}")
                raise

    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string (e.g., '90d', '2y', '30m') to seconds"""
        unit_map = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800,
            'y': 31536000  # 365 days
        }

        duration_str = duration_str.lower()

        # Extract number and unit
        import re
        match = re.match(r'^(\d+)([smhdwy])$', duration_str)
        if not match:
            raise ValueError(f"Invalid duration format: {duration_str}")

        number, unit = match.groups()
        return int(number) * unit_map[unit]

    def setup_flux_scripts(self) -> None:
        """Setup Flux scripts for common queries and downsampling"""
        logger.info("Setting up Flux scripts...")

        # Create downsampling tasks
        downsampling_tasks = [
            {
                "name": "downsample-to-hourly",
                "flux": self._generate_downsample_flux("market_data_raw", "market_data_hourly", "1h"),
                "every": "1h"
            },
            {
                "name": "downsample-to-daily",
                "flux": self._generate_downsample_flux("market_data_hourly", "market_data_daily", "1d"),
                "every": "1d"
            }
        ]

        # Note: Task creation requires additional permissions
        logger.info("⚠️  Downsampling tasks need to be created manually with appropriate permissions")

    def _generate_downsample_flux(self, source_bucket: str, target_bucket: str, window: str) -> str:
        """Generate Flux script for downsampling"""
        return f'''
from(bucket: "{source_bucket}")
  |> range(start: -1{window})
  |> filter(fn: (r) => r._measurement == "stock_price")
  |> aggregateWindow(
    every: {window},
    fn: (tables) => tables
      |> group(columns: ["_measurement", "symbol", "exchange"])
      |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
  )
  |> set(key: "_measurement", value: "stock_price_aggregated")
  |> to(bucket: "{target_bucket}", org: "{self.org}")
'''.strip()

    def test_connection(self) -> bool:
        """Test InfluxDB connection"""
        try:
            # Try to ping the server
            health = self.client.health()
            if health.status == "pass":
                logger.info("✅ InfluxDB connection successful")
                return True
            else:
                logger.error(f"❌ InfluxDB health check failed: {health.message}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to InfluxDB: {e}")
            return False

    def verify_setup(self, config: Dict) -> None:
        """Verify that all buckets are created correctly"""
        logger.info("Verifying setup...")

        bucket_configs = config.get('buckets', {})

        for bucket_name, bucket_config in bucket_configs.items():
            try:
                bucket = self.buckets_api.find_bucket_by_name(bucket_config['name'])
                if bucket:
                    logger.info(f"✅ Bucket '{bucket_config['name']}' verified")
                else:
                    logger.error(f"❌ Bucket '{bucket_config['name']}' not found")
            except Exception as e:
                logger.error(f"❌ Error verifying bucket '{bucket_config['name']}': {e}")

    def cleanup(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()


def main():
    """Main setup function"""
    # Get configuration from environment or defaults
    config_path = os.getenv('INFLUXDB_CONFIG_PATH', 'config/influxdb-market-data-schema.yml')
    url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    token = os.getenv('INFLUXDB_TOKEN')
    org = os.getenv('INFLUXDB_ORG', 'cbsc')

    if not token:
        logger.error("❌ INFLUXDB_TOKEN environment variable is required")
        sys.exit(1)

    # Initialize setup
    setup = InfluxDBSetup(url=url, token=token, org=org)

    try:
        # Test connection
        if not setup.test_connection():
            sys.exit(1)

        # Load configuration
        config = setup.load_config(config_path)

        # Create buckets
        bucket_configs = config.get('buckets', {})
        setup.create_buckets(bucket_configs)

        # Setup Flux scripts
        setup.setup_flux_scripts()

        # Verify setup
        setup.verify_setup(config)

        logger.info("✅ InfluxDB setup completed successfully")

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)
    finally:
        setup.cleanup()


if __name__ == "__main__":
    main()