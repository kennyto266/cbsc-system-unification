"""Integration tests for Hong Kong quantitative trading system.

This module provides comprehensive integration testing capabilities including
end-to-end testing, data flow testing, business process testing, and performance testing.
"""

import asyncio
import json
import logging
import os
import pytest
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# Import system components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integration.system_integration import SystemIntegration, IntegrationConfig, SystemStatus
from src.integration.config_manager import ConfigManager
from src.integration.component_orchestrator import ComponentOrchestrator, ComponentType, ComponentInfo
from src.integration.system_initializer import SystemInitializer, InitializationStep
from src.integration.health_monitor import SystemHealthMonitor, HealthStatus

from src.data_adapters.data_service import DataService
from src.backtest.stockbacktest_integration import StockBacktestIntegration
from src.agents.real_agents.real_quantitative_analyst import RealQuantitativeAnalyst
from src.agents.real_agents.real_quantitative_trader import RealQuantitativeTrader
from src.agents.real_agents.real_portfolio_manager import RealPortfolioManager
from src.agents.real_agents.real_risk_analyst import RealRiskAnalyst
from src.agents.real_agents.real_data_scientist import RealDataScientist
from src.agents.real_agents.real_quantitative_engineer import RealQuantitativeEngineer
from src.agents.real_agents.real_research_analyst import RealResearchAnalyst
from src.strategy_management.strategy_manager import StrategyManager
from src.monitoring.real_time_monitor import RealTimeMonitor
from src.telegram.integration_manager import IntegrationManager


