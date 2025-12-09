#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU環境檢測測試套件
驗證GPU檢測、配置和回退機制
"""

import unittest
import logging
import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Add simplified_system/src to path too for compatibility
simplified_src_path = os.path.join(os.path.dirname(__file__), '..', 'simplified_system', 'src')
if simplified_src_path not in sys.path:
    sys.path.insert(0, simplified_src_path)

# Configure logging
logging.basicConfig(level=logging.INFO)

from utils.gpu_detector import GPUEnvironment, get_gpu_environment

# Import gpu_config from main src
try:
    from utils.gpu_config import GPUConfigManager, get_gpu_config_manager
except ImportError:
    print("Warning: gpu_config not found, skipping ConfigManager tests")
    GPUConfigManager = None
    get_gpu_config_manager = None

class TestGPUEnvironment(unittest.TestCase):
    """GPU環境測試"""

    def setUp(self):
        """測試設置"""
        self.gpu_env = GPUEnvironment()

    def test_gpu_detection(self):
        """測試GPU檢測"""
        print("\n=== GPU Environment Test ===")

        # 基礎檢測
        self.assertIsInstance(self.gpu_env.cupy_available, bool)
        self.assertIsInstance(self.gpu_env.cuda_available, bool)
        self.assertIsInstance(self.gpu_env.gpu_count, int)
        self.assertIsInstance(self.gpu_env.gpu_memory_gb, (int, float))

        # 系統信息
        system_info = self.gpu_env.get_system_info()
        self.assertIsInstance(system_info, dict)

        # 驗證必要字段
        required_fields = [
            'cupy_available', 'cuda_available', 'gpu_count',
            'gpu_memory_gb', 'backend', 'gpu_acceleration_possible'
        ]

        for field in required_fields:
            self.assertIn(field, system_info)

        print(f"GPU detection: {system_info['gpu_count']} devices")
        print(f"Memory available: {system_info['gpu_memory_gb']:.1f} GB")
        print(f"Backend: {system_info['backend']}")

    def test_nonprice_optimization_readiness(self):
        """測試非價格優化準備度"""
        print("\n=== Non-Price Optimization Readiness ===")

        readiness = self.gpu_env.is_ready_for_nonprice_optimization()
        self.assertIsInstance(readiness, bool)

        # 獲取能力分數
        memory_score = self.gpu_env.memory_efficiency_score
        parallel_score = self.gpu_env.parallel_capability_score

        print(f"Non-price optimization ready: {readiness}")
        print(f"Memory efficiency score: {memory_score}")
        print(f"Parallel capability score: {parallel_score}")

        # 獲取優化建議
        recommendations = self.gpu_env.get_gpu_optimization_recommendations()
        self.assertIsInstance(recommendations, dict)

        print(f"GPU optimization recommended: {recommendations['recommended']}")
        print(f"Suggested batch size: {recommendations['batch_size_suggestion']}")
        print(f"Memory limit: {recommendations['memory_limit_gb']} GB")

    def test_gpu_computation(self):
        """測試GPU計算能力"""
        print("\n=== GPU Computation Test ===")

        if not self.gpu_env.is_gpu_available():
            print("GPU not available, skipping computation test")
            self.skipTest("GPU not available")

        test_results = self.gpu_env.test_gpu_computation(size=10000)
        self.assertIsInstance(test_results, dict)

        print(f"GPU test passed: {test_results['gpu_test_passed']}")
        print(f"CPU time: {test_results['cpu_time']:.4f}s")
        print(f"GPU time: {test_results['gpu_time']:.4f}s")

        if test_results['gpu_test_passed']:
            speedup = test_results.get('speedup', 0)
            print(f"Speedup: {speedup:.2f}x")

class TestGPUConfigManager(unittest.TestCase):
    """GPU配置管理器測試"""

    def setUp(self):
        """測試設置"""
        if GPUConfigManager is None:
            self.skipTest("GPUConfigManager not available")
        self.config_manager = GPUConfigManager()

    def test_config_initialization(self):
        """測試配置初始化"""
        print("\n=== GPU Config Manager Test ===")

        config_summary = self.config_manager.get_config_summary()
        self.assertIsInstance(config_summary, dict)

        print(f"GPU available: {config_summary['gpu_available']}")
        print(f"Max memory: {config_summary['config']['max_memory_gb']} GB")
        print(f"Batch size: {config_summary['config']['batch_size']}")

        if config_summary.get('memory_status'):
            memory_status = config_summary['memory_status']
            print(f"Memory utilization: {memory_status['utilization_percent']:.1f}%")

    def test_optimal_batch_size(self):
        """測試最優批大小計算"""
        print("\n=== Optimal Batch Size Test ===")

        test_cases = [
            (1000, 1.0),
            (10000, 1.0),
            (100000, 1.0),
        ]

        for data_size, complexity_factor in test_cases:
            batch_size = self.config_manager.get_optimal_batch_size(data_size)
            self.assertIsInstance(batch_size, int)
            self.assertGreater(batch_size, 0)
            self.assertLessEqual(batch_size, data_size)

            print(f"Data size {data_size:6d} -> Batch size {batch_size:6d}")

    def test_gpu_usage_decision(self):
        """測試GPU使用決策"""
        print("\n=== GPU Usage Decision Test ===")

        test_cases = [
            (500, 1.0),    # 小數據
            (5000, 1.0),   # 中等數據
            (50000, 1.0),  # 大數據
        ]

        for data_size, complexity_factor in test_cases:
            should_use_gpu = self.config_manager.should_use_gpu(data_size, complexity_factor)
            self.assertIsInstance(should_use_gpu, bool)

            print(f"Data size {data_size:6d} -> Use GPU: {should_use_gpu}")

def run_gpu_tests():
    """運行所有GPU測試"""
    print("Starting GPU Environment Tests")
    print("=" * 50)

    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加測試
    suite.addTests(loader.loadTestsFromTestCase(TestGPUEnvironment))
    suite.addTests(loader.loadTestsFromTestCase(TestGPUConfigManager))

    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 總結
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("All GPU tests passed!")
    else:
        print(f"{len(result.failures)} test failures, {len(result.errors)} errors")

        # 打印失敗詳情
        for test, failure in result.failures:
            print(f"\n{test}: {failure}")

    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_gpu_tests()
    sys.exit(0 if success else 1)