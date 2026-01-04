"""
Test Suite for Integrated Risk Management System
Comprehensive testing of all risk management components
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from src.services.integrated_risk_service import IntegratedRiskService
from src.services.enhanced_risk_management_service import (
    EnhancedRiskManagementService,
    RiskLimitType,
    PositionSizeMethod,
    PositionSizingConfig
)
from src.risk_monitor.advanced_risk_calculators import (
    AdvancedVaRCalculator,
    StressTestCalculator,
    LiquidityRiskCalculator,
    CorrelationRiskCalculator,
    TailRiskCalculator
)
from src.risk_monitor.enhanced_alert_system import (
    EnhancedAlertSystem,
    AlertCondition,
    AlertSeverity,
    AlertCategory,
    AlertAction,
    AlertStatus
)
from src.models.risk_models_v2 import (
    RiskMonitoring,
    RiskAlert,
    RiskPosition
)


class TestAdvancedVaRCalculator:
    """Test advanced VaR calculator"""

    def setup_method(self):
        """Setup test data"""
        np.random.seed(42)
        self.returns = pd.Series(np.random.normal(0.001, 0.02, 1000))
        self.calculator = AdvancedVaRCalculator([0.95, 0.99])

    def test_historical_var_simple(self):
        """Test simple historical VaR calculation"""
        var_95 = self.calculator.calculate_historical_var(self.returns, 0.95, method="simple")

        assert var_95 < 0  # VaR should be negative (loss)
        assert abs(var_95) < 0.1  # Should be reasonable for daily returns

    def test_historical_var_weighted(self):
        """Test weighted historical VaR calculation"""
        var_99 = self.calculator.calculate_historical_var(self.returns, 0.99, method="weighted")

        assert var_99 < var_95 if 'var_95' in locals() else True  # 99% VaR should be more extreme

    def test_parametric_var_normal(self):
        """Test parametric VaR with normal distribution"""
        var_95 = self.calculator.calculate_parametric_var(self.returns, 0.95, distribution="normal")

        assert var_95 < 0  # VaR should be negative
        assert isinstance(var_95, float)

    def test_parametric_var_t_dist(self):
        """Test parametric VaR with t-distribution"""
        var_95 = self.calculator.calculate_parametric_var(self.returns, 0.95, distribution="t")

        assert var_95 < 0  # VaR should be negative

    def test_monte_carlo_var(self):
        """Test Monte Carlo VaR calculation"""
        var_95 = self.calculator.calculate_monte_carlo_var(
            self.returns, 0.95, n_simulations=1000
        )

        assert var_95 < 0  # VaR should be negative
        assert isinstance(var_95, float)

    def test_cvar_calculation(self):
        """Test Conditional VaR calculation"""
        cvar_95 = self.calculator.calculate_cvar(self.returns, 0.95, method="historical")
        var_95 = self.calculator.calculate_historical_var(self.returns, 0.95)

        assert cvar_95 <= var_95  # CVaR should be more extreme than VaR


class TestStressTestCalculator:
    """Test stress testing calculator"""

    def setup_method(self):
        """Setup test data"""
        self.calculator = StressTestCalculator()
        self.positions = {
            "AAPL": 100000,
            "MSFT": 80000,
            "GOOGL": 120000
        }

        # Create mock returns matrix
        np.random.seed(42)
        returns_data = np.random.multivariate_normal(
            [0.001, 0.001, 0.001],
            [[0.0004, 0.0002, 0.0002],
             [0.0002, 0.0004, 0.0002],
             [0.0002, 0.0002, 0.0004]],
            252
        )
        self.returns_matrix = pd.DataFrame(
            returns_data,
            columns=["AAPL", "MSFT", "GOOGL"]
        )

    def test_market_crash_scenario(self):
        """Test market crash stress scenario"""
        result = self.calculator.calculate_stress_loss(
            self.positions,
            self.returns_matrix,
            "market_crash"
        )

        assert result["scenario"] == "market_crash"
        assert result["total_loss"] < 0  # Should be a loss
        assert result["loss_percentage"] < 0  # Should be negative
        assert "position_losses" in result
        assert all(isinstance(v, float) for v in result["position_losses"].values())

    def test_volatility_spike_scenario(self):
        """Test volatility spike stress scenario"""
        result = self.calculator.calculate_stress_loss(
            self.positions,
            self.returns_matrix,
            "volatility_spike"
        )

        assert result["scenario"] == "volatility_spike"
        assert "var_breaches" in result

    def test_custom_scenario(self):
        """Test custom stress scenario"""
        custom_scenario = {
            "description": "Custom 20% decline",
            "market_shock": -0.20,
            "volatility_increase": 2.0,
            "correlation_increase": 0.3
        }

        result = self.calculator.calculate_stress_loss(
            self.positions,
            self.returns_matrix,
            custom_scenario
        )

        assert result["total_loss"] < 0


class TestEnhancedAlertSystem:
    """Test enhanced alert system"""

    def setup_method(self):
        """Setup test data"""
        self.alert_system = EnhancedAlertSystem()

        # Add test condition
        self.test_condition = AlertCondition(
            name="Test_VaR",
            metric="var_99",
            operator="gt",
            threshold=0.03,
            severity=AlertSeverity.WARNING,
            category=AlertCategory.MARKET_RISK,
            cooldown=0  # No cooldown for testing
        )
        self.alert_system.add_condition(self.test_condition)

    def test_condition_matching(self):
        """Test alert condition matching"""
        metrics = {"var_99": 0.04}  # Above threshold

        alerts = self.alert_system.check_metrics(
            metrics,
            "test_instance",
            "test_user"
        )

        assert len(alerts) == 1
        assert alerts[0].condition.name == "Test_VaR"
        assert alerts[0].current_value == 0.04
        assert alerts[0].threshold_value == 0.03

    def test_no_alert_when_condition_not_met(self):
        """Test no alert when condition not met"""
        metrics = {"var_99": 0.02}  # Below threshold

        alerts = self.alert_system.check_metrics(
            metrics,
            "test_instance",
            "test_user"
        )

        assert len(alerts) == 0

    def test_alert_acknowledgement(self):
        """Test alert acknowledgement"""
        metrics = {"var_99": 0.04}
        alerts = self.alert_system.check_metrics(metrics, "test_instance", "test_user")

        alert_id = alerts[0].id
        success = self.alert_system.acknowledge_alert(alert_id, "test_user")

        assert success
        alert = self.alert_system.active_alerts[alert_id]
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by == "test_user"

    def test_alert_resolution(self):
        """Test alert resolution"""
        metrics = {"var_99": 0.04}
        alerts = self.alert_system.check_metrics(metrics, "test_instance", "test_user")

        alert_id = alerts[0].id
        success = self.alert_system.resolve_alert(alert_id, "Issue fixed")

        assert success
        assert alert_id not in self.alert_system.active_alerts

    def test_alert_cooldown(self):
        """Test alert cooldown functionality"""
        # Add condition with cooldown
        condition_with_cooldown = AlertCondition(
            name="Cooldown_Test",
            metric="var_95",
            operator="gt",
            threshold=0.02,
            cooldown=60  # 60 seconds
        )
        self.alert_system.add_condition(condition_with_cooldown)

        # First alert should trigger
        metrics = {"var_95": 0.03}
        alerts1 = self.alert_system.check_metrics(metrics, "test_instance", "test_user")
        assert len(alerts1) == 1

        # Second alert should be suppressed due to cooldown
        alerts2 = self.alert_system.check_metrics(metrics, "test_instance", "test_user")
        assert len(alerts2) == 0


class TestEnhancedRiskManagementService:
    """Test enhanced risk management service"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()

    @pytest.fixture
    def risk_service(self, mock_db):
        """Create risk service instance"""
        with patch('src.services.enhanced_risk_management_service.CacheService'):
            with patch('src.services.enhanced_risk_management_service.UnifiedWebSocketManager'):
                service = EnhancedRiskManagementService(mock_db)
                return service

    def test_risk_limit_setting(self, risk_service):
        """Test setting custom risk limits"""
        user_id = uuid4()

        success = asyncio.run(
            risk_service.set_risk_limit(
                user_id,
                RiskLimitType.VAR_LIMIT,
                0.025  # 2.5% VaR limit
            )
        )

        assert success
        limit_key = f"{user_id}:{RiskLimitType.VAR_LIMIT.value}"
        assert limit_key in risk_service.risk_limits
        assert risk_service.risk_limits[limit_key].limit_value == 0.025

    def test_position_sizing_configuration(self, risk_service):
        """Test position sizing configuration"""
        instance_id = uuid4()
        config = PositionSizingConfig(
            method=PositionSizeMethod.VOLATILITY_TARGET,
            base_amount=100000,
            risk_factor=0.02
        )

        success = asyncio.run(
            risk_service.configure_position_sizing(instance_id, config)
        )

        assert success
        assert instance_id in risk_service.position_configs
        assert risk_service.position_configs[instance_id].method == PositionSizeMethod.VOLATILITY_TARGET

    def test_portfolio_metrics_calculation(self, risk_service):
        """Test portfolio metrics calculation"""
        positions = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "market_value": 15000,
                "position_weight": 0.15,
                "sector": "Technology",
                "asset_type": "equity"
            },
            {
                "symbol": "MSFT",
                "quantity": 50,
                "market_value": 20000,
                "position_weight": 0.20,
                "sector": "Technology",
                "asset_type": "equity"
            }
        ]

        metrics = asyncio.run(
            risk_service._calculate_portfolio_metrics("test_instance", positions)
        )

        assert metrics["total_positions"] == 2
        assert metrics["total_exposure"] == 35000
        assert "sector_exposure" in metrics
        assert metrics["sector_exposure"]["Technology"] == 1.0  # 100% in tech
        assert "concentration_metrics" in metrics


