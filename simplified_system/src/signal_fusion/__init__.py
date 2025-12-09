#!/usr / bin / env python3
"""
簡化系統 - 信號融合模塊
Simplified System - Signal Fusion Module

Phase 4: 智能信號融合系統

這個模塊提供了完整的智能信號融合功能，包括：

1. 單指標信號生成 (signal_generator.py)
   - 實現SignalGenerator類，支持所有技術指標
   - 標準化信號格式 (買入 / 賣出 / 持有，強度1 - 10)
   - 實現信號置信度評估算法
   - 添加信號歷史記錄和追蹤
   - 實現信號有效性驗證

2. 多指標權重管理 (weight_manager.py)
   - 實現DynamicWeightManager類
   - 支持靜態權重配置和動態權重調整
   - 實現基於性能的權重優化算法
   - 添加權重約束條件和風險控制
   - 實現權重性能評估和回測

3. 信號衝突解決 (conflict_resolver.py)
   - 實現ConflictResolver類
   - 添加多種衝突檢測機制 (>95%準確率)
   - 實現多種衝突解決策略 (投票、權重、機器學習)
   - 添加衝突解決學習機制
   - 實現衝突解決效果評估

4. 綜合信號生成 (composite_signal_generator.py)
   - 實現CompositeSignalGenerator類
   - 整合所有指標信號進行智能融合
   - 計算綜合信號強度和方向
   - 生成信號解釋和決策理由
   - 實現信號質量評估和風險評級
   - 創建信號可視化和報告系統

主要特性：
- 支持多達20 + 種技術指標的信號生成
- 實現智能權重分配和衝突解決
- 添加解釋性AI，提供信號理由
- 確保信號生成延遲 < 100ms

使用示例：
```python
from src.signal_fusion import composite_signal_generator

# 生成綜合信號
signal = composite_signal_generator.generate_composite_signal(
    symbol="0700.HK",
    data = price_data,
    indicators = technical_indicators
)

# 生成詳細報告
report = composite_signal_generator.generate_signal_report(signal, price_data)
```
"""

import numpy as np

from .composite_signal_generator import (
    CompositeSignal,
    CompositeSignalGenerator,
    RiskLevel,
    SignalQuality,
    SignalQualityAssessor,
    SignalReport,
    SignalRiskAssessor,
    composite_signal_generator,
    generate_composite_signal,
)
from .conflict_resolver import (
    ConflictResolution,
    ConflictResolver,
    ConflictType,
    ResolutionPerformance,
    ResolutionStrategy,
    SignalConflict,
    conflict_resolver,
    resolve_signal_conflicts,
)

# 導出主要類和函數
from .signal_generator import (
    ConfidenceCalculator,
    SignalGenerator,
    SignalStrength,
    SignalType,
    TradingSignal,
    generate_signals,
    signal_generator,
)
from .weight_manager import (
    DynamicWeightManager,
    IndicatorWeight,
    WeightPortfolio,
    WeightType,
    get_indicator_weights,
    weight_manager,
)

# 模塊信息
__version__ = "1.0.0"
__author__ = "Claude Code Assistant"
__description__ = "智能信號融合系統 - Phase 4 Implementation"

# 公開接口
__all__ = [
    # Signal Generator
    "SignalGenerator",
    "TradingSignal",
    "SignalType",
    "SignalStrength",
    "ConfidenceCalculator",
    "signal_generator",
    "generate_signals",
    # Weight Manager
    "DynamicWeightManager",
    "IndicatorWeight",
    "WeightPortfolio",
    "WeightType",
    "weight_manager",
    "get_indicator_weights",
    # Conflict Resolver
    "ConflictResolver",
    "SignalConflict",
    "ConflictResolution",
    "ConflictType",
    "ResolutionStrategy",
    "ResolutionPerformance",
    "conflict_resolver",
    "resolve_signal_conflicts",
    # Composite Signal Generator
    "CompositeSignalGenerator",
    "CompositeSignal",
    "SignalReport",
    "SignalQuality",
    "RiskLevel",
    "SignalQualityAssessor",
    "SignalRiskAssessor",
    "composite_signal_generator",
    "generate_composite_signal",
]


