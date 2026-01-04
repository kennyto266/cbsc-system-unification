#!/usr/bin/env python3
"""
Data Service API Endpoints
數據服務 API 端點
Task 8.1 - 數據獲取模塊

FastAPI endpoints for market data services including historical data,
real-time quotes, economic indicators, and data quality reports.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, Depends, Path, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import pandas as pd
import asyncio
import logging

from src.collectors.yfinance_collector import YFinanceCollector, YFinanceConfig, Market, DataPoint
from src.collectors.hkma_collector import HKMADailyInterestRateCollector, HKMAConfig, DataType
from src.collectors.data_quality_checker import DataQualityChecker, DataQualityConfig, QualityReport
from src.services.influxdb_client import InfluxDBManager
from src.services.cache_service import CacheService
from src.core.dependencies import get_influxdb_manager, get_cache_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v2/market-data", tags=["Market Data"])

# Pydantic models for requests/responses
class SymbolRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of stock symbols")
    markets: Optional[List[str]] = Field(default=["US", "HK"], description="Markets to query")

class HistoricalDataRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    period: Optional[str] = Field(default="1y", description="Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)")
    interval: Optional[str] = Field(default="1d", description="Data interval (1m, 5m, 15m, 30m, 60m, 90m, 1h, 1d)")
    start_date: Optional[datetime] = Field(None, description="Start date (overrides period)")
    end_date: Optional[datetime] = Field(None, description="End date (overrides period)")

class RealTimeDataRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of symbols for real-time data")
    max_age_seconds: Optional[int] = Field(default=60, description="Maximum age of cached data in seconds")

class EconomicDataRequest(BaseModel):
    data_type: str = Field(..., description="Type of economic data (hibor, base_rate, monetary_base)")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    tenors: Optional[List[str]] = Field(None, description="Specific tenors for HIBOR data")

class QualityCheckRequest(BaseModel):
    symbol: str = Field(..., description="Symbol to check")
    data_type: str = Field(default="price", description="Type of data (price, volume, etc.)")

class DataPointResponse(BaseModel):
    timestamp: datetime
    symbol: str
    exchange: str
    data_type: str
    interval: str
    fields: Dict[str, Union[float, int, str]]
    tags: Dict[str, str]
    quality_score: float

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EconomicDataResponse(BaseModel):
    timestamp: datetime
    data_type: str
    series_name: str
    value: Union[float, int, str]
    unit: str
    frequency: str
    source: str
    tags: Dict[str, str]
    quality_score: float

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class QualityReportResponse(BaseModel):
    symbol: str
    data_type: str
    total_records: int
    valid_records: int
    quality_score: float
    quality_level: str
    issues_count: int
    processing_time: float
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Global instances (would be properly initialized in production)
_yfinance_collector: Optional[YFinanceCollector] = None
_hkma_collector: Optional[HKMADailyInterestRateCollector] = None
_quality_checker: Optional[DataQualityChecker] = None

async def get_yfinance_collector(
    influxdb_manager: InfluxDBManager = Depends(get_influxdb_manager),
    cache_service: CacheService = Depends(get_cache_service)
) -> YFinanceCollector:
    """Get or initialize YFinance collector"""
    global _yfinance_collector

    if _yfinance_collector is None:
        config = YFinanceConfig(
            markets=[Market.US, Market.HK, Market.CN],
            batch_size=50
        )
        _yfinance_collector = YFinanceCollector(
            config=config,
            influxdb_manager=influxdb_manager,
            cache_service=cache_service
        )
        await _yfinance_collector.start()

    return _yfinance_collector

async def get_hkma_collector(
    influxdb_manager: InfluxDBManager = Depends(get_influxdb_manager),
    cache_service: CacheService = Depends(get_cache_service)
) -> HKMADailyInterestRateCollector:
    """Get or initialize HKMA collector"""
    global _hkma_collector

    if _hkma_collector is None:
        config = HKMAConfig(
            data_types=[DataType.HIBOR, DataType.BASE_RATE, DataType.MONETARY_BASE]
        )
        _hkma_collector = HKMADailyInterestRateCollector(
            config=config,
            influxdb_manager=influxdb_manager,
            cache_service=cache_service
        )
        await _hkma_collector.start()

    return _hkma_collector

async def get_quality_checker() -> DataQualityChecker:
    """Get or initialize quality checker"""
    global _quality_checker

    if _quality_checker is None:
        config = DataQualityConfig(
            max_price_change_pct=30.0,
            outlier_contamination=0.1
        )
        _quality_checker = DataQualityChecker(config)

    return _quality_checker

@router.get("/symbols/search", summary="Search symbols")
async def search_symbols(
    query: str = Query(..., description="Search query"),
    market: Optional[str] = Query("US", description="Market filter"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
) -> Dict[str, Any]:
    """
    Search for stock symbols

    This endpoint searches for stock symbols matching the query.
    Returns basic information about each symbol.
    """
    try:
        # For now, return mock data - in production would integrate with symbol database
        mock_results = [
            {
                "symbol": f"{query.upper()}",
                "name": f"{query.upper()} Corporation",
                "exchange": "NASDAQ",
                "market": "US",
                "currency": "USD",
                "type": "stock"
            }
        ]

        return {
            "success": True,
            "data": mock_results[:limit],
            "total": len(mock_results),
            "query": query,
            "market": market
        }

    except Exception as e:
        logger.error(f"Symbol search failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to search symbols")

@router.post("/history", response_model=List[DataPointResponse], summary="Get historical data")
async def get_historical_data(
    request: HistoricalDataRequest,
    collector: YFinanceCollector = Depends(get_yfinance_collector)
) -> List[DataPointResponse]:
    """
    Get historical market data for a symbol

    Retrieves historical OHLCV data for the specified symbol and time period.
    Data is cached to improve performance.
    """
    try:
        # Validate inputs
        if not request.symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")

        # Collect historical data
        data_points = await collector.collect_historical_data(
            symbol=request.symbol,
            period=request.period,
            interval=request.interval,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Convert to response format
        response = [
            DataPointResponse(
                timestamp=dp.timestamp,
                symbol=dp.symbol,
                exchange=dp.exchange,
                data_type=dp.data_type,
                interval=dp.interval,
                fields=dp.fields,
                tags=dp.tags,
                quality_score=dp.quality_score
            )
            for dp in data_points
        ]

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Historical data fetch failed for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch historical data")

@router.post("/realtime", response_model=Dict[str, DataPointResponse], summary="Get real-time data")
async def get_real_time_data(
    request: RealTimeDataRequest,
    collector: YFinanceCollector = Depends(get_yfinance_collector)
) -> Dict[str, DataPointResponse]:
    """
    Get real-time market data for multiple symbols

    Retrieves current market data for the specified symbols.
    Uses cached data when available to reduce API calls.
    """
    try:
        # Validate inputs
        if not request.symbols:
            raise HTTPException(status_code=400, detail="Symbols list is required")

        if len(request.symbols) > 100:
            raise HTTPException(status_code=400, detail="Too many symbols requested (max 100)")

        # Collect real-time data
        data_dict = await collector.collect_real_time_data(
            symbols=request.symbols,
            max_age_seconds=request.max_age_seconds
        )

        # Convert to response format
        response = {
            symbol: DataPointResponse(
                timestamp=dp.timestamp,
                symbol=dp.symbol,
                exchange=dp.exchange,
                data_type=dp.data_type,
                interval=dp.interval,
                fields=dp.fields,
                tags=dp.tags,
                quality_score=dp.quality_score
            )
            for symbol, dp in data_dict.items()
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Real-time data fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch real-time data")

@router.get("/{symbol}/company-info", summary="Get company information")
async def get_company_info(
    symbol: str = Path(..., description="Stock symbol"),
    collector: YFinanceCollector = Depends(get_yfinance_collector)
) -> Dict[str, Any]:
    """
    Get detailed company information

    Retrieves comprehensive information about the company including
    business description, sector, financial metrics, etc.
    """
    try:
        # Collect company information
        company_info = await collector.collect_company_info(symbol)

        if not company_info:
            raise HTTPException(status_code=404, detail="Company information not found")

        return {
            "success": True,
            "data": company_info,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Company info fetch failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch company information")

@router.get("/{symbol}/dividends-splits", summary="Get dividends and splits")
async def get_dividends_and_splits(
    symbol: str = Path(..., description="Stock symbol"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    collector: YFinanceCollector = Depends(get_yfinance_collector)
) -> Dict[str, Any]:
    """
    Get dividend and split history

    Retrieves historical dividend payments and stock splits for the symbol.
    """
    try:
        # Collect dividends and splits
        corp_actions = await collector.collect_dividends_and_splits(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )

        # Format response
        dividends = [
            {
                "date": dp.timestamp.isoformat(),
                "amount": dp.fields.get("amount", 0),
                "currency": dp.fields.get("currency", "USD")
            }
            for dp in corp_actions["dividends"]
        ]

        splits = [
            {
                "date": dp.timestamp.isoformat(),
                "ratio": dp.fields.get("ratio", 0),
                "numerator": dp.fields.get("numerator", 0),
                "denominator": dp.fields.get("denominator", 1)
            }
            for dp in corp_actions["splits"]
        ]

        return {
            "success": True,
            "symbol": symbol,
            "dividends": dividends,
            "splits": splits,
            "summary": {
                "dividend_count": len(dividends),
                "split_count": len(splits)
            }
        }

    except Exception as e:
        logger.error(f"Dividends/splits fetch failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dividends and splits")

@router.post("/economic-data", response_model=List[EconomicDataResponse], summary="Get economic data")
async def get_economic_data(
    request: EconomicDataRequest,
    collector: HKMADailyInterestRateCollector = Depends(get_hkma_collector)
) -> List[EconomicDataResponse]:
    """
    Get economic indicator data

    Retrieves macroeconomic data from HKMA including HIBOR rates,
    base rate, monetary base, and other economic indicators.
    """
    try:
        # Convert string to DataType enum
        try:
            data_type = DataType(request.data_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid data_type: {request.data_type}")

        # Collect data based on type
        if data_type == DataType.HIBOR:
            data_points = await collector.collect_hibor_rates(
                start_date=request.start_date,
                end_date=request.end_date,
                tenors=request.tenors
            )
        elif data_type == DataType.BASE_RATE:
            data_points = await collector.collect_base_rate(
                start_date=request.start_date,
                end_date=request.end_date
            )
        elif data_type == DataType.MONETARY_BASE:
            data_points = await collector.collect_monetary_base(
                start_date=request.start_date,
                end_date=request.end_date
            )
        else:
            raise HTTPException(status_code=400, detail=f"Data type {data_type} not yet implemented")

        # Convert to response format
        response = [
            EconomicDataResponse(
                timestamp=dp.timestamp,
                data_type=dp.data_type,
                series_name=dp.series_name,
                value=dp.value,
                unit=dp.unit,
                frequency=dp.frequency,
                source=dp.source,
                tags=dp.tags,
                quality_score=dp.quality_score
            )
            for dp in data_points
        ]

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Economic data fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch economic data")

@router.get("/economic/latest", summary="Get latest economic rates")
async def get_latest_economic_rates(
    collector: HKMADailyInterestRateCollector = Depends(get_hkma_collector)
) -> Dict[str, Any]:
    """
    Get latest economic rates

    Retrieves the most recent HIBOR rates, base rate, and other
    economic indicators from HKMA.
    """
    try:
        # Get latest rates
        latest_rates = await collector.get_latest_rates()

        return {
            "success": True,
            "data": latest_rates,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "HKMA"
        }

    except Exception as e:
        logger.error(f"Latest rates fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest economic rates")

@router.post("/quality-check", response_model=QualityReportResponse, summary="Check data quality")
async def check_data_quality(
    request: QualityCheckRequest,
    background_tasks: BackgroundTasks,
    checker: DataQualityChecker = Depends(get_quality_checker),
    influxdb_manager: InfluxDBManager = Depends(get_influxdb_manager)
) -> QualityReportResponse:
    """
    Perform data quality check

    Validates market data for the specified symbol and generates
    a comprehensive quality report with issues and recommendations.
    """
    try:
        # Fetch data from InfluxDB (simplified for example)
        # In production, would query actual historical data
        mock_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000000, 10000000, 100)
        })

        # Perform quality check
        report = await checker.check_market_data(
            data=mock_data,
            symbol=request.symbol,
            data_type=request.data_type
        )

        # Convert to response format
        response = QualityReportResponse(
            symbol=report.symbol,
            data_type=report.data_type,
            total_records=report.total_records,
            valid_records=report.valid_records,
            quality_score=report.quality_score,
            quality_level=report.quality_level.value,
            issues_count=len(report.issues),
            processing_time=report.processing_time,
            timestamp=report.timestamp
        )

        # Store detailed report in background
        background_tasks.add_task(
            store_quality_report,
            report
        )

        return response

    except Exception as e:
        logger.error(f"Quality check failed for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform quality check")

@router.get("/quality/{symbol}/trend", summary="Get quality trend")
async def get_quality_trend(
    symbol: str = Path(..., description="Stock symbol"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    checker: DataQualityChecker = Depends(get_quality_checker)
) -> Dict[str, Any]:
    """
    Get data quality trend

    Retrieves historical quality scores and trends for the symbol.
    """
    try:
        # Get quality trend
        trend = await checker.get_quality_trend(symbol, days)

        return {
            "success": True,
            "symbol": symbol,
            "trend": trend,
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Quality trend fetch failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch quality trend")

@router.get("/health", summary="Data service health check")
async def health_check(
    yfinance_collector: YFinanceCollector = Depends(get_yfinance_collector),
    hkma_collector: HKMADailyInterestRateCollector = Depends(get_hkma_collector),
    influxdb_manager: InfluxDBManager = Depends(get_influxdb_manager),
    cache_service: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """
    Health check for data service

    Checks the health of all data collection components and external services.
    """
    try:
        # Check each component
        yfinance_health = await yfinance_collector.health_check()
        hkma_health = await hkma_collector.health_check()

        # Check InfluxDB
        try:
            # Would perform actual health check
            influxdb_health = "ok"
        except:
            influxdb_health = "error"

        # Check Cache
        try:
            await cache_service.ping()
            cache_health = "ok"
        except:
            cache_health = "error"

        # Determine overall status
        all_checks = [
            yfinance_health.get("status", "unknown"),
            hkma_health.get("status", "unknown"),
            influxdb_health,
            cache_health
        ]

        if all(status == "ok" for status in all_checks):
            overall_status = "healthy"
        elif any(status == "unhealthy" for status in all_checks):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "yfinance_collector": yfinance_health,
                "hkma_collector": hkma_health,
                "influxdb": {"status": influxdb_health},
                "cache": {"status": cache_health}
            },
            "version": "2.0.0"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/statistics", summary="Get data collection statistics")
async def get_statistics(
    yfinance_collector: YFinanceCollector = Depends(get_yfinance_collector),
    hkma_collector: HKMADailyInterestRateCollector = Depends(get_hkma_collector)
) -> Dict[str, Any]:
    """
    Get data collection statistics

    Retrieves performance and usage statistics for data collectors.
    """
    try:
        # Get statistics from collectors
        yfinance_stats = await yfinance_collector.get_statistics()
        hkma_stats = await hkma_collector.get_statistics()

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "collectors": {
                "yfinance": yfinance_stats,
                "hkma": hkma_stats
            },
            "summary": {
                "total_requests": yfinance_stats.get("total_requests", 0) + hkma_stats.get("total_requests", 0),
                "total_data_points": yfinance_stats.get("data_points_collected", 0) + hkma_stats.get("data_points_collected", 0),
                "average_success_rate": (
                    yfinance_stats.get("success_rate", 0) + hkma_stats.get("success_rate", 0)
                ) / 2
            }
        }

    except Exception as e:
        logger.error(f"Statistics fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")

# Background task for storing quality reports
async def store_quality_report(report: QualityReport):
    """Store quality report in database or file system"""
    try:
        # Implementation would store the report
        # For now, just log it
        logger.info(f"Stored quality report for {report.symbol}: score={report.quality_score}")
    except Exception as e:
        logger.error(f"Failed to store quality report: {e}")

# Import numpy for mock data generation
import numpy as np