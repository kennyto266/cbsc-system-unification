"""
pytest configuration and fixtures for CBSC VectorBT testing
CBSC VectorBT测试的pytest配置和fixtures

This file contains shared fixtures and configuration for all CBSC tests.
包含所有CBSC测试的共享fixtures和配置。

Author: CBSC Backtesting System Team
Date: 2025-12-04
Version: 1.0
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import warnings

# Suppress warnings for cleaner test output
warnings.filterwarnings('ignore')

# Import CBSC components
from data_loader import CBSCDataLoader
from signal_generator import CBSCSignalGenerator
from cbsc_backtester import CBSCBacktester
from optimizer import CBSCOptimizer

@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings"""
    return {
        'sentiment_path': "CODEX--/warrant_sentiment_daily.csv",
        'test_symbol': "0700.HK",
        'test_data_days': 100,  # Reduced for faster testing
        'performance_targets': {
            'max_total_time': 30.0,
            'max_data_loading': 5.0,
            'max_signal_generation': 3.0,
            'max_backtesting': 20.0,
            'max_memory_mb': 2048
        },
        'optimization_config': {
            'backtest_config': {
                'initial_cash': 1000000,
                'fees': 0.003,
                'slippage': 0.001
            },
            'optimization_ranges': {
                'sentiment_threshold': [0.2, 0.3, 0.4],
                'rsi_overbought': [65, 70, 75],
                'rsi_oversold': [25, 30, 35],
                'signal_smoothing': [1, 3, 5],
                'extreme_sentiment_boost': [1.2, 1.5, 1.8]
            },
            'optimization_metric': 'sharpe_ratio',
            'max_combinations': 100,
            'cv_folds': 3
        }
    }

@pytest.fixture(scope="session")
def mock_cbsc_data(test_config):
    """Generate mock CBSC sentiment data for testing"""
    np.random.seed(42)  # For reproducible tests
    days = test_config['test_data_days']

    dates = pd.date_range('2024-01-01', periods=days, freq='D')

    # Generate realistic sentiment data
    bull_ratio = np.random.beta(2, 2, days)  # Beta distribution for realistic ratios
    bear_ratio = 1 - bull_ratio

    # Create sentiment levels based on ratios
    sentiment_levels = []
    for br in bull_ratio:
        if br > 0.7:
            sentiment_levels.append('EXTREME BULL')
        elif br > 0.55:
            sentiment_levels.append('MOD BULL')
        elif br > 0.45:
            sentiment_levels.append('NEUTRAL')
        elif br > 0.3:
            sentiment_levels.append('MOD BEAR')
        else:
            sentiment_levels.append('EXTREME BEAR')

    # Generate price data with some correlation to sentiment
    base_price = 25000
    price_changes = np.random.randn(days) * 200
    sentiment_impact = (bull_ratio - 0.5) * 500  # Sentiment affects price
    prices = base_price + np.cumsum(price_changes + sentiment_impact)

    # Generate turnover data
    base_turnover = 5e6
    bull_turnover = base_turnover * (1 + bull_ratio + np.random.randn(days) * 0.2)
    bear_turnover = base_turnover * (1 + bear_ratio + np.random.randn(days) * 0.2)

    # Generate signals based on sentiment
    signals = np.where(bull_ratio > 0.65, 1, np.where(bull_ratio < 0.35, -1, 0))

    data = pd.DataFrame({
        'Date': dates,
        'Bull_Ratio': bull_ratio,
        'Bull_Bear_Ratio': bull_ratio / np.maximum(bear_ratio, 1e-6),
        'Bull_Turnover_HKD': np.maximum(bull_turnover, 0),
        'Bear_Turnover_HKD': np.maximum(bear_turnover, 0),
        'Afternoon_Close': prices,
        'Daily_Return': np.concatenate([[0], np.diff(prices) / prices[:-1]]),
        'Signal': signals,
        'Sentiment_Level': sentiment_levels
    })

    return data

@pytest.fixture(scope="session")
def mock_price_data(mock_cbsc_data):
    """Generate mock price data aligned with sentiment data"""
    np.random.seed(123)

    base_prices = mock_cbsc_data['Afternoon_Close'].values

    # Generate OHLC from close prices
    noise_factor = 0.01
    opens = base_prices * (1 + np.random.randn(len(base_prices)) * noise_factor)
    highs = np.maximum(base_prices, opens) * (1 + np.abs(np.random.randn(len(base_prices))) * noise_factor)
    lows = np.minimum(base_prices, opens) * (1 - np.abs(np.random.randn(len(base_prices))) * noise_factor)
    closes = base_prices
    volumes = np.random.randint(1_000_000, 10_000_000, len(base_prices))

    price_data = pd.DataFrame({
        'Date': mock_cbsc_data['Date'],
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })

    return price_data

