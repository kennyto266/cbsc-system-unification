"""
CBSC Focused Unit Tests
CBSC核心單元測試

Focused unit tests that work with actual CBSC model structure.
Tests core functionality without complex dependencies.
"""

import sys
import unittest
import time
from pathlib import Path
from datetime import datetime, date

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

class TestCBSCCore(unittest.TestCase):
    """Test Core CBSC Functionality"""

    def test_cbsc_contract_creation(self):
        """Test CBSC contract creation"""
        print("Testing CBSC contract creation...")

        from models.cbsc_models import create_sample_cbsc_contract

        # Create sample contract
        contract = create_sample_cbsc_contract()

        # Validate basic properties
        self.assertIsNotNone(contract.ticker)
        self.assertIsNotNone(contract.underlying_ticker)
        self.assertGreater(contract.call_price, 0)
        self.assertGreater(contract.leverage_ratio, 1)
        self.assertIsNotNone(contract.cbsc_type)

        print(f"OK: Created contract {contract.ticker} with leverage {contract.leverage_ratio}x")
        return True

    def test_distance_to_call_calculation(self):
        """Test distance to call price calculation"""
        print("Testing distance to call calculation...")

        from models.cbsc_models import create_sample_cbsc_contract

        contract = create_sample_cbsc_contract()
        call_price = contract.call_price

        # Test price above call price (safe zone)
        above_price = call_price * 1.1  # 10% above call
        distance = contract.calculate_distance_to_call(above_price)
        self.assertLess(distance, 0)  # Should be negative (above call price)
        self.assertAlmostEqual(distance, -0.0909, places=2)  # Should be ~-9.1%

        # Test price below call price (danger zone)
        below_price = call_price * 0.9  # 10% below call
        distance = contract.calculate_distance_to_call(below_price)
        self.assertGreater(distance, 0)  # Should be positive (below call price)
        self.assertAlmostEqual(distance, 0.1111, places=2)  # Should be ~11.1%

        # Test exactly at call price
        at_call_distance = contract.calculate_distance_to_call(call_price)
        self.assertEqual(at_call_distance, 0.0)

        print(f"OK: Distance calculations working correctly")
        return True

    def test_time_decay_calculation(self):
        """Test time decay factor calculation"""
        print("Testing time decay calculation...")

        from models.cbsc_models import create_sample_cbsc_contract

        contract = create_sample_cbsc_contract()

        # Test at issue date (should be close to 1.0)
        issue_decay = contract.calculate_time_decay_factor(contract.issue_date)
        self.assertAlmostEqual(issue_decay, 1.0, places=1)

        # Test at maturity date (should be close to 0.0)
        maturity_decay = contract.calculate_time_decay_factor(contract.maturity_date)
        self.assertLess(maturity_decay, 0.1)

        # Test middle date (should be between 0 and 1)
        mid_date = contract.issue_date + (contract.maturity_date - contract.issue_date) / 2
        mid_decay = contract.calculate_time_decay_factor(mid_date)
        self.assertGreater(mid_decay, 0.0)
        self.assertLess(mid_decay, 1.0)

        print(f"OK: Time decay calculations working correctly")
        return True

    def test_warrant_sentiment_model(self):
        """Test WarrantSentiment model with proper fields"""
        print("Testing WarrantSentiment model...")

        from models.cbsc_models import WarrantSentiment, SentimentLevel, SignalType

        # Create sentiment data with all required fields
        sentiment = WarrantSentiment(
            date=datetime(2024, 6, 1),
            afternoon_close=270.5,
            bull_ratio=0.6,
            bull_bear_ratio=1.5,
            bull_turnover_hkd=1000000,
            bear_turnover_hkd=666667,
            signal=SignalType.BUY_BULL,
            sentiment_level=SentimentLevel.MOD_BULL
        )

        # Validate calculated fields
        self.assertEqual(sentiment.total_turnover, 1666667)  # Sum of bull + bear
        self.assertGreater(sentiment.sentiment_strength, 0)  # Bullish sentiment
        self.assertEqual(sentiment.signal, SignalType.BUY_BULL)

        print(f"OK: Sentiment model working - strength: {sentiment.sentiment_strength:.3f}")
        return True

    def test_extreme_sentiment_detection(self):
        """Test extreme sentiment detection"""
        print("Testing extreme sentiment detection...")

        from models.cbsc_models import WarrantSentiment, SentimentLevel, SignalType

        # Test extreme bullish
        extreme_bull = WarrantSentiment(
            date=datetime(2024, 6, 1),
            afternoon_close=270.5,
            bull_ratio=0.9,  # Very high bull ratio
            bull_bear_ratio=9.0,  # Very high bull/bear ratio
            bull_turnover_hkd=9000000,
            bear_turnover_hkd=1000000,
            signal=SignalType.BUY_BULL,
            sentiment_level=SentimentLevel.EXTREME_BULL
        )

        # Test extreme bearish
        extreme_bear = WarrantSentiment(
            date=datetime(2024, 6, 1),
            afternoon_close=270.5,
            bull_ratio=0.1,  # Very low bull ratio
            bull_bear_ratio=0.11,  # Very low bull/bear ratio
            bull_turnover_hkd=1000000,
            bear_turnover_hkd=9000000,
            signal=SignalType.SELL_BEAR,
            sentiment_level=SentimentLevel.EXTREME_BEAR
        )

        # Test moderate sentiment
        moderate = WarrantSentiment(
            date=datetime(2024, 6, 1),
            afternoon_close=270.5,
            bull_ratio=0.55,  # Moderate bull ratio
            bull_bear_ratio=1.22,
            bull_turnover_hkd=1100000,
            bear_turnover_hkd=900000,
            signal=SignalType.BUY_BULL,
            sentiment_level=SentimentLevel.MOD_BULL
        )

        # Check extreme detection
        self.assertTrue(extreme_bull.get_extreme_signal())
        self.assertTrue(extreme_bear.get_extreme_signal())
        self.assertFalse(moderate.get_extreme_signal())

        print(f"OK: Extreme sentiment detection working correctly")
        return True

