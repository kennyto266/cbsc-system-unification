import random
"""
Test fixtures and utilities for comprehensive testing.
"""

import asyncio
import json
import logging
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock

import aiokafka
import docker
import numpy as np
import pandas as pd
import pytest
import redis.asyncio as redis
from docker.models.containers import Container
from docker.models.volumes import Volume
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..data_generators.market_data import MarketDataGenerator
from ..data_generators.trading_signals import TradingSignalGenerator
from ..mock_services.mock_api import MockAPIService
from ..mock_services.mock_cache import MockCacheService
from ..mock_services.mock_database import MockDatabaseService
from .core import TestConfig, TestEnvironment


class TestDataGenerator:
    """Comprehensive test data generator."""

    def __init__(self):
        self.market_generator = MarketDataGenerator()
        self.signal_generator = TradingSignalGenerator()
        self.logger = logging.getLogger(__name__)

    def generate_market_data(
        self,
        symbol: str = "00700.HK",
        days: int = 30,
        frequency: str = "1min",
        start_date: Optional[datetime] = None,
        price_range: tuple = (250.0, 350.0),
    ) -> pd.DataFrame:
        """Generate realistic market data."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)

        return self.market_generator.generate_ohlcv_data(
            symbol=symbol,
            start_date=start_date,
            days=days,
            frequency=frequency,
            price_range=price_range,
        )

    def generate_trading_signals(
        self, symbols: List[str], num_signals: int = 10, signal_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate trading signals."""
        if signal_types is None:
            signal_types = ["BUY", "SELL", "HOLD"]

        return self.signal_generator.generate_signals(
            symbols=symbols, count=num_signals, types=signal_types
        )

    def generate_portfolio_data(
        self,
        symbols: List[str],
        total_value: float = 1000000.0,
        allocations: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Generate portfolio data."""
        if allocations is None:
            # Equal allocation
            weight = 1.0 / len(symbols)
            allocations = {symbol: weight for symbol in symbols}

        portfolio = {
            "portfolio_id": str(uuid.uuid4()),
            "total_value": total_value,
            "positions": [],
            "created_at": datetime.now().isoformat(),
        }

        for symbol, weight in allocations.items():
            position_value = total_value * weight
            # Generate realistic share count and price
            price = np.random.uniform(50, 500)
            shares = int(position_value / price)

            portfolio["positions"].append(
                {
                    "symbol": symbol,
                    "shares": shares,
                    "avg_price": price,
                    "current_price": price * np.random.uniform(0.95, 1.05),
                    "market_value": shares * price,
                    "weight": weight,
                }
            )

        return portfolio

    def generate_risk_metrics(
        self, portfolio_value: float = 1000000.0, confidence_levels: List[float] = None
    ) -> Dict[str, Any]:
        """Generate risk metrics."""
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]

        return {
            "portfolio_value": portfolio_value,
            "var_95": {
                "confidence": 0.95,
                "value": portfolio_value * 0.02,
                "percentage": 2.0,
            },
            "var_99": {
                "confidence": 0.99,
                "value": portfolio_value * 0.03,
                "percentage": 3.0,
            },
            "max_drawdown": {"value": portfolio_value * 0.15, "percentage": 15.0},
            "sharpe_ratio": np.random.uniform(0.5, 2.5),
            "volatility": np.random.uniform(0.1, 0.3),
            "beta": np.random.uniform(0.8, 1.2),
            "alpha": np.random.uniform(-0.05, 0.1),
            "stress_scenarios": {
                "market_crash": -0.25,
                "interest_rate_shock": -0.15,
                "currency_crisis": -0.20,
            },
        }

    def generate_strategy_performance(
        self, days: int = 252, initial_capital: float = 100000.0
    ) -> Dict[str, Any]:
        """Generate strategy performance data."""
        # Generate daily returns
        daily_returns = np.random.normal(
            0.0008, 0.02, days
        )  # 0.08% daily return, 2% volatility
        cumulative_returns = np.cumprod(1 + daily_returns)

        portfolio_values = initial_capital * cumulative_returns
        peak_values = np.maximum.accumulate(portfolio_values)
        drawdowns = (portfolio_values - peak_values) / peak_values
        max_drawdown = np.min(drawdowns)

        # Calculate performance metrics
        total_return = (portfolio_values[-1] / initial_capital) - 1
        annual_return = (1 + total_return) ** (252 / days) - 1
        volatility = np.std(daily_returns) * np.sqrt(252)
        sharpe_ratio = annual_return / volatility

        return {
            "strategy_name": f"Test Strategy {uuid.uuid4().hex[:8]}",
            "start_date": (datetime.now() - timedelta(days=days)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "initial_capital": initial_capital,
            "final_value": portfolio_values[-1],
            "total_return": total_return,
            "annual_return": annual_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": abs(max_drawdown),
            "win_rate": np.random.uniform(0.45, 0.65),
            "profit_factor": np.random.uniform(1.1, 2.5),
            "calmar_ratio": (
                annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
            ),
            "daily_returns": daily_returns.tolist(),
            "portfolio_values": portfolio_values.tolist(),
        }


class MockServiceFactory:
    """Factory for creating mock services."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_mock_data_adapter(
        self, market_data: pd.DataFrame = None, error_rate: float = 0.0
    ):
        """Create mock data adapter."""
        mock_adapter = AsyncMock()

        if market_data is not None:
            mock_adapter.get_market_data.return_value = market_data.to_dict("records")

        if error_rate > 0:

            async def failing_adapter(*args, **kwargs):
                if np.random.random() < error_rate:
                    raise ConnectionError("Mock connection error")
                return market_data.to_dict("records") if market_data else []

            mock_adapter.get_market_data.side_effect = failing_adapter

        return mock_adapter

    def create_mock_ai_agent(
        self, agent_type: str, default_signal: str = "HOLD", confidence: float = 0.70
    ):
        """Create mock AI agent."""
        mock_agent = AsyncMock()

        async def mock_analyze(data):
            return {
                "signal": default_signal,
                "confidence": confidence,
                "reasoning": f"Mock {agent_type} analysis",
                "timestamp": datetime.now().isoformat(),
                "agent_type": agent_type,
            }

        mock_agent.analyze_market_data.side_effect = mock_analyze
        mock_agent.agent_type = agent_type
        mock_agent.confidence = confidence

        return mock_agent

    def create_mock_strategy_manager(self):
        """Create mock strategy manager."""
        mock_manager = AsyncMock()

        mock_manager.get_active_strategies.return_value = [
            {
                "strategy_id": f"strategy_{i:03d}",
                "name": f"Test Strategy {i}",
                "type": "momentum" if i % 2 == 0 else "mean_reversion",
                "status": "active",
                "created_at": datetime.now().isoformat(),
            }
            for i in range(1, 4)
        ]

        mock_manager.get_strategy_performance.return_value = {
            "sharpe_ratio": 1.85,
            "max_drawdown": 0.12,
            "total_return": 0.245,
            "volatility": 0.18,
            "win_rate": 0.62,
        }

        return mock_manager

    def create_mock_backtest_engine(self):
        """Create mock backtest engine."""
        mock_engine = AsyncMock()

        async def mock_backtest(strategy_id, start_date, end_date):
            return {
                "strategy_id": strategy_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "sharpe_ratio": np.random.uniform(0.5, 3.0),
                "max_drawdown": np.random.uniform(0.05, 0.25),
                "total_return": np.random.uniform(0.1, 0.5),
                "win_rate": np.random.uniform(0.45, 0.7),
                "trades_count": np.random.randint(50, 200),
                "avg_trade_return": np.random.uniform(0.001, 0.02),
            }

        mock_engine.run_backtest.side_effect = mock_backtest
        return mock_engine

    def create_mock_portfolio_manager(self):
        """Create mock portfolio manager."""
        mock_manager = AsyncMock()

        mock_manager.get_portfolio.return_value = {
            "portfolio_id": str(uuid.uuid4()),
            "total_value": 1000000.0,
            "cash_balance": 100000.0,
            "positions": [
                {
                    "symbol": "00700.HK",
                    "shares": 1000,
                    "avg_price": 320.0,
                    "current_price": 335.0,
                    "market_value": 335000.0,
                    "unrealized_pnl": 15000.0,
                },
                {
                    "symbol": "2800.HK",
                    "shares": 2000,
                    "avg_price": 45.0,
                    "current_price": 48.5,
                    "market_value": 97000.0,
                    "unrealized_pnl": 7000.0,
                },
            ],
            "last_updated": datetime.now().isoformat(),
        }

        return mock_manager


