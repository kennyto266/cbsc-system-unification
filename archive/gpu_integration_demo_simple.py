#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU集成簡化演示
展示非價格數據GPU加速系統的完整功能
"""

import sys
import os
import pandas as pd
import numpy as np
import time
from datetime import datetime

# 添加src路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_demo_data():
    """創建演示數據"""
    print("Creating demo stock data...")

    # 生成2年的日線數據
    dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')

    # 模擬真實股價走勢
    np.random.seed(42)
    base_price = 400.0
    trend = np.linspace(0, 0.3, len(dates))
    noise = np.random.normal(0, 0.02, len(dates))
    prices = base_price * np.cumprod(1 + trend + noise)

    # 創建數據
    data = pd.DataFrame(index=dates)
    data['close'] = prices
    data['open'] = data['close'].shift(1).fillna(base_price)

    daily_volatility = 0.025
    data['high'] = data['close'] * (1 + np.abs(np.random.normal(0, daily_volatility, len(dates))))
    data['low'] = data['close'] * (1 - np.abs(np.random.normal(0, daily_volatility, len(dates))))

    data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
    data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))

    base_volume = 15000000
    volume_changes = np.random.lognormal(0, 0.3, len(dates))
    data['volume'] = base_volume * volume_changes

    print(f"Generated {len(data)} days of data")
    print(f"Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")

    return data

def demo_gpu_optimization():
    """演示GPU優化功能"""
    print("\n" + "="*60)
    print("GPU Parameter Optimization Demo")
    print("="*60)

    try:
        from gpu.parameter_optimizer import get_gpu_parameter_optimizer
        from vectorization.time_series import get_time_series_vectorizer

        print("GPU optimizer loaded successfully")

        # 創建測試數據
        stock_data = create_demo_data()
        close_prices = stock_data['close']

        # 向量化數據
        vectorizer = get_time_series_vectorizer()
        vectorized_data = vectorizer.vectorize_dataframe(
            pd.DataFrame({'value': close_prices}), 'STOCK'
        )

        print(f"Vectorized data: {len(vectorized_data.values)} points")

        # GPU優化器
        optimizer = get_gpu_parameter_optimizer()

        # RSI參數優化
        print("\nStarting RSI parameter optimization...")
        start_time = time.time()

        opt_config = optimizer.create_optimization_config(
            strategy_type='rsi',
            param_ranges={'period': (10, 30)},
            use_gpu=True
        )

        report = optimizer.optimize_single_source(vectorized_data, opt_config)
        optimization_time = time.time() - start_time

        print(f"RSI optimization completed in {optimization_time:.3f}s")
        print(f"Best parameters: {report.best_strategy.parameters}")
        print(f"Best Sharpe ratio: {report.best_strategy.metrics['sharpe_ratio']:.4f}")
        print(f"Total return: {report.best_strategy.metrics['total_return']:.2%}")
        print(f"Win rate: {report.best_strategy.metrics['win_rate']:.2%}")
        print(f"Strategies tested: {len(report.results)}")
        print(f"GPU utilized: {report.gpu_utilized}")

        # 顯示前5個最佳策略
        print("\nTop 5 RSI strategies:")
        sorted_results = sorted(report.results, key=lambda x: x.metrics['sharpe_ratio'], reverse=True)
        for i, result in enumerate(sorted_results[:5]):
            print(f"  {i+1}. RSI({result.parameters['period']}): "
                  f"Sharpe={result.metrics['sharpe_ratio']:.4f}, "
                  f"Return={result.metrics['total_return']:.2%}")

        return True

    except Exception as e:
        print(f"GPU optimization demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_data_integration():
    """演示數據源集成"""
    print("\n" + "="*60)
    print("Data Source Integration Demo")
    print("="*60)

    try:
        from adapters.adapter_manager import get_nonprice_adapter_manager

        print("Data adapter manager loaded successfully")

        # 獲取適配器管理器
        adapter_manager = get_nonprice_adapter_manager()

        # 獲取所有可用數據源
        sources = adapter_manager.get_available_sources()
        print(f"Available data sources: {len(sources)}")

        # 獲取最新數據
        print("\nGetting latest data...")
        latest_data = adapter_manager.get_latest_data(days=7)

        for data_type, data in latest_data.items():
            if isinstance(data, dict) and len(data) > 0:
                print(f"  {data_type}: {len(data)} records")
            elif isinstance(data, (int, float)):
                print(f"  {data_type}: {data}")

        # 驗證數據源健康狀況
        print("\nChecking data source health...")
        validation_results = adapter_manager.validate_all_sources()

        healthy_count = sum(1 for is_healthy in validation_results.values() if is_healthy)
        print(f"Healthy data sources: {healthy_count}/{len(validation_results)}")

        return True

    except Exception as e:
        print(f"Data integration demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_vectorization():
    """演示向量化引擎"""
    print("\n" + "="*60)
    print("Vectorization Engine Demo")
    print("="*60)

    try:
        from vectorization.time_series import get_time_series_vectorizer

        print("Vectorization engine loaded successfully")

        # 創建測試數據
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')

        # 不同類型數據
        hibor_values = 3.5 + 0.5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365) + np.random.normal(0, 0.1, len(dates))
        hibor_data = pd.DataFrame({
            'value': hibor_values,
            'tenor': 'ON'
        }, index=dates)

        monetary_values = 1800 + 200 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365) + np.random.normal(0, 50, len(dates))
        monetary_data = pd.DataFrame({
            'value': monetary_values,
            'component': 'MB'
        }, index=dates)

        data_dict = {
            'HIBOR': hibor_data,
            'MONETARY': monetary_data
        }

        print(f"Created {len(data_dict)} data sources:")
        for source_id, df in data_dict.items():
            print(f"  {source_id}: {len(df)} records")

        # 向量化測試
        vectorizer = get_time_series_vectorizer()

        for source_id, df in data_dict.items():
            vectorized = vectorizer.vectorize_dataframe(df, source_id, scaling_method='zscore')
            print(f"\n{source_id} vectorization:")
            print(f"  Data points: {vectorized.metadata['record_count']}")
            print(f"  Data shape: {vectorized.metadata['shape']}")
            print(f"  Scaling method: {vectorized.metadata['scaling_method']}")
            print(f"  Mean: {np.mean(vectorized.values):.4f}")
            print(f"  Std: {np.std(vectorized.values):.4f}")

        # 性能基準測試
        print(f"\nPerformance benchmark test...")

        # 大數據測試
        large_dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
        large_values = np.random.normal(100, 20, len(large_dates))
        large_data = pd.DataFrame({'value': large_values}, index=large_dates)

        start_time = time.time()
        large_vectorized = vectorizer.vectorize_dataframe(large_data, 'LARGE')
        vectorization_time = time.time() - start_time

        print(f"Large dataset ({len(large_data)} records) vectorization: {vectorization_time:.4f}s")
        print(f"Processing speed: {len(large_data)/vectorization_time:.0f} records/second")

        return True

    except Exception as e:
        print(f"Vectorization demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主演示函數"""
    print("GPU-Accelerated Non-Price Data Integration Demo")
    print("Time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    results = []

    # 1. 數據源集成演示
    results.append(("Data Source Integration", demo_data_integration()))

    # 2. 向量化引擎演示
    results.append(("Vectorization Engine", demo_vectorization()))

    # 3. GPU優化演示
    results.append(("GPU Parameter Optimization", demo_gpu_optimization()))

    # 總結報告
    print("\n" + "="*60)
    print("Demo Results Summary")
    print("="*60)

    for demo_name, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"{demo_name}: {status}")

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    print(f"\nOverall success rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        print("All demos completed successfully!")
    else:
        print("Some demos failed, please check error messages")

    # 系統信息
    print(f"\nSystem Information:")
    print(f"  Python version: {sys.version}")
    print(f"  Current directory: {os.getcwd()}")

    try:
        import cupy as cp
        print(f"  CuPy version: {cp.__version__}")
        print(f"  CUDA available: {cp.cuda.is_available()}")
    except:
        print("  CuPy: Not installed")

    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)