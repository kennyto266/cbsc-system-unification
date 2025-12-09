"""
風險管理API路由
提供風險監控、警報和控制接口
"""

from datetime import datetime
from typing import List
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import check_permissions, get_current_active_trader
from shared.models.schemas import RiskMetrics, RiskAlert, User

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/metrics", response_model=List[RiskMetrics])
async def get_risk_metrics(
    current_user: User = Depends(check_permissions("risk_management"))
):
    """獲取風險指標"""
    try:
        # 返回模擬的風險指標
        metrics = [
            RiskMetrics(
                symbol="0700.HK",
                timestamp=datetime.now(),
                current_position=100000,
                unrealized_pnl=2500,
                realized_pnl=1200,
                daily_var=5000,
                portfolio_var=15000,
                position_limit=200000,
                loss_limit=10000,
                var_limit=8000,
                risk_level="MEDIUM",
                warnings=["VaR接近上限"],
                stop_loss=385.0,
                take_profit=450.0
            )
        ]

        return metrics

    except Exception as e:
        logger.error(f"獲取風險指標失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取風險指標失敗: {str(e)}"
        )