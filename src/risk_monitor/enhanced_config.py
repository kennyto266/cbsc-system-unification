"""
Enhanced Risk Monitoring Configuration

This module provides configuration classes for the enhanced dynamic risk monitoring system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import timedelta
import json
import os
from enum import Enum


class RiskControlMode(Enum):
    """Risk control execution mode"""
    SIMULATION = "simulation"  # Only log signals, don't execute
    SEMI_AUTOMATIC = "semi_automatic"  # Require approval for high-urgency actions
    AUTOMATIC = "automatic"  # Execute all signals automatically


class ReportFrequency(Enum):
    """Report generation frequency"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class MonteCarloConfig:
    """Monte Carlo simulation configuration"""
    # Simulation parameters
    n_simulations: int = 5000
    time_horizon: int = 10  # trading days
    confidence_levels: List[float] = field(default_factory=lambda: [0.90, 0.95, 0.99])

    # Method preferences
    primary_method: str = "parametric"  # 'bootstrap', 'parametric', 'historical'
    fallback_methods: List[str] = field(default_factory=lambda: ["bootstrap"])

    # Performance settings
    parallel_simulations: bool = True
    max_workers: int = 4
    cache_ttl_minutes: int = 5

    # Data requirements
    min_observations: int = 60
    max_observations: int = 2520  # 10 years

    # Advanced settings
    use_antithetic: bool = True
    use_variance_reduction: bool = True
    random_seed: Optional[int] = None


@dataclass
class DynamicThresholdConfig:
    """Dynamic threshold configuration"""
    # Base thresholds
    base_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'var_95': 0.05,
        'var_99': 0.10,
        'max_drawdown': 0.15,
        'volatility': 0.30,
        'concentration': 0.30,
        'correlation': 0.70,
        'liquidity': 0.05,
        'mc_var_99_ratio': 0.10
    })

    # Adjustment parameters
    adjustment_factor: float = 0.1  # 10% adjustment factor
    adjustment_frequency: timedelta = field(default_factory=lambda: timedelta(hours=1))

    # Market condition weights
    volatility_weight: float = 0.4
    correlation_weight: float = 0.3
    stress_weight: float = 0.3

    # Limits
    max_adjustment_up: float = 0.5  # Maximum 50% relaxation
    max_adjustment_down: float = 0.3  # Maximum 30% tightening

    # Stress thresholds
    stress_volatility_threshold: float = 0.30
    stress_correlation_threshold: float = 0.60
    extreme_stress_threshold: float = 0.80


@dataclass
class RiskControlConfig:
    """Risk control configuration"""
    # Execution mode
    mode: RiskControlMode = RiskControlMode.SIMULATION

    # Position limits
    max_position_size: float = 0.30  # Maximum 30% in single position
    max_sector_exposure: float = 0.40  # Maximum 40% in single sector
    max_leverage: float = 2.0
    min_leverage: float = 0.5

    # Control parameters
    emergency_exit_threshold: float = 0.20  # 20% drawdown triggers emergency exit
    reduce_exposure_factor: float = 0.5  # Reduce by 50% on alert
    hedge_ratio_min: float = 0.2
    hedge_ratio_max: float = 0.8

    # Execution settings
    max_signals_per_hour: int = 10
    signal_cooldown_minutes: int = 15
    require_approval_for: List[RiskControlAction] = field(default_factory=lambda: [
        RiskControlAction.EMERGENCY_EXIT,
        RiskControlAction.PAUSE_TRADING
    ])

    # Trading system integration
    execution_timeout_seconds: int = 30
    retry_attempts: int = 3
    confirmation_required: bool = True


@dataclass
class AlertConfig:
    """Alert configuration"""
    # Alert levels
    enabled_levels: List[str] = field(default_factory=lambda: ["warning", "error", "critical"])

    # Notification channels
    email_enabled: bool = True
    email_recipients: List[str] = field(default_factory=list)
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    websocket_enabled: bool = True

    # Rate limiting
    max_alerts_per_hour: int = 50
    cooldown_period_minutes: int = 5

    # Escalation
    auto_escalate: bool = True
    escalate_after_minutes: int = 30

    # Aggregation
    aggregate_similar: bool = True
    aggregation_window_minutes: int = 10


