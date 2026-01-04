#!/usr/bin/env python3
"""
Data Service Layer
數據服務層
Task 8.1 - 數據獲取模塊

Unified data service that orchestrates data collection, validation,
storage, and retrieval from multiple sources with caching and quality control.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.collectors.yfinance_collector import YFinanceCollector, YFinanceConfig, Market, DataPoint
from src.collectors.hkma_collector import HKMADailyInterestRateCollector, HKMAConfig, DataType, EconomicDataPoint
from src.collectors.data_quality_checker import DataQualityChecker, DataQualityConfig, QualityReport, QualityLevel
from src.services.influxdb_client import InfluxDBManager, InfluxDBConfig
from src.services.cache_service import CacheService
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Data sources"""
    YFINANCE = "yfinance"
    HKMA = "hkma"
    CACHE = "cache"
    DATABASE = "database"

class DataStatus(Enum):
    """Data status"""
    FRESH = "fresh"          # Fresh from source
    CACHED = "cached"        # From cache but still valid
    STALE = "stale"          # From cache but expired
    MISSING = "missing"      # No data available
    ERROR = "error"          # Error occurred

@dataclass
class DataRequest:
    """Data request specification"""
    symbol: str
    data_type: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    interval: str = "1d"
    source: Optional[DataSource] = None
    max_age_seconds: int = 300  # 5 minutes default
    force_refresh: bool = False
    quality_check: bool = True
    include_metadata: bool = False

@dataclass
class DataResponse:
    """Data response wrapper"""
    request: DataRequest
    data: List[Union[DataPoint, EconomicDataPoint]]
    status: DataStatus
    source: DataSource
    cached: bool
    quality_report: Optional[QualityReport] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DataServiceConfig:
    """Configuration for data service"""
    # Data sources configuration
    enable_yfinance: bool = True
    enable_hkma: bool = True
    enable_cache: bool = True
    enable_quality_check: bool = True

    # Cache configuration
    cache_ttl_historical: int = 3600  # 1 hour
    cache_ttl_realtime: int = 60     # 1 minute
    cache_ttl_company: int = 86400   # 24 hours

    # Quality thresholds
    min_quality_score: float = 60.0  # Minimum acceptable quality score
    auto_reject_poor_data: bool = True

    # Performance settings
    max_concurrent_requests: int = 10
    request_timeout: int = 30  # seconds
    retry_attempts: int = 3

    # Batch processing
    batch_size: int = 100
    enable_batch_processing: bool = True

