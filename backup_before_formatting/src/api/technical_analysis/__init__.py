"""
技術分析API模組 - 非價格數據轉換為技術指標
Technical Analysis API Module - Convert Non-Price Data to Technical Indicators
"""

from .endpoints import *
from .engine import *
from .models import *

__version__ = "1.0.0"
__description__ = "Technical Analysis API for Non-Price Data"

# 導出的主要類和函數
__all__ = [
    # 核心引擎
    "TechnicalIndicatorEngine",
    "NonPriceDataProcessor",
    "ResponseFormatter",

    # 數據模型
    "RSIRequest", "MACDRequest", "BollingerBandsRequest", "BatchRequest",
    "RSIResponse", "MACDResponse", "BollingerBandsResponse", "BatchResponse",
    "DateRange", "QualityMetrics", "ErrorResponse",

    # API路由
    "router",
    "calculate_rsi", "calculate_macd", "calculate_bollinger_bands",
    "calculate_batch", "get_data_sources", "health_check"
]
