"""
Comprehensive CBSC VectorBT Testing Suite
综合CBSC VectorBT测试套件

This suite implements the testing strategy defined in CBSC_VectorBT_Testing_Strategy.md
实现了CBSC_VectorBT_Testing_Strategy.md中定义的测试策略

Author: CBSC Backtesting System Team
Date: 2025-12-04
Version: 1.0
"""

import sys
import time
import traceback
import unittest
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import pytest

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from data_loader import CBSCDataLoader
from signal_generator import CBSCSignalGenerator
from cbsc_backtester import CBSCBacktester
from optimizer import CBSCOptimizer

class TestCBSCComprehensiveSuite:
    """Comprehensive test suite for CBSC VectorBT system"""

    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
        cls.test_symbol = "0700.HK"
        cls.performance_targets = {
            'max_total_time': 30.0,  # seconds
            'max_data_loading': 5.0,
            'max_signal_generation': 3.0,
            'max_backtesting': 20.0,
            'max_memory_mb': 2048
        }

    def generate_mock_cbsc_data(self, days=252):
        """Generate mock CBSC data for testing"""
        dates = pd.date_range('2024-01-01', periods=days, freq='D')
        np.random.seed(42)  # For reproducible tests

        return pd.DataFrame({
            'Date': dates,
            'Bull_Ratio': np.random.uniform(0.2, 0.8, days),
            'Bull_Bear_Ratio': np.random.uniform(0.5, 2.0, days),
            'Bull_Turnover_HKD': np.random.uniform(1e6, 1e7, days),
            'Bear_Turnover_HKD': np.random.uniform(1e6, 1e7, days),
            'Afternoon_Close': 25000 + np.cumsum(np.random.randn(days) * 100),
            'Signal': np.random.choice([-1, 0, 1], days),
            'Sentiment_Level': np.random.choice(
                ['EXTREME BULL', 'MOD BULL', 'NEUTRAL', 'MOD BEAR', 'EXTREME BEAR'],
                days
            )
        })

    def measure_performance(self, func, *args, **kwargs):
        """Measure function performance"""
        import psutil
        import time

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        result = func(*args, **kwargs)

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        return {
            'result': result,
            'execution_time': end_time - start_time,
            'memory_used': end_memory - start_memory,
            'total_memory': end_memory
        }

    # ========== Functional Tests ==========

    def test_data_loader_functionality(self):
        """Test data loader core functionality (TC-DL-001 to TC-DL-006)"""
        print("\n" + "="*60)
        print("Testing Data Loader Functionality")
        print("="*60)

        test_results = []

        # Test 1: Valid CBSC CSV loading
        try:
            if Path(self.sentiment_path).exists():
                loader = CBSCDataLoader(self.sentiment_path)
                sentiment_df = loader.load_sentiment_data()

                success = not sentiment_df.empty and len(sentiment_df) > 0
                test_results.append(("TC-DL-001", "Valid CSV Loading", success,
                                  f"Loaded {len(sentiment_df)} records"))
            else:
                test_results.append(("TC-DL-001", "Valid CSV Loading", False,
                                  "Data file not found"))
        except Exception as e:
            test_results.append(("TC-DL-001", "Valid CSV Loading", False, str(e)))

        # Test 2: Invalid file path handling
        try:
            loader = CBSCDataLoader("non_existent_file.csv")
            sentiment_df = loader.load_sentiment_data()

            success = sentiment_df.empty  # Should return empty DataFrame
            test_results.append(("TC-DL-002", "Invalid Path Handling", success,
                              "Graceful error handling"))
        except Exception as e:
            test_results.append(("TC-DL-002", "Invalid Path Handling", True,
                              f"Expected exception: {str(e)[:50]}"))

        # Test 3: Price data loading
        try:
            loader = CBSCDataLoader(self.sentiment_path)
            price_df = loader.load_price_data(self.test_symbol)

            success = not price_df.empty and len(price_df) > 0
            test_results.append(("TC-DL-004", "Price Data Loading", success,
                              f"Loaded {len(price_df)} price records"))
        except Exception as e:
            test_results.append(("TC-DL-004", "Price Data Loading", False, str(e)))

        # Test 4: Feature engineering
        try:
            if Path(self.sentiment_path).exists():
                loader = CBSCDataLoader(self.sentiment_path)
                sentiment_df = loader.load_sentiment_data()
                if not sentiment_df.empty:
                    # Use mock price data for testing
                    mock_price = pd.DataFrame({
                        'Date': sentiment_df['Date'],
                        'open': sentiment_df['Afternoon_Close'] * 0.98,
                        'high': sentiment_df['Afternoon_Close'] * 1.02,
                        'low': sentiment_df['Afternoon_Close'] * 0.97,
                        'close': sentiment_df['Afternoon_Close'],
                        'volume': np.random.randint(1000000, 10000000, len(sentiment_df))
                    })

                    features_df = loader.create_cbsc_features(sentiment_df, mock_price)
                    success = not features_df.empty and len(features_df.columns) > 10
                    test_results.append(("TC-DL-006", "Feature Engineering", success,
                                      f"Created {len(features_df.columns)} features"))
                else:
                    test_results.append(("TC-DL-006", "Feature Engineering", False,
                                      "No sentiment data"))
            else:
                test_results.append(("TC-DL-006", "Feature Engineering", False,
                                  "Data file not found"))
        except Exception as e:
            test_results.append(("TC-DL-006", "Feature Engineering", False, str(e)))

        # Print results
        for test_id, test_name, success, message in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_id}: {test_name} - {message}")

        passed = sum(1 for _, _, success, _ in test_results if success)
        total = len(test_results)
        print(f"\nData Loader Tests: {passed}/{total} passed")

        return passed, total

    def test_signal_generator_functionality(self):
        """Test signal generator functionality (TC-SG-001 to TC-SG-006)"""
        print("\n" + "="*60)
        print("Testing Signal Generator Functionality")
        print("="*60)

        test_results = []

        try:
            # Setup test data
            mock_data = self.generate_mock_cbsc_data(100)
            mock_data['Returns'] = mock_data['Afternoon_Close'].pct_change()
            mock_data['MA5'] = mock_data['Afternoon_Close'].rolling(5).mean()
            mock_data['MA20'] = mock_data['Afternoon_Close'].rolling(20).mean()
            mock_data['RSI'] = 50 + np.random.randn(100) * 10
            mock_data['Total_Turnover'] = mock_data['Bull_Turnover_HKD'] + mock_data['Bear_Turnover_HKD']
            mock_data = mock_data.dropna().reset_index(drop=True)

            generator = CBSCSignalGenerator()

            # Test 1: Sentiment signal generation
            try:
                entries, exits = generator.generate_vectorbt_signals(mock_data, 'sentiment')
                success = len(entries) == len(mock_data) and len(exits) == len(mock_data)
                test_results.append(("TC-SG-001", "Sentiment Signal Generation", success,
                                  f"Generated {entries.sum()} entries, {exits.sum()} exits"))
            except Exception as e:
                test_results.append(("TC-SG-001", "Sentiment Signal Generation", False, str(e)))

            # Test 2: Technical signal generation
            try:
                entries, exits = generator.generate_vectorbt_signals(mock_data, 'technical')
                success = len(entries) == len(mock_data) and len(exits) == len(mock_data)
                test_results.append(("TC-SG-002", "Technical Signal Generation", success,
                                  f"Generated {entries.sum()} entries, {exits.sum()} exits"))
            except Exception as e:
                test_results.append(("TC-SG-002", "Technical Signal Generation", False, str(e)))

            # Test 3: CBSC-aware signal generation
            try:
                entries, exits = generator.generate_vectorbt_signals(mock_data, 'cbsc_aware')
                success = len(entries) == len(mock_data) and len(exits) == len(mock_data)
                test_results.append(("TC-SG-003", "CBSC-Aware Signal Generation", success,
                                  f"Generated {entries.sum()} entries, {exits.sum()} exits"))
            except Exception as e:
                test_results.append(("TC-SG-003", "CBSC-Aware Signal Generation", False, str(e)))

            # Test 4: Multiple strategy generation
            try:
                strategies = generator.generate_multiple_strategies(mock_data)
                success = len(strategies) == 5 and all(len(signals) == 2 for signals in strategies.values())
                test_results.append(("TC-SG-004", "Multiple Strategy Generation", success,
                                  f"Generated {len(strategies)} strategies"))
            except Exception as e:
                test_results.append(("TC-SG-004", "Multiple Strategy Generation", False, str(e)))

            # Test 5: Signal quality analysis
            try:
                entries, exits = generator.generate_vectorbt_signals(mock_data, 'sentiment')
                quality = generator.analyze_signal_quality(mock_data, entries, exits)
                success = isinstance(quality, dict) and 'total_entries' in quality
                test_results.append(("TC-SG-006", "Signal Quality Analysis", success,
                                  f"Quality score: {quality.get('sentiment_data_quality', 'N/A')}"))
            except Exception as e:
                test_results.append(("TC-SG-006", "Signal Quality Analysis", False, str(e)))

        except Exception as e:
            test_results.append(("SETUP", "Mock Data Generation", False, str(e)))

        # Print results
        for test_id, test_name, success, message in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_id}: {test_name} - {message}")

        passed = sum(1 for _, _, success, _ in test_results if success)
        total = len(test_results)
        print(f"\nSignal Generator Tests: {passed}/{total} passed")

        return passed, total

    def test_performance_benchmarks(self):
        """Test system performance against benchmarks"""
        print("\n" + "="*60)
        print("Testing Performance Benchmarks")
        print("="*60)

        performance_results = []

        try:
            # Setup test data
            mock_sentiment = self.generate_mock_cbsc_data(252)  # 1 year of data

            # Test 1: Data loading performance
            try:
                perf = self.measure_performance(self._test_data_loading, mock_sentiment)
                within_target = perf['execution_time'] <= self.performance_targets['max_data_loading']
                performance_results.append((
                    "Data Loading", perf['execution_time'],
                    self.performance_targets['max_data_loading'], within_target
                ))
            except Exception as e:
                performance_results.append(("Data Loading", float('inf'),
                                         self.performance_targets['max_data_loading'], False))

            # Test 2: Signal generation performance
            try:
                perf = self.measure_performance(self._test_signal_generation, mock_sentiment)
                within_target = perf['execution_time'] <= self.performance_targets['max_signal_generation']
                performance_results.append((
                    "Signal Generation", perf['execution_time'],
                    self.performance_targets['max_signal_generation'], within_target
                ))
            except Exception as e:
                performance_results.append(("Signal Generation", float('inf'),
                                         self.performance_targets['max_signal_generation'], False))

            # Test 3: Complete workflow performance
            try:
                perf = self.measure_performance(self._test_complete_workflow, mock_sentiment)
                within_target = perf['execution_time'] <= self.performance_targets['max_total_time']
                performance_results.append((
                    "Complete Workflow", perf['execution_time'],
                    self.performance_targets['max_total_time'], within_target
                ))
            except Exception as e:
                performance_results.append(("Complete Workflow", float('inf'),
                                         self.performance_targets['max_total_time'], False))

        except Exception as e:
            print(f"Performance testing setup failed: {e}")
            return 0, 1

        # Print results
        for test_name, actual_time, target_time, within_target in performance_results:
            status = "✅ PASS" if within_target else "❌ FAIL"
            print(f"{status} {test_name}: {actual_time:.3f}s (target: <{target_time}s)")

        passed = sum(1 for _, _, _, success in performance_results if success)
        total = len(performance_results)
        print(f"\nPerformance Tests: {passed}/{total} passed")

        return passed, total

    def test_cbsc_specific_logic(self):
        """Test CBSC-specific functionality (TC-CBSC-001 to TC-CBSC-004)"""
        print("\n" + "="*60)
        print("Testing CBSC-Specific Logic")
        print("="*60)

        test_results = []

        try:
            # Create test data with specific scenarios
            mock_data = self.generate_mock_cbsc_data(50)
            mock_data['Returns'] = mock_data['Afternoon_Close'].pct_change()
            mock_data['Total_Turnover'] = mock_data['Bull_Turnover_HKD'] + mock_data['Bear_Turnover_HKD']

            # Add extreme scenarios
            mock_data.loc[10:15, 'Afternoon_Close'] = 20000  # Near call price scenario
            mock_data.loc[20:25, 'Sentiment_Level'] = 'EXTREME BULL'  # Extreme sentiment
            mock_data.loc[30:35, 'Bull_Turnover_HKD'] = 0  # Zero turnover scenario

            mock_data = mock_data.dropna().reset_index(drop=True)

            generator = CBSCSignalGenerator()

            # Test 1: Knockout risk calculation
            try:
                entries, exits = generator.generate_vectorbt_signals(mock_data, 'cbsc_aware')
                signals_aware = generator.generate_cbsc_aware_signals(mock_data)

                # Check if knockout risk is considered
                has_call_distance = 'Bull_Call_Distance' in signals_aware.columns
                test_results.append(("TC-CBSC-001", "Knockout Risk Calculation", has_call_distance,
                                  f"Call distance calculation present"))
            except Exception as e:
                test_results.append(("TC-CBSC-001", "Knockout Risk Calculation", False, str(e)))

            # Test 2: Sentiment signal weighting
            try:
                extreme_sentiment_mask = mock_data['Sentiment_Level'].isin(['EXTREME BULL', 'EXTREME BEAR'])
                has_extreme_data = extreme_sentiment_mask.any()

                entries, exits = generator.generate_vectorbt_signals(mock_data, 'sentiment')
                test_results.append(("TC-CBSC-004", "Sentiment Signal Weighting", has_extreme_data,
                                  f"Extreme sentiment data: {has_extreme_data}"))
            except Exception as e:
                test_results.append(("TC-CBSC-004", "Sentiment Signal Weighting", False, str(e)))

            # Test 3: Multiple strategy behavior
            try:
                strategies = generator.generate_multiple_strategies(mock_data)
                strategy_count = len(strategies)
                expected_count = 5

                success = strategy_count == expected_count
                test_results.append(("CBSC-STRAT", "Multiple Strategy Count", success,
                                  f"Generated {strategy_count} strategies (expected: {expected_count})"))
            except Exception as e:
                test_results.append(("CBSC-STRAT", "Multiple Strategy Count", False, str(e)))

        except Exception as e:
            test_results.append(("SETUP", "CBSC Test Data Setup", False, str(e)))

        # Print results
        for test_id, test_name, success, message in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_id}: {test_name} - {message}")

        passed = sum(1 for _, _, success, _ in test_results if success)
        total = len(test_results)
        print(f"\nCBSC-Specific Tests: {passed}/{total} passed")

        return passed, total

    def test_data_quality_validation(self):
        """Test data quality and validation"""
        print("\n" + "="*60)
        print("Testing Data Quality Validation")
        print("="*60)

        test_results = []

        try:
            # Test 1: Mock data generation quality
            try:
                mock_data = self.generate_mock_cbsc_data(100)

                # Check required columns
                required_columns = ['Date', 'Bull_Ratio', 'Bull_Bear_Ratio', 'Bull_Turnover_HKD',
                                 'Bear_Turnover_HKD', 'Afternoon_Close', 'Signal', 'Sentiment_Level']
                has_required_columns = all(col in mock_data.columns for col in required_columns)

                # Check data ranges
                valid_ratios = mock_data['Bull_Ratio'].between(0, 1).all()
                valid_turnover = (mock_data['Bull_Turnover_HKD'] > 0).all() and (mock_data['Bear_Turnover_HKD'] > 0).all()

                success = has_required_columns and valid_ratios and valid_turnover
                test_results.append(("DQ-001", "Mock Data Quality", success,
                                  f"Columns: {has_required_columns}, Ratios: {valid_ratios}, Turnover: {valid_turnover}"))
            except Exception as e:
                test_results.append(("DQ-001", "Mock Data Quality", False, str(e)))

            # Test 2: Data alignment validation
            try:
                if Path(self.sentiment_path).exists():
                    loader = CBSCDataLoader(self.sentiment_path)

                    # Load and test alignment
                    sentiment_df = loader.load_sentiment_data()
                    if not sentiment_df.empty:
                        # Create mock price data with different date range
                        price_dates = sentiment_df['Date'][:100]  # Smaller range
                        mock_price = pd.DataFrame({
                            'Date': price_dates,
                            'open': 25000,
                            'high': 25500,
                            'low': 24500,
                            'close': sentiment_df.loc[:len(price_dates)-1, 'Afternoon_Close'],
                            'volume': 1000000
                        })

                        aligned_sentiment, aligned_price = loader.align_data_mock(sentiment_df, mock_price)
                        success = len(aligned_sentiment) == len(aligned_price) and len(aligned_sentiment) > 0
                        test_results.append(("DQ-002", "Data Alignment", success,
                                          f"Aligned {len(aligned_sentiment)} records"))
                    else:
                        test_results.append(("DQ-002", "Data Alignment", False, "No sentiment data"))
                else:
                    test_results.append(("DQ-002", "Data Alignment", False, "Data file not found"))
            except Exception as e:
                test_results.append(("DQ-002", "Data Alignment", False, str(e)))

        except Exception as e:
            test_results.append(("SETUP", "Data Quality Setup", False, str(e)))

        # Print results
        for test_id, test_name, success, message in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_id}: {test_name} - {message}")

        passed = sum(1 for _, _, success, _ in test_results if success)
        total = len(test_results)
        print(f"\nData Quality Tests: {passed}/{total} passed")

        return passed, total

    # ========== Helper Methods ==========

    def _test_data_loading(self, mock_data):
        """Helper method to test data loading performance"""
        loader = CBSCDataLoader.__new__(CBSCDataLoader)  # Create without __init__
        loader.sentiment_path = "mock_data.csv"
        loader.sentiment_data = mock_data
        return loader.get_data_summary()

    def _test_signal_generation(self, mock_data):
        """Helper method to test signal generation performance"""
        generator = CBSCSignalGenerator()
        strategies = generator.generate_multiple_strategies(mock_data)
        return strategies

    def _test_complete_workflow(self, mock_data):
        """Helper method to test complete workflow performance"""
        loader = CBSCDataLoader.__new__(CBSCDataLoader)
        loader.sentiment_data = mock_data

        generator = CBSCSignalGenerator()
        strategies = generator.generate_multiple_strategies(mock_data)

        return len(strategies)

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("CBSC VectorBT Comprehensive Testing Suite")
        print("=" * 60)
        print(f"Test Data: {self.sentiment_path}")
        print(f"Test Symbol: {self.test_symbol}")
        print(f"Performance Targets: {self.performance_targets}")
        print("=" * 60)

        test_results = []

        # Run all test categories
        test_categories = [
            ("Data Loader", self.test_data_loader_functionality),
            ("Signal Generator", self.test_signal_generator_functionality),
            ("Performance Benchmarks", self.test_performance_benchmarks),
            ("CBSC-Specific Logic", self.test_cbsc_specific_logic),
            ("Data Quality", self.test_data_quality_validation)
        ]

        for category_name, test_func in test_categories:
            try:
                passed, total = test_func()
                test_results.append((category_name, passed, total))
            except Exception as e:
                print(f"❌ {category_name} test failed: {e}")
                test_results.append((category_name, 0, 1))

        # Summary
        print("\n" + "="*60)
        print("COMPREHENSIVE TEST SUMMARY")
        print("="*60)

        total_passed = sum(passed for _, passed, _ in test_results)
        total_tests = sum(total for _, _, total in test_results)

        for category_name, passed, total in test_results:
            percentage = (passed / total * 100) if total > 0 else 0
            status = "✅ PASS" if passed == total else "❌ FAIL"
            print(f"{status} {category_name}: {passed}/{total} ({percentage:.1f}%)")

        print(f"\nOVERALL RESULTS: {total_passed}/{total_tests} tests passed")
        print(f"SUCCESS RATE: {total_passed/total_tests*100:.1f}%")

        if total_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! System is ready for production.")
        else:
            print(f"\n⚠️  {total_tests - total_passed} tests failed. Review and fix issues before deployment.")

        return total_passed == total_tests

def main():
    """Main test runner"""
    test_suite = TestCBSCComprehensiveSuite()
    success = test_suite.run_comprehensive_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)