class DataService:
    """
    Unified data service layer that orchestrates data collection from multiple sources
    with intelligent caching, quality control, and performance optimization.
    """

    def __init__(
        self,
        config: DataServiceConfig,
        influxdb_manager: InfluxDBManager,
        cache_service: CacheService,
        redis_client: Optional[redis.Redis] = None
    ):
        self.config = config
        self.influxdb = influxdb_manager
        self.cache = cache_service
        self.redis_client = redis_client

        # Initialize collectors
        self.yfinance_collector: Optional[YFinanceCollector] = None
        self.hkma_collector: Optional[HKMADailyInterestRateCollector] = None
        self.quality_checker: Optional[DataQualityChecker] = None

        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)

        # Request statistics
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "database_hits": 0,
            "source_requests": 0,
            "quality_checks": 0,
            "errors": 0,
            "processing_time": 0
        }

        logger.info("Data service initialized")

    async def initialize(self):
        """Initialize data service and collectors"""
        try:
            # Initialize YFinance collector
            if self.config.enable_yfinance:
                yfinance_config = YFinanceConfig(
                    markets=[Market.US, Market.HK, Market.CN],
                    batch_size=self.config.batch_size
                )
                self.yfinance_collector = YFinanceCollector(
                    config=yfinance_config,
                    influxdb_manager=self.influxdb,
                    cache_service=self.cache,
                    redis_client=self.redis_client
                )
                await self.yfinance_collector.start()
                logger.info("YFinance collector initialized")

            # Initialize HKMA collector
            if self.config.enable_hkma:
                hkma_config = HKMAConfig(
                    data_types=[DataType.HIBOR, DataType.BASE_RATE, DataType.MONETARY_BASE],
                    enable_cache=self.config.enable_cache
                )
                self.hkma_collector = HKMADailyInterestRateCollector(
                    config=hkma_config,
                    influxdb_manager=self.influxdb,
                    cache_service=self.cache,
                    redis_client=self.redis_client
                )
                await self.hkma_collector.start()
                logger.info("HKMA collector initialized")

            # Initialize quality checker
            if self.config.enable_quality_check:
                quality_config = DataQualityConfig(
                    critical_threshold=self.config.min_quality_score,
                    enable_statistical_detection=True,
                    enable_pattern_detection=True
                )
                self.quality_checker = DataQualityChecker(quality_config)
                logger.info("Quality checker initialized")

            logger.info("✅ Data service initialization complete")

        except Exception as e:
            logger.error(f"Failed to initialize data service: {e}")
            raise

    async def shutdown(self):
        """Shutdown data service and cleanup resources"""
        try:
            if self.yfinance_collector:
                await self.yfinance_collector.stop()
            if self.hkma_collector:
                await self.hkma_collector.stop()

            # Shutdown thread pool
            self.executor.shutdown(wait=True)

            logger.info("Data service shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    async def get_data(self, request: DataRequest) -> DataResponse:
        """
        Get data with intelligent source selection and caching

        Args:
            request: DataRequest specifying what data to fetch

        Returns:
            DataResponse with requested data
        """
        start_time = datetime.utcnow()
        self.stats["total_requests"] += 1

        try:
            logger.debug(f"Processing data request: {request.symbol} - {request.data_type}")

            # Step 1: Check cache first (unless force refresh)
            data = None
            source = DataSource.CACHE
            cached = False

            if not request.force_refresh and self.config.enable_cache:
                data = await self._get_cached_data(request)
                if data:
                    cached = True
                    self.stats["cache_hits"] += 1
                    logger.debug(f"Cache hit for {request.symbol}")

            # Step 2: If no cached data, fetch from appropriate source
            if not data:
                data, source = await self._fetch_from_source(request)
                self.stats["source_requests"] += 1

                # Cache the fetched data
                if data and self.config.enable_cache:
                    await self._cache_data(request, data)

            # Step 3: Perform quality check if requested
            quality_report = None
            if request.quality_check and self.config.enable_quality_check and data:
                quality_report = await self._check_quality(request, data)
                self.stats["quality_checks"] += 1

                # Auto-reject poor quality data if configured
                if (self.config.auto_reject_poor_data and
                    quality_report.quality_score < self.config.min_quality_score):
                    logger.warning(f"Rejecting poor quality data for {request.symbol}")
                    data = []

            # Step 4: Add metadata if requested
            metadata = {}
            if request.include_metadata:
                metadata = await self._generate_metadata(request, data, source)

            # Determine status
            if data:
                status = DataStatus.FRESH if not cached else DataStatus.CACHED
            else:
                status = DataStatus.MISSING

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.stats["processing_time"] += processing_time

            response = DataResponse(
                request=request,
                data=data,
                status=status,
                source=source,
                cached=cached,
                quality_report=quality_report,
                metadata=metadata,
                timestamp=datetime.utcnow()
            )

            logger.debug(f"Request completed in {processing_time:.2f}s")
            return response

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Data request failed: {e}")

            return DataResponse(
                request=request,
                data=[],
                status=DataStatus.ERROR,
                source=DataSource.CACHE,
                cached=False,
                errors=[str(e)],
                timestamp=datetime.utcnow()
            )

    async def get_batch_data(
        self,
        requests: List[DataRequest]
    ) -> List[DataResponse]:
        """
        Get data for multiple requests in parallel

        Args:
            requests: List of DataRequest objects

        Returns:
            List of DataResponse objects
        """
        if not requests:
            return []

        # Limit concurrent requests
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)

        async def process_with_semaphore(req: DataRequest) -> DataResponse:
            async with semaphore:
                return await self.get_data(req)

        # Process requests concurrently
        tasks = [process_with_semaphore(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error responses
        final_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                final_responses.append(DataResponse(
                    request=requests[i],
                    data=[],
                    status=DataStatus.ERROR,
                    source=DataSource.CACHE,
                    cached=False,
                    errors=[str(response)],
                    timestamp=datetime.utcnow()
                ))
            else:
                final_responses.append(response)

        return final_responses

    async def _get_cached_data(self, request: DataRequest) -> Optional[List[Union[DataPoint, EconomicDataPoint]]]:
        """Get data from cache"""
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)

            # Get from cache
            cached_data = await self.cache.get(cache_key)
            if not cached_data:
                return None

            # Deserialize data
            data_list = json.loads(cached_data)

            # Convert to appropriate objects
            if request.data_type == "economic":
                return [EconomicDataPoint(**dp) for dp in data_list]
            else:
                return [DataPoint(**dp) for dp in data_list]

        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")
            return None

    async def _fetch_from_source(
        self,
        request: DataRequest
    ) -> Tuple[List[Union[DataPoint, EconomicDataPoint]], DataSource]:
        """Fetch data from appropriate source"""
        # Determine source based on request
        if request.data_type == "economic":
            return await self._fetch_economic_data(request)
        else:
            return await self._fetch_market_data(request)

    async def _fetch_market_data(
        self,
        request: DataRequest
    ) -> Tuple[List[DataPoint], DataSource]:
        """Fetch market data from YFinance"""
        if not self.yfinance_collector:
            raise Exception("YFinance collector not initialized")

        # Convert to collector method call
        if request.data_type == "realtime":
            data = await self.yfinance_collector.collect_real_time_data(
                symbols=[request.symbol],
                max_age_seconds=request.max_age_seconds
            )
            # Extract single symbol data
            data = data.get(request.symbol, [])
        elif request.data_type in ["price", "history", "historical"]:
            # Determine period from date range
            if request.start_date and request.end_date:
                period = None
            else:
                period = "1y"  # Default

            data = await self.yfinance_collector.collect_historical_data(
                symbol=request.symbol,
                period=period,
                interval=request.interval,
                start_date=request.start_date,
                end_date=request.end_date
            )
        elif request.data_type == "company_info":
            # Company info is handled differently
            info = await self.yfinance_collector.collect_company_info(request.symbol)
            # Convert to DataPoint format
            data = [DataPoint(
                timestamp=datetime.utcnow(),
                symbol=request.symbol,
                exchange="",
                data_type="company_info",
                interval="",
                fields=info,
                tags={}
            )]
        else:
            raise ValueError(f"Unsupported data type: {request.data_type}")

        return data, DataSource.YFINANCE

    async def _fetch_economic_data(
        self,
        request: DataRequest
    ) -> Tuple[List[EconomicDataPoint], DataSource]:
        """Fetch economic data from HKMA"""
        if not self.hkma_collector:
            raise Exception("HKMA collector not initialized")

        # Parse economic data type
        try:
            data_type = DataType(request.data_type)
        except ValueError:
            raise ValueError(f"Invalid economic data type: {request.data_type}")

        # Collect data based on type
        if data_type == DataType.HIBOR:
            # Extract tenors from request metadata or use defaults
            tenors = request.metadata.get("tenors", None)
            data = await self.hkma_collector.collect_hibor_rates(
                start_date=request.start_date,
                end_date=request.end_date,
                tenors=tenors
            )
        elif data_type == DataType.BASE_RATE:
            data = await self.hkma_collector.collect_base_rate(
                start_date=request.start_date,
                end_date=request.end_date
            )
        elif data_type == DataType.MONETARY_BASE:
            data = await self.hkma_collector.collect_monetary_base(
                start_date=request.start_date,
                end_date=request.end_date
            )
        else:
            raise ValueError(f"Economic data type {data_type} not yet implemented")

        return data, DataSource.HKMA

    async def _cache_data(
        self,
        request: DataRequest,
        data: List[Union[DataPoint, EconomicDataPoint]]
    ):
        """Cache data for future use"""
        try:
            if not data:
                return

            # Generate cache key
            cache_key = self._generate_cache_key(request)

            # Determine TTL based on data type
            if request.data_type == "realtime":
                ttl = self.config.cache_ttl_realtime
            elif request.data_type == "company_info":
                ttl = self.config.cache_ttl_company
            else:
                ttl = self.config.cache_ttl_historical

            # Serialize data
            data_list = [dp.__dict__ for dp in data]
            cache_data = json.dumps(data_list, default=str)

            # Store in cache
            await self.cache.set(cache_key, cache_data, ttl=ttl)

        except Exception as e:
            logger.debug(f"Failed to cache data: {e}")

    def _generate_cache_key(self, request: DataRequest) -> str:
        """Generate cache key for request"""
        parts = [
            "data",
            request.data_type,
            request.symbol,
            request.interval,
            request.start_date.isoformat() if request.start_date else "",
            request.end_date.isoformat() if request.end_date else ""
        ]
        return ":".join(filter(None, parts))

    async def _check_quality(
        self,
        request: DataRequest,
        data: List[Union[DataPoint, EconomicDataPoint]]
    ) -> Optional[QualityReport]:
        """Perform data quality check"""
        if not self.quality_checker:
            return None

        try:
            # Convert to DataFrame for quality checking
            df = self._convert_to_dataframe(data, request.data_type)

            if df.empty:
                return None

            # Perform quality check
            report = await self.quality_checker.check_market_data(
                data=df,
                symbol=request.symbol,
                data_type=request.data_type
            )

            return report

        except Exception as e:
            logger.debug(f"Quality check failed: {e}")
            return None

    def _convert_to_dataframe(
        self,
        data: List[Union[DataPoint, EconomicDataPoint]],
        data_type: str
    ) -> pd.DataFrame:
        """Convert data points to DataFrame"""
        if not data:
            return pd.DataFrame()

        if data_type == "economic":
            # Handle economic data points
            records = []
            for dp in data:
                record = {
                    "date": dp.timestamp,
                    dp.series_name: dp.value,
                    "unit": dp.unit,
                    "frequency": dp.frequency
                }
                records.append(record)

            df = pd.DataFrame(records)
            if not df.empty:
                df = df.pivot_table(
                    index="date",
                    columns="series_name",
                    values="value",
                    aggfunc="first"
                ).reset_index()

        else:
            # Handle market data points
            records = []
            for dp in data:
                record = {
                    "date": dp.timestamp,
                    "open": dp.fields.get("open", 0),
                    "high": dp.fields.get("high", 0),
                    "low": dp.fields.get("low", 0),
                    "close": dp.fields.get("close", 0),
                    "volume": dp.fields.get("volume", 0)
                }
                records.append(record)

            df = pd.DataFrame(records)

        return df

    async def _generate_metadata(
        self,
        request: DataRequest,
        data: List[Union[DataPoint, EconomicDataPoint]],
        source: DataSource
    ) -> Dict[str, Any]:
        """Generate metadata for the response"""
        metadata = {
            "source": source.value,
            "data_points": len(data),
            "requested_at": request.timestamp.isoformat() if hasattr(request, 'timestamp') else datetime.utcnow().isoformat()
        }

        # Add date range if available
        if data:
            timestamps = [dp.timestamp for dp in data]
            metadata["date_range"] = {
                "start": min(timestamps).isoformat(),
                "end": max(timestamps).isoformat()
            }

        # Add quality summary if available
        # (Quality report would be passed separately in actual implementation)

        return metadata

    async def search_symbols(
        self,
        query: str,
        market: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for symbols

        Args:
            query: Search query
            market: Market filter
            limit: Maximum results

        Returns:
            List of matching symbols
        """
        # For now, return mock data
        # In production, would integrate with symbol database or external API
        mock_results = [
            {
                "symbol": query.upper(),
                "name": f"{query.upper()} Corporation",
                "exchange": "NASDAQ",
                "market": market or "US",
                "currency": "USD",
                "type": "stock"
            }
        ]

        return mock_results[:limit]

    async def get_latest_rates(
        self,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get latest economic rates

        Args:
            data_types: List of data types to fetch

        Returns:
            Dictionary with latest rates
        """
        if not self.hkma_collector:
            return {}

        try:
            latest_rates = await self.hkma_collector.get_latest_rates()
            return latest_rates

        except Exception as e:
            logger.error(f"Failed to get latest rates: {e}")
            return {}

    async def get_statistics(self) -> Dict[str, Any]:
        """Get data service statistics"""
        stats = {
            **self.stats,
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(1, self.stats["total_requests"])
            ) * 100,
            "average_processing_time": (
                self.stats["processing_time"] / max(1, self.stats["total_requests"])
            ),
            "error_rate": (
                self.stats["errors"] / max(1, self.stats["total_requests"])
            ) * 100
        }

        # Add collector statistics
        if self.yfinance_collector:
            yfinance_stats = await self.yfinance_collector.get_statistics()
            stats["yfinance"] = yfinance_stats

        if self.hkma_collector:
            hkma_stats = await self.hkma_collector.get_statistics()
            stats["hkma"] = hkma_stats

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }

        try:
            # Check YFinance collector
            if self.yfinance_collector:
                yfinance_health = await self.yfinance_collector.health_check()
                health["components"]["yfinance"] = yfinance_health
                if yfinance_health.get("status") != "healthy":
                    health["status"] = "degraded"

            # Check HKMA collector
            if self.hkma_collector:
                hkma_health = await self.hkma_collector.health_check()
                health["components"]["hkma"] = hkma_health
                if hkma_health.get("status") != "healthy":
                    health["status"] = "degraded"

            # Check cache service
            try:
                await self.cache.ping()
                health["components"]["cache"] = {"status": "ok"}
            except:
                health["components"]["cache"] = {"status": "error"}
                health["status"] = "degraded"

            # Check Redis if available
            if self.redis_client:
                try:
                    self.redis_client.ping()
                    health["components"]["redis"] = {"status": "ok"}
                except:
                    health["components"]["redis"] = {"status": "error"}
                    health["status"] = "degraded"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health

