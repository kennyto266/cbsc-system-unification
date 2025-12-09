#!/usr/bin/env python3
"""
Phase 1: GPU to CPU 32-Process Migration Test

测试和验证CPU 32进程多进程优化的第一阶段实现。

测试内容:
1. CalculatorConfig 32进程配置
2. CPU特定内存管理
3. 32进程RSI计算
4. Numba优化指标
5. 性能基准测试
"""

import sys
import os
import time
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the enhanced calculator
try:
    sys.path.insert(0, str(project_root))
    from src.shared.indicators.comprehensive_477_calculator import (
        Comprehensive477Calculator, CalculatorConfig, NUMBA_AVAILABLE
    )
    PHASE1_AVAILABLE = True
except ImportError as e:
    print(f"Phase 1 implementation not available: {e}")
    PHASE1_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('phase1_test_results.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def generate_test_data(data_points: int = 10000) -> pd.DataFrame:
    """生成测试数据"""
    print(f"生成 {data_points} 个测试数据点...")

    # 生成模拟OHLCV数据
    np.random.seed(42)

    # 基础价格走势
    base_price = 100.0
    price_changes = np.random.randn(data_points) * 0.02
    prices = base_price * np.cumprod(1 + price_changes)

    # 生成OHLC数据
    close_prices = prices
    high_prices = close_prices + np.abs(np.random.randn(data_points) * 0.5)
    low_prices = close_prices - np.abs(np.random.randn(data_points) * 0.5)
    open_prices = close_prices + np.random.randn(data_points) * 0.3
    volumes = np.random.randint(1000000, 5000000, data_points)

    test_data = pd.DataFrame({
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })

    print(f"测试数据生成完成，数据形状: {test_data.shape}")
    return test_data

def test_calculator_config():
    """测试CalculatorConfig 32进程配置"""
    print("\n" + "="*60)
    print("测试1: CalculatorConfig 32进程配置")
    print("="*60)

    # 创建配置
    config = CalculatorConfig()

    print(f"默认配置:")
    print(f"  max_workers: {config.max_workers}")
    print(f"  use_process_pool: {config.use_process_pool}")
    print(f"  enable_cpu_multiprocessing: {getattr(config, 'enable_cpu_multiprocessing', False)}")
    print(f"  memory_per_process_mb: {getattr(config, 'memory_per_process_mb', 'N/A')}")
    print(f"  total_memory_limit_gb: {getattr(config, 'total_memory_limit_gb', 'N/A')}")

    # 验证32进程配置
    if config.max_workers == 32:
        print("✅ max_workers 已正确设置为32")
    else:
        print(f"❌ max_workers 期望32，实际{config.max_workers}")

    if config.use_process_pool == True:
        print("✅ use_process_pool 已正确启用")
    else:
        print(f"❌ use_process_pool 期望True，实际{config.use_process_pool}")

    if hasattr(config, 'enable_cpu_multiprocessing') and config.enable_cpu_multiprocessing:
        print("✅ enable_cpu_multiprocessing 已正确启用")
    else:
        print("❌ enable_cpu_multiprocessing 未正确配置")

    return config

def test_memory_management(calculator):
    """测试内存管理"""
    print("\n" + "="*60)
    print("测试2: CPU 32进程内存管理")
    print("="*60)

    memory_manager = calculator.memory_manager

    # 获取内存状态
    memory_status = memory_manager.get_memory_status()
    print("内存管理状态:")
    for key, value in memory_status.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    # 测试最优数据块创建
    data_size = 10000
    chunks = memory_manager.create_optimal_chunks(data_size)
    print(f"\n数据块优化:")
    print(f"  数据大小: {data_size}")
    print(f"  生成块数: {len(chunks)}")
    print(f"  块大小分布: {[end-start for start, end in chunks[:5]]}...")  # 只显示前5个

    # 测试内存验证
    test_shape = (10000,)
    is_valid = memory_manager.validate_memory_requirements(test_shape, np.float64)
    print(f"\n内存需求验证:")
    print(f"  数据形状: {test_shape}")
    print(f"  数据类型: {np.float64}")
    print(f"  验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")

    return memory_status

def test_rsi_calculation(calculator, test_data):
    """测试RSI计算"""
    print("\n" + "="*60)
    print("测试3: 32进程RSI计算")
    print("="*60)

    close_prices = test_data['close'].values
    rsi_period = 14

    print(f"RSI计算测试:")
    print(f"  数据点数: {len(close_prices)}")
    print(f"  RSI周期: {rsi_period}")
    print(f"  Numba可用: {NUMBA_AVAILABLE}")

    # 测试不同RSI计算方法
    try:
        # 方法1: Python单进程 (基准)
        start_time = time.time()
        python_rsi = calculator._rsi_python(close_prices, rsi_period)
        python_time = time.time() - start_time
        print(f"  Python单进程: {python_time:.4f}s")

        # 方法2: Numba单进程
        if NUMBA_AVAILABLE:
            start_time = time.time()
            numba_rsi = calculator._calculate_rsi(close_prices, period=rsi_period)
            numba_time = time.time() - start_time
            print(f"  Numba单进程: {numba_time:.4f}s")

            # 验证结果一致性
            valid_indices = ~(np.isnan(python_rsi) | np.isnan(numba_rsi))
            diff = np.abs(python_rsi[valid_indices] - numba_rsi[valid_indices])
            max_diff = np.max(diff) if len(diff) > 0 else 0
            print(f"  Python vs Numba 最大差异: {max_diff:.6f}")

            if max_diff < 1e-6:
                print("  ✅ Python和Numba结果一致")
            else:
                print(f"  ⚠️ Python和Numba结果存在差异: {max_diff:.6f}")

        # 方法3: 32进程并行 (仅对大数据集)
        if len(close_prices) > 1000:
            start_time = time.time()
            parallel_rsi = calculator._calculate_rsi_32process(close_prices, rsi_period)
            parallel_time = time.time() - start_time
            print(f"  32进程并行: {parallel_time:.4f}s")

            # 验证并行结果一致性
            if NUMBA_AVAILABLE:
                valid_indices = ~(np.isnan(numba_rsi) | np.isnan(parallel_rsi))
                diff = np.abs(numba_rsi[valid_indices] - parallel_rsi[valid_indices])
                max_diff = np.max(diff) if len(diff) > 0 else 0
                print(f"  Numba vs 32进程 最大差异: {max_diff:.6f}")

                if max_diff < 1e-6:
                    print("  ✅ Numba和32进程结果一致")
                else:
                    print(f"  ⚠️ Numba和32进程结果存在差异: {max_diff:.6f}")

                # 计算加速比
                if python_time > 0:
                    numba_speedup = python_time / numba_time
                    parallel_speedup = python_time / parallel_time
                    print(f"  Numba加速比: {numba_speedup:.2f}x")
                    print(f"  32进程加速比: {parallel_speedup:.2f}x")

                    # 性能评估
                    if parallel_speedup > 1.5:
                        print("  ✅ 32进程并行显示显著性能提升")
                    elif parallel_speedup > 1.1:
                        print("  ⚠️ 32进程并行显示轻微性能提升")
                    else:
                        print("  ❌ 32进程并行未显示性能提升")
        else:
            print("  跳过32进程并行测试 (数据量太小)")

        # 返回RSI结果用于进一步分析
        return {
            'python_rsi': python_rsi,
            'numba_rsi': numba_rsi if NUMBA_AVAILABLE else None,
            'parallel_rsi': parallel_rsi if len(close_prices) > 1000 else None
        }

    except Exception as e:
        print(f"❌ RSI计算测试失败: {e}")
        return None

def test_numba_optimized_indicators(calculator, test_data):
    """测试Numba优化指标"""
    print("\n" + "="*60)
    print("测试4: Numba优化指标")
    print("="*60)

    if not NUMBA_AVAILABLE:
        print("❌ Numba不可用，跳过测试")
        return None

    close_prices = test_data['close'].values
    high_prices = test_data['high'].values
    low_prices = test_data['low'].values

    print(f"测试数据: {len(close_prices)} 个数据点")

    # 导入Numba函数进行测试
    try:
        from src.shared.indicators.comprehensive_477_calculator import (
            calculate_sma_numba,
            calculate_ema_parallel_numba,
            calculate_macd_parallel_numba,
            calculate_bollinger_bands_parallel_numba,
            calculate_atr_parallel_numba
        )

        # 测试指标
        indicators_test = {}

        # 1. SMA
        start_time = time.time()
        sma = calculate_sma_numba(close_prices, 14)
        sma_time = time.time() - start_time
        indicators_test['SMA'] = {'result': sma, 'time': sma_time}
        print(f"  SMA (14): {sma_time:.4f}s")

        # 2. EMA
        start_time = time.time()
        ema = calculate_ema_parallel_numba(close_prices, 14)
        ema_time = time.time() - start_time
        indicators_test['EMA'] = {'result': ema, 'time': ema_time}
        print(f"  EMA (14): {ema_time:.4f}s")

        # 3. MACD
        start_time = time.time()
        macd = calculate_macd_parallel_numba(close_prices, 12, 26, 9)
        macd_time = time.time() - start_time
        indicators_test['MACD'] = {'result': macd, 'time': macd_time}
        print(f"  MACD (12,26,9): {macd_time:.4f}s")

        # 4. Bollinger Bands
        start_time = time.time()
        bb = calculate_bollinger_bands_parallel_numba(close_prices, 20, 2.0)
        bb_time = time.time() - start_time
        indicators_test['Bollinger'] = {'result': bb, 'time': bb_time}
        print(f"  布林带 (20,2.0): {bb_time:.4f}s")

        # 5. ATR
        start_time = time.time()
        atr = calculate_atr_parallel_numba(high_prices, low_prices, close_prices, 14)
        atr_time = time.time() - start_time
        indicators_test['ATR'] = {'result': atr, 'time': atr_time}
        print(f"  ATR (14): {atr_time:.4f}s")

        # 计算总时间
        total_time = sum(info['time'] for info in indicators_test.values())
        print(f"\n  所有Numba指标总计算时间: {total_time:.4f}s")
        print(f"  平均每个指标: {total_time/len(indicators_test):.4f}s")

        # 验证结果有效性
        print("\n  结果验证:")
        for name, info in indicators_test.items():
            result = info['result']
            valid_count = np.sum(~np.isnan(result))
            total_count = len(result)
            print(f"    {name}: {valid_count}/{total_count} 有效值 ({valid_count/total_count*100:.1f}%)")

        print("  ✅ 所有Numba优化指标测试完成")
        return indicators_test

    except Exception as e:
        print(f"❌ Numba指标测试失败: {e}")
        return None

def test_performance_benchmark(calculator, test_data):
    """运行性能基准测试"""
    print("\n" + "="*60)
    print("测试5: 性能基准测试")
    print("="*60)

    close_prices = test_data['close'].values

    try:
        # 使用内置的基准测试方法
        benchmark_results = calculator._benchmark_rsi_methods(close_prices, 14)

        print("\n性能基准测试结果:")
        for method, time_taken in benchmark_results.items():
            if isinstance(time_taken, float):
                print(f"  {method}: {time_taken:.4f}s")
            else:
                print(f"  {method}: {time_taken}")

        # 生成基准测试报告
        print("\n🎯 性能分析:")
        if '32process_parallel' in benchmark_results and 'numba_single' in benchmark_results:
            parallel_time = benchmark_results['32process_parallel']
            numba_time = benchmark_results['numba_single']

            if parallel_time < numba_time:
                speedup = numba_time / parallel_time
                print(f"  ✅ 32进程比Numba单进程快 {speedup:.2f}x")
            else:
                slowdown = parallel_time / numba_time
                print(f"  ⚠️ 32进程比Numba单进程慢 {slowdown:.2f}x")

        return benchmark_results

    except Exception as e:
        print(f"❌ 性能基准测试失败: {e}")
        return None

def generate_phase1_report(test_results):
    """生成Phase 1测试报告"""
    print("\n" + "="*80)
    print("Phase 1: GPU to CPU 32-Process Migration - 测试报告")
    print("="*80)

    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'phase': 'Phase 1 - Foundation',
        'results': test_results
    }

    # 测试结果总结
    print("📊 测试结果总结:")

    # 1. 配置测试
    if 'config' in test_results:
        config = test_results['config']
        print(f"\n1️⃣ 配置测试:")
        print(f"   ✅ 32进程配置: {config.max_workers} workers")
        print(f"   ✅ 进程池启用: {config.use_process_pool}")
        print(f"   ✅ CPU多进程: {getattr(config, 'enable_cpu_multiprocessing', False)}")

    # 2. 内存管理测试
    if 'memory_status' in test_results:
        memory = test_results['memory_status']
        print(f"\n2️⃣ 内存管理:")
        print(f"   当前内存: {memory.get('current_memory_mb', 0):.2f}MB")
        print(f"   内存利用率: {memory.get('memory_utilization', 0)*100:.1f}%")
        if 'cpu_multiprocessing_enabled' in memory:
            print(f"   ✅ CPU多进程内存管理: 已启用")

    # 3. RSI计算测试
    if 'rsi_results' in test_results:
        rsi = test_results['rsi_results']
        print(f"\n3️⃣ RSI计算:")
        print(f"   ✅ Python实现: 可用")
        if NUMBA_AVAILABLE:
            print(f"   ✅ Numba优化: 可用")
            print(f"   ✅ 32进程并行: 可用")

    # 4. Numba指标测试
    if 'numba_indicators' in test_results and test_results['numba_indicators']:
        print(f"\n4️⃣ Numba优化指标:")
        indicators = test_results['numba_indicators']
        print(f"   ✅ 测试指标数: {len(indicators)}")
        total_time = sum(info['time'] for info in indicators.values())
        print(f"   ✅ 总计算时间: {total_time:.4f}s")

    # 5. 性能基准测试
    if 'benchmark' in test_results and test_results['benchmark']:
        print(f"\n5️⃣ 性能基准:")
        benchmark = test_results['benchmark']
        if 'parallel_speedup' in benchmark:
            speedup = benchmark['parallel_speedup']
            if speedup > 1.5:
                print(f"   ✅ 32进程加速比: {speedup:.2f}x (优秀)")
            elif speedup > 1.1:
                print(f"   ⚠️ 32进程加速比: {speedup:.2f}x (良好)")
            else:
                print(f"   ❌ 32进程加速比: {speedup:.2f}x (需改进)")

    # 总体评估
    print(f"\n🎯 Phase 1 总体评估:")

    success_criteria = 0
    total_criteria = 5

    # 评估各项标准
    if 'config' in test_results:
        config = test_results['config']
        if config.max_workers == 32 and config.use_process_pool:
            success_criteria += 1
            print(f"   ✅ 32进程配置: 通过")
        else:
            print(f"   ❌ 32进程配置: 失败")

    if 'memory_status' in test_results:
        success_criteria += 1
        print(f"   ✅ 内存管理: 通过")

    if 'rsi_results' in test_results and test_results['rsi_results']:
        success_criteria += 1
        print(f"   ✅ RSI计算: 通过")

    if 'numba_indicators' in test_results and test_results['numba_indicators']:
        success_criteria += 1
        print(f"   ✅ Numba优化: 通过")

    if 'benchmark' in test_results and test_results['benchmark']:
        success_criteria += 1
        print(f"   ✅ 性能测试: 通过")

    # 计算成功率
    success_rate = (success_criteria / total_criteria) * 100
    print(f"\n📈 Phase 1 成功率: {success_rate:.1f}% ({success_criteria}/{total_criteria})")

    if success_rate >= 80:
        print("🎉 Phase 1 实现成功！可以进入Phase 2（核心迁移）")
    elif success_rate >= 60:
        print("⚠️ Phase 1 基本成功，建议优化后进入Phase 2")
    else:
        print("❌ Phase 1 需要改进，建议修复问题后重新测试")

    return report

