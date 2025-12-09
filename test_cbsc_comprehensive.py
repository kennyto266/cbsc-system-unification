"""
Comprehensive CBSC Unit Tests
CBSC完整單元測試

This test suite provides comprehensive unit testing for all CBSC components:
- Data models and validation
- Data adapters and processing
- Risk calculations and management
- Sentiment-technical integration
- Performance and edge cases

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

import sys
import unittest
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

class TestCBSCModels(unittest.TestCase):
    """Test CBSC Data Models"""

    def setUp(self):
        """Set up test fixtures"""
        from models.cbsc_models import CBSCContract, CBSCType, SentimentLevel, SignalType

        self.sample_contract = CBSCContract(
            ticker="12345.HK",
            underlying_ticker="0700.HK",
            cbsc_type=CBSCType.BULL,
            issuer="TEST_ISSUER",
            call_price=250.0,
            strike_price=270.0,
            entitlement_ratio=0.1,
            leverage_ratio=8.0,
            issue_date=date(2024, 1, 1),
            maturity_date=date(2025, 12, 31),
            listing_date=date(2024, 1, 2)
        )

    def test_cbsc_contract_creation(self):
        """Test CBSC contract creation and validation"""
        from models.cbsc_models import CBSCContract, CBSCType

        # Test valid contract creation
        contract = CBSCContract(
            ticker="12346.HK",
            underlying_ticker="0700.HK",
            cbsc_type=CBSCType.BEAR,
            issuer="TEST_ISSUER",
            call_price=300.0,
            strike_price=280.0,
            entitlement_ratio=0.05,
            leverage_ratio=10.0,
            issue_date=date(2024, 1, 1),
            maturity_date=date(2025, 12, 31),
            listing_date=date(2024, 1, 2)
        )

        self.assertEqual(contract.ticker, "12346.HK")
        self.assertEqual(contract.underlying_ticker, "0700.HK")
        self.assertEqual(contract.cbsc_type, CBSCType.BEAR)
        self.assertEqual(contract.call_price, 300.0)
        self.assertEqual(contract.leverage_ratio, 10.0)

    def test_contract_validation(self):
        """Test contract field validation"""
        from models.cbsc_models import CBSCContract, CBSCType
        from pydantic import ValidationError

        # Test invalid call price (negative)
        with self.assertRaises(ValidationError):
            CBSCContract(
                ticker="12347.HK",
                underlying_ticker="0700.HK",
                cbsc_type=CBSCType.BULL,
                issuer="TEST_ISSUER",
                call_price=-50.0,  # Invalid negative call price
                strike_price=270.0,
                entitlement_ratio=0.1,
                leverage_ratio=8.0,
                issue_date=date(2024, 1, 1),
                maturity_date=date(2025, 12, 31),
                listing_date=date(2024, 1, 2)
            )

        # Test invalid leverage ratio (less than 1)
        with self.assertRaises(ValidationError):
            CBSCContract(
                ticker="12348.HK",
                underlying_ticker="0700.HK",
                cbsc_type=CBSCType.BULL,
                issuer="TEST_ISSUER",
                call_price=250.0,
                strike_price=270.0,
                entitlement_ratio=0.1,
                leverage_ratio=0.5,  # Invalid leverage < 1
                issue_date=date(2024, 1, 1),
                maturity_date=date(2025, 12, 31),
                listing_date=date(2024, 1, 2)
            )

    def test_distance_to_call_calculation(self):
        """Test distance to call price calculation"""
        # Test distance when current price is above call price
        distance = self.sample_contract.calculate_distance_to_call(260.0)
        expected_distance = (260.0 - 250.0) / 250.0  # 4%
        self.assertAlmostEqual(distance, expected_distance, places=4)

        # Test distance when current price is below call price (should be negative)
        distance = self.sample_contract.calculate_distance_to_call(240.0)
        expected_distance = (240.0 - 250.0) / 250.0  # -4%
        self.assertAlmostEqual(distance, expected_distance, places=4)

        # Test zero distance
        distance = self.sample_contract.calculate_distance_to_call(250.0)
        self.assertEqual(distance, 0.0)

    def test_time_decay_calculation(self):
        """Test time decay factor calculation"""
        current_date = date(2024, 6, 1)  # Half way through year

        # Should be less than 1 (time decay)
        decay_factor = self.sample_contract.calculate_time_decay_factor(current_date)
        self.assertLess(decay_factor, 1.0)
        self.assertGreater(decay_factor, 0.0)

        # Test at maturity date
        maturity_decay = self.sample_contract.calculate_time_decay_factor(
            self.sample_contract.maturity_date
        )
        self.assertLess(maturity_decay, 0.1)  # Very close to zero

        # Test at issue date
        issue_decay = self.sample_contract.calculate_time_decay_factor(
            self.sample_contract.issue_date
        )
        self.assertAlmostEqual(issue_decay, 1.0, places=1)  # Should be close to 1

    def test_warrant_sentiment_model(self):
        """Test WarrantSentiment model"""
        from models.cbsc_models import WarrantSentiment, SentimentLevel, SignalType

        sentiment = WarrantSentiment(
            date=date(2024, 6, 1),
            bull_turnover=1000000.0,
            bear_turnover=800000.0,
            bull_turnover_ratio=0.55,
            bear_turnover_ratio=0.45,
            sentiment_strength=0.1,
            sentiment_level=SentimentLevel.MOD_BULL,
            signal=SignalType.BUY_BULL,
            total_turnover=1800000.0
        )

        self.assertEqual(sentiment.date, date(2024, 6, 1))
        self.assertEqual(sentiment.bull_turnover, 1000000.0)
        self.assertEqual(sentiment.sentiment_level, SentimentLevel.MOD_BULL)
        self.assertEqual(sentiment.signal, SignalType.BUY_BULL)
        self.assertFalse(sentiment.get_extreme_signal())  # Not extreme

    def test_extreme_sentiment_detection(self):
        """Test extreme sentiment signal detection"""
        from models.cbsc_models import WarrantSentiment, SentimentLevel, SignalType

        # Test extreme bullish
        extreme_bull = WarrantSentiment(
            date=date(2024, 6, 1),
            bull_turnover=2000000.0,
            bear_turnover=200000.0,
            bull_turnover_ratio=0.91,
            bear_turnover_ratio=0.09,
            sentiment_strength=0.82,
            sentiment_level=SentimentLevel.EXTREME_BULL,
            signal=SignalType.BUY_BULL,
            total_turnover=2200000.0
        )

        self.assertTrue(extreme_bull.get_extreme_signal())

        # Test extreme bearish
        extreme_bear = WarrantSentiment(
            date=date(2024, 6, 1),
            bull_turnover=200000.0,
            bear_turnover=2000000.0,
            bull_turnover_ratio=0.09,
            bear_turnover_ratio=0.91,
            sentiment_strength=-0.82,
            sentiment_level=SentimentLevel.EXTREME_BEAR,
            signal=SignalType.SELL_BEAR,
            total_turnover=2200000.0
        )

        self.assertTrue(extreme_bear.get_extreme_signal())

class TestCBSCDataAdapters(unittest.TestCase):
    """Test CBSC Data Adapters"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_csv_path = Path("test_sentiment_data.csv")
        self.create_test_csv()

    def create_test_csv(self):
        """Create test CSV data"""
        test_data = """Date,Bull_Turnover,Bear_Turnover,Bull_Turnover_Ratio,Bear_Turnover_Ratio,Sentiment_Strength,Sentiment_Level,Signal,Total_Turnover
2024-06-01,1000000,800000,0.55,0.45,0.10,MOD_BULL,1,1800000
2024-06-02,1200000,600000,0.67,0.33,0.34,MOD_BULL,1,1800000
2024-06-03,500000,1500000,0.25,0.75,-0.50,MOD_BEAR,-1,2000000
2024-06-04,1800000,300000,0.86,0.14,0.72,EXTREME_BULL,1,2100000
2024-06-05,200000,1800000,0.10,0.90,-0.80,EXTREME_BEAR,-1,2000000"""

        with open(self.test_csv_path, 'w', encoding='utf-8') as f:
            f.write(test_data)

    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_csv_path.exists():
            self.test_csv_path.unlink()

    def test_sentiment_csv_parsing(self):
        """Test sentiment CSV parsing"""
        from models.cbsc_models import parse_warrant_sentiment_csv

        sentiment_data = parse_warrant_sentiment_csv(str(self.test_csv_path))

        # Should parse 5 records
        self.assertEqual(len(sentiment_data), 5)

        # Test first record
        first_record = sentiment_data[0]
        self.assertEqual(first_record.date, date(2024, 6, 1))
        self.assertEqual(first_record.bull_turnover, 1000000.0)
        self.assertEqual(first_record.bear_turnover, 800000.0)
        self.assertAlmostEqual(first_record.sentiment_strength, 0.10, places=2)

        # Test extreme sentiment detection
        extreme_records = [r for r in sentiment_data if r.get_extreme_signal()]
        self.assertEqual(len(extreme_records), 2)  # 2 extreme records

    def test_data_quality_assessment(self):
        """Test data quality assessment"""
        from models.cbsc_models import parse_warrant_sentiment_csv
        from data_adapters.cbsc_adapter import CBSCDataAdapter

        # Create adapter
        adapter = CBSCDataAdapter()

        # Parse test data
        sentiment_data = parse_warrant_sentiment_csv(str(self.test_csv_path))

        # Assess data quality
        quality_report = adapter.assess_data_quality(sentiment_data)

        self.assertIn('total_records', quality_report)
        self.assertIn('date_range', quality_report)
        self.assertIn('extreme_sentiment_count', quality_report)
        self.assertIn('data_completeness', quality_report)

        # Should have 5 total records
        self.assertEqual(quality_report['total_records'], 5)

        # Should have 2 extreme sentiment records
        self.assertEqual(quality_report['extreme_sentiment_count'], 2)

    def test_sentiment_data_filtering(self):
        """Test sentiment data filtering"""
        from models.cbsc_models import parse_warrant_sentiment_csv
        from data_adapters.cbsc_adapter import CBSCDataAdapter

        adapter = CBSCDataAdapter()
        sentiment_data = parse_warrant_sentiment_csv(str(self.test_csv_path))

        # Filter extreme sentiment only
        extreme_only = adapter.filter_sentiment_data(sentiment_data, extreme_only=True)
        self.assertEqual(len(extreme_only), 2)

        # Filter by date range
        start_date = date(2024, 6, 3)
        end_date = date(2024, 6, 5)
        date_filtered = adapter.filter_sentiment_data(
            sentiment_data,
            start_date=start_date,
            end_date=end_date
        )
        self.assertEqual(len(date_filtered), 3)  # June 3-5 inclusive

        # Test that all filtered records are within date range
        for record in date_filtered:
            self.assertGreaterEqual(record.date, start_date)
            self.assertLessEqual(record.date, end_date)

