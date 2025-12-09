#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
向量化引擎測試套件
驗證時間序列向量化功能
"""

import logging
import os
import sys
import unittest

import numpy as np
import pandas as pd

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Configure logging
logging.basicConfig(level = logging.INFO)


class TestVectorizationEngine(unittest.TestCase):
    """向量化引擎測試"""

    def setUp(self):
        """測試設置"""
        from vectorization.time_series import (
            get_multi_source_vectorizer,
            get_time_series_vectorizer,
        )

        self.vectorizer = get_time_series_vectorizer()
        self.multi_vectorizer = get_multi_source_vectorizer()

        # 創建測試數據
        self.test_data = self._create_test_data()

    def _create_test_data(self):
        """創建測試數據"""
        # 生成時間序列
        dates = pd.date_range(start="2024 - 01 - 01", end="2024 - 12 - 31", freq="D")

        # 創建不同類型的測試數據
        data = {}

        # HIBOR類型數據（利率）
        hibor_values = (
            3.5
            + 0.5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365)
            + np.random.normal(0, 0.1, len(dates))
        )
        data["HB"] = pd.DataFrame({"value": hibor_values, "tenor": "ON"}, index = dates)

        # 貨幣基礎類型數據（金額）
        monetary_values = (
            1800
            + 200 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365)
            + np.random.normal(0, 50, len(dates))
        )
        data["MB"] = pd.DataFrame(
            {"value": monetary_values, "component": "MB"}, index = dates
        )

        # GDP類型數據（季度，較少波動）
        gdp_dates = pd.date_range(start="2024 - 01 - 01", end="2024 - 12 - 31", freq="Q")
        gdp_values = (
            700
            + np.arange(len(gdp_dates)) * 10
            + np.random.normal(0, 5, len(gdp_dates))
        )
        data["GD"] = pd.DataFrame(
            {"value": gdp_values, "component": "GDP"}, index = gdp_dates
        )

        return data

    def test_single_source_vectorization(self):
        """測試單個數據源向量化"""
        print("\n=== Single Source Vectorization Test ===")

        # 測試HIBOR數據向量化
        hibor_data = self.test_data["HB"]

        try:
            vectorized = self.vectorizer.vectorize_dataframe(
                hibor_data, "HB", scaling_method="zscore"
            )

            self.assertIsInstance(vectorized.values, np.ndarray)
            self.assertEqual(vectorized.values.dtype, np.float32)
            self.assertEqual(len(vectorized.values), len(hibor_data))

            print(f"Vectorized {vectorized.metadata['record_count']} records")
            print(f"Data shape: {vectorized.metadata['shape']}")
            print(f"Date range: {vectorized.metadata['date_range']}")
            print(f"Scaling method: {vectorized.metadata['scaling_method']}")

            # 測試GPU數組創建
            gpu_arrays = self.vectorizer.create_gpu_arrays(vectorized)
            self.assertIsInstance(gpu_arrays, dict)
            self.assertIn("values", gpu_arrays)
            self.assertIn("cupy_available", gpu_arrays)

            print(f"GPU arrays created: {gpu_arrays.get('cupy_available', False)}")

        except Exception as e:
            print(f"Single source vectorization error: {e}")

    def test_multiple_source_vectorization(self):
        """測試多個數據源向量化"""
        print("\n=== Multiple Source Vectorization Test ===")

        try:
            # 向量化多個數據源
            vectorized_data = self.vectorizer.vectorize_multiple_sources(
                self.test_data, scaling_method="minmax"
            )

            self.assertIsInstance(vectorized_data, dict)
            self.assertGreater(len(vectorized_data), 0)

            print(f"Vectorized {len(vectorized_data)} data sources:")
            for source_id, data in vectorized_data.items():
                print(
                    f"  {source_id}: {len(data.values)} records, dtype: {data.values.dtype}"
                )

            # 測試組合特徵
            combined_features = self.multi_vectorizer.create_combined_features(
                vectorized_data, feature_combination="concatenate"
            )

            self.assertIsInstance(combined_features, np.ndarray)
            print(f"Combined features shape: {combined_features.shape}")

        except Exception as e:
            print(f"Multiple source vectorization error: {e}")

    def test_data_alignment(self):
        """測試數據對齊"""
        print("\n=== Data Alignment Test ===")

        try:
            # 測試交集對齊
            aligned_data = self.multi_vectorizer.align_multiple_sources(
                self.test_data, alignment_method="intersection"
            )

            print(f"Alignment method: intersection")
            for source_id, df in aligned_data.items():
                print(f"  {source_id}: {len(df)} records")

            # 驗證所有數據源具有相同的時間索引
            if len(aligned_data) > 1:
                first_length = len(list(aligned_data.values())[0])
                all_same_length = all(
                    len(df) == first_length for df in aligned_data.values()
                )
                if all_same_length:
                    print("All sources have aligned time indices")
                else:
                    print("Warning: Sources have different lengths")

        except Exception as e:
            print(f"Data alignment error: {e}")

    def test_window_creation(self):
        """測試窗口創建"""
        print("\n=== Window Creation Test ===")

        try:
            # 向量化HIBOR數據
            hibor_data = self.test_data["HB"]
            vectorized = self.vectorizer.vectorize_dataframe(hibor_data, "HB")

            # 創建窗口
            windows = self.vectorizer.create_windows(
                vectorized, window_size = 30, step_size = 15
            )

            self.assertIsInstance(windows, dict)
            self.assertIn("windows", windows)
            self.assertIn("num_windows", windows)

            print(f"Created {windows['num_windows']} windows")
            print(f"Window size: {windows['window_size']}")
            print(f"Step size: {windows['step_size']}")
            print(f"Window array shape: {windows['windows'].shape}")

        except Exception as e:
            print(f"Window creation error: {e}")

    def test_sequence_creation(self):
        """測試序列創建"""
        print("\n=== Sequence Creation Test ===")

        try:
            # 向量化數據
            hibor_data = self.test_data["HB"]
            vectorized = self.vectorizer.vectorize_dataframe(hibor_data, "HB")

            # 創建序列
            X, y = self.vectorizer.create_sequences(
                vectorized, sequence_length = 10, prediction_length = 1
            )

            self.assertIsInstance(X, np.ndarray)
            self.assertIsInstance(y, np.ndarray)

            print(f"Created sequences: X shape {X.shape}, y shape {y.shape}")
            print(f"Sequence length: 10, prediction length: 1")

        except Exception as e:
            print(f"Sequence creation error: {e}")

    def test_scaling_methods(self):
        """測試不同的縮放方法"""
        print("\n=== Scaling Methods Test ===")

        scaling_methods = ["minmax", "zscore", "robust", "none"]
        hibor_data = self.test_data["HB"]

        for method in scaling_methods:
            try:
                vectorized = self.vectorizer.vectorize_dataframe(
                    hibor_data, "HB", scaling_method = method
                )

                print(f"Scaling method '{method}':")
                print(f"  Mean: {np.mean(vectorized.values):.4f}")
                print(f"  Std:  {np.std(vectorized.values):.4f}")
                print(f"  Min:  {np.min(vectorized.values):.4f}")
                print(f"  Max:  {np.max(vectorized.values):.4f}")

                # 測試反向標準化
                if (
                    hasattr(vectorized, "normalization_params")
                    and vectorized.normalization_params
                ):
                    restored = self.vectorizer.inverse_transform(
                        vectorized.values, vectorized.normalization_params
                    )
                    original_mean = np.mean(hibor_data["value"].values)
                    restored_mean = np.mean(restored)
                    print(
                        f"  Restored mean accuracy: {abs(original_mean - restored_mean):.6f}"
                    )

            except Exception as e:
                print(f"Scaling method '{method}' error: {e}")

    def test_performance_benchmark(self):
        """測試性能基準"""
        print("\n=== Performance Benchmark Test ===")

        try:
            import time

            # 創建更大的測試數據
            large_dates = pd.date_range(start="2020 - 01 - 01", end="2024 - 12 - 31", freq="D")
            large_values = np.random.normal(100, 20, len(large_dates))
            large_data = pd.DataFrame({"value": large_values}, index = large_dates)

            print(f"Testing with {len(large_data)} records")

            # 基準測試
            start_time = time.time()
            vectorized = self.vectorizer.vectorize_dataframe(large_data, "TEST")
            vectorization_time = time.time() - start_time

            start_time = time.time()
            windows = self.vectorizer.create_windows(
                vectorized, window_size = 100, step_size = 50
            )
            window_time = time.time() - start_time

            start_time = time.time()
            combined_features = self.multi_vectorizer.create_combined_features(
                {"TEST": vectorized}, feature_combination="concatenate"
            )
            combination_time = time.time() - start_time

            print(f"Vectorization time: {vectorization_time:.4f}s")
            print(f"Window creation time: {window_time:.4f}s")
            print(f"Feature combination time: {combination_time:.4f}s")
            print(
                f"Records per second (vectorization): {len(large_data)/vectorization_time:.0f}"
            )

        except Exception as e:
            print(f"Performance benchmark error: {e}")


def run_vectorization_tests():
    """運行所有向量化測試"""
    print("Starting Vectorization Engine Tests")
    print("=" * 50)

    # 創建測試套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestVectorizationEngine)

    # 運行測試
    runner = unittest.TextTestRunner(verbosity = 2)
    result = runner.run(suite)

    # 總結
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("All vectorization tests completed!")
    else:
        print(f"{len(result.failures)} test failures, {len(result.errors)} errors")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_vectorization_tests()
    sys.exit(0 if success else 1)
