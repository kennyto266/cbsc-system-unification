#!/usr/bin/env python3
"""
HIBOR Technical Prototype - Comprehensive System Testing
全方位系統測試 - 驗證所有功能的完整性和性能
"""

import sys
import os
import time
import traceback
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add simplified_system to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system'))

class ComprehensiveSystemTester:
    """全方位系統測試器"""

    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.test_data = None

        print("=" * 80)
        print("🧪 HIBOR TECHNICAL PROTOTYPE - COMPREHENSIVE SYSTEM TESTING")
        print("=" * 80)
        print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Working directory: {os.getcwd()}")
        print("")

    def setup_test_data(self):
        """設置測試數據"""
        print("📊 Setting up test data...")

        try:
            # Create realistic test data
            dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
            n_days = len(dates)

            # Simulate stock price movement
            np.random.seed(42)  # For reproducible results
            base_price = 100
            returns = np.random.normal(0.001, 0.02, n_days)  # Daily returns
            prices = base_price * np.exp(np.cumsum(returns))

            # Generate OHLCV data
            noise_factor = 0.01
            self.test_data = pd.DataFrame({
                'open': prices * (1 + np.random.normal(0, noise_factor, n_days)),
                'high': prices * (1 + np.abs(np.random.normal(0, noise_factor, n_days))),
                'low': prices * (1 - np.abs(np.random.normal(0, noise_factor, n_days))),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, n_days)
            }, index=dates)

            # Ensure OHLC relationships are valid
            self.test_data['high'] = np.maximum(
                self.test_data['high'],
                np.maximum(self.test_data['open'], self.test_data['close'])
            )
            self.test_data['low'] = np.minimum(
                self.test_data['low'],
                np.minimum(self.test_data['open'], self.test_data['close'])
            )

            print(f"  ✅ Generated test data: {len(self.test_data)} records")
            print(f"  📈 Price range: ${self.test_data['close'].min():.2f} - ${self.test_data['close'].max():.2f}")
            print(f"  📊 Volume range: {self.test_data['volume'].min():,} - {self.test_data['volume'].max():,}")

            self.test_results['data_setup'] = {
                'status': 'PASS',
                'records': len(self.test_data),
                'date_range': f"{self.test_data.index[0].date()} to {self.test_data.index[-1].date()}",
                'price_range': f"${self.test_data['close'].min():.2f} - ${self.test_data['close'].max():.2f}"
            }

            return True

        except Exception as e:
            print(f"  ❌ Data setup failed: {e}")
            self.test_results['data_setup'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False

    def test_data_layer(self):
        """測試數據接入層"""
        print("")
        print("🔌 LAYER 1: Data Access Layer Testing")
        print("-" * 50)

        # Test 1.1: Stock API
        print("📈 Testing Stock API...")
        try:
            from src.api.stock_api import get_hk_stock_data

            start_time = time.time()
            stock_data = get_hk_stock_data("0700.HK", 30)  # Get 30 days
            api_time = time.time() - start_time

            if not stock_data.empty:
                print(f"  ✅ Stock API: Retrieved {len(stock_data)} records in {api_time:.2f}s")
                self.test_results['stock_api'] = {
                    'status': 'PASS',
                    'records': len(stock_data),
                    'response_time': api_time,
                    'data_columns': list(stock_data.columns)
                }
            else:
                print("  ⚠️ Stock API: No data returned (may be expected)")
                self.test_results['stock_api'] = {
                    'status': 'WARN',
                    'message': 'No data returned'
                }

        except Exception as e:
            print(f"  ❌ Stock API test failed: {e}")
            self.test_results['stock_api'] = {
                'status': 'FAIL',
                'error': str(e)
            }

        # Test 1.2: Government Data API
        print("🏛️ Testing Government Data API...")
        try:
            from src.api.government_data import get_latest_hibor

            start_time = time.time()
            hibor_data = get_latest_hibor()
            gov_time = time.time() - start_time

            if hibor_data:
                print(f"  ✅ Government API: Retrieved HIBOR data in {gov_time:.2f}s")
                print(f"  📊 Latest HIBOR rates: {list(hibor_data.keys())[:3]}...")
                self.test_results['government_api'] = {
                    'status': 'PASS',
                    'response_time': gov_time,
                    'data_keys': len(hibor_data)
                }
            else:
                print("  ⚠️ Government API: No data returned")
                self.test_results['government_api'] = {
                    'status': 'WARN',
                    'message': 'No data returned'
                }

        except Exception as e:
            print(f"  ❌ Government API test failed: {e}")
            self.test_results['government_api'] = {
                'status': 'FAIL',
                'error': str(e)
            }

    def test_indicator_layer(self):
        """測試技術指標層"""
        print("")
        print("📊 LAYER 2: Technical Indicators Layer Testing")
        print("-" * 50)

        # Test 2.1: Core Indicators
        print("🔧 Testing Core Indicators...")
        try:
            from src.indicators.core_indicators import CoreIndicators

            indicators = CoreIndicators()

            # Test basic indicators
            test_data = self.test_data['close']

            start_time = time.time()
            sma = indicators.calculate_sma(test_data, 20)
            ema = indicators.calculate_ema(test_data, 20)
            rsi = indicators.calculate_rsi(test_data, 14)
            macd = indicators.calculate_macd(test_data, 12, 26, 9)
            bb = indicators.calculate_bollinger_bands(test_data, 20, 2)
            calc_time = time.time() - start_time

            print(f"  ✅ Core indicators calculated in {calc_time:.3f}s")
            print(f"  📈 SMA latest: {sma.iloc[-1]:.2f}")
            print(f"  📈 RSI latest: {rsi.iloc[-1]:.2f}")
            print(f"  📊 MACD signal: {macd['macd'].iloc[-1]:.4f}")

            self.test_results['core_indicators'] = {
                'status': 'PASS',
                'calculation_time': calc_time,
                'indicators_tested': 5,
                'sma_latest': float(sma.iloc[-1]),
                'rsi_latest': float(rsi.iloc[-1])
            }

        except Exception as e:
            print(f"  ❌ Core indicators test failed: {e}")
            self.test_results['core_indicators'] = {
                'status': 'FAIL',
                'error': str(e)
            }

        # Test 2.2: Extended Indicators (Phase 2)
        print("🚀 Testing Extended Indicators (Phase 2)...")
        try:
            from src.indicators.phase2_extended_indicators import Phase2ExtendedIndicators

            ext_indicators = Phase2ExtendedIndicators()

            start_time = time.time()

            # Test trend indicators
            dema = ext_indicators.calculate_dema(test_data, 20)
            tema = ext_indicators.calculate_tema(test_data, 20)
            trima = ext_indicators.calculate_trima(test_data, 20)

            # Test momentum indicators
            stoch = ext_indicators.calculate_stochastic(
                self.test_data['close'],
                self.test_data['low'],
                self.test_data['high'],
                14
            )
            williams_r = ext_indicators.calculate_williams_r(
                self.test_data['close'],
                self.test_data['low'],
                self.test_data['high'],
                14
            )

            # Test volatility indicators
            atr = ext_indicators.calculate_atr(
                self.test_data['high'],
                self.test_data['low'],
                self.test_data['close'],
                14
            )

            ext_calc_time = time.time() - start_time

            print(f"  ✅ Extended indicators calculated in {ext_calc_time:.3f}s")
            print(f"  📈 DEMA latest: {dema.iloc[-1]:.2f}")
            print(f"  📊 Stochastic latest: {stoch.iloc[-1]:.2f}")
            print(f"  📊 Williams %R latest: {williams_r.iloc[-1]:.2f}")
            print(f"  📊 ATR latest: {atr.iloc[-1]:.2f}")

            self.test_results['extended_indicators'] = {
                'status': 'PASS',
                'calculation_time': ext_calc_time,
                'indicators_tested': 6,
                'dema_latest': float(dema.iloc[-1]),
                'stoch_latest': float(stoch.iloc[-1])
            }

        except Exception as e:
            print(f"  ❌ Extended indicators test failed: {e}")
            traceback.print_exc()
            self.test_results['extended_indicators'] = {
                'status': 'FAIL',
                'error': str(e)
            }

    def test_optimization_layer(self):
        """測試參數優化層"""
        print("")
        print("⚡ LAYER 3: Parameter Optimization Layer Testing")
        print("-" * 50)

        # Test 3.1: VectorBT Engine
        print("🔬 Testing VectorBT Engine...")
        try:
            from src.backtest.vectorbt_engine import VectorBTEngine

            engine = VectorBTEngine()

            # Prepare data for VectorBT (need price data)
            price_data = self.test_data['close'].tail(100)  # Use last 100 days

            start_time = time.time()

            # Test RSI strategy
            rsi_result = engine.backtest_strategy(
                self.test_data.tail(100),
                'RSI_MEAN_REVERSION',
                {'period': 14, 'oversold': 30, 'overbought': 70}
            )

            vbt_time = time.time() - start_time

            if rsi_result:
                print(f"  ✅ VectorBT backtest completed in {vbt_time:.3f}s")
                print(f"  📊 Total return: {rsi_result.total_return:.2%}")
                print(f"  📊 Sharpe ratio: {rsi_result.sharpe_ratio:.3f}")
                print(f"  📊 Max drawdown: {rsi_result.max_drawdown:.2%}")

                self.test_results['vectorbt_engine'] = {
                    'status': 'PASS',
                    'backtest_time': vbt_time,
                    'total_return': float(rsi_result.total_return),
                    'sharpe_ratio': float(rsi_result.sharpe_ratio),
                    'max_drawdown': float(rsi_result.max_drawdown)
                }
            else:
                print("  ⚠️ VectorBT: No result returned")
                self.test_results['vectorbt_engine'] = {
                    'status': 'WARN',
                    'message': 'No result returned'
                }

        except Exception as e:
            print(f"  ❌ VectorBT engine test failed: {e}")
            self.test_results['vectorbt_engine'] = {
                'status': 'FAIL',
                'error': str(e)
            }

        # Test 3.2: Massive Optimizer (Phase 3)
        print("🚀 Testing Massive Parameter Optimizer (Phase 3)...")
        try:
            from src.backtest.massive_optimizer import massive_optimizer

            start_time = time.time()

            # Test small-scale optimization to avoid long execution
            result = massive_optimizer.optimize_single_strategy(
                strategy_name="RSI_MEAN_REVERSION",
                symbol="TEST",  # Use test symbol
                max_combinations=10,  # Very small for testing
                optimization_metric="sharpe_ratio"
            )

            opt_time = time.time() - start_time

            if result:
                print(f"  ✅ Parameter optimizer completed in {opt_time:.3f}s")
                print(f"  🔍 Combinations tested: {result.get('total_combinations', 'N/A')}")
                print(f"  🏆 Best score: {result.get('best_score', 'N/A')}")

                self.test_results['massive_optimizer'] = {
                    'status': 'PASS',
                    'optimization_time': opt_time,
                    'combinations_tested': result.get('total_combinations', 0),
                    'best_score': result.get('best_score', 0)
                }
            else:
                print("  ⚠️ Parameter optimizer: No result returned")
                self.test_results['massive_optimizer'] = {
                    'status': 'WARN',
                    'message': 'No result returned'
                }

        except Exception as e:
            print(f"  ❌ Massive optimizer test failed: {e}")
            self.test_results['massive_optimizer'] = {
                'status': 'FAIL',
                'error': str(e)
            }

    def test_signal_fusion_layer(self):
        """測試信號融合層"""
        print("")
        print("🧠 LAYER 4: Signal Fusion Layer Testing")
        print("-" * 50)

        # Test 4.1: Signal Generator
        print("📡 Testing Signal Generator...")
        try:
            from src.signal_fusion.signal_generator import SignalGenerator

            generator = SignalGenerator()

            # Use test data
            test_signals = generator.generate_rsi_signals(self.test_data['close'], 14)

            print(f"  ✅ Generated {len(test_signals)} RSI signals")

            # Check latest signal
            if test_signals:
                latest_signal = test_signals[-1]
                print(f"  📊 Latest signal: {latest_signal.get('signal', 'N/A')}")
                print(f"  💪 Signal strength: {latest_signal.get('strength', 'N/A')}/10")
                print(f"  🎯 Confidence: {latest_signal.get('confidence', 'N/A'):.2f}")

                self.test_results['signal_generator'] = {
                    'status': 'PASS',
                    'signals_generated': len(test_signals),
                    'latest_signal': latest_signal.get('signal', 'N/A'),
                    'latest_strength': latest_signal.get('strength', 0)
                }
            else:
                print("  ⚠️ Signal generator: No signals generated")
                self.test_results['signal_generator'] = {
                    'status': 'WARN',
                    'message': 'No signals generated'
                }

        except Exception as e:
            print(f"  ❌ Signal generator test failed: {e}")
            self.test_results['signal_generator'] = {
                'status': 'FAIL',
                'error': str(e)
            }

        # Test 4.2: Composite Signal Generator (Phase 4)
        print("🎯 Testing Composite Signal Generator (Phase 4)...")
        try:
            from src.signal_fusion.composite_signal_generator import CompositeSignalGenerator

            fusion = CompositeSignalGenerator()

            start_time = time.time()

            # Test with limited data to ensure quick execution
            limited_data = self.test_data.tail(50)

            # Use correct method signature
            signals = fusion.generate_composite_signal(limited_data)

            fusion_time = time.time() - start_time

            if signals:
                print(f"  ✅ Composite signal generated in {fusion_time:.3f}s")
                print(f"  🎯 Signal type: {signals.get('signal', 'N/A')}")
                print(f"  💪 Signal strength: {signals.get('strength', 'N/A')}/10")
                print(f"  🎯 Confidence: {signals.get('confidence', 'N/A'):.1%}")
                print(f"  ⭐ Quality score: {signals.get('quality_score', 'N/A')}/100")
                print(f"  ⚠️ Risk level: {signals.get('risk_level', 'N/A')}")

                self.test_results['composite_signal_generator'] = {
                    'status': 'PASS',
                    'generation_time': fusion_time,
                    'signal_type': signals.get('signal', 'N/A'),
                    'strength': signals.get('strength', 0),
                    'confidence': signals.get('confidence', 0),
                    'quality_score': signals.get('quality_score', 0)
                }
            else:
                print("  ⚠️ Composite signal generator: No result")
                self.test_results['composite_signal_generator'] = {
                    'status': 'WARN',
                    'message': 'No result returned'
                }

        except Exception as e:
            print(f"  ❌ Composite signal generator test failed: {e}")
            traceback.print_exc()
            self.test_results['composite_signal_generator'] = {
                'status': 'FAIL',
                'error': str(e)
            }

    def test_performance_benchmarks(self):
        """測試性能基準"""
        print("")
        print("⏱️ PERFORMANCE BENCHMARK TESTING")
        print("-" * 50)

        # Test 5.1: Indicator Performance
        print("📊 Testing Indicator Calculation Performance...")
        try:
            from src.indicators.core_indicators import CoreIndicators
            from src.indicators.phase2_extended_indicators import Phase2ExtendedIndicators

            core_indicators = CoreIndicators()
            ext_indicators = Phase2ExtendedIndicators()

            test_data = self.test_data['close']
            n_iterations = 10

            # Benchmark core indicators
            start_time = time.time()
            for _ in range(n_iterations):
                _ = core_indicators.calculate_rsi(test_data, 14)
                _ = core_indicators.calculate_macd(test_data, 12, 26, 9)
                _ = core_indicators.calculate_bollinger_bands(test_data, 20, 2)
            core_time = (time.time() - start_time) / n_iterations

            # Benchmark extended indicators
            start_time = time.time()
            for _ in range(n_iterations):
                _ = ext_indicators.calculate_dema(test_data, 20)
                _ = ext_indicators.calculate_stochastic(
                    self.test_data['close'],
                    self.test_data['low'],
                    self.test_data['high'],
                    14
                )
                _ = ext_indicators.calculate_atr(
                    self.test_data['high'],
                    self.test_data['low'],
                    self.test_data['close'],
                    14
                )
            ext_time = (time.time() - start_time) / n_iterations

            print(f"  ✅ Core indicators avg time: {core_time*1000:.2f}ms")
            print(f"  ✅ Extended indicators avg time: {ext_time*1000:.2f}ms")

            # Performance targets
            core_target = 1.0  # 1ms target
            ext_target = 2.0   # 2ms target for more complex indicators

            core_perf = 'PASS' if core_time < core_target/1000 else 'FAIL'
            ext_perf = 'PASS' if ext_time < ext_target/1000 else 'FAIL'

            self.test_results['performance_benchmarks'] = {
                'status': 'PASS' if core_perf == 'PASS' and ext_perf == 'PASS' else 'FAIL',
                'core_indicators_time_ms': core_time * 1000,
                'extended_indicators_time_ms': ext_time * 1000,
                'core_performance': core_perf,
                'extended_performance': ext_perf,
                'iterations': n_iterations
            }

        except Exception as e:
            print(f"  ❌ Performance benchmark failed: {e}")
            self.test_results['performance_benchmarks'] = {
                'status': 'FAIL',
                'error': str(e)
            }

        # Test 5.2: Memory Usage
        print("💾 Testing Memory Usage...")
        try:
            import psutil
            import gc

            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Perform memory-intensive operations
            large_data = self.test_data.copy()

            # Calculate multiple indicators on large dataset
            from src.indicators.phase2_extended_indicators import Phase2ExtendedIndicators
            ext_indicators = Phase2ExtendedIndicators()

            _ = ext_indicators.calculate_dema(large_data['close'], 50)
            _ = ext_indicators.calculate_tema(large_data['close'], 50)
            _ = ext_indicators.calculate_stochastic(
                large_data['close'], large_data['low'], large_data['high'], 50
            )

            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory

            # Clean up
            del large_data
            gc.collect()

            final_memory = process.memory_info().rss / 1024 / 1024  # MB

            print(f"  📊 Initial memory: {initial_memory:.1f}MB")
            print(f"  📊 Peak memory: {peak_memory:.1f}MB")
            print(f"  📊 Memory increase: {memory_increase:.1f}MB")
            print(f"  📊 Final memory: {final_memory:.1f}MB")

            # Memory target: < 100MB increase
            memory_target = 100
            memory_perf = 'PASS' if memory_increase < memory_target else 'FAIL'

            self.test_results['memory_usage'] = {
                'status': memory_perf,
                'initial_memory_mb': initial_memory,
                'peak_memory_mb': peak_memory,
                'memory_increase_mb': memory_increase,
                'final_memory_mb': final_memory,
                'target_mb': memory_target
            }

        except Exception as e:
            print(f"  ❌ Memory usage test failed: {e}")
            self.test_results['memory_usage'] = {
                'status': 'FAIL',
                'error': str(e)
            }

    def test_end_to_end_workflow(self):
        """測試端到端工作流程"""
        print("")
        print("🔄 END-TO-END WORKFLOW TESTING")
        print("-" * 50)

        try:
            # Simulate complete trading workflow
            print("🚀 Simulating Complete Trading Workflow...")

            workflow_start = time.time()

            # Step 1: Data Collection
            print("  📊 Step 1: Data Collection...")
            workflow_data = self.test_data.tail(100)  # Use last 100 days

            # Step 2: Technical Analysis
            print("  📈 Step 2: Technical Analysis...")
            from src.indicators.core_indicators import CoreIndicators
            from src.indicators.phase2_extended_indicators import Phase2ExtendedIndicators

            core_indicators = CoreIndicators()
            ext_indicators = Phase2ExtendedIndicators()

            # Calculate indicators
            rsi = core_indicators.calculate_rsi(workflow_data['close'], 14)
            macd = core_indicators.calculate_macd(workflow_data['close'], 12, 26, 9)
            bb = core_indicators.calculate_bollinger_bands(workflow_data['close'], 20, 2)

            dema = ext_indicators.calculate_dema(workflow_data['close'], 20)
            stoch = ext_indicators.calculate_stochastic(
                workflow_data['close'], workflow_data['low'], workflow_data['high'], 14
            )

            # Step 3: Signal Generation
            print("  📡 Step 3: Signal Generation...")
            from src.signal_fusion.composite_signal_generator import CompositeSignalGenerator

            fusion = CompositeSignalGenerator()
            signals = fusion.generate_composite_signal(workflow_data)

            # Step 4: Performance Analysis
            print("  📊 Step 4: Performance Analysis...")
            latest_rsi = rsi.iloc[-1]
            latest_macd = macd['macd'].iloc[-1]
            latest_price = workflow_data['close'].iloc[-1]
            price_change = (latest_price / workflow_data['close'].iloc[0] - 1) * 100

            workflow_time = time.time() - workflow_start

            print(f"  ✅ Workflow completed in {workflow_time:.3f}s")
            print(f"  📈 Latest price: ${latest_price:.2f}")
            print(f"  📊 Period change: {price_change:+.2f}%")
            print(f"  📊 Latest RSI: {latest_rsi:.2f}")
            print(f"  📊 Latest MACD: {latest_macd:.4f}")

            if signals:
                print(f"  🎯 Final signal: {signals.get('signal', 'N/A')}")
                print(f"  💪 Signal strength: {signals.get('strength', 'N/A')}/10")
                print(f"  🎯 Confidence: {signals.get('confidence', 'N/A'):.1%}")

            # Workflow performance target: < 5 seconds
            workflow_target = 5.0
            workflow_perf = 'PASS' if workflow_time < workflow_target else 'FAIL'

            self.test_results['end_to_end_workflow'] = {
                'status': workflow_perf,
                'workflow_time_seconds': workflow_time,
                'latest_price': latest_price,
                'period_change_percent': price_change,
                'latest_rsi': latest_rsi,
                'latest_macd': latest_macd,
                'final_signal': signals.get('signal', 'N/A') if signals else 'N/A',
                'signal_strength': signals.get('strength', 0) if signals else 0,
                'target_seconds': workflow_target
            }

        except Exception as e:
            print(f"  ❌ End-to-end workflow failed: {e}")
            traceback.print_exc()
            self.test_results['end_to_end_workflow'] = {
                'status': 'FAIL',
                'error': str(e)
            }

    def generate_test_report(self):
        """生成測試報告"""
        print("")
        print("=" * 80)
        print("📋 COMPREHENSIVE TEST REPORT")
        print("=" * 80)

        total_time = time.time() - self.start_time

        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results.values() if t['status'] == 'PASS'])
        failed_tests = len([t for t in self.test_results.values() if t['status'] == 'FAIL'])
        warned_tests = len([t for t in self.test_results.values() if t['status'] == 'WARN'])

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"🕐 Total test time: {total_time:.2f} seconds")
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"⚠️ Warnings: {warned_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        print("")

        # Detailed results
        for test_name, result in self.test_results.items():
            status_icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(result['status'], "❓")
            print(f"{status_icon} {test_name}: {result['status']}")

            if result['status'] == 'FAIL':
                print(f"    Error: {result.get('error', 'Unknown error')}")
            elif result['status'] == 'WARN':
                print(f"    Warning: {result.get('message', 'Unknown warning')}")

        print("")
        print("=" * 80)

        # Overall assessment
        if success_rate >= 80:
            print("🎉 SYSTEM STATUS: EXCELLENT")
            print("✅ The HIBOR Technical Prototype is ready for production use!")
        elif success_rate >= 60:
            print("👍 SYSTEM STATUS: GOOD")
            print("✅ The system is functional with minor issues that need attention.")
        else:
            print("⚠️ SYSTEM STATUS: NEEDS ATTENTION")
            print("❌ Significant issues found that need to be resolved before production use.")

        print("")
        print("🚀 Key Achievements:")
        if 'data_setup' in self.test_results and self.test_results['data_setup']['status'] == 'PASS':
            print(f"  📊 Realistic test data: {self.test_results['data_setup']['records']} records")

        if 'core_indicators' in self.test_results and self.test_results['core_indicators']['status'] == 'PASS':
            print(f"  📈 Core indicators: {self.test_results['core_indicators']['indicators_tested']} tested")

        if 'extended_indicators' in self.test_results and self.test_results['extended_indicators']['status'] == 'PASS':
            print(f"  🚀 Extended indicators: {self.test_results['extended_indicators']['indicators_tested']} tested")

        if 'vectorbt_engine' in self.test_results and self.test_results['vectorbt_engine']['status'] == 'PASS':
            print(f"  🔬 Backtesting: Sharpe {self.test_results['vectorbt_engine']['sharpe_ratio']:.3f}")

        if 'composite_signal_generator' in self.test_results and self.test_results['composite_signal_generator']['status'] == 'PASS':
            print(f"  🧠 Signal fusion: {self.test_results['composite_signal_generator']['signal_type']} signal")

        if 'end_to_end_workflow' in self.test_results and self.test_results['end_to_end_workflow']['status'] == 'PASS':
            print(f"  🔄 End-to-end workflow: {self.test_results['end_to_end_workflow']['workflow_time_seconds']:.2f}s")

        print("=" * 80)

        # Save detailed report
        self.save_test_report()

    def save_test_report(self):
        """保存測試報告到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'comprehensive_test_report_{timestamp}.json'

        try:
            # Prepare report data
            report_data = {
                'test_timestamp': timestamp,
                'total_test_time_seconds': time.time() - self.start_time,
                'test_environment': {
                    'python_version': sys.version,
                    'working_directory': os.getcwd(),
                    'platform': sys.platform
                },
                'test_statistics': {
                    'total_tests': len(self.test_results),
                    'passed_tests': len([t for t in self.test_results.values() if t['status'] == 'PASS']),
                    'failed_tests': len([t for t in self.test_results.values() if t['status'] == 'FAIL']),
                    'warned_tests': len([t for t in self.test_results.values() if t['status'] == 'WARN']),
                    'success_rate': len([t for t in self.test_results.values() if t['status'] == 'PASS']) / len(self.test_results) * 100 if self.test_results else 0
                },
                'detailed_results': self.test_results
            }

            # Save report
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"📄 Detailed test report saved to: {report_file}")

        except Exception as e:
            print(f"⚠️ Failed to save test report: {e}")

def main():
    """主測試函數"""
    tester = ComprehensiveSystemTester()

    try:
        # Setup test data
        if not tester.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return

        # Run all test layers
        tester.test_data_layer()
        tester.test_indicator_layer()
        tester.test_optimization_layer()
        tester.test_signal_fusion_layer()
        tester.test_performance_benchmarks()
        tester.test_end_to_end_workflow()

        # Generate final report
        tester.generate_test_report()

    except Exception as e:
        print(f"❌ Comprehensive testing failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()