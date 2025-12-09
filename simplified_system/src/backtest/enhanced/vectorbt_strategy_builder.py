#!/usr / bin / env python3
"""
Simplified System - VectorBT策略構建器
集成Cookbook策略到現有VectorBTEngine系統

這個模塊充當適配器，將Cookbook中的專業策略
與現有的Simplified System無縫集成。
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from .cookbook_strategies.ma_crossover_strategy import (
    ma_crossover_strategy,
    optimize_ma_crossover,
)
from .cookbook_strategies.rsi_mean_reversion_strategy import (
    optimize_rsi_strategy,
    rsi_mean_reversion_strategy,
    rsi_with_stop_loss_strategy,
)

logger = logging.getLogger(__name__)


@dataclass
class StrategyConfig:
    """策略配置"""

    name: str
    description: str
    strategy_func: Callable
    default_params: Dict[str, Any]
    param_ranges: Dict[str, List[Any]]
    optimization_func: Optional[Callable] = None


class CookbookStrategyBuilder:
    """
    Cookbook策略構建器

    提供統一的接口來使用Cookbook中的專業策略，
    同時保持與現有Simplified System的兼容性。
    """

    def __init__(self):
        """初始化策略構建器"""
        self.strategies = self._initialize_strategies()
        logger.info(f"初始化Cookbook策略構建器，加載了 {len(self.strategies)} 個策略")

    def _initialize_strategies(self) -> Dict[str, StrategyConfig]:
        """初始化所有可用的Cookbook策略"""
        strategies = {}

        # MA交叉策略
        strategies["MA_CROSSOVER"] = StrategyConfig(
            name="MA_CROSSOVER",
            description="雙移動平均線交叉策略 - 經典趨勢跟蹤策略",
            strategy_func = ma_crossover_strategy,
            default_params={"fast_window": 10, "slow_window": 30, "direction": "both"},
            param_ranges={
                "fast_window": list(range(5, 21, 5)),
                "slow_window": list(range(20, 61, 10)),
            },
            optimization_func = optimize_ma_crossover,
        )

        # RSI均值回歸策略
        strategies["RSI_MEAN_REVERSION"] = StrategyConfig(
            name="RSI_MEAN_REVERSION",
            description="RSI均值回歸策略 - 經典震盪策略",
            strategy_func = rsi_mean_reversion_strategy,
            default_params={"rsi_period": 14, "oversold": 30, "overbought": 70},
            param_ranges={
                "rsi_period": [10, 14, 20, 30],
                "oversold": [20, 25, 30],
                "overbought": [70, 75, 80],
            },
            optimization_func = optimize_rsi_strategy,
        )

        # RSI帶止損策略
        strategies["RSI_WITH_STOP_LOSS"] = StrategyConfig(
            name="RSI_WITH_STOP_LOSS",
            description="RSI均值回歸策略（帶止損） - 風險控制版本",
            strategy_func = rsi_with_stop_loss_strategy,
            default_params={
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70,
                "stop_loss": 0.05,
            },
            param_ranges={
                "rsi_period": [10, 14, 20, 30],
                "oversold": [20, 25, 30],
                "overbought": [70, 75, 80],
                "stop_loss": [0.03, 0.05, 0.08, 0.10],
            },
        )

        return strategies

    def get_available_strategies(self) -> List[str]:
        """
        獲取所有可用策略列表

        Returns:
            List[str]: 策略名稱列表
        """
        return list(self.strategies.keys())

    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取策略信息

        Args:
            strategy_name: 策略名稱

        Returns:
            Optional[Dict[str, Any]]: 策略信息
        """
        if strategy_name not in self.strategies:
            return None

        config = self.strategies[strategy_name]
        return {
            "name": config.name,
            "description": config.description,
            "default_params": config.default_params,
            "param_ranges": config.param_ranges,
            "has_optimization": config.optimization_func is not None,
        }

    def execute_strategy(
        self,
        strategy_name: str,
        price: pd.Series,
        params: Optional[Dict[str, Any]] = None,
        **portfolio_kwargs,
    ) -> Any:
        """
        執行指定策略

        Args:
            strategy_name: 策略名稱
            price: 價格數據
            params: 策略參數
            **portfolio_kwargs: 投資組合參數

        Returns:
            Any: 投資組合結果
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"未知策略: {strategy_name}")

        config = self.strategies[strategy_name]

        # 使用默認參數或用戶提供的參數
        strategy_params = config.default_params.copy()
        if params:
            strategy_params.update(params)

        logger.info(f"執行策略 {strategy_name}: {strategy_params}")

        try:
            # 執行策略
            portfolio = config.strategy_func(
                price, **strategy_params, **portfolio_kwargs
            )

            return portfolio

        except Exception as e:
            logger.error(f"策略 {strategy_name} 執行失敗: {e}")
            raise

    def optimize_strategy(
        self,
        strategy_name: str,
        price: pd.Series,
        param_ranges: Optional[Dict[str, List[Any]]] = None,
        **portfolio_kwargs,
    ) -> Dict[str, Any]:
        """
        優化策略參數

        Args:
            strategy_name: 策略名稱
            price: 價格數據
            param_ranges: 參數範圍
            **portfolio_kwargs: 投資組合參數

        Returns:
            Dict[str, Any]: 優化結果
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"未知策略: {strategy_name}")

        config = self.strategies[strategy_name]

        if not config.optimization_func:
            raise ValueError(f"策略 {strategy_name} 不支持優化")

        # 使用默認參數範圍或用戶提供的範圍
        optimization_ranges = config.param_ranges.copy()
        if param_ranges:
            optimization_ranges.update(param_ranges)

        logger.info(f"優化策略 {strategy_name}: {optimization_ranges}")

        try:
            # 執行優化
            optimization_result = config.optimization_func(
                price, **optimization_ranges, **portfolio_kwargs
            )

            return optimization_result

        except Exception as e:
            logger.error(f"策略 {strategy_name} 優化失敗: {e}")
            raise

    def compare_strategies(
        self,
        price: pd.Series,
        strategy_names: Optional[List[str]] = None,
        **portfolio_kwargs,
    ) -> pd.DataFrame:
        """
        比較多個策略的性能

        Args:
            price: 價格數據
            strategy_names: 要比較的策略列表
            **portfolio_kwargs: 投資組合參數

        Returns:
            pd.DataFrame: 策略比較結果
        """
        if strategy_names is None:
            strategy_names = self.get_available_strategies()

        results = []

        for strategy_name in strategy_names:
            try:
                config = self.strategies[strategy_name]

                # 執行策略
                portfolio = self.execute_strategy(
                    strategy_name, price, config.default_params, **portfolio_kwargs
                )

                # 收集性能指標
                stats = {
                    "strategy": strategy_name,
                    "description": config.description,
                    "sharpe_ratio": portfolio.sharpe_ratio(),
                    "total_return": portfolio.total_return(),
                    "max_drawdown": portfolio.max_drawdown(),
                    "win_rate": portfolio.win_rate(),
                    "expectancy": portfolio.expectancy(),
                }

                results.append(stats)

            except Exception as e:
                logger.warning(f"策略 {strategy_name} 比較失敗: {e}")

        return pd.DataFrame(results).set_index("strategy")

    def create_strategy_combination(
        self,
        price: pd.Series,
        strategies: List[Dict[str, Any]],
        combination_method: str = "equal_weight",
        **portfolio_kwargs,
    ) -> Any:
        """
        創建多策略組合

        Args:
            price: 價格數據
            strategies: 策略配置列表 [{'name': 'RSI', 'weight': 0.5, 'params': {...}}]
            combination_method: 組合方法 ('equal_weight', 'custom_weight')
            **portfolio_kwargs: 投資組合參數

        Returns:
            Any: 組合投資組合結果
        """
        logger.info(f"創建策略組合，方法: {combination_method}")

        all_entries = []
        all_exits = []

        for strategy_config in strategies:
            strategy_name = strategy_config["name"]
            weight = strategy_config.get("weight", 1.0)
            params = strategy_config.get("params", {})

            # 執行單個策略
            portfolio = self.execute_strategy(
                strategy_name, price, params, **portfolio_kwargs
            )

            # 獲取信號
            entries = portfolio.entries
            exits = portfolio.exits

            all_entries.append(entries * weight)
            all_exits.append(exits * weight)

        # 合併信號
        combined_entries = pd.concat(all_entries, axis = 1).any(axis = 1)
        combined_exits = pd.concat(all_exits, axis = 1).any(axis = 1)

        # 創建組合投資組合
        from vectorbt import Portfolio

        combined_portfolio = Portfolio.from_signals(
            price, combined_entries, combined_exits, **portfolio_kwargs
        )

        return combined_portfolio
