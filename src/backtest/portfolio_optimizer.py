"""
Advanced Portfolio Optimizer
============================

Sophisticated portfolio optimization with multiple objectives:
- Mean-variance optimization
- Risk parity allocation
- Black-Litterman model
- Factor-based optimization
- Robust optimization with uncertainty sets
- Dynamic rebalancing strategies

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from scipy.optimize import minimize, differential_evolution
from scipy.stats import multivariate_normal
from cvxpy import Parameter, Variable, Problem, Minimize, sum_squares, quad_form
import cvxpy as cp
from sklearn.covariance import LedoitWolf, ShrunkCovariance
import warnings

logger = logging.getLogger(__name__)


class OptimizationMethod(str, Enum):
    """Portfolio optimization methods"""
    MEAN_VARIANCE = "mean_variance"
    MINIMUM_VARIANCE = "minimum_variance"
    MAXIMUM_SHARPE = "maximum_sharpe"
    RISK_PARITY = "risk_parity"
    EQUAL_RISK = "equal_risk"
    EQUAL_WEIGHT = "equal_weight"
    BLACK_LITTERMAN = "black_litterman"
    FACTOR_MODEL = "factor_model"
    ROBUST = "robust"
    HIERARCHICAL = "hierarchical"


class RebalanceFrequency(str, Enum):
    """Rebalancing frequencies"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    VOLATILITY_TARGETED = "volatility_targeted"
    DRAWDOWN_CONTROLLED = "drawdown_controlled"


@dataclass
class OptimizationConfig:
    """Portfolio optimization configuration"""
    method: OptimizationMethod = OptimizationMethod.MEAN_VARIANCE
    risk_free_rate: float = 0.02
    target_return: Optional[float] = None
    target_volatility: Optional[float] = None
    max_weight: float = 1.0
    min_weight: float = 0.0
    leverage_limit: float = 1.0
    turnover_limit: float = 0.5

    # Risk constraints
    max_drawdown: Optional[float] = None
    var_limit: Optional[float] = None
    cvar_limit: Optional[float] = None

    # Factor model parameters
    n_factors: int = 5
    factor_exposure_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    # Robust optimization
    uncertainty_set: str = "box"  # box, ellipsoidal, polyhedral
    uncertainty_budget: float = 0.1

    # Black-Litterman
    views: List[Dict[str, Any]] = field(default_factory=list)
    view_confidence: List[float] = field(default_factory=list)
    tau: float = 0.025

    # Hierarchical clustering
    linkage_method: str = "ward"
    distance_metric: str = "euclidean"


@dataclass
class FactorModel:
    """Factor model for portfolio construction"""
    factor_returns: pd.DataFrame
    factor_loadings: pd.DataFrame
    idiosyncratic_var: pd.Series

    def get_expected_returns(self) -> pd.Series:
        """Get expected returns from factor model"""
        return self.factor_loadings @ self.factor_returns.mean()

    def get_covariance_matrix(self) -> pd.DataFrame:
        """Get covariance matrix from factor model"""
        factor_cov = self.factor_returns.cov() * 252  # Annualized
        return (
            self.factor_loadings @ factor_cov @ self.factor_loadings.T +
            np.diag(self.idiosyncratic_var)
        )


