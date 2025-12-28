"""
市场数据API模块 - 提供市场数据相关接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
try:
    from services.data_service import DataService
except ImportError:
    # 为开发环境设置基本导入
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from services.data_service import DataService

router = APIRouter()

# 初始化数据服务
data_service = DataService()

@router.get("/symbols")
async def get_market_symbols():
    """获取市场交易品种列表"""
    try:
        symbols = data_service.get_popular_stocks()
        return {
            "success": True,
            "data": symbols,
            "message": "交易品种列表获取成功",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易品种列表失败: {str(e)}")

@router.get("/symbols/{symbol}")
async def get_symbol_detail(symbol: str):
    """获取交易品种详情"""
    try:
        stock = data_service.get_stock_info(symbol)
        if not stock:
            # 尝试从API获取
            stock = data_service.fetch_stock_info(symbol)
            if not stock:
                raise HTTPException(status_code=404, detail="交易品种不存在")

        return {
            "success": True,
            "data": stock,
            "message": "交易品种详情获取成功",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易品种详情失败: {str(e)}")

@router.get("/symbols/{symbol}/data")
async def get_symbol_data(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d"
):
    """获取交易品种历史数据"""
    try:
        # 使用数据服务获取数据
        data = data_service.fetch_stock_data(symbol, period, interval)

        if not data:
            raise HTTPException(status_code=404, detail="未找到交易品种数据")

        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": data
            },
            "message": "交易品种数据获取成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易品种数据失败: {str(e)}")

@router.get("/symbols/{symbol}/quote")
async def get_symbol_quote(symbol: str):
    """获取交易品种实时报价"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # 提取关键报价信息
        quote = {
            "symbol": symbol,
            "name": info.get("longName", ""),
            "current_price": info.get("currentPrice", 0),
            "open_price": info.get("open", 0),
            "high_price": info.get("dayHigh", 0),
            "low_price": info.get("dayLow", 0),
            "volume": info.get("volume", 0),
            "previous_close": info.get("previousClose", 0),
            "change": info.get("currentPrice", 0) - info.get("previousClose", 0),
            "change_percent": ((info.get("currentPrice", 0) - info.get("previousClose", 0)) / info.get("previousClose", 1)) * 100,
            "currency": info.get("currency", "HKD"),
            "exchange": info.get("exchange", "HKEX"),
            "market_cap": info.get("marketCap", 0)
        }

        return {
            "success": True,
            "data": quote,
            "message": "实时报价获取成功",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实时报价失败: {str(e)}")

@router.get("/symbols/search")
async def search_symbols(q: str):
    """搜索交易品种"""
    try:
        stocks = data_service.search_stocks(q)
        return {
            "success": True,
            "data": stocks,
            "message": f"搜索到 {len(stocks)} 个结果",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索交易品种失败: {str(e)}")

@router.get("/symbols/{symbol}/historical")
async def get_historical_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "1d"
):
    """获取历史数据"""
    try:
        # 如果没有提供日期，则使用默认值
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # 尝试从数据库获取
        data = data_service.get_market_data(symbol, start_date, end_date)

        # 如果数据库中没有数据，则从API获取
        if not data:
            # 计算period
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            days_diff = (end_dt - start_dt).days

            if days_diff <= 30:
                period = "1mo"
            elif days_diff <= 90:
                period = "3mo"
            elif days_diff <= 180:
                period = "6mo"
            elif days_diff <= 365:
                period = "1y"
            else:
                period = "2y"

            data = data_service.fetch_stock_data(symbol, period, interval)

        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval,
                "data": data
            },
            "message": "历史数据获取成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")