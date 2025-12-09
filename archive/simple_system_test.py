#!/usr/bin/env python3
"""
HIBOR Technical Prototype - Simple System Testing
簡化系統測試 - 驗證核心功能
"""

import sys
import os
import time
import traceback
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Add simplified_system to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system'))

def test_all_systems():
    """Test all system components"""
    print("=" * 60)
    print("HIBOR TECHNICAL PROTOTYPE - COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)

    test_results = {}
    start_time = time.time()

    # Setup test data
    print("\n1. SETTING UP TEST DATA")
    print("-" * 40)

    try:
        # Create test data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        np.random.seed(42)

        prices = 100 + np.cumsum(np.random.normal(0, 2, 100))
        test_data = pd.DataFrame({
            'open': prices + np.random.normal(0, 1, 100),
            'high': prices + np.abs(np.random.normal(0, 2, 100)),
            'low': prices - np.abs(np.random.normal(0, 2, 100)),
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, 100)
        }, index=dates)

        print(f"[OK] Generated test data: {len(test_data)} records")
        test_results['data_setup'] = {'status': 'PASS', 'records': len(test_data)}

    except Exception as e:
        print(f"[FAIL] Data setup failed: {e}")
        test_results['data_setup'] = {'status': 'FAIL', 'error': str(e)}
        return generate_report(test_results, time.time() - start_time)

    # Test Core Indicators
    print("\n2. TESTING CORE INDICATORS")
    print("-" * 40)

    try:
        from src.indicators.core_indicators import CoreIndicators

        indicators = CoreIndicators()

        # Test basic indicators
        test_series = test_data['close']

        start_time = time.time()
        sma = indicators.calculate_sma(test_series, 20)
        ema = indicators.calculate_ema(test_series, 20)
        rsi = indicators.calculate_rsi(test_series, 14)
        macd = indicators.calculate_macd(test_series, 12, 26, 9)
        bb = indicators.calculate_bollinger_bands(test_series, 20, 2)
        calc_time = time.time() - start_time

        print(f"[OK] Core indicators calculated in {calc_time:.3f}s")
        print(f"    SMA latest: {sma.iloc[-1]:.2f}")
        print(f"    RSI latest: {rsi.iloc[-1]:.2f}")
        print(f"    MACD signal: {macd['macd'].iloc[-1]:.4f}")

        test_results['core_indicators'] = {
            'status': 'PASS',
            'calculation_time': calc_time,
            'indicators_tested': 5,
            'sma_latest': float(sma.iloc[-1]),
            'rsi_latest': float(rsi.iloc[-1])
        }

    except Exception as e:
        print(f"[FAIL] Core indicators test failed: {e}")
        traceback.print_exc()
        test_results['core_indicators'] = {'status': 'FAIL', 'error': str(e)}

    # Test Extended Indicators (Phase 2)
    print("\n3. TESTING EXTENDED INDICATORS (PHASE 2)")
    print("-" * 40)

    try:
        from src.indicators.phase2_extended_indicators import Phase2ExtendedIndicators

        ext_indicators = Phase2ExtendedIndicators()

        start_time = time.time()

        # Test trend indicators
        dema = ext_indicators.calculate_dema(test_series, 20)
        tema = ext_indicators.calculate_tema(test_series, 20)

        # Test momentum indicators
        stoch = ext_indicators.calculate_stochastic(
            test_data['close'], test_data['low'], test_data['high'], 14
        )
        williams_r = ext_indicators.calculate_williams_r(
            test_data['close'], test_data['low'], test_data['high'], 14
        )

        # Test volatility indicators
        atr = ext_indicators.calculate_atr(
            test_data['high'], test_data['low'], test_data['close'], 14
        )

        ext_calc_time = time.time() - start_time

        print(f"[OK] Extended indicators calculated in {ext_calc_time:.3f}s")
        print(f"    DEMA latest: {dema.iloc[-1]:.2f}")
        print(f"    Stochastic latest: {stoch.iloc[-1]:.2f}")
        print(f"    Williams %R latest: {williams_r.iloc[-1]:.2f}")
        print(f"    ATR latest: {atr.iloc[-1]:.2f}")

        test_results['extended_indicators'] = {
            'status': 'PASS',
            'calculation_time': ext_calc_time,
            'indicators_tested': 5,
            'dema_latest': float(dema.iloc[-1]),
            'stoch_latest': float(stoch.iloc[-1])
        }

    except Exception as e:
        print(f"[FAIL] Extended indicators test failed: {e}")
        traceback.print_exc()
        test_results['extended_indicators'] = {'status': 'FAIL', 'error': str(e)}

    # Test VectorBT Engine
    print("\n4. TESTING VECTORBT ENGINE")
    print("-" * 40)

    try:
        from src.backtest.vectorbt_engine import VectorBTEngine

        engine = VectorBTEngine()

        start_time = time.time()

        # Test RSI strategy
        rsi_result = engine.backtest_strategy(
            test_data,
            'RSI_MEAN_REVERSION',
            {'period': 14, 'oversold': 30, 'overbought': 70}
        )

        vbt_time = time.time() - start_time

        if rsi_result:
            print(f"[OK] VectorBT backtest completed in {vbt_time:.3f}s")
            print(f"    Total return: {rsi_result.total_return:.2%}")
            print(f"    Sharpe ratio: {rsi_result.sharpe_ratio:.3f}")
            print(f"    Max drawdown: {rsi_result.max_drawdown:.2%}")

            test_results['vectorbt_engine'] = {
                'status': 'PASS',
                'backtest_time': vbt_time,
                'total_return': float(rsi_result.total_return),
                'sharpe_ratio': float(rsi_result.sharpe_ratio),
                'max_drawdown': float(rsi_result.max_drawdown)
            }
        else:
            print("[WARN] VectorBT: No result returned")
            test_results['vectorbt_engine'] = {
                'status': 'WARN',
                'message': 'No result returned'
            }

    except Exception as e:
        print(f"[FAIL] VectorBT engine test failed: {e}")
        test_results['vectorbt_engine'] = {'status': 'FAIL', 'error': str(e)}

    # Test Massive Optimizer (Phase 3)
    print("\n5. TESTING MASSIVE PARAMETER OPTIMIZER (PHASE 3)")
    print("-" * 40)

    try:
        from src.backtest.massive_optimizer import massive_optimizer

        start_time = time.time()

        # Test small-scale optimization
        result = massive_optimizer.optimize_single_strategy(
            strategy_name="RSI_MEAN_REVERSION",
            symbol="TEST",
            max_combinations=5,  # Very small for testing
            optimization_metric="sharpe_ratio"
        )

        opt_time = time.time() - start_time

        if result:
            print(f"[OK] Parameter optimizer completed in {opt_time:.3f}s")
            print(f"    Combinations tested: {result.get('total_combinations', 'N/A')}")
            print(f"    Best score: {result.get('best_score', 'N/A')}")

            test_results['massive_optimizer'] = {
                'status': 'PASS',
                'optimization_time': opt_time,
                'combinations_tested': result.get('total_combinations', 0),
                'best_score': result.get('best_score', 0)
            }
        else:
            print("[WARN] Parameter optimizer: No result returned")
            test_results['massive_optimizer'] = {
                'status': 'WARN',
                'message': 'No result returned'
            }

    except Exception as e:
        print(f"[FAIL] Massive optimizer test failed: {e}")
        test_results['massive_optimizer'] = {'status': 'FAIL', 'error': str(e)}

    # Test Signal Fusion (Phase 4)
    print("\n6. TESTING COMPOSITE SIGNAL GENERATOR (PHASE 4)")
    print("-" * 40)

    try:
        from src.signal_fusion.composite_signal_generator import CompositeSignalGenerator

        fusion = CompositeSignalGenerator()

        start_time = time.time()

        # Test with limited data
        limited_data = test_data.tail(30)
        signals = fusion.generate_composite_signal(limited_data)

        fusion_time = time.time() - start_time

        if signals:
            print(f"[OK] Composite signal generated in {fusion_time:.3f}s")
            print(f"    Signal type: {signals.get('signal', 'N/A')}")
            print(f"    Signal strength: {signals.get('strength', 'N/A')}/10")
            print(f"    Confidence: {signals.get('confidence', 'N/A'):.1%}")
            print(f"    Quality score: {signals.get('quality_score', 'N/A')}/100")
            print(f"    Risk level: {signals.get('risk_level', 'N/A')}")

            test_results['composite_signal_generator'] = {
                'status': 'PASS',
                'generation_time': fusion_time,
                'signal_type': signals.get('signal', 'N/A'),
                'strength': signals.get('strength', 0),
                'confidence': signals.get('confidence', 0),
                'quality_score': signals.get('quality_score', 0)
            }
        else:
            print("[WARN] Composite signal generator: No result")
            test_results['composite_signal_generator'] = {
                'status': 'WARN',
                'message': 'No result returned'
            }

    except Exception as e:
        print(f"[FAIL] Composite signal generator test failed: {e}")
        traceback.print_exc()
        test_results['composite_signal_generator'] = {'status': 'FAIL', 'error': str(e)}

    # End-to-End Workflow Test
    print("\n7. TESTING END-TO-END WORKFLOW")
    print("-" * 40)

    try:
        print("[INFO] Simulating Complete Trading Workflow...")

        workflow_start = time.time()

        # Step 1: Technical Analysis
        from src.indicators.core_indicators import CoreIndicators
        from src.indicators.phase2_extended_indicators import Phase2ExtendedIndicators

        core_indicators = CoreIndicators()
        ext_indicators = Phase2ExtendedIndicators()

        workflow_data = test_data.tail(50)

        rsi = core_indicators.calculate_rsi(workflow_data['close'], 14)
        macd = core_indicators.calculate_macd(workflow_data['close'], 12, 26, 9)
        dema = ext_indicators.calculate_dema(workflow_data['close'], 20)
        stoch = ext_indicators.calculate_stochastic(
            workflow_data['close'], workflow_data['low'], workflow_data['high'], 14
        )

        # Step 2: Signal Generation
        from src.signal_fusion.composite_signal_generator import CompositeSignalGenerator

        fusion = CompositeSignalGenerator()
        signals = fusion.generate_composite_signal(workflow_data)

        # Step 3: Performance Analysis
        latest_rsi = rsi.iloc[-1]
        latest_macd = macd['macd'].iloc[-1]
        latest_price = workflow_data['close'].iloc[-1]
        price_change = (latest_price / workflow_data['close'].iloc[0] - 1) * 100

        workflow_time = time.time() - workflow_start

        print(f"[OK] Workflow completed in {workflow_time:.3f}s")
        print(f"    Latest price: ${latest_price:.2f}")
        print(f"    Period change: {price_change:+.2f}%")
        print(f"    Latest RSI: {latest_rsi:.2f}")
        print(f"    Latest MACD: {latest_macd:.4f}")

        if signals:
            print(f"    Final signal: {signals.get('signal', 'N/A')}")
            print(f"    Signal strength: {signals.get('strength', 'N/A')}/10")

        test_results['end_to_end_workflow'] = {
            'status': 'PASS',
            'workflow_time_seconds': workflow_time,
            'latest_price': latest_price,
            'period_change_percent': price_change,
            'latest_rsi': latest_rsi,
            'latest_macd': latest_macd,
            'final_signal': signals.get('signal', 'N/A') if signals else 'N/A',
            'signal_strength': signals.get('strength', 0) if signals else 0
        }

    except Exception as e:
        print(f"[FAIL] End-to-end workflow failed: {e}")
        traceback.print_exc()
        test_results['end_to_end_workflow'] = {'status': 'FAIL', 'error': str(e)}

    # Performance Benchmarks
    print("\n8. TESTING PERFORMANCE BENCHMARKS")
    print("-" * 40)

    try:
        from src.indicators.core_indicators import CoreIndicators
        from src.indicators.phase2_extended_indicators import Phase2ExtendedIndicators

        core_indicators = CoreIndicators()
        ext_indicators = Phase2ExtendedIndicators()

        test_series = test_data['close']
        n_iterations = 5

        # Benchmark core indicators
        start_time = time.time()
        for _ in range(n_iterations):
            _ = core_indicators.calculate_rsi(test_series, 14)
            _ = core_indicators.calculate_macd(test_series, 12, 26, 9)
            _ = core_indicators.calculate_bollinger_bands(test_series, 20, 2)
        core_time = (time.time() - start_time) / n_iterations

        # Benchmark extended indicators
        start_time = time.time()
        for _ in range(n_iterations):
            _ = ext_indicators.calculate_dema(test_series, 20)
            _ = ext_indicators.calculate_stochastic(
                test_data['close'], test_data['low'], test_data['high'], 14
            )
        ext_time = (time.time() - start_time) / n_iterations

        print(f"[OK] Performance benchmarks completed")
        print(f"    Core indicators avg: {core_time*1000:.2f}ms")
        print(f"    Extended indicators avg: {ext_time*1000:.2f}ms")

        # Performance targets
        core_target = 5.0  # 5ms target
        ext_target = 10.0   # 10ms target

        core_perf = 'PASS' if core_time < core_target/1000 else 'FAIL'
        ext_perf = 'PASS' if ext_time < ext_target/1000 else 'FAIL'

        test_results['performance_benchmarks'] = {
            'status': 'PASS' if core_perf == 'PASS' and ext_perf == 'PASS' else 'FAIL',
            'core_indicators_time_ms': core_time * 1000,
            'extended_indicators_time_ms': ext_time * 1000,
            'core_performance': core_perf,
            'extended_performance': ext_perf,
            'iterations': n_iterations
        }

    except Exception as e:
        print(f"[FAIL] Performance benchmark failed: {e}")
        test_results['performance_benchmarks'] = {'status': 'FAIL', 'error': str(e)}

    return generate_report(test_results, time.time() - start_time)

