"""
Real-time Risk Monitoring System

This module provides comprehensive risk monitoring capabilities for quantitative trading strategies,
including real-time risk calculations, dynamic adjustments, and alert systems.
"""

from .risk_engine import RiskEngine
from .risk_calculators import (
    VaRCalculator,
    ExpectedShortfallCalculator,
    MaxDrawdownCalculator,
    VolatilityCalculator,
    CorrelationAnalyzer
)
from .alert_system import AlertSystem, AlertLevel, AlertType
from .websocket_handler import RiskWebSocketHandler
from .influxdb_connector import InfluxDBConnector
from .dynamic_adjustment import DynamicRiskAdjuster

__version__ = "1.0.0"
__all__ = [
    "RiskEngine",
    "VaRCalculator",
    "ExpectedShortfallCalculator",
    "MaxDrawdownCalculator",
    "VolatilityCalculator",
    "CorrelationAnalyzer",
    "AlertSystem",
    "AlertLevel",
    "AlertType",
    "RiskWebSocketHandler",
    "InfluxDBConnector",
    "DynamicRiskAdjuster"
]