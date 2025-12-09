#!/usr / bin / env python3
"""
Multi - Objective Portfolio Optimization - Pareto Frontier Analysis
多目标投资组合优化 - 帕累托边界分析

Professional implementation of Pareto frontier calculation and analysis:
- Non - dominated sorting algorithms
- Pareto frontier approximation
- Dominance relationship analysis
- Knee point identification
- Pareto front visualization
- Sensitivity analysis
- Preference - based selection
"""

import logging
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

warnings.filterwarnings("ignore")

try:
    from scipy.interpolate import interp1d
    from scipy.spatial.distance import pdist, squareform
    from scipy.stats import pearsonr, spearmanr

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Some features may not work")

try:
    from sklearn.metrics import pairwise_distances
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit - learn not available. Some features may not work")

try:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.factory import get_reference_directions
    from pymoo.model.problem import Problem
    from pymoo.optimize import minimize
    from pymoo.visualization.scatter import Scatter

    PYMOO_AVAILABLE = True
except ImportError:
    PYMOO_AVAILABLE = False
    logging.warning("PyMOO not available. Using custom implementation")

from .objective_functions import ObjectiveConfig, ObjectiveFactory, PortfolioObjective

logger = logging.getLogger(__name__)


@dataclass
class ParetoConfig:
    """帕累托分析配置"""

    # 基本参数
    epsilon: float = 1e - 8  # 数值精度
    tolerance: float = 1e - 6  # 支配关系容差

    # 前端点数量
    max_frontier_points: int = 1000  # 最大前端点数
    min_frontier_points: int = 20  # 最小前端点数

    # 可视化
    plot_resolution: int = 100  # 绘图分辨率
    interactive: bool = True  # 交互式图表

    # 分析参数
    knee_detection_method: str = "curvature"  # curvature, distance, angle
    sensitivity_samples: int = 100  # 敏感性分析样本数

    # 聚类参数
    clustering_method: str = "kmeans"  # kmeans, hierarchical
    n_clusters: int = 5  # 聚类数量


@dataclass
class ParetoPoint:
    """帕累托点"""

    weights: np.ndarray  # 投资组合权重
    objectives: np.ndarray  # 目标函数值
    asset_names: List[str]  # 资产名称
    rank: int  # 帕累托排名
    crowding_distance: float  # 拥挤距离
    domination_count: int  # 被支配数量
    dominated_solutions: List[int]  # 支配的解集合

    # 元数据
    generation: int = 0
    calculation_time: float = 0.0
    is_knee_point: bool = False
    cluster_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        weights_dict = {
            asset: weight for asset, weight in zip(self.asset_names, self.weights)
        }

        return {
            "weights": weights_dict,
            "objectives": self.objectives.tolist(),
            "rank": self.rank,
            "crowding_distance": self.crowding_distance,
            "domination_count": self.domination_count,
            "is_knee_point": self.is_knee_point,
            "cluster_id": self.cluster_id,
            "metadata": {
                "generation": self.generation,
                "calculation_time": self.calculation_time,
            },
        }


@dataclass
class ParetoFrontier:
    """帕累托边界"""

    points: List[ParetoPoint]  # 帕累托点列表
    objective_names: List[str]  # 目标函数名称
    n_objectives: int  # 目标函数数量
    n_assets: int  # 资产数量
    asset_names: List[str]  # 资产名称

    # 分析结果
    knee_points: List[ParetoPoint] = field(default_factory = list)  # 膝点
    cluster_centers: Optional[np.ndarray] = None  # 聚类中心
    cluster_labels: Optional[np.ndarray] = None  # 聚类标签

    # 元数据
    calculation_time: float = 0.0  # 计算时间
    algorithm: str = ""  # 算法名称
    timestamp: str = ""  # 时间戳

    def __post_init__(self):
        """初始化后处理"""
        self.objectives_matrix = np.array([p.objectives for p in self.points])
        self.weights_matrix = np.array([p.weights for p in self.points])

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "points": [p.to_dict() for p in self.points],
            "objective_names": self.objective_names,
            "n_objectives": self.n_objectives,
            "n_assets": self.n_assets,
            "asset_names": self.asset_names,
            "knee_points": [kp.to_dict() for kp in self.knee_points],
            "cluster_centers": (
                self.cluster_centers.tolist()
                if self.cluster_centers is not None
                else None
            ),
            "cluster_labels": (
                self.cluster_labels.tolist()
                if self.cluster_labels is not None
                else None
            ),
            "metadata": {
                "calculation_time": self.calculation_time,
                "algorithm": self.algorithm,
                "timestamp": self.timestamp,
            },
        }


