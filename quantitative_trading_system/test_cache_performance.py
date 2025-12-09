#!/usr/bin/env python3
"""
缓存性能测试脚本
Cache Performance Test Script

验证指标缓存机制的性能提升效果
目标：计算速度提升5x以上

Author: Claude Code Assistant
Created: 2025-11-29
Version: 1.0.0 (Week 2 Task 2.4)
"""

import sys
import os
import time
import numpy as np
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indicators.core_indicators import CoreIndicators

def create_test_data(size: int = 1000) -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range('2020-01-01', periods=size, freq='D')
    return pd.DataFrame({
        'open': np.random.uniform(100, 200, size),
        'high': np.random.uniform(100, 200, size),
        'low': np.random.uniform(100, 200, size),
        'close': np.random.uniform(100, 200, size),
        'volume': np.random.randint(1000, 10000, size)
    }, index=dates)

def test_individual_indicator_performance():
    """测试单个指标的性能"""
    print("Individual Indicator Performance Test")
    print("=" * 50)

    indicators = CoreIndicators()
    test_data = create_test_data(1000)
    close_prices = test_data['close']

    # 测试指标列表
    test_indicators = [
        ('sma', {'period': 20}),
        ('ema', {'period': 20}),
        ('rsi', {'period': 14}),
        ('macd', {'fast': 12, 'slow': 26, 'signal': 9}),
    ]

    results = {}

    for indicator_name, params in test_indicators:
        print(f"\nTesting {indicator_name.upper()}...")

        # 清空缓存，确保第一次计算
        indicators.clear_cache()

        # 第一次计算（无缓存）
        start_time = time.time()
        if indicator_name == 'sma':
            result1 = indicators.calculate_sma(close_prices, **params)
        elif indicator_name == 'ema':
            result1 = indicators.calculate_ema(close_prices, **params)
        elif indicator_name == 'rsi':
            result1 = indicators.calculate_rsi(close_prices, **params)
        elif indicator_name == 'macd':
            result1 = indicators.calculate_macd(close_prices, **params)

        first_calc_time = time.time() - start_time

        # 第二次计算（使用缓存）
        start_time = time.time()
        if indicator_name == 'sma':
            result2 = indicators.calculate_sma(close_prices, **params)
        elif indicator_name == 'ema':
            result2 = indicators.calculate_ema(close_prices, **params)
        elif indicator_name == 'rsi':
            result2 = indicators.calculate_rsi(close_prices, **params)
        elif indicator_name == 'macd':
            result2 = indicators.calculate_macd(close_prices, **params)

        cached_calc_time = time.time() - start_time

        # 计算性能提升
        if cached_calc_time > 0:
            speedup = first_calc_time / cached_calc_time
        else:
            speedup = float('inf')

        results[indicator_name] = {
            'first_calc': first_calc_time,
            'cached_calc': cached_calc_time,
            'speedup': speedup
        }

        print(f"  First calculation: {first_calc_time:.4f}s")
        print(f"  Cached calculation: {cached_calc_time:.4f}s")
        print(f"  Speedup: {speedup:.1f}x")

    return results

def test_batch_calculation_performance():
    """测试批量计算性能"""
    print("\n" + "=" * 50)
    print("Batch Calculation Performance Test")
    print("=" * 50)

    indicators = CoreIndicators()
    test_data = create_test_data(500)

    # 第一次批量计算（无缓存）
    print("\nFirst batch calculation (no cache)...")
    indicators.clear_cache()
    start_time = time.time()
    results1 = indicators.calculate_all_indicators(test_data)
    first_batch_time = time.time() - start_time

    print(f"  Time: {first_batch_time:.4f}s")
    print(f"  Indicators calculated: {len(results1)}")

    # 第二次批量计算（使用缓存）
    print("\nSecond batch calculation (with cache)...")
    start_time = time.time()
    results2 = indicators.calculate_all_indicators(test_data)
    cached_batch_time = time.time() - start_time

    print(f"  Time: {cached_batch_time:.4f}s")
    print(f"  Indicators calculated: {len(results2)}")

    # 性能提升
    if cached_batch_time > 0:
        batch_speedup = first_batch_time / cached_batch_time
        print(f"  Batch speedup: {batch_speedup:.1f}x")
    else:
        batch_speedup = float('inf')
        print(f"  Batch speedup: >1000x (cached calculation was instant)")

    return {
        'first_batch_time': first_batch_time,
        'cached_batch_time': cached_batch_time,
        'batch_speedup': batch_speedup
    }

