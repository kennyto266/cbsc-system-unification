"""
Relative Strength Index (RSI) Strategy
相對強弱指標策略

重構後的RSI策略實現，遵循統一的技術指標策略架構
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .base import BaseTechnicalIndicatorStrategy
from ..enhanced_factory import StrategyType, StrategyMetadata

logger = logging.getLogger(__name__)


class RSIStrategy(BaseTechnicalIndicatorStrategy):
    """
    Relative Strength Index (RSI) Strategy

    RSI策略：基於相對強弱指標的超買超賣信號生成策略
    """

    # 策略元數據
    STRATEGY_NAME = "rsi"
    STRATEGY_TYPE = StrategyType.TECHNICAL_ANALYSIS
    DESCRIPTION = "Relative Strength Index Strategy"
    VERSION = "2.0.0"
    AUTHOR = "CBSC Team"

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

    # 指標配置
    INDICATORS = {
        "rsi": {
            "default": {"period": 14},
            "description": "RSI calculation period"
        }
    }

    # 默認參數
    DEFAULT_PARAMETERS = {
        "period": 14,
        "symbols": ["SPY", "QQQ", "IWM"],
        "position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.10,
        "oversold_threshold": 30,
        "overbought_threshold": 70,
        "signal_smoothing": False,
        "use_wilder_smoothing": True
    }

    # 必需參數
    REQUIRED_PARAMETERS = ["period"]

    # 可選參數
    OPTIONAL_PARAMETERS = {
        "oversold_threshold": {
            "type": (int, float),
            "default": 30,
            "min": 0,
            "max": 50
        },
        "overbought_threshold": {
            "type": (int, float),
            "default": 70,
            "min": 50,
            "max": 100
        },
        "signal_smoothing": {
            "type": bool,
            "default": False
        },
        "use_wilder_smoothing": {
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
        生成RSI信號

        Args:
            data: 價格數據，必須包含close列

        Returns:
            包含信號的DataFrame
        """
        try:
            df = data.copy()

            # 提取參數
            period = self.config["period"]
            oversold = self.config["oversold_threshold"]
            overbought = self.config["overbought_threshold"]
            smoothing = self.config["signal_smoothing"]
            wilder = self.config["use_wilder_smoothing"]

            # 檢查數據長度
            min_length = period * 3  # 需要足夠的數據計算RSI
            if len(df) < min_length:
                logger.warning(f"Insufficient data for RSI calculation (need {min_length} bars, have {len(df)})")
                return self._create_empty_signals(df)

            # 驗證閾值
            if oversold >= overbought:
                logger.error(f"Oversold threshold ({oversold}) must be less than overbought ({overbought})")
                return self._create_empty_signals(df)

            # 計算RSI
            rsi_col = "rsi"
            df[rsi_col] = self._calculate_rsi(df["close"], period, wilder)

            # 生成信號
            df["rsi_signal"] = 0
            df.loc[df[rsi_col] < oversold, "rsi_signal"] = 1  # 超賣，買入信號
            df.loc[df[rsi_col] > overbought, "rsi_signal"] = -1  # 超買，賣出信號

            # 應用信號平滑
            if smoothing:
                df["rsi_signal_smooth"] = df["rsi_signal"].rolling(window=3).apply(
                    lambda x: 1 if (x == 1).sum() >= 2 else (-1 if (x == -1).sum() >= 2 else 0)
                )
                signal_col = "rsi_signal_smooth"
            else:
                signal_col = "rsi_signal"

            # 檢測信號變化
            df["rsi_crossover"] = (df[signal_col] != df[signal_col].shift(1)).astype(int).fillna(0)

            # 持倉狀態
            df["rsi_position"] = np.where(
                df[signal_col] != 0,
                df[signal_col],
                np.where(
                    (df[signal_col] == 0) & (df["rsi_position"].shift(1) != 0),
                    df["rsi_position"].shift(1),
                    0
                )
            )

            # 信號元數據
            signal_types = {
                1: "buy",
                -1: "sell",
                0: "hold"
            }

            df["signal_type"] = df[signal_col].map(signal_types)
            df["rsi_value"] = df[rsi_col]
            df["rsi_distance"] = np.where(
                df[signal_col] == 1,
                oversold - df[rsi_col],
                np.where(
                    df[signal_col] == -1,
                    df[rsi_col] - overbought,
                    0
                )
            )

            # 添加交叉事件標記
            crossover_events = df[df["rsi_crossover"] != 0]
            if not crossover_events.empty:
                logger.info(
                    f"RSI crossover detected at {crossover_events.index[0]}: "
                    f"{crossover_events['signal_type'].iloc[0]} signal (RSI={crossover_events['rsi_value'].iloc[0]:.2f})"
                )

            return df

        except Exception as e:
            logger.error(f"Error generating RSI signals: {e}")
            raise

    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證RSI信號

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
            df = df[df["rsi_signal"].notna()]
            df = df[df["rsi_signal"] != 0]

            # 過濾連續相同的信號
            df["signal_change"] = df["rsi_signal"] != df["rsi_signal"].shift(1).fillna(0)
            df = df[df["signal_change"]]

            # 添加信號強度
            df["signal_strength"] = abs(df["rsi_distance"])

            # 驗證RSI值有效性
            df = df[(df["rsi_value"] >= 0) & (df["rsi_value"] <= 100)]

            return df

        except Exception as e:
            logger.error(f"Error validating RSI signals: {e}")
            raise

    def _calculate_rsi(self, prices: pd.Series, period: int, use_wilder: bool = True) -> pd.Series:
        """
        計算RSI指標

        Args:
            prices: 價格序列
            period: RSI週期
            use_wilder: 是否使用Wilder平滑方法

        Returns:
            RSI序列
        """
        delta = prices.diff()

        # 分離漲跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 計算平均漲跌
        if use_wilder:
            # Wilder's smoothing (exponential moving average)
            avg_gain = gain.ewm(com=period-1).mean()
            avg_loss = loss.ewm(com=period-1).mean()
        else:
            # Simple moving average
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

        # 計算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _create_empty_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建空的信號DataFrame"""
        signals = pd.DataFrame(index=df.index)
        signals["rsi_signal"] = 0
        signals["signal_type"] = "hold"
        signals["rsi_signal_smooth"] = 0
        signals["rsi_position"] = 0
        signals["rsi_crossover"] = 0
        signals["rsi_value"] = np.nan
        signals["rsi_distance"] = 0.0
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
                "avg_rsi": 0.0,
                "max_rsi": 0.0,
                "min_rsi": 0.0
            }

            # 執行策略獲取信號
            result = self.execute({symbol: df})
            signals_df = result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())

            if not signals_df.empty:
                symbol_analysis["signals_generated"] = len(signals_df)
                symbol_analysis["buy_signals"] = len(signals_df[signals_df["rsi_signal"] == 1])
                symbol_analysis["sell_signals"] = len(signals_df[signals_df["rsi_signal"] == -1])

            # 計算RSI統計
            if "rsi_value" in signals_df.columns:
                rsi_values = signals_df["rsi_value"].dropna()
                if not rsi_values.empty:
                    symbol_analysis["avg_rsi"] = rsi_values.mean()
                    symbol_analysis["max_rsi"] = rsi_values.max()
                    symbol_analysis["min_rsi"] = rsi_values.min()
                    symbol_analysis["oversold_hits"] = (rsi_values < self.config["oversold_threshold"]).sum()
                    symbol_analysis["overbought_hits"] = (rsi_values > self.config["overbought_threshold"]).sum()

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

        # 測試不同的RSI參數組合
        periods = [7, 14, 21, 28]
        oversold_levels = [20, 30, 40]
        overbought_levels = [60, 70, 80]

        best_sharpe = -float("inf")
        best_config = None

        for period in periods:
            for oversold in oversold_levels:
                for overbought in overbought_levels:
                    if oversold >= overbought:
                        continue

                    test_config = self.config.copy()
                    test_config["period"] = period
                    test_config["oversold_threshold"] = oversold
                    test_config["overbought_threshold"] = overbought

                    # 執行回測
                    backtest_result = self.backtest(data)
                    sharpe_ratio = backtest_result["backtest_results"].get("TEST", {}).get("sharpe_ratio", 0)

                    optimization_results["test_parameters"].append({
                        "period": period,
                        "oversold_threshold": oversold,
                        "overbought_threshold": overbought,
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
                f"oversold={best_config['oversold_threshold']}, "
                f"overbought={best_config['overbought_threshold']}"
            )

        return optimization_results