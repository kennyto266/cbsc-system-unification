#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的GPU功能测试
测试GPU计算核心和监控系统
"""

import sys
import os
import time
import numpy as np
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

def test_gpu_core():
    """测试GPU计算核心"""
    print("Testing GPU Computation Core...")

    try:
        from src.gpu.gpu_computation_core import get_gpu_computation_core

        # 创建GPU核心
        gpu_core = get_gpu_computation_core(0)
        print(f"GPU Core initialized: {gpu_core is not None}")

        # 生成测试数据
        test_data = np.random.uniform(100, 200, 1000).astype(np.float32)
        print(f"Generated test data: {len(test_data)} samples")

        # 测试RSI
        start_time = time.time()
        rsi_result = gpu_core.calculate_rsi_gpu(test_data, 14)
        rsi_time = time.time() - start_time

        print(f"RSI calculation: {rsi_time:.4f}s, result length: {len(rsi_result)}")
        print(f"RSI result range: {rsi_result.min():.2f} - {rsi_result.max():.2f}")

        # 测试MACD
        start_time = time.time()
        macd, signal, hist = gpu_core.calculate_macd_gpu(test_data)
        macd_time = time.time() - start_time

        print(f"MACD calculation: {macd_time:.4f}s")
        print(f"MACD result length: {len(macd)}, Signal: {len(signal)}, Hist: {len(hist)}")

        # 性能基准测试
        benchmark = gpu_core.benchmark_performance(50000)
        print(f"Performance benchmark: {benchmark}")

        return True

    except Exception as e:
        print(f"GPU Core test failed: {e}")
        return False

def test_gpu_monitor():
    """测试GPU监控"""
    print("\nTesting GPU Monitor...")

    try:
        from src.gpu.gpu_monitor import get_gpu_monitor, TemporaryGPUMonitor

        with TemporaryGPUMonitor() as monitor:
            print("GPU Monitor started successfully")

            # 模拟一些计算
            monitor.start_operation("test_computation")
            time.sleep(2)  # 模拟计算时间
            monitor.end_operation(data_size=10000, cpu_time_ms=5000, success=True)

            monitor.start_operation("test_computation_2")
            time.sleep(1)
            monitor.end_operation(data_size=5000, cpu_time_ms=3000, success=True)

            # 生成报告
            report = monitor.monitor.generate_performance_report()
            print(f"GPU Monitor Report Generated")
            print(f"Total operations: {report.get('performance_summary', {}).get('total_operations', 0)}")
            print(f"GPU success rate: {report.get('performance_summary', {}).get('gpu_success_rate', 0):.1f}%")

            return True

    except Exception as e:
        print(f"GPU Monitor test failed: {e}")
        return False

def test_memory_manager():
    """测试GPU内存管理"""
    print("\nTesting GPU Memory Manager...")

    try:
        from src.gpu.memory_manager import get_gpu_memory_manager

        memory_manager = get_gpu_memory_manager(0)
        print("GPU Memory Manager initialized")

        # 获取内存使用情况
        memory_usage = memory_manager.get_memory_usage()
        print(f"Memory usage: {memory_usage}")

        # 测试内存分配
        test_array = memory_manager.allocate_optimal((1000,), 'float32')
        print(f"Allocated test array: {test_array.shape}")

        # 获取统计信息
        stats = memory_manager.get_memory_stats()
        print(f"Memory stats: {stats}")

        # 清理内存
        memory_manager.cleanup_memory()
        print("Memory cleanup completed")

        return True

    except Exception as e:
        print(f"Memory Manager test failed: {e}")
        return False

def test_data_pipeline():
    """测试GPU数据管道"""
    print("\nTesting GPU Data Pipeline...")

    try:
        from src.gpu.gpu_pipeline import get_gpu_pipeline
        import pandas as pd

        # 创建测试数据
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        test_data = pd.DataFrame({
            'date': dates,
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.randint(1000, 5000, 100)
        })

        pipeline = get_gpu_pipeline(0)
        print("GPU Data Pipeline initialized")

        # 预处理股票数据
        gpu_stock_data = pipeline.preprocess_stock_data(test_data)
        print(f"Stock data preprocessing: {len(gpu_stock_data)} fields")

        # 准备技术分析数据
        analysis_data = pipeline.prepare_for_technical_analysis(gpu_stock_data)
        print(f"Technical analysis data: {len(analysis_data)} indicators")

        return True

    except Exception as e:
        print(f"Data Pipeline test failed: {e}")
        return False

def run_complete_test():
    """运行完整测试"""
    print("=" * 60)
    print("Fixed GPU System Comprehensive Test")
    print("=" * 60)

    results = {}

    # 测试各个组件
    results['gpu_core'] = test_gpu_core()
    results['gpu_monitor'] = test_gpu_monitor()
    results['memory_manager'] = test_memory_manager()
    results['data_pipeline'] = test_data_pipeline()

    # 汇总结果
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for component, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"{component:20s}: {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")

    # 保存测试结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_results = {
        'timestamp': timestamp,
        'test_results': results,
        'summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': passed_tests/total_tests*100
        }
    }

    filename = f"gpu_system_test_results_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nTest results saved to: {filename}")

    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_complete_test()

    if success:
        print("\nAll GPU system tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome GPU system tests FAILED!")
        sys.exit(1)