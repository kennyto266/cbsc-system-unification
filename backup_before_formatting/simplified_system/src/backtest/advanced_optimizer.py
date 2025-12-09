#!/usr/bin/env/python3
"""
Simplified System - 高級優化器
Advanced Optimizer for VectorBT Integration

貝葉斯優化、遺傳算法等高級參數優化算法
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional, Union
import logging
from scipy.optimize import differential_evolution
from scipy.stats import norm
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from dataclasses import dataclass

from .vectorbt_engine import VectorBTEngine, BacktestConfig

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """優化配置"""
    algorithm: str = "bayesian"  # bayesian, genetic, differential_evolution
    max_iterations: int = 100
    population_size: int = 50
    convergence_tolerance: float = 1e-6
    parallel_cores: Optional[int] = None  # None表示使用所有可用核心

class BayesianOptimizer:
    """貝葉斯優化器"""

    def __init__(self, engine: VectorBTEngine, config: OptimizationConfig):
        self.engine = engine
        self.config = config
        self.acquisition_function = "expected_improvement"

    def optimize(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_bounds: Dict[str, Tuple[float, float]],
        optimization_metric: str = "sharpe_ratio",
        n_calls: int = 50
    ) -> Dict[str, Any]:
        """
        貝葉斯優化

        Args:
            data: 價格數據
            strategy: 策略名稱
            param_bounds: 參數邊界 {param_name: (min, max)}
            optimization_metric: 優化目標
            n_calls: 優化調用次數

        Returns:
            優化結果
        """
        logger.info(f"Starting Bayesian optimization for {strategy}")

        # 初始化高斯過程
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern

        gp = GaussianProcessRegressor(
            kernel=Matern(length_scale=1.0, nu=2.5),
            alpha=1e-6,
            normalize_y=True
        )

        # 生成初始隨機樣本
        n_initial = min(10, n_calls // 2)
        X_init = []
        y_init = []

        param_names = list(param_bounds.keys())
        bounds_array = np.array([param_bounds[name] for name in param_names])

        # 初始隨機採樣
        for _ in range(n_initial):
            params = {}
            for i, name in enumerate(param_names):
                params[name] = np.random.uniform(bounds_array[i, 0], bounds_array[i, 1])

            try:
                score = self._evaluate_parameters(data, strategy, params, optimization_metric)
                if score is not None:
                    X_init.append([params[name] for name in param_names])
                    y_init.append(score)
            except Exception as e:
                logger.warning(f"Failed to evaluate initial sample: {e}")
                continue

        if len(X_init) == 0:
            # 如果初始採樣失敗，使用簡單網格搜索
            return self._fallback_grid_search(data, strategy, param_bounds, optimization_metric)

        X_init = np.array(X_init)
        y_init = np.array(y_init)

        # 貝葉斯優化循環
        best_params = None
        best_score = -float('inf')

        gp.fit(X_init, y_init)

        for iteration in range(n_initial, n_calls):
            # 獲取最大期望改進的點
            x_next = self._acquisition_maximization(gp, bounds_array, X_init, y_init)

            # 轉換回參數字典
            candidate_params = {param_names[i]: x_next[i] for i in range(len(param_names))}

            # 評評新點
            score = self._evaluate_parameters(data, strategy, candidate_params, optimization_metric)

            if score is not None and score > best_score:
                best_score = score
                best_params = candidate_params.copy()

            # 添加到訓練集
            X_init = np.vstack([X_init, x_next.reshape(1, -1)])
            y_init = np.append(y_init, score)

            # 更新高斯過程
            gp.fit(X_init, y_init)

            if iteration % 10 == 0:
                logger.info(f"Bayesian optimization iteration {iteration}: best_score={best_score:.4f}")

        return {
            'best_parameters': best_params,
            'best_score': best_score,
            'optimization_method': 'Bayesian Optimization',
            'total_evaluations': len(X_init),
            'converged': True
        }

    def _acquisition_maximization(self, gp, bounds, X_init, y_init):
        """最大期望改進獲取函數"""
        from scipy.optimize import minimize

        def acquisition_function(x):
            # 計算期望改進
            mu, sigma = gp.predict(x.reshape(1, -1), return_std=True)
            improvement = mu - np.max(y_init)
            z = improvement / (sigma + 1e-8)
            return -(improvement * norm.cdf(z) + sigma * norm.pdf(z))

        # 多個隨機起點避免局部最優
        best_x = None
        best_acq = float('inf')

        for _ in range(10):  # 10個隨機起點
            x0 = np.random.uniform(bounds[:, 0], bounds[:, 1])
            result = minimize(
                acquisition_function,
                x0,
                bounds=bounds,
                method='L-BFGS-B'
            )

            if result.fun < best_acq:
                best_acq = result.fun
                best_x = result.x

        return best_x

    def _fallback_grid_search(self, data, strategy, param_bounds, optimization_metric):
        """網格搜索後備方案"""
        logger.info("Falling back to grid search")

        param_names = list(param_bounds.keys())
        best_params = {}
        best_score = -float('inf')

        # 簡化的網格搜索
        for param_name, (min_val, max_val) in param_bounds.items():
            test_values = np.linspace(min_val, max_val, 10)
            best_val = None
            best_val_score = -float('inf')

            for test_val in test_values:
                params = {param_name: test_val}
                score = self._evaluate_parameters(data, strategy, params, optimization_metric)
                if score is not None and score > best_val_score:
                    best_val_score = score
                    best_val = test_val

            if best_val is not None:
                best_params[param_name] = best_val
                if param_name == param_names[-1]:  # 最後一個參數
                    best_score = best_val_score

        return {
            'best_parameters': best_params,
            'best_score': best_score,
            'optimization_method': 'Grid Search (Fallback)',
            'total_evaluations': len(param_bounds) * 10,
            'converged': False
        }

    def _evaluate_parameters(self, data, strategy, params, optimization_metric):
        """評估參數組合"""
        try:
            # 確保參數在合理範圍內
            if not self._validate_parameters(params):
                return None

            result = self.engine.backtest_strategy(data, strategy, params, "OPTIMIZATION")

            if optimization_metric == "sharpe_ratio":
                return result.sharpe_ratio
            elif optimization_metric == "total_return":
                return result.total_return
            elif optimization_metric == "max_drawdown":
                return -result.max_drawdown  # 負號因為我們希望最小化回撤
            else:
                return result.total_return

        except Exception as e:
            logger.warning(f"Failed to evaluate parameters {params}: {e}")
            return None

    def _validate_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證參數有效性"""
        # 基本參數驗證
        if 'period' in params:
            if not (5 <= params['period'] <= 100):
                return False
        if 'fast' in params and 'slow' in params:
            if params['fast'] >= params['slow']:
                return False
        if 'short_period' in params and 'long_period' in params:
            if params['short_period'] >= params['long_period']:
                return False

        return True

