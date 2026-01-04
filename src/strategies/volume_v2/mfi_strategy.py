"""
Money Flow Index (MFI) Strategy
資金流指標策略

重構後的MFI策略實現，遵循統一的成交量策略架構
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .base import BaseVolumeStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata

logger = logging.getLogger(__name__)


class MFIStrategy(BaseVolumeStrategy):
    """
    Money Flow Index (MFI) Strategy

    MFI策略：基於資金流指標的超買超賣和背離分析策略
    """

    # 策略元數據
    STRATEGY_NAME = "mfi"
    STRATEGY_TYPE = StrategyType.VOLUME
    DESCRIPTION = "Money Flow Index Strategy"
    VERSION = "2.0.0"
    AUTHOR = "CBSC Team"

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

    # 指標配置
    INDICATORS = {
        "mfi": {
            "default": {
                "period": 14,
                "overbought_level": 80,
                "oversold_level": 20
            },
            "description": "MFI calculation parameters"
        }
    }

    # 默認參數
    DEFAULT_PARAMETERS = {
        "period": 14,
        "overbought_level": 80,
        "oversold_level": 20,
        "symbols": ["SPY", "QQQ", "IWM"],
        "position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.20,
        "use_divergence": True,
        "divergence_period": 10,
        "use_center_line": True,
        "center_line": 50
    }

    # 必需參數
    REQUIRED_PARAMETERS = []

    # 可選參數
    OPTIONAL_PARAMETERS = {
        "period": {
            "type": int,
            "default": 14,
            "min": 5,
            "max": 30
        },
        "overbought_level": {
            "type": (int, float),
            "default": 80,
            "min": 70,
            "max": 95
        },
        "oversold_level": {
            "type": (int, float),
            "default": 20,
            "min": 5,
            "max": 30
        },
        "use_divergence": {
            "type": bool,
            "default": True
        },
        "divergence_period": {
            "type": int,
            "default": 10,
            "min": 5,
            "max": 20
        },
        "use_center_line": {
            "type": bool,
            "default": True
        },
        "center_line": {
            "type": (int, float),
            "default": 50,
            "min": 40,
            "max": 60
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
        生成MFI信號

        Args:
            data: 價格數據，必須包含OHLCV列

        Returns:
            包含信號的DataFrame
        """
        try:
            df = data.copy()

            # 提取參數
            period = self.config["period"]
            overbought = self.config["overbought_level"]
            oversold = self.config["oversold_level"]
            use_divergence = self.config["use_divergence"]
            divergence_period = self.config["divergence_period"]
            use_center_line = self.config["use_center_line"]
            center_line = self.config["center_line"]

            # 檢查數據長度
            min_length = period * 2
            if len(df) < min_length:
                logger.warning(f"Insufficient data for MFI calculation (need {min_length} bars, have {len(df)})")
                return self._create_empty_signals(df)

            # 驗證閾值
            if oversold >= overbought:
                logger.error(f"Oversold level ({oversold}) must be less than overbought ({overbought})")
                return self._create_empty_signals(df)

            # 計算MFI
            df["mfi"] = self._calculate_mfi(df, period)

            # 生成基本超買超賣信號
            df["mfi_oversold_signal"] = np.where(df["mfi"] < oversold, 1, 0)
            df["mfi_overbought_signal"] = np.where(df["mfi"] > overbought, -1, 0)

            # 檢測MFI穿越
            df["mfi_oversold_crossover"] = (
                (df["mfi"] > oversold) & (df["mfi"].shift(1) <= oversold.shift(1))
            ).astype(int)
            df["mfi_overbought_crossover"] = (
                (df["mfi"] < overbought) & (df["mfi"].shift(1) >= overbought.shift(1))
            ).astype(int)

            # 中心線信號
            if use_center_line:
                df["mfi_center_signal"] = np.where(
                    df["mfi"] > center_line, 1,
                    np.where(df["mfi"] < center_line, -1, 0)
                )
                df["mfi_center_crossover"] = (
                    df["mfi_center_signal"] != df["mfi_center_signal"].shift(1)
                ).astype(int).fillna(0)
            else:
                df["mfi_center_signal"] = 0
                df["mfi_center_crossover"] = 0

            # 背離檢測
            if use_divergence:
                df["mfi_divergence"] = self._detect_divergence(
                    df["close"], df["mfi"], divergence_period
                )
            else:
                df["mfi_divergence"] = 0

            # 綜合信號
            df["mfi_signal"] = 0

            # 背離信號優先級最高
            divergence_signals = df["mfi_divergence"] != 0
            df.loc[divergence_signals, "mfi_signal"] = df["mfi_divergence"]

            # 超賣回歸信號
            oversold_cross = df["mfi_oversold_crossover"] == 1
            df.loc[oversold_cross & (df["mfi_signal"] == 0), "mfi_signal"] = 1

            # 超買回歸信號
            overbought_cross = df["mfi_overbought_crossover"] == 1
            df.loc[overbought_cross & (df["mfi_signal"] == 0), "mfi_signal"] = -1

            # 中心線信號（趨勢確認）
            if use_center_line:
                center_cross = df["mfi_center_crossover"] != 0
                df.loc[center_cross & (df["mfi_signal"] == 0), "mfi_signal"] = df["mfi_center_signal"]

            # MFI強度計算
            df["mfi_strength"] = np.where(
                df["mfi"] >= center_line,
                (df["mfi"] - center_line) / (100 - center_line),
                (center_line - df["mfi"]) / center_line
            )

            # 持倉狀態
            df["mfi_position"] = np.where(
                df["mfi_signal"] != 0,
                df["mfi_signal"],
                np.where(
                    (df["mfi_signal"] == 0) & (df["mfi_position"].shift(1) != 0),
                    df["mfi_position"].shift(1),
                    0
                )
            )

            # 信號元數據
            signal_types = {
                1: "buy",
                -1: "sell",
                0: "hold"
            }

            df["signal_type"] = df["mfi_signal"].map(signal_types)
            df["mfi_zone"] = np.where(
                df["mfi"] > overbought, "overbought",
                np.where(
                    df["mfi"] < oversold, "oversold",
                    "neutral"
                )
            )
            df["mfi_distance"] = np.where(
                df["mfi"] >= center_line,
                df["mfi"] - center_line,
                center_line - df["mfi"]
            )

            # MFI趨勢
            df["mfi_trend"] = df["mfi"].diff()
            df["mfi_acceleration"] = df["mfi_trend"].diff()

            # 添加信號事件標記
            signal_events = df[df["mfi_signal"] != 0]
            if not signal_events.empty:
                divergence_type = " (divergence)" if use_divergence and signal_events["mfi_divergence"].iloc[0] != 0 else ""
                logger.info(
                    f"MFI signal at {signal_events.index[0]}: "
                    f"{signal_events['signal_type'].iloc[0]} signal{divergence_type} "
                    f"(MFI={signal_events['mfi'].iloc[0]:.2f}, "
                    f"Zone: {signal_events['mfi_zone'].iloc[0]})"
                )

            return df

        except Exception as e:
            logger.error(f"Error generating MFI signals: {e}")
            raise

    def _calculate_mfi(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        計算資金流指標(MFI)

        Args:
            df: 價格數據
            period: 計算週期

        Returns:
            MFI序列
        """
        # 典型價格
        tp = (df["high"] + df["low"] + df["close"]) / 3
        raw_money_flow = tp * df["volume"]

        # 正負資金流
        positive_mf = pd.Series(0, index=df.index)
        negative_mf = pd.Series(0, index=df.index)

        for i in range(1, len(df)):
            if tp.iloc[i] > tp.iloc[i-1]:
                positive_mf.iloc[i] = raw_money_flow.iloc[i]
            elif tp.iloc[i] < tp.iloc[i-1]:
                negative_mf.iloc[i] = raw_money_flow.iloc[i]

        # 資金流比率
        positive_mf_sum = positive_mf.rolling(window=period).sum()
        negative_mf_sum = negative_mf.rolling(window=period).sum()

        money_flow_ratio = positive_mf_sum / negative_mf_sum
        money_flow_ratio = money_flow_ratio.replace([np.inf, -np.inf], 0)

        # 資金流指標
        mfi = 100 - (100 / (1 + money_flow_ratio))

        return mfi

    def _detect_divergence(self, price: pd.Series, mfi: pd.Series, period: int) -> pd.Series:
        """
        檢測價格-MFI背離

        Args:
            price: 價格序列
            mfi: MFI序列
            period: 檢測週期

        Returns:
            背離信號序列
        """
        divergence = pd.Series(0, index=price.index)

        for i in range(period, len(price)):
            price_window = price.iloc[i-period:i+1]
            mfi_window = mfi.iloc[i-period:i+1]

            # 看漲背離：價格創新低，MFI未創新低
            if (price_window.iloc[-1] == price_window.min() and
                mfi_window.iloc[-1] > mfi_window.min()):
                divergence.iloc[i] = 1

            # 看跌背離：價格創新高，MFI未創新高
            elif (price_window.iloc[-1] == price_window.max() and
                  mfi_window.iloc[-1] < mfi_window.max()):
                divergence.iloc[i] = -1

        return divergence

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證MFI信號

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
            df = df[df["mfi_signal"].notna()]
            df = df[df["mfi_signal"] != 0]

            # 過濾連續相同的信號
            df["signal_change"] = df["mfi_signal"] != df["mfi_signal"].shift(1).fillna(0)
            df = df[df["signal_change"]]

            # 添加信號強度
            df["signal_strength"] = df["mfi_strength"]

            # 驗證MFI值有效性
            df = df[df["mfi"].notna()]
            df = df[(df["mfi"] >= 0) & (df["mfi"] <= 100)]

            return df

        except Exception as e:
            logger.error(f"Error validating MFI signals: {e}")
            raise

    def _create_empty_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建空的信號DataFrame"""
        signals = pd.DataFrame(index=df.index)
        signals["mfi_signal"] = 0
        signals["signal_type"] = "hold"
        signals["mfi_oversold_signal"] = 0
        signals["mfi_overbought_signal"] = 0
        signals["mfi_oversold_crossover"] = 0
        signals["mfi_overbought_crossover"] = 0
        signals["mfi_center_signal"] = 0
        signals["mfi_center_crossover"] = 0
        signals["mfi_divergence"] = 0
        signals["mfi_position"] = 0
        signals["mfi"] = np.nan
        signals["mfi_strength"] = 0.0
        signals["mfi_zone"] = "neutral"
        signals["mfi_distance"] = 0.0
        signals["mfi_trend"] = 0.0
        signals["mfi_acceleration"] = 0.0
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
                "oversold_hits": 0,
                "overbought_hits": 0,
                "divergences_detected": 0,
                "avg_mfi": 0.0,
                "max_mfi": 0.0,
                "min_mfi": 0.0,
                "mfi_zone_distribution": {"overbought": 0, "oversold": 0, "neutral": 0}
            }

            # 執行策略獲取信號
            result = self.execute({symbol: df})
            signals_df = result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())

            if not signals_df.empty:
                symbol_analysis["signals_generated"] = len(signals_df)
                symbol_analysis["buy_signals"] = len(signals_df[signals_df["mfi_signal"] == 1])
                symbol_analysis["sell_signals"] = len(signals_df[signals_df["mfi_signal"] == -1])

            # MFI統計
            if "mfi" in signals_df.columns:
                mfi_values = signals_df["mfi"].dropna()
                if not mfi_values.empty:
                    symbol_analysis["avg_mfi"] = mfi_values.mean()
                    symbol_analysis["max_mfi"] = mfi_values.max()
                    symbol_analysis["min_mfi"] = mfi_values.min()

                # 區域分布統計
                if "mfi_zone" in signals_df.columns:
                    zone_dist = signals_df["mfi_zone"].value_counts()
                    symbol_analysis["mfi_zone_distribution"]["overbought"] = zone_dist.get("overbought", 0)
                    symbol_analysis["mfi_zone_distribution"]["oversold"] = zone_dist.get("oversold", 0)
                    symbol_analysis["mfi_zone_distribution"]["neutral"] = zone_dist.get("neutral", 0)

                # 超買超賣次數
                symbol_analysis["oversold_hits"] = (mfi_values < self.config["oversold_level"]).sum()
                symbol_analysis["overbought_hits"] = (mfi_values > self.config["overbought_level"]).sum()

            # 背離檢測
            if "mfi_divergence" in signals_df.columns:
                symbol_analysis["divergences_detected"] = (signals_df["mfi_divergence"] != 0).sum()

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

        # 測試不同的MFI參數組合
        periods = [7, 14, 21]
        oversold_levels = [15, 20, 25]
        overbought_levels = [75, 80, 85]

        best_sharpe = -float("inf")
        best_config = None

        for period in periods:
            for oversold in oversold_levels:
                for overbought in overbought_levels:
                    if oversold >= overbought:
                        continue

                    test_config = self.config.copy()
                    test_config["period"] = period
                    test_config["oversold_level"] = oversold
                    test_config["overbought_level"] = overbought

                    # 執行回測
                    backtest_result = self.backtest(data)
                    sharpe_ratio = backtest_result["backtest_results"].get("TEST", {}).get("sharpe_ratio", 0)

                    optimization_results["test_parameters"].append({
                        "period": period,
                        "oversold_level": oversold,
                        "overbought_level": overbought,
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
                f"oversold={best_config['oversold_level']}, "
                f"overbought={best_config['overbought_level']}"
            )

        return optimization_results