#!/usr/bin/env python3
"""
智能參數優化系統
Intelligent Parameter Optimization System

實現專業級量化交易參數優化，包括：
1. Grid Search（網格搜尋）
2. Bayesian Optimization（貝葉斯優化）
3. Genetic Algorithm（遺傳演算法）
4. Walk-Forward Analysis（前進分析）
5. 過度擬合檢測與防護
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod
import itertools
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import warnings

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """優化配置"""
    strategy_type: str = 'RSI'
    parameter_ranges: Dict[str, List[Any]] = field(default_factory=dict)
    optimization_method: str = 'grid_search'  # grid_search, bayesian, genetic
    max_iterations: int = 1000
    cv_folds: int = 5  # 交叉驗證折數
    walk_forward_windows: int = 3
    parallel_workers: int = 32
    early_stopping_patience: int = 50
    min_improvement: float = 0.001

@dataclass
class ParameterResult:
    """參數優化結果"""
    parameters: Dict[str, Any]
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    win_rate: float
    cv_score: float  # 交叉驗證分數
    walk_forward_score: float
    overfitting_risk: float  # 過度擬合風險
    robustness_score: float  # 穩健性分數
    timestamp: datetime

class BaseOptimizer(ABC):
    """優化器基類"""

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.best_result = None
        self.optimization_history = []

    @abstractmethod
    def optimize(self, objective_func: Callable, **kwargs) -> ParameterResult:
        """執行優化"""
        pass

class GridSearchOptimizer(BaseOptimizer):
    """網格搜尋優化器"""

    def __init__(self, config: OptimizationConfig):
        super().__init__(config)
        self.param_combinations = self._generate_combinations()

    def _generate_combinations(self) -> List[Dict[str, Any]]:
        """生成所有參數組合"""
        param_names = list(self.config.parameter_ranges.keys())
        param_values = list(self.config.parameter_ranges.values())

        combinations = []
        for combo in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combo))
            combinations.append(param_dict)

        logger.info(f"Generated {len(combinations)} parameter combinations")
        return combinations

    def optimize(self, objective_func: Callable, **kwargs) -> ParameterResult:
        """執行網格搜尋"""
        logger.info(f"Starting Grid Search with {len(self.param_combinations)} combinations")

        results = []
        best_sharpe = -float('inf')

        # 並行處理
        with ProcessPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            futures = {
                executor.submit(self._evaluate_single, params, objective_func, i, **kwargs): (i, params)
                for i, params in enumerate(self.param_combinations)
            }

            completed = 0
            for future in as_completed(futures):
                i, params = futures[future]
                try:
                    result = future.result()
                    results.append(result)

                    if result.sharpe_ratio > best_sharpe:
                        best_sharpe = result.sharpe_ratio
                        self.best_result = result

                    completed += 1
                    if completed % 100 == 0:
                        logger.info(f"Completed {completed}/{len(self.param_combinations)} combinations")

                except Exception as e:
                    logger.error(f"Error evaluating parameters {params}: {e}")

        # 按Sharpe比率排序
        results.sort(key=lambda x: x.sharpe_ratio, reverse=True)
        self.optimization_history = results[:100]  # 保存前100個最佳結果

        logger.info(f"Grid Search completed. Best Sharpe: {best_sharpe:.4f}")
        return self.best_result

    def _evaluate_single(self, params: Dict[str, Any], objective_func: Callable,
                         param_id: int, **kwargs) -> ParameterResult:
        """評估單個參數組合"""
        try:
            result = objective_func(params, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Parameter {param_id} evaluation failed: {e}")
            # 返回最差結果
            return ParameterResult(
                parameters=params,
                sharpe_ratio=-10.0,
                total_return=0.0,
                max_drawdown=1.0,
                win_rate=0.0,
                cv_score=0.0,
                walk_forward_score=0.0,
                overfitting_risk=1.0,
                robustness_score=0.0,
                timestamp=datetime.now()
            )

class BayesianOptimizer(BaseOptimizer):
    """貝葉斯優化器"""

    def __init__(self, config: OptimizationConfig):
        super().__init__(config)
        self.explored_params = []
        self.scores = []

    def optimize(self, objective_func: Callable, **kwargs) -> ParameterResult:
        """執行貝葉斯優化"""
        logger.info(f"Starting Bayesian Optimization with {self.config.max_iterations} iterations")

        best_result = None
        best_sharpe = -float('inf')
        patience_counter = 0

        for iteration in range(self.config.max_iterations):
            # 採集函數：選擇下一個評估點
            if len(self.explored_params) < 5:
                # 初始隨機探索
                params = self._random_sample()
            else:
                # 貝葉斯優化選擇
                params = self._acquisition_function()

            # 評估參數
            result = objective_func(params, **kwargs)

            # 更新經驗
            self.explored_params.append(params)
            self.scores.append(result.sharpe_ratio)

            # 更新最佳結果
            if result.sharpe_ratio > best_sharpe:
                best_sharpe = result.sharpe_ratio
                best_result = result
                patience_counter = 0
                logger.info(f"Iteration {iteration}: New best Sharpe: {best_sharpe:.4f}")
            else:
                patience_counter += 1

            # 早停檢查
            if patience_counter >= self.config.early_stopping_patience:
                logger.info(f"Early stopping at iteration {iteration}")
                break

        self.best_result = best_result
        logger.info(f"Bayesian Optimization completed. Best Sharpe: {best_sharpe:.4f}")
        return best_result

    def _random_sample(self) -> Dict[str, Any]:
        """隨機採樣"""
        params = {}
        for param_name, param_range in self.config.parameter_ranges.items():
            if isinstance(param_range, list):
                params[param_name] = np.random.choice(param_range)
            else:
                # 假設是數值範圍
                params[param_name] = np.random.uniform(param_range[0], param_range[1])
        return params

    def _acquisition_function(self) -> Dict[str, Any]:
        """採集函數：平衡探索與利用"""
        # 簡化版：基於高斯過程的採集函數
        # 這裡使用簡單的 Upper Confidence Bound (UCB)

        # 將參數轉換為數值向量
        explored_vectors = self._params_to_vectors(self.explored_params)

        # 隨機生成候選點
        candidates = [self._random_sample() for _ in range(100)]
        candidate_vectors = self._params_to_vectors(candidates)

        # 計算UCB分數
        ucb_scores = []
        for vec in candidate_vectors:
            mean, std = self._gp_predict(vec, explored_vectors, self.scores)
            ucb = mean + 2.0 * std  # UCB = μ + 2σ
            ucb_scores.append(ucb)

        # 選擇UCB最大的候選點
        best_idx = np.argmax(ucb_scores)
        return candidates[best_idx]

    def _params_to_vectors(self, params_list: List[Dict[str, Any]]) -> np.ndarray:
        """將參數字典轉換為數值向量"""
        if not params_list:
            return np.array([])

        vectors = []
        for params in params_list:
            vector = []
            for param_name in sorted(self.config.parameter_ranges.keys()):
                value = params[param_name]
                if isinstance(value, (int, float)):
                    vector.append(value)
                else:
                    # 類別變量編碼
                    param_range = self.config.parameter_ranges[param_name]
                    if isinstance(param_range, list):
                        vector.append(param_range.index(value))
                    else:
                        vector.append(0.0)
            vectors.append(vector)

        return np.array(vectors)

    def _gp_predict(self, x: np.ndarray, X_train: np.ndarray, y_train: np.ndarray) -> Tuple[float, float]:
        """簡化的高斯過程預測"""
        if len(X_train) == 0:
            return 0.0, 1.0

        # 計算距離
        distances = np.linalg.norm(X_train - x, axis=1)

        # RBF核函數
        sigma = 1.0
        kernel_values = np.exp(-distances**2 / (2 * sigma**2))

        # 預測均值和方差
        mean = np.sum(kernel_values * y_train) / (np.sum(kernel_values) + 1e-8)

        # 預測方差
        variance = 1.0 - np.sum(kernel_values**2) / (np.sum(kernel_values) + 1e-8)

        return mean, max(0.0, variance)

class GeneticOptimizer(BaseOptimizer):
    """遺傳演算法優化器"""

    def __init__(self, config: OptimizationConfig):
        super().__init__(config)
        self.population_size = 50
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
        self.elite_ratio = 0.2

    def optimize(self, objective_func: Callable, **kwargs) -> ParameterResult:
        """執行遺傳演算法優化"""
        logger.info(f"Starting Genetic Algorithm Optimization")

        # 初始化種群
        population = self._initialize_population()

        best_result = None
        best_sharpe = -float('inf')

        for generation in range(self.config.max_iterations // self.population_size):
            # 評估種群
            fitness_scores = []
            for individual in population:
                try:
                    result = objective_func(individual, **kwargs)
                    fitness_scores.append(result.sharpe_ratio)

                    if result.sharpe_ratio > best_sharpe:
                        best_sharpe = result.sharpe_ratio
                        best_result = result
                        logger.info(f"Generation {generation}: New best Sharpe: {best_sharpe:.4f}")

                except Exception as e:
                    fitness_scores.append(-10.0)
                    logger.error(f"Error evaluating individual: {e}")

            # 選擇、交叉、變異
            new_population = self._evolve_population(population, fitness_scores)
            population = new_population

        self.best_result = best_result
        logger.info(f"Genetic Algorithm completed. Best Sharpe: {best_sharpe:.4f}")
        return best_result

    def _initialize_population(self) -> List[Dict[str, Any]]:
        """初始化種群"""
        population = []
        for _ in range(self.population_size):
            individual = {}
            for param_name, param_range in self.config.parameter_ranges.items():
                if isinstance(param_range, list):
                    individual[param_name] = np.random.choice(param_range)
                else:
                    individual[param_name] = np.random.uniform(param_range[0], param_range[1])
            population.append(individual)
        return population

    def _evolve_population(self, population: List[Dict[str, Any]],
                           fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """進化種群"""
        # 精英選擇
        elite_size = int(self.population_size * self.elite_ratio)
        elite_indices = np.argsort(fitness_scores)[-elite_size:]
        new_population = [population[i] for i in elite_indices]

        # 填充剩餘位置
        while len(new_population) < self.population_size:
            # 錦標賽選擇
            parent1 = self._tournament_selection(population, fitness_scores)
            parent2 = self._tournament_selection(population, fitness_scores)

            # 交叉
            if np.random.random() < self.crossover_rate:
                child = self._crossover(parent1, parent2)
            else:
                child = parent1.copy()

            # 變異
            if np.random.random() < self.mutation_rate:
                child = self._mutate(child)

            new_population.append(child)

        return new_population

    def _tournament_selection(self, population: List[Dict[str, Any]],
                              fitness_scores: List[float], tournament_size: int = 3) -> Dict[str, Any]:
        """錦標賽選擇"""
        indices = np.random.choice(len(population), tournament_size, replace=False)
        best_idx = max(indices, key=lambda i: fitness_scores[i])
        return population[best_idx].copy()

    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        """交叉操作"""
        child = {}
        for param_name in self.config.parameter_ranges.keys():
            if np.random.random() < 0.5:
                child[param_name] = parent1[param_name]
            else:
                child[param_name] = parent2[param_name]
        return child

    def _mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """變異操作"""
        mutant = individual.copy()
        param_name = np.random.choice(list(self.config.parameter_ranges.keys()))
        param_range = self.config.parameter_ranges[param_name]

        if isinstance(param_range, list):
            mutant[param_name] = np.random.choice(param_range)
        else:
            mutant[param_name] = np.random.uniform(param_range[0], param_range[1])

        return mutant

class WalkForwardAnalyzer:
    """前進分析器"""

    def __init__(self, n_windows: int = 3, train_ratio: float = 0.7):
        self.n_windows = n_windows
        self.train_ratio = train_ratio

    def analyze(self, data: pd.DataFrame, objective_func: Callable,
                optimizer: BaseOptimizer) -> float:
        """執行前進分析"""
        logger.info(f"Starting Walk-Forward Analysis with {self.n_windows} windows")

        window_size = len(data) // self.n_windows
        scores = []

        for window in range(self.n_windows):
            # 訓練期和測試期
            start_idx = window * window_size
            end_idx = (window + 1) * window_size

            if end_idx > len(data):
                break

            train_data = data.iloc[start_idx:int(start_idx + window_size * self.train_ratio)]
            test_data = data.iloc[int(start_idx + window_size * self.train_ratio):end_idx]

            # 在訓練期優化參數
            def train_objective(params):
                return objective_func(params, train_data)

            best_params = optimizer.optimize(train_objective)

            # 在測試期評估
            test_result = objective_func(best_params.parameters, test_data)
            scores.append(test_result.sharpe_ratio)

            logger.info(f"Window {window + 1}: Train Sharpe: {best_params.sharpe_ratio:.4f}, "
                       f"Test Sharpe: {test_result.sharpe_ratio:.4f}")

        walk_forward_score = np.mean(scores)
        logger.info(f"Walk-Forward Analysis completed. Average Sharpe: {walk_forward_score:.4f}")

        return walk_forward_score

class OverfittingDetector:
    """過度擬合檢測器"""

    @staticmethod
    def calculate_overfitting_risk(in_sample_score: float, out_sample_score: float,
                                  cv_scores: List[float]) -> float:
        """計算過度擬合風險"""
        # 樣本內外性能差異
        performance_gap = in_sample_score - out_sample_score

        # 交叉驗證方差
        cv_variance = np.var(cv_scores) if len(cv_scores) > 1 else 0

        # 綜合風險分數 (0-1)
        risk_score = min(1.0, max(0.0,
            (performance_gap / abs(in_sample_score) if in_sample_score != 0 else 0) * 0.6 +
            (cv_variance / 1.0) * 0.4
        ))

        return risk_score

    @staticmethod
    def calculate_robustness_score(cv_scores: List[float],
                                 walk_forward_score: float) -> float:
        """計算穩健性分數"""
        if len(cv_scores) == 0:
            return 0.0

        # 交叉驗證穩定性
        cv_mean = np.mean(cv_scores)
        cv_std = np.std(cv_scores)
        cv_stability = 1.0 - (cv_std / abs(cv_mean) if cv_mean != 0 else 1.0)

        # 前進分析一致性
        consistency = min(1.0, walk_forward_score / abs(cv_mean) if cv_mean != 0 else 0)

        # 綜合穩健性分數
        robustness = (cv_stability * 0.6 + consistency * 0.4)

        return max(0.0, robustness)

class IntelligentParameterOptimizer:
    """智能參數優化器主類"""

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.optimizer = self._create_optimizer()
        self.walk_forward_analyzer = WalkForwardAnalyzer(config.walk_forward_windows)
        self.overfitting_detector = OverfittingDetector()

    def _create_optimizer(self) -> BaseOptimizer:
        """創建優化器"""
        if self.config.optimization_method == 'grid_search':
            return GridSearchOptimizer(self.config)
        elif self.config.optimization_method == 'bayesian':
            return BayesianOptimizer(self.config)
        elif self.config.optimization_method == 'genetic':
            return GeneticOptimizer(self.config)
        else:
            raise ValueError(f"Unknown optimization method: {self.config.optimization_method}")

    def optimize(self, data: pd.DataFrame, objective_func: Callable) -> ParameterResult:
        """執行完整優化流程"""
        logger.info(f"Starting intelligent parameter optimization using {self.config.optimization_method}")

        # 1. 基本優化
        def basic_objective(params):
            return objective_func(params, data)

        best_result = self.optimizer.optimize(basic_objective)

        # 2. 交叉驗證
        cv_scores = self._cross_validation(data, objective_func, best_result.parameters)
        cv_score = np.mean(cv_scores)

        # 3. 前進分析
        walk_forward_score = self.walk_forward_analyzer.analyze(data, objective_func, self.optimizer)

        # 4. 過度擬合檢測
        overfitting_risk = self.overfitting_detector.calculate_overfitting_risk(
            best_result.sharpe_ratio, cv_score, cv_scores
        )

        # 5. 穩健性評分
        robustness_score = self.overfitting_detector.calculate_robustness_score(
            cv_scores, walk_forward_score
        )

        # 更新結果
        best_result.cv_score = cv_score
        best_result.walk_forward_score = walk_forward_score
        best_result.overfitting_risk = overfitting_risk
        best_result.robustness_score = robustness_score

        logger.info(f"Optimization completed:")
        logger.info(f"  In-Sample Sharpe: {best_result.sharpe_ratio:.4f}")
        logger.info(f"  CV Score: {cv_score:.4f}")
        logger.info(f"  Walk-Forward Score: {walk_forward_score:.4f}")
        logger.info(f"  Overfitting Risk: {overfitting_risk:.3f}")
        logger.info(f"  Robustness Score: {robustness_score:.3f}")

        return best_result

    def _cross_validation(self, data: pd.DataFrame, objective_func: Callable,
                         best_params: Dict[str, Any]) -> List[float]:
        """執行交叉驗證"""
        fold_size = len(data) // self.config.cv_folds
        scores = []

        for fold in range(self.config.cv_folds):
            start_idx = fold * fold_size
            end_idx = (fold + 1) * fold_size if fold < self.config.cv_folds - 1 else len(data)

            train_data = pd.concat([data.iloc[:start_idx], data.iloc[end_idx:]])
            val_data = data.iloc[start_idx:end_idx]

            # 在訓練集優化參數（使用較少的迭代）
            fold_optimizer = GridSearchOptimizer(OptimizationConfig(
                parameter_ranges=self.config.parameter_ranges,
                max_iterations=100
            ))

            def fold_objective(params):
                return objective_func(params, train_data)

            try:
                fold_result = fold_optimizer.optimize(fold_objective)
                val_result = objective_func(fold_result.parameters, val_data)
                scores.append(val_result.sharpe_ratio)
            except Exception as e:
                logger.error(f"Cross-validation fold {fold + 1} failed: {e}")
                scores.append(0.0)

        return scores

    def get_optimization_summary(self) -> Dict[str, Any]:
        """獲取優化摘要"""
        if not self.optimizer.best_result:
            return {}

        return {
            'best_parameters': self.optimizer.best_result.parameters,
            'performance_metrics': {
                'sharpe_ratio': self.optimizer.best_result.sharpe_ratio,
                'total_return': self.optimizer.best_result.total_return,
                'max_drawdown': self.optimizer.best_result.max_drawdown,
                'win_rate': self.optimizer.best_result.win_rate,
            },
            'validation_metrics': {
                'cv_score': self.optimizer.best_result.cv_score,
                'walk_forward_score': self.optimizer.best_result.walk_forward_score,
                'overfitting_risk': self.optimizer.best_result.overfitting_risk,
                'robustness_score': self.optimizer.best_result.robustness_score,
            },
            'optimization_config': {
                'method': self.config.optimization_method,
                'max_iterations': self.config.max_iterations,
                'cv_folds': self.config.cv_folds,
                'parallel_workers': self.config.parallel_workers,
            },
            'timestamp': datetime.now().isoformat()
        }

def create_optimization_config(strategy_type: str = 'RSI',
                             optimization_method: str = 'bayesian') -> OptimizationConfig:
    """創建優化配置範例"""

    if strategy_type == 'RSI':
        return OptimizationConfig(
            strategy_type=strategy_type,
            parameter_ranges={
                'window': list(range(5, 51, 5)),
                'buy_threshold': [x/10 for x in range(10, 36, 5)],
                'sell_threshold': [x/10 for x in range(65, 86, 5)]
            },
            optimization_method=optimization_method,
            max_iterations=500,
            cv_folds=5,
            walk_forward_windows=3,
            parallel_workers=16
        )

    elif strategy_type == 'MACD':
        return OptimizationConfig(
            strategy_type=strategy_type,
            parameter_ranges={
                'fast': list(range(5, 16, 2)),
                'slow': list(range(20, 41, 5)),
                'signal': list(range(5, 16, 2))
            },
            optimization_method=optimization_method,
            max_iterations=300,
            cv_folds=5,
            walk_forward_windows=3,
            parallel_workers=16
        )

    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

if __name__ == "__main__":
    # 示例使用
    config = create_optimization_config('RSI', 'bayesian')
    optimizer = IntelligentParameterOptimizer(config)

    print(f"Configuration created for {config.strategy_type} using {config.optimization_method}")
    print(f"Parameter ranges: {config.parameter_ranges}")
    print(f"Max iterations: {config.max_iterations}")
    print(f"Parallel workers: {config.parallel_workers}")