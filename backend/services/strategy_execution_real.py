"""
Real-Time Strategy Execution Service
使用真實市場數據的策略執行服務
"""
import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import yfinance as yf

from backend.services.data_validator import DataValidator
from backend.data_config import DataSourceConfig

logger = logging.getLogger(__name__)


class StrategyExecutionError(Exception):
    """策略執行錯誤"""
    pass


class RealTimeStrategyExecution:
    """實時策略執行引擎"""

    def __init__(self, data_config: Optional[DataSourceConfig] = None):
        self.data_config = data_config or DataSourceConfig()
        self.validator = DataValidator()
        self.active_strategies = {}  # strategy_id -> config

    async def get_real_time_signals(
        self,
        strategy_config: Dict[str, Any],
        symbols: List[str]
    ) -> Dict[str, Any]:
        """
        獲取實時交易信號

        Args:
            strategy_config: 策略配置
            symbols: 監控標的列表

        Returns:
            交易信號數據
        """
        try:
            signals = []

            for symbol in symbols:
                try:
                    # 獲取實時數據
                    signal = await self._generate_signal(symbol, strategy_config)
                    if signal:
                        signals.append(signal)

                except Exception as e:
                    logger.error(f"Error generating signal for {symbol}: {e}")
                    continue

            return {
                "success": True,
                "data": {
                    "signals": signals,
                    "total_signals": len(signals),
                    "timestamp": datetime.utcnow().isoformat()
                },
                "data_source": "yahoo_finance_realtime"
            }

        except Exception as e:
            logger.error(f"Real-time signals error: {e}")
            raise StrategyExecutionError(f"Failed to generate signals: {str(e)}")

    async def _generate_signal(
        self,
        symbol: str,
        strategy_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """生成單個標的的交易信號"""

        # 獲取最近的數據
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo", timeout=10)

        if hist.empty or len(hist) < 50:
            return None

        hist.columns = [col.lower() for col in hist.columns]

        # 根據策略類型生成信號
        strategy_type = strategy_config.get("type", "ma_cross")

        if strategy_type == "ma_cross":
            return self._ma_cross_signal(symbol, hist, strategy_config)
        else:
            return self._default_signal(symbol, hist)

    def _ma_cross_signal(
        self,
        symbol: str,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """移動平均交叉信號"""
        short_period = config.get("short_period", 20)
        long_period = config.get("long_period", 50)

        df['ma_short'] = df['close'].rolling(window=short_period).mean()
        df['ma_long'] = df['close'].rolling(window=long_period).mean()

        if len(df) < 2 or pd.isna(df['ma_short'].iloc[-1]) or pd.isna(df['ma_long'].iloc[-1]):
            return None

        # 檢查交叉
        prev_short = df['ma_short'].iloc[-2]
        prev_long = df['ma_long'].iloc[-2]
        curr_short = df['ma_short'].iloc[-1]
        curr_long = df['ma_long'].iloc[-1]

        signal_type = None
        strength = 0

        # 金叉 - 買入信號
        if prev_short <= prev_long and curr_short > curr_long:
            signal_type = "buy"
            strength = min(1.0, (curr_short - curr_long) / curr_long * 100)
        # 死叉 - 賣出信號
        elif prev_short >= prev_long and curr_short < curr_long:
            signal_type = "sell"
            strength = min(1.0, (curr_long - curr_short) / curr_long * 100)

        if signal_type:
            return {
                "symbol": symbol,
                "signal_type": signal_type,
                "strength": round(strength, 2),
                "price": float(df['close'].iloc[-1]),
                "ma_short": float(curr_short),
                "ma_long": float(curr_long),
                "timestamp": datetime.utcnow().isoformat()
            }

        return None

    def _default_signal(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """默認信號（基於價格變動）"""
        if len(df) < 2:
            return None

        # 計算 RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        curr_rsi = rsi.iloc[-1]
        if pd.isna(curr_rsi):
            return None

        signal_type = None
        if curr_rsi < 30:
            signal_type = "buy"  # 超賣
        elif curr_rsi > 70:
            signal_type = "sell"  # 超買

        if signal_type:
            strength = abs(curr_rsi - 50) / 50  # 0 to 1

            return {
                "symbol": symbol,
                "signal_type": signal_type,
                "strength": round(strength, 2),
                "price": float(df['close'].iloc[-1]),
                "rsi": float(curr_rsi),
                "timestamp": datetime.utcnow().isoformat()
            }

        return None


class RiskManagementService:
    """風險管理服務"""

    def __init__(self):
        self.position_limits = {}  # symbol -> max_position
        self.daily_loss_limits = {}  # strategy_id -> daily_loss_limit

    async def check_position_limit(
        self,
        symbol: str,
        quantity: int,
        current_positions: Dict[str, int]
    ) -> Dict[str, Any]:
        """檢查持倉限制"""
        try:
            # 獲取當前持倉
            current_quantity = current_positions.get(symbol, 0)
            new_quantity = current_quantity + quantity

            # 簡單限制：單個標的不超過總資金的 20%
            # 這裡可以用真實數據獲取股價來計算
            limit = 10000  # 簡化

            if new_quantity > limit:
                return {
                    "allowed": False,
                    "reason": f"超過持倉限制: {new_quantity} > {limit}",
                    "current": current_quantity,
                    "requested": quantity
                }

            return {
                "allowed": True,
                "current": current_quantity,
                "new": new_quantity
            }

        except Exception as e:
            logger.error(f"Position limit check error: {e}")
            return {
                "allowed": False,
                "reason": f"風險檢查失敗: {str(e)}"
            }

    async def check_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        stop_loss_pct: float
    ) -> Dict[str, Any]:
        """檢查止損"""
        try:
            pct_change = (current_price - entry_price) / entry_price * 100

            # 檢查是否觸發止損
            if pct_change <= -stop_loss_pct:
                return {
                    "triggered": True,
                    "action": "sell",
                    "loss_pct": round(pct_change, 2),
                    "message": f"觸發止損: {pct_change:.2f}% <= -{stop_loss_pct}%"
                }

            # 檢查止盈
            take_profit_pct = stop_loss_pct * 2  # 止盈是止損的2倍
            if pct_change >= take_profit_pct:
                return {
                    "triggered": True,
                    "action": "sell",
                    "profit_pct": round(pct_change, 2),
                    "message": f"觸發止盈: {pct_change:.2f}% >= {take_profit_pct}%"
                }

            return {
                "triggered": False,
                "current_pct": round(pct_change, 2)
            }

        except Exception as e:
            logger.error(f"Stop loss check error: {e}")
            return {
                "triggered": False,
                "error": str(e)
            }
