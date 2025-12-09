#!/usr/bin/env python3
"""
Multi-Objective Portfolio Optimization - Custom Objective Functions
多目标投资组合优化 - 自定义目标函数库

Professional collection of objective functions for multi-objective portfolio optimization:
- Performance metrics (Sharpe, Sortino, Calmar)
- Risk metrics (VaR, CVaR, Maximum Drawdown)
- Utility functions and behavioral objectives
- ESG and sustainability objectives
- Trading cost and turnover objectives
- Integrated risk-return objectives
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    from scipy import stats
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Some objective functions may not work")

try:
    from .risk_metrics import AdvancedRiskMetrics, RiskMetricsConfig
    RISK_METRICS_AVAILABLE = True
except ImportError:
    RISK_METRICS_AVAILABLE = False
    logging.warning("Advanced risk metrics not available")

logger = logging.getLogger(__name__)

@dataclass
class ObjectiveConfig:
    """目标函数配置"""
    # 基本参数
    risk_free_rate: float = 0.03  # 无风险利率
    trading_days_per_year: int = 252  # 交易日数

    # 性能指标参数
    benchmark_return: Optional[float] = None  # 基准回报率
    confidence_level: float = 0.95  # VaR/CVaR置信水平

    # 风险厌恶
    risk_aversion: float = 1.0  # 风险厌恶系数
    skewness_preference: float = 0.0  # 偏度偏好
    kurtosis_aversion: float = 0.0  # 峰度厌恶

    # 交易成本
    trading_cost_rate: float = 0.001  # 交易成本率
    turnover_penalty: float = 0.01  # 换手率惩罚

    # ESG参数
    esg_scores: Optional[np.ndarray] = None  # ESG评分
    esg_weight: float = 0.1  # ESG权重

    # 约束
    max_turnover: float = 1.0  # 最大换手率
    min_diversification: float = 0.5  # 最小分散度

class PortfolioObjective:
    """投资组合目标函数基类"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        self.config = config or ObjectiveConfig()
        self.name = self.__class__.__name__
        self.direction = "minimize"  # minimize or maximize

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """评估目标函数值"""
        raise NotImplementedError("Subclasses must implement evaluate method")

    def gradient(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> np.ndarray:
        """计算目标函数梯度"""
        # 默认数值梯度
        return self._numerical_gradient(weights, returns, **kwargs)

    def _numerical_gradient(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> np.ndarray:
        """数值梯度计算"""
        epsilon = 1e-8
        gradient = np.zeros_like(weights)
        base_value = self.evaluate(weights, returns, **kwargs)

        for i in range(len(weights)):
            weights_plus = weights.copy()
            weights_plus[i] += epsilon
            value_plus = self.evaluate(weights_plus, returns, **kwargs)
            gradient[i] = (value_plus - base_value) / epsilon

        return gradient

class SharpeRatioObjective(PortfolioObjective):
    """夏普比率目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "maximize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算负夏普比率（用于最小化）"""
        portfolio_returns = (returns * weights).sum(axis=1)

        # 年化指标
        mean_return = portfolio_returns.mean() * self.config.trading_days_per_year
        volatility = portfolio_returns.std() * np.sqrt(self.config.trading_days_per_year)

        if volatility < 1e-8:
            return -np.inf

        sharpe_ratio = (mean_return - self.config.risk_free_rate) / volatility

        # 返回负值用于最小化
        return -sharpe_ratio

class SortinoRatioObjective(PortfolioObjective):
    """索提诺比率目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "maximize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算负索提诺比率（用于最小化）"""
        portfolio_returns = (returns * weights).sum(axis=1)

        # 年化指标
        mean_return = portfolio_returns.mean() * self.config.trading_days_per_year

        # 下行波动率
        downside_returns = portfolio_returns[portfolio_returns < 0]
        if len(downside_returns) == 0:
            return -np.inf

        downside_volatility = downside_returns.std() * np.sqrt(self.config.trading_days_per_year)

        if downside_volatility < 1e-8:
            return -np.inf

        sortino_ratio = (mean_return - self.config.risk_free_rate) / downside_volatility

        # 返回负值用于最小化
        return -sortino_ratio

class CalmarRatioObjective(PortfolioObjective):
    """卡尔马比率目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "maximize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算负卡尔马比率（用于最小化）"""
        portfolio_returns = (returns * weights).sum(axis=1)

        # 年化回报
        annual_return = portfolio_returns.mean() * self.config.trading_days_per_year

        # 最大回撤
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        if max_drawdown > -1e-8:
            return -np.inf

        calmar_ratio = annual_return / abs(max_drawdown)

        # 返回负值用于最小化
        return -calmar_ratio

class ValueAtRiskObjective(PortfolioObjective):
    """风险价值目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "minimize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算VaR"""
        portfolio_returns = (returns * weights).sum(axis=1)

        # 历史VaR
        var = np.percentile(portfolio_returns, (1 - self.config.confidence_level) * 100)

        # 年化VaR
        annual_var = var * np.sqrt(self.config.trading_days_per_year)

        return annual_var

class ExpectedShortfallObjective(PortfolioObjective):
    """期望短缺目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "minimize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算CVaR/ES"""
        portfolio_returns = (returns * weights).sum(axis=1)

        # VaR阈值
        var_threshold = np.percentile(portfolio_returns, (1 - self.config.confidence_level) * 100)

        # 超过VaR的期望损失
        tail_losses = portfolio_returns[portfolio_returns <= var_threshold]
        if len(tail_losses) == 0:
            return var_threshold

        expected_shortfall = tail_losses.mean()

        # 年化
        annual_es = expected_shortfall * np.sqrt(self.config.trading_days_per_year)

        return annual_es

class MaximumDrawdownObjective(PortfolioObjective):
    """最大回撤目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "minimize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算最大回撤"""
        portfolio_returns = (returns * weights).sum(axis=1)

        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        return max_drawdown

class VarianceObjective(PortfolioObjective):
    """方差目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "minimize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算投资组合方差"""
        # 计算协方差矩阵
        cov_matrix = returns.cov() * self.config.trading_days_per_year

        # 投资组合方差
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))

        return portfolio_variance

