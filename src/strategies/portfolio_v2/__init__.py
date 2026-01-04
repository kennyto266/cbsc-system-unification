"""
Portfolio Strategies V2
重構後的組合策略模塊

提供統一的組合策略基類和實現
"""

from .base import BasePortfolioStrategy
from .multi_factor_strategy import MultiFactorStrategy
from .risk_parity_strategy import RiskParityStrategy
from .dynamic_allocation_strategy import DynamicAllocationStrategy
from .multi_asset_optimizer import (
    MultiAssetOptimizer,
    OptimizationMethod,
    OptimizationConstraints,
    BlackLittermanConfig
)
from .dynamic_weight_strategy import (
    DynamicWeightAdjustmentStrategy,
    DynamicWeightConfig,
    MarketRegime,
    RebalanceTrigger
)
from .correlation_analyzer import (
    CorrelationAnalyzer,
    CorrelationConfig,
    CorrelationMethod
)

# 策略註冊字典
PORTFOLIO_STRATEGIES = {
    "multi_factor": MultiFactorStrategy,
    "risk_parity": RiskParityStrategy,
    "dynamic_allocation": DynamicAllocationStrategy
}

__all__ = [
    # Base classes
    "BasePortfolioStrategy",

    # Portfolio strategies
    "MultiFactorStrategy",
    "RiskParityStrategy",
    "DynamicAllocationStrategy",

    # Multi-asset optimization
    "MultiAssetOptimizer",
    "OptimizationMethod",
    "OptimizationConstraints",
    "BlackLittermanConfig",

    # Dynamic weight adjustment
    "DynamicWeightAdjustmentStrategy",
    "DynamicWeightConfig",
    "MarketRegime",
    "RebalanceTrigger",

    # Correlation analysis
    "CorrelationAnalyzer",
    "CorrelationConfig",
    "CorrelationMethod",

    # Registry
    "PORTFOLIO_STRATEGIES"
]