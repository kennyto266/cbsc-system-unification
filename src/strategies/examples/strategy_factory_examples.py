"""
Strategy Factory v2.0 Usage Examples
策略工廠使用示例

This file demonstrates various ways to use the Strategy Factory v2.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import the factory
from ..enhanced_factory_v2 import (
    StrategyFactoryV2,
    create_strategy,
    get_available_strategies,
    get_strategies_by_type
)
from ..enhanced_factory import StrategyType


def create_sample_data(symbol: str = "AAPL", days: int = 252) -> pd.DataFrame:
    """創建樣本OHLCV數據"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=days),
                          periods=days, freq='D')

    # Generate realistic price data
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.02, days)
    prices = [100]

    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    # Create OHLCV data
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        high = close * (1 + abs(np.random.normal(0, 0.02)))
        low = close * (1 - abs(np.random.normal(0, 0.02)))
        open_price = close * (1 + np.random.normal(0, 0.01))
        volume = np.random.randint(1000000, 10000000)

        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    df = pd.DataFrame(data, index=dates)
    return df


def example_1_basic_usage():
    """示例1: 基本使用方法"""
    print("\n=== 示例1: 基本使用方法 ===")

    # 获取所有可用策略
    strategies = get_available_strategies()
    print(f"總可用策略數: {len(strategies)}")

    # 按类型获取策略
    technical_strategies = get_strategies_by_type(StrategyType.TECHNICAL_ANALYSIS)
    momentum_strategies = get_strategies_by_type(StrategyType.MOMENTUM)
    volume_strategies = get_strategies_by_type(StrategyType.VOLUME)

    print(f"技術指標策略: {list(technical_strategies.keys())}")
    print(f"動量策略: {list(momentum_strategies.keys())}")
    print(f"成交量策略: {list(volume_strategies.keys())}")

    # 创建一个简单策略
    ma_strategy = create_strategy("ma_crossover", {
        "fast_period": 10,
        "slow_period": 20,
        "symbols": ["AAPL"]
    })

    print(f"創建的策略: {ma_strategy.STRATEGY_NAME}")


def example_2_strategy_configuration():
    """示例2: 策略配置驗證"""
    print("\n=== 示例2: 策略配置驗證 ===")

    factory = StrategyFactoryV2()

    # 验证配置
    config = {
        "period": 14,
        "trend_threshold": 25,
        "symbols": ["AAPL", "GOOGL"]
    }

    result = factory.validate_strategy_config("adx", config)

    if result['valid']:
        print("✅ 配置有效")
        strategy = factory.create_strategy("adx", config)
        print(f"成功創建ADX策略: {strategy.STRATEGY_NAME}")
    else:
        print("❌ 配置無效:")
        for error in result['errors']:
            print(f"  - {error}")

    # 尝试无效配置
    invalid_config = {"period": -5}  # 负数周期
    result = factory.validate_strategy_config("rsi", invalid_config)

    if not result['valid']:
        print("\n無效配置示例:")
        for error in result['errors']:
            print(f"  - {error}")


def example_3_batch_operations():
    """示例3: 批量操作"""
    print("\n=== 示例3: 批量操作 ===")

    factory = StrategyFactoryV2()

    # 批量创建策略配置
    configs = [
        {
            "name": "ma_crossover",
            "fast_period": 10,
            "slow_period": 20,
            "symbols": ["AAPL"]
        },
        {
            "name": "rsi",
            "period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70,
            "symbols": ["AAPL"]
        },
        {
            "name": "adx",
            "period": 14,
            "trend_threshold": 25,
            "symbols": ["AAPL"]
        },
        {
            "name": "obv",
            "ma_period": 20,
            "divergence_period": 10,
            "symbols": ["AAPL"]
        }
    ]

    # 批量创建策略
    strategies = factory.create_strategy_batch(configs)
    print(f"成功創建 {len(strategies)} 個策略")

    # 显示创建的策略
    for strategy in strategies:
        print(f"  - {strategy.STRATEGY_NAME} ({strategy.STRATEGY_TYPE.value})")


def example_4_strategy_execution():
    """示例4: 策略執行"""
    print("\n=== 示例4: 策略執行 ===")

    # 创建测试数据
    data = {"AAPL": create_sample_data("AAPL", 100)}

    # 创建策略
    strategy = create_strategy("ma_crossover", {
        "fast_period": 10,
        "slow_period": 20,
        "symbols": ["AAPL"]
    })

    # 执行策略
    result = strategy.execute(data)

    print(f"策略名稱: {result['strategy_name']}")
    print(f"執行時間: {result['execution_time']:.4f}秒")

    # 获取信号
    signals = result['results']['AAPL']['signals']
    print(f"生成信號數: {len(signals)}")

    # 显示最新信号
    if len(signals) > 0:
        latest_signal = signals.iloc[-1]
        print(f"最新信號: {latest_signal['signal_type']}")
        print(f"信號強度: {latest_signal.get('signal_strength', 'N/A')}")


def example_5_strategy_search():
    """示例5: 策略搜索"""
    print("\n=== 示例5: 策略搜索 ===")

    factory = StrategyFactoryV2()

    # 搜索移动平均相关策略
    ma_strategies = factory.search_strategies("ma")
    print(f"移動平均相關策略 ({len(ma_strategies)}個):")
    for metadata in ma_strategies:
        print(f"  - {metadata.name}: {metadata.description}")

    # 搜索成交量相关策略
    volume_strategies = factory.search_strategies("volume")
    print(f"\n成交量相關策略 ({len(volume_strategies)}個):")
    for metadata in volume_strategies:
        print(f"  - {metadata.name}: {metadata.description}")

    # 搜索趋势相关策略
    trend_strategies = factory.search_strategies("trend")
    print(f"\n趨勢相關策略 ({len(trend_strategies)}個):")
    for metadata in trend_strategies:
        print(f"  - {metadata.name}: {metadata.description}")


