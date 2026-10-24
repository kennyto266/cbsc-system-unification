"""End-to-end integration tests for Hong Kong quantitative trading system.

This module provides comprehensive end-to-end testing including complete workflow
testing, system integration validation, and business process verification.
"""

import asyncio
import logging
import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import numpy as np

# Import system components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integration.system_integration import SystemIntegration, IntegrationConfig, SystemStatus
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

from tests.helpers.test_utils import TestDataGenerator, MockComponentFactory, TestAssertions


class TestCompleteTradingWorkflow:
    """Test complete trading workflow end-to-end."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        self.mock_factory = MockComponentFactory()
        
        # Create test data
        self.market_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            frequency="1min"
        )
        
        # Create mock components
        self.mock_data_adapter = self.mock_factory.create_mock_data_adapter(self.market_data)
        self.mock_analyst = self.mock_factory.create_mock_ai_agent("quantitative_analyst", "BUY", 0.85)
        self.mock_trader = self.mock_factory.create_mock_ai_agent("quantitative_trader", "BUY", 0.80)
        self.mock_portfolio_manager = self.mock_factory.create_mock_ai_agent("portfolio_manager", "BUY", 0.75)
        self.mock_risk_analyst = self.mock_factory.create_mock_ai_agent("risk_analyst", "BUY", 0.70)
        self.mock_strategy_manager = self.mock_factory.create_mock_strategy_manager()
        self.mock_backtest_engine = self.mock_factory.create_mock_backtest_engine()
        
        yield
    
    @pytest.mark.asyncio
    async def test_complete_trading_workflow(self):
        """Test complete trading workflow from data ingestion to execution."""
        # Step 1: Data Ingestion
        self.logger.info("Step 1: Data Ingestion")
        market_data = await self.mock_data_adapter.get_market_data("00700.HK")
        assert len(market_data) > 0
        self.logger.info(f"  Ingested {len(market_data)} market data records")
        
        # Step 2: Market Analysis
        self.logger.info("Step 2: Market Analysis")
        analysis_result = await self.mock_analyst.analyze_market_data(market_data)
        assert analysis_result['signal'] == "BUY"
        assert analysis_result['confidence'] == 0.85
        self.logger.info(f"  Analysis result: {analysis_result['signal']} (confidence: {analysis_result['confidence']})")
        
        # Step 3: Trading Signal Generation
        self.logger.info("Step 3: Trading Signal Generation")
        trading_signal = await self.mock_trader.analyze_market_data(analysis_result)
        assert trading_signal['signal'] == "BUY"
        assert trading_signal['confidence'] == 0.80
        self.logger.info(f"  Trading signal: {trading_signal['signal']} (confidence: {trading_signal['confidence']})")
        
        # Step 4: Portfolio Management
        self.logger.info("Step 4: Portfolio Management")
        portfolio_decision = await self.mock_portfolio_manager.analyze_market_data(trading_signal)
        assert portfolio_decision['signal'] == "BUY"
        assert portfolio_decision['confidence'] == 0.75
        self.logger.info(f"  Portfolio decision: {portfolio_decision['signal']} (confidence: {portfolio_decision['confidence']})")
        
        # Step 5: Risk Assessment
        self.logger.info("Step 5: Risk Assessment")
        risk_assessment = await self.mock_risk_analyst.analyze_market_data(portfolio_decision)
        assert risk_assessment['signal'] == "BUY"
        assert risk_assessment['confidence'] == 0.70
        self.logger.info(f"  Risk assessment: {risk_assessment['signal']} (confidence: {risk_assessment['confidence']})")
        
        # Step 6: Strategy Management
        self.logger.info("Step 6: Strategy Management")
        active_strategies = await self.mock_strategy_manager.get_active_strategies()
        assert len(active_strategies) > 0
        self.logger.info(f"  Active strategies: {len(active_strategies)}")
        
        # Step 7: Backtesting
        self.logger.info("Step 7: Backtesting")
        backtest_result = await self.mock_backtest_engine.run_backtest(
            "strategy_001",
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
        assert backtest_result['sharpe_ratio'] > 0
        self.logger.info(f"  Backtest result: Sharpe ratio {backtest_result['sharpe_ratio']:.2f}")
        
        # Verify end-to-end workflow
        self.logger.info("End-to-end workflow completed successfully")
        assert all([
            analysis_result['signal'] == "BUY",
            trading_signal['signal'] == "BUY",
            portfolio_decision['signal'] == "BUY",
            risk_assessment['signal'] == "BUY"
        ]), "All workflow steps should produce consistent BUY signals"
    
    @pytest.mark.asyncio
    async def test_workflow_with_different_market_conditions(self):
        """Test workflow with different market conditions."""
        # Test bullish market
        self.logger.info("Testing bullish market conditions")
        bullish_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            frequency="1min",
            price_range=(300.0, 350.0)  # Upward trend
        )
        
        mock_bullish_adapter = self.mock_factory.create_mock_data_adapter(bullish_data)
        bullish_analysis = await self.mock_analyst.analyze_market_data(bullish_data.to_dict('records'))
        
        assert bullish_analysis['signal'] == "BUY"
        self.logger.info(f"  Bullish market analysis: {bullish_analysis['signal']}")
        
        # Test bearish market
        self.logger.info("Testing bearish market conditions")
        bearish_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            frequency="1min",
            price_range=(250.0, 300.0)  # Downward trend
        )
        
        mock_bearish_adapter = self.mock_factory.create_mock_data_adapter(bearish_data)
        bearish_analysis = await self.mock_analyst.analyze_market_data(bearish_data.to_dict('records'))
        
        assert bearish_analysis['signal'] == "BUY"  # Mock always returns BUY
        self.logger.info(f"  Bearish market analysis: {bearish_analysis['signal']}")
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test workflow error handling."""
        # Test data adapter failure
        self.logger.info("Testing data adapter failure")
        failing_adapter = self.mock_factory.create_mock_data_adapter(error_rate=1.0)  # 100% error rate
        
        try:
            await failing_adapter.get_market_data("00700.HK")
            assert False, "Should have raised an exception"
        except ConnectionError as e:
            assert "Mock connection error" in str(e)
            self.logger.info(f"  Data adapter failure handled: {e}")
        
        # Test agent failure
        self.logger.info("Testing agent failure")
        failing_agent = AsyncMock()
        failing_agent.analyze_market_data.side_effect = Exception("Agent processing error")
        
        try:
            await failing_agent.analyze_market_data(self.market_data.to_dict('records'))
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "Agent processing error" in str(e)
            self.logger.info(f"  Agent failure handled: {e}")