class IntegrationTestBase:
    """Base class for integration tests."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.test_start_time = datetime.now()
        self.logger = logging.getLogger(__name__)
        
        # Test configuration
        self.test_config = {
            'system_id': 'test_system_001',
            'system_name': 'Test Trading System',
            'version': '1.0.0-test',
            'environment': 'test',
            'debug_mode': True
        }
        
        # Test data paths
        self.test_data_path = Path(__file__).parent / "test_data"
        self.test_data_path.mkdir(exist_ok=True)
        
        # Cleanup after test
        yield
        await self.cleanup_test_environment()
    
    async def cleanup_test_environment(self):
        """Cleanup test environment."""
        try:
            # Cleanup test data
            if self.test_data_path.exists():
                import shutil
                shutil.rmtree(self.test_data_path)
            
            self.logger.info("Test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up test environment: {e}")


class TestSystemIntegration(IntegrationTestBase):
    """Test system integration functionality."""
    
    @pytest.mark.asyncio
    async def test_system_startup_and_shutdown(self):
        """Test complete system startup and shutdown."""
        # Create integration config
        config = IntegrationConfig(
            system_id=self.test_config['system_id'],
            system_name=self.test_config['system_name'],
            version=self.test_config['version'],
            environment=self.test_config['environment'],
            debug_mode=self.test_config['debug_mode']
        )
        
        # Create system integration
        system_integration = SystemIntegration(config)
        
        try:
            # Initialize system
            assert await system_integration.initialize()
            
            # Start system
            assert await system_integration.start_system()
            assert system_integration.status == SystemStatus.RUNNING
            
            # Wait for system to stabilize
            await asyncio.sleep(2)
            
            # Check system status
            status = system_integration.get_system_status()
            assert status['status'] == SystemStatus.RUNNING.value
            assert status['system_id'] == self.test_config['system_id']
            
            # Stop system
            assert await system_integration.stop_system()
            assert system_integration.status == SystemStatus.STOPPED
            
        finally:
            # Cleanup
            await system_integration.shutdown()
    
    @pytest.mark.asyncio
    async def test_component_lifecycle_management(self):
        """Test component lifecycle management."""
        config = IntegrationConfig(
            system_id=self.test_config['system_id'],
            system_name=self.test_config['system_name']
        )
        
        system_integration = SystemIntegration(config)
        
        try:
            # Initialize system
            await system_integration.initialize()
            
            # Test component registration
            component_info = ComponentInfo(
                component_id="test_component",
                component_type=ComponentType.AI_AGENT,
                description="Test component"
            )
            
            # Register component
            assert await system_integration.component_orchestrator.register_component(component_info)
            
            # Check component is registered
            registered_component = system_integration.component_orchestrator.get_component_info("test_component")
            assert registered_component is not None
            assert registered_component.component_id == "test_component"
            
        finally:
            await system_integration.shutdown()
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self):
        """Test system health monitoring."""
        config = IntegrationConfig(
            system_id=self.test_config['system_id'],
            system_name=self.test_config['system_name']
        )
        
        system_integration = SystemIntegration(config)
        
        try:
            # Initialize system
            await system_integration.initialize()
            
            # Start system
            await system_integration.start_system()
            
            # Wait for health monitoring to start
            await asyncio.sleep(3)
            
            # Check system health
            health_result = await system_integration.health_monitor.check_system_health()
            assert health_result is not None
            assert health_result.system_id == "trading_system"
            assert health_result.overall_status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.UNKNOWN]
            
        finally:
            await system_integration.shutdown()


class TestDataFlowIntegration(IntegrationTestBase):
    """Test data flow integration."""
    
    @pytest.mark.asyncio
    async def test_data_adapter_to_agent_flow(self):
        """Test data flow from data adapter to AI agents."""
        # Mock data adapter
        mock_data_adapter = AsyncMock()
        mock_data_adapter.get_market_data.return_value = {
            'symbol': '00700.HK',
            'price': 300.50,
            'volume': 1000000,
            'timestamp': datetime.now()
        }
        
        # Mock AI agent
        mock_agent = AsyncMock()
        mock_agent.analyze_market_data.return_value = {
            'signal': 'BUY',
            'confidence': 0.85,
            'reasoning': 'Strong momentum detected'
        }
        
        # Test data flow
        market_data = await mock_data_adapter.get_market_data('00700.HK')
        analysis_result = await mock_agent.analyze_market_data(market_data)
        
        # Verify data flow
        assert market_data['symbol'] == '00700.HK'
        assert analysis_result['signal'] == 'BUY'
        assert analysis_result['confidence'] > 0.8
        
        # Verify method calls
        mock_data_adapter.get_market_data.assert_called_once_with('00700.HK')
        mock_agent.analyze_market_data.assert_called_once_with(market_data)
    
    @pytest.mark.asyncio
    async def test_agent_to_strategy_manager_flow(self):
        """Test data flow from AI agents to strategy manager."""
        # Mock agent signal
        agent_signal = {
            'agent_id': 'quantitative_analyst',
            'symbol': '00700.HK',
            'signal': 'BUY',
            'confidence': 0.85,
            'timestamp': datetime.now()
        }
        
        # Mock strategy manager
        mock_strategy_manager = AsyncMock()
        mock_strategy_manager.process_agent_signal.return_value = {
            'strategy_id': 'momentum_strategy_001',
            'action': 'OPEN_POSITION',
            'position_size': 1000,
            'risk_score': 0.2
        }
        
        # Test data flow
        strategy_result = await mock_strategy_manager.process_agent_signal(agent_signal)
        
        # Verify data flow
        assert strategy_result['strategy_id'] is not None
        assert strategy_result['action'] == 'OPEN_POSITION'
        assert strategy_result['position_size'] > 0
        
        # Verify method call
        mock_strategy_manager.process_agent_signal.assert_called_once_with(agent_signal)
    
    @pytest.mark.asyncio
    async def test_strategy_to_execution_flow(self):
        """Test data flow from strategy manager to execution."""
        # Mock strategy decision
        strategy_decision = {
            'strategy_id': 'momentum_strategy_001',
            'action': 'OPEN_POSITION',
            'symbol': '00700.HK',
            'position_size': 1000,
            'price': 300.50
        }
        
        # Mock execution system
        mock_execution = AsyncMock()
        mock_execution.execute_order.return_value = {
            'order_id': 'ORD_001',
            'status': 'FILLED',
            'filled_price': 300.45,
            'filled_quantity': 1000,
            'timestamp': datetime.now()
        }
        
        # Test data flow
        execution_result = await mock_execution.execute_order(strategy_decision)
        
        # Verify data flow
        assert execution_result['order_id'] is not None
        assert execution_result['status'] == 'FILLED'
        assert execution_result['filled_quantity'] == 1000
        
        # Verify method call
        mock_execution.execute_order.assert_called_once_with(strategy_decision)


class TestBusinessProcessIntegration(IntegrationTestBase):
    """Test business process integration."""
    
    @pytest.mark.asyncio
    async def test_trading_workflow_integration(self):
        """Test complete trading workflow integration."""
        # Mock components
        mock_data_adapter = AsyncMock()
        mock_analyst = AsyncMock()
        mock_trader = AsyncMock()
        mock_portfolio_manager = AsyncMock()
        mock_risk_analyst = AsyncMock()
        
        # Setup mock responses
        mock_data_adapter.get_market_data.return_value = {
            'symbol': '00700.HK',
            'price': 300.50,
            'volume': 1000000,
            'timestamp': datetime.now()
        }
        
        mock_analyst.analyze_market_data.return_value = {
            'signal': 'BUY',
            'confidence': 0.85,
            'reasoning': 'Strong momentum detected'
        }
        
        mock_trader.generate_trading_signal.return_value = {
            'action': 'BUY',
            'quantity': 1000,
            'price': 300.50,
            'stop_loss': 295.00,
            'take_profit': 310.00
        }
        
        mock_portfolio_manager.optimize_portfolio.return_value = {
            'optimized_weights': {'00700.HK': 0.3, '2800.HK': 0.7},
            'expected_return': 0.12,
            'risk_score': 0.15
        }
        
        mock_risk_analyst.assess_risk.return_value = {
            'risk_score': 0.15,
            'var_95': 0.05,
            'recommendation': 'ACCEPT'
        }
        
        # Execute trading workflow
        # Step 1: Get market data
        market_data = await mock_data_adapter.get_market_data('00700.HK')
        
        # Step 2: Analyze market data
        analysis = await mock_analyst.analyze_market_data(market_data)
        
        # Step 3: Generate trading signal
        trading_signal = await mock_trader.generate_trading_signal(analysis)
        
        # Step 4: Optimize portfolio
        portfolio_optimization = await mock_portfolio_manager.optimize_portfolio(trading_signal)
        
        # Step 5: Assess risk
        risk_assessment = await mock_risk_analyst.assess_risk(portfolio_optimization)
        
        # Verify workflow results
        assert market_data['symbol'] == '00700.HK'
        assert analysis['signal'] == 'BUY'
        assert trading_signal['action'] == 'BUY'
        assert portfolio_optimization['expected_return'] > 0
        assert risk_assessment['recommendation'] == 'ACCEPT'
    
    @pytest.mark.asyncio
    async def test_risk_management_workflow(self):
        """Test risk management workflow integration."""
        # Mock risk management components
        mock_risk_analyst = AsyncMock()
        mock_portfolio_manager = AsyncMock()
        mock_monitoring_system = AsyncMock()
        
        # Setup mock responses
        mock_risk_analyst.calculate_var.return_value = {
            'var_95': 0.05,
            'var_99': 0.08,
            'expected_shortfall': 0.12
        }
        
        mock_risk_analyst.stress_test.return_value = {
            'scenario_1': {'loss': 0.15, 'probability': 0.01},
            'scenario_2': {'loss': 0.25, 'probability': 0.005}
        }
        
        mock_portfolio_manager.get_current_positions.return_value = {
            '00700.HK': {'quantity': 1000, 'value': 300500},
            '2800.HK': {'quantity': 2000, 'value': 560000}
        }
        
        mock_monitoring_system.check_risk_limits.return_value = {
            'within_limits': True,
            'current_risk': 0.12,
            'risk_limit': 0.15
        }
        
        # Execute risk management workflow
        # Step 1: Calculate VaR
        var_result = await mock_risk_analyst.calculate_var()
        
        # Step 2: Perform stress test
        stress_test_result = await mock_risk_analyst.stress_test()
        
        # Step 3: Get current positions
        current_positions = await mock_portfolio_manager.get_current_positions()
        
        # Step 4: Check risk limits
        risk_check = await mock_monitoring_system.check_risk_limits()
        
        # Verify workflow results
        assert var_result['var_95'] > 0
        assert len(stress_test_result) > 0
        assert len(current_positions) > 0
        assert risk_check['within_limits'] is True
    
    @pytest.mark.asyncio
    async def test_strategy_optimization_workflow(self):
        """Test strategy optimization workflow integration."""
        # Mock strategy optimization components
        mock_strategy_manager = AsyncMock()
        mock_backtest_engine = AsyncMock()
        mock_optimizer = AsyncMock()
        
        # Setup mock responses
        mock_strategy_manager.get_active_strategies.return_value = [
            {'strategy_id': 'strategy_001', 'name': 'Momentum Strategy'},
            {'strategy_id': 'strategy_002', 'name': 'Mean Reversion Strategy'}
        ]
        
        mock_backtest_engine.run_backtest.return_value = {
            'strategy_id': 'strategy_001',
            'sharpe_ratio': 1.85,
            'max_drawdown': 0.12,
            'total_return': 0.25
        }
        
        mock_optimizer.optimize_parameters.return_value = {
            'optimized_parameters': {'lookback_period': 20, 'threshold': 0.02},
            'performance_improvement': 0.15,
            'new_sharpe_ratio': 2.1
        }
        
        # Execute strategy optimization workflow
        # Step 1: Get active strategies
        active_strategies = await mock_strategy_manager.get_active_strategies()
        
        # Step 2: Run backtest for each strategy
        backtest_results = []
        for strategy in active_strategies:
            result = await mock_backtest_engine.run_backtest(strategy['strategy_id'])
            backtest_results.append(result)
        
        # Step 3: Optimize best performing strategy
        best_strategy = max(backtest_results, key=lambda x: x['sharpe_ratio'])
        optimization_result = await mock_optimizer.optimize_parameters(best_strategy['strategy_id'])
        
        # Verify workflow results
        assert len(active_strategies) > 0
        assert len(backtest_results) > 0
        assert best_strategy['sharpe_ratio'] > 0
        assert optimization_result['performance_improvement'] > 0


class TestPerformanceIntegration(IntegrationTestBase):
    """Test performance integration."""
    
    @pytest.mark.asyncio
    async def test_system_performance_under_load(self):
        """Test system performance under load."""
        # Performance test configuration
        concurrent_requests = 100
        test_duration = 30  # seconds
        
        # Mock system components
        mock_analyst = AsyncMock()
        mock_analyst.analyze_market_data.return_value = {
            'signal': 'BUY',
            'confidence': 0.85,
            'processing_time': 0.05
        }
        
        # Performance test
        start_time = time.time()
        tasks = []
        
        for i in range(concurrent_requests):
            task = asyncio.create_task(
                mock_analyst.analyze_market_data({
                    'symbol': f'TEST{i:03d}.HK',
                    'price': 100.0 + i,
                    'timestamp': datetime.now()
                })
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance metrics
        requests_per_second = concurrent_requests / total_time
        average_response_time = total_time / concurrent_requests
        
        # Verify performance
        assert len(results) == concurrent_requests
        assert requests_per_second > 10  # At least 10 requests per second
        assert average_response_time < 1.0  # Average response time under 1 second
        
        self.logger.info(f"Performance test results:")
        self.logger.info(f"  Total requests: {concurrent_requests}")
        self.logger.info(f"  Total time: {total_time:.2f} seconds")
        self.logger.info(f"  Requests per second: {requests_per_second:.2f}")
        self.logger.info(f"  Average response time: {average_response_time:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage under load."""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large number of objects
        large_objects = []
        for i in range(1000):
            obj = {
                'id': i,
                'data': 'x' * 1000,  # 1KB per object
                'timestamp': datetime.now(),
                'nested': {
                    'value1': i * 2,
                    'value2': i * 3,
                    'value3': [j for j in range(10)]
                }
            }
            large_objects.append(obj)
        
        # Get memory usage after creating objects
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Cleanup
        del large_objects
        gc.collect()
        
        # Get memory usage after cleanup
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory usage metrics
        memory_increase = peak_memory - initial_memory
        memory_recovered = peak_memory - final_memory
        
        # Verify memory management
        assert memory_increase > 0  # Memory should increase
        assert memory_recovered > 0  # Memory should be recovered after cleanup
        assert final_memory < initial_memory * 1.5  # Final memory should not be too high
        
        self.logger.info(f"Memory usage test results:")
        self.logger.info(f"  Initial memory: {initial_memory:.2f} MB")
        self.logger.info(f"  Peak memory: {peak_memory:.2f} MB")
        self.logger.info(f"  Final memory: {final_memory:.2f} MB")
        self.logger.info(f"  Memory increase: {memory_increase:.2f} MB")
        self.logger.info(f"  Memory recovered: {memory_recovered:.2f} MB")
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_processing(self):
        """Test concurrent AI agent processing."""
        # Mock AI agents
        agents = []
        for i in range(10):
            agent = AsyncMock()
            agent.process_signal.return_value = {
                'agent_id': f'agent_{i}',
                'signal': 'BUY' if i % 2 == 0 else 'SELL',
                'confidence': 0.5 + (i * 0.05),
                'processing_time': 0.1 + (i * 0.01)
            }
            agents.append(agent)
        
        # Test concurrent processing
        start_time = time.time()
        
        tasks = []
        for i, agent in enumerate(agents):
            task = asyncio.create_task(
                agent.process_signal({
                    'symbol': f'TEST{i:03d}.HK',
                    'price': 100.0 + i,
                    'timestamp': datetime.now()
                })
            )
            tasks.append(task)
        
        # Wait for all agents to complete
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify results
        assert len(results) == len(agents)
        assert all(result['agent_id'].startswith('agent_') for result in results)
        assert total_time < 2.0  # Should complete within 2 seconds
        
        self.logger.info(f"Concurrent agent processing test results:")
        self.logger.info(f"  Number of agents: {len(agents)}")
        self.logger.info(f"  Total processing time: {total_time:.2f} seconds")
        self.logger.info(f"  Average processing time per agent: {total_time / len(agents):.2f} seconds")


