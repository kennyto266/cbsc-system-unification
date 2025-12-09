#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VectorBT Parameter Optimization Engine
VectorBT參數優化引擎 - 利用VectorBT原生優化功能
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from dataclasses import dataclass

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available")

from vectorbt_engine import VectorBTEngine, BacktestConfig

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """優化配置"""
    # 搜索空間
    param_ranges: Dict[str, Any] = None
    objective: str = 'sharpe_ratio'  # 'sharpe_ratio', 'total_return', 'calmar_ratio', 'max_drawdown'
    maximize: bool = True

    # 並行設置
    n_jobs: int = -1  # -1表示使用所有CPU核心
    chunk_size: Optional[int] = None

    # 約束條件
    min_trades: int = 10
    max_drawdown_limit: Optional[float] = None
    min_total_return: Optional[float] = None

class VectorBTOptimizer:
    """VectorBT參數優化器"""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self.engine = VectorBTEngine()

        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required for optimization")

    def optimize_strategy(self, data: pd.DataFrame, strategy: str,
                         param_ranges: Dict[str, List]) -> Dict:
        """
        單策略參數優化

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            param_ranges: 參數範圍字典

        Returns:
            優化結果
        """
        logger.info(f"Starting optimization for {strategy} with {len(param_ranges)} parameters")

        # 生成參數組合
        param_combinations = self._generate_param_combinations(param_ranges)

        # 使用VectorBT的優化功能
        if strategy == 'RSI_MEAN_REVERSION':
            return self._optimize_rsi_strategy(data, param_combinations)
        elif strategy == 'MACD_CROSSOVER':
            return self._optimize_macd_strategy(data, param_combinations)
        elif strategy == 'BOLLINGER_BANDS':
            return self._optimize_bollinger_strategy(data, param_combinations)
        else:
            return self._optimize_generic_strategy(data, strategy, param_combinations)

    def optimize_multi_objective(self, data: pd.DataFrame, strategy: str,
                                param_ranges: Dict[str, List],
                                objectives: List[str]) -> Dict:
        """
        多目標優化

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            param_ranges: 參數範圍
            objectives: 優化目標列表

        Returns:
            多目標優化結果
        """
        logger.info(f"Starting multi-objective optimization for {strategy}")

        # 生成參數組合
        param_combinations = self._generate_param_combinations(param_ranges)

        # 並行評估所有參數組合
        results = self._evaluate_parameter_combinations(data, strategy, param_combinations, objectives)

        # Pareto前沿分析
        pareto_results = self._find_pareto_frontier(results, objectives)

        return {
            'pareto_frontier': pareto_results,
            'total_evaluations': len(param_combinations),
            'objectives': objectives,
            'best_by_objective': {
                obj: max(results, key=lambda x: x.get(obj, float('-inf')))
                for obj in objectives
            }
        }

    def optimize_walk_forward(self, data: pd.DataFrame, strategy: str,
                             param_ranges: Dict[str, List],
                             window_size: int = 252,  # 1年
                             step_size: int = 63) -> Dict:
        """
        Walk-forward優化

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            param_ranges: 參數範圍
            window_size: 訓練窗口大小
            step_size: 前進步長

        Returns:
            Walk-forward優化結果
        """
        logger.info(f"Starting walk-forward optimization for {strategy}")

        results = []
        total_points = len(data)

        for start_idx in range(0, total_points - window_size, step_size):
            end_idx = start_idx + window_size
            test_start = end_idx
            test_end = min(test_start + step_size, total_points)

            if test_end <= test_start:
                break

            # 訓練期優化
            train_data = data.iloc[start_idx:end_idx]
            optimal_params = self._find_optimal_params(train_data, strategy, param_ranges)

            # 測試期評估
            test_data = data.iloc[test_start:test_end]
            test_result = self.engine.backtest_strategy(test_data, strategy, optimal_params)

            results.append({
                'train_period': (data.index[start_idx], data.index[end_idx-1]),
                'test_period': (data.index[test_start], data.index[test_end-1]),
                'optimal_params': optimal_params,
                'test_metrics': test_result.get_metrics(),
                'test_portfolio': test_result.portfolio
            })

        # 計算整體性能
        out_of_sample_returns = []
        for result in results:
            if 'test_portfolio' in result:
                returns = result['test_portfolio'].returns()
                out_of_sample_returns.extend(returns)

        overall_performance = self._calculate_portfolio_metrics(np.array(out_of_sample_returns))

        return {
            'walk_forward_results': results,
            'overall_performance': overall_performance,
            'num_periods': len(results)
        }

    def _generate_param_combinations(self, param_ranges: Dict[str, List]) -> List[Dict]:
        """生成參數組合"""
        from itertools import product

        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())

        combinations = []
        for values in product(*param_values):
            combinations.append(dict(zip(param_names, values)))

        return combinations

    def _optimize_rsi_strategy(self, data: pd.DataFrame, param_combinations: List[Dict]) -> Dict:
        """RSI策略優化"""
        close = data['close']

        # 準備參數數組
        periods = [params['period'] for params in param_combinations]
        oversold_levels = [params['oversold'] for params in param_combinations]
        overbought_levels = [params['overbought'] for params in param_combinations]

        # 使用VectorBT的批量RSI計算
        rsi_indicator = vbt.RSI.run(close, window=periods)
        rsi_values = rsi_indicator.rsi

        # 批量生成信號
        buy_signals = rsi_values.vbt.crossed_above(np.array(oversold_levels))
        sell_signals = rsi_values.vbt.crossed_below(np.array(overbought_levels))

        # 執行批量回測
        portfolios = vbt.Portfolio.from_signals(
            close=close,
            entries=buy_signals,
            exits=sell_signals,
            freq='D'
        )

        # 計算指標
        stats = portfolios.stats()

        # 找到最佳參數組合
        best_idx = self._find_best_portfolio_index(stats)

        return {
            'best_params': param_combinations[best_idx],
            'best_portfolio': portfolios.iloc[:, best_idx],
            'best_metrics': stats.iloc[best_idx].to_dict(),
            'all_results': {
                'param_combinations': param_combinations,
                'portfolios': portfolios,
                'stats': stats
            }
        }

    def _optimize_macd_strategy(self, data: pd.DataFrame, param_combinations: List[Dict]) -> Dict:
        """MACD策略優化"""
        close = data['close']

        # 準備參數數組
        fast_windows = [params['fast'] for params in param_combinations]
        slow_windows = [params['slow'] for params in param_combinations]
        signal_windows = [params['signal'] for params in param_combinations]

        # 使用VectorBT的批量MACD計算
        macd_indicator = vbt.MACD.run(
            close,
            fast_window=fast_windows,
            slow_window=slow_windows,
            signal_window=signal_windows
        )

        # 批量生成信號
        buy_signals = macd_indicator.macd.vbt.crossed_above(macd_indicator.signal)
        sell_signals = macd_indicator.macd.vbt.crossed_below(macd_indicator.signal)

        # 執行批量回測
        portfolios = vbt.Portfolio.from_signals(
            close=close,
            entries=buy_signals,
            exits=sell_signals,
            freq='D'
        )

        # 計算指標
        stats = portfolios.stats()

        # 找到最佳參數組合
        best_idx = self._find_best_portfolio_index(stats)

        return {
            'best_params': param_combinations[best_idx],
            'best_portfolio': portfolios.iloc[:, best_idx],
            'best_metrics': stats.iloc[best_idx].to_dict(),
            'all_results': {
                'param_combinations': param_combinations,
                'portfolios': portfolios,
                'stats': stats
            }
        }

    def _optimize_bollinger_strategy(self, data: pd.DataFrame, param_combinations: List[Dict]) -> Dict:
        """布林帶策略優化"""
        close = data['close']

        # 準備參數數組
        windows = [params['period'] for params in param_combinations]
        std_devs = [params['std_dev'] for params in param_combinations]

        # 使用VectorBT的批量布林帶計算
        bb_indicator = vbt.BBANDS.run(close, window=windows, std=std_devs)

        # 批量生成信號
        upper_band = bb_indicator.upper
        lower_band = bb_indicator.lower

        # 突破策略：價格突破上軌買入，突破下軌賣出
        buy_signals = close.vbt.crossed_above(upper_band)
        sell_signals = close.vbt.crossed_below(lower_band)

        # 執行批量回測
        portfolios = vbt.Portfolio.from_signals(
            close=close,
            entries=buy_signals,
            exits=sell_signals,
            freq='D'
        )

        # 計算指標
        stats = portfolios.stats()

        # 找到最佳參數組合
        best_idx = self._find_best_portfolio_index(stats)

        return {
            'best_params': param_combinations[best_idx],
            'best_portfolio': portfolios.iloc[:, best_idx],
            'best_metrics': stats.iloc[best_idx].to_dict(),
            'all_results': {
                'param_combinations': param_combinations,
                'portfolios': portfolios,
                'stats': stats
            }
        }

    def _optimize_generic_strategy(self, data: pd.DataFrame, strategy: str,
                                  param_combinations: List[Dict]) -> Dict:
        """通用策略優化"""
        best_result = None
        best_score = float('-inf') if self.config.maximize else float('inf')

        for params in param_combinations:
            result = self.engine.backtest_strategy(data, strategy, params)
            score = self._calculate_score(result, self.config.objective)

            if (self.config.maximize and score > best_score) or (not self.config.maximize and score < best_score):
                best_score = score
                best_result = result

        return {
            'best_params': best_result.params if best_result else None,
            'best_portfolio': best_result.portfolio if best_result else None,
            'best_metrics': best_result.get_metrics() if best_result else {},
            'best_score': best_score
        }

    def _find_best_portfolio_index(self, stats: pd.DataFrame) -> int:
        """根據配置的目標找到最佳投資組合索引"""
        if self.config.objective == 'sharpe_ratio':
            return stats['Sharpe Ratio'].idxmax()
        elif self.config.objective == 'total_return':
            return stats['Total Return [%]'].idxmax()
        elif self.config.objective == 'max_drawdown':
            return stats['Max Drawdown [%]'].idxmin()
        elif self.config.objective == 'calmar_ratio':
            return stats['Calmar Ratio'].idxmax()
        else:
            return stats['Sharpe Ratio'].idxmax()  # 默認Sharpe比率

    def _calculate_score(self, result, objective: str) -> float:
        """計算評分"""
        metrics = result.get_metrics()

        if objective == 'sharpe_ratio':
            return metrics.get('sharpe_ratio', 0)
        elif objective == 'total_return':
            return metrics.get('total_return', 0)
        elif objective == 'calmar_ratio':
            return metrics.get('calmar_ratio', 0)
        elif objective == 'max_drawdown':
            return -metrics.get('max_drawdown', 0)  # 負號，因為我們要最小化回撤
        else:
            return metrics.get('sharpe_ratio', 0)

    def _evaluate_parameter_combinations(self, data: pd.DataFrame, strategy: str,
                                        param_combinations: List[Dict],
                                        objectives: List[str]) -> List[Dict]:
        """並行評估參數組合"""
        results = []

        for params in param_combinations:
            result = self.engine.backtest_strategy(data, strategy, params)
            metrics = result.get_metrics()

            # 創建結果字典，包含所有目標
            param_result = {'params': params}
            for obj in objectives:
                param_result[obj] = self._calculate_score(result, obj)

            results.append(param_result)

        return results

    def _find_pareto_frontier(self, results: List[Dict], objectives: List[str]) -> List[Dict]:
        """找到Pareto前沿"""
        if len(results) == 0:
            return []

        # 提取目標值
        objective_values = np.array([[r[obj] for obj in objectives] for r in results])

        # 找到Pareto優越的點
        is_pareto = np.ones(len(results), dtype=bool)

        for i in range(len(results)):
            for j in range(len(results)):
                if i == j:
                    continue

                # 如果點j在所有目標上都優於或等於點i，且至少在一個目標上嚴格優於
                if np.all(objective_values[j] >= objective_values[i]) and \
                   np.any(objective_values[j] > objective_values[i]):
                    is_pareto[i] = False
                    break

        return [results[i] for i in range(len(results)) if is_pareto[i]]

    def _find_optimal_params(self, data: pd.DataFrame, strategy: str,
                             param_ranges: Dict[str, List]) -> Dict:
        """在訓練期找到最優參數"""
        optimization_result = self.optimize_strategy(data, strategy, param_ranges)
        return optimization_result['best_params']

    def _calculate_portfolio_metrics(self, returns: np.ndarray) -> Dict:
        """計算投資組合指標"""
        if len(returns) == 0:
            return {}

        total_return = np.prod(1 + returns) - 1

        # Sharpe比率 (假設無風險利率3%)
        excess_returns = returns - 0.03/252
        if np.std(excess_returns) > 0:
            sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # 最大回撤
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)

        # Calmar比率
        if max_drawdown != 0:
            calmar_ratio = (total_return + 1) / abs(max_drawdown)
        else:
            calmar_ratio = float('inf')

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'num_trades': len(returns)
        }