def test_memory_usage():
    """测试内存使用情况"""
    print("\n" + "=" * 50)
    print("Memory Usage Test")
    print("=" * 50)

    indicators = CoreIndicators()

    # 执行多次计算以填充缓存
    test_data = create_test_data(1000)
    for i in range(20):
        indicators.calculate_sma(test_data['close'], period=10 + i)
        indicators.calculate_ema(test_data['close'], period=10 + i)

    # 获取缓存信息
    cache_info = indicators.get_cache_info()
    print(f"\nCache Information:")
    print(f"  Cache size: {cache_info['cache_size']} items")
    print(f"  Memory usage: {cache_info['memory_usage_mb']} MB")
    print(f"  Hit rate: {cache_info['hit_rate_percent']}%")
    print(f"  Top indicators: {', '.join(cache_info['top_indicators'])}")

    return cache_info

def test_concurrent_access():
    """测试并发访问性能"""
    print("\n" + "=" * 50)
    print("Concurrent Access Test")
    print("=" * 50)

    indicators = CoreIndicators()
    test_data = create_test_data(500)

    # 模拟快速重复计算
    print("Testing rapid repeated calculations...")
    start_time = time.time()

    for i in range(10):
        result = indicators.calculate_sma(test_data['close'], 20)

    total_time = time.time() - start_time
    avg_time = total_time / 10

    print(f"  Total time for 10 calculations: {total_time:.4f}s")
    print(f"  Average time per calculation: {avg_time:.4f}s")

    # 获取缓存统计
    cache_info = indicators.get_cache_info()
    print(f"  Cache hit rate: {cache_info['hit_rate_percent']}%")

    return {
        'total_time': total_time,
        'avg_time': avg_time,
        'hit_rate': cache_info['hit_rate_percent']
    }

def generate_performance_report(individual_results, batch_results, cache_info, concurrent_results):
    """生成性能报告"""
    print("\n" + "=" * 50)
    print("PERFORMANCE OPTIMIZATION REPORT")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: 5x+ performance improvement")
    print()

    # 单个指标性能
    print("1. Individual Indicator Performance:")
    avg_speedup = np.mean([r['speedup'] for r in individual_results.values()])
    max_speedup = max([r['speedup'] for r in individual_results.values()])
    print(f"   Average speedup: {avg_speedup:.1f}x")
    print(f"   Maximum speedup: {max_speedup:.1f}x")

    for indicator, result in individual_results.items():
        status = "✅ PASS" if result['speedup'] >= 5 else "⚠️  NEED IMPROVEMENT"
        print(f"   {indicator.upper():<12}: {result['speedup']:.1f}x speedup {status}")

    # 批量计算性能
    print(f"\n2. Batch Calculation Performance:")
    batch_speedup = batch_results['batch_speedup']
    batch_status = "✅ PASS" if batch_speedup >= 5 else "⚠️  NEED IMPROVEMENT"
    print(f"   Batch speedup: {batch_speedup:.1f}x {batch_status}")

    # 内存使用
    print(f"\n3. Memory Usage:")
    print(f"   Cache items: {cache_info['cache_size']}")
    print(f"   Memory usage: {cache_info['memory_usage_mb']} MB")
    print(f"   Hit rate: {cache_info['hit_rate_percent']}%")

    # 并发性能
    print(f"\n4. Concurrent Access:")
    print(f"   Average calculation time: {concurrent_results['avg_time']:.4f}s")
    print(f"   Cache hit rate: {concurrent_results['hit_rate']:.1f}%")

    # 总体评估
    print(f"\n5. Overall Assessment:")
    all_speedups = list(individual_results.values()) + [batch_results]
    overall_avg_speedup = np.mean([r['speedup'] for r in all_speedups])

    if overall_avg_speedup >= 5:
        print(f"   🎉 SUCCESS: {overall_avg_speedup:.1f}x average speedup achieved!")
        print(f"   ✅ Week 2 Task 2.4 completed successfully")
        print(f"   ✅ Performance goal (5x+) exceeded")
    else:
        print(f"   ⚠️  PARTIAL: {overall_avg_speedup:.1f}x average speedup achieved")
        print(f"   🔧 Further optimization needed to reach 5x+ target")

    return overall_avg_speedup >= 5

def main():
    """主测试函数"""
    print("Cache Performance Optimization Test Suite")
    print("=" * 50)
    print("Week 2 Task 2.4: Verify 5x+ performance improvement")
    print()

    try:
        # 运行所有测试
        individual_results = test_individual_indicator_performance()
        batch_results = test_batch_calculation_performance()
        cache_info = test_memory_usage()
        concurrent_results = test_concurrent_access()

        # 生成报告
        success = generate_performance_report(individual_results, batch_results, cache_info, concurrent_results)

        if success:
            print(f"\n🏆 Week 2 Task 2.4 COMPLETED SUCCESSFULLY!")
            print(f"   Cache optimization achieved 5x+ performance improvement")
            return 0
        else:
            print(f"\n⚠️  Week 2 Task 2.4 NEEDS IMPROVEMENT")
            print(f"   Cache optimization did not reach 5x+ target")
            return 1

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)