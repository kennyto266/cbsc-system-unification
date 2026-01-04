"""
Enhanced Dynamic Risk Monitoring Demo

This script demonstrates the usage of the enhanced dynamic risk monitoring system
with Monte Carlo simulation, automatic risk control, and dynamic thresholds.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from .config import RiskConfig
from .enhanced_dynamic_monitor import EnhancedDynamicMonitor
from .risk_calculators import VaRCalculator, ExpectedShortfallCalculator
from .alert_system import AlertSystem, AlertLevel, AlertType
from ..backtest.monte_carlo import MonteCarloSimulator, MCSimulationConfig


class MockTradingSystem:
    """Mock trading system for demonstration"""

    def __init__(self):
        self.positions = {
            'AAPL': 0.25,
            'MSFT': 0.25,
            'GOOGL': 0.20,
            'AMZN': 0.15,
            'TSLA': 0.15
        }
        self.trading_paused = False
        self.leverage = 1.5

    def reduce_position(self, asset: str, factor: float) -> bool:
        """Reduce position in specific asset"""
        if asset in self.positions:
            original = self.positions[asset]
            self.positions[asset] *= (1 - factor)
            logger.info(f"Reduced {asset} position: {original:.2%} -> {self.positions[asset]:.2%}")
            return True
        return False

    def reduce_portfolio_exposure(self, portfolio_id: str, factor: float) -> bool:
        """Reduce entire portfolio exposure"""
        for asset in self.positions:
            self.positions[asset] *= (1 - factor)
        logger.info(f"Reduced portfolio exposure by factor {factor:.2%}")
        return True

    def emergency_exit(self, portfolio_id: str) -> bool:
        """Emergency exit - liquidate all positions"""
        self.positions = {k: 0.0 for k in self.positions}
        self.trading_paused = True
        logger.warning(f"EMERGENCY EXIT triggered for portfolio {portfolio_id}")
        return True

    def create_hedge(self, asset: str, ratio: float) -> bool:
        """Create hedge for asset"""
        logger.info(f"Created hedge for {asset} with ratio {ratio:.2%}")
        return True

    def dynamic_hedge(self, portfolio_id: str, target_ratio: float) -> bool:
        """Implement dynamic hedging"""
        logger.info(f"Dynamic hedging for portfolio {portfolio_id} - target ratio {target_ratio:.2%}")
        return True

    def reduce_leverage(self, portfolio_id: str, target_leverage: float) -> bool:
        """Reduce portfolio leverage"""
        self.leverage = target_leverage
        logger.info(f"Reduced leverage to {target_leverage:.1f}x")
        return True

    def pause_trading(self, portfolio_id: str) -> bool:
        """Pause trading"""
        self.trading_paused = True
        logger.warning(f"Trading paused for portfolio {portfolio_id}")
        return True

    def get_positions(self) -> Dict[str, float]:
        """Get current positions"""
        return self.positions


def generate_sample_data(
    n_days: int = 252,
    initial_value: float = 1000000,
    assets: List[str] = None
) -> pd.DataFrame:
    """
    Generate sample portfolio data for demonstration

    Args:
        n_days: Number of days of data
        initial_value: Initial portfolio value
        assets: List of assets in portfolio

    Returns:
        DataFrame with portfolio data
    """
    if assets is None:
        assets = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

    # Generate dates
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')

    # Generate returns with some correlation
    np.random.seed(42)
    n_assets = len(assets)

    # Correlation matrix
    corr_matrix = np.full((n_assets, n_assets), 0.3)
    np.fill_diagonal(corr_matrix, 1.0)

    # Cholesky decomposition for correlated returns
    chol = np.linalg.cholesky(corr_matrix)

    # Generate correlated random returns
    daily_returns = np.random.randn(n_days, n_assets) @ chol.T

    # Add some drift and volatility differences
    drifts = np.array([0.0005, 0.0004, 0.0003, 0.0006, 0.0008])  # Daily drifts
    vols = np.array([0.02, 0.018, 0.016, 0.025, 0.035])  # Daily volatilities

    for i in range(n_assets):
        daily_returns[:, i] = daily_returns[:, i] * vols[i] + drifts[i]

    # Add some stress periods
    stress_start = n_days // 2
    stress_end = stress_start + 20
    daily_returns[stress_start:stress_end, :] *= 3  # Triple volatility during stress

    # Add a crash period
    crash_start = n_days * 3 // 4
    crash_end = crash_start + 5
    daily_returns[crash_start:crash_end, :] -= 0.05  # 5% daily drop during crash

    # Create portfolio
    weights = np.array([0.25, 0.25, 0.20, 0.15, 0.15])

    # Calculate portfolio returns
    portfolio_returns = daily_returns @ weights

    # Calculate portfolio value
    portfolio_value = initial_value * np.cumprod(1 + portfolio_returns)

    # Create DataFrame
    df = pd.DataFrame(index=dates)
    df['total_value'] = portfolio_value
    df['returns'] = portfolio_returns
    df['daily_pnl'] = portfolio_returns * initial_value

    # Add individual asset values
    for i, asset in enumerate(assets):
        asset_returns = daily_returns[:, i]
        asset_value = initial_value * weights[i] * np.cumprod(1 + asset_returns)
        df[f'{asset}_value'] = asset_value

    return df


async def demo_enhanced_monitoring():
    """Demonstrate enhanced dynamic risk monitoring"""
    logger.info("Starting Enhanced Dynamic Risk Monitoring Demo")

    # Create configuration
    config = RiskConfig()
    config.calculation_interval = 2  # 2 seconds for demo
    config.alert_enabled = True

    # Initialize mock trading system
    trading_system = MockTradingSystem()

    # Create enhanced monitor
    monitor = EnhancedDynamicMonitor(config)

    # Generate sample data
    sample_data = generate_sample_data(n_days=100)

    # Create portfolio
    portfolios = {
        'demo_portfolio': {
            'name': 'Demo Portfolio',
            'positions': trading_system.get_positions(),
            'base_value': 1000000,
            'data': sample_data
        }
    }

    # Mock data fetching function
    async def mock_fetch_data(portfolio_id: str) -> pd.DataFrame:
        return portfolios[portfolio_id]['data']

    # Override monitor's data fetching
    monitor._fetch_portfolio_data = mock_fetch_data

    logger.info(f"Monitoring {len(portfolios)} portfolios")

    # Start monitoring
    monitor_task = await monitor.start_monitoring(portfolios)

    # Run for some time to collect data
    logger.info("Running monitoring for 30 seconds...")
    await asyncio.sleep(30)

    # Get monitoring summary
    summary = monitor.get_monitoring_summary()
    logger.info("\n=== Monitoring Summary ===")
    for key, value in summary.items():
        logger.info(f"{key}: {value}")

    # Get latest risk metrics
    if monitor.monitoring_data['risk_metrics_history']:
        latest_metrics = monitor.monitoring_data['risk_metrics_history'][-1]
        logger.info("\n=== Latest Risk Metrics ===")
        for metric, value in latest_metrics['metrics'].items():
            if isinstance(value, float):
                if 'var' in metric.lower() or 'drawdown' in metric.lower() or 'es' in metric.lower():
                    logger.info(f"{metric}: {value:.2%}")
                else:
                    logger.info(f"{metric}: {value:.4f}")

    # Get control signals
    if monitor.monitoring_data['control_signals_history']:
        logger.info("\n=== Recent Control Signals ===")
        for signal in monitor.monitoring_data['control_signals_history'][-5:]:
            logger.info(
                f"Signal: {signal['action']} - {signal.get('reason', 'No reason')} "
                f"(Urgency: {signal.get('urgency', 1)})"
            )

    # Generate a report
    if portfolios['demo_portfolio']:
        risk_metrics = latest_metrics['metrics'] if latest_metrics else {}
        report = monitor.report_generator.generate_daily_report(
            portfolio_id='demo_portfolio',
            risk_metrics=risk_metrics,
            monte_carlo_results={k: v for k, v in risk_metrics.items() if k.startswith('mc_')},
            alerts=[],
            control_actions=[asdict(s) for s in monitor.monitoring_data['control_signals_history']],
            performance_data={
                'portfolio_value': portfolios['demo_portfolio']['data']['total_value'].iloc[-1],
                'daily_return': portfolios['demo_portfolio']['data']['returns'].iloc[-1],
                'ytd_return': (portfolios['demo_portfolio']['data']['total_value'].iloc[-1] -
                             portfolios['demo_portfolio']['base_value']) / portfolios['demo_portfolio']['base_value']
            }
        )

        # Export report
        report_json = monitor.report_generator.export_report(report, format='json')
        logger.info("\n=== Risk Report Generated ===")
        logger.info(f"Report recommendations: {len(report.recommendations)}")
        for rec in report.recommendations:
            logger.info(f"- {rec}")

    # Stop monitoring
    await monitor.stop_monitoring()

    logger.info("Demo completed")


async def demo_monte_carlo_integration():
    """Demonstrate Monte Carlo integration with risk monitoring"""
    logger.info("\n\nStarting Monte Carlo Integration Demo")

    # Create Monte Carlo simulator
    mc_config = MCSimulationConfig(
        n_simulations=10000,
        time_horizon=10,
        confidence_levels=[0.90, 0.95, 0.99],
        random_seed=42
    )
    mc_simulator = MonteCarloSimulator(mc_config)

    # Generate sample returns
    np.random.seed(42)
    returns = pd.Series(np.random.randn(252) * 0.02 + 0.0005)

    # Run simulations
    logger.info("Running Monte Carlo simulations...")
    results_bootstrap = mc_simulator.simulate_bootstrap(returns, initial_capital=1000000)
    results_parametric = mc_simulator.simulate_parametric(returns, initial_capital=1000000)

    # Display results
    logger.info("\n=== Bootstrap Simulation Results ===")
    logger.info(f"Final value mean: ${results_bootstrap.final_values.mean():,.0f}")
    logger.info(f"Final value std: ${results_bootstrap.final_values.std():,.0f}")
    logger.info(f"VaR 95%: ${results_bootstrap.var[0.95]:,.0f}")
    logger.info(f"CVaR 95%: ${results_bootstrap.cvar[0.95]:,.0f}")

    logger.info("\n=== Parametric Simulation Results ===")
    logger.info(f"Final value mean: ${results_parametric.final_values.mean():,.0f}")
    logger.info(f"Final value std: ${results_parametric.final_values.std():,.0f}")
    logger.info(f"VaR 95%: ${results_parametric.var[0.95]:,.0f}")
    logger.info(f"CVaR 95%: ${results_parametric.cvar[0.95]:,.0f}")

    # Calculate risk contributions for multi-asset portfolio
    assets = ['Asset_A', 'Asset_B', 'Asset_C']
    returns_df = pd.DataFrame(
        np.random.randn(252, 3) * 0.02,
        columns=assets
    )
    weights = np.array([0.4, 0.3, 0.3])

    # Create enhanced monitor for contribution analysis
    config = RiskConfig()
    monitor = EnhancedDynamicMonitor(config)

    logger.info("\n=== VaR Contribution Analysis ===")
    contributions = monitor.mc_engine.calculate_portfolio_var_contribution(
        returns_df=returns_df,
        weights=weights,
        portfolio_value=1000000,
        confidence=0.95
    )

    for asset, contribution in contributions.items():
        logger.info(f"{asset}: ${contribution:,.0f}")

    logger.info("Monte Carlo integration demo completed")


async def demo_dynamic_thresholds():
    """Demonstrate dynamic threshold adjustment"""
    logger.info("\n\nStarting Dynamic Thresholds Demo")

    from .enhanced_dynamic_monitor import DynamicThresholdManager

    # Initialize threshold manager
    base_thresholds = {
        'var_95': 0.05,
        'var_99': 0.10,
        'max_drawdown': 0.15,
        'volatility': 0.30
    }

    threshold_manager = DynamicThresholdManager(
        base_thresholds=base_thresholds,
        adjustment_factor=0.2
    )

    logger.info("=== Initial Thresholds ===")
    for metric, threshold in threshold_manager.current_thresholds.items():
        logger.info(f"{metric}: {threshold:.2%}")

    # Simulate market stress conditions
    market_conditions = [
        ("Normal Market", 0.15, 0.3, 0.1),
        ("Moderate Stress", 0.25, 0.5, 0.4),
        ("High Stress", 0.40, 0.7, 0.8),
        ("Extreme Crisis", 0.60, 0.9, 1.0)
    ]

    for condition, vol, corr, stress in market_conditions:
        threshold_manager.update_thresholds(vol, corr, stress)
        logger.info(f"\n=== {condition} ===")
        logger.info(f"Market - Vol: {vol:.1%}, Corr: {corr:.1%}, Stress: {stress:.1%}")

        for metric, threshold in threshold_manager.current_thresholds.items():
            change = (threshold - base_thresholds[metric]) / base_thresholds[metric]
            direction = "tightened" if change < 0 else "relaxed"
            logger.info(f"{metric}: {threshold:.2%} ({direction} by {abs(change):.1%})")

    logger.info("Dynamic thresholds demo completed")


async def main():
    """Main demo function"""
    try:
        # Run all demos
        await demo_enhanced_monitoring()
        await demo_monte_carlo_integration()
        await demo_dynamic_thresholds()

        logger.info("\n=== All demos completed successfully ===")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())