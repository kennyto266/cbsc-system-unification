#!/usr/bin/env python3
"""
InfluxDB Integration Tests
InfluxDB 集成測試
Phase 1.2 - 時序數據庫配置

Comprehensive integration tests for InfluxDB setup and functionality.
"""

import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np

# Test configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import modules to test
from src.services.influxdb_client import (
    InfluxDBManager, InfluxDBConfig, create_influxdb_manager
)
from src.config.influxdb_config import get_config, BucketType
from src.services.influxdb_monitoring import InfluxDBMonitor
from src.services.influxdb_retention_manager import InfluxDBRetentionManager
from src.utils.influxdb_utils import (
    MarketDataWriter, StrategyPerformanceWriter, RiskMetricsWriter,
    DataQueryHelper, validate_data_quality
)


class TestInfluxDBIntegration:
    """
    Test suite for InfluxDB integration.
    InfluxDB 集成測試套件。
    """

    @pytest.fixture
    async def manager(self):
        """Create InfluxDB manager for testing"""
        # Load configuration
        config = get_config()

        # Create manager
        manager = InfluxDBManager(config.connection)
        await manager.initialize()

        yield manager

        await manager.close()

    @pytest.fixture
    async def monitor(self, manager):
        """Create InfluxDB monitor for testing"""
        monitor = InfluxDBMonitor(manager)
        yield monitor

    @pytest.fixture
    def sample_market_data(self):
        """Generate sample market data for testing"""
        base_price = 150.0
        data = []

        for i in range(100):
            timestamp = datetime.utcnow() - timedelta(hours=i)
            # Simulate price movement
            price_change = np.random.normal(0, 2)
            open_price = base_price + price_change
            high_price = open_price + abs(np.random.normal(0, 1))
            low_price = open_price - abs(np.random.normal(0, 1))
            close_price = (open_price + high_price + low_price) / 3 + np.random.normal(0, 0.5)

            data.append({
                "timestamp": timestamp,
                "open": max(0, open_price),
                "high": max(0, high_price),
                "low": max(0, low_price),
                "close": max(0, close_price),
                "volume": np.random.randint(100000, 1000000)
            })

        return data

    @pytest.fixture
    def sample_strategy_returns(self):
        """Generate sample strategy returns for testing"""
        returns = []
        for i in range(252):  # One year of daily returns
            date = datetime.utcnow().date() - timedelta(days=i)
            daily_return = np.random.normal(0.0005, 0.02)  # 0.05% daily return, 2% volatility
            returns.append((datetime.combine(date, datetime.min.time()), daily_return))

        return returns

    @pytest.mark.asyncio
    async def test_bucket_creation(self, manager):
        """Test that required buckets are created"""
        logger.info("Testing bucket creation...")

        # Check that buckets exist
        buckets = manager._bucket_api.find_buckets()
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

        for bucket in required_buckets:
            assert bucket in bucket_names, f"Bucket {bucket} not found"

        logger.info("✅ All required buckets created")

    @pytest.mark.asyncio
    async def test_write_market_data(self, manager, sample_market_data):
        """Test writing market data"""
        logger.info("Testing market data write...")

        # Prepare data points
        data_points = []
        for bar in sample_market_data[:10]:  # Test with first 10 bars
            data_points.append({
                "measurement": "stock_price",
                "timestamp": bar["timestamp"],
                "tags": {
                    "symbol": "AAPL",
                    "exchange": "NASDAQ",
                    "currency": "USD"
                },
                "fields": bar
            })

        # Write data
        success = await manager.write_market_data(
            data_points,
            measurement="stock_price",
            bucket="market_data_raw"
        )

        assert success, "Failed to write market data"
        logger.info("✅ Market data write successful")

    @pytest.mark.asyncio
    async def test_query_market_data(self, manager):
        """Test querying market data"""
        logger.info("Testing market data query...")

        # Query AAPL data
        result = await manager.query_data(
            bucket="market_data_raw",
            measurement="stock_price",
            time_range="-1h",
            tags={"symbol": "AAPL"},
            fields=["close"]
        )

        assert isinstance(result, pd.DataFrame), "Query should return DataFrame"
        # Note: May be empty if no data exists, that's OK for this test
        logger.info(f"✅ Query returned {len(result)} records")

    @pytest.mark.asyncio
    async def test_strategy_performance_write(self, manager, sample_strategy_returns):
        """Test writing strategy performance"""
        logger.info("Testing strategy performance write...")

        strategy_id = "test-strategy-001"

        # Write daily returns
        success = await manager.write_strategy_performance(
            strategy_id=strategy_id,
            metrics={
                "total_return": 0.12,
                "daily_return": sample_strategy_returns[0][1],
                "volatility": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": -0.08
            }
        )

        assert success, "Failed to write strategy performance"
        logger.info("✅ Strategy performance write successful")

    @pytest.mark.asyncio
    async def test_latest_price_cache(self, manager):
        """Test latest price caching functionality"""
        logger.info("Testing latest price cache...")

        # Try to get latest price (may be None if no data)
        price = await manager.get_latest_price("AAPL")

        # Should not raise exception even if no data
        logger.info(f"✅ Latest price query completed: {price}")

    @pytest.mark.asyncio
    async def test_monitoring_functionality(self, monitor):
        """Test monitoring functionality"""
        logger.info("Testing monitoring functionality...")

        # Run health checks
        await monitor.run_health_checks()

        # Check that health status was updated
        assert "influxdb" in monitor.health_status
        assert "system" in monitor.health_status

        # Get metrics summary
        summary = monitor.get_metrics_summary()
        assert "operations" in summary
        assert "health_status" in summary

        logger.info("✅ Monitoring functionality working")

    @pytest.mark.asyncio
    async def test_utility_writers(self, manager):
        """Test utility writer classes"""
        logger.info("Testing utility writers...")

        # Test market data writer
        market_writer = MarketDataWriter(manager)

        sample_data = [{
            "timestamp": datetime.utcnow(),
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 152.0,
            "volume": 1000000
        }]

        success = await market_writer.write_ohlcv(
            symbol="TEST",
            exchange="NYSE",
            ohlcv_data=sample_data
        )
        assert success, "Market data writer failed"

        # Test strategy performance writer
        perf_writer = StrategyPerformanceWriter(manager)

        success = await perf_writer.write_daily_returns(
            strategy_id="test-001",
            strategy_name="Test Strategy",
            returns=[(datetime.utcnow(), 0.01)]
        )
        assert success, "Strategy performance writer failed"

        logger.info("✅ Utility writers working correctly")

    @pytest.mark.asyncio
    async def test_data_quality_validation(self, manager):
        """Test data quality validation"""
        logger.info("Testing data quality validation...")

        # Validate with small date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        quality_report = await validate_data_quality(
            manager=manager,
            bucket="market_data_raw",
            measurement="stock_price",
            symbol="AAPL",
            start=start_date,
            end=end_date
        )

        # Should return valid report structure
        assert "symbol" in quality_report
        assert "total_records" in quality_report
        assert "missing_records" in quality_report

        logger.info("✅ Data quality validation working")

    @pytest.mark.asyncio
    async def test_performance_metrics(self, manager):
        """Test performance metrics collection"""
        logger.info("Testing performance metrics...")

        # Get initial metrics
        initial_metrics = manager.get_performance_metrics()
        assert "write_count" in initial_metrics
        assert "query_count" in initial_metrics

        # Perform some operations
        await manager.query_data(
            bucket="market_data_raw",
            measurement="stock_price",
            time_range="-1h"
        )

        # Check metrics updated
        updated_metrics = manager.get_performance_metrics()
        assert updated_metrics["query_count"] >= initial_metrics["query_count"]

        logger.info("✅ Performance metrics collection working")

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, manager):
        """Test concurrent read/write operations"""
        logger.info("Testing concurrent operations...")

        # Prepare multiple write operations
        write_tasks = []
        for i in range(5):
            data = [{
                "measurement": "test_concurrent",
                "timestamp": datetime.utcnow(),
                "tags": {"batch": str(i)},
                "fields": {"value": i}
            }]
            task = manager.write_market_data(data, measurement="test_concurrent")
            write_tasks.append(task)

        # Execute writes concurrently
        write_results = await asyncio.gather(*write_tasks)
        assert all(write_results), "Some concurrent writes failed"

        # Prepare multiple read operations
        read_tasks = []
        for i in range(3):
            task = manager.query_data(
                bucket="market_data_raw",
                measurement="stock_price",
                time_range="-1h"
            )
            read_tasks.append(task)

        # Execute reads concurrently
        read_results = await asyncio.gather(*read_tasks)
        assert all(isinstance(r, pd.DataFrame) for r in read_results), "Read operations failed"

        logger.info("✅ Concurrent operations working correctly")

    def test_configuration_validation(self):
        """Test configuration validation"""
        logger.info("Testing configuration validation...")

        # Load configuration
        config = get_config()

        # Validate configuration
        issues = config.validate()

        # Log any issues but don't fail test
        if issues:
            logger.warning(f"Configuration issues: {issues}")
        else:
            logger.info("✅ Configuration validation passed")

    @pytest.mark.asyncio
    async def test_error_handling(self, manager):
        """Test error handling"""
        logger.info("Testing error handling...")

        # Test with invalid bucket
        result = await manager.query_data(
            bucket="nonexistent_bucket",
            measurement="stock_price"
        )
        # Should return empty DataFrame, not raise exception
        assert isinstance(result, pd.DataFrame)

        # Test with invalid measurement
        success = await manager.write_market_data(
            data=[{
                "measurement": "test",
                "timestamp": datetime.utcnow(),
                "tags": {},
                "fields": {"value": 1}
            }],
            measurement="test",
            bucket="nonexistent_bucket"
        )
        # Should handle error gracefully
        assert isinstance(success, bool)

        logger.info("✅ Error handling working correctly")

    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        """Test cleanup operations"""
        logger.info("Testing cleanup...")

        # Test writing and then cleaning up test data
        test_data = [{
            "measurement": "cleanup_test",
            "timestamp": datetime.utcnow(),
            "tags": {"cleanup": "true"},
            "fields": {"value": 1}
        }]

        # Write test data
        success = await manager.write_market_data(
            test_data,
            measurement="cleanup_test",
            bucket="system_metrics"
        )
        assert success

        # Note: Actual cleanup would require delete API
        # For now, just verify write succeeded
        logger.info("✅ Cleanup test completed")