class TestCBSCRiskManagement(unittest.TestCase):
    """Test CBSC Risk Management"""

    def setUp(self):
        """Set up test fixtures"""
        from models.cbsc_models import CBSCContract, CBSCPortfolioPosition, CBSCType

        self.contract = CBSCContract(
            ticker="12345.HK",
            underlying_ticker="0700.HK",
            cbsc_type=CBSCType.BULL,
            issuer="TEST_ISSUER",
            call_price=250.0,
            strike_price=270.0,
            entitlement_ratio=0.1,
            leverage_ratio=8.0,
            issue_date=date(2024, 1, 1),
            maturity_date=date(2025, 12, 31),
            listing_date=date(2024, 1, 2)
        )

        self.position = CBSCPortfolioPosition(
            contract=self.contract,
            quantity=10000,
            entry_price=2.5,
            entry_date=datetime.now(),
            current_price=2.6
        )

    def test_call_risk_calculation(self):
        """Test call risk calculation"""
        from risk_management.cbsc_risk import create_cbsc_risk_manager

        risk_manager = create_cbsc_risk_manager()

        # Test normal price (far from call)
        normal_price = 270.0
        call_risk = risk_manager.calculate_call_risk(self.contract, normal_price)

        self.assertIn('distance_to_call', call_risk)
        self.assertIn('risk_level', call_risk)
        self.assertIn('call_probability', call_risk)
        self.assertGreater(call_risk['distance_to_call'], 0)  # Above call price

        # Test price very close to call price
        near_call_price = 250.5
        near_call_risk = risk_manager.calculate_call_risk(self.contract, near_call_price)

        self.assertLess(near_call_risk['distance_to_call'], normal_price - 250.0)
        self.assertIn(near_call_risk['risk_level'], ['HIGH', 'CRITICAL'])

        # Test price below call price (knocked out)
        below_call_price = 248.0
        knockout_risk = risk_manager.calculate_call_risk(self.contract, below_call_price)

        self.assertLess(knockout_risk['distance_to_call'], 0)
        self.assertEqual(knockout_risk['risk_level'], 'CRITICAL')

    def test_time_decay_risk_calculation(self):
        """Test time decay risk calculation"""
        from risk_management.cbsc_risk import create_cbsc_risk_manager

        risk_manager = create_cbsc_risk_manager()

        # Test early in contract life
        early_date = date(2024, 2, 1)
        early_risk = risk_manager.calculate_time_decay_risk(self.contract, early_date)

        self.assertIn('days_to_maturity', early_risk)
        self.assertIn('time_decay_factor', early_risk)
        self.assertIn('risk_level', early_risk)
        self.assertGreater(early_risk['days_to_maturity'], 300)  # Many days left
        self.assertGreater(early_risk['time_decay_factor'], 0.8)  # Low decay

        # Test late in contract life
        late_date = date(2025, 12, 1)
        late_risk = risk_manager.calculate_time_decay_risk(self.contract, late_date)

        self.assertLess(late_risk['days_to_maturity'], 30)  # Few days left
        self.assertLess(late_risk['time_decay_factor'], 0.2)  # High decay
        self.assertIn(late_risk['risk_level'], ['HIGH', 'CRITICAL'])

    def test_leverage_risk_calculation(self):
        """Test leverage risk calculation"""
        from risk_management.cbsc_risk import create_cbsc_risk_manager

        risk_manager = create_cbsc_risk_manager()

        # Test normal position
        leverage_risk = risk_manager.calculate_leverage_risk(self.position)

        self.assertIn('current_leverage', leverage_risk)
        self.assertIn('leverage_utilization', leverage_risk)
        self.assertIn('risk_level', leverage_risk)
        self.assertAlmostEqual(leverage_risk['current_leverage'], 8.0, places=1)

        # Test high leverage position
        high_leverage_position = CBSCPortfolioPosition(
            contract=self.contract,
            quantity=50000,  # 5x position size
            entry_price=2.5,
            entry_date=datetime.now(),
            current_price=2.4  # Loss position
        )

        high_leverage_risk = risk_manager.calculate_leverage_risk(high_leverage_position)
        self.assertEqual(high_leverage_risk['risk_level'], 'HIGH')

    def test_comprehensive_risk_assessment(self):
        """Test comprehensive risk assessment"""
        from risk_management.cbsc_risk import create_cbsc_risk_manager

        risk_manager = create_cbsc_risk_manager()
        current_date = date.today()

        # Test comprehensive risk calculation
        comprehensive_risk = risk_manager.calculate_comprehensive_risk(
            self.position, current_date
        )

        self.assertIn('overall_risk_score', comprehensive_risk)
        self.assertIn('risk_level', comprehensive_risk)
        self.assertIn('risk_components', comprehensive_risk)
        self.assertIn('recommendation', comprehensive_risk)

        # Check that all risk components are present
        components = comprehensive_risk['risk_components']
        self.assertIn('call_risk', components)
        self.assertIn('time_decay_risk', components)
        self.assertIn('leverage_risk', components)

        # Risk score should be between 0 and 1
        self.assertGreaterEqual(comprehensive_risk['overall_risk_score'], 0)
        self.assertLessEqual(comprehensive_risk['overall_risk_score'], 1)

        # Risk level should be valid
        self.assertIn(comprehensive_risk['risk_level'],
                     ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])

    def test_position_size_validation(self):
        """Test position size validation"""
        from risk_management.cbsc_risk import create_cbsc_risk_manager

        risk_manager = create_cbsc_risk_manager()

        # Test valid position size
        portfolio_value = 1000000  # 1M HKD
        valid_position_size = 50000  # 50K HKD position

        validation = risk_manager.validate_position_size(
            self.contract, valid_position_size, portfolio_value
        )

        self.assertIn('valid', validation)
        self.assertIn('position_ratio', validation)
        self.assertTrue(validation['valid'])
        self.assertLessEqual(validation['position_ratio'], 0.2)  # Should be under 20%

        # Test excessive position size
        excessive_position_size = 300000  # 300K HKD position

        validation = risk_manager.validate_position_size(
            self.contract, excessive_position_size, portfolio_value
        )

        self.assertFalse(validation['valid'])
        self.assertGreater(validation['position_ratio'], 0.2)  # Should exceed 20%

    def test_risk_report_generation(self):
        """Test risk report generation"""
        from risk_management.cbsc_risk import create_cbsc_risk_manager

        risk_manager = create_cbsc_risk_manager()
        current_date = date.today()

        # Generate risk report
        risk_report = risk_manager.generate_risk_report([self.position], current_date)

        self.assertIn('overall_portfolio_risk', risk_report)
        self.assertIn('position_count', risk_report)
        self.assertIn('high_risk_positions', risk_report)
        self.assertIn('risk_summary', risk_report)
        self.assertIn('generated_at', risk_report)

        self.assertEqual(risk_report['position_count'], 1)
        self.assertIn(risk_report['overall_portfolio_risk'],
                     ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])

