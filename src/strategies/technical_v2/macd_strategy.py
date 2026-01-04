"""
MACD (Moving Average Convergence Divergence) Strategy
移動平均收斂發散策略

重構後的MACD策略實現，遵循統一的技術指標策略架構
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .base import BaseTechnicalIndicatorStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata

logger = logging.getLogger(__name__)


class MACDStrategy(BaseTechnicalIndicatorStrategy):
    """
    Moving Average Convergence Divergence (MACD) Strategy

    MACD策略：基於快速和慢速EMA的交叉與發散信號生成策略
    """

    # 策略元數據
    STRATEGY_NAME = "macd"
    STRATEGY_TYPE = StrategyType.MOMENTUM
    DESCRIPTION = "Moving Average Convergence Divergence Strategy"
    VERSION = "2.0.0"
    AUTHOR = "CBSC Team"

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

    # 指標配置
    INDICATORS = {
        "macd": {
            "default": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            },
            "description": "MACD line parameters"
        }
    }

    # 默認參數
    DEFAULT_PARAMETERS = {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
        "symbols": ["SPY", "QQQ", "IWM"],
        "position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.10,
        "histogram_threshold": 0.0005,
        "use_signal_confirmation": True,
        "use_zero_line_crossover": True
    }

    # 必需參數
    REQUIRED_PARAMETERS = ["fast_period", "slow_period", "signal_period"]

    # 可選參數
    OPTIONAL_PARAMETERS = {
        "histogram_threshold": {
            "type": float,
            "default": 0.0005,
            "min": 0.0,
            "max": 0.05
        },
        "use_signal_confirmation": {
            "type": bool,
            "default": True
        },
        "use_zero_line_crossover": {
            "type": bool,
            "default": True
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
        生成MACD信號

        Args:
            data: 價格數據，必須包含close列

        Returns:
            包含信號的DataFrame
        """
        try:
            df = data.copy()

            # 提取參數
            fast_period = self.config["fast_period"]
            slow_period = self.config["slow_period"]
            signal_period = self.config["signal_period"]
            hist_threshold = self.config["histogram_threshold"]
            use_confirmation = self.config["use_signal_confirmation"]
            use_zero_cross = self.config["use_zero_line_crossover"]

            # 檢查數據長度
            min_length = slow_period + signal_period * 2
            if len(df) < min_length:
                logger.warning(f"Insufficient data for MACD calculation (need {min_length} bars, have {len(df)})")
                return self._create_empty_signals(df)

            # 驗證參數
            if fast_period >= slow_period:
                logger.error(f"Fast period ({fast_period}) must be less than slow period ({slow_period})")
                return self._create_empty_signals(df)

            # 計算MACD
            macd_line, signal_line, histogram = self._calculate_macd(
                df["close"], fast_period, slow_period, signal_period
            )

            df["macd_line"] = macd_line
            df["macd_signal"] = signal_line
            df["macd_histogram"] = histogram

            # 生成MACD線交叉信號
            df["macd_crossover_signal"] = 0
            df.loc[df["macd_line"] > df["macd_signal"], "macd_crossover_signal"] = 1
            df.loc[df["macd_line"] < df["macd_signal"], "macd_crossover_signal"] = -1

            # 檢測MACD線交叉點
            df["macd_crossover"] = (
                df["macd_crossover_signal"] != df["macd_crossover_signal"].shift(1)
            ).astype(int).fillna(0)

            # 零線交叉信號
            if use_zero_cross:
                df["zero_line_signal"] = np.where(df["macd_line"] > 0, 1, -1)
                df["zero_line_crossover"] = (
                    df["zero_line_signal"] != df["zero_line_signal"].shift(1)
                ).astype(int).fillna(0)
            else:
                df["zero_line_signal"] = 0
                df["zero_line_crossover"] = 0

            # 信號確認
            if use_confirmation:
                # 需要MACD線和信號線交叉，同時柱狀圖超過閾值
                df["confirmed_signal"] = np.where(
                    (df["macd_crossover"] != 0) & (abs(df["macd_histogram"]) > hist_threshold),
                    df["macd_crossover_signal"],
                    0
                )
                signal_col = "confirmed_signal"
            else:
                signal_col = "macd_crossover_signal"

            # 最終信號（結合MACD交叉和零線交叉）
            if use_zero_cross:
                df["macd_final_signal"] = np.where(
                    df["macd_crossover"] != 0,
                    df[signal_col],
                    np.where(
                        df["zero_line_crossover"] != 0,
                        df["zero_line_signal"],
                        0
                    )
                )
            else:
                df["macd_final_signal"] = df[signal_col]

            # 持倉狀態
            df["macd_position"] = np.where(
                df["macd_final_signal"] != 0,
                df["macd_final_signal"],
                np.where(
                    (df["macd_final_signal"] == 0) & (df["macd_position"].shift(1) != 0),
                    df["macd_position"].shift(1),
                    0
                )
            )

            # 信號元數據
            signal_types = {
                1: "buy",
                -1: "sell",
                0: "hold"
            }

            df["signal_type"] = df["macd_final_signal"].map(signal_types)
            df["macd_divergence"] = df["macd_line"] - df["macd_signal"]
            df["macd_strength"] = abs(df["macd_histogram"]) * 1000  # 放大便於顯示

            # 添加交叉事件標記
            crossover_events = df[df["macd_crossover"] != 0]
            if not crossover_events.empty:
                logger.info(
                    f"MACD crossover detected at {crossover_events.index[0]}: "
                    f"{crossover_events['signal_type'].iloc[0]} signal "
                    f"(MACD={crossover_events['macd_line'].iloc[0]:.4f}, "
                    f"Signal={crossover_events['macd_signal'].iloc[0]:.4f})"
                )

            return df

        except Exception as e:
            logger.error(f"Error generating MACD signals: {e}")
            raise

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證MACD信號

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
            df = df[df["macd_final_signal"].notna()]
            df = df[df["macd_final_signal"] != 0]

            # 過濾連續相同的信號
            df["signal_change"] = df["macd_final_signal"] != df["macd_final_signal"].shift(1).fillna(0)
            df = df[df["signal_change"]]

            # 添加信號強度
            df["signal_strength"] = abs(df["macd_divergence"])

            # 驗證MACD值有效性
            df = df[df["macd_line"].notna()]
            df = df[df["macd_signal"].notna()]

            return df

        except Exception as e:
            logger.error(f"Error validating MACD signals: {e}")
            raise

    def _calculate_macd(self, prices: pd.Series, fast: int, slow: int, signal: int) -> tuple:
        """
        計算MACD指標

        Args:
            prices: 價格序列
            fast: 快速EMA週期
            slow: 慢速EMA週期
            signal: 信號線EMA週期

        Returns:
            (MACD線, 信號線, 柱狀圖)
        """
        # 計算EMA
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()

        # MACD線
        macd_line = ema_fast - ema_slow

        # 信號線
        signal_line = macd_line.ewm(span=signal).mean()

        # 柱狀圖
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def _create_empty_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建空的信號DataFrame"""
        signals = pd.DataFrame(index=df.index)
        signals["macd_crossover_signal"] = 0
        signals["signal_type"] = "hold"
        signals["macd_crossover"] = 0
        signals["macd_position"] = 0
        signals["zero_line_signal"] = 0
        signals["zero_line_crossover"] = 0
        signals["confirmed_signal"] = 0
        signals["macd_final_signal"] = 0
        signals["macd_line"] = np.nan
        signals["macd_signal"] = np.nan
        signals["macd_histogram"] = np.nan
        signals["macd_divergence"] = 0.0
        signals["macd_strength"] = 0.0
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
                "macd_crossovers": 0,
                "zero_line_crossovers": 0,
                "avg_macd_divergence": 0.0,
                "max_histogram": 0.0,
                "min_histogram": 0.0
            }

            # 執行策略獲取信號
            result = self.execute({symbol: df})
            signals_df = result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())

            if not signals_df.empty:
                symbol_analysis["signals_generated"] = len(signals_df)
                symbol_analysis["buy_signals"] = len(signals_df[signals_df["macd_final_signal"] == 1])
                symbol_analysis["sell_signals"] = len(signals_df[signals_df["macd_final_signal"] == -1])
                symbol_analysis["macd_crossovers"] = signals_df["macd_crossover"].sum()
                symbol_analysis["zero_line_crossovers"] = signals_df["zero_line_crossover"].sum()

                if "macd_divergence" in signals_df.columns:
                    symbol_analysis["avg_macd_divergence"] = signals_df["macd_divergence"].abs().mean()

                if "macd_histogram" in signals_df.columns:
                    hist_values = signals_df["macd_histogram"].dropna()
                    if not hist_values.empty:
                        symbol_analysis["max_histogram"] = hist_values.max()
                        symbol_analysis["min_histogram"] = hist_values.min()

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

        # 測試不同的MACD參數組合
        fast_periods = [8, 12, 16]
        slow_periods = [21, 26, 34]
        signal_periods = [6, 9, 12]

        best_sharpe = -float("inf")
        best_config = None

        for fast_period in fast_periods:
            for slow_period in slow_periods:
                for signal_period in signal_periods:
                    if fast_period >= slow_period:
                        continue

                    test_config = self.config.copy()
                    test_config["fast_period"] = fast_period
                    test_config["slow_period"] = slow_period
                    test_config["signal_period"] = signal_period

                    # 執行回測
                    backtest_result = self.backtest(data)
                    sharpe_ratio = backtest_result["backtest_results"].get("TEST", {}).get("sharpe_ratio", 0)

                    optimization_results["test_parameters"].append({
                        "fast_period": fast_period,
                        "slow_period": slow_period,
                        "signal_period": signal_period,
                        "sharpe_ratio": sharpe_ratio
                    })

                    if sharpe_ratio > best_sharpe:
                        best_sharpe = sharpe_ratio
                        best_config = test_config.copy()

        if best_config:
            optimization_results["best_parameters"] = best_config
            optimization_results["performance"]["best_sharpe_ratio"] = best_sharpe
            logger.info(
                f"Optimized parameters: fast={best_config['fast_period']}, "
                f"slow={best_config['slow_period']}, "
                f"signal={best_config['signal_period']}"
            )

        return optimization_results