def example_6_configuration_templates():
    """示例6: 配置模板導出"""
    print("\n=== 示例6: 配置模板導出 ===")

    factory = StrategyFactoryV2()

    # 导出策略配置模板
    template = factory.export_strategy_config("ma_crossover")

    if template:
        print("MA交叉策略配置模板:")
        print(f"  名稱: {template['name']}")
        print(f"  類型: {template['type']}")
        print(f"  描述: {template['description']}")
        print(f"  必需參數: {template['required_parameters']}")
        print(f"  可選參數: {list(template['optional_parameters'].keys())}")

        # 使用默认配置创建策略
        default_strategy = factory.create_strategy(
            "ma_crossover",
            template["parameters"]
        )
        print(f"\n使用默認配置創建策略: {default_strategy.STRATEGY_NAME}")


def example_7_strategy_statistics():
    """示例7: 策略統計"""
    print("\n=== 示例7: 策略統計 ===")

    factory = StrategyFactoryV2()

    # 获取统计信息
    stats = factory.get_strategy_stats()

    print(f"總策略數: {stats['total_strategies']}")
    print(f"工廠版本: {stats['latest_version']}")
    print("\n各類型策略數量:")
    for strategy_type, count in stats['by_type'].items():
        print(f"  {strategy_type}: {count}個")


def example_8_legacy_strategy_compatibility():
    """示例8: 遺留策略兼容性"""
    print("\n=== 示例8: 遺留策略兼容性 ===")

    # 获取所有策略，包括遗留策略
    all_strategies = get_available_strategies()
    legacy_strategies = {name: meta for name, meta in all_strategies.items()
                        if name.endswith('_legacy')}

    print(f"遺留策略數: {len(legacy_strategies)}")
    if legacy_strategies:
        print("可用的遺留策略:")
        for name in legacy_strategies.keys():
            print(f"  - {name}")

        # 创建一个遗留策略
        if "adx_legacy" in legacy_strategies:
            legacy_strategy = create_strategy("adx_legacy", {
                "period": 14,
                "symbols": ["AAPL"]
            })
            print(f"\n創建遺留ADX策略: {legacy_strategy.STRATEGY_NAME}")


def example_9_advanced_workflow():
    """示例9: 高級工作流程"""
    print("\n=== 示例9: 高級工作流程 ===")

    # 创建多个策略进行组合测试
    symbols = ["AAPL", "GOOGL", "MSFT"]
    data = {symbol: create_sample_data(symbol, 200) for symbol in symbols}

    # 定义策略配置
    strategy_configs = [
        {
            "name": "ma_crossover",
            "fast_period": 10,
            "slow_period": 20,
            "symbols": symbols
        },
        {
            "name": "rsi",
            "period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70,
            "symbols": symbols
        },
        {
            "name": "adx",
            "period": 14,
            "trend_threshold": 25,
            "symbols": symbols
        },
        {
            "name": "obv",
            "ma_period": 20,
            "divergence_period": 10,
            "symbols": symbols
        }
    ]

    # 批量创建并执行策略
    factory = StrategyFactoryV2()
    strategies = factory.create_strategy_batch(strategy_configs)

    # 收集所有结果
    all_results = {}
    for strategy in strategies:
        result = strategy.execute(data)
        all_results[strategy.STRATEGY_NAME] = result

        # 显示简要结果
        total_signals = sum(
            len(r['signals']) for r in result['results'].values()
        )
        print(f"{strategy.STRATEGY_NAME}: {total_signals}個信號")

    # 分析信号一致性
    print("\n信號一致性分析:")
    for symbol in symbols:
        symbol_signals = {}
        for strategy_name, result in all_results.items():
            if symbol in result['results']:
                signals = result['results'][symbol]['signals']
                if len(signals) > 0:
                    latest_signal = signals.iloc[-1]['signal_type']
                    symbol_signals[strategy_name] = latest_signal

        print(f"\n{symbol}:")
        for strategy, signal in symbol_signals.items():
            print(f"  {strategy}: {signal}")


def example_10_error_handling():
    """示例10: 錯誤處理"""
    print("\n=== 示例10: 錯誤處理 ===")

    factory = StrategyFactoryV2()

    # 处理不存在的策略
    try:
        strategy = factory.create_strategy("nonexistent_strategy", {})
    except ValueError as e:
        print(f"捕獲錯誤: {e}")

    # 处理无效配置
    try:
        strategy = factory.create_strategy("rsi", {"period": "invalid"})
    except ValueError as e:
        print(f"捕獲配置錯誤: {e}")

    # 批量创建时的错误处理
    configs = [
        {"name": "ma_crossover", "fast_period": 10, "slow_period": 20},
        {"name": "invalid_strategy"},  # 这个会失败
        {"name": "rsi", "period": 14}
    ]

    strategies = factory.create_strategy_batch(configs)
    print(f"批量創建結果: 期望3個，實際創建{len(strategies)}個")


def run_all_examples():
    """運行所有示例"""
    print("🚀 Strategy Factory v2.0 使用示例")
    print("=" * 50)

    examples = [
        example_1_basic_usage,
        example_2_strategy_configuration,
        example_3_batch_operations,
        example_4_strategy_execution,
        example_5_strategy_search,
        example_6_configuration_templates,
        example_7_strategy_statistics,
        example_8_legacy_strategy_compatibility,
        example_9_advanced_workflow,
        example_10_error_handling
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ 示例 {example_func.__name__} 執行失敗: {e}")

    print("\n✅ 所有示例執行完成")


if __name__ == "__main__":
    run_all_examples()