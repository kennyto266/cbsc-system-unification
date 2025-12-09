#!/usr / bin / env python3
"""
Multi - Objective Portfolio Optimization System
多目标投资组合优化系统

Professional multi - objective portfolio optimization with advanced features:
- Multiple optimization algorithms (NSGA - II, SPEA2, MOEA / D)
- Interactive Pareto frontier visualization
- Preference - based optimization
- Sensitivity and robustness analysis
- Portfolio rebalancing with transaction costs
- Custom objective function integration
- Real - time optimization monitoring
"""

import logging
import time
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

try:
    from scipy.optimize import differential_evolution, minimize
    from scipy.spatial.distance import euclidean
    from scipy.stats import norm, t

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Some features may not work")

try:
    from pymoo.algorithms.moo.moead import MOEAD
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.algorithms.moo.spea2 import SPEA2
    from pymoo.factory import get_crossover, get_mutation, get_sampling, get_selection
    from pymoo.model.problem import Problem
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.default_operators import set_parents
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.sampling.rnd import IntegerRandomSampling
    from pymoo.optimize import minimize

    PYMOO_AVAILABLE = True
except ImportError:
    PYMOO_AVAILABLE = False
    logging.warning("PyMOO not available. Using custom algorithms")

try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit - learn not available. Some features may not work")

from .mpt_optimizer import MPTOptimizer, OptimizationResult
from .objective_functions import (
    ObjectiveConfig,
    ObjectiveFactory,
    PortfolioObjective,
    SharpeRatioObjective,
    TradingCostObjective,
    VarianceObjective,
)
from .pareto_frontier import (
    ParetoConfig,
    ParetoFrontier,
    ParetoFrontierCalculator,
    ParetoPoint,
)
from .risk_parity_optimizer import RiskParityOptimizer, RiskParityResult

logger = logging.getLogger(__name__)


@dataclass
class MultiObjectiveConfig:
    """多目标优化配置"""

    # 基本参数
    risk_free_rate: float = 0.03  # 无风险利率
    trading_days_per_year: int = 252  # 交易日数

    # 算法参数
    algorithm: str = "nsga2"  # nsga2, spea2, moead, weighted_sum
    population_size: int = 100  # 种群大小
    n_generations: int = 100  # 迭代次数

    # 优化参数
    crossover_prob: float = 0.9  # 交叉概率
    mutation_prob: float = 1.0 / 20  # 变异概率 (1 / n_genes)
    eta_crossover: float = 20  # 交叉分布参数
    eta_mutation: float = 20  # 变异分布参数

    # 约束条件
    min_weight: float = 0.0  # 最小权重
    max_weight: float = 1.0  # 最大权重
    weight_sum: float = 1.0  # 权重总和

    # 交易成本
    trading_cost: float = 0.001  # 交易成本率
    rebalance_threshold: float = 0.05  # 再平衡阈值

    # 偏好参数
    preference_weights: Optional[List[float]] = None  # 目标函数偏好权重
    aspiration_levels: Optional[List[float]] = None  # 期望水平
    reservation_levels: Optional[List[float]] = None  # 保留水平

    # 鲁棒性
    robust_samples: int = 1000  # 鲁棒性分析样本数
    confidence_interval: float = 0.95  # 置信区间

    # 输出
    save_pareto_frontier: bool = True  # 保存帕累托边界
    save_optimization_history: bool = True  # 保存优化历史
    interactive_plots: bool = True  # 交互式图表


@dataclass
class OptimizationHistory:
    """优化历史"""

    generation: int  # 迭代次数
    objectives_values: List[np.ndarray]  # 目标函数值
    best_solutions: List[ParetoPoint]  # 最优解
    hypervolume: float  # 超体积指标
    convergence_metrics: Dict[str, float]  # 收敛指标
    diversity_metrics: Dict[str, float]  # 多样性指标
    timestamp: str  # 时间戳


@dataclass
class PreferenceResult:
    """偏好优化结果"""

    preferred_solution: ParetoPoint  # 偏好解
    preference_method: str  # 偏好方法
    satisfaction_level: float  # 满意度
    trade_off_analysis: Dict[str, Any]  # 权衡分析
    sensitivity_analysis: Dict[str, float]  # 敏感性分析


