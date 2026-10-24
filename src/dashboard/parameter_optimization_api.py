"""
参数优化API服务

提供策略参数的实时优化、调整和性能分析功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
from scipy import optimize
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import pandas as pd

from ..models.cbsc_models import AdvancedSentimentProcessor
from ..backtest.enhanced_backtest_engine import EnhancedBacktestEngine


class OptimizationMethod(Enum):
    """优化方法枚举"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"


class ObjectiveType(Enum):
    """目标类型枚举"""
    MAXIMIZE_SHARPE = "maximize_sharpe"
    MAXIMIZE_RETURN = "maximize_return"
    MINIMIZE_RISK = "minimize_risk"
    MAXIMIZE_CALMAR = "maximize_calmar"
    MAXIMIZE_WIN_RATE = "maximize_win_rate"


@dataclass
class ParameterRange:
    """参数范围定义"""
    name: str
    min_value: float
    max_value: float
    step: Optional[float] = None
    data_type: str = "float"  # float, int, categorical
    categories: Optional[List[str]] = None


@dataclass
class OptimizationTask:
    """优化任务定义"""
    task_id: str
    strategy_type: str
    parameters: List[ParameterRange]
    objective: ObjectiveType
    method: OptimizationMethod
    constraints: Dict[str, Any]
    status: str = "pending"
    progress: float = 0.0
    best_parameters: Optional[Dict[str, Any]] = None
    best_score: Optional[float] = None
    results: List[Dict[str, Any]] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    calmar_ratio: float
    volatility: float
    sortino_ratio: float


