"""
Base Technical Indicator Strategy
技術指標策略基類

為所有技術指標策略提供統一的基礎實現
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


class BaseTechnicalIndicatorStrategy(BaseStrategy, ABC):
    """
    Technical Indicator Strategy Base Class

    提供技術指標策略的通用功能和接口
    """

    # 策略元數據（由子類覆蓋）
    STRATEGY_NAME: str = ""
    STRATEGY_TYPE: StrategyType = StrategyType.TECHNICAL_ANALYSIS
    DESCRIPTION: str = ""
    VERSION: str = "1.0.0"
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
        """初始化技術指標策略"""
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

                results[symbol] = {
                    "signals": risk_managed_signals,
                    "indicators": df.columns.tolist(),
                    "last_price": df["close"].iloc[-1],
                    "timestamp": df.index[-1]
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
                # 根�配置初始化指標
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

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        df = df.copy()

        # 計算通用指標
        if "close" in df.columns:
            # 基本統計
            df["returns"] = df["close"].pct_change()
            df["log_returns"] = np.log(df["close"] / df["close"].shift(1))

            # 移動平均
            for window in [5, 10, 20, 50, 200]:
                if window <= len(df):
                    df[f"sma_{window}"] = df["close"].rolling(window=window).mean()
                    df[f"ema_{window}"] = df["close"].ewm(span=window).mean()

        return df

    def _apply_risk_management(self, signals: pd.DataFrame) -> pd.DataFrame:
        """應用風險管理規則"""
        if signals.empty:
            return signals

        df = signals.copy()

        # 默認風險規則
        risk_rules = self.config.get("risk_rules", {
            "max_positions": 5,
            "max_loss_per_trade": 0.05,
            "max_drawdown": 0.20,
            "use_stop_loss": True,
            "use_take_profit": True
        })

        # 應用倉位限制
        if "signal" in df.columns and risk_rules["max_positions"]:
            position_count = df[df["signal"] != 0].shape[0]
            if position_count > risk_rules["max_positions"]:
                # 保留最近的信號
                df = df.groupby((df["signal"] != 0).cumsum()).apply(
                    lambda x: x if x.name <= risk_rules["max_positions"] else None
                )
                df = df.dropna(subset=["signal"])

        # 應用止損止盈
        if "close" in df.columns:
            df = self._apply_stop_loss_take_profit(df, risk_rules)

        return df

    def _apply_stop_loss_take_profit(self, df: pd.DataFrame, risk_rules: Dict[str, Any]) -> pd.DataFrame:
        """應用止損止盈邏輯"""
        if "signal" in df.columns and risk_rules["use_stop_loss"]:
            df["stop_loss"] = df["close"] * (1 - risk_rules["max_loss_per_trade"])

        if "signal" in df.columns and risk_rules["use_take_profit"]:
            profit_target = risk_rules.get("profit_target", 0.10)
            df["take_profit"] = df["close"] * (1 + profit_target)

        return df

    def _update_strategy_state(self, results: Dict[str, Any]) -> None:
        """更新策略狀態"""
        total_signals = sum(len(r.get("signals", pd.DataFrame())) for r in results.values())

        self._strategy_state.update({
            "last_execution": datetime.utcnow().isoformat(),
            "total_signals": total_signals,
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
            "sharpe_ratio": 0.0
        }

        # 這裡可以添加具體的性能計算邏輯
        # 例如計算勝率、回報率、夏普比率等

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
                    "signals": result.get("results", {}).get(symbol, {}).get("signals", pd.DataFrame())
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