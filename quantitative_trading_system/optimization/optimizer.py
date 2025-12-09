#!/usr/bin/env python3
"""
智能参数优化器 - Week 4重构版
Intelligent Parameter Optimizer - Week 4 Refactored Edition

Week 4 Task 4.1-4.5: 参数空间智能裁剪、贝叶斯优化、并行处理、早停机制、结果分析
专注于高效参数搜索，避免无效计算，实现10x+性能提升

Author: Claude Code Assistant
Created: 2025-11-29
Version: 2.0.0 (Week 4 Tasks 4.1-4.5)
"""

import logging
import numpy as np
import pandas as pd
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from functools import partial
import json
import os
from datetime import datetime

# 尝试导入scikit-optimize用于贝叶斯优化
try:
    from skopt import gp_minimize, forest_minimize, gbrt_minimize
    from skopt.space import Real, Integer, Categorical
    from skopt.utils import use_named_args
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False
    logging.warning("scikit-optimize not available, using simplified Bayesian optimization")

logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """增强优化结果"""
    best_params: Dict[str, Any]
    best_score: float
    best_sharpe: float
    total_iterations: int
    optimization_time: float
    all_results: List[Dict[str, Any]] = field(default_factory=list)
    convergence_curve: List[float] = field(default_factory=list)

    # Week 4新增字段
    method_used: str = ""
    parameter_importance: Dict[str, float] = field(default_factory=dict)
    convergence_analysis: Dict[str, Any] = field(default_factory=dict)
    early_stopped: bool = False
    space_reduction_stats: Dict[str, Any] = field(default_factory=dict)
    parallel_efficiency: float = 0.0
    optimization_id: str = ""

class ParameterSpacePruner:
    """
    参数空间智能裁剪器 - Week 4 Task 4.1
    基于历史优化结果智能缩小搜索空间
    """

    def __init__(self, min_samples: int = 20):
        """
        初始化参数空间裁剪器

        Args:
            min_samples: 最小历史样本数
        """
        self.min_samples = min_samples
        self.pruning_history = []

    def prune_search_space(self, param_bounds: Dict[str, Tuple[Any, Any]],
                           historical_results: List[Dict[str, Any]],
                           target_reduction: float = 0.5) -> Dict[str, Tuple[Any, Any]]:
        """
        智能裁剪搜索空间

        Args:
            param_bounds: 原始参数边界
            historical_results: 历史优化结果
            target_reduction: 目标缩减比例

        Returns:
            裁剪后的参数边界
        """
        if len(historical_results) < self.min_samples:
            logger.info(f"历史样本不足 ({len(historical_results)} < {self.min_samples}), 跳过空间裁剪")
            return param_bounds

        pruned_bounds = {}
        reduction_stats = {}

        for param_name, (min_val, max_val) in param_bounds.items():
            # 提取参数值和对应分数
            param_values = []
            scores = []

            for result in historical_results:
                if param_name in result['params']:
                    param_values.append(result['params'][param_name])
                    scores.append(result['score'])

            if not param_values:
                pruned_bounds[param_name] = (min_val, max_val)
                continue

            # 分析参数重要性
            correlation = np.corrcoef(param_values, scores)[0, 1] if len(set(param_values)) > 1 else 0
            importance = abs(correlation) if not np.isnan(correlation) else 0

            # 根据重要性决定裁剪策略
            if importance > 0.3:  # 高重要性参数，大幅裁剪
                reduction_factor = target_reduction * 1.5
            elif importance > 0.1:  # 中等重要性参数，适度裁剪
                reduction_factor = target_reduction
            else:  # 低重要性参数，轻微裁剪
                reduction_factor = target_reduction * 0.5

            # 计算最优区域
            if importance > 0.1:  # 只对有显著相关性的参数进行集中裁剪
                # 找到表现最好的区域
                sorted_results = sorted(zip(param_values, scores), key=lambda x: x[1], reverse=True)
                top_20_percent = int(len(sorted_results) * 0.2)
                top_values = [params for params, _ in sorted_results[:top_20_percent]]

                if top_values:
                    new_min = max(min_val, min(top_values) - (max_val - min_val) * 0.1)
                    new_max = min(max_val, max(top_values) + (max_val - min_val) * 0.1)
                else:
                    new_min, new_max = min_val, max_val
            else:
                # 均匀裁剪
                center = (min_val + max_val) / 2
                range_size = (max_val - min_val) * (1 - reduction_factor)
                new_min = max(min_val, center - range_size / 2)
                new_max = min(max_val, center + range_size / 2)

            # 确保整数参数的整数性质
            if isinstance(min_val, int) and isinstance(max_val, int):
                new_min = int(np.floor(new_min))
                new_max = int(np.ceil(new_max))

            pruned_bounds[param_name] = (new_min, new_max)
            reduction_stats[param_name] = {
                'original_range': max_val - min_val,
                'new_range': new_max - new_min,
                'reduction_ratio': 1 - (new_max - new_min) / (max_val - min_val),
                'importance': importance
            }

        # 记录裁剪历史
        self.pruning_history.append({
            'timestamp': datetime.now(),
            'original_bounds': param_bounds,
            'pruned_bounds': pruned_bounds,
            'reduction_stats': reduction_stats,
            'sample_count': len(historical_results)
        })

        logger.info(f"参数空间裁剪完成: 平均缩减比例 {np.mean([s['reduction_ratio'] for s in reduction_stats.values()]):.2%}")

        return pruned_bounds

