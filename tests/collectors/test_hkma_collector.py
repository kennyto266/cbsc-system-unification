#!/usr/bin/env python3
"""
Test cases for HKMA Collector
HKMA 收集器測試用例
Task 8.1 - 數據獲取模塊
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pandas as pd
import numpy as np
import json
from pytz import timezone

from src.collectors.hkma_collector import (
    HKMADailyInterestRateCollector, HKMAConfig, DataType, EconomicDataPoint
)

class TestHKMADailyInterestRateCollector:
    """Test cases for HKMADailyInterestRateCollector"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HKMAConfig(
            data_types=[DataType.HIBOR, DataType.BASE_RATE],
            enable_cache=True,
            cache_ttl=1800
        )

    @pytest.fixture
    def mock_influxdb(self):
        """Create mock InfluxDB manager"""
        mock = Mock()
        mock.write_market_data = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache service"""
        mock = Mock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.ping = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def collector(self, config, mock_influxdb, mock_cache):
        """Create HKMA collector instance"""
        return HKMADailyInterestRateCollector(
            config=config,
            influxdb_manager=mock_influxdb,
            cache_service=mock_cache
        )

    @pytest.mark.asyncio
    async def test_initialization(self, collector):
        """Test collector initialization"""
        assert collector.config.data_types == [DataType.HIBOR, DataType.BASE_RATE]
        assert collector.config.enable_cache is True
        assert collector.config.cache_ttl == 1800
        assert len(collector.hibor_tenors) == 7
        assert "ON" in collector.hibor_tenors
        assert "12M" in collector.hibor_tenors

    @pytest.mark.asyncio
    async def test_start_stop(self, collector):
        """Test collector start and stop"""
        # Mock aiohttp.ClientSession
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value = Mock()

            await collector.start()
            assert collector.session is not None

            await collector.stop()
            assert collector.session is None

    @pytest.mark.asyncio
    async def test_collect_hibor_rates(self, collector):
        """Test HIBOR rates collection"""
        # Mock API response
        mock_response_data = {
            "result": {
                "records": [
                    {
                        "end_of_date": "2020-01-01",
                        "hibor_on": "1.5",
                        "hibor_1w": "2.0",
                        "hibor_1m": "2.5",
                        "hibor_3m": "3.0",
                        "hibor_6m": "3.5",
                        "hibor_12m": "4.0"
                    },
                    {
                        "end_of_date": "2020-01-02",
                        "hibor_on": "1.6",
                        "hibor_1w": "2.1",
                        "hibor_1m": "2.6",
                        "hibor_3m": "3.1",
                        "hibor_6m": "3.6",
                        "hibor_12m": "4.1"
                    }
                ]
            }
        }

        # Mock session response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)

        with patch.object(collector, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            # Collect data
            data_points = await collector.collect_hibor_rates(
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2020, 1, 2),
                tenors=["ON", "1M", "3M"]
            )

            # Assertions
            assert len(data_points) > 0
            assert all(isinstance(dp, EconomicDataPoint) for dp in data_points)
            assert all(dp.data_type == DataType.HIBOR.value for dp in data_points)

            # Check specific tenors
            tenors = set(dp.tags.get("tenor") for dp in data_points)
            assert "ON" in tenors
            assert "1M" in tenors
            assert "3M" in tenors

    @pytest.mark.asyncio
    async def test_collect_base_rate(self, collector):
        """Test base rate collection"""
        # Mock API response
        mock_response_data = {
            "result": {
                "records": [
                    {
                        "end_of_date": "2020-01-01",
                        "base_rate": "1.75"
                    },
                    {
                        "end_of_date": "2020-01-02",
                        "base_rate": "1.80"
                    }
                ]
            }
        }

        # Mock session response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)

        with patch.object(collector, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            # Collect data
            data_points = await collector.collect_base_rate(
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2020, 1, 2)
            )

            # Assertions
            assert len(data_points) == 2
            assert all(isinstance(dp, EconomicDataPoint) for dp in data_points)
            assert all(dp.data_type == DataType.BASE_RATE.value for dp in data_points)
            assert all(dp.series_name == "HKMA_Base_Rate" for dp in data_points)

    @pytest.mark.asyncio
    async def test_collect_monetary_base(self, collector):
        """Test monetary base collection"""
        # Mock API response
        mock_response_data = {
            "result": {
                "records": [
                    {
                        "end_of_date": "2020-01-01",
                        "monetary_base": "1000000",
                        "certificates_of_indebtedness": "500000",
                        "government_notes_coins": "100000",
                        "aggregated_balance": "400000"
                    }
                ]
            }
        }

        # Mock session response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)

        with patch.object(collector, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            # Collect data
            data_points = await collector.collect_monetary_base(
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2020, 1, 1)
            )

            # Assertions
            assert len(data_points) > 0
            assert all(isinstance(dp, EconomicDataPoint) for dp in data_points)
            assert all(dp.data_type == DataType.MONETARY_BASE.value for dp in data_points)

            # Check different components
            components = set(dp.tags.get("component") for dp in data_points)
            assert "monetary_base" in components
            assert "certificates_of_indebtedness" in components

    @pytest.mark.asyncio
    async def test_collect_all_data(self, collector):
        """Test collecting all configured data types"""
        # Mock all API responses
        hibor_response_data = {
            "result": {"records": []}
        }
        base_rate_response_data = {
            "result": {"records": []}
        }

        mock_response = Mock()
        mock_response.status = 200

        with patch.object(collector, 'session') as mock_session:
            # Setup different responses for different endpoints
            def get_response(*args, **kwargs):
                if "hibor" in args[0]:
                    mock_response.json = AsyncMock(return_value=hibor_response_data)
                elif "base-rate" in args[0]:
                    mock_response.json = AsyncMock(return_value=base_rate_response_data)
                return mock_response.__aenter__

            mock_session.get.side_effect = get_response

            # Collect all data
            results = await collector.collect_all_data(
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2020, 1, 2)
            )

            # Assertions
            assert DataType.HIBOR in results
            assert DataType.BASE_RATE in results
            assert isinstance(results[DataType.HIBOR], list)
            assert isinstance(results[DataType.BASE_RATE], list)

    @pytest.mark.asyncio
    async def test_parse_hibor_data(self, collector):
        """Test HIBOR data parsing"""
        # Test data
        data = {
            "result": {
                "records": [
                    {
                        "end_of_date": "2020-01-01",
                        "hibor_on": "1.5",
                        "hibor_1m": "2.5"
                    }
                ]
            }
        }

        # Parse data for ON tenor
        data_points = collector._parse_hibor_data(data, "ON")

        # Assertions
        assert len(data_points) == 1
        dp = data_points[0]
        assert dp.data_type == DataType.HIBOR.value
        assert dp.series_name == "HIBOR_ON"
        assert dp.value == 1.5
        assert dp.unit == "percent"
        assert dp.tags["tenor"] == "ON"
        assert dp.tags["tenor_name"] == "Overnight"

    @pytest.mark.asyncio
    async def test_parse_base_rate_data(self, collector):
        """Test base rate data parsing"""
        # Test data
        data = {
            "result": {
                "records": [
                    {
                        "end_of_date": "2020-01-01",
                        "base_rate": "1.75"
                    }
                ]
            }
        }

        # Parse data
        data_points = collector._parse_base_rate_data(data)

        # Assertions
        assert len(data_points) == 1
        dp = data_points[0]
        assert dp.data_type == DataType.BASE_RATE.value
        assert dp.series_name == "HKMA_Base_Rate"
        assert dp.value == 1.75
        assert dp.unit == "percent"
        assert dp.frequency == "daily"

    @pytest.mark.asyncio
    async def test_parse_monetary_base_data(self, collector):
        """Test monetary base data parsing"""
        # Test data
        data = {
            "result": {
                "records": [
                    {
                        "end_of_date": "2020-01-01",
                        "monetary_base": "1000000",
                        "certificates_of_indebtedness": "500000"
                    }
                ]
            }
        }

        # Parse data
        data_points = collector._parse_monetary_base_data(data)

        # Assertions
        assert len(data_points) == 2

        # Check monetary base
        monetary_dp = next(dp for dp in data_points if dp.tags["component"] == "monetary_base")
        assert monetary_dp.value == 1000000
        assert monetary_dp.unit == "HKD_millions"

        # Check certificates
        cert_dp = next(dp for dp in data_points if dp.tags["component"] == "certificates_of_indebtedness")
        assert cert_dp.value == 500000
        assert cert_dp.unit == "HKD_millions"

    @pytest.mark.asyncio
    async def test_validate_data_point(self, collector):
        """Test data point validation"""
        # Valid data point
        valid_dp = EconomicDataPoint(
            timestamp=datetime.now(),
            data_type="hibor",
            series_name="HIBOR_ON",
            value=1.5,
            unit="percent",
            frequency="daily",
            source="HKMA"
        )
        assert await collector._validate_data_point(valid_dp) is True

        # Invalid - future date
        future_dp = EconomicDataPoint(
            timestamp=datetime.now() + timedelta(hours=2),
            data_type="hibor",
            series_name="HIBOR_ON",
            value=1.5,
            unit="percent",
            frequency="daily",
            source="HKMA"
        )
        assert await collector._validate_data_point(future_dp) is False

        # Invalid - extreme HIBOR rate
        extreme_dp = EconomicDataPoint(
            timestamp=datetime.now(),
            data_type="hibor",
            series_name="HIBOR_ON",
            value=25.0,  # > 20%
            unit="percent",
            frequency="daily",
            source="HKMA"
        )
        assert await collector._validate_data_point(extreme_dp) is False

    @pytest.mark.asyncio
    async def test_get_latest_rates(self, collector):
        """Test getting latest rates"""
        # Mock recent data
        with patch.object(collector, 'collect_hibor_rates') as mock_hibor:
            with patch.object(collector, 'collect_base_rate') as mock_base:

                # Mock HIBOR data
                now = datetime.now()
                hibor_data = [
                    EconomicDataPoint(
                        timestamp=now - timedelta(minutes=30),
                        data_type="hibor",
                        series_name="HIBOR_ON",
                        value=1.5,
                        unit="percent",
                        frequency="daily",
                        source="HKMA",
                        tags={"tenor": "ON"}
                    ),
                    EconomicDataPoint(
                        timestamp=now - timedelta(minutes=30),
                        data_type="hibor",
                        series_name="HIBOR_1M",
                        value=2.5,
                        unit="percent",
                        frequency="daily",
                        source="HKMA",
                        tags={"tenor": "1M"}
                    )
                ]
                mock_hibor.return_value = hibor_data

                # Mock base rate data
                base_data = [
                    EconomicDataPoint(
                        timestamp=now - timedelta(minutes=30),
                        data_type="base_rate",
                        series_name="HKMA_Base_Rate",
                        value=1.75,
                        unit="percent",
                        frequency="daily",
                        source="HKMA"
                    )
                ]
                mock_base.return_value = base_data

                # Get latest rates
                latest_rates = await collector.get_latest_rates()

                # Assertions
                assert "hibor" in latest_rates
                assert "base_rate" in latest_rates
                assert latest_rates["hibor"]["ON"] == 1.5
                assert latest_rates["hibor"]["1M"] == 2.5
                assert latest_rates["base_rate"] == 1.75

    @pytest.mark.asyncio
    async def test_get_statistics(self, collector):
        """Test statistics collection"""
        stats = await collector.get_statistics()

        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "data_points_collected" in stats
        assert "cache_hits" in stats
        assert "success_rate" in stats
        assert "cache_hit_rate" in stats
        assert "configured_data_types" in stats
        assert "hibor_tenors" in stats

    @pytest.mark.asyncio
    async def test_health_check(self, collector):
        """Test health check"""
        # Mock session
        collector.session = Mock()
        collector.session.close = AsyncMock()

        # Mock HTTP response
        mock_response = Mock()
        mock_response.status = 200

        with patch.object(collector, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            health = await collector.health_check()

            assert health["status"] in ["healthy", "degraded", "unhealthy"]
            assert "checks" in health
            assert "timestamp" in health

    def test_parse_xml_response(self, collector):
        """Test XML response parsing"""
        # Sample XML
        xml_text = """
        <root>
            <result>
                <records>
                    <record>
                        <end_of_date>2020-01-01</end_of_date>
                        <hibor_on>1.5</hibor_on>
                    </record>
                </records>
            </result>
        </root>
        """

        # Parse XML
        result = collector._parse_xml_response(xml_text)

        # Assertions
        assert "result" in result
        assert "records" in result["result"]
        assert len(result["result"]["records"]) == 1
        assert result["result"]["records"][0]["end_of_date"] == "2020-01-01"
        assert result["result"]["records"][0]["hibor_on"] == "1.5"

    def test_parse_text_response(self, collector):
        """Test text response parsing"""
        # Text response (returns empty structure for now)
        text = "Some text response"

        result = collector._parse_text_response(text)

        # Should return empty structure
        assert "result" in result
        assert "records" in result["result"]

class TestHKMAConfig:
    """Test cases for HKMAConfig"""

    def test_default_values(self):
        """Test default configuration values"""
        config = HKMAConfig()

        assert config.base_url == "https://api.hkma.gov.hk/public/market-data-and-statistics"
        assert config.rate_limit == 100
        assert config.timeout == 30
        assert config.retry_attempts == 3
        assert config.enable_cache is True
        assert config.cache_ttl == 3600
        assert config.timezone == "Asia/Hong_Kong"
        assert DataType.HIBOR in config.data_types

    def test_custom_values(self):
        """Test custom configuration values"""
        config = HKMAConfig(
            rate_limit=200,
            timeout=60,
            enable_cache=False,
            data_types=[DataType.BASE_RATE]
        )

        assert config.rate_limit == 200
        assert config.timeout == 60
        assert config.enable_cache is False
        assert config.data_types == [DataType.BASE_RATE]

class TestEconomicDataPoint:
    """Test cases for EconomicDataPoint"""

    def test_data_point_creation(self):
        """Test EconomicDataPoint creation"""
        timestamp = datetime.now()
        tags = {"tenor": "ON", "currency": "HKD"}
        metadata = {"source_api": "HKMA"}

        dp = EconomicDataPoint(
            timestamp=timestamp,
            data_type="hibor",
            series_name="HIBOR_ON",
            value=1.5,
            unit="percent",
            frequency="daily",
            source="HKMA",
            tags=tags,
            metadata=metadata
        )

        assert dp.timestamp == timestamp
        assert dp.data_type == "hibor"
        assert dp.series_name == "HIBOR_ON"
        assert dp.value == 1.5
        assert dp.unit == "percent"
        assert dp.frequency == "daily"
        assert dp.source == "HKMA"
        assert dp.tags == tags
        assert dp.metadata == metadata
        assert dp.quality_score == 1.0

# Integration tests
@pytest.mark.integration
class TestHKMADailyInterestRateCollectorIntegration:
    """Integration tests for HKMADailyInterestRateCollector"""

    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test with real HKMA API"""
        # This test requires internet access to HKMA API
        pytest.skip("Integration test - requires internet access to HKMA API")

    @pytest.mark.asyncio
    async def test_end_to_end_collection(self):
        """Test end-to-end data collection"""
        # This test would verify full collection pipeline
        pytest.skip("Integration test - requires specific setup")