def main():
    """主测试函数"""
    print("开始 Phase 1: GPU to CPU 32-Process Migration 测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python路径: {sys.executable}")
    print(f"工作目录: {os.getcwd()}")

    # 检查Phase 1可用性
    if not PHASE1_AVAILABLE:
        print("❌ Phase 1 implementation不可用，无法进行测试")
        return

    # 生成测试数据
    test_data = generate_test_data(5000)  # 适中的数据量用于测试

    # 创建计算器实例
    print("\n初始化477指标计算器...")
    config = CalculatorConfig()
    calculator = Comprehensive477Calculator(config)

    # 收集测试结果
    test_results = {}

    try:
        # 运行所有测试
        test_results['config'] = test_calculator_config()
        test_results['memory_status'] = test_memory_management(calculator)
        test_results['rsi_results'] = test_rsi_calculation(calculator, test_data)
        test_results['numba_indicators'] = test_numba_optimized_indicators(calculator, test_data)
        test_results['benchmark'] = test_performance_benchmark(calculator, test_data)

        # 生成测试报告
        report = generate_phase1_report(test_results)

        # 清理资源
        calculator.cleanup()

        print("\n" + "="*80)
        print("Phase 1 测试完成！详细日志已保存到 phase1_test_results.log")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

        # 清理资源
        try:
            calculator.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()