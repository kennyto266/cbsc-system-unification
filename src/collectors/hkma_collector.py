#!/usr/bin/env python3
"""
HKMA Data Collector
香港金融管理局數據收集器
Task 8.1 - 數據獲取模塊

Comprehensive collector for HKMA (Hong Kong Monetary Authority) macroeconomic data
including HIBOR rates, GDP, monetary aggregates, and other economic indicators.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import aiofiles
import pandas as pd
import numpy as np
import json
import xml.etree.ElementTree as ET
from src.services.influxdb_client import InfluxDBManager
from src.services.cache_service import CacheService
import redis
import backoff
from tenacity import retry, stop_after_attempt, wait_exponential
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataType(Enum):
    """HKMA data types"""
    HIBOR = "hibor"
    BASE_RATE = "base_rate"
    MONETARY_BASE = "monetary_base"
    EXCHANGE_RATE = "exchange_rate"
    INTERBANK_FLOW = "interbank_flow"
    LIQUIDITY_ADJUSTMENT = "liquidity_adjustment"
    GDP = "gdp"
    CPI = "cpi"
    UNEMPLOYMENT = "unemployment"
    TRADE_BALANCE = "trade_balance"

@dataclass
class HKMAConfig:
    """Configuration for HKMA collector"""
    base_url: str = "https://api.hkma.gov.hk/public/market-data-and-statistics"
    rate_limit: int = 100  # requests per hour
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_cache: bool = True
    cache_ttl: int = 3600  # seconds
    data_types: List[DataType] = field(default_factory=lambda: [
        DataType.HIBOR, DataType.BASE_RATE, DataType.MONETARY_BASE
    ])
    timezone: str = "Asia/Hong_Kong"

@dataclass
class EconomicDataPoint:
    """Single economic data point"""
    timestamp: datetime
    data_type: str
    series_name: str
    value: Union[float, int, str]
    unit: str
    frequency: str
    source: str
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0

class HKMADailyInterestRateCollector:
    """Enhanced HIBOR collector with comprehensive data handling"""

    def __init__(
        self,
        config: HKMAConfig,
        influxdb_manager: InfluxDBManager,
        cache_service: CacheService,
        redis_client: Optional[redis.Redis] = None
    ):
        self.config = config
        self.influxdb = influxdb_manager
        self.cache = cache_service
        self.redis_client = redis_client
        self.session: Optional[aiohttp.ClientSession] = None

        # HK timezone
        self.hk_tz = pytz.timezone(config.timezone)

        # HIBOR tenors configuration
        self.hibor_tenors = {
            "ON": {"name": "Overnight", "api_key": "hibor_on"},
            "1W": {"name": "1 Week", "api_key": "hibor_1w"},
            "1M": {"name": "1 Month", "api_key": "hibor_1m"},
            "2M": {"name": "2 Months", "api_key": "hibor_2m"},
            "3M": {"name": "3 Months", "api_key": "hibor_3m"},
            "6M": {"name": "6 Months", "api_key": "hibor_6m"},
            "12M": {"name": "12 Months", "api_key": "hibor_12m"}
        }

        # Data source configurations
        self.data_sources = {
            DataType.HIBOR: {
                "endpoint": "/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily",
                "parser": self._parse_hibor_data
            },
            DataType.BASE_RATE: {
                "endpoint": "/monthly-statistical-bulletin/er-ir/base-rate",
                "parser": self._parse_base_rate_data
            },
            DataType.MONETARY_BASE: {
                "endpoint": "/monthly-statistical-bulletin/mo/cm/monetary-base",
                "parser": self._parse_monetary_base_data
            },
            DataType.EXCHANGE_RATE: {
                "endpoint": "/daily-statistical-bulletin/er-ir/exchange-rates",
                "parser": self._parse_exchange_rate_data
            },
            DataType.GDP: {
                "endpoint": "/quarterly-statistical-bulletel/gdp",
                "parser": self._parse_gdp_data
            }
        }

        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "data_points_collected": 0,
            "cache_hits": 0,
            "last_collection": None,
            "errors": []
        }

        logger.info(f"HKMA collector initialized for {len(config.data_types)} data types")

    async def start(self):
        """Initialize and start the collector"""
        if self.session:
            logger.warning("Collector already started")
            return

        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            connector=aiohttp.TCPConnector(limit=10),
            headers={
                'User-Agent': 'CBSC-QuantSystem/1.0',
                'Accept': 'application/json, text/xml, */*'
            }
        )

        logger.info("✅ HKMA collector started")

    async def stop(self):
        """Stop the collector and cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None

        logger.info("HKMA collector stopped")

    async def collect_hibor_rates(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenors: Optional[List[str]] = None,
        force_refresh: bool = False
    ) -> List[EconomicDataPoint]:
        """
        Collect HIBOR rates for specified period and tenors

        Args:
            start_date: Start date for collection
            end_date: End date for collection
            tenors: List of tenors to collect (default: all)
            force_refresh: Ignore cache and fetch fresh data

        Returns:
            List of EconomicDataPoint objects
        """
        try:
            if not tenors:
                tenors = list(self.hibor_tenors.keys())

            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now(self.hk_tz)
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Generate cache key
            cache_key = f"hibor_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{'_'.join(tenors)}"

            # Check cache
            if not force_refresh and self.config.enable_cache:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    self.stats["cache_hits"] += 1
                    logger.debug(f"Cache hit for HIBOR data")
                    return [EconomicDataPoint(**dp) for dp in json.loads(cached_data)]

            # Collect data for each tenor
            all_data = []

            for tenor in tenors:
                if tenor not in self.hibor_tenors:
                    logger.warning(f"Invalid tenor: {tenor}")
                    continue

                # Fetch data from HKMA API
                data = await self._fetch_hibor_tenor(tenor, start_date, end_date)
                all_data.extend(data)

                # Rate limiting
                await asyncio.sleep(0.1)

            # Validate and quality check
            valid_data = []
            for dp in all_data:
                if await self._validate_data_point(dp):
                    valid_data.append(dp)
                else:
                    logger.debug(f"Invalid HIBOR data point at {dp.timestamp}")

            # Cache results
            if valid_data and self.config.enable_cache:
                cache_data = json.dumps([dp.__dict__ for dp in valid_data], default=str)
                await self.cache.set(cache_key, cache_data, ttl=self.config.cache_ttl)

            # Update statistics
            self.stats["successful_requests"] += 1
            self.stats["data_points_collected"] += len(valid_data)
            self.stats["last_collection"] = datetime.utcnow()

            logger.info(f"Collected {len(valid_data)} HIBOR data points for {len(tenors)} tenors")
            return valid_data

        except Exception as e:
            self.stats["failed_requests"] += 1
            self.stats["errors"].append(f"HIBOR collection failed: {str(e)}")
            logger.error(f"Failed to collect HIBOR rates: {e}")
            return []

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        base=1,
        max_value=10
    )
    async def _fetch_hibor_tenor(
        self,
        tenor: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[EconomicDataPoint]:
        """Fetch HIBOR data for a specific tenor"""
        endpoint = f"{self.config.base_url}/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily"

        # Build query parameters
        params = {
            "from": start_date.strftime("%d-%m-%Y"),
            "to": end_date.strftime("%d-%m-%Y"),
            "lang": "en"
        }

        async with self.session.get(endpoint, params=params) as response:
            if response.status != 200:
                raise Exception(f"API request failed with status {response.status}")

            # Parse response
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                data = await response.json()
            elif 'text/xml' in content_type:
                xml_text = await response.text()
                data = self._parse_xml_response(xml_text)
            else:
                text = await response.text()
                data = self._parse_text_response(text)

            # Parse HIBOR specific data
            return self._parse_hibor_data(data, tenor)

    def _parse_hibor_data(self, data: Dict[str, Any], tenor: str) -> List[EconomicDataPoint]:
        """Parse HIBOR data from API response"""
        data_points = []

        try:
            # Handle different response formats
            if "result" in data:
                records = data["result"].get("records", [])
            else:
                records = data.get("records", [])

            for record in records:
                try:
                    # Extract date
                    date_str = record.get("end_of_date") or record.get("date")
                    if not date_str:
                        continue

                    # Parse date with timezone awareness
                    if isinstance(date_str, str):
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                        timestamp = self.hk_tz.localize(datetime.combine(date_obj, datetime.min.time()))
                    else:
                        timestamp = date_str

                    # Extract rate value
                    rate_key = self.hibor_tenors[tenor]["api_key"]
                    rate_value = record.get(rate_key)

                    if rate_value is None or rate_value == "":
                        continue

                    # Convert to float
                    try:
                        rate = float(rate_value)
                    except (ValueError, TypeError):
                        continue

                    # Validate rate value
                    if rate < 0 or rate > 100:
                        logger.warning(f"Unusual HIBOR rate for {tenor}: {rate}")
                        continue

                    # Create data point
                    dp = EconomicDataPoint(
                        timestamp=timestamp,
                        data_type=DataType.HIBOR.value,
                        series_name=f"HIBOR_{tenor}",
                        value=rate,
                        unit="percent",
                        frequency="daily",
                        source="HKMA",
                        tags={
                            "tenor": tenor,
                            "tenor_name": self.hibor_tenors[tenor]["name"],
                            "currency": "HKD"
                        },
                        metadata={
                            "raw_value": rate_value,
                            "collection_time": datetime.utcnow()
                        }
                    )

                    data_points.append(dp)

                except Exception as e:
                    logger.debug(f"Failed to parse HIBOR record: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to parse HIBOR data: {e}")

        return data_points

    async def collect_base_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        force_refresh: bool = False
    ) -> List[EconomicDataPoint]:
        """Collect Base Rate data"""
        try:
            if not end_date:
                end_date = datetime.now(self.hk_tz)
            if not start_date:
                start_date = end_date - timedelta(days=365)

            cache_key = f"base_rate_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"

            if not force_refresh and self.config.enable_cache:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    self.stats["cache_hits"] += 1
                    return [EconomicDataPoint(**dp) for dp in json.loads(cached_data)]

            # Fetch from HKMA API
            endpoint = f"{self.config.base_url}/monthly-statistical-bulletin/er-ir/base-rate"
            params = {
                "from": start_date.strftime("%d-%m-%Y"),
                "to": end_date.strftime("%d-%m-%Y"),
                "lang": "en"
            }

            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Base rate API request failed: {response.status}")

                data = await response.json()
                data_points = self._parse_base_rate_data(data)

                # Validate data
                valid_data = [dp for dp in data_points if await self._validate_data_point(dp)]

                # Cache results
                if valid_data and self.config.enable_cache:
                    cache_data = json.dumps([dp.__dict__ for dp in valid_data], default=str)
                    await self.cache.set(cache_key, cache_data, ttl=self.config.cache_ttl)

                logger.info(f"Collected {len(valid_data)} base rate data points")
                return valid_data

        except Exception as e:
            logger.error(f"Failed to collect base rate data: {e}")
            return []

    def _parse_base_rate_data(self, data: Dict[str, Any]) -> List[EconomicDataPoint]:
        """Parse Base Rate data from API response"""
        data_points = []

        try:
            records = data.get("result", {}).get("records", [])

            for record in records:
                date_str = record.get("end_of_date")
                rate_str = record.get("base_rate")

                if not date_str or rate_str is None:
                    continue

                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                timestamp = self.hk_tz.localize(datetime.combine(date_obj, datetime.min.time()))

                try:
                    rate = float(rate_str)
                except (ValueError, TypeError):
                    continue

                dp = EconomicDataPoint(
                    timestamp=timestamp,
                    data_type=DataType.BASE_RATE.value,
                    series_name="HKMA_Base_Rate",
                    value=rate,
                    unit="percent",
                    frequency="daily",
                    source="HKMA",
                    tags={
                        "currency": "HKD",
                        "rate_type": "base_rate"
                    }
                )

                data_points.append(dp)

        except Exception as e:
            logger.error(f"Failed to parse base rate data: {e}")

        return data_points

    async def collect_monetary_base(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        force_refresh: bool = False
    ) -> List[EconomicDataPoint]:
        """Collect Monetary Base data"""
        try:
            if not end_date:
                end_date = datetime.now(self.hk_tz)
            if not start_date:
                start_date = end_date - timedelta(days=365)

            cache_key = f"monetary_base_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"

            if not force_refresh and self.config.enable_cache:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    self.stats["cache_hits"] += 1
                    return [EconomicDataPoint(**dp) for dp in json.loads(cached_data)]

            # Fetch from HKMA API
            endpoint = f"{self.config.base_url}/monthly-statistical-bulletin/mo/cm/monetary-base"
            params = {
                "from": start_date.strftime("%d-%m-%Y"),
                "to": end_date.strftime("%d-%m-%Y"),
                "lang": "en"
            }

            async with self.session.get(endpoint, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Monetary base API request failed: {response.status}")

                data = await response.json()
                data_points = self._parse_monetary_base_data(data)

                # Validate data
                valid_data = [dp for dp in data_points if await self._validate_data_point(dp)]

                # Cache results
                if valid_data and self.config.enable_cache:
                    cache_data = json.dumps([dp.__dict__ for dp in valid_data], default=str)
                    await self.cache.set(cache_key, cache_data, ttl=self.config.cache_ttl)

                logger.info(f"Collected {len(valid_data)} monetary base data points")
                return valid_data

        except Exception as e:
            logger.error(f"Failed to collect monetary base data: {e}")
            return []

    def _parse_monetary_base_data(self, data: Dict[str, Any]) -> List[EconomicDataPoint]:
        """Parse Monetary Base data from API response"""
        data_points = []

        try:
            records = data.get("result", {}).get("records", [])

            for record in records:
                date_str = record.get("end_of_date")
                if not date_str:
                    continue

                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                timestamp = self.hk_tz.localize(datetime.combine(date_obj, datetime.min.time()))

                # Extract different components of monetary base
                components = {
                    "monetary_base": record.get("monetary_base"),
                    "certificates_of_indebtedness": record.get("certificates_of_indebtedness"),
                    "government_notes_coins": record.get("government_notes_coins"),
                    "aggregated_balance": record.get("aggregated_balance"),
                    "exchange_fund_bill": record.get("exchange_fund_bill"),
                    "exchange_fund_notes": record.get("exchange_fund_notes")
                }

                for component, value in components.items():
                    if value is not None:
                        try:
                            amount = float(value)
                            if amount < 0:
                                continue

                            dp = EconomicDataPoint(
                                timestamp=timestamp,
                                data_type=DataType.MONETARY_BASE.value,
                                series_name=f"HKMA_Monetary_Base_{component}",
                                value=amount,
                                unit="HKD_millions",
                                frequency="daily",
                                source="HKMA",
                                tags={
                                    "currency": "HKD",
                                    "component": component,
                                    "scale": "millions"
                                }
                            )

                            data_points.append(dp)

                        except (ValueError, TypeError):
                            continue

        except Exception as e:
            logger.error(f"Failed to parse monetary base data: {e}")

        return data_points

    async def collect_all_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        force_refresh: bool = False
    ) -> Dict[DataType, List[EconomicDataPoint]]:
        """
        Collect all configured data types

        Args:
            start_date: Start date for collection
            end_date: End date for collection
            force_refresh: Ignore cache

        Returns:
            Dictionary mapping data types to collected data points
        """
        results = {}

        # Collect each data type
        for data_type in self.config.data_types:
            try:
                if data_type == DataType.HIBOR:
                    results[data_type] = await self.collect_hibor_rates(
                        start_date=start_date,
                        end_date=end_date,
                        force_refresh=force_refresh
                    )
                elif data_type == DataType.BASE_RATE:
                    results[data_type] = await self.collect_base_rate(
                        start_date=start_date,
                        end_date=end_date,
                        force_refresh=force_refresh
                    )
                elif data_type == DataType.MONETARY_BASE:
                    results[data_type] = await self.collect_monetary_base(
                        start_date=start_date,
                        end_date=end_date,
                        force_refresh=force_refresh
                    )
                else:
                    logger.warning(f"Data type {data_type} not yet implemented")

                # Rate limiting between data types
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to collect {data_type}: {e}")
                results[data_type] = []

        # Calculate total statistics
        total_points = sum(len(data) for data in results.values())
        logger.info(f"Collected total of {total_points} economic data points")

        return results

    async def _validate_data_point(self, dp: EconomicDataPoint) -> bool:
        """Validate an economic data point"""
        # Check timestamp
        if not dp.timestamp:
            return False

        # Check for future dates (allow slight buffer for timezone differences)
        if dp.timestamp > datetime.now(self.hk_tz) + timedelta(hours=1):
            return False

        # Check value
        if dp.value is None:
            return False

        # Type-specific validation
        if dp.data_type == DataType.HIBOR.value:
            # HIBOR rates should be between 0 and 20%
            try:
                rate = float(dp.value)
                if rate < 0 or rate > 20:
                    logger.warning(f"Unusual HIBOR rate: {rate}")
                    return False
            except:
                return False

        elif dp.data_type == DataType.MONETARY_BASE.value:
            # Monetary base should be positive
            try:
                amount = float(dp.value)
                if amount < 0:
                    return False
            except:
                return False

        return True

    def _parse_xml_response(self, xml_text: str) -> Dict[str, Any]:
        """Parse XML response from HKMA API"""
        try:
            root = ET.fromstring(xml_text)
            data = {"result": {"records": []}}

            # This is a simplified parser - would need to adapt to actual HKMA XML structure
            for record in root.findall(".//record"):
                record_dict = {}
                for child in record:
                    record_dict[child.tag] = child.text
                data["result"]["records"].append(record_dict)

            return data

        except ET.ParseError as e:
            logger.error(f"Failed to parse XML response: {e}")
            return {"result": {"records": []}}

    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Parse text response from HKMA API"""
        # This would be implemented based on actual text format
        return {"result": {"records": []}}

    async def get_latest_rates(self) -> Dict[str, Dict[str, float]]:
        """
        Get latest available rates for all data types

        Returns:
            Dictionary with latest rates
        """
        latest_rates = {}

        # Get latest HIBOR rates
        hibor_data = await self.collect_hibor_rates(
            start_date=datetime.now(self.hk_tz) - timedelta(days=7),
            end_date=datetime.now(self.hk_tz)
        )

        if hibor_data:
            # Group by tenor and get latest
            tenor_rates = {}
            for dp in hibor_data:
                tenor = dp.tags.get("tenor")
                if tenor:
                    if tenor not in tenor_rates or dp.timestamp > tenor_rates[tenor]["timestamp"]:
                        tenor_rates[tenor] = {
                            "value": float(dp.value),
                            "timestamp": dp.timestamp
                        }

            latest_rates["hibor"] = {k: v["value"] for k, v in tenor_rates.items()}

        # Get latest base rate
        base_rate_data = await self.collect_base_rate(
            start_date=datetime.now(self.hk_tz) - timedelta(days=7),
            end_date=datetime.now(self.hk_tz)
        )

        if base_rate_data:
            latest_dp = max(base_rate_data, key=lambda x: x.timestamp)
            latest_rates["base_rate"] = float(latest_dp.value)

        return latest_rates

    async def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return {
            **self.stats,
            "configured_data_types": len(self.config.data_types),
            "hibor_tenors": list(self.hibor_tenors.keys()),
            "success_rate": (
                self.stats["successful_requests"] / max(1, self.stats["total_requests"])
            ) * 100,
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(1, self.stats["total_requests"])
            ) * 100
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            # Test HKMA API connectivity
            test_url = f"{self.config.base_url}/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily"
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    health["checks"]["hkma_api"] = "ok"
                else:
                    health["checks"]["hkma_api"] = f"error_{response.status}"
                    health["status"] = "degraded"

            # Check cache service
            await self.cache.ping()
            health["checks"]["cache_service"] = "ok"

            # Check Redis if available
            if self.redis_client:
                self.redis_client.ping()
                health["checks"]["redis"] = "ok"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health

# Example usage
async def main():
    """Example usage of HKMA collector"""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Create configuration
    config = HKMAConfig(
        data_types=[DataType.HIBOR, DataType.BASE_RATE, DataType.MONETARY_BASE],
        enable_cache=True,
        cache_ttl=1800  # 30 minutes
    )

    try:
        # Create collector
        collector = HKMADailyInterestRateCollector(
            config=config,
            influxdb_manager=None,  # Would be initialized
            cache_service=None      # Would be initialized
        )

        # Start collector
        await collector.start()

        # Collect HIBOR data
        hibor_data = await collector.collect_hibor_rates(
            start_date=datetime.now() - timedelta(days=7),
            tenors=["ON", "1M", "3M", "6M", "12M"]
        )
        print(f"Collected {len(hibor_data)} HIBOR data points")

        # Get latest rates
        latest_rates = await collector.get_latest_rates()
        print(f"Latest HIBOR rates: {latest_rates.get('hibor', {})}")
        print(f"Latest base rate: {latest_rates.get('base_rate', 'N/A')}")

        # Collect all data types
        all_data = await collector.collect_all_data(
            start_date=datetime.now() - timedelta(days=7)
        )
        print(f"Collected data for {len(all_data)} data types")

        # Get statistics
        stats = await collector.get_statistics()
        print(f"Collector stats: {stats}")

        # Health check
        health = await collector.health_check()
        print(f"Health status: {health['status']}")

        # Stop collector
        await collector.stop()

    except Exception as e:
        logger.error(f"Example failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())