def generate_report(test_results, total_time):
    """Generate comprehensive test report"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST REPORT")
    print("=" * 60)

    # Calculate statistics
    total_tests = len(test_results)
    passed_tests = len([t for t in test_results.values() if t['status'] == 'PASS'])
    failed_tests = len([t for t in test_results.values() if t['status'] == 'FAIL'])
    warned_tests = len([t for t in test_results.values() if t['status'] == 'WARN'])

    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"\nOverall Test Results:")
    print(f"  Total test time: {total_time:.2f} seconds")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Warnings: {warned_tests}")
    print(f"  Failed: {failed_tests}")
    print(f"  Success rate: {success_rate:.1f}%")

    print(f"\nDetailed Results:")
    for test_name, result in test_results.items():
        status_icon = "[OK]" if result['status'] == 'PASS' else "[FAIL]" if result['status'] == 'FAIL' else "[WARN]"
        print(f"  {status_icon} {test_name}: {result['status']}")

        if result['status'] == 'FAIL':
            print(f"    Error: {result.get('error', 'Unknown error')}")
        elif result['status'] == 'WARN':
            print(f"    Warning: {result.get('message', 'Unknown warning')}")

    # Overall assessment
    print(f"\nSystem Assessment:")
    if success_rate >= 80:
        print("  STATUS: EXCELLENT")
        print("  The HIBOR Technical Prototype is ready for production use!")
        readiness = "PRODUCTION_READY"
    elif success_rate >= 60:
        print("  STATUS: GOOD")
        print("  The system is functional with minor issues.")
        readiness = "MOSTLY_READY"
    else:
        print("  STATUS: NEEDS ATTENTION")
        print("  Significant issues found that need to be resolved.")
        readiness = "NEEDS_FIXES"

    # Key achievements
    print(f"\nKey Achievements:")
    if 'core_indicators' in test_results and test_results['core_indicators']['status'] == 'PASS':
        print(f"  Core indicators: {test_results['core_indicators']['indicators_tested']} tested")

    if 'extended_indicators' in test_results and test_results['extended_indicators']['status'] == 'PASS':
        print(f"  Extended indicators: {test_results['extended_indicators']['indicators_tested']} tested")

    if 'vectorbt_engine' in test_results and test_results['vectorbt_engine']['status'] == 'PASS':
        print(f"  Backtesting: Sharpe {test_results['vectorbt_engine']['sharpe_ratio']:.3f}")

    if 'composite_signal_generator' in test_results and test_results['composite_signal_generator']['status'] == 'PASS':
        print(f"  Signal fusion: {test_results['composite_signal_generator']['signal_type']} signal")

    if 'end_to_end_workflow' in test_results and test_results['end_to_end_workflow']['status'] == 'PASS':
        print(f"  End-to-end workflow: {test_results['end_to_end_workflow']['workflow_time_seconds']:.2f}s")

    print("\n" + "=" * 60)

    # Save detailed report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'simple_system_test_report_{timestamp}.json'

    try:
        report_data = {
            'test_timestamp': timestamp,
            'total_test_time_seconds': total_time,
            'test_statistics': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'warned_tests': warned_tests,
                'success_rate': success_rate
            },
            'readiness_level': readiness,
            'detailed_results': test_results
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"Detailed report saved to: {report_file}")

    except Exception as e:
        print(f"Failed to save report: {e}")

    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'success_rate': success_rate,
        'readiness_level': readiness,
        'report_file': report_file if 'report_file' in locals() else None
    }

if __name__ == "__main__":
    print("Starting comprehensive system validation...")

    try:
        report = test_all_systems()

        if report['readiness_level'] in ['PRODUCTION_READY', 'MOSTLY_READY']:
            print(f"\nSystem validation PASSED!")
            print("Ready for next deployment phase")
            exit(0)
        else:
            print(f"\nSystem validation FAILED!")
            print("Address issues before proceeding")
            exit(1)

    except Exception as e:
        print(f"\nComprehensive test failed: {e}")
        traceback.print_exc()
        exit(1)