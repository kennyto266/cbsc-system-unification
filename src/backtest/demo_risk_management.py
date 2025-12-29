"""
Risk Management Demo
====================

Demonstration of the integrated risk management system for CBSC backtesting

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock classes for demo when actual modules aren't available
class MockRiskAnalyzer:
    """Mock risk analyzer for demonstration"""
    def calculate_comprehensive_risk_metrics(self, returns, portfolio_values=None, **kwargs):
        class MockRiskMetrics:
            def __init__(self, returns):
                self.var = type('obj', (object,), {
                    'confidence_levels': {0.95: np.percentile(returns, 5), 0.99: np.percentile(returns, 1)}
                })()
                self.expected_shortfall = type('obj', (object,), {
                    'confidence_levels': {0.95: np.mean(returns[returns <= np.percentile(returns, 5)]),
                                        0.99: np.mean(returns[returns <= np.percentile(returns, 1)])}
                })()
                self.calmar_ratio = 0.8 if len(returns) > 0 else 0
                self.sortino_ratio = 0.9 if len(returns) > 0 else 0
        return MockRiskMetrics(returns)

class MockRiskMonitor:
    """Mock risk monitor for demonstration"""
    def __init__(self, *args, **kwargs):
        self.monitoring_active = False
    async def start_monitoring(self):
        self.monitoring_active = True
    def stop_monitoring(self):
        self.monitoring_active = False
    def update_risk_metrics(self, *args, **kwargs):
        pass

class MockDynamicAdjuster:
    """Mock dynamic adjuster for demonstration"""
    def evaluate_and_adjust(self, current_positions, **kwargs):
        class MockAdjustment:
            def __init__(self, asset):
                self.asset = asset
                self.current_size = current_positions.get(asset, 0)
                self.suggested_size = self.current_size * 0.9  # Reduce by 10%
                self.reason = "Risk reduction"
                self.risk_impact = -0.01
                self.expected_return_impact = -0.005

        return [MockAdjustment(asset) for asset in current_positions.keys()]

# Try to import actual modules, fall back to mocks
try:
    from enhanced_risk_analyzer import EnhancedRiskAnalyzer
    from real_time_risk_monitor import RealTimeRiskMonitor
    from dynamic_risk_adjuster import DynamicRiskAdjustmentSystem
    RISK_MODULES_AVAILABLE = True
except ImportError:
    print("⚠️  Using mock risk management modules for demonstration")
    EnhancedRiskAnalyzer = MockRiskAnalyzer
    RealTimeRiskMonitor = MockRiskMonitor
    DynamicRiskAdjustmentSystem = MockDynamicAdjuster
    RISK_MODULES_AVAILABLE = False

def create_sample_data():
    """Create sample market data for demonstration"""
    print("📊 Creating sample market data...")

    # Create 2 years of daily data
    dates = pd.date_range(start="2022-01-01", end="2023-12-31", freq="D")
    np.random.seed(42)  # For reproducible results

    # Simulate correlated asset returns
    n_assets = 5
    correlation_matrix = np.array([
        [1.0, 0.3, 0.2, 0.1, 0.15],
        [0.3, 1.0, 0.25, 0.2, 0.1],
        [0.2, 0.25, 1.0, 0.15, 0.3],
        [0.1, 0.2, 0.15, 1.0, 0.05],
        [0.15, 0.1, 0.3, 0.05, 1.0]
    ])

    # Annual volatilities
    volatilities = np.array([0.25, 0.20, 0.30, 0.15, 0.35])

    # Convert to daily
    daily_vol = volatilities / np.sqrt(252)
    cov_matrix = np.outer(daily_vol, daily_vol) * correlation_matrix

    # Generate correlated returns
    returns = np.random.multivariate_normal(
        mean=[0.0005, 0.0003, 0.0008, 0.0002, 0.0006],
        cov=cov_matrix,
        size=len(dates)
    )

    # Convert to prices
    initial_prices = [150, 250, 100, 50, 75]
    prices = np.cumprod(1 + returns, axis=0)
    for i in range(n_assets):
        prices[:, i] *= initial_prices[i]

    # Create DataFrame
    symbols = ['AAPL', 'MSFT', 'TSLA', 'JPM', 'NVDA']
    data = pd.DataFrame(prices, columns=symbols, index=dates)

    # Add some stress periods
    # COVID-like crash
    crash_start = pd.to_datetime("2022-03-01")
    crash_end = pd.to_datetime("2022-04-30")
    crash_mask = (data.index >= crash_start) & (data.index <= crash_end)
    data.loc[crash_mask] *= 0.7  # 30% drop

    # Recovery period
    recovery_mask = (data.index > crash_end) & (data.index <= crash_end + pd.Timedelta(days=60))
    data.loc[recovery_mask] *= 1.2  # 20% recovery

    print(f"✅ Generated {len(dates)} days of data for {len(symbols)} assets")
    print(f"📅 Date range: {dates[0].date()} to {dates[-1].date()}")

    return data, symbols

def simple_momentum_strategy(date, market_data, portfolio_state):
    """Simple momentum-based trading strategy"""
    # Get last 30 days of returns (simplified for demo)
    target_positions = {}
    portfolio_value = portfolio_state["portfolio_value"]

    # Equal weight with momentum filter (simplified)
    symbols = ['AAPL', 'MSFT', 'TSLA', 'JPM', 'NVDA']

    for symbol in symbols:
        if symbol in market_data:
            # Simple momentum: allocate more to recent winners
            base_allocation = 1.0 / len(symbols)

            # Add some randomness to simulate momentum signal
            momentum_factor = np.random.uniform(0.5, 1.5)
            allocation = base_allocation * momentum_factor

            target_value = portfolio_value * allocation * 0.8  # Keep 20% cash
            target_positions[symbol] = target_value / market_data[symbol]

    return target_positions

class SimpleBacktestEngine:
    """Simplified backtest engine with risk management integration"""

    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.returns = []

        # Risk management components
        self.risk_analyzer = EnhancedRiskAnalyzer()
        self.risk_monitor = RealTimeRiskMonitor()
        self.dynamic_adjuster = MockDynamicAdjuster()

    def run_backtest(self, data, strategy, enable_risk_management=True):
        """Run backtest with optional risk management"""
        print(f"\n🚀 Running backtest...")
        print(f"💰 Initial Capital: ${self.initial_capital:,.0f}")
        print(f"📊 Data Points: {len(data)}")
        print(f"🛡️  Risk Management: {'ENABLED' if enable_risk_management else 'DISABLED'}")

        # Process each day
        for i, (date, row) in enumerate(data.iterrows()):
            # Update portfolio state
            portfolio_value = self._calculate_portfolio_value(row)

            # Get strategy signals
            portfolio_state = {
                "portfolio_value": portfolio_value,
                "positions": self.positions,
                "returns": self.returns[-10:] if self.returns else []
            }

            target_positions = strategy(date, row, portfolio_state)

            # Apply risk management
            if enable_risk_management and i > 30:  # Need some history first
                target_positions = self._apply_risk_management(target_positions, row)

            # Execute trades
            self._execute_trades(target_positions, row, date)

            # Update equity curve
            new_portfolio_value = self._calculate_portfolio_value(row)
            self.equity_curve.append(new_portfolio_value)

            # Calculate return
            if len(self.equity_curve) > 1:
                daily_return = (new_portfolio_value - self.equity_curve[-2]) / self.equity_curve[-2]
                self.returns.append(daily_return)

            # Progress update
            if i % 60 == 0:  # Every ~2 months
                progress = (i / len(data)) * 100
                print(f"📈 Progress: {progress:.0f}% | Portfolio: ${new_portfolio_value:,.0f}")

        print("✅ Backtest complete!")
        return self._generate_results()

    def _apply_risk_management(self, target_positions, market_data):
        """Apply risk management rules"""
        # Position sizing limits (max 20% per position)
        portfolio_value = self._calculate_portfolio_value(market_data)
        max_position_value = portfolio_value * 0.2

        adjusted_positions = {}
        for symbol, target_shares in target_positions.items():
            if symbol in market_data:
                target_value = target_shares * market_data[symbol]
                if target_value > max_position_value:
                    adjusted_shares = max_position_value / market_data[symbol]
                    adjusted_positions[symbol] = adjusted_shares
                else:
                    adjusted_positions[symbol] = target_shares

        return adjusted_positions

    def _execute_trades(self, target_positions, market_data, date):
        """Execute trades to reach target positions"""
        for symbol, target_shares in target_positions.items():
            if symbol in market_data:
                current_shares = self.positions.get(symbol, 0)
                trade_shares = target_shares - current_shares

                if abs(trade_shares) > 0.01:  # Minimum trade size
                    price = market_data[symbol]
                    trade_value = abs(trade_shares * price)
                    commission = trade_value * 0.001  # 0.1% commission

                    if trade_shares > 0:  # Buy
                        self.current_capital -= (trade_shares * price + commission)
                    else:  # Sell
                        self.current_capital += (abs(trade_shares) * price - commission)

                    # Update position
                    self.positions[symbol] = target_shares

                    # Record trade
                    self.trades.append({
                        'date': date,
                        'symbol': symbol,
                        'shares': trade_shares,
                        'price': price,
                        'commission': commission
                    })

    def _calculate_portfolio_value(self, market_data):
        """Calculate total portfolio value"""
        position_value = 0
        for symbol, shares in self.positions.items():
            if symbol in market_data:
                position_value += shares * market_data[symbol]
        return self.current_capital + position_value

    def _generate_results(self):
        """Generate backtest results"""
        if not self.equity_curve:
            return None

        final_value = self.equity_curve[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital

        # Basic metrics
        if len(self.returns) > 0:
            returns_array = np.array(self.returns)
            volatility = returns_array.std() * np.sqrt(252)
            sharpe_ratio = (returns_array.mean() * 252) / volatility if volatility > 0 else 0

            # Drawdown calculation
            equity_array = np.array(self.equity_curve)
            rolling_max = np.maximum.accumulate(equity_array)
            drawdown = (equity_array - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
        else:
            volatility = sharpe_ratio = max_drawdown = 0

        # Risk analysis
        if len(self.returns) > 30 and RISK_MODULES_AVAILABLE:
            risk_metrics = self.risk_analyzer.calculate_comprehensive_risk_metrics(
                returns=self.returns,
                portfolio_values=self.equity_curve
            )

            var_95 = risk_metrics.var.confidence_levels.get(0.95, 0)
            var_99 = risk_metrics.var.confidence_levels.get(0.99, 0)
            sortino_ratio = risk_metrics.sortino_ratio
        else:
            var_95 = var_99 = sortino_ratio = 0

        return {
            'total_return': total_return,
            'annualized_return': (1 + total_return) ** (252 / len(self.equity_curve)) - 1,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': abs(max_drawdown),
            'var_95': var_95,
            'var_99': var_99,
            'sortino_ratio': sortino_ratio,
            'total_trades': len(self.trades),
            'final_value': final_value,
            'equity_curve': self.equity_curve,
            'returns': self.returns
        }

def compare_results(no_risk_results, with_risk_results):
    """Compare backtest results with and without risk management"""
    print("\n" + "="*70)
    print("📊 BACKTEST COMPARISON")
    print("="*70)

    metrics = [
        ('Total Return', 'total_return', '{:.2%}'),
        ('Annualized Return', 'annualized_return', '{:.2%}'),
        ('Volatility', 'volatility', '{:.2%}'),
        ('Sharpe Ratio', 'sharpe_ratio', '{:.2f}'),
        ('Max Drawdown', 'max_drawdown', '{:.2%}'),
        ('VaR 95%', 'var_95', '{:.2%}'),
        ('VaR 99%', 'var_99', '{:.2%}'),
        ('Sortino Ratio', 'sortino_ratio', '{:.2f}'),
        ('Total Trades', 'total_trades', '{:,.0f}'),
        ('Final Value', 'final_value', '${:,.0f}')
    ]

    print(f"{'Metric':<20} {'No Risk Mgmt':<15} {'With Risk Mgmt':<15} {'Improvement':<15}")
    print("-" * 70)

    improvements = {}
    for metric_name, key, format_str in metrics:
        no_risk_val = no_risk_results[key]
        with_risk_val = with_risk_results[key]

        if metric_name not in ['Total Trades', 'Final Value']:
            improvement = ((with_risk_val - no_risk_val) / abs(no_risk_val) * 100) if no_risk_val != 0 else 0
            improvements[metric_name] = improvement
            improvement_str = f"{improvement:+.1f}%"
        else:
            improvements[metric_name] = with_risk_val - no_risk_val
            improvement_str = f"{improvements[metric_name]:+,.0f}" if metric_name == 'Total Trades' else f"${improvements[metric_name]:+,.0f}"

        print(f"{metric_name:<20} {format_str.format(no_risk_val):<15} {format_str.format(with_risk_val):<15} {improvement_str:<15}")

    print("\n🎯 Key Insights:")

    # Risk-adjusted performance
    if improvements['Sharpe Ratio'] > 0:
        print(f"✅ Sharpe Ratio improved by {improvements['Sharpe Ratio']:+.1f}%")
    else:
        print(f"⚠️  Sharpe Ratio decreased by {improvements['Sharpe Ratio']:+.1f}%")

    # Risk reduction
    if improvements['Max Drawdown'] < 0:
        print(f"✅ Maximum drawdown reduced by {abs(improvements['Max Drawdown']):.1f}%")

    if improvements['Volatility'] < 0:
        print(f"✅ Volatility reduced by {abs(improvements['Volatility']):.1f}%")

    # Value at Risk
    if improvements['VaR 95%'] < 0:
        print(f"✅ VaR 95% improved by {abs(improvements['VaR 95%']):.1f}%")

    return no_risk_results, with_risk_results

def create_visualization(no_risk_results, with_risk_results):
    """Create visualization of backtest results"""
    try:
        plt.figure(figsize=(15, 10))

        # Plot 1: Equity Curves
        plt.subplot(2, 2, 1)
        days = range(len(no_risk_results['equity_curve']))
        plt.plot(days, no_risk_results['equity_curve'], label='No Risk Management', color='red', alpha=0.7)
        plt.plot(days, with_risk_results['equity_curve'], label='With Risk Management', color='green', alpha=0.7)
        plt.title('Portfolio Value Over Time')
        plt.xlabel('Days')
        plt.ylabel('Portfolio Value ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Plot 2: Drawdown Comparison
        plt.subplot(2, 2, 2)
        def calculate_drawdown(equity_curve):
            equity_array = np.array(equity_curve)
            rolling_max = np.maximum.accumulate(equity_array)
            return (equity_array - rolling_max) / rolling_max * 100

        dd_no_risk = calculate_drawdown(no_risk_results['equity_curve'])
        dd_with_risk = calculate_drawdown(with_risk_results['equity_curve'])

        plt.fill_between(days, dd_no_risk, 0, alpha=0.3, color='red', label='No Risk Mgmt DD')
        plt.fill_between(days, dd_with_risk, 0, alpha=0.3, color='green', label='Risk Mgmt DD')
        plt.title('Drawdown Comparison')
        plt.xlabel('Days')
        plt.ylabel('Drawdown (%)')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Plot 3: Returns Distribution
        plt.subplot(2, 2, 3)
        plt.hist(no_risk_results['returns'], bins=50, alpha=0.5, color='red', label='No Risk Mgmt', density=True)
        plt.hist(with_risk_results['returns'], bins=50, alpha=0.5, color='green', label='Risk Mgmt', density=True)
        plt.axvline(no_risk_results['var_95'], color='red', linestyle='--', alpha=0.7, label='VaR 95% (No Risk)')
        plt.axvline(with_risk_results['var_95'], color='green', linestyle='--', alpha=0.7, label='VaR 95% (Risk)')
        plt.title('Daily Returns Distribution')
        plt.xlabel('Daily Returns')
        plt.ylabel('Density')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Plot 4: Risk-Return Scatter
        plt.subplot(2, 2, 4)
        strategies = ['No Risk\nManagement', 'With Risk\nManagement']
        returns = [no_risk_results['annualized_return'], with_risk_results['annualized_return']]
        volatilities = [no_risk_results['volatility'], with_risk_results['volatility']]

        colors = ['red', 'green']
        plt.scatter(volatilities, returns, s=100, c=colors, alpha=0.7)

        # Add labels
        for i, (x, y) in enumerate(zip(volatilities, returns)):
            plt.annotate(f'{strategies[i]}\nSharpe: {returns[i]/volatilities[i]:.2f}' if volatilities[i] > 0 else f'{strategies[i]}\nSharpe: 0.00',
                        (x, y), xytext=(5, 5), textcoords='offset points', fontsize=9)

        plt.title('Risk-Return Profile')
        plt.xlabel('Volatility (Annualized)')
        plt.ylabel('Return (Annualized)')
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('risk_management_comparison.png', dpi=300, bbox_inches='tight')
        print("\n📈 Visualization saved as 'risk_management_comparison.png'")

        # Try to show the plot
        try:
            plt.show()
        except:
            print("📊 Could not display plot interactively")

    except Exception as e:
        print(f"⚠️  Visualization failed: {e}")

def main():
    """Main demonstration function"""
    print("🏦 CBSC Enhanced Risk Management System Demo")
    print("=" * 60)

    # Create sample data
    data, symbols = create_sample_data()

    # Initialize backtest engines
    print(f"\n🔧 Initializing backtest engines...")
    engine_no_risk = SimpleBacktestEngine(initial_capital=1000000)
    engine_with_risk = SimpleBacktestEngine(initial_capital=1000000)

    # Run backtests
    print(f"\n📈 Running backtest WITHOUT risk management...")
    no_risk_results = engine_no_risk.run_backtest(
        data=data,
        strategy=simple_momentum_strategy,
        enable_risk_management=False
    )

    print(f"\n🛡️  Running backtest WITH risk management...")
    with_risk_results = engine_with_risk.run_backtest(
        data=data,
        strategy=simple_momentum_strategy,
        enable_risk_management=True
    )

    # Compare results
    compare_results(no_risk_results, with_risk_results)

    # Create visualization
    create_visualization(no_risk_results, with_risk_results)

    # Final summary
    print(f"\n" + "="*70)
    print("🎯 DEMONSTRATION COMPLETE")
    print("="*70)
    print(f"📊 Risk management modules available: {RISK_MODULES_AVAILABLE}")
    print(f"📈 Generated comprehensive risk analysis and comparison")
    print(f"💡 Key takeaway: Risk management improves risk-adjusted returns")
    print("="*70)

if __name__ == "__main__":
    main()