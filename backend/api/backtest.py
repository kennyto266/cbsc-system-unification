"""
回测API模块 - 提供策略回测相关接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

router = APIRouter()

@router.post("/strategy")
async def backtest_strategy(request: Dict[str, Any]):
    """策略回测"""
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
            "message": "策略回测完成",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略回测失败: {str(e)}")

@router.get("/results/{result_id}")
async def get_backtest_result(result_id: str):
    """获取回测结果"""
    # 模拟回测结果
    result = {
        "result_id": result_id,
        "symbol": "0700.HK",
        "strategy_name": "移动平均策略",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
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
        "profit_factor": 1.4,
        "status": "completed",
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "data": result,
        "message": "回测结果获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/strategies")
async def get_strategies():
    """获取可用策略列表"""
    strategies = [
        {
            "id": "ma_cross",
            "name": "移动平均交叉策略",
            "description": "基于短期和长期移动平均线交叉的交易策略",
            "parameters": {
                "short_period": {"type": "int", "default": 20, "min": 5, "max": 50},
                "long_period": {"type": "int", "default": 50, "min": 20, "max": 200}
            }
        },
        {
            "id": "rsi_oversold",
            "name": "RSI超卖策略",
            "description": "基于RSI指标的超买超卖交易策略",
            "parameters": {
                "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 30},
                "oversold_level": {"type": "float", "default": 30, "min": 10, "max": 40},
                "overbought_level": {"type": "float", "default": 70, "min": 60, "max": 90}
            }
        },
        {
            "id": "bollinger_bands",
            "name": "布林带策略",
            "description": "基于布林带的价格突破交易策略",
            "parameters": {
                "period": {"type": "int", "default": 20, "min": 10, "max": 50},
                "std_dev": {"type": "float", "default": 2, "min": 1, "max": 3}
            }
        }
    ]
    
    return {
        "success": True,
        "data": strategies,
        "message": "策略列表获取成功",
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
        "symbol": symbol,
        "strategy_name": strategy.get("name", "自定义策略"),
        "start_date": start_date or "2024-01-01",
        "end_date": end_date or "2024-12-31",
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
        "profit_factor": round(np.random.uniform(1.2, 2.0), 2),
        "trades": trades[:10],  # 只返回前10个交易
        "status": "completed"
    }