class ExpectedReturnObjective(PortfolioObjective):
    """期望回报目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "maximize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算期望回报"""
        portfolio_returns = (returns * weights).sum(axis=1)

        # 年化期望回报
        annual_return = portfolio_returns.mean() * self.config.trading_days_per_year

        # 返回负值用于最小化
        return -annual_return

class SkewnessObjective(PortfolioObjective):
    """偏度目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "maximize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算偏度"""
        portfolio_returns = (returns * weights).sum(axis=1)

        # 计算偏度
        skewness = stats.skew(portfolio_returns)

        # 根据偏好调整
        adjusted_skewness = skewness * (1 + self.config.skewness_preference)

        # 返回负值用于最小化
        return -adjusted_skewness

class KurtosisObjective(PortfolioObjective):
    """峰度目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "minimize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算峰度"""
        portfolio_returns = (returns * weights).sum(axis=1)

        # 计算超额峰度
        kurtosis = stats.kurtosis(portfolio_returns)

        # 根据厌恶程度调整
        adjusted_kurtosis = kurtosis * (1 + self.config.kurtosis_aversion)

        return adjusted_kurtosis

class TradingCostObjective(PortfolioObjective):
    """交易成本目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "minimize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算交易成本"""
        # 如果没有提供前一个权重，使用等权重
        previous_weights = kwargs.get('previous_weights', np.ones(len(weights)) / len(weights))

        # 计算换手率
        turnover = np.sum(np.abs(weights - previous_weights)) / 2

        # 交易成本
        trading_cost = turnover * self.config.trading_cost_rate

        return trading_cost

class DiversificationObjective(PortfolioObjective):
    """分散化目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "minimize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算分散化惩罚"""
        # 负的赫芬达尔指数作为分散化指标
        herfindahl_index = np.sum(weights ** 2)

        # 分散化惩罚（负值）
        diversification_penalty = -herfindahl_index

        # 确保满足最小分散度要求
        if herfindahl_index > 1 / self.config.min_diversification:
            penalty = (herfindahl_index - 1 / self.config.min_diversification) * 1000
            diversification_penalty -= penalty

        return diversification_penalty

class ESGObjective(PortfolioObjective):
    """ESG目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "maximize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算ESG评分"""
        if self.config.esg_scores is None:
            return 0.0

        # 加权ESG评分
        esg_score = np.sum(weights * self.config.esg_scores)

        # 返回负值用于最小化
        return -esg_score * self.config.esg_weight

