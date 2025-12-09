#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Classes and Interfaces
統一基礎類和接口定義，為整個系統提供一致的抽象層

This module provides the foundational base classes for the unified quantitative trading
system architecture, establishing consistent interfaces and abstractions across all
components.

Core Classes:
- BaseComponent: 系統組件基類
- BaseIndicator: 技術指標基類
- BaseStrategy: 交易策略基類
- BaseBacktest: 回測引擎基類

Author: Architecture Consolidation Team
Date: 2025-11-30
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class BaseConfig:
    """基礎配置類"""
    name: str
    version: str = "1.0.0"
    enabled: bool = True
    debug: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseComponent(ABC):
    """
    系統組件基類

    為所有系統組件提供統一的接口和通用功能：
    - 配置管理
    - 日誌記錄
    - 狀態管理
    - 生命周期管理
    """

    def __init__(self, config: BaseConfig):
        self.config = config
        self.name = config.name
        self.version = config.version
        self.enabled = config.enabled
        self.debug = config.debug
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        # 組件狀態
        self._state = "initialized"
        self._error_count = 0
        self._last_error = None
        self._created_at = datetime.now()

        if self.debug:
            self.logger.setLevel(logging.DEBUG)

        self.logger.info(f"Component {self.name} v{self.version} initialized")

    @property
    def state(self) -> str:
        """獲取組件狀態"""
        return self._state

    @property
    def is_healthy(self) -> bool:
        """檢查組件健康狀態"""
        return self._state == "running" and self._error_count == 0

    def start(self) -> bool:
        """啟動組件"""
        try:
            self.logger.info(f"Starting component {self.name}")
            self._on_start()
            self._state = "running"
            self.logger.info(f"Component {self.name} started successfully")
            return True
        except Exception as e:
            self._handle_error(e, "start")
            return False

    def stop(self) -> bool:
        """停止組件"""
        try:
            self.logger.info(f"Stopping component {self.name}")
            self._on_stop()
            self._state = "stopped"
            self.logger.info(f"Component {self.name} stopped successfully")
            return True
        except Exception as e:
            self._handle_error(e, "stop")
            return False

    def reset(self) -> bool:
        """重置組件狀態"""
        try:
            self.logger.info(f"Resetting component {self.name}")
            self._on_reset()
            self._state = "initialized"
            self._error_count = 0
            self._last_error = None
            self.logger.info(f"Component {self.name} reset successfully")
            return True
        except Exception as e:
            self._handle_error(e, "reset")
            return False

    @abstractmethod
    def _on_start(self) -> None:
        """啟動時執行的具體邏輯"""
        pass

    @abstractmethod
    def _on_stop(self) -> None:
        """停止時執行的具體邏輯"""
        pass

    def _on_reset(self) -> None:
        """重置時執行的具體邏輯"""
        pass

    def _handle_error(self, error: Exception, operation: str) -> None:
        """處理錯誤"""
        self._error_count += 1
        self._last_error = str(error)
        self._state = "error"
        self.logger.error(f"Error in {self.name}.{operation}: {error}")

    def get_status(self) -> Dict[str, Any]:
        """獲取組件狀態"""
        return {
            'name': self.name,
            'version': self.version,
            'state': self._state,
            'enabled': self.enabled,
            'healthy': self.is_healthy,
            'error_count': self._error_count,
            'last_error': self._last_error,
            'created_at': self._created_at.isoformat()
        }

@dataclass
class IndicatorResult:
    """技術指標結果"""
    name: str
    values: Union[np.ndarray, pd.Series]
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    computation_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

class BaseIndicator(BaseComponent):
    """
    技術指標基類

    為所有技術指標提供統一的接口：
    - 統一計算接口
    - 參數驗證
    - 結果格式化
    - 性能監控
    """

    def __init__(self, config: BaseConfig):
        super().__init__(config)
        self._parameters = {}
        self._last_result = None

    @abstractmethod
    def calculate(self, data: Union[pd.DataFrame, pd.Series, np.ndarray],
                   **kwargs) -> IndicatorResult:
        """
        計算技術指標

        Args:
            data: 價格數據 (OHLCV)
            **kwargs: 指標參數

        Returns:
            IndicatorResult: 計算結果
        """
        pass

    @abstractmethod
    def validate_parameters(self, **kwargs) -> bool:
        """驗證指標參數"""
        pass

    def calculate_with_validation(self, data: Union[pd.DataFrame, pd.Series, np.ndarray],
                                 **kwargs) -> IndicatorResult:
        """帶參數驗證的計算"""
        if not self.validate_parameters(**kwargs):
            raise ValueError(f"Invalid parameters for {self.name}: {kwargs}")

        return self.calculate(data, **kwargs)

    def get_last_result(self) -> Optional[IndicatorResult]:
        """獲取最後計算結果"""
        return self._last_result

    def _store_result(self, result: IndicatorResult) -> None:
        """存儲計算結果"""
        self._last_result = result

