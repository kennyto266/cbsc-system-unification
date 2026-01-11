"""
回测API模块 - 提供批量策略回测相关接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

router = APIRouter()

@router.post("/tasks", status_code=201)
async def create_backtest(request: Dict[str, Any]):
    """创建回测任务"""
    try:
        symbol = request.get("symbol")
        strategy = request.get("strategy", {})
        start_date = request.get("start_date")
        end_date = request.get("end_date")

        if not symbol or not strategy:
            raise HTTPException(status_code=400, detail="缺少必要参数")

        # 模拟回测结果
        backtest_result = simulate_backtest(symbol, strategy, start_date, end_date)

        return {
            "success": True,
            "data": backtest_result,
            "message": "回测任务创建成功",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建回测任务失败: {str(e)}")

@router.get("/tasks")
async def get_backtests():
    """获取回测任务列表"""
    # 模拟回测任务列表
    backtests = [
        {
            "id": "bt_001",
            "symbol": "0700.HK",
            "strategy_name": "RSI策略",
            "status": "completed",
            "total_return": 15.6,
            "created_at": "2024-01-15T10:30:00Z",
            "completed_at": "2024-01-15T10:35:00Z"
        },
        {
            "id": "bt_002",
            "symbol": "9988.HK",
            "strategy_name": "移动平均策略",
            "status": "running",
            "progress": 65,
            "created_at": "2024-01-15T11:00:00Z",
            "completed_at": None
        },
        {
            "id": "bt_003",
            "symbol": "0941.HK",
            "strategy_name": "布林带策略",
            "status": "failed",
            "error": "数据不足",
            "created_at": "2024-01-15T09:45:00Z",
            "completed_at": "2024-01-15T09:50:00Z"
        }
    ]

    return {
        "success": True,
        "data": backtests,
        "message": "回测任务列表获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/tasks/{backtest_id}")
async def get_backtest(backtest_id: str):
    """获取特定回测任务详情"""
    # 模拟回测任务详情
    backtest = {
        "id": backtest_id,
        "symbol": "0700.HK",
        "strategy": {
            "type": "RSI",
            "parameters": {
                "period": 14,
                "oversold": 30,
                "overbought": 70
            }
        },
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "status": "completed",
        "progress": 100,
        "result": {
            "total_return": 15.6,
            "annual_return": 15.6,
            "max_drawdown": -8.2,
            "sharpe_ratio": 1.8,
            "win_rate": 65.5,
            "total_trades": 45,
            "profit_trades": 29,
            "loss_trades": 16,
            "avg_profit": 2.1,
            "avg_loss": -1.5,
            "profit_factor": 1.4
        },
        "created_at": "2024-01-15T10:30:00Z",
        "started_at": "2024-01-15T10:30:05Z",
        "completed_at": "2024-01-15T10:35:00Z",
        "execution_time": 295
    }

    return {
        "success": True,
        "data": backtest,
        "message": "回测任务详情获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/tasks/{backtest_id}")
async def delete_backtest(backtest_id: str):
    """删除回测任务"""
    # 模拟删除操作
    return {
        "success": True,
        "data": {"deleted": True, "id": backtest_id},
        "message": "回测任务删除成功",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/tasks/{backtest_id}/cancel")
async def cancel_backtest(backtest_id: str):
    """取消正在运行的回测任务"""
    # 模拟取消操作
    return {
        "success": True,
        "data": {"cancelled": True, "id": backtest_id},
        "message": "回测任务取消成功",
        "timestamp": datetime.now().isoformat()
    }

def simulate_backtest(symbol: str, strategy: Dict[str, Any], start_date: str, end_date: str) -> Dict[str, Any]:
    """模拟回测过程"""
    # 生成模拟的交易数据
    np.random.seed(42)
    dates = pd.date_range(start=start_date or "2024-01-01", end=end_date or "2024-12-31", freq='D')
    prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)

    # 模拟交易信号
    trades = []
    for i in range(20, len(prices)):
        if np.random.random() > 0.95:  # 5%概率产生交易信号
            trade = {
                "date": dates[i].isoformat(),
                "price": float(prices[i]),
                "action": "buy" if np.random.random() > 0.5 else "sell",
                "quantity": 100
            }
            trades.append(trade)

    # 计算回测指标
    total_trades = len(trades)
    profit_trades = len([t for t in trades if np.random.random() > 0.4])  # 60%胜率
    loss_trades = total_trades - profit_trades

    total_return = np.random.uniform(5, 25)  # 5-25%总收益
    max_drawdown = -np.random.uniform(5, 15)  # -5到-15%最大回撤
    sharpe_ratio = np.random.uniform(1.0, 2.5)  # 1.0-2.5夏普比率

    return {
        "id": f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "symbol": symbol,
        "strategy": strategy,
        "start_date": start_date or "2024-01-01",
        "end_date": end_date or "2024-12-31",
        "status": "completed",
        "progress": 100,
        "result": {
            "total_return": round(total_return, 2),
            "annual_return": round(total_return, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "win_rate": round(profit_trades / total_trades * 100, 1) if total_trades > 0 else 0,
            "total_trades": total_trades,
            "profit_trades": profit_trades,
            "loss_trades": loss_trades,
            "avg_profit": round(np.random.uniform(1.5, 3.0), 2),
            "avg_loss": round(-np.random.uniform(1.0, 2.0), 2),
            "profit_factor": round(np.random.uniform(1.2, 2.0), 2)
        },
        "trades": trades[:10],  # 只返回前10个交易
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "execution_time": np.random.randint(60, 600)  # 60-600秒执行时间
    }