class TestErrorHandlingIntegration(IntegrationTestBase):
    """Test error handling integration."""
    
    @pytest.mark.asyncio
    async def test_component_failure_recovery(self):
        """Test component failure recovery."""
        # Mock failing component
        mock_failing_component = AsyncMock()
        mock_failing_component.process.side_effect = Exception("Component failure")
        
        # Mock recovery mechanism
        recovery_attempts = 0
        max_attempts = 3
        
        async def recover_component():
            nonlocal recovery_attempts
            recovery_attempts += 1
            if recovery_attempts < max_attempts:
                raise Exception("Recovery failed")
            return True
        
        # Test failure and recovery
        try:
            await mock_failing_component.process()
        except Exception as e:
            assert str(e) == "Component failure"
            
            # Attempt recovery
            recovery_success = await recover_component()
            assert recovery_success is True
            assert recovery_attempts == max_attempts
    
    @pytest.mark.asyncio
    async def test_data_validation_error_handling(self):
        """Test data validation error handling."""
        # Mock data validator
        def validate_data(data):
            if 'symbol' not in data:
                raise ValueError("Missing required field: symbol")
            if 'price' not in data:
                raise ValueError("Missing required field: price")
            if data['price'] <= 0:
                raise ValueError("Price must be positive")
            return True
        
        # Test valid data
        valid_data = {'symbol': '00700.HK', 'price': 300.50}
        assert validate_data(valid_data) is True
        
        # Test invalid data - missing symbol
        try:
            invalid_data = {'price': 300.50}
            validate_data(invalid_data)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Missing required field: symbol" in str(e)
        
        # Test invalid data - negative price
        try:
            invalid_data = {'symbol': '00700.HK', 'price': -100.0}
            validate_data(invalid_data)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Price must be positive" in str(e)
    
    @pytest.mark.asyncio
    async def test_network_failure_handling(self):
        """Test network failure handling."""
        # Mock network component
        network_failures = 0
        max_failures = 3
        
        async def mock_network_call():
            nonlocal network_failures
            network_failures += 1
            if network_failures <= max_failures:
                raise ConnectionError("Network connection failed")
            return {"status": "success", "data": "test_data"}
        
        # Test network failure and recovery
        for attempt in range(max_failures + 1):
            try:
                result = await mock_network_call()
                if attempt == max_failures:
                    assert result["status"] == "success"
                    break
            except ConnectionError as e:
                assert "Network connection failed" in str(e)
                if attempt < max_failures:
                    # Wait before retry
                    await asyncio.sleep(0.1)


