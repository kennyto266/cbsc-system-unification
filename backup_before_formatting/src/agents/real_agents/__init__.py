"""Real AI Agents module for Hong Kong quantitative trading system.

This module provides real data - driven AI agents that replace the simulated agents
with actual market data analysis, machine learning models, and intelligent decision making.
"""

from .base_real_agent import BaseRealAgent, RealAgentConfig, RealAgentStatus
from .ml_integration import MLModelManager, ModelPerformance, ModelType
from .real_data_analyzer import AnalysisResult, RealDataAnalyzer, SignalStrength
from .real_data_scientist import (
    AnomalyDetection,
    AnomalyType,
    Feature,
    FeatureEngineering,
    FeatureType,
    MLModel,
    ModelStatus,
    RealDataScientist,
)
from .real_portfolio_manager import (
    Asset,
    AssetClass,
    OptimizationMethod,
    Portfolio,
    RealPortfolioManager,
    RebalanceDecision,
    RebalanceTrigger,
    RiskBudget,
)
from .real_quantitative_analyst import (
    QuantitativeAnalysisResult,
    RealQuantitativeAnalyst,
)
from .real_quantitative_engineer import (
    AlertSeverity,
    ComponentType,
    OptimizationRecommendation,
    PerformanceMetric,
    RealQuantitativeEngineer,
    SystemAlert,
    SystemComponent,
    SystemStatus,
)
from .real_quantitative_trader import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    RealQuantitativeTrader,
    TradingPerformance,
    TradingSignal,
    TradingStrategy,
)
from .real_research_analyst import (
    Factor,
    FactorType,
    HypothesisStatus,
    LiteratureReview,
    RealResearchAnalyst,
    ResearchHypothesis,
    ResearchType,
    StrategyResearch,
)
from .real_risk_analyst import (
    AlertLevel,
    RealRiskAnalyst,
    RiskAlert,
    RiskLevel,
    RiskMetric,
    RiskType,
    StressTestScenario,
    VaRAnalysis,
)

__all__ = [
    # Base classes
    "BaseRealAgent",
    "RealAgentConfig",
    "RealAgentStatus",
    # Data analysis
    "RealDataAnalyzer",
    "AnalysisResult",
    "SignalStrength",
    # Machine learning
    "MLModelManager",
    "ModelType",
    "ModelPerformance",
    # Real agents
    "RealQuantitativeAnalyst",
    "QuantitativeAnalysisResult",
    "RealQuantitativeTrader",
    "TradingSignal",
    "Order",
    "Position",
    "TradingStrategy",
    "TradingPerformance",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "RealPortfolioManager",
    "Asset",
    "Portfolio",
    "RiskBudget",
    "RebalanceDecision",
    "AssetClass",
    "OptimizationMethod",
    "RebalanceTrigger",
    "RealRiskAnalyst",
    "RiskMetric",
    "RiskAlert",
    "StressTestScenario",
    "VaRAnalysis",
    "RiskLevel",
    "RiskType",
    "AlertLevel",
    "RealDataScientist",
    "Feature",
    "MLModel",
    "AnomalyDetection",
    "FeatureEngineering",
    "ModelStatus",
    "FeatureType",
    "AnomalyType",
    "RealQuantitativeEngineer",
    "PerformanceMetric",
    "SystemAlert",
    "SystemComponent",
    "OptimizationRecommendation",
    "SystemStatus",
    "AlertSeverity",
    "ComponentType",
    "RealResearchAnalyst",
    "ResearchHypothesis",
    "Factor",
    "StrategyResearch",
    "LiteratureReview",
    "ResearchType",
    "HypothesisStatus",
    "FactorType",
]
