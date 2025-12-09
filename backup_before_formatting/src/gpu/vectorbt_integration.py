#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速VectorBT集成模塊
將非價格GPU引擎與VectorBT回測系統無縫集成
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import time
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from gpu.parameter_optimizer import GPUParameterOptimizer, OptimizationConfig, OptimizationReport
from gpu.nonprice_engine import NonPriceGPUEngine, OptimizationResult
from gpu.performance_monitor import get_performance_monitor, get_memory_manager
from vectorization.time_series import get_time_series_vectorizer, VectorizedData

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt")

logger = logging.getLogger(__name__)

@dataclass
class GPUVectorBTConfig:
    """GPU-VectorBT集成配置"""
    # GPU配置
    use_gpu: bool = True
    gpu_memory_limit: float = 8.0  # GB
    batch_size: int = 1000

    # 優化配置
    optimization_metric: str = 'sharpe_ratio'
    risk_free_rate: float = 0.03
    max_combinations: int = 10000

    # VectorBT配置
    initial_cash: float = 100000.0
    fees: float = 0.001
    slippage: float = 0.0005

    # 數據處理
    data_frequency: str = '1D'  # 日線數據
    min_data_points: int = 100

@dataclass
class GPUVectorBTResult:
    """GPU-VectorBT集成結果"""
    strategy_name: str
    parameters: Dict[str, Any]

    # 性能指標
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    calmar_ratio: float
    sortino_ratio: float

    # GPU加速信息
    gpu_utilized: bool
    execution_time: float
    strategies_tested: int
    gpu_memory_used: float

    # VectorBT結果
    portfolio: Optional[Any] = None
    equity_curve: Optional[pd.Series] = None
    trades: Optional[pd.DataFrame] = None
    signals: Optional[pd.DataFrame] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'strategy': self.strategy_name,
            'parameters': self.parameters,
            'performance': {
                'total_return': round(self.total_return * 100, 2),
                'sharpe_ratio': round(self.sharpe_ratio, 3),
                'max_drawdown': round(self.max_drawdown * 100, 2),
                'win_rate': round(self.win_rate * 100, 2),
                'profit_factor': round(self.profit_factor, 2),
                'calmar_ratio': round(self.calmar_ratio, 3),
                'sortino_ratio': round(self.sortino_ratio, 3)
            },
            'gpu_info': {
                'gpu_utilized': self.gpu_utilized,
                'execution_time': round(self.execution_time, 3),
                'strategies_tested': self.strategies_tested,
                'gpu_memory_used': round(self.gpu_memory_used, 2)
            }
        }

