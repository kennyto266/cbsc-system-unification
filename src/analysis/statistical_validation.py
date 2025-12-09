"""
Phase 2: Statistical Validation Framework with Bootstrap Confidence Intervals
Professional statistical validation for quantitative trading strategies
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy import special
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
import warnings
from sklearn.utils import resample
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import jarque_bera
from statsmodels.stats.multitest import multipletests
import arch
from arch.univariate import GARCH, EGARCH, TGARCH
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

@dataclass
class ValidationConfig:
    """Configuration for statistical validation"""
    bootstrap_samples: int = 10000
    confidence_levels: List[float] = field(default_factory=lambda: [0.90, 0.95, 0.99])
    random_seed: int = 42
    min_samples: int = 30
    max_samples: int = 10000
    parallel_jobs: int = 4
    significance_level: float = 0.05
    multiple_testing_correction: str = 'fdr_bh'  # 'bonferroni', 'fdr_bh', 'fdr_by'
    volatility_model: str = 'GARCH'  # 'GARCH', 'EGARCH', 'TGARCH'
    risk_free_rate: float = 0.02  # Annual risk-free rate

@dataclass
class BootstrapResult:
    """Result of bootstrap analysis"""
    statistic: float
    confidence_intervals: Dict[float, Tuple[float, float]]
    bias: float
    standard_error: float
    bootstrap_distribution: np.ndarray
    sample_size: int

@dataclass
class StatisticalTest:
    """Statistical test result"""
    test_name: str
    statistic: float
    p_value: float
    critical_value: Optional[float] = None
    is_significant: bool = False
    interpretation: str = ""
    assumptions: List[str] = field(default_factory=list)

@dataclass
class ValidationReport:
    """Comprehensive statistical validation report"""
    strategy_name: str
    symbol: str
    sample_size: int
    time_period: str
    bootstrap_results: Dict[str, BootstrapResult]
    statistical_tests: Dict[str, StatisticalTest]
    risk_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]
    assumption_checks: Dict[str, bool]
    recommendations: List[str]
    validation_timestamp: datetime
    overall_validity_score: float

class StatisticalValidationFramework:
    """Professional statistical validation framework for trading strategies"""

    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
        np.random.seed(self.config.random_seed)

    def validate_strategy(self, returns: pd.Series, benchmark_returns: Optional[pd.Series] = None,
                         strategy_name: str = "Unnamed Strategy", symbol: str = "Unknown") -> ValidationReport:
        """
        Comprehensive statistical validation of trading strategy

        Args:
            returns: Strategy returns series
            benchmark_returns: Optional benchmark returns for comparison
            strategy_name: Name of the strategy
            symbol: Trading symbol

        Returns:
            ValidationReport with comprehensive analysis
        """
        logger.info(f"Starting statistical validation for {strategy_name}")

        try:
            # Data preparation and cleaning
            cleaned_returns = self._prepare_data(returns)

            # Basic performance metrics
            performance_metrics = self._calculate_performance_metrics(cleaned_returns, benchmark_returns)

            # Bootstrap analysis
            bootstrap_results = self._perform_bootstrap_analysis(cleaned_returns, benchmark_returns)

            # Statistical tests
            statistical_tests = self._perform_statistical_tests(cleaned_returns, benchmark_returns)

            # Risk metrics
            risk_metrics = self._calculate_risk_metrics(cleaned_returns)

            # Assumption checks
            assumption_checks = self._check_assumptions(cleaned_returns)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                performance_metrics, statistical_tests, risk_metrics, assumption_checks
            )

            # Calculate overall validity score
            validity_score = self._calculate_validity_score(
                statistical_tests, risk_metrics, assumption_checks
            )

            # Create validation report
            report = ValidationReport(
                strategy_name=strategy_name,
                symbol=symbol,
                sample_size=len(cleaned_returns),
                time_period=f"{cleaned_returns.index.min()} to {cleaned_returns.index.max()}",
                bootstrap_results=bootstrap_results,
                statistical_tests=statistical_tests,
                risk_metrics=risk_metrics,
                performance_metrics=performance_metrics,
                assumption_checks=assumption_checks,
                recommendations=recommendations,
                validation_timestamp=datetime.now(),
                overall_validity_score=validity_score
            )

            logger.info(f"Statistical validation completed for {strategy_name}")
            return report

        except Exception as e:
            logger.error(f"Error in statistical validation: {e}")
            raise

    def _prepare_data(self, returns: pd.Series) -> pd.Series:
        """Prepare and clean returns data"""
        # Remove NaN values
        cleaned = returns.dropna()

        # Check minimum sample size
        if len(cleaned) < self.config.min_samples:
            raise ValueError(f"Insufficient data: {len(cleaned)} < {self.config.min_samples}")

        # Cap maximum sample size for computational efficiency
        if len(cleaned) > self.config.max_samples:
            cleaned = cleaned.tail(self.config.max_samples)
            logger.warning(f"Sample size capped at {self.config.max_samples}")

        # Remove extreme outliers (beyond 5 standard deviations)
        mean_return = cleaned.mean()
        std_return = cleaned.std()
        outliers = np.abs(cleaned - mean_return) > 5 * std_return
        if outliers.any():
            cleaned = cleaned[~outliers]
            logger.warning(f"Removed {outliers.sum()} extreme outliers")

        return cleaned

    def _calculate_performance_metrics(self, returns: pd.Series,
                                     benchmark_returns: Optional[pd.Series] = None) -> Dict[str, float]:
        """Calculate performance metrics"""
        metrics = {}

        # Basic metrics
        metrics['mean_return'] = float(returns.mean())
        metrics['std_return'] = float(returns.std())
        metrics['sharpe_ratio'] = float(returns.mean() / returns.std() * np.sqrt(252))  # Annualized
        metrics['sortino_ratio'] = self._calculate_sortino_ratio(returns)
        metrics['calmar_ratio'] = self._calculate_calmar_ratio(returns)

        # Value at Risk and Expected Shortfall
        metrics['var_95'] = float(np.percentile(returns, 5))
        metrics['var_99'] = float(np.percentile(returns, 1))
        metrics['cvar_95'] = float(returns[returns <= np.percentile(returns, 5)].mean())
        metrics['cvar_99'] = float(returns[returns <= np.percentile(returns, 1)].mean())

        # Maximum drawdown
        metrics['max_drawdown'] = float(self._calculate_max_drawdown(returns))
        metrics['drawdown_duration'] = int(self._calculate_drawdown_duration(returns))

        # Win rate and statistics
        metrics['win_rate'] = float((returns > 0).mean())
        metrics['profit_factor'] = float(returns[returns > 0].sum() / abs(returns[returns < 0].sum())) if (returns < 0).any() else np.inf

        # Skewness and kurtosis
        metrics['skewness'] = float(stats.skew(returns))
        metrics['kurtosis'] = float(stats.kurtosis(returns))

        # Tail ratio (95th percentile / 5th percentile)
        metrics['tail_ratio'] = float(np.percentile(returns, 95) / abs(np.percentile(returns, 5)))

        # Benchmark comparison if provided
        if benchmark_returns is not None:
            aligned_returns, aligned_benchmark = self._align_returns(returns, benchmark_returns)

            # Information ratio
            excess_returns = aligned_returns - aligned_benchmark
            metrics['information_ratio'] = float(excess_returns.mean() / excess_returns.std() * np.sqrt(252))

            # Beta and Alpha (using regression)
            if len(aligned_returns) > 30:
                beta, alpha = self._calculate_beta_alpha(aligned_returns, aligned_benchmark)
                metrics['beta'] = float(beta)
                metrics['alpha'] = float(alpha * 252)  # Annualized alpha

        return metrics

    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return np.inf
        downside_deviation = downside_returns.std()
        return returns.mean() / downside_deviation * np.sqrt(252) if downside_deviation > 0 else np.inf

    def _calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """Calculate Calmar ratio (annual return / maximum drawdown)"""
        annual_return = returns.mean() * 252
        max_dd = self._calculate_max_drawdown(returns)
        return annual_return / abs(max_dd) if max_dd != 0 else np.inf

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def _calculate_drawdown_duration(self, returns: pd.Series) -> int:
        """Calculate maximum drawdown duration in days"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        # Find periods in drawdown
        in_drawdown = drawdown < 0
        drawdown_periods = self._find_consecutive_periods(in_drawdown)

        return max(drawdown_periods) if drawdown_periods else 0

    def _find_consecutive_periods(self, boolean_series: pd.Series) -> List[int]:
        """Find lengths of consecutive True periods"""
        periods = []
        current_period = 0

        for value in boolean_series:
            if value:
                current_period += 1
            else:
                if current_period > 0:
                    periods.append(current_period)
                    current_period = 0

        if current_period > 0:
            periods.append(current_period)

        return periods

    def _calculate_beta_alpha(self, returns: pd.Series, benchmark_returns: pd.Series) -> Tuple[float, float]:
        """Calculate beta and alpha using linear regression"""
        model = LinearRegression()
        model.fit(benchmark_returns.values.reshape(-1, 1), returns.values)
        beta = model.coef_[0]
        alpha = model.intercept_
        return beta, alpha

    def _align_returns(self, returns1: pd.Series, returns2: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Align two return series by date"""
        return returns1.align(returns2, join='inner')

    def _perform_bootstrap_analysis(self, returns: pd.Series,
                                  benchmark_returns: Optional[pd.Series] = None) -> Dict[str, BootstrapResult]:
        """Perform bootstrap analysis for key statistics"""
        logger.info("Performing bootstrap analysis")

        bootstrap_results = {}

        # Statistics to bootstrap
        statistics = {
            'mean_return': lambda x: np.mean(x),
            'std_return': lambda x: np.std(x),
            'sharpe_ratio': lambda x: np.mean(x) / np.std(x) * np.sqrt(252),
            'max_drawdown': self._calculate_max_drawdown,
            'var_95': lambda x: np.percentile(x, 5),
            'skewness': lambda x: stats.skew(x),
            'kurtosis': lambda x: stats.kurtosis(x)
        }

        # Add benchmark statistics if available
        if benchmark_returns is not None:
            aligned_returns, aligned_benchmark = self._align_returns(returns, benchmark_returns)
            excess_returns = aligned_returns - aligned_benchmark
            statistics['information_ratio'] = lambda x: np.mean(x) / np.std(x) * np.sqrt(252)

        # Perform bootstrap for each statistic
        with ThreadPoolExecutor(max_workers=self.config.parallel_jobs) as executor:
            future_to_stat = {
                executor.submit(self._bootstrap_statistic, returns, stat_func, stat_name): stat_name
                for stat_name, stat_func in statistics.items()
            }

            for future in future_to_stat:
                stat_name = future_to_stat[future]
                try:
                    result = future.result()
                    bootstrap_results[stat_name] = result
                except Exception as e:
                    logger.error(f"Error in bootstrap for {stat_name}: {e}")

        return bootstrap_results

    def _bootstrap_statistic(self, returns: pd.Series, stat_func: callable, stat_name: str) -> BootstrapResult:
        """Bootstrap a single statistic"""
        n = len(returns)
        bootstrap_stats = []

        for i in range(self.config.bootstrap_samples):
            # Resample with replacement
            bootstrap_sample = np.random.choice(returns, size=n, replace=True)

            # Calculate statistic on bootstrap sample
            try:
                bootstrap_stat = stat_func(bootstrap_sample)
                if np.isfinite(bootstrap_stat):
                    bootstrap_stats.append(bootstrap_stat)
            except:
                continue

        bootstrap_stats = np.array(bootstrap_stats)

        # Calculate original statistic
        original_stat = stat_func(returns.values)

        # Calculate confidence intervals
        confidence_intervals = {}
        for conf_level in self.config.confidence_levels:
            alpha = 1 - conf_level
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            ci = (np.percentile(bootstrap_stats, lower_percentile),
                  np.percentile(bootstrap_stats, upper_percentile))
            confidence_intervals[conf_level] = ci

        # Calculate bias and standard error
        bias = np.mean(bootstrap_stats) - original_stat
        standard_error = np.std(bootstrap_stats)

        return BootstrapResult(
            statistic=original_stat,
            confidence_intervals=confidence_intervals,
            bias=bias,
            standard_error=standard_error,
            bootstrap_distribution=bootstrap_stats,
            sample_size=n
        )

    def _perform_statistical_tests(self, returns: pd.Series,
                                 benchmark_returns: Optional[pd.Series] = None) -> Dict[str, StatisticalTest]:
        """Perform comprehensive statistical tests"""
        logger.info("Performing statistical tests")

        tests = {}

        # 1. Normality tests
        tests.update(self._test_normality(returns))

        # 2. Stationarity tests
        tests.update(self._test_stationarity(returns))

        # 3. Autocorrelation tests
        tests.update(self._test_autocorrelation(returns))

        # 4. Volatility clustering tests
        tests.update(self._test_volatility_clustering(returns))

        # 5. Risk-adjusted performance tests
        tests.update(self._test_risk_adjusted_performance(returns))

        # 6. Benchmark comparison tests
        if benchmark_returns is not None:
            tests.update(self._test_benchmark_comparison(returns, benchmark_returns))

        # Multiple testing correction
        tests = self._apply_multiple_testing_correction(tests)

        return tests

    def _test_normality(self, returns: pd.Series) -> Dict[str, StatisticalTest]:
        """Test for normality of returns"""
        tests = {}

        # Jarque-Bera test
        jb_stat, jb_pvalue, _, _ = jarque_bera(returns)
        tests['jarque_bera'] = StatisticalTest(
            test_name='Jarque-Bera Test',
            statistic=float(jb_stat),
            p_value=float(jb_pvalue),
            is_significant=jb_pvalue < self.config.significance_level,
            interpretation='Returns are normally distributed' if jb_pvalue >= self.config.significance_level else 'Returns are not normally distributed',
            assumptions=['Sample size > 8', 'Independent observations']
        )

        # Shapiro-Wilk test (if sample size <= 5000)
        if len(returns) <= 5000:
            sw_stat, sw_pvalue = stats.shapiro(returns)
            tests['shapiro_wilk'] = StatisticalTest(
                test_name='Shapiro-Wilk Test',
                statistic=float(sw_stat),
                p_value=float(sw_pvalue),
                is_significant=sw_pvalue < self.config.significance_level,
                interpretation='Returns are normally distributed' if sw_pvalue >= self.config.significance_level else 'Returns are not normally distributed',
                assumptions=['Sample size <= 5000', 'Independent observations']
            )

        # Anderson-Darling test
        ad_stat, ad_critical, ad_significance = stats.anderson(returns, dist='norm')
        tests['anderson_darling'] = StatisticalTest(
            test_name='Anderson-Darling Test',
            statistic=float(ad_stat),
            p_value=float(ad_significance[2]),  # 5% significance level
            critical_value=float(ad_critical[2]),
            is_significant=ad_stat > ad_critical[2],
            interpretation='Returns are normally distributed' if ad_stat <= ad_critical[2] else 'Returns are not normally distributed',
            assumptions=['Large sample size']
        )

        return tests

    def _test_stationarity(self, returns: pd.Series) -> Dict[str, StatisticalTest]:
        """Test for stationarity of returns"""
        tests = {}

        # Augmented Dickey-Fuller test
        adf_stat, adf_pvalue, _, _, adf_critical, _ = adfuller(returns, autolag='AIC')
        tests['adf_test'] = StatisticalTest(
            test_name='Augmented Dickey-Fuller Test',
            statistic=float(adf_stat),
            p_value=float(adf_pvalue),
            critical_value=float(adf_critical['5%']),
            is_significant=adf_pvalue < self.config.significance_level,
            interpretation='Returns are stationary' if adf_pvalue < self.config.significance_level else 'Returns are non-stationary',
            assumptions=['No structural breaks', 'Appropriate lag selection']
        )

        # KPSS test
        kpss_stat, kpss_pvalue, _, kpss_critical = kpss(returns, regression='c')
        tests['kpss_test'] = StatisticalTest(
            test_name='KPSS Test',
            statistic=float(kpss_stat),
            p_value=float(kpss_pvalue),
            critical_value=float(kpss_critical['5%']),
            is_significant=kpss_pvalue < self.config.significance_level,
            interpretation='Returns are stationary' if kpss_stat < kpss_critical['5%'] else 'Returns are non-stationary',
            assumptions=['No structural breaks', 'Linear trend specification']
        )

        return tests

    def _test_autocorrelation(self, returns: pd.Series) -> Dict[str, StatisticalTest]:
        """Test for autocorrelation in returns"""
        tests = {}

        # Ljung-Box test for autocorrelation
        # Test multiple lags
        for lag in [5, 10, 20]:
            if len(returns) > lag:
                lb_stat, lb_pvalue = acorr_ljungbox(returns, lags=[lag], return_df=False)
                tests[f'ljung_box_lag_{lag}'] = StatisticalTest(
                    test_name=f'Ljung-Box Test (lag {lag})',
                    statistic=float(lb_stat[0]),
                    p_value=float(lb_pvalue[0]),
                    is_significant=lb_pvalue[0] < self.config.significance_level,
                    interpretation='No significant autocorrelation' if lb_pvalue[0] >= self.config.significance_level else f'Significant autocorrelation at lag {lag}',
                    assumptions=[f'Lag length = {lag}', 'Independence under null hypothesis']
                )

        return tests

    def _test_volatility_clustering(self, returns: pd.Series) -> Dict[str, StatisticalTest]:
        """Test for volatility clustering"""
        tests = {}

        # Engle's ARCH test
        if len(returns) > 100:  # Need sufficient data for ARCH test
            try:
                # Calculate squared returns
                squared_returns = returns ** 2

                # Simple ARCH test using regression
                n_lags = min(10, len(squared_returns) // 10)

                # Prepare data for regression
                X = []
                y = squared_returns[n_lags:]

                for i in range(len(squared_returns) - n_lags):
                    X.append(squared_returns[i:i+n_lags])

                X = np.array(X)

                # Regression
                model = LinearRegression()
                model.fit(X, y)

                # R-squared
                r_squared = model.score(X, y)

                # ARCH test statistic (LM test)
                arch_stat = len(y) * r_squared
                arch_pvalue = 1 - stats.chi2.cdf(arch_stat, n_lags)

                tests['engle_arch'] = StatisticalTest(
                    test_name='Engle ARCH Test',
                    statistic=float(arch_stat),
                    p_value=float(arch_pvalue),
                    is_significant=arch_pvalue < self.config.significance_level,
                    interpretation='No ARCH effects' if arch_pvalue >= self.config.significance_level else 'Significant ARCH effects (volatility clustering)',
                    assumptions=['Sufficient sample size', 'Correct lag specification']
                )

            except Exception as e:
                logger.warning(f"Error in ARCH test: {e}")

        return tests

    def _test_risk_adjusted_performance(self, returns: pd.Series) -> Dict[str, StatisticalTest]:
        """Test risk-adjusted performance metrics"""
        tests = {}

        # Test if Sharpe ratio is significantly different from zero
        n = len(returns)
        mean_return = returns.mean()
        std_return = returns.std()

        if std_return > 0:
            # Standard error of Sharpe ratio
            sharpe_se = np.sqrt((1 + 0.5 * mean_return**2 / std_return**2) / n)

            # t-statistic
            sharpe_stat = mean_return / std_return / sharpe_se
            sharpe_pvalue = 2 * (1 - stats.t.cdf(abs(sharpe_stat), n - 1))

            tests['sharpe_ratio_test'] = StatisticalTest(
                test_name='Sharpe Ratio Significance Test',
                statistic=float(sharpe_stat),
                p_value=float(sharpe_pvalue),
                is_significant=sharpe_pvalue < self.config.significance_level,
                interpretation='Sharpe ratio is not significantly different from zero' if sharpe_pvalue >= self.config.significance_level else 'Sharpe ratio is significantly different from zero',
                assumptions=['Normal distribution of returns', 'Independent observations']
            )

        return tests

    def _test_benchmark_comparison(self, returns: pd.Series, benchmark_returns: pd.Series) -> Dict[str, StatisticalTest]:
        """Test comparison with benchmark"""
        tests = {}

        try:
            # Align returns
            aligned_returns, aligned_benchmark = self._align_returns(returns, benchmark_returns)
            excess_returns = aligned_returns - aligned_benchmark

            # Test if excess returns are significantly different from zero
            mean_excess = excess_returns.mean()
            std_excess = excess_returns.std()
            n = len(excess_returns)

            if std_excess > 0:
                t_stat = mean_excess / (std_excess / np.sqrt(n))
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 1))

                tests['excess_returns_test'] = StatisticalTest(
                    test_name='Excess Returns Significance Test',
                    statistic=float(t_stat),
                    p_value=float(p_value),
                    is_significant=p_value < self.config.significance_level,
                    interpretation='Excess returns are not significantly different from zero' if p_value >= self.config.significance_level else 'Excess returns are significantly different from zero',
                    assumptions=['Normal distribution of excess returns', 'Independent observations']
                )

            # Paired t-test
            t_stat, p_value = stats.ttest_rel(aligned_returns, aligned_benchmark)
            tests['paired_t_test'] = StatisticalTest(
                test_name='Paired t-test vs Benchmark',
                statistic=float(t_stat),
                p_value=float(p_value),
                is_significant=p_value < self.config.significance_level,
                interpretation='No significant difference from benchmark' if p_value >= self.config.significance_level else 'Significant difference from benchmark',
                assumptions=['Normal distribution of differences', 'Paired observations']
            )

            # Wilcoxon signed-rank test (non-parametric alternative)
            if len(excess_returns) >= 10:  # Minimum sample size for Wilcoxon test
                wilcoxon_stat, wilcoxon_pvalue = stats.wilcoxon(aligned_returns, aligned_benchmark)
                tests['wilcoxon_test'] = StatisticalTest(
                    test_name='Wilcoxon Signed-Rank Test',
                    statistic=float(wilcoxon_stat),
                    p_value=float(wilcoxon_pvalue),
                    is_significant=wilcoxon_pvalue < self.config.significance_level,
                    interpretation='No significant difference from benchmark' if wilcoxon_pvalue >= self.config.significance_level else 'Significant difference from benchmark',
                    assumptions=['Symmetric distribution of differences', 'Independent observations']
                )

        except Exception as e:
            logger.error(f"Error in benchmark comparison tests: {e}")

        return tests

    def _apply_multiple_testing_correction(self, tests: Dict[str, StatisticalTest]) -> Dict[str, StatisticalTest]:
        """Apply multiple testing correction to p-values"""
        if not tests:
            return tests

        # Extract p-values
        test_names = list(tests.keys())
        p_values = [test.p_value for test in tests.values()]

        # Apply correction
        if self.config.multiple_testing_correction == 'bonferroni':
            rejected, p_corrected, _, _ = multipletests(p_values, method='bonferroni')
        elif self.config.multiple_testing_correction == 'fdr_bh':
            rejected, p_corrected, _, _ = multipletests(p_values, method='fdr_bh')
        elif self.config.multiple_testing_correction == 'fdr_by':
            rejected, p_corrected, _, _ = multipletests(p_values, method='fdr_by')
        else:
            # No correction
            p_corrected = p_values
            rejected = [p < self.config.significance_level for p in p_values]

        # Update test results
        for i, test_name in enumerate(test_names):
            tests[test_name].p_value = float(p_corrected[i])
            tests[test_name].is_significant = rejected[i]

        return tests

    def _calculate_risk_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate risk metrics"""
        metrics = {}

        # Volatility metrics
        metrics['annual_volatility'] = float(returns.std() * np.sqrt(252))
        metrics['downside_volatility'] = float(returns[returns < 0].std() * np.sqrt(252))
        metrics['upside_volatility'] = float(returns[returns > 0].std() * np.sqrt(252))

        # Risk-adjusted metrics
        metrics['sharpe_ratio'] = float(returns.mean() / returns.std() * np.sqrt(252))
        metrics['sortino_ratio'] = self._calculate_sortino_ratio(returns)
        metrics['calmar_ratio'] = self._calculate_calmar_ratio(returns)

        # Value at Risk metrics
        metrics['var_95_daily'] = float(np.percentile(returns, 5))
        metrics['var_99_daily'] = float(np.percentile(returns, 1))
        metrics['var_95_annual'] = float(np.percentile(returns, 5) * np.sqrt(252))
        metrics['var_99_annual'] = float(np.percentile(returns, 1) * np.sqrt(252))

        # Conditional Value at Risk
        metrics['cvar_95_daily'] = float(returns[returns <= np.percentile(returns, 5)].mean())
        metrics['cvar_99_daily'] = float(returns[returns <= np.percentile(returns, 1)].mean())
        metrics['cvar_95_annual'] = float(returns[returns <= np.percentile(returns, 5)].mean() * np.sqrt(252))
        metrics['cvar_99_annual'] = float(returns[returns <= np.percentile(returns, 1)].mean() * np.sqrt(252))

        # Maximum drawdown metrics
        metrics['max_drawdown'] = float(self._calculate_max_drawdown(returns))
        metrics['drawdown_duration'] = int(self._calculate_drawdown_duration(returns))

        # Gain/Loss metrics
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]

        if len(positive_returns) > 0:
            metrics['avg_gain'] = float(positive_returns.mean())
            metrics['max_gain'] = float(positive_returns.max())

        if len(negative_returns) > 0:
            metrics['avg_loss'] = float(negative_returns.mean())
            metrics['max_loss'] = float(negative_returns.min())

        if len(positive_returns) > 0 and len(negative_returns) > 0:
            metrics['gain_loss_ratio'] = float(abs(positive_returns.mean() / negative_returns.mean()))
            metrics['profit_factor'] = float(positive_returns.sum() / abs(negative_returns.sum()))

        return metrics

    def _check_assumptions(self, returns: pd.Series) -> Dict[str, bool]:
        """Check statistical assumptions"""
        assumptions = {}

        # Normality assumption
        jb_stat, jb_pvalue = jarque_bera(returns)
        assumptions['normality'] = jb_pvalue >= self.config.significance_level

        # Stationarity assumption
        adf_stat, adf_pvalue, _, _, _, _ = adfuller(returns)
        assumptions['stationarity'] = adf_pvalue < self.config.significance_level

        # Independence assumption (no autocorrelation)
        if len(returns) > 10:
            lb_stat, lb_pvalue = acorr_ljungbox(returns, lags=[10], return_df=False)
            assumptions['independence'] = lb_pvalue[0] >= self.config.significance_level
        else:
            assumptions['independence'] = True

        # Sufficient sample size
        assumptions['sufficient_sample'] = len(returns) >= self.config.min_samples

        # No extreme outliers
        z_scores = np.abs(stats.zscore(returns))
        extreme_outliers = (z_scores > 4).sum()
        assumptions['no_extreme_outliers'] = extreme_outliers / len(returns) < 0.01  # Less than 1% extreme outliers

        return assumptions

    def _generate_recommendations(self, performance_metrics: Dict[str, float],
                                statistical_tests: Dict[str, StatisticalTest],
                                risk_metrics: Dict[str, float],
                                assumption_checks: Dict[str, bool]) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []

        # Performance-based recommendations
        if performance_metrics.get('sharpe_ratio', 0) < 1.0:
            recommendations.append("Consider improving risk-adjusted returns (Sharpe ratio < 1.0)")

        if risk_metrics.get('max_drawdown', 0) < -0.20:  # 20% drawdown
            recommendations.append("Maximum drawdown exceeds 20%, consider adding risk management")

        # Statistical test-based recommendations
        normality_test = statistical_tests.get('jarque_bera')
        if normality_test and normality_test.is_significant:
            recommendations.append("Returns are not normally distributed, consider non-parametric methods")

        stationarity_test = statistical_tests.get('adf_test')
        if stationarity_test and not stationarity_test.is_significant:
            recommendations.append("Returns may be non-stationary, consider differencing or transformation")

        # Assumption-based recommendations
        if not assumption_checks.get('normality', False):
            recommendations.append("Normality assumption violated, use robust statistical methods")

        if not assumption_checks.get('stationarity', False):
            recommendations.append("Stationarity assumption violated, check for trends or structural breaks")

        if not assumption_checks.get('independence', False):
            recommendations.append("Independence assumption violated (autocorrelation detected)")

        if not assumption_checks.get('sufficient_sample', False):
            recommendations.append("Insufficient sample size for reliable statistical inference")

        if not assumption_checks.get('no_extreme_outliers', False):
            recommendations.append("Extreme outliers detected, consider robust estimation methods")

        # Risk-based recommendations
        if risk_metrics.get('var_99_daily', 0) < -0.05:  # 5% daily loss
            recommendations.append("High tail risk detected (99% VaR < -5%), consider position sizing")

        if performance_metrics.get('profit_factor', 0) < 1.5:
            recommendations.append("Low profit factor (< 1.5), consider strategy refinement")

        # Generate positive feedback if metrics are good
        if performance_metrics.get('sharpe_ratio', 0) > 2.0:
            recommendations.append("Excellent risk-adjusted performance (Sharpe ratio > 2.0)")

        if risk_metrics.get('max_drawdown', 0) > -0.10:  # Less than 10% drawdown
            recommendations.append("Good risk control with manageable drawdowns")

        return recommendations

    def _calculate_validity_score(self, statistical_tests: Dict[str, StatisticalTest],
                                risk_metrics: Dict[str, float],
                                assumption_checks: Dict[str, bool]) -> float:
        """Calculate overall statistical validity score"""
        score = 100.0

        # Penalize failed statistical tests
        failed_tests = sum(1 for test in statistical_tests.values() if test.is_significant and 'Jarque-Bera' not in test.test_name)
        score -= failed_tests * 5

        # Penalize violated assumptions
        violated_assumptions = sum(1 for check in assumption_checks.values() if not check)
        score -= violated_assumptions * 10

        # Adjust for risk metrics
        if risk_metrics.get('max_drawdown', 0) < -0.30:  # Severe drawdown
            score -= 20

        if risk_metrics.get('sharpe_ratio', 0) < 0.5:  # Poor risk-adjusted return
            score -= 15

        return max(0.0, score)

    def generate_validation_report_json(self, report: ValidationReport) -> str:
        """Generate JSON report"""
        report_dict = {
            'strategy_name': report.strategy_name,
            'symbol': report.symbol,
            'sample_size': report.sample_size,
            'time_period': report.time_period,
            'bootstrap_results': {
                name: {
                    'statistic': result.statistic,
                    'confidence_intervals': {str(k): v for k, v in result.confidence_intervals.items()},
                    'bias': result.bias,
                    'standard_error': result.standard_error,
                    'sample_size': result.sample_size
                }
                for name, result in report.bootstrap_results.items()
            },
            'statistical_tests': {
                name: {
                    'test_name': result.test_name,
                    'statistic': result.statistic,
                    'p_value': result.p_value,
                    'critical_value': result.critical_value,
                    'is_significant': result.is_significant,
                    'interpretation': result.interpretation,
                    'assumptions': result.assumptions
                }
                for name, result in report.statistical_tests.items()
            },
            'risk_metrics': report.risk_metrics,
            'performance_metrics': report.performance_metrics,
            'assumption_checks': report.assumption_checks,
            'recommendations': report.recommendations,
            'validation_timestamp': report.validation_timestamp.isoformat(),
            'overall_validity_score': report.overall_validity_score
        }

        return json.dumps(report_dict, indent=2)

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create sample returns data
    np.random.seed(42)
    n_days = 1000
    returns = pd.Series(
        np.random.normal(0.001, 0.02, n_days),  # Daily returns with 0.1% mean, 2% std
        index=pd.date_range('2020-01-01', periods=n_days, freq='D')
    )

    # Create benchmark returns
    benchmark_returns = pd.Series(
        np.random.normal(0.0005, 0.015, n_days),
        index=pd.date_range('2020-01-01', periods=n_days, freq='D')
    )

    # Initialize validation framework
    validator = StatisticalValidationFramework()

    # Validate strategy
    report = validator.validate_strategy(
        returns=returns,
        benchmark_returns=benchmark_returns,
        strategy_name="Momentum Strategy",
        symbol="0700.HK"
    )

    print(f"Overall Validity Score: {report.overall_validity_score:.1f}")
    print(f"Number of Recommendations: {len(report.recommendations)}")
    print(f"Sample Size: {report.sample_size}")

    # Save report
    json_report = validator.generate_validation_report_json(report)
    with open("validation_report.json", "w") as f:
        f.write(json_report)

    print("Validation report saved to validation_report.json")