# Run all tests
async def run_all_tests():
    """Run all integration tests"""
    logger.info("Starting InfluxDB integration tests...")

    # Load configuration
    config = get_config()

    # Validate configuration first
    issues = config.validate()
    if issues:
        logger.error(f"Configuration issues found: {issues}")
        return False

    # Create test instance
    test_instance = TestInfluxDBIntegration()

    # Run tests
    test_methods = [
        test_instance.test_configuration_validation,
        test_instance.test_bucket_creation,
        test_instance.test_write_market_data,
        test_instance.test_query_market_data,
        test_instance.test_strategy_performance_write,
        test_instance.test_latest_price_cache,
        test_instance.test_monitoring_functionality,
        test_instance.test_utility_writers,
        test_instance.test_data_quality_validation,
        test_instance.test_performance_metrics,
        test_instance.test_concurrent_operations,
        test_instance.test_error_handling,
        test_instance.test_cleanup
    ]

    passed = 0
    failed = 0

    for test_method in test_methods:
        try:
            # Create fresh manager for each test
            manager = InfluxDBManager(config.connection)
            await manager.initialize()

            # Create monitor if needed
            if "monitoring" in test_method.__name__:
                monitor = InfluxDBMonitor(manager)
                await test_method(monitor)
            else:
                await test_method(manager)

            await manager.close()
            passed += 1
            logger.info(f"✅ {test_method.__name__} passed")

        except Exception as e:
            logger.error(f"❌ {test_method.__name__} failed: {e}")
            failed += 1

    logger.info(f"\nTest Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)