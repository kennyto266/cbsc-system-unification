import pandas as pd
"""
機器學習模塊 - 生產級別港股量化交易ML / DL系統
完整的高級機器學習和深度學習集成平台

功能模塊:
- 特徵工程和存儲 (FeatureStore, AdvancedFeatureStore)
- 模型註冊和管理 (ModelRegistry, ModelDeployment)
- 高級交易模型 (PricePredictor, VolatilityForecaster, MarketRegimeDetector)
- 深度學習模型 (LSTM, Transformer, RL Agents)
- 強化學習系統 (MultiAgent, DQN, PPO, A3C)
- 流水線編排 (MLPipeline, Training, Evaluation)
- 監控和漂移檢測 (MLMonitoring, DataDrift, PerformanceTracking)
- 統一編排器 (MLOrchestrator, InferenceService)
"""

# 核心特徵工程
from .feature_store import (
    AdvancedFeatureStore,
    FeatureCalculator,
    FeatureQualityMonitor,
    FeatureRegistry,
    FeatureType,
    TimeFrame,
)

# 監控系統
from .ml_monitoring import (
    Alert,
    AlertManager,
    AlertSeverity,
    DataDriftDetector,
    DriftDetectionResult,
    DriftType,
    MLMonitoringSystem,
    ModelPerformanceMonitor,
    MonitoringMetric,
)

# 統一編排器
from .ml_orchestrator import (
    InferenceMode,
    MLModelOrchestrator,
    PredictionRequest,
    PredictionResponse,
    SystemMode,
    SystemStatus,
)

# ML流水線
from .ml_pipeline import (
    DataProcessor,
    ModelEvaluator,
    ModelTrainer,
    PipelineConfig,
    PipelineOrchestrator,
    PipelineResult,
    PipelineStatus,
    PipelineType,
)

# 模型註冊和管理
from .model_registry import (
    AutoMLManager,
    DeploymentStrategy,
    ModelMetadata,
    ModelMetrics,
    ModelPerformanceMonitor,
    ModelRegistry,
    ModelStatus,
    ModelVersion,
)

# 強化學習
from .reinforcement_learning import (
    ActionType,
    AgentAction,
    AgentMetrics,
    AgentType,
    DQNAgent,
    MultiAgentSystem,
    PPOAgent,
    RLTrainingManager,
    TradingEnvironment,
)

# 高級交易模型
from .trading_models import (
    AdvancedPricePredictor,
    MarketRegimeDetector,
    ModelCategory,
    ModelPrediction,
    PredictionHorizon,
    RiskMetrics,
    SentimentAnalyzer,
    VolatilityForecaster,
)

# 向後兼容 - 舊版本組件
try:
    from .prediction_engine import MLPredictionEngine
except ImportError:
    MLPredictionEngine = None

try:
    from .price_predictor import PricePredictor
except ImportError:
    PricePredictor = None

try:
    from .trend_analyzer import TrendAnalyzer
except ImportError:
    TrendAnalyzer = None

try:
    from .anomaly_detector import AnomalyDetector
except ImportError:
    AnomalyDetector = None

try:
    from .risk_predictor import RiskPredictor
except ImportError:
    RiskPredictor = None

# 公開API - 主要組件
__all__ = [
    # 核心系統
    "MLModelOrchestrator",
    "AdvancedFeatureStore",
    "ModelRegistry",
    "MLMonitoringSystem",
    # 特徵工程
    "FeatureRegistry",
    "FeatureCalculator",
    "FeatureType",
    "TimeFrame",
    # 模型管理
    "ModelMetadata",
    "ModelVersion",
    "ModelMetrics",
    "ModelStatus",
    "DeploymentStrategy",
    "AutoMLManager",
    # 交易模型
    "AdvancedPricePredictor",
    "VolatilityForecaster",
    "MarketRegimeDetector",
    "SentimentAnalyzer",
    "ModelPrediction",
    "RiskMetrics",
    "ModelCategory",
    "PredictionHorizon",
    # 強化學習
    "TradingEnvironment",
    "DQNAgent",
    "PPOAgent",
    "MultiAgentSystem",
    "RLTrainingManager",
    "AgentAction",
    "AgentMetrics",
    "ActionType",
    "AgentType",
    # 流水線
    "PipelineOrchestrator",
    "DataProcessor",
    "ModelTrainer",
    "ModelEvaluator",
    "PipelineConfig",
    "PipelineResult",
    "PipelineStatus",
    "PipelineType",
    # 監控
    "DataDriftDetector",
    "ModelPerformanceMonitor",
    "AlertManager",
    "DriftDetectionResult",
    "Alert",
    "AlertSeverity",
    "DriftType",
    "MonitoringMetric",
    # 接口
    "PredictionRequest",
    "PredictionResponse",
    "SystemStatus",
    "SystemMode",
    "InferenceMode",
    # 向後兼容
    "MLPredictionEngine",
    "PricePredictor",
    "TrendAnalyzer",
    "AnomalyDetector",
    "RiskPredictor",
]

