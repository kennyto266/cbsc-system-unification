#!/usr/bin/env python3
"""
InfluxDB Client Service
InfluxDB 客戶端服務
Phase 1.2 - 時序數據庫配置

Provides high-performance time-series database operations for market data,
strategy performance metrics, and system monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import json
import pandas as pd
import numpy as np
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS, PointSettings
from influxdb_client.client.exceptions import InfluxDBError
import redis
import aiohttp
from aiohttp import ClientTimeout
import backoff
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InfluxDBConfig:
    """InfluxDB configuration class"""
    url: str = "http://localhost:8086"
    token: str = ""
    org: str = "cbsc"
    default_bucket: str = "market_data"
    timeout: int = 30000  # milliseconds
    connection_pool_size: int = 10
    batch_size: int = 1000
    flush_interval: int = 1000  # milliseconds
    gzip_threshold: int = 1000
    retry_attempts: int = 3
    retry_delay: int = 1000  # milliseconds

class InfluxDBManager:
    """
    High-performance InfluxDB client with connection pooling,
    batch processing, and automatic retry logic.
    """

    def __init__(self, config: InfluxDBConfig, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.redis_client = redis_client
        self._client: Optional[InfluxDBClient] = None
        self._write_api = None
        self._query_api = None
        self._bucket_api = None
        self._task_api = None
        self._executor = ThreadPoolExecutor(max_workers=config.connection_pool_size)
        self._connection_pool = []

        # Performance metrics
        self._write_count = 0
        self._query_count = 0
        self._error_count = 0
        self._last_error: Optional[str] = None

        logger.info(f"Initializing InfluxDB manager for org: {config.org}")

    async def initialize(self):
        """Initialize InfluxDB connection and APIs"""
        try:
            # Create InfluxDB client with optimized settings
            self._client = InfluxDBClient(
                url=self.config.url,
                token=self.config.token,
                org=self.config.org,
                timeout=self.config.timeout,
                connection_pool_maxsize=self.config.connection_pool_size,
                gzip_threshold=self.config.gzip_threshold
            )

            # Initialize APIs
            self._write_api = self._client.write_api(
                write_options=ASYNCHRONOUS,
                point_settings=PointSettings()
            )
            self._query_api = self._client.query_api()
            self._bucket_api = self._client.buckets_api()
            self._task_api = self._client.tasks_api()

            # Test connection
            health = await self._test_connection()
            if health:
                logger.info("✅ InfluxDB connection established successfully")
                await self._initialize_buckets()
            else:
                raise Exception("Failed to establish InfluxDB connection")

        except Exception as e:
            logger.error(f"❌ Failed to initialize InfluxDB: {e}")
            raise

    async def _test_connection(self) -> bool:
        """Test InfluxDB connection"""
        try:
            health = self._client.health()
            return health.status == "pass"
        except Exception as e:
            logger.error(f"InfluxDB health check failed: {e}")
            return False

    async def _initialize_buckets(self):
        """Initialize required buckets if they don't exist"""
        required_buckets = [
            {"name": "market_data_raw", "retention": "90d"},
            {"name": "market_data_hourly", "retention": "2y"},
            {"name": "market_data_daily", "retention": "10y"},
            {"name": "strategy_performance", "retention": "5y"},
            {"name": "risk_metrics", "retention": "5y"},
            {"name": "trading_signals", "retention": "2y"},
            {"name": "system_metrics", "retention": "30d"},
        ]

        for bucket_info in required_buckets:
            await self._ensure_bucket_exists(bucket_info["name"], bucket_info["retention"])

    async def _ensure_bucket_exists(self, bucket_name: str, retention: str):
        """Ensure bucket exists, create if necessary"""
        try:
            buckets = self._bucket_api.find_buckets()
            bucket_exists = any(b.name == bucket_name for b in buckets)

            if not bucket_exists:
                logger.info(f"Creating bucket: {bucket_name}")
                self._bucket_api.create_bucket(
                    bucket_name=bucket_name,
                    org=self.config.org,
                    retention_rules=[self._create_retention_rule(retention)]
                )
                logger.info(f"✅ Bucket created: {bucket_name}")
            else:
                logger.debug(f"Bucket already exists: {bucket_name}")

        except Exception as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")

    def _create_retention_rule(self, duration: str) -> Dict:
        """Create retention rule from duration string"""
        duration_map = {
            "30d": {"type": "expire", "everySeconds": 2592000},
            "90d": {"type": "expire", "everySeconds": 7776000},
            "2y": {"type": "expire", "everySeconds": 63072000},
            "5y": {"type": "expire", "everySeconds": 15768000},
            "10y": {"type": "expire", "everySeconds": 315360000},
        }
        return duration_map.get(duration, duration_map["90d"])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def write_market_data(
        self,
        data: List[Dict],
        measurement: str = "stock_price",
        bucket: Optional[str] = None
    ) -> bool:
        """
        Write market data with high performance batch processing

        Args:
            data: List of market data dictionaries
            measurement: Measurement name
            bucket: Target bucket (defaults to config.default_bucket)

        Returns:
            bool: Success status
        """
        if not self._write_api:
            raise RuntimeError("InfluxDB not initialized")

        target_bucket = bucket or self.config.default_bucket

        try:
            # Process data in batches
            batch_size = min(self.config.batch_size, len(data))
            points = []

            for i, record in enumerate(data):
                # Create point
                point = Point(measurement) \
                    .time(record.get("timestamp", datetime.utcnow()), WritePrecision.MS)

                # Add tags (indexed fields)
                for tag_key, tag_value in record.get("tags", {}).items():
                    if tag_value is not None:
                        point = point.tag(tag_key, str(tag_value))

                # Add fields (data fields)
                for field_key, field_value in record.get("fields", {}).items():
                    if field_value is not None:
                        point = point.field(field_key, float(field_value) if isinstance(field_value, (int, float)) else str(field_value))

                points.append(point)

                # Write batch when full
                if len(points) >= batch_size or i == len(data) - 1:
                    self._write_api.write(bucket=target_bucket, org=self.config.org, record=points)
                    points.clear()
                    self._write_count += 1

            logger.debug(f"✅ Wrote {len(data)} points to {target_bucket}")

            # Cache latest price for quick access
            if self.redis_client and measurement == "stock_price":
                await self._cache_latest_prices(data)

            return True

        except InfluxDBError as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"❌ InfluxDB write error: {e}")
            return False
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"❌ Write error: {e}")
            return False

    async def _cache_latest_prices(self, data: List[Dict]):
        """Cache latest prices in Redis for fast access"""
        try:
            for record in data[-100:]:  # Cache last 100 records
                symbol = record.get("tags", {}).get("symbol")
                if symbol:
                    cache_key = f"price:{symbol}"
                    price_data = {
                        "price": record.get("fields", {}).get("close"),
                        "timestamp": record.get("timestamp", datetime.utcnow()).isoformat(),
                        "volume": record.get("fields", {}).get("volume", 0)
                    }
                    self.redis_client.setex(cache_key, 60, json.dumps(price_data))  # Cache for 60 seconds
        except Exception as e:
            logger.debug(f"Failed to cache prices: {e}")

    @backoff.on_exception(backoff.expo, InfluxDBError, max_tries=3)
    async def query_data(
        self,
        query: str,
        bucket: Optional[str] = None,
        measurement: Optional[str] = None,
        time_range: Optional[str] = None,
        tags: Optional[Dict] = None,
        fields: Optional[List[str]] = None,
        aggregation: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Query data with flexible parameters and automatic optimization

        Args:
            query: Custom Flux query (overrides other parameters)
            bucket: Bucket to query
            measurement: Measurement to filter
            time_range: Time range (e.g., "-1h", "-24h", "-7d")
            tags: Tag filters
            fields: Field filters
            aggregation: Aggregation settings

        Returns:
            pd.DataFrame: Query results
        """
        if not self._query_api:
            raise RuntimeError("InfluxDB not initialized")

        try:
            # Build query if not provided
            if not query:
                query = self._build_query(
                    bucket=bucket,
                    measurement=measurement,
                    time_range=time_range,
                    tags=tags,
                    fields=fields,
                    aggregation=aggregation
                )

            # Execute query
            logger.debug(f"Executing query: {query[:100]}...")
            result = self._query_api.query_data_frame(query, org=self.config.org)
            self._query_count += 1

            # Process result
            if isinstance(result, list) and result:
                df = pd.concat(result, ignore_index=True)
            elif isinstance(result, pd.DataFrame):
                df = result
            else:
                df = pd.DataFrame()

            # Convert time column
            if "_time" in df.columns:
                df["_time"] = pd.to_datetime(df["_time"])
                df = df.sort_values("_time")

            logger.debug(f"Query returned {len(df)} records")
            return df

        except InfluxDBError as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"❌ InfluxDB query error: {e}")
            return pd.DataFrame()
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"❌ Query error: {e}")
            return pd.DataFrame()

    def _build_query(
        self,
        bucket: Optional[str] = None,
        measurement: Optional[str] = None,
        time_range: Optional[str] = None,
        tags: Optional[Dict] = None,
        fields: Optional[List[str]] = None,
        aggregation: Optional[Dict] = None
    ) -> str:
        """Build Flux query from parameters"""
        query_parts = []

        # From bucket
        bucket_name = bucket or self.config.default_bucket
        query_parts.append(f'from(bucket: "{bucket_name}")')

        # Time range
        if time_range:
            query_parts.append(f'|> range(start: {time_range})')
        else:
            query_parts.append('|> range(start: -1h)')  # Default to last hour

        # Filter by measurement
        if measurement:
            query_parts.append(f'|> filter(fn: (r) => r._measurement == "{measurement}")')

        # Filter by tags
        if tags:
            for tag_key, tag_value in tags.items():
                query_parts.append(f'|> filter(fn: (r) => r.{tag_key} == "{tag_value}")')

        # Filter by fields
        if fields:
            field_filter = ' or '.join([f'r._field == "{field}"' for field in fields])
            query_parts.append(f'|> filter(fn: (r) => {field_filter})')

        # Aggregation
        if aggregation:
            window = aggregation.get("window", "1m")
            function = aggregation.get("function", "mean")
            query_parts.append(f'|> aggregateWindow(every: {window}, fn: {function}, createEmpty: false)')

        # Limit results
        query_parts.append('|> limit(n: 10000)')

        return "  \n".join(query_parts)

    async def write_strategy_performance(
        self,
        strategy_id: str,
        metrics: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write strategy performance metrics

        Args:
            strategy_id: Strategy identifier
            metrics: Performance metrics dictionary
            timestamp: Timestamp (defaults to now)

        Returns:
            bool: Success status
        """
        if not timestamp:
            timestamp = datetime.utcnow()

        # Prepare data for market_data measurement (returns)
        returns_data = [{
            "measurement": "strategy_returns",
            "timestamp": timestamp,
            "tags": {
                "strategy_id": strategy_id,
                "frequency": "daily"
            },
            "fields": {
                k: float(v) for k, v in metrics.items()
                if k in ["total_return", "daily_return", "cumulative_return", "annualized_return",
                         "excess_return", "alpha", "beta", "tracking_error"]
                and v is not None
            }
        }]

        # Prepare data for risk metrics
        risk_data = [{
            "measurement": "strategy_risk",
            "timestamp": timestamp,
            "tags": {
                "strategy_id": strategy_id,
                "risk_type": "portfolio",
                "confidence_level": 95
            },
            "fields": {
                k: float(v) for k, v in metrics.items()
                if k in ["volatility", "max_drawdown", "sharpe_ratio", "sortino_ratio", "calmar_ratio",
                         "var_95", "expected_shortfall_95", "downside_deviation"]
                and v is not None
            }
        }]

        # Prepare data for ratios
        ratios_data = [{
            "measurement": "strategy_ratios",
            "timestamp": timestamp,
            "tags": {
                "strategy_id": strategy_id,
                "benchmark": "SPY"
            },
            "fields": {
                k: float(v) for k, v in metrics.items()
                if k in ["sharpe_ratio", "sortino_ratio", "calmar_ratio", "information_ratio",
                         "treynor_ratio", "win_rate", "profit_factor", "recovery_factor"]
                and v is not None
            }
        }]

        # Write all data
        success = True
        success &= await self.write_market_data(returns_data, "strategy_returns", "strategy_performance")
        success &= await self.write_market_data(risk_data, "strategy_risk", "risk_metrics")
        success &= await self.write_market_data(ratios_data, "strategy_ratios", "strategy_performance")

        return success

    async def get_latest_price(self, symbol: str, exchange: str = "NASDAQ") -> Optional[float]:
        """
        Get latest price for a symbol with caching

        Args:
            symbol: Stock symbol
            exchange: Exchange name

        Returns:
            Optional[float]: Latest price or None if not found
        """
        # Check cache first
        if self.redis_client:
            cache_key = f"price:{symbol}"
            cached = self.redis_client.get(cache_key)
            if cached:
                try:
                    price_data = json.loads(cached)
                    logger.debug(f"Price from cache: {symbol} = {price_data['price']}")
                    return float(price_data["price"])
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass

        # Query from InfluxDB
        query = f'''
        from(bucket: "market_data_raw")
          |> range(start: -1h)
          |> filter(fn: (r) => r._measurement == "stock_price")
          |> filter(fn: (r) => r.symbol == "{symbol}")
          |> filter(fn: (r) => r.exchange == "{exchange}")
          |> filter(fn: (r) => r._field == "close")
          |> last()
        '''

        result = await self.query_data(query)

        if not result.empty:
            price = float(result.iloc[0]["_value"])
            return price

        return None

    async def batch_write_signals(
        self,
        signals: List[Dict],
        batch_size: Optional[int] = None
    ) -> int:
        """
        Batch write trading signals with performance optimization

        Args:
            signals: List of trading signal dictionaries
            batch_size: Batch size for writing

        Returns:
            int: Number of signals written
        """
        if not batch_size:
            batch_size = self.config.batch_size

        written_count = 0

        # Process in batches
        for i in range(0, len(signals), batch_size):
            batch = signals[i:i + batch_size]

            # Prepare data points
            data_points = []
            for signal in batch:
                data_points.append({
                    "measurement": "trading_signals",
                    "timestamp": signal.get("timestamp", datetime.utcnow()),
                    "tags": {
                        "strategy_id": signal.get("strategy_id"),
                        "symbol": signal.get("symbol"),
                        "signal_type": signal.get("signal_type", "price"),
                        "direction": signal.get("direction", "long")
                    },
                    "fields": {
                        "signal_value": float(signal.get("signal_value", 0)),
                        "confidence": float(signal.get("confidence", 0)),
                        "price": float(signal.get("price", 0)) if signal.get("price") else None
                    }
                })

            # Write batch
            if await self.write_market_data(data_points, "trading_signals", "trading_signals"):
                written_count += len(batch)

        return written_count

    def get_performance_metrics(self) -> Dict:
        """Get client performance metrics"""
        return {
            "write_count": self._write_count,
            "query_count": self._query_count,
            "error_count": self._error_count,
            "last_error": self._last_error,
            "connection_pool_size": len(self._connection_pool),
            "uptime": datetime.utcnow().isoformat() if self._client else None
        }

    async def close(self):
        """Close InfluxDB connection and cleanup"""
        if self._client:
            self._client.close()
            logger.info("InfluxDB connection closed")

        self._executor.shutdown(wait=True)

        # Log final metrics
        metrics = self.get_performance_metrics()
        logger.info(f"InfluxDB final metrics: {metrics}")


# Utility functions for common operations
async def create_influxdb_manager(
    config: InfluxDBConfig,
    redis_client: Optional[redis.Redis] = None
) -> InfluxDBManager:
    """Factory function to create and initialize InfluxDB manager"""
    manager = InfluxDBManager(config, redis_client)
    await manager.initialize()
    return manager


# Example usage and testing
async def main():
    """Example usage of InfluxDB manager"""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Create configuration
    config = InfluxDBConfig(
        url=os.getenv("INFLUXDB_URL", "http://localhost:8086"),
        token=os.getenv("INFLUXDB_TOKEN", ""),
        org="cbsc",
        batch_size=500
    )

    # Create manager
    manager = await create_influxdb_manager(config)

    try:
        # Example: Write market data
        sample_data = [{
            "timestamp": datetime.utcnow(),
            "tags": {"symbol": "AAPL", "exchange": "NASDAQ", "currency": "USD"},
            "fields": {"open": 150.25, "high": 152.75, "low": 149.50, "close": 152.10, "volume": 52341000}
        }]

        success = await manager.write_market_data(sample_data)
        print(f"Write success: {success}")

        # Example: Query data
        result = await manager.query_data(
            measurement="stock_price",
            time_range="-1h",
            tags={"symbol": "AAPL"}
        )
        print(f"Query result: {len(result)} records")

        # Example: Get latest price
        price = await manager.get_latest_price("AAPL")
        print(f"Latest AAPL price: {price}")

    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())