#!/usr/bin/env python3
"""
InfluxDB Configuration Module
InfluxDB 配置模組
Phase 1.2 - 時序數據庫配置

Centralized configuration for InfluxDB connections and operations.
"""

import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path


class BucketType(Enum):
    """Enumeration of InfluxDB bucket types"""
    MARKET_DATA_RAW = "market_data_raw"
    MARKET_DATA_HOURLY = "market_data_hourly"
    MARKET_DATA_DAILY = "market_data_daily"
    STRATEGY_PERFORMANCE = "strategy_performance"
    RISK_METRICS = "risk_metrics"
    TRADING_SIGNALS = "trading_signals"
    SYSTEM_METRICS = "system_metrics"
    MONITORING = "monitoring"


@dataclass
class BucketConfig:
    """Configuration for a specific InfluxDB bucket"""
    name: str
    description: str
    retention: str
    shard_group_duration: str
    bucket_type: BucketType
    measurement_types: List[str] = field(default_factory=list)
    indexed_tags: List[str] = field(default_factory=list)


@dataclass
class InfluxDBConnectionConfig:
    """InfluxDB connection configuration"""
    url: str = "http://localhost:8086"
    token: str = ""
    org: str = "cbsc"
    timeout: int = 30000  # milliseconds
    connection_pool_size: int = 10
    verify_ssl: bool = True
    debug: bool = False


@dataclass
class InfluxDBWriteConfig:
    """InfluxDB write operation configuration"""
    batch_size: int = 1000
    flush_interval: int = 1000  # milliseconds
    gzip_threshold: int = 1000
    jitter_interval: int = 0
    retry_interval: int = 5000
    max_retries: int = 3
    max_retry_delay: int = 30000
    exponential_base: int = 2


@dataclass
class InfluxDBQueryConfig:
    """InfluxDB query operation configuration"""
    default_time_range: str = "-1h"
    max_results: int = 10000
    query_timeout: int = 60000  # milliseconds
    enable_logging: bool = False
    max_concurrent_queries: int = 10


@dataclass
class RetentionPolicy:
    """Data retention policy configuration"""
    bucket: str
    duration: str
    shard_group_duration: str
    default: bool = False
    downsample_tasks: List[Dict] = field(default_factory=list)


@dataclass
class CacheConfig:
    """Cache configuration for InfluxDB queries"""
    enabled: bool = True
    redis_client: Optional[str] = None
    ttl_latest_price: int = 60  # seconds
    ttl_strategy_summary: int = 300  # seconds
    ttl_market_overview: int = 600  # seconds
    ttl_query_result: int = 180  # seconds