class ParetoFrontierCalculator:
    """帕累托边界计算器"""

    def __init__(self, config: Optional[ParetoConfig] = None):
        """初始化帕累托计算器"""
        self.config = config or ParetoConfig()
        logger.info("Pareto Frontier Calculator initialized")

    def calculate_pareto_frontier(
        self,
        returns: pd.DataFrame,
        objectives: List[PortfolioObjective],
        objective_weights: Optional[List[float]] = None,
        n_solutions: int = 100,
        algorithm: str = "nsga2",
    ) -> ParetoFrontier:
        """
        计算帕累托边界

        Args:
            returns: 资产回报率矩阵
            objectives: 目标函数列表
            objective_weights: 目标函数权重
            n_solutions: 解的数量
            algorithm: 优化算法

        Returns:
            ParetoFrontier: 帕累托边界
        """
        start_time = time.time()
        logger.info(
            f"Starting Pareto frontier calculation with {len(objectives)} objectives"
        )

        try:
            # 选择算法
            if algorithm == "nsga2" and PYMOO_AVAILABLE:
                points = self._nsga2_optimization(returns, objectives, n_solutions)
            else:
                points = self._weighted_sum_optimization(
                    returns, objectives, objective_weights, n_solutions
                )

            # 计算帕累托排序
            points = self._non_dominated_sorting(points, objectives)

            # 计算拥挤距离
            points = self._calculate_crowding_distance(points)

            # 识别膝点
            knee_points = self._identify_knee_points(points)

            # 聚类分析
            if len(points) > self.config.min_frontier_points:
                self._cluster_analysis(points)

            # 创建帕累托边界
            frontier = ParetoFrontier(
                points = points,
                objective_names=[obj.name for obj in objectives],
                n_objectives = len(objectives),
                n_assets = returns.shape[1],
                asset_names = list(returns.columns),
                knee_points = knee_points,
                cluster_centers = getattr(self, "_cluster_centers", None),
                cluster_labels = getattr(self, "_cluster_labels", None),
                calculation_time = time.time() - start_time,
                algorithm = algorithm,
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            logger.info(
                f"Pareto frontier calculated in {frontier.calculation_time:.3f}s with {len(points)} points"
            )
            return frontier

        except Exception as e:
            logger.error(f"Pareto frontier calculation failed: {e}")
            raise

    def _nsga2_optimization(
        self,
        returns: pd.DataFrame,
        objectives: List[PortfolioObjective],
        n_solutions: int,
    ) -> List[ParetoPoint]:
        """NSGA - II优化"""
        if not PYMOO_AVAILABLE:
            raise ImportError("PyMOO is required for NSGA - II optimization")

        class PortfolioProblem(Problem):
            def __init__(self, returns, objectives, n_assets):
                super().__init__(
                    n_var = n_assets,
                    n_obj = len(objectives),
                    n_constr = 1,  # 权重和约束
                    xl = 0.0,
                    xu = 1.0,
                )
                self.returns = returns
                self.objectives = objectives

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
        problem = PortfolioProblem(returns, objectives, returns.shape[1])

        # 运行NSGA - II
        algorithm = NSGA2(pop_size = n_solutions, eliminate_duplicates = True)

        res = minimize(
            problem, algorithm, termination=("n_gen", 100), seed = 1, verbose = False
        )

        # 转换结果为帕累托点
        points = []
        for i in range(len(res.X)):
            weights = res.X[i]
            weights = weights / np.sum(weights)
            objectives_values = res.F[i]

            point = ParetoPoint(
                weights = weights,
                objectives = objectives_values,
                asset_names = list(returns.columns),
                rank = 0,  # 将在排序中设置
                crowding_distance = 0.0,
                domination_count = 0,
                dominated_solutions=[],
            )
            points.append(point)

        return points

    def _weighted_sum_optimization(
        self,
        returns: pd.DataFrame,
        objectives: List[PortfolioObjective],
        objective_weights: Optional[List[float]],
        n_solutions: int,
    ) -> List[ParetoPoint]:
        """加权和优化"""
        if objective_weights is None:
            objective_weights = [1.0] * len(objectives)

        # 生成权重组合
        weight_combinations = self._generate_weight_combinations(
            len(objectives), n_solutions
        )

        points = []
        n_assets = returns.shape[1]

        for weights_comb in weight_combinations:
            # 组合目标函数
            def combined_objective(portfolio_weights):
                total_objective = 0.0
                for obj_weight, objective in zip(weights_comb, objectives):
                    value = objective.evaluate(portfolio_weights, returns)
                    # 根据目标方向调整符号
                    if objective.direction == "maximize":
                        value = -value
                    total_objective += obj_weight * value
                return total_objective

            # 约束优化
            from scipy.optimize import minimize

            constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
            bounds = [(0.0, 1.0) for _ in range(n_assets)]
            initial_weights = np.ones(n_assets) / n_assets

            result = minimize(
                combined_objective,
                initial_weights,
                method="SLSQP",
                bounds = bounds,
                constraints = constraints,
                options={"maxiter": 1000},
            )

            if result.success:
                weights = result.x
                weights = weights / np.sum(weights)  # 归一化

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

        return points

    def _generate_weight_combinations(
        self, n_objectives: int, n_combinations: int
    ) -> List[List[float]]:
        """生成目标函数权重组合"""
        combinations = []

        if n_objectives == 2:
            # 两目标：均匀分割
            for i in range(n_combinations):
                w1 = i / (n_combinations - 1)
                w2 = 1 - w1
                combinations.append([w1, w2])

        else:
            # 多目标：使用简单网格或随机生成
            import random

            for _ in range(n_combinations):
                weights = [random.random() for _ in range(n_objectives)]
                total = sum(weights)
                weights = [w / total for w in weights]
                combinations.append(weights)

        return combinations

    def _non_dominated_sorting(
        self, points: List[ParetoPoint], objectives: List[PortfolioObjective]
    ) -> List[ParetoPoint]:
        """非支配排序"""
        n_points = len(points)

        # 初始化
        for point in points:
            point.rank = 1  # 第一前端
            point.domination_count = 0
            point.dominated_solutions = []

        if n_points == 0:
            return points

        # 计算支配关系
        for i in range(n_points):
            for j in range(n_points):
                if i != j:
                    if self._dominates(points[i], points[j], objectives):
                        points[i].dominated_solutions.append(j)
                        points[j].domination_count += 1

        # 分配帕累托排名
        front = 1
        remaining_points = points[:]

        while remaining_points:
            # 找到当前前端
            current_front = [p for p in remaining_points if p.domination_count == 0]

            if not current_front:
                break

            # 为当前前端分配排名
            for point in current_front:
                point.rank = front

            # 更新被支配解的计数
            for point in current_front:
                for dominated_idx in point.dominated_solutions:
                    points[dominated_idx].domination_count -= 1

            # 移除当前前端
            remaining_points = [p for p in remaining_points if p not in current_front]
            front += 1

        return points

    def _dominates(
        self,
        point1: ParetoPoint,
        point2: ParetoPoint,
        objectives: List[PortfolioObjective],
    ) -> bool:
        """判断点1是否支配点2"""
        better_in_any = False

        for obj1_val, obj2_val, objective in zip(
            point1.objectives, point2.objectives, objectives
        ):
            if objective.direction == "minimize":
                if obj1_val > obj2_val + self.config.tolerance:
                    return False  # point1不优于point2
                if obj1_val < obj2_val - self.config.tolerance:
                    better_in_any = True
            else:  # maximize
                if obj1_val < obj2_val - self.config.tolerance:
                    return False  # point1不优于point2
                if obj1_val > obj2_val + self.config.tolerance:
                    better_in_any = True

        return better_in_any

    def _calculate_crowding_distance(
        self, points: List[ParetoPoint]
    ) -> List[ParetoPoint]:
        """计算拥挤距离"""
        if not points:
            return points

        # 按排名分组
        fronts = {}
        for point in points:
            rank = point.rank
            if rank not in fronts:
                fronts[rank] = []
            fronts[rank].append(point)

        # 为每个前端计算拥挤距离
        for front_points in fronts.values():
            if len(front_points) <= 2:
                # 前端点太少，设置大距离
                for point in front_points:
                    point.crowding_distance = float("inf")
                continue

            # 初始化距离
            for point in front_points:
                point.crowding_distance = 0.0

            # 对每个目标函数计算距离
            n_objectives = len(front_points[0].objectives)
            for obj_idx in range(n_objectives):
                # 按目标函数值排序
                sorted_points = sorted(
                    front_points, key = lambda p: p.objectives[obj_idx]
                )

                # 边界点设置为无穷大
                sorted_points[0].crowding_distance = float("inf")
                sorted_points[-1].crowding_distance = float("inf")

                # 计算目标函数值范围
                obj_min = sorted_points[0].objectives[obj_idx]
                obj_max = sorted_points[-1].objectives[obj_idx]

                if obj_max - obj_min < self.config.epsilon:
                    continue  # 避免除零

                # 计算中间点的拥挤距离
                for i in range(1, len(sorted_points) - 1):
                    if sorted_points[i].crowding_distance != float("inf"):
                        distance = (
                            sorted_points[i + 1].objectives[obj_idx]
                            - sorted_points[i - 1].objectives[obj_idx]
                        ) / (obj_max - obj_min)
                        sorted_points[i].crowding_distance += distance

        return points

    def _identify_knee_points(self, points: List[ParetoPoint]) -> List[ParetoPoint]:
        """识别膝点"""
        # 只考虑第一前端
        first_front = [p for p in points if p.rank == 0]

        if len(first_front) < 3:
            return []

        knee_points = []

        if (
            self.config.knee_detection_method == "curvature"
            and len(first_front[0].objectives) == 2
        ):
            # 二目标曲率方法
            knee_points = self._curvature_knee_detection(first_front)
        elif self.config.knee_detection_method == "distance":
            # 距离方法
            knee_points = self._distance_knee_detection(first_front)
        else:
            # 角度方法
            knee_points = self._angle_knee_detection(first_front)

        # 标记膝点
        for point in knee_points:
            point.is_knee_point = True

        return knee_points

    def _curvature_knee_detection(self, points: List[ParetoPoint]) -> List[ParetoPoint]:
        """基于曲率的膝点检测（仅适用于二目标）"""
        # 按第一个目标排序
        sorted_points = sorted(points, key = lambda p: p.objectives[0])

        if len(sorted_points) < 3:
            return []

        knee_points = []
        max_curvature = 0

        for i in range(1, len(sorted_points) - 1):
            # 计算三点形成的曲率
            p1 = sorted_points[i - 1].objectives
            p2 = sorted_points[i].objectives
            p3 = sorted_points[i + 1].objectives

            # 简化的曲率计算
            v1 = np.array(p2) - np.array(p1)
            v2 = np.array(p3) - np.array(p2)

            # 计算角度变化作为曲率代理
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 > self.config.epsilon and norm2 > self.config.epsilon:
                cos_angle = np.dot(v1, v2) / (norm1 * norm2)
                cos_angle = np.clip(cos_angle, -1, 1)
                curvature = 1 - cos_angle  # 角度越大，曲率越大

                if curvature > max_curvature:
                    max_curvature = curvature
                    knee_points = [sorted_points[i]]

        return knee_points

    def _distance_knee_detection(self, points: List[ParetoPoint]) -> List[ParetoPoint]:
        """基于距离的膝点检测"""
        if not SKLEARN_AVAILABLE:
            return []

        # 归一化目标函数值
        scaler = StandardScaler()
        objectives_normalized = scaler.fit_transform([p.objectives for p in points])

        # 计算到理想点（各目标最优值）和反理想点（各目标最差值）的距离
        ideal_point = np.min(objectives_normalized, axis = 0)
        anti_ideal_point = np.max(objectives_normalized, axis = 0)

        knee_points = []
        max_distance = 0

        for i, point in enumerate(points):
            dist_to_ideal = np.linalg.norm(objectives_normalized[i] - ideal_point)
            dist_to_anti_ideal = np.linalg.norm(
                objectives_normalized[i] - anti_ideal_point
            )

            # 膝点指标：到理想点近，到反理想点远
            knee_score = dist_to_anti_ideal / (dist_to_ideal + self.config.epsilon)

            if knee_score > max_distance:
                max_distance = knee_score
                knee_points = [point]

        return knee_points

    def _angle_knee_detection(self, points: List[ParetoPoint]) -> List[ParetoPoint]:
        """基于角度的膝点检测"""
        if len(points[0].objectives) != 2:
            return self._distance_knee_detection(points)

        # 按第一个目标排序
        sorted_points = sorted(points, key = lambda p: p.objectives[0])

        if len(sorted_points) < 3:
            return []

        # 计算每个点的角度
        knee_points = []
        max_angle = 0

        for i in range(1, len(sorted_points) - 1):
            # 计算向量
            v1 = np.array(sorted_points[i - 1].objectives) - np.array(
                sorted_points[i].objectives
            )
            v2 = np.array(sorted_points[i + 1].objectives) - np.array(
                sorted_points[i].objectives
            )

            # 计算角度
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 > self.config.epsilon and norm2 > self.config.epsilon:
                cos_angle = np.dot(v1, v2) / (norm1 * norm2)
                cos_angle = np.clip(cos_angle, -1, 1)
                angle = np.arccos(cos_angle)

                if angle > max_angle:
                    max_angle = angle
                    knee_points = [sorted_points[i]]

        return knee_points

    def _cluster_analysis(self, points: List[ParetoPoint]) -> None:
        """聚类分析"""
        if len(points) < self.config.n_clusters:
            return

        try:
            if SKLEARN_AVAILABLE:
                from sklearn.cluster import KMeans

                # 提取第一前端的目标函数值
                first_front = [p for p in points if p.rank == 0]
                if len(first_front) < self.config.n_clusters:
                    return

                X = np.array([p.objectives for p in first_front])

                # K - means聚类
                kmeans = KMeans(n_clusters = self.config.n_clusters, random_state = 42)
                labels = kmeans.fit_predict(X)

                # 设置聚类信息
                for i, point in enumerate(first_front):
                    point.cluster_id = labels[i]

                self._cluster_centers = kmeans.cluster_centers_
                self._cluster_labels = labels

        except Exception as e:
            logger.warning(f"Cluster analysis failed: {e}")

    def visualize_pareto_frontier(
        self,
        frontier: ParetoFrontier,
        objective_indices: Optional[List[int]] = None,
        interactive: Optional[bool] = None,
        save_path: Optional[str] = None,
    ) -> None:
        """可视化帕累托边界"""
        if objective_indices is None:
            objective_indices = list(range(min(3, frontier.n_objectives)))

        interactive = (
            interactive if interactive is not None else self.config.interactive
        )

        # 准备数据
        first_front = [p for p in frontier.points if p.rank == 0]
        if not first_front:
            logger.warning("No points on Pareto frontier")
            return

        objectives_data = np.array(
            [p.objectives[objective_indices] for p in first_front]
        )
        knee_points_data = np.array(
            [p.objectives[objective_indices] for p in frontier.knee_points]
        )

        if interactive:
            self._plot_interactive_pareto(
                objectives_data,
                knee_points_data,
                frontier,
                objective_indices,
                save_path,
            )
        else:
            self._plot_static_pareto(
                objectives_data,
                knee_points_data,
                frontier,
                objective_indices,
                save_path,
            )

    def _plot_interactive_pareto(
        self,
        objectives_data: np.ndarray,
        knee_points_data: np.ndarray,
        frontier: ParetoFrontier,
        objective_indices: List[int],
        save_path: Optional[str],
    ) -> None:
        """交互式帕累托边界图"""
        if len(objective_indices) == 2:
            # 2D散点图
            fig = go.Figure()

            # 帕累托前沿
            fig.add_trace(
                go.Scatter(
                    x = objectives_data[:, 0],
                    y = objectives_data[:, 1],
                    mode="markers",
                    name="Pareto Frontier",
                    marker = dict(size = 8, color="blue", opacity = 0.6),
                )
            )

            # 膝点
            if len(knee_points_data) > 0:
                fig.add_trace(
                    go.Scatter(
                        x = knee_points_data[:, 0],
                        y = knee_points_data[:, 1],
                        mode="markers",
                        name="Knee Points",
                        marker = dict(size = 12, color="red", symbol="star"),
                    )
                )

            fig.update_layout(
                title = f"Pareto Frontier: {frontier.objective_names[objective_indices[0]]} vs {frontier.objective_names[objective_indices[1]]}",
                xaxis_title = frontier.objective_names[objective_indices[0]],
                yaxis_title = frontier.objective_names[objective_indices[1]],
                hovermode="closest",
            )

        elif len(objective_indices) == 3:
            # 3D散点图
            fig = go.Figure()

            # 帕累托前沿
            fig.add_trace(
                go.Scatter3d(
                    x = objectives_data[:, 0],
                    y = objectives_data[:, 1],
                    z = objectives_data[:, 2],
                    mode="markers",
                    name="Pareto Frontier",
                    marker = dict(
                        size = 5,
                        color = objectives_data[:, 2],
                        colorscale="Viridis",
                        opacity = 0.6,
                    ),
                )
            )

            # 膝点
            if len(knee_points_data) > 0:
                fig.add_trace(
                    go.Scatter3d(
                        x = knee_points_data[:, 0],
                        y = knee_points_data[:, 1],
                        z = knee_points_data[:, 2],
                        mode="markers",
                        name="Knee Points",
                        marker = dict(size = 10, color="red", symbol="diamond"),
                    )
                )

            fig.update_layout(
                title = f"Pareto Frontier: {len(objective_indices)} Objectives",
                scene = dict(
                    xaxis_title = frontier.objective_names[objective_indices[0]],
                    yaxis_title = frontier.objective_names[objective_indices[1]],
                    zaxis_title = frontier.objective_names[objective_indices[2]],
                ),
            )

        if save_path:
            fig.write_html(save_path)

        fig.show()

    def _plot_static_pareto(
        self,
        objectives_data: np.ndarray,
        knee_points_data: np.ndarray,
        frontier: ParetoFrontier,
        objective_indices: List[int],
        save_path: Optional[str],
    ) -> None:
        """静态帕累托边界图"""
        fig, ax = plt.subplots(figsize=(10, 8))

        if len(objective_indices) == 2:
            # 2D散点图
            ax.scatter(
                objectives_data[:, 0],
                objectives_data[:, 1],
                c="blue",
                alpha = 0.6,
                label="Pareto Frontier",
            )

            if len(knee_points_data) > 0:
                ax.scatter(
                    knee_points_data[:, 0],
                    knee_points_data[:, 1],
                    c="red",
                    s = 100,
                    marker="*",
                    label="Knee Points",
                )

            ax.set_xlabel(frontier.objective_names[objective_indices[0]])
            ax.set_ylabel(frontier.objective_names[objective_indices[1]])
            ax.set_title(
                f"Pareto Frontier: {frontier.objective_names[objective_indices[0]]} vs {frontier.objective_names[objective_indices[1]]}"
            )

        else:
            # 多目标散点图矩阵
            n_obj = len(objective_indices)
            fig, axes = plt.subplots(n_obj, n_obj, figsize=(15, 15))

            for i in range(n_obj):
                for j in range(n_obj):
                    if i == j:
                        axes[i, j].hist(objectives_data[:, i], bins = 20, alpha = 0.6)
                        axes[i, j].set_title(
                            frontier.objective_names[objective_indices[i]]
                        )
                    else:
                        axes[i, j].scatter(
                            objectives_data[:, j],
                            objectives_data[:, i],
                            c="blue",
                            alpha = 0.6,
                            s = 10,
                        )
                        axes[i, j].set_xlabel(
                            frontier.objective_names[objective_indices[j]]
                        )
                        axes[i, j].set_ylabel(
                            frontier.objective_names[objective_indices[i]]
                        )

        ax.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi = 300, bbox_inches="tight")

        plt.show()


# 便利函数
def create_pareto_calculator(
    config: Optional[ParetoConfig] = None,
) -> ParetoFrontierCalculator:
    """创建帕累托计算器"""
    return ParetoFrontierCalculator(config)


def calculate_pareto_frontier(
    returns: pd.DataFrame,
    objectives: List[str],
    objective_weights: Optional[List[float]] = None,
    n_solutions: int = 100,
    algorithm: str = "nsga2",
) -> ParetoFrontier:
    """便利函数：计算帕累托边界"""
    factory = ObjectiveFactory()
    objective_instances = [factory.create_objective(name) for name in objectives]

    calculator = ParetoFrontierCalculator()
    return calculator.calculate_pareto_frontier(
        returns, objective_instances, objective_weights, n_solutions, algorithm
    )
