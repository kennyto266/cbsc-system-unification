"""Configuration and fixtures for integration tests.

This module provides shared configuration, fixtures, and utilities
for all integration tests in the Hong Kong quantitative trading system.
"""

import asyncio
import logging
import os
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

# Import system components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.helpers.test_utils import TestDataGenerator, MockComponentFactory, TestEnvironment


# Test configuration
@pytest.fixture(scope="session")
def test_config():
    """Test configuration for integration tests."""
    return {
        'test_system_id': 'integration_test_system',
        'test_system_name': 'Integration Test Trading System',
        'test_version': '1.0.0-test',
        'test_environment': 'test',
        'debug_mode': True,
        'log_level': 'DEBUG',
        'test_data_path': 'test_data/integration',
        'test_timeout': 300,  # 5 minutes
        'test_retries': 3,
        'test_parallel_workers': 4
    }


# Test data generators
@pytest.fixture(scope="session")
def test_data_generator():
    """Test data generator fixture."""
    return TestDataGenerator()


@pytest.fixture(scope="session")
def mock_component_factory():
    """Mock component factory fixture."""
    return MockComponentFactory()


# Test environment management
@pytest.fixture(scope="function")
async def test_environment():
    """Test environment fixture."""
    env = TestEnvironment("integration_test")
    await env.setup()
    yield env
    await env.cleanup()


# Test data fixtures
@pytest.fixture(scope="function")
def sample_market_data(test_data_generator):
    """Sample market data fixture."""
    return test_data_generator.generate_market_data(
        symbol="00700.HK",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        frequency="1min"
    )


@pytest.fixture(scope="function")
def sample_trading_signals(test_data_generator):
    """Sample trading signals fixture."""
    return test_data_generator.generate_trading_signals(
        symbols=["00700.HK", "2800.HK", "0700.HK"],
        num_signals=20
    )


@pytest.fixture(scope="function")
def sample_portfolio_data(test_data_generator):
    """Sample portfolio data fixture."""
    return test_data_generator.generate_portfolio_data(
        symbols=["00700.HK", "2800.HK", "0700.HK"],
        total_value=1000000.0
    )


@pytest.fixture(scope="function")
def sample_risk_metrics(test_data_generator):
    """Sample risk metrics fixture."""
    return test_data_generator.generate_risk_metrics(
        portfolio_value=1000000.0
    )


@pytest.fixture(scope="function")
def sample_system_metrics(test_data_generator):
    """Sample system metrics fixture."""
    return test_data_generator.generate_system_metrics()


# Mock component fixtures
@pytest.fixture(scope="function")
def mock_data_adapter(sample_market_data, mock_component_factory):
    """Mock data adapter fixture."""
    return mock_component_factory.create_mock_data_adapter(sample_market_data)


@pytest.fixture(scope="function")
def mock_quantitative_analyst(mock_component_factory):
    """Mock quantitative analyst fixture."""
    return mock_component_factory.create_mock_ai_agent(
        agent_id="quantitative_analyst",
        signal_type="BUY",
        confidence=0.85
    )


@pytest.fixture(scope="function")
def mock_quantitative_trader(mock_component_factory):
    """Mock quantitative trader fixture."""
    return mock_component_factory.create_mock_ai_agent(
        agent_id="quantitative_trader",
        signal_type="BUY",
        confidence=0.80
    )


@pytest.fixture(scope="function")
def mock_portfolio_manager(mock_component_factory):
    """Mock portfolio manager fixture."""
    return mock_component_factory.create_mock_ai_agent(
        agent_id="portfolio_manager",
        signal_type="BUY",
        confidence=0.75
    )


@pytest.fixture(scope="function")
def mock_risk_analyst(mock_component_factory):
    """Mock risk analyst fixture."""
    return mock_component_factory.create_mock_ai_agent(
        agent_id="risk_analyst",
        signal_type="BUY",
        confidence=0.70
    )


@pytest.fixture(scope="function")
def mock_data_scientist(mock_component_factory):
    """Mock data scientist fixture."""
    return mock_component_factory.create_mock_ai_agent(
        agent_id="data_scientist",
        signal_type="BUY",
        confidence=0.75
    )


@pytest.fixture(scope="function")
def mock_quantitative_engineer(mock_component_factory):
    """Mock quantitative engineer fixture."""
    return mock_component_factory.create_mock_ai_agent(
        agent_id="quantitative_engineer",
        signal_type="BUY",
        confidence=0.65
    )


@pytest.fixture(scope="function")
def mock_research_analyst(mock_component_factory):
    """Mock research analyst fixture."""
    return mock_component_factory.create_mock_ai_agent(
        agent_id="research_analyst",
        signal_type="BUY",
        confidence=0.70
    )


@pytest.fixture(scope="function")
def mock_strategy_manager(mock_component_factory):
    """Mock strategy manager fixture."""
    return mock_component_factory.create_mock_strategy_manager()


@pytest.fixture(scope="function")
def mock_backtest_engine(mock_component_factory):
    """Mock backtest engine fixture."""
    return mock_component_factory.create_mock_backtest_engine()