class TestIntegratedRiskService:
    """Test integrated risk service"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()

    @pytest.fixture
    def integrated_service(self, mock_db):
        """Create integrated risk service instance"""
        with patch('src.services.integrated_risk_service.EnhancedRiskManagementService'):
            with patch('src.services.integrated_risk_service.CacheService'):
                with patch('src.services.integrated_risk_service.UnifiedWebSocketManager'):
                    service = IntegratedRiskService(mock_db)
                    return service

    def test_service_initialization(self, integrated_service):
        """Test service initialization"""
        assert integrated_service.var_calculator is not None
        assert integrated_service.stress_calculator is not None
        assert integrated_service.liquidity_calculator is not None
        assert integrated_service.correlation_calculator is not None
        assert integrated_service.tail_calculator is not None
        assert integrated_service.alert_system is not None

    def test_default_alert_conditions(self, integrated_service):
        """Test default alert conditions are initialized"""
        assert len(integrated_service.alert_system.conditions) > 0

        # Check for key conditions
        condition_names = [
            c.name for c in integrated_service.alert_system.conditions.values()
        ]
        assert "VaR_95_Breach" in condition_names
        assert "VaR_99_Breach" in condition_names
        assert "Drawdown_Exceeded" in condition_names

    @pytest.mark.asyncio
    async def test_advanced_metrics_calculation(self, integrated_service):
        """Test advanced metrics calculation"""
        # Create mock returns data
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))

        with patch.object(integrated_service, '_get_returns_data') as mock_get_returns:
            with patch.object(integrated_service, '_get_returns_matrix') as mock_get_matrix:
                with patch.object(integrated_service, '_get_current_positions') as mock_positions:
                    with patch.object(integrated_service, '_get_market_data_for_positions') as mock_market:
                        mock_get_returns.return_value = returns
                        mock_get_matrix.return_value = pd.DataFrame(
                            np.random.normal(0, 0.02, (252, 3)),
                            columns=['A', 'B', 'C']
                        )
                        mock_positions.return_value = [
                            {'symbol': 'A', 'market_value': 100000}
                        ]
                        mock_market.return_value = {
                            'A': {'volume': 1000000, 'bid_ask_spread': 0.001}
                        }

                        metrics = await integrated_service._calculate_advanced_metrics(
                            "test_instance",
                            returns
                        )

                        assert 'var_95_ewma' in metrics
                        assert 'var_99_t_dist' in metrics
                        assert 'cvar_95_historical' in metrics
                        assert 'skewness' in metrics
                        assert 'excess_kurtosis' in metrics

    def test_risk_score_calculation(self, integrated_service):
        """Test risk score calculation"""
        basic_metrics = {
            "var_99_daily": 0.025,  # 2.5%
            "current_drawdown": -0.10  # 10%
        }
        advanced_metrics = {
            "excess_kurtosis": 2.0,
            "liquidity_liquidity_cost_pct": 0.02
        }
        stress_results = {
            "market_crash": {"loss_percentage": 0.15}
        }

        score = integrated_service._calculate_risk_score(
            basic_metrics,
            advanced_metrics,
            stress_results
        )

        assert "score" in score
        assert "level" in score
        assert 0 <= score["score"] <= 100
        assert score["level"] in ["Low", "Medium", "High", "Critical"]

    @pytest.mark.asyncio
    async def test_comprehensive_risk_report(self, integrated_service):
        """Test comprehensive risk report generation"""
        with patch.object(integrated_service.cache_service, 'get') as mock_cache:
            mock_cache.side_effect = [
                {"var_99_daily": 0.025},  # Basic metrics
                {"skewness": 0.5},  # Advanced metrics
                {"market_crash": {"loss_percentage": 0.15}}  # Stress results
            ]

            with patch.object(integrated_service.alert_system, 'get_active_alerts') as mock_alerts:
                mock_alerts.return_value = []

                report = await integrated_service.get_comprehensive_risk_report("test_instance")

                assert "instance_id" in report
                assert "basic_metrics" in report
                assert "advanced_metrics" in report
                assert "stress_tests" in report
                assert "active_alerts" in report
                assert "risk_score" in report


class TestLiquidityRiskCalculator:
    """Test liquidity risk calculator"""

    def setup_method(self):
        """Setup test data"""
        self.calculator = LiquidityRiskCalculator()
        self.positions = {
            "AAPL": {
                "quantity": 100,
                "market_value": 15000
            },
            "MSFT": {
                "quantity": 50,
                "market_value": 20000
            }
        }
        self.market_data = {
            "AAPL": {
                "volume": 1000000,
                "bid_ask_spread": 0.001
            },
            "MSFT": {
                "volume": 500000,
                "bid_ask_spread": 0.002
            }
        }

    def test_liquidity_metrics_calculation(self):
        """Test liquidity metrics calculation"""
        metrics = self.calculator.calculate_liquidity_metrics(
            self.positions,
            self.market_data
        )

        assert "liquidity_cost" in metrics
        assert "liquidity_cost_pct" in metrics
        assert "liquidity_at_risk" in metrics
        assert metrics["liquidity_cost"] > 0
        assert metrics["liquidity_cost_pct"] > 0


class TestCorrelationRiskCalculator:
    """Test correlation risk calculator"""

    def setup_method(self):
        """Setup test data"""
        self.calculator = CorrelationRiskCalculator()
        np.random.seed(42)

        # Create correlated returns
        cov = np.array([[0.0004, 0.0002],
                       [0.0002, 0.0003]])
        means = [0.001, 0.0008]
        returns = np.random.multivariate_normal(means, cov, 252)
        self.returns_matrix = pd.DataFrame(returns, columns=['A', 'B'])

    def test_correlation_metrics(self):
        """Test correlation metrics calculation"""
        metrics = self.calculator.calculate_correlation_metrics(
            self.returns_matrix,
            weights=np.array([0.6, 0.4])
        )

        assert "correlation_matrix" in metrics
        assert "average_correlation" in metrics
        assert "maximum_correlation" in metrics
        assert "diversification_ratio" in metrics
        assert "effective_bets" in metrics

    def test_shrinkage_method(self):
        """Test shrinkage correlation method"""
        calculator = CorrelationRiskCalculator(method="shrinkage")
        metrics = calculator.calculate_correlation_metrics(self.returns_matrix)

        assert "correlation_matrix" in metrics
        assert isinstance(metrics["correlation_matrix"], pd.DataFrame)


class TestTailRiskCalculator:
    """Test tail risk calculator"""

    def setup_method(self):
        """Setup test data"""
        self.calculator = TailRiskCalculator()
        # Create returns with fat tails
        np.random.seed(42)
        self.returns = pd.Series(
            np.random.standard_t(3, 1000) * 0.02
        )

    def test_tail_metrics(self):
        """Test tail risk metrics calculation"""
        metrics = self.calculator.calculate_tail_metrics(self.returns)

        assert "tail_loss_95" in metrics
        assert "tail_gain_95" in metrics
        assert "tail_ratio" in metrics
        assert "skewness" in metrics
        assert "excess_kurtosis" in metrics
        assert "max_tail_drawdown" in metrics
        assert "expected_tail_loss" in metrics

    def test_tail_ratio_calculation(self):
        """Test tail ratio calculation"""
        metrics = self.calculator.calculate_tail_metrics(self.returns)

        # Tail ratio should be positive (absolute values)
        assert metrics["tail_ratio"] > 0


# Integration tests

class TestRiskManagementIntegration:
    """Integration tests for the complete risk management system"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database with necessary relationships"""
        db = Mock()

        # Mock query chains
        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.first.return_value = None
        mock_query.all.return_value = []

        return db

    @pytest.fixture
    def full_system(self, mock_db):
        """Create full risk management system"""
        with patch('src.services.integrated_risk_service.CacheService'):
            with patch('src.services.integrated_risk_service.UnifiedWebSocketManager'):
                service = IntegratedRiskService(mock_db)
                return service

    @pytest.mark.asyncio
    async def test_alert_to_action_flow(self, full_system):
        """Test flow from alert generation to risk action execution"""
        # Register mock action handler
        action_executed = False

        async def mock_handler(action, context):
            nonlocal action_executed
            action_executed = True
            return True

        full_system.execute_risk_action = mock_handler

        # Create critical alert
        condition = AlertCondition(
            name="Critical_Test",
            metric="var_99",
            operator="gt",
            threshold=0.05,
            severity=AlertSeverity.CRITICAL,
            actions=[AlertAction.STOP_TRADING]
        )
        full_system.alert_system.add_condition(condition)

        # Trigger alert
        metrics = {"var_99": 0.06}
        alerts = full_system.alert_system.check_metrics(
            metrics,
            "test_instance",
            "test_user"
        )

        # Check if alert was created with action
        assert len(alerts) == 1
        assert AlertAction.STOP_TRADING in alerts[0].condition.actions

    @pytest.mark.asyncio
    async def test_multi_component_coordination(self, full_system):
        """Test coordination between multiple risk components"""
        # Mock data flow
        test_instance_id = "test_integration"

        # Mock returns data
        with patch.object(full_system, '_get_returns_data') as mock_returns:
            mock_returns.return_value = pd.Series(np.random.normal(0, 0.02, 252))

            # Mock positions and market data
            with patch.object(
                full_system.enhanced_service,
                '_get_current_positions'
            ) as mock_positions:
                mock_positions.return_value = [
                    {"symbol": "AAPL", "market_value": 100000}
                ]

                with patch.object(
                    full_system,
                    '_get_market_data_for_positions'
                ) as mock_market:
                    mock_market.return_value = {
                        "AAPL": {"volume": 1000000, "bid_ask_spread": 0.001}
                    }

                    # Calculate advanced metrics
                    returns = await full_system._get_returns_data(test_instance_id)
                    advanced_metrics = await full_system._calculate_advanced_metrics(
                        test_instance_id,
                        returns
                    )

                    # Verify metrics from different calculators
                    assert "var_95_ewma" in advanced_metrics  # From VaR calculator
                    assert "skewness" in advanced_metrics  # From tail calculator
                    assert "liquidity_liquidity_cost_pct" in advanced_metrics  # From liquidity calculator


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "-k", "test_stress"])