class TestSentimentTechnicalIntegration(unittest.TestCase):
    """Test Sentiment-Technical Integration"""

    def setUp(self):
        """Set up test fixtures"""
        from models.cbsc_models import WarrantSentiment, SentimentLevel, SignalType

        # Create sample sentiment data
        self.sentiment_data = [
            WarrantSentiment(
                date=date(2024, 6, 1),
                bull_turnover=1000000,
                bear_turnover=800000,
                bull_turnover_ratio=0.55,
                bear_turnover_ratio=0.45,
                sentiment_strength=0.10,
                sentiment_level=SentimentLevel.MOD_BULL,
                signal=SignalType.BUY_BULL,
                total_turnover=1800000
            ),
            WarrantSentiment(
                date=date(2024, 6, 2),
                bull_turnover=1500000,
                bear_turnover=600000,
                bull_turnover_ratio=0.71,
                bear_turnover_ratio=0.29,
                sentiment_strength=0.42,
                sentiment_level=SentimentLevel.MOD_BULL,
                signal=SignalType.BUY_BULL,
                total_turnover=2100000
            )
        ]

        # Create sample price data
        self.price_data = pd.DataFrame({
            'close': [250.0, 255.0, 260.0, 265.0, 270.0],
            'date': pd.date_range('2024-06-01', periods=5)
        })

    def test_sentiment_indicators_calculation(self):
        """Test sentiment indicators calculation"""
        from analysis.sentiment_technical_integration import create_sentiment_integrator

        integrator = create_sentiment_integrator()

        # Calculate sentiment indicators
        indicators = integrator.calculate_sentiment_indicators(self.sentiment_data)

        self.assertIn('sentiment_momentum', indicators)
        self.assertIn('sentiment_trend', indicators)
        self.assertIn('sentiment_volatility', indicators)
        self.assertIn('extreme_sentiment_ratio', indicators)
        self.assertIn('sentiment_strength', indicators)

        # Check data types
        self.assertIsInstance(indicators['sentiment_momentum'], float)
        self.assertIsInstance(indicators['sentiment_trend'], str)
        self.assertIsInstance(indicators['sentiment_volatility'], float)
        self.assertIsInstance(indicators['extreme_sentiment_ratio'], float)

        # Check trend is valid
        self.assertIn(indicators['sentiment_trend'],
                     ['BULLISH', 'BEARISH', 'NEUTRAL'])

    def test_technical_score_calculation(self):
        """Test technical score calculation"""
        from analysis.sentiment_technical_integration import create_sentiment_integrator

        integrator = create_sentiment_integrator()

        # Calculate technical score
        tech_score = integrator.calculate_technical_score(self.price_data)

        self.assertIsInstance(tech_score, float)
        self.assertGreaterEqual(tech_score, -1.0)
        self.assertLessEqual(tech_score, 1.0)

    def test_sentiment_score_calculation(self):
        """Test sentiment score calculation"""
        from analysis.sentiment_technical_integration import create_sentiment_integrator

        integrator = create_sentiment_integrator()

        # Calculate sentiment score
        sent_score = integrator.calculate_sentiment_score(self.sentiment_data)

        self.assertIsInstance(sent_score, float)
        self.assertGreaterEqual(sent_score, -1.0)
        self.assertLessEqual(sent_score, 1.0)

    def test_signal_combination(self):
        """Test signal combination logic"""
        from analysis.sentiment_technical_integration import create_sentiment_integrator

        integrator = create_sentiment_integrator()

        # Test consensus signals (both positive)
        consensus_score = integrator.combine_signals(0.6, 0.7)
        self.assertGreater(consensus_score, 0.6)  # Should be enhanced

        # Test conflicting signals
        conflict_score = integrator.combine_signals(0.6, -0.7)
        self.assertLess(abs(conflict_score), 0.6)  # Should be reduced

        # Test neutral signals
        neutral_score = integrator.combine_signals(0.0, 0.0)
        self.assertAlmostEqual(neutral_score, 0.0, places=2)

    def test_trading_signal_generation(self):
        """Test trading signal generation"""
        from analysis.sentiment_technical_integration import create_sentiment_integrator

        integrator = create_sentiment_integrator()

        # Generate trading signal
        signal = integrator.generate_trading_signal(
            "0700.HK", self.price_data, self.sentiment_data
        )

        # Check signal structure
        self.assertEqual(signal.symbol, "0700.HK")
        self.assertIn(signal.signal_type.name, ['BUY_BULL', 'SELL_BEAR', 'HOLD'])
        self.assertIsInstance(signal.technical_score, float)
        self.assertIsInstance(signal.sentiment_score, float)
        self.assertIsInstance(signal.combined_score, float)
        self.assertIsInstance(signal.confidence, float)
        self.assertIn(signal.recommendation, ['EXECUTE', 'CONSIDER', 'WAIT'])
        self.assertIn(signal.risk_level, ['LOW', 'MEDIUM', 'HIGH'])

    def test_backtest_strategy(self):
        """Test strategy backtesting"""
        from analysis.sentiment_technical_integration import create_sentiment_integrator

        integrator = create_sentiment_integrator()

        # Run backtest
        backtest_results = integrator.backtest_strategy(
            "0700.HK", self.price_data, self.sentiment_data
        )

        # Check results structure
        self.assertIn('total_return', backtest_results)
        self.assertIn('sharpe_ratio', backtest_results)
        self.assertIn('max_drawdown', backtest_results)
        self.assertIn('win_rate', backtest_results)
        self.assertIn('total_trades', backtest_results)
        self.assertIn('signals_count', backtest_results)

        # Check data types
        self.assertIsInstance(backtest_results['total_return'], float)
        self.assertIsInstance(backtest_results['sharpe_ratio'], float)
        self.assertIsInstance(backtest_results['max_drawdown'], float)
        self.assertIsInstance(backtest_results['win_rate'], float)
        self.assertIsInstance(backtest_results['total_trades'], int)
        self.assertIsInstance(backtest_results['signals_count'], int)

