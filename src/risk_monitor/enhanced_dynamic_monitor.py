"""
Enhanced Dynamic Risk Monitoring System

This module implements advanced dynamic risk monitoring with:
- Real-time Monte Carlo VaR calculation
- Automatic risk control mechanisms
- Dynamic threshold adjustment
- Risk report generation
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from collections import deque
import warnings

from .config import RiskConfig
from .risk_calculators import (
    VaRCalculator,
    ExpectedShortfallCalculator,
    MaxDrawdownCalculator,
    VolatilityCalculator,
    CorrelationAnalyzer
)
from .alert_system import AlertSystem, AlertLevel, AlertType
from ..backtest.monte_carlo import MonteCarloSimulator, MCSimulationConfig, MCResults

logger = logging.getLogger(__name__)


class RiskControlAction(Enum):
    """Risk control action types"""
    NO_ACTION = "no_action"
    REDUCE_EXPOSURE = "reduce_exposure"
    INCREASE_EXPOSURE = "increase_exposure"
    HEDGE_POSITION = "hedge_position"
    EMERGENCY_EXIT = "emergency_exit"
    DYNAMIC_HEDGING = "dynamic_hedging"
    PAUSE_TRADING = "pause_trading"
    REDUCE_LEVERAGE = "reduce_leverage"


@dataclass
class RiskControlSignal:
    """Risk control signal data structure"""
    action: RiskControlAction
    asset_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    current_exposure: Optional[float] = None
    target_exposure: Optional[float] = None
    adjustment_factor: Optional[float] = None
    reason: Optional[str] = None
    urgency: int = 1  # 1=low, 2=medium, 3=high, 4=urgent
    triggered_by: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RiskReport:
    """Risk report data structure"""
    portfolio_id: str
    report_date: datetime
    period_start: datetime
    period_end: datetime
    risk_metrics: Dict[str, Any]
    monte_carlo_results: Optional[Dict[str, Any]]
    alerts_summary: Dict[str, int]
    control_actions: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    recommendations: List[str]
    risk_attribution: Dict[str, float]


class DynamicThresholdManager:
    """Manages dynamic risk thresholds based on market conditions"""

    def __init__(self, base_thresholds: Dict[str, float], adjustment_factor: float = 0.1):
        """
        Initialize dynamic threshold manager

        Args:
            base_thresholds: Base risk thresholds
            adjustment_factor: Factor for dynamic adjustment (0.1 = 10%)
        """
        self.base_thresholds = base_thresholds
        self.adjustment_factor = adjustment_factor
        self.current_thresholds = base_thresholds.copy()
        self.threshold_history = deque(maxlen=100)
        self.last_adjustment = datetime.now()
        self.adjustment_frequency = timedelta(hours=1)

    def update_thresholds(
        self,
        market_volatility: float,
        market_correlation: float,
        market_stress_index: float
    ):
        """
        Update thresholds based on market conditions

        Args:
            market_volatility: Current market volatility
            market_correlation: Average market correlation
            market_stress_index: Market stress indicator (0-1)
        """
        # Check if enough time has passed since last adjustment
        if datetime.now() - self.last_adjustment < self.adjustment_frequency:
            return

        # Calculate adjustment factor based on market conditions
        volatility_adjustment = min(market_volatility / 0.20 - 1, 0.5)  # Cap at 50%
        correlation_adjustment = min(market_correlation - 0.5, 0.3)  # Cap at 30%
        stress_adjustment = market_stress_index * 0.5

        total_adjustment = (
            volatility_adjustment * 0.4 +
            correlation_adjustment * 0.3 +
            stress_adjustment * 0.3
        )

        # Apply adjustments to thresholds
        for metric, base_value in self.base_thresholds.items():
            # For risk metrics like VaR, drawdown - tighten thresholds in stress
            if metric in ['var_95', 'var_99', 'max_drawdown']:
                adjustment = 1 - (total_adjustment * self.adjustment_factor)
            # For volatility - also tighten in stress
            elif metric == 'volatility':
                adjustment = 1 - (total_adjustment * self.adjustment_factor)
            else:
                adjustment = 1.0

            self.current_thresholds[metric] = base_value * adjustment

        # Record adjustment
        self.threshold_history.append({
            'timestamp': datetime.now(),
            'adjustment': total_adjustment,
            'market_volatility': market_volatility,
            'market_correlation': market_correlation,
            'market_stress_index': market_stress_index
        })

        self.last_adjustment = datetime.now()
        logger.info(f"Thresholds updated: avg adjustment = {total_adjustment:.2%}")

    def get_threshold(self, metric: str) -> float:
        """Get current threshold for a metric"""
        return self.current_thresholds.get(metric, self.base_thresholds.get(metric, 0))


class MonteCarloRiskEngine:
    """Enhanced Monte Carlo engine for real-time risk calculation"""

    def __init__(self, config: MCSimulationConfig = None):
        """
        Initialize Monte Carlo risk engine

        Args:
            config: Monte Carlo simulation configuration
        """
        self.config = config or MCSimulationConfig(
            n_simulations=5000,  # Reduce for real-time performance
            time_horizon=10,     # 10 trading days
            confidence_levels=[0.90, 0.95, 0.99]
        )
        self.simulator = MonteCarloSimulator(self.config)
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)

    def calculate_monte_carlo_risk(
        self,
        returns: pd.Series,
        portfolio_value: float = 100000,
        force_refresh: bool = False
    ) -> Dict[str, float]:
        """
        Calculate Monte Carlo risk metrics

        Args:
            returns: Historical returns
            portfolio_value: Current portfolio value
            force_refresh: Force new calculation even if cached

        Returns:
            Dictionary of risk metrics
        """
        # Check cache
        cache_key = hash(returns.tobytes()) if hasattr(returns, 'tobytes') else str(hash(tuple(returns.values)))
        now = datetime.now()

        if not force_refresh and cache_key in self.cache:
            cached_result, cached_time = self.cache[cache_key]
            if now - cached_time < self.cache_ttl:
                return cached_result

        try:
            # Run parametric simulation for speed
            results = self.simulator.simulate_parametric(
                returns=returns,
                initial_capital=portfolio_value
            )

            # Extract risk metrics
            metrics = {
                'mc_var_90': results.var[0.90],
                'mc_var_95': results.var[0.95],
                'mc_var_99': results.var[0.99],
                'mc_cvar_90': results.cvar[0.90],
                'mc_cvar_95': results.cvar[0.95],
                'mc_cvar_99': results.cvar[0.99],
                'mc_expected_shortfall': np.mean(results.final_values[results.final_values < np.percentile(results.final_values, 5)]),
                'mc_probability_of_loss': np.mean(results.final_values < portfolio_value),
                'mc_max_drawdown_mean': np.mean(results.drawdowns),
                'mc_max_drawdown_worst': np.max(results.drawdowns)
            }

            # Cache results
            self.cache[cache_key] = (metrics, now)

            return metrics

        except Exception as e:
            logger.error(f"Monte Carlo simulation failed: {e}")
            return {}

    def calculate_portfolio_var_contribution(
        self,
        returns_df: pd.DataFrame,
        weights: np.ndarray,
        portfolio_value: float,
        confidence: float = 0.95
    ) -> Dict[str, float]:
        """
        Calculate VaR contribution by component

        Args:
            returns_df: DataFrame of component returns
            weights: Portfolio weights
            portfolio_value: Portfolio value
            confidence: Confidence level

        Returns:
            Dictionary of VaR contributions
        """
        try:
            # Calculate portfolio returns
            portfolio_returns = (returns_df * weights).sum(axis=1)

            # Run Monte Carlo simulation
            results = self.simulator.simulate_parametric(
                returns=portfolio_returns,
                initial_capital=portfolio_value
            )

            # Calculate component contributions using marginal VaR
            var_threshold = np.percentile(results.final_values, (1 - confidence) * 100)
            var_contribution = {}

            for i, asset in enumerate(returns_df.columns):
                # Calculate portfolio with small change to this asset
                delta = 0.001
                perturbed_weights = weights.copy()
                perturbed_weights[i] += delta
                perturbed_weights = perturbed_weights / np.sum(perturbed_weights)

                perturbed_returns = (returns_df * perturbed_weights).sum(axis=1)
                perturbed_results = self.simulator.simulate_parametric(
                    returns=perturbed_returns,
                    initial_capital=portfolio_value
                )

                perturbed_var = np.percentile(perturbed_results.final_values, (1 - confidence) * 100)
                marginal_var = (perturbed_var - var_threshold) / delta
                contribution_var = marginal_var * weights[i]

                var_contribution[asset] = contribution_var

            return var_contribution

        except Exception as e:
            logger.error(f"VaR contribution calculation failed: {e}")
            return {}


class AutomaticRiskController:
    """Automatic risk control system"""

    def __init__(
        self,
        thresholds: Dict[str, float],
        control_config: Dict[str, Any] = None
    ):
        """
        Initialize automatic risk controller

        Args:
            thresholds: Risk control thresholds
            control_config: Control configuration
        """
        self.thresholds = thresholds
        self.config = control_config or {
            'max_position_size': 0.30,
            'max_leverage': 2.0,
            'emergency_exit_threshold': 0.20,
            'reduce_exposure_factor': 0.5,
            'min_hedge_ratio': 0.2,
            'max_hedge_ratio': 0.8
        }
        self.control_history = deque(maxlen=1000)

    def generate_control_signals(
        self,
        portfolio_id: str,
        risk_metrics: Dict[str, float],
        positions: Dict[str, float],
        portfolio_value: float
    ) -> List[RiskControlSignal]:
        """
        Generate automatic risk control signals

        Args:
            portfolio_id: Portfolio identifier
            risk_metrics: Current risk metrics
            positions: Current positions
            portfolio_value: Portfolio value

        Returns:
            List of control signals
        """
        signals = []

        # Check VaR breaches
        var_95 = risk_metrics.get('var_95_historical', 0) or risk_metrics.get('var_95_parametric', 0)
        if var_95 > self.thresholds.get('var_95', 0.05):
            signals.append(RiskControlSignal(
                action=RiskControlAction.REDUCE_EXPOSURE,
                portfolio_id=portfolio_id,
                reason=f"VaR 95% breach: {var_95:.2%}",
                triggered_by='var_95',
                metric_value=var_95,
                threshold=self.thresholds.get('var_95'),
                adjustment_factor=self.config['reduce_exposure_factor'],
                urgency=2
            ))

        # Check maximum drawdown
        current_drawdown = risk_metrics.get('current_drawdown', 0)
        if current_drawdown > self.thresholds.get('max_drawdown', 0.15):
            if current_drawdown > self.config['emergency_exit_threshold']:
                signals.append(RiskControlSignal(
                    action=RiskControlAction.EMERGENCY_EXIT,
                    portfolio_id=portfolio_id,
                    reason=f"Emergency drawdown: {current_drawdown:.2%}",
                    triggered_by='drawdown',
                    metric_value=current_drawdown,
                    threshold=self.config['emergency_exit_threshold'],
                    urgency=4
                ))
            else:
                signals.append(RiskControlSignal(
                    action=RiskControlAction.REDUCE_EXPOSURE,
                    portfolio_id=portfolio_id,
                    reason=f"High drawdown: {current_drawdown:.2%}",
                    triggered_by='drawdown',
                    metric_value=current_drawdown,
                    threshold=self.thresholds.get('max_drawdown'),
                    adjustment_factor=0.7,
                    urgency=3
                ))

        # Check volatility spikes
        volatility = risk_metrics.get('volatility_20d', 0)
        if volatility > self.thresholds.get('volatility', 0.30):
            signals.append(RiskControlSignal(
                action=RiskControlAction.REDUCE_LEVERAGE,
                portfolio_id=portfolio_id,
                reason=f"High volatility: {volatility:.2%}",
                triggered_by='volatility',
                metric_value=volatility,
                threshold=self.thresholds.get('volatility'),
                adjustment_factor=0.8,
                urgency=2
            ))

        # Check concentration risk
        max_position = max(positions.values()) if positions else 0
        if max_position > self.config['max_position_size']:
            largest_asset = max(positions.items(), key=lambda x: x[1])[0]
            signals.append(RiskControlSignal(
                action=RiskControlAction.REDUCE_EXPOSURE,
                asset_id=largest_asset,
                portfolio_id=portfolio_id,
                reason=f"High concentration: {max_position:.2%} in {largest_asset}",
                triggered_by='concentration',
                metric_value=max_position,
                threshold=self.config['max_position_size'],
                adjustment_factor=0.6,
                urgency=2
            ))

        # Check Monte Carlo risk metrics
        mc_var_99 = risk_metrics.get('mc_var_99', 0)
        if mc_var_99 > portfolio_value * self.thresholds.get('mc_var_99_ratio', 0.1):
            signals.append(RiskControlSignal(
                action=RiskControlAction.DYNAMIC_HEDGING,
                portfolio_id=portfolio_id,
                reason=f"Monte Carlo VaR 99% high: ${mc_var_99:,.0f}",
                triggered_by='monte_carlo_var',
                metric_value=mc_var_99,
                threshold=portfolio_value * self.thresholds.get('mc_var_99_ratio', 0.1),
                urgency=3
            ))

        # Record signals
        for signal in signals:
            signal.timestamp = datetime.now()
            self.control_history.append(signal)

        return signals

    def execute_control_signal(
        self,
        signal: RiskControlSignal,
        trading_system
    ) -> bool:
        """
        Execute a risk control signal

        Args:
            signal: Control signal to execute
            trading_system: Trading system interface

        Returns:
            Success status
        """
        try:
            if signal.action == RiskControlAction.REDUCE_EXPOSURE:
                if signal.asset_id:
                    # Reduce specific position
                    return trading_system.reduce_position(
                        asset=signal.asset_id,
                        factor=signal.adjustment_factor or 0.5
                    )
                else:
                    # Reduce all positions
                    return trading_system.reduce_portfolio_exposure(
                        portfolio_id=signal.portfolio_id,
                        factor=signal.adjustment_factor or 0.5
                    )

            elif signal.action == RiskControlAction.EMERGENCY_EXIT:
                return trading_system.emergency_exit(
                    portfolio_id=signal.portfolio_id
                )

            elif signal.action == RiskControlAction.HEDGE_POSITION:
                return trading_system.create_hedge(
                    asset=signal.asset_id,
                    ratio=signal.adjustment_factor or 0.5
                )

            elif signal.action == RiskControlAction.DYNAMIC_HEDGING:
                return trading_system.dynamic_hedge(
                    portfolio_id=signal.portfolio_id,
                    target_ratio=signal.adjustment_factor or 0.5
                )

            elif signal.action == RiskControlAction.REDUCE_LEVERAGE:
                return trading_system.reduce_leverage(
                    portfolio_id=signal.portfolio_id,
                    target_leverage=signal.adjustment_factor or 1.0
                )

            elif signal.action == RiskControlAction.PAUSE_TRADING:
                return trading_system.pause_trading(
                    portfolio_id=signal.portfolio_id
                )

            return True

        except Exception as e:
            logger.error(f"Failed to execute control signal: {e}")
            return False


class RiskReportGenerator:
    """Generate comprehensive risk reports"""

    def __init__(self):
        """Initialize risk report generator"""
        self.report_templates = self._load_report_templates()

    def _load_report_templates(self) -> Dict[str, str]:
        """Load report templates"""
        return {
            'daily': """
            Daily Risk Report - {date}

            Portfolio Performance:
            - Return: {return:.2%}
            - Volatility: {volatility:.2%}
            - Max Drawdown: {max_drawdown:.2%}
            - Sharpe Ratio: {sharpe_ratio:.2f}

            Risk Metrics:
            - VaR (95%): {var_95:.2%}
            - VaR (99%): {var_99:.2%}
            - Expected Shortfall (95%): {es_95:.2%}
            - Beta: {beta:.2f}

            Monte Carlo Risk:
            - MC VaR (95%): ${mc_var_95:,.0f}
            - Probability of Loss: {prob_loss:.2%}

            Alerts: {alert_count} generated
            Control Actions: {control_count} executed
            """,

            'weekly': """
            Weekly Risk Report - {date}

            Summary: {summary}

            Top Risk Contributors: {top_risks}

            Risk Trend Analysis: {risk_trends}

            Recommendations: {recommendations}
            """,

            'stress_test': """
            Stress Test Results - {date}

            Scenario Analysis: {scenarios}

            Portfolio Resilience: {resilience}

            Mitigation Strategies: {mitigations}
            """
        }

    def generate_daily_report(
        self,
        portfolio_id: str,
        risk_metrics: Dict[str, float],
        monte_carlo_results: Optional[Dict[str, float]],
        alerts: List[Dict[str, Any]],
        control_actions: List[Dict[str, Any]],
        performance_data: Dict[str, float]
    ) -> RiskReport:
        """
        Generate daily risk report

        Args:
            portfolio_id: Portfolio identifier
            risk_metrics: Current risk metrics
            monte_carlo_results: Monte Carlo simulation results
            alerts: Recent alerts
            control_actions: Recent control actions
            performance_data: Performance metrics

        Returns:
            RiskReport object
        """
        now = datetime.now()
        period_start = now - timedelta(days=1)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_metrics,
            alerts,
            control_actions
        )

        # Calculate risk attribution
        risk_attribution = self._calculate_risk_attribution(risk_metrics)

        report = RiskReport(
            portfolio_id=portfolio_id,
            report_date=now,
            period_start=period_start,
            period_end=now,
            risk_metrics=risk_metrics,
            monte_carlo_results=monte_carlo_results,
            alerts_summary={
                'total': len(alerts),
                'warning': len([a for a in alerts if a.get('level') == 'warning']),
                'error': len([a for a in alerts if a.get('level') == 'error']),
                'critical': len([a for a in alerts if a.get('level') == 'critical'])
            },
            control_actions=control_actions,
            performance_metrics=performance_data,
            recommendations=recommendations,
            risk_attribution=risk_attribution
        )

        return report

    def _generate_recommendations(
        self,
        risk_metrics: Dict[str, float],
        alerts: List[Dict[str, Any]],
        control_actions: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []

        # VaR recommendations
        var_95 = risk_metrics.get('var_95_historical', 0) or risk_metrics.get('var_95_parametric', 0)
        if var_95 > 0.05:
            recommendations.append(
                f"Consider reducing position sizes - VaR 95% is elevated at {var_95:.2%}"
            )

        # Drawdown recommendations
        drawdown = risk_metrics.get('current_drawdown', 0)
        if drawdown > 0.10:
            recommendations.append(
                f"Portfolio is in drawdown of {drawdown:.2%} - review strategy performance"
            )

        # Volatility recommendations
        volatility = risk_metrics.get('volatility_20d', 0)
        if volatility > 0.25:
            recommendations.append(
                f"High volatility detected ({volatility:.2%}) - consider reducing leverage"
            )

        # Alert pattern recommendations
        if len(alerts) > 5:
            recommendations.append(
                "High number of alerts generated - review risk thresholds"
            )

        # Control action recommendations
        if len(control_actions) > 3:
            recommendations.append(
                "Multiple risk controls triggered - consider strategy adjustment"
            )

        # Monte Carlo recommendations
        mc_var_99 = risk_metrics.get('mc_var_99', 0)
        portfolio_value = risk_metrics.get('portfolio_value', 100000)
        if mc_var_99 > portfolio_value * 0.15:
            recommendations.append(
                "Monte Carlo shows significant tail risk - implement hedging"
            )

        return recommendations

    def _calculate_risk_attribution(self, risk_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate risk attribution by factor"""
        # Simplified risk attribution
        attribution = {
            'market_risk': 0.4,
            'volatility_risk': 0.3,
            'drawdown_risk': 0.2,
            'tail_risk': 0.1
        }

        # Adjust based on actual metrics
        if risk_metrics.get('volatility_20d', 0) > 0.25:
            attribution['volatility_risk'] = 0.5
            attribution['market_risk'] = 0.3

        if risk_metrics.get('current_drawdown', 0) > 0.1:
            attribution['drawdown_risk'] = 0.35

        return attribution

    def export_report(self, report: RiskReport, format: str = 'json') -> str:
        """
        Export risk report in specified format

        Args:
            report: Risk report to export
            format: Export format ('json', 'html', 'pdf')

        Returns:
            Report as string
        """
        if format == 'json':
            return json.dumps(asdict(report), indent=2, default=str)

        elif format == 'html':
            # Generate HTML report
            html = f"""
            <html>
            <head>
                <title>Risk Report - {report.portfolio_id}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .metric {{ margin: 10px 0; }}
                    .warning {{ color: orange; }}
                    .error {{ color: red; }}
                    .critical {{ color: darkred; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>Risk Report - {report.portfolio_id}</h1>
                <p>Date: {report.report_date.strftime('%Y-%m-%d %H:%M')}</p>

                <h2>Risk Metrics</h2>
                {self._format_metrics_html(report.risk_metrics)}

                <h2>Performance</h2>
                {self._format_metrics_html(report.performance_metrics)}

                <h2>Alerts Summary</h2>
                <p>Total: {report.alerts_summary['total']}</p>
                <p class="warning">Warnings: {report.alerts_summary['warning']}</p>
                <p class="error">Errors: {report.alerts_summary['error']}</p>
                <p class="critical">Critical: {report.alerts_summary['critical']}</p>

                <h2>Recommendations</h2>
                <ul>
                {"".join([f"<li>{r}</li>" for r in report.recommendations])}
                </ul>
            </body>
            </html>
            """
            return html

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _format_metrics_html(self, metrics: Dict[str, Any]) -> str:
        """Format metrics as HTML"""
        html = ""
        for key, value in metrics.items():
            if isinstance(value, float):
                if 'var' in key.lower() or 'drawdown' in key.lower():
                    html += f'<div class="metric">{key}: {value:.2%}</div>'
                elif 'sharpe' in key.lower() or 'beta' in key.lower():
                    html += f'<div class="metric">{key}: {value:.2f}</div>
                else:
                    html += f'<div class="metric">{key}: {value}</div>'
            else:
                html += f'<div class="metric">{key}: {value}</div>'
        return html


