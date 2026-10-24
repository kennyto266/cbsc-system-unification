"""Test utilities for Hong Kong quantitative trading system.

This module provides comprehensive test utilities including mock data generators,
test fixtures, performance measurement tools, and assertion helpers.
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

import numpy as np
import pandas as pd


class TestDataGenerator:
    """Generator for test data."""
    
    @staticmethod
    def generate_market_data(
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        frequency: str = "1min",
        price_range: tuple = (100.0, 500.0),
        volume_range: tuple = (1000, 100000)
    ) -> pd.DataFrame:
        """Generate mock market data."""
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)
        
        # Generate price data using random walk
        initial_price = random.uniform(*price_range)
        price_changes = np.random.normal(0, 0.01, len(date_range))
        prices = [initial_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 0.01))  # Ensure positive price
        
        # Generate volume data
        volumes = [random.randint(*volume_range) for _ in range(len(date_range))]
        
        # Generate OHLC data
        data = []
        for i, (timestamp, price, volume) in enumerate(zip(date_range, prices, volumes)):
            # Generate OHLC from price
            high = price * random.uniform(1.0, 1.02)
            low = price * random.uniform(0.98, 1.0)
            open_price = prices[i-1] if i > 0 else price
            close_price = price
            
            data.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume,
                'bid': round(price - 0.01, 2),
                'ask': round(price + 0.01, 2)
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_trading_signals(
        symbols: List[str],
        num_signals: int,
        signal_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate mock trading signals."""
        if signal_types is None:
            signal_types = ['BUY', 'SELL', 'HOLD']
        
        signals = []
        for i in range(num_signals):
            signal = {
                'signal_id': f'SIG_{i:06d}',
                'symbol': random.choice(symbols),
                'action': random.choice(signal_types),
                'confidence': random.uniform(0.5, 1.0),
                'timestamp': datetime.now() - timedelta(minutes=random.randint(0, 60)),
                'price': random.uniform(100.0, 500.0),
                'quantity': random.randint(100, 10000),
                'stop_loss': random.uniform(0.95, 0.99),
                'take_profit': random.uniform(1.01, 1.10),
                'reasoning': f'Generated signal {i}',
                'agent_id': f'agent_{random.randint(1, 7)}'
            }
            signals.append(signal)
        
        return signals
    
    @staticmethod
    def generate_portfolio_data(
        symbols: List[str],
        total_value: float = 1000000.0,
        cash_ratio: float = 0.2
    ) -> Dict[str, Any]:
        """Generate mock portfolio data."""
        cash = total_value * cash_ratio
        invested_value = total_value - cash
        
        # Generate random weights for symbols
        weights = np.random.dirichlet(np.ones(len(symbols)))
        weights = weights / weights.sum()  # Normalize
        
        positions = {}
        for i, symbol in enumerate(symbols):
            position_value = invested_value * weights[i]
            quantity = random.randint(100, 10000)
            price = position_value / quantity
            
            positions[symbol] = {
                'quantity': quantity,
                'price': round(price, 2),
                'value': round(position_value, 2),
                'weight': round(weights[i], 4),
                'unrealized_pnl': round(random.uniform(-0.1, 0.1) * position_value, 2)
            }
        
        # Generate performance metrics
        performance = {
            'daily_return': random.uniform(-0.05, 0.05),
            'weekly_return': random.uniform(-0.1, 0.1),
            'monthly_return': random.uniform(-0.2, 0.2),
            'total_return': random.uniform(-0.3, 0.5),
            'sharpe_ratio': random.uniform(0.5, 2.5),
            'max_drawdown': random.uniform(0.05, 0.3),
            'volatility': random.uniform(0.1, 0.4),
            'beta': random.uniform(0.5, 1.5)
        }
        
        return {
            'total_value': total_value,
            'cash': cash,
            'invested_value': invested_value,
            'positions': positions,
            'performance': performance,
            'last_updated': datetime.now()
        }
    
    @staticmethod
    def generate_risk_metrics(
        portfolio_value: float = 1000000.0,
        confidence_levels: List[float] = None
    ) -> Dict[str, Any]:
        """Generate mock risk metrics."""
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]
        
        risk_metrics = {}
        
        # Generate VaR for different confidence levels
        for conf in confidence_levels:
            var_key = f'var_{int(conf * 100)}'
            risk_metrics[var_key] = {
                'value': random.uniform(0.01, 0.05) * portfolio_value,
                'confidence': conf,
                'method': 'historical_simulation'
            }
        
        # Generate other risk metrics
        risk_metrics.update({
            'expected_shortfall': {
                'value': random.uniform(0.02, 0.08) * portfolio_value,
                'confidence': 0.95
            },
            'max_drawdown': {
                'value': random.uniform(0.05, 0.25) * portfolio_value,
                'period': '1_year'
            },
            'volatility': {
                'daily': random.uniform(0.01, 0.03),
                'annualized': random.uniform(0.15, 0.40)
            },
            'beta': random.uniform(0.5, 1.5),
            'correlation_matrix': TestDataGenerator._generate_correlation_matrix(5)
        })
        
        return risk_metrics
    
    @staticmethod
    def _generate_correlation_matrix(size: int) -> np.ndarray:
        """Generate a valid correlation matrix."""
        # Generate random matrix
        A = np.random.randn(size, size)
        # Make it symmetric
        A = A + A.T
        # Make it positive definite
        A = A @ A.T
        # Normalize to get correlation matrix
        D = np.diag(1.0 / np.sqrt(np.diag(A)))
        return D @ A @ D
    
    @staticmethod
    def generate_system_metrics() -> Dict[str, Any]:
        """Generate mock system metrics."""
        return {
            'cpu_usage': random.uniform(10.0, 80.0),
            'memory_usage': random.uniform(100.0, 800.0),  # MB
            'disk_usage': random.uniform(20.0, 90.0),  # Percentage
            'network_io': random.uniform(100.0, 1000.0),  # KB/s
            'active_connections': random.randint(10, 100),
            'queue_length': random.randint(0, 50),
            'error_rate': random.uniform(0.0, 0.05),
            'response_time': random.uniform(0.01, 0.5),  # seconds
            'throughput': random.uniform(100.0, 1000.0),  # requests/second
            'timestamp': datetime.now()
        }


