"""
Bollinger Bands Strategy
布林帶策略

重構後的布林帶策略實現，遵循統一的技術指標策略架構
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .base import BaseTechnicalIndicatorStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata

logger = logging.getLogger(__name__)


class BollingerBandsStrategy(BaseTechnicalIndicatorStrategy):
    """
    Bollinger Bands Strategy

    布林帶策略：基於價格波動率的突破和回歸信號生成策略
    """

    # 策略元數據
    STRATEGY_NAME = "bollinger_bands"
    STRATEGY_TYPE = StrategyType.VOLATILITY
    DESCRIPTION = "Bollinger Bands Strategy"
    VERSION = "2.0.0"
    AUTHOR = "CBSC Team"

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

    # 指標配置
    INDICATORS = {
        "bollinger_bands": {
            "default": {
                "period": 20,
                "std_dev": 2.0
            },
            "description": "Bollinger Bands calculation parameters"
        }
    }

    # 默認參數
    DEFAULT_PARAMETERS = {
        "period": 20,
        "std_dev": 2.0,
        "symbols": ["SPY", "QQQ", "IWM"],
        "position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.10,
        "use_squeeze": True,
        "use_walk": False,
        "entry_threshold": 0.1,
        "exit_threshold": 0.5
    }

    # 必需參數
    REQUIRED_PARAMETERS = ["period", "std_dev"]

    # 可選參數
    OPTIONAL_PARAMETERS = {
        "use_squeeze": {
            "type": bool,
            "default": True
        },
        "use_walk": {
            "type": bool,
            "default": False
        },
        "entry_threshold": {
            "type": float,
            "default": 0.1,
            "min": 0.0,
            "max": 1.0
        },
        "exit_threshold": {
            "type": float,
            "default": 0.5,
            "min": 0.0,
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
            "default": 0.10,
            "min": 0.02,
            "max": 0.50
        }
    }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成布林帶信號

        Args:
            data: 價格數據，必須包含close列

        Returns:
            包含信號的DataFrame
        """
        try:
            df = data.copy()

            # 提取參數
            period = self.config["period"]
            std_dev = self.config["std_dev"]
            use_squeeze = self.config["use_squeeze"]
            use_walk = self.config["use_walk"]
            entry_thresh = self.config["entry_threshold"]
            exit_thresh = self.config["exit_threshold"]

            # 檢查數據長度
            min_length = period * 2
            if len(df) < min_length:
                logger.warning(f"Insufficient data for Bollinger Bands (need {min_length} bars, have {len(df)})")
                return self._create_empty_signals(df)

            # 計算布林帶
            upper_band, middle_band, lower_band = self._calculate_bollinger_bands(
                df["close"], period, std_dev
            )

            df["bb_upper"] = upper_band
            df["bb_middle"] = middle_band
            df["bb_lower"] = lower_band

            # 計算帶寬和位置
            df["bb_width"] = (upper_band - lower_band) / middle_band
            df["bb_position"] = (df["close"] - lower_band) / (upper_band - lower_band)

            # 基本信號（突破）
            df["bb_breakout_signal"] = 0
            df.loc[df["close"] > df["bb_upper"], "bb_breakout_signal"] = 1  # 突破上軌，賣出
            df.loc[df["close"] < df["bb_lower"], "bb_breakout_signal"] = -1  # 突破下軌，買入

            # 回歸信號（均值回歸）
            df["bb_reversion_signal"] = 0
            df.loc[df["bb_position"] > 1 - entry_thresh, "bb_reversion_signal"] = -1  # 接近上軌，賣出
            df.loc[df["bb_position"] < entry_thresh, "bb_reversion_signal"] = 1  # 接近下軌，買入

            # 退出信號
            df.loc[df["bb_position"] > exit_thresh, "bb_reversion_signal"] = 0  # 退出賣出
            df.loc[df["bb_position"] < 1 - exit_thresh, "bb_reversion_signal"] = 0  # 退出買入

            # 擠壓信號（收縮後的突破）
            if use_squeeze:
                # 檢測擠壓（帶寬收縮）
                df["bb_width_ma"] = df["bb_width"].rolling(window=20).mean()
                df["bb_squeeze"] = df["bb_width"] < df["bb_width_ma"] * 0.8

                # 擠壓後突破信號
                squeeze_breakout = df["bb_squeeze"].shift(1).fillna(False) & (~df["bb_squeeze"])
                df.loc[squeeze_breakout & (df["close"] > df["bb_upper"]), "bb_breakout_signal"] = 1
                df.loc[squeeze_breakout & (df["close"] < df["bb_lower"]), "bb_breakout_signal"] = -1
            else:
                df["bb_squeeze"] = False

            # 通道行走（沿著上下軌移動）
            if use_walk:
                # 沿上軌行走
                walk_up = (df["close"] > df["bb_lower"]) & (df["close"] < df["bb_upper"])
                df.loc[walk_up & (df["close"].rolling(5).mean() > df["bb_middle"]), "bb_walk_signal"] = 1

                # 沿下軌行走
                walk_down = (df["close"] > df["bb_lower"]) & (df["close"] < df["bb_upper"])
                df.loc[walk_down & (df["close"].rolling(5).mean() < df["bb_middle"]), "bb_walk_signal"] = -1
            else:
                df["bb_walk_signal"] = 0

            # 綜合信號
            df["bb_final_signal"] = np.where(
                df["bb_breakout_signal"] != 0,
                df["bb_breakout_signal"],
                np.where(
                    df["bb_walk_signal"] != 0,
                    df["bb_walk_signal"],
                    df["bb_reversion_signal"]
                )
            )

            # 檢測信號變化
            df["bb_signal_change"] = (df["bb_final_signal"] != df["bb_final_signal"].shift(1)).astype(int).fillna(0)

            # 持倉狀態
            df["bb_position_status"] = np.where(
                df["bb_final_signal"] != 0,
                df["bb_final_signal"],
                np.where(
                    (df["bb_final_signal"] == 0) & (df["bb_position_status"].shift(1) != 0),
                    df["bb_position_status"].shift(1),
                    0
                )
            )

            # 信號元數據
            signal_types = {
                1: "buy",
                -1: "sell",
                0: "hold"
            }

            df["signal_type"] = df["bb_final_signal"].map(signal_types)
            df["bb_distance"] = np.where(
                df["bb_final_signal"] == 1,
                df["bb_middle"] - df["close"],
                np.where(
                    df["bb_final_signal"] == -1,
                    df["close"] - df["bb_middle"],
                    0
                )
            )
            df["bb_strength"] = abs(df["bb_position"] - 0.5) * 2  # 0到1之間的強度

            # 添加信號事件標記
            signal_events = df[df["bb_signal_change"] != 0]
            if not signal_events.empty:
                logger.info(
                    f"Bollinger Bands signal at {signal_events.index[0]}: "
                    f"{signal_events['signal_type'].iloc[0]} "
                    f"(Position: {signal_events['bb_position'].iloc[0]:.2f}, "
                    f"Width: {signal_events['bb_width'].iloc[0]:.4f})"
                )

            return df

        except Exception as e:
            logger.error(f"Error generating Bollinger Bands signals: {e}")
            raise

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證布林帶信號

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
            df = df[df["bb_final_signal"].notna()]
            df = df[df["bb_final_signal"] != 0]

            # 過濾連續相同的信號
            df["signal_change"] = df["bb_final_signal"] != df["bb_final_signal"].shift(1).fillna(0)
            df = df[df["signal_change"]]

            # 添加信號強度
            df["signal_strength"] = df["bb_strength"]

            # 驗證布林帶值有效性
            df = df[df["bb_upper"].notna()]
            df = df[df["bb_lower"].notna()]
            df = df[df["bb_upper"] > df["bb_lower"]]

            return df

        except Exception as e:
            logger.error(f"Error validating Bollinger Bands signals: {e}")
            raise

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int, std_dev: float) -> tuple:
        """
        計算布林帶

        Args:
            prices: 價格序列
            period: 週期
            std_dev: 標準差倍數

        Returns:
            (上軌, 中軌, 下軌)
        """
        # 中軌（簡單移動平均）
        middle_band = prices.rolling(window=period).mean()

        # 標準差
        rolling_std = prices.rolling(window=period).std()

        # 上下軌
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)

        return upper_band, middle_band, lower_band

    def _create_empty_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建空的信號DataFrame"""
        signals = pd.DataFrame(index=df.index)
        signals["bb_breakout_signal"] = 0
        signals["signal_type"] = "hold"
        signals["bb_reversion_signal"] = 0
        signals["bb_walk_signal"] = 0
        signals["bb_final_signal"] = 0
        signals["bb_signal_change"] = 0
        signals["bb_position_status"] = 0
        signals["bb_upper"] = np.nan
        signals["bb_middle"] = np.nan
        signals["bb_lower"] = np.nan
        signals["bb_width"] = 0.0
        signals["bb_position"] = 0.5
        signals["bb_squeeze"] = False
        signals["bb_distance"] = 0.0
        signals["bb_strength"] = 0.0
        signals["bb_width_ma"] = np.nan
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
                "breakout_signals": 0,
                "reversion_signals": 0,
                "squeeze_breakouts": 0,
                "avg_bb_width": 0.0,
                "max_bb_width": 0.0,
                "min_bb_width": 0.0
            }

            # 執行策略獲取信號
            result = self.execute({symbol: df})
            signals_df = result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())

            if not signals_df.empty:
                symbol_analysis["signals_generated"] = len(signals_df)
                symbol_analysis["buy_signals"] = len(signals_df[signals_df["bb_final_signal"] == 1])
                symbol_analysis["sell_signals"] = len(signals_df[signals_df["bb_final_signal"] == -1])
                symbol_analysis["breakout_signals"] = len(signals_df[signals_df["bb_breakout_signal"] != 0])
                symbol_analysis["reversion_signals"] = len(signals_df[signals_df["bb_reversion_signal"] != 0])
                symbol_analysis["squeeze_breakouts"] = signals_df["bb_squeeze"].sum()

                if "bb_width" in signals_df.columns:
                    width_values = signals_df["bb_width"].dropna()
                    if not width_values.empty:
                        symbol_analysis["avg_bb_width"] = width_values.mean()
                        symbol_analysis["max_bb_width"] = width_values.max()
                        symbol_analysis["min_bb_width"] = width_values.min()

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

        # 測試不同的布林帶參數組合
        periods = [10, 20, 30]
        std_devs = [1.5, 2.0, 2.5]

        best_sharpe = -float("inf")
        best_config = None

        for period in periods:
            for std_dev in std_devs:
                test_config = self.config.copy()
                test_config["period"] = period
                test_config["std_dev"] = std_dev

                # 執行回測
                backtest_result = self.backtest(data)
                sharpe_ratio = backtest_result["backtest_results"].get("TEST", {}).get("sharpe_ratio", 0)

                optimization_results["test_parameters"].append({
                    "period": period,
                    "std_dev": std_dev,
                    "sharpe_ratio": sharpe_ratio
                })

                if sharpe_ratio > best_sharpe:
                    best_sharpe = sharpe_ratio
                    best_config = test_config.copy()

        if best_config:
            optimization_results["best_parameters"] = best_config
            optimization_results["performance"]["best_sharpe_ratio"] = best_sharpe
            logger.info(
                f"Optimized parameters: period={best_config['period']}, "
                f"std_dev={best_config['std_dev']}"
            )

        return optimization_results