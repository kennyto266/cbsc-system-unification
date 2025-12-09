"""Strategy management and optimization system for Hong Kong quantitative trading.

This package provides comprehensive strategy lifecycle management, automated
optimization, and performance evaluation capabilities for the AI Agent trading system.
"""

from .strategy_deployer import (
    DeploymentConfig,
    DeploymentStatus,
    RollbackStrategy,
    StrategyDeployer,
)
from .strategy_evaluator import (
    DrawdownAnalysis,
    EvaluationMetrics,
    PerformanceComparison,
    RiskMetrics,
    StrategyEvaluator,
)
from .strategy_manager import (
    OptimizationMethod,
    StrategyConfig,
    StrategyManager,
    StrategyStatus,
    StrategyType,
)
from .strategy_monitor import (
    MonitoringConfig,
    PerformanceAlert,
    StrategyHealth,
    StrategyMonitor,
)
from .strategy_optimizer import (
    FitnessFunction,
    OptimizationAlgorithm,
    OptimizationResult,
    ParameterSpace,
    StrategyOptimizer,
)

__all__ = [
    # Strategy management
    "StrategyManager",
    "StrategyConfig",
    "StrategyStatus",
    "StrategyType",
    "OptimizationMethod",
    # Strategy optimization
    "StrategyOptimizer",
    "OptimizationResult",
    "ParameterSpace",
    "OptimizationAlgorithm",
    "FitnessFunction",
    # Strategy evaluation
    "StrategyEvaluator",
    "EvaluationMetrics",
    "PerformanceComparison",
    "RiskMetrics",
    "DrawdownAnalysis",
    # Strategy deployment
    "StrategyDeployer",
    "DeploymentConfig",
    "DeploymentStatus",
    "RollbackStrategy",
    # Strategy monitoring
    "StrategyMonitor",
    "MonitoringConfig",
    "PerformanceAlert",
    "StrategyHealth",
]
