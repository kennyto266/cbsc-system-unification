"""
Base Volume Strategy
成交量策略基類

為所有成交量策略提供統一的基礎實現
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4

import pandas as pd
import numpy as np

from ..base import BaseStrategy
from ..enhanced_factory import StrategyMetadata, StrategyType
from ...core.exceptions import StrategyError, StrategyValidationError

logger = logging.getLogger(__name__)


class BaseVolumeStrategy(BaseStrategy, ABC):
    """
    Volume Strategy Base Class

    提供成交量策略的通用功能和接口
    """

    # 策略元數據（由子類覆蓋）
    STRATEGY_NAME: str = ""
    STRATEGY_TYPE: StrategyType = StrategyType.VOLUME
    DESCRIPTION: str = ""
    VERSION: str = "2.0.0"
    AUTHOR: str = "CBSC Team"

    # 指標配置
    INDICATORS: Dict[str, Dict[str, Any]] = {}

    # 默認參數配置
    DEFAULT_PARAMETERS: Dict[str, Any] = {}

    # 必需參數
    REQUIRED_PARAMETERS: List[str] = []

    # 可選參數
    OPTIONAL_PARAMETERS: Dict[str, Dict[str, Any]] = {}

    # 支持的時間週期
    SUPPORTED_TIMEFRAMES: List[str] = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

    def __init__(self, instance_id: uuid4, config: Dict[str, Any], metadata: StrategyMetadata):
        """初始化成交量策略"""
        super().__init__(instance_id, config, metadata)

        # 驗證配置
        self._validate_config()

        # 初始化參數
        self._initialize_parameters()

        # 初始化指標計算器
        self._initialize_indicators()

        # 策略狀態
        self._strategy_state = {
            "signals": [],
            "positions": {},
            "performance": {},
            "volume_profile": {},
            "last_updated": None
        }

        logger.info(f"Initialized {self.STRATEGY_NAME} strategy")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信號

        Args:
            data: 價格數據，包含OHLCV列

        Returns:
            包含信號的DataFrame
        """
        pass

    @abstractmethod
    def validate_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        驗證和過濾信號

        Args:
            signals: 原始信號數據

        Returns:
            驗證後的信號數據
        """
        pass

    def execute(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        執行策略

        Args:
            data: 符號數據字典，鍵為符號名稱

        Returns:
            執行結果字典
        """
        try:
            results = {}

            for symbol, df in data.items():
                if df.empty:
                    logger.warning(f"No data for symbol {symbol}")
                    continue

                # 驗證數據格式
                self._validate_dataframe(df)

                # 計算指標
                df = self._calculate_indicators(df)

                # 生成信號
                signals = self.generate_signals(df)

                # 驗證信號
                validated_signals = self.validate_signals(signals)

                # 執行風險管理
                risk_managed_signals = self._apply_risk_management(validated_signals)

                # 計算成交量分析
                volume_analysis = self._calculate_volume_analysis(df)

                results[symbol] = {
                    "signals": risk_managed_signals,
                    "indicators": df.columns.tolist(),
                    "last_price": df["close"].iloc[-1],
                    "timestamp": df.index[-1],
                    "volume_analysis": volume_analysis
                }

            # 更新策略狀態
            self._update_strategy_state(results)

            return {
                "strategy_id": str(self.instance_id),
                "strategy_name": self.STRATEGY_NAME,
                "execution_time": datetime.utcnow().isoformat(),
                "results": results,
                "state": self._strategy_state
            }

        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")
            raise StrategyError(f"Strategy execution failed: {e}") from e

    def _validate_config(self) -> None:
        """驗證策略配置"""
        # 檢查必需參數
        for param in self.REQUIRED_PARAMETERS:
            if param not in self.config:
                raise StrategyValidationError(f"Required parameter '{param}' is missing")

        # 檢查參數範圍
        for param, value in self.config.items():
            if param in self.OPTIONAL_PARAMETERS:
                param_config = self.OPTIONAL_PARAMETERS[param]

                # 類型檢查
                expected_type = param_config.get("type")
                if expected_type and not isinstance(value, expected_type):
                    raise StrategyValidationError(
                        f"Parameter '{param}' must be of type {expected_type.__name__}, got {type(value).__name__}"
                    )

                # 範圍檢查
                min_val = param_config.get("min")
                max_val = param_config.get("max")

                if min_val is not None and value < min_val:
                    raise StrategyValidationError(
                        f"Parameter '{param}' must be >= {min_val}, got {value}"
                    )

                if max_val is not None and value > max_val:
                    raise StrategyValidationError(
                        f"Parameter '{param}' must be <= {max_val}, got {value}"
                    )

    def _initialize_parameters(self) -> None:
        """初始化策略參數"""
        # 合併默認參數
        for param, default_value in self.DEFAULT_PARAMETERS.items():
            if param not in self.config:
                self.config[param] = default_value

    def _initialize_indicators(self) -> None:
        """初始化指標計算器"""
        self.indicators = {}

        for indicator_name, indicator_config in self.INDICATORS.items():
            try:
                # 根據配置初始化指標
                indicator_params = self.config.get(indicator_name, {})
                self.indicators[indicator_name] = {
                    "config": {**indicator_config.get("default", {}), **indicator_params},
                    "calculated": False,
                    "values": []
                }
                logger.debug(f"Initialized indicator: {indicator_name}")
            except Exception as e:
                logger.error(f"Failed to initialize indicator {indicator_name}: {e}")

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """驗證數據框格式"""
        required_columns = ["open", "high", "low", "close", "volume"]

        for col in required_columns:
            if col not in df.columns:
                raise StrategyValidationError(f"Required column '{col}' missing from data")

        # 檢查成交量有效性
        if (df["volume"] <= 0).any():
            logger.warning("Zero or negative volume values detected")

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算成交量指標"""
        df = df.copy()

        # 計算基本成交量指標
        if "volume" in df.columns:
            # 成交量移動平均
            for period in [5, 10, 20, 50]:
                if period <= len(df):
                    df[f"volume_ma_{period}"] = df["volume"].rolling(window=period).mean()
                    df[f"volume_ratio_{period}"] = df["volume"] / df[f"volume_ma_{period}"]

            # 成交量變化率
            df["volume_change"] = df["volume"].pct_change()
            df["volume_change_pct"] = df["volume_change"] * 100

            # 價格成交量關聯
            df["price_volume"] = df["close"] * df["volume"]
            df["volume_price_trend"] = (df["price_volume"] - df["price_volume"].shift(1)) / df["volume"]

            # 成交量標準化
            df["volume_normalized"] = (df["volume"] - df["volume"].rolling(window=20).mean()) / df["volume"].rolling(window=20).std()

        # 計算價格相關指標
        if "close" in df.columns:
            df["price_change"] = df["close"].pct_change()
            df["returns"] = df["price_change"]

            # 成交量加權價格
            df["vwap_simple"] = (df["price_volume"].cumsum() / df["volume"].cumsum())

            # 價格與成交量相關性
            if len(df) >= 20:
                df["price_volume_corr"] = df["returns"].rolling(window=20).corr(df["volume_change"])

        return df

    def _calculate_volume_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算成交量分析"""
        try:
            if df.empty or len(df) < 10:
                return {"strength": 0.0, "trend": "neutral"}

            # 成交量強度
            avg_volume = df["volume"].mean()
            current_volume = df["volume"].iloc[-1]
            volume_strength = current_volume / avg_volume if avg_volume > 0 else 1.0

            # 成交量趨勢
            volume_ma_20 = df["volume"].rolling(window=20).mean().iloc[-1]
            volume_ma_5 = df["volume"].rolling(window=5).mean().iloc[-1]

            if volume_ma_5 > volume_ma_20 * 1.2:
                volume_trend = "increasing"
            elif volume_ma_5 < volume_ma_20 * 0.8:
                volume_trend = "decreasing"
            else:
                volume_trend = "stable"

            # 成交量異常檢測
            volume_std = df["volume"].rolling(window=20).std().iloc[-1]
            is_anomaly = abs(current_volume - avg_volume) > 2 * volume_std

            # 價量配合分析
            if "price_change" in df.columns:
                recent_price_change = df["price_change"].tail(5).mean()
                if recent_price_change > 0 and volume_strength > 1.2:
                    price_volume_relation = "bullish_confirm"
                elif recent_price_change < 0 and volume_strength > 1.2:
                    price_volume_relation = "bearish_confirm"
                elif abs(recent_price_change) > 0.02 and volume_strength < 0.8:
                    price_volume_relation = "divergence"
                else:
                    price_volume_relation = "neutral"
            else:
                price_volume_relation = "neutral"

            return {
                "strength": min(volume_strength, 3.0),  # 限制最大值
                "trend": volume_trend,
                "is_anomaly": is_anomaly,
                "price_volume_relation": price_volume_relation,
                "current_volume": current_volume,
                "avg_volume": avg_volume,
                "volume_ratio_20": df["volume"].iloc[-1] / df["volume"].tail(20).mean() if len(df) >= 20 else 1.0
            }

        except Exception as e:
            logger.error(f"Error calculating volume analysis: {e}")
            return {"strength": 0.0, "trend": "neutral"}

    def _apply_risk_management(self, signals: pd.DataFrame) -> pd.DataFrame:
        """應用風險管理規則"""
        if signals.empty:
            return signals

        df = signals.copy()

        # 默認風險規則
        risk_rules = self.config.get("risk_rules", {
            "max_positions": 3,
            "max_loss_per_trade": 0.04,
            "max_drawdown": 0.20,
            "use_stop_loss": True,
            "use_take_profit": True,
            "min_volume_strength": 1.0
        })

        # 應用成交量強度過濾
        if "volume_strength" in df.columns and risk_rules["min_volume_strength"]:
            df = df[df["volume_strength"] >= risk_rules["min_volume_strength"]]

        # 應用倉位限制
        if "signal" in df.columns and risk_rules["max_positions"]:
            position_count = df[df["signal"] != 0].shape[0]
            if position_count > risk_rules["max_positions"]:
                # 保留強度最高的信號
                df = df.nlargest(risk_rules["max_positions"], "volume_strength")

        # 應用止損止盈
        if "close" in df.columns:
            df = self._apply_stop_loss_take_profit(df, risk_rules)

        return df

    def _apply_stop_loss_take_profit(self, df: pd.DataFrame, risk_rules: Dict[str, Any]) -> pd.DataFrame:
        """應用止損止盈邏輯"""
        if "signal" in df.columns and risk_rules["use_stop_loss"]:
            df["stop_loss"] = df["close"] * (1 - risk_rules["max_loss_per_trade"])

        if "signal" in df.columns and risk_rules["use_take_profit"]:
            profit_target = risk_rules.get("profit_target", 0.20)
            df["take_profit"] = df["close"] * (1 + profit_target)

        return df

    def _update_strategy_state(self, results: Dict[str, Any]) -> None:
        """更新策略狀態"""
        total_signals = sum(len(r.get("signals", pd.DataFrame())) for r in results.values())

        # 計算平均成交量強度
        volume_strengths = [r.get("volume_analysis", {}).get("strength", 0) for r in results.values()]
        avg_volume_strength = np.mean(volume_strengths) if volume_strengths else 0

        self._strategy_state.update({
            "last_execution": datetime.utcnow().isoformat(),
            "total_signals": total_signals,
            "avg_volume_strength": avg_volume_strength,
            "active_positions": self._strategy_state.get("active_positions", 0),
            "performance": self._calculate_performance_metrics(results)
        })

    def _calculate_performance_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """計算性能指標"""
        metrics = {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_loss": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "avg_volume_strength": 0.0
        }

        # 計算平均成交量強度
        volume_strengths = [r.get("volume_analysis", {}).get("strength", 0) for r in results.values()]
        if volume_strengths:
            metrics["avg_volume_strength"] = np.mean(volume_strengths)

        return metrics

    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "name": self.STRATEGY_NAME,
            "type": self.STRATEGY_TYPE,
            "description": self.DESCRIPTION,
            "version": self.VERSION,
            "author": self.AUTHOR,
            "parameters": self.config,
            "indicators": self.INDICATORS,
            "supported_timeframes": self.SUPPORTED_TIMEFRAMES,
            "required_parameters": self.REQUIRED_PARAMETERS,
            "optional_parameters": self.OPTIONAL_PARAMETERS
        }

    def backtest(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        回測策略

        Args:
            data: 歷史數據字典

        Returns:
            回測結果
        """
        backtest_results = {}

        for symbol, df in data.items():
            if df.empty:
                continue

            # 執行回測
            try:
                result = self.execute({symbol: df})
                backtest_results[symbol] = {
                    "total_return": self._calculate_total_return(df),
                    "max_drawdown": self._calculate_max_drawdown(df),
                    "sharpe_ratio": self._calculate_sharpe_ratio(df),
                    "total_trades": len(result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())),
                    "signals": result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame()),
                    "volume_analysis": result.get("results", {}).get(symbol, {}).get("volume_analysis", {})
                }
            except Exception as e:
                logger.error(f"Backtest failed for {symbol}: {e}")
                backtest_results[symbol] = {"error": str(e)}

        return {
            "strategy": self.get_strategy_info(),
            "backtest_results": backtest_results,
            "backtest_period": {
                "start": min(df.index.min() for df in data.values() if not df.empty),
                "end": max(df.index.max() for df in data.values() if not df.empty)
            }
        }

    def _calculate_total_return(self, df: pd.DataFrame) -> float:
        """計算總回報率"""
        if "close" in df.columns and len(df) > 1:
            return (df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0]
        return 0.0

    def _calculate_max_drawdown(self, df: pd.DataFrame) -> float:
        """計算最大回撤"""
        if "close" in df.columns:
            cumulative = (1 + df["close"].pct_change()).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            return drawdown.min()
        return 0.0

    def _calculate_sharpe_ratio(self, df: pd.DataFrame) -> float:
        """計算夏普比率"""
        returns = df["close"].pct_change().dropna()
        if len(returns) > 1:
            return np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0.0
        return 0.0