class TestConfigurationIntegration(IntegrationTestBase):
    """Test configuration integration."""
    
    @pytest.mark.asyncio
    async def test_configuration_loading_and_validation(self):
        """Test configuration loading and validation."""
        # Create test configuration
        test_config = {
            'environment': {
                'name': 'test',
                'debug': True,
                'log_level': 'DEBUG'
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'test_db'
            },
            'trading': {
                'symbols': ['00700.HK', '2800.HK'],
                'max_position_size': 1000000.0
            }
        }
        
        # Save test configuration
        config_file = self.test_data_path / "test_config.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        # Test configuration loading
        config_manager = ConfigManager(str(self.test_data_path))
        await config_manager.initialize()
        
        # Verify configuration loading
        assert config_manager.get_config('environment', 'name') == 'test'
        assert config_manager.get_config('database', 'host') == 'localhost'
        assert config_manager.get_config('trading', 'symbols') == ['00700.HK', '2800.HK']
    
    @pytest.mark.asyncio
    async def test_environment_variable_override(self):
        """Test environment variable configuration override."""
        # Set environment variables
        os.environ['TRADING_ENV'] = 'production'
        os.environ['TRADING_DEBUG'] = 'false'
        os.environ['TRADING_LOG_LEVEL'] = 'INFO'
        
        try:
            # Create configuration manager
            config_manager = ConfigManager()
            await config_manager.initialize()
            
            # Verify environment variable override
            assert config_manager.get_config('environment', 'name') == 'production'
            assert config_manager.get_config('environment', 'debug') is False
            assert config_manager.get_config('logging', 'level') == 'INFO'
            
        finally:
            # Cleanup environment variables
            for key in ['TRADING_ENV', 'TRADING_DEBUG', 'TRADING_LOG_LEVEL']:
                if key in os.environ:
                    del os.environ[key]