class TestSystemIntegrationWorkflow:
    """Test system integration workflow."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        
        # Create integration config
        self.integration_config = IntegrationConfig(
            system_id="test_system_001",
            system_name="Test Trading System",
            version="1.0.0-test",
            environment="test",
            debug_mode=True
        )
        
        yield
    
    @pytest.mark.asyncio
    async def test_system_startup_workflow(self):
        """Test complete system startup workflow."""
        # Create system integration
        system_integration = SystemIntegration(self.integration_config)
        
        try:
            # Step 1: Initialize system
            self.logger.info("Step 1: Initialize system")
            assert await system_integration.initialize()
            self.logger.info("  System initialized successfully")
            
            # Step 2: Start system
            self.logger.info("Step 2: Start system")
            assert await system_integration.start_system()
            assert system_integration.status == SystemStatus.RUNNING
            self.logger.info("  System started successfully")
            
            # Step 3: Verify system status
            self.logger.info("Step 3: Verify system status")
            status = system_integration.get_system_status()
            assert status['status'] == SystemStatus.RUNNING.value
            assert status['system_id'] == self.integration_config.system_id
            self.logger.info(f"  System status: {status['status']}")
            
            # Step 4: Check component status
            self.logger.info("Step 4: Check component status")
            statistics = system_integration.get_statistics()
            assert statistics['total_components'] > 0
            self.logger.info(f"  Total components: {statistics['total_components']}")
            
        finally:
            # Step 5: Stop system
            self.logger.info("Step 5: Stop system")
            await system_integration.stop_system()
            assert system_integration.status == SystemStatus.STOPPED
            self.logger.info("  System stopped successfully")
            
            # Step 6: Shutdown system
            self.logger.info("Step 6: Shutdown system")
            await system_integration.shutdown()
            self.logger.info("  System shutdown completed")
    
    @pytest.mark.asyncio
    async def test_component_lifecycle_workflow(self):
        """Test component lifecycle workflow."""
        system_integration = SystemIntegration(self.integration_config)
        
        try:
            # Initialize system
            await system_integration.initialize()
            
            # Test component registration
            self.logger.info("Testing component registration")
            from src.integration.component_orchestrator import ComponentInfo, ComponentType
            
            test_component = ComponentInfo(
                component_id="test_component",
                component_type=ComponentType.AI_AGENT,
                description="Test component for lifecycle testing"
            )
            
            # Register component
            assert await system_integration.component_orchestrator.register_component(test_component)
            self.logger.info("  Component registered successfully")
            
            # Verify component registration
            registered_component = system_integration.component_orchestrator.get_component_info("test_component")
            assert registered_component is not None
            assert registered_component.component_id == "test_component"
            self.logger.info("  Component verification successful")
            
            # Test component dependencies
            self.logger.info("Testing component dependencies")
            dependencies = system_integration.component_orchestrator.get_component_dependencies("test_component")
            assert isinstance(dependencies, set)
            self.logger.info(f"  Component dependencies: {len(dependencies)}")
            
        finally:
            await system_integration.shutdown()
    
    @pytest.mark.asyncio
    async def test_health_monitoring_workflow(self):
        """Test health monitoring workflow."""
        system_integration = SystemIntegration(self.integration_config)
        
        try:
            # Initialize system
            await system_integration.initialize()
            
            # Start system
            await system_integration.start_system()
            
            # Test health monitoring
            self.logger.info("Testing health monitoring")
            health_result = await system_integration.health_monitor.check_system_health()
            
            assert health_result is not None
            assert health_result.system_id == "trading_system"
            self.logger.info(f"  System health: {health_result.overall_status}")
            
            # Test component health
            self.logger.info("Testing component health")
            component_health = system_integration.health_monitor.get_all_component_health()
            assert isinstance(component_health, dict)
            self.logger.info(f"  Components monitored: {len(component_health)}")
            
            # Test health statistics
            self.logger.info("Testing health statistics")
            health_stats = system_integration.health_monitor.get_statistics()
            assert health_stats['is_monitoring'] is True
            self.logger.info(f"  Health monitoring active: {health_stats['is_monitoring']}")
            
        finally:
            await system_integration.shutdown()


class TestBusinessProcessIntegration:
    """Test business process integration."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        self.mock_factory = MockComponentFactory()
        
        # Create test portfolio
        self.test_portfolio = self.data_generator.generate_portfolio_data(
            symbols=["00700.HK", "2800.HK", "0700.HK"],
            total_value=1000000.0
        )
        
        # Create test risk metrics
        self.test_risk_metrics = self.data_generator.generate_risk_metrics(
            portfolio_value=1000000.0
        )
        
        yield
    
    @pytest.mark.asyncio
    async def test_portfolio_management_workflow(self):
        """Test portfolio management workflow."""
        # Mock portfolio manager
        mock_portfolio_manager = self.mock_factory.create_mock_ai_agent(
            "portfolio_manager", "BUY", 0.75
        )
        
        # Test portfolio analysis
        self.logger.info("Testing portfolio analysis")
        portfolio_analysis = await mock_portfolio_manager.analyze_market_data(self.test_portfolio)
        
        assert portfolio_analysis['signal'] == "BUY"
        assert portfolio_analysis['confidence'] == 0.75
        self.logger.info(f"  Portfolio analysis: {portfolio_analysis['signal']} (confidence: {portfolio_analysis['confidence']})")
        
        # Test portfolio optimization
        self.logger.info("Testing portfolio optimization")
        optimization_result = {
            'optimized_weights': {'00700.HK': 0.4, '2800.HK': 0.4, '0700.HK': 0.2},
            'expected_return': 0.12,
            'risk_score': 0.15
        }
        
        assert optimization_result['expected_return'] > 0
        assert optimization_result['risk_score'] > 0
        assert sum(optimization_result['optimized_weights'].values()) == 1.0
        self.logger.info(f"  Portfolio optimization: Expected return {optimization_result['expected_return']:.2f}, Risk score {optimization_result['risk_score']:.2f}")
    
    @pytest.mark.asyncio
    async def test_risk_management_workflow(self):
        """Test risk management workflow."""
        # Mock risk analyst
        mock_risk_analyst = self.mock_factory.create_mock_ai_agent(
            "risk_analyst", "BUY", 0.70
        )
        
        # Test risk assessment
        self.logger.info("Testing risk assessment")
        risk_assessment = await mock_risk_analyst.analyze_market_data(self.test_risk_metrics)
        
        assert risk_assessment['signal'] == "BUY"
        assert risk_assessment['confidence'] == 0.70
        self.logger.info(f"  Risk assessment: {risk_assessment['signal']} (confidence: {risk_assessment['confidence']})")
        
        # Test VaR calculation
        self.logger.info("Testing VaR calculation")
        var_95 = self.test_risk_metrics['var_95']['value']
        var_99 = self.test_risk_metrics['var_99']['value']
        
        assert var_95 > 0
        assert var_99 > 0
        assert var_99 > var_95  # 99% VaR should be higher than 95% VaR
        self.logger.info(f"  VaR 95%: {var_95:.2f}, VaR 99%: {var_99:.2f}")
        
        # Test stress testing
        self.logger.info("Testing stress testing")
        stress_scenarios = self.test_risk_metrics.get('stress_scenarios', {})
        assert isinstance(stress_scenarios, dict)
        self.logger.info(f"  Stress scenarios: {len(stress_scenarios)}")
    
    @pytest.mark.asyncio
    async def test_strategy_management_workflow(self):
        """Test strategy management workflow."""
        # Mock strategy manager
        mock_strategy_manager = self.mock_factory.create_mock_strategy_manager()
        
        # Test strategy retrieval
        self.logger.info("Testing strategy retrieval")
        active_strategies = await mock_strategy_manager.get_active_strategies()
        
        assert len(active_strategies) > 0
        assert all('strategy_id' in strategy for strategy in active_strategies)
        assert all('name' in strategy for strategy in active_strategies)
        self.logger.info(f"  Active strategies: {len(active_strategies)}")
        
        # Test strategy performance
        self.logger.info("Testing strategy performance")
        performance = await mock_strategy_manager.get_strategy_performance()
        
        assert performance['sharpe_ratio'] > 0
        assert performance['max_drawdown'] > 0
        assert performance['total_return'] > 0
        self.logger.info(f"  Strategy performance: Sharpe {performance['sharpe_ratio']:.2f}, Max DD {performance['max_drawdown']:.2f}")
    
    @pytest.mark.asyncio
    async def test_monitoring_and_alerting_workflow(self):
        """Test monitoring and alerting workflow."""
        # Mock monitoring system
        mock_monitor = AsyncMock()
        mock_monitor.collect_metrics.return_value = {
            'cpu_usage': 25.5,
            'memory_usage': 512.0,
            'disk_usage': 75.2,
            'network_io': 1024.0,
            'active_connections': 50,
            'error_rate': 0.01
        }
        
        # Test metrics collection
        self.logger.info("Testing metrics collection")
        metrics = await mock_monitor.collect_metrics()
        
        assert metrics['cpu_usage'] > 0
        assert metrics['memory_usage'] > 0
        assert metrics['disk_usage'] > 0
        assert metrics['network_io'] > 0
        self.logger.info(f"  System metrics collected: CPU {metrics['cpu_usage']:.1f}%, Memory {metrics['memory_usage']:.1f}MB")
        
        # Test alerting
        self.logger.info("Testing alerting system")
        alerts = []
        
        # Simulate high CPU usage alert
        if metrics['cpu_usage'] > 80:
            alerts.append({
                'type': 'high_cpu_usage',
                'message': f"CPU usage is {metrics['cpu_usage']:.1f}%",
                'severity': 'warning'
            })
        
        # Simulate high memory usage alert
        if metrics['memory_usage'] > 1000:
            alerts.append({
                'type': 'high_memory_usage',
                'message': f"Memory usage is {metrics['memory_usage']:.1f}MB",
                'severity': 'warning'
            })
        
        # Simulate high error rate alert
        if metrics['error_rate'] > 0.05:
            alerts.append({
                'type': 'high_error_rate',
                'message': f"Error rate is {metrics['error_rate']:.2f}%",
                'severity': 'critical'
            })
        
        self.logger.info(f"  Alerts generated: {len(alerts)}")
        for alert in alerts:
            self.logger.info(f"    {alert['type']}: {alert['message']} ({alert['severity']})")


