"""
Dashboard API - Provides mock data for frontend dashboard
Dashboard API - 為前端儀表板提供模擬數據
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

router = APIRouter(tags=["Dashboard"])


@router.get("/api/v1/dashboard/overview")
async def get_dashboard_overview() -> Dict[str, Any]:
    """
    Get dashboard overview data
    獲取儀表板概覽數據
    """
    return {
        "success": True,
        "data": {
            "performance": {
                "today_return": random.uniform(-0.05, 0.08),  # -5% to +8%
                "weekly_return": random.uniform(-0.15, 0.20),
                "monthly_return": random.uniform(-0.30, 0.40),
                "total_return": random.uniform(-0.50, 1.50)
            },
            "system_health": {
                "api_status": "正常",
                "database_status": "連接正常",
                "cache_status": "運行中",
                "vectorbt_status": "已安裝 v0.28.2",
                "last_update": datetime.now().isoformat()
            },
            "active_strategies": random.randint(5, 15),
            "total_trades_today": random.randint(10, 100),
            "win_rate": round(random.uniform(0.45, 0.65), 2)
        }
    }


@router.get("/api/v1/strategies")
async def get_strategies() -> Dict[str, Any]:
    """
    Get list of strategies (without authentication for development)
    獲取策略列表（開發環境無需認證）
    """
    strategies = [
        {
            "id": 1,
            "name": "MA_Crossover_5_20",
            "type": "移動平均交叉",
            "status": "活躍",
            "return": 12.5,
            "sharpe_ratio": 1.8,
            "max_drawdown": -8.3,
            "created_at": "2024-12-01T10:00:00Z"
        },
        {
            "id": 2,
            "name": "RSI_Mean_Reversion",
            "type": "RSI均值回歸",
            "status": "活躍",
            "return": 8.7,
            "sharpe_ratio": 1.4,
            "max_drawdown": -5.2,
            "created_at": "2024-12-05T14:30:00Z"
        },
        {
            "id": 3,
            "name": "Bollinger_Bands",
            "type": "布林帶策略",
            "status": "測試中",
            "return": -2.1,
            "sharpe_ratio": 0.6,
            "max_drawdown": -12.8,
            "created_at": "2024-12-10T09:15:00Z"
        },
        {
            "id": 4,
            "name": "MACD_Momentum",
            "type": "MACD動量",
            "status": "活躍",
            "return": 15.3,
            "sharpe_ratio": 2.1,
            "max_drawdown": -6.7,
            "created_at": "2024-12-12T16:45:00Z"
        },
        {
            "id": 5,
            "name": "VectorBT_MA_Strategy",
            "type": "VectorBT移動平均",
            "status": "活躍",
            "return": 22.8,
            "sharpe_ratio": 2.5,
            "max_drawdown": -4.5,
            "created_at": "2024-12-20T11:00:00Z"
        }
    ]

    return {
        "success": True,
        "data": strategies
    }


@router.get("/api/v1/economic-data")
async def get_economic_data() -> Dict[str, Any]:
    """
    Get economic indicators data
    獲取經濟指標數據
    """
    base_date = datetime.now() - timedelta(days=90)

    # Generate mock economic data for the last 90 days
    dates = []
    hibor_rates = []
    monetary_base = []
    for i in range(90):
        date = base_date + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
        hibor_rates.append(round(random.uniform(3.0, 5.5), 2))
        monetary_base.append(round(random.uniform(1800, 2200), 2))

    return {
        "success": True,
        "data": {
            "hibor": {
                "dates": dates,
                "rates": hibor_rates,
                "current_rate": hibor_rates[-1]
            },
            "monetary": {
                "dates": dates,
                "base": monetary_base,
                "current_base": monetary_base[-1]
            },
            "last_update": datetime.now().isoformat()
        }
    }


@router.get("/api/v1/market/status")
async def get_market_status() -> Dict[str, Any]:
    """
    Get current market status
    獲取當前市場狀態
    """
    return {
        "success": True,
        "data": {
            "market_status": "開盤" if random.random() > 0.3 else "休市",
            "index_value": round(random.uniform(17500, 18500), 2),
            "index_change": round(random.uniform(-500, 500), 2),
            "volume": random.randint(80, 150)  # Billion HKD
        }
    }


@router.get("/api/v1/backtest/history")
async def get_backtest_history() -> Dict[str, Any]:
    """
    Get backtest history
    獲取回測歷史
    """
    return {
        "success": True,
        "data": {
            "recent_backtests": [
                {
                    "id": "bt_001",
                    "strategy_name": "MA_Crossover_5_20",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-20",
                    "return": 22.8,
                    "sharpe_ratio": 2.5,
                    "max_drawdown": -4.5,
                    "status": "完成",
                    "created_at": "2024-12-26T10:30:00Z"
                },
                {
                    "id": "bt_002",
                    "strategy_name": "RSI_Mean_Reversion",
                    "start_date": "2024-06-01",
                    "end_date": "2024-12-20",
                    "return": -5.2,
                    "sharpe_ratio": 0.8,
                    "max_drawdown": -15.3,
                    "status": "完成",
                    "created_at": "2024-12-25T15:20:00Z"
                }
            ],
            "total_count": 2
        }
    }