class TestMonitoringIntegration(IntegrationTestBase):
    """Test monitoring integration."""
    
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self):
        """Test health monitoring integration."""
        # Create health monitor
        health_monitor = SystemHealthMonitor()
        await health_monitor.initialize()
        
        # Add test component
        from src.integration.health_monitor import ComponentHealth, HealthStatus
        test_component = ComponentHealth(
            component_id="test_component",
            status=HealthStatus.HEALTHY,
            message="Test component is healthy"
        )
        health_monitor.component_health["test_component"] = test_component
        
        # Test health check
        system_health = await health_monitor.check_system_health()
        
        # Verify health check results
        assert system_health is not None
        assert system_health.system_id == "trading_system"
        assert system_health.total_components == 1
        assert system_health.healthy_components == 1
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test performance monitoring integration."""
        # Mock performance monitor
        mock_performance_monitor = AsyncMock()
        mock_performance_monitor.collect_metrics.return_value = {
            'cpu_usage': 25.5,
            'memory_usage': 512.0,
            'disk_usage': 75.2,
            'network_io': 1024.0
        }
        
        # Test performance monitoring
        metrics = await mock_performance_monitor.collect_metrics()
        
        # Verify metrics
        assert metrics['cpu_usage'] > 0
        assert metrics['memory_usage'] > 0
        assert metrics['disk_usage'] > 0
        assert metrics['network_io'] > 0


# Test utilities
class TestUtils:
    """Test utilities for integration tests."""
    
    @staticmethod
    def create_mock_market_data(symbol: str, price: float, volume: int) -> Dict[str, Any]:
        """Create mock market data."""
        return {
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'timestamp': datetime.now(),
            'bid': price - 0.01,
            'ask': price + 0.01,
            'high': price + 1.0,
            'low': price - 1.0,
            'open': price - 0.5,
            'close': price
        }
    
    @staticmethod
    def create_mock_trading_signal(symbol: str, action: str, confidence: float) -> Dict[str, Any]:
        """Create mock trading signal."""
        return {
            'symbol': symbol,
            'action': action,
            'confidence': confidence,
            'timestamp': datetime.now(),
            'price': 300.50,
            'quantity': 1000,
            'stop_loss': 295.00,
            'take_profit': 310.00
        }
    
    @staticmethod
    def create_mock_portfolio_data() -> Dict[str, Any]:
        """Create mock portfolio data."""
        return {
            'total_value': 1000000.0,
            'cash': 200000.0,
            'positions': {
                '00700.HK': {'quantity': 1000, 'value': 300500.0, 'weight': 0.3},
                '2800.HK': {'quantity': 2000, 'value': 560000.0, 'weight': 0.56}
            },
            'performance': {
                'daily_return': 0.02,
                'total_return': 0.15,
                'sharpe_ratio': 1.85,
                'max_drawdown': 0.12
            }
        }


# Performance benchmarks
class PerformanceBenchmarks:
    """Performance benchmarks for integration tests."""
    
    @staticmethod
    async def benchmark_data_processing_throughput():
        """Benchmark data processing throughput."""
        # Mock data processor
        async def process_data(data):
            await asyncio.sleep(0.001)  # Simulate processing time
            return {'processed': True, 'data': data}
        
        # Benchmark parameters
        num_records = 1000
        batch_size = 100
        
        start_time = time.time()
        
        # Process data in batches
        for i in range(0, num_records, batch_size):
            batch = [{'id': j, 'value': j * 2} for j in range(i, min(i + batch_size, num_records))]
            tasks = [process_data(record) for record in batch]
            await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = num_records / total_time
        
        return {
            'total_records': num_records,
            'total_time': total_time,
            'throughput': throughput,
            'records_per_second': throughput
        }
    
    @staticmethod
    async def benchmark_concurrent_requests():
        """Benchmark concurrent request handling."""
        # Mock request handler
        async def handle_request(request_id):
            await asyncio.sleep(0.01)  # Simulate processing time
            return {'request_id': request_id, 'status': 'processed'}
        
        # Benchmark parameters
        num_requests = 500
        concurrent_limit = 50
        
        start_time = time.time()
        
        # Process requests with concurrency limit
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def limited_request(request_id):
            async with semaphore:
                return await handle_request(request_id)
        
        tasks = [limited_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        requests_per_second = num_requests / total_time
        
        return {
            'total_requests': num_requests,
            'concurrent_limit': concurrent_limit,
            'total_time': total_time,
            'requests_per_second': requests_per_second,
            'successful_requests': len([r for r in results if r['status'] == 'processed'])
        }


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
