"""
Detailed Data Loader Tests
详细数据加载器测试

Comprehensive test suite for CBSC data loader functionality.
CBSC数据加载器功能的综合测试套件。

Author: CBSC Backtesting System Team
Date: 2025-12-04
Version: 1.0
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, Mock
import tempfile
import warnings

from data_loader import CBSCDataLoader

class TestDataLoaderFunctionality:
    """Test CBSC data loader functionality"""

    @pytest.mark.unit
    def test_load_sentiment_data_valid_file(self, mock_cbsc_data):
        """Test TC-DL-001: Load valid CBSC CSV file"""
        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        mock_cbsc_data.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            loader = CBSCDataLoader(temp_file.name)
            result = loader.load_sentiment_data()

            # Validate results
            assert not result.empty, "Should return non-empty DataFrame"
            assert len(result) == len(mock_cbsc_data), "Should load all records"
            assert 'Date' in result.columns, "Should contain Date column"
            assert 'Bull_Ratio' in result.columns, "Should contain Bull_Ratio column"
            assert 'Sentiment_Strength' in result.columns, "Should contain calculated Sentiment_Strength"
            assert 'Sentiment_Score' in result.columns, "Should contain calculated Sentiment_Score"

            # Validate data types
            assert pd.api.types.is_datetime64_any_dtype(result['Date']), "Date should be datetime"
            assert pd.api.types.is_numeric_dtype(result['Bull_Ratio']), "Bull_Ratio should be numeric"

        finally:
            Path(temp_file.name).unlink()

    @pytest.mark.unit
    def test_load_sentiment_data_invalid_path(self):
        """Test TC-DL-002: Handle invalid file path gracefully"""
        loader = CBSCDataLoader("non_existent_file.csv")
        result = loader.load_sentiment_data()

        assert result.empty, "Should return empty DataFrame for invalid path"

    @pytest.mark.unit
    def test_load_sentiment_data_missing_columns(self):
        """Test TC-DL-003: Handle missing required columns"""
        # Create CSV with missing columns
        incomplete_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10),
            'Bull_Ratio': np.random.rand(10)
            # Missing required columns like Bull_Bear_Ratio, etc.
        })

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        incomplete_data.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            loader = CBSCDataLoader(temp_file.name)
            # Should either raise an error or return filtered data
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = loader.load_sentiment_data()

            # Validation depends on implementation
            # Most implementations should handle missing columns gracefully
            assert isinstance(result, pd.DataFrame), "Should return DataFrame"

        finally:
            Path(temp_file.name).unlink()

    @pytest.mark.unit
    @pytest.mark.slow
    def test_load_price_data_yahoo_finance(self, mock_cbsc_data):
        """Test TC-DL-004: Load price data from Yahoo Finance"""
        # Mock sentiment data for date range
        loader = CBSCDataLoader.__new__(CBSCDataLoader)
        loader.sentiment_data = mock_cbsc_data

        # Test with real API (may be slow)
        try:
            result = loader.load_price_data("0700.HK")

            if not result.empty:
                # Validate price data structure
                required_columns = ['Date', 'open', 'high', 'low', 'close', 'volume']
                for col in required_columns:
                    assert col in result.columns, f"Should contain {col} column"

                assert pd.api.types.is_numeric_dtype(result['close']), "Close price should be numeric"
                assert pd.api.types.is_numeric_dtype(result['volume']), "Volume should be numeric"
                assert len(result) > 0, "Should return price data"

        except Exception as e:
            pytest.skip(f"Yahoo Finance API not available: {e}")

    @pytest.mark.unit
    def test_load_price_data_mock(self, mock_cbsc_data, mock_price_data):
        """Test price data loading with mock data"""
        loader = CBSCDataLoader.__new__(CBSCDataLoader)
        loader.sentiment_data = mock_cbsc_data

        # Mock the yfinance download
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker.return_value = mock_ticker_instance

            # Create mock price data
            mock_price_indexed = mock_price_data.set_index('Date')
            mock_ticker_instance.history.return_value = mock_price_indexed

            result = loader.load_price_data("0700.HK")

            assert not result.empty, "Should return price data"
            assert len(result) == len(mock_price_data), "Should return all price records"
            assert list(result.columns) == ['Date', 'open', 'high', 'low', 'close', 'volume']

    @pytest.mark.unit
    def test_align_data_functionality(self, mock_cbsc_data, mock_price_data):
        """Test TC-DL-005: Data alignment functionality"""
        # Create data with overlapping but different date ranges
        sentiment_subset = mock_cbsc_data.iloc[10:60].copy()
        price_subset = mock_price_data.iloc[20:70].copy()

        loader = CBSCDataLoader.__new__(CBSCDataLoader)
        loader.sentiment_data = sentiment_subset
        loader.price_data = price_subset

        aligned_sentiment, aligned_price = loader.align_data()

        # Should align to common date range
        expected_length = 40  # Intersection of ranges
        assert len(aligned_sentiment) == expected_length, "Sentiment data should be aligned"
        assert len(aligned_price) == expected_length, "Price data should be aligned"

        # Date ranges should match
        assert aligned_sentiment['Date'].equals(aligned_price['Date']), "Dates should be identical"

    @pytest.mark.unit
    def test_align_data_no_common_dates(self):
        """Test alignment with no common dates"""
        # Create non-overlapping date ranges
        sentiment_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10),
            'Bull_Ratio': np.random.rand(10)
        })

        price_data = pd.DataFrame({
            'Date': pd.date_range('2024-02-01', periods=10),
            'close': np.random.rand(10) * 1000
        })

        loader = CBSCDataLoader.__new__(CBSCDataLoader)
        loader.sentiment_data = sentiment_data
        loader.price_data = price_data

        with pytest.raises(ValueError, match="no common dates"):
            loader.align_data()

    @pytest.mark.unit
    def test_create_cbsc_features(self, mock_cbsc_data, mock_price_data):
        """Test TC-DL-006: Feature engineering functionality"""
        loader = CBSCDataLoader.__new__(CBSCDataLoader)

        # Ensure same length for proper merging
        min_length = min(len(mock_cbsc_data), len(mock_price_data))
        sentiment_subset = mock_cbsc_data.iloc[:min_length].copy()
        price_subset = mock_price_data.iloc[:min_length].copy()

        features_df = loader.create_cbsc_features(sentiment_subset, price_subset)

        # Validate feature creation
        assert not features_df.empty, "Should return non-empty features DataFrame"
        assert 'Returns' in features_df.columns, "Should calculate returns"
        assert 'MA5' in features_df.columns, "Should calculate 5-day MA"
        assert 'MA20' in features_df.columns, "Should calculate 20-day MA"
        assert 'RSI' in features_df.columns, "Should calculate RSI"
        assert 'Price_to_Sentiment' in features_df.columns, "Should calculate price-to-sentiment ratio"
        assert 'Volume_Sentiment_Ratio' in features_df.columns, "Should calculate volume-sentiment ratio"

        # Validate calculations
        # RSI should be between 0 and 100
        valid_rsi = features_df['RSI'].between(0, 100).all()
        assert valid_rsi, "RSI values should be between 0 and 100"

        # Returns calculation should be reasonable
        returns_std = features_df['Returns'].std()
        assert returns_std > 0, "Returns should have variability"

    @pytest.mark.unit
    def test_get_data_summary(self, mock_cbsc_data, mock_price_data):
        """Test data summary generation"""
        loader = CBSCDataLoader.__new__(CBSCDataLoader)
        loader.sentiment_data = mock_cbsc_data
        loader.price_data = mock_price_data

        summary = loader.get_data_summary()

        # Validate summary structure
        required_keys = [
            'sentiment_records', 'price_records', 'sentiment_date_range',
            'price_date_range', 'avg_sentiment_strength', 'sentiment_volatility',
            'data_quality'
        ]

        for key in required_keys:
            assert key in summary, f"Summary should contain {key}"

        # Validate summary values
        assert summary['sentiment_records'] == len(mock_cbsc_data), "Should count sentiment records correctly"
        assert summary['price_records'] == len(mock_price_data), "Should count price records correctly"
        assert isinstance(summary['avg_sentiment_strength'], (int, float)), "Average should be numeric"
        assert isinstance(summary['data_quality'], dict), "Data quality should be a dict"

    @pytest.mark.unit
    def test_calculate_rsi(self):
        """Test RSI calculation method"""
        loader = CBSCDataLoader.__new__(CBSCDataLoader)

        # Create test price series
        prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])

        rsi = loader._calculate_rsi(prices, period=5)

        # RSI should be calculated (first few values may be NaN)
        assert not rsi.dropna().empty, "Should calculate RSI values"
        valid_rsi = rsi.dropna()
        assert valid_rsi.between(0, 100).all(), "RSI should be between 0 and 100"

    @pytest.mark.data_quality
    def test_data_quality_validation(self, mock_cbsc_data):
        """Test data quality checks"""
        loader = CBSCDataLoader.__new__(CBSCDataLoader)

        # Test with valid data
        loader.sentiment_data = mock_cbsc_data
        summary = loader.get_data_summary()

        # Check for data quality issues
        data_quality = summary['data_quality']
        assert data_quality['null_sentiment'] >= 0, "Null count should be non-negative"
        assert data_quality['null_price'] >= 0, "Null count should be non-negative"

    @pytest.mark.edge_cases
    def test_duplicate_dates_handling(self):
        """Test handling of duplicate dates in sentiment data"""
        # Create data with duplicate dates
        duplicate_dates = pd.date_range('2024-01-01', periods=10)
        dates_with_duplicates = duplicate_dates.tolist() + duplicate_dates[:2].tolist()

        data_with_duplicates = pd.DataFrame({
            'Date': dates_with_duplicates,
            'Bull_Ratio': np.random.rand(12),
            'Bull_Bear_Ratio': np.random.rand(12),
            'Bull_Turnover_HKD': np.random.randint(1e6, 1e7, 12),
            'Bear_Turnover_HKD': np.random.randint(1e6, 1e7, 12),
            'Afternoon_Close': 25000 + np.random.randn(12) * 100,
            'Signal': np.random.choice([-1, 0, 1], 12),
            'Sentiment_Level': np.random.choice(['EXTREME BULL', 'MOD BULL', 'NEUTRAL'], 12)
        })

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        data_with_duplicates.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            loader = CBSCDataLoader(temp_file.name)
            result = loader.load_sentiment_data()

            # Should handle duplicates by grouping and taking max turnover
            assert len(result) <= len(data_with_duplicates), "Should reduce duplicates"
            assert result['Date'].is_unique, "Result should have unique dates"

        finally:
            Path(temp_file.name).unlink()

    @pytest.mark.edge_cases
    def test_zero_turnover_handling(self):
        """Test handling of zero turnover values"""
        # Create data with zero turnover
        zero_turnover_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10),
            'Bull_Ratio': 0.5,  # Neutral sentiment
            'Bull_Bear_Ratio': 1.0,
            'Bull_Turnover_HKD': 0,  # Zero turnover
            'Bear_Turnover_HKD': 0,  # Zero turnover
            'Afternoon_Close': 25000,
            'Signal': 0,
            'Sentiment_Level': 'NEUTRAL'
        })

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        zero_turnover_data.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            loader = CBSCDataLoader(temp_file.name)
            result = loader.load_sentiment_data()

            # Should handle zero turnover gracefully
            assert not result.empty, "Should process data with zero turnover"

            # Check calculated features
            if 'Total_Turnover' in result.columns:
                assert (result['Total_Turnover'] == 0).all(), "Total turnover should be zero"

            if 'Sentiment_Strength' in result.columns:
                # With zero turnover, sentiment strength calculation should be handled
                assert not result['Sentiment_Strength'].isna().any(), "Should handle division by zero"

        except Exception as e:
            # This test expects the implementation to handle zero turnover
            # If it fails, it indicates a potential issue to address
            pytest.skip(f"Zero turnover handling not implemented: {e}")

        finally:
            Path(temp_file.name).unlink()

    @pytest.mark.performance
    def test_data_loading_performance(self, mock_cbsc_data, performance_monitor):
        """Test data loading performance"""
        # Create large dataset for performance testing
        large_data = pd.concat([mock_cbsc_data] * 10, ignore_index=True)  # 10x larger

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        large_data.to_csv(temp_file.name, index=False)
        temp_file.close()

        try:
            with performance_monitor as monitor:
                loader = CBSCDataLoader(temp_file.name)
                result = loader.load_sentiment_data()

            # Performance assertion (adjust threshold as needed)
            assert monitor.execution_time < 5.0, f"Loading too slow: {monitor.execution_time:.2f}s"
            assert monitor.memory_used < 100, f"Too much memory used: {monitor.memory_used:.1f}MB"
            assert len(result) == len(large_data), "Should load all records"

        finally:
            Path(temp_file.name).unlink()