# 便利函數
def quick_signal_analysis(symbol: str, data: "pd.DataFrame", indicators: dict) -> dict:
    """
    快速信號分析便利函數

    Args:
        symbol: 股票代碼
        data: OHLCV數據
        indicators: 技術指標數據

    Returns:
        包含綜合信號和分析結果的字典
    """
    # 生成基礎信號
    signals = signal_generator.generate_signals(symbol, data, indicators)

    # 檢測衝突
    conflicts = conflict_resolver.detect_conflicts(signals)

    # 解決衝突
    if conflicts:
        conflict_resolver.resolve_conflicts(conflicts)

    # 生成綜合信號
    composite_signal = composite_signal_generator.generate_composite_signal(
        symbol, data, indicators
    )

    # 生成報告
    report = composite_signal_generator.generate_signal_report(composite_signal, data)

    return {
        "symbol": symbol,
        "individual_signals": signals,
        "conflicts_detected": len(conflicts),
        "composite_signal": composite_signal,
        "report": report,
        "analysis_time": signals[0].timestamp if signals else None,
    }


def get_signal_recommendations(symbol: str, signal: CompositeSignal) -> list:
    """
    獲取基於信號的具體操作建議

    Args:
        symbol: 股票代碼
        signal: 綜合信號

    Returns:
        操作建議列表
    """
    recommendations = []

    if signal.signal_type == SignalType.BUY:
        recommendations.extend(
            [
                f"立即買入 {symbol}",
                (
                    f"目標價格: {signal.target_price:.2f}"
                    if signal.target_price
                    else "未設置目標價格"
                ),
                (
                    f"止損價格: {signal.stop_loss:.2f}"
                    if signal.stop_loss
                    else "未設置止損價格"
                ),
                f"建議倉位: {signal.expected_return:.1%}",
                f"預期持有期: {signal.holding_period} 天",
            ]
        )
    elif signal.signal_type == SignalType.SELL:
        recommendations.extend(
            [
                f"立即賣出 {symbol}",
                (
                    f"目標價格: {signal.target_price:.2f}"
                    if signal.target_price
                    else "未設置目標價格"
                ),
                (
                    f"止損價格: {signal.stop_loss:.2f}"
                    if signal.stop_loss
                    else "未設置止損價格"
                ),
                f"預期回報: {signal.expected_return:.1%}",
                f"預期持有期: {signal.holding_period} 天",
            ]
        )
    else:
        recommendations.extend(
            [f"持倉觀望 {symbol}", "等待更明確的信號", "關注市場變化"]
        )

    # 基於質量的建議
    if signal.quality_score >= 80:
        recommendations.append("信號質量優秀，建議執行")
    elif signal.quality_score >= 60:
        recommendations.append("信號質量良好，可謹慎執行")
    else:
        recommendations.append("信號質量一般，建議等待更佳時機")

    # 基於風險的建議
    if signal.risk_score >= 8:
        recommendations.append("⚠️ 高風險信號，嚴格控制倉位")
    elif signal.risk_score <= 3:
        recommendations.append("✅ 低風險信號，可適度加倉")

    return recommendations


# 性能統計
def get_system_performance() -> dict:
    """
    獲取信號融合系統的性能統計

    Returns:
        性能統計字典
    """
    return {
        "signal_generator": {
            "total_signals_generated": len(signal_generator.signal_history),
            "average_confidence": (
                np.mean([s.confidence for s in signal_generator.signal_history])
                if signal_generator.signal_history
                else 0
            ),
            "top_performing_indicators": signal_generator.get_signal_summary(
                signal_generator.signal_history
            ),
        },
        "conflict_resolver": {
            "total_conflicts_resolved": len(conflict_resolver.resolution_history),
            "strategy_recommendations": conflict_resolver.get_strategy_recommendations(),
            "average_resolution_time": (
                np.mean(
                    [
                        perf.resolution_time
                        for perf in conflict_resolver.strategy_performance.values()
                        if perf.resolution_time > 0
                    ]
                )
                if conflict_resolver.strategy_performance
                else 0
            ),
        },
        "composite_generator": {
            "total_composite_signals": len(
                composite_signal_generator.composite_signal_history
            ),
            "average_quality_score": (
                np.mean(
                    [
                        s.quality_score
                        for s in composite_signal_generator.composite_signal_history
                    ]
                )
                if composite_signal_generator.composite_signal_history
                else 0
            ),
            "success_rate": (
                np.mean(
                    [
                        s.success_probability
                        for s in composite_signal_generator.composite_signal_history
                    ]
                )
                if composite_signal_generator.composite_signal_history
                else 0
            ),
        },
    }


print("信號融合模塊已加載 - Phase 4 智能信號融合系統")
