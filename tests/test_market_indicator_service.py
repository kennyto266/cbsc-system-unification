"""
Test Market Indicator Service

Unit tests for market indicator service layer functions.
Tests date range calculation, data fetching, attribution calculation, and mock data.
"""
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.market_indicator_service import (
    get_date_range,
    fetch_indicators,
    calculate_return_attribution,
    get_mock_data,
    TIME_RANGES
)


class TestGetDateRange:
    """Test date range calculation function"""

    def test_get_date_range_1w(self):
        """Test 1 week range calculation"""
        start, end = get_date_range("1w")
        now = datetime.now()

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert end >= now
        # Should be approximately 7 days ago
        expected_start = now - timedelta(days=7)
        assert abs((start - expected_start).total_seconds()) < 2  # Allow 2 seconds tolerance

    def test_get_date_range_1m(self):
        """Test 1 month range calculation"""
        start, end = get_date_range("1m")
        now = datetime.now()

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        expected_start = now - timedelta(days=30)
        assert abs((start - expected_start).total_seconds()) < 2

    def test_get_date_range_3m(self):
        """Test 3 month range calculation"""
        start, end = get_date_range("3m")
        now = datetime.now()

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        expected_start = now - timedelta(days=90)
        assert abs((start - expected_start).total_seconds()) < 2

    def test_get_date_range_1y(self):
        """Test 1 year range calculation"""
        start, end = get_date_range("1y")
        now = datetime.now()

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        expected_start = now - timedelta(days=365)
        assert abs((start - expected_start).total_seconds()) < 2

    def test_get_date_range_invalid(self):
        """Test invalid range raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_date_range("invalid")

        assert "Invalid time_range" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

    def test_get_date_range_all_supported_ranges(self):
        """Test all supported ranges work"""
        for range_key in TIME_RANGES.keys():
            start, end = get_date_range(range_key)
            assert isinstance(start, datetime)
            assert isinstance(end, datetime)
            assert start < end


class TestFetchIndicators:
    """Test fetch_indicators function"""

    @patch('src.services.market_indicator_service.RealDictCursor')
    def test_fetch_indicators_success(self, mock_cursor_class):
        """Test successful indicator fetching"""
        # Setup mock connection and cursor
        mock_conn = Mock()
        mock_cursor = MagicMock()
        mock_cursor_class.return_value = mock_cursor
        mock_conn.cursor.return_value = mock_cursor

        # Mock database rows
        mock_row1 = {
            'date': datetime(2025, 12, 20),
            'advance_decline_ratio': 0.44,
            'volume_change_percent': 5.2,
            'sentiment_score': 17.64,
            'breadth_momentum': 0.0
        }
        mock_row2 = {
            'date': datetime(2025, 12, 21),
            'advance_decline_ratio': 0.55,
            'volume_change_percent': 3.1,
            'sentiment_score': 22.5,
            'breadth_momentum': 0.0
        }
        mock_cursor.fetchall.return_value = [mock_row1, mock_row2]

        start_date = datetime(2025, 12, 1)
        end_date = datetime(2025, 12, 31)

        # Call function
        indicators = fetch_indicators(mock_conn, start_date, end_date)

        # Verify results
        assert len(indicators) == 2
        assert indicators[0]['date'] == '2025-12-20T00:00:00'
        assert indicators[0]['advance_decline_ratio'] == 0.44
        assert indicators[0]['volume_change_percent'] == 5.2
        assert indicators[0]['sentiment_score'] == 17.64
        assert indicators[1]['date'] == '2025-12-21T00:00:00'

        # Verify query was executed correctly
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert 'market_indicators' in call_args[0][0]
        assert call_args[0][1] == (start_date, end_date)

    @patch('src.services.market_indicator_service.RealDictCursor')
    def test_fetch_indicators_empty_result(self, mock_cursor_class):
        """Test fetching when no indicators exist"""
        mock_conn = Mock()
        mock_cursor = MagicMock()
        mock_cursor_class.return_value = mock_cursor
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        start_date = datetime(2025, 12, 1)
        end_date = datetime(2025, 12, 31)

        indicators = fetch_indicators(mock_conn, start_date, end_date)

        assert indicators == []
        mock_cursor.execute.assert_called_once()

    @patch('src.services.market_indicator_service.RealDictCursor')
    def test_fetch_indicators_with_null_values(self, mock_cursor_class):
        """Test handling of null values in database"""
        mock_conn = Mock()
        mock_cursor = MagicMock()
        mock_cursor_class.return_value = mock_cursor
        mock_conn.cursor.return_value = mock_cursor

        # Mock row with None values
        mock_row = {
            'date': None,
            'advance_decline_ratio': None,
            'volume_change_percent': None,
            'sentiment_score': None,
            'breadth_momentum': None
        }
        mock_cursor.fetchall.return_value = [mock_row]

        indicators = fetch_indicators(mock_conn, datetime(2025, 12, 1), datetime(2025, 12, 31))

        assert len(indicators) == 1
        assert indicators[0]['date'] is None
        assert indicators[0]['advance_decline_ratio'] is None


class TestCalculateReturnAttribution:
    """Test calculate_return_attribution function"""

    def test_calculate_return_attribution_empty(self):
        """Test with empty indicators list"""
        result = calculate_return_attribution([])

        assert result["total"] == 0.0
        assert len(result["breakdown"]) == 3

        # All contributions should be 0
        for item in result["breakdown"]:
            assert item["contribution"] == 0.0
            assert item["percentage"] == 0.0

        # Check indicator names
        indicator_names = [item["indicator"] for item in result["breakdown"]]
        assert "市場漲跌情緒" in indicator_names
        assert "成交量活躍度" in indicator_names
        assert "市場廣度" in indicator_names

    def test_calculate_return_attribution_single_indicator(self):
        """Test with single indicator"""
        indicators = [{
            'advance_decline_ratio': 1.0,
            'volume_change_percent': 10.0,
            'sentiment_score': 50.0,
            'breadth_momentum': 0
        }]

        result = calculate_return_attribution(indicators)

        assert result["total"] > 0
        assert len(result["breakdown"]) == 3

        # Check percentage calculation
        total_pct = sum(item["percentage"] for item in result["breakdown"])
        assert 99 <= total_pct <= 101  # Allow small rounding error

    def test_calculate_return_attribution_multiple_indicators(self):
        """Test with multiple indicators"""
        indicators = [
            {
                'advance_decline_ratio': 0.44,
                'volume_change_percent': 5.2,
                'sentiment_score': 17.64,
                'breadth_momentum': 0
            },
            {
                'advance_decline_ratio': 0.55,
                'volume_change_percent': 3.1,
                'sentiment_score': 22.5,
                'breadth_momentum': 0
            }
        ]

        result = calculate_return_attribution(indicators)

        assert result["total"] > 0
        assert len(result["breakdown"]) == 3

        # Verify structure
        for item in result["breakdown"]:
            assert "indicator" in item
            assert "contribution" in item
            assert "percentage" in item
            assert isinstance(item["contribution"], float)
            assert isinstance(item["percentage"], float)

        # Check percentages sum to ~100
        total_pct = sum(item["percentage"] for item in result["breakdown"])
        assert 99 <= total_pct <= 101

    def test_calculate_return_attribution_with_null_values(self):
        """Test handling of None values in indicators"""
        indicators = [
            {
                'advance_decline_ratio': None,
                'volume_change_percent': None,
                'sentiment_score': None,
                'breadth_momentum': None
            },
            {
                'advance_decline_ratio': 1.0,
                'volume_change_percent': 10.0,
                'sentiment_score': 50.0,
                'breadth_momentum': 0
            }
        ]

        result = calculate_return_attribution(indicators)

        # Should handle None values gracefully
        assert result["total"] > 0
        assert len(result["breakdown"]) == 3

    def test_calculate_return_attribution_zero_total(self):
        """Test when all values are zero"""
        indicators = [
            {
                'advance_decline_ratio': 0,
                'volume_change_percent': 0,
                'sentiment_score': 0,
                'breadth_momentum': 0
            }
        ]

        result = calculate_return_attribution(indicators)

        assert result["total"] == 0.0
        # All percentages should be 0 when total is 0
        for item in result["breakdown"]:
            assert item["percentage"] == 0.0

    def test_calculate_return_attribution_weighting(self):
        """Test that contributions are weighted correctly"""
        indicators = [{
            'advance_decline_ratio': 1.0,
            'volume_change_percent': 1.0,
            'sentiment_score': 100.0,  # Results in 1.0 when divided by 100
            'breadth_momentum': 0
        }]

        result = calculate_return_attribution(indicators)

        # Expected contributions:
        # Ratio: 1.0 * 0.4 = 0.4
        # Volume: 1.0 * 0.3 = 0.3
        # Breadth: (100/100) * 0.3 * 100 = 30
        # Total: 0.4 + 0.3 + 30 = 30.7

        assert abs(result["total"] - 30.7) < 0.01


class TestGetMockData:
    """Test get_mock_data function"""

    def test_get_mock_data_structure(self):
        """Test mock data has correct structure"""
        result = get_mock_data()

        # Check top-level keys
        assert "return_attribution" in result
        assert "risk_exposure" in result
        assert "correlations" in result
        assert "stress_test" in result

    def test_get_mock_data_return_attribution(self):
        """Test return attribution structure"""
        result = get_mock_data()
        attribution = result["return_attribution"]

        assert "total" in attribution
        assert "breakdown" in attribution
        assert isinstance(attribution["total"], (int, float))
        assert isinstance(attribution["breakdown"], list)
        assert len(attribution["breakdown"]) == 3

        # Check breakdown items
        for item in attribution["breakdown"]:
            assert "indicator" in item
            assert "contribution" in item
            assert "percentage" in item

    def test_get_mock_data_risk_exposure(self):
        """Test risk exposure structure"""
        result = get_mock_data()
        risk = result["risk_exposure"]

        assert isinstance(risk, dict)
        assert "systematic" in risk
        assert "interestRate" in risk
        assert "liquidity" in risk
        assert "economicGrowth" in risk
        assert "fx" in risk

    def test_get_mock_data_correlations(self):
        """Test correlations structure"""
        result = get_mock_data()
        correlations = result["correlations"]

        assert "matrix" in correlations
        assert "strategies" in correlations
        assert isinstance(correlations["matrix"], list)
        assert isinstance(correlations["strategies"], list)
        assert len(correlations["strategies"]) == 3

    def test_get_mock_data_stress_test(self):
        """Test stress test structure"""
        result = get_mock_data()
        stress_test = result["stress_test"]

        assert isinstance(stress_test, list)
        assert len(stress_test) == 4

        # Check each scenario
        for scenario in stress_test:
            assert "scenario" in scenario
            assert "expectedReturn" in scenario
            assert "maxDrawdown" in scenario
            assert "sharpeRatio" in scenario

    def test_get_mock_data_scenarios(self):
        """Test specific stress test scenarios"""
        result = get_mock_data()
        scenarios = result["stress_test"]

        scenario_names = [s["scenario"] for s in scenarios]
        assert "基準" in scenario_names
        assert "利率+200bp" in scenario_names
        assert "經濟衰退" in scenario_names
        assert "市場崩盤" in scenario_names


class TestIntegration:
    """Integration tests for service functions"""

    def test_date_range_and_fetch_workflow(self):
        """Test typical workflow: get date range, then fetch"""
        start, end = get_date_range("1w")

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert start < end

        # Date range should be usable for fetch_indicators
        # (We don't actually call fetch here as it needs a DB connection)

    def test_fetch_and_calculate_workflow(self):
        """Test typical workflow: fetch indicators, then calculate attribution"""
        # Simulate fetched indicators
        mock_indicators = [
            {
                'advance_decline_ratio': 0.5,
                'volume_change_percent': 5.0,
                'sentiment_score': 20.0,
                'breadth_momentum': 0
            }
        ]

        result = calculate_return_attribution(mock_indicators)

        assert result["total"] > 0
        assert len(result["breakdown"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
