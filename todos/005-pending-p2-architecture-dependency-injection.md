---
status: pending
priority: p2
issue_id: "005"
tags: [architecture, dependency-injection, maintainability, code-review]
dependencies: []
---

# Problem Statement

Phase 3 real-time infrastructure lacks proper dependency management, configuration systems, and architectural patterns needed for production maintainability, testing, and scalability.

# Findings

## Architectural Analysis Results

**Critical architectural issues limiting production readiness:**

### 1. Hard-coded Dependencies
- Direct instantiation of Redis clients, executors, and components
- No dependency injection or inversion of control
- Components tightly coupled to specific implementations
- Difficult to test in isolation

### 2. Missing Configuration Management
- Hard-coded configuration values throughout codebase
- No environment-specific configurations
- No centralized configuration management
- Runtime configuration changes impossible

### 3. No Interface Abstractions
- Missing abstract base classes and interfaces
- Concrete implementations directly referenced
- No ability to swap implementations for testing or production
- Violates dependency inversion principle

### 4. Lifecycle Management Issues
- No proper component startup/shutdown coordination
- Resource cleanup inconsistent across components
- Missing health checks and status monitoring
- No graceful degradation patterns

### 5. Testing Infrastructure Gaps
- Components difficult to unit test due to hard dependencies
- No mocking or test double patterns
- Integration testing requires full system setup
- No contract testing between components

# Proposed Solutions

## Solution 1: Dependency Injection Container (Recommended)

**Description:** Implement comprehensive DI container for component lifecycle management

**Implementation:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Type, TypeVar, Any, Optional, Callable
from dataclasses import dataclass
import inspect
import asyncio
from contextlib import asynccontextmanager

T = TypeVar('T')

class DIContainer:
    """Comprehensive dependency injection container for Phase 3 components."""

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._instances: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._creation_stack: set[Type] = set()

    def register_singleton(
        self,
        interface: Type[T],
        implementation: Type[T],
        factory: Optional[Callable[[], T]] = None
    ) -> 'DIContainer':
        """Register singleton service."""
        self._services[interface] = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        return self

    def register_transient(
        self,
        interface: Type[T],
        implementation: Type[T],
        factory: Optional[Callable[[], T]] = None
    ) -> 'DIContainer':
        """Register transient service (new instance each time)."""
        self._services[interface] = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        return self

    def register_scoped(
        self,
        interface: Type[T],
        implementation: Type[T],
        factory: Optional[Callable[[], T]] = None
    ) -> 'DIContainer':
        """Register scoped service (one instance per scope)."""
        self._services[interface] = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED
        )
        return self

    async def resolve(self, interface: Type[T]) -> T:
        """Resolve service instance with dependency injection."""
        if interface not in self._services:
            raise ValueError(f"Service {interface} not registered")

        # Check for circular dependencies
        if interface in self._creation_stack:
            cycle_path = " -> ".join(str(t) for t in list(self._creation_stack) + [interface])
            raise CircularDependencyError(f"Circular dependency detected: {cycle_path}")

        descriptor = self._services[interface]

        # Handle singletons
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]

        # Create instance
        self._creation_stack.add(interface)
        try:
            if descriptor.factory:
                instance = await descriptor.factory(self)
            else:
                instance = await self._create_instance(descriptor)

            # Store singleton
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                self._singletons[interface] = instance

            return instance
        finally:
            self._creation_stack.remove(interface)

    async def _create_instance(self, descriptor: 'ServiceDescriptor') -> Any:
        """Create instance with constructor dependency injection."""
        implementation_class = descriptor.implementation

        # Get constructor signature
        sig = inspect.signature(implementation_class.__init__)
        parameters = sig.parameters

        # Prepare constructor arguments
        kwargs = {}
        for param_name, param in parameters.items():
            if param_name == 'self':
                continue

            # Check for type hints
            if param.annotation != inspect.Parameter.empty:
                dependency_type = param.annotation
                try:
                    kwargs[param_name] = await self.resolve(dependency_type)
                except ValueError:
                    # Optional dependency not registered
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        raise DependencyResolutionError(
                            f"Required dependency {dependency_type} not found for {implementation_class}"
                        )
            elif param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default

        # Create instance
        return implementation_class(**kwargs)

    @asynccontextmanager
    async def scope(self):
        """Create a scoped context for scoped services."""
        old_instances = self._instances.copy()
        try:
            yield self
        finally:
            # Cleanup scoped instances
            for instance in self._instances.values():
                if hasattr(instance, 'cleanup'):
                    try:
                        await instance.cleanup()
                    except Exception as e:
                        logger.warning(f"Error cleaning up scoped instance: {e}")
            self._instances = old_instances

    async def shutdown(self):
        """Shutdown all services and cleanup resources."""
        logger.info("Shutting down DI container")

        # Cleanup all instances in reverse creation order
        for instance in list(self._singletons.values())[::-1]:
            if hasattr(instance, 'cleanup'):
                try:
                    await instance.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up instance: {e}")

        self._singletons.clear()
        self._instances.clear()