# Factory function for easy initialization
async def create_data_service(
    influxdb_manager: InfluxDBManager,
    cache_service: CacheService,
    redis_client: Optional[redis.Redis] = None,
    config: Optional[DataServiceConfig] = None
) -> DataService:
    """
    Create and initialize data service

    Args:
        influxdb_manager: InfluxDB manager instance
        cache_service: Cache service instance
        redis_client: Redis client instance
        config: Optional configuration

    Returns:
        Initialized DataService instance
    """
    service = DataService(
        config=config or DataServiceConfig(),
        influxdb_manager=influxdb_manager,
        cache_service=cache_service,
        redis_client=redis_client
    )

    await service.initialize()
    return service

# Example usage
async def main():
    """Example usage of data service"""
    # Mock dependencies for example
    from unittest.mock import Mock

    # Create mock dependencies
    influxdb_manager = Mock()
    cache_service = Mock()
    cache_service.get = Mock(return_value=None)
    cache_service.set = Mock()
    cache_service.ping = Mock()

    # Create service
    config = DataServiceConfig(
        enable_yfinance=True,
        enable_hkma=True,
        max_concurrent_requests=5
    )

    service = DataService(
        config=config,
        influxdb_manager=influxdb_manager,
        cache_service=cache_service
    )

    try:
        # Mock initialization (since we don't have real dependencies)
        # await service.initialize()

        # Create data request
        request = DataRequest(
            symbol="AAPL",
            data_type="historical",
            interval="1d",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )

        # Get data
        # response = await service.get_data(request)
        # print(f"Data status: {response.status}")
        # print(f"Data points: {len(response.data)}")

        # Get statistics
        stats = await service.get_statistics()
        print(f"Service statistics: {stats}")

        # Health check
        health = await service.health_check()
        print(f"Health status: {health['status']}")

    except Exception as e:
        logger.error(f"Example failed: {e}")
    finally:
        await service.shutdown()


if __name__ == "__main__":
    asyncio.run(main())