class TestEnvironmentManager:
    """Manages test environment lifecycle."""

    def __init__(self, config: TestConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.temp_dir: Optional[Path] = None
        self.docker_client: Optional[docker.DockerClient] = None
        self.containers: Dict[str, Container] = {}
        self.volumes: Dict[str, Volume] = {}

    async def setup(self):
        """Setup test environment."""
        self.logger.info("Setting up test environment")

        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="quant_test_"))
        self.logger.info(f"Created temporary directory: {self.temp_dir}")

        # Setup Docker if needed
        if self.config.environment in [
            TestEnvironment.DOCKER,
            TestEnvironment.KUBERNETES,
        ]:
            await self._setup_docker()

        # Setup test data
        await self._setup_test_data()

        # Setup configuration files
        await self._setup_config_files()

        self.logger.info("Test environment setup completed")

    async def teardown(self):
        """Teardown test environment."""
        self.logger.info("Tearing down test environment")

        # Stop and remove containers
        await self._cleanup_docker()

        # Remove temporary directory
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.logger.info(f"Removed temporary directory: {self.temp_dir}")

        self.logger.info("Test environment teardown completed")

    async def _setup_docker(self):
        """Setup Docker environment."""
        try:
            self.docker_client = docker.from_env()
            self.logger.info("Docker client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            raise

    async def _cleanup_docker(self):
        """Cleanup Docker resources."""
        if not self.docker_client:
            return

        # Stop and remove containers
        for name, container in self.containers.items():
            try:
                container.stop()
                container.remove()
                self.logger.info(f"Removed container: {name}")
            except Exception as e:
                self.logger.warning(f"Failed to remove container {name}: {e}")

        # Remove volumes
        for name, volume in self.volumes.items():
            try:
                volume.remove()
                self.logger.info(f"Removed volume: {name}")
            except Exception as e:
                self.logger.warning(f"Failed to remove volume {name}: {e}")

    async def _setup_test_data(self):
        """Setup test data files."""
        if not self.temp_dir:
            return

        data_dir = self.temp_dir / "data"
        data_dir.mkdir(exist_ok=True)

        # Create sample data files
        generator = TestDataGenerator()

        # Generate market data
        market_data = generator.generate_market_data()
        market_file = data_dir / "market_data.csv"
        market_data.to_csv(market_file, index=False)

        # Generate trading signals
        signals = generator.generate_trading_signals(["00700.HK", "2800.HK"])
        signals_file = data_dir / "trading_signals.json"
        with open(signals_file, "w") as f:
            json.dump(signals, f, indent=2, default=str)

        # Generate portfolio data
        portfolio = generator.generate_portfolio_data(["00700.HK", "2800.HK"])
        portfolio_file = data_dir / "portfolio.json"
        with open(portfolio_file, "w") as f:
            json.dump(portfolio, f, indent=2, default=str)

        self.logger.info(f"Test data created in: {data_dir}")

    async def _setup_config_files(self):
        """Setup configuration files."""
        if not self.temp_dir:
            return

        config_dir = self.temp_dir / "config"
        config_dir.mkdir(exist_ok=True)

        # Create test database configuration
        db_config = {
            "database": {
                "url": "sqlite + aiosqlite:///./test.db",
                "echo": False,
                "pool_pre_ping": True,
            }
        }
        db_file = config_dir / "database.json"
        with open(db_file, "w") as f:
            json.dump(db_config, f, indent=2)

        # Create test cache configuration
        cache_config = {
            "redis": {
                "url": "redis://localhost:6379 / 1",
                "encoding": "utf - 8",
                "decode_responses": True,
            }
        }
        cache_file = config_dir / "cache.json"
        with open(cache_file, "w") as f:
            json.dump(cache_config, f, indent=2)

        self.logger.info(f"Configuration files created in: {config_dir}")


class DatabaseFixture:
    """Database test fixture."""

    def __init__(self, database_url: str = "sqlite + aiosqlite:///:memory:"):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.logger = logging.getLogger(__name__)

    async def setup(self):
        """Setup database."""
        self.logger.info("Setting up test database")

        # Create async engine
        self.engine = create_async_engine(self.database_url, echo=False, future=True)

        # Create session factory
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables (would need actual models)
        # await self.create_tables()

        self.logger.info("Test database setup completed")

    async def teardown(self):
        """Teardown database."""
        self.logger.info("Tearing down test database")

        if self.engine:
            await self.engine.dispose()

        self.logger.info("Test database teardown completed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if not self.session_factory:
            raise RuntimeError("Database not setup")

        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


class CacheFixture:
    """Cache test fixture."""

    def __init__(self, redis_url: str = "redis://localhost:6379 / 1"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)

    async def setup(self):
        """Setup cache."""
        self.logger.info("Setting up test cache")

        try:
            self.redis_client = redis.from_url(self.redis_url)

            # Test connection
            await self.redis_client.ping()

            # Clear test database
            await self.redis_client.flushdb()

            self.logger.info("Test cache setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup Redis cache: {e}")
            # Fallback to mock cache
            self.redis_client = None

    async def teardown(self):
        """Teardown cache."""
        self.logger.info("Tearing down test cache")

        if self.redis_client:
            await self.redis_client.flushdb()
            await self.redis_client.close()

        self.logger.info("Test cache teardown completed")

    async def get_client(self) -> Optional[redis.Redis]:
        """Get Redis client."""
        return self.redis_client


class KafkaFixture:
    """Kafka test fixture."""

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[aiokafka.AIOKafkaProducer] = None
        self.consumer: Optional[aiokafka.AIOKafkaConsumer] = None
        self.logger = logging.getLogger(__name__)

    async def setup(self):
        """Setup Kafka."""
        self.logger.info("Setting up test Kafka")

        try:
            # Setup producer
            self.producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers
            )
            await self.producer.start()

            # Setup consumer
            self.consumer = aiokafka.AIOKafkaConsumer(
                "test_topic",
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset="earliest",
            )
            await self.consumer.start()

            self.logger.info("Test Kafka setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup Kafka: {e}")
            # Fallback to mock
            self.producer = None
            self.consumer = None

    async def teardown(self):
        """Teardown Kafka."""
        self.logger.info("Tearing down test Kafka")

        if self.producer:
            await self.producer.stop()

        if self.consumer:
            await self.consumer.stop()

        self.logger.info("Test Kafka teardown completed")

    async def send_message(self, topic: str, message: Dict[str, Any]):
        """Send message to Kafka topic."""
        if not self.producer:
            self.logger.warning("Kafka producer not available, message not sent")
            return

        import json

        await self.producer.send_and_wait(topic, json.dumps(message).encode("utf - 8"))

    async def consume_messages(
        self, topic: str, timeout: float = 1.0
    ) -> List[Dict[str, Any]]:
        """Consume messages from Kafka topic."""
        if not self.consumer:
            self.logger.warning("Kafka consumer not available, returning empty list")
            return []

        messages = []
        try:
            async for msg in self.consumer:
                import json

                messages.append(json.loads(msg.value.decode("utf - 8")))
                # Break after timeout or first message for testing
                break
        except Exception as e:
            self.logger.warning(f"Error consuming messages: {e}")

        return messages


# pytest fixtures
@pytest.fixture
async def test_data_generator():
    """Provide test data generator."""
    return TestDataGenerator()


@pytest.fixture
async def mock_service_factory():
    """Provide mock service factory."""
    return MockServiceFactory()


@pytest.fixture
async def test_environment_manager():
    """Provide test environment manager."""
    config = TestConfig(environment=TestEnvironment.LOCAL)
    manager = TestEnvironmentManager(config)
    await manager.setup()
    yield manager
    await manager.teardown()


@pytest.fixture
async def database_fixture():
    """Provide database fixture."""
    fixture = DatabaseFixture()
    await fixture.setup()
    yield fixture
    await fixture.teardown()


@pytest.fixture
async def cache_fixture():
    """Provide cache fixture."""
    fixture = CacheFixture()
    await fixture.setup()
    yield fixture
    await fixture.teardown()


@pytest.fixture
async def kafka_fixture():
    """Provide Kafka fixture."""
    fixture = KafkaFixture()
    await fixture.setup()
    yield fixture
    await fixture.teardown()
