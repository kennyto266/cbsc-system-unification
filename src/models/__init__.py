"""
CBSC統一數據模型模組

提供企業級數據模型定義，支持：
- 用戶和權限管理
- 策略管理和配置
- 市場數據和技術指標
- 交易和投資組合
- 分析報告和回測結果
"""

from .base import BaseModel
from .user import User, Role, Permission, UserRole
from .strategy import Strategy, StrategyConfig, StrategyPerformance, StrategyCategory
from .market import MarketData, TechnicalIndicator, SentimentData
from .trading import Trade, Portfolio, Position, Order
from .analytics import AnalysisReport, BacktestResult, PerformanceMetrics
from .system import SystemConfig, AuditLog, DataSchema

# Legacy compatibility imports
from .legacy import MarketData as LegacyMarketData, TradingSignal, Portfolio as LegacyPortfolio, RiskMetrics

__all__ = [
    # Base models
    "BaseModel",

    # User and permissions
    "User", "Role", "Permission", "UserRole",

    # Strategy management
    "Strategy", "StrategyConfig", "StrategyPerformance", "StrategyCategory",

    # Market data
    "MarketData", "TechnicalIndicator", "SentimentData",

    # Trading and portfolio
    "Trade", "Portfolio", "Position", "Order",

    # Analytics and reporting
    "AnalysisReport", "BacktestResult", "PerformanceMetrics",

    # System management
    "SystemConfig", "AuditLog", "DataSchema",

    # Legacy compatibility
    "LegacyMarketData", "TradingSignal", "LegacyPortfolio", "RiskMetrics",
]
