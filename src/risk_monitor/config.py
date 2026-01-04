"""
Configuration module for risk monitoring system
"""

import os
from typing import Dict, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class RiskConfig:
    """Configuration for risk monitoring system"""

    # InfluxDB configuration
    influxdb_host: str = "localhost"
    influxdb_port: int = 8086
    influxdb_database: str = "risk_monitoring"
    influxdb_username: str = ""
    influxdb_password: str = ""

    # WebSocket configuration
    websocket_host: str = "0.0.0.0"
    websocket_port: int = 8765
    websocket_max_connections: int = 100

    # Risk calculation configuration
    var_confidence_levels: list = None
    es_confidence_levels: list = None
    volatility_windows: list = None
    max_drawdown_window: int = 252

    # Alert configuration
    alert_enabled: bool = True
    alert_thresholds: Dict[str, Any] = None
    alert_cooldown: int = 60  # seconds

    # Dynamic adjustment configuration
    dynamic_adjustment_enabled: bool = True
    volatility_target: float = 0.15  # 15% annualized
    max_position_size: float = 1.0
    rebalance_threshold: float = 0.05

    # Performance configuration
    calculation_interval: int = 5  # seconds
    batch_size: int = 1000
    max_history_days: int = 252 * 5  # 5 years

    def __post_init__(self):
        """Initialize default values"""
        if self.var_confidence_levels is None:
            self.var_confidence_levels = [0.95, 0.99]
        if self.es_confidence_levels is None:
            self.es_confidence_levels = [0.95, 0.97, 0.99]
        if self.volatility_windows is None:
            self.volatility_windows = [20, 60, 252]
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "var_95_warning": 0.02,  # 2%
                "var_95_error": 0.05,    # 5%
                "var_99_warning": 0.03,  # 3%
                "var_99_error": 0.07,    # 7%
                "max_drawdown_warning": 0.10,  # 10%
                "max_drawdown_error": 0.20,    # 20%
                "volatility_warning": 0.25,    # 25%
                "volatility_error": 0.40,      # 40%
                "concentration_warning": 0.3,  # 30%
                "concentration_error": 0.5     # 50%
            }

    @classmethod
    def from_env(cls) -> "RiskConfig":
        """Load configuration from environment variables"""
        config = cls()

        # InfluxDB settings
        if os.getenv("INFLUXDB_HOST"):
            config.influxdb_host = os.getenv("INFLUXDB_HOST")
        if os.getenv("INFLUXDB_PORT"):
            config.influxdb_port = int(os.getenv("INFLUXDB_PORT"))
        if os.getenv("INFLUXDB_DATABASE"):
            config.influxdb_database = os.getenv("INFLUXDB_DATABASE")
        if os.getenv("INFLUXDB_USERNAME"):
            config.influxdb_username = os.getenv("INFLUXDB_USERNAME")
        if os.getenv("INFLUXDB_PASSWORD"):
            config.influxdb_password = os.getenv("INFLUXDB_PASSWORD")

        # WebSocket settings
        if os.getenv("WEBSOCKET_HOST"):
            config.websocket_host = os.getenv("WEBSOCKET_HOST")
        if os.getenv("WEBSOCKET_PORT"):
            config.websocket_port = int(os.getenv("WEBSOCKET_PORT"))
        if os.getenv("WEBSOCKET_MAX_CONNECTIONS"):
            config.websocket_max_connections = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS"))

        # Performance settings
        if os.getenv("RISK_CALCULATION_INTERVAL"):
            config.calculation_interval = int(os.getenv("RISK_CALCULATION_INTERVAL"))
        if os.getenv("RISK_BATCH_SIZE"):
            config.batch_size = int(os.getenv("RISK_BATCH_SIZE"))

        return config

    @classmethod
    def from_file(cls, file_path: str) -> "RiskConfig":
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)

    def save_to_file(self, file_path: str):
        """Save configuration to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def validate(self) -> bool:
        """Validate configuration parameters"""
        # Validate port numbers
        if not (1 <= self.influxdb_port <= 65535):
            raise ValueError("InfluxDB port must be between 1 and 65535")
        if not (1 <= self.websocket_port <= 65535):
            raise ValueError("WebSocket port must be between 1 and 65535")

        # Validate confidence levels
        for level in self.var_confidence_levels + self.es_confidence_levels:
            if not (0 < level < 1):
                raise ValueError("Confidence levels must be between 0 and 1")

        # Validate thresholds
        if not (0 < self.volatility_target < 1):
            raise ValueError("Volatility target must be between 0 and 1")
        if not (0 < self.max_position_size <= 1):
            raise ValueError("Max position size must be between 0 and 1")
        if not (0 < self.rebalance_threshold < 1):
            raise ValueError("Rebalance threshold must be between 0 and 1")

        # Validate performance settings
        if self.calculation_interval < 1:
            raise ValueError("Calculation interval must be at least 1 second")
        if self.batch_size < 1:
            raise ValueError("Batch size must be at least 1")

        return True


# Default configuration instance
default_config = RiskConfig()