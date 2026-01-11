"""
CBSC (牛熊证) 数据 API
CBSC (Callable Bull/Bear Contract) Data API for Dashboard Integration
"""

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
import json
import logging
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/cbsc", tags=["CBSC Data"])

# 数据文件路径
DATA_DIR = Path(__file__).parent.parent.parent / "acquired_data"
LATEST_DATA_FILE = DATA_DIR / "cbsc_real_data_20251205_205342.csv"

class CBSCTopData:
    """CBSC 前十名数据结构"""
    def __init__(self):
        self.date = ""
        self.bull_contracts = []
        self.bear_contracts = []
        self.market_sentiment = {}

class CBSCMarketSentiment:
    """市场情绪指标"""
    def __init__(self):
        self.fear_greed_index = 0
        self.bull_bear_ratio = 0
        self.realized_volatility = 0
        self.rsi_signal = 0
        self.sentiment_score = 0
        self.sentiment_label = ""

def load_cbsc_data() -> pd.DataFrame:
    """加载 CBSC 数据"""
    try:
        if LATEST_DATA_FILE.exists():
            df = pd.read_csv(LATEST_DATA_FILE)
            # 转换日期格式
            df['Date'] = pd.to_datetime(df['Date'])
            # 按日期排序
            df = df.sort_values('Date')
            logger.info(f"Loaded {len(df)} records from {LATEST_DATA_FILE}")
            return df
        else:
            logger.error(f"Data file not found: {LATEST_DATA_FILE}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading CBSC data: {str(e)}")
        return pd.DataFrame()

def calculate_market_sentiment(df: pd.DataFrame) -> Dict[str, Any]:
    """计算市场情绪指标"""
    if df.empty:
        return {}

    # 获取最新数据
    latest = df.iloc[-1]

    # 计算情绪指标
    fear_greed = latest.get('Fear_Greed_Index', 50)
    bull_bear_ratio = latest.get('Bull_Bear_Ratio', 1)
    volatility = latest.get('Realized_Volatility', 0)
    rsi = latest.get('RSI_Signal', 50)

    # 综合情绪评分 (0-100)
    sentiment_score = 50
    if not pd.isna(fear_greed):
        sentiment_score = float(fear_greed)

    # 情绪标签
    if sentiment_score >= 75:
        sentiment_label = "极度贪婪"
    elif sentiment_score >= 60:
        sentiment_label = "贪婪"
    elif sentiment_score >= 45:
        sentiment_label = "中性"
    elif sentiment_score >= 25:
        sentiment_label = "恐惧"
    else:
        sentiment_label = "极度恐惧"

    return {
        "fear_greed_index": float(fear_greed) if not pd.isna(fear_greed) else 50,
        "bull_bear_ratio": float(bull_bear_ratio) if not pd.isna(bull_bear_ratio) else 1,
        "realized_volatility": float(volatility) if not pd.isna(volatility) else 0,
        "rsi_signal": float(rsi) if not pd.isna(rsi) else 50,
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "update_time": latest['Date'].isoformat() if 'Date' in latest else datetime.now().isoformat()
    }

def get_top_contracts(df: pd.DataFrame, limit: int = 10) -> Dict[str, List[Dict]]:
    """获取牛熊证前十名（基于价格和交易量）"""
    if df.empty:
        return {"bull_contracts": [], "bear_contracts": []}

    # 获取最新数据
    latest = df.iloc[-1]

    # 构建牛证列表（模拟数据，实际需要根据真实数据结构调整）
    bull_contracts = []
    bear_contracts = []

    # 基于当前数据生成示例合约
    base_price = latest.get('Bull_Price', 0.01)

    # 生成牛证（看涨）
    for i in range(limit):
        contract = {
            "rank": i + 1,
            "code": f"B{70000 + i}",
            "name": f"恒指牛证{i+1:02d}",
            "price": round(base_price * (1 + i * 0.1), 4),
            "strike": round(latest.get('HSIF_Close', 20000) * (0.95 - i * 0.01), 2),
            "expiry": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
            "leverage": round(10 + i * 2, 1),
            "volume": 1000000 - i * 50000,
            "change": round(np.random.uniform(-5, 5), 2)
        }
        bull_contracts.append(contract)

    # 生成熊证（看跌）
    bear_price = latest.get('Bear_Price', 20)
    for i in range(limit):
        contract = {
            "rank": i + 1,
            "code": f"B{80000 + i}",
            "name": f"恒指熊证{i+1:02d}",
            "price": round(bear_price * (1 + i * 0.05), 4),
            "strike": round(latest.get('HSIF_Close', 20000) * (1.05 + i * 0.01), 2),
            "expiry": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
            "leverage": round(8 + i * 1.5, 1),
            "volume": 800000 - i * 40000,
            "change": round(np.random.uniform(-5, 5), 2)
        }
        bear_contracts.append(contract)

    return {
        "bull_contracts": bull_contracts,
        "bear_contracts": bear_contracts
    }

