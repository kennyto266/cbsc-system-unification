"""
Parabolic SAR Strategy
拋物線SAR策略

重構後的SAR策略實現，遵循統一的動量策略架構
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .base import BaseMomentumStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata

logger = logging.getLogger(__name__)


class SARStrategy(BaseMomentumStrategy):
    """
    Parabolic SAR Strategy

    SAR策略：基於拋物線停止與反轉的趨勢跟蹤策略
    """

    # 策略元數據
    STRATEGY_NAME = "sar"
    STRATEGY_TYPE = StrategyType.MOMENTUM
    DESCRIPTION = "Parabolic SAR Strategy"
    VERSION = "2.0.0"
    AUTHOR = "CBSC Team"

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

    # 指標配置
    INDICATORS = {
        "sar": {
            "default": {
                "acceleration_factor": 0.02,
                "maximum_acceleration": 0.2
            },
            "description": "Parabolic SAR parameters"
        }
    }

    # 默認參數
    DEFAULT_PARAMETERS = {
        "acceleration_factor": 0.02,
        "maximum_acceleration": 0.2,
        "symbols": ["SPY", "QQQ", "IWM"],
        "position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.15,
        "use_price_filter": True,
        "min_move_distance": 0.01,
        "use_confirmation": True,
        "confirmation_periods": 1
    }

    # 必需參數
    REQUIRED_PARAMETERS = ["acceleration_factor", "maximum_acceleration"]

    # 可選參數
    OPTIONAL_PARAMETERS = {
        "use_price_filter": {
            "type": bool,
            "default": True
        },
        "min_move_distance": {
            "type": float,
            "default": 0.01,
            "min": 0.001,
            "max": 0.1
        },
        "use_confirmation": {
            "type": bool,
            "default": True
        },
        "confirmation_periods": {
            "type": int,
            "default": 1,
            "min": 1,
            "max": 5
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
            "default": 0.15,
            "min": 0.05,
            "max": 0.50
        }
    }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成SAR信號

        Args:
            data: 價格數據，必須包含OHLCV列

        Returns:
            包含信號的DataFrame
        """
        try:
            df = data.copy()

            # 提取參數
            af = self.config["acceleration_factor"]
            max_af = self.config["maximum_acceleration"]
            use_price_filter = self.config["use_price_filter"]
            min_move_distance = self.config["min_move_distance"]
            use_confirmation = self.config["use_confirmation"]
            confirm_periods = self.config["confirmation_periods"]

            # 檢查數據長度
            if len(df) < 10:
                logger.warning(f"Insufficient data for SAR calculation (need at least 10 bars, have {len(df)})")
                return self._create_empty_signals(df)

            # 計算SAR
            df = self._calculate_sar(df, af, max_af)

            # 生成基本信號（SAR交叉）
            df["sar_basic_signal"] = np.where(
                df["close"] > df["sar"], 1, -1
            )

            # 檢測SAR反轉點
            df["sar_reversal"] = (
                df["sar_basic_signal"] != df["sar_basic_signal"].shift(1)
            ).astype(int).fillna(0)

            # 價格過濾（避免在SAR接近價格時發出信號）
            if use_price_filter:
                price_distance = abs(df["close"] - df["sar"]) / df["close"]
                df["price_filtered_signal"] = np.where(
                    price_distance >= min_move_distance,
                    df["sar_basic_signal"],
                    0
                )
            else:
                df["price_filtered_signal"] = df["sar_basic_signal"]

            # 確認機制（需要持續幾個週期確認趨勢）
            if use_confirmation:
                df["trend_confirmation"] = (
                    df["sar_basic_signal"].rolling(window=confirm_periods).apply(
                        lambda x: 1 if (x == 1).all() else (-1 if (x == -1).all() else 0)
                    )
                )
                df["sar_signal"] = np.where(
                    df["sar_reversal"] != 0,
                    df["price_filtered_signal"],
                    df["trend_confirmation"]
                )
            else:
                df["trend_confirmation"] = 0
                df["sar_signal"] = df["price_filtered_signal"]

            # SAR位置關係
            df["sar_position"] = df["sar_basic_signal"]
            df["sar_distance"] = (df["close"] - df["sar"]) / df["close"]
            df["sar_trend_strength"] = abs(df["sar_distance"])

            # 持倉狀態
            df["sar_position_status"] = np.where(
                df["sar_signal"] != 0,
                df["sar_signal"],
                np.where(
                    (df["sar_signal"] == 0) & (df["sar_position_status"].shift(1) != 0),
                    df["sar_position_status"].shift(1),
                    0
                )
            )

            # 信號元數據
            signal_types = {
                1: "buy",
                -1: "sell",
                0: "hold"
            }

            df["signal_type"] = df["sar_signal"].map(signal_types)
            df["sar_af"] = df["acceleration_factor"]

            # 趨勢持續性
            df["trend_persistence"] = df.groupby(
                (df["sar_position"] != df["sar_position"].shift(1)).cumsum()
            ).cumcount()

            # 添加信號事件標記
            reversal_events = df[df["sar_reversal"] != 0]
            if not reversal_events.empty:
                logger.info(
                    f"SAR reversal at {reversal_events.index[0]}: "
                    f"{reversal_events['signal_type'].iloc[0]} signal "
                    f"(SAR={reversal_events['sar'].iloc[0]:.2f}, "
                    f"Price={reversal_events['close'].iloc[0]:.2f})"
                )

            return df

        except Exception as e:
            logger.error(f"Error generating SAR signals: {e}")
            raise

    def _calculate_sar(self, df: pd.DataFrame, af: float, max_af: float) -> pd.DataFrame:
        """
        計算拋物線SAR

        Args:
            df: 價格數據
            af: 初始加速因子
            max_af: 最大加速因子

        Returns:
            包含SAR值的DataFrame
        """
        high = df["high"].values
        low = df["low"].values
        close = df["close"].values

        # 初始化SAR變量
        sar = np.zeros(len(df))
        ep = np.zeros(len(df))  # Extreme point
        af_values = np.zeros(len(df))
        position = np.ones(len(df))  # 1 for long, -1 for short

        # 初始值
        sar[0] = low[0]
        ep[0] = high[0]
        af_values[0] = af
        position[0] = 1  # 從多頭開始

        for i in range(1, len(df)):
            if position[i-1] == 1:  # 多頭倉位
                # 計算新的SAR
                sar[i] = sar[i-1] + af_values[i-1] * (ep[i-1] - sar[i-1])

                # SAR不能高於前一根K線的最低點
                sar[i] = min(sar[i], low[i-1])

                # 檢查是否需要反轉（SAR突破當前最低點）
                if sar[i] > low[i]:
                    # 反轉為空頭
                    position[i] = -1
                    sar[i] = max(ep[i-1], high[i])
                    ep[i] = low[i]
                    af_values[i] = af
                else:
                    # 繼續多頭
                    position[i] = 1

                    # 更新極值點
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af_values[i] = min(af_values[i-1] + af, max_af)
                    else:
                        ep[i] = ep[i-1]
                        af_values[i] = af_values[i-1]

            else:  # 空頭倉位
                # 計算新的SAR
                sar[i] = sar[i-1] + af_values[i-1] * (ep[i-1] - sar[i-1])

                # SAR不能低於前一根K線的最高點
                sar[i] = max(sar[i], high[i-1])

                # 檢查是否需要反轉（SAR跌破當前最高點）
                if sar[i] < high[i]:
                    # 反轉為多頭
                    position[i] = 1
                    sar[i] = min(ep[i-1], low[i])
                    ep[i] = high[i]
                    af_values[i] = af
                else:
                    # 繼續空頭
                    position[i] = -1

                    # 更新極值點
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af_values[i] = min(af_values[i-1] + af, max_af)
                    else:
                        ep[i] = ep[i-1]
                        af_values[i] = af_values[i-1]

        # 添加到DataFrame
        df["sar"] = sar
        df["ep"] = ep
        df["acceleration_factor"] = af_values
        df["sar_position"] = position

        return df

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證SAR信號

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
            df = df[df["sar_signal"].notna()]
            df = df[df["sar_signal"] != 0]

            # 過濾連續相同的信號
            df["signal_change"] = df["sar_signal"] != df["sar_signal"].shift(1).fillna(0)
            df = df[df["signal_change"]]

            # 添加信號強度
            df["signal_strength"] = df["sar_trend_strength"]

            # 驗證SAR值有效性
            df = df[df["sar"].notna()]
            df = df[df["sar"] > 0]

            return df

        except Exception as e:
            logger.error(f"Error validating SAR signals: {e}")
            raise

    def _create_empty_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建空的信號DataFrame"""
        signals = pd.DataFrame(index=df.index)
        signals["sar_basic_signal"] = 0
        signals["signal_type"] = "hold"
        signals["sar_reversal"] = 0
        signals["price_filtered_signal"] = 0
        signals["trend_confirmation"] = 0
        signals["sar_signal"] = 0
        signals["sar_position"] = 0
        signals["sar_position_status"] = 0
        signals["sar"] = np.nan
        signals["ep"] = np.nan
        signals["acceleration_factor"] = self.config["acceleration_factor"]
        signals["sar_distance"] = 0.0
        signals["sar_trend_strength"] = 0.0
        signals["trend_persistence"] = 0
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
                "reversals": 0,
                "avg_sar_distance": 0.0,
                "max_sar_distance": 0.0,
                "avg_trend_persistence": 0.0,
                "max_trend_persistence": 0
            }

            # 執行策略獲取信號
            result = self.execute({symbol: df})
            signals_df = result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())

            if not signals_df.empty:
                symbol_analysis["signals_generated"] = len(signals_df)
                symbol_analysis["buy_signals"] = len(signals_df[signals_df["sar_signal"] == 1])
                symbol_analysis["sell_signals"] = len(signals_df[signals_df["sar_signal"] == -1])

                # SAR統計
                if "sar_distance" in signals_df.columns:
                    symbol_analysis["avg_sar_distance"] = signals_df["sar_distance"].abs().mean()
                    symbol_analysis["max_sar_distance"] = signals_df["sar_distance"].abs().max()

                # 趨勢持續性統計
                if "trend_persistence" in signals_df.columns:
                    symbol_analysis["avg_trend_persistence"] = signals_df["trend_persistence"].mean()
                    symbol_analysis["max_trend_persistence"] = signals_df["trend_persistence"].max()

                # 反轉次數
                if "sar_reversal" in signals_df.columns:
                    symbol_analysis["reversals"] = signals_df["sar_reversal"].sum()

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

        # 測試不同的SAR參數組合
        af_values = [0.01, 0.02, 0.03]
        max_af_values = [0.15, 0.2, 0.25]

        best_sharpe = -float("inf")
        best_config = None

        for af in af_values:
            for max_af in max_af_values:
                if af >= max_af:
                    continue

                test_config = self.config.copy()
                test_config["acceleration_factor"] = af
                test_config["maximum_acceleration"] = max_af

                # 執行回測
                backtest_result = self.backtest(data)
                sharpe_ratio = backtest_result["backtest_results"].get("TEST", {}).get("sharpe_ratio", 0)

                optimization_results["test_parameters"].append({
                    "acceleration_factor": af,
                    "maximum_acceleration": max_af,
                    "sharpe_ratio": sharpe_ratio
                })

                if sharpe_ratio > best_sharpe:
                    best_sharpe = sharpe_ratio
                    best_config = test_config.copy()

        if best_config:
            optimization_results["best_parameters"] = best_config
            optimization_results["performance"]["best_sharpe_ratio"] = best_sharpe
            logger.info(
                f"Optimized parameters: af={best_config['acceleration_factor']}, "
                f"max_af={best_config['maximum_acceleration']}"
            )

        return optimization_results