class GeneticOptimizer:
    """遺傳算法優化器"""

    def __init__(self, engine: VectorBTEngine, config: OptimizationConfig):
        self.engine = engine
        self.config = config
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
        self.elitism_rate = 0.1

    def optimize(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_bounds: Dict[str, Tuple[float, float]],
        optimization_metric: str = "sharpe_ratio",
        n_generations: int = 50
    ) -> Dict[str, Any]:
        """
        遺傳算法優化

        Args:
            data: 價格數據
            strategy: 策略名稱
            param_bounds: 參數邊界
            optimization_metric: 優化目標
            n_generations: 演化代數

        Returns:
            優化結果
        """
        logger.info(f"Starting genetic algorithm optimization for {strategy}")

        param_names = list(param_bounds.keys())
        bounds_array = np.array([param_bounds[name] for name in param_names])

        # 初始化種群
        population_size = self.config.population_size
        population = self._initialize_population(bounds_array, population_size, param_names)
        fitness_scores = self._evaluate_population(data, strategy, population, param_names, optimization_metric)

        best_individual = None
        best_fitness = -float('inf')

        for generation in range(n_generations):
            # 選擇
            mating_pool = self._selection(population, fitness_scores)

            # 交叉
            offspring = self._crossover(mating_pool, param_names)

            # 變異
            offspring = self._mutation(offspring, bounds_array, param_names)

            # 評估後代
            offspring_fitness = self._evaluate_population(data, strategy, offspring, param_names, optimization_metric)

            # 精英主義：保留最優的個體
            combined_population = population + offspring
            combined_fitness = fitness_scores + offspring_fitness
            elite_indices = np.argsort(combined_fitness)[-int(len(population) * (1 - self.elitism_rate)):]

            population = [combined_population[i] for i in elite_indices]
            fitness_scores = [combined_fitness[i] for i in elite_indices]

            # 更新最佳個體
            current_best_idx = np.argmax(fitness_scores)
            if fitness_scores[current_best_idx] > best_fitness:
                best_fitness = fitness_scores[current_best_idx]
                best_individual = population[current_best_idx].copy()

            if generation % 10 == 0:
                logger.info(f"Generation {generation}: best_fitness={best_fitness:.4f}")

            # 檢查收斂
            if self._check_convergence(fitness_scores):
                logger.info(f"Genetic algorithm converged at generation {generation}")
                break

        # 轉換最佳個體回參數字典
        best_params = {param_names[i]: best_individual[i] for i in range(len(param_names))}

        return {
            'best_parameters': best_params,
            'best_score': best_fitness,
            'optimization_method': 'Genetic Algorithm',
            'total_generations': generation + 1,
            'population_size': population_size,
            'converged': True
        }

    def _initialize_population(self, bounds, population_size, param_names):
        """初始化種群"""
        population = []
        for _ in range(population_size):
            individual = []
            for i in range(len(param_names)):
                individual.append(np.random.uniform(bounds[i, 0], bounds[i, 1]))
            population.append(individual)
        return population

    def _evaluate_population(self, data, strategy, population, param_names, optimization_metric):
        """評估種群適應度"""
        fitness_scores = []
        for individual in population:
            params = {param_names[i]: individual[i] for i in range(len(param_names))}

            try:
                result = self.engine.backtest_strategy(data, strategy, params, "OPTIMIZATION")

                if optimization_metric == "sharpe_ratio":
                    score = result.sharpe_ratio
                elif optimization_metric == "total_return":
                    score = result.total_return
                elif optimization_metric == "max_drawdown":
                    score = -result.max_drawdown
                else:
                    score = result.total_return

                # 確保分數是有效的
                score = score if not np.isnan(score) and np.isfinite(score) else -1e6
                fitness_scores.append(score)

            except Exception as e:
                logger.warning(f"Failed to evaluate individual: {e}")
                fitness_scores.append(-1e6)  # 極低的適應度

        return fitness_scores

    def _selection(self, population, fitness_scores):
        """輪盤選擇（錦標賽選）"""
        # 計算選擇概率（適應度比例）
        fitness_array = np.array(fitness_scores)
        # 避免負適應度
        fitness_array = np.maximum(fitness_array, fitness_array.min() + 1e-6)
        probabilities = fitness_array / fitness_array.sum()

        # 錦標賽選
        selected_indices = np.random.choice(
            len(population),
            size=int(len(population) * 0.8),
            replace=True,
            p=probabilities
        )

        return [population[i] for i in selected_indices]

    def _crossover(self, parents, param_names):
        """交叉操作"""
        offspring = []

        for i in range(0, len(parents), 2):
            if i + 1 >= len(parents):
                # 奇數個體直接複製
                offspring.append(parents[i].copy())
                continue

            parent1, parent2 = parents[i], parents[i+1]

            if np.random.random() < self.crossover_rate:
                # 單點交叉
                crossover_point = np.random.randint(1, len(param_names))
                child1 = parent1[:crossover_point] + parent2[crossover_point:]
                child2 = parent2[:crossover_point] + parent1[crossover_point:]
            else:
                # 不交叉，直接複製
                child1 = parent1.copy()
                child2 = parent2.copy()

            offspring.extend([child1, child2])

        return offspring

    def _mutation(self, population, bounds, param_names):
        """變異操作"""
        for individual in population:
            for i in range(len(individual)):
                if np.random.random() < self.mutation_rate:
                    # 高斯變異
                    mutation = np.random.normal(0, 0.1)
                    individual[i] += mutation
                    # 確保在邊界內
                    individual[i] = np.clip(individual[i], bounds[i, 0], bounds[i, 1])
        return population

    def _check_convergence(self, fitness_scores, tolerance=1e-6):
        """檢查收斷"""
        if len(fitness_scores) < 2:
            return False

        # 檢查最近幾代的改進
        recent_fitness = fitness_scores[-min(5, len(fitness_scores))]
        if len(recent_fitness) < 2:
            return False

        return np.std(recent_fitness) < tolerance

