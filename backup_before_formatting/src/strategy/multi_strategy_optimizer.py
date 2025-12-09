#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多策略優化器框架
Multi - Strategy Optimizer Framework
支持RSI、MACD、布林帶等多種技術指標策略優化
"""

import asyncio
import json
import logging
import multiprocessing as mp
import os
import sys
import time
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Protocol, Tuple

import aiohttp
import numpy as np
import pandas as pd
import requests

# 添加路徑支持
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)

from src.data.integrated_data_collector import (
    get_gdp_data,
    get_hibor_data,
    get_trade_data,
)

@dataclass
class StrategyConfig:
    """策略配置基類"""
    initial_capital: float = 100000
    commission_rate: float = 0.001
    max_processes: int = 4
    optimization_timeout: int = 300  # 5分鐘超時

@dataclass
class OptimizationResult:
    """統一的優化結果"""
    strategy_type: str
    parameters: Dict[str, Any]
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    optimization_score: float
    optimization_time: float

class TradingStrategy(ABC):
    """交易策略抽象基類"""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.strategy_name = self.__class__.__name__

    @abstractmethod
    def generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """生成參數組合"""
        pass

    @abstractmethod
    def calculate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """計算交易信號"""
        pass

    @abstractmethod
    def get_parameter_ranges(self) -> Dict[str, Tuple]:
        """獲取參數範圍"""
        pass

    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證參數有效性"""
        pass

    def backtest_strategy(self, data: pd.DataFrame, params: Dict[str, Any]) -> OptimizationResult:
        """回測策略"""
        try:
            # 驗證參數
            if not self.validate_parameters(params):
                return self._create_error_result(params, "Invalid parameters")

            # 計算信號
            signals = self.calculate_signals(data, params)

            if signals is None or len(signals) == 0:
                return self._create_error_result(params, "No signals generated")

            # 計算收益
            returns = self._calculate_returns(data, signals)

            # 計算性能指標
            total_return = (1 + returns).prod() - 1
            annualized_return = (1 + total_return) ** (252 / len(data)) - 1

            # 計算最大回撤
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()

            # 計算夏普比率
            excess_returns = returns - 0.02 / 252  # 假設無風險利率2%
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

            # 計算勝率
            win_rate = (returns > 0).mean()
            total_trades = (signals != 0).sum()

            # 綜合評分 (權重: 收益率40% + 夏普30% + 回撤 - 20% + 勝率10%)
            optimization_score = (
                total_return * 40 +
                sharpe_ratio * 30 -
                abs(max_drawdown) * 20 +
                win_rate * 100 * 10
            ) / 100

            return OptimizationResult(
                strategy_type=self.strategy_name,
                parameters=params,
                total_return=total_return,
                annualized_return=annualized_return,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                total_trades=total_trades,
                optimization_score=optimization_score,
                optimization_time=0
            )

        except Exception as e:
            logger.error(f"Backtest error for {self.strategy_name}: {e}")
            return self._create_error_result(params, str(e))

    def _calculate_returns(self, data: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """計算收益率"""
        # 使用收盤價計算收益率
        returns = data['close'].pct_change()

        # 根據信號調整收益率
        position = signals.shift(1).fillna(0)  # 用前一天的信號決定當天持倉

        # 計算交易成本
        position_changes = position.diff().abs()
        trading_costs = position_changes * self.config.commission_rate

        # 淨收益率
        net_returns = position * returns - trading_costs

        return net_returns

    def _create_error_result(self, params: Dict[str, Any], error_msg: str) -> OptimizationResult:
        """創建錯誤結果"""
        return OptimizationResult(
            strategy_type=self.strategy_name,
            parameters=params,
            total_return=0,
            annualized_return=0,
            max_drawdown=1,
            sharpe_ratio=0,
            win_rate=0,
            total_trades=0,
            optimization_score=-999,
            optimization_time=0
        )

class RSIStrategy(TradingStrategy):
    """RSI策略"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.strategy_name = "RSI"

    def get_parameter_ranges(self) -> Dict[str, Tuple]:
        return {
            'rsi_period': (5, 30),
            'rsi_oversold': (20, 40),
            'rsi_overbought': (60, 80),
            'sma_period': (5, 50)
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證RSI參數"""
        try:
            rsi_oversold = float(params['rsi_oversold'])
            rsi_overbought = float(params['rsi_overbought'])
            rsi_period = int(params['rsi_period'])
            sma_period = int(params['sma_period'])

            return (
                5 <= rsi_period <= 30 and
                20 <= rsi_oversold < rsi_overbought <= 80 and
                5 <= sma_period <= 50
            )
        except Exception:
            return False

    def generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """生成RSI參數組合"""
        ranges = self.get_parameter_ranges()

        combinations = []
        rsi_period_range = range(ranges['rsi_period'][0], ranges['rsi_period'][1] + 1, 2)

        for rsi_period in rsi_period_range:
            for rsi_oversold in np.arange(ranges['rsi_oversold'][0], ranges['rsi_oversold'][1] + 1, 2):
                for rsi_overbought in np.arange(ranges['rsi_overbought'][0], ranges['rsi_overbought'][1] + 1, 2):
                    if rsi_oversold < rsi_overbought:
                        for sma_period in range(ranges['sma_period'][0], ranges['sma_period'][1] + 1, 5):
                            combinations.append({
                                'rsi_period': int(rsi_period),
                                'rsi_oversold': float(rsi_oversold),
                                'rsi_overbought': float(rsi_overbought),
                                'sma_period': int(sma_period)
                            })

        return combinations[:200]  # 限制組合數量避免過長運行時間

    def calculate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """計算RSI信號"""
        try:
            # 計算RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=params['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=params['rsi_period']).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # 計算移動平均線
            sma = data['close'].rolling(window=params['sma_period']).mean()

            # 生成交易信號
            signals = pd.Series(0, index=data.index)

            # 超賣區買入信號
            buy_condition = (rsi < params['rsi_oversold']) & (data['close'] > sma)
            signals[buy_condition] = 1

            # 超買區賣出信號
            sell_condition = (rsi > params['rsi_overbought']) & (data['close'] < sma)
            signals[sell_condition] = -1

            return signals

        except Exception as e:
            logger.error(f"RSI calculation error: {e}")
            return pd.Series(0, index=data.index)

class MACDStrategy(TradingStrategy):
    """MACD策略"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.strategy_name = "MACD"

    def get_parameter_ranges(self) -> Dict[str, Tuple]:
        return {
            'fast_period': (8, 20),
            'slow_period': (20, 40),
            'signal_period': (5, 15),
            'threshold': (0.001, 0.01)
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證MACD參數"""
        try:
            fast_period = int(params['fast_period'])
            slow_period = int(params['slow_period'])
            signal_period = int(params['signal_period'])
            threshold = float(params['threshold'])

            return (
                8 <= fast_period < slow_period <= 40 and
                5 <= signal_period <= 15 and
                0.001 <= threshold <= 0.01
            )
        except Exception:
            return False

    def generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """生成MACD參數組合"""
        ranges = self.get_parameter_ranges()

        combinations = []
        fast_periods = range(ranges['fast_period'][0], ranges['fast_period'][1] + 1, 2)

        for fast_period in fast_periods:
            slow_periods = range(max(fast_period + 2, ranges['slow_period'][0]),
                               ranges['slow_period'][1] + 1, 4)

            for slow_period in slow_periods:
                for signal_period in range(ranges['signal_period'][0], ranges['signal_period'][1] + 1, 2):
                    for threshold in np.arange(ranges['threshold'][0], ranges['threshold'][1] + 1, 0.002):
                        combinations.append({
                            'fast_period': int(fast_period),
                            'slow_period': int(slow_period),
                            'signal_period': int(signal_period),
                            'threshold': float(threshold)
                        })

        return combinations[:150]  # 限制組合數量

    def calculate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """計算MACD信號"""
        try:
            # 計算EMA
            ema_fast = data['close'].ewm(span=params['fast_period']).mean()
            ema_slow = data['close'].ewm(span=params['slow_period']).mean()

            # 計算MACD線
            macd_line = ema_fast - ema_slow

            # 計算信號線
            signal_line = macd_line.ewm(span=params['signal_period']).mean()

            # 計算MACD柱
            macd_histogram = macd_line - signal_line

            # 生成交易信號
            signals = pd.Series(0, index=data.index)

            # MACD金叉買入信號
            buy_condition = (macd_line > signal_line) & (macd_histogram > params['threshold'])
            signals[buy_condition] = 1

            # MACD死叉賣出信號
            sell_condition = (macd_line < signal_line) & (macd_histogram < -params['threshold'])
            signals[sell_condition] = -1

            return signals

        except Exception as e:
            logger.error(f"MACD calculation error: {e}")
            return pd.Series(0, index=data.index)

class BollingerBandsStrategy(TradingStrategy):
    """布林帶策略"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.strategy_name = "BollingerBands"

    def get_parameter_ranges(self) -> Dict[str, Tuple]:
        return {
            'period': (10, 30),
            'std_dev': (1.5, 3.0),
            'rsi_period': (5, 20)
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證布林帶參數"""
        try:
            period = int(params['period'])
            std_dev = float(params['std_dev'])
            rsi_period = int(params['rsi_period'])

            return (
                10 <= period <= 30 and
                1.5 <= std_dev <= 3.0 and
                5 <= rsi_period <= 20
            )
        except Exception:
            return False

    def generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """生成布林帶參數組合"""
        ranges = self.get_parameter_ranges()

        combinations = []
        periods = range(ranges['period'][0], ranges['period'][1] + 1, 2)

        for period in periods:
            for std_dev in np.arange(ranges['std_dev'][0], ranges['std_dev'][1] + 0.1, 0.2):
                for rsi_period in range(ranges['rsi_period'][0], ranges['rsi_period'][1] + 1, 2):
                    combinations.append({
                        'period': int(period),
                        'std_dev': float(std_dev),
                        'rsi_period': int(rsi_period)
                    })

        return combinations[:120]  # 限制組合數量

    def calculate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """計算布林帶信號"""
        try:
            # 計算移動平均線和標準差
            sma = data['close'].rolling(window=params['period']).mean()
            std = data['close'].rolling(window=params['period']).std()

            # 計算布林帶
            upper_band = sma + (std * params['std_dev'])
            lower_band = sma - (std * params['std_dev'])

            # 計算RSI用於過濾信號
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=params['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=params['rsi_period']).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # 生成交易信號
            signals = pd.Series(0, index=data.index)

            # 布林帶下軌買入信號（RSI過濾）
            buy_condition = (data['close'] <= lower_band) & (rsi < 30)
            signals[buy_condition] = 1

            # 布林帶上軌賣出信號（RSI過濾）
            sell_condition = (data['close'] >= upper_band) & (rsi > 70)
            signals[sell_condition] = -1

            return signals

        except Exception as e:
            logger.error(f"Bollinger Bands calculation error: {e}")
            return pd.Series(0, index=data.index)

class MultiStrategyOptimizer:
    """多策略優化器"""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.strategies = {
            'RSI': RSIStrategy(config),
            'MACD': MACDStrategy(config),
            'BollingerBands': BollingerBandsStrategy(config)
        }

    async def fetch_stock_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """獲取股票數據"""
        try:
            # 嘗試從數據接入層獲取數據
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:8001/api/stock-data/{symbol}?days={days}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        df = pd.DataFrame(data['data'])
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                        return df
        except Exception as e:
            logger.warning(f"Failed to fetch data from API: {e}")

        # 如果API失敗，生成模擬數據
        import random
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

        # 基於隨機漫步生成價格數據
        np.random.seed(hash(symbol) % (2 ** 32))
        returns = np.random.normal(0.001, 0.02, days)
        prices = [100]  # 起始價格

        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        # 創建模擬OHLCV數據
        data = []
        for i, date in enumerate(dates):
            close_price = prices[i]
            high_price = close_price * (1 + abs(np.random.normal(0, 0.01)))
            low_price = close_price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = low_price + (high_price - low_price) * np.random.random()
            volume = int(np.random.normal(1000000, 200000))

            if volume < 10000:
                volume = 10000

            data.append({
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })

        df = pd.DataFrame(data, index=dates)
        df.index.name = 'timestamp'
        return df

    def optimize_strategy(self, strategy_name: str, data: pd.DataFrame) -> List[OptimizationResult]:
        """優化單個策略"""
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        strategy = self.strategies[strategy_name]
        parameter_combinations = strategy.generate_parameter_combinations()

        print(f"[OPTIMIZE] 開始優化 {strategy_name} 策略")
        print(f"[OPTIMIZE] 參數組合數: {len(parameter_combinations)}")

        results = []

        # 使用進程池進行並行優化
        with ProcessPoolExecutor(max_workers=self.config.max_processes) as executor:
            futures = {
                executor.submit(self._optimize_single_combination, strategy, data, params): params
                for params in parameter_combinations
            }

            for future in as_completed(futures):
                try:
                    result = future.result(timeout=60)  # 60秒超時
                    if result.optimization_score > -900:  # 過濋錯誤結果
                        results.append(result)
                except Exception as e:
                    logger.error(f"Optimization failed: {e}")

        # 按優化分數排序
        results.sort(key=lambda x: x.optimization_score, reverse=True)

        print(f"[OPTIMIZE] {strategy_name} 策略優化完成，有效結果: {len(results)}")

        return results

    def _optimize_single_combination(self, strategy: TradingStrategy, data: pd.DataFrame, params: Dict[str, Any]) -> OptimizationResult:
        """優化單個參數組合"""
        return strategy.backtest_strategy(data, params)

    async def optimize_multiple_strategies(self, symbol: str, strategies: List[str] = None) -> Dict[str, List[OptimizationResult]]:
        """優化多個策略"""
        if strategies is None:
            strategies = list(self.strategies.keys())

        # 獲取數據
        data = await self.fetch_stock_data(symbol)
        print(f"[DATA] 獲取到 {len(data)} 天的數據 for {symbol}")

        results = {}

        for strategy_name in strategies:
            try:
                strategy_results = self.optimize_strategy(strategy_name, data)
                results[strategy_name] = strategy_results

                # 輸出最佳結果
                if strategy_results:
                    best = strategy_results[0]
                    print(f"[BEST] {strategy_name}: 參數={best.parameters}, 分數={best.optimization_score:.2f}")
                    print(f"[BEST] 收益率={best.total_return:.2%}, 夏普={best.sharpe_ratio:.2f}, 勝率={best.win_rate:.2%}")

            except Exception as e:
                logger.error(f"Failed to optimize {strategy_name}: {e}")
                results[strategy_name] = []

        return results

    def compare_strategies(self, results: Dict[str, List[OptimizationResult]]) -> Dict[str, OptimizationResult]:
        """比較策略並返回最佳結果"""
        comparison = {}

        for strategy_name, strategy_results in results.items():
            if strategy_results:
                comparison[strategy_name] = strategy_results[0]  # 最佳結果

        return comparison