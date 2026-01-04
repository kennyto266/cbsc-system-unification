"""
Market Data API v2 Endpoints
市場數據API v2端點實現

Provides historical and real-time market data endpoints
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import pandas as pd
import numpy as np

from src.dependencies import get_db, get_current_user
from src.services.influxdb_client import InfluxDBService
from src.services.cache_service import CacheService
from src.models.user import User

logger = logging.getLogger(__name__)

# Create router for market data endpoints
market_router = APIRouter(prefix="/market-data", tags=["market-data"])

# Initialize services
influxdb_service = InfluxDBService()
cache_service = CacheService()


@market_router.get("/{symbol}/history", response_model=Dict[str, Any])
async def get_market_data_history(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL, MSFT)"),
    interval: str = Query("1d", regex="^(1m|5m|15m|30m|1h|4h|1d|1w|1M)$",
                         description="Time interval"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of records"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Records per page"),
    adjusted: bool = Query(True, description="Include adjusted prices"),
    include_prepost: bool = Query(False, description="Include pre/post market data"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    獲取市場數據歷史記錄

    Args:
        symbol: 股票代碼
        interval: 時間間隔
        start_date: 開始日期
        end_date: 結束日期
        limit: 最大記錄數
        page: 頁碼
        page_size: 每頁記錄數
        adjusted: 是否包含調整後價格
        include_prepost: 是否包含盤前盤後數據

    Returns:
        Historical market data with pagination
    """
    try:
        # Validate and parse dates
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        else:
            # Default to 1 year ago
            start_dt = datetime.utcnow() - timedelta(days=365)

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        else:
            end_dt = datetime.utcnow()

        # Validate date range
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )

        # Check cache first
        cache_key = f"market_history:{symbol}:{interval}:{start_date}:{end_date}:{page}:{page_size}"
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {symbol} historical data")
            return cached_data

        # Fetch data from InfluxDB
        data = await influxdb_service.get_market_data(
            symbol=symbol,
            interval=interval,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )

        # Convert to list of dictionaries
        records = []
        for record in data:
            records.append({
                "timestamp": record.get("time"),
                "open": record.get("open"),
                "high": record.get("high"),
                "low": record.get("low"),
                "close": record.get("close"),
                "volume": record.get("volume"),
                "adjusted_close": record.get("adjusted_close") if adjusted else None,
                "pre_market": record.get("pre_market") if include_prepost else None,
                "post_market": record.get("post_market") if include_prepost else None
            })

        # Apply pagination
        total_records = len(records)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_records = records[start_idx:end_idx]

        # Calculate pagination metadata
        total_pages = (total_records + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        # Format response
        response = {
            "symbol": symbol,
            "interval": interval,
            "currency": "USD",  # Default currency
            "data": paginated_records,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total_records,
                "pages": total_pages,
                "hasNext": has_next,
                "hasPrev": has_prev
            },
            "metadata": {
                "startDate": start_dt.isoformat(),
                "endDate": end_dt.isoformat(),
                "adjusted": adjusted,
                "includePrePost": include_prepost,
                "dataPoints": total_records
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        # Cache response for 5 minutes
        await cache_service.set(cache_key, response, expire=300)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data history for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch market data history"
        )


@market_router.get("/{symbol}/realtime", response_model=Dict[str, Any])
async def get_real_time_data(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL, MSFT)"),
    fields: Optional[str] = Query(None, description="Comma-separated fields to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    獲取實時市場數據

    Args:
        symbol: 股票代碼
        fields: 要返回的字段列表

    Returns:
        Real-time market data
    """
    try:
        # Default fields to return
        default_fields = ["price", "change", "change_percent", "volume", "bid", "ask", "high", "low"]
        if fields:
            requested_fields = [f.strip() for f in fields.split(",")]
        else:
            requested_fields = default_fields

        # Check cache first (very short cache for real-time data)
        cache_key = f"realtime:{symbol}"
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {symbol} real-time data")
            # Filter fields if specified
            if fields:
                filtered_data = {k: v for k, v in cached_data.items() if k in requested_fields}
                return filtered_data
            return cached_data

        # Fetch latest data from InfluxDB
        latest_data = await influxdb_service.get_latest_market_data(symbol)

        if not latest_data:
            raise HTTPException(
                status_code=404,
                detail=f"No real-time data found for symbol {symbol}"
            )

        # Get previous close for change calculation
        prev_close = await influxdb_service.get_previous_close(symbol)
        current_price = latest_data.get("price", 0)

        # Calculate changes
        change = current_price - prev_close if prev_close else 0
        change_percent = (change / prev_close * 100) if prev_close and prev_close != 0 else 0

        # Format response
        response = {
            "symbol": symbol,
            "price": current_price,
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": latest_data.get("volume", 0),
            "bid": latest_data.get("bid", 0),
            "ask": latest_data.get("ask", 0),
            "high": latest_data.get("high", 0),
            "low": latest_data.get("low", 0),
            "open": latest_data.get("open", 0),
            "previous_close": prev_close,
            "timestamp": latest_data.get("time"),
            "market_state": _get_market_state(),
            "currency": "USD"
        }

        # Filter fields if specified
        if fields:
            response = {k: v for k, v in response.items() if k in requested_fields}

        # Cache for very short time (30 seconds)
        await cache_service.set(cache_key, response, expire=30)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching real-time data for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch real-time data"
        )


@market_router.get("/{symbol}/stats", response_model=Dict[str, Any])
async def get_market_stats(
    symbol: str = Path(..., description="Stock symbol"),
    period: str = Query("1M", regex="^(1D|1W|1M|3M|6M|1Y|ALL)$",
                       description="Statistics period"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    獲取市場統計數據

    Args:
        symbol: 股票代碼
        period: 統計週期

    Returns:
        Market statistics including volatility, averages, etc.
    """
    try:
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1D":
            start_date = end_date - timedelta(days=1)
        elif period == "1W":
            start_date = end_date - timedelta(weeks=1)
        elif period == "1M":
            start_date = end_date - timedelta(days=30)
        elif period == "3M":
            start_date = end_date - timedelta(days=90)
        elif period == "6M":
            start_date = end_date - timedelta(days=180)
        elif period == "1Y":
            start_date = end_date - timedelta(days=365)
        else:  # ALL
            start_date = None

        # Fetch historical data
        data = await influxdb_service.get_market_data(
            symbol=symbol,
            interval="1d",
            start_time=start_date,
            end_time=end_date
        )

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for symbol {symbol}"
            )

        # Convert to DataFrame for calculations
        df = pd.DataFrame(data)

        # Calculate statistics
        closes = df['close'].values
        volumes = df['volume'].values

        stats = {
            "symbol": symbol,
            "period": period,
            "data_points": len(df),
            "price": {
                "current": closes[-1],
                "high": closes.max(),
                "low": closes.min(),
                "average": closes.mean(),
                "median": np.median(closes)
            },
            "volume": {
                "current": volumes[-1] if len(volumes) > 0 else 0,
                "average": volumes.mean(),
                "total": volumes.sum()
            },
            "volatility": {
                "daily": np.std(np.diff(closes) / closes[:-1]) * 100,
                "annualized": np.std(np.diff(closes) / closes[:-1]) * np.sqrt(252) * 100
            },
            "returns": {
                "total": ((closes[-1] - closes[0]) / closes[0] * 100) if len(closes) > 1 else 0,
                "max_drawdown": _calculate_max_drawdown(closes),
                "sharpe_ratio": _calculate_sharpe_ratio(closes)
            },
            "period_start": df.iloc[0]['time'] if len(df) > 0 else None,
            "period_end": df.iloc[-1]['time'] if len(df) > 0 else None,
            "timestamp": datetime.utcnow().isoformat()
        }

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating market stats for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate market statistics"
        )


