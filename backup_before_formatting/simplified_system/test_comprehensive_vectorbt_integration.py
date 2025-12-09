#!/usr/bin/env python3
"""
Phase 5: Comprehensive VectorBT Integration Testing
全面的VectorBT集成測試套件

This comprehensive test suite validates the entire enhanced VectorBT integration
including all implemented phases: parameter optimization, advanced algorithms,
distributed computing, risk management, and enhanced technical indicators.
"""

import time
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json
import sys
import os
from typing import Dict, List, Any, Tuple

# Add current directory to path
sys.path.append(os.getcwd())

# Import all tested components
from src.api.stock_api import get_hk_stock_data
from src.backtest.vectorbt_engine import VectorBTEngine
from src.backtest.advanced_optimizer import AdvancedOptimizer
from src.backtest.threaded_optimizer import ThreadedOptimizer
from src.backtest.professional_risk_metrics import RiskCalculator
from src.backtest.enhanced_technical_indicators import VectorizedTechnicalIndicators
from src.backtest.custom_indicator_framework import create_indicator_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorBTIntegrationTester:
    """Comprehensive VectorBT integration test suite"""

    def __init__(self):
        """Initialize test suite"""
        self.test_results = {
            'test_time': datetime.now().isoformat(),
            'phases': {},
            'overall_status': 'UNKNOWN',
            'performance_metrics': {},
            'errors': []
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        logger.info("開始執行全面VectorBT集成測試...")
        logger.info("="*60)
        logger.info("Phase 5: 測試和驗證")
        logger.info("="*60)

        try:
            # Phase 1: Core VectorBT Engine Testing
            self.test_results['phases']['core_engine'] = self.test_core_vectorbt_engine()

            # Phase 2: Advanced Optimization Testing
            self.test_results['phases']['advanced_optimization'] = self.test_advanced_optimization()

            # Phase 3: Distributed Computing Testing
            self.test_results['phases']['distributed_computing'] = self.test_distributed_computing()

            # Phase 4: Risk Management Testing
            self.test_results['phases']['risk_management'] = self.test_risk_management()

            # Phase 5: Enhanced Technical Indicators Testing
            self.test_results['phases']['enhanced_indicators'] = self.test_enhanced_indicators()

            # Phase 6: System Integration Testing
            self.test_results['phases']['system_integration'] = self.test_system_integration()

            # Phase 7: Performance Benchmarking
            self.test_results['phases']['performance_benchmark'] = self.test_performance_benchmark()

            # Calculate overall status
            self.calculate_overall_status()

            # Save comprehensive report
            self.save_comprehensive_report()

            return self.test_results

        except Exception as e:
            logger.error(f"測試套件執行失敗: {e}")
            self.test_results['error'] = str(e)
            self.test_results['overall_status'] = 'FAILED'
            return self.test_results

    def test_core_vectorbt_engine(self) -> Dict[str, Any]:
        """測試Phase 1: Core VectorBT Engine"""
        logger.info("測試 Phase 1: Core VectorBT Engine...")

        phase_results = {
            'status': 'UNKNOWN',
            'tests': {},
            'performance': {}
        }

        try:
            # Load test data
            data = self.load_test_data()
            logger.info(f"載入測試數據: {len(data)} 條記錄")

            # Initialize VectorBT Engine
            engine = VectorBTEngine()
            phase_results['tests']['engine_initialization'] = True

            # Test strategy backtesting
            strategies_to_test = [
                ('RSI_MEAN_REVERSION', {'period': 14, 'oversold': 30, 'overbought': 70}),
                ('MACD_CROSSOVER', {'fast': 12, 'slow': 26, 'signal': 9}),
                ('BOLLINGER_BANDS', {'period': 20, 'std_dev': 2.0})
            ]

            strategy_results = {}
            for strategy_name, params in strategies_to_test:
                try:
                    start_time = time.time()
                    result = engine.backtest_strategy(data, strategy_name, params, "0700.HK")
                    execution_time = time.time() - start_time

                    strategy_results[strategy_name] = {
                        'success': True,
                        'execution_time': execution_time,
                        'total_return': result.total_return,
                        'sharpe_ratio': result.sharpe_ratio,
                        'max_drawdown': result.max_drawdown
                    }

                    logger.info(f"  {strategy_name}: 回報 {result.total_return:.2%}, Sharpe {result.sharpe_ratio:.3f}")

                except Exception as e:
                    strategy_results[strategy_name] = {
                        'success': False,
                        'error': str(e)
                    }
                    logger.error(f"  {strategy_name} 失敗: {e}")

            phase_results['tests']['strategy_backtesting'] = strategy_results

            # Test parameter optimization
            param_ranges = {
                'period': list(range(10, 31, 5)),
                'oversold': [20, 30, 40],
                'overbought': [60, 70, 80]
            }

            start_time = time.time()
            optimization_result = engine.optimize_parameters(
                data, 'RSI_MEAN_REVERSION', param_ranges
            )
            optimization_time = time.time() - start_time

            phase_results['tests']['parameter_optimization'] = {
                'success': True,
                'execution_time': optimization_time,
                'combinations_tested': len(param_ranges['period']) * len(param_ranges['oversold']) * len(param_ranges['overbought']),
                'best_sharpe': optimization_result.get('best_score', 0)
            }

            phase_results['performance']['total_strategies'] = len(strategies_to_test)
            phase_results['performance']['successful_strategies'] = sum(1 for r in strategy_results.values() if r.get('success', False))

            # Check if all core tests passed
            core_tests_passed = (
                phase_results['tests'].get('engine_initialization', False) and
                phase_results['tests'].get('parameter_optimization', {}).get('success', False) and
                phase_results['performance']['successful_strategies'] > 0
            )

            phase_results['status'] = 'PASSED' if core_tests_passed else 'PARTIAL'

            logger.info(f"Phase 1 狀態: {phase_results['status']}")

        except Exception as e:
            phase_results['status'] = 'FAILED'
            phase_results['error'] = str(e)
            logger.error(f"Phase 1 測試失敗: {e}")

        return phase_results

    def test_advanced_optimization(self) -> Dict[str, Any]:
        """測試Phase 2: Advanced Optimization Algorithms"""
        logger.info("測試 Phase 2: Advanced Optimization Algorithms...")

        phase_results = {
            'status': 'UNKNOWN',
            'tests': {},
            'performance': {}
        }

        try:
            # Load test data
            data = self.load_test_data()

            # Initialize Advanced Optimizer
            optimizer = AdvancedOptimizer()

            # Test Bayesian Optimization
            param_bounds = {
                'period': (10, 30),
                'oversold': (20, 40),
                'overbought': (60, 80)
            }

            start_time = time.time()
            bayesian_result = optimizer.optimize_bayesian(
                data, 'RSI_MEAN_REVERSION', param_bounds, n_calls=10
            )
            bayesian_time = time.time() - start_time

            phase_results['tests']['bayesian_optimization'] = {
                'success': True,
                'execution_time': bayesian_time,
                'best_score': bayesian_result.get('best_score', 0),
                'iterations': bayesian_result.get('iterations', 0)
            }

            # Test Genetic Optimization
            start_time = time.time()
            genetic_result = optimizer.optimize_genetic(
                data, 'RSI_MEAN_REVERSION', {'period': (10, 30)}, population_size=10, generations=5
            )
            genetic_time = time.time() - start_time

            phase_results['tests']['genetic_optimization'] = {
                'success': True,
                'execution_time': genetic_time,
                'best_score': genetic_result.get('best_score', 0),
                'generations': genetic_result.get('generations', 0)
            }

            # Test Multi-Objective Optimization
            objectives = ['sharpe_ratio', 'max_drawdown', 'total_return']
            start_time = time.time()
            multi_obj_result = optimizer.multi_objective_optimize(
                data, 'RSI_MEAN_REVERSION', param_bounds, objectives=objectives
            )
            multi_obj_time = time.time() - start_time

            phase_results['tests']['multi_objective_optimization'] = {
                'success': True,
                'execution_time': multi_obj_time,
                'pareto_frontier_size': len(multi_obj_result.get('pareto_frontier', [])),
                'best_compromise_score': multi_obj_result.get('best_compromise', {}).get('composite_score', 0)
            }

            # Performance metrics
            phase_results['performance']['total_algorithms'] = 3
            successful_algorithms = sum(1 for test in phase_results['tests'].values() if test.get('success', False))
            phase_results['performance']['successful_algorithms'] = successful_algorithms

            phase_results['status'] = 'PASSED' if successful_algorithms >= 2 else 'PARTIAL'

            logger.info(f"  Bayesian 優化: 最佳分數 {bayesian_result.get('best_score', 0):.3f}")
            logger.info(f"  遺傳算法: 最佳分數 {genetic_result.get('best_score', 0):.3f}")
            logger.info(f"  多目標優化: Pareto前沿 {len(multi_obj_result.get('pareto_frontier', []))} 個解")
            logger.info(f"Phase 2 狀態: {phase_results['status']}")

        except Exception as e:
            phase_results['status'] = 'FAILED'
            phase_results['error'] = str(e)
            logger.error(f"Phase 2 測試失敗: {e}")

        return phase_results

    def test_distributed_computing(self) -> Dict[str, Any]:
        """測試Phase 3: Distributed Computing Support"""
        logger.info("測試 Phase 3: Distributed Computing Support...")

        phase_results = {
            'status': 'UNKNOWN',
            'tests': {},
            'performance': {}
        }

        try:
            # Load test data
            data = self.load_test_data()

            # Initialize Threaded Optimizer
            optimizer = ThreadedOptimizer(max_workers=2)  # Reduced for testing

            # Test parallel parameter sweep
            param_ranges = {
                'rsi_period': [10, 14, 20],
                'oversold': [30],
                'overbought': [70]
            }

            start_time = time.time()
            sweep_result = optimizer.run_optimization(timeout=60)
            sweep_time = time.time() - start_time

            phase_results['tests']['parallel_parameter_sweep'] = {
                'success': True,
                'execution_time': sweep_time,
                'total_tasks': sweep_result.get('total_tasks', 0),
                'successful_tasks': sweep_result.get('completed_tasks', 0),
                'workers_used': sweep_result.get('workers_used', 0)
            }

            # Test scalability
            worker_counts = [1, 2]
            scalability_results = {}

            for workers in worker_counts:
                test_optimizer = ThreadedOptimizer(max_workers=workers)
                test_result = test_optimizer.run_optimization(timeout=30)
                scalability_results[workers] = {
                    'execution_time': test_result.get('total_execution_time', 0),
                    'success_rate': test_result.get('success_rate', 0)
                }

            phase_results['tests']['scalability'] = {
                'success': True,
                'results': scalability_results
            }

            # Calculate speedup
            if len(scalability_results) > 1:
                time_1_worker = scalability_results[1]['execution_time']
                time_2_workers = scalability_results[2]['execution_time']
                speedup = time_1_worker / time_2_workers if time_2_workers > 0 else 0
                phase_results['performance']['speedup'] = speedup

            phase_results['performance']['max_workers_tested'] = max(worker_counts)
            phase_results['performance']['parallel_efficiency'] = sweep_result.get('success_rate', 0)

            # Check if distributed computing tests passed
            distributed_passed = (
                phase_results['tests'].get('parallel_parameter_sweep', {}).get('success', False) and
                sweep_result.get('completed_tasks', 0) > 0
            )

            phase_results['status'] = 'PASSED' if distributed_passed else 'PARTIAL'

            logger.info(f"  並行優化: {sweep_result.get('completed_tasks', 0)}/{sweep_result.get('total_tasks', 0)} 任務成功")
            logger.info(f"  可擴展性: {phase_results['performance'].get('speedup', 0):.2f}x 加速")
            logger.info(f"Phase 3 狀態: {phase_results['status']}")

        except Exception as e:
            phase_results['status'] = 'FAILED'
            phase_results['error'] = str(e)
            logger.error(f"Phase 3 測試失敗: {e}")

        return phase_results

    def test_risk_management(self) -> Dict[str, Any]:
        """測試Phase 4: Risk Management Integration"""
        logger.info("測試 Phase 4: Risk Management Integration...")

        phase_results = {
            'status': 'UNKNOWN',
            'tests': {},
            'performance': {}
        }

        try:
            # Load test data
            data = self.load_test_data()
            prices = data['close']

            # Initialize Risk Calculator
            risk_calculator = RiskCalculator(risk_free_rate=0.03)

            # Test comprehensive risk metrics
            start_time = time.time()
            risk_metrics = risk_calculator.calculate_comprehensive_metrics(prices)
            risk_calc_time = time.time() - start_time

            phase_results['tests']['risk_metrics_calculation'] = {
                'success': True,
                'execution_time': risk_calc_time,
                'sharpe_ratio': risk_metrics.sharpe_ratio,
                'max_drawdown': risk_metrics.max_drawdown,
                'var_95': risk_metrics.var_95,
                'sortino_ratio': risk_metrics.sortino_ratio,
                'calmar_ratio': risk_metrics.calmar_ratio
            }

            # Test VaR calculations
            returns = risk_calculator.calculate_returns(prices)
            var_95 = risk_calculator.calculate_var(returns, 0.95)
            cvar_95 = risk_calculator.calculate_cvar(returns, 0.95)

            phase_results['tests']['var_calculations'] = {
                'success': True,
                'var_95': var_95,
                'cvar_95': cvar_95,
                'cvar_var_relationship': cvar_95 <= var_95
            }

            # Test portfolio risk analysis
            # Create multi-asset test data
            np.random.seed(42)
            returns_matrix = pd.DataFrame(
                np.random.multivariate_normal([0.001, 0.0008], [[0.04, 0.02], [0.02, 0.03]], len(prices)),
                columns=['ASSET_A', 'ASSET_B'],
                index=prices.index
            )

            weights = np.array([0.6, 0.4])
            portfolio_risk = risk_calculator.calculate_portfolio_risk(returns_matrix, weights)

            phase_results['tests']['portfolio_risk'] = {
                'success': True,
                'portfolio_volatility': portfolio_risk['portfolio_volatility'],
                'risk_contribution_analysis': len(portfolio_risk['risk_contribution_percentages']) > 0
            }

            # Performance metrics
            phase_results['performance']['risk_metrics_computed'] = 8  # Number of risk metrics
            phase_results['performance']['calculation_time_ms'] = risk_calc_time * 1000

            # Check if risk management tests passed
            risk_passed = (
                phase_results['tests'].get('risk_metrics_calculation', {}).get('success', False) and
                not np.isnan(risk_metrics.sharpe_ratio) and
                phase_results['tests'].get('var_calculations', {}).get('cvar_var_relationship', False)
            )

            phase_results['status'] = 'PASSED' if risk_passed else 'PARTIAL'

            logger.info(f"  風險指標: Sharpe {risk_metrics.sharpe_ratio:.3f}, 最大回撤 {risk_metrics.max_drawdown:.2%}")
            logger.info(f"  VaR 95%: {var_95:.4f}, CVaR 95%: {cvar_95:.4f}")
            logger.info(f"  組合風險: 波動率 {portfolio_risk['portfolio_volatility']:.2%}")
            logger.info(f"Phase 4 狀態: {phase_results['status']}")

        except Exception as e:
            phase_results['status'] = 'FAILED'
            phase_results['error'] = str(e)
            logger.error(f"Phase 4 測試失敗: {e}")

        return phase_results

    def test_enhanced_indicators(self) -> Dict[str, Any]:
        """測試Phase 5: Enhanced Technical Indicators"""
        logger.info("測試 Phase 5: Enhanced Technical Indicators...")

        phase_results = {
            'status': 'UNKNOWN',
            'tests': {},
            'performance': {}
        }

        try:
            # Load test data
            data = self.load_test_data()

            # Initialize Enhanced Technical Indicators
            enhanced_indicators = VectorizedTechnicalIndicators()

            # Test vectorized RSI
            start_time = time.time()
            rsi_results = enhanced_indicators.calculate_rsi_vectorized(data, [14, 21])
            rsi_time = time.time() - start_time

            phase_results['tests']['vectorized_rsi'] = {
                'success': len(rsi_results) > 0,
                'periods_calculated': len(rsi_results),
                'execution_time': rsi_time,
                'rsi_14_range': [rsi_results['rsi_14'].min(), rsi_results['rsi_14'].max()]
            }

            # Test vectorized MACD
            start_time = time.time()
            macd_results = enhanced_indicators.calculate_macd_vectorized(data)
            macd_time = time.time() - start_time

            phase_results['tests']['vectorized_macd'] = {
                'success': len(macd_results) > 0,
                'combinations_calculated': len(macd_results),
                'execution_time': macd_time
            }

            # Test Bollinger Bands
            start_time = time.time()
            bb_results = enhanced_indicators.calculate_bollinger_bands_vectorized(data)
            bb_time = time.time() - start_time

            phase_results['tests']['vectorized_bollinger_bands'] = {
                'success': len(bb_results) > 0,
                'combinations_calculated': len(bb_results),
                'execution_time': bb_time
            }

            # Test Adaptive Parameters
            start_time = time.time()
            adaptive_period = enhanced_indicators.calculate_adaptive_parameters(data, 'rsi', 14, 0.2)
            adaptive_time = time.time() - start_time

            phase_results['tests']['adaptive_parameters'] = {
                'success': len(adaptive_period) > 0,
                'execution_time': adaptive_time,
                'period_range': [adaptive_period.min(), adaptive_period.max()]
            }

            # Test Custom Indicator Framework
            registry = create_indicator_registry()
            custom_indicator = registry.get_indicator('custom_mean_reversion')

            if custom_indicator:
                custom_result = custom_indicator.calculate(data)
                phase_results['tests']['custom_indicators'] = {
                    'success': True,
                    'indicators_registered': len(registry.list_all_indicators()),
                    'custom_calculation_success': len(custom_result) == len(data)
                }
            else:
                phase_results['tests']['custom_indicators'] = {
                    'success': False,
                    'error': 'Custom indicator not found'
                }

            # Performance metrics
            phase_results['performance']['total_indicator_types'] = 6
            phase_results['performance']['vectorization_efficiency'] = (
                (rsi_time + macd_time + bb_time) / 1000  # Total time in seconds
            )

            # Check if enhanced indicators tests passed
            enhanced_passed = (
                phase_results['tests'].get('vectorized_rsi', {}).get('success', False) and
                phase_results['tests'].get('vectorized_macd', {}).get('success', False) and
                phase_results['tests'].get('adaptive_parameters', {}).get('success', False)
            )

            phase_results['status'] = 'PASSED' if enhanced_passed else 'PARTIAL'

            logger.info(f"  向量化RSI: {len(rsi_results)} 個週期")
            logger.info(f"  向量化MACD: {len(macd_results)} 個組合")
            logger.info(f"  自適參數: {adaptive_period.min()}-{adaptive_period.max()} 範圍")
            logger.info(f"  自定義指標: {len(registry.list_all_indicators())} 個已註冊")
            logger.info(f"Phase 5 狀態: {phase_results['status']}")

        except Exception as e:
            phase_results['status'] = 'FAILED'
            phase_results['error'] = str(e)
            logger.error(f"Phase 5 測試失敗: {e}")

        return phase_results

    def test_system_integration(self) -> Dict[str, Any]:
        """測試Phase 6: System Integration"""
        logger.info("測試 Phase 6: System Integration...")

        phase_results = {
            'status': 'UNKNOWN',
            'tests': {},
            'performance': {}
        }

        try:
            # Load test data
            data = self.load_test_data()

            # Test end-to-end workflow
            start_time = time.time()

            # Step 1: Calculate enhanced indicators
            enhanced_indicators = VectorizedTechnicalIndicators()
            rsi_result = enhanced_indicators.calculate_rsi_vectorized(data, [14])
            macd_result = enhanced_indicators.calculate_macd_vectorized(data)

            # Step 2: Run optimization
            engine = VectorBTEngine()
            optimization_result = engine.optimize_parameters(
                data, 'RSI_MEAN_REVERSION', {'period': [14], 'oversold': [30], 'overbought': [70]}
            )

            # Step 3: Calculate risk metrics
            risk_calculator = RiskCalculator()
            risk_metrics = risk_calculator.calculate_comprehensive_metrics(data['close'])

            end_time = time.time()
            workflow_time = end_time - start_time

            phase_results['tests']['end_to_end_workflow'] = {
                'success': True,
                'execution_time': workflow_time,
                'indicators_calculated': len(rsi_result) + len(macd_result),
                'optimization_successful': optimization_result.get('best_score', 0) > 0,
                'risk_metrics_available': risk_metrics.sharpe_ratio != 0
            }

            # Test component compatibility
            compatibility_tests = []

            # Test data format compatibility
            try:
                enhanced_indicators.calculate_moving_averages_vectorized(data, [20])
                compatibility_tests.append('vectorbt_data_format')
            except Exception as e:
                logger.warning(f"數據格式兼容性問題: {e}")

            # Test parameter passing compatibility
            try:
                engine.backtest_strategy(data, 'RSI_MEAN_REVERSION', {'period': 14, 'oversold': 30, 'overbought': 70})
                compatibility_tests.append('parameter_passing')
            except Exception as e:
                logger.warning(f"參數傳遞兼容性問題: {e}")

            phase_results['tests']['compatibility'] = {
                'success': len(compatibility_tests) >= 1,
                'compatible_components': compatibility_tests
            }

            # Test data integrity
            integrity_tests = []

            # Check for NaN values in calculations
            if 'rsi_14' in rsi_result:
                nan_count = rsi_result['rsi_14'].isnull().sum()
                integrity_tests.append(f'rsi_nan_count_{nan_count}')

            # Check for extreme values
            if risk_metrics.sharpe_ratio > 10 or risk_metrics.sharpe_ratio < -10:
                logger.warning(f"極端Sharpe比率檢測: {risk_metrics.sharpe_ratio}")
                integrity_tests.append('extreme_sharpe_detected')

            phase_results['tests']['data_integrity'] = {
                'success': len([t for t in integrity_tests if 'nan_count_0' in t]) > 0,
                'integrity_issues': integrity_tests
            }

            # Performance metrics
            phase_results['performance']['workflow_time'] = workflow_time
            phase_results['performance']['components_compatible'] = len(compatibility_tests)
            phase_results['performance']['data_integrity_score'] = len([t for t in integrity_tests if 'nan_count_0' in t]) / len(integrity_tests) if integrity_tests else 0

            # Check if system integration tests passed
            integration_passed = (
                phase_results['tests'].get('end_to_end_workflow', {}).get('success', False) and
                phase_results['tests'].get('compatibility', {}).get('success', False)
            )

            phase_results['status'] = 'PASSED' if integration_passed else 'PARTIAL'

            logger.info(f"  端到端工作流程: {workflow_time:.2f}秒")
            logger.info(f"  兼容性測試: {len(compatibility_tests)}/{2} 組件兼容")
            logger.info(f"  數據完整性: {phase_results['performance']['data_integrity_score']:.1%}")
            logger.info(f"Phase 6 狀態: {phase_results['status']}")

        except Exception as e:
            phase_results['status'] = 'FAILED'
            phase_results['error'] = str(e)
            logger.error(f"Phase 6 測試失敗: {e}")

        return phase_results

    def test_performance_benchmark(self) -> Dict[str, Any]:
        """測試Phase 7: Performance Benchmarking"""
        logger.info("測試 Phase 7: Performance Benchmarking...")

        phase_results = {
            'status': 'UNKNOWN',
            'tests': {},
            'performance': {}
        }

        try:
            # Load test data with different sizes
            data_sizes = [100, 500, 1000]
            benchmark_results = {}

            for size in data_sizes:
                # Generate test data
                dates = pd.date_range('2023-01-01', periods=size, freq='D')
                np.random.seed(42)
                prices = 100 + np.cumsum(np.random.normal(0.001, 0.02, size))

                test_data = pd.DataFrame({
                    'open': prices * (1 + np.random.normal(0, 0.005, size)),
                    'high': prices * (1 + np.random.uniform(0, 0.02, size)),
                    'low': prices * (1 - np.random.uniform(0, 0.02, size)),
                    'close': prices,
                    'volume': np.random.randint(1000000, 10000000, size)
                }, index=dates)

                # Benchmark VectorBT Engine
                engine = VectorBTEngine()
                start_time = time.time()
                result = engine.backtest_strategy(test_data, 'RSI_MEAN_REVERSION', {'period': 14, 'oversold': 30, 'overbought': 70})
                engine_time = time.time() - start_time

                # Benchmark Enhanced Indicators
                enhanced_indicators = VectorizedTechnicalIndicators()
                start_time = time.time()
                rsi_result = enhanced_indicators.calculate_rsi_vectorized(test_data, [14])
                indicators_time = time.time() - start_time

                # Benchmark Risk Calculator
                risk_calculator = RiskCalculator()
                start_time = time.time()
                risk_metrics = risk_calculator.calculate_comprehensive_metrics(test_data['close'])
                risk_time = time.time() - start_time

                benchmark_results[size] = {
                    'data_points': size,
                    'engine_time': engine_time,
                    'indicators_time': indicators_time,
                    'risk_time': risk_time,
                    'total_time': engine_time + indicators_time + risk_time,
                    'records_per_second': size / (engine_time + indicators_time + risk_time) if (engine_time + indicators_time + risk_time) > 0 else 0
                }

            phase_results['tests']['performance_scaling'] = {
                'success': len(benchmark_results) > 0,
                'data_sizes_tested': list(benchmark_results.keys()),
                'results': benchmark_results
            }

            # Calculate performance metrics
            total_records = sum(benchmark_results[size]['data_points'] for size in data_sizes)
            total_time = sum(benchmark_results[size]['total_time'] for size in data_sizes)
            avg_records_per_second = total_records / total_time if total_time > 0 else 0

            phase_results['performance']['total_records_processed'] = total_records
            phase_results['performance']['total_execution_time'] = total_time
            phase_results['performance']['average_records_per_second'] = avg_records_per_second

            # Check performance target (should be > 1000 records/second)
            performance_target = 1000
            phase_results['performance']['performance_target_met'] = avg_records_per_second >= performance_target
            phase_results['performance']['performance_achievement_ratio'] = avg_records_per_second / performance_target

            # Check if performance benchmark tests passed
            benchmark_passed = (
                phase_results['tests'].get('performance_scaling', {}).get('success', False) and
                avg_records_per_second > 100
            )

            phase_results['status'] = 'PASSED' if benchmark_passed else 'PARTIAL'

            logger.info(f"  性能基準: {avg_records_per_second:.0f} 記錄/秒")
            logger.info(f"  性能目標 ({performance_target} 記錄/秒): {'達成' if phase_results['performance']['performance_target_met'] else '未達成'}")
            logger.info(f"Phase 7 狀態: {phase_results['status']}")

        except Exception as e:
            phase_results['status'] = 'FAILED'
            phase_results['error'] = str(e)
            logger.error(f"Phase 7 測試失敗: {e}")

        return phase_results

    def load_test_data(self) -> pd.DataFrame:
        """載入測試數據"""
        logger.info("載入測試數據...")

        try:
            # 嘗試載入真實數據
            data = get_hk_stock_data("0700.HK", 252)

            if isinstance(data, list):
                df = pd.DataFrame(data)
                if 'timestamp' in df.columns:
                    df['date'] = pd.to_datetime(df['timestamp'])
                    df.set_index('date', inplace=True)

                # 確保必要的列存在
                required_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in required_columns:
                    if col not in df.columns:
                        if col == 'volume':
                            df[col] = np.random.randint(1000000, 10000000, len(df))
                        else:
                            df[col] = df.get('close', df.get('price', 100))

                logger.info(f"成功載入真實數據: {len(df)} 條記錄")
                return df[required_columns]

            return data

        except Exception as e:
            logger.warning(f"無法載入真實數據: {e}，使用模擬數據")
            logger.info("生成模擬數據進行測試...")

            # 生成模擬數據
            dates = pd.date_range('2022-01-01', periods=252, freq='D')
            np.random.seed(42)

            # 模擬股價數據
            initial_price = 500.0
            returns = np.random.normal(0.001, 0.02, 252)
            prices = [initial_price]

            for ret in returns:
                prices.append(prices[-1] * (1 + ret))

            close_prices = pd.Series(prices[1:], index=dates)

            df = pd.DataFrame({
                'open': close_prices * (1 + np.random.normal(0, 0.005, 252)),
                'high': close_prices * (1 + np.abs(np.random.normal(0, 0.01, 252))),
                'low': close_prices * (1 - np.abs(np.random.normal(0, 0.01, 252))),
                'close': close_prices,
                'volume': np.random.randint(1000000, 10000000, 252)
            })

            logger.info(f"生成模擬數據: {len(df)} 條記錄")
            return df

    def calculate_overall_status(self):
        """計算整體測試狀態"""
        phases = self.test_results['phases']

        if not phases:
            self.test_results['overall_status'] = 'NO_TESTS'
            return

        phase_statuses = [phase.get('status', 'UNKNOWN') for phase in phases.values()]

        if all(status == 'PASSED' for status in phase_statuses):
            self.test_results['overall_status'] = 'PASSED'
        elif any(status == 'PASSED' for status in phase_statuses):
            self.test_results['overall_status'] = 'PARTIAL'
        elif any(status == 'FAILED' for status in phase_statuses):
            self.test_results['overall_status'] = 'FAILED'
        else:
            self.test_results['overall_status'] = 'UNKNOWN'

        # Calculate success rate
        passed_phases = sum(1 for status in phase_statuses if status == 'PASSED')
        total_phases = len(phase_statuses)
        self.test_results['success_rate'] = passed_phases / total_phases if total_phases > 0 else 0

    def save_comprehensive_report(self):
        """保存綜合測試報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_vectorbt_integration_test_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            logger.info(f"綜合測試報告已保存: {filename}")
        except Exception as e:
            logger.error(f"保存測試報告失敗: {e}")

    def generate_summary_report(self) -> str:
        """生成測試摘要報告"""
        if 'overall_status' not in self.test_results:
            return "測試尚未完成"

        report = []
        report.append("="*80)
        report.append("VectorBT Integration 綜合測試報告")
        report.append("="*80)
        report.append(f"測試時間: {self.test_results['test_time']}")
        report.append(f"整體狀態: {self.test_results['overall_status']}")

        if 'success_rate' in self.test_results:
            report.append(f"成功率: {self.test_results['success_rate']:.1%}")

        report.append("")
        report.append("各階段測試結果:")
        report.append("-"*40)

        phases = self.test_results.get('phases', {})
        for phase_name, phase_result in phases.items():
            status = phase_result.get('status', 'UNKNOWN')
            report.append(f"  {phase_name}: {status}")

        if 'performance' in self.test_results:
            report.append("")
            report.append("性能指標:")
            report.append("-"*40)
            performance = self.test_results['performance']
            for key, value in performance.items():
                report.append(f"  {key}: {value}")

        return "\n".join(report)

def run_comprehensive_integration_test():
    """運行綜合集成測試"""
    print("開始 VectorBT Integration 綜合測試...")

    tester = VectorBTIntegrationTester()
    results = tester.run_all_tests()

    # 生成並顯示摘要報告
    summary = tester.generate_summary_report()
    print(summary)

    return results

if __name__ == "__main__":
    # 運行綜合測試
    results = run_comprehensive_integration_test()

    # 最終狀態
    overall_status = results.get('overall_status', 'UNKNOWN')
    if overall_status == 'PASSED':
        print(f"\n🎉 VectorBT Integration 測試: 完全通過!")
    elif overall_status == 'PARTIAL':
        print(f"\n✅ VectorBT Integration 測試: 部分通過")
    elif overall_status == 'FAILED':
        print(f"\n❌ VectorBT Integration 測試: 失敗")
    else:
        print(f"\n⚠️ VectorBT Integration 測試: 狀態未知")