class MultiObjectiveOptimizer:
    """多目标投资组合优化引擎"""

    def __init__(self, config: Optional[MultiObjectiveConfig] = None):
        """初始化多目标优化引擎"""
        self.config = config or MultiObjectiveConfig()
        self.objective_factory = ObjectiveFactory()
        self.pareto_calculator = ParetoFrontierCalculator()

        # 初始化优化器组件
        self.mpt_optimizer = MPTOptimizer()
        self.risk_parity_optimizer = RiskParityOptimizer()

        # 优化历史
        self.optimization_history: List[OptimizationHistory] = []

        logger.info(
            f"Multi - Objective Optimizer initialized with {self.config.algorithm} algorithm"
        )

    def optimize_portfolio(
        self,
        returns: pd.DataFrame,
        objectives: List[str],
        objective_configs: Optional[List[ObjectiveConfig]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        custom_objectives: Optional[List[PortfolioObjective]] = None,
    ) -> ParetoFrontier:
        """
        多目标投资组合优化

        Args:
            returns: 资产回报率矩阵
            objectives: 目标函数名称列表
            objective_configs: 目标函数配置列表
            constraints: 约束条件
            custom_objectives: 自定义目标函数列表

        Returns:
            ParetoFrontier: 帕累托边界
        """
        start_time = time.time()
        logger.info(
            f"Starting multi - objective optimization with {len(objectives)} objectives"
        )

        try:
            # 准备目标函数
            if custom_objectives:
                objective_instances = custom_objectives
            else:
                objective_instances = self._prepare_objectives(
                    objectives, objective_configs
                )

            # 验证输入
            self._validate_inputs(returns, objective_instances, constraints)

            # 选择优化算法
            if self.config.algorithm == "nsga2" and PYMOO_AVAILABLE:
                pareto_frontier = self._nsga2_optimization(
                    returns, objective_instances, constraints
                )
            elif self.config.algorithm == "spea2" and PYMOO_AVAILABLE:
                pareto_frontier = self._spea2_optimization(
                    returns, objective_instances, constraints
                )
            elif self.config.algorithm == "moead" and PYMOO_AVAILABLE:
                pareto_frontier = self._moead_optimization(
                    returns, objective_instances, constraints
                )
            else:
                pareto_frontier = self._weighted_sum_optimization(
                    returns, objective_instances, constraints
                )

            # 后处理分析
            self._post_process_analysis(pareto_frontier, objective_instances)

            logger.info(
                f"Multi - objective optimization completed in {time.time() - start_time:.3f}s"
            )
            return pareto_frontier

        except Exception as e:
            logger.error(f"Multi - objective optimization failed: {e}")
            raise

    def preference_optimization(
        self,
        returns: pd.DataFrame,
        objectives: List[str],
        preference_method: str = "weighted_sum",
        preference_weights: Optional[List[float]] = None,
        aspiration_levels: Optional[List[float]] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> PreferenceResult:
        """
        基于偏好的优化

        Args:
            returns: 资产回报率矩阵
            objectives: 目标函数列表
            preference_method: 偏好方法
            preference_weights: 偏好权重
            aspiration_levels: 期望水平
            constraints: 约束条件

        Returns:
            PreferenceResult: 偏好优化结果
        """
        start_time = time.time()
        logger.info(f"Starting preference - based optimization using {preference_method}")

        try:
            # 准备目标函数
            objective_instances = self._prepare_objectives(objectives)

            # 计算帕累托边界
            pareto_frontier = self.optimize_portfolio(
                returns, objectives, constraints = constraints
            )

            # 应用偏好
            if preference_method == "weighted_sum":
                preferred_solution = self._weighted_sum_preference(
                    pareto_frontier,
                    preference_weights or self.config.preference_weights,
                )
            elif preference_method == "goal_programming":
                preferred_solution = self._goal_programming_preference(
                    pareto_frontier, aspiration_levels or self.config.aspiration_levels
                )
            elif preference_method == "lexicographic":
                preferred_solution = self._lexicographic_preference(
                    pareto_frontier,
                    preference_weights or self.config.preference_weights,
                )
            elif preference_method == "compromise_programming":
                preferred_solution = self._compromise_programming_preference(
                    pareto_frontier, aspiration_levels or self.config.aspiration_levels
                )
            else:
                raise ValueError(f"Unknown preference method: {preference_method}")

            # 计算满意度
            satisfaction_level = self._calculate_satisfaction(
                preferred_solution,
                objective_instances,
                preference_weights,
                aspiration_levels,
            )

            # 权衡分析
            trade_off_analysis = self._analyze_trade_offs(
                preferred_solution, pareto_frontier, objective_instances
            )

            # 敏感性分析
            sensitivity_analysis = self._sensitivity_analysis(
                returns, preferred_solution, objective_instances
            )

            result = PreferenceResult(
                preferred_solution = preferred_solution,
                preference_method = preference_method,
                satisfaction_level = satisfaction_level,
                trade_off_analysis = trade_off_analysis,
                sensitivity_analysis = sensitivity_analysis,
            )

            logger.info(
                f"Preference optimization completed in {time.time() - start_time:.3f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Preference optimization failed: {e}")
            raise

    def robust_optimization(
        self,
        returns: pd.DataFrame,
        objectives: List[str],
        uncertainty_scenarios: Optional[List[pd.DataFrame]] = None,
        confidence_level: Optional[float] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> ParetoFrontier:
        """
        鲁棒性优化

        Args:
            returns: 基准资产回报率矩阵
            objectives: 目标函数列表
            uncertainty_scenarios: 不确定性情景
            confidence_level: 置信水平
            constraints: 约束条件

        Returns:
            ParetoFrontier: 鲁棒帕累托边界
        """
        start_time = time.time()
        logger.info("Starting robust multi - objective optimization")

        try:
            # 生成不确定性情景
            if uncertainty_scenarios is None:
                uncertainty_scenarios = self._generate_uncertainty_scenarios(returns)

            confidence_level = confidence_level or self.config.confidence_interval

            # 在每个情景下优化
            scenario_frontiers = []
            for i, scenario_returns in enumerate(uncertainty_scenarios):
                logger.info(f"Optimizing scenario {i + 1}/{len(uncertainty_scenarios)}")
                frontier = self.optimize_portfolio(
                    scenario_returns, objectives, constraints = constraints
                )
                scenario_frontiers.append(frontier)

            # 计算鲁棒帕累托边界
            robust_frontier = self._compute_robust_frontier(
                scenario_frontiers, confidence_level, objectives
            )

            logger.info(
                f"Robust optimization completed in {time.time() - start_time:.3f}s"
            )
            return robust_frontier

        except Exception as e:
            logger.error(f"Robust optimization failed: {e}")
            raise

    def dynamic_rebalancing(
        self,
        returns_history: pd.DataFrame,
        objectives: List[str],
        rebalance_frequency: str = "monthly",
        window_size: int = 252,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, ParetoPoint]]:
        """
        动态再平衡优化

        Args:
            returns_history: 历史回报率数据
            objectives: 目标函数列表
            rebalance_frequency: 再平衡频率
            window_size: 优化窗口大小
            constraints: 约束条件

        Returns:
            List[Tuple[str, ParetoPoint]]: 再平衡结果列表
        """
        start_time = time.time()
        logger.info(
            f"Starting dynamic rebalancing with {rebalance_frequency} frequency"
        )

        try:
            # 确定再平衡日期
            rebalance_dates = self._get_rebalance_dates(
                returns_history, rebalance_frequency
            )

            rebalancing_results = []
            previous_weights = None

            for rebalance_date in rebalance_dates:
                # 获取优化窗口数据
                window_data = self._get_rebalance_window(
                    returns_history, rebalance_date, window_size
                )

                if len(window_data) < window_size // 2:  # 数据不足
                    continue

                logger.info(f"Rebalancing on {rebalance_date}")

                # 优化
                pareto_frontier = self.optimize_portfolio(
                    window_data, objectives, constraints = constraints
                )

                # 选择最优解（考虑交易成本）
                optimal_solution = self._select_optimal_with_costs(
                    pareto_frontier, previous_weights, objectives
                )

                rebalancing_results.append((rebalance_date, optimal_solution))
                previous_weights = optimal_solution.weights

            logger.info(
                f"Dynamic rebalancing completed in {time.time() - start_time:.3f}s"
            )
            return rebalancing_results

        except Exception as e:
            logger.error(f"Dynamic rebalancing failed: {e}")
            raise

    def _prepare_objectives(
        self,
        objectives: List[str],
        objective_configs: Optional[List[ObjectiveConfig]] = None,
    ) -> List[PortfolioObjective]:
        """准备目标函数实例"""
        objective_instances = []

        for i, obj_name in enumerate(objectives):
            config = (
                objective_configs[i]
                if objective_configs and i < len(objective_configs)
                else None
            )
            objective = self.objective_factory.create_objective(obj_name, config)
            objective_instances.append(objective)

        return objective_instances

    def _validate_inputs(
        self,
        returns: pd.DataFrame,
        objectives: List[PortfolioObjective],
        constraints: Optional[Dict[str, Any]],
    ) -> None:
        """验证输入参数"""
        if len(returns) == 0:
            raise ValueError("Returns data is empty")

        if len(objectives) == 0:
            raise ValueError("No objectives specified")

        returns.shape[1]
        for objective in objectives:
            # 目标函数验证
            pass  # 可以添加更多验证逻辑

    def _nsga2_optimization(
        self,
        returns: pd.DataFrame,
        objectives: List[PortfolioObjective],
        constraints: Optional[Dict[str, Any]],
    ) -> ParetoFrontier:
        """NSGA - II算法实现"""
        if not PYMOO_AVAILABLE:
            raise ImportError("PyMOO is required for NSGA - II optimization")

        class PortfolioProblem(Problem):
            def __init__(self, returns, objectives, config):
                super().__init__(
                    n_var = returns.shape[1],
                    n_obj = len(objectives),
                    n_constr = 1,  # 权重和约束
                    xl = config.min_weight,
                    xu = config.max_weight,
                )
                self.returns = returns
                self.objectives = objectives
                self.config = config

            def _evaluate(self, X, out, *args, **kwargs):
                n_solutions = X.shape[0]
                n_objectives = len(self.objectives)

                F = np.zeros((n_solutions, n_objectives))
                G = np.zeros(n_solutions)

                for i in range(n_solutions):
                    weights = X[i]
                    weights = weights / np.sum(weights)  # 归一化

                    for j, objective in enumerate(self.objectives):
                        F[i, j] = objective.evaluate(weights, self.returns)

                    # 约束：权重和应为1
                    G[i] = np.sum(weights) - 1.0

                out["F"] = F
                out["G"] = G

        # 定义问题
        problem = PortfolioProblem(returns, objectives, self.config)

        # 设置算法参数
        algorithm = NSGA2(
            pop_size = self.config.population_size,
            n_offsprings = 10,
            sampling = get_sampling("real_random"),
            crossover = get_crossover(
                "real_sbx",
                prob = self.config.crossover_prob,
                eta = self.config.eta_crossover,
            ),
            mutation = get_mutation("real_pm", eta = self.config.eta_mutation),
            eliminate_duplicates = True,
        )

        # 运行优化
        res = minimize(
            problem,
            algorithm,
            termination=("n_gen", self.config.n_generations),
            seed = 42,
            verbose = False,
        )

        # 转换结果为帕累托边界
        return self._convert_pymoo_results(res, returns, objectives)

    def _spea2_optimization(
        self,
        returns: pd.DataFrame,
        objectives: List[PortfolioObjective],
        constraints: Optional[Dict[str, Any]],
    ) -> ParetoFrontier:
        """SPEA2算法实现"""
        if not PYMOO_AVAILABLE:
            raise ImportError("PyMOO is required for SPEA2 optimization")

        class PortfolioProblem(Problem):
            def __init__(self, returns, objectives, config):
                super().__init__(
                    n_var = returns.shape[1],
                    n_obj = len(objectives),
                    n_constr = 1,
                    xl = config.min_weight,
                    xu = config.max_weight,
                )
                self.returns = returns
                self.objectives = objectives
                self.config = config

            def _evaluate(self, X, out, *args, **kwargs):
                n_solutions = X.shape[0]
                n_objectives = len(self.objectives)

                F = np.zeros((n_solutions, n_objectives))
                G = np.zeros(n_solutions)

                for i in range(n_solutions):
                    weights = X[i]
                    weights = weights / np.sum(weights)

                    for j, objective in enumerate(self.objectives):
                        F[i, j] = objective.evaluate(weights, self.returns)

                    G[i] = np.sum(weights) - 1.0

                out["F"] = F
                out["G"] = G

        problem = PortfolioProblem(returns, objectives, self.config)

        algorithm = SPEA2(
            pop_size = self.config.population_size,
            n_offsprings = 10,
            sampling = get_sampling("real_random"),
            crossover = get_crossover(
                "real_sbx",
                prob = self.config.crossover_prob,
                eta = self.config.eta_crossover,
            ),
            mutation = get_mutation("real_pm", eta = self.config.eta_mutation),
        )

        res = minimize(
            problem,
            algorithm,
            termination=("n_gen", self.config.n_generations),
            seed = 42,
            verbose = False,
        )

        return self._convert_pymoo_results(res, returns, objectives)

    def _moead_optimization(
        self,
        returns: pd.DataFrame,
        objectives: List[PortfolioObjective],
        constraints: Optional[Dict[str, Any]],
    ) -> ParetoFrontier:
        """MOEA / D算法实现"""
        if not PYMOO_AVAILABLE:
            raise ImportError("PyMOO is required for MOEA / D optimization")

        class PortfolioProblem(Problem):
            def __init__(self, returns, objectives, config):
                super().__init__(
                    n_var = returns.shape[1],
                    n_obj = len(objectives),
                    n_constr = 1,
                    xl = config.min_weight,
                    xu = config.max_weight,
                )
                self.returns = returns
                self.objectives = objectives
                self.config = config

            def _evaluate(self, X, out, *args, **kwargs):
                n_solutions = X.shape[0]
                n_objectives = len(self.objectives)

                F = np.zeros((n_solutions, n_objectives))
                G = np.zeros(n_solutions)

                for i in range(n_solutions):
                    weights = X[i]
                    weights = weights / np.sum(weights)

                    for j, objective in enumerate(self.objectives):
                        F[i, j] = objective.evaluate(weights, self.returns)

                    G[i] = np.sum(weights) - 1.0

                out["F"] = F
                out["G"] = G

        problem = PortfolioProblem(returns, objectives, self.config)

        # 生成参考方向
        ref_dirs = get_reference_directions(
            "das - dennis", len(objectives), n_partitions = 12
        )

        algorithm = MOEAD(
            ref_dirs = ref_dirs,
            n_neighbors = 15,
            prob_neighbor_mating = 0.9,
            sampling = get_sampling("real_random"),
            crossover = get_crossover("real_sbx", prob = 0.9, eta = 30),
            mutation = get_mutation("real_pm", eta = 20),
            eliminate_duplicates = True,
        )

        res = minimize(
            problem,
            algorithm,
            termination=("n_gen", self.config.n_generations),
            seed = 42,
            verbose = False,
        )

        return self._convert_pymoo_results(res, returns, objectives)

    def _weighted_sum_optimization(
        self,
        returns: pd.DataFrame,
        objectives: List[PortfolioObjective],
        constraints: Optional[Dict[str, Any]],
    ) -> ParetoFrontier:
        """加权和优化方法"""
        logger.info("Using weighted sum optimization method")

        # 生成权重组合
        n_objectives = len(objectives)
        weight_combinations = self._generate_objective_weights(
            n_objectives, self.config.population_size
        )

        points = []
        n_assets = returns.shape[1]

        for obj_weights in weight_combinations:
            # 定义加权目标函数
            def weighted_objective(portfolio_weights):
                total_objective = 0.0
                for obj_weight, objective in zip(obj_weights, objectives):
                    value = objective.evaluate(portfolio_weights, returns)
                    # 根据目标方向调整符号
                    if objective.direction == "maximize":
                        value = -value
                    total_objective += obj_weight * value
                return total_objective

            # 约束优化
            if SCIPY_AVAILABLE:
                constraints_list = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
                bounds = [
                    (self.config.min_weight, self.config.max_weight)
                    for _ in range(n_assets)
                ]
                initial_weights = np.ones(n_assets) / n_assets

                result = minimize(
                    weighted_objective,
                    initial_weights,
                    method="SLSQP",
                    bounds = bounds,
                    constraints = constraints_list,
                    options={"maxiter": 1000},
                )

                if result.success:
                    weights = result.x
                    weights = weights / np.sum(weights)
                else:
                    weights = initial_weights
            else:
                # 简单随机搜索作为后备
                weights = np.random.dirichlet(np.ones(n_assets))

            # 计算所有目标函数值
            objectives_values = np.array(
                [obj.evaluate(weights, returns) for obj in objectives]
            )

            point = ParetoPoint(
                weights = weights,
                objectives = objectives_values,
                asset_names = list(returns.columns),
                rank = 0,
                crowding_distance = 0.0,
                domination_count = 0,
                dominated_solutions=[],
            )
            points.append(point)

        # 计算帕累托排序和拥挤距离
        points = self.pareto_calculator._non_dominated_sorting(points, objectives)
        points = self.pareto_calculator._calculate_crowding_distance(points)

        # 识别膝点
        knee_points = self.pareto_calculator._identify_knee_points(points)

        # 创建帕累托边界
        frontier = ParetoFrontier(
            points = points,
            objective_names=[obj.name for obj in objectives],
            n_objectives = len(objectives),
            n_assets = n_assets,
            asset_names = list(returns.columns),
            knee_points = knee_points,
            calculation_time = 0.0,
            algorithm="weighted_sum",
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        return frontier

    def _generate_objective_weights(
        self, n_objectives: int, n_combinations: int
    ) -> List[List[float]]:
        """生成目标函数权重组合"""
        combinations = []

        if n_objectives == 2:
            # 两目标：均匀分割
            for i in range(n_combinations):
                w1 = i / (n_combinations - 1) if n_combinations > 1 else 0.5
                w2 = 1 - w1
                combinations.append([w1, w2])

        elif n_objectives == 3:
            # 三目标：使用简单网格
            n1 = int(np.cbrt(n_combinations))
            n2 = n1
            n3 = n1

            for i in range(n1):
                for j in range(n2):
                    for k in range(n3):
                        w1, w2, w3 = (
                            i / (n1 - 1) if n1 > 1 else 0,
                            j / (n2 - 1) if n2 > 1 else 0,
                            k / (n3 - 1) if n3 > 1 else 0,
                        )
                        total = w1 + w2 + w3
                        if total > 0:
                            combinations.append([w1 / total, w2 / total, w3 / total])

        else:
            # 更多目标：随机生成
            for _ in range(n_combinations):
                weights = np.random.exponential(1, n_objectives)
                weights = weights / np.sum(weights)
                combinations.append(weights.tolist())

        return combinations

    def _convert_pymoo_results(
        self, pymoo_results, returns: pd.DataFrame, objectives: List[PortfolioObjective]
    ) -> ParetoFrontier:
        """转换PyMOO结果为帕累托边界"""
        points = []

        for i in range(len(pymoo_results.X)):
            weights = pymoo_results.X[i]
            weights = weights / np.sum(weights)  # 归一化
            objectives_values = pymoo_results.F[i]

            point = ParetoPoint(
                weights = weights,
                objectives = objectives_values,
                asset_names = list(returns.columns),
                rank = 0,
                crowding_distance = 0.0,
                domination_count = 0,
                dominated_solutions=[],
            )
            points.append(point)

        # 计算帕累托排序和拥挤距离
        points = self.pareto_calculator._non_dominated_sorting(points, objectives)
        points = self.pareto_calculator._calculate_crowding_distance(points)

        # 识别膝点
        knee_points = self.pareto_calculator._identify_knee_points(points)

        # 创建帕累托边界
        frontier = ParetoFrontier(
            points = points,
            objective_names=[obj.name for obj in objectives],
            n_objectives = len(objectives),
            n_assets = returns.shape[1],
            asset_names = list(returns.columns),
            knee_points = knee_points,
            calculation_time = 0.0,
            algorithm = self.config.algorithm,
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        return frontier

    def _post_process_analysis(
        self, pareto_frontier: ParetoFrontier, objectives: List[PortfolioObjective]
    ) -> None:
        """后处理分析"""
        # 计算超体积
        hypervolume = self._calculate_hypervolume(pareto_frontier, objectives)

        # 计算收敛指标
        convergence_metrics = self._calculate_convergence_metrics(
            pareto_frontier, objectives
        )

        # 计算多样性指标
        diversity_metrics = self._calculate_diversity_metrics(pareto_frontier)

        # 保存优化历史
        history = OptimizationHistory(
            generation = self.config.n_generations,
            objectives_values=[p.objectives for p in pareto_frontier.points],
            best_solutions = pareto_frontier.points[:10],  # 前10个最优解
            hypervolume = hypervolume,
            convergence_metrics = convergence_metrics,
            diversity_metrics = diversity_metrics,
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.optimization_history.append(history)

    def _calculate_hypervolume(
        self, frontier: ParetoFrontier, objectives: List[PortfolioObjective]
    ) -> float:
        """计算超体积指标"""
        # 简化的超体积计算
        if frontier.n_objectives > 3:
            return 0.0  # 超体积计算在高维情况下复杂度高

        # 获取第一前端
        first_front = [p for p in frontier.points if p.rank == 0]
        if not first_front:
            return 0.0

        # 找到参考点（最差点）
        objectives_matrix = np.array([p.objectives for p in first_front])
        reference_point = np.max(objectives_matrix, axis = 0)

        # 简化的超体积计算（仅适用于二目标）
        if frontier.n_objectives == 2:
            # 按第一个目标排序
            sorted_points = sorted(first_front, key = lambda p: p.objectives[0])
            hypervolume = 0.0

            for i in range(len(sorted_points)):
                if i == 0:
                    width = reference_point[0] - sorted_points[i].objectives[0]
                else:
                    width = (
                        sorted_points[i - 1].objectives[0]
                        - sorted_points[i].objectives[0]
                    )

                height = reference_point[1] - sorted_points[i].objectives[1]
                hypervolume += width * height

            return hypervolume

        return 0.0

    def _calculate_convergence_metrics(
        self, frontier: ParetoFrontier, objectives: List[PortfolioObjective]
    ) -> Dict[str, float]:
        """计算收敛指标"""
        first_front = [p for p in frontier.points if p.rank == 0]
        if not first_front:
            return {}

        objectives_matrix = np.array([p.objectives for p in first_front])

        metrics = {}

        # 理想点距离
        ideal_point = np.min(objectives_matrix, axis = 0)
        distances_to_ideal = np.linalg.norm(objectives_matrix - ideal_point, axis = 1)
        metrics["avg_distance_to_ideal"] = np.mean(distances_to_ideal)
        metrics["min_distance_to_ideal"] = np.min(distances_to_ideal)

        # 解的分布
        if len(first_front) > 1:
            pairwise_distances = pdist(objectives_matrix)
            metrics["avg_pairwise_distance"] = np.mean(pairwise_distances)
            metrics["min_pairwise_distance"] = np.min(pairwise_distances)

        return metrics

    def _calculate_diversity_metrics(
        self, frontier: ParetoFrontier
    ) -> Dict[str, float]:
        """计算多样性指标"""
        first_front = [p for p in frontier.points if p.rank == 0]
        if not first_front:
            return {}

        objectives_matrix = np.array([p.objectives for p in first_front])

        metrics = {}

        # 拥挤距离统计
        crowding_distances = [p.crowding_distance for p in first_front]
        metrics["avg_crowding_distance"] = np.mean(crowding_distances)
        metrics["min_crowding_distance"] = np.min(
            [cd for cd in crowding_distances if cd != float("inf")]
        )

        # 空间分布度量
        if len(first_front) > 1:
            pairwise_distances = pdist(objectives_matrix)
            metrics["diversity_spread"] = np.std(pairwise_distances)

        return metrics

    def _generate_uncertainty_scenarios(
        self, returns: pd.DataFrame
    ) -> List[pd.DataFrame]:
        """生成不确定性情景"""
        scenarios = []

        # 基准情景（原始数据）
        scenarios.append(returns)

        # 情景1：增加波动性
        returns_high_vol = returns * 1.2
        scenarios.append(returns_high_vol)

        # 情景2：降低波动性
        returns_low_vol = returns * 0.8
        scenarios.append(returns_low_vol)

        # 情景3：偏移均值
        returns_shifted = returns + returns.std() * 0.1
        scenarios.append(returns_shifted)

        # 情景4：相关性变化（简化版本）
        if len(returns.columns) > 1:
            correlation_noise = np.random.normal(0, 0.1, returns.shape)
            returns_noisy = returns + correlation_noise
            scenarios.append(returns_noisy)

        return scenarios

    def _compute_robust_frontier(
        self,
        scenario_frontiers: List[ParetoFrontier],
        confidence_level: float,
        objectives: List[str],
    ) -> ParetoFrontier:
        """计算鲁棒帕累托边界"""
        # 收集所有情景的解
        all_solutions = []
        for frontier in scenario_frontiers:
            all_solutions.extend(frontier.points)

        # 按权重聚类相似解
        if not all_solutions:
            return ParetoFrontier(
                points=[],
                objective_names = objectives,
                n_objectives = len(objectives),
                n_assets = 0,
                asset_names=[],
                knee_points=[],
                calculation_time = 0.0,
                algorithm="robust",
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

        # 简化的聚类：使用权重相似性
        robust_solutions = []
        threshold = 0.1  # 权重差异阈值

        for solution in all_solutions:
            is_duplicate = False
            for robust_solution in robust_solutions:
                weight_diff = np.linalg.norm(solution.weights - robust_solution.weights)
                if weight_diff < threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                robust_solutions.append(solution)

        # 计算鲁棒目标函数值（各情景下的平均值）
        for solution in robust_solutions:
            robust_objectives = []
            for frontier in scenario_frontiers:
                # 找到最相似的解
                min_distance = float("inf")
                closest_objectives = None

                for other_solution in frontier.points:
                    distance = np.linalg.norm(solution.weights - other_solution.weights)
                    if distance < min_distance:
                        min_distance = distance
                        closest_objectives = other_solution.objectives

                if closest_objectives is not None:
                    robust_objectives.append(closest_objectives)

            if robust_objectives:
                solution.objectives = np.mean(robust_objectives, axis = 0)

        # 重新排序
        robust_solutions = self.pareto_calculator._non_dominated_sorting(
            robust_solutions, []
        )

        return ParetoFrontier(
            points = robust_solutions,
            objective_names = objectives,
            n_objectives = len(objectives),
            n_assets = robust_solutions[0].weights.shape[0] if robust_solutions else 0,
            asset_names = robust_solutions[0].asset_names if robust_solutions else [],
            knee_points=[],
            calculation_time = 0.0,
            algorithm="robust",
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def _get_rebalance_dates(
        self, returns_history: pd.DataFrame, frequency: str
    ) -> List[str]:
        """获取再平衡日期"""
        if frequency == "monthly":
            dates = returns_history.resample("M").last().index
        elif frequency == "quarterly":
            dates = returns_history.resample("Q").last().index
        elif frequency == "yearly":
            dates = returns_history.resample("Y").last().index
        else:
            dates = returns_history.index

        return [date.strftime("%Y-%m-%d") for date in dates]

    def _get_rebalance_window(
        self, returns_history: pd.DataFrame, rebalance_date: str, window_size: int
    ) -> pd.DataFrame:
        """获取再平衡窗口数据"""
        target_date = pd.to_datetime(rebalance_date)
        end_date = returns_history.index[returns_history.index <= target_date]

        if len(end_date) == 0:
            return pd.DataFrame()

        end_idx = returns_history.index.get_loc(end_date[-1])
        start_idx = max(0, end_idx - window_size + 1)

        return returns_history.iloc[start_idx : end_idx + 1]

    def _select_optimal_with_costs(
        self,
        frontier: ParetoFrontier,
        previous_weights: Optional[np.ndarray],
        objectives: List[str],
    ) -> ParetoPoint:
        """考虑交易成本的最优解选择"""
        if previous_weights is None or len(frontier.points) == 0:
            return frontier.points[0] if frontier.points else None

        # 计算每个解的调整后目标值
        best_solution = None
        best_score = float("inf")

        for solution in frontier.points:
            # 计算交易成本
            turnover = np.sum(np.abs(solution.weights - previous_weights)) / 2
            trading_cost = turnover * self.config.trading_cost

            # 选择第一个目标函数作为主要指标
            if len(solution.objectives) > 0:
                # 对于最小化目标，加上交易成本
                adjusted_objective = solution.objectives[0] + trading_cost

                if adjusted_objective < best_score:
                    best_score = adjusted_objective
                    best_solution = solution

        return best_solution or frontier.points[0]

    def _weighted_sum_preference(
        self, frontier: ParetoFrontier, preference_weights: Optional[List[float]]
    ) -> ParetoPoint:
        """加权和偏好选择"""
        if not preference_weights or len(frontier.points) == 0:
            return frontier.points[0] if frontier.points else None

        best_solution = None
        best_score = float("inf")

        for solution in frontier.points:
            # 计算加权和
            weighted_score = np.dot(solution.objectives, preference_weights)

            if weighted_score < best_score:
                best_score = weighted_score
                best_solution = solution

        return best_solution

    def _goal_programming_preference(
        self, frontier: ParetoFrontier, aspiration_levels: Optional[List[float]]
    ) -> ParetoPoint:
        """目标规划偏好选择"""
        if not aspiration_levels or len(frontier.points) == 0:
            return frontier.points[0] if frontier.points else None

        best_solution = None
        best_score = float("inf")

        for solution in frontier.points:
            # 计算到期望水平的偏差
            deviations = np.abs(solution.objectives - np.array(aspiration_levels))
            total_deviation = np.sum(deviations)

            if total_deviation < best_score:
                best_score = total_deviation
                best_solution = solution

        return best_solution

    def _lexicographic_preference(
        self, frontier: ParetoFrontier, preference_weights: Optional[List[float]]
    ) -> ParetoPoint:
        """词典式偏好选择"""
        if not preference_weights or len(frontier.points) == 0:
            return frontier.points[0] if frontier.points else None

        # 按权重排序目标优先级
        objective_priorities = sorted(
            range(len(preference_weights)),
            key = lambda i: preference_weights[i],
            reverse = True,
        )

        # 按优先级筛选
        remaining_solutions = frontier.points[:]

        for obj_idx in objective_priorities:
            if len(remaining_solutions) <= 1:
                break

            # 按当前目标排序
            remaining_solutions.sort(key = lambda s: s.objectives[obj_idx])

            # 保留前几个解（避免过早收敛）
            top_k = max(1, len(remaining_solutions) // 2)
            remaining_solutions = remaining_solutions[:top_k]

        return remaining_solutions[0] if remaining_solutions else frontier.points[0]

    def _compromise_programming_preference(
        self, frontier: ParetoFrontier, aspiration_levels: Optional[List[float]]
    ) -> ParetoPoint:
        """妥协规划偏好选择"""
        if not aspiration_levels or len(frontier.points) == 0:
            return frontier.points[0] if frontier.points else None

        # 找到理想点
        all_objectives = np.array([s.objectives for s in frontier.points])
        ideal_point = np.min(all_objectives, axis = 0)

        best_solution = None
        best_distance = float("inf")

        for solution in frontier.points:
            # 计算到理想点的距离
            distance = np.linalg.norm(solution.objectives - ideal_point)

            if distance < best_distance:
                best_distance = distance
                best_solution = solution

        return best_solution

    def _calculate_satisfaction(
        self,
        solution: ParetoPoint,
        objectives: List[PortfolioObjective],
        preference_weights: Optional[List[float]],
        aspiration_levels: Optional[List[float]],
    ) -> float:
        """计算满意度"""
        satisfaction = 0.5  # 默认中等满意度

        if preference_weights and aspiration_levels:
            # 基于期望水平的满意度
            for i, (obj_val, asp_level) in enumerate(
                zip(solution.objectives, aspiration_levels)
            ):
                obj_direction = objectives[i].direction
                weight = preference_weights[i] if i < len(preference_weights) else 1.0

                if obj_direction == "minimize":
                    if obj_val <= asp_level:
                        satisfaction += weight * (asp_level - obj_val) / asp_level
                    else:
                        satisfaction -= weight * (obj_val - asp_level) / asp_level
                else:  # maximize
                    if obj_val >= asp_level:
                        satisfaction += weight * (obj_val - asp_level) / asp_level
                    else:
                        satisfaction -= weight * (asp_level - obj_val) / asp_level

            satisfaction = max(0.0, min(1.0, satisfaction))

        return satisfaction

    def _analyze_trade_offs(
        self,
        solution: ParetoPoint,
        frontier: ParetoFrontier,
        objectives: List[PortfolioObjective],
    ) -> Dict[str, Any]:
        """分析权衡关系"""
        if len(frontier.points) < 3:
            return {}

        analysis = {}

        # 找到相邻解
        first_front = [p for p in frontier.points if p.rank == 0]
        if solution not in first_front:
            return {}

        # 按第一个目标排序
        sorted_solutions = sorted(first_front, key = lambda s: s.objectives[0])

        # 找到当前解的位置
        solution_idx = sorted_solutions.index(solution)
        n_objectives = len(objectives)

        # 计算权衡率
        trade_offs = {}
        if solution_idx > 0:
            prev_solution = sorted_solutions[solution_idx - 1]
            for i in range(n_objectives):
                for j in range(i + 1, n_objectives):
                    delta_i = solution.objectives[i] - prev_solution.objectives[i]
                    delta_j = solution.objectives[j] - prev_solution.objectives[j]

                    if abs(delta_j) > 1e - 8:
                        trade_offs[f"obj_{i}_vs_obj_{j}"] = delta_i / delta_j

        analysis["trade_off_rates"] = trade_offs

        # 计算改进潜力
        improvements = {}
        ideal_values = np.min([s.objectives for s in first_front], axis = 0)

        for i, obj_name in enumerate([f"objective_{i}" for i in range(n_objectives)]):
            current_value = solution.objectives[i]
            ideal_value = ideal_values[i]

            if abs(ideal_value) > 1e - 8:
                improvement_potential = (current_value - ideal_value) / abs(ideal_value)
                improvements[obj_name] = improvement_potential

        analysis["improvement_potential"] = improvements

        return analysis

    def _sensitivity_analysis(
        self,
        returns: pd.DataFrame,
        solution: ParetoPoint,
        objectives: List[PortfolioObjective],
    ) -> Dict[str, float]:
        """敏感性分析"""
        sensitivity = {}

        n_assets = len(solution.weights)
        epsilon = 1e - 4

        for i in range(n_assets):
            # 微调第i个资产的权重
            perturbed_weights = solution.weights.copy()
            perturbed_weights[i] += epsilon
            perturbed_weights = perturbed_weights / np.sum(perturbed_weights)

            # 计算目标函数值的变化
            original_values = solution.objectives.copy()
            perturbed_values = np.array(
                [obj.evaluate(perturbed_weights, returns) for obj in objectives]
            )

            # 计算敏感性
            for j, (original, perturbed) in enumerate(
                zip(original_values, perturbed_values)
            ):
                if abs(epsilon) > 1e - 8:
                    sensitivity[f"asset_{i}_obj_{j}"] = (perturbed - original) / epsilon

        return sensitivity

    def plot_optimization_progress(self, save_path: Optional[str] = None) -> None:
        """绘制优化进度图"""
        if not self.optimization_history:
            logger.warning("No optimization history available")
            return

        generations = [h.generation for h in self.optimization_history]
        hypervolumes = [h.hypervolume for h in self.optimization_history]

        fig = make_subplots(
            rows = 2,
            cols = 2,
            subplot_titles=(
                "Hypervolume",
                "Average Distance to Ideal",
                "Average Crowding Distance",
                "Solution Diversity",
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}],
            ],
        )

        # 超体积
        fig.add_trace(
            go.Scatter(
                x = generations, y = hypervolumes, mode="lines + markers", name="Hypervolume"
            ),
            row = 1,
            col = 1,
        )

        # 收敛指标
        avg_distances = [
            h.convergence_metrics.get("avg_distance_to_ideal", 0)
            for h in self.optimization_history
        ]
        fig.add_trace(
            go.Scatter(
                x = generations,
                y = avg_distances,
                mode="lines + markers",
                name="Avg Distance",
            ),
            row = 1,
            col = 2,
        )

        # 拥挤距离
        avg_crowding = [
            h.diversity_metrics.get("avg_crowding_distance", 0)
            for h in self.optimization_history
        ]
        fig.add_trace(
            go.Scatter(
                x = generations, y = avg_crowding, mode="lines + markers", name="Avg Crowding"
            ),
            row = 2,
            col = 1,
        )

        # 多样性
        diversity_spread = [
            h.diversity_metrics.get("diversity_spread", 0)
            for h in self.optimization_history
        ]
        fig.add_trace(
            go.Scatter(
                x = generations,
                y = diversity_spread,
                mode="lines + markers",
                name="Diversity",
            ),
            row = 2,
            col = 2,
        )

        fig.update_layout(
            title="Multi - Objective Optimization Progress", height = 800, showlegend = False
        )

        if save_path:
            fig.write_html(save_path)

        fig.show()


# 便利函数
def create_multi_objective_optimizer(
    config: Optional[MultiObjectiveConfig] = None,
) -> MultiObjectiveOptimizer:
    """创建多目标优化引擎"""
    return MultiObjectiveOptimizer(config)


def optimize_multi_objective_portfolio(
    returns: pd.DataFrame,
    objectives: List[str],
    algorithm: str = "nsga2",
    population_size: int = 100,
    n_generations: int = 100,
) -> ParetoFrontier:
    """便利函数：多目标投资组合优化"""
    config = MultiObjectiveConfig(
        algorithm = algorithm,
        population_size = population_size,
        n_generations = n_generations,
    )
    optimizer = MultiObjectiveOptimizer(config)
    return optimizer.optimize_portfolio(returns, objectives)