class TestCBSCPerformance(unittest.TestCase):
    """Test CBSC Performance"""

    def test_contract_creation_performance(self):
        """Test contract creation performance"""
        print("Testing contract creation performance...")

        from models.cbsc_models import create_sample_cbsc_contract

        # Measure time to create 1000 contracts
        start_time = time.time()
        contracts = []

        for i in range(1000):
            contract = create_sample_cbsc_contract()
            contracts.append(contract)

        creation_time = time.time() - start_time

        # Should complete within 1 second
        self.assertLess(creation_time, 1.0)
        self.assertEqual(len(contracts), 1000)

        avg_time = creation_time / 1000 * 1000  # Convert to milliseconds
        print(f"OK: Created 1000 contracts in {creation_time:.3f}s ({avg_time:.3f}ms per contract)")
        return True

    def test_risk_calculation_performance(self):
        """Test basic risk calculation performance"""
        print("Testing basic risk calculation performance...")

        from models.cbsc_models import create_sample_cbsc_contract

        # Create test contracts
        contracts = [create_sample_cbsc_contract() for _ in range(100)]

        # Measure basic distance calculation time (core risk metric)
        start_time = time.time()

        for contract in contracts:
            distance = contract.calculate_distance_to_call(260.0)
            decay_factor = contract.calculate_time_decay_factor(date.today())

        risk_time = time.time() - start_time

        # Should complete within 0.5 seconds for 100 contracts
        self.assertLess(risk_time, 0.5)

        avg_time = risk_time / 100 * 1000  # Convert to milliseconds
        print(f"OK: Calculated basic risk for 100 contracts in {risk_time:.3f}s ({avg_time:.3f}ms per contract)")
        return True

    def test_sentiment_processing_performance(self):
        """Test sentiment data processing performance"""
        print("Testing sentiment processing performance...")

        from models.cbsc_models import WarrantSentiment, SentimentLevel, SignalType

        # Create large dataset
        start_time = time.time()
        sentiment_data = []

        for i in range(1000):
            sentiment = WarrantSentiment(
                date=datetime(2024, 1, 1) + timedelta(days=i),
                afternoon_close=270.0 + (i % 20),
                bull_ratio=0.5 + (i % 40) * 0.01,
                bull_bear_ratio=1.0 + (i % 20) * 0.1,
                bull_turnover_hkd=1000000 + (i % 500000),
                bear_turnover_hkd=1000000 - (i % 500000),
                signal=SignalType.BUY_BULL if i % 3 == 0 else (SignalType.SELL_BEAR if i % 3 == 1 else SignalType.HOLD),
                sentiment_level=SentimentLevel.MOD_BULL if i % 4 == 0 else (SentimentLevel.MOD_BEAR if i % 4 == 1 else SentimentLevel.NEUTRAL)
            )
            sentiment_data.append(sentiment)

        creation_time = time.time() - start_time

        # Test processing time
        start_time = time.time()
        extreme_count = sum(1 for record in sentiment_data if record.get_extreme_signal())
        processing_time = time.time() - start_time

        total_time = creation_time + processing_time

        # Should complete within 1 second
        self.assertLess(total_time, 1.0)

        print(f"OK: Processed 1000 sentiment records in {total_time:.3f}s ({extreme_count} extreme)")
        return True

def run_focused_tests():
    """Run focused CBSC unit tests"""
    print("=" * 60)
    print("CBSC Focused Unit Test Suite")
    print("=" * 60)

    # Create test suite
    test_classes = [
        TestCBSCCore,
        TestCBSCPerformance
    ]

    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors

    print(f"Total tests run: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    print(f"Success rate: {(passed/total_tests)*100:.1f}%")

    if failures == 0 and errors == 0:
        print("\nSUCCESS: All CBSC focused unit tests passed!")
        print("Phase 1 implementation is COMPLETE and ready!")
        return True
    else:
        print(f"\nWARNING: {failures + errors} tests failed.")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")

        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")

        return False

if __name__ == "__main__":
    # Import timedelta for performance tests
    from datetime import timedelta

    success = run_focused_tests()
    sys.exit(0 if success else 1)