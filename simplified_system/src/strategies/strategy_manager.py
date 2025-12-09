#!/usr / bin / env python3
"""
Simplified System - Strategy Manager
简化系统 - 策略管理器

统一管理和协调所有交易策略的执行。
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base_strategy import BaseStrategy
from .bollinger_strategy import BollingerStrategy
from .macd_strategy import MACDStrategy
from .rsi_strategy import RSIStrategy

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """策略执行结果"""

    strategy_name: str
    parameters: Dict[str, Any]
    signals: pd.Series
    performance: Dict[str, float]
    execution_time: float
    timestamp: str


class StrategyManager:
    """策略管理器"""

    def __init__(self):
        """初始化策略管理器"""
        self.strategies: Dict[str, BaseStrategy] = {}
        self.results_history: List[StrategyResult] = []

        # 注册内置策略
        self._register_builtin_strategies()

        logger.info(
            "Strategy Manager initialized with %d strategies", len(self.strategies)
        )

    def _register_builtin_strategies(self):
        """注册内置策略"""
        builtin_strategies = [RSIStrategy(), MACDStrategy(), BollingerStrategy()]

        for strategy in builtin_strategies:
            self.register_strategy(strategy)

    def register_strategy(self, strategy: BaseStrategy):
        """注册策略"""
        self.strategies[strategy.name] = strategy
        logger.info(f"Registered strategy: {strategy.name}")

    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """获取策略"""
        return self.strategies.get(name)

    def list_strategies(self) -> List[str]:
        """列出所有可用策略"""
        return list(self.strategies.keys())

    def execute_strategy(
        self,
        strategy_name: str,
        data: pd.DataFrame,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[StrategyResult]:
        """
        执行单个策略

        Args:
            strategy_name: 策略名称
            data: 价格数据
            parameters: 策略参数

        Returns:
            策略执行结果
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            logger.error(f"Strategy not found: {strategy_name}")
            return None

        try:
            start_time = time.time()

            # 执行策略
            signals = strategy.execute(data, parameters or {})

            # 计算性能指标
            performance = strategy.calculate_performance(data, signals)

            execution_time = time.time() - start_time

            result = StrategyResult(
                strategy_name = strategy_name,
                parameters = parameters or {},
                signals = signals,
                performance = performance,
                execution_time = execution_time,
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S"),
            )

            # 保存结果历史
            self.results_history.append(result)

            logger.info(
                f"Strategy {strategy_name} executed in {execution_time:.3f}s, "
                f"Performance: {performance}"
            )

            return result

        except Exception as e:
            logger.error(f"Error executing strategy {strategy_name}: {e}")
            return None

    def execute_multiple_strategies(
        self,
        strategy_names: List[str],
        data: pd.DataFrame,
        parameters_dict: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[StrategyResult]:
        """
        执行多个策略

        Args:
            strategy_names: 策略名称列表
            data: 价格数据
            parameters_dict: 策略参数字典

        Returns:
            策略结果列表
        """
        results = []
        parameters_dict = parameters_dict or {}

        for strategy_name in strategy_names:
            parameters = parameters_dict.get(strategy_name)
            result = self.execute_strategy(strategy_name, data, parameters)
            if result:
                results.append(result)

        return results

    def optimize_strategy(
        self,
        strategy_name: str,
        data: pd.DataFrame,
        parameter_grid: Dict[str, List[Any]],
        metric: str = "sharpe_ratio",
    ) -> Tuple[StrategyResult, Dict[str, Any]]:
        """
        优化策略参数

        Args:
            strategy_name: 策略名称
            data: 价格数据
            parameter_grid: 参数网格
            metric: 优化指标

        Returns:
            最佳结果和最佳参数
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            logger.error(f"Strategy not found: {strategy_name}")
            return None, {}

        best_result = None
        best_params = {}
        best_metric_value = float("-inf")

        total_combinations = 1
        for param_values in parameter_grid.values():
            total_combinations *= len(param_values)

        logger.info(
            f"Starting optimization for {strategy_name}: {total_combinations} combinations"
        )

        tested_combinations = 0
        for params in strategy._generate_parameter_combinations(parameter_grid):
            tested_combinations += 1

            if tested_combinations % 100 == 0:
                logger.info(
                    f"Tested {tested_combinations}/{total_combinations} combinations"
                )

            result = self.execute_strategy(strategy_name, data, params)
            if result and result.performance:
                metric_value = result.performance.get(metric, 0)
                if metric_value > best_metric_value:
                    best_metric_value = metric_value
                    best_result = result
                    best_params = params

        logger.info(
            f"Optimization completed. Best {metric}: {best_metric_value:.4f}, "
            f"Parameters: {best_params}"
        )

        return best_result, best_params

    def compare_strategies(
        self,
        strategy_names: List[str],
        data: pd.DataFrame,
        parameters_dict: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> pd.DataFrame:
        """
        比较多个策略的性能

        Args:
            strategy_names: 策略名称列表
            data: 价格数据
            parameters_dict: 策略参数字典

        Returns:
            比较结果DataFrame
        """
        results = self.execute_multiple_strategies(
            strategy_names, data, parameters_dict
        )

        comparison_data = []
        for result in results:
            comparison_data.append(
                {
                    "Strategy": result.strategy_name,
                    "Total Return": result.performance.get("total_return", 0),
                    "Sharpe Ratio": result.performance.get("sharpe_ratio", 0),
                    "Max Drawdown": result.performance.get("max_drawdown", 0),
                    "Win Rate": result.performance.get("win_rate", 0),
                    "Execution Time (s)": result.execution_time,
                }
            )

        return pd.DataFrame(comparison_data).sort_values(
            "Sharpe Ratio", ascending = False
        )

    def get_strategy_summary(self) -> Dict[str, Any]:
        """获取策略管理器摘要"""
        return {
            "total_strategies": len(self.strategies),
            "available_strategies": list(self.strategies.keys()),
            "total_executions": len(self.results_history),
            "last_execution": (
                self.results_history[-1].timestamp if self.results_history else None
            ),
        }


# 全局策略管理器实例
_strategy_manager = None


def get_strategy_manager() -> StrategyManager:
    """获取策略管理器单例"""
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager


if __name__ == "__main__":
    # 测试策略管理器
    print("Testing Strategy Manager...")

    manager = get_strategy_manager()

    # 显示可用策略
    print(f"Available strategies: {manager.list_strategies()}")

    # 获取摘要
    summary = manager.get_strategy_summary()
    print(f"Strategy Manager Summary: {summary}")

    print("\n✅ Strategy Manager test completed successfully!")
