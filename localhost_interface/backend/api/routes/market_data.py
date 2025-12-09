"""
市場數據API路由
提供實時市場數據和非價格信號接口
"""

from datetime import datetime
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.api.auth import check_permissions, get_current_active_trader
from shared.models.schemas import MarketDataPoint, NonPriceData, DataSourceType, User

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/price", response_model=List[MarketDataPoint])
async def get_market_data(
    symbol: Optional[str] = Query(None, description="股票代碼"),
    current_user: User = Depends(check_permissions("read"))
):
    """獲取市場價格數據"""
    try:
        # 返回模擬的市場數據
        data_points = [
            MarketDataPoint(
                symbol=symbol or "0700.HK",
                timestamp=datetime.now(),
                price=398.50,
                volume=1500000,
                high=401.20,
                low=395.80,
                open=399.00,
                close=398.50
            )
        ]

        return data_points

    except Exception as e:
        logger.error(f"獲取市場數據失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取市場數據失敗: {str(e)}"
        )

@router.get("/non-price", response_model=List[NonPriceData])
async def get_non_price_data(
    source_type: Optional[DataSourceType] = Query(None, description="數據源類型"),
    current_user: User = Depends(check_permissions("read"))
):
    """獲取非價格信號數據"""
    try:
        # 獲取最新的非價格數據
        from main import app
        non_price_service = app.state.non_price_service

        if source_type:
            non_price_data = await non_price_service.get_latest_data([source_type])
        else:
            non_price_data = await non_price_service.get_latest_data()

        return non_price_data

    except Exception as e:
        logger.error(f"獲取非價格數據失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取非價格數據失敗: {str(e)}"
        )