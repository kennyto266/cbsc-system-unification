"""
Signal Fusion System - Phase 4 Implementation
信号融合系统 - Phase 4完整实施

This package implements the complete signal fusion system for the enhanced
non-price technical analysis system, integrating all components from Phase 4.

Components:
1. SignalGenerator - Single indicator signal generation
2. DynamicWeightManager - Multi-indicator weight management
3. ConflictResolver - Signal conflict resolution
4. CompositeSignalGenerator - Comprehensive composite signal generation

Usage:
    from signal_fusion import (
        SignalGenerator,
        DynamicWeightManager,
        ConflictResolver,
        CompositeSignalGenerator
    )

    # Initialize components
    signal_gen = SignalGenerator()
    weight_mgr = DynamicWeightManager(initial_weights)
    conflict_resolver = ConflictResolver()
    composite_gen = CompositeSignalGenerator(signal_gen, weight_mgr, conflict_resolver)

    # Generate composite signal
    composite_signal = composite_gen.generate_composite_signal(
        indicator_data, parameters, market_context
    )
"""

from .signal_generator import (
    SignalGenerator,
    Signal,
    SignalType,
    SignalFormat,
    SignalStatistics
)

from .weight_manager import (
    DynamicWeightManager,
    IndicatorWeight,
    WeightConstraints,
    WeightPerformanceMetrics,
    WeightAdjustmentStrategy,
    MarketRegime
)

# Import everything from conflict_resolver at once to avoid circular imports
from .conflict_resolver import (
    ConflictResolver,
    SignalConflict,
    ConflictType,
    ConflictSeverity,
    ConflictResolutionStrategy,
    ResolutionHistory,
    ConflictResolutionMetrics
)

from .composite_signal_generator import (
    CompositeSignalGenerator,
    CompositeSignal,
    SignalExplanation,
    SignalQuality,
    ExplanationLevel,
    ExplainableAI,
    SignalQualityAssessor,
    CompositeSignalMetrics
)

__version__ = "1.0.0"
__author__ = "Claude Code Assistant"

# Package metadata
__all__ = [
    # Signal Generation
    "SignalGenerator",
    "Signal",
    "SignalType",
    "SignalFormat",
    "SignalStatistics",

    # Weight Management
    "DynamicWeightManager",
    "IndicatorWeight",
    "WeightConstraints",
    "WeightPerformanceMetrics",
    "WeightAdjustmentStrategy",
    "MarketRegime",

    # Conflict Resolution
    "ConflictResolver",
    "SignalConflict",
    "ConflictType",
    "ConflictSeverity",
    "ConflictResolutionStrategy",
    "ResolutionHistory",
    "ConflictResolutionMetrics",

    # Composite Signal Generation
    "CompositeSignalGenerator",
    "CompositeSignal",
    "SignalExplanation",
    "SignalQuality",
    "ExplanationLevel",
    "ExplainableAI",
    "SignalQualityAssessor",
    "CompositeSignalMetrics"
]

# Utility functions for easy integration
def create_complete_fusion_system(initial_weights: dict,
                                 explanation_level: str = "detailed",
                                 enable_quality_assessment: bool = True) -> CompositeSignalGenerator:
    """
    创建完整的信号融合系统

    Args:
        initial_weights: 初始权重配置
        explanation_level: 解释详细程度 ("minimal", "basic", "detailed", "comprehensive")
        enable_quality_assessment: 启用质量评估

    Returns:
        CompositeSignalGenerator: 完整的信号融合系统
    """
    from .signal_generator import SignalGenerator
    from .weight_manager import DynamicWeightManager
    from .conflict_resolver import ConflictResolver
    from .composite_signal_generator import (
        CompositeSignalGenerator, ExplanationLevel
    )

    # 创建组件
    signal_generator = SignalGenerator()
    weight_manager = DynamicWeightManager(initial_weights)
    conflict_resolver = ConflictResolver()
    explanation_enum = ExplanationLevel(explanation_level)

    # 创建复合信号生成器
    composite_generator = CompositeSignalGenerator(
        signal_generator=signal_generator,
        weight_manager=weight_manager,
        conflict_resolver=conflict_resolver,
        explanation_level=explanation_enum,
        enable_quality_assessment=enable_quality_assessment
    )

    return composite_generator

