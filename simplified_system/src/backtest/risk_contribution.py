#!/usr / bin / env python3
"""
Risk Contribution Analysis
风险贡献分析

Advanced risk contribution calculation and attribution
高级风险贡献计算和归因

Features:
- Marginal and component risk contributions
- Risk factor decomposition
- Risk attribution analysis
- Contribution time series
- Risk budget monitoring
- Multiple risk measures
"""

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import scipy.linalg as la
    from scipy.optimize import minimize
    from scipy.stats import norm
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning(
        "Scikit - learn not available. Install with: pip install scikit - learn"
    )

try:
    from .risk_metrics import AdvancedRiskMetrics
except ImportError:
    # Fallback for direct module execution
    import risk_metrics

    AdvancedRiskMetrics = risk_metrics.AdvancedRiskMetrics

logger = logging.getLogger(__name__)


@dataclass
class RiskContributionConfig:
    """风险贡献分析配置"""

    # 基本参数
    trading_days_per_year: int = 252  # 交易日数
    confidence_levels: List[float] = field(default_factory = lambda: [0.95, 0.99])

    # 风险度量
    risk_measures: List[str] = field(
        default_factory = lambda: ["volatility", "var", "cvar"]
    )

    # 因子分析
    num_factors: int = 5  # 主成分因子数量
    factor分析方法: str = "pca"  # pca, regression, clustering

    # 时间序列分析
    rolling_window: int = 60  # 滚动窗口
    rebalance_frequency: str = "monthly"  # daily, weekly, monthly

    # 数值设置
    epsilon: float = 1e - 8  # 数值精度
    monte_carlo_simulations: int = 10000  # Monte Carlo模拟次数


@dataclass
class MarginalRiskContribution:
    """边际风险贡献"""

    asset_name: str
    marginal_contribution: float  # 边际贡献
    component_contribution: float  # 成分贡献
    percentage_contribution: float  # 百分比贡献

    # 不同风险度量的贡献
    volatility_contribution: float
    var_contribution: float
    cvar_contribution: float


@dataclass
class FactorRiskContribution:
    """因子风险贡献"""

    factor_name: str
    factor_exposure: float  # 因子暴露
    factor_risk: float  # 因子风险
    contribution_to_portfolio_risk: float  # 对投资组合风险的贡献
    eigenvalue: Optional[float] = None  # 特征值 (PCA)


@dataclass
class RiskContributionAnalysis:
    """风险贡献分析结果"""

    marginal_contributions: List[MarginalRiskContribution]
    factor_contributions: List[FactorRiskContribution]

    # 投资组合指标
    portfolio_volatility: float
    portfolio_var: float
    portfolio_cvar: float

    # 分解指标
    systematic_risk: float
    idiosyncratic_risk: float
    diversification_ratio: float

    # 风险度量
    risk_measure: str
    confidence_level: float

    # 元数据
    assets: List[str]
    calculation_date: str
    lookback_period: int

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "marginal_contributions": {
                mc.asset_name: {
                    "marginal_contribution": round(mc.marginal_contribution, 6),
                    "component_contribution": round(mc.component_contribution, 6),
                    "percentage_contribution": round(
                        mc.percentage_contribution * 100, 2
                    ),
                    "volatility_contribution": round(mc.volatility_contribution, 6),
                    "var_contribution": round(mc.var_contribution, 6),
                    "cvar_contribution": round(mc.cvar_contribution, 6),
                }
                for mc in self.marginal_contributions
            },
            "factor_contributions": {
                fc.factor_name: {
                    "factor_exposure": round(fc.factor_exposure, 4),
                    "factor_risk": round(fc.factor_risk, 6),
                    "contribution_to_portfolio_risk": round(
                        fc.contribution_to_portfolio_risk, 6
                    ),
                    "eigenvalue": (
                        round(fc.eigenvalue, 6) if fc.eigenvalue is not None else None
                    ),
                }
                for fc in self.factor_contributions
            },
            "portfolio_metrics": {
                "volatility": round(self.portfolio_volatility, 6),
                "var": round(self.portfolio_var, 6),
                "cvar": round(self.portfolio_cvar, 6),
                "systematic_risk": round(self.systematic_risk, 6),
                "idiosyncratic_risk": round(self.idiosyncratic_risk, 6),
                "diversification_ratio": round(self.diversification_ratio, 4),
            },
            "analysis_metadata": {
                "risk_measure": self.risk_measure,
                "confidence_level": self.confidence_level,
                "assets": self.assets,
                "calculation_date": self.calculation_date,
                "lookback_period": self.lookback_period,
            },
        }