@dataclass
class Signal:
    """交易信號"""
    symbol: str
    timestamp: datetime
    action: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0-1
    strength: float  # 信號強度
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseStrategy(BaseComponent):
    """
    交易策略基類

    為所有交易策略提供統一的接口：
    - 統一信號生成接口
    - 風險管理集成
    - 策略性能追蹤
    - 回測兼容性
    """

    def __init__(self, config: BaseConfig):
        super().__init__(config)
        self._indicators = {}
        self._signals_history = []
        self._performance_metrics = {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame, **kwargs) -> List[Signal]:
        """
        生成交易信號

        Args:
            data: 市場數據
            **kwargs: 策略參數

        Returns:
            List[Signal]: 生成的交易信號列表
        """
        pass

    def add_indicator(self, name: str, indicator: BaseIndicator) -> None:
        """添加技術指標"""
        self._indicators[name] = indicator
        self.logger.debug(f"Added indicator {name} to strategy {self.name}")

    def get_indicator(self, name: str) -> Optional[BaseIndicator]:
        """獲取技術指標"""
        return self._indicators.get(name)

    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, IndicatorResult]:
        """計算所有指標"""
        results = {}
        for name, indicator in self._indicators.items():
            try:
                result = indicator.calculate_with_validation(data)
                results[name] = result
            except Exception as e:
                self.logger.error(f"Error calculating {name}: {e}")
        return results

    def get_signals_history(self, limit: Optional[int] = None) -> List[Signal]:
        """獲取信號歷史"""
        if limit is None:
            return self._signals_history.copy()
        return self._signals_history[-limit:]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取策略性能指標"""
        return {
            'total_signals': len(self._signals_history),
            'indicators_count': len(self._indicators),
            **self._performance_metrics
        }

@dataclass
class BacktestResult:
    """回測結果"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    losing_trades: int
    equity_curve: pd.Series
    trades_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseBacktest(BaseComponent):
    """
    回測引擎基類

    為所有回測引擎提供統一的接口：
    - 統一回測流程
    - 結果標準化
    - 性能指標計算
    - 風險評估
    """

    def __init__(self, config: BaseConfig):
        super().__init__(config)
        self._strategies = {}
        self._results_cache = {}

    @abstractmethod
    def run_backtest(self, strategy: BaseStrategy, data: pd.DataFrame,
                    initial_capital: float = 100000, **kwargs) -> BacktestResult:
        """
        運行回測

        Args:
            strategy: 交易策略
            data: 歷史數據
            initial_capital: 初始資金
            **kwargs: 回測參數

        Returns:
            BacktestResult: 回測結果
        """
        pass

    def add_strategy(self, name: str, strategy: BaseStrategy) -> None:
        """添加回測策略"""
        self._strategies[name] = strategy
        self.logger.debug(f"Added strategy {name} to backtest engine {self.name}")

    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """獲取回測策略"""
        return self._strategies.get(name)

    def run_strategy_backtest(self, strategy_name: str, data: pd.DataFrame,
                             initial_capital: float = 100000, **kwargs) -> BacktestResult:
        """運行指定策略回測"""
        strategy = self.get_strategy(strategy_name)
        if strategy is None:
            raise ValueError(f"Strategy {strategy_name} not found")

        return self.run_backtest(strategy, data, initial_capital, **kwargs)

    def get_cached_result(self, strategy_name: str, data_hash: str) -> Optional[BacktestResult]:
        """獲取緩存的回測結果"""
        cache_key = f"{strategy_name}_{data_hash}"
        return self._results_cache.get(cache_key)

    def cache_result(self, strategy_name: str, data_hash: str, result: BacktestResult) -> None:
        """緩存回測結果"""
        cache_key = f"{strategy_name}_{data_hash}"
        self._results_cache[cache_key] = result
        self.logger.debug(f"Cached backtest result for {strategy_name}")

# 導出主要類
__all__ = [
    'BaseComponent',
    'BaseConfig',
    'BaseIndicator',
    'IndicatorResult',
    'BaseStrategy',
    'Signal',
    'BaseBacktest',
    'BacktestResult'
]