class TestPerformanceAndEdgeCases(unittest.TestCase):
    """Test Performance and Edge Cases"""

    def test_empty_data_handling(self):
        """Test handling of empty data"""
        from models.cbsc_models import parse_warrant_sentiment_csv
        from analysis.sentiment_technical_integration import create_sentiment_integrator

        # Test empty sentiment data
        integrator = create_sentiment_integrator()
        indicators = integrator.calculate_sentiment_indicators([])

        self.assertEqual(indicators['sentiment_momentum'], 0.0)
        self.assertEqual(indicators['sentiment_trend'], 'NEUTRAL')
        self.assertEqual(indicators['sentiment_volatility'], 0.0)

        # Test empty price data
        import pandas as pd
        empty_price_data = pd.DataFrame({'close': []})
        tech_score = integrator.calculate_technical_score(empty_price_data)
        self.assertEqual(tech_score, 0.0)

    def test_large_dataset_performance(self):
        """Test performance with large datasets"""
        from models.cbsc_models import create_sample_cbsc_contract

        # Test model creation performance
        start_time = time.time()
        contracts = []

        for i in range(1000):  # Create 1000 contracts
            contract = create_sample_cbsc_contract()
            contracts.append(contract)

        creation_time = time.time() - start_time

        # Should complete within reasonable time (less than 1 second)
        self.assertLess(creation_time, 1.0)
        self.assertEqual(len(contracts), 1000)

        # Test risk calculation performance
        from risk_management.cbsc_risk import create_cbsc_risk_manager
        risk_manager = create_cbsc_risk_manager()

        start_time = time.time()
        for contract in contracts[:100]:  # Test first 100
            risk_manager.calculate_call_risk(contract, 260.0)

        risk_calc_time = time.time() - start_time

        # Should complete within reasonable time (less than 0.5 seconds for 100 contracts)
        self.assertLess(risk_calc_time, 0.5)

    def test_extreme_values(self):
        """Test handling of extreme values"""
        from models.cbsc_models import WarrantSentiment, SentimentLevel, SignalType

        # Test extremely high sentiment values
        extreme_sentiment = WarrantSentiment(
            date=date(2024, 6, 1),
            bull_turnover=999999999.0,
            bear_turnover=1.0,
            bull_turnover_ratio=0.999999999,
            bear_turnover_ratio=0.000000001,
            sentiment_strength=1.0,  # Maximum possible
            sentiment_level=SentimentLevel.EXTREME_BULL,
            signal=SignalType.BUY_BULL,
            total_turnover=1000000000.0
        )

        self.assertTrue(extreme_sentiment.get_extreme_signal())
        self.assertEqual(extreme_sentiment.sentiment_level, SentimentLevel.EXTREME_BULL)

        # Test extremely low values
        extreme_bear = WarrantSentiment(
            date=date(2024, 6, 1),
            bull_turnover=1.0,
            bear_turnover=999999999.0,
            bull_turnover_ratio=0.000000001,
            bear_turnover_ratio=0.999999999,
            sentiment_strength=-1.0,  # Minimum possible
            sentiment_level=SentimentLevel.EXTREME_BEAR,
            signal=SignalType.SELL_BEAR,
            total_turnover=1000000000.0
        )

        self.assertTrue(extreme_bear.get_extreme_signal())
        self.assertEqual(extreme_bear.sentiment_level, SentimentLevel.EXTREME_BEAR)

def run_comprehensive_tests():
    """Run all CBSC unit tests"""
    print("=" * 80)
    print("CBSC Comprehensive Unit Test Suite")
    print("=" * 80)

    # Create test suite
    test_classes = [
        TestCBSCModels,
        TestCBSCDataAdapters,
        TestCBSCRiskManagement,
        TestSentimentTechnicalIntegration,
        TestPerformanceAndEdgeCases
    ]

    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 80)
    print("Test Results Summary")
    print("=" * 80)

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
        print("\n🎉 SUCCESS: All CBSC unit tests passed!")
        print("   Phase 1 implementation is COMPLETE and ready for production!")
        return True
    else:
        print(f"\n⚠ WARNING: {failures + errors} tests failed.")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)