class InfluxDBConfig:
    """
    Main InfluxDB configuration class with all settings.
    包含所有設置的主要 InfluxDB 配置類。
    """

    def __init__(self, config_file: Optional[str] = None):
        # Initialize with defaults
        self.connection = InfluxDBConnectionConfig()
        self.write = InfluxDBWriteConfig()
        self.query = InfluxDBQueryConfig()
        self.cache = CacheConfig()

        # Load configuration from file if provided
        if config_file:
            self.load_from_file(config_file)

        # Override with environment variables
        self.load_from_env()

        # Initialize bucket configurations
        self._init_bucket_configs()

        # Initialize retention policies
        self._init_retention_policies()

    def load_from_file(self, config_file: str):
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)

            # Update connection config
            if 'connection' in config_data:
                conn_data = config_data['connection']
                self.connection = InfluxDBConnectionConfig(
                    url=conn_data.get('url', self.connection.url),
                    token=conn_data.get('token', self.connection.token),
                    org=conn_data.get('org', self.connection.org),
                    timeout=conn_data.get('timeout', self.connection.timeout),
                    connection_pool_size=conn_data.get('connection_pool_size', self.connection.connection_pool_size),
                    verify_ssl=conn_data.get('verify_ssl', self.connection.verify_ssl),
                    debug=conn_data.get('debug', self.connection.debug)
                )

            # Update write config
            if 'write' in config_data:
                write_data = config_data['write']
                self.write = InfluxDBWriteConfig(
                    batch_size=write_data.get('batch_size', self.write.batch_size),
                    flush_interval=write_data.get('flush_interval', self.write.flush_interval),
                    gzip_threshold=write_data.get('gzip_threshold', self.write.gzip_threshold),
                    jitter_interval=write_data.get('jitter_interval', self.write.jitter_interval),
                    retry_interval=write_data.get('retry_interval', self.write.retry_interval),
                    max_retries=write_data.get('max_retries', self.write.max_retries),
                    max_retry_delay=write_data.get('max_retry_delay', self.write.max_retry_delay),
                    exponential_base=write_data.get('exponential_base', self.write.exponential_base)
                )

            # Update query config
            if 'query' in config_data:
                query_data = config_data['query']
                self.query = InfluxDBQueryConfig(
                    default_time_range=query_data.get('default_time_range', self.query.default_time_range),
                    max_results=query_data.get('max_results', self.query.max_results),
                    query_timeout=query_data.get('query_timeout', self.query.query_timeout),
                    enable_logging=query_data.get('enable_logging', self.query.enable_logging),
                    max_concurrent_queries=query_data.get('max_concurrent_queries', self.query.max_concurrent_queries)
                )

            # Update cache config
            if 'cache' in config_data:
                cache_data = config_data['cache']
                self.cache = CacheConfig(
                    enabled=cache_data.get('enabled', self.cache.enabled),
                    redis_client=cache_data.get('redis_client', self.cache.redis_client),
                    ttl_latest_price=cache_data.get('ttl_latest_price', self.cache.ttl_latest_price),
                    ttl_strategy_summary=cache_data.get('ttl_strategy_summary', self.cache.ttl_strategy_summary),
                    ttl_market_overview=cache_data.get('ttl_market_overview', self.cache.ttl_market_overview),
                    ttl_query_result=cache_data.get('ttl_query_result', self.cache.ttl_query_result)
                )

        except Exception as e:
            print(f"Warning: Failed to load config from {config_file}: {e}")

    def load_from_env(self):
        """Load configuration from environment variables"""
        # Connection settings
        self.connection.url = os.getenv("INFLUXDB_URL", self.connection.url)
        self.connection.token = os.getenv("INFLUXDB_TOKEN", self.connection.token)
        self.connection.org = os.getenv("INFLUXDB_ORG", self.connection.org)

        # Write settings
        self.write.batch_size = int(os.getenv("INFLUXDB_BATCH_SIZE", str(self.write.batch_size)))
        self.write.flush_interval = int(os.getenv("INFLUXDB_FLUSH_INTERVAL", str(self.write.flush_interval)))

        # Cache settings
        self.cache.redis_client = os.getenv("REDIS_CLIENT", self.cache.redis_client)
        self.cache.enabled = os.getenv("INFLUXDB_CACHE_ENABLED", "true").lower() == "true"

    def _init_bucket_configs(self):
        """Initialize bucket configurations"""
        self.buckets: Dict[BucketType, BucketConfig] = {
            BucketType.MARKET_DATA_RAW: BucketConfig(
                name="market_data_raw",
                description="Raw market data with minute-level granularity",
                retention="90d",
                shard_group_duration="1d",
                bucket_type=BucketType.MARKET_DATA_RAW,
                measurement_types=["stock_price", "technical_indicators", "market_depth", "market_sentiment"],
                indexed_tags=["symbol", "exchange", "currency", "market"]
            ),
            BucketType.MARKET_DATA_HOURLY: BucketConfig(
                name="market_data_hourly",
                description="Hourly aggregated market data",
                retention="2y",
                shard_group_duration="7d",
                bucket_type=BucketType.MARKET_DATA_HOURLY,
                measurement_types=["stock_price"],
                indexed_tags=["symbol", "exchange"]
            ),
            BucketType.MARKET_DATA_DAILY: BucketConfig(
                name="market_data_daily",
                description="Daily aggregated market data",
                retention="10y",
                shard_group_duration="30d",
                bucket_type=BucketType.MARKET_DATA_DAILY,
                measurement_types=["stock_price"],
                indexed_tags=["symbol", "exchange"]
            ),
            BucketType.STRATEGY_PERFORMANCE: BucketConfig(
                name="strategy_performance",
                description="Strategy performance metrics and analytics",
                retention="5y",
                shard_group_duration="7d",
                bucket_type=BucketType.STRATEGY_PERFORMANCE,
                measurement_types=["strategy_returns", "strategy_ratios", "trade_analysis"],
                indexed_tags=["strategy_id", "strategy_name", "user_id", "portfolio_id", "benchmark"]
            ),
            BucketType.RISK_METRICS: BucketConfig(
                name="risk_metrics",
                description="Risk calculation results and VaR/ES metrics",
                retention="5y",
                shard_group_duration="7d",
                bucket_type=BucketType.RISK_METRICS,
                measurement_types=["strategy_risk"],
                indexed_tags=["strategy_id", "risk_type", "confidence_level", "time_horizon"]
            ),
            BucketType.TRADING_SIGNALS: BucketConfig(
                name="trading_signals",
                description="Trading signals, orders, and execution data",
                retention="2y",
                shard_group_duration="1d",
                bucket_type=BucketType.TRADING_SIGNALS,
                measurement_types=["trading_signals"],
                indexed_tags=["strategy_id", "symbol", "signal_type", "direction"]
            ),
            BucketType.SYSTEM_METRICS: BucketConfig(
                name="system_metrics",
                description="System performance and monitoring metrics",
                retention="30d",
                shard_group_duration="1h",
                bucket_type=BucketType.SYSTEM_METRICS,
                measurement_types=["api_performance", "database_performance"],
                indexed_tags=["endpoint", "service", "database_type", "operation_type"]
            ),
            BucketType.MONITORING: BucketConfig(
                name="monitoring",
                description="System monitoring and alerts",
                retention="30d",
                shard_group_duration="1h",
                bucket_type=BucketType.MONITORING,
                measurement_types=["system_health", "alerts"],
                indexed_tags=["alert_type", "severity", "source"]
            )
        }

    def _init_retention_policies(self):
        """Initialize retention policies"""
        self.retention_policies: List[RetentionPolicy] = [
            RetentionPolicy(
                bucket="market_data_raw",
                duration="90d",
                shard_group_duration="1d",
                downsample_tasks=[
                    {
                        "target_bucket": "market_data_hourly",
                        "interval": "1h",
                        "aggregations": [
                            {"field": "open", "function": "first"},
                            {"field": "high", "function": "max"},
                            {"field": "low", "function": "min"},
                            {"field": "close", "function": "last"},
                            {"field": "volume", "function": "sum"}
                        ]
                    }
                ]
            ),
            RetentionPolicy(
                bucket="market_data_hourly",
                duration="2y",
                shard_group_duration="7d",
                downsample_tasks=[
                    {
                        "target_bucket": "market_data_daily",
                        "interval": "1d",
                        "aggregations": [
                            {"field": "open", "function": "first"},
                            {"field": "high", "function": "max"},
                            {"field": "low", "function": "min"},
                            {"field": "close", "function": "last"},
                            {"field": "volume", "function": "sum"}
                        ]
                    }
                ]
            ),
            RetentionPolicy(
                bucket="market_data_daily",
                duration="10y",
                shard_group_duration="30d",
                default=True
            ),
            RetentionPolicy(
                bucket="strategy_performance",
                duration="5y",
                shard_group_duration="7d"
            ),
            RetentionPolicy(
                bucket="risk_metrics",
                duration="5y",
                shard_group_duration="7d"
            ),
            RetentionPolicy(
                bucket="trading_signals",
                duration="2y",
                shard_group_duration="1d"
            ),
            RetentionPolicy(
                bucket="system_metrics",
                duration="30d",
                shard_group_duration="1h"
            )
        ]

    def get_bucket_config(self, bucket_type: BucketType) -> Optional[BucketConfig]:
        """Get configuration for a specific bucket type"""
        return self.buckets.get(bucket_type)

    def get_bucket_config_by_name(self, bucket_name: str) -> Optional[BucketConfig]:
        """Get configuration for a bucket by name"""
        for bucket_config in self.buckets.values():
            if bucket_config.name == bucket_name:
                return bucket_config
        return None

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of issues.
        驗證配置並返回問題列表。
        """
        issues = []

        # Check required connection settings
        if not self.connection.url:
            issues.append("InfluxDB URL is required")
        if not self.connection.token:
            issues.append("InfluxDB token is required")
        if not self.connection.org:
            issues.append("InfluxDB organization is required")

        # Check numeric values
        if self.write.batch_size <= 0:
            issues.append("Batch size must be positive")
        if self.connection.connection_pool_size <= 0:
            issues.append("Connection pool size must be positive")
        if self.query.max_results <= 0:
            issues.append("Max results must be positive")

        # Check cache configuration
        if self.cache.enabled and not self.cache.redis_client:
            issues.append("Redis client is required when cache is enabled")

        return issues

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            "connection": {
                "url": self.connection.url,
                "org": self.connection.org,
                "timeout": self.connection.timeout,
                "connection_pool_size": self.connection.connection_pool_size,
                "verify_ssl": self.connection.verify_ssl,
                "debug": self.connection.debug
            },
            "write": {
                "batch_size": self.write.batch_size,
                "flush_interval": self.write.flush_interval,
                "gzip_threshold": self.write.gzip_threshold,
                "jitter_interval": self.write.jitter_interval,
                "retry_interval": self.write.retry_interval,
                "max_retries": self.write.max_retries,
                "max_retry_delay": self.write.max_retry_delay,
                "exponential_base": self.write.exponential_base
            },
            "query": {
                "default_time_range": self.query.default_time_range,
                "max_results": self.query.max_results,
                "query_timeout": self.query.query_timeout,
                "enable_logging": self.query.enable_logging,
                "max_concurrent_queries": self.query.max_concurrent_queries
            },
            "cache": {
                "enabled": self.cache.enabled,
                "redis_client": self.cache.redis_client,
                "ttl_latest_price": self.cache.ttl_latest_price,
                "ttl_strategy_summary": self.cache.ttl_strategy_summary,
                "ttl_market_overview": self.cache.ttl_market_overview,
                "ttl_query_result": self.cache.ttl_query_result
            },
            "buckets": {
                bucket_type.value: {
                    "name": config.name,
                    "description": config.description,
                    "retention": config.retention,
                    "shard_group_duration": config.shard_group_duration,
                    "measurement_types": config.measurement_types,
                    "indexed_tags": config.indexed_tags
                }
                for bucket_type, config in self.buckets.items()
            }
        }


# Global configuration instance
_config: Optional[InfluxDBConfig] = None


def get_config(config_file: Optional[str] = None) -> InfluxDBConfig:
    """
    Get global InfluxDB configuration instance.
    獲取全局 InfluxDB 配置實例。
    """
    global _config
    if _config is None:
        _config = InfluxDBConfig(config_file)

        # Validate configuration
        issues = _config.validate()
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")

    return _config


def reload_config(config_file: Optional[str] = None):
    """Reload configuration from file"""
    global _config
    _config = InfluxDBConfig(config_file)
    return _config