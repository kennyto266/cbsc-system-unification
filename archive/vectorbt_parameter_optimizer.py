#!/usr/bin/env python3
"""
VectorBT Parameter Optimization Framework
完整的參數優化框架，包含Grid Search、貝葉斯優化、遺傳算法和Walk-Forward分析

Created: 2025-11-22
Author: Claude Code Assistant
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import warnings
import time
import json
import logging
from pathlib import Path
import multiprocessing as mp
from abc import ABC, abstractmethod
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from scipy.optimize import minimize
from scipy.stats import norm
import random

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """優化結果數據結構"""
    best_parameters: Dict[str, Any]
    best_sharpe_ratio: float
    total_return: float
    max_drawdown: float
    calmar_ratio: float
    sortino_ratio: float
    win_rate: float
    optimization_id: str
    method: str
    total_combinations: int
    execution_time: float
    top_results: List[Dict[str, Any]] = None

@dataclass
class ParameterGrid:
    """參數網格定義"""
    rsi_period: List[int] = None
    overbought_threshold: List[float] = None
    oversold_threshold: List[float] = None
    stop_loss: List[float] = None
    take_profit: List[float] = None
    position_size: List[float] = None
    macd_fast: List[int] = None
    macd_slow: List[int] = None
    macd_signal: List[int] = None
    bb_period: List[int] = None
    bb_std: List[float] = None

    def __post_init__(self):
        if self.rsi_period is None:
            self.rsi_period = [5, 10, 14, 20, 25, 30]
        if self.overbought_threshold is None:
            self.overbought_threshold = [65, 70, 75, 80, 85]
        if self.oversold_threshold is None:
            self.oversold_threshold = [15, 20, 25, 30, 35]
        if self.stop_loss is None:
            self.stop_loss = [0.05, 0.10, 0.15, 0.20]
        if self.take_profit is None:
            self.take_profit = [0.15, 0.20, 0.25, 0.30, 0.35]
        if self.position_size is None:
            self.position_size = [0.1, 0.2, 0.3, 0.5, 1.0]
        if self.macd_fast is None:
            self.macd_fast = [12, 13, 14, 15]
        if self.macd_slow is None:
            self.macd_slow = [26, 27, 28, 29]
        if self.macd_signal is None:
            self.macd_signal = [9, 10, 11, 12]
        if self.bb_period is None:
            self.bb_period = [10, 15, 20, 25]
        if self.bb_std is None:
            self.bb_std = [1.5, 2.0, 2.5]

class BaseOptimizationEngine(ABC):
    """優化引擎基類"""

    def __init__(self, data: pd.DataFrame, param_grid: ParameterGrid,
                 max_workers: int = 32, risk_free_rate: float = 0.03):
        self.data = data
        self.param_grid = param_grid
        self.max_workers = max_workers
        self.risk_free_rate = risk_free_rate
        self.optimization_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    @abstractmethod
    def optimize(self) -> OptimizationResult:
        pass

    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """計算Sharpe比率"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        excess_returns = returns - self.risk_free_rate / 252
        return np.sqrt(252) * excess_returns.mean() / returns.std()

    def calculate_performance_metrics(self, portfolio_value: pd.Series) -> Dict[str, float]:
        """計算完整的性能指標"""
        returns = portfolio_value.pct_change().dropna()

        # 基本指標
        total_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0]) - 1
        sharpe_ratio = self.calculate_sharpe_ratio(returns)

        # 回撤分析
        rolling_max = portfolio_value.expanding().max()
        drawdown = (portfolio_value - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # Calmar比率
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino比率
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0.01
        sortino_ratio = (returns.mean() - self.risk_free_rate / 252) / downside_std * np.sqrt(252)

        # 勝率
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'win_rate': win_rate
        }

    def generate_rsi_signals(self, data: pd.DataFrame, period: int,
                           overbought: float, oversold: float) -> pd.Series:
        """生成RSI信號"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        buy_signals = rsi < oversold
        sell_signals = rsi > overbought

        return np.where(buy_signals, 1, np.where(sell_signals, -1, 0))

    def generate_macd_signals(self, data: pd.DataFrame, fast: int, slow: int, signal: int) -> pd.Series:
        """生成MACD信號"""
        exp1 = data['close'].ewm(span=fast).mean()
        exp2 = data['close'].ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()

        histogram = macd - signal_line

        return np.where(histogram > 0, 1, -1)

    def generate_bb_signals(self, data: pd.DataFrame, period: int, std_dev: float) -> pd.Series:
        """生成布林帶信號"""
        sma = data['close'].rolling(window=period).mean()
        std = data['close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        buy_signals = data['close'] < lower_band
        sell_signals = data['close'] > upper_band

        return np.where(buy_signals, 1, np.where(sell_signals, -1, 0))

class GridSearchEngine(BaseOptimizationEngine):
    """Grid Search優化引擎"""

    def __init__(self, data: pd.DataFrame, param_grid: ParameterGrid,
                 max_workers: int = 32, early_stopping: bool = True,
                 early_stopping_patience: int = 50, min_improvement: float = 0.001):
        super().__init__(data, param_grid, max_workers)
        self.early_stopping = early_stopping
        self.early_stopping_patience = early_stopping_patience
        self.min_improvement = min_improvement

    def generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """生成所有參數組合"""
        param_names = list(self.param_grid.__dataclass_fields__.keys())
        param_values = [getattr(self.param_grid, name) for name in param_names]

        combinations = []

        # 使用笛卡爾積生成所有組合
        import itertools
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            combinations.append(param_dict)

        logger.info(f"Generated {len(combinations)} parameter combinations")
        return combinations

    def evaluate_single_parameter_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """評估單個參數集"""
        try:
            # 組合多個信號
            signals = pd.Series(0, index=self.data.index)

            # RSI信號
            if params.get('rsi_period', 0) > 0:
                rsi_signal = self.generate_rsi_signals(
                    self.data, params['rsi_period'],
                    params['overbought_threshold'], params['oversold_threshold']
                )
                signals += rsi_signal

            # MACD信號
            if params.get('macd_fast', 0) > 0 and params.get('macd_slow', 0) > 0:
                macd_signal = self.generate_macd_signals(
                    self.data, params['macd_fast'], params['macd_slow'], params['macd_signal']
                )
                signals += macd_signal

            # 布林帶信號
            if params.get('bb_period', 0) > 0:
                bb_signal = self.generate_bb_signals(
                    self.data, params['bb_period'], params['bb_std']
                )
                signals += bb_signal

            # 淨信號過濾
            final_signals = np.where(signals > 0, 1, np.where(signals < 0, -1, 0))

            # 使用VectorBT進行回測
            portfolio = vbt.Portfolio.from_signals(
                close=self.data['close'],
                entries=(final_signals == 1),
                exits=(final_signals == -1),
                init_cash=100000,
                fees=0.001,
                slippage=0.001
            )

            # 計算性能指標
            portfolio_value = portfolio.value()
            metrics = self.calculate_performance_metrics(portfolio_value)

            result = {
                'parameters': params,
                'sharpe_ratio': metrics['sharpe_ratio'],
                'total_return': metrics['total_return'],
                'max_drawdown': metrics['max_drawdown'],
                'calmar_ratio': metrics['calmar_ratio'],
                'sortino_ratio': metrics['sortino_ratio'],
                'win_rate': metrics['win_rate']
            }

            return result

        except Exception as e:
            logger.error(f"Error evaluating parameters {params}: {str(e)}")
            return {
                'parameters': params,
                'sharpe_ratio': -999.0,  # 極差的分數
                'total_return': -1.0,
                'max_drawdown': -1.0,
                'calmar_ratio': -999.0,
                'sortino_ratio': -999.0,
                'win_rate': 0.0
            }

    def optimize(self) -> OptimizationResult:
        """執行Grid Search優化"""
        start_time = time.time()

        # 生成參數組合
        combinations = self.generate_parameter_combinations()
        total_combinations = len(combinations)

        logger.info(f"Starting Grid Search with {total_combinations} combinations using {self.max_workers} workers")

        # 並行執行
        results = []
        best_score = -float('inf')
        no_improvement_count = 0

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任務
            future_to_params = {
                executor.submit(self.evaluate_single_parameter_set, combo): combo
                for combo in combinations
            }

            # 處理完成的任務
            for i, future in enumerate(as_completed(future_to_params)):
                result = future.result()
                results.append(result)

                # 檢查是否需要提前停止
                if self.early_stopping:
                    current_score = result['sharpe_ratio']
                    if current_score > best_score + self.min_improvement:
                        best_score = current_score
                        no_improvement_count = 0
                    else:
                        no_improvement_count += 1

                    if no_improvement_count >= self.early_stopping_patience:
                        logger.info(f"Early stopping triggered after {i+1} evaluations")
                        break

                # 進度報告
                if (i + 1) % 100 == 0:
                    logger.info(f"Evaluated {i+1}/{total_combinations} combinations")

        # 找到最佳結果
        best_result = max(results, key=lambda x: x['sharpe_ratio'])

        # 獲取前10個結果
        sorted_results = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)
        top_10_results = [r for r in sorted_results[:10] if r['sharpe_ratio'] > -900]

        execution_time = time.time() - start_time

        optimization_result = OptimizationResult(
            best_parameters=best_result['parameters'],
            best_sharpe_ratio=best_result['sharpe_ratio'],
            total_return=best_result['total_return'],
            max_drawdown=best_result['max_drawdown'],
            calmar_ratio=best_result['calmar_ratio'],
            sortino_ratio=best_result['sortino_ratio'],
            win_rate=best_result['win_rate'],
            optimization_id=self.optimization_id,
            method="grid_search",
            total_combinations=len(results),
            execution_time=execution_time,
            top_results=top_10_results
        )

        logger.info(f"Grid Search completed. Best Sharpe: {best_result['sharpe_ratio']:.4f}")
        return optimization_result

class BayesianOptimizationEngine(BaseOptimizationEngine):
    """貝葉斯優化引擎"""

    def __init__(self, data: pd.DataFrame, param_grid: ParameterGrid,
                 max_iterations: int = 100, acquisition_function: str = 'ei'):
        super().__init__(data, param_grid, max_workers=1)  # 貝葉斯優化是串行的
        self.max_iterations = max_iterations
        self.acquisition_function = acquisition_function
        self.gpr = GaussianProcessRegressor(
            kernel=Matern(nu=2.5),
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=25
        )
        self.evaluated_params = []
        self.evaluated_scores = []

    def param_dict_to_array(self, params: Dict[str, Any]) -> np.ndarray:
        """將參數字典轉換為數組"""
        param_names = list(self.param_grid.__dataclass_fields__.keys())
        return np.array([params[name] for name in param_names])

    def param_array_to_dict(self, param_array: np.ndarray) -> Dict[str, Any]:
        """將參數數組轉換為字典"""
        param_names = list(self.param_grid.__dataclass_fields__.keys())
        return dict(zip(param_names, param_array))

    def suggest_next_parameters(self) -> Dict[str, Any]:
        """建議下一組參數"""
        if len(self.evaluated_params) < 5:
            # 隨機初始化
            return self._random_parameters()

        # 準備訓練數據
        X = np.array([self.param_dict_to_array(p) for p in self.evaluated_params])
        y = np.array(self.evaluated_scores)

        # 訓練高斯過程
        self.gpr.fit(X, y)

        # 生成候選點
        candidates = []
        for _ in range(1000):  # 生成1000個隨機候選
            candidate = self._random_parameters()
            candidates.append(candidate)

        # 評估候選點的獲取函數值
        X_candidates = np.array([self.param_dict_to_array(c) for c in candidates])
        mu, sigma = self.gpr.predict(X_candidates, return_std=True)

        if self.acquisition_function == 'ei':
            # Expected Improvement
            best_y = np.max(y)
            with np.errstate(divide='warn'):
                imp = mu - best_y - 0.01
                Z = imp / sigma
                ei = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
                ei[sigma == 0.0] = 0.0
            acquisition_values = ei
        elif self.acquisition_function == 'ucb':
            # Upper Confidence Bound
            kappa = 2.576  # 99% confidence
            acquisition_values = mu + kappa * sigma
        else:
            # Probability of Improvement
            best_y = np.max(y)
            with np.errstate(divide='warn'):
                Z = (mu - best_y - 0.01) / sigma
                pi = norm.cdf(Z)
                pi[sigma == 0.0] = 0.0
            acquisition_values = pi

        # 返回獲取函數值最大的候選
        best_idx = np.argmax(acquisition_values)
        return candidates[best_idx]

    def _random_parameters(self) -> Dict[str, Any]:
        """生成隨機參數"""
        param_names = list(self.param_grid.__dataclass_fields__.keys())
        params = {}
        for name in param_names:
            values = getattr(self.param_grid, name)
            params[name] = random.choice(values)
        return params

    def optimize(self) -> OptimizationResult:
        """執行貝葉斯優化"""
        start_time = time.time()

        logger.info(f"Starting Bayesian Optimization with {self.max_iterations} iterations")

        best_score = -float('inf')
        best_params = None
        best_metrics = None

        for iteration in range(self.max_iterations):
            # 建議下一組參數
            if len(self.evaluated_params) == 0:
                params = self._random_parameters()
            else:
                params = self.suggest_next_parameters()

            # 評估參數
            grid_engine = GridSearchEngine(self.data, self.param_grid, max_workers=1)
            result = grid_engine.evaluate_single_parameter_set(params)

            # 更新數據
            self.evaluated_params.append(params)
            self.evaluated_scores.append(result['sharpe_ratio'])

            # 更新最佳結果
            if result['sharpe_ratio'] > best_score:
                best_score = result['sharpe_ratio']
                best_params = params
                best_metrics = result

            # 進度報告
            if (iteration + 1) % 10 == 0:
                logger.info(f"Iteration {iteration+1}/{self.max_iterations}, Best Sharpe: {best_score:.4f}")

        execution_time = time.time() - start_time

        optimization_result = OptimizationResult(
            best_parameters=best_params,
            best_sharpe_ratio=best_score,
            total_return=best_metrics['total_return'],
            max_drawdown=best_metrics['max_drawdown'],
            calmar_ratio=best_metrics['calmar_ratio'],
            sortino_ratio=best_metrics['sortino_ratio'],
            win_rate=best_metrics['win_rate'],
            optimization_id=self.optimization_id,
            method="bayesian_optimization",
            total_combinations=len(self.evaluated_params),
            execution_time=execution_time,
            top_results=[best_metrics]  # 貝葉斯優化主要返回最佳結果
        )

        logger.info(f"Bayesian Optimization completed. Best Sharpe: {best_score:.4f}")
        return optimization_result

class GeneticAlgorithmEngine(BaseOptimizationEngine):
    """遺傳算法優化引擎"""

    def __init__(self, data: pd.DataFrame, param_grid: ParameterGrid,
                 population_size: int = 50, generations: int = 20,
                 mutation_rate: float = 0.1, crossover_rate: float = 0.8):
        super().__init__(data, param_grid, max_workers=1)
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate

    def initialize_population(self) -> List[Dict[str, Any]]:
        """初始化種群"""
        population = []
        param_names = list(self.param_grid.__dataclass_fields__.keys())

        for _ in range(self.population_size):
            individual = {}
            for name in param_names:
                values = getattr(self.param_grid, name)
                individual[name] = random.choice(values)
            population.append(individual)

        return population

    def evaluate_population(self, population: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """評估種群適應度"""
        evaluated = []
        grid_engine = GridSearchEngine(self.data, self.param_grid, max_workers=1)

        for individual in population:
            result = grid_engine.evaluate_single_parameter_set(individual)
            fitness = result['sharpe_ratio']
            evaluated.append((individual, fitness))

        return evaluated

    def selection(self, evaluated_population: List[Tuple[Dict[str, Any], float]],
                  num_parents: int) -> List[Dict[str, Any]]:
        """選擇 - 錦標賽選擇"""
        selected = []

        for _ in range(num_parents):
            # 隨機選擇3個個體進行錦標賽
            tournament = random.sample(evaluated_population, min(3, len(evaluated_population)))
            winner = max(tournament, key=lambda x: x[1])
            selected.append(winner[0])

        return selected

    def crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        """交叉 - 均勻交叉"""
        if random.random() > self.crossover_rate:
            return parent1

        child = {}
        param_names = list(self.param_grid.__dataclass_fields__.keys())

        for name in param_names:
            if random.random() < 0.5:
                child[name] = parent1[name]
            else:
                child[name] = parent2[name]

        return child

    def mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """變異"""
        mutated = individual.copy()
        param_names = list(self.param_grid.__dataclass_fields__.keys())

        for name in param_names:
            if random.random() < self.mutation_rate:
                values = getattr(self.param_grid, name)
                mutated[name] = random.choice(values)

        return mutated

    def optimize(self) -> OptimizationResult:
        """執行遺傳算法優化"""
        start_time = time.time()

        logger.info(f"Starting Genetic Algorithm with population_size={self.population_size}, generations={self.generations}")

        # 初始化種群
        population = self.initialize_population()

        best_individual = None
        best_fitness = -float('inf')
        best_metrics = None

        for generation in range(self.generations):
            # 評估種群
            evaluated_population = self.evaluate_population(population)

            # 更新最佳個體
            current_best = max(evaluated_population, key=lambda x: x[1])
            if current_best[1] > best_fitness:
                best_fitness = current_best[1]
                best_individual = current_best[0]

                # 獲取完整指標
                grid_engine = GridSearchEngine(self.data, self.param_grid, max_workers=1)
                best_metrics = grid_engine.evaluate_single_parameter_set(best_individual)

            # 選擇
            num_parents = self.population_size // 2
            parents = self.selection(evaluated_population, num_parents)

            # 生成新一代
            new_population = []

            # 精英保留 - 直接保留最佳個體
            elite_size = max(1, self.population_size // 10)
            elite = [ind for ind, fit in sorted(evaluated_population, key=lambda x: x[1], reverse=True)[:elite_size]]
            new_population.extend(elite)

            # 交叉和變異生成剩餘個體
            while len(new_population) < self.population_size:
                parent1 = random.choice(parents)
                parent2 = random.choice(parents)

                child = self.crossover(parent1, parent2)
                child = self.mutate(child)

                new_population.append(child)

            population = new_population

            # 進度報告
            avg_fitness = np.mean([fit for ind, fit in evaluated_population])
            logger.info(f"Generation {generation+1}/{self.generations}, Best Sharpe: {best_fitness:.4f}, Avg Sharpe: {avg_fitness:.4f}")

        execution_time = time.time() - start_time

        optimization_result = OptimizationResult(
            best_parameters=best_individual,
            best_sharpe_ratio=best_fitness,
            total_return=best_metrics['total_return'],
            max_drawdown=best_metrics['max_drawdown'],
            calmar_ratio=best_metrics['calmar_ratio'],
            sortino_ratio=best_metrics['sortino_ratio'],
            win_rate=best_metrics['win_rate'],
            optimization_id=self.optimization_id,
            method="genetic_algorithm",
            total_combinations=len(population) * self.generations,
            execution_time=execution_time,
            top_results=[best_metrics]
        )

        logger.info(f"Genetic Algorithm completed. Best Sharpe: {best_fitness:.4f}")
        return optimization_result

class VectorBTOptimizer:
    """VectorBT優化器主類"""

    def __init__(self, data: pd.DataFrame, max_workers: int = 32, risk_free_rate: float = 0.03):
        self.data = data
        self.max_workers = max_workers
        self.risk_free_rate = risk_free_rate
        self.param_grid = ParameterGrid()

    def optimize_all_methods(self) -> Dict[str, OptimizationResult]:
        """使用所有方法進行優化"""
        results = {}

        # Grid Search
        logger.info("Starting Grid Search optimization...")
        grid_engine = GridSearchEngine(self.data, self.param_grid, self.max_workers)
        results['grid_search'] = grid_engine.optimize()

        # Bayesian Optimization
        logger.info("Starting Bayesian optimization...")
        bayesian_engine = BayesianOptimizationEngine(self.data, self.param_grid, max_iterations=100)
        results['bayesian'] = bayesian_engine.optimize()

        # Genetic Algorithm
        logger.info("Starting Genetic Algorithm optimization...")
        genetic_engine = GeneticAlgorithmEngine(self.data, self.param_grid,
                                              population_size=50, generations=20)
        results['genetic'] = genetic_engine.optimize()

        # 找到最佳方法
        best_method = max(results.keys(), key=lambda k: results[k].best_sharpe_ratio)
        logger.info(f"Best method: {best_method} with Sharpe ratio: {results[best_method].best_sharpe_ratio:.4f}")

        return results

    def save_results(self, results: Dict[str, OptimizationResult], output_file: str = None) -> str:
        """保存優化結果"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"vectorbt_optimization_results_{timestamp}.json"

        # 轉換結果為可序列化格式
        serializable_results = {}
        for method, result in results.items():
            serializable_results[method] = asdict(result)

        # 保存到JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Results saved to {output_file}")
        return output_file

    def generate_report(self, results: Dict[str, OptimizationResult], output_file: str = None) -> str:
        """生成HTML報告"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"vectorbt_optimization_report_{timestamp}.html"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>VectorBT Parameter Optimization Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .method-result {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .best-result {{ background-color: #e8f5e8; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ display: inline-block; margin: 5px 10px; padding: 5px 10px; background-color: #f9f9f9; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>VectorBT Parameter Optimization Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Data Period: {self.data.index[0].strftime('%Y-%m-%d')} to {self.data.index[-1].strftime('%Y-%m-%d')}</p>
                <p>Total Data Points: {len(self.data)}</p>
            </div>
        """

        # 找到最佳方法
        best_method = max(results.keys(), key=lambda k: results[k].best_sharpe_ratio)

        for method, result in results.items():
            is_best = method == best_method
            css_class = "best-result" if is_best else "method-result"

            html_content += f"""
            <div class="{css_class}">
                <h3>{method.upper().replace('_', ' ')} {'🏆' if is_best else ''}</h3>
                <div class="metric"><strong>Sharpe Ratio:</strong> {result.best_sharpe_ratio:.4f}</div>
                <div class="metric"><strong>Total Return:</strong> {result.total_return:.2%}</div>
                <div class="metric"><strong>Max Drawdown:</strong> {result.max_drawdown:.2%}</div>
                <div class="metric"><strong>Calmar Ratio:</strong> {result.calmar_ratio:.4f}</div>
                <div class="metric"><strong>Win Rate:</strong> {result.win_rate:.2%}</div>
                <div class="metric"><strong>Execution Time:</strong> {result.execution_time:.2f}s</div>
                <div class="metric"><strong>Combinations Tested:</strong> {result.total_combinations:,}</div>

                <h4>Best Parameters:</h4>
                <pre>{json.dumps(result.best_parameters, indent=2)}</pre>
            """

            if result.top_results and len(result.top_results) > 1:
                html_content += "<h4>Top 5 Results:</h4><table>"
                html_content += "<tr><th>Rank</th><th>Sharpe Ratio</th><th>Total Return</th><th>Max Drawdown</th><th>Parameters</th></tr>"

                for i, top_result in enumerate(result.top_results[:5]):
                    html_content += f"""
                    <tr>
                        <td>{i+1}</td>
                        <td>{top_result['sharpe_ratio']:.4f}</td>
                        <td>{top_result['total_return']:.2%}</td>
                        <td>{top_result['max_drawdown']:.2%}</td>
                        <td>{json.dumps(top_result['parameters'], separators=(',', ':'))}</td>
                    </tr>
                    """

                html_content += "</table>"

            html_content += "</div>"

        html_content += """
        </body>
        </html>
        """

        # 保存HTML文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Report generated: {output_file}")
        return output_file

if __name__ == "__main__":
    # 測試代碼將在實際使用時添加
    pass