@market_router.get("/bulk/realtime", response_model=Dict[str, Any])
async def get_bulk_real_time_data(
    symbols: List[str] = Query(..., description="List of stock symbols"),
    fields: Optional[str] = Query(None, description="Comma-separated fields to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量獲取實時市場數據

    Args:
        symbols: 股票代碼列表
        fields: 要返回的字段列表

    Returns:
        Real-time data for multiple symbols
    """
    try:
        # Limit number of symbols
        if len(symbols) > 100:
            raise HTTPException(
                status_code=400,
                detail="Maximum 100 symbols allowed per request"
            )

        # Default fields
        default_fields = ["price", "change", "change_percent", "volume"]
        if fields:
            requested_fields = [f.strip() for f in fields.split(",")]
        else:
            requested_fields = default_fields

        results = {}
        errors = []

        # Process each symbol
        for symbol in symbols:
            try:
                # Check cache
                cache_key = f"realtime:{symbol}"
                cached_data = await cache_service.get(cache_key)

                if cached_data:
                    data = cached_data
                else:
                    # Fetch from database
                    data = await influxdb_service.get_latest_market_data(symbol)
                    if not data:
                        errors.append({"symbol": symbol, "error": "No data found"})
                        continue

                    # Calculate changes
                    prev_close = await influxdb_service.get_previous_close(symbol)
                    current_price = data.get("price", 0)
                    change = current_price - prev_close if prev_close else 0
                    change_percent = (change / prev_close * 100) if prev_close and prev_close != 0 else 0

                    data = {
                        "symbol": symbol,
                        "price": current_price,
                        "change": round(change, 2),
                        "change_percent": round(change_percent, 2),
                        "volume": data.get("volume", 0),
                        "timestamp": data.get("time")
                    }

                    # Cache for 30 seconds
                    await cache_service.set(cache_key, data, expire=30)

                # Filter fields
                filtered_data = {k: v for k, v in data.items() if k in requested_fields}
                results[symbol] = filtered_data

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                errors.append({"symbol": symbol, "error": str(e)})

        return {
            "data": results,
            "errors": errors if errors else None,
            "timestamp": datetime.utcnow().isoformat(),
            "symbols_requested": len(symbols),
            "symbols_returned": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk real-time data fetch: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch bulk real-time data"
        )


def _get_market_state() -> str:
    """獲取當前市場狀態"""
    now = datetime.utcnow()
    # Simple market hours check (NYSE)
    market_open = now.replace(hour=13, minute=30, second=0)  # 9:30 AM EST
    market_close = now.replace(hour=20, minute=0, second=0)   # 4:00 PM EST

    if now.weekday() >= 5:  # Weekend
        return "closed"
    elif market_open <= now <= market_close:
        return "open"
    elif now < market_open:
        return "pre_market"
    else:
        return "post_market"


def _calculate_max_drawdown(prices: np.ndarray) -> float:
    """計算最大回撤"""
    if len(prices) < 2:
        return 0.0

    peak = prices[0]
    max_drawdown = 0.0

    for price in prices:
        if price > peak:
            peak = price
        drawdown = (peak - price) / peak * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return max_drawdown


def _calculate_sharpe_ratio(prices: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """計算夏普比率"""
    if len(prices) < 2:
        return 0.0

    # Calculate daily returns
    returns = np.diff(prices) / prices[:-1]

    # Calculate excess returns
    daily_risk_free = risk_free_rate / 252
    excess_returns = returns - daily_risk_free

    # Calculate Sharpe ratio
    if np.std(excess_returns) == 0:
        return 0.0

    sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    return sharpe