@pytest.fixture(scope="session")
def mock_features_data(mock_cbsc_data, mock_price_data):
    """Generate mock features data combining sentiment and price data"""
    # Merge sentiment and price data
    features_df = mock_cbsc_data.copy()

    # Add price columns
    price_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in price_columns:
        features_df[col] = mock_price_data[col].values

    # Calculate technical indicators
    features_df['Returns'] = features_df['close'].pct_change()
    features_df['MA5'] = features_df['close'].rolling(5).mean()
    features_df['MA20'] = features_df['close'].rolling(20).mean()

    # Calculate RSI
    def calculate_rsi(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    features_df['RSI'] = calculate_rsi(features_df['close'])

    # Add CBSC-specific features
    features_df['Total_Turnover'] = features_df['Bull_Turnover_HKD'] + features_df['Bear_Turnover_HKD']
    features_df['Sentiment_Strength'] = (features_df['Bull_Turnover_HKD'] - features_df['Bear_Turnover_HKD']) / features_df['Total_Turnover']
    features_df['Sentiment_Score'] = (features_df['Sentiment_Strength'] + 1) * 50

    # Drop rows with NaN values from rolling calculations
    features_df = features_df.dropna().reset_index(drop=True)

    return features_df

@pytest.fixture
def data_loader(test_config):
    """Create CBSCDataLoader instance for testing"""
    if Path(test_config['sentiment_path']).exists():
        return CBSCDataLoader(test_config['sentiment_path'])
    else:
        # Create a temporary CSV file for testing
        temp_data = mock_cbsc_data(test_config)
        temp_path = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_data.to_csv(temp_path.name, index=False)
        temp_path.close()

        try:
            loader = CBSCDataLoader(temp_path.name)
            yield loader
        finally:
            Path(temp_path.name).unlink()  # Clean up

@pytest.fixture
def signal_generator():
    """Create CBSCSignalGenerator instance for testing"""
    return CBSCSignalGenerator()

@pytest.fixture
def backtester(test_config):
    """Create CBSCBacktester instance for testing"""
    if Path(test_config['sentiment_path']).exists():
        return CBSCBacktester(test_config['sentiment_path'])
    else:
        # Use temporary file
        temp_data = mock_cbsc_data(test_config)
        temp_path = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_data.to_csv(temp_path.name, index=False)
        temp_path.close()

        try:
            backtester = CBSCBacktester(temp_path.name)
            yield backtester
        finally:
            Path(temp_path.name).unlink()

@pytest.fixture
def optimizer(test_config):
    """Create CBSCOptimizer instance for testing"""
    if Path(test_config['sentiment_path']).exists():
        return CBSCOptimizer(test_config['sentiment_path'], test_config['optimization_config'])
    else:
        # Use temporary file
        temp_data = mock_cbsc_data(test_config)
        temp_path = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_data.to_csv(temp_path.name, index=False)
        temp_path.close()

        try:
            optimizer = CBSCOptimizer(temp_path.name, test_config['optimization_config'])
            yield optimizer
        finally:
            Path(temp_path.name).unlink()

@pytest.fixture
def performance_monitor():
    """Context manager for monitoring performance"""
    import psutil
    import time

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.end_time = None
            self.end_memory = None

        def __enter__(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end_time = time.time()
            self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        @property
        def execution_time(self):
            return self.end_time - self.start_time if self.end_time else None

        @property
        def memory_used(self):
            return self.end_memory - self.start_memory if self.end_memory else None

        @property
        def total_memory(self):
            return self.end_memory if self.end_memory else None

    return PerformanceMonitor

# Custom pytest markers for CBSC testing
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interaction"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests with timing requirements"
    )
    config.addinivalue_line(
        "markers", "cbsc_specific: CBSC-specific functionality tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run (>30 seconds)"
    )
    config.addinivalue_line(
        "markers", "data_quality: Data validation and quality tests"
    )
    config.addinivalue_line(
        "markers", "edge_cases: Edge case and error handling tests"
    )
    config.addinivalue_line(
        "markers", "risk_management: Risk management and validation tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers dynamically"""
    for item in items:
        # Add markers based on test file/function names
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "cbsc" in item.nodeid.lower():
            item.add_marker(pytest.mark.cbsc_specific)
        if "data_quality" in item.nodeid or "quality" in item.nodeid:
            item.add_marker(pytest.mark.data_quality)
        if "edge" in item.nodeid or "error" in item.nodeid:
            item.add_marker(pytest.mark.edge_cases)

# Helper functions for testing
def assert_dataframe_equal(df1, df2, check_names=True, **kwargs):
    """Assert two DataFrames are equal with better error messages"""
    try:
        pd.testing.assert_frame_equal(df1, df2, check_names=check_names, **kwargs)
    except AssertionError as e:
        print(f"DataFrame comparison failed:")
        print(f"Shape mismatch: {df1.shape} vs {df2.shape}")
        print(f"Columns mismatch: {set(df1.columns) ^ set(df2.columns)}")
        if df1.shape == df2.shape:
            diff_mask = df1.ne(df2)
            diff_count = diff_mask.any(axis=1).sum()
            print(f"Different values in {diff_count} rows")
        raise

def create_test_report(test_results: Dict[str, Any]) -> str:
    """Create a formatted test report"""
    report_lines = [
        "CBSC VectorBT Test Report",
        "=" * 40,
        f"Generated at: {pd.Timestamp.now()}",
        ""
    ]

    for test_category, results in test_results.items():
        report_lines.append(f"{test_category}:")
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            report_lines.append(f"  {test_name}: {status}")
        report_lines.append("")

    return "\n".join(report_lines)