class EnhancedDynamicMonitor:
    """Enhanced dynamic risk monitoring system"""

    def __init__(self, config: RiskConfig):
        """
        Initialize enhanced dynamic monitor

        Args:
            config: Risk configuration
        """
        self.config = config
        self.running = False

        # Initialize components
        self.threshold_manager = DynamicThresholdManager(
            base_thresholds={
                'var_95': 0.05,
                'var_99': 0.10,
                'max_drawdown': 0.15,
                'volatility': 0.30,
                'mc_var_99_ratio': 0.10
            }
        )

        self.mc_engine = MonteCarloRiskEngine(
            config=MCSimulationConfig(
                n_simulations=5000,
                time_horizon=10,
                confidence_levels=[0.90, 0.95, 0.99]
            )
        )

        self.risk_controller = AutomaticRiskController(
            thresholds=self.threshold_manager.current_thresholds
        )

        self.report_generator = RiskReportGenerator()

        # Monitoring data
        self.monitoring_data = {
            'risk_metrics_history': deque(maxlen=1000),
            'control_signals_history': deque(maxlen=500),
            'alerts_history': deque(maxlen=1000),
            'report_history': deque(maxlen=100)
        }

        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.process_pool = ProcessPoolExecutor(max_workers=2)

        # Lock for thread safety
        self._lock = threading.Lock()

    async def start_monitoring(self, portfolios: Dict[str, Dict]):
        """
        Start enhanced monitoring

        Args:
            portfolios: Portfolios to monitor
        """
        self.running = True
        self.portfolios = portfolios

        logger.info("Starting enhanced dynamic risk monitoring")

        # Start monitoring loop
        monitor_task = asyncio.create_task(self._enhanced_monitoring_loop())

        return monitor_task

    async def stop_monitoring(self):
        """Stop enhanced monitoring"""
        self.running = False
        self.executor.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        logger.info("Enhanced dynamic monitoring stopped")

    async def _enhanced_monitoring_loop(self):
        """Enhanced monitoring loop"""
        while self.running:
            try:
                for portfolio_id, portfolio_info in self.portfolios.items():
                    await self._process_portfolio_enhanced(portfolio_id, portfolio_info)

                # Sleep until next cycle
                await asyncio.sleep(self.config.calculation_interval)

            except Exception as e:
                logger.error(f"Error in enhanced monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _process_portfolio_enhanced(self, portfolio_id: str, portfolio_info: Dict):
        """
        Process a portfolio with enhanced monitoring

        Args:
            portfolio_id: Portfolio identifier
            portfolio_info: Portfolio information
        """
        try:
            # Fetch portfolio data
            portfolio_data = await self._fetch_portfolio_data(portfolio_id)
            if portfolio_data.empty:
                return

            # Calculate traditional risk metrics
            risk_metrics = await self._calculate_traditional_risk_metrics(portfolio_data)

            # Calculate Monte Carlo risk metrics
            portfolio_value = portfolio_data.get('total_value', pd.Series()).iloc[-1] if 'total_value' in portfolio_data else 100000
            returns = portfolio_data.get('returns', pd.Series())
            if not returns.empty:
                mc_metrics = self.mc_engine.calculate_monte_carlo_risk(
                    returns=returns,
                    portfolio_value=portfolio_value
                )
                risk_metrics.update(mc_metrics)

            # Update dynamic thresholds
            market_volatility = self._calculate_market_volatility(portfolio_data)
            market_correlation = self._calculate_market_correlation(portfolio_data)
            market_stress = self._calculate_market_stress_index(portfolio_data)

            self.threshold_manager.update_thresholds(
                market_volatility=market_volatility,
                market_correlation=market_correlation,
                market_stress_index=market_stress
            )

            # Generate control signals
            positions = portfolio_info.get('positions', {})
            control_signals = self.risk_controller.generate_control_signals(
                portfolio_id=portfolio_id,
                risk_metrics=risk_metrics,
                positions=positions,
                portfolio_value=portfolio_value
            )

            # Store monitoring data
            self.monitoring_data['risk_metrics_history'].append({
                'portfolio_id': portfolio_id,
                'timestamp': datetime.now(),
                'metrics': risk_metrics
            })

            self.monitoring_data['control_signals_history'].extend([
                asdict(signal) for signal in control_signals
            ])

            # Execute control signals (if trading system available)
            for signal in control_signals:
                if signal.urgency >= 3:  # High urgency
                    logger.warning(
                        f"High urgency control signal: {signal.action.value} - {signal.reason}"
                    )

            # Generate daily report
            if datetime.now().hour == 16 and datetime.now().minute == 0:  # 4 PM
                await self._generate_daily_report(portfolio_id, risk_metrics)

        except Exception as e:
            logger.error(f"Error processing portfolio {portfolio_id}: {e}")

    async def _calculate_traditional_risk_metrics(self, portfolio_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate traditional risk metrics"""
        metrics = {}

        # Extract returns
        returns = portfolio_data.get('returns', pd.Series())
        if returns.empty and 'total_value' in portfolio_data:
            returns = portfolio_data['total_value'].pct_change().dropna()

        if not returns.empty and len(returns) > 20:
            # VaR calculations
            metrics['var_95_historical'] = returns.quantile(0.05)
            metrics['var_99_historical'] = returns.quantile(0.01)

            # Expected Shortfall
            metrics['es_95_historical'] = returns[returns <= metrics['var_95_historical']].mean()
            metrics['es_99_historical'] = returns[returns <= metrics['var_99_historical']].mean()

            # Volatility
            metrics['volatility_20d'] = returns.rolling(20).std().iloc[-1] * np.sqrt(252)

            # Maximum Drawdown
            if 'total_value' in portfolio_data:
                drawdown = self._calculate_drawdown(portfolio_data['total_value'])
                metrics['current_drawdown'] = drawdown['current']
                metrics['max_drawdown'] = drawdown['max']

            # Sharpe Ratio
            if len(returns) > 60:
                excess_returns = returns - 0.02 / 252  # Assuming 2% risk-free rate
                metrics['sharpe_ratio'] = excess_returns.mean() / excess_returns.std() * np.sqrt(252)

        return metrics

    def _calculate_drawdown(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate drawdown metrics"""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        return {
            'current': abs(drawdown.iloc[-1]),
            'max': abs(drawdown.min())
        }

    def _calculate_market_volatility(self, portfolio_data: pd.DataFrame) -> float:
        """Calculate market volatility estimate"""
        if 'returns' in portfolio_data:
            return portfolio_data['returns'].rolling(20).std().iloc[-1] * np.sqrt(252)
        return 0.20  # Default

    def _calculate_market_correlation(self, portfolio_data: pd.DataFrame) -> float:
        """Calculate market correlation estimate"""
        # Simplified - would use market data in production
        return 0.5

    def _calculate_market_stress_index(self, portfolio_data: pd.DataFrame) -> float:
        """Calculate market stress index"""
        # Simplified stress index based on volatility and drawdown
        volatility = self._calculate_market_volatility(portfolio_data)
        drawdown = 0  # Would calculate from market data

        stress_index = min(1.0, max(0.0, (volatility - 0.10) / 0.20))
        return stress_index

    async def _fetch_portfolio_data(self, portfolio_id: str) -> pd.DataFrame:
        """Fetch portfolio data"""
        # This would integrate with actual data source
        return pd.DataFrame()

    async def _generate_daily_report(self, portfolio_id: str, risk_metrics: Dict[str, float]):
        """Generate daily risk report"""
        try:
            # Get recent alerts and control actions
            recent_alerts = list(self.monitoring_data['alerts_history'])[-10:]
            recent_actions = list(self.monitoring_data['control_signals_history'])[-10:]

            # Generate performance metrics
            performance_metrics = {
                'portfolio_value': risk_metrics.get('portfolio_value', 0),
                'daily_return': 0,  # Would calculate from data
                'ytd_return': 0  # Would calculate from data
            }

            # Create report
            report = self.report_generator.generate_daily_report(
                portfolio_id=portfolio_id,
                risk_metrics=risk_metrics,
                monte_carlo_results={k: v for k, v in risk_metrics.items() if k.startswith('mc_')},
                alerts=recent_alerts,
                control_actions=recent_actions,
                performance_data=performance_metrics
            )

            # Store report
            self.monitoring_data['report_history'].append(asdict(report))

            # Export report
            report_html = self.report_generator.export_report(report, format='html')

            # Save to file or send via email
            report_path = f"reports/risk_report_{portfolio_id}_{datetime.now().strftime('%Y%m%d')}.html"
            with open(report_path, 'w') as f:
                f.write(report_html)

            logger.info(f"Daily report generated for portfolio {portfolio_id}")

        except Exception as e:
            logger.error(f"Error generating daily report: {e}")

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        return {
            'active_portfolios': len(self.portfolios) if hasattr(self, 'portfolios') else 0,
            'risk_metrics_count': len(self.monitoring_data['risk_metrics_history']),
            'control_signals_count': len(self.monitoring_data['control_signals_history']),
            'alerts_count': len(self.monitoring_data['alerts_history']),
            'reports_generated': len(self.monitoring_data['report_history']),
            'current_thresholds': self.threshold_manager.current_thresholds,
            'last_threshold_adjustment': self.threshold_manager.last_adjustment.isoformat()
        }