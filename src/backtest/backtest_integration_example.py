"""
Advanced Backtest System Integration Example
==========================================

This example demonstrates how to use all the enhanced backtesting features together:
- Vectorized backtest engine
- Advanced Monte Carlo simulation
- Transaction cost modeling
- Portfolio optimization
- Performance attribution analysis
- Parallel processing
- Visualization reports
- Parameter optimization

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

# Import enhanced backtest modules
try:
    from .enhanced_backtest_engine import EnhancedBacktestEngine, BacktestConfig, BacktestMode
    from .vectorized_backtest_engine import VectorizedBacktestEngine, VectorizedBacktestMode, PortfolioConfig
    from .transaction_cost_model import TransactionCostModel, create_default_cost_config
    from .advanced_monte_carlo import AdvancedMonteCarlo, AdvancedMCConfig, create_stress_scenarios
    from .portfolio_optimizer import PortfolioOptimizer, create_optimization_config
    from .performance_attribution_analyzer import PerformanceAttributionAnalyzer, create_attribution_config
    from .parallel_processor_new import ParallelProcessor, create_parallel_config
    from .visualization_reports import BacktestVisualizer, ReportGenerator
    from .parameter_optimizer import ParameterOptimizer, create_optimization_config, create_parameter_space
except ImportError as e:
    logging.error(f"Failed to import backtest modules: {e}")
    raise

logger = logging.getLogger(__name__)


class AdvancedBacktestSystem:
    """
    Integrated advanced backtest system combining all enhanced features
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize advanced backtest system

        Args:
            config: Backtest configuration
        """
        self.config = config or BacktestConfig(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=1000000,
            enable_risk_management=True,
            enable_dynamic_adjustments=True,
            enable_stress_testing=True
        )

        # Initialize components
        self.vectorized_engine = None
        self.cost_model = None
        self.monte_carlo = None
        self.portfolio_optimizer = None
        self.attribution_analyzer = None
        self.parallel_processor = None
        self.visualizer = None
        self.parameter_optimizer = None

        logger.info("Advanced backtest system initialized")

    def generate_sample_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        n_assets: int = 5
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate sample price and returns data

        Args:
            symbols: List of symbols to generate data for
            start_date: Start date
            end_date: End date
            n_assets: Number of assets if not using symbols

        Returns:
            Tuple of (prices DataFrame, returns DataFrame)
        """
        # Use provided symbols or generate generic ones
        if not symbols:
            symbols = [f'Asset_{i}' for i in range(n_assets)]

        # Create date range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        n_days = len(dates)

        # Generate correlated random returns
        np.random.seed(42)
        correlation_matrix = np.random.uniform(0.2, 0.8, (len(symbols), len(symbols)))
        np.fill_diagonal(correlation_matrix, 1.0)

        # Ensure correlation matrix is positive semi-definite
        eigenvals, eigenvects = np.linalg.eigh(correlation_matrix)
        eigenvals = np.maximum(eigenvals, 0.1)
        correlation_matrix = eigenvects @ np.diag(eigenvals) @ eigenvects.T

        # Generate returns with correlation
        volatilities = np.random.uniform(0.15, 0.4, len(symbols))
        chol_matrix = np.linalg.cholesky(correlation_matrix)
        correlated_returns = np.random.randn(n_days, len(symbols)) @ chol_matrix.T
        scaled_returns = correlated_returns * volatilities

        # Add drift
        drift = np.random.uniform(0.0001, 0.001, len(symbols))
        scaled_returns += drift

        # Create returns DataFrame
        returns = pd.DataFrame(
            scaled_returns,
            index=dates,
            columns=symbols
        )

        # Generate prices from returns
        prices = (1 + returns).cumprod()
        prices = prices * 100  # Start at 100

        return prices, returns

    def run_comprehensive_backtest(
        self,
        symbols: List[str],
        strategy_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive backtest with all advanced features

        Args:
            symbols: List of symbols to backtest
            strategy_func: Strategy function (optional)

        Returns:
            Dictionary with all results
        """
        logger.info("Starting comprehensive backtest")

        results = {}

        # 1. Generate data
        prices, returns = self.generate_sample_data(symbols, self.config.start_date, self.config.end_date)
        results['data'] = {'prices': prices, 'returns': returns}

        # 2. Initialize vectorized engine
        self._initialize_vectorized_engine()
        results['vectorized_backtest'] = self._run_vectorized_backtest(prices, returns, strategy_func)

        # 3. Transaction cost analysis
        results['transaction_costs'] = self._analyze_transaction_costs(results['vectorized_backtest'])

        # 4. Monte Carlo simulation
        results['monte_carlo'] = self._run_monte_carlo_simulation(returns)

        # 5. Portfolio optimization
        results['portfolio_optimization'] = self._run_portfolio_optimization(returns)

        # 6. Performance attribution
        results['performance_attribution'] = self._run_performance_attribution(returns)

        # 7. Parameter optimization
        results['parameter_optimization'] = self._run_parameter_optimization(returns)

        # 8. Generate visualizations
        results['visualizations'] = self._generate_visualizations(results)

        # 9. Generate reports
        results['reports'] = self._generate_reports(results)

        logger.info("Comprehensive backtest completed successfully")
        return results

    def _initialize_vectorized_engine(self) -> None:
        """Initialize vectorized backtest engine"""
        self.vectorized_engine = VectorizedBacktestEngine(self.config)

        # Initialize transaction cost model
        cost_config = create_default_cost_config()
        cost_config.commission_model = 'percentage'
        cost_config.slippage_model = 'square_root'
        self.cost_model = TransactionCostModel(cost_config)

    def _run_vectorized_backtest(
        self,
        prices: pd.DataFrame,
        returns: pd.DataFrame,
        strategy_func: Optional[Callable]
    ) -> Dict[str, Any]:
        """Run vectorized backtest"""
        logger.info("Running vectorized backtest")

        # Create portfolio config
        portfolio_config = PortfolioConfig(
            assets=prices.columns.tolist(),
            rebalance_frequency="monthly",
            optimization_method="mean_variance",
            risk_free_rate=0.02
        )

        # Define default strategy if not provided
        if strategy_func is None:
            def default_strategy(prices, returns_data, portfolio_cfg):
                # Simple momentum strategy
                lookback = 20
                weights = {}

                for asset in prices.columns:
                    # Simple momentum signal
                    momentum = (prices[asset] / prices[asset].shift(20) - 1).iloc[-1]
                    if momentum > 0:
                        weights[asset] = min(0.3, momentum * 10)  # Cap at 30%
                    else:
                        weights[asset] = 0

                # Normalize weights
                total_weight = sum(weights.values())
                if total_weight > 0:
                    weights = {k: v / total_weight for k, v in weights.items()}

                return weights

            strategy_func = default_strategy

        # Load data
        self.vectorized_engine.load_data(prices)

        # Run backtest
        result = self.vectorized_engine.run_vectorized_backtest(
            strategy=strategy_func,
            mode=VectorizedBacktestMode.MULTI_ASSET,
            portfolio_config=portfolio_config
        )

        return {
            'result': result,
            'equity_curve': result.equity_curve,
            'returns': result.returns,
            'total_return': result.total_return,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown
        }

    def _analyze_transaction_costs(self, backtest_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transaction costs"""
        logger.info("Analyzing transaction costs")

        # This is a simplified implementation
        # In practice, you would extract actual trades from the backtest

        # Simulate some trades
        trades = []
        n_trades = 100
        for i in range(n_trades):
            trade = {
                'symbol': np.random.choice(self.config.symbols) if hasattr(self.config, 'symbols') else f'Asset_{i%5}',
                'quantity': np.random.choice([-1, 1]) * 100,
                'price': 100 + np.random.randn() * 5,
                'timestamp': pd.Timestamp.now() + timedelta(days=i),
                'volume': np.random.randint(1000, 10000)
            }
            trades.append(trade)

        # Convert to Trade objects
        from .transaction_cost_model import Trade
        trade_objects = []
        for trade in trades:
            trade_obj = Trade(
                timestamp=trade['timestamp'],
                symbol=trade['symbol'],
                side='buy' if trade['quantity'] > 0 else 'sell',
                quantity=abs(trade['quantity']),
                price=trade['price'],
                volume=trade['volume'],
                bid_ask_spread=trade['price'] * 0.001,
                volatility=0.02,
                mid_price=trade['price']
            )
            trade_objects.append(trade_obj)

        # Calculate costs
        cost_analysis = self.cost_model.calculate_portfolio_costs(
            trades=trade_objects,
            positions=pd.DataFrame(),  # Would extract from backtest
            prices=backtest_result['data']['prices'] if 'data' in backtest_result else None,
            current_prices={},
            holding_period=0.25  # Quarter
        )

        return {
            'cost_breakdown': cost_analysis,
            'total_cost': cost_analysis['total_costs'],
            'cost_per_trade': cost_analysis['total_costs'] / len(trades)
        }

    def _run_monte_carlo_simulation(self, returns: pd.DataFrame) -> Dict[str, Any]:
        """Run Monte Carlo simulation"""
        logger.info("Running Monte Carlo simulation")

        # Configure Monte Carlo
        mc_config = AdvancedMCConfig(
            simulation_method='bootstrap',
            n_simulations=5000,  # Reduced for example
            time_horizon=252,
            generate_reports=True
        )

        # Create Monte Carlo engine
        self.monte_carlo = AdvancedMonteCarlo(mc_config)

        # Create scenarios
        scenarios = create_stress_scenarios()

        # Run simulation
        mc_results = self.monte_carlo.run_simulation(returns, scenarios=scenarios)

        return {
            'base_results': mc_results['base_results'],
            'scenario_results': mc_results['scenario_results'],
            'combined_results': mc_results['combined_results'],
            'summary': mc_results['reports']['summary'] if 'reports' in mc_results else {}
        }

    def _run_portfolio_optimization(self, returns: pd.DataFrame) -> Dict[str, Any]:
        """Run portfolio optimization"""
        logger.info("Running portfolio optimization")

        # Configure optimizer
        opt_config = create_optimization_config(
            method='mean_variance',
            target_volatility=0.15,
            max_weight=0.3,
            min_weight=0.0
        )

        # Create optimizer
        self.portfolio_optimizer = PortfolioOptimizer(opt_config)

        # Run optimization
        self.portfolio_optimizer.fit(returns)
        optimal_weights = self.portfolio_optimizer.optimize()

        # Calculate metrics
        metrics = self.portfolio_optimizer.get_portfolio_metrics()

        return {
            'optimal_weights': optimal_weights.to_dict(),
            'metrics': metrics,
            'risk_contributions': self.portfolio_optimizer.get_risk_contributions().to_dict(),
            'effective_assets': self.portfolio_optimizer.get_effective_assets()
        }

    def _run_performance_attribution(self, returns: pd.DataFrame) -> Dict[str, Any]:
        """Run performance attribution analysis"""
        logger.info("Running performance attribution")

        # Configure attribution
        attr_config = create_attribution_config(
            method='brinson_fachler',
            frequency='monthly'
        )

        # Create analyzer
        self.attribution_analyzer = PerformanceAttributionAnalyzer(attr_config)

        # Generate sample weights for demonstration
        n_periods = len(returns)
        portfolio_weights = pd.DataFrame(
            np.random.dirichlet(np.ones(len(returns.columns)), size=(n_periods // 30, len(returns.columns))),
            index=returns.index[::30],
            columns=returns.columns
        )
        benchmark_weights = pd.DataFrame(
            np.ones(len(returns.columns)) / len(returns.columns),
            index=portfolio_weights.index,
            columns=portfolio_weights.columns
        )

        # Run attribution
        attribution_result = self.attribution_analyzer.analyze(
            returns,
            portfolio_weights,
            benchmark_weights,
            returns
        )

        return {
            'total_return': attribution_result.total_return,
            'benchmark_return': attribution_result.benchmark_return,
            'active_return': attribution_result.active_return,
            'allocation_effect': attribution_result.allocation_effect,
            'selection_effect': attribution_result.selection_effect,
            'interaction_effect': attribution_result.interaction_effect,
            'summary': self.attribution_analyzer.get_attribution_summary()
        }

    def _run_parameter_optimization(self, returns: pd.DataFrame) -> Dict[str, Any]:
        """Run parameter optimization"""
        logger.info("Running parameter optimization")

        # Configure optimizer
        opt_config = create_optimization_config(
            method='random_search',
            objective_type='maximize_sharpe',
            max_iterations=50  # Reduced for example
        )

        # Create optimizer
        self.parameter_optimizer = ParameterOptimizer(opt_config)

        # Define parameter space for strategy optimization
        self.parameter_optimizer.add_parameter(
            create_parameter_space(
                name='lookback_window',
                param_type='discrete',
                bounds=(10, 60)
            )
        )

        self.parameter_optimizer.add_parameter(
            create_parameter_space(
                name='momentum_threshold',
                param_type='continuous',
                bounds=(0.01, 0.10)
            )
        )

        self.parameter_optimizer.add_parameter(
            create_parameter_space(
                name='volatility_target',
                param_type='continuous',
                bounds=(0.10, 0.30)
            )
        )

        # Define objective function
        def objective_func(params, data):
            # Simplified objective function
            lookback = int(params['lookback_window'])
            threshold = params['momentum_threshold']
            vol_target = params['volatility_target']

            # Calculate strategy performance (simplified)
            returns_rolling = returns.rolling(window=lookback).mean()
            positions = (returns_rolling > threshold).astype(int)
            strategy_returns = (positions.shift(1) * returns).sum(axis=1)

            # Calculate metrics
            mean_return = strategy_returns.mean() * 252
            volatility = strategy_returns.std() * np.sqrt(252)
            sharpe = mean_return / volatility if volatility > 0 else 0

            # Penalty for volatility deviation from target
            vol_penalty = abs(volatility - vol_target) * 0.5

            return sharpe - vol_penalty

        # Run optimization
        optimization_result = self.parameter_optimizer.optimize(objective_func, returns)

        return {
            'best_params': optimization_result.best_params,
            'best_score': optimization_result.best_score,
            'optimization_history': optimization_result.optimization_history
        }

    def _generate_visualizations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualizations"""
        logger.info("Generating visualizations")

        # Initialize visualizer
        viz_config = {
            'theme': 'plotly_white',
            'interactive': True
        }
        self.visualizer = BacktestVisualizer(viz_config)

        visualizations = {}

        # Equity curve
        if 'vectorized_backtest' in results:
            visualizations['equity_curve'] = self.visualizer.create_equity_curve(
                results['vectorized_backtest']['equity_curve'],
                title="Portfolio Equity Curve"
            )

        # Drawdown
        if 'vectorized_backtest' in results:
            visualizations['drawdown'] = self.visualizer.create_drawdown_chart(
                results['vectorized_backtest']['equity_curve'],
                title="Portfolio Drawdown"
            )

        # Returns distribution
        if 'vectorized_backtest' in results:
            visualizations['returns_dist'] = self.visualizer.create_returns_distribution(
                results['vectorized_backtest']['returns'],
                title="Returns Distribution"
            )

        # Monte Carlo results
        if 'monte_carlo' in results and 'combined_results' in results['monte_carlo']:
            visualizations['monte_carlo'] = self.visualizer.create_monte_carlo_results(
                results['monte_carlo']['combined_results'].equity_curves,
                title="Monte Carlo Simulation Results"
            )

        # Performance attribution
        if 'performance_attribution' in results:
            visualizations['attribution'] = self.visualizer.create_performance_attribution(
                {
                    'Total': results['performance_attribution'].get('allocation_effect', {}),
                    'Selection': results['performance_attribution'].get('selection_effect', {}),
                    'Interaction': results['performance_attribution'].get('interaction_effect', {})
                },
                title="Performance Attribution"
            )

        return {
            'figures': visualizations,
            'html': {name: fig.to_html(include_plotlyjs='cdn') for name, fig in visualizations.items()}
        }

    def _generate_reports(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive reports"""
        logger.info("Generating reports")

        # Initialize report generator
        report_config = {
            'title': 'Advanced Backtest Analysis Report',
            'subtitle': 'Comprehensive analysis using enhanced backtesting features',
            'author': 'CBS-C Quant Team',
            'include_summary': True,
            'include_performance': True,
            'include_risk_analysis': True,
            'format': 'interactive_html'
        }
        report_generator = ReportGenerator(report_config)

        # Generate HTML report
        html_report = report_generator.generate_html_report(
            results=results,
            figures=self.visualizer.figures if self.visualizer else {},
            output_path='reports/backtest_report.html'
        )

        return {
            'html_report': html_report,
            'html_path': 'reports/backtest_report.html'
        }


def run_example():
    """Run example of advanced backtest system"""
    print("=" * 60)
    print("Advanced Backtest System Example")
    print("=" * 60)

    # Initialize system
    backtest_system = AdvancedBacktestSystem()

    # Define symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

    # Run comprehensive backtest
    results = backtest_system.run_comprehensive_backtest(symbols)

    # Print summary
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 60)

    if 'vectorized_backtest' in results:
        print(f"Total Return: {results['vectorized_backtest']['total_return']:.2%}")
        print(f"Sharpe Ratio: {results['vectorized_backtest']['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['vectorized_backtest']['max_drawdown']:.2%}")

    if 'monte_carlo' in results and 'summary' in results['monte_carlo']:
        print(f"\nMonte Carlo Mean Return: {results['monte_carlo']['summary'].get('mean_final_value', 0):,.0f}")
        print(f"Monte Carlo 5% VaR: {results['monte_carlo']['summary'].get('var_95', 0):,.2f}")

    if 'portfolio_optimization' in results:
        print(f"\nOptimal Portfolio:")
        for asset, weight in results['portfolio_optimization']['optimal_weights'].items():
            print(f"  {asset}: {weight:.2%}")

    if 'parameter_optimization' in results:
        print(f"\nOptimized Parameters:")
        for param, value in results['parameter_optimization']['best_params'].items():
            print(f"  {param}: {value}")

    if 'transaction_costs' in results:
        print(f"\nTransaction Costs: ${results['transaction_costs']['total_cost']:,.2f}")
        print(f"Cost per Trade: ${results['transaction_costs']['cost_per_trade']:,.2f}")

    print("\n" + "=" * 60)
    print("Reports generated in 'reports/' directory")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_example()