"""
Enhanced Non-Price Technical Analysis System
基於OpenSpec enhance-nonprice-ta-system提案的增強版非價格技術分析系統

核心目標：
- 保持MB_KDJ_[10,2]策略的成功性能(Sharpe 3.672)
- 增強系統性能而非簡化
- 模組化重構保持所有現有功能
"""

__version__ = "1.0.0"
__author__ = "Enhanced TA System"

from .core_optimizer import EnhancedOptimizerEngine
from .data_manager import EnhancedDataManager
from .indicator_engine import EnhancedIndicatorEngine

# 核心成功策略保護
PROTECTED_STRATEGIES = {
    'MB_KDJ_[10,2]': {
        'expected_sharpe': 3.672,
        'max_drawdown': -9.16,
        'annual_return': 121.62
    }
}

# 系統性能基準
PERFORMANCE_BENCHMARKS = {
    'strategies_per_second': 396,
    'parallel_cores': 32,
    'total_strategies': 24044,
    'success_rate': 100.0
}