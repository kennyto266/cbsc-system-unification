#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU-VectorBT集成演示
展示非價格數據GPU加速與VectorBT回測系統的完整集成
"""

import sys
import os
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# 添加src路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_demo_stock_data(symbol="0700.HK"):
    """創建演示股票數據"""
    print(f"Creating demo stock data for {symbol}")

    # 生成2年的日線數據
    dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')

    # 模擬真實股價走勢
    np.random.seed(42)
    base_price = 400.0  # 騰訊基準價格

    # 生成趨勢和隨機波動
    trend = np.linspace(0, 0.3, len(dates))  # 30%上漲趨勢
    noise = np.random.normal(0, 0.02, len(dates))  # 2%日波動

    # 價格計算
    price_changes = trend + noise
    prices = base_price * np.cumprod(1 + price_changes)

    # 創建OHLCV數據
    data = pd.DataFrame(index=dates)
    data['close'] = prices
    data['open'] = data['close'].shift(1).fillna(base_price)

    # 生成高開低收（基於真實市場模式）
    daily_volatility = 0.025
    data['high'] = data['close'] * (1 + np.abs(np.random.normal(0, daily_volatility, len(dates))))
    data['low'] = data['close'] * (1 - np.abs(np.random.normal(0, daily_volatility, len(dates))))

    # 確保high >= max(open, close), low <= min(open, close)
    data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
    data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))

    # 模擬成交量
    base_volume = 15000000  # 1500萬股基準
    volume_changes = np.random.lognormal(0, 0.3, len(dates))
    data['volume'] = base_volume * volume_changes

    print(f"Generated {len(data)} days of data for {symbol}")
    print(f"Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
    print(f"Average daily volume: {data['volume'].mean():,.0f}")

    return data

def demo_gpu_optimization_only():
    """僅演示GPU優化功能（不依賴VectorBT）"""
    print("\n" + "="*60)
    print("GPU參數優化演示")
    print("="*60)

    try:
        from gpu.parameter_optimizer import get_gpu_parameter_optimizer
        from vectorization.time_series import get_time_series_vectorizer

        print("✅ GPU優化引擎加載成功")

        # 創建測試數據
        stock_data = create_demo_stock_data()
        close_prices = stock_data['close']

        # 向量化數據
        vectorizer = get_time_series_vectorizer()
        vectorized_data = vectorizer.vectorize_dataframe(
            pd.DataFrame({'value': close_prices}), 'STOCK'
        )

        print(f"📊 向量化數據: {len(vectorized_data.values)} 個數據點")

        # GPU優化器
        optimizer = get_gpu_parameter_optimizer()

        # RSI參數優化
        print("\n🚀 開始RSI參數優化...")
        start_time = time.time()

        opt_config = optimizer.create_optimization_config(
            strategy_type='rsi',
            param_ranges={'period': (10, 30)},
            use_gpu=True
        )

        report = optimizer.optimize_single_source(vectorized_data, opt_config)
        optimization_time = time.time() - start_time

        print(f"✅ RSI優化完成，耗時: {optimization_time:.3f}秒")
        print(f"📈 最佳參數: {report.best_strategy.parameters}")
        print(f"📈 最佳Sharpe比率: {report.best_strategy.metrics['sharpe_ratio']:.4f}")
        print(f"📈 總回報: {report.best_strategy.metrics['total_return']:.2%}")
        print(f"📈 勝率: {report.best_strategy.metrics['win_rate']:.2%}")
        print(f"📈 測試策略數: {len(report.results)}")
        print(f"📈 GPU利用率: {report.gpu_utilized}")

        # 顯示前5個最佳策略
        print("\n🏆 Top 5 RSI策略:")
        sorted_results = sorted(report.results, key=lambda x: x.metrics['sharpe_ratio'], reverse=True)
        for i, result in enumerate(sorted_results[:5]):
            print(f"  {i+1}. RSI({result.parameters['period']}): "
                  f"Sharpe={result.metrics['sharpe_ratio']:.4f}, "
                  f"Return={result.metrics['total_return']:.2%}")

        # MACD參數優化
        print("\n🚀 開始MACD參數優化...")
        start_time = time.time()

        macd_config = optimizer.create_optimization_config(
            strategy_type='macd',
            param_ranges={
                'fast_period': (8, 15),
                'slow_period': (20, 30),
                'signal_period': (8, 12)
            },
            use_gpu=True
        )

        macd_report = optimizer.optimize_single_source(vectorized_data, macd_config)
        macd_time = time.time() - start_time

        print(f"✅ MACD優化完成，耗時: {macd_time:.3f}秒")
        print(f"📈 最佳參數: {macd_report.best_strategy.parameters}")
        print(f"📈 最佳Sharpe比率: {macd_report.best_strategy.metrics['sharpe_ratio']:.4f}")

        # 綜合優化（多策略）
        print("\n🚀 開始綜合多策略優化...")
        start_time = time.time()

        comprehensive_results = optimizer.run_comprehensive_optimization(
            {'STOCK': vectorized_data},
            strategy_types=['rsi', 'macd', 'bollinger']
        )

        comprehensive_time = time.time() - start_time

        print(f"✅ 綜合優化完成，耗時: {comprehensive_time:.3f}秒")
        print("\n🏆 綜合優化結果:")
        for strategy_type, report in comprehensive_results.items():
            print(f"  {strategy_type.upper()}: Sharpe={report.best_strategy.metrics['sharpe_ratio']:.4f}")

        # 性能監控
        print("\n📊 性能監控信息:")
        try:
            from gpu.performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
            memory_info = monitor.get_memory_manager().get_memory_usage()

            print(f"  GPU內存使用: {memory_info['gpu_memory']['used_mb']:.2f} MB")
            print(f"  CPU內存使用: {memory_info['cpu_memory']['used_mb']:.2f} MB")
            print(f"  管理的分配: {memory_info['managed_allocations']['count']} 個")

        except Exception as e:
            print(f"  性能監控信息獲取失敗: {e}")

        return True

    except Exception as e:
        print(f"❌ GPU優化演示失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_data_source_integration():
    """演示數據源集成"""
    print("\n" + "="*60)
    print("數據源集成演示")
    print("="*60)

    try:
        from adapters.adapter_manager import get_nonprice_adapter_manager

        print("✅ 數據適配器管理器加載成功")

        # 獲取適配器管理器
        adapter_manager = get_nonprice_adapter_manager()

        # 獲取所有可用數據源
        sources = adapter_manager.get_available_sources()
        print(f"📡 可用數據源: {len(sources)} 個")

        # 獲取最新數據
        print("\n📊 獲取最新數據...")
        latest_data = adapter_manager.get_latest_data(days=7)

        for data_type, data in latest_data.items():
            if isinstance(data, dict) and len(data) > 0:
                print(f"  {data_type}: {len(data)} 條記錄")
            elif isinstance(data, (int, float)):
                print(f"  {data_type}: {data}")
            else:
                print(f"  {data_type}: {type(data).__name__}")

        # 驗證數據源健康狀況
        print("\n🔍 數據源健康檢查...")
        validation_results = adapter_manager.validate_all_sources()

        healthy_count = sum(1 for is_healthy in validation_results.values() if is_healthy)
        print(f"  健康數據源: {healthy_count}/{len(validation_results)}")

        # 獲取數據質量報告
        print("\n📋 數據質量報告...")
        quality_report = adapter_manager.get_data_quality_report()

        print(f"  報告生成時間: {quality_report.get('generated_at', 'N/A')}")
        print(f"  整體完整性: {quality_report.get('overall_quality', {}).get('completeness', 0):.2%}")
        print(f"  分析的數據源: {len(quality_report.get('sources', {}))}")

        return True

    except Exception as e:
        print(f"❌ 數據源集成演示失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_vectorization_engine():
    """演示向量化引擎"""
    print("\n" + "="*60)
    print("向量化引擎演示")
    print("="*60)

    try:
        from vectorization.time_series import get_time_series_vectorizer, get_multi_source_vectorizer

        print("✅ 向量化引擎加載成功")

        # 創建多種類型的測試數據
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')

        # HIBOR類型數據（利率）
        hibor_values = 3.5 + 0.5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365) + np.random.normal(0, 0.1, len(dates))
        hibor_data = pd.DataFrame({
            'value': hibor_values,
            'tenor': 'ON'
        }, index=dates)

        # 貨幣基礎數據
        monetary_values = 1800 + 200 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365) + np.random.normal(0, 50, len(dates))
        monetary_data = pd.DataFrame({
            'value': monetary_values,
            'component': 'MB'
        }, index=dates)

        # GDP類型數據（季度）
        gdp_dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='Q')
        gdp_values = 700 + np.arange(len(gdp_dates)) * 10 + np.random.normal(0, 5, len(gdp_dates))
        gdp_data = pd.DataFrame({
            'value': gdp_values,
            'component': 'GDP'
        }, index=gdp_dates)

        data_dict = {
            'HIBOR': hibor_data,
            'MONETARY': monetary_data,
            'GDP': gdp_data
        }

        print(f"📊 創建了 {len(data_dict)} 種數據源:")
        for source_id, df in data_dict.items():
            print(f"  {source_id}: {len(df)} 條記錄")

        # 單源向量化
        print("\n🚀 單源向量化測試...")
        vectorizer = get_time_series_vectorizer()

        for source_id, df in data_dict.items():
            vectorized = vectorizer.vectorize_dataframe(df, source_id, scaling_method='zscore')
            print(f"  {source_id}:")
            print(f"    數據點數: {vectorized.metadata['record_count']}")
            print(f"    數據形狀: {vectorized.metadata['shape']}")
            print(f"    標準化方法: {vectorized.metadata['scaling_method']}")
            print(f"    平均值: {np.mean(vectorized.values):.4f}")
            print(f"    標準差: {np.std(vectorized.values):.4f}")

        # 多源向量化
        print("\n🚀 多源向量化測試...")
        multi_vectorizer = get_multi_source_vectorizer()

        # 對齊數據源
        aligned_data = multi_vectorizer.align_multiple_sources(data_dict, 'intersection')
        print(f"對齊後數據源: {len(aligned_data)} 個")

        for source_id, df in aligned_data.items():
            print(f"  {source_id}: {len(df)} 條記錄")

        # 批量向量化
        vectorized_data = vectorizer.vectorize_multiple_sources(aligned_data, scaling_method='minmax')

        # 創建組合特徵
        combined_features = multi_vectorizer.create_combined_features(
            vectorized_data, feature_combination='concatenate'
        )

        print(f"\n🔗 特徵組合完成:")
        print(f"  組合特徵形狀: {combined_features.shape}")
        print(f"  特徵維度: {combined_features.shape[1]}")

        # 創建窗口
        sample_vectorized = list(vectorized_data.values())[0]
        windows = vectorizer.create_windows(sample_vectorized, window_size=30, step_size=15)

        print(f"\n🪟 窗口創建完成:")
        print(f"  窗口數量: {windows['num_windows']}")
        print(f"  窗口大小: {windows['window_size']}")
        print(f"  步長: {windows['step_size']}")

        # 性能基準測試
        print(f"\n⚡ 性能基準測試...")

        # 大數據測試
        large_dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
        large_values = np.random.normal(100, 20, len(large_dates))
        large_data = pd.DataFrame({'value': large_values}, index=large_dates)

        start_time = time.time()
        large_vectorized = vectorizer.vectorize_dataframe(large_data, 'LARGE')
        vectorization_time = time.time() - start_time

        print(f"  大數據集 ({len(large_data)} 條記錄) 向量化時間: {vectorization_time:.4f}秒")
        print(f"  處理速度: {len(large_data)/vectorization_time:.0f} records/second")

        return True

    except Exception as e:
        print(f"❌ 向量化引擎演示失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主演示函數"""
    print("🚀 GPU加速非價格數據VectorBT集成演示")
    print("📅 時間:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    results = []

    # 1. 數據源集成演示
    results.append(("數據源集成", demo_data_source_integration()))

    # 2. 向量化引擎演示
    results.append(("向量化引擎", demo_vectorization_engine()))

    # 3. GPU優化演示
    results.append(("GPU參數優化", demo_gpu_optimization_only()))

    # 總結報告
    print("\n" + "="*60)
    print("演示結果總結")
    print("="*60)

    for demo_name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{demo_name}: {status}")

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    print(f"\n🎯 總體成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        print("🎉 所有演示都成功完成！")
    else:
        print("⚠️  部分演示失敗，請檢查錯誤信息")

    # 系統信息
    print(f"\n💻 系統信息:")
    print(f"  Python版本: {sys.version}")
    print(f"  當前工作目錄: {os.getcwd()}")

    try:
        import cupy as cp
        print(f"  CuPy版本: {cp.__version__}")
        print(f"  CUDA可用: {cp.cuda.is_available()}")
    except:
        print("  CuPy: 未安裝")

    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)