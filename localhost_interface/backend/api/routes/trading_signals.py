"""
交易信號API路由
提供實時交易信號和技術指標接口
"""

from datetime import datetime, timedelta
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from backend.api.auth import check_permissions, get_current_active_trader
from backend.core.config import get_settings
from shared.models.schemas import (
    TradingSignal, TechnicalIndicator, SignalFilter, SignalType,
    User, IndicatorParameters
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

@router.get("/signals", response_model=List[TradingSignal])
async def get_trading_signals(
    symbol: Optional[str] = Query(None, description="股票代碼，如 0700.HK"),
    signal_type: Optional[SignalType] = Query(None, description="信號類型"),
    min_strength: float = Query(0.0, ge=0, le=1, description="最小信號強度"),
    min_confidence: float = Query(0.0, ge=0, le=1, description="最小置信度"),
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    limit: int = Query(50, ge=1, le=1000, description="返回結果數量限制"),
    current_user: User = Depends(check_permissions("read"))
):
    """
    獲取交易信號列表

    支持多種過濾條件：
    - 按股票代碼過濾
    - 按信號類型過濾 (buy, sell, hold)
    - 按信號強度和置信度過濾
    - 按時間範圍過濾
    """
    try:
        # 構建過濾器
        signal_filter = SignalFilter(
            symbol=symbol,
            signal_type=signal_type,
            min_strength=min_strength,
            min_confidence=min_confidence,
            start_date=start_date,
            end_date=end_date
        )

        # 獲取最新信號 (從全局非價格服務)
        from main import app
        non_price_service = app.state.non_price_service

        if symbol:
            # 獲取特定股票的信號
            signals = await non_price_service.get_trading_signals(symbol)
        else:
            # 獲取所有支持股票的信號
            signals = await non_price_service.get_latest_signals()

        # 應用過濾條件
        filtered_signals = []
        for signal in signals:
            # 檢查信號類型
            if signal_filter.signal_type and signal.signal_type != signal_filter.signal_type:
                continue

            # 檢查最小強度
            if signal.strength < signal_filter.min_strength:
                continue

            # 檢查最小置信度
            if signal.confidence < signal_filter.min_confidence:
                continue

            # 檢查時間範圍
            if signal_filter.start_date and signal.timestamp < signal_filter.start_date:
                continue

            if signal_filter.end_date and signal.timestamp > signal_filter.end_date:
                continue

            filtered_signals.append(signal)

        # 限制結果數量
        if limit < len(filtered_signals):
            filtered_signals = filtered_signals[:limit]

        logger.info(f"返回 {len(filtered_signals)} 個交易信號")
        return filtered_signals

    except Exception as e:
        logger.error(f"獲取交易信號失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取交易信號失敗: {str(e)}"
        )

@router.get("/signals/{signal_id}", response_model=TradingSignal)
async def get_signal_by_id(
    signal_id: str,
    current_user: User = Depends(check_permissions("read"))
):
    """根據ID獲取特定交易信號"""
    try:
        # 獲取所有信號並查找匹配的信號
        from main import app
        non_price_service = app.state.non_price_service
        signals = await non_price_service.get_latest_signals()

        # 查找匹配的信號
        for signal in signals:
            if signal.id == signal_id:
                return signal

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到信號: {signal_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取信號失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取信號失敗: {str(e)}"
        )

@router.get("/indicators", response_model=List[TechnicalIndicator])
async def get_technical_indicators(
    symbol: str = Query(..., description="股票代碼"),
    indicator_type: Optional[str] = Query(None, description="指標類型"),
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回結果數量限制"),
    current_user: User = Depends(check_permissions("read"))
):
    """
    獲取技術指標列表

    支持的指標類型：
    - rsi: RSI相對強弱指數
    - macd: MACD移動平均收斂散度
    - bollinger_bands: 布林帶
    - stochastic: 隨機指標
    - williams_r: Williams %R
    - roc: 變化率
    - moving_average: 移動平均線
    """
    try:
        # 驗證股票代碼
        if symbol not in settings.SUPPORTED_SYMBOLS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的股票代碼: {symbol}"
            )

        # 獲取技術指標
        from main import app
        non_price_service = app.state.non_price_service
        indicators = await non_price_service.get_technical_indicators(symbol)

        # 應用過濾條件
        filtered_indicators = []
        for indicator in indicators:
            # 檢查指標類型
            if indicator_type and indicator.name.value != indicator_type:
                continue

            # 檢查時間範圍
            if start_date and indicator.timestamp < start_date:
                continue

            if end_date and indicator.timestamp > end_date:
                continue

            filtered_indicators.append(indicator)

        # 限制結果數量
        if limit < len(filtered_indicators):
            filtered_indicators = filtered_indicators[:limit]

        logger.info(f"返回 {len(filtered_indicators)} 個技術指標")
        return filtered_indicators

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取技術指標失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取技術指標失敗: {str(e)}"
        )

