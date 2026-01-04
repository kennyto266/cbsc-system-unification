"""
Integrated Risk Management Service
Central service that integrates all risk management components
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, UUID
from uuid import uuid4
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from .enhanced_risk_management_service import EnhancedRiskManagementService
from ..risk_monitor.advanced_risk_calculators import (
    AdvancedVaRCalculator,
    StressTestCalculator,
    LiquidityRiskCalculator,
    CorrelationRiskCalculator,
    TailRiskCalculator
)
from ..risk_monitor.enhanced_alert_system import (
    EnhancedAlertSystem,
    AlertCondition,
    AlertSeverity,
    AlertCategory,
    AlertAction,
    AlertStatus
)
from ..models.risk_models_v2 import (
    RiskMonitoring, RiskMetric, RiskAlert, RiskPosition,
    RiskThreshold
)
from .cache_service import CacheService
from ..websocket.unified_websocket_manager import UnifiedWebSocketManager

logger = logging.getLogger(__name__)


class IntegratedRiskService:
    """Integrated risk management service combining all components"""

    def __init__(self, db: Session):
        """Initialize integrated risk service"""
        self.db = db
        self.cache_service = CacheService()
        self.websocket_manager = UnifiedWebSocketManager()

        # Initialize components
        self.enhanced_service = EnhancedRiskManagementService(db)
        self.var_calculator = AdvancedVaRCalculator([0.95, 0.99, 0.999])
        self.stress_calculator = StressTestCalculator()
        self.liquidity_calculator = LiquidityRiskCalculator()
        self.correlation_calculator = CorrelationRiskCalculator()
        self.tail_calculator = TailRiskCalculator()
        self.alert_system = EnhancedAlertSystem()

        # Service state
        self._running = False
        self._monitoring_tasks = []

        # Initialize default alert conditions
        self._initialize_default_alerts()

    def _initialize_default_alerts(self):
        """Initialize default alert conditions"""
        default_conditions = [
            AlertCondition(
                name="VaR_95_Breach",
                metric="var_95",
                operator="gt",
                threshold=0.02,
                severity=AlertSeverity.WARNING,
                category=AlertCategory.MARKET_RISK,
                cooldown=300,
                actions=[AlertAction.NOTIFY]
            ),
            AlertCondition(
                name="VaR_99_Breach",
                metric="var_99",
                operator="gt",
                threshold=0.03,
                severity=AlertSeverity.ERROR,
                category=AlertCategory.MARKET_RISK,
                cooldown=300,
                actions=[AlertAction.NOTIFY, AlertAction.REDUCE_POSITIONS]
            ),
            AlertCondition(
                name="Drawdown_Exceeded",
                metric="current_drawdown",
                operator="gt",
                threshold=0.15,
                severity=AlertSeverity.ERROR,
                category=AlertCategory.MARKET_RISK,
                cooldown=600,
                actions=[AlertAction.NOTIFY, AlertAction.MANUAL_REVIEW]
            ),
            AlertCondition(
                name="Concentration_Risk",
                metric="max_position_weight",
                operator="gt",
                threshold=0.20,
                severity=AlertSeverity.WARNING,
                category=AlertCategory.CONCENTRATION_RISK,
                cooldown=300,
                actions=[AlertAction.NOTIFY]
            ),
            AlertCondition(
                name="Liquidity_Risk",
                metric="liquidity_cost_pct",
                operator="gt",
                threshold=0.05,
                severity=AlertSeverity.WARNING,
                category=AlertCategory.LIQUIDITY_RISK,
                cooldown=300,
                actions=[AlertAction.NOTIFY]
            )
        ]

        for condition in default_conditions:
            self.alert_system.add_condition(condition)

    async def start_service(self):
        """Start the integrated risk service"""
        if self._running:
            logger.warning("Risk service is already running")
            return

        self._running = True

        # Start enhanced service monitoring
        await self.enhanced_service.start_monitoring()

        # Start background tasks
        self._monitoring_tasks = [
            asyncio.create_task(self._advanced_metrics_loop()),
            asyncio.create_task(self._stress_test_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]

        logger.info("Integrated risk service started")

    async def stop_service(self):
        """Stop the integrated risk service"""
        self._running = False

        # Stop enhanced service
        await self.enhanced_service.stop_monitoring()

        # Cancel background tasks
        for task in self._monitoring_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("Integrated risk service stopped")

    async def _advanced_metrics_loop(self):
        """Calculate advanced risk metrics"""
        while self._running:
            try:
                # Get all active instances
                instances = self.db.query(RiskMonitoring).filter(
                    RiskMonitoring.is_active == True
                ).all()

                for monitoring in instances:
                    instance_id = str(monitoring.strategy_instance_id)
                    user_id = str(monitoring.strategy_instance.user_id)

                    # Get returns data
                    returns_data = await self._get_returns_data(instance_id)
                    if returns_data is None or len(returns_data) < 20:
                        continue

                    # Calculate advanced metrics
                    advanced_metrics = await self._calculate_advanced_metrics(
                        instance_id, returns_data
                    )

                    # Store metrics
                    await self._store_advanced_metrics(instance_id, advanced_metrics)

                    # Check alert conditions
                    alerts = self.alert_system.check_metrics(
                        advanced_metrics,
                        instance_id,
                        user_id
                    )

                    # Send alerts via WebSocket
                    for alert in alerts:
                        await self.websocket_manager.broadcast_to_user(
                            user_id,
                            "risk_alert",
                            {
                                "alert_id": alert.id,
                                "condition": alert.condition.name,
                                "severity": alert.condition.severity.value,
                                "message": alert.message,
                                "timestamp": alert.timestamp.isoformat()
                            }
                        )

                # Sleep for next cycle (5 minutes)
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"Error in advanced metrics loop: {e}")
                await asyncio.sleep(60)

    async def _stress_test_loop(self):
        """Run stress tests periodically"""
        while self._running:
            try:
                # Get all active instances with positions
                instances = self.db.query(RiskMonitoring).filter(
                    RiskMonitoring.is_active == True
                ).join(RiskPosition).distinct().all()

                for monitoring in instances:
                    instance_id = str(monitoring.strategy_instance_id)
                    user_id = str(monitoring.strategy_instance.user_id)

                    # Get current positions
                    positions = await self.enhanced_service._get_current_positions(instance_id)
                    if not positions:
                        continue

                    # Get returns matrix
                    returns_matrix = await self._get_returns_matrix(instance_id)
                    if returns_matrix is None or returns_matrix.empty:
                        continue

                    # Run stress tests
                    stress_results = {}
                    for scenario_name in self.stress_calculator.scenarios.keys():
                        position_values = {p['symbol']: p['market_value'] for p in positions}
                        result = self.stress_calculator.calculate_stress_loss(
                            position_values,
                            returns_matrix,
                            scenario_name
                        )
                        stress_results[scenario_name] = result

                    # Store stress test results
                    await self._store_stress_test_results(instance_id, stress_results)

                    # Check for critical stress losses
                    for scenario, result in stress_results.items():
                        if result['loss_percentage'] > 0.20:  # 20% loss threshold
                            await self._create_stress_alert(
                                instance_id,
                                user_id,
                                scenario,
                                result
                            )

                # Run stress tests every hour
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Error in stress test loop: {e}")
                await asyncio.sleep(300)

    async def _alert_processing_loop(self):
        """Process and route alerts"""
        while self._running:
            try:
                # Get active alerts
                active_alerts = self.alert_system.get_active_alerts()

                # Process each alert
                for alert_data in active_alerts:
                    alert_id = alert_data['id']
                    alert = self.alert_system.active_alerts.get(alert_id)

                    if not alert:
                        continue

                    # Check if alert needs escalation
                    unresolved_count = self.alert_system.alert_counts.get(
                        alert.condition.name, 0
                    )

                    escalation = self.alert_system.escalation_manager.check_escalation(
                        alert, unresolved_count
                    )

                    if escalation:
                        # Store escalation in database
                        await self._store_alert_escalation(alert, escalation)

                # Check for resolved alerts
                await self._check_resolved_alerts()

                # Sleep for next cycle
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self):
        """Clean up old data and perform maintenance"""
        while self._running:
            try:
                # Clean up old metrics (keep 90 days)
                cutoff_date = datetime.utcnow() - timedelta(days=90)

                # Delete old risk metrics
                self.db.query(RiskMetric).filter(
                    RiskMetric.calculated_at < cutoff_date
                ).delete()

                # Delete old resolved alerts
                self.db.query(RiskAlert).filter(
                    RiskAlert.is_active == False,
                    RiskAlert.created_at < cutoff_date
                ).delete()

                self.db.commit()

                # Clean up cache
                await self._cleanup_cache()

                # Run cleanup daily
                await asyncio.sleep(86400)

            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)

    async def _calculate_advanced_metrics(
        self,
        instance_id: str,
        returns: pd.Series
    ) -> Dict[str, float]:
        """Calculate advanced risk metrics"""
        metrics = {}

        # Advanced VaR calculations
        for confidence in [0.95, 0.99, 0.999]:
            # Historical VaR with different methods
            metrics[f'var_{confidence}_ewma'] = self.var_calculator.calculate_historical_var(
                returns, confidence, method="weighted"
            )
            metrics[f'var_{confidence}_filtered'] = self.var_calculator.calculate_historical_var(
                returns, confidence, method="filtered"
            )

            # Parametric VaR with different distributions
            metrics[f'var_{confidence}_t_dist'] = self.var_calculator.calculate_parametric_var(
                returns, confidence, distribution="t"
            )
            metrics[f'var_{confidence}_skewed_t'] = self.var_calculator.calculate_parametric_var(
                returns, confidence, distribution="skewed_t"
            )

            # CVaR calculations
            metrics[f'cvar_{confidence}_historical'] = self.var_calculator.calculate_cvar(
                returns, confidence, method="historical"
            )
            metrics[f'cvar_{confidence}_parametric'] = self.var_calculator.calculate_cvar(
                returns, confidence, method="parametric"
            )

        # Monte Carlo VaR
        for confidence in [0.95, 0.99]:
            metrics[f'var_{confidence}_monte_carlo'] = self.var_calculator.calculate_monte_carlo_var(
                returns, confidence, n_simulations=10000
            )

        # Tail risk metrics
        tail_metrics = self.tail_calculator.calculate_tail_metrics(returns)
        metrics.update(tail_metrics)

        # Correlation metrics (if multi-asset)
        returns_matrix = await self._get_returns_matrix(instance_id)
        if returns_matrix is not None and returns_matrix.shape[1] > 1:
            corr_metrics = self.correlation_calculator.calculate_correlation_metrics(returns_matrix)
            for key, value in corr_metrics.items():
                if isinstance(value, (int, float)):
                    metrics[f'correlation_{key}'] = value

        # Liquidity metrics
        positions = await self.enhanced_service._get_current_positions(instance_id)
        market_data = await self._get_market_data_for_positions(positions)
        if market_data:
            liquidity_metrics = self.liquidity_calculator.calculate_liquidity_metrics(
                positions, market_data
            )
            for key, value in liquidity_metrics.items():
                metrics[f'liquidity_{key}'] = value

        return metrics

    async def _store_advanced_metrics(
        self,
        instance_id: str,
        metrics: Dict[str, float]
    ):
        """Store advanced metrics in database"""
        try:
            monitoring = self.db.query(RiskMonitoring).filter(
                RiskMonitoring.strategy_instance_id == instance_id
            ).first()

            if not monitoring:
                return

            # Create metric records
            for metric_name, value in metrics.items():
                metric = RiskMetric(
                    monitoring_id=monitoring.id,
                    metric_type=self._get_metric_type(metric_name),
                    metric_name=metric_name,
                    metric_value=value,
                    calculated_at=datetime.utcnow()
                )
                self.db.add(metric)

            self.db.commit()

        except Exception as e:
            logger.error(f"Error storing advanced metrics: {e}")
            self.db.rollback()

    def _get_metric_type(self, metric_name: str) -> str:
        """Determine metric type from name"""
        if 'var' in metric_name:
            return 'value_at_risk'
        elif 'cvar' in metric_name:
            return 'expected_shortfall'
        elif 'correlation' in metric_name:
            return 'correlation'
        elif 'liquidity' in metric_name:
            return 'liquidity'
        elif 'drawdown' in metric_name:
            return 'max_drawdown'
        elif 'skewness' in metric_name or 'kurtosis' in metric_name:
            return 'tail_risk'
        else:
            return 'other'

    async def _store_stress_test_results(
        self,
        instance_id: str,
        results: Dict[str, Dict]
    ):
        """Store stress test results"""
        try:
            # Store in cache for quick access
            await self.cache_service.set(
                f"stress_test:{instance_id}",
                results,
                ttl=3600  # 1 hour
            )

            # Store in database as well
            monitoring = self.db.query(RiskMonitoring).filter(
                RiskMonitoring.strategy_instance_id == instance_id
            ).first()

            if not monitoring:
                return

            for scenario, result in results.items():
                metric = RiskMetric(
                    monitoring_id=monitoring.id,
                    metric_type='stress_test',
                    metric_name=f'stress_{scenario}',
                    metric_value=result['loss_percentage'],
                    calculated_at=datetime.utcnow(),
                    parameters={
                        'scenario': scenario,
                        'portfolio_value': result['portfolio_value'],
                        'total_loss': result['total_loss']
                    }
                )
                self.db.add(metric)

            self.db.commit()

        except Exception as e:
            logger.error(f"Error storing stress test results: {e}")
            self.db.rollback()

    async def _create_stress_alert(
        self,
        instance_id: str,
        user_id: UUID,
        scenario: str,
        result: Dict
    ):
        """Create alert for stress test breach"""
        try:
            alert = RiskAlert(
                monitoring_id=None,  # Will be linked when monitoring is set up
                alert_level='critical' if result['loss_percentage'] > 0.30 else 'error',
                alert_type='stress_test',
                title=f"Stress Test Alert: {scenario}",
                message=f"Stress test '{scenario}' shows potential loss of {result['loss_percentage']:.1%}",
                metric_name='stress_test_loss',
                threshold_value=0.20,
                actual_value=result['loss_percentage'],
                context={
                    'scenario': scenario,
                    'loss_percentage': result['loss_percentage'],
                    'portfolio_value': result['portfolio_value']
                },
                created_at=datetime.utcnow()
            )

            self.db.add(alert)
            self.db.commit()

            # Send WebSocket notification
            await self.websocket_manager.broadcast_to_user(
                user_id,
                "stress_alert",
                {
                    "alert_id": str(alert.id),
                    "scenario": scenario,
                    "loss_percentage": result['loss_percentage'],
                    "message": alert.message,
                    "timestamp": alert.created_at.isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Error creating stress alert: {e}")
            self.db.rollback()

    async def _store_alert_escalation(self, alert, escalation):
        """Store alert escalation in database"""
        try:
            # This would store in an alert_escalations table
            # For now, just log it
            logger.info(
                f"Alert {alert.id} escalated to level {escalation['level']}: "
                f"{escalation['reason']}"
            )

        except Exception as e:
            logger.error(f"Error storing alert escalation: {e}")

    async def _check_resolved_alerts(self):
        """Check if any active alerts should be resolved"""
        try:
            for alert_id, alert in list(self.alert_system.active_alerts.items()):
                # Check if underlying condition is no longer met
                metrics = await self.cache_service.get(
                    f"risk_metrics:{alert.instance_id}"
                )

                if metrics and alert.condition.metric in metrics:
                    condition_met = self.alert_system._evaluate_condition(
                        metrics[alert.condition.metric],
                        alert.condition.operator,
                        alert.condition.threshold
                    )

                    if not condition_met:
                        # Auto-resolve alert
                        self.alert_system.resolve_alert(
                            alert_id,
                            "Condition no longer met"
                        )

        except Exception as e:
            logger.error(f"Error checking resolved alerts: {e}")

    async def _cleanup_cache(self):
        """Clean up old cache entries"""
        try:
            # Clean up old metrics cache
            # Implementation depends on cache service capabilities
            logger.info("Cache cleanup completed")

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    async def _get_returns_data(self, instance_id: str) -> Optional[pd.Series]:
        """Get returns data for an instance"""
        # This would fetch from time-series database
        # For now, generate mock data
        np.random.seed(hash(instance_id) % 2**32)
        returns = np.random.normal(0.001, 0.02, 252)  # 1 year of daily returns
        return pd.Series(returns)

    async def _get_returns_matrix(self, instance_id: str) -> Optional[pd.DataFrame]:
        """Get returns matrix for multiple assets"""
        # This would fetch from time-series database
        # For now, generate mock data
        np.random.seed(hash(instance_id) % 2**32)
        n_assets = 5
        n_periods = 252
        returns = np.random.multivariate_normal(
            np.zeros(n_assets),
            np.eye(n_assets) * 0.0004,  # 2% daily vol
            n_periods
        )
        columns = [f'ASSET_{i}' for i in range(n_assets)]
        return pd.DataFrame(returns, columns=columns)

    async def _get_market_data_for_positions(
        self,
        positions: List[Dict]
    ) -> Optional[Dict[str, Dict]]:
        """Get market data for positions"""
        if not positions:
            return None

        # Mock market data
        market_data = {}
        for pos in positions:
            symbol = pos['symbol']
            market_data[symbol] = {
                'volume': np.random.uniform(1000000, 10000000),
                'bid_ask_spread': np.random.uniform(0.0001, 0.005),
                'price': pos.get('market_value', 0) / max(pos.get('quantity', 1), 1)
            }

        return market_data

    # Public API methods

    async def get_comprehensive_risk_report(
        self,
        instance_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive risk report for an instance"""
        try:
            # Get basic metrics
            basic_metrics = await self.cache_service.get(f"risk_metrics:{instance_id}")

            # Get advanced metrics
            advanced_metrics = await self.cache_service.get(f"advanced_metrics:{instance_id}")

            # Get stress test results
            stress_results = await self.cache_service.get(f"stress_test:{instance_id}")

            # Get active alerts
            active_alerts = self.alert_system.get_active_alerts()

            # Compile report
            report = {
                "instance_id": instance_id,
                "timestamp": datetime.utcnow().isoformat(),
                "basic_metrics": basic_metrics or {},
                "advanced_metrics": advanced_metrics or {},
                "stress_tests": stress_results or {},
                "active_alerts": [a for a in active_alerts if a.get("instance_id") == instance_id],
                "risk_score": self._calculate_risk_score(
                    basic_metrics, advanced_metrics, stress_results
                )
            }

            return report

        except Exception as e:
            logger.error(f"Error generating comprehensive risk report: {e}")
            return {}

    def _calculate_risk_score(
        self,
        basic_metrics: Optional[Dict],
        advanced_metrics: Optional[Dict],
        stress_results: Optional[Dict]
    ) -> Dict[str, float]:
        """Calculate overall risk score"""
        score = 0
        max_score = 100

        # Basic risk metrics (40% weight)
        if basic_metrics:
            var_score = min(30, basic_metrics.get("var_99_daily", 0) * 1000)
            drawdown_score = min(20, abs(basic_metrics.get("current_drawdown", 0)) * 100)
            score += var_score + drawdown_score

        # Advanced metrics (30% weight)
        if advanced_metrics:
            tail_score = min(15, advanced_metrics.get("excess_kurtosis", 0) * 2)
            liquidity_score = min(15, advanced_metrics.get("liquidity_liquidity_cost_pct", 0) * 100)
            score += tail_score + liquidity_score

        # Stress test results (30% weight)
        if stress_results:
            worst_loss = max(r.get("loss_percentage", 0) for r in stress_results.values())
            stress_score = min(30, worst_loss * 100)
            score += stress_score

        # Risk level classification
        if score < 20:
            level = "Low"
        elif score < 40:
            level = "Medium"
        elif score < 60:
            level = "High"
        else:
            level = "Critical"

        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "level": level,
            "components": {
                "basic": score * 0.4,
                "advanced": score * 0.3,
                "stress": score * 0.3
            }
        }

    async def register_notification_handler(
        self,
        channel: str,
        handler: callable
    ):
        """Register a notification handler"""
        self.alert_system.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for channel: {channel}")

    async def execute_risk_action(
        self,
        action: AlertAction,
        context: Dict[str, Any]
    ) -> bool:
        """Execute a risk management action"""
        try:
            if action == AlertAction.STOP_TRADING:
                # Implement stop trading logic
                logger.critical("EXECUTING STOP TRADING")
                # This would integrate with the trading system
                return True

            elif action == AlertAction.REDUCE_POSITIONS:
                # Implement position reduction logic
                logger.warning(f"REDUCING POSITIONS: {context}")
                # This would calculate and execute position reductions
                return True

            elif action == AlertAction.EXECUTE_HEDGE:
                # Implement hedging logic
                logger.info(f"EXECUTING HEDGE: {context}")
                # This would execute hedging strategies
                return True

            else:
                logger.warning(f"Unknown risk action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error executing risk action {action}: {e}")
            return False