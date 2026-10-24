"""
Advanced Backtest Engine with Monte Carlo and Stress Testing

This module provides an advanced backtesting engine that integrates
Monte Carlo simulation and stress testing capabilities.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
import warnings
from concurrent.futures import ProcessPoolExecutor
import logging

from .enhanced_backtest_engine import EnhancedBacktestEngine
from .monte_carlo import MonteCarloSimulator, MCSimulationConfig, MCResults
from ..strategies.base_strategy import BaseStrategy
from ..data.data_loader import DataLoader


class AdvancedBacktestEngine(EnhancedBacktestEngine):
    """
    Advanced backtesting engine with Monte Carlo and stress testing
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize advanced backtest engine

        Args:
            *args: Arguments for EnhancedBacktestEngine
            **kwargs: Keyword arguments for EnhancedBacktestEngine
        """
        super().__init__(*args, **kwargs)
        self.mc_simulator = None
        self.logger = logging.getLogger(__name__)

    def run_with_monte_carlo(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        mc_config: Optional[MCSimulationConfig] = None,
        mc_method: str = 'bootstrap',
        parallel_mc: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run backtest with Monte Carlo simulation

        Args:
            strategy: Trading strategy to test
            data: Historical price data
            mc_config: Monte Carlo configuration
            mc_method: Simulation method ('bootstrap', 'parametric', 'gbm')
            parallel_mc: Use parallel processing for MC simulation
            **kwargs: Additional backtest parameters

        Returns:
            Dictionary containing backtest results and MC analysis
        """
        # First run standard backtest
        self.logger.info("Running standard backtest...")
        backtest_result = self.run_backtest(strategy, data, **kwargs)

        # Extract returns for Monte Carlo
        returns = self._extract_returns(backtest_result)

        if len(returns) < 30:
            self.logger.warning("Insufficient data for Monte Carlo simulation")
            return {
                'backtest': backtest_result,
                'monte_carlo': None,
                'warning': 'Insufficient data for Monte Carlo simulation'
            }

        # Configure Monte Carlo simulator
        if mc_config is None:
            mc_config = MCSimulationConfig(
                n_simulations=1000,
                time_horizon=len(returns),
                random_seed=42
            )

        self.mc_simulator = MonteCarloSimulator(mc_config)

        # Run Monte Carlo simulation
        self.logger.info(f"Running Monte Carlo simulation with {mc_method} method...")
        if parallel_mc:
            mc_results = self.mc_simulator.simulate_parallel(
                mc_method, returns, backtest_result.get('initial_capital', 100000)
            )
        else:
            if mc_method == 'bootstrap':
                mc_results = self.mc_simulator.simulate_bootstrap(
                    returns, backtest_result.get('initial_capital', 100000)
                )
            elif mc_method == 'parametric':
                mc_results = self.mc_simulator.simulate_parametric(
                    returns, backtest_result.get('initial_capital', 100000)
                )
            elif mc_method == 'gbm':
                mc_results = self.mc_simulator.simulate_geometric_brownian(
                    returns, backtest_result.get('initial_capital', 100000)
                )
            else:
                raise ValueError(f"Unknown Monte Carlo method: {mc_method}")

        # Generate Monte Carlo report
        mc_report = self.mc_simulator.generate_report(mc_results)

        # Combine results
        combined_results = {
            'backtest': backtest_result,
            'monte_carlo': {
                'results': mc_results,
                'report': mc_report,
                'config': mc_config.__dict__,
                'method': mc_method
            },
            'analysis': self._analyze_backtest_vs_monte_carlo(
                backtest_result, mc_results
            )
        }

        self.logger.info("Advanced backtest with Monte Carlo completed successfully")
        return combined_results

    def run_stress_test(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        stress_scenarios: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run stress testing scenarios

        Args:
            strategy: Trading strategy to test
            data: Historical price data
            stress_scenarios: List of stress scenarios to test
            **kwargs: Additional backtest parameters

        Returns:
            Dictionary containing stress test results
        """
        if stress_scenarios is None:
            stress_scenarios = self._default_stress_scenarios()

        # Run baseline backtest
        baseline_result = self.run_backtest(strategy, data, **kwargs)

        # Run stress scenarios
        stress_results = {}
        for scenario in stress_scenarios:
            self.logger.info(f"Running stress test: {scenario['name']}")
            modified_data = self._apply_stress_scenario(data, scenario)
            result = self.run_backtest(strategy, modified_data, **kwargs)
            stress_results[scenario['name']] = {
                'scenario': scenario,
                'result': result,
                'impact': self._calculate_stress_impact(baseline_result, result)
            }

        return {
            'baseline': baseline_result,
            'stress_tests': stress_results,
            'summary': self._summarize_stress_tests(baseline_result, stress_results)
        }

    def run_comprehensive_analysis(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        mc_config: Optional[MCSimulationConfig] = None,
        stress_scenarios: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run comprehensive analysis including backtest, Monte Carlo, and stress testing

        Args:
            strategy: Trading strategy to test
            data: Historical price data
            mc_config: Monte Carlo configuration
            stress_scenarios: List of stress scenarios
            **kwargs: Additional parameters

        Returns:
            Comprehensive analysis results
        """
        self.logger.info("Starting comprehensive strategy analysis...")

        # Run all analyses
        results = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy.__class__.__name__,
            'data_period': {
                'start': data.index[0].isoformat(),
                'end': data.index[-1].isoformat(),
                'total_days': len(data)
            }
        }

        # Standard backtest
        results['backtest'] = self.run_backtest(strategy, data, **kwargs)

        # Monte Carlo simulation
        try:
            results['monte_carlo'] = self.run_with_monte_carlo(
                strategy, data, mc_config, **kwargs
            )
        except Exception as e:
            self.logger.error(f"Monte Carlo simulation failed: {e}")
            results['monte_carlo'] = {'error': str(e)}

        # Stress testing
        try:
            results['stress_test'] = self.run_stress_test(
                strategy, data, stress_scenarios, **kwargs
            )
        except Exception as e:
            self.logger.error(f"Stress testing failed: {e}")
            results['stress_test'] = {'error': str(e)}

        # Overall assessment
        results['assessment'] = self._generate_overall_assessment(results)

        self.logger.info("Comprehensive analysis completed")
        return results

    def _extract_returns(self, backtest_result: Dict) -> pd.Series:
        """Extract returns from backtest result"""
        # Try to extract returns from different possible result formats
        if 'returns' in backtest_result:
            return backtest_result['returns']
        elif 'equity_curve' in backtest_result:
            equity = pd.Series(backtest_result['equity_curve'])
            return equity.pct_change().dropna()
        elif 'portfolio_value' in backtest_result:
            equity = pd.Series(backtest_result['portfolio_value'])
            return equity.pct_change().dropna()
        else:
            raise ValueError("Cannot extract returns from backtest result")

    def _default_stress_scenarios(self) -> List[Dict]:
        """Define default stress test scenarios"""
        return [
            {
                'name': 'market_crash',
                'description': 'Sudden 30% market drop',
                'type': 'price_shock',
                'magnitude': -0.30,
                'duration': 5
            },
            {
                'name': 'volatility_spike',
                'description': 'Volatility increases by 3x',
                'type': 'volatility_shock',
                'multiplier': 3.0,
                'duration': 20
            },
            {
                'name': 'bear_market',
                'description': 'Prolonged 40% decline over 3 months',
                'type': 'trend_shock',
                'trend': -0.005,  # Daily decline
                'duration': 60
            },
            {
                'name': 'liquidity_crisis',
                'description': 'Bid-ask spread widens by 10x',
                'type': 'liquidity_shock',
                'spread_multiplier': 10.0,
                'duration': 30
            },
            {
                'name': 'correlation_breakdown',
                'description': 'Assets become perfectly correlated',
                'type': 'correlation_shock',
                'target_correlation': 0.95
            }
        ]

    def _apply_stress_scenario(self, data: pd.DataFrame, scenario: Dict) -> pd.DataFrame:
        """Apply stress scenario to data"""
        stressed_data = data.copy()

        if scenario['type'] == 'price_shock':
            # Apply immediate price shock
            magnitude = scenario.get('magnitude', -0.20)
            price_columns = [col for col in data.columns if 'close' in col.lower() or 'price' in col.lower()]
            for col in price_columns:
                stressed_data[col] *= (1 + magnitude)

        elif scenario['type'] == 'volatility_shock':
            # Increase volatility
            multiplier = scenario.get('multiplier', 2.0)
            returns = stressed_data.pct_change()
            stressed_returns = returns * multiplier
            stressed_data = (1 + stressed_returns).cumprod() * stressed_data.iloc[0]

        elif scenario['type'] == 'trend_shock':
            # Apply trend
            trend = scenario.get('trend', -0.001)
            duration = scenario.get('duration', 30)
            for col in stressed_data.columns:
                if stressed_data[col].dtype in ['float64', 'int64']:
                    trend_factor = np.array([1 + trend] * min(duration, len(stressed_data)))
                    trend_factor = np.concatenate([trend_factor, [1] * (len(stressed_data) - duration)])
                    stressed_data[col] *= np.cumprod(trend_factor)

        elif scenario['type'] == 'liquidity_shock':
            # This would affect trading costs more than prices
            # For simplicity, we'll add some noise to simulate wider spreads
            multiplier = scenario.get('spread_multiplier', 5.0)
            noise = np.random.normal(0, 0.001 * multiplier, len(stressed_data))
            for col in stressed_data.columns:
                if stressed_data[col].dtype in ['float64', 'int64']:
                    stressed_data[col] *= (1 + noise)

        return stressed_data

    def _calculate_stress_impact(self, baseline: Dict, stressed: Dict) -> Dict:
        """Calculate impact of stress scenario"""
        baseline_metrics = baseline.get('metrics', {})
        stressed_metrics = stressed.get('metrics', {})

        impact = {}
        for metric in ['total_return', 'sharpe_ratio', 'max_drawdown', 'volatility']:
            if metric in baseline_metrics and metric in stressed_metrics:
                baseline_val = baseline_metrics[metric]
                stressed_val = stressed_metrics[metric]

                if baseline_val != 0:
                    pct_change = (stressed_val - baseline_val) / abs(baseline_val)
                else:
                    pct_change = stressed_val

                impact[metric] = {
                    'baseline': baseline_val,
                    'stressed': stressed_val,
                    'absolute_change': stressed_val - baseline_val,
                    'percent_change': pct_change
                }

        return impact

    def _summarize_stress_tests(self, baseline: Dict, stress_results: Dict) -> Dict:
        """Summarize stress test results"""
        summary = {
            'worst_scenario': None,
            'most_resilient_metric': None,
            'average_impact': {},
            'recommendations': []
        }

        impacts = {}
        for scenario_name, scenario_data in stress_results.items():
            scenario_impact = scenario_data.get('impact', {})
            for metric, impact_data in scenario_impact.items():
                if metric not in impacts:
                    impacts[metric] = []
                impacts[metric].append(impact_data.get('percent_change', 0))

        # Calculate average impacts
        for metric, changes in impacts.items():
            summary['average_impact'][metric] = np.mean(changes)

        # Find worst scenario
        worst_impact = float('inf')
        worst_scenario = None
        for scenario_name, scenario_data in stress_results.items():
            total_impact = sum(
                abs(impact.get('percent_change', 0))
                for impact in scenario_data.get('impact', {}).values()
            )
            if total_impact < worst_impact:
                worst_impact = total_impact
                worst_scenario = scenario_name

        summary['worst_scenario'] = worst_scenario

        # Generate recommendations
        for metric, avg_impact in summary['average_impact'].items():
            if avg_impact < -0.2:  # More than 20% degradation
                if metric == 'max_drawdown':
                    summary['recommendations'].append(
                        "Consider implementing stricter drawdown controls"
                    )
                elif metric == 'sharpe_ratio':
                    summary['recommendations'].append(
                        "Strategy may need risk adjustments for volatile periods"
                    )
                elif metric == 'volatility':
                    summary['recommendations'].append(
                        "Consider position sizing adjustments"
                    )

        return summary

    def _analyze_backtest_vs_monte_carlo(
        self,
        backtest_result: Dict,
        mc_results: MCResults
    ) -> Dict:
        """Analyze differences between backtest and Monte Carlo results"""
        backtest_return = backtest_result.get('metrics', {}).get('total_return', 0)
        backtest_final = backtest_result.get('initial_capital', 100000) * (1 + backtest_return)

        # Compare backtest final value with Monte Carlo distribution
        mc_mean = mc_results.statistics['mean']
        mc_median = mc_results.statistics['median']
        mc_std = mc_results.statistics['std']

        # Calculate percentiles
        percentiles = {}
        for p in [10, 25, 75, 90]:
            percentiles[f'p{p}'] = np.percentile(mc_results.final_values, p)

        # How does backtest compare to MC distribution?
        backtest_percentile = (mc_results.final_values < backtest_final).mean() * 100

        analysis = {
            'backtest_vs_mc_mean': (backtest_final - mc_mean) / mc_mean,
            'backtest_vs_mc_median': (backtest_final - mc_median) / mc_median,
            'backtest_percentile': backtest_percentile,
            'backtest_outlier': backtest_percentile < 5 or backtest_percentile > 95,
            'mc_distribution_stats': {
                'mean': mc_mean,
                'median': mc_median,
                'std': mc_std,
                'skewness': mc_results.statistics['skewness'],
                'kurtosis': mc_results.statistics['kurtosis']
            },
            'backtest_relative_position': {
                'above_mean': backtest_final > mc_mean,
                'above_median': backtest_final > mc_median,
                'within_1_std': abs(backtest_final - mc_mean) < mc_std,
                'within_2_std': abs(backtest_final - mc_mean) < 2 * mc_std
            },
            'percentile_comparison': percentiles
        }

        # Risk assessment
        if backtest_percentile > 80:
            analysis['assessment'] = "Backtest results appear unusually optimistic compared to Monte Carlo analysis"
        elif backtest_percentile < 20:
            analysis['assessment'] = "Backtest results appear unusually pessimistic compared to Monte Carlo analysis"
        else:
            analysis['assessment'] = "Backtest results are consistent with Monte Carlo expectations"

        return analysis

    def _generate_overall_assessment(self, results: Dict) -> Dict:
        """Generate overall assessment of strategy"""
        assessment = {
            'strategy': results.get('strategy', 'Unknown'),
            'overall_score': 0,
            'strengths': [],
            'weaknesses': [],
            'recommendations': [],
            'risk_level': 'Medium'
        }

        # Analyze backtest performance
        backtest = results.get('backtest', {})
        if 'metrics' in backtest:
            metrics = backtest['metrics']
            score = 0

            # Return analysis
            total_return = metrics.get('total_return', 0)
            if total_return > 0.20:
                score += 20
                assessment['strengths'].append("Strong positive returns")
            elif total_return < 0:
                score -= 20
                assessment['weaknesses'].append("Negative returns")

            # Sharpe ratio
            sharpe = metrics.get('sharpe_ratio', 0)
            if sharpe > 1.5:
                score += 20
                assessment['strengths'].append("Excellent risk-adjusted returns")
            elif sharpe < 0.5:
                score -= 10
                assessment['weaknesses'].append("Poor risk-adjusted returns")

            # Max drawdown
            max_dd = metrics.get('max_drawdown', 0)
            if max_dd < 0.10:
                score += 15
                assessment['strengths'].append("Low maximum drawdown")
            elif max_dd > 0.30:
                score -= 15
                assessment['weaknesses'].append("High maximum drawdown")
                assessment['risk_level'] = 'High'

            assessment['overall_score'] = max(0, min(100, score))

        # Monte Carlo analysis
        mc_data = results.get('monte_carlo', {})
        if 'analysis' in mc_data:
            mc_analysis = mc_data['analysis']
            if mc_analysis.get('backtest_outlier', False):
                assessment['weaknesses'].append(
                    "Backtest results may not be representative of expected performance"
                )

        # Stress test analysis
        stress_data = results.get('stress_test', {})
        if 'summary' in stress_data:
            stress_summary = stress_data['summary']
            if 'recommendations' in stress_summary:
                assessment['recommendations'].extend(stress_summary['recommendations'])

        # Default recommendations
        if not assessment['recommendations']:
            assessment['recommendations'] = [
                "Monitor strategy performance going forward",
                "Consider periodic rebalancing",
                "Maintain appropriate risk controls"
            ]

        return assessment

    def export_results(
        self,
        results: Dict,
        format: str = 'dict',
        include_plots: bool = False
    ) -> Union[Dict, str]:
        """
        Export analysis results in various formats

        Args:
            results: Analysis results to export
            format: Export format ('dict', 'json', 'excel')
            include_plots: Include plot visualizations

        Returns:
            Exported results
        """
        if format == 'dict':
            return results
        elif format == 'json':
            import json
            return json.dumps(results, indent=2, default=str)
        elif format == 'excel':
            # Export to Excel would require additional implementation
            raise NotImplementedError("Excel export not yet implemented")
        else:
            raise ValueError(f"Unsupported export format: {format}")


__all__ = [
    'AdvancedBacktestEngine'
]