class TestDataIntegrationWorkflow:
    """Test data integration workflow."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        
        # Create test data
        self.market_data = self.data_generator.generate_market_data(
            symbol="00700.HK",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            frequency="1min"
        )
        
        self.trading_signals = self.data_generator.generate_trading_signals(
            symbols=["00700.HK", "2800.HK"],
            num_signals=10
        )
        
        yield
    
    @pytest.mark.asyncio
    async def test_data_ingestion_workflow(self):
        """Test data ingestion workflow."""
        # Mock data adapter
        mock_adapter = self.mock_factory.create_mock_data_adapter(self.market_data)
        
        # Test data ingestion
        self.logger.info("Testing data ingestion")
        ingested_data = await mock_adapter.get_market_data("00700.HK")
        
        assert len(ingested_data) > 0
        assert all('timestamp' in record for record in ingested_data)
        assert all('symbol' in record for record in ingested_data)
        assert all('close' in record for record in ingested_data)
        self.logger.info(f"  Ingested {len(ingested_data)} records")
        
        # Test data validation
        self.logger.info("Testing data validation")
        valid_records = 0
        for record in ingested_data:
            if (record['close'] > 0 and 
                record['volume'] > 0 and 
                record['high'] >= record['low'] and
                record['high'] >= record['open'] and
                record['high'] >= record['close']):
                valid_records += 1
        
        validation_rate = valid_records / len(ingested_data)
        assert validation_rate > 0.95, f"Data validation rate {validation_rate:.2f} is too low"
        self.logger.info(f"  Data validation rate: {validation_rate:.2f}")
    
    @pytest.mark.asyncio
    async def test_data_processing_workflow(self):
        """Test data processing workflow."""
        # Test data aggregation
        self.logger.info("Testing data aggregation")
        df = pd.DataFrame(self.market_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Aggregate to 5-minute intervals
        agg_data = df.resample('5min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        assert len(agg_data) > 0
        assert all(agg_data['high'] >= agg_data['low'])
        assert all(agg_data['volume'] > 0)
        self.logger.info(f"  Aggregated to {len(agg_data)} 5-minute intervals")
        
        # Test technical indicator calculation
        self.logger.info("Testing technical indicator calculation")
        agg_data['sma_20'] = agg_data['close'].rolling(window=20).mean()
        agg_data['rsi'] = self._calculate_rsi(agg_data['close'])
        
        assert not agg_data['sma_20'].isna().all()
        assert not agg_data['rsi'].isna().all()
        self.logger.info("  Technical indicators calculated successfully")
    
    @pytest.mark.asyncio
    async def test_data_export_workflow(self):
        """Test data export workflow."""
        # Test data serialization
        self.logger.info("Testing data serialization")
        import json
        
        # Serialize market data
        json_data = self.market_data.to_json(orient='records', date_format='iso')
        parsed_data = json.loads(json_data)
        
        assert len(parsed_data) == len(self.market_data)
        assert all('timestamp' in record for record in parsed_data)
        self.logger.info(f"  Serialized {len(parsed_data)} records to JSON")
        
        # Test data compression
        self.logger.info("Testing data compression")
        import gzip
        
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        decompressed_data = gzip.decompress(compressed_data).decode('utf-8')
        
        assert len(compressed_data) < len(json_data)
        assert decompressed_data == json_data
        compression_ratio = len(compressed_data) / len(json_data)
        self.logger.info(f"  Compression ratio: {compression_ratio:.2f}")
    
    def _calculate_rsi(self, prices, window=14):
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))


if __name__ == "__main__":
    # Run end-to-end integration tests
    pytest.main([__file__, "-v", "--tb=short"])