@dataclass
class ReportConfig:
    """Report configuration"""
    # Generation settings
    frequency: ReportFrequency = ReportFrequency.DAILY
    auto_generate: bool = True
    auto_distribute: bool = False

    # Content settings
    include_monte_carlo: bool = True
    include_recommendations: bool = True
    include_attribution: bool = True
    include_forecast: bool = False

    # Export formats
    default_format: str = "html"
    enabled_formats: List[str] = field(default_factory=lambda: ["html", "json", "pdf"])

    # Distribution
    email_recipients: List[str] = field(default_factory=list)
    save_location: str = "reports/"
    retention_days: int = 90

    # Advanced settings
    custom_templates: Dict[str, str] = field(default_factory=dict)
    benchmark_portfolio: Optional[str] = None


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    # Caching
    enable_cache: bool = True
    cache_ttl_minutes: int = 5
    max_cache_size_mb: int = 100

    # Parallel processing
    enable_parallel: bool = True
    max_workers: int = 4
    use_process_pool: bool = True

    # Batch processing
    batch_size: int = 100
    batch_timeout_seconds: int = 10

    # Resource limits
    max_memory_mb: int = 1024
    max_cpu_percent: float = 80.0

    # Monitoring
    enable_performance_metrics: bool = True
    metrics_export_interval: int = 60  # seconds