def get_system_capabilities() -> dict:
    """获取系统能力概述"""
    return {
        "signal_generation": {
            "supported_formats": ["binary", "multi_level", "continuous", "probability"],
            "signal_types": ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL", "WEAK_BUY", "WEAK_SELL"],
            "strength_scoring": True,
            "confidence_assessment": True,
            "historical_tracking": True
        },
        "weight_management": {
            "strategies": ["static", "performance", "market_regime", "volatility", "correlation", "ml_optimized", "hybrid"],
            "optimization_methods": ["grid_search", "random_search", "bayesian"],
            "dynamic_adjustment": True,
            "constraint_management": True
        },
        "conflict_resolution": {
            "strategies": ["majority_voting", "weighted_voting", "consensus_based", "hierarchical", "confidence_weighted", "ml_based", "ensemble"],
            "conflict_types": ["buy_sell", "strength", "timing", "direction", "confidence"],
            "learning_mechanism": True,
            "performance_tracking": True
        },
        "composite_generation": {
            "explainable_ai": True,
            "quality_assessment": True,
            "visualization": True,
            "reporting": True,
            "historical_analysis": True
        }
    }

# Quick start example
QUICK_START_EXAMPLE = '''
# Quick Start Example - Signal Fusion System

from signal_fusion import create_complete_fusion_system
import pandas as pd
import numpy as np

# 1. 创建示例数据
def create_sample_data():
    dates = pd.date_range('2023-01-01', periods=100, freq='D')

    # 模拟多个指标数据
    data = {
        'RSI': pd.Series(50 + 20 * np.sin(np.linspace(0, 10, 100)), index=dates),
        'MACD': pd.Series(np.cumsum(np.random.randn(100) * 0.1), index=dates),
        'BOLLINGER': pd.Series(100 + 10 * np.sin(np.linspace(0, 5, 100)), index=dates),
        'HIBOR_RATE': pd.Series(3.0 + 0.5 * np.sin(np.linspace(0, 8, 100)), index=dates),
        'MONETARY_BASE': pd.Series(np.exp(np.linspace(0, 0.1, 100)), index=dates)
    }

    return data

# 2. 配置初始权重
initial_weights = {
    'RSI': 0.3,
    'MACD': 0.25,
    'BOLLINGER': 0.2,
    'HIBOR_RATE': 0.15,
    'MONETARY_BASE': 0.1
}

# 3. 创建信号融合系统
fusion_system = create_complete_fusion_system(
    initial_weights=initial_weights,
    explanation_level="detailed",
    enable_quality_assessment=True
)

# 4. 配置指标参数
indicator_parameters = {
    'RSI': {'period': 14, 'oversold': 30, 'overbought': 70},
    'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
    'BOLLINGER': {'period': 20, 'std_dev': 2},
    'HIBOR_RATE': {'name': 'HIBOR_RATE'},
    'MONETARY_BASE': {'name': 'MONETARY_BASE'}
}

# 5. 创建市场上下文
market_context = {
    'regime': 'bull',
    'volatility': 0.02,
    'trend': 'upward'
}

# 6. 生成复合信号
indicator_data = create_sample_data()
composite_signal = fusion_system.generate_composite_signal(
    indicator_data=indicator_data,
    parameters=indicator_parameters,
    market_context=market_context
)

# 7. 查看结果
print(f"信号类型: {composite_signal.signal_type.name}")
print(f"信号强度: {composite_signal.strength:.2f}/10")
print(f"置信度: {composite_signal.confidence:.2%}")
print(f"信号质量: {composite_signal.quality.value}")

# 8. 生成解释报告
report = fusion_system.generate_explanation_report(composite_signal)
print("\\n" + "="*50)
print("信号解释报告:")
print("="*50)
print(report)

# 9. 生成可视化
viz_path = fusion_system.generate_signal_visualization(composite_signal)
if viz_path:
    print(f"\\n可视化已保存到: {viz_path}")

# 10. 获取系统性能指标
metrics = fusion_system.get_performance_metrics()
print(f"\\n系统性能指标:")
print(f"总信号数: {metrics.total_signals}")
print(f"平均置信度: {metrics.avg_confidence:.2%}")
print(f"平均强度: {metrics.avg_strength:.2f}")
'''

__doc__ += f"""

## Quick Start Example

```python
{QUICK_START_EXAMPLE}
```

## System Capabilities

```python
from signal_fusion import get_system_capabilities
capabilities = get_system_capabilities()
print(capabilities)
```

This signal fusion system provides a complete solution for integrating multiple
technical indicators into actionable trading signals with explainable AI capabilities.
"""