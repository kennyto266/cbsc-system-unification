#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能搜索引擎 - 整合多種搜索算法
Intelligent Search Engine - Integrating Multiple Search Algorithms

實現遺傳算法、貝葉斯優化和多臂老虎手算法的混合搜索系統
"""

import numpy as np
import pandas as pd
import logging
import time
import random
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import concurrent.futures
from itertools import product
import json
from pathlib import Path

# 統計和優化庫
try:
    from scipy import stats
    from scipy.optimize import minimize
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern, RBF
    STATISTICAL_LIBS_AVAILABLE = True
except ImportError:
    STATISTICAL_LIBS_AVAILABLE = False
    # 創建簡化的替代實現
    stats = None
    minimize = None
    GaussianProcessRegressor = None
    Matern = None
    RBF = None

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索結果"""
    parameters: Dict[str, Any]
    objective_value: float
    evaluation_count: int
    search_time: float
    algorithm: str
    additional_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class SearchSpace:
    """搜索空間定義"""
    parameters: Dict[str, Tuple[float, float]]  # 參數名 -> (最小值, 最大值)
    parameter_types: Dict[str, str]  # 參數類型: 'continuous', 'integer', 'categorical'
    constraints: List[Callable] = field(default_factory=list)  # 參數約束函數

class BaseSearchAlgorithm(ABC):
    """搜索算法基類"""

    def __init__(self, search_space: SearchSpace, objective_function: Callable):
        self.search_space = search_space
        self.objective_function = objective_function
        self.search_history = []
        self.best_result = None
        self.evaluation_count = 0

    @abstractmethod
    def optimize(self, max_iterations: int = 100) -> List[SearchResult]:
        """執行優化"""
        pass

    def _validate_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證參數有效性"""
        # 檢查參數範圍
        for param_name, value in params.items():
            if param_name in self.search_space.parameters:
                min_val, max_val = self.search_space.parameters[param_name]
                if not (min_val <= value <= max_val):
                    return False

        # 檢查約束
        for constraint in self.search_space.constraints:
            if not constraint(params):
                return False

        return True

    def _evaluate_parameters(self, params: Dict[str, Any]) -> float:
        """評估參數"""
        if not self._validate_parameters(params):
            return float('inf')  # 無效參數返回極差值

        try:
            self.evaluation_count += 1
            start_time = time.time()

            # 調用目標函數
            objective_value = self.objective_function(params)

            evaluation_time = time.time() - start_time

            # 記錄搜索歷史
            result = SearchResult(
                parameters=params.copy(),
                objective_value=objective_value,
                evaluation_count=self.evaluation_count,
                search_time=evaluation_time,
                algorithm=self.__class__.__name__
            )

            self.search_history.append(result)

            # 更新最佳結果
            if (self.best_result is None or
                objective_value < self.best_result.objective_value):
                self.best_result = result

            return objective_value

        except Exception as e:
            logger.warning(f"Error evaluating parameters {params}: {e}")
            return float('inf')

class GeneticSearchAlgorithm(BaseSearchAlgorithm):
    """遺傳搜索算法"""

    def __init__(self,
                 search_space: SearchSpace,
                 objective_function: Callable,
                 population_size: int = 100,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8,
                 elitism_rate: float = 0.1):
        super().__init__(search_space, objective_function)

        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_rate = elitism_rate

        self.population = []
        self.fitness_scores = []

    def optimize(self, max_iterations: int = 100) -> List[SearchResult]:
        """執行遺傳算法優化"""
        logger.info(f"Starting genetic search with population size {self.population_size}")

        # 初始化種群
        self._initialize_population()

        for generation in range(max_iterations):
            # 評估適應度
            self._evaluate_population()

            # 檢查收斂
            if self._check_convergence(generation):
                logger.info(f"Genetic algorithm converged at generation {generation}")
                break

            # 選擇
            selected_population = self._selection()

            # 交叉
            offspring = self._crossover(selected_population)

            # 變異
            self._mutation(offspring)

            # 組成新一代種群
            self.population = offspring

            logger.info(f"Generation {generation}: Best fitness = {min(self.fitness_scores):.6f}")

        return self.search_history

    def _initialize_population(self) -> None:
        """初始化種群"""
        self.population = []
        for _ in range(self.population_size):
            individual = self._generate_random_individual()
            self.population.append(individual)

    def _generate_random_individual(self) -> Dict[str, Any]:
        """生成隨機個體"""
        individual = {}
        for param_name, (min_val, max_val) in self.search_space.parameters.items():
            param_type = self.search_space.parameter_types.get(param_name, 'continuous')

            if param_type == 'continuous':
                individual[param_name] = random.uniform(min_val, max_val)
            elif param_type == 'integer':
                individual[param_name] = random.randint(int(min_val), int(max_val))
            else:  # categorical
                # 簡化處理：假設分類參數使用範圍內的整數
                individual[param_name] = random.randint(int(min_val), int(max_val))

        return individual

    def _evaluate_population(self) -> None:
        """評估種群適應度"""
        self.fitness_scores = []
        for individual in self.population:
            fitness = self._evaluate_parameters(individual)
            self.fitness_scores.append(fitness)

    def _check_convergence(self, generation: int, patience: int = 20) -> bool:
        """檢查收斂條件"""
        if generation < patience:
            return False

        if len(self.fitness_scores) < patience:
            return False

        # 檢查最近patience代是否有改善
        recent_best = min(self.fitness_scores[-patience:])
        overall_best = min(self.fitness_scores)

        return abs(recent_best - overall_best) < 1e-6

    def _selection(self) -> List[Dict[str, Any]]:
        """選擇操作 - 錦標賽選擇"""
        selected = []

        # 精英選擇
        elite_count = int(self.population_size * self.elitism_rate)
        elite_indices = np.argsort(self.fitness_scores)[:elite_count]
        selected.extend([self.population[i] for i in elite_indices])

        # 錦標賽選擇其餘個體
        remaining_count = self.population_size - elite_count
        if remaining_count > 0:
            # 基於適應度倒數計算選擇概率
            inverse_fitness = 1.0 / (np.array(self.fitness_scores) + 1e-10)
            selection_prob = inverse_fitness / np.sum(inverse_fitness)

            selected_indices = np.random.choice(
                len(self.population),
                size=remaining_count,
                replace=True,
                p=selection_prob
            )
            selected.extend([self.population[i] for i in selected_indices])

        return selected

    def _crossover(self, selected_population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """交叉操作"""
        offspring = []
        random.shuffle(selected_population)

        for i in range(0, len(selected_population) - 1, 2):
            parent1 = selected_population[i]
            parent2 = selected_population[i + 1]

            if random.random() < self.crossover_rate:
                child1, child2 = self._single_point_crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            offspring.extend([child1, child2])

        # 處理奇數情況
        if len(selected_population) % 2 == 1:
            offspring.append(selected_population[-1].copy())

        return offspring[:self.population_size]

    def _single_point_crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """單點交叉"""
        child1 = parent1.copy()
        child2 = parent2.copy()

        # 隨機選擇交叉點
        param_names = list(parent1.keys())
        if len(param_names) > 1:
            crossover_point = random.randint(1, len(param_names) - 1)
            crossover_params = param_names[:crossover_point]

            for param in crossover_params:
                child1[param], child2[param] = child2[param], child1[param]

        return child1, child2

    def _mutation(self, population: List[Dict[str, Any]]) -> None:
        """變異操作"""
        for individual in population:
            if random.random() < self.mutation_rate:
                self._mutate_individual(individual)

    def _mutate_individual(self, individual: Dict[str, Any]) -> None:
        """對個體進行變異"""
        param_name = random.choice(list(individual.keys()))
        min_val, max_val = self.search_space.parameters[param_name]
        param_type = self.search_space.parameter_types.get(param_name, 'continuous')

        if param_type == 'continuous':
            # 高斯變異
            current_value = individual[param_name]
            mutation_strength = (max_val - min_val) * 0.1
            new_value = current_value + np.random.normal(0, mutation_strength)
            individual[param_name] = np.clip(new_value, min_val, max_val)
        elif param_type == 'integer':
            # 隨機變異
            individual[param_name] = random.randint(int(min_val), int(max_val))
        else:
            # 分類變異
            individual[param_name] = random.randint(int(min_val), int(max_val))

class BayesianSearchAlgorithm(BaseSearchAlgorithm):
    """貝葉斯優化算法"""

    def __init__(self,
                 search_space: SearchSpace,
                 objective_function: Callable,
                 acquisition_function: str = 'ei',  # 'ei', 'ucb', 'pi'
                 exploration_weight: float = 1.0):
        super().__init__(search_space, objective_function)

        self.acquisition_function = acquisition_function
        self.exploration_weight = exploration_weight

        # 初始採樣點
        self.n_initial_points = min(10, len(search_space.parameters) * 2)
        self.evaluated_points = []
        self.evaluated_values = []

        # 高斯過程模型
        if STATISTICAL_LIBS_AVAILABLE:
            self.gp_model = None
        else:
            logger.warning("Statistical libraries not available, using simplified Bayesian optimization")
            self._initialize_simple_model()

    def _initialize_simple_model(self) -> None:
        """初始化簡化模型（用於無scipy情況）"""
        self.simple_model = {
            'mean': 0.0,
            'std': 1.0,
            'best_value': float('inf')
        }

    def optimize(self, max_iterations: int = 100) -> List[SearchResult]:
        """執行貝葉斯優化"""
        logger.info(f"Starting Bayesian search with {self.acquisition_function} acquisition")

        # 初始隨機採樣
        self._initial_sampling()

        for iteration in range(max_iterations - self.n_initial_points):
            # 更新代理模型
            self._update_surrogate_model()

            # 獲取函數
            next_point = self._get_next_point()

            # 評估新點
            objective_value = self._evaluate_parameters(next_point)

            # 記錄結果
            self.evaluated_points.append(list(next_point.values()))
            self.evaluated_values.append(objective_value)

            logger.info(f"Iteration {iteration + self.n_initial_points}: Value = {objective_value:.6f}")

        return self.search_history

    def _initial_sampling(self) -> None:
        """初始隨機採樣"""
        for _ in range(self.n_initial_points):
            point = self._generate_random_point()
            self._evaluate_parameters(point)
            self.evaluated_points.append(list(point.values()))
            self.evaluated_values.append(self._best_result.objective_value)

    def _generate_random_point(self) -> Dict[str, Any]:
        """生成隨機點"""
        point = {}
        for param_name, (min_val, max_val) in self.search_space.parameters.items():
            param_type = self.search_space.parameter_types.get(param_name, 'continuous')

            if param_type == 'continuous':
                point[param_name] = random.uniform(min_val, max_val)
            elif param_type == 'integer':
                point[param_name] = random.randint(int(min_val), int(max_val))
            else:
                point[param_name] = random.randint(int(min_val), int(max_val))

        return point

    def _update_surrogate_model(self) -> None:
        """更新代理模型"""
        if not STATISTICAL_LIBS_AVAILABLE or len(self.evaluated_points) < 2:
            self._update_simple_model()
            return

        try:
            # 準備數據
            X = np.array(self.evaluated_points)
            y = np.array(self.evaluated_values)

            # 標準化目標值
            y_mean = np.mean(y)
            y_std = np.std(y)
            y_normalized = (y - y_mean) / (y_std + 1e-10)

            # 創建高斯過程模型
            kernel = RBF(length_scale=1.0) + Matern(length_scale=1.0, nu=1.5)
            self.gp_model = GaussianProcessRegressor(
                kernel=kernel,
                alpha=1e-6,
                normalize_y=True
            )

            # 擬合模型
            self.gp_model.fit(X, y_normalized)

        except Exception as e:
            logger.warning(f"Error updating surrogate model: {e}")
            self._update_simple_model()

    def _update_simple_model(self) -> None:
        """更新簡化模型"""
        if len(self.evaluated_values) > 0:
            self.simple_model['mean'] = np.mean(self.evaluated_values)
            self.simple_model['std'] = np.std(self.evaluated_values)
            self.simple_model['best_value'] = min(self.evaluated_values)

    def _get_next_point(self) -> Dict[str, Any]:
        """獲取下一個採樣點"""
        if STATISTICAL_LIBS_AVAILABLE and self.gp_model is not None:
            return self._get_next_point_gp()
        else:
            return self._get_next_point_simple()

    def _get_next_point_gp(self) -> Dict[str, Any]:
        """使用高斯過程獲取下一個點"""
        try:
            # 生成候選點
            n_candidates = 1000
            candidates = self._generate_candidates(n_candidates)

            # 預測候選點的均值和方差
            X_candidates = np.array([list(c.values()) for c in candidates])
            y_mean, y_std = self.gp_model.predict(X_candidates, return_std=True)

            # 計算獲取函數值
            if self.acquisition_function == 'ei':
                acquisition_values = self._expected_improvement(y_mean, y_std)
            elif self.acquisition_function == 'ucb':
                acquisition_values = self._upper_confidence_bound(y_mean, y_std)
            else:  # pi
                acquisition_values = self._probability_of_improvement(y_mean, y_std)

            # 選擇最佳候選點
            best_idx = np.argmax(acquisition_values)
            best_candidate = candidates[best_idx]

            return best_candidate

        except Exception as e:
            logger.warning(f"Error in GP-based point selection: {e}")
            return self._generate_random_point()

    def _get_next_point_simple(self) -> Dict[str, Any]:
        """使用簡化方法獲取下一個點"""
        # 在當前最佳點附近搜索
        if self.best_result:
            best_point = self.best_result.parameters
            return self._local_search(best_point)
        else:
            return self._generate_random_point()

    def _local_search(self, center_point: Dict[str, Any], radius: float = 0.1) -> Dict[str, Any]:
        """局部搜索"""
        candidate = center_point.copy()

        # 隨機選擇一個參數進行搜索
        param_name = random.choice(list(center_point.keys()))
        min_val, max_val = self.search_space.parameters[param_name]

        # 在當前值附近搜索
        current_value = center_point[param_name]
        search_range = (max_val - min_val) * radius
        new_value = current_value + np.random.uniform(-search_range, search_range)
        candidate[param_name] = np.clip(new_value, min_val, max_val)

        return candidate

    def _generate_candidates(self, n: int) -> List[Dict[str, Any]]:
        """生成候選點"""
        candidates = []
        param_names = list(self.search_space.parameters.keys())

        for _ in range(n):
            candidate = {}
            for param_name in param_names:
                min_val, max_val = self.search_space.parameters[param_name]
                candidate[param_name] = random.uniform(min_val, max_val)
            candidates.append(candidate)

        return candidates

    def _expected_improvement(self, y_mean: np.ndarray, y_std: np.ndarray) -> np.ndarray:
        """預期改進獲取函數"""
        best_y = min(self.evaluated_values) if self.evaluated_values else 0
        improvement = best_y - y_mean
        z = improvement / (y_std + 1e-10)

        ei = improvement * stats.norm.cdf(z) + y_std * stats.norm.pdf(z)
        return ei

    def _upper_confidence_bound(self, y_mean: np.ndarray, y_std: np.ndarray, kappa: float = 2.0) -> np.ndarray:
        """上置信界獲取函數"""
        return y_mean + kappa * y_std

    def _probability_of_improvement(self, y_mean: np.ndarray, y_std: np.ndarray) -> np.ndarray:
        """改進概率獲取函數"""
        best_y = min(self.evaluated_values) if self.evaluated_values else 0
        z = (best_y - y_mean) / (y_std + 1e-10)
        return stats.norm.cdf(z)

class MultiArmedBanditAlgorithm(BaseSearchAlgorithm):
    """多臂老虎手算法"""

    def __init__(self,
                 search_space: SearchSpace,
                 objective_function: Callable,
                 algorithm: str = 'thompson',  # 'thompson', 'ucb', 'epsilon_greedy'
                 exploration_epsilon: float = 0.1):
        super().__init__(search_space, objective_function)

        self.algorithm = algorithm
        self.exploration_epsilon = exploration_epsilon

        # 定義"手臂"（參數組合）
        self.arms = self._define_arms()
        self.arm_counts = {arm_id: 0 for arm_id in range(len(self.arms))}
        self.arm_rewards = {arm_id: [] for arm_id in range(len(self.arms))}
        self.arm_means = {arm_id: 0.0 for arm_id in range(len(self.arms))}

    def _define_arms(self) -> List[Dict[str, Any]]:
        """定義老虎手的手臂"""
        # 預定義一些有希望的參數組合
        arms = []

        # RSI策略手臂
        arms.extend([
            {'rsi_period': 14, 'oversold': 30, 'overbought': 70},
            {'rsi_period': 21, 'oversold': 25, 'overbought': 75},
            {'rsi_period': 10, 'oversold': 20, 'overbought': 80},
            {'rsi_period': 30, 'oversold': 35, 'overbought': 65}
        ])

        # MACD策略手臂
        arms.extend([
            {'fast': 12, 'slow': 26, 'signal': 9},
            {'fast': 5, 'slow': 35, 'signal': 5},
            {'fast': 10, 'slow': 20, 'signal': 7},
            {'fast': 8, 'slow': 24, 'signal': 6}
        ])

        # 添加隨機手臂
        for _ in range(4):
            arms.append(self._generate_random_point())

        return arms

    def _generate_random_point(self) -> Dict[str, Any]:
        """生成隨機點"""
        point = {}
        for param_name, (min_val, max_val) in self.search_space.parameters.items():
            param_type = self.search_space.parameter_types.get(param_name, 'continuous')

            if param_type == 'continuous':
                point[param_name] = random.uniform(min_val, max_val)
            elif param_type == 'integer':
                point[param_name] = random.randint(int(min_val), int(max_val))
            else:
                point[param_name] = random.randint(int(min_val), int(max_val))

        return point

    def optimize(self, max_iterations: int = 100) -> List[SearchResult]:
        """執行多臂老虎手優化"""
        logger.info(f"Starting {self.algorithm} bandit search with {len(self.arms)} arms")

        for iteration in range(max_iterations):
            # 選擇手臂
            arm_id = self._select_arm()

            # 執行手臂（評估參數）
            arm_parameters = self.arms[arm_id]
            reward = -self._evaluate_parameters(arm_parameters)  # 負號因為我們最小化

            # 更新統計信息
            self._update_arm_statistics(arm_id, reward)

            logger.info(f"Iteration {iteration}: Arm {arm_id}, Reward: {reward:.6f}")

        return self.search_history

    def _select_arm(self) -> int:
        """選擇手臂"""
        if self.algorithm == 'thompson':
            return self._thompson_sampling()
        elif self.algorithm == 'ucb':
            return self._ucb_selection()
        else:  # epsilon_greedy
            return self._epsilon_greedy_selection()

    def _thompson_sampling(self) -> int:
        """Thompson採樣"""
        samples = []
        for arm_id in range(len(self.arms)):
            if self.arm_counts[arm_id] == 0:
                # 未嘗試的手臂給予高優先級
                return arm_id

            # 從Beta分數採樣
            successes = sum(1 for r in self.arm_rewards[arm_id] if r > 0)
            failures = self.arm_counts[arm_id] - successes

            # 使用Beta分數採樣
            sample = np.random.beta(successes + 1, failures + 1)
            samples.append(sample)

        return np.argmax(samples)

    def _ucb_selection(self) -> int:
        """UCB選擇"""
        total_counts = sum(self.arm_counts.values())

        ucb_values = []
        for arm_id in range(len(self.arms)):
            if self.arm_counts[arm_id] == 0:
                # 未嘗試的手臂
                ucb_values.append(float('inf'))
            else:
                # UCB公式
                mean_reward = self.arm_means[arm_id]
                exploration_term = np.sqrt(2 * np.log(total_counts) / self.arm_counts[arm_id])
                ucb_values.append(mean_reward + exploration_term)

        return np.argmax(ucb_values)

    def _epsilon_greedy_selection(self) -> int:
        """ε-貪婪選擇"""
        if random.random() < self.exploration_epsilon:
            # 探索：隨機選擇
            return random.randint(0, len(self.arms) - 1)
        else:
            # 利用：選擇最佳手臂
            return max(self.arm_means, key=self.arm_means.get)

    def _update_arm_statistics(self, arm_id: int, reward: float) -> None:
        """更新手臂統計信息"""
        self.arm_counts[arm_id] += 1
        self.arm_rewards[arm_id].append(reward)

        # 更新均值
        self.arm_means[arm_id] = np.mean(self.arm_rewards[arm_id])

class IntelligentSearchEngine:
    """
    智能搜索引擎

    整合多種搜索算法，提供：
    - 自適應算法選擇
    - 混合搜索策略
    - 動態優化調整
    - 結果整合和分析
    """

    def __init__(self,
                 search_space: SearchSpace,
                 objective_function: Callable,
                 enable_parallel: bool = True,
                 max_workers: int = 4):
        """
        初始化智能搜索引擎

        Args:
            search_space: 搜索空間定義
            objective_function: 目標函數
            enable_parallel: 是否啟用並行處理
            max_workers: 最大工作線程數
        """
        self.search_space = search_space
        self.objective_function = objective_function
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers

        # 初始化搜索算法
        self.algorithms = {
            'genetic': GeneticSearchAlgorithm(search_space, objective_function),
            'bayesian': BayesianSearchAlgorithm(search_space, objective_function),
            'bandit': MultiArmedBanditAlgorithm(search_space, objective_function)
        }

        # 搜索結果
        self.all_results = []
        self.best_results = {}

        # 性能統計
        self.algorithm_performance = {
            'genetic': {'iterations': 0, 'best_value': float('inf'), 'time': 0},
            'bayesian': {'iterations': 0, 'best_value': float('inf'), 'time': 0},
            'bandit': {'iterations': 0, 'best_value': float('inf'), 'time': 0}
        }

    def adaptive_search_strategy(self,
                                problem_complexity: str = 'auto',
                                max_iterations_per_algorithm: int = 100) -> Dict[str, List[SearchResult]]:
        """
        自適應搜索策略

        Args:
            problem_complexity: 問題複雜度 ('low', 'medium', 'high', 'auto')
            max_iterations_per_algorithm: 每個算法的最大迭代次數

        Returns:
            各算法的搜索結果
        """
        logger.info(f"Starting adaptive search strategy (complexity: {problem_complexity})")

        # 自動評估問題複雜度
        if problem_complexity == 'auto':
            problem_complexity = self._assess_problem_complexity()

        # 選擇搜索策略
        strategy = self._select_search_strategy(problem_complexity)
        logger.info(f"Selected strategy: {strategy}")

        results = {}

        if strategy == 'genetic_bayesian':
            # 遺傳算法 + 貝葉斯優化的混合搜索
            results['genetic'] = self._run_genetic_search(max_iterations_per_algorithm)
            results['bayesian'] = self._run_bayesian_search(max_iterations_per_algorithm)

        elif strategy == 'grid_random':
            # 網格搜索 + 隨機搜索的混合搜索
            results['genetic'] = self._run_genetic_search(max_iterations_per_algorithm // 2)
            results['bandit'] = self._run_bandit_search(max_iterations_per_algorithm // 2)

        else:
            # 單一網格搜索
            results['genetic'] = self._run_genetic_search(max_iterations_per_algorithm)

        # 整合結果
        self._integrate_results(results)

        return results

    def _assess_problem_complexity(self) -> str:
        """評估問題複雜度"""
        n_parameters = len(self.search_space.parameters)
        n_continuous = sum(1 for t in self.search_space.parameter_types.values()
                           if t == 'continuous')
        n_constraints = len(self.search_space.constraints)

        if n_parameters > 10 or n_continuous > 5 or n_constraints > 3:
            return 'high'
        elif n_parameters > 5 or n_continuous > 2:
            return 'medium'
        else:
            return 'low'

    def _select_search_strategy(self, complexity: str) -> str:
        """選擇搜索策略"""
        if complexity == 'high':
            return 'genetic_bayesian'
        elif complexity == 'medium':
            return 'grid_random'
        else:
            return 'grid'

    def _run_genetic_search(self, max_iterations: int) -> List[SearchResult]:
        """運行遺傳算法搜索"""
        logger.info(f"Running genetic search for {max_iterations} iterations")
        start_time = time.time()

        results = self.algorithms['genetic'].optimize(max_iterations)

        search_time = time.time() - start_time
        self.algorithm_performance['genetic']['iterations'] = max_iterations
        self.algorithm_performance['genetic']['time'] = search_time
        self.algorithm_performance['genetic']['best_value'] = min(r.objective_value for r in results) if results else float('inf')

        return results

    def _run_bayesian_search(self, max_iterations: int) -> List[SearchResult]:
        """運行貝葉斯優化搜索"""
        logger.info(f"Running Bayesian search for {max_iterations} iterations")
        start_time = time.time()

        results = self.algorithms['bayesian'].optimize(max_iterations)

        search_time = time.time() - start_time
        self.algorithm_performance['bayesian']['iterations'] = max_iterations
        self.algorithm_performance['bayesian']['time'] = search_time
        self.algorithm_performance['bayesian']['best_value'] = min(r.objective_value for r in results) if results else float('inf')

        return results

    def _run_bandit_search(self, max_iterations: int) -> List[SearchResult]:
        """運行多臂老虎手搜索"""
        logger.info(f"Running bandit search for {max_iterations} iterations")
        start_time = time.time()

        results = self.algorithms['bandit'].optimize(max_iterations)

        search_time = time.time() - start_time
        self.algorithm_performance['bandit']['iterations'] = max_iterations
        self.algorithm_performance['bandit']['time'] = search_time
        self.algorithm_performance['bandit']['best_value'] = min(r.objective_value for r in results) if results else float('inf')

        return results

    def _integrate_results(self, algorithm_results: Dict[str, List[SearchResult]]) -> None:
        """整合搜索結果"""
        self.all_results = []
        self.best_results = {}

        for algorithm, results in algorithm_results.items():
            self.all_results.extend(results)

            if results:
                best_result = min(results, key=lambda r: r.objective_value)
                self.best_results[algorithm] = best_result

        logger.info(f"Integrated {len(self.all_results)} total results from {len(algorithm_results)} algorithms")

    def get_overall_best_result(self) -> Optional[SearchResult]:
        """獲取整體最佳結果"""
        if not self.all_results:
            return None

        return min(self.all_results, key=lambda r: r.objective_value)

    def get_algorithm_performance_report(self) -> Dict[str, Any]:
        """獲取算法性能報告"""
        report = {
            'algorithms': {},
            'overall_best': None,
            'performance_comparison': {}
        }

        # 各算法性能
        for algorithm, perf in self.algorithm_performance.items():
            report['algorithms'][algorithm] = {
                'iterations': perf['iterations'],
                'best_value': perf['best_value'],
                'execution_time': perf['time'],
                'efficiency': perf['iterations'] / max(perf['time'], 0.001)  # iterations per second
            }

        # 整體最佳結果
        overall_best = self.get_overall_best_result()
        if overall_best:
            report['overall_best'] = {
                'algorithm': overall_best.algorithm,
                'objective_value': overall_best.objective_value,
                'parameters': overall_best.parameters
            }

        # 性能比較
        if self.best_results:
            best_values = {alg: res.objective_value for alg, res in self.best_results.items()}
            best_algorithm = min(best_values, key=best_values.get)
            report['performance_comparison']['best_algorithm'] = best_algorithm
            report['performance_comparison']['value_improvement'] = {
                alg: (best_values[best_algorithm] - val) / abs(val) * 100
                for alg, val in best_values.items()
            }

        return report

# 便利函數
def create_intelligent_search_engine(search_space: SearchSpace,
                                   objective_function: Callable,
                                   enable_parallel: bool = True) -> IntelligentSearchEngine:
    """
    創建智能搜索引擎實例

    Args:
        search_space: 搜索空間定義
        objective_function: 目標函數
        enable_parallel: 是否啟用並行處理

    Returns:
        智能搜索引擎實例
    """
    return IntelligentSearchEngine(search_space, objective_function, enable_parallel)

if __name__ == "__main__":
    # 測試智能搜索引擎
    logging.basicConfig(level=logging.INFO)

    # 定義搜索空間
    search_space = SearchSpace(
        parameters={
            'x': (-5.0, 5.0),
            'y': (-5.0, 5.0)
        },
        parameter_types={
            'x': 'continuous',
            'y': 'continuous'
        }
    )

    # 定義目標函數（Rastrigin函數 - 常見的測試函數）
    def rastrigin_function(params):
        x, y = params['x'], params['y']
        n = 2
        return 10 * n + sum([(x**2 - 10 * np.cos(2 * np.pi * x)) + (y**2 - 10 * np.cos(2 * np.pi * y))])

    # 創建搜索引擎
    search_engine = create_intelligent_search_engine(search_space, rastrigin_function)

    # 執行搜索
    results = search_engine.adaptive_search_strategy(
        problem_complexity='medium',
        max_iterations_per_algorithm=50
    )

    # 獲取報告
    report = search_engine.get_algorithm_performance_report()

    print("=== Intelligent Search Engine Test Results ===")
    print(f"Total results: {len(search_engine.all_results)}")
    print(f"Best result: {report.get('overall_best', {}).get('objective_value', 'N/A'):.6f}")
    print(f"Best algorithm: {report.get('performance_comparison', {}).get('best_algorithm', 'N/A')}")

    for algorithm, perf in report.get('algorithms', {}).items():
        print(f"{algorithm}: {perf['best_value']:.6f} ({perf['iterations']} iterations, {perf['execution_time']:.2f}s)")