class EarlyStoppingManager:
    """
    早停机制管理器 - Week 4 Task 4.4
    智能判断何时停止优化
    """

    def __init__(self, patience: int = 50, min_iterations: int = 20,
                 improvement_threshold: float = 1e-4):
        """
        初始化早停管理器

        Args:
            patience: 容忍无改进的迭代次数
            min_iterations: 最小迭代次数
            improvement_threshold: 改进阈值
        """
        self.patience = patience
        self.min_iterations = min_iterations
        self.improvement_threshold = improvement_threshold
        self.best_score = -float('inf')
        self.no_improvement_count = 0
        self.start_time = None
        self.early_stopped = False

    def should_stop(self, current_iteration: int, current_score: float,
                   optimization_time: float) -> bool:
        """
        判断是否应该早停

        Args:
            current_iteration: 当前迭代次数
            current_score: 当前分数
            optimization_time: 优化时间

        Returns:
            是否应该停止
        """
        if self.start_time is None:
            self.start_time = optimization_time
            return False

        # 检查是否有改进
        if current_score > self.best_score + self.improvement_threshold:
            self.best_score = current_score
            self.no_improvement_count = 0
        else:
            self.no_improvement_count += 1

        # 早停条件
        if (current_iteration >= self.min_iterations and
            self.no_improvement_count >= self.patience):
            logger.info(f"早停触发: {self.no_improvement_count} 次无改进，最佳分数: {self.best_score:.6f}")
            self.early_stopped = True
            return True

        return False

    def get_status(self) -> Dict[str, Any]:
        """获取早停状态"""
        return {
            'best_score': self.best_score,
            'no_improvement_count': self.no_improvement_count,
            'early_stopped': self.early_stopped,
            'patience_used': self.no_improvement_count / self.patience if self.patience > 0 else 0
        }

