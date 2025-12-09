"""
策略管理API路由
提供策略配置、管理和性能分析接口
"""

from datetime import datetime
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.auth import check_permissions, get_current_active_trader
from shared.models.schemas import StrategyConfig, StrategyPerformance, User

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/strategies", response_model=List[StrategyConfig])
async def get_strategies(
    current_user: User = Depends(check_permissions("read"))
):
    """獲取策略列表"""
    try:
        # 返回預定義的策略列表
        strategies = [
            StrategyConfig(
                name="RSI均倉策略",
                description="基於RSI指標的均倉策略",
                symbols=["0700.HK", "0941.HK", "1299.HK"],
                parameters={"rsi_period": 14, "oversold": 30, "overbought": 70},
                indicators=["rsi"],
                risk_limits={"max_position_size": 0.1, "stop_loss": -0.05},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            StrategyConfig(
                name="MACD趨勢策略",
                description="基於MACD指標的趨勢跟蹤策略",
                symbols=["0700.HK", "2318.HK"],
                parameters={"macd_fast": 12, "macd_slow": 26, "signal": 9},
                indicators=["macd"],
                risk_limits={"max_position_size": 0.15, "stop_loss": -0.08},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        return strategies

    except Exception as e:
        logger.error(f"獲取策略列表失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取策略列表失敗: {str(e)}"
        )