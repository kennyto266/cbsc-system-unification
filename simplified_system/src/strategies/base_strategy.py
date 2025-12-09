#!/usr / bin / env python3
"""
Simplified System - Base Strategy
简化系统 - 基础策略类

所有交易策略的基类，定义通用接口和方法。
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """基础策略抽象类"""

    def __init__(self, name: str):
        """
        初始化策略

        Args:
            name: 策略名称
        """
        self.name = name
        self.default_parameters = self._get_default_parameters()
        self.description = self._get_description()

    @abstractmethod
    def _get_default_parameters(self) -> Dict[str, Any]:
        """获取默认参数"""

    @abstractmethod
    def _get_description(self) -> str:
        """获取策略描述"""

    @abstractmethod
    def generate_signals(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> pd.Series:
        """
        生成交易信号

        Args:
            data: 价格数据，必须包含'close'列
            parameters: 策略参数

        Returns:
            交易信号序列 (1 = 买入, 0 = 持有, -1 = 卖出)
        """

    def execute(
        self, data: pd.DataFrame, parameters: Optional[Dict[str, Any]] = None
    ) -> pd.Series:
        """
        执行策略

        Args:
            data: 价格数据
            parameters: 策略参数，如果为None则使用默认参数

        Returns:
            交易信号序列
        """
        if not isinstance(data, pd.DataFrame) or "close" not in data.columns:
            raise ValueError("Data must be a DataFrame with 'close' column")

        # 使用默认参数如果没有提供
        if parameters is None:
            parameters = self.default_parameters

        # 验证参数
        self._validate_parameters(parameters)

        try:
            signals = self.generate_signals(data, parameters)
            logger.info(f"Generated {len(signals)} signals for strategy {self.name}")
            return signals
        except Exception as e:
            logger.error(f"Error generating signals for {self.name}: {e}")
            raise

    def _validate_parameters(self, parameters: Dict[str, Any]):
        """验证参数"""
        required_params = set(self.default_parameters.keys())
        provided_params = set(parameters.keys())

        missing_params = required_params - provided_params
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")

        # 检查参数范围
        for param, value in parameters.items():
            if param in self.default_parameters:
                default_value = self.default_parameters[param]
                if not isinstance(value, type(default_value)):
                    raise TypeError(
                        f"Parameter {param} should be {type(default_value)}, got {type(value)}"
                    )

    def calculate_performance(
        self, data: pd.DataFrame, signals: pd.Series
    ) -> Dict[str, float]:
        """
        计算策略性能指标

        Args:
            data: 价格数据
            signals: 交易信号

        Returns:
            性能指标字典
        """
        if len(signals) != len(data):
            raise ValueError("Signals length must match data length")

        try:
            # 计算收益率
            returns = data["close"].pct_change().dropna()

            # 根据信号计算策略收益率
            strategy_returns = returns * signals.shift(1).dropna()

            # 计算性能指标
            total_return = (1 + strategy_returns).prod() - 1
            sharpe_ratio = self._calculate_sharpe_ratio(strategy_returns)
            max_drawdown = self._calculate_max_drawdown(strategy_returns)
            win_rate = self._calculate_win_rate(strategy_returns)

            return {
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "annual_return": (1 + total_return) ** (252 / len(strategy_returns))
                - 1,
            }

        except Exception as e:
            logger.error(f"Error calculating performance: {e}")
            return {}

    def _calculate_sharpe_ratio(
        self, returns: pd.Series, risk_free_rate: float = 0.03
    ) -> float:
        """计算Sharpe比率"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        daily_risk_free = risk_free_rate / 252
        excess_returns = returns - daily_risk_free

        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        if len(returns) == 0:
            return 0.0

        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        return drawdown.min()

    def _calculate_win_rate(self, returns: pd.Series) -> float:
        """计算胜率"""
        if len(returns) == 0:
            return 0.0

        winning_trades = (returns > 0).sum()
        total_trades = len(returns)

        return winning_trades / total_trades if total_trades > 0 else 0.0

    def _generate_parameter_combinations(
        self, parameter_grid: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """
        生成参数组合

        Args:
            parameter_grid: 参数网格

        Returns:
            参数组合列表
        """
        import itertools

        if not parameter_grid:
            return [{}]

        keys = list(parameter_grid.keys())
        values = list(parameter_grid.values())

        combinations = []
        for combination in itertools.product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)

        return combinations

    def get_parameter_ranges(self) -> Dict[str, List[Any]]:
        """
        获取推荐的参数优化范围

        Returns:
            参数范围字典
        """
        return self._get_optimization_ranges()

    @abstractmethod
    def _get_optimization_ranges(self) -> Dict[str, List[Any]]:
        """获取参数优化范围"""

    def get_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            "name": self.name,
            "description": self.description,
            "default_parameters": self.default_parameters,
            "optimization_ranges": self.get_parameter_ranges(),
        }