@dataclass
class EnhancedRiskConfig:
    """Complete enhanced risk monitoring configuration"""
    # Core settings
    calculation_interval_seconds: int = 5
    monitoring_enabled: bool = True

    # Component configurations
    monte_carlo: MonteCarloConfig = field(default_factory=MonteCarloConfig)
    dynamic_thresholds: DynamicThresholdConfig = field(default_factory=DynamicThresholdConfig)
    risk_control: RiskControlConfig = field(default_factory=RiskControlConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    reports: ReportConfig = field(default_factory=ReportConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    # External integrations
    influxdb_config: Dict[str, Any] = field(default_factory=dict)
    trading_system_config: Dict[str, Any] = field(default_factory=dict)
    notification_config: Dict[str, Any] = field(default_factory=dict)

    # Feature flags
    enable_monte_carlo: bool = True
    enable_dynamic_thresholds: bool = True
    enable_automatic_control: bool = False  # Default to false for safety
    enable_advanced_reporting: bool = True

    # Environment settings
    environment: str = "development"  # 'development', 'testing', 'production'
    debug_mode: bool = False
    log_level: str = "INFO"


class ConfigManager:
    """Configuration manager for enhanced risk monitoring"""

    @staticmethod
    def load_from_file(file_path: str) -> EnhancedRiskConfig:
        """Load configuration from JSON file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, 'r') as f:
            config_dict = json.load(f)

        return ConfigManager.from_dict(config_dict)

    @staticmethod
    def save_to_file(config: EnhancedRiskConfig, file_path: str):
        """Save configuration to JSON file"""
        config_dict = ConfigManager.to_dict(config)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> EnhancedRiskConfig:
        """Create config from dictionary"""
        # Handle nested configurations
        if 'monte_carlo' in config_dict:
            config_dict['monte_carlo'] = MonteCarloConfig(**config_dict['monte_carlo'])

        if 'dynamic_thresholds' in config_dict:
            config_dict['dynamic_thresholds'] = DynamicThresholdConfig(**config_dict['dynamic_thresholds'])

        if 'risk_control' in config_dict:
            # Convert string actions to enum
            rc_config = config_dict['risk_control']
            if 'require_approval_for' in rc_config:
                rc_config['require_approval_for'] = [
                    RiskControlAction(action) for action in rc_config['require_approval_for']
                ]
            if 'mode' in rc_config:
                rc_config['mode'] = RiskControlMode(rc_config['mode'])
            config_dict['risk_control'] = RiskControlConfig(**rc_config)

        if 'alerts' in config_dict:
            config_dict['alerts'] = AlertConfig(**config_dict['alerts'])

        if 'reports' in config_dict:
            # Convert string frequency to enum
            if 'frequency' in config_dict['reports']:
                config_dict['reports']['frequency'] = ReportFrequency(
                    config_dict['reports']['frequency']
                )
            config_dict['reports'] = ReportConfig(**config_dict['reports'])

        if 'performance' in config_dict:
            config_dict['performance'] = PerformanceConfig(**config_dict['performance'])

        return EnhancedRiskConfig(**config_dict)

    @staticmethod
    def to_dict(config: EnhancedRiskConfig) -> Dict[str, Any]:
        """Convert config to dictionary"""
        config_dict = {}

        for key, value in config.__dict__.items():
            if hasattr(value, '__dict__'):
                # Handle nested dataclasses
                if isinstance(value, (MonteCarloConfig, DynamicThresholdConfig,
                                   RiskControlConfig, AlertConfig, ReportConfig,
                                   PerformanceConfig)):
                    nested_dict = {}
                    for nested_key, nested_value in value.__dict__.items():
                        if isinstance(nested_value, Enum):
                            nested_dict[nested_key] = nested_value.value
                        elif isinstance(nested_value, list) and nested_value and isinstance(nested_value[0], Enum):
                            nested_dict[nested_key] = [item.value for item in nested_value]
                        else:
                            nested_dict[nested_key] = nested_value
                    config_dict[key] = nested_dict
                else:
                    config_dict[key] = value
            elif isinstance(value, Enum):
                config_dict[key] = value.value
            elif isinstance(value, timedelta):
                config_dict[key] = str(value)
            else:
                config_dict[key] = value

        return config_dict


def create_default_config() -> EnhancedRiskConfig:
    """Create default configuration"""
    return EnhancedRiskConfig()


def create_production_config() -> EnhancedRiskConfig:
    """Create production-ready configuration"""
    config = EnhancedRiskConfig()

    # Production-specific settings
    config.environment = "production"
    config.debug_mode = False
    config.log_level = "WARNING"
    config.calculation_interval_seconds = 60  # 1 minute

    # Enable all features
    config.enable_monte_carlo = True
    config.enable_dynamic_thresholds = True
    config.enable_automatic_control = True  # Enable in production with proper safeguards
    config.enable_advanced_reporting = True

    # Tighter thresholds for production
    config.dynamic_thresholds.base_thresholds.update({
        'var_95': 0.03,
        'var_99': 0.07,
        'max_drawdown': 0.10,
        'volatility': 0.25
    })

    # More conservative risk control
    config.risk_control.mode = RiskControlMode.SEMI_AUTOMATIC
    config.risk_control.max_position_size = 0.25
    config.risk_control.max_leverage = 1.5
    config.risk_control.emergency_exit_threshold = 0.15

    # Enable all alert channels
    config.alerts.email_enabled = True
    config.alerts.webhook_enabled = True
    config.alerts.websocket_enabled = True

    # Daily reports with distribution
    config.reports.frequency = ReportFrequency.DAILY
    config.reports.auto_distribute = True
    config.reports.enabled_formats = ["html", "pdf"]

    return config


def create_development_config() -> EnhancedRiskConfig:
    """Create development configuration"""
    config = EnhancedRiskConfig()

    # Development-specific settings
    config.environment = "development"
    config.debug_mode = True
    config.log_level = "DEBUG"
    config.calculation_interval_seconds = 5  # 5 seconds for testing

    # Simulation mode for safety
    config.risk_control.mode = RiskControlMode.SIMULATION
    config.enable_automatic_control = False

    # Relaxed thresholds for testing
    config.dynamic_thresholds.base_thresholds.update({
        'var_95': 0.08,
        'var_99': 0.15,
        'max_drawdown': 0.20,
        'volatility': 0.40
    })

    # Minimal alerts during development
    config.alerts.enabled_levels = ["error", "critical"]
    config.alerts.email_enabled = False

    # Real-time reports for development
    config.reports.frequency = ReportFrequency.HOURLY
    config.reports.auto_distribute = False

    return config


# Preset configurations
PRESET_CONFIGS = {
    'default': create_default_config,
    'production': create_production_config,
    'development': create_development_config
}


def get_preset_config(preset_name: str) -> EnhancedRiskConfig:
    """Get preset configuration by name"""
    if preset_name not in PRESET_CONFIGS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(PRESET_CONFIGS.keys())}")

    return PRESET_CONFIGS[preset_name]()