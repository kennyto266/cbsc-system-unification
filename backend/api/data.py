"""
数据API模块 - 提供股票数据相关接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from backend.services.data_service import DataService

router = APIRouter()

# 初始化数据服务
data_service = DataService()

@router.get("/stocks")
async def get_stocks():
    """获取股票列表"""
    try:
        stocks = data_service.get_popular_stocks()
        return {
            "success": True,
            "data": stocks,
            "message": "股票列表获取成功",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")

@router.get("/stocks/{symbol}")
async def get_stock_detail(symbol: str):
    """获取股票详情"""
    try:
        stock = data_service.get_stock_info(symbol)
        if not stock:
            # 尝试从API获取
            stock = data_service.fetch_stock_info(symbol)
            if not stock:
                raise HTTPException(status_code=404, detail="股票不存在")
        
        return {
            "success": True,
            "data": stock,
            "message": "股票详情获取成功",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票详情失败: {str(e)}")

@router.get("/stocks/{symbol}/data")
async def get_stock_data(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d"
):
    """获取股票历史数据"""
    try:
        # 使用数据服务获取数据
        data = data_service.fetch_stock_data(symbol, period, interval)
        
        if not data:
            raise HTTPException(status_code=404, detail="未找到股票数据")
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": data
            },
            "message": "股票数据获取成功",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")

@router.get("/stocks/{symbol}/info")
async def get_stock_info(symbol: str):
    """获取股票基本信息"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 提取关键信息
        stock_info = {
            "symbol": symbol,
            "name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "dividend_yield": info.get("dividendYield", 0),
            "currency": info.get("currency", "HKD"),
            "exchange": info.get("exchange", "HKEX")
        }
        
        return {
            "success": True,
            "data": stock_info,
            "message": "股票信息获取成功",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票信息失败: {str(e)}")

@router.get("/stocks/search")
async def search_stocks(q: str):
    """搜索股票"""
    try:
        stocks = data_service.search_stocks(q)
        return {
            "success": True,
            "data": stocks,
            "message": f"搜索到 {len(stocks)} 个结果",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索股票失败: {str(e)}")