class GPUVectorBTIntegration:
    """GPU加速VectorBT集成引擎"""

    def __init__(self, config: Optional[GPUVectorBTConfig] = None):
        """
        初始化GPU-VectorBT集成引擎

        Args:
            config: 集成配置
        """
        self.config = config or GPUVectorBTConfig()

        # 初始化組件
        self.gpu_optimizer = GPUParameterOptimizer()
        self.vectorizer = get_time_series_vectorizer()
        self.performance_monitor = get_performance_monitor()
        self.memory_manager = get_memory_manager()

        # 檢查依賴
        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required. Install with: pip install vectorbt")

        # GPU檢查
        self.gpu_available = self._check_gpu_availability()

        logger.info(f"GPU-VectorBT Integration initialized. GPU available: {self.gpu_available}")

    def _check_gpu_availability(self) -> bool:
        """檢查GPU可用性"""
        if not self.config.use_gpu:
            return False

        try:
            import cupy as cp
            # 測試GPU操作
            test_array = cp.array([1, 2, 3])
            result = cp.sum(test_array)
            del test_array, result
            cp.get_default_memory_pool().free_all_blocks()
            return True
        except:
            logger.warning("GPU not available, falling back to CPU")
            return False

    def optimize_nonprice_strategy(
        self,
        data: pd.DataFrame,
        strategy_type: str,
        param_ranges: Optional[Dict[str, Tuple[int, int]]] = None,
        data_source_id: str = "STOCK"
    ) -> GPUVectorBTResult:
        """
        使用GPU加速優化非價格策略

        Args:
            data: 價格數據 (OHLCV)
            strategy_type: 策略類型 (rsi, macd, bollinger, etc.)
            param_ranges: 參數範圍
            data_source_id: 數據源ID

        Returns:
            GPU-VectorBT集成結果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting GPU-VectorBT optimization for {strategy_type}")

            # 1. 數據驗證和預處理
            validated_data = self._validate_and_prepare_data(data)

            # 2. 向量化數據
            vectorized_data = self.vectorizer.vectorize_dataframe(
                validated_data[['close']], data_source_id
            )

            # 3. 創建優化配置
            if param_ranges is None:
                param_ranges = self._get_default_param_ranges(strategy_type)

            opt_config = self.gpu_optimizer.create_optimization_config(
                strategy_type=strategy_type,
                param_ranges=param_ranges,
                optimization_metric=self.config.optimization_metric,
                risk_free_rate=self.config.risk_free_rate,
                use_gpu=self.gpu_available,
                enable_parallel=True
            )

            # 4. 執行GPU優化
            optimization_report = self.gpu_optimizer.optimize_single_source(
                vectorized_data, opt_config
            )

            # 5. 獲取最佳策略
            best_strategy = optimization_report.best_strategy

            # 6. 使用VectorBT執行完整回測
            vectorbt_result = self._execute_vectorbt_backtest(
                validated_data, strategy_type, best_strategy.parameters
            )

            # 7. 計算性能指標
            performance_metrics = self._calculate_comprehensive_metrics(
                vectorbt_result, best_strategy
            )

            # 8. 創建集成結果
            result = GPUVectorBTResult(
                strategy_name=strategy_type.upper(),
                parameters=best_strategy.parameters,
                **performance_metrics,
                gpu_utilized=optimization_report.gpu_utilized,
                execution_time=time.time() - start_time,
                strategies_tested=len(optimization_report.results),
                gpu_memory_used=self._get_gpu_memory_usage(),
                portfolio=vectorbt_result.get('portfolio'),
                equity_curve=vectorbt_result.get('equity_curve'),
                trades=vectorbt_result.get('trades'),
                signals=vectorbt_result.get('signals')
            )

            logger.info(f"GPU-VectorBT optimization completed for {strategy_type}")
            logger.info(f"Best parameters: {best_strategy.parameters}")
            logger.info(f"Sharpe ratio: {result.sharpe_ratio:.3f}")

            return result

        except Exception as e:
            logger.error(f"GPU-VectorBT optimization failed: {e}")
            raise

    def _validate_and_prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """驗證和準備數據"""
        # 基本驗證
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # 數據長度檢查
        if len(data) < self.config.min_data_points:
            raise ValueError(f"Insufficient data: {len(data)} < {self.config.min_data_points}")

        # 數據清理
        cleaned_data = data.dropna().copy()

        # 價格合理性檢查
        if (cleaned_data['high'] < cleaned_data['low']).any():
            raise ValueError("Invalid price data: high < low detected")

        return cleaned_data

    def _get_default_param_ranges(self, strategy_type: str) -> Dict[str, Tuple[int, int]]:
        """獲取默認參數範圍"""
        if strategy_type == 'rsi':
            return {'period': (5, 50)}
        elif strategy_type == 'macd':
            return {
                'fast_period': (5, 20),
                'slow_period': (21, 50),
                'signal_period': (5, 15)
            }
        elif strategy_type == 'bollinger':
            return {
                'period': (10, 30),
                'num_std': (1, 3)
            }
        elif strategy_type == 'moving_average':
            return {
                'short_period': (5, 20),
                'long_period': (21, 50)
            }
        else:
            return {'period': (5, 30)}

    def _execute_vectorbt_backtest(
        self,
        data: pd.DataFrame,
        strategy_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """執行VectorBT回測"""
        try:
            # 生成交易信號
            signals = self._generate_vectorbt_signals(data, strategy_type, parameters)

            # 執行回測
            portfolio = vbt.Portfolio.from_signals(
                data['close'],
                signals['entries'],
                signals['exits'],
                init_cash=self.config.initial_cash,
                fees=self.config.fees,
                slippage=self.config.slippage
            )

            # 提取結果
            equity_curve = portfolio.value()
            returns = portfolio.returns()
            trades = portfolio.trades.records_readable

            return {
                'portfolio': portfolio,
                'equity_curve': equity_curve,
                'returns': returns,
                'trades': trades,
                'signals': signals
            }

        except Exception as e:
            logger.error(f"VectorBT backtest execution failed: {e}")
            raise

    def _generate_vectorbt_signals(
        self,
        data: pd.DataFrame,
        strategy_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, pd.Series]:
        """生成VectorBT交易信號"""
        close_prices = data['close']

        if strategy_type == 'rsi':
            import talib
            period = parameters.get('period', 14)
            rsi = talib.RSI(close_prices.values, timeperiod=period)

            # RSI均值回歸策略
            entries = (rsi < 30)
            exits = (rsi > 70)

        elif strategy_type == 'macd':
            import talib
            fast_period = parameters.get('fast_period', 12)
            slow_period = parameters.get('slow_period', 26)
            signal_period = parameters.get('signal_period', 9)

            macd, signal, hist = talib.MACD(
                close_prices.values, fastperiod=fast_period,
                slowperiod=slow_period, signalperiod=signal_period
            )

            # MACD交叉策略
            entries = (hist > 0)
            exits = (hist < 0)

        elif strategy_type == 'bollinger':
            import talib
            period = parameters.get('period', 20)
            num_std = parameters.get('num_std', 2)

            upper, middle, lower = talib.BBANDS(
                close_prices.values, timeperiod=period, nbdevup=num_std, nbdevdn=num_std
            )

            # 布林帶策略
            entries = (close_prices.values < lower)
            exits = (close_prices.values > upper)

        elif strategy_type == 'moving_average':
            import talib
            short_period = parameters.get('short_period', 10)
            long_period = parameters.get('long_period', 30)

            short_ma = talib.SMA(close_prices.values, timeperiod=short_period)
            long_ma = talib.SMA(close_prices.values, timeperiod=long_period)

            # 雙移動平均策略
            entries = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
            exits = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))

        else:
            raise ValueError(f"Unsupported strategy type: {strategy_type}")

        # 轉換為pandas Series並對齊索引
        entries = pd.Series(entries, index=close_prices.index, dtype=bool)
        exits = pd.Series(exits, index=close_prices.index, dtype=bool)

        return {
            'entries': entries,
            'exits': exits
        }

    def _calculate_comprehensive_metrics(
        self,
        vectorbt_result: Dict[str, Any],
        best_strategy: OptimizationResult
    ) -> Dict[str, float]:
        """計算綜合性能指標"""
        portfolio = vectorbt_result['portfolio']

        # 基本指標
        total_return = portfolio.total_return()
        returns = portfolio.returns()

        # Sharpe比率
        sharpe_ratio = portfolio.sharpe_ratio(risk_free=self.config.risk_free_rate / 252)

        # 最大回撤
        max_drawdown = portfolio.max_drawdown()

        # 勝率
        win_rate = portfolio.trades.win_rate()

        # 獲利因子
        profit_factor = portfolio.trades.profit_factor()

        # Calmar比率
        calmar_ratio = portfolio.calmar_ratio()

        # Sortino比率
        sortino_ratio = portfolio.sortino_ratio()

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio
        }

    def _get_gpu_memory_usage(self) -> float:
        """獲取GPU內存使用量"""
        try:
            memory_info = self.memory_manager.get_memory_usage()
            return memory_info.get('gpu_memory', {}).get('used_mb', 0.0) / 1024.0  # 轉換為GB
        except:
            return 0.0

    def batch_optimize_strategies(
        self,
        data: pd.DataFrame,
        strategy_types: List[str],
        param_ranges: Optional[Dict[str, Dict[str, Tuple[int, int]]]] = None
    ) -> Dict[str, GPUVectorBTResult]:
        """
        批量優化多個策略

        Args:
            data: 價格數據
            strategy_types: 策略類型列表
            param_ranges: 各策略的參數範圍

        Returns:
            策略結果字典
        """
        results = {}

        logger.info(f"Starting batch optimization for {len(strategy_types)} strategies")

        for strategy_type in strategy_types:
            try:
                strategy_param_ranges = None
                if param_ranges and strategy_type in param_ranges:
                    strategy_param_ranges = param_ranges[strategy_type]

                result = self.optimize_nonprice_strategy(
                    data, strategy_type, strategy_param_ranges
                )
                results[strategy_type] = result

                logger.info(f"Completed optimization for {strategy_type}: Sharpe {result.sharpe_ratio:.3f}")

            except Exception as e:
                logger.error(f"Failed to optimize {strategy_type}: {e}")
                continue

        return results

    def compare_gpu_cpu_performance(
        self,
        data: pd.DataFrame,
        strategy_type: str,
        param_ranges: Optional[Dict[str, Tuple[int, int]]] = None
    ) -> Dict[str, Any]:
        """
        比較GPU和CPU性能

        Args:
            data: 價格數據
            strategy_type: 策略類型
            param_ranges: 參數範圍

        Returns:
            性能比較結果
        """
        logger.info(f"Starting GPU vs CPU performance comparison for {strategy_type}")

        # GPU測試
        self.config.use_gpu = True
        gpu_start = time.time()
        gpu_result = self.optimize_nonprice_strategy(data, strategy_type, param_ranges)
        gpu_time = time.time() - gpu_start

        # CPU測試
        self.config.use_gpu = False
        cpu_start = time.time()
        cpu_result = self.optimize_nonprice_strategy(data, strategy_type, param_ranges)
        cpu_time = time.time() - cpu_start

        # 恢復GPU設置
        self.config.use_gpu = self._check_gpu_availability()

        # 計算加速比
        speedup = cpu_time / gpu_time if gpu_time > 0 else 0

        comparison = {
            'strategy_type': strategy_type,
            'gpu_result': gpu_result.to_dict(),
            'cpu_result': cpu_result.to_dict(),
            'performance': {
                'gpu_time': round(gpu_time, 3),
                'cpu_time': round(cpu_time, 3),
                'speedup': round(speedup, 2),
                'efficiency_gain': f"{(speedup - 1) * 100:.1f}%" if speedup > 1 else "0%"
            },
            'accuracy': {
                'sharpe_difference': abs(gpu_result.sharpe_ratio - cpu_result.sharpe_ratio),
                'return_difference': abs(gpu_result.total_return - cpu_result.total_return)
            }
        }

        logger.info(f"Performance comparison completed. Speedup: {speedup:.2f}x")

        return comparison

    def cleanup(self):
        """清理資源"""
        try:
            self.memory_manager.free_all()
            logger.info("GPU-VectorBT Integration cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# 全局集成引擎實例
_gpu_vectorbt_integration = None

def get_gpu_vectorbt_integration(config: Optional[GPUVectorBTConfig] = None) -> GPUVectorBTIntegration:
    """獲取GPU-VectorBT集成引擎實例"""
    global _gpu_vectorbt_integration
    if _gpu_vectorbt_integration is None:
        _gpu_vectorbt_integration = GPUVectorBTIntegration(config)
    return _gpu_vectorbt_integration