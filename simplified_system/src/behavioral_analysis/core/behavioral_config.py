#!/usr / bin / env python3
"""
第4阶段：行为分析层 - 核心配置模块
Phase 4: Behavioral Analysis Layer - Core Configuration Module

香港量化交易系统最复杂的行为分析层配置
Includes ML models, time series analysis, anomaly detection, and pattern recognition
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

import numpy as np


class MarketRegime(Enum):
    """市场状态枚举"""

    BULL_MARKET = "bull_market"  # 牛市
    BEAR_MARKET = "bear_market"  # 熊市
    SIDEWAYS = "sideways"  # 横盘
    HIGH_VOLATILITY = "high_volatility"  # 高波动
    LOW_VOLATILITY = "low_volatility"  # 低波动


class TradingSession(Enum):
    """香港交易时段枚举"""

    PRE_MARKET = "pre_market"  # 盘前 9:00 - 9:30
    MORNING_SESSION = "morning"  # 早市 9:30 - 12:00
    LUNCH_BREAK = "lunch"  # 午休 12:00 - 1:00
    AFTERNOON_SESSION = "afternoon"  # 午市 1:00 - 4:00
    AFTER_MARKET = "after_market"  # 盘后 4:00 - 5:00


class AnomalyType(Enum):
    """异常类型枚举"""

    PRICE_SPIKE = "price_spike"  # 价格异常
    VOLUME_SURGE = "volume_surge"  # 成交量异常
    VOLATILITY_BURST = "volatility_burst"  # 波动率异常
    PATTERN_DEVIATION = "pattern_deviation"  # 模式偏离
    CORRELATION_BREAK = "correlation_break"  # 相关性断裂
    LIQUIDITY_CRISIS = "liquidity_crisis"  # 流动性危机


@dataclass
class TimeSeriesConfig:
    """时间序列分析配置"""

    # Seasonal decomposition settings
    seasonal_period: int = 252  # 交易日季节周期
    seasonal_model: str = "additive"  # additive or multiplicative
    trend_method: str = "hp_filter"  # hp_filter, linear, polynomial

    # STL decomposition parameters
    stl_seasonal: int = 7
    stl_trend: int = 21
    stl_robust: bool = True

    # Hodrick - Prescott filter parameters
    hp_lambda: float = 1600  # For monthly data, adjust for daily

    # Structural break detection
    break_detection_method: str = "chow"  # chow, cusum, bayes
    min_segment_length: int = 30
    significance_level: float = 0.05


@dataclass
class IntradayPatternConfig:
    """盘中模式识别配置"""

    # Time windows for analysis (in minutes)
    short_window: int = 5
    medium_window: int = 15
    long_window: int = 60

    # Volatility windows
    vol_short_window: int = 10
    vol_medium_window: int = 30
    vol_long_window: int = 100

    # Trading session analysis
    session_analysis_enabled: bool = True
    lunch_time_analysis: bool = True
    month_end_analysis: bool = True

    # Pattern recognition thresholds
    pattern_similarity_threshold: float = 0.85
    min_pattern_length: int = 20
    max_pattern_length: int = 100


@dataclass
class MLModelConfig:
    """机器学习模型配置"""

    # Isolation Forest parameters
    isolation_n_estimators: int = 100
    isolation_contamination: float = 0.1
    isolation_max_features: float = 0.8

    # One - Class SVM parameters
    svm_kernel: str = "rbf"
    svm_gamma: str = "scale"
    svm_nu: float = 0.1

    # Local Outlier Factor parameters
    lof_n_neighbors: int = 20
    lof_contamination: float = 0.1
    lof_novelty: bool = True

    # Random Forest parameters
    rf_n_estimators: int = 200
    rf_max_depth: Optional[int] = None
    rf_min_samples_split: int = 5
    rf_min_samples_leaf: int = 2

    # Gradient Boosting parameters
    gb_n_estimators: int = 200
    gb_learning_rate: float = 0.05
    gb_max_depth: int = 6
    gb_subsample: float = 0.8

    # Neural Network parameters
    nn_hidden_layers: List[int] = field(default_factory = lambda: [128, 64, 32])
    nn_activation: str = "relu"
    nn_dropout: float = 0.2
    nn_learning_rate: float = 0.001
    nn_epochs: int = 100
    nn_batch_size: int = 32


@dataclass
class EnsembleConfig:
    """集成方法配置"""

    # Voting strategy weights
    isolation_weight: float = 0.25
    svm_weight: float = 0.20
    lof_weight: float = 0.20
    rf_weight: float = 0.15
    gb_weight: float = 0.15
    nn_weight: float = 0.05

    # Ensemble threshold
    ensemble_threshold: float = 0.5
    confidence_calibration: bool = True

    # Feature importance
    feature_importance_enabled: bool = True
    top_features_count: int = 20


@dataclass
class HistoricalPatternConfig:
    """历史模式比较配置"""

    # Baseline establishment
    baseline_window: int = 252  # 1 year of trading data
    baseline_min_quality: float = 0.8

    # Pattern similarity metrics
    similarity_methods: List[str] = field(
        default_factory = lambda: ["cosine", "dtw", "pearson", "euclidean", "manhattan"]
    )

    # Dynamic Time Warping parameters
    dtw_window: int = 10
    dtw_constraint: str = "sakoe_chiba"

    # Regime change detection
    regime_change_method: str = "bayesian_changepoint"
    min_regime_length: int = 30
    regime_confidence_threshold: float = 0.7

    # Pattern matching
    pattern_match_threshold: float = 0.8
    max_pattern_matches: int = 10


@dataclass
class RealTimeMonitoringConfig:
    """实时行为监控配置"""

    # Sliding windows
    short_window_size: int = 100
    medium_window_size: int = 500
    long_window_size: int = 1000

    # Prediction horizon
    prediction_horizon: int = 10  # Predict 10 points ahead

    # Adaptive thresholds
    adaptive_threshold_enabled: bool = True
    learning_rate: float = 0.01
    decay_factor: float = 0.99

    # Early warning system
    warning_threshold: float = 0.7
    critical_threshold: float = 0.9

    # Alert cooldown (in seconds)
    alert_cooldown: int = 300

    # Real - time processing
    max_processing_time_ms: int = 5
    buffer_size: int = 10000


@dataclass
class HongKongMarketConfig:
    """香港市场特定配置"""

    # HSI constituents for analysis
    hsi_constituents: List[str] = field(
        default_factory = lambda: [
            "0700.HK",  # Tencent
            "0941.HK",  # China Mobile
            "1299.HK",  # AIA
            "0388.HK",  # HKEX
            "2318.HK",  # Ping An Insurance
            "0005.HK",  # HSBC
            "0398.HK",  # Bank of China
            "1398.HK",  # ICBC
            "0939.HK",  # CCB
            "0002.HK",  # CLP Holdings
        ]
    )

    # Trading hours (Hong Kong Time)
    market_open_time: str = "09:30"
    market_close_time: str = "16:00"
    lunch_start_time: str = "12:00"
    lunch_end_time: str = "13:00"

    # Hong Kong specific patterns
    lunchtime_volatility_analysis: bool = True
    mainland_influence_analysis: bool = True
    typhoon_impact_analysis: bool = True
    holiday_season_analysis: bool = True

    # IPO and delisting events
    event_impact_window: int = 5  # days before / after events

    # Cross - market correlations
    mainland_correlation_enabled: bool = True
    us_market_correlation_enabled: bool = True


@dataclass
class BehavioralAnalysisConfig:
    """行为分析层主配置"""

    # Component configurations
    time_series: TimeSeriesConfig = field(default_factory = TimeSeriesConfig)
    intraday_pattern: IntradayPatternConfig = field(
        default_factory = IntradayPatternConfig
    )
    ml_models: MLModelConfig = field(default_factory = MLModelConfig)
    ensemble: EnsembleConfig = field(default_factory = EnsembleConfig)
    historical_pattern: HistoricalPatternConfig = field(
        default_factory = HistoricalPatternConfig
    )
    realtime_monitoring: RealTimeMonitoringConfig = field(
        default_factory = RealTimeMonitoringConfig
    )
    hk_market: HongKongMarketConfig = field(default_factory = HongKongMarketConfig)

    # Global settings
    model_training_window: int = 252  # Training window in days
    retraining_frequency: int = 7  # Retraining frequency in days
    cross_validation_folds: int = 5  # CV folds

    # Performance requirements (in milliseconds)
    time_series_analysis_time_limit: int = 50
    ml_inference_time_limit: int = 10
    historical_comparison_time_limit: int = 100
    realtime_processing_time_limit: int = 5
    multi_dimensional_analysis_time_limit: int = 200

    # Data paths
    model_storage_path: Path = Path("models / behavioral_analysis")
    baseline_storage_path: Path = Path("data / baselines")
    pattern_storage_path: Path = Path("data / patterns")
    alert_storage_path: Path = Path("data / alerts")

    # Feature engineering
    feature_selection_enabled: bool = True
    feature_scaling_method: str = "standard"  # standard, minmax, robust
    dimensionality_reduction: str = "pca"  # pca, tsne, umap
    max_features: int = 50

    # Model persistence
    model_versioning: bool = True
    model_backup_enabled: bool = True
    auto_model_update: bool = True

    # Quality control
    min_data_quality_score: float = 0.7
    anomaly_detection_threshold: float = 0.8
    pattern_validation_enabled: bool = True

    # Logging and monitoring
    detailed_logging: bool = True
    performance_monitoring: bool = True
    model_drift_detection: bool = True

    def __post_init__(self):
        """初始化后处理"""
        # 确保路径存在
        for path in [
            self.model_storage_path,
            self.baseline_storage_path,
            self.pattern_storage_path,
            self.alert_storage_path,
        ]:
            path.mkdir(parents = True, exist_ok = True)

        # 验证权重总和
        total_weight = (
            self.ensemble.isolation_weight
            + self.ensemble.svm_weight
            + self.ensemble.lof_weight
            + self.ensemble.rf_weight
            + self.ensemble.gb_weight
            + self.ensemble.nn_weight
        )

        if abs(total_weight - 1.0) > 0.01:
            # 标准化权重
            self.ensemble.isolation_weight /= total_weight
            self.ensemble.svm_weight /= total_weight
            self.ensemble.lof_weight /= total_weight
            self.ensemble.rf_weight /= total_weight
            self.ensemble.gb_weight /= total_weight
            self.ensemble.nn_weight /= total_weight


# Default configuration instance
DEFAULT_BEHAVIORAL_CONFIG = BehavioralAnalysisConfig()


def get_behavioral_config() -> BehavioralAnalysisConfig:
    """获取默认行为分析配置"""
    return DEFAULT_BEHAVIORAL_CONFIG


def create_custom_config(
    market_regime: MarketRegime = MarketRegime.BULL_MARKET,
    volatility_level: str = "normal",
    analysis_focus: str = "comprehensive",
) -> BehavioralAnalysisConfig:
    """创建自定义配置"""
    config = BehavioralAnalysisConfig()

    # 根据市场状态调整配置
    if market_regime == MarketRegime.HIGH_VOLATILITY:
        config.ml_models.isolation_contamination = 0.15
        config.realtime_monitoring.warning_threshold = 0.6
        config.ensemble.ensemble_threshold = 0.4
    elif market_regime == MarketRegime.BEAR_MARKET:
        config.ml_models.rf_max_depth = 10
        config.historical_pattern.baseline_window = 504  # 2 years
        config.realtime_monitoring.prediction_horizon = 20

    # 根据波动率水平调整
    if volatility_level == "high":
        config.intraday_pattern.vol_short_window = 5
        config.intraday_pattern.vol_medium_window = 15
        config.intraday_pattern.vol_long_window = 50
    elif volatility_level == "low":
        config.intraday_pattern.vol_short_window = 20
        config.intraday_pattern.vol_medium_window = 60
        config.intraday_pattern.vol_long_window = 200

    # 根据分析重点调整
    if analysis_focus == "speed":
        config.ml_models.isolation_n_estimators = 50
        config.ml_models.rf_n_estimators = 100
        config.time_series_analysis_time_limit = 30
    elif analysis_focus == "accuracy":
        config.ml_models.isolation_n_estimators = 200
        config.ml_models.rf_n_estimators = 500
        config.cross_validation_folds = 10

    return config


if __name__ == "__main__":
    # 测试配置
    print("Testing Behavioral Analysis Configuration...")

    config = get_behavioral_config()
    print(f"Default config loaded: {type(config).__name__}")

    # 创建自定义配置
    custom_config = create_custom_config(
        market_regime = MarketRegime.HIGH_VOLATILITY,
        volatility_level="high",
        analysis_focus="speed",
    )
    print(f"Custom config created for high volatility, speed - focused analysis")

    # 验证配置
    print(
        f"Total ensemble weights: {sum([custom_config.ensemble.isolation_weight, custom_config.ensemble.svm_weight, custom_config.ensemble.lof_weight, custom_config.ensemble.rf_weight, custom_config.ensemble.gb_weight, custom_config.ensemble.nn_weight]):.3f}"
    )
    print("✅ Configuration validation passed!")
