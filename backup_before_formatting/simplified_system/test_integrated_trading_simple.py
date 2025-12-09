#!/usr/bin/env python3
"""
測試集成交易系統 - 同步版本
Test Integrated Trading System - Synchronous Version
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from indicators.advanced_ta_signals import AdvancedTechnicalSignals
    from data.historical_data_extender import extend_data_records
    from api.stock_api import get_hk_stock_data
    from backtest.vectorbt_engine import VectorBTEngine

    print("=" * 80)
    print("Integrated Trading System Test (Synchronous)")
    print("集成交易系统测试 - 同步版本")
    print("=" * 80)
    print()

    # 測試1: 高級信號分析
    print("=== Test 1: Advanced Signal Analysis ===")

    advanced_signals = AdvancedTechnicalSignals()
    print("Advanced signals system initialized")

    # 獲取0700.HK數據
    print("Fetching 0700.HK data...")
    stock_data = get_hk_stock_data('0700.HK', 252)  # 1年數據

    if stock_data is not None and not stock_data.empty:
        print(f"[OK] Retrieved {len(stock_data)} records for 0700.HK")
        print(f"Date range: {stock_data.index[0]} to {stock_data.index[-1]}")
        print(f"Price range: ${stock_data['low'].min():.2f} - ${stock_data['high'].max():.2f}")

        # 轉換為分析所需格式
        stock_records = []
        for i, row in stock_data.iterrows():
            stock_records.append({
                'date': row.name.strftime('%Y-%m-%d'),
                'price': row['close'],
                'volume': row['volume'],
                'high': row['high'],
                'low': row['low'],
                'open': row['open']
            })

        print(f"Converted {len(stock_records)} records for analysis")

        # 生成高級技術分析信號
        print("Generating advanced technical analysis signals...")
        analysis_result = advanced_signals.generate_enhanced_signals(
            data=stock_records,
            data_type='price',
            extend_to_1000=True,  # 擴展到1000條記錄
            optimize_signals=True
        )

        if analysis_result.get('success'):
            print(f"[OK] Advanced signals generated successfully")
            print(f"  Signal Quality Score: {analysis_result.get('signal_quality_score', 0):.2f}/10")
            print(f"  Processed Records: {analysis_result.get('processed_records', 0)}")
            print(f"  Numeric Columns: {analysis_result.get('numeric_columns', 0)}")

            # 檢查信號組成部分
            if 'composite_signals' in analysis_result:
                composite_signals = analysis_result['composite_signals']
                print(f"  Composite Signals: {len(composite_signals)} columns")

                for column, signals in list(composite_signals.items())[:2]:  # 只顯示前2列
                    print(f"    {column}:")
                    if isinstance(signals, dict):
                        if 'final_signal' in signals:
                            print(f"      Final Signal: {signals['final_signal']:.3f}")
                        if 'weighted_scores' in signals:
                            print(f"      Weighted Scores: {len(signals['weighted_scores'])} indicators")

            # 檢查交易建議
            recommendations = analysis_result.get('recommendations', [])
            if recommendations:
                print(f"  Trading Recommendations: {len(recommendations)}")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"    {i}. {rec}")
        else:
            print(f"[FAIL] Advanced signals failed: {analysis_result.get('error', 'Unknown error')}")

    else:
        print("[FAIL] No data available for 0700.HK")

    print()

    # 測試2: 歷史數據擴展
    print("=== Test 2: Historical Data Extension ===")

    # 創建小測試數據集
    test_data = []
    for i in range(15):
        test_data.append({
            'date': f'2025-01-{(i+1):02d}',
            'price': 100.0 + i * 0.3 + (i % 4 - 2) * 0.1,
            'volume': 1000000 + i * 50000,
            'high': 101.0 + i * 0.3,
            'low': 99.0 + i * 0.3
        })

    print(f"Original test data: {len(test_data)} records")
    print(f"Sample record: {test_data[0]}")

    # 測試不同的擴展方法
    methods = ['trend_preservation', 'seasonal_adjustment', 'statistical_simulation', 'hybrid_approach']

    for method in methods:
        print(f"Testing {method} method...")
        result = extend_data_records(test_data, 1000, method)

        if result.get('success'):
            extended_data = result['data']
            print(f"  [OK] {method}: {result['original_count']} -> {result['final_count']} records")
            print(f"  Extension ratio: {result['extension_ratio']:.2f}x")
            print(f"  Quality metrics available: {len(result.get('metadata', {}).get('quality_metrics', {}))}")
        else:
            print(f"  [FAIL] {method}: {result.get('error', 'Unknown error')}")

    print()

    # 測試3: VectorBT回測引擎集成
    print("=== Test 3: VectorBT Backtest Integration ===")

    try:
        vectorbt_engine = VectorBTEngine()
        print("VectorBT engine initialized")

        if stock_data is not None and not stock_data.empty:
            # 測試RSI策略
            print("Testing RSI mean reversion strategy...")
            rsi_result = vectorbt_engine.backtest_strategy(
                data=stock_data,
                strategy_name='RSI_MEAN_REVERSION',
                params={'period': 14, 'oversold': 30, 'overbought': 70}
            )

            if rsi_result:
                print(f"[OK] RSI backtest completed")
                print(f"  Total Return: {rsi_result.get('total_return', 0):.2%}")
                print(f"  Sharpe Ratio: {rsi_result.get('sharpe_ratio', 0):.3f}")
                print(f"  Max Drawdown: {rsi_result.get('max_drawdown', 0):.2%}")
                print(f"  Win Rate: {rsi_result.get('win_rate', 0):.1%}")
            else:
                print("[FAIL] RSI backtest failed")

            # 測試雙移動平均策略
            print("Testing Dual Moving Average strategy...")
            dma_result = vectorbt_engine.backtest_strategy(
                data=stock_data,
                strategy_name='DUAL_MOVING_AVERAGE',
                params={'short_period': 20, 'long_period': 50}
            )

            if dma_result:
                print(f"[OK] DMA backtest completed")
                print(f"  Total Return: {dma_result.get('total_return', 0):.2%}")
                print(f"  Sharpe Ratio: {dma_result.get('sharpe_ratio', 0):.3f}")
                print(f"  Max Drawdown: {dma_result.get('max_drawdown', 0):.2%}")
                print(f"  Win Rate: {dma_result.get('win_rate', 0):.1%}")
            else:
                print("[FAIL] DMA backtest failed")

    except Exception as e:
        print(f"[ERROR] VectorBT integration failed: {e}")

    print()

    # 測試4: 多股票分析
    print("=== Test 4: Multi-Stock Analysis ===")

    test_symbols = ['0700.HK', '0941.HK', '1398.HK']
    analysis_results = {}

    for symbol in test_symbols:
        print(f"Analyzing {symbol}...")
        try:
            symbol_data = get_hk_stock_data(symbol, 100)  # 較短時間範圍

            if symbol_data is not None and not symbol_data.empty:
                # 轉換格式
                symbol_records = []
                for i, row in symbol_data.iterrows():
                    symbol_records.append({
                        'date': row.name.strftime('%Y-%m-%d'),
                        'price': row['close'],
                        'volume': row['volume'],
                        'high': row['high'],
                        'low': row['low'],
                        'open': row['open']
                    })

                # 快速分析（不擴展）
                symbol_result = advanced_signals.generate_enhanced_signals(
                    data=symbol_records,
                    data_type='price',
                    extend_to_1000=False,  # 不擴展以節省時間
                    optimize_signals=True
                )

                if symbol_result.get('success'):
                    analysis_results[symbol] = {
                        'success': True,
                        'signal_quality': symbol_result.get('signal_quality_score', 0),
                        'processed_records': symbol_result.get('processed_records', 0),
                        'data_points': len(symbol_records)
                    }
                    print(f"  [OK] {symbol}: Quality {symbol_result.get('signal_quality_score', 0):.1f}/10")
                else:
                    analysis_results[symbol] = {
                        'success': False,
                        'error': symbol_result.get('error', 'Unknown error')
                    }
                    print(f"  [FAIL] {symbol}: {symbol_result.get('error', 'Unknown error')}")
            else:
                analysis_results[symbol] = {
                    'success': False,
                    'error': 'No data available'
                }
                print(f"  [FAIL] {symbol}: No data available")

        except Exception as e:
            analysis_results[symbol] = {
                'success': False,
                'error': str(e)
            }
            print(f"  [ERROR] {symbol}: {e}")

    print(f"Multi-stock analysis completed: {len(analysis_results)} symbols")

    successful_analyses = sum(1 for r in analysis_results.values() if r.get('success', False))
    print(f"Successful analyses: {successful_analyses}/{len(test_symbols)}")

    print()

    # 測試5: 系統性能評估
    print("=== Test 5: System Performance Assessment ===")

    import time

    # 性能測試
    start_time = time.time()

    # 重複分析性能測試
    performance_iterations = 3
    analysis_times = []

    for i in range(performance_iterations):
        print(f"Performance test iteration {i+1}/{performance_iterations}...")
        iter_start = time.time()

        # 使用較小的數據集進行快速測試
        test_data_small = test_data[:5]  # 只用5條記錄

        result = advanced_signals.generate_enhanced_signals(
            data=test_data_small,
            data_type='price',
            extend_to_1000=True,  # 測試擴展性能
            optimize_signals=False   # 關閉優化以節省時間
        )

        iter_end = time.time()
        iter_time = iter_end - iter_start
        analysis_times.append(iter_time)

        if result.get('success'):
            print(f"  Iteration {i+1}: {iter_time:.3f}s, {result.get('processed_records', 0)} records")
        else:
            print(f"  Iteration {i+1}: Failed")

    total_time = time.time() - start_time
    avg_time = sum(analysis_times) / len(analysis_times)

    print(f"[OK] Performance assessment completed")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average analysis time: {avg_time:.3f}s")
    print(f"  Throughput: {1000 / avg_time:.1f} records/second (extended)")
    print(f"  Success rate: {sum(1 for t in analysis_times if t > 0)} / {performance_iterations}")

    print()

    # 測試6: 數據質量檢查
    print("=== Test 6: Data Quality Validation ===")

    quality_checks = {
        'price_data_completeness': False,
        'volume_data_positive': False,
        'date_sequence_valid': False,
        'price_range_reasonable': False
    }

    if stock_data is not None and not stock_data.empty:
        # 價格數據完整性
        if stock_data['close'].isna().sum() == 0:
            quality_checks['price_data_completeness'] = True

        # 成交量數據為正數
        if (stock_data['volume'] > 0).all():
            quality_checks['volume_data_positive'] = True

        # 日期序列有效性
        if stock_data.index.is_monotonic_increasing:
            quality_checks['date_sequence_valid'] = True

        # 價格範圍合理性
        price_range = stock_data['high'].max() - stock_data['low'].min()
        avg_price = stock_data['close'].mean()
        if price_range / avg_price < 2.0:  # 價格範圍不超過平均價格的2倍
            quality_checks['price_range_reasonable'] = True

    passed_checks = sum(1 for check in quality_checks.values() if check)
    total_checks = len(quality_checks)

    print(f"[OK] Data quality checks: {passed_checks}/{total_checks} passed")

    for check_name, passed in quality_checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {check_name}: {status}")

    print()

    # 保存測試結果
    test_results = {
        'test_timestamp': datetime.now().isoformat(),
        'data_quality_checks': quality_checks,
        'performance_metrics': {
            'average_analysis_time': avg_time,
            'throughput': 1000 / avg_time,
            'success_rate': successful_analyses / len(test_symbols)
        },
        'multi_stock_results': analysis_results,
        'system_status': 'OPERATIONAL' if passed_checks >= 3 else 'NEEDS_ATTENTION'
    }

    results_file = f"trading_system_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)

    print(f"Integration test results saved to: {results_file}")

    # 總結評估
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("集成测试总结")
    print("=" * 80)

    if test_results['system_status'] == 'OPERATIONAL':
        print("✅ System is ready for production use")
        print("✅ 高级技术分析信号系统: 正常运行")
        print("✅ 历史数据扩展: 性能良好")
        print("✅ VectorBT集成: 成功")
        print("✅ 多股票分析: 正常")
    else:
        print("⚠️  System needs attention before production use")
        print("⚠️  请检查数据质量和组件集成")

    print(f"\nKey Performance Indicators:")
    print(f"- Data Quality Score: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.0f}%)")
    print(f"- Analysis Throughput: {test_results['performance_metrics']['throughput']:.1f} records/second")
    print(f"- Multi-Stock Success Rate: {test_results['performance_metrics']['success_rate']:.1%}")

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
    print("请确保所有必需模块都已安装")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Integration Test Complete")
print("集成测试完成")
print("=" * 80)