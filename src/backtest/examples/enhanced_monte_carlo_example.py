"""
Enhanced Monte Carlo Simulation Example
====================================

Comprehensive example demonstrating the enhanced Monte Carlo simulation system
with VectorBT integration, parallel processing, and advanced analytics.

Author: Claude Code Assistant
Date: 2025-01-19
"""

import asyncio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings

# Import the enhanced Monte Carlo system
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_monte_carlo import (
    EnhancedMonteCarloSimulator,
    EnhancedMCConfig,
    EnhancedMCResults,
    SimulationMethod,
    SimulationScenario,
    VectorBTMonteCarlo,
    run_enhanced_monte_carlo,
    generate_monte_carlo_report
)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


def generate_realistic_returns(days: int = 252, mu: float = 0.0008, sigma: float = 0.015,
                               skew: float = 0.5, kurt: float = 5.0, seed: int = 42) -> pd.Series:
    """
    Generate realistic return series with skewness and kurtosis

    Args:
        days: Number of trading days
        mu: Daily mean return
        sigma: Daily volatility
        skew: Skewness parameter
        kurt: Kurtosis parameter
        seed: Random seed

    Returns:
        Series of returns
    """
    np.random.seed(seed)

    # Generate returns from a skewed t-distribution
    from scipy import stats

    # Use Johnson SU distribution for flexible shape
    a, b = 0, 1  # Location and scale
    gamma, delta = skew, kurt  # Shape parameters

    # Generate Johnson SU random variates
    returns = stats.johnsonsu.rvs(a, b, gamma, delta, size=days)

    # Scale to desired mean and volatility
    returns = (returns - np.mean(returns)) / np.std(returns) * sigma + mu

    # Create pandas Series with date index
    index = pd.date_range(start='2023-01-01', periods=days, freq='D')
    return pd.Series(returns, index=index)