class MockComponentFactory:
    """Factory for creating mock components."""
    
    @staticmethod
    def create_mock_data_adapter(
        market_data: Optional[pd.DataFrame] = None,
        error_rate: float = 0.0
    ) -> AsyncMock:
        """Create mock data adapter."""
        mock_adapter = AsyncMock()
        
        if market_data is not None:
            mock_adapter.get_market_data.return_value = market_data.to_dict('records')
            mock_adapter.get_latest_price.return_value = market_data['close'].iloc[-1]
            mock_adapter.get_historical_data.return_value = market_data
        
        # Add error simulation
        if error_rate > 0:
            def error_wrapper(func):
                async def wrapper(*args, **kwargs):
                    if random.random() < error_rate:
                        raise ConnectionError("Mock connection error")
                    return await func(*args, **kwargs)
                return wrapper
            
            mock_adapter.get_market_data = error_wrapper(mock_adapter.get_market_data)
        
        return mock_adapter
    
    @staticmethod
    def create_mock_ai_agent(
        agent_id: str,
        signal_type: str = "BUY",
        confidence: float = 0.8,
        processing_time: float = 0.1
    ) -> AsyncMock:
        """Create mock AI agent."""
        mock_agent = AsyncMock()
        
        async def analyze_market_data(data):
            await asyncio.sleep(processing_time)  # Simulate processing time
            return {
                'agent_id': agent_id,
                'signal': signal_type,
                'confidence': confidence,
                'reasoning': f'Mock analysis by {agent_id}',
                'timestamp': datetime.now(),
                'processing_time': processing_time
            }
        
        mock_agent.analyze_market_data = analyze_market_data
        mock_agent.get_status.return_value = {
            'agent_id': agent_id,
            'status': 'running',
            'last_activity': datetime.now(),
            'processed_signals': random.randint(100, 1000)
        }
        
        return mock_agent
    
    @staticmethod
    def create_mock_strategy_manager(
        strategies: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncMock:
        """Create mock strategy manager."""
        if strategies is None:
            strategies = [
                {'strategy_id': 'strategy_001', 'name': 'Momentum Strategy', 'status': 'active'},
                {'strategy_id': 'strategy_002', 'name': 'Mean Reversion Strategy', 'status': 'active'}
            ]
        
        mock_manager = AsyncMock()
        mock_manager.get_active_strategies.return_value = strategies
        mock_manager.get_strategy_performance.return_value = {
            'sharpe_ratio': random.uniform(1.0, 2.5),
            'max_drawdown': random.uniform(0.05, 0.2),
            'total_return': random.uniform(0.1, 0.4)
        }
        
        return mock_manager
    
    @staticmethod
    def create_mock_backtest_engine() -> AsyncMock:
        """Create mock backtest engine."""
        mock_engine = AsyncMock()
        
        async def run_backtest(strategy_id, start_date, end_date, **kwargs):
            await asyncio.sleep(0.1)  # Simulate backtest time
            return {
                'strategy_id': strategy_id,
                'start_date': start_date,
                'end_date': end_date,
                'total_return': random.uniform(0.05, 0.3),
                'sharpe_ratio': random.uniform(1.0, 2.5),
                'max_drawdown': random.uniform(0.05, 0.25),
                'win_rate': random.uniform(0.4, 0.7),
                'profit_factor': random.uniform(1.1, 2.0),
                'total_trades': random.randint(50, 500),
                'backtest_duration': random.uniform(0.1, 1.0)
            }
        
        mock_engine.run_backtest = run_backtest
        return mock_engine


class PerformanceMeasurer:
    """Performance measurement utilities."""
    
    def __init__(self):
        self.measurements = {}
    
    def start_measurement(self, name: str) -> None:
        """Start performance measurement."""
        self.measurements[name] = {
            'start_time': time.time(),
            'end_time': None,
            'duration': None
        }
    
    def end_measurement(self, name: str) -> float:
        """End performance measurement and return duration."""
        if name not in self.measurements:
            raise ValueError(f"Measurement '{name}' not found")
        
        end_time = time.time()
        start_time = self.measurements[name]['start_time']
        duration = end_time - start_time
        
        self.measurements[name].update({
            'end_time': end_time,
            'duration': duration
        })
        
        return duration
    
    def get_measurement(self, name: str) -> Optional[Dict[str, Any]]:
        """Get measurement results."""
        return self.measurements.get(name)
    
    def get_all_measurements(self) -> Dict[str, Any]:
        """Get all measurement results."""
        return self.measurements.copy()
    
    def clear_measurements(self) -> None:
        """Clear all measurements."""
        self.measurements.clear()


class TestAssertions:
    """Custom assertion helpers for testing."""
    
    @staticmethod
    def assert_performance_within_bounds(
        actual_value: float,
        expected_min: float,
        expected_max: float,
        metric_name: str
    ) -> None:
        """Assert that performance metric is within expected bounds."""
        assert expected_min <= actual_value <= expected_max, \
            f"{metric_name} {actual_value} is not within bounds [{expected_min}, {expected_max}]"
    
    @staticmethod
    def assert_data_structure_valid(
        data: Any,
        required_fields: List[str],
        data_name: str = "data"
    ) -> None:
        """Assert that data structure contains required fields."""
        if isinstance(data, dict):
            missing_fields = [field for field in required_fields if field not in data]
            assert not missing_fields, \
                f"{data_name} is missing required fields: {missing_fields}"
        elif isinstance(data, list) and data:
            # Check first item in list
            TestAssertions.assert_data_structure_valid(data[0], required_fields, f"{data_name}[0]")
        else:
            assert False, f"{data_name} is not a valid data structure"
    
    @staticmethod
    def assert_trading_signal_valid(signal: Dict[str, Any]) -> None:
        """Assert that trading signal is valid."""
        required_fields = ['symbol', 'action', 'confidence', 'timestamp']
        TestAssertions.assert_data_structure_valid(signal, required_fields, "trading signal")
        
        assert signal['action'] in ['BUY', 'SELL', 'HOLD'], \
            f"Invalid action: {signal['action']}"
        assert 0.0 <= signal['confidence'] <= 1.0, \
            f"Confidence must be between 0 and 1: {signal['confidence']}"
        assert isinstance(signal['timestamp'], datetime), \
            f"Timestamp must be datetime object: {type(signal['timestamp'])}"
    
    @staticmethod
    def assert_portfolio_valid(portfolio: Dict[str, Any]) -> None:
        """Assert that portfolio data is valid."""
        required_fields = ['total_value', 'cash', 'positions', 'performance']
        TestAssertions.assert_data_structure_valid(portfolio, required_fields, "portfolio")
        
        assert portfolio['total_value'] > 0, "Total value must be positive"
        assert portfolio['cash'] >= 0, "Cash must be non-negative"
        assert isinstance(portfolio['positions'], dict), "Positions must be a dictionary"
        assert isinstance(portfolio['performance'], dict), "Performance must be a dictionary"


class TestEnvironment:
    """Test environment management."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.test_dir = Path(f"test_data/{test_name}")
        self.logger = logging.getLogger(f"test.{test_name}")
        
    async def setup(self) -> None:
        """Setup test environment."""
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Test environment setup: {self.test_dir}")
    
    async def cleanup(self) -> None:
        """Cleanup test environment."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.logger.info(f"Test environment cleaned up: {self.test_dir}")
    
    def create_test_file(self, filename: str, content: str) -> Path:
        """Create test file with content."""
        file_path = self.test_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path
    
    def create_test_config(self, config: Dict[str, Any]) -> Path:
        """Create test configuration file."""
        import yaml
        config_file = self.test_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        return config_file


class AsyncTestRunner:
    """Async test runner utilities."""
    
    @staticmethod
    async def run_concurrent_tasks(
        tasks: List[callable],
        max_concurrent: int = 10,
        timeout: float = 30.0
    ) -> List[Any]:
        """Run tasks concurrently with limits."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_task(task):
            async with semaphore:
                return await task()
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[limited_task(task) for task in tasks]),
                timeout=timeout
            )
            return results
        except asyncio.TimeoutError:
            raise AssertionError(f"Concurrent tasks timed out after {timeout} seconds")
    
    @staticmethod
    async def run_with_retry(
        func: callable,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """Run function with retry logic."""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func()
            except exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                else:
                    raise last_exception
        
        raise last_exception


class TestDataManager:
    """Test data management utilities."""
    
    def __init__(self, base_dir: str = "test_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def save_test_data(self, data: Any, filename: str) -> Path:
        """Save test data to file."""
        file_path = self.base_dir / filename
        
        if filename.endswith('.json'):
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif filename.endswith('.csv'):
            if isinstance(data, pd.DataFrame):
                data.to_csv(file_path, index=False)
            else:
                pd.DataFrame(data).to_csv(file_path, index=False)
        else:
            file_path.write_text(str(data))
        
        return file_path
    
    def load_test_data(self, filename: str) -> Any:
        """Load test data from file."""
        file_path = self.base_dir / filename
        
        if filename.endswith('.json'):
            with open(file_path, 'r') as f:
                return json.load(f)
        elif filename.endswith('.csv'):
            return pd.read_csv(file_path)
        else:
            return file_path.read_text()
    
    def cleanup_test_data(self) -> None:
        """Cleanup all test data."""
        import shutil
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
        self.base_dir.mkdir(exist_ok=True)


# Test fixtures
@pytest.fixture
def test_data_generator():
    """Fixture for test data generator."""
    return TestDataGenerator()


@pytest.fixture
def mock_component_factory():
    """Fixture for mock component factory."""
    return MockComponentFactory()


@pytest.fixture
def performance_measurer():
    """Fixture for performance measurer."""
    return PerformanceMeasurer()


@pytest.fixture
def test_environment():
    """Fixture for test environment."""
    env = TestEnvironment("test_session")
    yield env
    # Cleanup after test
    import asyncio
    asyncio.run(env.cleanup())


@pytest.fixture
def test_data_manager():
    """Fixture for test data manager."""
    manager = TestDataManager()
    yield manager
    # Cleanup after test
    manager.cleanup_test_data()


if __name__ == "__main__":
    # Example usage
    generator = TestDataGenerator()
    
    # Generate test data
    market_data = generator.generate_market_data(
        symbol="00700.HK",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        frequency="1min"
    )
    
    print(f"Generated {len(market_data)} market data records")
    print(market_data.head())
    
    # Generate trading signals
    signals = generator.generate_trading_signals(
        symbols=["00700.HK", "2800.HK"],
        num_signals=10
    )
    
    print(f"Generated {len(signals)} trading signals")
    print(signals[0])
