"""
Moving Average Crossover Strategy
移動平均線交叉策略

重構後的MA交叉策略實現，遵循統一的技術指標策略架構
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .base import BaseTechnicalIndicatorStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata

logger = logging.getLogger(__name__)


class MACrossoverStrategy(BaseTechnicalIndicatorStrategy):
    """
    Moving Average Crossover Strategy

    當移動平均線交叉策略：當短期移動平均線向上突破長期移動平均線時產生買入信號，
    當短期向下突破時產生賣出信號。
    """

    # 策略元數據
    STRATEGY_NAME = "ma_crossover"
    STRATEGY_TYPE = StrategyType.MOMENTUM
    DESCRIPTION = "Moving Average Crossover Strategy"
    VERSION = "2.0.0"
    AUTHOR = "CBSC Team"

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

    # 指標配置
    INDICATORS = {
        "fast_ma": {
            "default": {"period": 10},
            "description": "Fast moving average period"
        },
        "slow_ma": {
            "default": {"period": 20},
            "description": "Slow moving average period"
        }
    }

    # 默認參數
    DEFAULT_PARAMETERS = {
        "fast_period": 10,
        "slow_period": 20,
        "symbols": ["SPY", "QQQ", "IWM"],
        "position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.10,
        "use_ema": False,
        "signal_threshold": 0.001  # 最小交叉閾值
    }

    # 必需參數
    REQUIRED_PARAMETERS = ["fast_period", "slow_period"]

    # 可選參數
    OPTIONAL_PARAMETERS = {
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
        },
        "use_ema": {
            "type": bool,
            "default": False
        },
        "signal_threshold": {
            "type": float,
            "default": 0.001,
            "min": 0.0,
            "max": 0.1
        }
    }

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成MA交叉信號

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
            use_ema = self.config["use_ema"]
            signal_threshold = self.config["signal_threshold"]

            # 計置窗口大小至少要有慢週期的兩倍數據
            min_length = max(fast_period * 2, slow_period * 2)
            if len(df) < min_length:
                logger.warning(f"Insufficient data for MA calculation (need {min_length} bars, have {len(df)})")
                return self._create_empty_signals(df)

            # 計置閾值檢查
            if fast_period >= slow_period:
                logger.error(f"Fast period ({fast_period}) must be less than slow period ({slow_period})")
                return self._create_empty_signals(df)

            # 計置參數
            ma_type = "EMA" if use_ema else "SMA"

            # 計置指標名稱
            fast_ma_col = f"{ma_type}_{fast_period}"
            slow_ma_col = f"{ma_type}_{slow_period}"
            signal_col = "ma_cross_signal"
            position_col = "ma_cross_position"
            crossover_col = "ma_crossover"

            # 計置信號類型
            signal_types = {
                1: "buy",
                -1: "sell",
                0: "hold"
            }

            # 生成移動平均線
            df[fast_ma_col] = self._calculate_ma(df["close"], fast_period, ma_type)
            df[slow_ma_col] = self._calculate_ma(df["close"], slow_period, ma_type)

            # 生成交叉信號
            df[signal_col] = np.where(
                df[fast_ma_col] > df[slow_ma_col] + signal_threshold,
                1,
                np.where(
                    df[fast_ma_col] < df[slow_ma_col] - signal_threshold,
                    -1,
                    0
                )
            )

            # 檢測交叉點
            df[crossover_col] = (
                (df[signal_col] != df[signal_col].shift(1)).astype(int)
            ).fillna(0)

            # 設置持倉狀態
            df[position_col] = np.where(
                df[signal_col] != 0,
                df[signal_col],
                np.where(
                    (df[signal_col] == 0) & (df[position_col].shift(1) != 0),
                    df[position_col].shift(1),
                    0
                )
            )

            # 添加信號元數據
            df["signal_type"] = df[signal_col].map(signal_types)
            df["fast_ma"] = df[fast_ma_col]
            df["slow_ma"] = df[slow_ma_col]
            df["ma_distance"] = (df[fast_ma_col] - df[slow_ma_col]) / df[slow_ma_col]
            df["ma_ratio"] = df[fast_ma_col] / df[slow_ma_col]

            # 添加交叉事件標記
            crossover_events = df[df[crossover_col] != 0]
            if not crossover_events.empty:
                logger.info(
                    f"MA crossover detected at {crossover_events.index[0]}: "
                    f"{crossover_events['signal_type'].iloc[0]} signal"
                )

            return df

        except Exception as e:
            logger.error(f"Error generating MA crossover signals: {e}")
            raise

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證MA交叉信號

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
            df = df[df["signal"].notna()]
            df = df[df["signal"] != 0]

            # 過濾連續相同的信號
            df["signal_change"] = df["signal"] != df["signal"].shift(1).fillna(0)
            df = df[df["signal_change"]]

            # 添加信號置信度
            df["signal_strength"] = abs(df["ma_distance"]) * 100

            return df

        except Exception as e:
            logger.error(f"Error validating MA crossover signals: {e}")
            raise

    def _calculate_ma(self, prices: pd.Series, period: int, ma_type: str = "SMA") -> pd.Series:
        """
        計算移動平均線

        Args:
            prices: 價格序列
            period: 週期
            ma_type: MA類型 ("SMA" 或 "EMA")

        Returns:
            移動平均線序列
        """
        if ma_type == "SMA":
            return prices.rolling(window=period).mean()
        elif ma_type == "EMA":
            return prices.ewm(span=period).mean()
        else:
            raise ValueError(f"Unsupported MA type: {ma_type}")

    def _create_empty_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建空的信號DataFrame"""
        signals = pd.DataFrame(index=df.index)
        signals["signal"] = 0
        signals["signal_type"] = "hold"
        signals["ma_cross_signal"] = 0
        signals["ma_cross_position"] = 0
        signals["ma_crossover"] = 0
        signals["fast_ma"] = np.nan
        signals["slow_ma"] = np.nan
        signals["ma_distance"] = 0.0
        signals["ma_ratio"] = 1.0
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
                "sell_signals": 0",
                "crossovers": 0,
                "avg_ma_distance": 0.0,
                "max_ma_distance": 0.0,
                "min_ma_distance": 0.0
            }

            # 執行策略獲取信號
            result = self.execute({symbol: df})
            signals_df = result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())

            if not signals_df.empty:
                symbol_analysis["signals_generated"] = len(signals_df)
                symbol_analysis["buy_signals"] = len(signals_df[signals_df["signal"] == 1])
                symbol_analysis["sell_signals"] = len(signals_df[signals_df["signal"] == -1])
                symbol_analysis["crossovers"] = signals_df["ma_crossover"].sum()

                if "ma_distance" in signals_df.columns:
                    distances = signals_df["ma_distance"].abs()
                    symbol_analysis["avg_ma_distance"] = distances.mean()
                    symbol_analysis["max_ma_distance"] = distances.max()
                    symbol_analysis["min_ma_distance"] = distances.min()

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

        # 測試不同的快慢週期組合
        fast_periods = [5, 10, 15, 20]
        slow_periods = [20, 30, 40, 50]

        best_sharpe = -float("inf")
        best_config = None

        for fast_period in fast_periods:
            for slow_period in slow_periods:
                if fast_period >= slow_period:
                    continue

                test_config = self.config.copy()
                test_config["fast_period"] = fast_period
                test_config["slow_period"] = slow_period

                # 執行回測
                backtest_result = self.backtest(data)
                sharpe_ratio = backtest_result["backtest_results"].get("TEST", {}).get("sharpe_ratio", 0)

                optimization_results["test_parameters"].append({
                    "fast_period": fast_period,
                    "slow_period": slow_period,
                    "sharpe_ratio": sharpe_ratio
                })

                if sharpe_ratio > best_sharpe:
                    best_sharpe = sharpe_ratio
                    best_config = test_config.copy()

        if best_config:
            optimization_results["best_parameters"] = best_config
            optimization_results["performance"]["best_sharpe_ratio"] = best_sharpe_ratio
            logger.info(f"Optimized parameters: fast={best_config['fast_period']}, slow={best_config['slow_period']}")

        return optimization_results