class RiskContributionCalculator:
    """
    风险贡献计算器

    提供全面的风险贡献分析:
    - 边际风险贡献
    - 成分风险贡献
    - 因子风险贡献
    - 时间序列分析
    - 风险归因
    """

    def __init__(self, config: Optional[RiskContributionConfig] = None):
        """初始化风险贡献计算器"""
        self.config = config or RiskContributionConfig()

        # 风险指标计算器
        self.risk_calculator = AdvancedRiskMetrics()

        logger.info("Risk Contribution Calculator initialized")

    def calculate_marginal_contributions(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        risk_measure: str = "volatility",
        confidence_level: float = 0.95,
    ) -> RiskContributionAnalysis:
        """
        计算边际风险贡献

        Args:
            returns: 资产回报率
            weights: 投资组合权重
            risk_measure: 风险度量
            confidence_level: 置信水平

        Returns:
            RiskContributionAnalysis: 风险贡献分析结果
        """
        try:
            logger.info(f"Calculating marginal risk contributions using {risk_measure}")

            # 准备数据
            returns_clean = returns.dropna()
            cov_matrix = returns_clean.cov().values * self.config.trading_days_per_year

            # 计算边际贡献
            marginal_results = self._calculate_marginal_contributions_by_measure(
                weights, cov_matrix, returns_clean, risk_measure, confidence_level
            )

            # 计算因子贡献
            factor_results = self._calculate_factor_contributions(
                returns_clean, weights
            )

            # 计算投资组合指标
            portfolio_metrics = self._calculate_portfolio_risk_metrics(
                weights, cov_matrix, returns_clean, risk_measure, confidence_level
            )

            # 计算分解指标
            decomposition = self._calculate_risk_decomposition(cov_matrix, weights)

            # 创建边际贡献对象
            marginal_contributions = []
            for i, asset in enumerate(returns.columns):
                mc = MarginalRiskContribution(
                    asset_name = asset,
                    marginal_contribution = marginal_results["marginal"][i],
                    component_contribution = marginal_results["component"][i],
                    percentage_contribution = marginal_results["percentage"][i],
                    volatility_contribution = marginal_results["volatility"][i],
                    var_contribution = marginal_results["var"][i],
                    cvar_contribution = marginal_results["cvar"][i],
                )
                marginal_contributions.append(mc)

            # 创建因子贡献对象
            factor_contributions = []
            for i, factor_result in enumerate(factor_results):
                fc = FactorRiskContribution(
                    factor_name = factor_result["name"],
                    factor_exposure = factor_result["exposure"],
                    factor_risk = factor_result["risk"],
                    contribution_to_portfolio_risk = factor_result["contribution"],
                    eigenvalue = factor_result.get("eigenvalue"),
                )
                factor_contributions.append(fc)

            # 创建分析结果
            analysis = RiskContributionAnalysis(
                marginal_contributions = marginal_contributions,
                factor_contributions = factor_contributions,
                portfolio_volatility = portfolio_metrics["volatility"],
                portfolio_var = portfolio_metrics["var"],
                portfolio_cvar = portfolio_metrics["cvar"],
                systematic_risk = decomposition["systematic"],
                idiosyncratic_risk = decomposition["idiosyncratic"],
                diversification_ratio = decomposition["diversification_ratio"],
                risk_measure = risk_measure,
                confidence_level = confidence_level,
                assets = list(returns.columns),
                calculation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                lookback_period = len(returns_clean),
            )

            logger.info("Marginal risk contribution calculation completed")
            return analysis

        except Exception as e:
            logger.error(f"Marginal contribution calculation failed: {e}")
            raise

    def calculate_rolling_contributions(
        self, returns: pd.DataFrame, weights: np.ndarray, window: Optional[int] = None
    ) -> pd.DataFrame:
        """
        计算滚动风险贡献

        Args:
            returns: 资产回报率
            weights: 投资组合权重
            window: 滚动窗口

        Returns:
            pd.DataFrame: 滚动风险贡献时间序列
        """
        window = window or self.config.rolling_window
        assets = returns.columns

        contribution_series = []

        for i in range(window, len(returns)):
            window_returns = returns.iloc[i - window : i]

            try:
                # 计算当前窗口的风险贡献
                analysis = self.calculate_marginal_contributions(
                    window_returns, weights, "volatility"
                )

                # 提取边际贡献
                contributions = {
                    "date": returns.index[i],
                    **{
                        f"{asset}_marginal": mc.marginal_contribution
                        for asset, mc in zip(assets, analysis.marginal_contributions)
                    },
                    **{
                        f"{asset}_component": mc.component_contribution
                        for asset, mc in zip(assets, analysis.marginal_contributions)
                    },
                    **{
                        f"{asset}_percentage": mc.percentage_contribution
                        for asset, mc in zip(assets, analysis.marginal_contributions)
                    },
                    "portfolio_volatility": analysis.portfolio_volatility,
                    "diversification_ratio": analysis.diversification_ratio,
                }

                contribution_series.append(contributions)

            except Exception as e:
                logger.warning(
                    f"Rolling contribution calculation failed at index {i}: {e}"
                )
                continue

        return pd.DataFrame(contribution_series).set_index("date")

    def attribution_analysis(
        self,
        returns: pd.DataFrame,
        current_weights: np.ndarray,
        previous_weights: np.ndarray,
        factor_returns: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        风险归因分析

        Args:
            returns: 资产回报率
            current_weights: 当前权重
            previous_weights: 前期权重
            factor_returns: 因子回报率 (可选)

        Returns:
            Dict: 归因分析结果
        """
        try:
            logger.info("Performing risk attribution analysis")

            # 计算两个时期的风险贡献
            current_analysis = self.calculate_marginal_contributions(
                returns, current_weights
            )
            previous_analysis = self.calculate_marginal_contributions(
                returns, previous_weights
            )

            # 权重变化归因
            weight_changes = current_weights - previous_weights
            weight_attribution = self._calculate_weight_attribution(
                weight_changes, current_analysis, previous_analysis
            )

            # 风险因子归因 (如果提供因子回报率)
            factor_attribution = {}
            if factor_returns is not None and SKLEARN_AVAILABLE:
                factor_attribution = self._calculate_factor_attribution(
                    returns, current_weights, factor_returns
                )

            # 波动率归因
            volatility_attribution = self._calculate_volatility_attribution(
                current_analysis, previous_analysis
            )

            attribution_result = {
                "weight_attribution": weight_attribution,
                "factor_attribution": factor_attribution,
                "volatility_attribution": volatility_attribution,
                "current_portfolio_metrics": {
                    "volatility": current_analysis.portfolio_volatility,
                    "diversification_ratio": current_analysis.diversification_ratio,
                },
                "previous_portfolio_metrics": {
                    "volatility": previous_analysis.portfolio_volatility,
                    "diversification_ratio": previous_analysis.diversification_ratio,
                },
                "attribution_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            logger.info("Risk attribution analysis completed")
            return attribution_result

        except Exception as e:
            logger.error(f"Risk attribution analysis failed: {e}")
            raise

    def _calculate_marginal_contributions_by_measure(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray,
        returns: pd.DataFrame,
        risk_measure: str,
        confidence_level: float,
    ) -> Dict[str, np.ndarray]:
        """根据不同风险度量计算边际贡献"""
        len(weights)

        if risk_measure == "volatility":
            return self._volatility_contributions(weights, cov_matrix)
        elif risk_measure == "var":
            return self._var_contributions(
                weights, cov_matrix, returns, confidence_level
            )
        elif risk_measure == "cvar":
            return self._cvar_contributions(
                weights, cov_matrix, returns, confidence_level
            )
        else:
            raise ValueError(f"Unsupported risk measure: {risk_measure}")

    def _volatility_contributions(
        self, weights: np.ndarray, cov_matrix: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """波动率贡献计算"""
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)

        if portfolio_volatility < self.config.epsilon:
            return {
                "marginal": np.zeros_like(weights),
                "component": np.zeros_like(weights),
                "percentage": np.ones_like(weights) / len(weights),
                "volatility": np.zeros_like(weights),
                "var": np.zeros_like(weights),
                "cvar": np.zeros_like(weights),
            }

        # 边际贡献
        marginal_contributions = np.dot(cov_matrix, weights) / portfolio_volatility

        # 成分贡献
        component_contributions = weights * marginal_contributions

        # 百分比贡献
        percentage_contributions = component_contributions / portfolio_variance

        # 为其他风险度量提供占位符
        vol_contributions = component_contributions / portfolio_volatility

        return {
            "marginal": marginal_contributions,
            "component": component_contributions,
            "percentage": percentage_contributions,
            "volatility": vol_contributions,
            "var": component_contributions,  # 简化版本
            "cvar": component_contributions,  # 简化版本
        }

    def _var_contributions(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray,
        returns: pd.DataFrame,
        confidence_level: float,
    ) -> Dict[str, np.ndarray]:
        """VaR贡献计算"""
        # 获取波动率贡献作为基础
        vol_results = self._volatility_contributions(weights, cov_matrix)

        # 计算投资组合VaR
        portfolio_returns = returns @ weights
        portfolio_var = np.percentile(portfolio_returns, (1 - confidence_level) * 100)

        # 使用Cornish - Fisher展开式调整VaR贡献
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        # 调整系数 (简化版本)
        adjustment_factor = (
            1
            + (skewness / 6) * (norm.ppf(confidence_level) ** 2 - 1)
            + (kurtosis / 24)
            * (norm.ppf(confidence_level) ** 3 - 3 * norm.ppf(confidence_level))
        )

        adjusted_contributions = vol_results["component"] * adjustment_factor

        return {
            "marginal": vol_results["marginal"],
            "component": adjusted_contributions,
            "percentage": adjusted_contributions / np.sum(adjusted_contributions),
            "volatility": vol_results["volatility"],
            "var": adjusted_contributions / portfolio_var,
            "cvar": adjusted_contributions,  # 简化版本
        }

    def _cvar_contributions(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray,
        returns: pd.DataFrame,
        confidence_level: float,
    ) -> Dict[str, np.ndarray]:
        """CVaR贡献计算"""
        # 使用Monte Carlo模拟计算CVaR贡献
        num_simulations = min(self.config.monte_carlo_simulations, 5000)  # 限制模拟次数

        # 模拟回报率
        np.random.seed(42)  # 确保可重复性
        simulated_returns = np.random.multivariate_normal(
            np.zeros(len(weights)),
            cov_matrix / self.config.trading_days_per_year,
            num_simulations,
        )

        # 计算投资组合回报
        portfolio_sim_returns = simulated_returns @ weights

        # 计算VaR阈值
        var_threshold = np.percentile(
            portfolio_sim_returns, (1 - confidence_level) * 100
        )

        # 识别超过VaR的情景
        tail_scenarios = portfolio_sim_returns <= var_threshold
        tail_returns = simulated_returns[tail_scenarios]

        if len(tail_returns) == 0:
            # 如果没有尾部情景，返回波动率贡献
            return self._volatility_contributions(weights, cov_matrix)

        # 计算条件期望贡献
        conditional_contributions = np.mean(tail_returns, axis = 0)

        return {
            "marginal": conditional_contributions
            / np.sum(np.abs(conditional_contributions)),
            "component": conditional_contributions,
            "percentage": np.abs(conditional_contributions)
            / np.sum(np.abs(conditional_contributions)),
            "volatility": np.zeros_like(weights),  # 占位符
            "var": conditional_contributions,
            "cvar": conditional_contributions
            / np.mean(portfolio_sim_returns[tail_scenarios]),
        }

    def _calculate_factor_contributions(
        self, returns: pd.DataFrame, weights: np.ndarray
    ) -> List[Dict[str, Any]]:
        """计算因子风险贡献"""
        factor_results = []

        if not SKLEARN_AVAILABLE:
            # 如果没有sklearn，返回简单结果
            num_assets = len(weights)
            for i in range(min(self.config.num_factors, num_assets)):
                factor_results.append(
                    {
                        "name": f"Factor_{i + 1}",
                        "exposure": weights[i] if i < num_assets else 0.0,
                        "risk": 0.1,  # 占位符
                        "contribution": 0.1,  # 占位符
                        "eigenvalue": 1.0,  # 占位符
                    }
                )
            return factor_results

        try:
            # 使用PCA进行因子分析
            pca = PCA(n_components = self.config.num_factors)
            returns_array = returns.values

            # 标准化数据
            standardized_returns = (
                returns_array - np.mean(returns_array, axis = 0)
            ) / np.std(returns_array, axis = 0)

            # 执行PCA
            factor_loadings = pca.fit_transform(standardized_returns.T)

            # 计算因子贡献
            for i in range(self.config.num_factors):
                factor_loading = factor_loadings[:, i]
                factor_exposure = np.dot(weights, factor_loading)

                # 因子风险
                factor_risk = np.sqrt(pca.explained_variance_[i])

                # 对投资组合风险的贡献
                portfolio_factor_risk = factor_exposure * factor_risk

                factor_results.append(
                    {
                        "name": f"PCA_Factor_{i + 1}",
                        "exposure": factor_exposure,
                        "risk": factor_risk,
                        "contribution": portfolio_factor_risk,
                        "eigenvalue": pca.explained_variance_[i],
                    }
                )

        except Exception as e:
            logger.warning(f"Factor contribution calculation failed: {e}")
            # 返回简化结果
            for i in range(min(self.config.num_factors, len(weights))):
                factor_results.append(
                    {
                        "name": f"Simple_Factor_{i + 1}",
                        "exposure": weights[i],
                        "risk": (
                            np.sqrt(np.diag(returns.cov().values)[i])
                            if i < len(weights)
                            else 0.0
                        ),
                        "contribution": (
                            weights[i] * np.sqrt(np.diag(returns.cov().values)[i])
                            if i < len(weights)
                            else 0.0
                        ),
                        "eigenvalue": None,
                    }
                )

        return factor_results

    def _calculate_portfolio_risk_metrics(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray,
        returns: pd.DataFrame,
        risk_measure: str,
        confidence_level: float,
    ) -> Dict[str, float]:
        """计算投资组合风险指标"""
        # 波动率
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)

        # VaR和CVaR (简化版本)
        portfolio_returns = returns @ weights
        var_95 = np.percentile(portfolio_returns, 5)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()

        return {"volatility": portfolio_volatility, "var": var_95, "cvar": cvar_95}

    def _calculate_risk_decomposition(
        self, cov_matrix: np.ndarray, weights: np.ndarray
    ) -> Dict[str, float]:
        """计算风险分解"""
        # 特征值分解
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

        # 系统性风险 (最大特征值对应的方向)
        systematic_risk = eigenvalues[-1] if len(eigenvalues) > 0 else 0.0

        # 特质性风险
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        idiosyncratic_risk = portfolio_variance - systematic_risk

        # 分散化比率
        weighted_volatility = np.sum(weights * np.sqrt(np.diag(cov_matrix)))
        portfolio_volatility = np.sqrt(portfolio_variance)
        diversification_ratio = (
            weighted_volatility / portfolio_volatility
            if portfolio_volatility > 0
            else 1.0
        )

        return {
            "systematic": systematic_risk,
            "idiosyncratic": max(0.0, idiosyncratic_risk),
            "diversification_ratio": diversification_ratio,
        }

    def _calculate_weight_attribution(
        self,
        weight_changes: np.ndarray,
        current_analysis: RiskContributionAnalysis,
        previous_analysis: RiskContributionAnalysis,
    ) -> Dict[str, Any]:
        """计算权重变化归因"""
        # 权重变化对风险贡献的影响
        current_contributions = np.array(
            [
                mc.component_contribution
                for mc in current_analysis.marginal_contributions
            ]
        )
        previous_contributions = np.array(
            [
                mc.component_contribution
                for mc in previous_analysis.marginal_contributions
            ]
        )

        contribution_changes = current_contributions - previous_contributions

        return {
            "weight_changes": weight_changes.tolist(),
            "contribution_changes": contribution_changes.tolist(),
            "attribution_by_asset": {
                asset: {"weight_change": float(wc), "contribution_change": float(cc)}
                for asset, wc, cc in zip(
                    [mc.asset_name for mc in current_analysis.marginal_contributions],
                    weight_changes,
                    contribution_changes,
                )
            },
        }

    def _calculate_factor_attribution(
        self, returns: pd.DataFrame, weights: np.ndarray, factor_returns: pd.DataFrame
    ) -> Dict[str, Any]:
        """计算因子归因"""
        try:
            # 计算资产对因子的暴露
            factor_exposures = []

            for asset in returns.columns:
                asset_returns = returns[asset]
                aligned_data = pd.concat(
                    [asset_returns, factor_returns], axis = 1, join="inner"
                )

                if len(aligned_data) > 10:
                    # 线性回归
                    X = aligned_data.iloc[:, 1:].values
                    y = aligned_data.iloc[:, 0].values
                    X = np.column_stack([np.ones(len(X)), X])

                    try:
                        coefficients = np.linalg.lstsq(X, y, rcond = None)[0]
                        exposure = coefficients[1:]  # 去掉常数项
                    except Exception:
                        exposure = np.zeros(len(factor_returns.columns))
                else:
                    exposure = np.zeros(len(factor_returns.columns))

                factor_exposures.append(exposure)

            factor_exposures = np.array(factor_exposures)

            # 计算投资组合因子暴露
            portfolio_factor_exposure = np.dot(weights, factor_exposures)

            return {
                "asset_factor_exposures": {
                    asset: exposure.tolist()
                    for asset, exposure in zip(returns.columns, factor_exposures)
                },
                "portfolio_factor_exposure": portfolio_factor_exposure.tolist(),
                "factor_names": list(factor_returns.columns),
            }

        except Exception as e:
            logger.warning(f"Factor attribution calculation failed: {e}")
            return {}

    def _calculate_volatility_attribution(
        self,
        current_analysis: RiskContributionAnalysis,
        previous_analysis: RiskContributionAnalysis,
    ) -> Dict[str, Any]:
        """计算波动率归因"""
        vol_change = (
            current_analysis.portfolio_volatility
            - previous_analysis.portfolio_volatility
        )
        div_ratio_change = (
            current_analysis.diversification_ratio
            - previous_analysis.diversification_ratio
        )

        return {
            "volatility_change": vol_change,
            "diversification_ratio_change": div_ratio_change,
            "volatility_attribution_sources": {
                "component_contributions_change": (
                    sum(
                        [
                            mc.component_contribution
                            for mc in current_analysis.marginal_contributions
                        ]
                    )
                    - sum(
                        [
                            mc.component_contribution
                            for mc in previous_analysis.marginal_contributions
                        ]
                    )
                ),
                "diversification_effect": div_ratio_change
                * current_analysis.portfolio_volatility,
            },
        }


# 便利函数
def calculate_risk_contributions(
    returns: pd.DataFrame,
    weights: np.ndarray,
    risk_measure: str = "volatility",
    confidence_level: float = 0.95,
) -> RiskContributionAnalysis:
    """便利函数：计算风险贡献"""
    calculator = RiskContributionCalculator()
    return calculator.calculate_marginal_contributions(
        returns, weights, risk_measure, confidence_level
    )
