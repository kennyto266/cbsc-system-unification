#!/usr/bin/env python3
"""
Phase 4 Signal Fusion System Complete Demo
Phase 4 信号融合系统完整演示

This script demonstrates the complete functionality of the Phase 4 Signal Fusion System,
including all four components: signal generation, weight management, conflict resolution,
and composite signal generation with explainable AI capabilities.
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import warnings

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 抑制警告
warnings.filterwarnings('ignore')

def create_comprehensive_test_data():
    """创建全面的测试数据"""
    print("🔧 创建测试数据...")

    # 生成时间序列
    dates = pd.date_range('2023-01-01', periods=252, freq='D')  # 一年的交易日

    # 基础价格序列（模拟股价走势）
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 252)
    price = 100 * np.exp(np.cumsum(returns))

    # 生成各种技术指标数据
    data = {}

    # 1. 趋势指标
    data['RSI'] = pd.Series(
        50 + 30 * np.sin(np.linspace(0, 4*np.pi, 252)) + np.random.normal(0, 5, 252),
        index=dates,
        name='RSI'
    ).clip(0, 100)

    data['MACD'] = pd.Series(
        np.cumsum(np.random.randn(252) * 0.1),
        index=dates,
        name='MACD'
    )

    data['DEMA'] = pd.Series(
        price * (1 + 0.01 * np.sin(np.linspace(0, 2*np.pi, 252))),
        index=dates,
        name='DEMA'
    )

    # 2. 动量指标
    data['STOCHASTIC'] = pd.Series(
        50 + 40 * np.sin(np.linspace(0, 6*np.pi, 252)) + np.random.normal(0, 8, 252),
        index=dates,
        name='STOCHASTIC'
    ).clip(0, 100)

    data['WILLIAMS_R'] = pd.Series(
        50 + 45 * np.sin(np.linspace(0, 5*np.pi, 252)) + np.random.normal(0, 10, 252),
        index=dates,
        name='WILLIAMS_R'
    ).clip(-100, 0)

    # 3. 波动率指标
    data['BOLLINGER_BANDS'] = pd.Series(
        price * (1 + 0.02 * np.sin(np.linspace(0, 3*np.pi, 252))),
        index=dates,
        name='BOLLINGER_BANDS'
    )

    data['ATR'] = pd.Series(
        2 + np.abs(np.random.randn(252) * 0.5),
        index=dates,
        name='ATR'
    ).clip(0.5, 10)

    # 4. 香港政府数据专用指标
    data['HIBOR_RATE'] = pd.Series(
        3.0 + 1.5 * np.sin(np.linspace(0, 2*np.pi, 252)) + np.random.normal(0, 0.2, 252),
        index=dates,
        name='HIBOR_RATE'
    ).clip(0.5, 8)

    data['MONETARY_BASE'] = pd.Series(
        1000 * np.exp(np.linspace(0, 0.05, 252)) + np.random.normal(0, 10, 252),
        index=dates,
        name='MONETARY_BASE'
    ).clip(900, 1500)

    data['EXCHANGE_RATE'] = pd.Series(
        7.8 + 0.2 * np.sin(np.linspace(0, 4*np.pi, 252)) + np.random.normal(0, 0.05, 252),
        index=dates,
        name='EXCHANGE_RATE'
    ).clip(7.5, 8.1)

    data['LIQUIDITY_PRESSURE'] = pd.Series(
        50 + 30 * np.sin(np.linspace(0, 3*np.pi, 252)) + np.random.normal(0, 8, 252),
        index=dates,
        name='LIQUIDITY_PRESSURE'
    ).clip(0, 100)

    print(f"✅ 创建了 {len(data)} 个指标的测试数据，每个指标 {len(dates)} 个数据点")
    return data

def create_indicator_parameters():
    """创建指标参数配置"""
    print("⚙️ 配置指标参数...")

    parameters = {
        # 趋势指标参数
        'RSI': {
            'name': 'RSI',
            'period': 14,
            'oversold': 30,
            'overbought': 70
        },
        'MACD': {
            'name': 'MACD_HIST',
            'fast': 12,
            'slow': 26,
            'signal': 9
        },
        'DEMA': {
            'name': 'DEMA',
            'period': 21
        },

        # 动量指标参数
        'STOCHASTIC': {
            'name': 'STOCHASTIC',
            'oversold': 20,
            'overbought': 80
        },
        'WILLIAMS_R': {
            'name': 'WILLIAMS_R',
            'oversold': -80,
            'overbought': -20
        },

        # 波动率指标参数
        'BOLLINGER_BANDS': {
            'name': 'BOLLINGER',
            'period': 20,
            'std_dev': 2
        },
        'ATR': {
            'name': 'ATR',
            'period': 14
        },

        # 香港政府数据指标参数
        'HIBOR_RATE': {
            'name': 'HIBOR_RATE',
            'threshold_high': 4.0,
            'threshold_low': 2.0
        },
        'MONETARY_BASE': {
            'name': 'MONETARY_BASE',
            'growth_threshold': 0.02
        },
        'EXCHANGE_RATE': {
            'name': 'EXCHANGE_RATE',
            'strong_threshold': 7.85,
            'weak_threshold': 7.95
        },
        'LIQUIDITY_PRESSURE': {
            'name': 'LIQUIDITY_PRESSURE',
            'high_pressure': 70,
            'low_pressure': 30
        }
    }

    print(f"✅ 配置了 {len(parameters)} 个指标的参数")
    return parameters

def create_market_contexts():
    """创建多种市场上下文场景"""
    print("📊 创建市场上下文场景...")

    contexts = {
        'bull_market': {
            'regime': 'bull',
            'volatility': 0.015,
            'trend': 'upward',
            'market_sentiment': 'optimistic',
            'economic_cycle': 'expansion'
        },
        'bear_market': {
            'regime': 'bear',
            'volatility': 0.035,
            'trend': 'downward',
            'market_sentiment': 'pessimistic',
            'economic_cycle': 'contraction'
        },
        'sideways_market': {
            'regime': 'sideways',
            'volatility': 0.020,
            'trend': 'neutral',
            'market_sentiment': 'uncertain',
            'economic_cycle': 'transition'
        },
        'high_volatility': {
            'regime': 'crisis',
            'volatility': 0.050,
            'trend': 'volatile',
            'market_sentiment': 'fearful',
            'economic_cycle': 'recession'
        },
        'low_volatility': {
            'regime': 'stable',
            'volatility': 0.008,
            'trend': 'steady',
            'market_sentiment': 'calm',
            'economic_cycle': 'stable'
        }
    }

    print(f"✅ 创建了 {len(contexts)} 种市场上下文场景")
    return contexts

def demo_phase4_1_signal_generation(signal_generator, indicator_data, parameters):
    """演示 Phase 4.1: 单指标信号生成"""
    print("\n" + "="*60)
    print("🚀 Phase 4.1 演示: 单指标信号生成")
    print("="*60)

    # 选择几个代表性指标进行演示
    demo_indicators = ['RSI', 'MACD', 'HIBOR_RATE', 'MONETARY_BASE']

    for indicator in demo_indicators:
        if indicator not in indicator_data:
            continue

        print(f"\n📈 分析指标: {indicator}")

        try:
            # 生成信号
            signal = signal_generator.generate_signal(
                indicator_name=indicator,
                indicator_values=indicator_data[indicator],
                parameters=parameters[indicator]
            )

            # 显示信号详情
            print(f"  • 信号类型: {signal.signal_type.name}")
            print(f"  • 信号值: {signal.signal_value:.3f}")
            print(f"  • 信号强度: {signal.strength:.2f}/10")
            print(f"  • 置信度: {signal.confidence:.2%}")
            print(f"  • 原始指标值: {signal.raw_indicator_value:.4f}")
            print(f"  • 生成时间: {signal.timestamp.strftime('%H:%M:%S')}")

            # 获取信号统计
            stats = signal_generator.get_signal_statistics(indicator)
            if stats:
                print(f"  • 历史统计: 总信号={stats.total_signals}, "
                      f"买入={stats.buy_signals}, 卖出={stats.sell_signals}, "
                      f"平均强度={stats.avg_strength:.2f}")

        except Exception as e:
            print(f"  ❌ 信号生成失败: {str(e)}")

    # 显示系统性能摘要
    print(f"\n📊 信号生成器性能摘要:")
    performance = signal_generator.get_performance_summary()
    print(f"  • 总指标数: {performance['total_indicators']}")
    print(f"  • 总信号数: {performance['total_signals']}")
    print(f"  • 信号格式: {performance['configuration']['signal_format']}")

def demo_phase4_2_weight_management(weight_manager, signal_generator, indicator_data, parameters):
    """演示 Phase 4.2: 多指标权重管理"""
    print("\n" + "="*60)
    print("⚖️ Phase 4.2 演示: 多指标权重管理")
    print("="*60)

    # 显示初始权重
    print("\n📊 初始权重配置:")
    initial_weights = weight_manager.initial_weights
    for indicator, weight in sorted(initial_weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {indicator}: {weight:.3f}")

    # 生成一些性能数据用于权重调整
    print("\n🔄 模拟权重调整...")

    # 创建模拟性能数据
    performance_data = {
        'indicator_performance': {},
        'correlation_matrix': {}
    }

    indicators = list(initial_weights.keys())
    for indicator in indicators:
        # 模拟不同的性能表现
        base_performance = np.random.uniform(0.3, 0.8)
        performance_data['indicator_performance'][indicator] = {
            'sharpe_ratio': base_performance + np.random.uniform(-0.2, 0.3),
            'total_return': base_performance * 0.5,
            'win_rate': base_performance,
            'max_drawdown': -np.random.uniform(0.05, 0.2),
            'stability_score': base_performance,
            'performance_score': base_performance
        }

    # 模拟相关性矩阵
    for i, indicator1 in enumerate(indicators):
        performance_data['correlation_matrix'][indicator1] = {}
        for j, indicator2 in enumerate(indicators):
            if i == j:
                performance_data['correlation_matrix'][indicator1][indicator2] = 1.0
            else:
                correlation = np.random.uniform(0.1, 0.8)
                performance_data['correlation_matrix'][indicator1][indicator2] = correlation

    # 市场数据
    market_data = {
        'price_data': indicator_data.get('RSI', pd.Series()),
        'volatility': 0.025
    }

    # 更新权重
    updated_weights = weight_manager.update_weights(
        performance_data=performance_data,
        market_data=market_data,
        force_rebalance=True
    )

    print("\n📊 更新后权重配置:")
    for indicator, weight in sorted(updated_weights.items(), key=lambda x: x[1], reverse=True):
        old_weight = initial_weights[indicator]
        change = weight - old_weight
        arrow = "↗️" if change > 0 else "↘️" if change < 0 else "➡️"
        print(f"  • {indicator}: {weight:.3f} {arrow} ({change:+.3f})")

    # 权重统计
    stats = weight_manager.get_weight_statistics()
    print(f"\n📈 权重统计信息:")
    print(f"  • 最大权重变化: {max(stats['weight_changes'].values()):.3f}")
    print(f"  • 平均性能分数: {np.mean(list(stats['performance_scores'].values())):.3f}")

    # 演示权重优化
    print("\n🎯 演示权重优化...")

    def objective_function(weights):
        """简单的目标函数"""
        # 模拟基于权重的性能分数
        score = 0
        for indicator, weight in weights.items():
            indicator_perf = performance_data['indicator_performance'].get(indicator, {})
            perf_score = indicator_perf.get('performance_score', 0.5)
            score += weight * perf_score
        return score

    try:
        optimized_weights = weight_manager.optimize_weights(
            objective_function=objective_function,
            optimization_method='random_search',
            num_iterations=50
        )

        print("✅ 权重优化完成")
        original_score = objective_function(initial_weights)
        optimized_score = objective_function(optimized_weights)
        print(f"  • 原始权重分数: {original_score:.4f}")
        print(f"  • 优化权重分数: {optimized_score:.4f}")
        print(f"  • 改善程度: {((optimized_score - original_score) / original_score * 100):+.2f}%")

    except Exception as e:
        print(f"  ❌ 权重优化失败: {str(e)}")

def demo_phase4_3_conflict_resolution(conflict_resolver, signal_generator, indicator_data, parameters):
    """演示 Phase 4.3: 信号冲突解决"""
    print("\n" + "="*60)
    print("⚔️ Phase 4.3 演示: 信号冲突解决")
    print("="*60)

    # 生成多个信号，可能产生冲突
    print("\n🔍 生成测试信号...")

    # 选择容易产生冲突的指标
    conflict_indicators = ['RSI', 'STOCHASTIC', 'MACD', 'HIBOR_RATE', 'LIQUIDITY_PRESSURE']
    signals = []

    for indicator in conflict_indicators:
        if indicator not in indicator_data:
            continue

        try:
            # 创建一些可能冲突的参数
            modified_params = parameters[indicator].copy()
            if indicator == 'RSI':
                # 创建超买超卖信号
                current_value = indicator_data[indicator].iloc[-1]
                if current_value > 70:
                    modified_params['overbought'] = 60  # 降低阈值，增加卖出信号
                elif current_value < 30:
                    modified_params['oversold'] = 40  # 提高阈值，增加买入信号

            signal = signal_generator.generate_signal(
                indicator_name=indicator,
                indicator_values=indicator_data[indicator],
                parameters=modified_params
            )
            signals.append(signal)

            print(f"  • {indicator}: {signal.signal_type.name} (强度: {signal.strength:.1f}, 置信度: {signal.confidence:.2f})")

        except Exception as e:
            print(f"  ❌ {indicator} 信号生成失败: {str(e)}")

    if len(signals) < 2:
        print("⚠️  信号数量不足，跳过冲突解决演示")
        return

    print(f"\n🎭 生成 {len(signals)} 个信号，检测冲突...")

    # 测试不同的冲突解决策略
    strategies = [
        ('多数投票', None),
        ('加权投票', None),
        ('置信度加权', None),
        ('共识方法', None),
        ('集成方法', None)
    ]

    market_context = {
        'regime': 'bull',
        'volatility': 0.025,
        'trend': 'upward'
    }

    for strategy_name, strategy in strategies:
        print(f"\n🔧 测试策略: {strategy_name}")

        try:
            resolved_signal, conflicts = conflict_resolver.resolve_conflicts(
                signals=signals,
                weights={'RSI': 0.3, 'MACD': 0.25, 'STOCHASTIC': 0.2, 'HIBOR_RATE': 0.15, 'LIQUIDITY_PRESSURE': 0.1},
                market_context=market_context,
                strategy=strategy
            )

            if resolved_signal:
                print(f"  ✅ 解决结果: {resolved_signal.signal_type.name}")
                print(f"     强度: {resolved_signal.strength:.2f}, 置信度: {resolved_signal.confidence:.2f}")
                print(f"     策略: {conflicts[0].resolution_strategy.value if conflicts else 'N/A'}")
            else:
                print(f"  ⚠️  未生成解决信号")

            if conflicts:
                print(f"  ⚠️  检测到 {len(conflicts)} 个冲突:")
                for i, conflict in enumerate(conflicts[:3]):  # 只显示前3个
                    print(f"     {i+1}. {conflict.conflict_type.value} (严重程度: {conflict.severity.name})")

        except Exception as e:
            print(f"  ❌ 策略测试失败: {str(e)}")

    # 显示冲突解决性能指标
    print(f"\n📊 冲突解决性能指标:")
    metrics = conflict_resolver.get_resolution_metrics()
    print(f"  • 总冲突数: {metrics.total_conflicts}")
    print(f"  • 解决冲突数: {metrics.resolved_conflicts}")
    print(f"  • 解决成功率: {metrics.resolution_success_rate:.2%}")
    print(f"  • 平均解决时间: {metrics.avg_resolution_time:.3f}秒")

def demo_phase4_4_composite_generation(composite_generator, indicator_data, parameters, market_contexts):
    """演示 Phase 4.4: 复合信号生成"""
    print("\n" + "="*60)
    print("🎯 Phase 4.4 演示: 复合信号生成")
    print("="*60)

    # 在不同市场上下文中生成复合信号
    for context_name, context in market_contexts.items():
        print(f"\n🌍 市场场景: {context_name}")
        print(f"   市场状态: {context.get('regime', 'unknown')}")
        print(f"   波动率: {context.get('volatility', 0):.2%}")
        print(f"   趋势: {context.get('trend', 'unknown')}")

        try:
            # 生成复合信号
            composite_signal = composite_generator.generate_composite_signal(
                indicator_data=indicator_data,
                parameters=parameters,
                market_context=context
            )

            # 显示复合信号详情
            print(f"\n📊 复合信号结果:")
            print(f"  • 信号类型: {composite_signal.signal_type.name}")
            print(f"  • 信号值: {composite_signal.signal_value:.3f}")
            print(f"  • 信号强度: {composite_signal.strength:.2f}/10")
            print(f"  • 置信度: {composite_signal.confidence:.2%}")
            print(f"  • 信号质量: {composite_signal.quality.value}")
            print(f"  • 组成信号数: {len(composite_signal.component_signals)}")
            print(f"  • 解决策略: {composite_signal.resolution_strategy.value if composite_signal.resolution_strategy else 'N/A'}")

            # 显示信号解释摘要
            if composite_signal.explanation:
                print(f"\n💡 信号解释:")
                print(f"  • 摘要: {composite_signal.explanation.summary}")
                print(f"  • 关键因素: {list(composite_signal.explanation.key_factors.keys())[:3]}")
                print(f"  • 贡献指标: {composite_signal.explanation.contributing_indicators[:3]}")
                if composite_signal.explanation.risk_factors:
                    print(f"  • 风险因素: {', '.join(composite_signal.explanation.risk_factors[:2])}")

            # 生成解释报告
            report = composite_generator.generate_explanation_report(composite_signal)
            report_file = f"signal_report_{context_name}_{datetime.now().strftime('%H%M%S')}.md"

            try:
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"  📄 详细报告已保存: {report_file}")
            except Exception as e:
                print(f"  ⚠️  报告保存失败: {str(e)}")

            # 生成可视化
            viz_file = f"signal_viz_{context_name}_{datetime.now().strftime('%H%M%S')}.html"
            try:
                viz_path = composite_generator.generate_signal_visualization(
                    composite_signal, viz_file
                )
                if viz_path:
                    print(f"  📊 可视化已保存: {viz_path}")
            except Exception as e:
                print(f"  ⚠️  可视化生成失败: {str(e)}")

        except Exception as e:
            print(f"  ❌ 复合信号生成失败: {str(e)}")

    # 显示系统性能指标
    print(f"\n📈 复合信号生成器性能指标:")
    metrics = composite_generator.get_performance_metrics()
    print(f"  • 总信号数: {metrics.total_signals}")
    print(f"  • 平均置信度: {metrics.avg_confidence:.2%}")
    print(f"  • 平均强度: {metrics.avg_strength:.2f}")
    print(f"  • 解释效果: {metrics.explanation_effectiveness:.2f}")

    # 质量分布
    if metrics.quality_distribution:
        print(f"  • 质量分布:")
        for quality, count in metrics.quality_distribution.items():
            percentage = count / metrics.total_signals * 100 if metrics.total_signals > 0 else 0
            print(f"     - {quality}: {count} ({percentage:.1f}%)")

def main():
    """主演示函数"""
    print("🚀 Phase 4 信号融合系统完整演示")
    print("="*60)
    print("本演示将展示信号融合系统的所有四个Phase的功能")

    try:
        # 1. 导入必要的模块
        print("\n📦 导入信号融合系统模块...")
        from signal_fusion import (
            SignalGenerator,
            DynamicWeightManager,
            ConflictResolver,
            CompositeSignalGenerator,
            create_complete_fusion_system
        )
        print("✅ 模块导入成功")

        # 2. 创建测试数据
        indicator_data = create_comprehensive_test_data()
        parameters = create_indicator_parameters()
        market_contexts = create_market_contexts()

        # 3. 初始化系统组件
        print("\n🔧 初始化系统组件...")

        # 创建初始权重
        initial_weights = {
            'RSI': 0.20,
            'MACD': 0.15,
            'DEMA': 0.10,
            'STOCHASTIC': 0.10,
            'WILLIAMS_R': 0.08,
            'BOLLINGER_BANDS': 0.08,
            'ATR': 0.05,
            'HIBOR_RATE': 0.12,
            'MONETARY_BASE': 0.07,
            'EXCHANGE_RATE': 0.03,
            'LIQUIDITY_PRESSURE': 0.02
        }

        # 创建各个组件
        signal_generator = SignalGenerator(
            signal_format='multi_level',
            confidence_threshold=0.6,
            enable_historical_tracking=True
        )

        weight_manager = DynamicWeightManager(
            initial_weights=initial_weights,
            adjustment_strategy='hybrid',
            enable_optimization=True
        )

        conflict_resolver = ConflictResolver(
            default_strategy='weighted_voting',
            enable_learning=True
        )

        composite_generator = CompositeSignalGenerator(
            signal_generator=signal_generator,
            weight_manager=weight_manager,
            conflict_resolver=conflict_resolver,
            explanation_level='detailed',
            enable_quality_assessment=True
        )

        print("✅ 系统组件初始化完成")

        # 4. 演示各个Phase
        demo_phase4_1_signal_generation(signal_generator, indicator_data, parameters)
        demo_phase4_2_weight_management(weight_manager, signal_generator, indicator_data, parameters)
        demo_phase4_3_conflict_resolution(conflict_resolver, signal_generator, indicator_data, parameters)
        demo_phase4_4_composite_generation(composite_generator, indicator_data, parameters, market_contexts)

        # 5. 生成综合报告
        print("\n" + "="*60)
        print("📋 生成综合报告")
        print("="*60)

        # 导出信号数据
        try:
            signal_dataframe = composite_generator.export_composite_signals(format='dataframe')
            if not signal_dataframe.empty:
                export_file = f"composite_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                signal_dataframe.to_csv(export_file, index=False)
                print(f"✅ 复合信号数据已导出: {export_file}")
                print(f"   包含 {len(signal_dataframe)} 个信号记录")
        except Exception as e:
            print(f"❌ 数据导出失败: {str(e)}")

        # 系统综合报告
        comprehensive_report = composite_generator.generate_comprehensive_report()
        report_file = f"fusion_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)
            print(f"✅ 综合报告已保存: {report_file}")
        except Exception as e:
            print(f"❌ 报告保存失败: {str(e)}")

        # 显示系统摘要
        print(f"\n📊 系统运行摘要:")
        print(f"  • 处理指标数: {len(indicator_data)}")
        print(f"  • 生成信号数: {comprehensive_report['performance_metrics']['total_signals']}")
        print(f"  • 平均置信度: {comprehensive_report['performance_metrics']['avg_confidence']:.2%}")
        print(f"  • 系统质量评估: {comprehensive_report['recent_statistics']['avg_confidence']:.2%}")

        print(f"\n🎉 Phase 4 信号融合系统演示完成!")
        print(f"系统已成功演示:")
        print(f"  ✅ Phase 4.1: 单指标信号生成")
        print(f"  ✅ Phase 4.2: 多指标权重管理")
        print(f"  ✅ Phase 4.3: 信号冲突解决")
        print(f"  ✅ Phase 4.4: 复合信号生成")

        return True

    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n✨ 演示成功完成! 查看生成的文件了解详细结果。")
    else:
        print(f"\n💥 演示过程中遇到问题，请检查日志。")
        sys.exit(1)