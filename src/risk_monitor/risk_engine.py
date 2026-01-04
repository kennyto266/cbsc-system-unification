"""
Risk Engine - Main Orchestrator

This module implements the main risk monitoring engine that coordinates
all risk calculations, alerts, and real-time monitoring functionalities.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from .config import RiskConfig
from .risk_calculators import (
    VaRCalculator,
    ExpectedShortfallCalculator,
    MaxDrawdownCalculator,
    VolatilityCalculator,
    CorrelationAnalyzer
)
from .alert_system import AlertSystem, AlertLevel, AlertType
from .websocket_handler import RiskWebSocketHandler
from .influxdb_connector import InfluxDBConnector
from .dynamic_adjustment import (
    DynamicRiskAdjuster,
    VolatilityTargeter,
    DynamicRebalancer,
    DynamicStopLoss
)

logger = logging.getLogger(__name__)


class RiskEngine:
    """Main risk monitoring engine"""

    def __init__(self, config: RiskConfig):
        """
        Initialize risk engine

        Args:
            config: Risk configuration
        """
        self.config = config
        self.running = False

        # Initialize components
        self._initialize_calculators()
        self._initialize_alert_system()
        self._initialize_dynamic_adjustment()
        self._initialize_influxdb()
        self._initialize_websocket()

        # Thread pool for parallel calculations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Portfolio and asset tracking
        self.portfolios: Dict[str, Dict] = {}
        self.asset_prices: Dict[str, pd.Series] = {}
        self.risk_cache: Dict[str, Dict] = {}
        self.last_update_times: Dict[str, datetime] = {}

        # Performance metrics
        self.calculation_times = []
        self.last_calculation_time = None

        # Lock for thread safety
        self._lock = threading.Lock()

    def _initialize_calculators(self):
        """Initialize risk calculators"""
        self.var_calculator = VaRCalculator(
            confidence_levels=self.config.var_confidence_levels
        )
        self.es_calculator = ExpectedShortfallCalculator(
            confidence_levels=self.config.es_confidence_levels
        )
        self.drawdown_calculator = MaxDrawdownCalculator(
            window=self.config.max_drawdown_window
        )
        self.volatility_calculator = VolatilityCalculator()
        self.correlation_analyzer = CorrelationAnalyzer()

    def _initialize_alert_system(self):
        """Initialize alert system"""
        self.alert_system = AlertSystem()

        # Register alert handler for WebSocket broadcasting
        if self.config.alert_enabled:
            self.alert_system.add_alert_handler(self._handle_alert_broadcast)

    def _initialize_dynamic_adjustment(self):
        """Initialize dynamic risk adjustment"""
        if self.config.dynamic_adjustment_enabled:
            self.volatility_targeter = VolatilityTargeter(
                target_volatility=self.config.volatility_target
            )
            self.rebalancer = DynamicRebalancer(
                rebalance_threshold=self.config.rebalance_threshold
            )
            self.stop_loss = DynamicStopLoss()

            self.dynamic_adjuster = DynamicRiskAdjuster(
                volatility_targeter=self.volatility_targeter,
                rebalancer=self.rebalancer,
                stop_loss=self.stop_loss,
                config={
                    "max_portfolio_volatility": 0.25,
                    "max_single_position": 0.30,
                    "emergency_exit_threshold": 0.15
                }
            )

    def _initialize_influxdb(self):
        """Initialize InfluxDB connector"""
        try:
            self.influxdb = InfluxDBConnector(
                host=self.config.influxdb_host,
                port=self.config.influxdb_port,
                database=self.config.influxdb_database,
                username=self.config.influxdb_username,
                password=self.config.influxdb_password
            )
            logger.info("InfluxDB connector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB: {e}")
            self.influxdb = None

    def _initialize_websocket(self):
        """Initialize WebSocket handler"""
        try:
            self.websocket_handler = RiskWebSocketHandler(
                host=self.config.websocket_host,
                port=self.config.websocket_port,
                max_connections=self.config.websocket_max_connections
            )
            logger.info("WebSocket handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket: {e}")
            self.websocket_handler = None

    async def start(self):
        """Start the risk engine"""
        if self.running:
            logger.warning("Risk engine is already running")
            return

        self.running = True

        # Start WebSocket server if enabled
        if self.websocket_handler:
            await self.websocket_handler.start_server()

        # Start main monitoring loop
        monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Risk engine started")
        return monitor_task

    async def stop(self):
        """Stop the risk engine"""
        if not self.running:
            return

        self.running = False

        # Stop WebSocket server
        if self.websocket_handler:
            await self.websocket_handler.stop_server()

        # Close InfluxDB connection
        if self.influxdb:
            self.influxdb.close()

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        logger.info("Risk engine stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                start_time = time.time()

                # Process all portfolios
                for portfolio_id in list(self.portfolios.keys()):
                    await self._process_portfolio(portfolio_id)

                # Record calculation time
                calc_time = time.time() - start_time
                self.calculation_times.append(calc_time)
                self.last_calculation_time = calc_time

                # Keep only recent calculation times
                if len(self.calculation_times) > 100:
                    self.calculation_times = self.calculation_times[-100:]

                # Sleep until next calculation
                await asyncio.sleep(self.config.calculation_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _process_portfolio(self, portfolio_id: str):
        """Process a single portfolio"""
        try:
            portfolio = self.portfolios[portfolio_id]
            last_update = self.last_update_times.get(portfolio_id)

            # Skip if updated recently (to avoid excessive calculations)
            if last_update and (datetime.now() - last_update).seconds < self.config.calculation_interval:
                return

            # Fetch portfolio data from InfluxDB
            portfolio_data = await self._fetch_portfolio_data(portfolio_id)
            if portfolio_data.empty:
                return

            # Calculate risk metrics
            risk_metrics = await self._calculate_risk_metrics(
                portfolio_id,
                portfolio_data
            )

            # Store in cache
            self.risk_cache[portfolio_id] = risk_metrics
            self.last_update_times[portfolio_id] = datetime.now()

            # Check alerts
            await self._check_alerts(portfolio_id, risk_metrics)

            # Generate dynamic adjustments if enabled
            if self.config.dynamic_adjustment_enabled:
                adjustments = self._generate_adjustments(
                    portfolio_id,
                    portfolio_data,
                    risk_metrics
                )
                if adjustments:
                    await self._handle_adjustments(portfolio_id, adjustments)

            # Store metrics in InfluxDB
            if self.influxdb:
                self.influxdb.write_risk_metrics(
                    portfolio_id=portfolio_id,
                    timestamp=datetime.now(),
                    metrics=risk_metrics
                )

            # Broadcast updates via WebSocket
            if self.websocket_handler:
                await self.websocket_handler.broadcast_risk_update(
                    portfolio_id=portfolio_id,
                    risk_data=risk_metrics
                )

        except Exception as e:
            logger.error(f"Error processing portfolio {portfolio_id}: {e}")

    async def _fetch_portfolio_data(self, portfolio_id: str) -> pd.DataFrame:
        """Fetch portfolio data from InfluxDB"""
        if not self.influxdb:
            return pd.DataFrame()

        try:
            # Fetch recent data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)

            data = self.influxdb.query_portfolio_data(
                portfolio_id=portfolio_id,
                start_time=start_time,
                end_time=end_time
            )

            return data
        except Exception as e:
            logger.error(f"Error fetching portfolio data: {e}")
            return pd.DataFrame()

    async def _calculate_risk_metrics(
        self,
        portfolio_id: str,
        portfolio_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate comprehensive risk metrics"""
        if portfolio_data.empty:
            return {}

        # Extract returns series
        returns = portfolio_data.get('returns', pd.Series())
        if returns.empty:
            # Calculate returns from total_value if available
            if 'total_value' in portfolio_data:
                returns = portfolio_data['total_value'].pct_change().dropna()

        if returns.empty or len(returns) < 20:
            logger.warning(f"Insufficient data for portfolio {portfolio_id}")
            return {}

        metrics = {}

        # Calculate VaR
        for confidence in self.config.var_confidence_levels:
            var_historical = self.var_calculator.calculate_historical_var(
                returns, confidence
            )
            var_parametric = self.var_calculator.calculate_parametric_var(
                returns, confidence
            )
            metrics[f"var_{confidence}_historical"] = var_historical
            metrics[f"var_{confidence}_parametric"] = var_parametric

        # Calculate Expected Shortfall
        for confidence in self.config.es_confidence_levels:
            es_historical = self.es_calculator.calculate_historical_es(
                returns, confidence
            )
            es_parametric = self.es_calculator.calculate_parametric_es(
                returns, confidence
            )
            metrics[f"es_{confidence}_historical"] = es_historical
            metrics[f"es_{confidence}_parametric"] = es_parametric

        # Calculate volatility
        for window in self.config.volatility_windows:
            vol = self.volatility_calculator.calculate_returns_volatility(
                returns, window=window
            )
            metrics[f"volatility_{window}d"] = vol

        # Calculate maximum drawdown
        if 'total_value' in portfolio_data:
            prices = portfolio_data['total_value']
            drawdown_metrics = self.drawdown_calculator.calculate_max_drawdown(prices)
            metrics.update({
                "max_drawdown": drawdown_metrics["max_drawdown"],
                "current_drawdown": drawdown_metrics["current_drawdown"],
                "drawdown_duration": drawdown_metrics["max_drawdown_duration"]
            })

        # Calculate Sharpe ratio (if enough data)
        if len(returns) > 60:
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            metrics["sharpe_ratio"] = sharpe_ratio

        # Calculate beta if market data available
        if "market_returns" in portfolio_data:
            beta = self._calculate_beta(returns, portfolio_data["market_returns"])
            metrics["beta"] = beta

        return metrics

    def _calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - risk_free_rate / 252
        if len(excess_returns) == 0 or excess_returns.std() == 0:
            return 0

        sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        return sharpe

    def _calculate_beta(
        self,
        asset_returns: pd.Series,
        market_returns: pd.Series
    ) -> float:
        """Calculate beta relative to market"""
        # Align series
        aligned_data = pd.concat([asset_returns, market_returns], axis=1).dropna()
        if len(aligned_data) < 30:
            return 1.0  # Default beta

        covariance = aligned_data.iloc[:, 0].cov(aligned_data.iloc[:, 1])
        market_variance = aligned_data.iloc[:, 1].var()

        if market_variance == 0:
            return 1.0

        beta = covariance / market_variance
        return beta

    async def _check_alerts(self, portfolio_id: str, risk_metrics: Dict[str, float]):
        """Check risk metrics against alert thresholds"""
        # Convert metrics to percentages for alerts
        alert_metrics = {}
        for key, value in risk_metrics.items():
            if key in ["var_95_historical", "var_95_parametric", "var_99_historical", "var_99_parametric"]:
                alert_metrics["var_95"] = max(
                    risk_metrics.get("var_95_historical", 0),
                    risk_metrics.get("var_95_parametric", 0)
                )
                alert_metrics["var_99"] = max(
                    risk_metrics.get("var_99_historical", 0),
                    risk_metrics.get("var_99_parametric", 0)
                )
            elif key == "max_drawdown" or key == "current_drawdown":
                alert_metrics["max_drawdown"] = value
            elif key.startswith("volatility_"):
                alert_metrics["volatility"] = value

        # Generate alerts
        alerts = self.alert_system.check_metrics(
            metrics=alert_metrics,
            portfolio_id=portfolio_id
        )

        # Handle new alerts
        for alert in alerts:
            logger.warning(
                f"Alert generated for portfolio {portfolio_id}: "
                f"{alert.level.value} - {alert.message}"
            )

    async def _handle_alert_broadcast(self, alert):
        """Handle alert broadcasting via WebSocket"""
        if self.websocket_handler:
            await self.websocket_handler.broadcast_alert(alert.to_dict())

    def _generate_adjustments(
        self,
        portfolio_id: str,
        portfolio_data: pd.DataFrame,
        risk_metrics: Dict[str, float]
    ) -> List:
        """Generate dynamic adjustment signals"""
        if not hasattr(self, 'dynamic_adjuster'):
            return []

        # Get current positions (this would come from portfolio management system)
        current_positions = self.portfolios.get(portfolio_id, {}).get("positions", {})
        current_prices = {}  # Would be fetched from market data

        # Generate adjustment signals
        portfolio_df = portfolio_data  # Convert to required format
        adjustments = self.dynamic_adjuster.generate_adjustment_signals(
            portfolio_data={"portfolio": portfolio_df},
            current_positions=current_positions,
            current_prices=current_prices
        )

        return adjustments

    async def _handle_adjustments(self, portfolio_id: str, adjustments: List):
        """Handle dynamic adjustment signals"""
        for adjustment in adjustments:
            logger.info(
                f"Adjustment for portfolio {portfolio_id}: "
                f"{adjustment.signal.value} - {adjustment.reason}"
            )

            # Here you would integrate with the execution system
            # to actually implement the adjustments

    def add_portfolio(
        self,
        portfolio_id: str,
        portfolio_info: Dict[str, Any]
    ):
        """Add a portfolio for monitoring"""
        with self._lock:
            self.portfolios[portfolio_id] = portfolio_info
            logger.info(f"Added portfolio {portfolio_id} for monitoring")

    def remove_portfolio(self, portfolio_id: str):
        """Remove a portfolio from monitoring"""
        with self._lock:
            self.portfolios.pop(portfolio_id, None)
            self.risk_cache.pop(portfolio_id, None)
            self.last_update_times.pop(portfolio_id, None)
            logger.info(f"Removed portfolio {portfolio_id} from monitoring")

    def get_portfolio_risk_metrics(self, portfolio_id: str) -> Optional[Dict[str, float]]:
        """Get latest risk metrics for a portfolio"""
        return self.risk_cache.get(portfolio_id)

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get overall risk monitoring summary"""
        summary = {
            "monitored_portfolios": len(self.portfolios),
            "active_alerts": len(self.alert_system.get_active_alerts()),
            "calculation_interval": self.config.calculation_interval,
            "last_calculation_time": self.last_calculation_time,
            "average_calculation_time": np.mean(self.calculation_times) if self.calculation_times else 0
        }

        # Add WebSocket stats if available
        if self.websocket_handler:
            summary["websocket"] = self.websocket_handler.get_client_stats()

        return summary

    async def run_risk_calculation(
        self,
        portfolio_id: str,
        force_refresh: bool = False
    ) -> Dict[str, float]:
        """Run immediate risk calculation for a portfolio"""
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        # Force refresh if requested
        if force_refresh:
            self.last_update_times.pop(portfolio_id, None)

        # Fetch data and calculate
        portfolio_data = await self._fetch_portfolio_data(portfolio_id)
        risk_metrics = await self._calculate_risk_metrics(
            portfolio_id,
            portfolio_data
        )

        # Update cache
        self.risk_cache[portfolio_id] = risk_metrics
        self.last_update_times[portfolio_id] = datetime.now()

        return risk_metrics

    def configure_alert_thresholds(self, thresholds: Dict[str, Dict[str, float]]):
        """Configure custom alert thresholds"""
        from .alert_system import AlertThreshold, AlertType

        for name, config in thresholds.items():
            alert_threshold = AlertThreshold(
                name=name,
                metric_type=AlertType(config.get("type", "system_error")),
                warning_threshold=config.get("warning"),
                error_threshold=config.get("error"),
                critical_threshold=config.get("critical"),
                comparison_operator=config.get("operator", "greater_than"),
                cooldown_period=config.get("cooldown", 60),
                enabled=config.get("enabled", True)
            )
            self.alert_system.add_threshold(alert_threshold)

    def export_risk_report(
        self,
        portfolio_id: str,
        format: str = "json",
        hours: int = 24
    ) -> str:
        """Export risk report for a portfolio"""
        # Get historical risk metrics from InfluxDB
        if not self.influxdb:
            raise RuntimeError("InfluxDB not configured")

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        risk_data = self.influxdb.query_risk_metrics(
            portfolio_id=portfolio_id,
            start_time=start_time,
            end_time=end_time
        )

        if format == "json":
            report = {
                "portfolio_id": portfolio_id,
                "report_period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "hours": hours
                },
                "current_metrics": self.risk_cache.get(portfolio_id, {}),
                "historical_data": risk_data.to_dict() if not risk_data.empty else {},
                "alerts": [a.to_dict() for a in self.alert_system.get_alert_history(hours=hours)]
            }
            return json.dumps(report, indent=2)
        else:
            # Export as CSV
            if not risk_data.empty:
                return risk_data.to_csv()
            else:
                return "No data available"