@dataclass
class ServiceDescriptor:
    """Service registration descriptor."""
    interface: Type
    implementation: Type
    factory: Optional[Callable] = None
    lifetime: 'ServiceLifetime' = ServiceLifetime.TRANSIENT

class ServiceLifetime:
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class CircularDependencyError(Exception):
    """Raised when circular dependency is detected."""
    pass

class DependencyResolutionError(Exception):
    """Raised when dependency cannot be resolved."""
    pass

# Interface definitions for Phase 3 components
class ICacheManager(ABC):
    """Interface for cache management."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check cache health."""
        pass

class IWebSocketServer(ABC):
    """Interface for WebSocket server."""

    @abstractmethod
    async def start(self, host: str, port: int) -> None:
        """Start WebSocket server."""
        pass

    @abstractmethod
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all clients."""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        pass

class IDataValidator(ABC):
    """Interface for data validation."""

    @abstractmethod
    async def validate_data_point(self, data_point: MarketDataPoint) -> ValidationResult:
        """Validate a single data point."""
        pass

    @abstractmethod
    async def get_quality_report(self) -> Dict[str, Any]:
        """Get validation quality report."""
        pass

# Concrete implementations with dependency injection
class ProductionCacheManager(ICacheManager):
    """Production Redis cache manager with dependency injection."""

    def __init__(
        self,
        config: 'RedisConfig',
        serializer: ISerializer,
        health_checker: IHealthChecker
    ):
        self.config = config
        self.serializer = serializer
        self.health_checker = health_checker
        self.redis_client: Optional[aioredis.Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        self.redis_client = aioredis.Redis.from_url(
            self.config.redis_url,
            **self.config.connection_options
        )
        await self.redis_client.ping()
        logger.info("Redis connection established")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            raise CacheError("Cache not initialized")

        try:
            data = await self.redis_client.get(key)
            if data:
                return self.serializer.deserialize(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self.redis_client:
            raise CacheError("Cache not initialized")

        try:
            serialized_data = self.serializer.serialize(value)
            if ttl:
                return await self.redis_client.setex(key, ttl, serialized_data)
            else:
                return await self.redis_client.set(key, serialized_data)
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False

    async def health_check(self) -> bool:
        """Check cache health."""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except Exception:
            return False

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.redis_client:
            await self.redis_client.close()

# Container registration
def setup_container(config: 'AppConfig') -> DIContainer:
    """Set up dependency injection container with all Phase 3 services."""
    container = DIContainer()

    # Configuration
    container.register_singleton(AppConfig, lambda: config)

    # Redis configuration
    container.register_singleton(RedisConfig, lambda: config.redis)

    # Core services
    container.register_singleton(ISerializer, OptimizedMessageSerializer)
    container.register_singleton(IHealthChecker, RedisHealthChecker)
    container.register_singleton(ICacheManager, ProductionCacheManager)

    # WebSocket components
    container.register_singleton(IConnectionManager, WebSocketConnectionManager)
    container.register_singleton(IWebSocketServer, RealtimeWebSocketServer)

    # Data processing
    container.register_singleton(IDataValidator, MultiSourceDataValidator)
    container.register_singleton(IDataProcessor, HighPerformanceDataProcessor)
    container.register_singleton(ISignalGenerator, MarketSignalGenerator)

    # Monitoring
    container.register_singleton(IMetricsCollector, PrometheusMetricsCollector)
    container.register_singleton(IHealthChecker, SystemHealthChecker)

    return container

# Application startup with DI container
class RealtimeApplication:
    """Main application class with dependency injection."""

    def __init__(self, container: DIContainer):
        self.container = container
        self.web_socket_server: Optional[IWebSocketServer] = None
        self.cache_manager: Optional[ICacheManager] = None
        self.data_processor: Optional[IDataProcessor] = None

    async def start(self) -> None:
        """Start all application services."""
        logger.info("Starting realtime application")

        try:
            # Resolve dependencies
            self.cache_manager = await self.container.resolve(ICacheManager)
            self.web_socket_server = await self.container.resolve(IWebSocketServer)
            self.data_processor = await self.container.resolve(IDataProcessor)

            # Initialize services
            await self.cache_manager.initialize()
            await self.web_socket_server.start(host="0.0.0.0", port=8000)
            await self.data_processor.start()

            logger.info("All services started successfully")

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        """Shutdown all services gracefully."""
        logger.info("Shutting down realtime application")

        try:
            if self.web_socket_server:
                await self.web_socket_server.stop()

            if self.data_processor:
                await self.data_processor.stop()

            if self.cache_manager:
                await self.cache_manager.cleanup()

            await self.container.shutdown()
            logger.info("Application shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Usage
async def main():
    # Load configuration
    config = load_configuration("production")

    # Setup container
    container = setup_container(config)

    # Create and start application
    app = RealtimeApplication(container)

    try:
        await app.start()
        # Run until interrupted
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

**Pros:**
- ✅ Complete dependency management and inversion of control
- ✅ Easy testing with mock implementations
- ✅ Runtime configuration changes possible
- ✅ Proper component lifecycle management
- ✅ Circular dependency detection and prevention

**Cons:**
- ❌ Initial implementation complexity
- ❌ Learning curve for team
- ❌ Runtime overhead (minimal)

**Effort:** High (4-5 days)
**Risk:** Low

## Solution 2: Configuration Management System

**Description:** Centralized configuration with environment-specific settings

**Implementation:**
```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
import yaml
from pathlib import Path

@dataclass
class RedisConfig:
    """Redis configuration settings."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True

    @property
    def redis_url(self) -> str:
        """Build Redis URL from configuration."""
        auth_part = f":{self.password}@" if self.password else ""
        return f"redis://{auth_part}{self.host}:{self.port}/{self.db}"

    @property
    def connection_options(self) -> Dict[str, Any]:
        """Get connection options for aioredis."""
        return {
            'max_connections': self.max_connections,
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.socket_connect_timeout,
            'retry_on_timeout': self.retry_on_timeout,
            'decode_responses': True
        }

