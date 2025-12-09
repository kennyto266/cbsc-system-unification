#!/usr/bin/env python3
"""
Phase 2: Statistical Validation Framework for Professional Backtesting
=====================================================================

Advanced statistical validation system for ensuring robustness and reliability
of long-term backtesting results (5+ years).

Key Features:
- Statistical significance testing
- Sample size validation
- Confidence intervals
- Multiple hypothesis testing correction
- Professional-grade validation metrics

Author: Claude Code Assistant
Date: 2025-11-29
Phase: 2 - Statistical Validation Framework
"""

import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from scipy import stats
from scipy.stats import jarque_bera, normaltest, kstest, norm, t

logger = logging.getLogger(__name__)


@dataclass
class StatisticalValidationConfig:
    """Configuration for statistical validation framework"""
    
    # Significance testing
    significance_level: float = 0.05
    confidence_level: float = 0.95
    bonferroni_correction: bool = True
    bootstrap_samples: int = 10000
    
    # Sample size requirements
    min_observations: int = 252  # 1 year of trading days
    preferred_observations: int = 1260  # 5 years of trading days
    min_trades: int = 30
    preferred_trades: int = 100
    
    # Performance validation
    min_sharpe_ratio: float = 0.5
    max_drawdown_threshold: float = -0.25  # 25% max drawdown
    min_win_rate: float = 0.4
    min_profit_factor: float = 1.2
    
    # Stability testing
    stability_window: int = 252  # 1 year rolling window
    minimum_stable_periods: int = 3
    stability_threshold: float = 0.7
    
    # Outlier detection
    outlier_method: str = "iqr"  # "iqr", "zscore", "isolation_forest"
    outlier_threshold: float = 3.0
    
    # Benchmark requirements
    benchmark_alpha_requirement: float = 0.02  # 2% annual alpha
    max_tracking_error: float = 0.15  # 15% tracking error


@dataclass
class ValidationResults:
    """Results of statistical validation"""
    
    # Basic validation
    is_valid: bool
    validation_score: float  # 0-100 score
    critical_issues: List[str]
    warnings: List[str]
    
    # Statistical tests
    sharpe_significance: bool
    sharpe_p_value: float
    sharpe_confidence_interval: Tuple[float, float]
    
    # Sample size analysis
    sample_size_adequate: bool
    sample_size_score: float
    trade_count_adequate: bool
    
    # Performance validation
    meets_performance_criteria: bool
    performance_score: float
    
    # Stability analysis
    stability_score: float
    is_stable: bool
    
    # Distribution analysis
    returns_normal: bool
    normality_p_value: float
    outlier_count: int
    outlier_percentage: float
    
    # Benchmark comparison
    alpha_significant: bool
    alpha_p_value: float
    beta_stable: bool
    tracking_error_acceptable: bool
    
    # Overall recommendation
    recommendation: str  # "ACCEPT", "REJECT", "CONDITIONAL"
    recommendation_reason: str


