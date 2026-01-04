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
