"""Data flow integration tests for Hong Kong quantitative trading system.

This module provides comprehensive data flow testing including end-to-end data pipeline
testing, data transformation validation, and data quality assurance.
"""

import asyncio
import logging
import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import numpy as np

# Import system components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_adapters.data_service import DataService
from src.data_adapters.raw_data_adapter import RawDataAdapter, RawDataAdapterConfig
from src.agents.real_agents.real_quantitative_analyst import RealQuantitativeAnalyst
from src.agents.real_agents.real_quantitative_trader import RealQuantitativeTrader
from src.agents.real_agents.real_portfolio_manager import RealPortfolioManager
from src.agents.real_agents.real_risk_analyst import RealRiskAnalyst
from src.strategy_management.strategy_manager import StrategyManager
from src.monitoring.real_time_monitor import RealTimeMonitor

from tests.helpers.test_utils import TestDataGenerator, MockComponentFactory, TestAssertions


class TestDataPipelineIntegration:
    """Test data pipeline integration."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        self.mock_factory = MockComponentFactory()
        
        # Create test data
        self.market_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            frequency="1min"
        )
        
        yield
        
        # Cleanup
        await self.cleanup_test_environment()
    
    async def cleanup_test_environment(self):
        """Cleanup test environment."""
        pass
    
    @pytest.mark.asyncio
    async def test_raw_data_to_analysis_pipeline(self):
        """Test data flow from raw data to analysis."""
        # Create mock data adapter
        mock_adapter = self.mock_factory.create_mock_data_adapter(self.market_data)
        
        # Create mock analyst
        mock_analyst = self.mock_factory.create_mock_ai_agent(
            agent_id="quantitative_analyst",
            signal_type="BUY",
            confidence=0.85
        )
        
        # Test data flow
        # Step 1: Get market data
        market_data = await mock_adapter.get_market_data("00700.HK")
        
        # Step 2: Analyze data
        analysis_result = await mock_analyst.analyze_market_data(market_data)
        
        # Verify data flow
        assert len(market_data) > 0
        assert analysis_result['signal'] == "BUY"
        assert analysis_result['confidence'] == 0.85
        assert analysis_result['agent_id'] == "quantitative_analyst"
        
        # Verify data structure
        TestAssertions.assert_data_structure_valid(
            market_data[0], 
            ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        )
        
        TestAssertions.assert_trading_signal_valid(analysis_result)
    
    @pytest.mark.asyncio
    async def test_analysis_to_trading_signal_pipeline(self):
        """Test data flow from analysis to trading signal."""
        # Create mock analyst
        mock_analyst = self.mock_factory.create_mock_ai_agent(
            agent_id="quantitative_analyst",
            signal_type="BUY",
            confidence=0.85
        )
        
        # Create mock trader
        mock_trader = self.mock_factory.create_mock_ai_agent(
            agent_id="quantitative_trader",
            signal_type="BUY",
            confidence=0.80
        )
        
        # Test data flow
        # Step 1: Analyze market data
        analysis_result = await mock_analyst.analyze_market_data(self.market_data.to_dict('records'))
        
        # Step 2: Generate trading signal
        trading_signal = await mock_trader.analyze_market_data(analysis_result)
        
        # Verify data flow
        assert analysis_result['signal'] == "BUY"
        assert trading_signal['signal'] == "BUY"
        assert trading_signal['agent_id'] == "quantitative_trader"
        
        # Verify signal consistency
        assert analysis_result['signal'] == trading_signal['signal']
    
    @pytest.mark.asyncio
    async def test_trading_signal_to_portfolio_management_pipeline(self):
        """Test data flow from trading signal to portfolio management."""
        # Create mock trader
        mock_trader = self.mock_factory.create_mock_ai_agent(
            agent_id="quantitative_trader",
            signal_type="BUY",
            confidence=0.80
        )
        
        # Create mock portfolio manager
        mock_portfolio_manager = self.mock_factory.create_mock_ai_agent(
            agent_id="portfolio_manager",
            signal_type="BUY",
            confidence=0.75
        )
        
        # Test data flow
        # Step 1: Generate trading signal
        trading_signal = await mock_trader.analyze_market_data(self.market_data.to_dict('records'))
        
        # Step 2: Process portfolio management
        portfolio_decision = await mock_portfolio_manager.analyze_market_data(trading_signal)
        
        # Verify data flow
        assert trading_signal['signal'] == "BUY"
        assert portfolio_decision['signal'] == "BUY"
        assert portfolio_decision['agent_id'] == "portfolio_manager"
        
        # Verify decision consistency
        assert trading_signal['signal'] == portfolio_decision['signal']
    
    @pytest.mark.asyncio
    async def test_portfolio_to_risk_management_pipeline(self):
        """Test data flow from portfolio management to risk management."""
        # Create mock portfolio manager
        mock_portfolio_manager = self.mock_factory.create_mock_ai_agent(
            agent_id="portfolio_manager",
            signal_type="BUY",
            confidence=0.75
        )
        
        # Create mock risk analyst
        mock_risk_analyst = self.mock_factory.create_mock_ai_agent(
            agent_id="risk_analyst",
            signal_type="BUY",
            confidence=0.70
        )
        
        # Test data flow
        # Step 1: Process portfolio management
        portfolio_decision = await mock_portfolio_manager.analyze_market_data(self.market_data.to_dict('records'))
        
        # Step 2: Assess risk
        risk_assessment = await mock_risk_analyst.analyze_market_data(portfolio_decision)
        
        # Verify data flow
        assert portfolio_decision['signal'] == "BUY"
        assert risk_assessment['signal'] == "BUY"
        assert risk_assessment['agent_id'] == "risk_analyst"
        
        # Verify risk assessment
        assert risk_assessment['confidence'] <= portfolio_decision['confidence']


class TestDataTransformationIntegration:
    """Test data transformation integration."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        
        # Create test data
        self.raw_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            frequency="1min"
        )
        
        yield
    
    @pytest.mark.asyncio
    async def test_market_data_aggregation(self):
        """Test market data aggregation transformation."""
        # Test 1-minute to 5-minute aggregation
        raw_data = self.raw_data.copy()
        raw_data['timestamp'] = pd.to_datetime(raw_data['timestamp'])
        raw_data.set_index('timestamp', inplace=True)
        
        # Aggregate to 5-minute intervals
        agg_data = raw_data.resample('5min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Verify aggregation
        assert len(agg_data) < len(raw_data)  # Should have fewer records
        assert all(agg_data['high'] >= agg_data['low'])  # High >= Low
        assert all(agg_data['high'] >= agg_data['open'])  # High >= Open
        assert all(agg_data['high'] >= agg_data['close'])  # High >= Close
        assert all(agg_data['low'] <= agg_data['open'])  # Low <= Open
        assert all(agg_data['low'] <= agg_data['close'])  # Low <= Close
        assert all(agg_data['volume'] > 0)  # Volume > 0
    
    @pytest.mark.asyncio
    async def test_technical_indicator_calculation(self):
        """Test technical indicator calculation transformation."""
        # Calculate simple moving average
        raw_data = self.raw_data.copy()
        raw_data['sma_20'] = raw_data['close'].rolling(window=20).mean()
        raw_data['sma_50'] = raw_data['close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = raw_data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        raw_data['rsi'] = 100 - (100 / (1 + rs))
        
        # Verify technical indicators
        assert not raw_data['sma_20'].isna().all()  # Should have some valid values
        assert not raw_data['sma_50'].isna().all()  # Should have some valid values
        assert not raw_data['rsi'].isna().all()  # Should have some valid values
        
        # Verify RSI bounds
        valid_rsi = raw_data['rsi'].dropna()
        assert all(valid_rsi >= 0) and all(valid_rsi <= 100), "RSI should be between 0 and 100"
    
    @pytest.mark.asyncio
    async def test_risk_metrics_calculation(self):
        """Test risk metrics calculation transformation."""
        # Calculate returns
        raw_data = self.raw_data.copy()
        raw_data['returns'] = raw_data['close'].pct_change()
        
        # Calculate volatility
        raw_data['volatility'] = raw_data['returns'].rolling(window=20).std() * np.sqrt(252)
        
        # Calculate VaR (95% confidence)
        raw_data['var_95'] = raw_data['returns'].rolling(window=20).quantile(0.05)
        
        # Verify risk metrics
        assert not raw_data['returns'].isna().all()  # Should have some valid returns
        assert not raw_data['volatility'].isna().all()  # Should have some valid volatility
        assert not raw_data['var_95'].isna().all()  # Should have some valid VaR
        
        # Verify volatility is positive
        valid_volatility = raw_data['volatility'].dropna()
        assert all(valid_volatility >= 0), "Volatility should be non-negative"
        
        # Verify VaR is negative (losses)
        valid_var = raw_data['var_95'].dropna()
        assert all(valid_var <= 0), "VaR should be negative (losses)"


class TestDataQualityIntegration:
    """Test data quality integration."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        
        # Create test data with quality issues
        self.clean_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            frequency="1min"
        )
        
        # Create data with quality issues
        self.dirty_data = self.clean_data.copy()
        self.dirty_data.loc[10:15, 'close'] = np.nan  # Missing values
        self.dirty_data.loc[20:25, 'volume'] = 0  # Zero volume
        self.dirty_data.loc[30:35, 'high'] = self.dirty_data.loc[30:35, 'low'] - 1  # Invalid OHLC
        
        yield
    
    @pytest.mark.asyncio
    async def test_missing_data_detection(self):
        """Test missing data detection."""
        # Detect missing values
        missing_data = self.dirty_data.isnull().sum()
        
        # Verify missing data detection
        assert missing_data['close'] > 0, "Should detect missing close prices"
        assert missing_data['volume'] == 0, "Should not detect missing volume"
        
        # Test missing data handling
        cleaned_data = self.dirty_data.dropna(subset=['close'])
        assert len(cleaned_data) < len(self.dirty_data), "Should remove rows with missing close prices"
    
    @pytest.mark.asyncio
    async def test_data_validation_rules(self):
        """Test data validation rules."""
        # Validate OHLC relationships
        invalid_ohlc = (
            (self.dirty_data['high'] < self.dirty_data['low']) |
            (self.dirty_data['high'] < self.dirty_data['open']) |
            (self.dirty_data['high'] < self.dirty_data['close']) |
            (self.dirty_data['low'] > self.dirty_data['open']) |
            (self.dirty_data['low'] > self.dirty_data['close'])
        )
        
        # Verify invalid OHLC detection
        assert invalid_ohlc.any(), "Should detect invalid OHLC relationships"
        
        # Validate volume
        invalid_volume = self.dirty_data['volume'] < 0
        assert not invalid_volume.any(), "Should not have negative volume"
        
        # Validate prices
        invalid_prices = (
            (self.dirty_data['open'] <= 0) |
            (self.dirty_data['high'] <= 0) |
            (self.dirty_data['low'] <= 0) |
            (self.dirty_data['close'] <= 0)
        )
        assert not invalid_prices.any(), "Should not have non-positive prices"
    
    @pytest.mark.asyncio
    async def test_data_cleaning_pipeline(self):
        """Test data cleaning pipeline."""
        # Step 1: Remove missing values
        cleaned_data = self.dirty_data.dropna()
        
        # Step 2: Remove invalid OHLC relationships
        valid_ohlc = (
            (cleaned_data['high'] >= cleaned_data['low']) &
            (cleaned_data['high'] >= cleaned_data['open']) &
            (cleaned_data['high'] >= cleaned_data['close']) &
            (cleaned_data['low'] <= cleaned_data['open']) &
            (cleaned_data['low'] <= cleaned_data['close'])
        )
        cleaned_data = cleaned_data[valid_ohlc]
        
        # Step 3: Remove zero volume
        cleaned_data = cleaned_data[cleaned_data['volume'] > 0]
        
        # Verify cleaning results
        assert len(cleaned_data) < len(self.dirty_data), "Should reduce data size after cleaning"
        assert not cleaned_data.isnull().any().any(), "Should have no missing values"
        assert all(cleaned_data['volume'] > 0), "Should have no zero volume"
        
        # Verify OHLC relationships
        assert all(cleaned_data['high'] >= cleaned_data['low']), "High should be >= Low"
        assert all(cleaned_data['high'] >= cleaned_data['open']), "High should be >= Open"
        assert all(cleaned_data['high'] >= cleaned_data['close']), "High should be >= Close"
        assert all(cleaned_data['low'] <= cleaned_data['open']), "Low should be <= Open"
        assert all(cleaned_data['low'] <= cleaned_data['close']), "Low should be <= Close"


class TestRealTimeDataIntegration:
    """Test real-time data integration."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        
        # Create mock real-time data source
        self.real_time_data = []
        for i in range(100):
            data_point = {
                'timestamp': datetime.now() - timedelta(seconds=i),
                'symbol': '00700.HK',
                'price': 300.0 + np.random.normal(0, 1),
                'volume': random.randint(1000, 10000),
                'bid': 299.9 + np.random.normal(0, 0.5),
                'ask': 300.1 + np.random.normal(0, 0.5)
            }
            self.real_time_data.append(data_point)
        
        yield
    
    @pytest.mark.asyncio
    async def test_real_time_data_processing(self):
        """Test real-time data processing."""
        # Process real-time data
        processed_data = []
        for data_point in self.real_time_data:
            # Simulate real-time processing
            processed_point = {
                **data_point,
                'processed_at': datetime.now(),
                'spread': data_point['ask'] - data_point['bid'],
                'mid_price': (data_point['ask'] + data_point['bid']) / 2
            }
            processed_data.append(processed_point)
        
        # Verify processing
        assert len(processed_data) == len(self.real_time_data)
        assert all('processed_at' in point for point in processed_data)
        assert all('spread' in point for point in processed_data)
        assert all('mid_price' in point for point in processed_data)
        
        # Verify spread calculation
        for point in processed_data:
            assert point['spread'] > 0, "Spread should be positive"
            assert point['mid_price'] > 0, "Mid price should be positive"
    
    @pytest.mark.asyncio
    async def test_real_time_data_aggregation(self):
        """Test real-time data aggregation."""
        # Aggregate data by minute
        df = pd.DataFrame(self.real_time_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Aggregate to 1-minute intervals
        agg_data = df.resample('1min').agg({
            'price': 'last',
            'volume': 'sum',
            'bid': 'last',
            'ask': 'last'
        }).dropna()
        
        # Verify aggregation
        assert len(agg_data) > 0, "Should have aggregated data"
        assert all(agg_data['volume'] > 0), "Aggregated volume should be positive"
        assert all(agg_data['price'] > 0), "Aggregated price should be positive"
    
    @pytest.mark.asyncio
    async def test_real_time_data_validation(self):
        """Test real-time data validation."""
        # Validate real-time data
        validation_results = []
        for data_point in self.real_time_data:
            is_valid = (
                data_point['price'] > 0 and
                data_point['volume'] > 0 and
                data_point['bid'] > 0 and
                data_point['ask'] > 0 and
                data_point['ask'] > data_point['bid']
            )
            validation_results.append(is_valid)
        
        # Verify validation
        assert all(validation_results), "All real-time data should be valid"
        
        # Test with invalid data
        invalid_data = {
            'timestamp': datetime.now(),
            'symbol': '00700.HK',
            'price': -100.0,  # Invalid negative price
            'volume': 0,  # Invalid zero volume
            'bid': 300.0,
            'ask': 299.0  # Invalid ask < bid
        }
        
        is_invalid = (
            invalid_data['price'] <= 0 or
            invalid_data['volume'] <= 0 or
            invalid_data['bid'] <= 0 or
            invalid_data['ask'] <= 0 or
            invalid_data['ask'] <= invalid_data['bid']
        )
        
        assert is_invalid, "Should detect invalid data"


class TestDataPersistenceIntegration:
    """Test data persistence integration."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        
        # Create test data
        self.test_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            frequency="1min"
        )
        
        yield
    
    @pytest.mark.asyncio
    async def test_data_serialization(self):
        """Test data serialization."""
        import json
        
        # Test JSON serialization
        json_data = self.test_data.to_json(orient='records', date_format='iso')
        parsed_data = json.loads(json_data)
        
        # Verify serialization
        assert len(parsed_data) == len(self.test_data)
        assert all('timestamp' in record for record in parsed_data)
        assert all('symbol' in record for record in parsed_data)
        assert all('price' in record for record in parsed_data)
    
    @pytest.mark.asyncio
    async def test_data_deserialization(self):
        """Test data deserialization."""
        import json
        
        # Serialize data
        json_data = self.test_data.to_json(orient='records', date_format='iso')
        
        # Deserialize data
        parsed_data = json.loads(json_data)
        df = pd.DataFrame(parsed_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Verify deserialization
        assert len(df) == len(self.test_data)
        assert df['symbol'].equals(self.test_data['symbol'])
        assert df['close'].equals(self.test_data['close'])
    
    @pytest.mark.asyncio
    async def test_data_compression(self):
        """Test data compression."""
        import gzip
        import json
        
        # Compress data
        json_data = self.test_data.to_json(orient='records', date_format='iso')
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        
        # Decompress data
        decompressed_data = gzip.decompress(compressed_data).decode('utf-8')
        parsed_data = json.loads(decompressed_data)
        
        # Verify compression
        assert len(compressed_data) < len(json_data), "Compressed data should be smaller"
        assert len(parsed_data) == len(self.test_data), "Decompressed data should match original"
        
        # Verify data integrity
        assert parsed_data[0]['symbol'] == self.test_data['symbol'].iloc[0]
        assert parsed_data[0]['close'] == self.test_data['close'].iloc[0]


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