class StatisticalValidator:
    """
    Advanced statistical validation system for backtesting results
    """
    
    def __init__(self, config: Optional[StatisticalValidationConfig] = None):
        self.config = config or StatisticalValidationConfig()
        self._validation_cache = {}
        
        logger.info("Statistical Validation Framework initialized")
    
    def validate_backtest_results(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        trade_data: Optional[pd.DataFrame] = None,
        custom_metrics: Optional[Dict[str, float]] = None
    ) -> ValidationResults:
        """
        Comprehensive statistical validation of backtesting results
        
        Args:
            returns: Strategy returns series
            benchmark_returns: Benchmark returns for comparison (optional)
            trade_data: Detailed trade information (optional)
            custom_metrics: Additional performance metrics (optional)
            
        Returns:
            ValidationResults with comprehensive validation analysis
        """
        
        try:
            logger.info(f"Starting statistical validation for {len(returns)} return observations")
            
            # Initialize results
            results = ValidationResults(
                is_valid=True,
                validation_score=0.0,
                critical_issues=[],
                warnings=[],
                sharpe_significance=False,
                sharpe_p_value=1.0,
                sharpe_confidence_interval=(0.0, 0.0),
                sample_size_adequate=False,
                sample_size_score=0.0,
                trade_count_adequate=False,
                meets_performance_criteria=False,
                performance_score=0.0,
                stability_score=0.0,
                is_stable=False,
                returns_normal=False,
                normality_p_value=1.0,
                outlier_count=0,
                outlier_percentage=0.0,
                alpha_significant=False,
                alpha_p_value=1.0,
                beta_stable=False,
                tracking_error_acceptable=False,
                recommendation="REJECT",
                recommendation_reason=""
            )
            
            # 1. Sample size validation
            self._validate_sample_size(returns, trade_data, results)
            
            # 2. Performance validation
            self._validate_performance_metrics(returns, results)
            
            # 3. Sharpe ratio significance testing
            self._test_sharpe_significance(returns, results)
            
            # 4. Stability analysis
            self._analyze_stability(returns, results)
            
            # 5. Distribution analysis
            self._analyze_return_distribution(returns, results)
            
            # 6. Benchmark comparison
            if benchmark_returns is not None:
                self._compare_to_benchmark(returns, benchmark_returns, results)
            
            # 7. Calculate overall validation score
            self._calculate_overall_score(results)
            
            # 8. Generate recommendation
            self._generate_recommendation(results)
            
            logger.info(f"Validation completed. Score: {results.validation_score:.1f}, Recommendation: {results.recommendation}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during statistical validation: {e}")
            raise
    
    def _validate_sample_size(
        self, 
        returns: pd.Series, 
        trade_data: Optional[pd.DataFrame], 
        results: ValidationResults
    ) -> None:
        """Validate sample size adequacy"""
        
        n_observations = len(returns)
        results.sample_size_score = min(n_observations / self.config.preferred_observations, 1.0) * 100
        
        # Check minimum requirements
        results.sample_size_adequate = n_observations >= self.config.min_observations
        
        if not results.sample_size_adequate:
            results.critical_issues.append(
                f"Insufficient observations: {n_observations} < {self.config.min_observations}"
            )
        elif n_observations < self.config.preferred_observations:
            results.warnings.append(
                f"Prefer more observations: {n_observations} < {self.config.preferred_observations}"
            )
        
        # Check trade count if available
        if trade_data is not None:
            n_trades = len(trade_data)
            results.trade_count_adequate = n_trades >= self.config.min_trades
            
            if not results.trade_count_adequate:
                results.critical_issues.append(
                    f"Insufficient trades: {n_trades} < {self.config.min_trades}"
                )
            elif n_trades < self.config.preferred_trades:
                results.warnings.append(
                    f"Prefer more trades: {n_trades} < {self.config.preferred_trades}"
                )
    
    def _validate_performance_metrics(
        self, 
        returns: pd.Series, 
        results: ValidationResults
    ) -> None:
        """Validate performance against minimum criteria"""
        
        # Calculate key metrics
        total_return = (1 + returns).prod() - 1
        annual_return = returns.mean() * 252
        annual_volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # Calculate drawdown
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calculate win rate and profit factor
        win_rate = (returns > 0).mean()
        winning_returns = returns[returns > 0].sum() if (returns > 0).any() else 0
        losing_returns = abs(returns[returns < 0].sum()) if (returns < 0).any() else 0
        profit_factor = winning_returns / losing_returns if losing_returns > 0 else float('inf')
        
        # Check criteria
        score_components = []
        
        if sharpe_ratio >= self.config.min_sharpe_ratio:
            score_components.append(25)
        else:
            results.critical_issues.append(f"Sharpe ratio too low: {sharpe_ratio:.3f} < {self.config.min_sharpe_ratio}")
        
        if max_drawdown >= self.config.max_drawdown_threshold:
            score_components.append(25)
        else:
            results.critical_issues.append(f"Max drawdown too high: {max_drawdown:.2%}")
        
        if win_rate >= self.config.min_win_rate:
            score_components.append(25)
        else:
            results.warnings.append(f"Low win rate: {win_rate:.2%} < {self.config.min_win_rate:.2%}")
        
        if profit_factor >= self.config.min_profit_factor:
            score_components.append(25)
        else:
            results.warnings.append(f"Low profit factor: {profit_factor:.2f} < {self.config.min_profit_factor:.2f}")
        
        results.performance_score = sum(score_components)
        results.meets_performance_criteria = results.performance_score >= 50  # At least 2 criteria met
    
    def _test_sharpe_significance(
        self, 
        returns: pd.Series, 
        results: ValidationResults
    ) -> None:
        """Test statistical significance of Sharpe ratio"""
        
        if len(returns) < 2:
            return
        
        # Calculate Sharpe ratio
        annual_return = returns.mean() * 252
        annual_volatility = returns.std() * np.sqrt(252)
        
        if annual_volatility == 0:
            results.sharpe_significance = False
            results.sharpe_p_value = 1.0
            return
        
        sharpe_ratio = annual_return / annual_volatility
        
        # Test significance using t-test
        n = len(returns)
        
        # Standard error of Sharpe ratio
        se_sharpe = np.sqrt((1 + 0.5 * sharpe_ratio**2) / n)
        
        # t-statistic
        t_stat = sharpe_ratio / se_sharpe
        
        # Two-tailed test
        from scipy.stats import t as t_dist
        p_value = 2 * (1 - t_dist.cdf(abs(t_stat), n - 1))
        
        results.sharpe_p_value = p_value
        results.sharpe_significance = p_value < self.config.significance_level
        
        # Calculate confidence interval
        t_critical = t_dist.ppf(1 - (1 - self.config.confidence_level) / 2, n - 1)
        margin_error = t_critical * se_sharpe
        
        results.sharpe_confidence_interval = (
            sharpe_ratio - margin_error,
            sharpe_ratio + margin_error
        )
    
    def _analyze_stability(
        self, 
        returns: pd.Series, 
        results: ValidationResults
    ) -> None:
        """Analyze performance stability over time"""
        
        if len(returns) < self.config.stability_window * 2:
            results.warnings.append("Insufficient data for stability analysis")
            results.stability_score = 50
            results.is_stable = False
            return
        
        # Calculate rolling performance metrics
        rolling_returns = returns.rolling(window=self.config.stability_window)
        rolling_sharpe = rolling_returns.mean() / rolling_returns.std() * np.sqrt(252)
        rolling_volatility = rolling_returns.std() * np.sqrt(252)
        
        # Get valid rolling metrics
        valid_sharpe = rolling_sharpe.dropna()
        valid_volatility = rolling_volatility.dropna()
        
        # Calculate stability metrics
        sharpe_stability = 1 - (valid_sharpe.std() / abs(valid_sharpe.mean())) if valid_sharpe.mean() != 0 else 0
        volatility_stability = 1 - (valid_volatility.std() / valid_volatility.mean()) if valid_volatility.mean() > 0 else 0
        
        # Combined stability score
        results.stability_score = (sharpe_stability + volatility_stability) / 2 * 100
        results.is_stable = results.stability_score >= (self.config.stability_threshold * 100)
        
        if not results.is_stable:
            results.warnings.append(f"Performance instability detected: {results.stability_score:.1f}%")
    
    def _analyze_return_distribution(
        self, 
        returns: pd.Series, 
        results: ValidationResults
    ) -> None:
        """Analyze return distribution for normality and outliers"""
        
        if len(returns) < 8:
            return
        
        # Test for normality using Jarque-Bera test
        jb_stat, jb_p_value = jarque_bera(returns.dropna())
        results.normality_p_value = jb_p_value
        results.returns_normal = jb_p_value > self.config.significance_level
        
        # Detect outliers
        if self.config.outlier_method == "zscore":
            z_scores = np.abs(stats.zscore(returns.dropna()))
            outlier_mask = z_scores > self.config.outlier_threshold
        elif self.config.outlier_method == "iqr":
            Q1 = returns.quantile(0.25)
            Q3 = returns.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outlier_mask = (returns < lower_bound) | (returns > upper_bound)
        else:
            # Default to z-score method
            z_scores = np.abs(stats.zscore(returns.dropna()))
            outlier_mask = z_scores > self.config.outlier_threshold
        
        results.outlier_count = outlier_mask.sum()
        results.outlier_percentage = (results.outlier_count / len(returns)) * 100
        
        if results.outlier_percentage > 5:
            results.warnings.append(f"High outlier percentage: {results.outlier_percentage:.1f}%")
    
    def _compare_to_benchmark(
        self, 
        returns: pd.Series, 
        benchmark_returns: pd.Series, 
        results: ValidationResults
    ) -> None:
        """Compare strategy performance to benchmark"""
        
        # Align returns
        common_index = returns.index.intersection(benchmark_returns.index)
        if len(common_index) < 30:
            results.warnings.append("Insufficient overlapping data for benchmark comparison")
            return
        
        aligned_returns = returns.reindex(common_index)
        aligned_benchmark = benchmark_returns.reindex(common_index)
        
        # Calculate alpha and beta
        from sklearn.linear_model import LinearRegression
        
        X = aligned_benchmark.values.reshape(-1, 1)
        y = aligned_returns.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        beta = model.coef_[0]
        alpha = model.intercept() * 252  # Annualized alpha
        
        # Test alpha significance
        n = len(aligned_returns)
        if n > 2:
            # Calculate residual standard error
            predictions = model.predict(X)
            residuals = y - predictions
            mse = np.sum(residuals**2) / (n - 2)
            se_alpha = np.sqrt(mse * (1/n + (aligned_benchmark.mean()**2) / np.sum((aligned_benchmark - aligned_benchmark.mean())**2)))
            
            # t-test for alpha
            t_stat_alpha = alpha / se_alpha if se_alpha > 0 else 0
            from scipy.stats import t as t_dist
            p_value_alpha = 2 * (1 - t_dist.cdf(abs(t_stat_alpha), n - 2))
            
            results.alpha_p_value = p_value_alpha
            results.alpha_significant = p_value_alpha < self.config.significance_level
        
        # Check if alpha meets requirement
        alpha_adequate = alpha >= self.config.benchmark_alpha_requirement
        
        # Calculate tracking error
        tracking_error = (aligned_returns - aligned_benchmark).std() * np.sqrt(252)
        results.tracking_error_acceptable = tracking_error <= self.config.max_tracking_error
        
        # Check beta stability (beta close to 1 for market-tracking strategies)
        results.beta_stable = 0.8 <= beta <= 1.2
        
        if not alpha_adequate:
            results.warnings.append(f"Alpha below requirement: {alpha:.2%} < {self.config.benchmark_alpha_requirement:.2%}")
        
        if not results.tracking_error_acceptable:
            results.warnings.append(f"High tracking error: {tracking_error:.2%}")
    
    def _calculate_overall_score(self, results: ValidationResults) -> None:
        """Calculate overall validation score"""
        
        score_components = [
            min(results.sample_size_score, 100) * 0.20,
            results.performance_score * 0.25,
            100 if results.sharpe_significance else 0 * 0.20,
            results.stability_score * 0.15,
            100 if results.returns_normal else 50 * 0.10,
            100 if len(results.critical_issues) == 0 else 0 * 0.10
        ]
        
        results.validation_score = sum(score_components)
        
        # Determine if overall valid
        results.is_valid = (
            results.validation_score >= 70 and
            len(results.critical_issues) == 0
        )
    
    def _generate_recommendation(self, results: ValidationResults) -> None:
        """Generate overall recommendation"""
        
        if results.is_valid and results.validation_score >= 85:
            results.recommendation = "ACCEPT"
            results.recommendation_reason = "Strong validation results with minimal concerns"
        elif results.is_valid and results.validation_score >= 70:
            results.recommendation = "CONDITIONAL"
            results.recommendation_reason = "Acceptable results but monitor specified warnings"
        else:
            results.recommendation = "REJECT"
            if results.critical_issues:
                results.recommendation_reason = f"Critical issues: {'; '.join(results.critical_issues[:2])}"
            else:
                results.recommendation_reason = f"Insufficient validation score: {results.validation_score:.1f}%"
    
    def bootstrap_performance_metrics(
        self, 
        returns: pd.Series, 
        n_samples: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Bootstrap performance metrics for robust confidence intervals
        
        Args:
            returns: Strategy returns series
            n_samples: Number of bootstrap samples
            
        Returns:
            Dictionary with bootstrap results
        """
        
        n_samples = n_samples or self.config.bootstrap_samples
        n_observations = len(returns)
        
        if n_observations < 10:
            logger.warning("Insufficient observations for bootstrap analysis")
            return {}
        
        logger.info(f"Running bootstrap analysis with {n_samples} samples")
        
        bootstrap_metrics = {
            'sharpe_ratios': [],
            'total_returns': [],
            'max_drawdowns': [],
            'volatilities': [],
            'win_rates': []
        }
        
        np.random.seed(42)  # For reproducibility
        
        for _ in range(n_samples):
            # Sample with replacement
            sample_indices = np.random.choice(n_observations, size=n_observations, replace=True)
            sample_returns = returns.iloc[sample_indices]
            
            # Calculate metrics
            total_return = (1 + sample_returns).prod() - 1
            annual_return = sample_returns.mean() * 252
            annual_volatility = sample_returns.std() * np.sqrt(252)
            sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
            
            # Calculate drawdown
            cumulative_returns = (1 + sample_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            win_rate = (sample_returns > 0).mean()
            
            bootstrap_metrics['sharpe_ratios'].append(sharpe_ratio)
            bootstrap_metrics['total_returns'].append(total_return)
            bootstrap_metrics['max_drawdowns'].append(max_drawdown)
            bootstrap_metrics['volatilities'].append(annual_volatility)
            bootstrap_metrics['win_rates'].append(win_rate)
        
        # Calculate confidence intervals
        confidence_intervals = {}
        for metric_name, values in bootstrap_metrics.items():
            values = np.array(values)
            confidence_intervals[metric_name] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'median': np.median(values),
                'confidence_interval_95': np.percentile(values, [2.5, 97.5]),
                'confidence_interval_99': np.percentile(values, [0.5, 99.5])
            }
        
        return {
            'bootstrap_config': {
                'n_samples': n_samples,
                'n_observations': n_observations
            },
            'confidence_intervals': confidence_intervals
        }


# Convenience functions
def create_statistical_validator(
    config: Optional[StatisticalValidationConfig] = None
) -> StatisticalValidator:
    """Create statistical validator instance"""
    return StatisticalValidator(config)


def validate_strategy_performance(
    returns: pd.Series,
    benchmark_returns: Optional[pd.Series] = None,
    config: Optional[StatisticalValidationConfig] = None
) -> ValidationResults:
    """
    Convenience function to validate strategy performance
    
    Args:
        returns: Strategy returns series
        benchmark_returns: Benchmark returns for comparison
        config: Optional validation configuration
        
    Returns:
        ValidationResults with comprehensive analysis
    """
    validator = StatisticalValidator(config)
    return validator.validate_backtest_results(returns, benchmark_returns)


def bootstrap_confidence_intervals(
    returns: pd.Series,
    n_samples: int = 10000
) -> Dict[str, Any]:
    """
    Convenience function for bootstrap confidence intervals
    
    Args:
        returns: Strategy returns series
        n_samples: Number of bootstrap samples
        
    Returns:
        Dictionary with bootstrap results
    """
    validator = StatisticalValidator()
    return validator.bootstrap_performance_metrics(returns, n_samples)