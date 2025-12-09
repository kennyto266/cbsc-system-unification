#!/usr / bin / env python3
"""
Simplified System - Alpha Factor System
機構級Alpha因子分析和投資組合管理系統

這個模塊提供專業級的Alpha因子分析功能：
- 因子計算引擎
- 因子有效性檢驗
- AlphaLens集成分析
- 多因子模型構建
- 因子投資組合管理

使用示例:
    from alpha import (
        AlphaFactorEngine,
        FactorValidator,
        AlphaLensAnalyzer,
        FactorPortfolio,
        FactorInvestmentPortfolio
    )
"""

import logging
import warnings

# Setup logging
logger = logging.getLogger(__name__)

# Import core components with error handling
try:
    from .factor_analyzer import AlphaLensAnalyzer, FactorValidator
    from .factor_engine import AlphaFactorEngine, FactorMetrics, FactorTypes
    from .factor_portfolio import FactorInvestmentPortfolio, FactorPortfolio

    logger.info("Alpha Factor System loaded successfully")

    __all__ = [
        "AlphaFactorEngine",
        "FactorValidator",
        "AlphaLensAnalyzer",
        "FactorPortfolio",
        "FactorInvestmentPortfolio",
        "FactorTypes",
        "FactorMetrics",
    ]

except ImportError as e:
    logger.warning(f"Some Alpha Factor components could not be imported: {e}")

    # Define placeholders for missing components
    AlphaFactorEngine = None
    FactorValidator = None
    AlphaLensAnalyzer = None
    FactorPortfolio = None
    FactorInvestmentPortfolio = None

    __all__ = [
        "AlphaFactorEngine",
        "FactorValidator",
        "AlphaLensAnalyzer",
        "FactorPortfolio",
        "FactorInvestmentPortfolio",
    ]

__version__ = "1.0.0"
__author__ = "Simplified System Team"


# Module initialization
def _init_module():
    """Alpha Factor系統初始化"""

    # Check for optional dependencies
    try:
        import alphalens

        logger.info("AlphaLens available for advanced factor analysis")
    except ImportError:
        logger.info("AlphaLens not available, using built - in factor analysis")

    try:
        import sklearn

        logger.info("Scikit - learn available for machine learning features")
    except ImportError:
        logger.info("Scikit - learn not available, some ML features limited")

    try:
        import scipy

        logger.info("SciPy available for statistical analysis")
    except ImportError:
        logger.warning("SciPy not available, statistical features limited")


# Execute initialization
try:
    _init_module()
except Exception as e:
    logger.warning(f"Alpha Factor system initialization failed: {e}")

# Suppress common warnings for cleaner output
warnings.filterwarnings("ignore", category = FutureWarning)
warnings.filterwarnings("ignore", category = UserWarning)
