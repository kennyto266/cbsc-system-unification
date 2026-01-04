"""
Average Directional Index (ADX) Strategy
平均方向指標策略

重構後的ADX策略實現，遵循統一的動量策略架構
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .base import BaseMomentumStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata

logger = logging.getLogger(__name__)


class ADXStrategy(BaseMomentumStrategy):
    """
    Average Directional Index (ADX) Strategy

    ADX策略：基於平均方向指標的趨勢強度和方向判斷策略
    """

    # 策略元數據
    STRATEGY_NAME = "adx"
    STRATEGY_TYPE = StrategyType.MOMENTUM
    DESCRIPTION = "Average Directional Index Strategy"
    VERSION = "2.0.0"
    AUTHOR = "CBSC Team"

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES = ["15m", "30m", "1h", "4h", "1d"]

    # 指標配置
    INDICATORS = {
        "adx": {
            "default": {"period": 14},
            "description": "ADX calculation period"
        },
        "directional_movement": {
            "default": {"period": 14},
            "description": "Directional Movement calculation"
        }
    }

    # 默認參數
    DEFAULT_PARAMETERS = {
        "period": 14,
        "trend_threshold": 25,
        "strong_trend_threshold": 40,
        "symbols": ["SPY", "QQQ", "IWM"],
        "position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.15,
        "use_di_crossover": True,
        "use_adx_trend": True,
        "min_adx_for_signal": 20
    }

    # 必需參數
    REQUIRED_PARAMETERS = ["period"]

    # 可選參數
    OPTIONAL_PARAMETERS = {
        "trend_threshold": {
            "type": (int, float),
            "default": 25,
            "min": 10,
            "max": 50
        },
        "strong_trend_threshold": {
            "type": (int, float),
            "default": 40,
            "min": 30,
            "max": 70
        },
        "use_di_crossover": {
            "type": bool,
            "default": True
        },
        "use_adx_trend": {
            "type": bool,
            "default": True
        },
        "min_adx_for_signal": {
            "type": (int, float),
            "default": 20,
            "min": 10,
            "max": 30
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
        生成ADX信號

        Args:
            data: 價格數據，必須包含OHLCV列

        Returns:
            包含信號的DataFrame
        """
        try:
            df = data.copy()

            # 提取參數
            period = self.config["period"]
            trend_threshold = self.config["trend_threshold"]
            strong_trend_threshold = self.config["strong_trend_threshold"]
            use_di_crossover = self.config["use_di_crossover"]
            use_adx_trend = self.config["use_adx_trend"]
            min_adx = self.config["min_adx_for_signal"]

            # 檢查數據長度
            min_length = period * 2
            if len(df) < min_length:
                logger.warning(f"Insufficient data for ADX calculation (need {min_length} bars, have {len(df)})")
                return self._create_empty_signals(df)

            # 計算True Range
            df["tr1"] = df["high"] - df["low"]
            df["tr2"] = abs(df["high"] - df["close"].shift(1))
            df["tr3"] = abs(df["low"] - df["close"].shift(1))
            df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

            # 計算Directional Movement
            df["up_move"] = df["high"] - df["high"].shift(1)
            df["down_move"] = df["low"].shift(1) - df["low"]

            df["plus_dm"] = np.where(
                (df["up_move"] > df["down_move"]) & (df["up_move"] > 0),
                df["up_move"], 0
            )
            df["minus_dm"] = np.where(
                (df["down_move"] > df["up_move"]) & (df["down_move"] > 0),
                df["down_move"], 0
            )

            # 計算平滑值
            df["tr_smooth"] = df["tr"].rolling(window=period).mean()
            df["plus_di"] = 100 * (df["plus_dm"].rolling(window=period).sum() /
                                 df["tr_smooth"].rolling(window=period).sum())
            df["minus_di"] = 100 * (df["minus_dm"].rolling(window=period).sum() /
                                   df["tr_smooth"].rolling(window=period).sum())

            # 計算DX和ADX
            df["di_diff"] = abs(df["plus_di"] - df["minus_di"])
            df["di_sum"] = df["plus_di"] + df["minus_di"]
            df["dx"] = np.where(df["di_sum"] > 0, df["di_diff"] / df["di_sum"] * 100, 0)
            df["adx"] = df["dx"].rolling(window=period).mean()

            # 生成DI交叉信號
            if use_di_crossover:
                df["di_crossover_signal"] = np.where(
                    df["plus_di"] > df["minus_di"], 1, -1
                )
                # 檢測DI交叉
                df["di_crossover"] = (
                    df["di_crossover_signal"] != df["di_crossover_signal"].shift(1)
                ).astype(int).fillna(0)
            else:
                df["di_crossover_signal"] = 0
                df["di_crossover"] = 0

            # 生成ADX趨勢信號
            if use_adx_trend:
                df["adx_trend_signal"] = np.where(
                    df["adx"] > trend_threshold, 1, 0
                )
                df["adx_strong_trend"] = df["adx"] > strong_trend_threshold
            else:
                df["adx_trend_signal"] = 0
                df["adx_strong_trend"] = False

            # 綜合信號
            df["adx_signal"] = 0
            signal_conditions = (
                (df["adx"] >= min_adx) &  # ADX超過最小閾值
                (df["di_crossover"] != 0) &  # DI有交叉
                (df["adx_trend_signal"] == 1)  # ADX顯示趨勢
            )
            df.loc[signal_conditions, "adx_signal"] = df["di_crossover_signal"]

            # 持倉狀態
            df["adx_position"] = np.where(
                df["adx_signal"] != 0,
                df["adx_signal"],
                np.where(
                    (df["adx_signal"] == 0) & (df["adx_position"].shift(1) != 0),
                    df["adx_position"].shift(1),
                    0
                )
            )

            # 信號元數據
            signal_types = {
                1: "buy",
                -1: "sell",
                0: "hold"
            }

            df["signal_type"] = df["adx_signal"].map(signal_types)
            df["trend_strength"] = df["adx"] / 50  # 正規化到0-1
            df["di_spread"] = abs(df["plus_di"] - df["minus_di"])

            # 趨勢分類
            df["trend_category"] = np.where(
                df["adx"] >= strong_trend_threshold, "strong",
                np.where(
                    df["adx"] >= trend_threshold, "moderate",
                    "weak"
                )
            )

            # 添加信號事件標記
            signal_events = df[df["di_crossover"] != 0]
            if not signal_events.empty:
                logger.info(
                    f"ADX signal at {signal_events.index[0]}: "
                    f"{signal_events['signal_type'].iloc[0]} signal "
                    f"(ADX={signal_events['adx'].iloc[0]:.2f}, "
                    f"Trend: {signal_events['trend_category'].iloc[0]})"
                )

            return df

        except Exception as e:
            logger.error(f"Error generating ADX signals: {e}")
            raise

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證ADX信號

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
            df = df[df["adx_signal"].notna()]
            df = df[df["adx_signal"] != 0]

            # 過濾連續相同的信號
            df["signal_change"] = df["adx_signal"] != df["adx_signal"].shift(1).fillna(0)
            df = df[df["signal_change"]]

            # 驗證ADX值
            df = df[df["adx"] >= self.config["min_adx_for_signal"]]

            # 添加信號強度
            df["signal_strength"] = df["trend_strength"]

            return df

        except Exception as e:
            logger.error(f"Error validating ADX signals: {e}")
            raise

    def _create_empty_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建空的信號DataFrame"""
        signals = pd.DataFrame(index=df.index)
        signals["adx_signal"] = 0
        signals["signal_type"] = "hold"
        signals["di_crossover_signal"] = 0
        signals["di_crossover"] = 0
        signals["adx_position"] = 0
        signals["adx_trend_signal"] = 0
        signals["adx"] = np.nan
        signals["plus_di"] = np.nan
        signals["minus_di"] = np.nan
        signals["trend_strength"] = 0.0
        signals["di_spread"] = 0.0
        signals["trend_category"] = "weak"
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
                "di_crossovers": 0,
                "strong_trend_periods": 0,
                "avg_adx": 0.0,
                "max_adx": 0.0,
                "trend_distribution": {"strong": 0, "moderate": 0, "weak": 0}
            }

            # 執行策略獲取信號
            result = self.execute({symbol: df})
            signals_df = result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())

            if not signals_df.empty:
                symbol_analysis["signals_generated"] = len(signals_df)
                symbol_analysis["buy_signals"] = len(signals_df[signals_df["adx_signal"] == 1])
                symbol_analysis["sell_signals"] = len(signals_df[signals_df["adx_signal"] == -1])

            # ADX統計
            if "adx" in signals_df.columns:
                adx_values = signals_df["adx"].dropna()
                if not adx_values.empty:
                    symbol_analysis["avg_adx"] = adx_values.mean()
                    symbol_analysis["max_adx"] = adx_values.max()

                # 趨勢分布統計
                if "trend_category" in signals_df.columns:
                    trend_dist = signals_df["trend_category"].value_counts()
                    symbol_analysis["trend_distribution"]["strong"] = trend_dist.get("strong", 0)
                    symbol_analysis["trend_distribution"]["moderate"] = trend_dist.get("moderate", 0)
                    symbol_analysis["trend_distribution"]["weak"] = trend_dist.get("weak", 0)

                # 強趨勢時期
                if "adx_strong_trend" in signals_df.columns:
                    symbol_analysis["strong_trend_periods"] = signals_df["adx_strong_trend"].sum()

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

        # 測試不同的ADX參數組合
        periods = [7, 14, 21, 28]
        trend_thresholds = [20, 25, 30]

        best_sharpe = -float("inf")
        best_config = None

        for period in periods:
            for trend_threshold in trend_thresholds:
                test_config = self.config.copy()
                test_config["period"] = period
                test_config["trend_threshold"] = trend_threshold

                # 執行回測
                backtest_result = self.backtest(data)
                sharpe_ratio = backtest_result["backtest_results"].get("TEST", {}).get("sharpe_ratio", 0)

                optimization_results["test_parameters"].append({
                    "period": period,
                    "trend_threshold": trend_threshold,
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
                f"trend_threshold={best_config['trend_threshold']}"
            )

        return optimization_results