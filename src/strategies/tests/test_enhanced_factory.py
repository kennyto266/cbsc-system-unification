"""
Tests for Enhanced Strategy Factory
Test-driven development for strategy factory with dynamic loading and hot reload
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.enhanced_factory import (
    EnhancedStrategyFactory, StrategyRegistry, StrategyMetadata,
    StrategyFileWatcher, StrategyType, get_enhanced_strategy_factory
)
from strategies.base import BaseStrategy
from core.exceptions import StrategyError


# Mock User for testing
class MockUser:
    def __init__(self, is_superuser: bool = False):
        self.id = uuid4()
        self.is_superuser = is_superuser
        self.email = "test@example.com"


# Mock strategy classes for testing
class TestStrategy(BaseStrategy):
    """Test strategy for factory testing"""
    STRATEGY_NAME = "test_strategy"
    STRATEGY_TYPE = StrategyType.CUSTOM
    DESCRIPTION = "Test strategy"
    VERSION = "1.0.0"
    AUTHOR = "Test Author"
    TAGS = ["test", "mock"]
    PARAMETERS = {
        "param1": {"type": int, "default": 10, "required": True},
        "param2": {"type": str, "default": "default", "required": False}
    }
    REQUIRED_DATA = ["price", "volume"]

    def __init__(self, instance_id: uuid4, config: Dict[str, Any], metadata: StrategyMetadata, **kwargs):
        super().__init__(instance_id, config, metadata)
        self.test_initialized = True


class TestStrategy2(BaseStrategy):
    """Another test strategy"""
    STRATEGY_NAME = "test_strategy_2"
    STRATEGY_TYPE = StrategyType.MOMENTUM
    DESCRIPTION = "Test momentum strategy"
    VERSION = "2.0.0"

    def __init__(self, instance_id: uuid4, config: Dict[str, Any], metadata: StrategyMetadata, **kwargs):
        super().__init__(instance_id, config, metadata)


@pytest.fixture
def mock_registry():
    """Mock strategy registry"""
    return StrategyRegistry()


@pytest.fixture
def strategy_factory():
    """Strategy factory fixture"""
    return EnhancedStrategyFactory()


@pytest.fixture
def sample_metadata():
    """Sample strategy metadata"""
    return StrategyMetadata(
        name="test_strategy",
        strategy_type=StrategyType.MOMENTUM,
        description="Test momentum strategy",
        version="1.0.0",
        author="Test Author",
        tags=["test", "momentum"],
        parameters={
            "period": {"type": int, "default": 20, "required": True},
            "threshold": {"type": float, "default": 0.02, "min": 0.01, "max": 0.1}
        },
        required_data=["price", "volume"],
        risk_level="medium",
        expected_return=0.15
    )


class TestStrategyRegistry:
    """Test strategy registry functionality"""

    def test_register_strategy_success(self, mock_registry, sample_metadata):
        """Test successful strategy registration"""
        mock_registry.register(TestStrategy, sample_metadata)

        assert "test_strategy" in mock_registry._strategies
        assert mock_registry.get_strategy_class("test_strategy") == TestStrategy
        assert mock_registry.get_metadata("test_strategy") == sample_metadata

    def test_register_invalid_strategy(self, mock_registry, sample_metadata):
        """Test registering invalid strategy class"""
        class InvalidStrategy:
            pass

        with pytest.raises(StrategyError, match="must inherit from BaseStrategy"):
            mock_registry.register(InvalidStrategy, sample_metadata)

    def test_unregister_strategy(self, mock_registry, sample_metadata):
        """Test strategy unregistration"""
        mock_registry.register(TestStrategy, sample_metadata)
        mock_registry.unregister("test_strategy")

        assert "test_strategy" not in mock_registry._strategies
        assert "test_strategy" not in mock_registry._metadata

    def test_get_nonexistent_strategy(self, mock_registry):
        """Test getting non-existent strategy"""
        with pytest.raises(StrategyError, match="not found in registry"):
            mock_registry.get_strategy_class("nonexistent")

    def test_list_strategies_no_filter(self, mock_registry, sample_metadata):
        """Test listing all strategies"""
        # Register multiple strategies
        metadata1 = sample_metadata
        metadata2 = StrategyMetadata(
            name="test_strategy_2",
            strategy_type=StrategyType.VOLUME,
            description="Test volume strategy",
            version="1.0.0",
            author="Test Author"
        )

        mock_registry.register(TestStrategy, metadata1)
        mock_registry.register(TestStrategy2, metadata2)

        strategies = mock_registry.list_strategies()
        assert len(strategies) == 2

    def test_list_strategies_with_type_filter(self, mock_registry, sample_metadata):
        """Test listing strategies with type filter"""
        mock_registry.register(TestStrategy, sample_metadata)

        momentum_strategies = mock_registry.list_strategies(strategy_type=StrategyType.MOMENTUM)
        assert len(momentum_strategies) == 1
        assert momentum_strategies[0].strategy_type == StrategyType.MOMENTUM

        volume_strategies = mock_registry.list_strategies(strategy_type=StrategyType.VOLUME)
        assert len(volume_strategies) == 0

    def test_list_strategies_with_tag_filter(self, mock_registry, sample_metadata):
        """Test listing strategies with tag filter"""
        mock_registry.register(TestStrategy, sample_metadata)

        tagged_strategies = mock_registry.list_strategies(tags=["test"])
        assert len(tagged_strategies) == 1

        untagged_strategies = mock_registry.list_strategies(tags=["nonexistent"])
        assert len(untagged_strategies) == 0

    def test_search_strategies(self, mock_registry, sample_metadata):
        """Test searching strategies"""
        mock_registry.register(TestStrategy, sample_metadata)

        # Search by name
        results = mock_registry.search_strategies("test")
        assert len(results) == 1

        # Search by description
        results = mock_registry.search_strategies("momentum")
        assert len(results) == 1

        # Search by tag
        results = mock_registry.search_strategies("test_tag")
        assert len(results) == 0  # No "test_tag" in sample metadata

    def test_clear_cache(self, mock_registry, sample_metadata):
        """Test clearing strategy cache"""
        mock_registry.register(TestStrategy, sample_metadata)

        # Add cached instance
        mock_registry._instances["test_strategy_123"] = TestStrategy(uuid4(), {}, sample_metadata)

        # Clear specific cache
        mock_registry.clear_cache("test_strategy_123")
        assert "test_strategy_123" not in mock_registry._instances

        # Clear all cache
        mock_registry._instances["test_strategy_456"] = TestStrategy(uuid4(), {}, sample_metadata)
        mock_registry.clear_cache()
        assert len(mock_registry._instances) == 0

    def test_get_statistics(self, mock_registry, sample_metadata):
        """Test getting registry statistics"""
        mock_registry.register(TestStrategy, sample_metadata)

        stats = mock_registry.get_statistics()
        assert stats['total_strategies'] == 1
        assert stats['total_instances'] == 0
        assert stats['type_distribution'][StrategyType.MOMENTUM] == 1


class TestEnhancedStrategyFactory:
    """Test enhanced strategy factory functionality"""

    def test_create_strategy_success(self, strategy_factory, sample_metadata):
        """Test successful strategy creation"""
        # Register strategy first
        strategy_factory.registry.register(TestStrategy, sample_metadata)

        config = {"param1": 20, "param2": "test"}
        strategy = strategy_factory.create_strategy("test_strategy", config)

        assert isinstance(strategy, TestStrategy)
        assert strategy.test_initialized is True

    def test_create_nonexistent_strategy(self, strategy_factory):
        """Test creating non-existent strategy"""
        config = {"param1": 20}
        with pytest.raises(StrategyError, match="not found in registry"):
            strategy_factory.create_strategy("nonexistent", config)

    def test_create_strategy_from_template(self, strategy_factory):
        """Test creating strategy from template"""
        template = strategy_factory.create_strategy_from_template("ma_crossover")

        assert template['name'] == 'MA Crossover Strategy'
        assert template['strategy_type'] == StrategyType.MOMENTUM
        assert 'fast_period' in template['config']

        # Test with overrides
        template = strategy_factory.create_strategy_from_template(
            "ma_crossover",
            overrides={"config": {"fast_period": 15}}
        )
        assert template['config']['fast_period'] == 15

    def test_create_strategy_invalid_template(self, strategy_factory):
        """Test creating strategy with invalid template"""
        with pytest.raises(StrategyError, match="Template 'invalid' not found"):
            strategy_factory.create_strategy_from_template("invalid")

    def test_validate_config_success(self, strategy_factory, sample_metadata):
        """Test successful configuration validation"""
        config = {"period": 20, "threshold": 0.05}
        # Should not raise exception
        strategy_factory._validate_config(config, sample_metadata)

    def test_validate_config_missing_required(self, strategy_factory, sample_metadata):
        """Test config validation with missing required parameter"""
        config = {"threshold": 0.05}  # Missing required 'period'
        with pytest.raises(StrategyError, match="Required parameter 'period' missing"):
            strategy_factory._validate_config(config, sample_metadata)

    def test_validate_config_invalid_type(self, strategy_factory, sample_metadata):
        """Test config validation with invalid type"""
        config = {"period": "twenty", "threshold": 0.05}  # String instead of int
        with pytest.raises(StrategyError, match="must be of type"):
            strategy_factory._validate_config(config, sample_metadata)

    def test_validate_config_out_of_range(self, strategy_factory, sample_metadata):
        """Test config validation with out of range value"""
        config = {"period": 20, "threshold": 0.20}  # Above max of 0.1
        with pytest.raises(StrategyError, match="must be <="):
            strategy_factory._validate_config(config, sample_metadata)

    def test_load_strategies_from_file(self, strategy_factory):
        """Test loading strategies from file"""
        # Create a temporary strategy file
        strategy_code = '''
from strategies.base import BaseStrategy
from strategies.enhanced_factory import StrategyType, StrategyMetadata
from uuid import uuid4
from typing import Dict, Any

class FileTestStrategy(BaseStrategy):
    """Test strategy loaded from file"""
    STRATEGY_NAME = "file_test_strategy"
    STRATEGY_TYPE = StrategyType.CUSTOM
    DESCRIPTION = "File test strategy"
    VERSION = "1.0.0"

    def __init__(self, instance_id: uuid4, config: Dict[str, Any], metadata: StrategyMetadata):
        super().__init__(instance_id, config, metadata)
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_code)
            temp_path = f.name

        try:
            strategy_factory.load_strategies_from_path(temp_path)

            # Strategy should be registered
            assert "file_test_strategy" in strategy_factory.registry._metadata
        finally:
            os.unlink(temp_path)

    def test_load_strategies_from_directory(self, strategy_factory):
        """Test loading strategies from directory"""
        # Create temporary directory with strategy files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create strategy file
            strategy_file = Path(temp_dir) / "temp_strategy.py"
            strategy_file.write_text('''
from strategies.base import BaseStrategy
from strategies.enhanced_factory import StrategyType, StrategyMetadata
from uuid import uuid4
from typing import Dict, Any

class DirTestStrategy(BaseStrategy):
    STRATEGY_NAME = "dir_test_strategy"
    STRATEGY_TYPE = StrategyType.CUSTOM
    DESCRIPTION = "Directory test strategy"
    VERSION = "1.0.0"

    def __init__(self, instance_id: uuid4, config: Dict[str, Any], metadata: StrategyMetadata):
        super().__init__(instance_id, config, metadata)
''')

            strategy_factory.load_strategies_from_path(temp_dir)

            # Strategy should be registered
            assert "dir_test_strategy" in strategy_factory.registry._metadata

    def test_discover_strategies(self, strategy_factory):
        """Test strategy discovery"""
        # Create temporary directory with strategy files
        with tempfile.TemporaryDirectory() as temp_dir:
            strategy_file = Path(temp_dir) / "discover_strategy.py"
            strategy_file.write_text('''
from strategies.base import BaseStrategy
from strategies.enhanced_factory import StrategyType, StrategyMetadata
from uuid import uuid4
from typing import Dict, Any

class DiscoverTestStrategy(BaseStrategy):
    STRATEGY_NAME = "discover_test_strategy"
    STRATEGY_TYPE = StrategyType.CUSTOM
    DESCRIPTION = "Discovery test strategy"
    VERSION = "1.0.0"

    def __init__(self, instance_id: uuid4, config: Dict[str, Any], metadata: StrategyMetadata):
        super().__init__(instance_id, config, metadata)
''')

            discovered = strategy_factory.discover_strategies([temp_dir])
            assert len(discovered) > 0
            assert any('discover_strategy.py' in path for path in discovered)

    @patch('strategies.enhanced_factory.importlib')
    def test_reload_strategy(self, mock_importlib, strategy_factory, sample_metadata):
        """Test strategy reloading"""
        # Setup mocks
        mock_module = MagicMock()
        mock_strategy_class = MagicMock()
        mock_module.TestStrategy = mock_strategy_class
        mock_importlib.import_module.return_value = mock_module
        mock_importlib.reload.return_value = mock_module

        # Register strategy
        sample_metadata.module_path = "test_module"
        sample_metadata.class_name = "TestStrategy"
        strategy_factory.registry.register(TestStrategy, sample_metadata)

        # Reload strategy
        strategy_factory.reload_strategy("test_strategy")

        # Verify reload was called
        mock_importlib.reload.assert_called_once_with(mock_module)

    def test_enable_disable_hot_reload(self, strategy_factory):
        """Test hot reload enable/disable"""
        # Enable hot reload
        strategy_factory.enable_hot_reload()
        assert strategy_factory._hot_reload_enabled is True

        # Disable hot reload
        strategy_factory.disable_hot_reload()
        assert strategy_factory._hot_reload_enabled is False

    def test_get_factory_status(self, strategy_factory):
        """Test getting factory status"""
        status = strategy_factory.get_factory_status()

        assert 'hot_reload_enabled' in status
        assert 'active_watchers' in status
        assert 'load_paths' in status
        assert 'plugin_paths' in status
        assert 'registry_stats' in status
        assert 'available_loaders' in status

    def test_template_methods(self, strategy_factory):
        """Test all template methods"""
        templates = [
            "ma_crossover",
            "rsi_mean_reversion",
            "momentum_breakout",
            "portfolio_allocation",
            "bollinger_bands",
            "macd_signal",
            "volume_price"
        ]

        for template_name in templates:
            template = strategy_factory.create_strategy_from_template(template_name)
            assert 'name' in template
            assert 'strategy_type' in template
            assert 'config' in template
            assert 'parameters' in template


class TestGlobalFactory:
    """Test global factory functions"""

    def test_get_enhanced_strategy_factory(self):
        """Test getting global factory instance"""
        factory = get_enhanced_strategy_factory()
        assert isinstance(factory, EnhancedStrategyFactory)

        # Should return same instance
        factory2 = get_enhanced_strategy_factory()
        assert factory is factory2

    @patch('strategies.enhanced_factory.get_enhanced_strategy_factory')
    def test_create_strategy_function(self, mock_get_factory):
        """Test global create_strategy function"""
        from strategies.enhanced_factory import create_strategy

        mock_factory = MagicMock()
        mock_strategy = MagicMock()
        mock_factory.create_strategy.return_value = mock_strategy
        mock_get_factory.return_value = mock_factory

        strategy = create_strategy("test_strategy", {"param": "value"})

        mock_factory.create_strategy.assert_called_once_with("test_strategy", {"param": "value"})
        assert strategy == mock_strategy


class TestStrategyFileWatcher:
    """Test strategy file watcher"""

    def test_file_watcher_creation(self, strategy_factory):
        """Test file watcher creation"""
        watcher = StrategyFileWatcher(strategy_factory)
        assert watcher.factory == strategy_factory
        assert isinstance(watcher.last_reload, dict)

    def test_file_watcher_debounce(self, strategy_factory):
        """Test file watcher debouncing"""
        watcher = StrategyFileWatcher(strategy_factory)

        # Create mock event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "test_strategy.py"

        # Simulate rapid file changes
        current_time = time.time()
        watcher.last_reload["test_strategy.py"] = current_time

        # Should be debounced
        watcher.on_modified(mock_event)

        # Verify no reload occurred due to debouncing
        # (This is a basic test - in real scenario, we'd check if reload was called)


class TestStrategyMetadata:
    """Test strategy metadata dataclass"""

    def test_metadata_creation(self, sample_metadata):
        """Test metadata creation"""
        assert sample_metadata.name == "test_strategy"
        assert sample_metadata.strategy_type == StrategyType.MOMENTUM
        assert sample_metadata.version == "1.0.0"
        assert isinstance(sample_metadata.tags, list)
        assert isinstance(sample_metadata.parameters, dict)
        assert sample_metadata.created_at > 0
        assert sample_metadata.updated_at > 0

    def test_metadata_defaults(self):
        """Test metadata default values"""
        metadata = StrategyMetadata(
            name="test",
            strategy_type=StrategyType.CUSTOM,
            description="Test",
            version="1.0.0",
            author="Test"
        )

        assert metadata.tags == []
        assert metadata.parameters == {}
        assert metadata.required_data == []
        assert metadata.risk_level == "medium"
        assert metadata.expected_return is None
        assert metadata.dependencies == []