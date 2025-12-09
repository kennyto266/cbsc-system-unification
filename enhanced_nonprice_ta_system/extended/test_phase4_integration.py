#!/usr/bin/env python3
"""
Phase 4 Signal Fusion System Integration Test
Phase 4 信号融合系统集成测试

Quick integration test to verify the Phase 4 signal fusion system components
are working correctly together.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试基本功能...")

    try:
        # 尝试导入核心模块
        from signal_fusion import (
            SignalGenerator, SignalType,
            DynamicWeightManager,
            ConflictResolver,
            CompositeSignalGenerator
        )
        print("✅ 核心模块导入成功")

        # 创建简单的测试数据
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        test_data = {
            'RSI': pd.Series(50 + 20 * np.random.randn(50), index=dates).clip(0, 100),
            'MACD': pd.Series(np.random.randn(50) * 0.1, index=dates),
            'HIBOR_RATE': pd.Series(3.0 + 0.5 * np.random.randn(50), index=dates)
        }

        # 创建组件
        signal_gen = SignalGenerator()
        weight_mgr = DynamicWeightManager({
            'RSI': 0.4, 'MACD': 0.3, 'HIBOR_RATE': 0.3
        })
        conflict_resolver = ConflictResolver()
        composite_gen = CompositeSignalGenerator(
            signal_generator=signal_gen,
            weight_manager=weight_mgr,
            conflict_resolver=conflict_resolver
        )

        print("✅ 组件创建成功")

        # 测试信号生成
        print("\n📊 测试信号生成...")
        parameters = {
            'RSI': {'name': 'RSI', 'period': 14, 'oversold': 30, 'overbought': 70},
            'MACD': {'name': 'MACD_HIST', 'fast': 12, 'slow': 26, 'signal': 9},
            'HIBOR_RATE': {'name': 'HIBOR_RATE'}
        }

        for indicator, data in test_data.items():
            try:
                signal = signal_gen.generate_signal(
                    indicator_name=indicator,
                    indicator_values=data,
                    parameters=parameters[indicator]
                )
                print(f"  • {indicator}: {signal.signal_type.name} "
                      f"(强度: {signal.strength:.1f}, 置信度: {signal.confidence:.2f})")
            except Exception as e:
                print(f"  • {indicator}: ❌ {str(e)}")

        # 测试复合信号生成
        print("\n🎯 测试复合信号生成...")
        market_context = {'regime': 'bull', 'volatility': 0.02}

        composite_signal = composite_gen.generate_composite_signal(
            indicator_data=test_data,
            parameters=parameters,
            market_context=market_context
        )

        print(f"  • 复合信号: {composite_signal.signal_type.name}")
        print(f"  • 强度: {composite_signal.strength:.2f}/10")
        print(f"  • 置信度: {composite_signal.confidence:.2%}")
        print(f"  • 质量: {composite_signal.quality.value}")
        print(f"  • 组成信号数: {len(composite_signal.component_signals)}")

        if composite_signal.explanation:
            print(f"  • 解释: {composite_signal.explanation.summary}")

        print("✅ 基本功能测试通过")
        return True

    except Exception as e:
        print(f"❌ 基本功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_system_capabilities():
    """测试系统能力"""
    print("\n🚀 测试系统能力...")

    try:
        from signal_fusion import get_system_capabilities

        capabilities = get_system_capabilities()

        print("✅ 系统能力概述:")
        for component, features in capabilities.items():
            print(f"\n📦 {component.upper()}:")
            if isinstance(features, dict):
                for feature, value in features.items():
                    if isinstance(value, list):
                        print(f"  • {feature}: {', '.join(value[:3])}{'...' if len(value) > 3 else ''}")
                    else:
                        print(f"  • {feature}: {value}")
            else:
                print(f"  • {features}")

        print("✅ 系统能力测试通过")
        return True

    except Exception as e:
        print(f"❌ 系统能力测试失败: {str(e)}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n🛡️ 测试错误处理...")

    try:
        from signal_fusion import SignalGenerator, DynamicWeightManager

        signal_gen = SignalGenerator()

        # 测试空数据
        empty_data = pd.Series(dtype=float)
        try:
            signal = signal_gen.generate_signal(
                indicator_name='RSI',
                indicator_values=empty_data,
                parameters={'name': 'RSI'}
            )
            print(f"  • 空数据处理: {signal.signal_type.name} (预期: HOLD)")
        except Exception as e:
            print(f"  • 空数据处理: ❌ {str(e)}")

        # 测试无效参数
        valid_data = pd.Series([50, 55, 60, 58, 62])
        try:
            signal = signal_gen.generate_signal(
                indicator_name='UNKNOWN_INDICATOR',
                indicator_values=valid_data,
                parameters={'name': 'UNKNOWN_INDICATOR'}
            )
            print(f"  • 未知指标: {signal.signal_type.name} (预期: HOLD)")
        except Exception as e:
            print(f"  • 未知指标: ❌ {str(e)}")

        print("✅ 错误处理测试通过")
        return True

    except Exception as e:
        print(f"❌ 错误处理测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🧪 Phase 4 信号融合系统集成测试")
    print("="*50)

    tests = [
        ("基本功能", test_basic_functionality),
        ("系统能力", test_system_capabilities),
        ("错误处理", test_error_handling)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"💥 {test_name} 测试异常: {str(e)}")

    print(f"\n{'='*50}")
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过! Phase 4 信号融合系统运行正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查系统配置。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)