class ParameterOptimizationAPI:
    """参数优化API服务"""

    def __init__(self):
        self.logger = logging.getLogger("parameter_optimization_api")
        self.router = APIRouter(prefix="/api/optimization", tags=["parameter_optimization"])

        # 数据存储
        self.optimization_tasks: Dict[str, OptimizationTask] = {}
        self.parameter_history: Dict[str, List[Dict[str, Any]]] = {}
        self.performance_cache: Dict[str, PerformanceMetrics] = {}

        # 核心组件
        self.sentiment_processor = AdvancedSentimentProcessor()
        self.backtest_engine = EnhancedBacktestEngine()

        # WebSocket连接管理
        self.active_connections: List[WebSocket] = []

        self._setup_routes()

    def _setup_routes(self):
        """设置API路由"""

        @self.router.get("/parameters/{strategy_type}")
        async def get_strategy_parameters(strategy_type: str):
            """获取策略参数配置"""
            try:
                parameters = self._get_default_parameters(strategy_type)
                return {
                    "strategy_type": strategy_type,
                    "parameters": parameters,
                    "current_values": self._get_current_parameters(strategy_type)
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.post("/parameters/{strategy_type}/update")
        async def update_strategy_parameters(strategy_type: str, parameters: Dict[str, Any]):
            """更新策略参数"""
            try:
                # 验证参数
                validated_params = await self._validate_parameters(strategy_type, parameters)

                # 计算性能影响
                performance_impact = await self._calculate_performance_impact(
                    strategy_type, validated_params
                )

                # 保存参数历史
                self._save_parameter_history(strategy_type, validated_params, performance_impact)

                # 广播参数更新
                await self._broadcast_parameter_update(strategy_type, validated_params, performance_impact)

                return {
                    "success": True,
                    "parameters": validated_params,
                    "performance_impact": performance_impact,
                    "message": "参数更新成功"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.post("/optimize/start")
        async def start_optimization(task_config: Dict[str, Any]):
            """启动参数优化"""
            try:
                task_id = self._generate_task_id()

                # 创建优化任务
                task = OptimizationTask(
                    task_id=task_id,
                    strategy_type=task_config["strategy_type"],
                    parameters=self._parse_parameter_ranges(task_config["parameter_ranges"]),
                    objective=ObjectiveType(task_config["objective"]),
                    method=OptimizationMethod(task_config["method"]),
                    constraints=task_config.get("constraints", {}),
                    results=[],
                    created_at=datetime.now()
                )

                self.optimization_tasks[task_id] = task

                # 启动优化任务
                asyncio.create_task(self._run_optimization(task))

                # 广播任务创建
                await self._broadcast_task_update(task)

                return {
                    "task_id": task_id,
                    "status": "started",
                    "message": "优化任务已启动"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.get("/optimize/{task_id}")
        async def get_optimization_status(task_id: str):
            """获取优化任务状态"""
            if task_id not in self.optimization_tasks:
                raise HTTPException(status_code=404, detail="任务未找到")

            task = self.optimization_tasks[task_id]
            return asdict(task)

        @self.router.get("/optimize/{task_id}/results")
        async def get_optimization_results(task_id: str):
            """获取优化结果"""
            if task_id not in self.optimization_tasks:
                raise HTTPException(status_code=404, detail="任务未找到")

            task = self.optimization_tasks[task_id]
            if task.status != "completed":
                raise HTTPException(status_code=400, detail="任务尚未完成")

            return {
                "task_id": task_id,
                "best_parameters": task.best_parameters,
                "best_score": task.best_score,
                "results": task.results,
                "optimization_summary": self._generate_optimization_summary(task)
            }

        @self.router.get("/performance/{strategy_type}/history")
        async def get_parameter_performance_history(strategy_type: str, days: int = 30):
            """获取参数性能历史"""
            try:
                cutoff_date = datetime.now() - timedelta(days=days)
                history = self.parameter_history.get(strategy_type, [])

                filtered_history = [
                    record for record in history
                    if datetime.fromisoformat(record["timestamp"]) >= cutoff_date
                ]

                return {
                    "strategy_type": strategy_type,
                    "history": filtered_history,
                    "trends": self._analyze_parameter_trends(filtered_history)
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.post("/compare")
        async def compare_parameter_sets(comparison_config: Dict[str, Any]):
            """比较不同参数组合的性能"""
            try:
                strategy_type = comparison_config["strategy_type"]
                parameter_sets = comparison_config["parameter_sets"]

                results = []
                for params in parameter_sets:
                    performance = await self._calculate_performance_metrics(strategy_type, params)
                    results.append({
                        "parameters": params,
                        "performance": asdict(performance)
                    })

                # 排序和排名
                ranked_results = sorted(
                    results,
                    key=lambda x: x["performance"]["sharpe_ratio"],
                    reverse=True
                )

                return {
                    "strategy_type": strategy_type,
                    "comparison_results": ranked_results,
                    "best_parameters": ranked_results[0]["parameters"] if ranked_results else None,
                    "recommendation": self._generate_parameter_recommendation(ranked_results)
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket实时通信端点"""
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message["type"] == "subscribe_task":
                        task_id = message["task_id"]
                        if task_id in self.optimization_tasks:
                            await websocket.send_json({
                                "type": "task_update",
                                "task": asdict(self.optimization_tasks[task_id])
                            })

                    elif message["type"] == "subscribe_optimization":
                        strategy_type = message["strategy_type"]
                        # 发送相关策略的优化状态
                        await self._send_strategy_optimization_status(websocket, strategy_type)

            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

    async def _run_optimization(self, task: OptimizationTask):
        """运行优化任务"""
        try:
            task.status = "running"
            await self._broadcast_task_update(task)

            if task.method == OptimizationMethod.GRID_SEARCH:
                await self._grid_search_optimization(task)
            elif task.method == OptimizationMethod.RANDOM_SEARCH:
                await self._random_search_optimization(task)
            elif task.method == OptimizationMethod.BAYESIAN_OPTIMIZATION:
                await self._bayesian_optimization(task)
            elif task.method == OptimizationMethod.GENETIC_ALGORITHM:
                await self._genetic_algorithm_optimization(task)
            elif task.method == OptimizationMethod.PARTICLE_SWARM:
                await self._particle_swarm_optimization(task)

            task.status = "completed"
            task.completed_at = datetime.now()
            await self._broadcast_task_update(task)

        except Exception as e:
            self.logger.error(f"优化任务 {task.task_id} 失败: {e}")
            task.status = "failed"
            await self._broadcast_task_update(task)

    async def _grid_search_optimization(self, task: OptimizationTask):
        """网格搜索优化"""
        param_grids = []
        for param in task.parameters:
            if param.data_type == "int":
                values = list(range(int(param.min_value), int(param.max_value) + 1, int(param.step or 1)))
            elif param.data_type == "float":
                step = param.step or (param.max_value - param.min_value) / 20
                values = np.arange(param.min_value, param.max_value + step, step).tolist()
            else:  # categorical
                values = param.categories or []
            param_grids.append(values)

        total_combinations = np.prod([len(grid) for grid in param_grids])
        current_iteration = 0

        best_score = float('-inf')
        best_params = None

        for combination in np.ndindex(*[len(grid) for grid in param_grids]):
            params = {}
            for i, param in enumerate(task.parameters):
                if param.data_type == "int":
                    params[param.name] = int(param_grids[i][combination[i]])
                else:
                    params[param.name] = param_grids[i][combination[i]]

            # 计算性能指标
            performance = await self._calculate_performance_metrics(task.strategy_type, params)
            score = self._calculate_objective_score(task.objective, performance)

            # 记录结果
            result = {
                "parameters": params,
                "performance": asdict(performance),
                "score": score,
                "iteration": current_iteration
            }
            task.results.append(result)

            # 更新最佳结果
            if score > best_score:
                best_score = score
                best_params = params
                task.best_parameters = params
                task.best_score = score

            # 更新进度
            current_iteration += 1
            task.progress = (current_iteration / total_combinations) * 100

            # 定期广播更新
            if current_iteration % max(1, total_combinations // 20) == 0:
                await self._broadcast_task_update(task)

            # 避免过度计算
            if current_iteration >= 1000:  # 限制最大迭代次数
                break

    async def _random_search_optimization(self, task: OptimizationTask):
        """随机搜索优化"""
        n_iterations = 200
        best_score = float('-inf')
        best_params = None

        for i in range(n_iterations):
            params = {}
            for param in task.parameters:
                if param.data_type == "int":
                    params[param.name] = np.random.randint(param.min_value, param.max_value + 1)
                elif param.data_type == "float":
                    params[param.name] = np.random.uniform(param.min_value, param.max_value)
                else:  # categorical
                    params[param.name] = np.random.choice(param.categories or [])

            # 计算性能指标
            performance = await self._calculate_performance_metrics(task.strategy_type, params)
            score = self._calculate_objective_score(task.objective, performance)

            # 记录结果
            result = {
                "parameters": params,
                "performance": asdict(performance),
                "score": score,
                "iteration": i
            }
            task.results.append(result)

            # 更新最佳结果
            if score > best_score:
                best_score = score
                best_params = params
                task.best_parameters = params
                task.best_score = score

            # 更新进度
            task.progress = ((i + 1) / n_iterations) * 100

            # 定期广播更新
            if (i + 1) % 20 == 0:
                await self._broadcast_task_update(task)

    async def _bayesian_optimization(self, task: OptimizationTask):
        """贝叶斯优化"""
        # 简化的贝叶斯优化实现
        n_iterations = 50
        best_score = float('-inf')
        best_params = None

        # 初始随机采样
        for i in range(5):
            params = self._generate_random_parameters(task.parameters)
            performance = await self._calculate_performance_metrics(task.strategy_type, params)
            score = self._calculate_objective_score(task.objective, performance)

            result = {
                "parameters": params,
                "performance": asdict(performance),
                "score": score,
                "iteration": i
            }
            task.results.append(result)

            if score > best_score:
                best_score = score
                best_params = params

        # 迭代优化
        for i in range(5, n_iterations):
            # 基于历史结果生成新的参数组合
            params = self._generate_bayesian_suggestion(task.results, task.parameters)
            performance = await self._calculate_performance_metrics(task.strategy_type, params)
            score = self._calculate_objective_score(task.objective, performance)

            result = {
                "parameters": params,
                "performance": asdict(performance),
                "score": score,
                "iteration": i
            }
            task.results.append(result)

            if score > best_score:
                best_score = score
                best_params = params
                task.best_parameters = params
                task.best_score = score

            task.progress = ((i + 1) / n_iterations) * 100

            if (i + 1) % 10 == 0:
                await self._broadcast_task_update(task)

    async def _genetic_algorithm_optimization(self, task: OptimizationTask):
        """遗传算法优化"""
        population_size = 20
        n_generations = 10
        mutation_rate = 0.1

        # 初始化种群
        population = [self._generate_random_parameters(task.parameters) for _ in range(population_size)]

        for generation in range(n_generations):
            # 评估适应度
            fitness_scores = []
            for individual in population:
                performance = await self._calculate_performance_metrics(task.strategy_type, individual)
                score = self._calculate_objective_score(task.objective, performance)
                fitness_scores.append(score)

                result = {
                    "parameters": individual,
                    "performance": asdict(performance),
                    "score": score,
                    "generation": generation
                }
                task.results.append(result)

            # 选择最佳个体
            best_idx = np.argmax(fitness_scores)
            if fitness_scores[best_idx] > (task.best_score or float('-inf')):
                task.best_parameters = population[best_idx]
                task.best_score = fitness_scores[best_idx]

            # 选择、交叉、变异
            population = self._genetic_algorithm_evolution(
                population, fitness_scores, task.parameters, mutation_rate
            )

            task.progress = ((generation + 1) / n_generations) * 100
            await self._broadcast_task_update(task)

    async def _particle_swarm_optimization(self, task: OptimizationTask):
        """粒子群优化"""
        n_particles = 15
        n_iterations = 30
        w = 0.7  # 惯性权重
        c1 = 1.5  # 认知系数
        c2 = 1.5  # 社会系数

        # 初始化粒子群
        particles = []
        velocities = []
        personal_best = []
        personal_best_scores = []

        for _ in range(n_particles):
            position = self._generate_random_parameters(task.parameters)
            velocity = self._generate_random_velocities(task.parameters)

            particles.append(position)
            velocities.append(velocity)

            performance = await self._calculate_performance_metrics(task.strategy_type, position)
            score = self._calculate_objective_score(task.objective, performance)

            personal_best.append(position.copy())
            personal_best_scores.append(score)

        global_best_score = max(personal_best_scores)
        global_best = personal_best[np.argmax(personal_best_scores)]

        for iteration in range(n_iterations):
            for i in range(n_particles):
                # 更新速度
                for j, param in enumerate(task.parameters):
                    param_name = param.name
                    r1, r2 = np.random.random(), np.random.random()

                    velocities[i][param_name] = (
                        w * velocities[i][param_name] +
                        c1 * r1 * (personal_best[i][param_name] - particles[i][param_name]) +
                        c2 * r2 * (global_best[param_name] - particles[i][param_name])
                    )

                    # 更新位置
                    particles[i][param_name] += velocities[i][param_name]

                    # 限制在参数范围内
                    particles[i][param_name] = np.clip(
                        particles[i][param_name], param.min_value, param.max_value
                    )

                # 评估新位置
                performance = await self._calculate_performance_metrics(task.strategy_type, particles[i])
                score = self._calculate_objective_score(task.objective, performance)

                # 更新个体最优
                if score > personal_best_scores[i]:
                    personal_best[i] = particles[i].copy()
                    personal_best_scores[i] = score

                # 更新全局最优
                if score > global_best_score:
                    global_best = particles[i].copy()
                    global_best_score = score
                    task.best_parameters = global_best.copy()
                    task.best_score = global_best_score

                result = {
                    "parameters": particles[i].copy(),
                    "performance": asdict(performance),
                    "score": score,
                    "iteration": iteration,
                    "particle": i
                }
                task.results.append(result)

            task.progress = ((iteration + 1) / n_iterations) * 100
            await self._broadcast_task_update(task)

    def _generate_random_parameters(self, parameter_ranges: List[ParameterRange]) -> Dict[str, Any]:
        """生成随机参数组合"""
        params = {}
        for param in parameter_ranges:
            if param.data_type == "int":
                params[param.name] = np.random.randint(param.min_value, param.max_value + 1)
            elif param.data_type == "float":
                params[param.name] = np.random.uniform(param.min_value, param.max_value)
            else:  # categorical
                params[param.name] = np.random.choice(param.categories or [])
        return params

    def _generate_random_velocities(self, parameter_ranges: List[ParameterRange]) -> Dict[str, float]:
        """生成随机速度向量"""
        velocities = {}
        for param in parameter_ranges:
            if param.data_type in ["int", "float"]:
                range_size = param.max_value - param.min_value
                velocities[param.name] = np.random.uniform(-range_size * 0.1, range_size * 0.1)
            else:
                velocities[param.name] = 0
        return velocities

    def _genetic_algorithm_evolution(self, population: List[Dict], fitness_scores: List[float],
                                   parameter_ranges: List[ParameterRange], mutation_rate: float) -> List[Dict]:
        """遗传算法进化"""
        # 锦标赛选择
        new_population = []
        for _ in range(len(population)):
            tournament_size = 3
            tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            winner_idx = tournament_indices[np.argmax(tournament_fitness)]

            new_population.append(population[winner_idx].copy())

        # 交叉和变异
        for i in range(0, len(new_population), 2):
            if i + 1 < len(new_population):
                # 单点交叉
                crossover_point = np.random.randint(1, len(parameter_ranges))
                for j in range(crossover_point, len(parameter_ranges)):
                    param_name = parameter_ranges[j].name
                    new_population[i][param_name], new_population[i+1][param_name] = \
                        new_population[i+1][param_name], new_population[i][param_name]

                # 变异
                for individual in [new_population[i], new_population[i+1]]:
                    if np.random.random() < mutation_rate:
                        param = np.random.choice(parameter_ranges)
                        if param.data_type == "int":
                            individual[param.name] = np.random.randint(param.min_value, param.max_value + 1)
                        elif param.data_type == "float":
                            individual[param.name] = np.random.uniform(param.min_value, param.max_value)

        return new_population

    def _generate_bayesian_suggestion(self, history: List[Dict], parameter_ranges: List[ParameterRange]) -> Dict[str, Any]:
        """基于历史结果生成贝叶斯优化建议"""
        # 简化的贝叶斯优化建议生成
        if len(history) < 5:
            return self._generate_random_parameters(parameter_ranges)

        # 找到最佳参数组合
        best_result = max(history, key=lambda x: x["score"])
        best_params = best_result["parameters"]

        # 在最佳参数附近进行随机探索
        suggested_params = best_params.copy()
        for param in parameter_ranges:
            if param.data_type in ["int", "float"] and np.random.random() < 0.3:
                noise_range = (param.max_value - param.min_value) * 0.1
                suggested_params[param.name] += np.random.uniform(-noise_range, noise_range)
                suggested_params[param.name] = np.clip(
                    suggested_params[param.name], param.min_value, param.max_value
                )
                if param.data_type == "int":
                    suggested_params[param.name] = int(suggested_params[param.name])

        return suggested_params

    async def _calculate_performance_metrics(self, strategy_type: str, parameters: Dict[str, Any]) -> PerformanceMetrics:
        """计算性能指标"""
        # 生成缓存键
        cache_key = f"{strategy_type}_{hash(json.dumps(parameters, sort_keys=True))}"

        if cache_key in self.performance_cache:
            return self.performance_cache[cache_key]

        try:
            # 使用回测引擎计算性能指标
            backtest_config = {
                "strategy_type": strategy_type,
                "parameters": parameters,
                "start_date": datetime.now() - timedelta(days=365),
                "end_date": datetime.now()
            }

            # 这里应该调用实际的回测引擎
            # 为了演示，我们使用模拟数据
            performance = await self._simulate_performance_metrics(strategy_type, parameters)

            # 缓存结果
            self.performance_cache[cache_key] = performance

            return performance

        except Exception as e:
            self.logger.error(f"计算性能指标失败: {e}")
            # 返回默认性能指标
            return PerformanceMetrics(
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=1.0,
                calmar_ratio=0.0,
                volatility=0.0,
                sortino_ratio=0.0
            )

    async def _simulate_performance_metrics(self, strategy_type: str, parameters: Dict[str, Any]) -> PerformanceMetrics:
        """模拟性能指标计算"""
        import random

        # 基于策略类型和参数生成合理的性能指标
        base_return = random.uniform(-0.2, 0.4)
        base_volatility = random.uniform(0.1, 0.3)

        # 参数调整影响
        param_influence = sum(1 for param in parameters.values() if param > 0) * 0.01

        total_return = base_return + param_influence
        volatility = base_volatility - param_influence * 0.1
        max_drawdown = -abs(total_return) * random.uniform(0.5, 1.5)

        # 计算衍生指标
        sharpe_ratio = total_return / volatility if volatility > 0 else 0
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
        win_rate = max(0.3, min(0.8, 0.5 + sharpe_ratio * 0.1))
        profit_factor = 1 + abs(total_return) * random.uniform(1, 3)
        sortino_ratio = total_return / (volatility * random.uniform(0.7, 1.0)) if volatility > 0 else 0

        return PerformanceMetrics(
            total_return=total_return * 100,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown * 100,
            win_rate=win_rate * 100,
            profit_factor=profit_factor,
            calmar_ratio=calmar_ratio,
            volatility=volatility * 100,
            sortino_ratio=sortino_ratio
        )

    def _calculate_objective_score(self, objective: ObjectiveType, performance: PerformanceMetrics) -> float:
        """计算目标函数得分"""
        if objective == ObjectiveType.MAXIMIZE_SHARPE:
            return performance.sharpe_ratio
        elif objective == ObjectiveType.MAXIMIZE_RETURN:
            return performance.total_return
        elif objective == ObjectiveType.MINIMIZE_RISK:
            return -performance.max_drawdown
        elif objective == ObjectiveType.MAXIMIZE_CALMAR:
            return performance.calmar_ratio
        elif objective == ObjectiveType.MAXIMIZE_WIN_RATE:
            return performance.win_rate
        else:
            return performance.sharpe_ratio

    def _generate_optimization_summary(self, task: OptimizationTask) -> Dict[str, Any]:
        """生成优化摘要"""
        if not task.results:
            return {}

        scores = [result["score"] for result in task.results]
        performances = [result["performance"] for result in task.results]

        return {
            "total_iterations": len(task.results),
            "best_score": max(scores),
            "worst_score": min(scores),
            "average_score": np.mean(scores),
            "score_std": np.std(scores),
            "optimization_efficiency": len([s for s in scores if s > np.mean(scores)]) / len(scores),
            "parameter_sensitivity": self._calculate_parameter_sensitivity(task.results),
            "convergence_iteration": self._find_convergence_iteration(scores)
        }

    def _calculate_parameter_sensitivity(self, results: List[Dict]) -> Dict[str, float]:
        """计算参数敏感性"""
        if len(results) < 10:
            return {}

        # 分析参数变化对性能的影响
        parameter_names = set()
        for result in results:
            parameter_names.update(result["parameters"].keys())

        sensitivity = {}
        for param in parameter_names:
            param_values = [result["parameters"].get(param, 0) for result in results]
            scores = [result["score"] for result in results]

            if len(set(param_values)) > 1:
                correlation = np.corrcoef(param_values, scores)[0, 1]
                sensitivity[param] = abs(correlation) if not np.isnan(correlation) else 0.0
            else:
                sensitivity[param] = 0.0

        return sensitivity

    def _find_convergence_iteration(self, scores: List[float]) -> int:
        """找到收敛迭代次数"""
        if len(scores) < 10:
            return len(scores)

        # 计算移动平均
        window_size = max(5, len(scores) // 10)
        moving_avg = []
        for i in range(window_size, len(scores)):
            avg = np.mean(scores[i-window_size:i])
            moving_avg.append(avg)

        # 找到改进小于阈值的点
        threshold = np.std(moving_avg) * 0.1
        for i in range(1, len(moving_avg)):
            if abs(moving_avg[i] - moving_avg[i-1]) < threshold:
                return i + window_size

        return len(scores)

    def _get_default_parameters(self, strategy_type: str) -> List[ParameterRange]:
        """获取策略默认参数范围"""
        parameter_configs = {
            "direct_rsi": [
                ParameterRange("rsi_period", 5, 30, 1, "int"),
                ParameterRange("oversold_threshold", 20, 40, 1, "int"),
                ParameterRange("overbought_threshold", 60, 80, 1, "int"),
                ParameterRange("volume_weight", 0.0, 1.0, 0.1, "float")
            ],
            "sentiment_momentum": [
                ParameterRange("fast_period", 5, 20, 1, "int"),
                ParameterRange("slow_period", 15, 40, 1, "int"),
                ParameterRange("signal_period", 5, 15, 1, "int"),
                ParameterRange("momentum_threshold", 0.01, 0.1, 0.01, "float")
            ],
            "composite_index": [
                ParameterRange("bb_period", 10, 30, 1, "int"),
                ParameterRange("bb_std", 1.5, 3.0, 0.1, "float"),
                ParameterRange("weight_sentiment", 0.0, 1.0, 0.1, "float"),
                ParameterRange("weight_technical", 0.0, 1.0, 0.1, "float")
            ],
            "volatility_adjusted": [
                ParameterRange("volatility_window", 10, 30, 1, "int"),
                ParameterRange("volume_weight", 0.0, 1.0, 0.1, "float"),
                ParameterRange("volatility_threshold", 0.1, 0.5, 0.05, "float"),
                ParameterRange("adjustment_factor", 0.5, 2.0, 0.1, "float")
            ]
        }

        return parameter_configs.get(strategy_type, [])

    def _get_current_parameters(self, strategy_type: str) -> Dict[str, Any]:
        """获取当前参数值"""
        # 这里应该从实际的策略配置中获取
        default_values = {
            "direct_rsi": {"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70, "volume_weight": 0.5},
            "sentiment_momentum": {"fast_period": 12, "slow_period": 26, "signal_period": 9, "momentum_threshold": 0.05},
            "composite_index": {"bb_period": 20, "bb_std": 2.0, "weight_sentiment": 0.6, "weight_technical": 0.4},
            "volatility_adjusted": {"volatility_window": 20, "volume_weight": 0.3, "volatility_threshold": 0.25, "adjustment_factor": 1.0}
        }

        return default_values.get(strategy_type, {})

    async def _validate_parameters(self, strategy_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        default_params = self._get_default_parameters(strategy_type)
        validated_params = {}

        for param_range in default_params:
            param_name = param_range.name
            param_value = parameters.get(param_name)

            if param_value is None:
                raise ValueError(f"参数 {param_name} 不能为空")

            # 类型验证
            if param_range.data_type == "int":
                try:
                    param_value = int(param_value)
                except ValueError:
                    raise ValueError(f"参数 {param_name} 必须为整数")
            elif param_range.data_type == "float":
                try:
                    param_value = float(param_value)
                except ValueError:
                    raise ValueError(f"参数 {param_name} 必须为浮点数")

            # 范围验证
            if param_value < param_range.min_value or param_value > param_range.max_value:
                raise ValueError(
                    f"参数 {param_name} 必须在 {param_range.min_value} 到 {param_range.max_value} 之间"
                )

            validated_params[param_name] = param_value

        return validated_params

    async def _calculate_performance_impact(self, strategy_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """计算参数变更的性能影响"""
        current_params = self._get_current_parameters(strategy_type)
        current_performance = await self._calculate_performance_metrics(strategy_type, current_params)
        new_performance = await self._calculate_performance_metrics(strategy_type, parameters)

        return {
            "current_performance": asdict(current_performance),
            "new_performance": asdict(new_performance),
            "performance_change": {
                "total_return_change": new_performance.total_return - current_performance.total_return,
                "sharpe_ratio_change": new_performance.sharpe_ratio - current_performance.sharpe_ratio,
                "max_drawdown_change": new_performance.max_drawdown - current_performance.max_drawdown,
                "win_rate_change": new_performance.win_rate - current_performance.win_rate
            },
            "recommendation": self._generate_parameter_change_recommendation(current_performance, new_performance)
        }

    def _generate_parameter_change_recommendation(self, current: PerformanceMetrics, new: PerformanceMetrics) -> str:
        """生成参数变更建议"""
        if new.sharpe_ratio > current.sharpe_ratio * 1.1:
            return "强烈推荐：显著提升风险调整收益"
        elif new.sharpe_ratio > current.sharpe_ratio:
            return "推荐：改善风险调整收益"
        elif new.total_return > current.total_return * 1.2:
            return "谨慎考虑：提升收益但增加风险"
        elif new.max_drawdown < current.max_drawdown * 0.8:
            return "推荐：降低最大回撤风险"
        else:
            return "不推荐：性能指标恶化"

    def _save_parameter_history(self, strategy_type: str, parameters: Dict[str, Any], performance_impact: Dict[str, Any]):
        """保存参数历史"""
        if strategy_type not in self.parameter_history:
            self.parameter_history[strategy_type] = []

        history_record = {
            "timestamp": datetime.now().isoformat(),
            "parameters": parameters,
            "performance_impact": performance_impact
        }

        self.parameter_history[strategy_type].append(history_record)

        # 保留最近1000条记录
        if len(self.parameter_history[strategy_type]) > 1000:
            self.parameter_history[strategy_type] = self.parameter_history[strategy_type][-1000:]

    def _analyze_parameter_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析参数趋势"""
        if len(history) < 5:
            return {}

        # 分析参数使用频率
        param_frequency = {}
        param_trends = {}

        # 获取所有参数名
        if history:
            param_names = set(history[0]["parameters"].keys())
        else:
            return {}

        for param_name in param_names:
            values = [record["parameters"].get(param_name, 0) for record in history]
            param_frequency[param_name] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": min(values),
                "max": max(values),
                "current": values[-1] if values else 0
            }

            # 计算趋势
            if len(values) >= 10:
                recent_values = values[-10:]
                earlier_values = values[:-10]
                trend = np.mean(recent_values) - np.mean(earlier_values)
                param_trends[param_name] = {
                    "trend": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable",
                    "trend_strength": abs(trend)
                }

        return {
            "frequency": param_frequency,
            "trends": param_trends,
            "total_changes": len(history)
        }

    def _generate_parameter_recommendation(self, ranked_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成参数建议"""
        if not ranked_results:
            return {"recommendation": "无足够数据生成建议"}

        best_result = ranked_results[0]
        second_best = ranked_results[1] if len(ranked_results) > 1 else None

        recommendation = {
            "best_parameters": best_result["parameters"],
            "expected_performance": best_result["performance"],
            "confidence": "high" if len(ranked_results) > 5 else "medium",
            "improvement_potential": 0.0
        }

        if second_best:
            improvement = best_result["performance"]["sharpe_ratio"] - second_best["performance"]["sharpe_ratio"]
            recommendation["improvement_potential"] = improvement
            recommendation["second_best"] = second_best

        return recommendation

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        import uuid
        return f"opt_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

    def _parse_parameter_ranges(self, parameter_configs: List[Dict]) -> List[ParameterRange]:
        """解析参数范围配置"""
        parameters = []
        for config in parameter_configs:
            parameters.append(ParameterRange(
                name=config["name"],
                min_value=config["min_value"],
                max_value=config["max_value"],
                step=config.get("step"),
                data_type=config.get("data_type", "float"),
                categories=config.get("categories")
            ))
        return parameters

    async def _broadcast_parameter_update(self, strategy_type: str, parameters: Dict[str, Any], performance_impact: Dict[str, Any]):
        """广播参数更新"""
        message = {
            "type": "parameter_update",
            "strategy_type": strategy_type,
            "parameters": parameters,
            "performance_impact": performance_impact,
            "timestamp": datetime.now().isoformat()
        }

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def _broadcast_task_update(self, task: OptimizationTask):
        """广播任务更新"""
        message = {
            "type": "task_update",
            "task": asdict(task)
        }

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def _send_strategy_optimization_status(self, websocket: WebSocket, strategy_type: str):
        """发送策略优化状态"""
        strategy_tasks = [
            task for task in self.optimization_tasks.values()
            if task.strategy_type == strategy_type
        ]

        await websocket.send_json({
            "type": "strategy_optimization_status",
            "strategy_type": strategy_type,
            "tasks": [asdict(task) for task in strategy_tasks]
        })


# 创建全局实例
_parameter_optimization_api: Optional[ParameterOptimizationAPI] = None


def get_parameter_optimization_api() -> ParameterOptimizationAPI:
    """获取参数优化API实例"""
    global _parameter_optimization_api
    if _parameter_optimization_api is None:
        _parameter_optimization_api = ParameterOptimizationAPI()
    return _parameter_optimization_api