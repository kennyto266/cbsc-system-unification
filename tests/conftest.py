"""
Pytest configuration for HKEX integration tests

Simplified configuration that avoids importing the full main application
which has complex dependencies. This focuses on database and service layer testing.
"""

import pytest
import asyncio
import sys
import os
from typing import Generator, Dict, Any
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_available():
    """Check if test database is available"""
    try:
        from src.database.connection import get_db_connection
        conn = get_db_connection()
        conn.close()
        return True
    except Exception as e:
        print(f"Note: Database not available for integration tests: {e}")
        return False


@pytest.fixture
def db_connection(test_db_available):
    """
    Create database connection for tests that need it
    Tests are skipped if database is not available
    """
    if not test_db_available:
        pytest.skip("Database not available")

    from src.database.connection import get_db_connection

    conn = get_db_connection()
    yield conn

    try:
        conn.close()
    except:
        pass


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_db_connection():
    """Create a mock database connection for unit tests"""
    mock_conn = Mock()
    mock_cursor = Mock()

    # Setup cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)

    return mock_conn


@pytest.fixture
def sample_indicators_data():
    """Sample market indicators data for testing"""
    return [
        {
            'date': '2025-12-20',
            'advance_decline_ratio': 0.44,
            'volume_change_percent': 5.2,
            'sentiment_score': 17.64,
            'breadth_momentum': 0
        },
        {
            'date': '2025-12-21',
            'advance_decline_ratio': 0.55,
            'volume_change_percent': 3.1,
            'sentiment_score': 22.5,
            'breadth_momentum': 0
        },
        {
            'date': '2025-12-22',
            'advance_decline_ratio': 0.62,
            'volume_change_percent': -2.5,
            'sentiment_score': 15.0,
            'breadth_momentum': 0
        }
    ]


# =============================================================================
# Custom Markers
# =============================================================================

def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "database: Tests that require database connection"
    )
    config.addinivalue_line(
        "markers", "api: Tests that verify API endpoints"
    )
    config.addinivalue_line(
        "markers", "service: Tests for service layer"
    )
    config.addinivalue_line(
        "markers", "integration: Full integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )


# =============================================================================
# Environment Setup
# =============================================================================

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