# Error handling tests
@pytest.mark.error_handling
class TestHKMADailyInterestRateCollectorErrors:
    """Error handling tests for HKMADailyInterestRateCollector"""

    @pytest.mark.asyncio
    async def test_api_error_handling(self, collector):
        """Test handling of API errors"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status = 500
        mock_response.raise_for_status = Mock(side_effect=Exception("API Error"))

        with patch.object(collector, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            await collector.start()

            data_points = await collector.collect_hibor_rates()

            # Should return empty list on error
            assert data_points == []

            await collector.stop()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, collector):
        """Test handling of timeouts"""
        config = HKMAConfig(timeout=1)  # Very short timeout
        collector_with_timeout = HKMADailyInterestRateCollector(
            config=config,
            influxdb_manager=Mock(),
            cache_service=Mock()
        )

        # Mock slow response
        with patch.object(collector_with_timeout, 'session') as mock_session:
            mock_response = Mock()
            mock_response.status = 200

            # Simulate timeout
            async def mock_get(*args, **kwargs):
                await asyncio.sleep(2)  # Longer than timeout
                raise asyncio.TimeoutError()

            mock_session.get = mock_get

            await collector_with_timeout.start()

            data_points = await collector_with_timeout.collect_hibor_rates()

            # Should handle timeout gracefully
            assert data_points == []

            await collector_with_timeout.stop()

    @pytest.mark.asyncio
    async def test_invalid_data_parsing(self, collector):
        """Test handling of invalid data"""
        # Mock invalid API response
        mock_response_data = {
            "result": {
                "records": [
                    {
                        "end_of_date": "2020-01-01",
                        "hibor_on": "invalid_value"
                    },
                    {
                        "end_of_date": None,  # Invalid date
                        "hibor_on": "1.5"
                    }
                ]
            }
        }

        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)

        with patch.object(collector, 'session') as mock_session:
            mock_session.get.return_value.__aenter__.return_value = mock_response

            await collector.start()

            data_points = await collector.collect_hibor_rates()

            # Should filter out invalid records
            valid_points = [dp for dp in data_points if await collector._validate_data_point(dp)]
            assert len(valid_points) == 0

            await collector.stop()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])