class AdvancedOptimizer:
    """高級優化器主類"""

    def __init__(self, engine: VectorBTEngine, config: OptimizationConfig = None):
        self.engine = engine
        self.config = config or OptimizationConfig()

        # 檢測並設置並行核心數
        if self.config.parallel_cores is None:
            self.config.parallel_cores = multiprocessing.cpu_count()

        logger.info(f"Advanced Optimizer initialized with {self.config.parallel_cores} cores")

    def optimize(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_bounds: Dict[str, Tuple[float, float]],
        optimization_metric: str = "sharpe_ratio",
        algorithm: str = None
    ) -> Dict[str, Any]:
        """
        高級優化主接口

        Args:
            data: 價格數據
            strategy: 策略名稱
            param_bounds: 參數邊界
            optimization_metric: 優化目標
            algorithm: 優化算法，如果為None則使用配置中的算法

        Returns:
            優化結果
        """
        algorithm = algorithm or self.config.algorithm

        if algorithm == "bayesian":
            optimizer = BayesianOptimizer(self.engine, self.config)
        elif algorithm == "genetic":
            optimizer = GeneticOptimizer(self.engine, self.config)
        elif algorithm == "differential_evolution":
            return self._differential_evolution_optimization(
                data, strategy, param_bounds, optimization_metric
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        return optimizer.optimize(data, strategy, param_bounds, optimization_metric)

    def _differential_evolution_optimization(
        self, data, strategy, param_bounds, optimization_metric
    ):
        """微分進化優化"""
        param_names = list(param_bounds.keys())
        bounds_array = np.array([param_bounds[name] for name in param_names])

        def objective_function(params):
            params_dict = {param_names[i]: params[i] for i in range(len(param_names))}
            try:
                result = self.engine.backtest_strategy(data, strategy, params_dict, "OPTIMIZATION")

                if optimization_metric == "sharpe_ratio":
                    return -result.sharpe_ratio  # 最小化負Sharpe比率
                elif optimization_metric == "total_return":
                    return -result.total_return  # 最小化負回報
                elif optimization_metric == "max_drawdown":
                    return result.max_drawdown  # 最小化回撤
                else:
                    return -result.total_return

            except Exception:
                return 1e6  # 大的懲罰值

        # 執行微分進化優化
        result = differential_evolution(
            objective_function,
            bounds_array,
            maxiter=self.config.max_iterations,
            popsize=self.config.population_size,
            tol=self.config.convergence_tolerance,
            seed=42
        )

        best_params = {param_names[i]: result.x[i] for i in range(len(param_names))}
        best_score = -result.fun

        return {
            'best_parameters': best_params,
            'best_score': best_score,
            'optimization_method': 'Differential Evolution',
            'iterations': result.nit,
            'converged': result.success,
            'message': result.message
        }

    def optimize_parallel(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_bounds: Dict[str, Tuple[float, float]],
        optimization_metric: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """並行優化"""
        logger.info(f"Starting parallel optimization with {self.config.parallel_cores} cores")

        # 將參數空間分割
        param_names = list(param_bounds.keys())
        n_params = len(param_names)

        # 創建並行任務
        def parallel_objective(params_subset):
            optimizer = AdvancedOptimizer(self.engine, self.config)
            subset_bounds = {param_names[i]: params_subset[i] for i in range(n_params)}
            return optimizer.optimize(data, strategy, subset_bounds, optimization_metric, "bayesian")

        # 分割參數空間用於並行處理
        chunk_size = len(param_names) // self.config.parallel_cores
        param_chunks = []

        for i in range(self.config.parallel_cores):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size
            chunk_bounds = {}

            for j in range(start_idx, min(end_idx, n_params)):
                param_name = param_names[j]
                min_val, max_val = param_bounds[param_name]

                # 為每個核心分配一個參數的範圍
                range_size = (max_val - min_val) / self.config.parallel_cores
                chunk_min = min_val + i * range_size
                chunk_max = min_val + (i + 1) * range_size
                chunk_bounds[param_name] = (chunk_min, chunk_max)

            param_chunks.append(chunk_bounds)

        # 並行執行
        with ProcessPoolExecutor(max_workers=self.config.parallel_cores) as executor:
            futures = [executor.submit(parallel_objective, chunk) for chunk in param_chunks]
            results = [future.result() for future in as_completed(futures)]

        # 分析並行結果
        best_result = max(results, key=lambda x: x['best_score'])

        return {
            'parallel_results': results,
            'overall_best': best_result,
            'cores_used': self.config.parallel_cores,
            'optimization_method': 'Parallel VectorBT'
        }