# 版本和依賴信息
__version__ = "4.0.0"
__author__ = "Hong Kong Quantitative Trading Team"
__description__ = "Production - Grade ML / DL System for Hong Kong Trading"


# 可用性檢查
def check_dependencies():
    """檢查可選依賴的可用性"""
    deps = {
        "tensorflow": False,
        "torch": False,
        "mlflow": False,
        "evidently": False,
        "alibi_detect": False,
        "river": False,
        "prometheus_client": False,
        "prefect": False,
        "kfp": False,
        "ray": False,
        "stable_baselines3": False,
        "optuna": False,
        "arch": False,
        "transformers": False,
    }

    try:
        import tensorflow

        deps["tensorflow"] = True
    except ImportError:
        pass

    try:
        import torch

        deps["torch"] = True
    except ImportError:
        pass

    try:
        import mlflow

        deps["mlflow"] = True
    except ImportError:
        pass

    try:
        import evidently

        deps["evidently"] = True
    except ImportError:
        pass

    try:
        import alibi_detect

        deps["alibi_detect"] = True
    except ImportError:
        pass

    try:
        import river

        deps["river"] = True
    except ImportError:
        pass

    try:
        import prometheus_client

        deps["prometheus_client"] = True
    except ImportError:
        pass

    try:
        import prefect

        deps["prefect"] = True
    except ImportError:
        pass

    try:
        import kfp

        deps["kfp"] = True
    except ImportError:
        pass

    try:
        import ray

        deps["ray"] = True
    except ImportError:
        pass

    try:
        import stable_baselines3

        deps["stable_baselines3"] = True
    except ImportError:
        pass

    try:
        import optuna

        deps["optuna"] = True
    except ImportError:
        pass

    try:
        import arch

        deps["arch"] = True
    except ImportError:
        pass

    try:
        import transformers

        deps["transformers"] = True
    except ImportError:
        pass

    return deps


# 系統信息
DEPENDENCIES = check_dependencies()

# 組件狀態
COMPONENT_STATUS = {
    "feature_store": "active",
    "model_registry": "active",
    "trading_models": "active",
    "reinforcement_learning": "active" if DEPENDENCIES["torch"] else "limited",
    "ml_pipeline": "active",
    "ml_monitoring": "active" if DEPENDENCIES["evidently"] else "limited",
    "ml_orchestrator": "active",
    "deep_learning": (
        "active"
        if DEPENDENCIES["tensorflow"] or DEPENDENCIES["torch"]
        else "unavailable"
    ),
    "auto_ml": "active" if DEPENDENCIES["optuna"] else "limited",
    "nlp": "active" if DEPENDENCIES["transformers"] else "unavailable",
    "time_series": "active" if DEPENDENCIES["arch"] else "limited",
}


def get_system_info():
    """獲取系統信息"""
    return {
        "version": __version__,
        "dependencies": DEPENDENCIES,
        "component_status": COMPONENT_STATUS,
        "description": __description__,
        "author": __author__,
    }


# 初始化日誌
import logging

logger = logging.getLogger(__name__)
logger.info(f"ML Module v{__version__} initialized")
logger.info(
    f"Available components: {sum(1 for status in COMPONENT_STATUS.values() if status == 'active')}/{len(COMPONENT_STATUS)}"
)
if not all(DEPENDENCIES.values()):
    missing_deps = [dep for dep, available in DEPENDENCIES.items() if not available]
    logger.warning(f"Optional dependencies not available: {missing_deps}")

# 全局實例 (懶加載)
_global_orchestrator = None


def get_ml_orchestrator():
    """獲取全局ML編排器實例"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = MLModelOrchestrator()
    return _global_orchestrator


# 快速開始函數
async def quick_start(
    symbols: List[str],
    mode: SystemMode = SystemMode.DEVELOPMENT,
    enable_monitoring: bool = True,
):
    """快速啟動ML系統"""
    orchestrator = get_ml_orchestrator()
    orchestrator.system_mode = mode

    # 啟動系統
    tasks = await orchestrator.start_system()

    # 添加模型監控
    if enable_monitoring:
        for symbol in symbols:
            orchestrator.add_model_for_monitoring(
                f"{symbol}_price_predictor", pd.DataFrame()
            )

    logger.info(f"ML System started in {mode.value} mode for symbols: {symbols}")
    return orchestrator, tasks