class PortfolioOptimizer:
    """
    Advanced portfolio optimizer with multiple methods
    """

    def __init__(self, config: OptimizationConfig):
        """
        Initialize portfolio optimizer

        Args:
            config: Optimization configuration
        """
        self.config = config

        # Internal state
        self.expected_returns: Optional[pd.Series] = None
        self.covariance_matrix: Optional[pd.DataFrame] = None
        self.n_assets: int = 0

        # Optimization results
        self.optimal_weights: Optional[pd.Series] = None
        self.optimization_status: Optional[str] = None
        self.optimization_metrics: Dict[str, float] = {}

        logger.info(f"Portfolio optimizer initialized with {config.method} method")

    def fit(self, returns: pd.DataFrame, lookback_window: int = 252) -> 'PortfolioOptimizer':
        """
        Fit optimizer to historical returns

        Args:
            returns: Historical returns DataFrame
            lookback_window: Lookback window for estimation

        Returns:
            Self for method chaining
        """
        try:
            # Use lookback window
            if len(returns) > lookback_window:
                returns = returns.iloc[-lookback_window:]

            # Estimate expected returns
            self.expected_returns = self._estimate_expected_returns(returns)

            # Estimate covariance matrix
            self.covariance_matrix = self._estimate_covariance_matrix(returns)

            self.n_assets = len(self.expected_returns)

            logger.info(f"Optimizer fitted to {len(returns)} observations")
            return self

        except Exception as e:
            logger.error(f"Fitting optimizer failed: {e}")
            raise

    def optimize(self) -> pd.Series:
        """
        Run portfolio optimization

        Returns:
            Optimal weights
        """
        try:
            if self.expected_returns is None or self.covariance_matrix is None:
                raise ValueError("Optimizer not fitted. Call fit() first.")

            if self.config.method == OptimizationMethod.MEAN_VARIANCE:
                self._optimize_mean_variance()
            elif self.config.method == OptimizationMethod.MINIMUM_VARIANCE:
                self._optimize_minimum_variance()
            elif self.config.method == OptimizationMethod.MAXIMUM_SHARPE:
                self._optimize_maximum_sharpe()
            elif self.config.method == OptimizationMethod.RISK_PARITY:
                self._optimize_risk_parity()
            elif self.config.method == OptimizationMethod.EQUAL_RISK:
                self._optimize_equal_risk()
            elif self.config.method == OptimizationMethod.EQUAL_WEIGHT:
                self._optimize_equal_weight()
            elif self.config.method == OptimizationMethod.BLACK_LITTERMAN:
                self._optimize_black_litterman()
            elif self.config.method == OptimizationMethod.FACTOR_MODEL:
                self._optimize_factor_model()
            elif self.config.method == OptimizationMethod.ROBUST:
                self._optimize_robust()
            elif self.config.method == OptimizationMethod.HIERARCHICAL:
                self._optimize_hierarchical()
            else:
                raise ValueError(f"Unknown optimization method: {self.config.method}")

            self._validate_weights()
            self._calculate_optimization_metrics()

            logger.info(f"Optimization completed: {self.optimization_status}")
            return self.optimal_weights

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise

    def optimize_portfolio(
        self,
        returns: pd.DataFrame,
        rebalance_frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
    ) -> pd.DataFrame:
        """
        Optimize portfolio over time with rebalancing

        Args:
            returns: Historical returns DataFrame
            rebalance_frequency: Rebalancing frequency

        Returns:
            DataFrame with optimal weights over time
        """
        rebalance_dates = self._get_rebalance_dates(returns.index, rebalance_frequency)
        weights_history = []

        for i, rebalance_date in enumerate(rebalance_dates):
            # Get data up to rebalance date
            historical_returns = returns.loc[:rebalance_date]

            # Fit and optimize
            self.fit(historical_returns)
            weights = self.optimize()

            # Store weights
            weights_history.append(weights.rename(rebalance_date))

            if i % 10 == 0:
                logger.info(f"Optimized for {len(weights_history)} rebalance dates")

        # Combine weights
        weights_df = pd.concat(weights_history, axis=1).T
        weights_df.index.name = 'date'

        return weights_df

    def _estimate_expected_returns(self, returns: pd.DataFrame) -> pd.Series:
        """Estimate expected returns"""

        # Use James-Stein shrinkage estimator
        sample_mean = returns.mean()

        # Shrink towards equal mean
        grand_mean = sample_mean.mean()
        shrinkage_factor = max(0, 1 - (self.n_assets + 2) / (returns.shape[0] - 1))

        expected_returns = shrinkage_factor * grand_mean + (1 - shrinkage_factor) * sample_mean

        # Annualize
        return expected_returns * 252

    def _estimate_covariance_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Estimate covariance matrix with shrinkage"""

        # Use Ledoit-Wolf shrinkage
        lw = LedoitWolf()
        lw.fit(returns)

        # Annualize
        cov_matrix = pd.DataFrame(
            lw.covariance_ * 252,
            index=returns.columns,
            columns=returns.columns
        )

        # Ensure positive definite
        eigenvalues = np.linalg.eigvals(cov_matrix)
        min_eigenvalue = np.min(eigenvalues)

        if min_eigenvalue < 0:
            # Add small positive constant to diagonal
            cov_matrix += np.eye(self.n_assets) * abs(min_eigenvalue) * 1.01

        return cov_matrix

    def _optimize_mean_variance(self) -> None:
        """Mean-variance optimization"""

        n = self.n_assets
        mu = self.expected_returns.values
        Sigma = self.covariance_matrix.values

        # Define optimization variables
        w = Variable(n)

        # Define objective
        if self.config.target_return is not None:
            # Minimize variance for given return
            objective = Minimize(quad_form(w, Sigma))
            constraints = [
                w @ mu == self.config.target_return,
                sum(w) == 1
            ]
        elif self.config.target_volatility is not None:
            # Maximize return for given volatility
            objective = Minimize(-w @ mu)
            constraints = [
                quad_form(w, Sigma) <= self.config.target_volatility**2,
                sum(w) == 1
            ]
        else:
            # Maximize Sharpe ratio
            objective = Minimize(quad_form(w, Sigma))
            constraints = [
                w @ mu >= 0.001,  # Minimum return
                sum(w) == 1
            ]

        # Add weight constraints
        constraints.extend([
            w >= self.config.min_weight,
            w <= self.config.max_weight,
            sum(w) <= self.config.leverage_limit
        ])

        # Solve optimization
        problem = Problem(objective, constraints)
        problem.solve()

        if problem.status == 'optimal':
            self.optimal_weights = pd.Series(w.value, index=self.expected_returns.index)
            self.optimization_status = 'optimal'
        else:
            raise ValueError(f"Optimization failed: {problem.status}")

    def _optimize_minimum_variance(self) -> None:
        """Minimum variance optimization"""

        n = self.n_assets
        Sigma = self.covariance_matrix.values

        # Define optimization variables
        w = Variable(n)

        # Minimize variance
        objective = Minimize(quad_form(w, Sigma))

        # Constraints
        constraints = [
            sum(w) == 1,
            w >= self.config.min_weight,
            w <= self.config.max_weight
        ]

        # Solve
        problem = Problem(objective, constraints)
        problem.solve()

        if problem.status == 'optimal':
            self.optimal_weights = pd.Series(w.value, index=self.expected_returns.index)
            self.optimization_status = 'optimal'
        else:
            raise ValueError(f"Optimization failed: {problem.status}")

    def _optimize_maximum_sharpe(self) -> None:
        """Maximum Sharpe ratio optimization"""

        n = self.n_assets
        mu = self.expected_returns.values
        Sigma = self.covariance_matrix.values
        rf = self.config.risk_free_rate

        # Transform to convex problem (see Boyd & Vandenberghe)
        w = Variable(n)
        kappa = Variable()

        # Objective: maximize Sharpe ratio
        # Equivalent to minimizing - (w' * (mu - rf)) / sqrt(w' * Sigma * w)
        objective = Minimize(kappa)

        # Constraints
        constraints = [
            sum(w) == 1,
            quad_form(w, Sigma) <= kappa**2,
            w @ (mu - rf) >= 1,
            w >= self.config.min_weight,
            w <= self.config.max_weight
        ]

        # Solve
        problem = Problem(objective, constraints)
        problem.solve()

        if problem.status == 'optimal':
            self.optimal_weights = pd.Series(w.value, index=self.expected_returns.index)
            self.optimization_status = 'optimal'
        else:
            raise ValueError(f"Optimization failed: {problem.status}")

    def _optimize_risk_parity(self) -> None:
        """Risk parity optimization"""

        n = self.n_assets
        Sigma = self.covariance_matrix.values

        # Risk parity: equalize risk contributions
        def risk_parity_objective(weights):
            weights = np.abs(weights)  # Ensure positive
            weights = weights / np.sum(weights)  # Normalize

            portfolio_vol = np.sqrt(weights.T @ Sigma @ weights)
            marginal_contrib = Sigma @ weights
            risk_contrib = weights * marginal_contrib / portfolio_vol

            # Minimize squared differences from target risk contribution
            target_risk = 1.0 / n
            return np.sum((risk_contrib - target_risk)**2)

        # Constraints
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = [(self.config.min_weight, self.config.max_weight) for _ in range(n)]

        # Initial guess (equal weights)
        x0 = np.ones(n) / n

        # Optimize
        result = minimize(
            risk_parity_objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'ftol': 1e-9, 'disp': False}
        )

        if result.success:
            self.optimal_weights = pd.Series(result.x, index=self.expected_returns.index)
            self.optimization_status = 'optimal'
        else:
            raise ValueError(f"Risk parity optimization failed: {result.message}")

    def _optimize_equal_risk(self) -> None:
        """Equal risk contribution optimization"""

        n = self.n_assets
        Sigma = self.covariance_matrix.values

        # Equal risk using convex optimization
        w = Variable(n)
        risk_budget = Parameter(1.0 / n)

        portfolio_risk = cp.sqrt(quad_form(w, Sigma))
        marginal_risk = Sigma @ w
        risk_contribution = cp.multiply(w, marginal_risk) / portfolio_risk

        # Minimize variance of risk contributions
        objective = Minimize(cp.sum_squares(risk_contribution - risk_budget))

        constraints = [
            sum(w) == 1,
            w >= self.config.min_weight,
            w <= self.config.max_weight
        ]

        problem = Problem(objective, constraints)
        problem.solve()

        if problem.status == 'optimal':
            self.optimal_weights = pd.Series(w.value, index=self.expected_returns.index)
            self.optimization_status = 'optimal'
        else:
            raise ValueError(f"Equal risk optimization failed: {problem.status}")

    def _optimize_equal_weight(self) -> None:
        """Equal weight optimization (1/N portfolio)"""

        n = self.n_assets
        weights = np.ones(n) / n

        # Apply weight limits
        weights = np.clip(weights, self.config.min_weight, self.config.max_weight)
        weights = weights / np.sum(weights)  # Renormalize

        self.optimal_weights = pd.Series(weights, index=self.expected_returns.index)
        self.optimization_status = 'optimal'

    def _optimize_black_litterman(self) -> None:
        """Black-Litterman optimization"""

        if not self.config.views:
            raise ValueError("No views provided for Black-Litterman optimization")

        n = self.n_assets
        mu = self.expected_returns.values
        Sigma = self.covariance_matrix.values

        # Black-Litterman parameters
        tau = self.config.tau

        # Build view matrix P and view vector Q
        P = []
        Q = []

        for view in self.config.views:
            if view['type'] == 'absolute':
                p_vec = np.zeros(n)
                p_vec[self.expected_returns.index.get_loc(view['asset'])] = 1
                P.append(p_vec)
                Q.append(view['return'])
            elif view['type'] == 'relative':
                p_vec = np.zeros(n)
                p_vec[self.expected_returns.index.get_loc(view['asset1'])] = 1
                p_vec[self.expected_returns.index.get_loc(view['asset2'])] = -1
                P.append(p_vec)
                Q.append(view['spread'])

        P = np.array(P)
        Q = np.array(Q)

        # View uncertainty matrix Omega
        if self.config.view_confidence:
            Omega = np.diag(1.0 / np.array(self.config.view_confidence))
        else:
            Omega = np.diag(P @ Sigma @ P.T)  # Simple heuristic

        # Black-Litterman expected returns
        pi = mu  # Implied equilibrium returns (using historical for simplicity)
        tau_sigma = tau * Sigma

        # Calculate posterior returns
        tau_sigma_inv = np.linalg.inv(tau_sigma)
        omega_inv = np.linalg.inv(Omega)

        posterior_mu = np.linalg.inv(
            tau_sigma_inv + P.T @ omega_inv @ P
        ) @ (
            tau_sigma_inv @ pi + P.T @ omega_inv @ Q
        )

        # Posterior covariance
        posterior_sigma = np.linalg.inv(
            tau_sigma_inv + P.T @ omega_inv @ P
        )

        # Use posterior for mean-variance optimization
        self.expected_returns = pd.Series(posterior_mu, index=self.expected_returns.index)
        self.covariance_matrix = pd.DataFrame(
            posterior_sigma,
            index=self.expected_returns.index,
            columns=self.expected_returns.index
        )

        # Run mean-variance optimization
        self._optimize_mean_variance()

    def _optimize_factor_model(self) -> None:
        """Factor model optimization"""

        # This would require factor data
        # Simplified implementation using PCA
        n_factors = self.config.n_factors

        # Perform PCA on returns
        from sklearn.decomposition import PCA

        # Get returns matrix (need to fit on actual returns)
        # This is a placeholder - in practice, you'd pass factor data
        pca = PCA(n_components=n_factors)

        # Use identity for factor loadings (placeholder)
        n = self.n_assets
        factor_loadings = np.random.randn(n, n_factors)
        factor_cov = np.eye(n_factors) * 0.1**2  # 10% annual factor vol

        # Factor model covariance
        model_cov = factor_loadings @ factor_cov @ factor_loadings.T

        # Add idiosyncratic risk
        idio_var = np.diag(self.covariance_matrix) - np.diag(model_cov)
        model_cov += np.diag(np.maximum(idio_var, 0.01**2))

        self.covariance_matrix = pd.DataFrame(
            model_cov,
            index=self.expected_returns.index,
            columns=self.expected_returns.index
        )

        # Apply factor exposure limits if specified
        if self.config.factor_exposure_limits:
            self._apply_factor_exposure_limits(factor_loadings)

        # Run mean-variance optimization
        self._optimize_mean_variance()

    def _optimize_robust(self) -> None:
        """Robust optimization with uncertainty"""

        n = self.n_assets
        mu = self.expected_returns.values
        Sigma = self.covariance_matrix.values

        # Uncertainty set for expected returns
        delta = self.config.uncertainty_budget

        if self.config.uncertainty_set == "box":
            # Box uncertainty set
            mu_lower = mu - delta
            mu_upper = mu + delta

            # Robust optimization: maximize worst-case return
            w = Variable(n)
            mu_robust = Parameter(n)

            objective = Minimize(quad_form(w, Sigma) - mu_robust @ w)

            constraints = [
                sum(w) == 1,
                w >= self.config.min_weight,
                w <= self.config.max_weight,
                mu_robust <= mu_upper,
                mu_robust >= mu_lower
            ]

        elif self.config.uncertainty_set == "ellipsoidal":
            # Ellipsoidal uncertainty set
            w = Variable(n)

            # Worst-case expected returns under ellipsoidal uncertainty
            worst_case_mu = mu - delta * np.diag(np.sqrt(np.diag(Sigma))) @ cp.sign(w)

            objective = Minimize(quad_form(w, Sigma) - worst_case_mu @ w)

            constraints = [
                sum(w) == 1,
                w >= self.config.min_weight,
                w <= self.config.max_weight
            ]

        problem = Problem(objective, constraints)
        problem.solve()

        if problem.status == 'optimal':
            self.optimal_weights = pd.Series(w.value, index=self.expected_returns.index)
            self.optimization_status = 'optimal'
        else:
            raise ValueError(f"Robust optimization failed: {problem.status}")

    def _optimize_hierarchical(self) -> None:
        """Hierarchical risk parity optimization"""

        # Calculate correlation matrix
        corr_matrix = self.covariance_matrix.corr()

        # Calculate distance matrix
        distance_matrix = np.sqrt((1 - corr_matrix) / 2)

        # Hierarchical clustering
        from scipy.cluster.hierarchy import linkage, fcluster
        from scipy.spatial.distance import squareform

        # Convert to condensed distance matrix
        condensed_distances = squareform(distance_matrix)

        # Perform linkage
        Z = linkage(
            condensed_distances,
            method=self.config.linkage_method
        )

        # Get cluster assignments
        n_clusters = self.n_assets  # One cluster per asset initially
        clusters = fcluster(Z, n_clusters, criterion='maxclust')

        # Inverse volatility weighting within clusters
        weights = np.zeros(self.n_assets)

        for cluster_id in np.unique(clusters):
            cluster_assets = np.where(clusters == cluster_id)[0]

            if len(cluster_assets) == 1:
                weights[cluster_assets[0]] = 1.0 / len(np.unique(clusters))
            else:
                # Inverse volatility weighting
                volatilities = np.sqrt(np.diag(self.covariance_matrix))[cluster_assets]
                inv_vol = 1.0 / volatilities
                inv_vol_weights = inv_vol / np.sum(inv_vol)

                weights[cluster_assets] = inv_vol_weights * (1.0 / len(np.unique(clusters)))

        self.optimal_weights = pd.Series(weights, index=self.expected_returns.index)
        self.optimization_status = 'optimal'

    def _apply_factor_exposure_limits(self, factor_loadings: np.ndarray) -> None:
        """Apply factor exposure limits to optimization"""

        # This would be implemented in the optimization constraints
        # Placeholder for now
        pass

    def _get_rebalance_dates(
        self,
        date_index: pd.DatetimeIndex,
        frequency: RebalanceFrequency
    ) -> List[pd.Timestamp]:
        """Get rebalancing dates"""

        if frequency == RebalanceFrequency.DAILY:
            return date_index.tolist()
        elif frequency == RebalanceFrequency.WEEKLY:
            return date_index[date_index.weekday == 0].tolist()  # Mondays
        elif frequency == RebalanceFrequency.MONTHLY:
            return date_index[date_index.is_month_start].tolist()
        elif frequency == RebalanceFrequency.QUARTERLY:
            return date_index[
                (date_index.is_month_start) & (date_index.month % 3 == 0)
            ].tolist()
        else:
            # Default to monthly
            return date_index[date_index.is_month_start].tolist()

    def _validate_weights(self) -> None:
        """Validate optimal weights"""

        if self.optimal_weights is None:
            return

        # Check weight constraints
        if any(self.optimal_weights < self.config.min_weight - 1e-6):
            logger.warning("Some weights below minimum constraint")

        if any(self.optimal_weights > self.config.max_weight + 1e-6):
            logger.warning("Some weights above maximum constraint")

        # Check leverage
        leverage = abs(self.optimal_weights).sum()
        if leverage > self.config.leverage_limit + 1e-6:
            logger.warning(f"Leverage {leverage:.2f} exceeds limit {self.config.leverage_limit}")

    def _calculate_optimization_metrics(self) -> None:
        """Calculate optimization metrics"""

        if self.optimal_weights is None:
            return

        w = self.optimal_weights.values

        # Expected return
        expected_return = w @ self.expected_returns.values

        # Expected volatility
        expected_volatility = np.sqrt(w @ self.covariance_matrix.values @ w)

        # Sharpe ratio
        sharpe_ratio = (expected_return - self.config.risk_free_rate) / expected_volatility

        # Portfolio metrics
        self.optimization_metrics = {
            'expected_return': expected_return,
            'expected_volatility': expected_volatility,
            'sharpe_ratio': sharpe_ratio,
            'leverage': abs(w).sum(),
            'max_weight': np.max(w),
            'min_weight': np.min(w)
        }

    def get_portfolio_metrics(self) -> Dict[str, float]:
        """Get portfolio performance metrics"""
        return self.optimization_metrics

    def get_risk_contributions(self) -> pd.Series:
        """Calculate risk contributions of each asset"""

        if self.optimal_weights is None:
            raise ValueError("Optimization not performed")

        w = self.optimal_weights.values
        Sigma = self.covariance_matrix.values

        # Calculate marginal contributions
        portfolio_vol = np.sqrt(w @ Sigma @ w)
        marginal_contrib = Sigma @ w

        # Risk contributions
        risk_contrib = w * marginal_contrib / portfolio_vol

        return pd.Series(risk_contrib, index=self.expected_returns.index)

    def get_effective_assets(self) -> float:
        """Calculate effective number of assets (inverse Herfindahl)"""

        if self.optimal_weights is None:
            raise ValueError("Optimization not performed")

        hhi = np.sum(self.optimal_weights**2)
        return 1.0 / hhi

    def plot_optimization_results(self) -> None:
        """Plot optimization results (requires matplotlib)"""

        try:
            import matplotlib.pyplot as plt

            if self.optimal_weights is None:
                raise ValueError("Optimization not performed")

            # Plot weights
            plt.figure(figsize=(12, 6))

            plt.subplot(1, 2, 1)
            self.optimal_weights.plot(kind='bar')
            plt.title('Optimal Portfolio Weights')
            plt.xticks(rotation=45)
            plt.ylabel('Weight')

            # Plot risk contributions
            plt.subplot(1, 2, 2)
            risk_contrib = self.get_risk_contributions()
            risk_contrib.plot(kind='bar')
            plt.title('Risk Contributions')
            plt.xticks(rotation=45)
            plt.ylabel('Risk Contribution')

            plt.tight_layout()
            plt.show()

        except ImportError:
            logger.warning("Matplotlib not available for plotting")


# Utility functions
def create_optimization_config(
    method: OptimizationMethod = OptimizationMethod.MEAN_VARIANCE,
    **kwargs
) -> OptimizationConfig:
    """Create optimization configuration with defaults"""

    config = {
        'method': method,
        'risk_free_rate': 0.02,
        'max_weight': 1.0,
        'min_weight': 0.0,
        'leverage_limit': 1.0
    }

    config.update(kwargs)
    return OptimizationConfig(**config)


def calculate_risk_metrics(weights: pd.Series, returns: pd.DataFrame) -> Dict[str, float]:
    """Calculate portfolio risk metrics for given weights"""

    mu = returns.mean() * 252
    Sigma = returns.cov() * 252
    w = weights.values

    # Portfolio return and volatility
    portfolio_return = w @ mu
    portfolio_vol = np.sqrt(w @ Sigma @ w)

    # Maximum drawdown (simplified)
    portfolio_returns = (returns @ w).cumsum()
    running_max = np.maximum.accumulate(portfolio_returns)
    drawdown = portfolio_returns - running_max
    max_drawdown = np.min(drawdown)

    # VaR and CVaR (5% level)
    daily_returns = returns @ w
    var_95 = np.percentile(daily_returns, 5)
    cvar_95 = np.mean(daily_returns[daily_returns <= var_95])

    return {
        'expected_return': portfolio_return,
        'volatility': portfolio_vol,
        'sharpe_ratio': portfolio_return / portfolio_vol,
        'max_drawdown': max_drawdown,
        'var_95': var_95,
        'cvar_95': cvar_95
    }


__all__ = [
    'PortfolioOptimizer',
    'OptimizationConfig',
    'OptimizationMethod',
    'RebalanceFrequency',
    'FactorModel',
    'create_optimization_config',
    'calculate_risk_metrics'
]