@dataclass
class WebSocketConfig:
    """WebSocket server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    max_connections: int = 1000
    heartbeat_interval: int = 30
    message_size_limit: int = 1024 * 1024  # 1MB
    enable_compression: bool = True

@dataclass
class DataProcessorConfig:
    """Data processor configuration."""
    num_workers: int = 4
    max_queue_size: int = 10000
    buffer_size: int = 50000
    batch_size: int = 100
    processing_timeout: float = 1.0
    enable_metrics: bool = True

@dataclass
class AppConfig:
    """Main application configuration."""
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    redis: RedisConfig = field(default_factory=RedisConfig)
    websocket: WebSocketConfig = field(default_factory=WebSocketConfig)
    data_processor: DataProcessorConfig = field(default_factory=DataProcessorConfig)
    monitoring: MonitoringConfig = field(default_factory=lambda: MonitoringConfig())

    @classmethod
    def load_from_file(cls, config_path: Path) -> 'AppConfig':
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        return cls.from_dict(config_data)

    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> 'AppConfig':
        """Create configuration from dictionary."""
        # Extract nested configurations
        redis_config = config_data.get('redis', {})
        websocket_config = config_data.get('websocket', {})
        processor_config = config_data.get('data_processor', {})
        monitoring_config = config_data.get('monitoring', {})

        return cls(
            environment=config_data.get('environment', 'development'),
            debug=config_data.get('debug', False),
            log_level=config_data.get('log_level', 'INFO'),
            redis=RedisConfig(**redis_config),
            websocket=WebSocketConfig(**websocket_config),
            data_processor=DataProcessorConfig(**processor_config),
            monitoring=MonitoringConfig(**monitoring_config)
        )

    @classmethod
    def load_from_environment(cls) -> 'AppConfig':
        """Load configuration from environment variables."""
        env = os.getenv('ENVIRONMENT', 'development')

        config = cls(
            environment=env,
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )

        # Override Redis settings
        if os.getenv('REDIS_HOST'):
            config.redis.host = os.getenv('REDIS_HOST')
        if os.getenv('REDIS_PORT'):
            config.redis.port = int(os.getenv('REDIS_PORT'))
        if os.getenv('REDIS_PASSWORD'):
            config.redis.password = os.getenv('REDIS_PASSWORD')

        # Override WebSocket settings
        if os.getenv('WEBSOCKET_PORT'):
            config.websocket.port = int(os.getenv('WEBSOCKET_PORT'))

        return config

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if self.websocket.port < 1 or self.websocket.port > 65535:
            errors.append("WebSocket port must be between 1 and 65535")

        if self.data_processor.num_workers < 1:
            errors.append("Number of workers must be at least 1")

        if self.data_processor.max_queue_size < 100:
            errors.append("Max queue size should be at least 100")

        return errors

# Configuration files
# config/development.yaml
environment: "development"
debug: true
log_level: "DEBUG"

redis:
  host: "localhost"
  port: 6379
  max_connections: 10

websocket:
  host: "localhost"
  port: 8000
  max_connections: 100

data_processor:
  num_workers: 2
  max_queue_size: 1000

# config/production.yaml
environment: "production"
debug: false
log_level: "INFO"

redis:
  host: "redis-cluster.internal"
  port: 6379
  password: "${REDIS_PASSWORD}"
  max_connections: 100

websocket:
  host: "0.0.0.0"
  port: 8000
  max_connections: 1000

data_processor:
  num_workers: 8
  max_queue_size: 50000

monitoring:
  enabled: true
  prometheus_port: 9090
```

**Pros:**
- ✅ Environment-specific configurations
- ✅ Type-safe configuration
- ✅ Configuration validation
- ✅ Support for environment variables
- ✅ Hot configuration reload capability

**Cons:**
- ❌ Additional configuration management complexity
- ❌ Need for configuration deployment pipeline

**Effort:** Medium (2-3 days)
**Risk:** Low

## Solution 3: Interface-Driven Testing Framework

**Description:** Implement comprehensive testing framework with mocking and contract testing

**Implementation:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import TypeVar, Generic

T = TypeVar('T')

class MockServiceBuilder(Generic[T]):
    """Builder for creating mock services with realistic behavior."""

    def __init__(self, interface: Type[T]):
        self.interface = interface
        self.mock = AsyncMock(spec=interface)
        self._setup_default_behavior()

    def _setup_default_behavior(self) -> None:
        """Setup realistic default behavior for common interfaces."""
        if hasattr(self.interface, 'get'):
            self.mock.get.return_value = None

        if hasattr(self.interface, 'set'):
            self.mock.set.return_value = True

        if hasattr(self.interface, 'health_check'):
            self.mock.health_check.return_value = True

    def with_get_behavior(self, return_value: Any = None, side_effect: Exception = None):
        """Configure get method behavior."""
        if side_effect:
            self.mock.get.side_effect = side_effect
        else:
            self.mock.get.return_value = return_value
        return self

    def with_set_behavior(self, return_value: bool = True, side_effect: Exception = None):
        """Configure set method behavior."""
        if side_effect:
            self.mock.set.side_effect = side_effect
        else:
            self.mock.set.return_value = return_value
        return self

    def build(self) -> T:
        """Build the mock service."""
        return self.mock

# Test fixtures with dependency injection
@pytest.fixture
async def mock_container():
    """Create test container with mock services."""
    container = DIContainer()

    # Register mock services
    cache_mock = MockServiceBuilder(ICacheManager).build()
    container.register_singleton(ICacheManager, lambda: cache_mock)

    websocket_mock = MockServiceBuilder(IWebSocketServer).build()
    container.register_singleton(IWebSocketServer, lambda: websocket_mock)

    validator_mock = MockServiceBuilder(IDataValidator).build()
    container.register_singleton(IDataValidator, lambda: validator_mock)

    yield container

    await container.shutdown()

@pytest.fixture
async def test_data_point():
    """Create test market data point."""
    return MarketDataPoint(
        symbol="0700.HK",
        timestamp=datetime.now(),
        price=300.50,
        volume=15000,
        bid=300.25,
        ask=300.75,
        source="test"
    )

# Integration tests with real dependencies
@pytest.fixture
async def integration_container():
    """Create container with real services for integration testing."""
    config = AppConfig.load_from_environment()
    config.redis.host = "localhost"  # Use local Redis for testing
    config.redis.db = 1  # Use separate database

    container = setup_container(config)

    # Initialize real services
    cache_manager = await container.resolve(ICacheManager)
    await cache_manager.initialize()

    yield container

    # Cleanup
    cache_manager = await container.resolve(ICacheManager)
    await cache_manager.cleanup()
    await container.shutdown()

# Example test classes
class TestCacheManager:
    """Test cache manager with mocking and real dependencies."""

    @pytest.mark.asyncio
    async def test_cache_get_miss(self, mock_container):
        """Test cache miss scenario."""
        # Arrange
        cache_manager = await mock_container.resolve(ICacheManager)

        # Mock cache miss behavior
        cache_manager.get.return_value = None

        # Act
        result = await cache_manager.get("nonexistent_key")

        # Assert
        assert result is None
        cache_manager.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_cache_get_success(self, mock_container):
        """Test cache hit scenario."""
        # Arrange
        cache_manager = await mock_container.resolve(ICacheManager)
        test_value = {"symbol": "0700.HK", "price": 300.50}

        # Mock cache hit behavior
        cache_manager.get.return_value = test_value

        # Act
        result = await cache_manager.get("test_key")

        # Assert
        assert result == test_value
        cache_manager.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_set_success(self, mock_container):
        """Test successful cache set."""
        # Arrange
        cache_manager = await mock_container.resolve(ICacheManager)
        test_value = {"symbol": "0700.HK", "price": 300.50}

        # Mock successful set
        cache_manager.set.return_value = True

        # Act
        result = await cache_manager.set("test_key", test_value, ttl=300)

        # Assert
        assert result is True
        cache_manager.set.assert_called_once_with("test_key", test_value, ttl=300)

class TestDataProcessor:
    """Test data processor with dependency injection."""

    @pytest.mark.asyncio
    async def test_data_processing_success(self, mock_container, test_data_point):
        """Test successful data point processing."""
        # Arrange
        data_processor = await mock_container.resolve(IDataProcessor)

        # Mock successful processing
        expected_signals = [
            ProcessedSignal("0700.HK", datetime.now(), "momentum", 0.05, 0.8, {})
        ]
        data_processor.process_data_point.return_value = expected_signals

        # Act
        signals = await data_processor.process_data_point(test_data_point)

        # Assert
        assert len(signals) == 1
        assert signals[0].signal_type == "momentum"
        assert signals[0].symbol == "0700.HK"
        data_processor.process_data_point.assert_called_once_with(test_data_point)

# Contract testing between components
class TestComponentContracts:
    """Test contracts between different components."""

    @pytest.mark.asyncio
    async def test_cache_validator_contract(self, integration_container):
        """Test contract between cache manager and data validator."""
        # Arrange
        cache_manager = await integration_container.resolve(ICacheManager)
        validator = await integration_container.resolve(IDataValidator)

        # Create test data point
        data_point = MarketDataPoint(
            symbol="0700.HK",
            timestamp=datetime.now(),
            price=300.50,
            volume=15000,
            bid=300.25,
            ask=300.75,
            source="test"
        )

        # Act
        validation_result = await validator.validate_data_point(data_point)

        # Store validation result in cache
        cache_key = f"validation_result:{data_point.symbol}"
        cache_success = await cache_manager.set(cache_key, validation_result.to_dict(), ttl=300)

        # Retrieve from cache
        cached_result = await cache_manager.get(cache_key)

        # Assert
        assert cache_success is True
        assert cached_result is not None
        assert cached_result['symbol'] == data_point.symbol
        assert cached_result['validation_passed'] == validation_result.validation_passed

# Performance tests
class TestPerformance:
    """Performance tests for critical components."""

    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self, integration_container):
        """Test cache performance under high load."""
        # Arrange
        cache_manager = await integration_container.resolve(ICacheManager)
        test_data = {"test": "data"} * 100  # Simulate real data size

        # Act
        start_time = time.perf_counter()

        # Perform 1000 operations
        for i in range(1000):
            await cache_manager.set(f"key_{i}", test_data, ttl=60)
            await cache_manager.get(f"key_{i}")

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Assert
        avg_operation_time = total_time / 2000  # 1000 sets + 1000 gets
        assert avg_operation_time < 0.001  # Should be under 1ms average
        assert total_time < 5.0  # Total should be under 5 seconds
```

**Pros:**
- ✅ Comprehensive testing with realistic mocks
- ✅ Contract testing between components
- ✅ Performance testing framework
- ✅ Easy test setup and teardown
- ✅ Integration testing with real dependencies

**Cons:**
- ❌ Additional testing infrastructure complexity
- ❌ Mock maintenance overhead

**Effort:** Medium (3-4 days)
**Risk:** Low

# Recommended Action

**Implement all three architectural improvements:**

1. **Week 1:** Dependency injection container and interface definitions
2. **Week 2:** Configuration management system with environment support
3. **Week 3:** Comprehensive testing framework with mocking and contract testing

# Acceptance Criteria

- [ ] All components use dependency injection
- [ ] Interface abstractions defined for all major components
- [ ] Configuration system supports multiple environments
- [ ] Components can be easily mocked for unit testing
- [ ] Integration tests work with both mocks and real dependencies
- [ ] Application startup/shutdown works correctly
- [ ] Health checks implemented for all services
- [ ] Configuration validation prevents invalid deployments
- [ ] Performance impact of DI container is minimal (<2%)

# Technical Details

**Files to create:**
- `simplified_system/src/realtime/di_container.py` (dependency injection container)
- `simplified_system/src/realtime/interfaces.py` (interface definitions)
- `simplified_system/src/realtime/config.py` (configuration management)
- `simplified_system/src/realtime/testing.py` (testing utilities)
- `simplified_system/config/development.yaml` (development config)
- `simplified_system/config/production.yaml` (production config)

**Files to modify:**
- All Phase 3 implementation files to use dependency injection
- Application startup scripts
- Testing files

**Dependencies to add:**
- `pyyaml>=6.0` (configuration file parsing)
- `pytest>=7.0.0` (testing framework)
- `pytest-asyncio>=0.21.0` (async testing support)

**Configuration changes:**
- Environment-specific configuration files
- CI/CD pipeline updates for configuration management
- Development environment setup

# Resources

**Architecture patterns:**
- [Dependency Injection Pattern](https://en.wikipedia.org/wiki/Dependency_injection)
- [Inversion of Control](https://en.wikipedia.org/wiki/Inversion_of_control)
- [Configuration Management Best Practices](https://12factor.net/config)

**Code examples:**
- [Python DI Containers](https://github.com/ets-labs/python-dependency-injector)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

**Testing frameworks:**
- [Pytest Async Testing](https://pytest-asyncio.readthedocs.io/)
- [Mock Objects in Python](https://docs.python.org/3/library/unittest.mock.html)

# Work Log

## 2025-11-29 - Architecture Review and Planning

**By:** Code Review Agent

**Actions:**
- Conducted comprehensive architectural review of Phase 3 implementation
- Identified critical dependency management and configuration issues
- Analyzed testing infrastructure gaps and maintainability concerns
- Designed comprehensive solution with dependency injection and configuration management
- Created detailed implementation plans with concrete code examples

**Learnings:**
- Dependency injection essential for testability and maintainability
- Configuration management critical for production deployments
- Interface abstractions enable better component design
- Testing infrastructure investment pays off in long-term quality
- Architecture refactoring requires careful planning and incremental implementation

## Next Steps

1. **Week 1 (P2):** Implement dependency injection container
2. **Week 2 (P2):** Add configuration management system
3. **Week 3 (P2):** Build comprehensive testing framework
4. **P3:** Add health checks and monitoring integration
5. **P3:** Update development documentation and guidelines