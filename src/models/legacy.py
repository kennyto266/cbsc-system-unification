"""
Legacy兼容性模型

為現有代碼提供兼容性支持，逐步遷移到新的統一模型。
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from .base import (
    MarketData as LegacyBaseMarketData,
    TradingSignal,
    Portfolio as LegacyBasePortfolio,
    RiskMetrics,
    Holding,
    PerformanceMetrics as LegacyPerformanceMetrics
)

# Re-export legacy models with new naming for compatibility
MarketData = LegacyBaseMarketData
Portfolio = LegacyBasePortfolio

class SignalType(str, Enum):
    """交易信號類型 (兼容舊版)"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class AgentStatus(str, Enum):
    """Agent狀態 (兼容舊版)"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"

class MessageType(str, Enum):
    """消息類型 (兼容舊版)"""
    SIGNAL = "signal"
    DATA = "data"
    CONTROL = "control"
    HEARTBEAT = "heartbeat"

# Legacy compatibility adapters
class LegacyDataAdapter:
    """舊版數據適配器

    提供舊版模型和新版統一模型之間的轉換功能。
    """

    @staticmethod
    def market_data_to_unified(legacy_market_data: MarketData) -> Dict[str, Any]:
        """將舊版市場數據轉換為統一格式"""
        return {
            "symbol": legacy_market_data.symbol,
            "timestamp": legacy_market_data.timestamp,
            "timeframe": "1d",  # 默認值
            "open_price": float(legacy_market_data.open_price),
            "high_price": float(legacy_market_data.high_price),
            "low_price": float(legacy_market_data.low_price),
            "close_price": float(legacy_market_data.close_price),
            "volume": legacy_market_data.volume,
            "turnover": float(legacy_market_data.turnover) if legacy_market_data.turnover else None,
            "exchange": "HKEX",  # 默認值
            "asset_type": "stock",
            "data_source": "legacy",
            "quality_score": 1.0,
            "is_adjusted": False
        }

    @staticmethod
    def trading_signal_to_unified(legacy_signal: TradingSignal) -> Dict[str, Any]:
        """將舊版交易信號轉換為統一格式"""
        return {
            "symbol": legacy_signal.symbol,
            "timestamp": legacy_signal.timestamp,
            "indicator_type": "signal",
            "indicator_name": "trading_signal",
            "signal": legacy_signal.signal_type.value,
            "values": {
                "strength": legacy_signal.strength,
                "price": float(legacy_signal.price)
            },
            "parameters": legacy_signal.metadata,
            "confidence": min(1.0, abs(legacy_signal.strength)),
            "strength": abs(legacy_signal.strength)
        }

    @staticmethod
    def portfolio_to_unified(legacy_portfolio: Portfolio) -> Dict[str, Any]:
        """將舊版投資組合轉換為統一格式"""
        return {
            "name": "Legacy Portfolio",
            "portfolio_type": "discretionary",
            "cash_balance": float(legacy_portfolio.cash),
            "total_value": float(legacy_portfolio.total_value) if legacy_portfolio.total_value else float(legacy_portfolio.cash),
            "total_positions": len(legacy_portfolio.holdings),
            "active_positions": len([h for h in legacy_portfolio.holdings if h.quantity != 0]),
            "inception_date": datetime.now(),
            "is_active": True
        }

    @staticmethod
    def holding_to_position(legacy_holding: Holding, portfolio_id: str) -> Dict[str, Any]:
        """將舊版持倉轉換為統一持倉格式"""
        return {
            "portfolio_id": portfolio_id,
            "symbol": legacy_holding.symbol,
            "exchange": "HKEX",
            "asset_type": "stock",
            "side": "long" if legacy_holding.quantity > 0 else "short",
            "quantity": abs(legacy_holding.quantity),
            "average_cost": float(legacy_holding.entry_price),
            "total_cost": float(legacy_holding.entry_price * abs(legacy_holding.quantity)),
            "current_price": float(legacy_holding.current_price) if legacy_holding.current_price else None,
            "market_value": float(legacy_holding.market_value) if legacy_holding.market_value else None,
            "unrealized_pnl": float(legacy_holding.unrealized_pnl) if legacy_holding.unrealized_pnl else None,
            "first_opened": legacy_holding.entry_date,
            "last_updated": datetime.now()
        }

class MigrationHelper:
    """數據遷移輔助工具"""

    @staticmethod
    def validate_legacy_data(data: Any, data_type: str) -> tuple[bool, Optional[str]]:
        """驗證舊版數據格式"""
        try:
            if data_type == "market_data":
                required_fields = ["symbol", "timestamp", "open_price", "high_price", "low_price", "close_price", "volume"]
                for field in required_fields:
                    if not hasattr(data, field) or getattr(data, field) is None:
                        return False, f"Missing required field: {field}"

                # 檢查價格合理性
                if data.high_price < data.low_price:
                    return False, "High price cannot be lower than low price"
                if data.open_price < data.low_price or data.open_price > data.high_price:
                    return False, "Open price outside high-low range"
                if data.close_price < data.low_price or data.close_price > data.high_price:
                    return False, "Close price outside high-low range"

            elif data_type == "trading_signal":
                required_fields = ["symbol", "signal_type", "strength", "timestamp", "price"]
                for field in required_fields:
                    if not hasattr(data, field) or getattr(data, field) is None:
                        return False, f"Missing required field: {field}"

                if abs(data.strength) > 1:
                    return False, "Signal strength must be between -1 and 1"

            elif data_type == "portfolio":
                required_fields = ["holdings", "cash"]
                for field in required_fields:
                    if not hasattr(data, field):
                        return False, f"Missing required field: {field}"

                if data.cash < 0:
                    return False, "Cash balance cannot be negative"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def calculate_migration_stats(legacy_data: List[Any]) -> Dict[str, Any]:
        """計算遷移統計信息"""
        total_records = len(legacy_data)
        valid_records = 0
        error_count = 0
        errors = []

        for data in legacy_data:
            is_valid, error = MigrationHelper.validate_legacy_data(data, type(data).__name__)
            if is_valid:
                valid_records += 1
            else:
                error_count += 1
                errors.append(error)

        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "invalid_records": error_count,
            "success_rate": (valid_records / total_records * 100) if total_records > 0 else 0,
            "common_errors": errors[:10]  # 前10個常見錯誤
        }

# 便捷函數
def create_unified_market_data(
    symbol: str,
    timestamp: datetime,
    open_price: Decimal,
    high_price: Decimal,
    low_price: Decimal,
    close_price: Decimal,
    volume: int,
    **kwargs
) -> MarketData:
    """創建統一格式的市場數據（兼容舊版）"""
    return MarketData(
        symbol=symbol,
        timestamp=timestamp,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=volume,
        **kwargs
    )

def create_legacy_trading_signal(
    symbol: str,
    signal_type: str,
    strength: float,
    timestamp: datetime,
    price: Decimal,
    **kwargs
) -> TradingSignal:
    """創建舊版格式的交易信號（兼容舊版）"""
    return TradingSignal(
        symbol=symbol,
        signal_type=SignalType(signal_type),
        strength=strength,
        timestamp=timestamp,
        price=price,
        metadata=kwargs.get("metadata", {})
    )

# 向後兼容性導出
__all__ = [
    # Legacy models (re-exported)
    "MarketData",
    "Portfolio",
    "TradingSignal",
    "Holding",
    "RiskMetrics",
    "PerformanceMetrics",

    # Enums
    "SignalType",
    "AgentStatus",
    "MessageType",

    # Migration tools
    "LegacyDataAdapter",
    "MigrationHelper",

    # Utility functions
    "create_unified_market_data",
    "create_legacy_trading_signal",
]