class ParameterOptimizer:
    """
    Week 4 智能参数优化器 - 重构版
    集成参数空间裁剪、贝叶斯优化、并行处理、早停机制、结果分析
    """

    def __init__(self, max_workers: int = 8, enable_space_pruning: bool = True,
                 enable_early_stopping: bool = True, enable_bayesian: bool = True):
        """
        初始化优化器 - Week 4完整版

        Args:
            max_workers: 最大并行工作进程数
            enable_space_pruning: 启用参数空间智能裁剪
            enable_early_stopping: 启用早停机制
            enable_bayesian: 启用贝叶斯优化
        """
        self.max_workers = max_workers
        self.enable_space_pruning = enable_space_pruning
        self.enable_early_stopping = enable_early_stopping
        self.enable_bayesian = enable_bayesian

        # Week 4 新增组件
        self.space_pruner = ParameterSpacePruner() if enable_space_pruning else None
        self.early_stopping_manager = EarlyStoppingManager() if enable_early_stopping else None

        self.optimization_methods = {
            'grid_search': self._grid_search,
            'random_search': self._random_search,
            'bayesian': self._bayesian_optimization,
            'smart_search': self._smart_search,
            'hybrid_parallel': self._hybrid_parallel_search,  # Week 4 新增
            'adaptive_bayesian': self._adaptive_bayesian_search  # Week 4 新增
        }

        # 性能统计
        self.optimization_count = 0
        self.total_optimization_time = 0.0
        self.space_pruning_count = 0
        self.early_stopping_count = 0
        self.optimization_history = []  # Week 4 优化历史记录

        logger.info(f"Week 4 智能参数优化器初始化完成")
        logger.info(f"  并行进程数: {max_workers}")
        logger.info(f"  参数空间裁剪: {'启用' if enable_space_pruning else '禁用'}")
        logger.info(f"  早停机制: {'启用' if enable_early_stopping else '禁用'}")
        logger.info(f"  贝叶斯优化: {'启用' if enable_bayesian else '禁用'}")
        logger.info(f"  Scikit-Optimize: {'可用' if SKOPT_AVAILABLE else '不可用'}")

    def optimize_strategy(self,
                         data: pd.DataFrame,
                         strategy_func: Callable,
                         param_bounds: Dict[str, Tuple[Any, Any]],
                         objective: str = 'sharpe_ratio',
                         method: str = 'smart_search',
                         max_iterations: int = 1000,
                         timeout: float = 300.0) -> Optional[OptimizationResult]:
        """
        Week 4 策略参数优化主函数 - 增强版
        集成所有Week 4功能：参数空间裁剪、贝叶斯优化、并行处理、早停机制

        Args:
            data: 价格数据
            strategy_func: 策略函数，参数为 (data, params) -> BacktestResult
            param_bounds: 参数边界 {'param_name': (min, max)}
            objective: 优化目标 ('sharpe_ratio', 'total_return', 'calmar_ratio')
            method: 优化方法 (新增: hybrid_parallel, adaptive_bayesian)
            max_iterations: 最大迭代次数
            timeout: 超时时间（秒）

        Returns:
            增强的优化结果
        """
        try:
            # 更新统计
            self.optimization_count += 1

            if method not in self.optimization_methods:
                logger.error(f"未知优化方法: {method}")
                logger.info(f"可用方法: {list(self.optimization_methods.keys())}")
                return None

            logger.info(f"Week 4 参数优化开始: 方法={method}, 目标={objective}, 最大迭代={max_iterations}")
            logger.info(f"功能特性: 参数空间裁剪={self.enable_space_pruning}, 早停={self.enable_early_stopping}, 贝叶斯={self.enable_bayesian}")

            start_time = time.time()
            optimization_func = self.optimization_methods[method]

            result = optimization_func(
                data, strategy_func, param_bounds, objective,
                max_iterations, timeout, start_time
            )

            # 更新统计
            self.total_optimization_time += time.time() - start_time

            if result:
                logger.info(f"Week 4 优化完成: 最佳{objective}={result.best_score:.4f}, Sharpe={result.best_sharpe:.3f}")
                logger.info(f"性能指标: 迭代={result.total_iterations}, 耗时={result.optimization_time:.2f}s, 并行效率={result.parallel_efficiency:.2%}")

                if result.early_stopped:
                    logger.info(f"早停已触发，节省了 {(1 - len(result.convergence_curve) / max_iterations) * 100:.1f}% 的计算资源")

                # 自动保存结果
                if hasattr(self, 'auto_save') and self.auto_save:
                    saved_path = self.save_optimization_result(result)
                    logger.info(f"优化结果已自动保存: {saved_path}")

            else:
                logger.warning("Week 4 优化失败")

            return result

        except Exception as e:
            logger.error(f"Week 4 参数优化失败: {e}")
            return None

    def _create_final_result(self, all_results: List[Dict[str, Any]], convergence_curve: List[float],
                              best_score: float, best_params: Dict[str, Any], best_sharpe: float,
                              param_bounds: Dict[str, Tuple[Any, Any]], max_iterations: int, start_time: float) -> Optional[OptimizationResult]:
        """创建最终结果"""
        total_time = time.time() - start_time

        # Week 4 结果分析
        parameter_importance = self._analyze_parameter_importance(all_results) if all_results else {}
        convergence_analysis = self._analyze_convergence(convergence_curve) if convergence_curve else {}
        space_reduction_stats = {
            'original_params': len(param_bounds),
            'final_iterations': len(all_results),
            'efficiency': len(all_results) / max_iterations if max_iterations > 0 else 0
        }

        # 计算并行效率
        if len(all_results) > 0 and total_time > 0:
            parallel_efficiency = (len(all_results) / total_time) / (self.max_workers * 100)
            parallel_efficiency = min(1.0, parallel_efficiency)
        else:
            parallel_efficiency = 0.0

        early_stopped = (self.early_stopping_manager.early_stopped
                           if self.early_stopping_manager else False)

        logger.info(f"智能搜索完成: 最佳分数={best_score:.4f}, 迭代={len(all_results)}, 耗时={total_time:.2f}s")

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            best_sharpe=best_sharpe,
            total_iterations=len(all_results),
            optimization_time=total_time,
            all_results=all_results,
            convergence_curve=convergence_curve,
            method_used='smart_search_week4',
            parameter_importance=parameter_importance,
            convergence_analysis=convergence_analysis,
            early_stopped=early_stopped,
            space_reduction_stats=space_reduction_stats,
            parallel_efficiency=parallel_efficiency,
            optimization_id=f"smart_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    def _hybrid_parallel_search(self, data: pd.DataFrame, strategy_func: Callable,
                               param_bounds: Dict[str, Tuple[Any, Any]], objective: str,
                               max_iterations: int, timeout: float, start_time: float) -> Optional[OptimizationResult]:
        """
        混合并行搜索 - Week 4 Task 4.3
        结合多种优化方法的并行搜索
        """
        try:
            # 将迭代分配给不同的方法
            method_iterations = {
                'random_search': max_iterations // 3,
                'grid_search': max_iterations // 4,
                'bayesian': max_iterations // 3
            }

            all_results = []
            convergence_curve = []
            best_score = -float('inf')
            best_params = {}
            best_sharpe = 0
            current_iterations = 0

            # 并行执行不同优化方法
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []

                # 提交不同方法的优化任务
                for method, iterations in method_iterations.items():
                    if iterations > 0:
                        future = executor.submit(
                            self.optimization_methods[method],
                            data, strategy_func, param_bounds, objective,
                            iterations, timeout / len(method_iterations), start_time
                        )
                        futures.append((method, future))

                # 收集结果
                for method, future in futures:
                    try:
                        result = future.result(timeout=timeout)
                        if result:
                            all_results.extend(result.all_results)
                            convergence_curve.extend(result.convergence_curve)

                            if result.best_score > best_score:
                                best_score = result.best_score
                                best_params = result.best_params.copy()
                                best_sharpe = result.best_sharpe

                            current_iterations += result.total_iterations
                            logger.info(f"混合优化 - {method}: 最佳分数={result.best_score:.4f}, 迭代={result.total_iterations}")

                    except Exception as e:
                        logger.warning(f"混合优化 - {method} 失败: {e}")

            # 基于所有结果的精细搜索
            if len(all_results) > 20:
                fine_iterations = max_iterations - current_iterations
                if fine_iterations > 0:
                    logger.info(f"混合优化 - 精细搜索阶段 ({fine_iterations} 次迭代)")

                    # 使用参数空间裁剪
                    if self.space_pruner:
                        pruned_bounds = self.space_pruner.prune_search_space(
                            param_bounds, all_results, target_reduction=0.7
                        )
                        self.space_pruning_count += 1
                    else:
                        pruned_bounds = self._narrow_search_bounds(param_bounds, best_params, factor=0.3)

                    # 最终精细搜索
                    fine_results = self._random_search(
                        data, strategy_func, pruned_bounds, objective,
                        fine_iterations, timeout * 0.3, start_time
                    )

                    if fine_results:
                        all_results.extend(fine_results.all_results)
                        convergence_curve.extend(fine_results.convergence_curve)

                        if fine_results.best_score > best_score:
                            best_score = fine_results.best_score
                            best_params = fine_results.best_params.copy()
                            best_sharpe = fine_results.best_sharpe

            total_time = time.time() - start_time

            return OptimizationResult(
                best_params=best_params,
                best_score=best_score,
                best_sharpe=best_sharpe,
                total_iterations=len(all_results),
                optimization_time=total_time,
                all_results=all_results,
                convergence_curve=convergence_curve,
                method_used='hybrid_parallel'
            )

        except Exception as e:
            logger.error(f"混合并行搜索失败: {e}")
            return None

    def _adaptive_bayesian_search(self, data: pd.DataFrame, strategy_func: Callable,
                                   param_bounds: Dict[str, Tuple[Any, Any]], objective: str,
                                   max_iterations: int, timeout: float, start_time: float) -> Optional[OptimizationResult]:
        """
        自适应贝叶斯优化 - Week 4 Task 4.2
        使用scikit-optimize的高级贝叶斯优化
        """
        if not SKOPT_AVAILABLE:
            logger.warning("scikit-optimize不可用，使用简化贝叶斯优化")
            return self._bayesian_optimization(data, strategy_func, param_bounds, objective, max_iterations, timeout, start_time)

        try:
            from skopt.space import Real, Integer
            from skopt.utils import use_named_args

            # 构建搜索空间
            dimensions = []
            param_names = []

            for param_name, (min_val, max_val) in param_bounds.items():
                param_names.append(param_name)

                if isinstance(min_val, int) and isinstance(max_val, int):
                    dimensions.append(Integer(min_val, max_val, name=param_name))
                else:
                    dimensions.append(Real(min_val, max_val, name=param_name))

            # 目标函数包装
            @use_named_args(dimensions)
            def objective_func(**params):
                score, sharpe = self._evaluate_single_params(data, strategy_func, params, objective)
                if score is None:
                    return -float('inf')
                return -score  # 最小化负分数等于最大化分数

            # 执行贝叶斯优化
            logger.info(f"自适应贝叶斯优化开始: {max_iterations} 次迭代, {len(dimensions)} 个参数")

            result = gp_minimize(
                func=objective_func,
                dimensions=dimensions,
                n_calls=max_iterations,
                n_initial_points=min(20, max_iterations // 4),
                acq_func='EI',  # Expected Improvement
                random_state=42,
                verbose=False
            )

            # 提取最佳参数
            best_params = dict(zip(param_names, result.x))
            best_score = -result.fun
            best_sharpe = 0  # 需要重新计算

            # 重新计算Sharpe比率
            _, best_sharpe = self._evaluate_single_params(data, strategy_func, best_params, objective)

            # 生成完整结果记录
            all_results = []
            convergence_curve = []

            for i, (params, func_val) in enumerate(zip(result.x_iters, result.func_vals)):
                param_dict = dict(zip(param_names, params))
                score = -func_val
                _, sharpe = self._evaluate_single_params(data, strategy_func, param_dict, objective)

                all_results.append({'params': param_dict, 'score': score, 'sharpe': sharpe})
                convergence_curve.append(score)

            total_time = time.time() - start_time

            logger.info(f"自适应贝叶斯优化完成: 最佳分数={best_score:.4f}, 耗时={total_time:.2f}s")

            return OptimizationResult(
                best_params=best_params,
                best_score=best_score,
                best_sharpe=best_sharpe,
                total_iterations=len(all_results),
                optimization_time=total_time,
                all_results=all_results,
                convergence_curve=convergence_curve,
                method_used='adaptive_bayesian'
            )

        except Exception as e:
            logger.error(f"自适应贝叶斯优化失败: {e}")
            return self._bayesian_optimization(data, strategy_func, param_bounds, objective, max_iterations, timeout, start_time)

    def _smart_search(self, data: pd.DataFrame, strategy_func: Callable,
                      param_bounds: Dict[str, Tuple[Any, Any]], objective: str,
                      max_iterations: int, timeout: float, start_time: float) -> Optional[OptimizationResult]:
        """
        Week 4 智能搜索优化算法 - 增强版
        集成早停机制、参数空间裁剪、结果分析
        """
        try:
            all_results = []
            convergence_curve = []
            best_score = -float('inf')
            best_params = {}
            best_sharpe = 0
            optimization_id = f"smart_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 初始化早停管理器
            if self.early_stopping_manager:
                self.early_stopping_manager = EarlyStoppingManager()

            # 阶段1: 快速网格搜索 (20%的迭代)
            grid_iterations = max_iterations // 5
            logger.info(f"阶段1: 网格搜索 ({grid_iterations} 次迭代)")

            grid_results = self._grid_search(
                data, strategy_func, param_bounds, objective,
                grid_iterations, timeout * 0.3, start_time
            )

            if grid_results:
                all_results.extend(grid_results.all_results)
                convergence_curve.extend(grid_results.convergence_curve)
                if grid_results.best_score > best_score:
                    best_score = grid_results.best_score
                    best_params = grid_results.best_params.copy()
                    best_sharpe = grid_results.best_sharpe

                # 检查早停
                if self.early_stopping_manager and self.early_stopping_manager.should_stop(
                        len(all_results), best_score, time.time() - start_time):
                    self.early_stopping_count += 1
                    logger.info("早停触发于阶段1")
                    return self._create_final_result(all_results, convergence_curve, best_score, best_params, best_sharpe,
                                                   param_bounds, max_iterations, start_time)

            # 阶段2: 围绕最优区域的随机搜索 (50%的迭代)
            random_iterations = max_iterations // 2
            logger.info(f"阶段2: 局部随机搜索 ({random_iterations} 次迭代)")

            # 使用参数空间智能裁剪
            if self.space_pruner and len(all_results) >= 20:
                narrowed_bounds = self.space_pruner.prune_search_space(
                    param_bounds, all_results, target_reduction=0.5
                )
                self.space_pruning_count += 1
                logger.info("参数空间智能裁剪已应用")
            else:
                narrowed_bounds = self._narrow_search_bounds(param_bounds, best_params, factor=0.5)

            random_results = self._random_search(
                data, strategy_func, narrowed_bounds, objective,
                random_iterations, timeout * 0.5, start_time
            )

            if random_results:
                all_results.extend(random_results.all_results)
                convergence_curve.extend(random_results.convergence_curve)
                if random_results.best_score > best_score:
                    best_score = random_results.best_score
                    best_params = random_results.best_params.copy()
                    best_sharpe = random_results.best_sharpe

                # 检查早停
                if self.early_stopping_manager and self.early_stopping_manager.should_stop(
                        len(all_results), best_score, time.time() - start_time):
                    self.early_stopping_count += 1
                    logger.info("早停触发于阶段2")
                    return self._create_final_result(all_results, convergence_curve, best_score, best_params, best_sharpe,
                                                   param_bounds, max_iterations, start_time)

            # 阶段3: 贝叶斯优化精细搜索 (30%的迭代)
            bayesian_iterations = max_iterations - grid_iterations - random_iterations
            if bayesian_iterations > 0:
                logger.info(f"阶段3: 贝叶斯优化 ({bayesian_iterations} 次迭代)")

                # 进一步缩小搜索范围
                if self.space_pruner and len(all_results) >= 20:
                    final_bounds = self.space_pruner.prune_search_space(
                        narrowed_bounds, all_results, target_reduction=0.3
                    )
                    self.space_pruning_count += 1
                else:
                    final_bounds = self._narrow_search_bounds(narrowed_bounds, best_params, factor=0.3)

                if self.enable_bayesian and SKOPT_AVAILABLE:
                    bayesian_results = self._adaptive_bayesian_search(
                        data, strategy_func, final_bounds, objective,
                        bayesian_iterations, timeout * 0.2, start_time
                    )
                else:
                    bayesian_results = self._bayesian_optimization(
                        data, strategy_func, final_bounds, objective,
                        bayesian_iterations, timeout * 0.2, start_time
                    )

                if bayesian_results:
                    all_results.extend(bayesian_results.all_results)
                    convergence_curve.extend(bayesian_results.convergence_curve)
                    if bayesian_results.best_score > best_score:
                        best_score = bayesian_results.best_score
                        best_params = bayesian_results.best_params.copy()
                        best_sharpe = bayesian_results.best_sharpe

            # 智能搜索完成，创建最终结果
            return self._create_final_result(all_results, convergence_curve, best_score, best_params, best_sharpe,
                                           param_bounds, max_iterations, start_time, method_used="smart_search_week4")

        except Exception as e:
            logger.error(f"智能搜索失败: {e}")
            return None

    def _grid_search(self, data: pd.DataFrame, strategy_func: Callable,
                     param_bounds: Dict[str, Tuple[Any, Any]], objective: str,
                     max_iterations: int, timeout: float, start_time: float) -> Optional[OptimizationResult]:
        """网格搜索"""
        try:
            param_combinations = self._generate_grid_combinations(param_bounds, max_iterations)
            return self._evaluate_combinations(data, strategy_func, param_combinations, objective, start_time)

        except Exception as e:
            logger.error(f"网格搜索失败: {e}")
            return None

    def _random_search(self, data: pd.DataFrame, strategy_func: Callable,
                       param_bounds: Dict[str, Tuple[Any, Any]], objective: str,
                       max_iterations: int, timeout: float, start_time: float) -> Optional[OptimizationResult]:
        """随机搜索"""
        try:
            param_combinations = self._generate_random_combinations(param_bounds, max_iterations)
            return self._evaluate_combinations(data, strategy_func, param_combinations, objective, start_time)

        except Exception as e:
            logger.error(f"随机搜索失败: {e}")
            return None

    def _bayesian_optimization(self, data: pd.DataFrame, strategy_func: Callable,
                              param_bounds: Dict[str, Tuple[Any, Any]], objective: str,
                              max_iterations: int, timeout: float, start_time: float) -> Optional[OptimizationResult]:
        """贝叶斯优化（简化实现）"""
        try:
            # 简化的贝叶斯优化：基于历史结果的加权随机搜索
            all_results = []
            convergence_curve = []
            best_score = -float('inf')
            best_params = {}
            best_sharpe = 0

            # 初始随机采样
            initial_samples = min(20, max_iterations // 4)
            param_combinations = self._generate_random_combinations(param_bounds, initial_samples)

            for i, params in enumerate(param_combinations):
                if time.time() - start_time > timeout:
                    break

                score, sharpe = self._evaluate_single_params(data, strategy_func, params, objective)
                if score is not None:
                    all_results.append({'params': params, 'score': score, 'sharpe': sharpe})
                    convergence_curve.append(score)

                    if score > best_score:
                        best_score = score
                        best_params = params.copy()
                        best_sharpe = sharpe

            # 基于结果的加权采样
            remaining_iterations = max_iterations - initial_samples
            if remaining_iterations > 0 and len(all_results) > 5:
                param_combinations = self._generate_weighted_combinations(
                    param_bounds, all_results, remaining_iterations
                )

                for params in param_combinations:
                    if time.time() - start_time > timeout:
                        break

                    score, sharpe = self._evaluate_single_params(data, strategy_func, params, objective)
                    if score is not None:
                        all_results.append({'params': params, 'score': score, 'sharpe': sharpe})
                        convergence_curve.append(score)

                        if score > best_score:
                            best_score = score
                            best_params = params.copy()
                            best_sharpe = sharpe

            total_time = time.time() - start_time

            return OptimizationResult(
                best_params=best_params,
                best_score=best_score,
                best_sharpe=best_sharpe,
                total_iterations=len(all_results),
                optimization_time=total_time,
                all_results=all_results,
                convergence_curve=convergence_curve
            )

        except Exception as e:
            logger.error(f"贝叶斯优化失败: {e}")
            return None

    def _evaluate_combinations(self, data: pd.DataFrame, strategy_func: Callable,
                               param_combinations: List[Dict], objective: str,
                               start_time: float) -> Optional[OptimizationResult]:
        """评估参数组合"""
        all_results = []
        convergence_curve = []
        best_score = -float('inf')
        best_params = {}
        best_sharpe = 0

        # 并行评估
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_params = {
                executor.submit(self._evaluate_single_params, data, strategy_func, params, objective): params
                for params in param_combinations
            }

            # 收集结果
            for future in as_completed(future_to_params):
                if time.time() - start_time > 300:  # 5分钟超时
                    break

                params = future_to_params[future]
                try:
                    score, sharpe = future.result(timeout=30)
                    if score is not None:
                        all_results.append({'params': params, 'score': score, 'sharpe': sharpe})
                        convergence_curve.append(score)

                        if score > best_score:
                            best_score = score
                            best_params = params.copy()
                            best_sharpe = sharpe

                except Exception as e:
                    logger.warning(f"参数评估失败: {e}")

        total_time = time.time() - start_time

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            best_sharpe=best_sharpe,
            total_iterations=len(all_results),
            optimization_time=total_time,
            all_results=all_results,
            convergence_curve=convergence_curve
        )

    def _evaluate_single_params(self, data: pd.DataFrame, strategy_func: Callable,
                                params: Dict[str, Any], objective: str) -> Tuple[Optional[float], float]:
        """评估单个参数组合"""
        try:
            result = strategy_func(data, **params)
            if result is None:
                return None, 0

            # 根据目标函数返回分数
            if objective == 'sharpe_ratio':
                return result.sharpe_ratio, result.sharpe_ratio
            elif objective == 'total_return':
                return result.total_return, result.sharpe_ratio
            elif objective == 'calmar_ratio':
                return result.calmar_ratio, result.sharpe_ratio
            else:
                return result.sharpe_ratio, result.sharpe_ratio

        except Exception as e:
            logger.debug(f"参数评估失败 {params}: {e}")
            return None, 0

    def _generate_grid_combinations(self, param_bounds: Dict[str, Tuple[Any, Any]], max_combinations: int) -> List[Dict[str, Any]]:
        """生成网格搜索组合"""
        import itertools

        param_names = list(param_bounds.keys())
        param_ranges = []

        for param_name, (min_val, max_val) in param_bounds.items():
            if isinstance(min_val, int) and isinstance(max_val, int):
                # 整数参数
                range_size = min(5, max_val - min_val + 1)
                param_range = list(np.linspace(min_val, max_val, range_size, dtype=int))
            else:
                # 浮点参数
                param_range = list(np.linspace(min_val, max_val, 5))

            param_ranges.append(param_range)

        # 生成所有组合
        all_combinations = list(itertools.product(*param_ranges))
        param_combinations = [dict(zip(param_names, combo)) for combo in all_combinations]

        # 限制组合数量
        if len(param_combinations) > max_combinations:
            # 均匀采样
            indices = np.linspace(0, len(param_combinations) - 1, max_combinations, dtype=int)
            param_combinations = [param_combinations[i] for i in indices]

        return param_combinations

    def _generate_random_combinations(self, param_bounds: Dict[str, Tuple[Any, Any]], n_combinations: int) -> List[Dict[str, Any]]:
        """生成随机参数组合"""
        param_combinations = []
        param_names = list(param_bounds.keys())

        for _ in range(n_combinations):
            params = {}
            for param_name, (min_val, max_val) in param_bounds.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    # 整数参数
                    params[param_name] = np.random.randint(min_val, max_val + 1)
                else:
                    # 浮点参数
                    params[param_name] = np.random.uniform(min_val, max_val)

            param_combinations.append(params)

        return param_combinations

    def _generate_weighted_combinations(self, param_bounds: Dict[str, Tuple[Any, Any]],
                                        historical_results: List[Dict], n_combinations: int) -> List[Dict[str, Any]]:
        """基于历史结果生成加权参数组合"""
        param_combinations = []
        param_names = list(param_bounds.keys())

        # 根据历史结果的分数计算权重
        scores = [result['score'] for result in historical_results]
        weights = np.array(scores) - min(scores) + 1  # 确保权重为正
        weights = weights / weights.sum()

        for _ in range(n_combinations):
            # 选择历史结果作为基础
            base_idx = np.random.choice(len(historical_results), p=weights)
            base_params = historical_results[base_idx]['params']

            # 在基础参数周围添加随机扰动
            params = {}
            for param_name, (min_val, max_val) in param_bounds.items():
                base_val = base_params.get(param_name, (min_val + max_val) / 2)

                # 添加高斯扰动
                if isinstance(min_val, int) and isinstance(max_val, int):
                    noise = np.random.normal(0, (max_val - min_val) * 0.1)
                    new_val = int(base_val + noise)
                else:
                    noise = np.random.normal(0, (max_val - min_val) * 0.1)
                    new_val = base_val + noise

                # 确保在边界内
                params[param_name] = max(min_val, min(max_val, new_val))

            param_combinations.append(params)

        return param_combinations

    def _narrow_search_bounds(self, original_bounds: Dict[str, Tuple[Any, Any]],
                              center_params: Dict[str, Any], factor: float = 0.5) -> Dict[str, Tuple[Any, Any]]:
        """缩小搜索范围到中心参数附近"""
        narrowed_bounds = {}

        for param_name, (min_val, max_val) in original_bounds.items():
            center_val = center_params.get(param_name, (min_val + max_val) / 2)
            range_size = (max_val - min_val) * factor
            new_min = max(min_val, center_val - range_size / 2)
            new_max = min(max_val, center_val + range_size / 2)

            narrowed_bounds[param_name] = (new_min, new_max)

        return narrowed_bounds

    def get_optimization_methods(self) -> List[str]:
        """获取可用的优化方法"""
        return list(self.optimization_methods.keys())

    def analyze_optimization_result(self, result: OptimizationResult) -> Dict[str, Any]:
        """
        Week 4 增强优化结果分析 - Task 4.5
        提供全面的优化结果分析和可视化数据
        """
        if not result:
            return {}

        analysis = {
            'best_params': result.best_params,
            'best_score': result.best_score,
            'best_sharpe': result.best_sharpe,
            'total_iterations': result.total_iterations,
            'optimization_time': result.optimization_time,
            'iterations_per_second': result.total_iterations / result.optimization_time if result.optimization_time > 0 else 0,
            'method_used': result.method_used,
            'early_stopped': result.early_stopped,
            'parallel_efficiency': result.parallel_efficiency,
            'optimization_id': result.optimization_id
        }

        # 使用Week 4新增的分析结果
        if result.parameter_importance:
            analysis['parameter_importance'] = result.parameter_importance

        if result.convergence_analysis:
            analysis['convergence_analysis'] = result.convergence_analysis

        if result.space_reduction_stats:
            analysis['space_reduction_stats'] = result.space_reduction_stats

        # Week 4 新增分析
        if result.all_results:
            # 性能分布分析
            scores = [r['score'] for r in result.all_results if r['score'] != -float('inf')]
            if scores:
                analysis['performance_distribution'] = {
                    'mean_score': np.mean(scores),
                    'std_score': np.std(scores),
                    'min_score': np.min(scores),
                    'max_score': np.max(scores),
                    'score_range': np.max(scores) - np.min(scores),
                    'score_cv': np.std(scores) / np.mean(scores) if np.mean(scores) != 0 else 0
                }

            # 参数统计
            param_stats = {}
            if result.all_results:
                param_names = list(result.all_results[0]['params'].keys())
                for param_name in param_names:
                    param_values = [r['params'].get(param_name) for r in result.all_results if param_name in r['params']]
                    if param_values:
                        param_stats[param_name] = {
                            'mean': np.mean(param_values),
                            'std': np.std(param_values),
                            'min': np.min(param_values),
                            'max': np.max(param_values),
                            'unique_count': len(set(param_values)),
                            'exploration_coverage': len(set(param_values)) / len(param_values) if len(param_values) > 0 else 0
                        }
                analysis['parameter_statistics'] = param_stats

            # 优化效率分析
            analysis['efficiency_metrics'] = {
                'success_rate': len([r for r in result.all_results if r['score'] > 0]) / len(result.all_results),
                'improvement_rate': self._calculate_improvement_rate(result.convergence_curve) if result.convergence_curve else 0,
                'convergence_speed': self._calculate_convergence_speed(result.convergence_curve) if result.convergence_curve else 0
            }

        return analysis

    def generate_optimization_report(self, result: OptimizationResult,
                                     save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Week 4 生成优化报告 - Task 4.5
        生成详细的优化报告并可选择保存到文件
        """
        if not result:
            return {}

        analysis = self.analyze_optimization_result(result)

        # 生成报告
        report = {
            'summary': {
                'optimization_id': result.optimization_id,
                'method_used': result.method_used,
                'best_score': result.best_score,
                'best_sharpe': result.best_sharpe,
                'best_params': result.best_params,
                'total_iterations': result.total_iterations,
                'optimization_time': result.optimization_time,
                'iterations_per_second': result.total_iterations / result.optimization_time if result.optimization_time > 0 else 0,
                'early_stopped': result.early_stopped,
                'parallel_efficiency': result.parallel_efficiency,
                'timestamp': datetime.now().isoformat()
            },
            'performance_analysis': analysis.get('performance_distribution', {}),
            'parameter_analysis': {
                'importance': result.parameter_importance,
                'statistics': analysis.get('parameter_statistics', {}),
                'space_reduction': result.space_reduction_stats
            },
            'convergence_analysis': {
                'metrics': result.convergence_analysis,
                'efficiency_metrics': analysis.get('efficiency_metrics', {})
            },
            'detailed_results': result.all_results[:100] if result.all_results else []  # 限制详细结果数量
        }

        # 保存报告到文件
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                logger.info(f"优化报告已保存到: {save_path}")
            except Exception as e:
                logger.error(f"保存优化报告失败: {e}")

        return report

    def save_optimization_result(self, result: OptimizationResult,
                                base_path: str = "optimization_results") -> str:
        """
        保存优化结果到JSON文件
        """
        try:
            os.makedirs(base_path, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimization_{result.optimization_id}_{timestamp}.json"
            filepath = os.path.join(base_path, filename)

            # 准备保存的数据
            save_data = {
                'optimization_result': {
                    'best_params': result.best_params,
                    'best_score': result.best_score,
                    'best_sharpe': result.best_sharpe,
                    'total_iterations': result.total_iterations,
                    'optimization_time': result.optimization_time,
                    'method_used': result.method_used,
                    'early_stopped': result.early_stopped,
                    'parallel_efficiency': result.parallel_efficiency,
                    'optimization_id': result.optimization_id,
                    'parameter_importance': result.parameter_importance,
                    'convergence_analysis': result.convergence_analysis,
                    'space_reduction_stats': result.space_reduction_stats
                },
                'all_results': result.all_results,
                'convergence_curve': result.convergence_curve,
                'timestamp': datetime.now().isoformat()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"优化结果已保存到: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"保存优化结果失败: {e}")
            return ""

    def _calculate_improvement_rate(self, convergence_curve: List[float]) -> float:
        """计算改进率"""
        if len(convergence_curve) < 2:
            return 0.0

        initial_score = convergence_curve[0]
        final_score = max(convergence_curve)

        if initial_score <= 0:
            return 0.0

        improvement = (final_score - initial_score) / abs(initial_score)
        return max(0.0, improvement)

    def _calculate_convergence_speed(self, convergence_curve: List[float]) -> float:
        """计算收敛速度"""
        if len(convergence_curve) < 10:
            return 0.0

        # 找到达到90%最终性能的时间点
        final_score = max(convergence_curve)
        target_score = final_score * 0.9

        for i, score in enumerate(convergence_curve):
            if score >= target_score:
                return i / len(convergence_curve)

        return 1.0

    def get_optimizer_stats(self) -> Dict[str, Any]:
        """获取优化器统计信息"""
        return {
            'total_optimizations': self.optimization_count,
            'total_optimization_time': self.total_optimization_time,
            'average_time_per_optimization': self.total_optimization_time / self.optimization_count if self.optimization_count > 0 else 0,
            'space_pruning_count': self.space_pruning_count,
            'early_stopping_count': self.early_stopping_count,
            'space_pruning_rate': self.space_pruning_count / self.optimization_count if self.optimization_count > 0 else 0,
            'early_stopping_rate': self.early_stopping_count / self.optimization_count if self.optimization_count > 0 else 0,
            'optimization_history_length': len(self.optimization_history),
            'features': {
                'space_pruning': self.enable_space_pruning,
                'early_stopping': self.enable_early_stopping,
                'bayesian_optimization': self.enable_bayesian,
                'skopt_available': SKOPT_AVAILABLE,
                'max_workers': self.max_workers
            }
        }

    def _analyze_parameter_importance(self, results: List[Dict]) -> Dict[str, float]:
        """分析参数重要性"""
        if not results:
            return {}

        # 简化的重要性分析：基于参数与分数的相关性
        param_names = list(results[0]['params'].keys())
        importance = {}

        scores = [result['score'] for result in results]

        for param_name in param_names:
            param_values = [result['params'][param_name] for result in results]
            correlation = np.corrcoef(param_values, scores)[0, 1]
            importance[param_name] = abs(correlation) if not np.isnan(correlation) else 0

        return importance

    def _analyze_convergence(self, convergence_curve: List[float]) -> Dict[str, Any]:
        """分析收敛性"""
        if len(convergence_curve) < 10:
            return {}

        # 计算收敛指标
        max_score = max(convergence_curve)
        max_idx = convergence_curve.index(max_score)
        convergence_point = max_idx / len(convergence_curve)

        # 计算最后10%的改进幅度
        last_10_percent = int(len(convergence_curve) * 0.1)
        if last_10_percent > 1:
            recent_scores = convergence_curve[-last_10_percent:]
            recent_improvement = max(recent_scores) - min(recent_scores)
        else:
            recent_improvement = 0

        return {
            'max_score': max_score,
            'convergence_point': convergence_point,
            'recent_improvement': recent_improvement,
            'converged': convergence_point < 0.8 and recent_improvement < max_score * 0.01
        }


# 便捷函数
def get_optimizer() -> ParameterOptimizer:
    """获取优化器实例"""
    return ParameterOptimizer()

def quick_optimize(data: pd.DataFrame, strategy_func: Callable,
                   param_bounds: Dict[str, Tuple[Any, Any]], **kwargs) -> Optional[OptimizationResult]:
    """便捷的快速优化函数"""
    optimizer = ParameterOptimizer()
    return optimizer.optimize_strategy(data, strategy_func, param_bounds, **kwargs)