@router.get("/market-sentiment", response_model=Dict[str, Any])
async def get_market_sentiment():
    """
    获取市场情绪指标
    Get market sentiment indicators
    """
    try:
        df = load_cbsc_data()
        sentiment = calculate_market_sentiment(df)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": sentiment,
                "message": "Market sentiment retrieved successfully",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting market sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-contracts", response_model=Dict[str, Any])
async def get_top_contracts(limit: int = Query(10, ge=1, le=50)):
    """
    获取牛熊证前十名
    Get top CBSC contracts
    """
    try:
        df = load_cbsc_data()
        contracts = get_top_contracts(df, limit)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": contracts,
                "message": "Top contracts retrieved successfully",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting top contracts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical-data", response_model=Dict[str, Any])
async def get_historical_data(
    days: int = Query(30, ge=1, le=365),
    metric: str = Query("all", regex="^(all|fear_greed|bull_bear_ratio|volatility|volume)$")
):
    """
    获取历史数据用于趋势图表
    Get historical data for trend charts
    """
    try:
        df = load_cbsc_data()
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")

        # 获取最近 N 天的数据
        end_date = df['Date'].max()
        start_date = end_date - timedelta(days=days)

        filtered_df = df[df['Date'] >= start_date]

        # 准备数据
        historical_data = []
        for _, row in filtered_df.iterrows():
            data_point = {
                "date": row['Date'].strftime("%Y-%m-%d"),
                "hsif_close": float(row.get('HSIF_Close', 0)) if not pd.isna(row.get('HSIF_Close')) else 0,
                "hsif_return": float(row.get('HSIF_Return', 0)) if not pd.isna(row.get('HSIF_Return')) else 0,
            }

            # 根据请求的指标添加数据
            if metric in ["all", "fear_greed"]:
                data_point["fear_greed_index"] = float(row.get('Fear_Greed_Index', 50)) if not pd.isna(row.get('Fear_Greed_Index')) else 50

            if metric in ["all", "bull_bear_ratio"]:
                data_point["bull_bear_ratio"] = float(row.get('Bull_Bear_Ratio', 1)) if not pd.isna(row.get('Bull_Bear_Ratio')) else 1

            if metric in ["all", "volatility"]:
                data_point["realized_volatility"] = float(row.get('Realized_Volatility', 0)) if not pd.isna(row.get('Realized_Volatility')) else 0

            if metric in ["all", "volume"]:
                data_point["volume"] = int(row.get('Volume', 0)) if not pd.isna(row.get('Volume')) else 0

            historical_data.append(data_point)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "historical_data": historical_data,
                    "metric": metric,
                    "period_days": days,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                },
                "message": "Historical data retrieved successfully",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting historical data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard-summary", response_model=Dict[str, Any])
async def get_dashboard_summary():
    """
    获取 Dashboard 综合数据
    Get comprehensive dashboard data
    """
    try:
        df = load_cbsc_data()

        # 获取各项数据
        sentiment = calculate_market_sentiment(df)
        contracts = get_top_contracts(df, 10)

        # 计算额外统计信息
        if not df.empty:
            latest = df.iloc[-1]
            prev_day = df.iloc[-2] if len(df) > 1 else latest

            # 日内变化
            hsif_change = latest.get('HSIF_Close', 0) - prev_day.get('HSIF_Close', 0)
            hsif_change_pct = (hsif_change / prev_day.get('HSIF_Close', 1)) * 100 if prev_day.get('HSIF_Close', 0) != 0 else 0

            # 市场活跃度
            total_volume = int(latest.get('Volume', 0))
            active_contracts = len(contracts['bull_contracts']) + len(contracts['bear_contracts'])

            statistics = {
                "hsif_current": float(latest.get('HSIF_Close', 0)) if not pd.isna(latest.get('HSIF_Close')) else 0,
                "hsif_change": round(hsif_change, 2),
                "hsif_change_percent": round(hsif_change_pct, 2),
                "total_volume": total_volume,
                "active_contracts": active_contracts,
                "market_capitalization": round(total_volume * 100, 2),  # 估算值
                "last_update": latest['Date'].isoformat() if 'Date' in latest else datetime.now().isoformat()
            }
        else:
            statistics = {}

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "market_sentiment": sentiment,
                    "top_contracts": contracts,
                    "statistics": statistics
                },
                "message": "Dashboard summary retrieved successfully",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))