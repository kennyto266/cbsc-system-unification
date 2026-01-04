"""
On-Balance Volume (OBV) Strategy
能量潮策略

重構後的OBV策略實現，遵循統一的成交量策略架構
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .base import BaseVolumeStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata

logger = logging.getLogger(__name__)


class OBVStrategy(BaseVolumeStrategy):
    """
    On-Balance Volume (OBV) Strategy

    OBV策略：基於能量潮指標的價量關係分析策略
    """

    # 策略元數據
    STRATEGY_NAME = "obv"
    STRATEGY_TYPE = StrategyType.VOLUME
    DESCRIPTION = "On-Balance Volume Strategy"
    VERSION = "2.0.0"
    AUTHOR = "CBSC Team"

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

    # 指標配置
    INDICATORS = {
        "obv": {
            "default": {"ma_period": 20},
            "description": "OBV moving average period"
        },
        "divergence": {
            "default": {"period": 10},
            "description": "Divergence detection period"
        }
    }

    # 默認參數
    DEFAULT_PARAMETERS = {
        "ma_period": 20,
        "divergence_period": 10,
        "symbols": ["SPY", "QQQ", "IWM"],
        "position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.20,
        "use_divergence": True,
        "use_trend_confirmation": True,
        "min_signal_strength": 0.3
    }

    # 必需參數
    REQUIRED_PARAMETERS = []

    # 可選參數
    OPTIONAL_PARAMETERS = {
        "ma_period": {
            "type": int,
            "default": 20,
            "min": 5,
            "max": 50
        },
        "divergence_period": {
            "type": int,
            "default": 10,
            "min": 5,
            "max": 30
        },
        "use_divergence": {
            "type": bool,
            "default": True
        },
        "use_trend_confirmation": {
            "type": bool,
            "default": True
        },
        "min_signal_strength": {
            "type": float,
            "default": 0.3,
            "min": 0.1,
            "max": 1.0
        },
        "position_size": {
            "type": float,
            "default": 0.1,
            "min": 0.01,
            "max": 1.0
        },
        "stop_loss": {
            "type": float,
            "default": 0.05,
            "min": 0.01,
            "max": 0.20
        },
        "take_profit": {
            "type": float,
            "default": 0.20,
            "min": 0.05,
            "max": 0.50
        }
    }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成OBV信號

        Args:
            data: 價格數據，必須包含OHLCV列

        Returns:
            包含信號的DataFrame
        """
        try:
            df = data.copy()

            # 提取參數
            ma_period = self.config["ma_period"]
            divergence_period = self.config["divergence_period"]
            use_divergence = self.config["use_divergence"]
            use_trend_confirmation = self.config["use_trend_confirmation"]
            min_strength = self.config["min_signal_strength"]

            # 檢查數據長度
            min_length = max(ma_period, divergence_period) + 5
            if len(df) < min_length:
                logger.warning(f"Insufficient data for OBV calculation (need {min_length} bars, have {len(df)})")
                return self._create_empty_signals(df)

            # 計算OBV
            df["obv"] = self._calculate_obv(df["close"], df["volume"])

            # 計算OBV移動平均
            df["obv_ma"] = df["obv"].rolling(window=ma_period).mean()
            df["obv_ma_slope"] = df["obv_ma"].diff()

            # 計算OBV強度
            df["obv_strength"] = abs(df["obv_ma_slope"]) / df["obv"].rolling(window=20).std()

            # 生成基本趨勢信號
            df["obv_trend_signal"] = np.where(
                df["obv_ma_slope"] > 0, 1,
                np.where(df["obv_ma_slope"] < 0, -1, 0)
            )

            # 檢測背離
            if use_divergence:
                df["obv_divergence"] = self._detect_divergence(
                    df["close"], df["obv"], divergence_period
                )
            else:
                df["obv_divergence"] = 0

            # 趨勢確認
            if use_trend_confirmation:
                # 需要持續幾個週期確認趨勢
                df["obv_trend_confirmation"] = (
                    df["obv_trend_signal"].rolling(window=3).apply(
                        lambda x: 1 if (x == 1).all() else (-1 if (x == -1).all() else 0)
                    )
                )
            else:
                df["obv_trend_confirmation"] = df["obv_trend_signal"]

            # 綜合信號
            df["obv_signal"] = 0

            # 背離信號優先級最高
            divergence_signals = df["obv_divergence"] != 0
            df.loc[divergence_signals, "obv_signal"] = df["obv_divergence"]

            # 趨勢確認信號
            trend_signals = (df["obv_divergence"] == 0) & (df["obv_trend_confirmation"] != 0)
            df.loc[trend_signals, "obv_signal"] = df["obv_trend_confirmation"]

            # 信號強度過濾
            df["obv_signal"] = np.where(
                df["obv_strength"] >= min_strength,
                df["obv_signal"],
                0
            )

            # 持倉狀態
            df["obv_position"] = np.where(
                df["obv_signal"] != 0,
                df["obv_signal"],
                np.where(
                    (df["obv_signal"] == 0) & (df["obv_position"].shift(1) != 0),
                    df["obv_position"].shift(1),
                    0
                )
            )

            # 信號元數據
            signal_types = {
                1: "buy",
                -1: "sell",
                0: "hold"
            }

            df["signal_type"] = df["obv_signal"].map(signal_types)
            df["obv_distance"] = df["obv"] - df["obv_ma"]
            df["obv_relative"] = df["obv_distance"] / df["obv"].rolling(window=20).std()

            # OBV突破檢測
            df["obv_breakout"] = self._detect_obv_breakouts(df["obv"], df["obv_ma"])

            # 添加信號事件標記
            signal_events = df[df["obv_signal"] != 0]
            if not signal_events.empty:
                divergence_type = " (divergence)" if use_divergence and signal_events["obv_divergence"].iloc[0] != 0 else ""
                logger.info(
                    f"OBV signal at {signal_events.index[0]}: "
                    f"{signal_events['signal_type'].iloc[0]} signal{divergence_type} "
                    f"(OBV={signal_events['obv'].iloc[0]:.0f}, "
                    f"Strength={signal_events['obv_strength'].iloc[0]:.2f})"
                )

            return df

        except Exception as e:
            logger.error(f"Error generating OBV signals: {e}")
            raise

    def _calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        計算能量潮(OBV)

        Args:
            close: 收盤價序列
            volume: 成交量序列

        Returns:
            OBV序列
        """
        # 計算價格變化
        price_change = close.diff()

        # 計算OBV
        obv = pd.Series(0, index=close.index)

        for i in range(1, len(close)):
            if price_change.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif price_change.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]

        return obv

    def _detect_divergence(self, price: pd.Series, obv: pd.Series, period: int) -> pd.Series:
        """
        檢測價格-OBV背離

        Args:
            price: 價格序列
            obv: OBV序列
            period: 檢測週期

        Returns:
            背離信號序列
        """
        divergence = pd.Series(0, index=price.index)

        for i in range(period, len(price)):
            price_window = price.iloc[i-period:i+1]
            obv_window = obv.iloc[i-period:i+1]

            # 看漲背離：價格創新低，OBV未創新低
            if (price_window.iloc[-1] == price_window.min() and
                obv_window.iloc[-1] > obv_window.min()):
                divergence.iloc[i] = 1

            # 看跌背離：價格創新高，OBV未創新高
            elif (price_window.iloc[-1] == price_window.max() and
                  obv_window.iloc[-1] < obv_window.max()):
                divergence.iloc[i] = -1

        return divergence

    def _detect_obv_breakouts(self, obv: pd.Series, obv_ma: pd.Series) -> pd.Series:
        """
        檢測OBV突破

        Args:
            obv: OBV序列
            obv_ma: OBV移動平均

        Returns:
            突破信號
        """
        # OBV突破移動平均線
        ma_breakout = (obv > obv_ma) & (obv.shift(1) <= obv_ma.shift(1))
        ma_breakdown = (obv < obv_ma) & (obv.shift(1) >= obv_ma.shift(1))

        return np.where(ma_breakout, 1, np.where(ma_breakdown, -1, 0))

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證OBV信號

        Args:
            signals: 原始信號數據

        Returns:
            驗證後的信號數據
        """
        try:
            df = signals.copy()

            if df.empty:
                return df

            # 移除無效信號
            df = df[df["obv_signal"].notna()]
            df = df[df["obv_signal"] != 0]

            # 過濾連續相同的信號
            df["signal_change"] = df["obv_signal"] != df["obv_signal"].shift(1).fillna(0)
            df = df[df["signal_change"]]

            # 添加信號強度
            df["signal_strength"] = df["obv_strength"]

            # 驗證OBV值
            df = df[df["obv"].notna()]

            return df

        except Exception as e:
            logger.error(f"Error validating OBV signals: {e}")
            raise

    def _create_empty_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建空的信號DataFrame"""
        signals = pd.DataFrame(index=df.index)
        signals["obv_signal"] = 0
        signals["signal_type"] = "hold"
        signals["obv_trend_signal"] = 0
        signals["obv_trend_confirmation"] = 0
        signals["obv_divergence"] = 0
        signals["obv_position"] = 0
        signals["obv"] = 0
        signals["obv_ma"] = 0
        signals["obv_ma_slope"] = 0.0
        signals["obv_strength"] = 0.0
        signals["obv_distance"] = 0.0
        signals["obv_relative"] = 0.0
        signals["obv_breakout"] = 0
        signals["signal_strength"] = 0.0
        signals["signal_change"] = False
        return signals

    def analyze_performance(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        分析策略性能

        Args:
            data: 符號數據字典

        Returns:
            性能分析結果
        """
        analysis = {
            "strategy": self.STRATEGY_NAME,
            "parameters": self.config,
            "symbols_analyzed": [],
            "performance_metrics": {}
        }

        for symbol, df in data.items():
            if df.empty:
                continue

            symbol_analysis = {
                "symbol": symbol,
                "total_bars": len(df),
                "signals_generated": 0,
                "buy_signals": 0,
                "sell_signals": 0,
                "divergences_detected": 0,
                "breakouts_detected": 0,
                "avg_obv_strength": 0.0,
                "max_obv_strength": 0.0,
                "obv_trend_periods": {"bullish": 0, "bearish": 0}
            }

            # 執行策略獲取信號
            result = self.execute({symbol: df})
            signals_df = result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())

            if not signals_df.empty:
                symbol_analysis["signals_generated"] = len(signals_df)
                symbol_analysis["buy_signals"] = len(signals_df[signals_df["obv_signal"] == 1])
                symbol_analysis["sell_signals"] = len(signals_df[signals_df["obv_signal"] == -1])

            # OBV統計
            if "obv_divergence" in signals_df.columns:
                symbol_analysis["divergences_detected"] = (signals_df["obv_divergence"] != 0).sum()

            if "obv_breakout" in signals_df.columns:
                symbol_analysis["breakouts_detected"] = (signals_df["obv_breakout"] != 0).sum()

            if "obv_strength" in signals_df.columns:
                strength_values = signals_df["obv_strength"].dropna()
                if not strength_values.empty:
                    symbol_analysis["avg_obv_strength"] = strength_values.mean()
                    symbol_analysis["max_obv_strength"] = strength_values.max()

            # 趨勢週期統計
            if "obv_trend_signal" in signals_df.columns:
                bullish_periods = (signals_df["obv_trend_signal"] == 1).sum()
                bearish_periods = (signals_df["obv_trend_signal"] == -1).sum()
                symbol_analysis["obv_trend_periods"]["bullish"] = bullish_periods
                symbol_analysis["obv_trend_periods"]["bearish"] = bearish_periods

            analysis["symbols_analyzed"].append(symbol_analysis)

        return analysis

    def optimize_parameters(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        優化策略參數

        Args:
            data: 歷史數據字典

        Returns:
            參數優化結果
        """
        optimization_results = {
            "strategy": self.STRATEGY_NAME,
            "optimization_method": "grid_search",
            "test_parameters": [],
            "best_parameters": {},
            "performance": {}
        }

        # 測試不同的OBV參數組合
        ma_periods = [10, 20, 30]
        divergence_periods = [5, 10, 15]

        best_sharpe = -float("inf")
        best_config = None

        for ma_period in ma_periods:
            for divergence_period in divergence_periods:
                test_config = self.config.copy()
                test_config["ma_period"] = ma_period
                test_config["divergence_period"] = divergence_period

                # 執行回測
                backtest_result = self.backtest(data)
                sharpe_ratio = backtest_result["backtest_results"].get("TEST", {}).get("sharpe_ratio", 0)

                optimization_results["test_parameters"].append({
                    "ma_period": ma_period,
                    "divergence_period": divergence_period,
                    "sharpe_ratio": sharpe_ratio
                })

                if sharpe_ratio > best_sharpe:
                    best_sharpe = sharpe_ratio
                    best_config = test_config.copy()

        if best_config:
            optimization_results["best_parameters"] = best_config
            optimization_results["performance"]["best_sharpe_ratio"] = best_sharpe
            logger.info(
                f"Optimized parameters: ma_period={best_config['ma_period']}, "
                f"divergence_period={best_config['divergence_period']}"
            )

        return optimization_results