# System integration fixtures
@pytest.fixture(scope="function")
def integration_config(test_config):
    """Integration configuration fixture."""
    from src.integration.system_integration import IntegrationConfig
    
    return IntegrationConfig(
        system_id=test_config['test_system_id'],
        system_name=test_config['test_system_name'],
        version=test_config['test_version'],
        environment=test_config['test_environment'],
        debug_mode=test_config['debug_mode']
    )


@pytest.fixture(scope="function")
async def system_integration(integration_config):
    """System integration fixture."""
    from src.integration.system_integration import SystemIntegration
    
    system = SystemIntegration(integration_config)
    await system.initialize()
    yield system
    await system.shutdown()


# Test utilities
@pytest.fixture(scope="function")
def test_logger():
    """Test logger fixture."""
    logger = logging.getLogger("integration_test")
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


@pytest.fixture(scope="function")
def performance_measurer():
    """Performance measurer fixture."""
    from tests.helpers.test_utils import PerformanceMeasurer
    return PerformanceMeasurer()


# Test data management
@pytest.fixture(scope="function")
def test_data_manager():
    """Test data manager fixture."""
    from tests.helpers.test_utils import TestDataManager
    manager = TestDataManager("test_data/integration")
    yield manager
    manager.cleanup_test_data()


# Async test utilities
@pytest.fixture(scope="function")
def event_loop():
    """Event loop fixture for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "stress: mark test as stress test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow test"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    # Add markers based on test names
    for item in items:
        if "performance" in item.name:
            item.add_marker(pytest.mark.performance)
        if "stress" in item.name:
            item.add_marker(pytest.mark.stress)
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)
        if "integration" in item.name:
            item.add_marker(pytest.mark.integration)


# Test session setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """Setup test session."""
    # Create test directories
    test_dirs = [
        "test_data/integration",
        "test_data/performance",
        "test_data/stress",
        "logs/integration"
    ]
    
    for test_dir in test_dirs:
        Path(test_dir).mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/integration/test_session.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("test_session")
    logger.info("Integration test session started")
    
    yield
    
    # Cleanup test session
    logger.info("Integration test session completed")


# Test error handling
@pytest.fixture(scope="function")
def error_handler():
    """Error handler fixture."""
    def handle_error(error, context=""):
        """Handle test errors."""
        logger = logging.getLogger("error_handler")
        logger.error(f"Test error in {context}: {error}")
        raise error
    
    return handle_error


# Test timeout configuration
@pytest.fixture(scope="function")
def test_timeout(test_config):
    """Test timeout fixture."""
    return test_config['test_timeout']


# Test retry configuration
@pytest.fixture(scope="function")
def test_retries(test_config):
    """Test retries fixture."""
    return test_config['test_retries']


# Test parallel workers configuration
@pytest.fixture(scope="function")
def test_parallel_workers(test_config):
    """Test parallel workers fixture."""
    return test_config['test_parallel_workers']


# Test data validation
@pytest.fixture(scope="function")
def data_validator():
    """Data validator fixture."""
    def validate_market_data(data):
        """Validate market data."""
        if not isinstance(data, (list, pd.DataFrame)):
            raise ValueError("Data must be a list or DataFrame")
        
        if isinstance(data, list) and len(data) == 0:
            raise ValueError("Data cannot be empty")
        
        if isinstance(data, pd.DataFrame) and len(data) == 0:
            raise ValueError("Data cannot be empty")
        
        return True
    
    def validate_trading_signal(signal):
        """Validate trading signal."""
        required_fields = ['symbol', 'action', 'confidence', 'timestamp']
        for field in required_fields:
            if field not in signal:
                raise ValueError(f"Missing required field: {field}")
        
        if signal['action'] not in ['BUY', 'SELL', 'HOLD']:
            raise ValueError(f"Invalid action: {signal['action']}")
        
        if not 0 <= signal['confidence'] <= 1:
            raise ValueError(f"Confidence must be between 0 and 1: {signal['confidence']}")
        
        return True
    
    return {
        'validate_market_data': validate_market_data,
        'validate_trading_signal': validate_trading_signal
    }


# Test performance benchmarks
@pytest.fixture(scope="function")
def performance_benchmarks():
    """Performance benchmarks fixture."""
    return {
        'min_throughput': 100,  # requests per second
        'max_response_time': 1.0,  # seconds
        'min_success_rate': 0.95,  # 95%
        'max_memory_usage': 1000,  # MB
        'min_cpu_efficiency': 0.5  # 50%
    }


# Test cleanup utilities
@pytest.fixture(scope="function", autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test."""
    yield
    
    # Cleanup temporary files
    import tempfile
    import shutil
    
    temp_dir = tempfile.gettempdir()
    test_files = list(Path(temp_dir).glob("test_*"))
    
    for test_file in test_files:
        try:
            if test_file.is_file():
                test_file.unlink()
            elif test_file.is_dir():
                shutil.rmtree(test_file)
        except Exception:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    # Run configuration test
    import pytest
    pytest.main([__file__, "-v"])
