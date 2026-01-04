#!/usr/bin/env python3
"""
Test cases for Data Quality Checker
數據質量檢查器測試用例
Task 8.1 - 數據獲取模塊
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
import numpy as np

from src.collectors.data_quality_checker import (
    DataQualityChecker, DataQualityConfig, QualityReport,
    QualityLevel, AlertLevel, QualityIssue, DataType
)

class TestDataQualityChecker:
    """Test cases for DataQualityChecker"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return DataQualityConfig(
            max_price_change_pct=30.0,
            missing_data_threshold=0.05,
            outlier_contamination=0.1,
            enable_statistical_detection=True,
            enable_pattern_detection=True
        )

    @pytest.fixture
    def checker(self, config):
        """Create data quality checker instance"""
        return DataQualityChecker(config)

    @pytest.fixture
    def sample_data(self):
        """Create sample market data"""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        np.random.seed(42)

        # Generate mostly normal data
        base_price = 100
        returns = np.random.normal(0, 0.02, 100)
        prices = base_price * (1 + returns).cumprod()

        data = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 100)
        })

        return data

    @pytest.fixture
    def problematic_data(self):
        """Create data with quality issues"""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        np.random.seed(42)

        # Start with normal data
        base_price = 100
        returns = np.random.normal(0, 0.02, 100)
        prices = base_price * (1 + returns).cumprod()

        data = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 100)
        })

        # Introduce quality issues
        data.loc[10, 'close'] = 0  # Zero price
        data.loc[20, 'close'] = 10000  # Extreme price
        data.loc[30:35, 'close'] = data.loc[29, 'close']  # Flat period
        data.loc[40, 'close'] = None  # Missing value
        data.loc[50, 'volume'] = -100  # Negative volume
        data.loc[60, 'high'] = data.loc[60, 'close'] - 1  # Invalid OHLC

        # Duplicate date
        data = pd.concat([data, data.iloc[70:71]], ignore_index=True)

        return data

    @pytest.mark.asyncio
    async def test_check_market_data_perfect(self, checker, sample_data):
        """Test quality check on perfect data"""
        report = await checker.check_market_data(sample_data, "AAPL", "price")

        # Should have high quality score
        assert report.quality_score > 90
        assert report.quality_level == QualityLevel.EXCELLENT
        assert report.total_records == len(sample_data)
        assert report.valid_records == len(sample_data)
        assert len(report.issues) == 0

    @pytest.mark.asyncio
    async def test_check_market_data_with_issues(self, checker, problematic_data):
        """Test quality check on data with issues"""
        report = await checker.check_market_data(problematic_data, "AAPL", "price")

        # Should have lower quality score
        assert report.quality_score < 90
        assert report.valid_records < report.total_records
        assert len(report.issues) > 0

        # Check for specific issues
        issue_types = [issue.issue_type for issue in report.issues]
        assert "non_positive_prices" in issue_types
        assert "extreme_prices" in issue_types
        assert "missing_prices" in issue_types
        assert "negative_volume" in issue_types
        assert "duplicate_dates" in issue_types

    @pytest.mark.asyncio
    async def test_check_structure(self, checker):
        """Test structure validation"""
        # Valid data
        valid_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'open': np.random.randn(10),
            'high': np.random.randn(10),
            'low': np.random.randn(10),
            'close': np.random.randn(10)
        })
        issues = await checker._check_structure(valid_data, "price")
        assert len(issues) == 0

        # Missing columns
        invalid_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'open': np.random.randn(10)
        })
        issues = await checker._check_structure(invalid_data, "price")
        assert len(issues) > 0
        assert any(issue.issue_type == "missing_columns" for issue in issues)

        # Empty data
        empty_data = pd.DataFrame()
        issues = await checker._check_structure(empty_data, "price")
        assert len(issues) > 0
        assert any(issue.issue_type == "empty_data" for issue in issues)

    @pytest.mark.asyncio
    async def test_check_datetime(self, checker):
        """Test datetime validation"""
        # Valid dates
        valid_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10)
        })
        issues = await checker._check_datetime(valid_data)
        assert len(issues) == 0

        # Future dates
        future_date = datetime.now() + timedelta(days=1)
        future_data = pd.DataFrame({
            'date': [future_date]
        })
        issues = await checker._check_datetime(future_data)
        assert len(issues) > 0
        assert any(issue.issue_type == "future_dates" for issue in issues)

        # Duplicate dates
        duplicate_dates = pd.DataFrame({
            'date': [datetime(2020, 1, 1), datetime(2020, 1, 1)]
        })
        issues = await checker._check_datetime(duplicate_dates)
        assert len(issues) > 0
        assert any(issue.issue_type == "duplicate_dates" for issue in issues)

    @pytest.mark.asyncio
    async def test_check_price_data(self, checker):
        """Test price data validation"""
        # Create test data
        data = pd.DataFrame({
            'open': [100, 100, 0, 10000],  # Normal, Normal, Zero, Extreme
            'high': [105, 99, 105, 10005],  # Valid, Invalid, Valid, Valid
            'low': [95, 101, 95, 9995],  # Valid, Invalid, Valid, Valid
            'close': [104, 102, 0, 10000]  # Normal, Normal, Zero, Extreme
        })

        issues = await checker._check_price_data(data, "AAPL")

        # Should detect issues
        assert len(issues) > 0
        issue_types = [issue.issue_type for issue in issues]
        assert "non_positive_prices" in issue_types
        assert "extreme_prices" in issue_types
        assert "invalid_ohlc_high" in issue_types
        assert "invalid_ohlc_low" in issue_types

    @pytest.mark.asyncio
    async def test_check_volume_data(self, checker):
        """Test volume data validation"""
        # Create test data
        data = pd.DataFrame({
            'volume': [1000000, -100, 100000000, 0]  # Valid, Negative, Extreme, Zero
        })

        issues = await checker._check_volume_data(data, "AAPL")

        # Should detect negative volume
        assert len(issues) > 0
        issue_types = [issue.issue_type for issue in issues]
        assert "negative_volume" in issue_types

    @pytest.mark.asyncio
    async def test_check_missing_data(self, checker):
        """Test missing data detection"""
        # Create data with missing values
        data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'close': [1, 2, None, 4, None, None, 7, 8, 9, 10]
        })

        issues = await checker._check_missing_data(data)

        # Should detect missing data
        assert len(issues) > 0
        issue_types = [issue.issue_type for issue in issues]
        assert "high_missing_rate" in issue_types
        assert "consecutive_missing" in issue_types

    @pytest.mark.asyncio
    async def test_check_duplicates(self, checker):
        """Test duplicate data detection"""
        # Create data with duplicates
        data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=5)
        })
        # Add duplicate row
        data = pd.concat([data, data.iloc[2:3]], ignore_index=True)

        issues = await checker._check_duplicates(data)

        # Should detect duplicates
        assert len(issues) > 0
        issue_types = [issue.issue_type for issue in issues]
        assert "date_duplicates" in issue_types

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, checker):
        """Test statistical anomaly detection"""
        # Create data with clear outlier
        normal_data = np.random.normal(100, 5, 100)
        normal_data[50] = 200  # Clear outlier

        data = pd.DataFrame({
            'value': normal_data
        })

        issues = await checker._detect_anomalies(data, "AAPL")

        # Should detect outliers
        assert len(issues) > 0
        issue_types = [issue.issue_type for issue in issues]
        assert "statistical_outliers" in issue_types

    @pytest.mark.asyncio
    async def test_check_patterns(self, checker):
        """Test pattern-based validation"""
        # Create data with flat period
        dates = pd.date_range('2020-01-01', periods=20)
        prices = list(range(100, 120)) + [130] * 10  # Flat period

        data = pd.DataFrame({
            'date': dates,
            'close': prices
        })

        issues = await checker._check_patterns(data, "AAPL")

        # Should detect flat prices
        assert len(issues) > 0
        issue_types = [issue.issue_type for issue in issues]
        assert "flat_prices" in issue_types

    @pytest.mark.asyncio
    async def test_calculate_quality_score(self, checker):
        """Test quality score calculation"""
        # No issues - perfect score
        issues = []
        score = await checker._calculate_quality_score(pd.DataFrame({"a": [1, 2, 3]}), issues)
        assert score == 100.0

        # Critical issue
        critical_issue = QualityIssue(
            issue_type="critical",
            severity=AlertLevel.CRITICAL,
            message="Critical error"
        )
        issues = [critical_issue]
        score = await checker._calculate_quality_score(pd.DataFrame({"a": [1, 2, 3]}), issues)
        assert score == 80.0

        # Multiple issues
        warning_issue = QualityIssue(
            issue_type="warning",
            severity=AlertLevel.WARNING,
            message="Warning"
        )
        issues = [critical_issue, warning_issue]
        score = await checker._calculate_quality_score(pd.DataFrame({"a": [1, 2, 3]}), issues)
        assert score == 75.0

    def test_get_quality_level(self, checker):
        """Test quality level determination"""
        assert checker._get_quality_level(95) == QualityLevel.EXCELLENT
        assert checker._get_quality_level(80) == QualityLevel.GOOD
        assert checker._get_quality_level(65) == QualityLevel.FAIR
        assert checker._get_quality_level(50) == QualityLevel.POOR

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, checker):
        """Test recommendation generation"""
        # Critical issue
        critical_issue = QualityIssue(
            issue_type="missing_data",
            severity=AlertLevel.CRITICAL,
            message="Missing critical data",
            suggestion="Fix data source"
        )

        report = QualityReport(
            symbol="AAPL",
            data_type="price",
            total_records=100,
            valid_records=80,
            quality_score=60,
            quality_level=QualityLevel.FAIR,
            issues=[critical_issue],
            statistics={},
            recommendations=[],
            processing_time=1.0,
            timestamp=datetime.now()
        )

        recommendations = checker._generate_recommendations(
            report.issues,
            report.quality_level
        )

        assert len(recommendations) > 0
        assert any("URGENT" in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_store_quality_history(self, checker):
        """Test storing quality history"""
        report = QualityReport(
            symbol="AAPL",
            data_type="price",
            total_records=100,
            valid_records=100,
            quality_score=95,
            quality_level=QualityLevel.EXCELLENT,
            issues=[],
            statistics={},
            recommendations=[],
            processing_time=1.0,
            timestamp=datetime.now()
        )

        # Store report
        await checker._store_quality_history("AAPL", report)

        # Check if stored
        assert "AAPL" in checker.quality_history
        assert len(checker.quality_history["AAPL"]) == 1
        assert checker.quality_history["AAPL"][0].quality_score == 95

    @pytest.mark.asyncio
    async def test_get_quality_trend(self, checker):
        """Test quality trend analysis"""
        # Create multiple reports over time
        base_time = datetime.now()
        scores = [80, 85, 90, 88, 92]

        for i, score in enumerate(scores):
            report = QualityReport(
                symbol="AAPL",
                data_type="price",
                total_records=100,
                valid_records=100,
                quality_score=score,
                quality_level=QualityLevel.GOOD,
                issues=[],
                statistics={},
                recommendations=[],
                processing_time=1.0,
                timestamp=base_time - timedelta(days=i)
            )
            await checker._store_quality_history("AAPL", report)

        # Get trend
        trend = await checker.get_quality_trend("AAPL")

        assert trend["trend"] == "improving"
        assert trend["average_score"] == np.mean(scores)
        assert "latest_score" in trend

    @pytest.mark.asyncio
    async def test_batch_check(self, checker, sample_data):
        """Test batch quality checking"""
        data_dict = {
            "AAPL": sample_data,
            "MSFT": sample_data.copy(),
            "GOOGL": sample_data.copy()
        }

        results = await checker.batch_check(data_dict, "price")

        assert len(results) == 3
        assert all(symbol in results for symbol in data_dict.keys())
        assert all(isinstance(report, QualityReport) for report in results.values())

    @pytest.mark.asyncio
    async def test_generate_quality_summary(self, checker):
        """Test quality summary generation"""
        # Create multiple reports
        reports = {
            "AAPL": QualityReport(
                symbol="AAPL",
                data_type="price",
                total_records=100,
                valid_records=100,
                quality_score=95,
                quality_level=QualityLevel.EXCELLENT,
                issues=[],
                statistics={},
                recommendations=[],
                processing_time=1.0,
                timestamp=datetime.now()
            ),
            "MSFT": QualityReport(
                symbol="MSFT",
                data_type="price",
                total_records=100,
                valid_records=80,
                quality_score=60,
                quality_level=QualityLevel.FAIR,
                issues=[QualityIssue(
                    issue_type="missing_data",
                    severity=AlertLevel.WARNING,
                    message="Some data missing"
                )],
                statistics={},
                recommendations=[],
                processing_time=1.5,
                timestamp=datetime.now()
            )
        }

        summary = await checker.generate_quality_summary(reports)

        assert summary["total_symbols"] == 2
        assert summary["total_records"] == 200
        assert summary["average_quality_score"] == 77.5
        assert "excellent" in summary["quality_distribution"]
        assert "fair" in summary["quality_distribution"]
        assert "common_issues" in summary

class TestDataQualityConfig:
    """Test cases for DataQualityConfig"""

    def test_default_values(self):
        """Test default configuration values"""
        config = DataQualityConfig()

        assert config.max_price_change_pct == 50.0
        assert config.min_price == 0.01
        assert config.max_price == 1000000
        assert config.max_volume_change_pct == 1000.0
        assert config.missing_data_threshold == 0.05
        assert config.outlier_contamination == 0.1
        assert config.enable_statistical_detection is True
        assert config.enable_pattern_detection is True

    def test_custom_values(self):
        """Test custom configuration values"""
        config = DataQualityConfig(
            max_price_change_pct=30.0,
            outlier_contamination=0.05,
            enable_statistical_detection=False
        )

        assert config.max_price_change_pct == 30.0
        assert config.outlier_contamination == 0.05
        assert config.enable_statistical_detection is False

class TestQualityIssue:
    """Test cases for QualityIssue"""

    def test_quality_issue_creation(self):
        """Test QualityIssue creation"""
        issue = QualityIssue(
            issue_type="test_issue",
            severity=AlertLevel.WARNING,
            message="Test message",
            row_index=10,
            column="close",
            value=100.0,
            suggestion="Fix it"
        )

        assert issue.issue_type == "test_issue"
        assert issue.severity == AlertLevel.WARNING
        assert issue.message == "Test message"
        assert issue.row_index == 10
        assert issue.column == "close"
        assert issue.value == 100.0
        assert issue.suggestion == "Fix it"

class TestQualityReport:
    """Test cases for QualityReport"""

    def test_quality_report_creation(self):
        """Test QualityReport creation"""
        report = QualityReport(
            symbol="AAPL",
            data_type="price",
            total_records=100,
            valid_records=95,
            quality_score=85.0,
            quality_level=QualityLevel.GOOD,
            issues=[],
            statistics={"mean": 100},
            recommendations=["Check data source"],
            processing_time=1.5,
            timestamp=datetime.now()
        )

        assert report.symbol == "AAPL"
        assert report.data_type == "price"
        assert report.total_records == 100
        assert report.valid_records == 95
        assert report.quality_score == 85.0
        assert report.quality_level == QualityLevel.GOOD
        assert len(report.issues) == 0
        assert report.processing_time == 1.5

# Error handling tests
@pytest.mark.error_handling
class TestDataQualityCheckerErrors:
    """Error handling tests for DataQualityChecker"""

    @pytest.mark.asyncio
    async def test_empty_dataframe(self, checker):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame()
        report = await checker.check_market_data(empty_df, "AAPL", "price")

        assert report.quality_score == 0.0
        assert report.quality_level == QualityLevel.POOR
        assert len(report.issues) > 0

    @pytest.mark.asyncio
    async def test_invalid_column_types(self, checker):
        """Test handling of invalid column types"""
        invalid_df = pd.DataFrame({
            'date': ['2020-01-01', 'invalid_date', '2020-01-03'],
            'close': ['100', 'not_a_number', '102']
        })

        report = await checker.check_market_data(invalid_df, "AAPL", "price")

        assert report.quality_score < 100
        assert len(report.issues) > 0

    @pytest.mark.asyncio
    async def test_extreme_data_values(self, checker):
        """Test handling of extreme data values"""
        extreme_df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=3),
            'close': [1e10, -1e10, np.inf]
        })

        report = await checker.check_market_data(extreme_df, "AAPL", "price")

        assert report.quality_score < 90
        assert len(report.issues) > 0

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])