class UtilityObjective(PortfolioObjective):
    """效用函数目标函数"""

    def __init__(self, config: Optional[ObjectiveConfig] = None):
        super().__init__(config)
        self.direction = "maximize"

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算期望效用"""
        portfolio_returns = (returns * weights).sum(axis=1)

        # 年化回报和方差
        annual_return = portfolio_returns.mean() * self.config.trading_days_per_year
        annual_variance = portfolio_returns.var() * self.config.trading_days_per_year

        # 均值方差效用
        utility = annual_return - 0.5 * self.config.risk_aversion * annual_variance

        # 返回负值用于最小化
        return -utility

class IntegratedObjective(PortfolioObjective):
    """综合目标函数"""

    def __init__(self, objectives: List[PortfolioObjective], weights: Optional[List[float]] = None):
        super().__init__()
        self.objectives = objectives
        self.weights = weights or [1.0] * len(objectives)

        # 确保权重和为1
        total_weight = sum(self.weights)
        if total_weight != 0:
            self.weights = [w / total_weight for w in self.weights]

    def evaluate(self, weights: np.ndarray, returns: pd.DataFrame, **kwargs) -> float:
        """计算加权综合目标值"""
        total_value = 0.0

        for objective, weight in zip(self.objectives, self.weights):
            value = objective.evaluate(weights, returns, **kwargs)

            # 如果目标是最大化，转换符号
            if objective.direction == "maximize":
                value = -value

            total_value += weight * value

        return total_value

class ObjectiveFactory:
    """目标函数工厂"""

    @staticmethod
    def create_objective(name: str, config: Optional[ObjectiveConfig] = None, **kwargs) -> PortfolioObjective:
        """创建目标函数实例"""
        objectives = {
            'sharpe': SharpeRatioObjective,
            'sortino': SortinoRatioObjective,
            'calmar': CalmarRatioObjective,
            'var': ValueAtRiskObjective,
            'cvar': ExpectedShortfallObjective,
            'max_drawdown': MaximumDrawdownObjective,
            'variance': VarianceObjective,
            'return': ExpectedReturnObjective,
            'skewness': SkewnessObjective,
            'kurtosis': KurtosisObjective,
            'trading_cost': TradingCostObjective,
            'diversification': DiversificationObjective,
            'esg': ESGObjective,
            'utility': UtilityObjective
        }

        if name not in objectives:
            raise ValueError(f"Unknown objective: {name}. Available: {list(objectives.keys())}")

        return objectives[name](config, **kwargs)

    @staticmethod
    def get_available_objectives() -> Dict[str, Dict[str, str]]:
        """获取可用目标函数信息"""
        objectives = {
            'sharpe': {
                'name': 'Sharpe Ratio',
                'description': 'Risk-adjusted return measure',
                'direction': 'maximize',
                'category': 'performance'
            },
            'sortino': {
                'name': 'Sortino Ratio',
                'description': 'Downside risk-adjusted return',
                'direction': 'maximize',
                'category': 'performance'
            },
            'calmar': {
                'name': 'Calmar Ratio',
                'description': 'Return to maximum drawdown ratio',
                'direction': 'maximize',
                'category': 'performance'
            },
            'var': {
                'name': 'Value at Risk',
                'description': 'Quantile-based risk measure',
                'direction': 'minimize',
                'category': 'risk'
            },
            'cvar': {
                'name': 'Conditional Value at Risk',
                'description': 'Expected shortfall beyond VaR',
                'direction': 'minimize',
                'category': 'risk'
            },
            'max_drawdown': {
                'name': 'Maximum Drawdown',
                'description': 'Maximum peak-to-trough decline',
                'direction': 'minimize',
                'category': 'risk'
            },
            'variance': {
                'name': 'Portfolio Variance',
                'description': 'Traditional risk measure',
                'direction': 'minimize',
                'category': 'risk'
            },
            'return': {
                'name': 'Expected Return',
                'description': 'Portfolio expected return',
                'direction': 'maximize',
                'category': 'return'
            },
            'skewness': {
                'name': 'Skewness',
                'description': 'Third moment of distribution',
                'direction': 'maximize',
                'category': 'higher_moments'
            },
            'kurtosis': {
                'name': 'Kurtosis',
                'description': 'Fourth moment of distribution',
                'direction': 'minimize',
                'category': 'higher_moments'
            },
            'trading_cost': {
                'name': 'Trading Cost',
                'description': 'Portfolio turnover cost',
                'direction': 'minimize',
                'category': 'cost'
            },
            'diversification': {
                'name': 'Diversification',
                'description': 'Portfolio diversification benefit',
                'direction': 'maximize',
                'category': 'diversification'
            },
            'esg': {
                'name': 'ESG Score',
                'description': 'Environmental, Social, Governance score',
                'direction': 'maximize',
                'category': 'esg'
            },
            'utility': {
                'name': 'Utility Function',
                'description': 'Mean-variance utility',
                'direction': 'maximize',
                'category': 'utility'
            }
        }

        return objectives

# 便利函数
def create_sharpe_objective(config: Optional[ObjectiveConfig] = None) -> SharpeRatioObjective:
    """创建夏普比率目标函数"""
    return SharpeRatioObjective(config)

def create_risk_objective(risk_type: str = 'var', config: Optional[ObjectiveConfig] = None) -> PortfolioObjective:
    """创建风险目标函数"""
    factory = ObjectiveFactory()
    return factory.create_objective(risk_type, config)

def create_multi_objective(objective_names: List[str], weights: Optional[List[float]] = None,
                         config: Optional[ObjectiveConfig] = None) -> IntegratedObjective:
    """创建多目标函数"""
    factory = ObjectiveFactory()
    objectives = [factory.create_objective(name, config) for name in objective_names]
    return IntegratedObjective(objectives, weights)