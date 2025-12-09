#!/usr/bin/env python3
"""
香港市場專用API端點 - Hong Kong Exclusive Market API Endpoints
專注於香港股票市場的數據API，確保只處理和返回香港相關數據
Hong Kong Exclusive Market API Endpoints - Focused on Hong Kong Stock Market Data APIs
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from ..data.hk_market_data_manager import get_hk_market_data_manager, HKMarketData
from ..multi_asset.asset_models import parse_symbol, is_hk_market_open

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="香港市場量化交易API",
    description="Hong Kong Exclusive Quantitative Trading API - 專注於香港股票市場數據",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全局數據管理器
hk_manager = get_hk_market_data_manager()

# 香港市場符號驗證函數
def validate_hk_symbol(symbol: str) -> str:
    """驗證並標準化香港股票符號"""
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol cannot be empty")

    # 解析符號為香港格式
    parsed = parse_symbol(symbol)
    if parsed.get('exchange', {}).get('value') != 'HKEX':
        raise HTTPException(
            status_code=400,
            detail=f"Symbol {symbol} is not a valid Hong Kong stock symbol. Expected format: 0700.HK or 0700"
        )

    return parsed['symbol']

def validate_hk_symbols_list(symbols: List[str]) -> List[str]:
    """驗證並標準化香港股票符號列表"""
    validated_symbols = []
    for symbol in symbols:
        try:
            validated_symbol = validate_hk_symbol(symbol)
            if validated_symbol not in validated_symbols:
                validated_symbols.append(validated_symbol)
        except HTTPException:
            logger.warning(f"Skipping non-HK symbol: {symbol}")
            continue

    if not validated_symbols:
        raise HTTPException(
            status_code=400,
            detail="No valid Hong Kong stock symbols provided. Expected format: 0700.HK or 0700"
        )

    return validated_symbols

# Pydantic模型
class StockDataResponse(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    currency: str = "HKD"
    asset_class: str = "equity"

class EconomicDataResponse(BaseModel):
    data_type: str
    timestamp: datetime
    value: Optional[float]
    source: str = "HKMA"
    metadata: Optional[Dict[str, Any]] = None

class MarketStatusResponse(BaseModel):
    is_open: bool
    next_open_time: Optional[datetime] = None
    next_close_time: Optional[datetime] = None
    current_time: datetime
    timezone: str = "HKT"

# API端點
@app.get("/", response_model=Dict[str, Any])
async def root():
    """API根端點"""
    return {
        "name": "香港市場量化交易API",
        "version": "1.0.0",
        "description": "Hong Kong Exclusive Quantitative Trading API",
        "market_focus": "Hong Kong Stock Exchange (HKEX)",
        "supported_assets": ["equity", "reit", "etf", "warrant", "trust"],
        "data_sources": ["HKMA", "Yahoo Finance HK", "Alpha Vantage"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """API健康檢查"""
    try:
        hk_health = await hk_manager.health_check()
        is_market_open = is_hk_market_open()

        return {
            "status": "healthy",
            "api_version": "1.0.0",
            "hk_market_status": "open" if is_market_open else "closed",
            "data_sources_health": hk_health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/market/status", response_model=MarketStatusResponse)
async def get_market_status():
    """獲取香港市場狀態"""
    try:
        from datetime import datetime, time
        import pytz

        hk_tz = pytz.timezone('Asia/Hong_Kong')
        now = datetime.now(hk_tz)

        # 計算下一個開盤和收盤時間
        is_open = is_hk_market_open()

        # 今天是週末嗎？
        is_weekend = now.weekday() >= 5

        # 計算今天的交易時間
        morning_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        morning_close = now.replace(hour=12, minute=0, second=0, microsecond=0)
        afternoon_open = now.replace(hour=13, minute=0, second=0, microsecond=0)
        afternoon_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

        next_open = None
        next_close = None

        if is_open:
            # 市場開盤中，返回下一個收盤時間
            if now.time() < morning_close.time():
                next_close = morning_close
            elif afternoon_open.time() <= now.time() < afternoon_close.time():
                next_close = afternoon_close
        else:
            # 市場收盤，返回下一個開盤時間
            if now.time() < morning_open.time() and not is_weekend:
                next_open = morning_open
            else:
                # 下個交易日
                days_ahead = 1
                while True:
                    next_day = now + timedelta(days=days_ahead)
                    if next_day.weekday() < 5:  # 週一到週五
                        next_open = next_day.replace(hour=9, minute=30, second=0, microsecond=0)
                        break
                    days_ahead += 1

        return MarketStatusResponse(
            is_open=is_open,
            next_open_time=next_open,
            next_close_time=next_close,
            current_time=now,
            timezone="HKT"
        )

    except Exception as e:
        logger.error(f"Failed to get market status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market status: {str(e)}")

@app.get("/stocks/{symbol}", response_model=StockDataResponse)
async def get_stock_data(symbol: str):
    """獲取單個香港股票數據"""
    try:
        # 驗證符號
        validated_symbol = validate_hk_symbol(symbol)

        # 獲取數據
        stock_data = await hk_manager.get_hk_stock_data([validated_symbol])

        if validated_symbol not in stock_data:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for Hong Kong stock: {validated_symbol}"
            )

        data = stock_data[validated_symbol]
        return StockDataResponse(
            symbol=data.symbol,
            timestamp=data.timestamp,
            open=data.open,
            high=data.high,
            low=data.low,
            close=data.close,
            volume=data.volume,
            currency=data.currency,
            asset_class=data.asset_class
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stock data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stock data: {str(e)}")

@app.get("/stocks/batch", response_model=List[StockDataResponse])
async def get_batch_stock_data(
    symbols: str = Query(..., description="香港股票符號列表，逗號分隔，例如: 0700.HK,0941.HK,1299.HK")
):
    """批量獲取香港股票數據"""
    try:
        # 解析符號列表
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

        # 驗證符號
        validated_symbols = validate_hk_symbols_list(symbol_list)

        # 限制批量請求大小
        if len(validated_symbols) > 20:
            raise HTTPException(
                status_code=400,
                detail="Batch request limited to maximum 20 symbols per request"
            )

        # 獲取數據
        stock_data = await hk_manager.get_hk_stock_data(validated_symbols)

        results = []
        for symbol in validated_symbols:
            if symbol in stock_data:
                data = stock_data[symbol]
                results.append(StockDataResponse(
                    symbol=data.symbol,
                    timestamp=data.timestamp,
                    open=data.open,
                    high=data.high,
                    low=data.low,
                    close=data.close,
                    volume=data.volume,
                    currency=data.currency,
                    asset_class=data.asset_class
                ))
            else:
                logger.warning(f"No data found for {symbol}")

        if not results:
            raise HTTPException(
                status_code=404,
                detail="No data found for any of the provided Hong Kong stock symbols"
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch stock data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch stock data: {str(e)}")

@app.get("/hsi/constituents", response_model=Dict[str, Any])
async def get_hsi_constituents():
    """獲取恆生指數成分股列表"""
    try:
        symbols = await hk_manager.get_hsi_constituents_data()

        return {
            "index": "Hang Seng Index (HSI)",
            "total_constituents": len(symbols),
            "symbols": symbols,
            "market": "Hong Kong",
            "exchange": "HKEX",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get HSI constituents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get HSI constituents: {str(e)}")

@app.get("/economic/hibor", response_model=EconomicDataResponse)
async def get_hibor_data():
    """獲取香港銀行同業拆息率 (HIBOR)"""
    try:
        data = await hk_manager.get_hkma_economic_data("hibor")

        return EconomicDataResponse(
            data_type="hibor",
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            value=data.get('value'),
            source=data.get('source', 'HKMA'),
            metadata=data.get('metadata')
        )

    except Exception as e:
        logger.error(f"Failed to get HIBOR data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get HIBOR data: {str(e)}")

@app.get("/economic/monetary-base", response_model=EconomicDataResponse)
async def get_monetary_base_data():
    """獲取香港貨幣基礎數據"""
    try:
        data = await hk_manager.get_hkma_economic_data("monetary")

        return EconomicDataResponse(
            data_type="monetary_base",
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            value=data.get('value'),
            source=data.get('source', 'HKMA'),
            metadata=data.get('metadata')
        )

    except Exception as e:
        logger.error(f"Failed to get monetary base data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monetary base data: {str(e)}")

@app.get("/economic/exchange-rate", response_model=EconomicDataResponse)
async def get_exchange_rate_data():
    """獲取香港匯率數據"""
    try:
        data = await hk_manager.get_hkma_economic_data("exchange")

        return EconomicDataResponse(
            data_type="exchange_rate",
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            value=data.get('value'),
            source=data.get('source', 'HKMA'),
            metadata=data.get('metadata')
        )

    except Exception as e:
        logger.error(f"Failed to get exchange rate data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get exchange rate data: {str(e)}")

@app.get("/market/summary", response_model=Dict[str, Any])
async def get_market_summary():
    """獲取香港市場摘要數據"""
    try:
        # 獲取主要藍籌股數據
        major_stocks = ["0700.HK", "0941.HK", "1299.HK", "2318.HK", "0388.HK"]
        stock_data = await hk_manager.get_hk_stock_data(major_stocks)

        # 獲取經濟數據
        hibor_data = await hk_manager.get_hkma_economic_data("hibor")
        monetary_data = await hk_manager.get_hkma_economic_data("monetary")
        exchange_data = await hk_manager.get_hkma_economic_data("exchange")

        # 獲取HSI成分股數量
        hsi_symbols = await hk_manager.get_hsi_constituents_data()

        return {
            "market": "Hong Kong",
            "exchange": "HKEX",
            "is_open": is_hk_market_open(),
            "major_stocks": {
                symbol: {
                    "price": data.close,
                    "change": data.close - data.open,
                    "change_percent": ((data.close - data.open) / data.open * 100) if data.open > 0 else 0,
                    "volume": data.volume
                } for symbol, data in stock_data.items()
            },
            "economic_indicators": {
                "hibor": hibor_data.get('value'),
                "monetary_base": monetary_data.get('value'),
                "exchange_rate": exchange_data.get('value')
            },
            "hsi_constituents_count": len(hsi_symbols),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get market summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market summary: {str(e)}")

@app.get("/search/symbols")
async def search_symbols(
    query: str = Query(..., min_length=1, description="搜索查詢，支持股票代碼或名稱"),
    limit: int = Query(10, ge=1, le=50, description="返回結果數量限制")
):
    """搜索香港股票符號"""
    try:
        # 獲取HSI成分股
        hsi_symbols = await hk_manager.get_hsi_constituents_data()

        # 簡單的搜索過濾
        query_lower = query.lower()
        matching_symbols = []

        for symbol in hsi_symbols:
            # 檢查代碼匹配
            if query_lower in symbol.lower():
                matching_symbols.append(symbol)
                continue

            # 這裡可以添加名稱匹配邏輯，如果有股票名稱數據庫
            # 目前只做代碼匹配

        # 限制結果數量
        results = matching_symbols[:limit]

        return {
            "query": query,
            "market": "Hong Kong",
            "total_matches": len(matching_symbols),
            "symbols": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to search symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search symbols: {str(e)}")

@app.post("/cache/clear")
async def clear_cache():
    """清除緩存"""
    try:
        hk_manager.clear_cache()
        return {
            "message": "Hong Kong market data cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.get("/data-sources/status", response_model=Dict[str, Any])
async def get_data_sources_status():
    """獲取數據源狀態"""
    try:
        status = hk_manager.get_source_status()
        health = await hk_manager.health_check()

        return {
            "data_sources": status,
            "overall_health": health,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get data sources status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data sources status: {str(e)}")

# 啟動和關閉事件
@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    logger.info("Hong Kong Market API starting up...")
    logger.info("Focus: Hong Kong Stock Exchange (HKEX) only")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    await hk_manager.close()
    logger.info("Hong Kong Market API shutdown complete")

# 運行API的函數
def run_api(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """運行香港市場API"""
    logger.info(f"Starting Hong Kong Market API on {host}:{port}")
    logger.info("Focus: Hong Kong Stock Exchange (HKEX) only")
    logger.info("API Documentation: http://localhost:8000/docs")

    uvicorn.run(
        "simplified_system.src.api.hk_market_api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

if __name__ == "__main__":
    run_api(debug=True)