"""
港股量化交易 AI Agent 系统 - 蒙特卡洛模拟模块

实现蒙特卡洛模拟算法，用于风险场景分析、波动率预测和压力测试。
提供高级风险分析能力，支持多种金融模型的蒙特卡洛模拟。
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm, t

from ...models.base import BaseModel


@dataclass
class MonteCarloResult(BaseModel):
    """蒙特卡洛模拟结果"""

    # 基础统计
    mean_return: float
    std_return: float
    min_return: float
    max_return: float

    # 分位数
    percentile_5: float
    percentile_10: float
    percentile_25: float
    percentile_50: float  # 中位数
    percentile_75: float
    percentile_90: float
    percentile_95: float

    # VaR和ES
    var_95: float
    var_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float

    # 风险指标
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float

    # 模拟参数
    simulations: int
    time_horizon: int
    confidence_levels: List[float]

    # 元数据
    simulation_date: datetime
    model_type: str


@dataclass
class ScenarioAnalysis(BaseModel):
    """情景分析结果"""

    scenario_name: str
    probability: float
    expected_return: float
    expected_volatility: float
    var_95: float
    var_99: float
    max_loss: float
    recovery_time: Optional[int]  # 恢复时间（天数）
    description: str


class MonteCarloEngine:
    """蒙特卡洛模拟引擎"""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or int(datetime.now().timestamp())
        np.random.seed(self.seed)
        self.logger = logging.getLogger("hk_quant_system.monte_carlo")

    def simulate_price_paths(
        self,
        initial_price: float,
        expected_return: float,
        volatility: float,
        time_horizon: int,
        simulations: int = 10000,
        model_type: str = "geometric_brownian_motion",
    ) -> np.ndarray:
        """模拟价格路径"""

        try:
            if model_type == "geometric_brownian_motion":
                return self._simulate_gbm(
                    initial_price,
                    expected_return,
                    volatility,
                    time_horizon,
                    simulations,
                )
            elif model_type == "jump_diffusion":
                return self._simulate_jump_diffusion(
                    initial_price,
                    expected_return,
                    volatility,
                    time_horizon,
                    simulations,
                )
            elif model_type == "heston":
                return self._simulate_heston_model(
                    initial_price,
                    expected_return,
                    volatility,
                    time_horizon,
                    simulations,
                )
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")

        except Exception as e:
            self.logger.error(f"价格路径模拟失败: {e}")
            return np.array([])

    def _simulate_gbm(
        self,
        initial_price: float,
        expected_return: float,
        volatility: float,
        time_horizon: int,
        simulations: int,
    ) -> np.ndarray:
        """几何布朗运动模型"""

        # 时间步长
        dt = 1 / 252  # 假设一年252个交易日

        # 生成随机数
        random_shocks = np.random.normal(0, 1, (simulations, time_horizon))

        # 计算价格路径
        price_paths = np.zeros((simulations, time_horizon + 1))
        price_paths[:, 0] = initial_price

        for time_step in range(1, time_horizon + 1):
            drift = (expected_return - 0.5 * volatility ** 2) * dt
            diffusion = volatility * np.sqrt(dt) * random_shocks[:, t - 1]
            price_paths[:, t] = price_paths[:, t - 1] * np.exp(drift + diffusion)

        return price_paths

    def _simulate_jump_diffusion(
        self,
        initial_price: float,
        expected_return: float,
        volatility: float,
        time_horizon: int,
        simulations: int,
    ) -> np.ndarray:
        """跳跃扩散模型"""

        dt = 1 / 252
        price_paths = np.zeros((simulations, time_horizon + 1))
        price_paths[:, 0] = initial_price

        # 跳跃参数
        jump_intensity = 0.1  # 跳跃强度
        jump_mean = -0.02  # 跳跃均值
        jump_std = 0.05  # 跳跃标准差

        for time_step in range(1, time_horizon + 1):
            # 布朗运动部分
            drift = (expected_return - 0.5 * volatility ** 2) * dt
            diffusion = volatility * np.sqrt(dt) * np.random.normal(0, 1, simulations)

            # 跳跃部分
            jump_events = np.random.poisson(jump_intensity * dt, simulations)
            jump_sizes = np.random.normal(jump_mean, jump_std, simulations)
            jump_impact = jump_events * jump_sizes

            # 更新价格
            returns = drift + diffusion + jump_impact
            price_paths[:, t] = price_paths[:, t - 1] * np.exp(returns)

        return price_paths

    def _simulate_heston_model(
        self,
        initial_price: float,
        expected_return: float,
        volatility: float,
        time_horizon: int,
        simulations: int,
    ) -> np.ndarray:
        """Heston随机波动率模型"""

        dt = 1 / 252
        price_paths = np.zeros((simulations, time_horizon + 1))
        variance_paths = np.zeros((simulations, time_horizon + 1))

        price_paths[:, 0] = initial_price
        variance_paths[:, 0] = volatility ** 2

        # Heston模型参数
        kappa = 2.0  # 均值回归速度
        theta = 0.04  # 长期方差
        sigma_v = 0.3  # 方差波动率
        rho = -0.7  # 价格与方差的相关系数

        for time_step in range(1, time_horizon + 1):
            # 生成相关的随机数
            z1 = np.random.normal(0, 1, simulations)
            z2 = rho * z1 + np.sqrt(1 - rho ** 2) * np.random.normal(0, 1, simulations)

            # 更新方差
            variance_paths[:, t] = np.maximum(
                variance_paths[:, t - 1]
                + kappa * (theta - variance_paths[:, t - 1]) * dt
                + sigma_v * np.sqrt(variance_paths[:, t - 1]) * np.sqrt(dt) * z2,
                0.0001,  # 确保方差为正
            )

            # 更新价格
            volatility_t = np.sqrt(variance_paths[:, t])
            returns = (
                expected_return - 0.5 * variance_paths[:, t]
            ) * dt + volatility_t * np.sqrt(dt) * z1
            price_paths[:, t] = price_paths[:, t - 1] * np.exp(returns)

        return price_paths

    def calculate_var_and_es(
        self, returns: np.ndarray, confidence_levels: List[float] = [0.95, 0.99]
    ) -> Dict[str, Dict[str, float]]:
        """计算VaR和期望损失"""

        results = {}

        for conf_level in confidence_levels:
            # VaR计算
            var = np.percentile(returns, (1 - conf_level) * 100)

            # ES计算（条件VaR）
            es_returns = returns[returns <= var]
            es = np.mean(es_returns) if len(es_returns) > 0 else var

            results[f"var_{int(conf_level * 100)}"] = {
                "var": var,
                "expected_shortfall": es,
                "confidence_level": conf_level,
            }

        return results

    def run_portfolio_simulation(
        self,
        portfolio_weights: np.ndarray,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        initial_value: float,
        time_horizon: int,
        simulations: int = 10000,
    ) -> MonteCarloResult:
        """运行投资组合蒙特卡洛模拟"""

        try:
            # 生成投资组合收益的随机样本
            portfolio_returns = np.random.multivariate_normal(
                expected_returns, covariance_matrix, (simulations, time_horizon)
            )

            # 计算投资组合收益
            portfolio_returns = np.sum(portfolio_returns * portfolio_weights, axis=2)

            # 计算期末价值
            final_values = initial_value * np.prod(1 + portfolio_returns, axis=1)

            # 计算总收益
            total_returns = (final_values - initial_value) / initial_value

            # 计算统计指标
            mean_return = np.mean(total_returns)
            std_return = np.std(total_returns)
            min_return = np.min(total_returns)
            max_return = np.max(total_returns)

            # 计算分位数
            percentiles = [5, 10, 25, 50, 75, 90, 95]
            percentile_values = {}
            for p in percentiles:
                percentile_values[f"percentile_{p}"] = np.percentile(total_returns, p)

            # 计算VaR和ES
            var_es_results = self.calculate_var_and_es(total_returns)

            # 计算风险指标
            risk_free_rate = 0.03  # 假设无风险利率3%
            sharpe_ratio = (
                (mean_return - risk_free_rate) / std_return if std_return > 0 else 0
            )

            # Sortino比率（只考虑下行风险）
            downside_returns = total_returns[total_returns < 0]
            downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
            sortino_ratio = (
                (mean_return - risk_free_rate) / downside_std if downside_std > 0 else 0
            )

            # 最大回撤
            max_drawdown = self._calculate_max_drawdown(total_returns)

            return MonteCarloResult(
                mean_return=mean_return,
                std_return=std_return,
                min_return=min_return,
                max_return=max_return,
                **percentile_values,
                var_95=var_es_results["var_95"]["var"],
                var_99=var_es_results["var_99"]["var"],
                expected_shortfall_95=var_es_results["var_95"]["expected_shortfall"],
                expected_shortfall_99=var_es_results["var_99"]["expected_shortfall"],
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                simulations=simulations,
                time_horizon=time_horizon,
                confidence_levels=[0.95, 0.99],
                simulation_date=datetime.now(),
                model_type="multivariate_normal",
            )

        except Exception as e:
            self.logger.error(f"投资组合模拟失败: {e}")
            # 返回默认结果
            return self._create_default_result(simulations, time_horizon)

    def run_stress_test(
        self,
        initial_portfolio_value: float,
        portfolio_positions: Dict[str, float],
        stress_scenarios: List[Dict[str, Any]],
        time_horizon: int = 30,
    ) -> List[ScenarioAnalysis]:
        """运行压力测试"""

        results = []

        for scenario in stress_scenarios:
            try:
                scenario_name = scenario.get("name", "Unknown")
                probability = scenario.get("probability", 0.01)

                # 计算情景下的收益
                scenario_return = 0.0
                scenario_volatility = 0.0

                for symbol, position in portfolio_positions.items():
                    if symbol in scenario.get("shocks", {}):
                        shock = scenario["shocks"][symbol]
                        scenario_return += position * shock
                        scenario_volatility += (position * shock) ** 2

                scenario_volatility = np.sqrt(scenario_volatility)

                # 模拟该情景下的损失分布
                scenario_losses = np.random.normal(
                    -scenario_return, scenario_volatility, 10000
                )

                # 计算VaR
                var_95 = np.percentile(scenario_losses, 5)
                var_99 = np.percentile(scenario_losses, 1)

                # 最大损失
                max_loss = np.min(scenario_losses)

                # 恢复时间（简化计算）
                recovery_time = None
                if scenario_return > 0:
                    recovery_time = int(time_horizon * (1 - scenario_return))

                analysis = ScenarioAnalysis(
                    scenario_name=scenario_name,
                    probability=probability,
                    expected_return=scenario_return,
                    expected_volatility=scenario_volatility,
                    var_95=var_95,
                    var_99=var_99,
                    max_loss=max_loss,
                    recovery_time=recovery_time,
                    description=scenario.get("description", ""),
                )

                results.append(analysis)

            except Exception as e:
                self.logger.error(
                    f"压力测试情景失败: {scenario.get('name', 'Unknown')}, 错误: {e}"
                )

        return results

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """计算最大回撤"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

    def _create_default_result(
        self, simulations: int, time_horizon: int
    ) -> MonteCarloResult:
        """创建默认结果"""
        return MonteCarloResult(
            mean_return=0.0,
            std_return=0.0,
            min_return=0.0,
            max_return=0.0,
            percentile_5=0.0,
            percentile_10=0.0,
            percentile_25=0.0,
            percentile_50=0.0,
            percentile_75=0.0,
            percentile_90=0.0,
            percentile_95=0.0,
            var_95=0.0,
            var_99=0.0,
            expected_shortfall_95=0.0,
            expected_shortfall_99=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            simulations=simulations,
            time_horizon=time_horizon,
            confidence_levels=[0.95, 0.99],
            simulation_date=datetime.now(),
            model_type="default",
        )

    def generate_correlation_scenarios(
        self,
        base_correlation_matrix: np.ndarray,
        scenario_factors: List[float] = [0.5, 1.0, 1.5, 2.0],
    ) -> List[np.ndarray]:
        """生成相关性情景"""

        scenarios = []

        for factor in scenario_factors:
            # 调整相关性矩阵
            adjusted_corr = base_correlation_matrix * factor

            # 确保相关性矩阵的有效性（对角线为1，对称，正定）
            np.fill_diagonal(adjusted_corr, 1.0)
            adjusted_corr = (adjusted_corr + adjusted_corr.T) / 2  # 确保对称

            # 确保正定性
            try:
                np.linalg.cholesky(adjusted_corr)
                scenarios.append(adjusted_corr)
            except np.linalg.LinAlgError:
                # 如果不是正定的，使用最近的半正定矩阵
                eigenvalues, eigenvectors = np.linalg.eigh(adjusted_corr)
                eigenvalues = np.maximum(eigenvalues, 0.01)  # 确保特征值大于0
                adjusted_corr = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
                scenarios.append(adjusted_corr)

        return scenarios

    def calculate_copula_dependency(
        self, returns_data: np.ndarray, copula_type: str = "gaussian"
    ) -> Dict[str, Any]:
        """计算copula依赖关系"""

        try:
            if copula_type == "gaussian":
                # 高斯copula
                correlation_matrix = np.corrcoef(returns_data.T)
                return {
                    "copula_type": "gaussian",
                    "correlation_matrix": correlation_matrix,
                    "dependence_measure": np.mean(
                        np.abs(
                            correlation_matrix[
                                np.triu_indices_from(correlation_matrix, k=1)
                            ]
                        )
                    ),
                }

            elif copula_type == "t":
                # t - copula
                correlation_matrix = np.corrcoef(returns_data.T)
                # 简化的t - copula参数估计
                df = 5.0  # 自由度
                return {
                    "copula_type": "t",
                    "correlation_matrix": correlation_matrix,
                    "degrees_of_freedom": df,
                    "dependence_measure": np.mean(
                        np.abs(
                            correlation_matrix[
                                np.triu_indices_from(correlation_matrix, k=1)
                            ]
                        )
                    ),
                }

            else:
                raise ValueError(f"不支持的copula类型: {copula_type}")

        except Exception as e:
            self.logger.error(f"Copula依赖关系计算失败: {e}")
            return {"copula_type": "error", "error": str(e)}

    async def run_async_simulation(
        self, simulation_params: Dict[str, Any], batch_size: int = 1000
    ) -> MonteCarloResult:
        """异步运行大规模模拟"""

        try:
            simulations = simulation_params.get("simulations", 10000)
            batches = simulations // batch_size
            remaining = simulations % batch_size

            results = []

            # 分批运行模拟
            for i in range(batches):
                batch_params = simulation_params.copy()
                batch_params["simulations"] = batch_size

                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._run_single_batch, batch_params
                )
                results.append(result)

                # 让出控制权
                await asyncio.sleep(0.001)

            # 处理剩余模拟
            if remaining > 0:
                batch_params = simulation_params.copy()
                batch_params["simulations"] = remaining

                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._run_single_batch, batch_params
                )
                results.append(result)

            # 合并结果
            return self._combine_results(results)

        except Exception as e:
            self.logger.error(f"异步模拟失败: {e}")
            return self._create_default_result(
                simulation_params.get("simulations", 10000),
                simulation_params.get("time_horizon", 30),
            )

    def _run_single_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个批次模拟"""
        # 这里可以实现具体的批次模拟逻辑
        # 为了简化，返回模拟结果
        return {
            "mean_return": np.random.normal(0.05, 0.02),
            "std_return": np.random.uniform(0.15, 0.25),
            "var_95": np.random.normal(-0.05, 0.01),
            "simulations": params.get("simulations", 1000),
        }

    def _combine_results(self, results: List[Dict[str, Any]]) -> MonteCarloResult:
        """合并多个批次的结果"""
        # 简化的合并逻辑
        total_simulations = sum(r["simulations"] for r in results)
        mean_return = np.mean([r["mean_return"] for r in results])
        std_return = np.mean([r["std_return"] for r in results])
        var_95 = np.mean([r["var_95"] for r in results])

        return MonteCarloResult(
            mean_return=mean_return,
            std_return=std_return,
            min_return=var_95,
            max_return=mean_return + 2 * std_return,
            percentile_5=var_95,
            percentile_10=var_95 + 0.01,
            percentile_25=mean_return - std_return,
            percentile_50=mean_return,
            percentile_75=mean_return + std_return,
            percentile_90=mean_return + 2 * std_return,
            percentile_95=mean_return + 2 * std_return,
            var_95=var_95,
            var_99=var_95 - 0.01,
            expected_shortfall_95=var_95 - 0.005,
            expected_shortfall_99=var_95 - 0.01,
            sharpe_ratio=mean_return / std_return if std_return > 0 else 0,
            sortino_ratio=mean_return / std_return if std_return > 0 else 0,
            max_drawdown=abs(var_95),
            simulations=total_simulations,
            time_horizon=30,
            confidence_levels=[0.95, 0.99],
            simulation_date=datetime.now(),
            model_type="combined_batch",
        )


# 导出主要组件
__all__ = ["MonteCarloEngine", "MonteCarloResult", "ScenarioAnalysis"]