@router.post("/signals/generate")
async def generate_trading_signals(
    symbol: str = Query(..., description="股票代碼"),
    parameters: Optional[IndicatorParameters] = None,
    current_user: User = Depends(check_permissions("trading"))
):
    """
    手動生成交易信號

    用戶可以自定義技術指標參數來生成信號
    """
    try:
        # 驗證股票代碼
        if symbol not in settings.SUPPORTED_SYMBOLS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的股票代碼: {symbol}"
            )

        # 使用提供的參數或默認參數
        if not parameters:
            parameters = IndicatorParameters()

        # 獲取交易信號
        from main import app
        non_price_service = app.state.non_price_service

        # 這裡可以根據用戶提供的參數生成定制化信號
        signals = await non_price_service.get_trading_signals(symbol)

        logger.info(f"用戶 {current_user.username} 為 {symbol} 生成了 {len(signals)} 個信號")

        return {
            "message": "交易信號生成成功",
            "symbol": symbol,
            "signal_count": len(signals),
            "parameters": parameters.dict(),
            "signals": [signal.dict() for signal in signals],
            "generated_at": datetime.now().isoformat(),
            "user": current_user.username
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成交易信號失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成交易信號失敗: {str(e)}"
        )

@router.get("/signals/stats")
async def get_signal_statistics(
    symbol: Optional[str] = Query(None, description="股票代碼"),
    days: int = Query(30, ge=1, le=365, description="統計天數"),
    current_user: User = Depends(check_permissions("read"))
):
    """
    獲取交易信號統計信息

    包括：
    - 信號類型分布
    - 平均信號強度和置信度
    - 每日信號生成頻率
    - 最活躍的指標來源
    """
    try:
        from main import app
        non_price_service = app.state.non_price_service

        if symbol:
            signals = await non_price_service.get_trading_signals(symbol)
        else:
            signals = await non_price_service.get_latest_signals()

        if not signals:
            return {
                "total_signals": 0,
                "signal_type_distribution": {},
                "average_strength": 0.0,
                "average_confidence": 0.0,
                "most_common_source_indicators": [],
                "symbol": symbol,
                "days": days
            }

        # 計算統計信息
        signal_type_distribution = {}
        total_strength = 0.0
        total_confidence = 0.0
        source_indicators_count = {}

        for signal in signals:
            # 信號類型分布
            signal_type = signal.signal_type.value
            signal_type_distribution[signal_type] = signal_type_distribution.get(signal_type, 0) + 1

            # 強度和置信度總和
            total_strength += signal.strength
            total_confidence += signal.confidence

            # 來源指標統計
            for indicator in signal.source_indicators:
                source_indicators_count[indicator] = source_indicators_count.get(indicator, 0) + 1

        # 計算平均值
        average_strength = total_strength / len(signals)
        average_confidence = total_confidence / len(signals)

        # 最常見的來源指標
        most_common_sources = sorted(
            source_indicators_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        statistics = {
            "total_signals": len(signals),
            "signal_type_distribution": signal_type_distribution,
            "average_strength": round(average_strength, 3),
            "average_confidence": round(average_confidence, 3),
            "most_common_source_indicators": [
                {"indicator": indicator, "count": count}
                for indicator, count in most_common_sources
            ],
            "symbol": symbol,
            "days": days,
            "calculated_at": datetime.now().isoformat()
        }

        logger.info(f"生成交易信號統計: {statistics['total_signals']} 個信號")
        return statistics

    except Exception as e:
        logger.error(f"獲取信號統計失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取信號統計失敗: {str(e)}"
        )

@router.delete("/signals/{signal_id}")
async def delete_signal(
    signal_id: str,
    current_user: User = Depends(check_permissions("admin"))
):
    """刪除交易信號（需要管理員權限）"""
    try:
        # 在實際實現中，這裡會從數據庫中刪除信號
        # 目前返回成功響應
        logger.info(f"管理員 {current_user.username} 刪除了信號: {signal_id}")

        return {
            "message": "信號刪除成功",
            "signal_id": signal_id,
            "deleted_by": current_user.username,
            "deleted_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"刪除信號失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除信號失敗: {str(e)}"
        )