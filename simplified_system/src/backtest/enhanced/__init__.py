#!/usr / bin / env python3
"""
Simplified System - VectorBT Enhanced Module
Professional quantitative trading techniques based on Python Algorithmic Trading Cookbook

This module integrates advanced VectorBT techniques from Cookbook, including:
- Walk - Forward optimization engine
- Cookbook strategy library
- Advanced portfolio analyzer
- GPU acceleration support

Usage example:
    from backtest.enhanced import (
        WalkForwardOptimizer,
        CookbookStrategyBuilder,
        AdvancedPortfolioAnalyzer,
        GPUVectorBTAccelerator
    )
"""

import logging

# Setup logging
logger = logging.getLogger(__name__)

try:
    # Strategy convenient imports
    from .cookbook_strategies.ma_crossover_strategy import (
        ma_crossover_strategy,
        optimize_ma_crossover,
    )
    from .cookbook_strategies.rsi_mean_reversion_strategy import (
        optimize_rsi_strategy,
        rsi_mean_reversion_strategy,
        rsi_with_stop_loss_strategy,
    )
    from .gpu_vectorbt_accelerator import (
        GPUBenchmarkResult,
        GPUConfig,
        GPUVectorBTAccelerator,
    )
    from .vectorbt_portfolio_analyzer import (
        AdvancedPortfolioAnalyzer,
        PerformanceMetrics,
        PortfolioAnalysisConfig,
        RiskMetrics,
    )
    from .vectorbt_strategy_builder import CookbookStrategyBuilder, StrategyConfig
    from .vectorbt_walkforward_optimizer import (
        WalkForwardConfig,
        WalkForwardOptimizer,
        WalkForwardResult,
    )

except ImportError as e:
    logger.warning(f"Some enhanced features could not be imported: {e}")
    # Define empty placeholders for missing components
    WalkForwardOptimizer = None
    CookbookStrategyBuilder = None
    AdvancedPortfolioAnalyzer = None
    GPUVectorBTAccelerator = None

__version__ = "1.0.0"
__author__ = "Simplified System Team"

# 模塊導出列表
__all__ = [
    # 核心類
    "WalkForwardOptimizer",
    "CookbookStrategyBuilder",
    "AdvancedPortfolioAnalyzer",
    "GPUVectorBTAccelerator",
    # 配置類
    "WalkForwardConfig",
    "StrategyConfig",
    "PortfolioAnalysisConfig",
    "GPUConfig",
    # 結果類
    "WalkForwardResult",
    "RiskMetrics",
    "PerformanceMetrics",
    "GPUBenchmarkResult",
    # 策略函數
    "ma_crossover_strategy",
    "rsi_mean_reversion_strategy",
    "rsi_with_stop_loss_strategy",
    "optimize_ma_crossover",
    "optimize_rsi_strategy",
]


def get_enhanced_backtest_engine(price_data = None, gpu_enabled = True):
    """
    創建增強的回測引擎，整合所有Cookbook功能

    Args:
        price_data: 價格數據 (pd.DataFrame or pd.Series)
        gpu_enabled: 是否啟用GPU加速

    Returns:
        dict: 包含所有增強功能的字典
    """
    logger.info(f"創建增強回測引擎，GPU加速: {gpu_enabled}")

    # 初始化組件
    components = {}

    # GPU加速器
    components["gpu_accelerator"] = GPUVectorBTAccelerator()

    # 策略構建器
    components["strategy_builder"] = CookbookStrategyBuilder()

    # 投資組合分析器
    components["portfolio_analyzer"] = AdvancedPortfolioAnalyzer()

    # Walk - Forward優化器（如果有數據）
    if price_data is not None:
        components["walkforward_optimizer"] = WalkForwardOptimizer(
            price_data, rsi_mean_reversion_strategy  # 使用RSI策略作為默認示例
        )

    return components


def quick_strategy_analysis(price_data, strategy_name="RSI_MEAN_REVERSION"):
    """
    快速策略分析 - 一行代碼完成完整分析

    Args:
        price_data: 價格數據
        strategy_name: 策略名稱

    Returns:
        dict: 分析結果
    """
    logger.info(f"執行快速策略分析: {strategy_name}")

    # 初始化組件
    builder = CookbookStrategyBuilder()
    analyzer = AdvancedPortfolioAnalyzer()

    # 執行策略
    portfolio = builder.execute_strategy(strategy_name, price_data)

    # 分析結果
    analysis_result = analyzer.analyze_portfolio(portfolio)

    # 生成報告
    report = analyzer.generate_comprehensive_report(analysis_result)

    return {"portfolio": portfolio, "analysis": analysis_result, "report": report}


def compare_all_strategies(price_data, benchmark = None):
    """
    比較所有可用的Cookbook策略

    Args:
        price_data: 價格數據
        benchmark: 基準數據

    Returns:
        pd.DataFrame: 策略比較結果
    """
    logger.info("比較所有Cookbook策略")

    builder = CookbookStrategyBuilder()
    comparison = builder.compare_strategies(price_data)

    return comparison


def run_walkforward_optimization(price_data, strategy_func = None, config = None):
    """
    運行Walk - Forward優化

    Args:
        price_data: 價格數據
        strategy_func: 策略函數
        config: Walk - Forward配置

    Returns:
        WalkForwardResult: 優化結果
    """
    logger.info("執行Walk - Forward優化")

    if strategy_func is None:
        strategy_func = rsi_mean_reversion_strategy

    optimizer = WalkForwardOptimizer(price_data, strategy_func, config)
    result = optimizer.optimize()

    # 生成報告
    report = optimizer.generate_report(result)

    return {"result": result, "report": report}


# Module initialization
def _init_module():
    """Module initialization"""
    import logging

    logging.basicConfig(level = logging.INFO)

    # Check dependencies
    try:
        import vectorbt as vbt

        logger.info(f"VectorBT available, version: {vbt.__version__}")
    except ImportError:
        logger.warning("VectorBT not available, some features may be limited")

    try:
        import cupy as cp

        logger.info(f"CuPy available, version: {cp.__version__}")
    except ImportError:
        logger.info("CuPy not available, GPU acceleration features will be limited")


# Execute initialization
try:
    _init_module()
except Exception as e:
    logger.warning(f"Module initialization failed: {e}")
