"""
Volume Weighted Average Price (VWAP) Strategy
成交量加權平均價格策略

重構後的VWAP策略實現，遵循統一的成交量策略架構
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

from .base import BaseVolumeStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata

logger = logging.getLogger(__name__)


class VWAPStrategy(BaseVolumeStrategy):
    """
    Volume Weighted Average Price (VWAP) Strategy

    VWAP策略：基於成交量加權平均價格的均值回歸和突破策略
    """

    # 策略元數據
    STRATEGY_NAME = "vwap"
    STRATEGY_TYPE = StrategyType.VOLUME
    DESCRIPTION = "Volume Weighted Average Price Strategy"
    VERSION = "2.0.0"
    AUTHOR = "CBSC Team"

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h"]

    # 指標配置
    INDICATORS = {
        "vwap": {
            "default": {
                "reset_period": None,
                "std_dev_bands": 2.0
            },
            "description": "VWAP calculation parameters"
        }
    }

    # 默認參數
    DEFAULT_PARAMETERS = {
        "reset_period": None,  # None for cumulative, int for reset
        "std_dev_bands": 2.0,
        "symbols": ["SPY", "QQQ", "IWM"],
        "position_size": 0.1,
        "stop_loss": 0.04,
        "take_profit": 0.15,
        "use_bands": True,
        "mean_reversion_threshold": 0.02,
        "breakout_threshold": 0.01,
        "use_volume_confirmation": True
    }

    # 必需參數
    REQUIRED_PARAMETERS = []

    # 可選參數
    OPTIONAL_PARAMETERS = {
        "reset_period": {
            "type": (int, type(None)),
            "default": None,
            "min": 1,
            "max": 390
        },
        "std_dev_bands": {
            "type": float,
            "default": 2.0,
            "min": 0.5,
            "max": 3.0
        },
        "use_bands": {
            "type": bool,
            "default": True
        },
        "mean_reversion_threshold": {
            "type": float,
            "default": 0.02,
            "min": 0.005,
            "max": 0.1
        },
        "breakout_threshold": {
            "type": float,
            "default": 0.01,
            "min": 0.002,
            "max": 0.05
        },
        "use_volume_confirmation": {
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
            "default": 0.04,
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
        生成VWAP信號

        Args:
            data: 價格數據，必須包含OHLCV列

        Returns:
            包含信號的DataFrame
        """
        try:
            df = data.copy()

            # 提取參數
            reset_period = self.config["reset_period"]
            std_dev_bands = self.config["std_dev_bands"]
            use_bands = self.config["use_bands"]
            mean_reversion_threshold = self.config["mean_reversion_threshold"]
            breakout_threshold = self.config["breakout_threshold"]
            use_volume_confirmation = self.config["use_volume_confirmation"]

            # 檢查數據長度
            min_length = 20
            if len(df) < min_length:
                logger.warning(f"Insufficient data for VWAP calculation (need {min_length} bars, have {len(df)})")
                return self._create_empty_signals(df)

            # 計算VWAP和標準差帶
            df["vwap"], df["vwap_upper"], df["vwap_lower"] = self._calculate_vwap(
                df, reset_period, std_dev_bands
            )

            # 計算價格相對VWAP的位置
            df["price_to_vwap"] = (df["close"] - df["vwap"]) / df["vwap"]
            df["vwap_distance"] = abs(df["price_to_vwap"])

            # 生成均值回歸信號
            df["vwap_mean_reversion_signal"] = 0
            # 價格遠離VWAP上軌，賣出
            df.loc[df["price_to_vwap"] > mean_reversion_threshold, "vwap_mean_reversion_signal"] = -1
            # 價格遠離VWAP下軌，買入
            df.loc[df["price_to_vwap"] < -mean_reversion_threshold, "vwap_mean_reversion_signal"] = 1

            # 生成突破信號
            df["vwap_breakout_signal"] = 0
            # 向上突破VWAP
            breakout_up = (df["close"] > df["vwap"]) & (df["close"].shift(1) <= df["vwap"].shift(1))
            df.loc[breakout_up, "vwap_breakout_signal"] = 1

            # 向下突破VWAP
            breakout_down = (df["close"] < df["vwap"]) & (df["close"].shift(1) >= df["vwap"].shift(1))
            df.loc[breakout_down, "vwap_breakout_signal"] = -1

            # 生成帶突破信號
            if use_bands:
                df["vwap_band_signal"] = 0
                # 突破上帶（強勢突破）
                band_breakout_up = (df["close"] > df["vwap_upper"]) & (df["close"].shift(1) <= df["vwap_upper"].shift(1))
                df.loc[band_breakout_up, "vwap_band_signal"] = 1

                # 突破下帶（弱勢突破）
                band_breakout_down = (df["close"] < df["vwap_lower"]) & (df["close"].shift(1) >= df["vwap_lower"].shift(1))
                df.loc[band_breakout_down, "vwap_band_signal"] = -1

                # 帶內回歸信號
                df["vwap_band_reversion"] = 0
                df.loc[df["close"] > df["vwap_upper"], "vwap_band_reversion"] = -1
                df.loc[df["close"] < df["vwap_lower"], "vwap_band_reversion"] = 1
            else:
                df["vwap_band_signal"] = 0
                df["vwap_band_reversion"] = 0

            # 成交量確認
            if use_volume_confirmation and "volume_ma_20" in df.columns:
                volume_confirmed = df["volume"] > df["volume_ma_20"] * 1.2
                df["vwap_signal"] = np.where(
                    volume_confirmed,
                    df["vwap_breakout_signal"],
                    df["vwap_mean_reversion_signal"]
                )
            else:
                df["vwap_signal"] = df["vwap_breakout_signal"]

            # 帶突破信號優先級高於基本突破
            if use_bands:
                df.loc[df["vwap_band_signal"] != 0, "vwap_signal"] = df["vwap_band_signal"]

            # VWAP位置分類
            df["vwap_position"] = np.where(
                df["close"] > df["vwap_upper"], "above_upper",
                np.where(
                    df["close"] < df["vwap_lower"], "below_lower",
                    "within_bands"
                )
            )

            # 持倉狀態
            df["vwap_position_status"] = np.where(
                df["vwap_signal"] != 0,
                df["vwap_signal"],
                np.where(
                    (df["vwap_signal"] == 0) & (df["vwap_position_status"].shift(1) != 0),
                    df["vwap_position_status"].shift(1),
                    0
                )
            )

            # 信號元數據
            signal_types = {
                1: "buy",
                -1: "sell",
                0: "hold"
            }

            df["signal_type"] = df["vwap_signal"].map(signal_types)
            df["vwap_band_width"] = (df["vwap_upper"] - df["vwap_lower"]) / df["vwap"]
            df["vwap_band_position"] = (df["close"] - df["vwap_lower"]) / (df["vwap_upper"] - df["vwap_lower"])

            # VWAP趨勢
            df["vwap_trend"] = df["vwap"].diff()
            df["vwap_trend_signal"] = np.where(
                df["vwap_trend"] > 0, 1,
                np.where(df["vwap_trend"] < 0, -1, 0)
            )

            # 添加信號事件標記
            signal_events = df[df["vwap_signal"] != 0]
            if not signal_events.empty:
                position_type = signal_events["vwap_position"].iloc[0]
                logger.info(
                    f"VWAP signal at {signal_events.index[0]}: "
                    f"{signal_events['signal_type'].iloc[0]} signal "
                    f"(Position: {position_type}, "
                    f"VWAP={signal_events['vwap'].iloc[0]:.2f}, "
                    f"Price={signal_events['close'].iloc[0]:.2f})"
                )

            return df

        except Exception as e:
            logger.error(f"Error generating VWAP signals: {e}")
            raise

    def _calculate_vwap(self, df: pd.DataFrame, reset_period: Optional[int],
                         std_dev_bands: float) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        計算VWAP和標準差帶

        Args:
            df: 價格數據
            reset_period: 重置週期，None表示累積
            std_dev_bands: 標準差倍數

        Returns:
            (VWAP, 上軌, 下軌)
        """
        if reset_period is None:
            # 累積VWAP
            typical_price = (df["high"] + df["low"] + df["close"]) / 3
            cumulative_volume = df["volume"].cumsum()
            cumulative_price_volume = (typical_price * df["volume"]).cumsum()

            vwap = cumulative_price_volume / cumulative_volume

            # 計算標準差帶
            variance = ((typical_price - vwap) ** 2 * df["volume"]).cumsum() / cumulative_volume
            std_dev = np.sqrt(variance)

        else:
            # 按週期重置VWAP
            typical_price = (df["high"] + df["low"] + df["close"]) / 3

            # 創建重置組
            if hasattr(df.index, 'dayofyear'):
                reset_groups = df.index.dayofyear // reset_period
            else:
                reset_groups = np.arange(len(df)) // reset_period

            def calc_vwap(group):
                """計算組內VWAP"""
                group_tp = typical_price.loc[group.index]
                group_vol = df.loc[group.index, 'volume']
                return (group_tp * group_vol).sum() / group_vol.sum()

            def calc_std(group):
                """計算組內標準差"""
                group_tp = typical_price.loc[group.index]
                group_vol = df.loc[group.index, 'volume']
                vwap_val = (group_tp * group_vol).sum() / group_vol.sum()
                variance = ((group_tp - vwap_val) ** 2 * group_vol).sum() / group_vol.sum()
                return np.sqrt(variance)

            vwap = typical_price.groupby(reset_groups).transform(calc_vwap)
            std_dev = typical_price.groupby(reset_groups).transform(calc_std)

        # 計算帶
        upper_band = vwap + (std_dev * std_dev_bands)
        lower_band = vwap - (std_dev * std_dev_bands)

        return vwap, upper_band, lower_band

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證VWAP信號

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
            df = df[df["vwap_signal"].notna()]
            df = df[df["vwap_signal"] != 0]

            # 過濾連續相同的信號
            df["signal_change"] = df["vwap_signal"] != df["vwap_signal"].shift(1).fillna(0)
            df = df[df["signal_change"]]

            # 添加信號強度
            df["signal_strength"] = df["vwap_distance"]

            # 驗證VWAP值有效性
            df = df[df["vwap"].notna()]
            df = df[df["vwap"] > 0]

            return df

        except Exception as e:
            logger.error(f"Error validating VWAP signals: {e}")
            raise

    def _create_empty_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建空的信號DataFrame"""
        signals = pd.DataFrame(index=df.index)
        signals["vwap_signal"] = 0
        signals["signal_type"] = "hold"
        signals["vwap_breakout_signal"] = 0
        signals["vwap_mean_reversion_signal"] = 0
        signals["vwap_band_signal"] = 0
        signals["vwap_band_reversion"] = 0
        signals["vwap_position_status"] = 0
        signals["vwap"] = np.nan
        signals["vwap_upper"] = np.nan
        signals["vwap_lower"] = np.nan
        signals["price_to_vwap"] = 0.0
        signals["vwap_distance"] = 0.0
        signals["vwap_band_width"] = 0.0
        signals["vwap_band_position"] = 0.5
        signals["vwap_position"] = "within_bands"
        signals["vwap_trend"] = 0.0
        signals["vwap_trend_signal"] = 0
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
                "breakout_signals": 0,
                "reversion_signals": 0,
                "band_signals": 0,
                "avg_vwap_distance": 0.0,
                "max_vwap_distance": 0.0,
                "time_above_vwap": 0,
                "time_below_vwap": 0
            }

            # 執行策略獲取信號
            result = self.execute({symbol: df})
            signals_df = result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())

            if not signals_df.empty:
                symbol_analysis["signals_generated"] = len(signals_df)
                symbol_analysis["buy_signals"] = len(signals_df[signals_df["vwap_signal"] == 1])
                symbol_analysis["sell_signals"] = len(signals_df[signals_df["vwap_signal"] == -1])

                # VWAP統計
                if "vwap_distance" in signals_df.columns:
                    symbol_analysis["avg_vwap_distance"] = signals_df["vwap_distance"].mean()
                    symbol_analysis["max_vwap_distance"] = signals_df["vwap_distance"].max()

                # 信號類型統計
                if "vwap_breakout_signal" in signals_df.columns:
                    symbol_analysis["breakout_signals"] = (signals_df["vwap_breakout_signal"] != 0).sum()

                if "vwap_mean_reversion_signal" in signals_df.columns:
                    symbol_analysis["reversion_signals"] = (signals_df["vwap_mean_reversion_signal"] != 0).sum()

                if "vwap_band_signal" in signals_df.columns:
                    symbol_analysis["band_signals"] = (signals_df["vwap_band_signal"] != 0).sum()

                # VWAP位置時間分布
                if "vwap_position" in signals_df.columns:
                    position_counts = signals_df["vwap_position"].value_counts()
                    symbol_analysis["time_above_vwap"] = position_counts.get("above_upper", 0) + position_counts.get("within_bands", 0)
                    symbol_analysis["time_below_vwap"] = position_counts.get("below_lower", 0)

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

        # 測試不同的VWAP參數組合
        std_dev_values = [1.5, 2.0, 2.5]
        mean_reversion_thresholds = [0.01, 0.02, 0.03]

        best_sharpe = -float("inf")
        best_config = None

        for std_dev in std_dev_values:
            for mean_reversion_threshold in mean_reversion_thresholds:
                test_config = self.config.copy()
                test_config["std_dev_bands"] = std_dev
                test_config["mean_reversion_threshold"] = mean_reversion_threshold

                # 執行回測
                backtest_result = self.backtest(data)
                sharpe_ratio = backtest_result["backtest_results"].get("TEST", {}).get("sharpe_ratio", 0)

                optimization_results["test_parameters"].append({
                    "std_dev_bands": std_dev,
                    "mean_reversion_threshold": mean_reversion_threshold,
                    "sharpe_ratio": sharpe_ratio
                })

                if sharpe_ratio > best_sharpe:
                    best_sharpe = sharpe_ratio
                    best_config = test_config.copy()

        if best_config:
            optimization_results["best_parameters"] = best_config
            optimization_results["performance"]["best_sharpe_ratio"] = best_sharpe
            logger.info(
                f"Optimized parameters: std_dev_bands={best_config['std_dev_bands']}, "
                f"mean_reversion_threshold={best_config['mean_reversion_threshold']}"
            )

        return optimization_results