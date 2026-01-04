"""Test data storage layer functionality"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.strategies.optimization.data.storage import DataStorage


def test_data_storage_initialization():
    """Test DataStorage can be initialized"""
    storage = DataStorage()

    assert storage is not None
    assert storage.postgres_config is not None
    assert storage.influx_config is not None
    assert storage.postgres_config['database'] == 'cbsc'


def test_data_storage_save_and_retrieve():
    """Test saving and retrieving market data (requires PostgreSQL)"""
    storage = DataStorage()

    # Create sample data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    data = pd.DataFrame({
        'open': range(100),
        'high': range(100, 200),
        'low': range(50, 150),
        'close': range(75, 175),
        'volume': range(1000, 1100)
    }, index=dates)

    # Save data
    result = storage.save('TEST', data, 'daily')

    # If PostgreSQL is not available, save returns False
    # and get returns None - this is expected behavior
    if result is True:
        # Retrieve data only if save succeeded
        retrieved = storage.get('TEST', 'daily')

        assert retrieved is not None
        assert len(retrieved) == 100
        assert 'close' in retrieved.columns
    else:
        # PostgreSQL not available, test graceful degradation
        assert storage.postgres_conn is None
        retrieved = storage.get('TEST', 'daily')
        assert retrieved is None


def test_timeframe_validation_accepts_valid_timeframes():
    """Test that valid timeframes are accepted"""
    storage = DataStorage()

    # Test all allowed timeframes
    assert storage._validate_timeframe('minute') is True
    assert storage._validate_timeframe('daily') is True
    assert storage._validate_timeframe('weekly') is True


def test_timeframe_validation_rejects_invalid_timeframes():
    """Test that invalid timeframes are rejected to prevent SQL injection"""
    storage = DataStorage()

    # Test various invalid inputs that could be SQL injection attempts
    invalid_inputs = [
        "daily'; DROP TABLE market_data_daily; --",
        "daily OR '1'='1",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --",
        "daily' UNION SELECT * FROM users --",
        "'; EXEC xp_cmdshell('format c:'); --",
        "admin'--",
        "admin' /*",
        "admin' OR 1=1#",
        "'; DROP DATABASE market_data; --",
        "daily; DELETE FROM market_data_daily WHERE 1=1; --",
        "invalid_timeframe",
        "hourly",
        "monthly",
        "",
        "   ",
        "' OR ''='",
        "1' OR '1'='1",
        "../../etc/passwd",
        "<script>alert('xss')</script>",
    ]

    for invalid_input in invalid_inputs:
        assert storage._validate_timeframe(invalid_input) is False, \
            f"Should reject invalid timeframe: {invalid_input}"


def test_save_rejects_invalid_timeframe():
    """Test that save() method rejects invalid timeframes"""
    storage = DataStorage()

    # Create sample data
    dates = pd.date_range(end=datetime.now(), periods=10, freq='D')
    data = pd.DataFrame({
        'open': range(10),
        'high': range(10, 20),
        'low': range(5, 15),
        'close': range(7, 17),
        'volume': range(100, 110)
    }, index=dates)

    # Try to save with invalid timeframe (SQL injection attempt)
    result = storage.save('TEST', data, "daily'; DROP TABLE market_data_daily; --")

    # Should fail validation and return False
    assert result is False


def test_get_rejects_invalid_timeframe():
    """Test that get() method rejects invalid timeframes"""
    storage = DataStorage()

    # Try to retrieve with invalid timeframe (SQL injection attempt)
    result = storage.get('TEST', "daily' UNION SELECT * FROM users --")

    # Should fail validation and return None
    assert result is None

