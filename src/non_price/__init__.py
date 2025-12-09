#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非价格信号系统模块 - Non-Price Signals System Module
将非价格信号转换为技术分析指标并进行SR/MDD优化的完整系统
"""

from .signal_data_manager import (
NonPriceSignal,
SignalQualityMetrics,
EnhancedSignalDataManager,
SignalDataQualityValidator,
get_signal_manager
)

from .signal_conversion_engine import (
TechnicalIndicatorSignal,
SignalConversionEngine,
get_conversion_engine
)

from .integration import (
NonPriceSignalsSystem,
NonPriceSignalsParallelProcessor,
GPUAcceleratedProcessor,
get_non_price_system
)

__version__ = "1.0.0"
__author__ = "Non-Price Signals Development Team"
__description__ = "Advanced Non-Price Signal Conversion and SR/MDD Optimization System"

__all__ = [

"NonPriceSignal",
"SignalQualityMetrics",
"TechnicalIndicatorSignal",

"EnhancedSignalDataManager",
"SignalConversionEngine",
"NonPriceSignalsSystem",
"NonPriceSignalsParallelProcessor",
"GPUAcceleratedProcessor",

"get_signal_manager",
"get_conversion_engine",
"get_non_price_system",

"__version__",
"__author__",
"__description__"
]

import logging
logger = logging.getLogger__name__

logger.infof"Non-Price Signals System v{__version__} initialized"
logger.infof"Components: Signal Manager, Conversion Engine, SR/MDD Optimizer, Parallel Processor"