def plot_simulation_results(results: EnhancedMCResults, title: str = "Monte Carlo Simulation Results",
                           save_path: str = None):
    """
    Create comprehensive visualization of simulation results

    Args:
        results: Enhanced simulation results
        title: Plot title
        save_path: Path to save plot
    """
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle(title, fontsize=16, y=0.98)

    # Create grid specification for better layout
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

    # 1. Sample Equity Curves
    ax1 = fig.add_subplot(gs[0, :2])
    n_paths = min(100, len(results.equity_curves))
    indices = np.random.choice(len(results.equity_curves), n_paths, replace=False)

    for idx in indices:
        ax1.plot(results.equity_curves[idx], alpha=0.3, linewidth=0.5)

    # Add percentiles
    percentiles = [5, 25, 50, 75, 95]
    for p in percentiles:
        percentile_path = np.percentile(results.equity_curves, p, axis=0)
        ax1.plot(percentile_path, linewidth=2, label=f'{p}th percentile')

    ax1.set_title('Sample Equity Curves with Percentiles')
    ax1.set_xlabel('Days')
    ax1.set_ylabel('Portfolio Value')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # 2. Final Value Distribution
    ax2 = fig.add_subplot(gs[0, 2:])
    ax2.hist(results.final_values, bins=50, alpha=0.7, edgecolor='black', density=True)

    # Add fitted normal distribution
    mean = np.mean(results.final_values)
    std = np.std(results.final_values)
    x = np.linspace(results.final_values.min(), results.final_values.max(), 100)
    ax2.plot(x, stats.norm.pdf(x, mean, std), 'r-', linewidth=2, label='Normal Fit')

    ax2.axvline(mean, color='red', linestyle='--', label=f'Mean: ${mean:,.0f}')
    ax2.axvline(np.median(results.final_values), color='green', linestyle='--',
               label=f'Median: ${np.median(results.final_values):,.0f}')
    ax2.set_title('Final Value Distribution')
    ax2.set_xlabel('Final Portfolio Value')
    ax2.set_ylabel('Density')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    # 3. Risk Metrics Heatmap
    ax3 = fig.add_subplot(gs[1, 0])
    risk_data = [
        [results.var.get(0.90, 0), results.cvar.get(0.90, 0)],
        [results.var.get(0.95, 0), results.cvar.get(0.95, 0)],
        [results.var.get(0.99, 0), results.cvar.get(0.99, 0)]
    ]
    sns.heatmap(risk_data, annot=True, fmt='.0f', cmap='Reds',
                xticklabels=['VaR', 'CVaR'], yticklabels=['90%', '95%', '99%'],
                ax=ax3, cbar_kws={'label': 'Loss ($)'})
    ax3.set_title('Risk Metrics')

    # 4. Drawdown Distribution
    ax4 = fig.add_subplot(gs[1, 1])
    max_drawdowns = np.min(results.drawdowns, axis=1) * 100
    ax4.hist(max_drawdowns, bins=50, alpha=0.7, edgecolor='black')
    ax4.axvline(np.mean(max_drawdowns), color='red', linestyle='--',
               label=f'Mean: {np.mean(max_drawdowns):.1f}%')
    ax4.set_title('Maximum Drawdown Distribution')
    ax4.set_xlabel('Maximum Drawdown (%)')
    ax4.set_ylabel('Frequency')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)

    # 5. Success Probability Bar Chart
    ax5 = fig.add_subplot(gs[1, 2])
    success_probs = results.success_probability
    probs = list(success_probs.values())
    labels = [k.replace('_', ' ').title() for k in success_probs.keys()]
    colors = ['green' if p > 0.5 else 'orange' if p > 0.3 else 'red' for p in probs]
    bars = ax5.barh(labels, probs, color=colors, alpha=0.7)
    ax5.set_xlim(0, 1)
    ax5.set_xlabel('Probability')
    ax5.set_title('Success Probabilities')
    ax5.grid(True, alpha=0.3, axis='x')

    # Add percentage labels
    for bar, prob in zip(bars, probs):
        ax5.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f'{prob:.1%}', va='center', fontsize=8)

    # 6. Scenario Comparison (if available)
    ax6 = fig.add_subplot(gs[1, 3])
    if results.scenario_results:
        scenarios = list(results.scenario_results.keys())
        means = [results.scenario_results[s].statistics['mean'] for s in scenarios]
        bars = ax6.bar(scenarios, means, alpha=0.7)
        ax6.set_title('Scenario Means')
        ax6.set_ylabel('Mean Final Value')
        ax6.tick_params(axis='x', rotation=45)
        ax6.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for bar, mean in zip(bars, means):
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'${mean:,.0f}', ha='center', va='bottom', fontsize=8)
    else:
        ax6.text(0.5, 0.5, 'No Scenarios\nAnalyzed', ha='center', va='center',
                transform=ax6.transAxes, fontsize=12)
        ax6.set_title('Scenario Analysis')

    # 7. Sensitivity Analysis (if available)
    ax7 = fig.add_subplot(gs[2, :2])
    if results.sensitivity_results and results.sensitivity_results.sensitivities:
        sensitivities = results.sensitivity_results.sensitivities

        # Create subplots for each parameter
        n_params = len(sensitivities)
        if n_params > 0:
            for i, (param, data) in enumerate(sensitivities.items()):
                if 'param_values' in data and 'final_values' in data:
                    ax7.plot(data['param_values'], data['final_values'],
                           marker='o', label=param)

            ax7.set_xlabel('Parameter Value')
            ax7.set_ylabel('Mean Final Value')
            ax7.set_title('Sensitivity Analysis')
            ax7.legend(fontsize=8)
            ax7.grid(True, alpha=0.3)
    else:
        ax7.text(0.5, 0.5, 'No Sensitivity\nAnalysis', ha='center', va='center',
                transform=ax7.transAxes, fontsize=12)
        ax7.set_title('Sensitivity Analysis')

    # 8. Execution Stats
    ax8 = fig.add_subplot(gs[2, 2:])
    if results.execution_stats:
        stats_text = (
            f"Simulation ID: {results.simulation_id}\n"
            f"Total Simulations: {len(results.final_values):,}\n"
            f"Execution Time: {results.execution_stats.get('execution_time', 0):.2f}s\n"
            f"Simulations/sec: {results.execution_stats.get('simulations_per_second', 0):.0f}\n"
            f"Workers Used: {results.execution_stats.get('n_workers_used', 0)}\n"
            f"VectorBT Used: {results.execution_stats.get('vectorbt_used', False)}\n"
            f"Memory Optimized: {results.execution_stats.get('memory_optimized', False)}"
        )
        ax8.text(0.1, 0.5, stats_text, transform=ax8.transAxes, fontsize=10,
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax8.set_xlim(0, 1)
        ax8.set_ylim(0, 1)
        ax8.axis('off')
        ax8.set_title('Execution Statistics')
    else:
        ax8.text(0.5, 0.5, 'No Execution\nStatistics', ha='center', va='center',
                transform=ax8.transAxes, fontsize=12)
        ax8.set_title('Execution Statistics')

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")

    plt.show()


async def example_basic_simulation():
    """Example 1: Basic Monte Carlo simulation"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Monte Carlo Simulation")
    print("="*60)

    # Generate test data
    returns = generate_realistic_returns(days=252, mu=0.0008, sigma=0.015)

    # Quick simulation
    results = await run_enhanced_monte_carlo(
        returns=returns,
        method=SimulationMethod.BOOTSTRAP,
        n_simulations=5000,
        time_horizon=252,
        initial_capital=100000,
        n_workers=4
    )

    # Print basic statistics
    print(f"\nSimulation Results:")
    print(f"  Mean Final Value: ${results.statistics['mean']:,.2f}")
    print(f"  Median Final Value: ${results.statistics['median']:,.2f}")
    print(f"  Standard Deviation: ${results.statistics['std']:,.2f}")
    print(f"  5th Percentile: ${np.percentile(results.final_values, 5):,.2f}")
    print(f"  95th Percentile: ${np.percentile(results.final_values, 95):,.2f}")
    print(f"  Success Probability: {results.success_probability['positive_return']:.1%}")

    # Plot results
    plot_simulation_results(results, "Basic Monte Carlo Simulation",
                          "example1_basic_simulation.png")

    return results


async def example_vectorbt_acceleration():
    """Example 2: VectorBT accelerated simulation"""
    print("\n" + "="*60)
    print("EXAMPLE 2: VectorBT Accelerated Simulation")
    print("="*60)

    # Generate test data
    returns = generate_realistic_returns(days=252, mu=0.001, sigma=0.02)

    # Try VectorBT simulation
    try:
        # Create price data for VectorBT
        prices = (1 + returns).cumprod() * 100000
        price_df = pd.DataFrame({'close': prices})

        # Create VectorBT Monte Carlo instance
        vbt_mc = VectorBTMonteCarlo(price_df)

        # Generate paths using VectorBT
        n_paths = 5000
        n_steps = 252
        paths = vbt_mc.generate_paths_vectorized(
            n_paths=n_paths,
            n_steps=n_steps,
            method='geometric_brownian'
        )

        print(f"\nVectorBT Results:")
        print(f"  Generated {n_paths} paths with {n_steps} steps each")
        print(f"  Path shape: {paths.shape}")
        print(f"  All paths start at: ${paths[0, 0]:,.2f}")
        print(f"  Average final value: ${np.mean(paths[:, -1]):,.2f}")

        # Calculate risk metrics
        equity_curves = paths * 100000  # Scale to $100k initial capital
        risk_metrics = vbt_mc.calculate_risk_metrics_vectorized(equity_curves)

        print(f"\nRisk Metrics:")
        print(f"  Average VaR (95%): ${risk_metrics['var_95'].mean():,.2f}")
        print(f"  Average CVaR (95%): ${risk_metrics['cvar_95'].mean():,.2f}")
        print(f"  Average Sharpe Ratio: {risk_metrics['sharpe_ratio'].mean():.2f}")
        print(f"  Average Sortino Ratio: {risk_metrics['sortino_ratio'].mean():.2f}")

        # Plot sample paths
        plt.figure(figsize=(12, 6))
        sample_paths = paths[:100]
        for path in sample_paths:
            plt.plot(path, alpha=0.3, linewidth=0.5)

        percentiles = [5, 25, 50, 75, 95]
        for p in percentiles:
            percentile_path = np.percentile(paths, p, axis=0)
            plt.plot(percentile_path, linewidth=2, label=f'{p}th percentile')

        plt.title(f'VectorBT Monte Carlo Paths ({n_paths} simulations)')
        plt.xlabel('Days')
        plt.ylabel('Normalized Value')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('example2_vectorbt_paths.png', dpi=300, bbox_inches='tight')
        plt.show()

    except ImportError:
        print("VectorBT not installed. Skipping VectorBT example.")
        return None

    return paths


async def example_with_scenarios():
    """Example 3: Monte Carlo with scenario analysis"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Monte Carlo with Scenario Analysis")
    print("="*60)

    # Generate test data
    returns = generate_realistic_returns(days=252, mu=0.0008, sigma=0.015)

    # Define scenarios
    scenarios = [
        SimulationScenario(
            name="base_case",
            params={},
            description="Base case with historical parameters"
        ),
        SimulationScenario(
            name="market_crash",
            params={
                "mean_adjustment": -0.005,
                "volatility_multiplier": 3.0,
                "stress_events": [
                    {"start": "2023-06-01", "end": "2023-06-30", "adjustment": -0.02}
                ]
            },
            description="Market crash scenario with -50bp mean and 3x volatility"
        ),
        SimulationScenario(
            name="bull_market",
            params={
                "mean_adjustment": 0.002,
                "volatility_multiplier": 0.5
            },
            description="Bull market scenario with +20bp mean and 0.5x volatility"
        ),
        SimulationScenario(
            name="high_volatility",
            params={
                "volatility_multiplier": 5.0
            },
            description="High volatility regime with 5x normal volatility"
        )
    ]

    # Run simulation with scenarios
    results = await run_enhanced_monte_carlo(
        returns=returns,
        method=SimulationMethod.BOOTSTRAP,
        n_simulations=2000,
        time_horizon=252,
        initial_capital=100000,
        n_workers=4,
        scenarios=scenarios,
        enable_sensitivity_analysis=True
    )

    # Print scenario comparison
    print(f"\nScenario Analysis Results:")
    print(f"{'Scenario':<15} {'Mean Value':<12} {'Success %':<10} {'VaR 95%':<10}")
    print("-" * 50)

    for scenario_name, scenario_results in results.scenario_results.items():
        mean_val = scenario_results.statistics['mean']
        success = scenario_results.success_probability['positive_return'] * 100
        var_95 = scenario_results.var[0.95]
        print(f"{scenario_name:<15} ${mean_val:>9,.0f} {success:>9.1f}% ${var_95:>9,.0f}")

    # Plot scenario comparison
    plt.figure(figsize=(12, 8))

    # Subplot 1: Final value distributions
    ax1 = plt.subplot(2, 2, 1)
    for scenario_name, scenario_results in results.scenario_results.items():
        ax1.hist(scenario_results.final_values, bins=30, alpha=0.6,
                label=scenario_name.replace('_', ' ').title(), density=True)

    ax1.set_title('Final Value Distributions by Scenario')
    ax1.set_xlabel('Final Portfolio Value')
    ax1.set_ylabel('Density')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # Subplot 2: Success probabilities
    ax2 = plt.subplot(2, 2, 2)
    scenarios = list(results.scenario_results.keys())
    success_rates = [results.scenario_results[s].success_probability['positive_return'] * 100
                    for s in scenarios]
    colors = ['green' if sr > 50 else 'orange' if sr > 30 else 'red' for sr in success_rates]
    bars = ax2.bar(scenarios, success_rates, color=colors, alpha=0.7)
    ax2.set_ylabel('Success Rate (%)')
    ax2.set_title('Success Probability by Scenario')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')

    # Add percentage labels
    for bar, sr in zip(bars, success_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{sr:.1f}%', ha='center', va='bottom', fontsize=8)

    # Subplot 3: VaR comparison
    ax3 = plt.subplot(2, 2, 3)
    var_95_values = [results.scenario_results[s].var[0.95] for s in scenarios]
    ax3.bar(scenarios, var_95_values, alpha=0.7, color='red')
    ax3.set_ylabel('VaR at 95% ($)')
    ax3.set_title('Value at Risk Comparison')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')

    # Subplot 4: Sensitivity results
    ax4 = plt.subplot(2, 2, 4)
    if results.sensitivity_results and results.sensitivity_results.sensitivities:
        for param, data in results.sensitivity_results.sensitivities.items():
            if 'param_values' in data and 'final_values' in data:
                ax4.plot(data['param_values'], data['final_values'],
                        marker='o', label=param.replace('_', ' ').title())
        ax4.set_xlabel('Parameter Value')
        ax4.set_ylabel('Mean Final Value')
        ax4.set_title('Sensitivity Analysis')
        ax4.legend(fontsize=8)
        ax4.grid(True, alpha=0.3)
    else:
        ax4.text(0.5, 0.5, 'Sensitivity Analysis\nNot Available',
                ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Sensitivity Analysis')

    plt.tight_layout()
    plt.savefig('example3_scenario_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    return results


async def example_portfolio_optimization():
    """Example 4: Portfolio optimization with Monte Carlo"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Portfolio Optimization with Monte Carlo")
    print("="*60)

    # Generate multi-asset returns
    np.random.seed(42)
    n_assets = 4
    n_days = 252

    # Create correlated returns
    returns_data = np.random.multivariate_normal(
        mean=[0.0008, 0.0010, 0.0006, 0.0012],
        cov=[
            [0.000225, 0.000100, 0.000050, 0.000075],
            [0.000100, 0.000400, 0.000060, 0.000090],
            [0.000050, 0.000060, 0.000144, 0.000048],
            [0.000075, 0.000090, 0.000048, 0.000256]
        ],
        size=n_days
    )

    returns_df = pd.DataFrame(
        returns_data,
        columns=['Stock_A', 'Stock_B', 'Bond_A', 'Bond_B'],
        index=pd.date_range(start='2023-01-01', periods=n_days, freq='D')
    )

    # Convert to prices for VectorBT
    prices = (1 + returns_df).cumprod()
    price_df = pd.DataFrame({
        'open': prices.iloc[:, 0],  # Use first asset as reference
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices.iloc[:, 0],
        'volume': 10000
    })

    try:
        # Create VectorBT Monte Carlo for portfolio optimization
        vbt_mc = VectorBTMonteCarlo(price_df)

        # Run portfolio optimization
        opt_results = vbt_mc.portfolio_optimization_monte_carlo(
            returns=returns_df,
            n_simulations=10000,
            risk_free_rate=0.02
        )

        # Print optimization results
        print(f"\nPortfolio Optimization Results:")
        print(f"\nOptimal Sharpe Ratio Portfolio:")
        print(f"  Expected Annual Return: {opt_results['optimal_sharpe']['return']:.2%}")
        print(f"  Annual Volatility: {opt_results['optimal_sharpe']['volatility']:.2%}")
        print(f"  Sharpe Ratio: {opt_results['optimal_sharpe']['sharpe_ratio']:.2f}")
        print(f"  Weights:")
        for asset, weight in zip(returns_df.columns, opt_results['optimal_sharpe']['weights']):
            print(f"    {asset}: {weight:.2%}")

        print(f"\nMinimum Variance Portfolio:")
        print(f"  Expected Annual Return: {opt_results['minimum_variance']['return']:.2%}")
        print(f"  Annual Volatility: {opt_results['minimum_variance']['volatility']:.2%}")
        print(f"  Sharpe Ratio: {opt_results['minimum_variance']['sharpe_ratio']:.2f}")
        print(f"  Weights:")
        for asset, weight in zip(returns_df.columns, opt_results['minimum_variance']['weights']):
            print(f"    {asset}: {weight:.2%}")

        # Plot efficient frontier
        plt.figure(figsize=(12, 6))
        plt.scatter(opt_results['all_volatilities'], opt_results['all_returns'],
                   c=opt_results['all_sharpe_ratios'], cmap='viridis', alpha=0.5, s=1)
        plt.colorbar(label='Sharpe Ratio')

        # Mark optimal portfolios
        plt.scatter(opt_results['optimal_sharpe']['volatility'],
                   opt_results['optimal_sharpe']['return'],
                   marker='*', s=200, color='red', label='Max Sharpe')
        plt.scatter(opt_results['minimum_variance']['volatility'],
                   opt_results['minimum_variance']['return'],
                   marker='*', s=200, color='blue', label='Min Variance')

        plt.xlabel('Annual Volatility')
        plt.ylabel('Annual Return')
        plt.title('Monte Carlo Portfolio Optimization - Efficient Frontier')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('example4_portfolio_optimization.png', dpi=300, bbox_inches='tight')
        plt.show()

    except ImportError:
        print("VectorBT not installed. Skipping portfolio optimization example.")
        return None

    return opt_results


async def main():
    """Run all examples"""
    print("Enhanced Monte Carlo Simulation System Examples")
    print("=" * 60)

    # Example 1: Basic simulation
    results1 = await example_basic_simulation()

    # Example 2: VectorBT acceleration
    results2 = await example_vectorbt_acceleration()

    # Example 3: Scenario analysis
    results3 = await example_with_scenarios()

    # Example 4: Portfolio optimization
    results4 = await example_portfolio_optimization()

    # Generate comprehensive report for Example 1
    if results1:
        report = generate_monte_carlo_report(results1)
        print("\n" + "="*60)
        print("COMPREHENSIVE REPORT FOR EXAMPLE 1")
        print("="*60)
        print(f"\nExecutive Summary:")
        for key, value in report['executive_summary'].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        print(f"\nRisk Analysis:")
        for key, value in report['risk_analysis'].items():
            if isinstance(value, (int, float)):
                print(f"  {key.replace('_', ' ').title()}: ${value:,.2f}")

    print("\n" + "="*60)
    print("All examples completed successfully!")
    print("="*60)


if __name__ == '__main__':
    # Run all examples
    asyncio.run(main())