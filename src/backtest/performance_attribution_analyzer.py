"""
Performance Attribution Analyzer
===============================

Comprehensive performance attribution analysis including:
- Asset allocation attribution
- Security selection attribution
- Factor attribution
- Sector attribution
- Interaction effects
- Multi-level decomposition
- Contribution analysis

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import warnings
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class AttributionType(str, Enum):
    """Attribution analysis types"""
    ASSET_ALLOCATION = "asset_allocation"
    SECURITY_SELECTION = "security_selection"
    SECTOR = "sector"
    FACTOR = "factor"
    STYLE = "style"
    CURRENCY = "currency"
    INTERACTION = "interaction"


class AttributionMethod(str, Enum):
    """Attribution calculation methods"""
    BRINSON_FACHLER = "brinson_fachler"
    BRINSON_HOOD_BEEbower = "brinson_hood_beebower"
    TOP_DOWN = "top_down"
    BOTTOM_UP = "bottom_up"
    MULTI_FACTOR = "multi_factor"
    HOLDINGS_BASED = "holdings_based"
    RETURNS_BASED = "returns_based"


@dataclass
class AttributionConfig:
    """Attribution analysis configuration"""
    method: AttributionMethod = AttributionMethod.BRINSON_FACHLER
    frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    currency: str = "USD"

    # Sector analysis
    sector_mapping: Dict[str, str] = field(default_factory=dict)
    sector_weights: Dict[str, float] = field(default_factory=dict)

    # Factor model
    factor_model: Optional[str] = None  # Fama-French, Barra, custom
    factor_data: Optional[pd.DataFrame] = None

    # Currency analysis
    currency_data: Optional[pd.DataFrame] = None
    base_currency: str = "USD"

    # Performance thresholds
    min_weight_threshold: float = 0.001  # 0.1%
    min_return_threshold: float = 0.0001  # 0.01%

    # Output settings
    include_interaction: bool = True
    include_benchmark_comparison: bool = True
    include_factor_attribution: bool = True


@dataclass
class AttributionResult:
    """Attribution analysis result"""
    # Overall attribution
    total_return: float
    benchmark_return: float
    active_return: float

    # Attribution components
    allocation_effect: Dict[str, float]
    selection_effect: Dict[str, float]
    interaction_effect: Dict[str, float]

    # Breakdown by category
    sector_attribution: Dict[str, Dict[str, float]]
    factor_attribution: Dict[str, float]
    currency_attribution: Dict[str, float]

    # Time series data
    attribution_over_time: pd.DataFrame

    # Summary statistics
    contribution_summary: pd.DataFrame

    # Risk attribution
    risk_attribution: Optional[Dict[str, float]] = None


class PerformanceAttributionAnalyzer:
    """
    Performance attribution analyzer with multiple methods
    """

    def __init__(self, config: AttributionConfig):
        """
        Initialize attribution analyzer

        Args:
            config: Attribution configuration
        """
        self.config = config

        # Internal state
        self.portfolio_data: Optional[pd.DataFrame] = None
        self.benchmark_data: Optional[pd.DataFrame] = None
        self.sector_mapping: Optional[pd.Series] = None

        # Factor model
        self.factor_model = None
        self.factor_loadings: Optional[pd.DataFrame] = None

        # Results
        self.attribution_result: Optional[AttributionResult] = None

        logger.info(f"Performance attribution analyzer initialized with {config.method} method")

    def analyze(
        self,
        portfolio_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        prices: Optional[pd.DataFrame] = None
    ) -> AttributionResult:
        """
        Run performance attribution analysis

        Args:
            portfolio_returns: Portfolio returns DataFrame
            portfolio_weights: Portfolio weights DataFrame
            benchmark_weights: Benchmark weights DataFrame
            benchmark_returns: Benchmark returns DataFrame
            prices: Price data for security-level analysis

        Returns:
            AttributionResult: Comprehensive attribution results
        """
        try:
            logger.info("Starting performance attribution analysis")

            # Prepare data
            self._prepare_data(
                portfolio_returns,
                portfolio_weights,
                benchmark_weights,
                benchmark_returns,
                prices
            )

            # Run attribution based on method
            if self.config.method == AttributionMethod.BRINSON_FACHLER:
                self._run_brinson_fachler_attribution()
            elif self.config.method == AttributionMethod.BRINSON_HOOD_BEEbower:
                self._run_brinson_hood_beebower_attribution()
            elif self.config.method == AttributionMethod.TOP_DOWN:
                self._run_top_down_attribution()
            elif self.config.method == AttributionMethod.BOTTOM_UP:
                self._run_bottom_up_attribution()
            elif self.config.method == AttributionMethod.MULTI_FACTOR:
                self._run_multi_factor_attribution()
            else:
                raise ValueError(f"Unknown attribution method: {self.config.method}")

            # Add additional analyses
            if self.config.include_factor_attribution:
                self._add_factor_attribution()

            if self.config.sector_mapping:
                self._add_sector_attribution()

            # Create time series attribution
            self._create_time_series_attribution()

            # Create contribution summary
            self._create_contribution_summary()

            logger.info("Performance attribution analysis completed")
            return self.attribution_result

        except Exception as e:
            logger.error(f"Attribution analysis failed: {e}")
            raise

    def _prepare_data(
        self,
        portfolio_returns: pd.DataFrame,
        portfolio_weights: pd.DataFrame,
        benchmark_weights: pd.DataFrame,
        benchmark_returns: pd.DataFrame,
        prices: Optional[pd.DataFrame] = None
    ) -> None:
        """Prepare data for attribution analysis"""

        # Convert to float
        self.portfolio_returns = portfolio_returns.astype(float)
        self.portfolio_weights = portfolio_weights.astype(float)
        self.benchmark_weights = benchmark_weights.astype(float)
        self.benchmark_returns = benchmark_returns.astype(float)

        # Store prices if provided
        self.prices = prices

        # Create sector mapping if provided
        if self.config.sector_mapping:
            self.sector_mapping = pd.Series(self.config.sector_mapping)

        # Align dates
        common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
        self.common_dates = common_dates

        # Calculate portfolio and benchmark returns from weights
        if prices is not None:
            self.portfolio_return_series = self._calculate_portfolio_returns_from_weights(
                portfolio_weights, prices
            )
            self.benchmark_return_series = self._calculate_portfolio_returns_from_weights(
                benchmark_weights, prices
            )
        else:
            self.portfolio_return_series = portfolio_returns.sum(axis=1)
            self.benchmark_return_series = benchmark_returns.sum(axis=1)

    def _calculate_portfolio_returns_from_weights(
        self,
        weights: pd.DataFrame,
        prices: pd.DataFrame
    ) -> pd.Series:
        """Calculate portfolio returns from weights and prices"""

        asset_returns = prices.pct_change().dropna()
        portfolio_returns = (weights.shift(1) * asset_returns).sum(axis=1)
        return portfolio_returns.reindex(weights.index, fill_value=0)

    def _run_brinson_fachler_attribution(self) -> None:
        """Run Brinson-Fachler attribution analysis"""

        dates = self.portfolio_weights.index
        assets = self.portfolio_weights.columns

        # Initialize attribution results
        allocation_effect = {}
        selection_effect = {}
        interaction_effect = {}

        attribution_over_time = []

        for date in dates[1:]:  # Skip first date
            # Get weights for current and previous period
            prev_date = dates[dates.get_loc(date) - 1]

            portfolio_w = self.portfolio_weights.loc[prev_date]
            benchmark_w = self.benchmark_weights.loc[prev_date]

            # Get asset returns for current period
            asset_returns = self.portfolio_returns.loc[date]

            # Skip if no data
            if asset_returns.isnull().all():
                continue

            # Calculate portfolio and benchmark returns for the period
            portfolio_return = (portfolio_w * asset_returns).sum()
            benchmark_return = (benchmark_w * asset_returns).sum()

            # Calculate attribution effects
            for asset in assets:
                # Allocation effect
                allocation = (portfolio_w[asset] - benchmark_w[asset]) * \
                           (asset_returns[asset] - benchmark_return)

                # Selection effect
                selection = benchmark_w[asset] * (asset_returns[asset] - benchmark_return)

                # Interaction effect
                interaction = (portfolio_w[asset] - benchmark_w[asset]) * \
                            (asset_returns[asset] - benchmark_return)

                # Accumulate effects
                if asset not in allocation_effect:
                    allocation_effect[asset] = 0
                    selection_effect[asset] = 0
                    interaction_effect[asset] = 0

                allocation_effect[asset] += allocation
                selection_effect[asset] += selection
                interaction_effect[asset] += interaction

            # Store period attribution
            period_attribution = {
                'date': date,
                'allocation_effect': sum(allocation_effect.values()),
                'selection_effect': sum(selection_effect.values()),
                'interaction_effect': sum(interaction_effect.values()),
                'active_return': portfolio_return - benchmark_return
            }

            attribution_over_time.append(period_attribution)

        # Create result
        self.attribution_result = AttributionResult(
            total_return=self.portfolio_return_series.sum(),
            benchmark_return=self.benchmark_return_series.sum(),
            active_return=self.portfolio_return_series.sum() - self.benchmark_return_series.sum(),
            allocation_effect=allocation_effect,
            selection_effect=selection_effect,
            interaction_effect=interaction_effect,
            sector_attribution={},
            factor_attribution={},
            currency_attribution={},
            attribution_over_time=pd.DataFrame(attribution_over_time),
            contribution_summary=pd.DataFrame()
        )

    def _run_brinson_hood_beebower_attribution(self) -> None:
        """Run Brinson-Hood-Beebower attribution"""

        # Similar to Brinson-Fachler but without interaction effect
        dates = self.portfolio_weights.index
        assets = self.portfolio_weights.columns

        allocation_effect = {}
        selection_effect = {}

        for date in dates[1:]:
            prev_date = dates[dates.get_loc(date) - 1]

            portfolio_w = self.portfolio_weights.loc[prev_date]
            benchmark_w = self.benchmark_weights.loc[prev_date]

            asset_returns = self.portfolio_returns.loc[date]

            if asset_returns.isnull().all():
                continue

            benchmark_return = (benchmark_w * asset_returns).sum()

            for asset in assets:
                # Allocation effect
                allocation = (portfolio_w[asset] - benchmark_w[asset]) * benchmark_return

                # Selection effect
                selection = benchmark_w[asset] * (asset_returns[asset] - benchmark_return)

                if asset not in allocation_effect:
                    allocation_effect[asset] = 0
                    selection_effect[asset] = 0

                allocation_effect[asset] += allocation
                selection_effect[asset] += selection

        # Create result without interaction
        self.attribution_result = AttributionResult(
            total_return=self.portfolio_return_series.sum(),
            benchmark_return=self.benchmark_return_series.sum(),
            active_return=self.portfolio_return_series.sum() - self.benchmark_return_series.sum(),
            allocation_effect=allocation_effect,
            selection_effect=selection_effect,
            interaction_effect={},
            sector_attribution={},
            factor_attribution={},
            currency_attribution={},
            attribution_over_time=pd.DataFrame(),
            contribution_summary=pd.DataFrame()
        )

    def _run_top_down_attribution(self) -> None:
        """Run top-down attribution (sector level first, then security level)"""

        # First calculate sector-level attribution
        if not self.sector_mapping:
            # Create simple sector mapping if not provided
            self.sector_mapping = pd.Series(
                index=self.portfolio_weights.columns,
                data='Unknown'
            )

        # Aggregate weights by sector
        portfolio_sector_weights = self._aggregate_weights_by_sector(self.portfolio_weights)
        benchmark_sector_weights = self._aggregate_weights_by_sector(self.benchmark_weights)

        # Aggregate returns by sector
        portfolio_sector_returns = self._aggregate_returns_by_sector(self.portfolio_returns)
        benchmark_sector_returns = self._aggregate_returns_by_sector(self.benchmark_returns)

        # Calculate sector attribution
        sector_allocation = {}
        sector_selection = {}

        for date in self.portfolio_weights.index[1:]:
            prev_date = self.portfolio_weights.index[self.portfolio_weights.index.get_loc(date) - 1]

            portfolio_w = portfolio_sector_weights.loc[prev_date]
            benchmark_w = benchmark_sector_weights.loc[prev_date]

            sector_returns = portfolio_sector_returns.loc[date]

            for sector in portfolio_w.index:
                allocation = (portfolio_w[sector] - benchmark_w[sector]) * sector_returns[sector]
                selection = benchmark_w[sector] * sector_returns[sector]

                if sector not in sector_allocation:
                    sector_allocation[sector] = 0
                    sector_selection[sector] = 0

                sector_allocation[sector] += allocation
                sector_selection[sector] += selection

        # Store sector attribution
        self.sector_attribution = {
            sector: {
                'allocation': sector_allocation.get(sector, 0),
                'selection': sector_selection.get(sector, 0)
            }
            for sector in self.sector_mapping.unique()
        }

        # Then run Brinson-Fachler at security level
        self._run_brinson_fachler_attribution()

    def _run_bottom_up_attribution(self) -> None:
        """Run bottom-up attribution (security level first, then aggregate)"""

        # Start with security-level attribution
        self._run_brinson_fachler_attribution()

        # Aggregate to sector level if sector mapping provided
        if self.sector_mapping is not None:
            self.attribution_result.sector_attribution = self._aggregate_attribution_by_sector()

    def _run_multi_factor_attribution(self) -> None:
        """Run multi-factor attribution"""

        if self.config.factor_data is None:
            raise ValueError("Factor data required for multi-factor attribution")

        # Run regression to get factor exposures
        factor_returns = self.config.factor_data

        # Calculate excess returns
        excess_returns = self.portfolio_return_series - self.benchmark_return_series

        # Align data
        common_dates = excess_returns.index.intersection(factor_returns.index)
        excess_returns = excess_returns.loc[common_dates]
        factor_returns = factor_returns.loc[common_dates]

        # Run regression
        X = factor_returns.values
        y = excess_returns.values

        model = LinearRegression()
        model.fit(X, y)

        # Calculate factor contributions
        factor_contributions = {}
        for i, factor in enumerate(factor_returns.columns):
            contribution = model.coef_[i] * factor_returns.mean()
            factor_contributions[factor] = contribution

        # Store factor attribution
        self.attribution_result.factor_attribution = factor_contributions

    def _add_factor_attribution(self) -> None:
        """Add factor attribution using PCA"""

        if self.prices is None:
            return

        # Calculate returns
        asset_returns = self.prices.pct_change().dropna()

        # Run PCA
        n_factors = min(5, len(asset_returns.columns))
        pca = PCA(n_components=n_factors)
        factor_returns = pd.DataFrame(
            pca.fit_transform(asset_returns),
            index=asset_returns.index,
            columns=[f'Factor_{i+1}' for i in range(n_factors)]
        )

        # Use factor data for attribution
        self.config.factor_data = factor_returns
        self._run_multi_factor_attribution()

    def _add_sector_attribution(self) -> None:
        """Add sector-level attribution"""

        if self.sector_mapping is None:
            return

        # Aggregate weights and returns by sector
        portfolio_sector_weights = self._aggregate_weights_by_sector(self.portfolio_weights)
        benchmark_sector_weights = self._aggregate_weights_by_sector(self.benchmark_weights)

        # Calculate sector attribution
        self.attribution_result.sector_attribution = {}

        for date in portfolio_sector_weights.index:
            if date in benchmark_sector_weights.index:
                portfolio_w = portfolio_sector_weights.loc[date]
                benchmark_w = benchmark_sector_weights.loc[date]

                for sector in self.sector_mapping.unique():
                    if sector in portfolio_w.index and sector in benchmark_w.index:
                        allocation_effect = (portfolio_w[sector] - benchmark_w[sector])

                        if sector not in self.attribution_result.sector_attribution:
                            self.attribution_result.sector_attribution[sector] = {
                                'allocation': 0,
                                'selection': 0
                            }

                        self.attribution_result.sector_attribution[sector]['allocation'] += allocation_effect

    def _aggregate_weights_by_sector(self, weights: pd.DataFrame) -> pd.DataFrame:
        """Aggregate weights by sector"""

        sector_weights = pd.DataFrame(index=weights.index, columns=self.sector_mapping.unique())

        for date in weights.index:
            date_weights = weights.loc[date]
            for sector in self.sector_mapping.unique():
                sector_assets = self.sector_mapping[self.sector_mapping == sector].index
                sector_weights.loc[date, sector] = date_weights[sector_assets].sum()

        return sector_weights.fillna(0)

    def _aggregate_returns_by_sector(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Aggregate returns by sector"""

        sector_returns = pd.DataFrame(index=returns.index, columns=self.sector_mapping.unique())

        for date in returns.index:
            date_returns = returns.loc[date]
            for sector in self.sector_mapping.unique():
                sector_assets = self.sector_mapping[self.sector_mapping == sector].index
                sector_weights = self.portfolio_weights.loc[date, sector_assets]
                sector_weights = sector_weights / sector_weights.sum() if sector_weights.sum() > 0 else sector_weights

                if len(sector_assets) > 0 and not date_returns[sector_assets].isnull().all():
                    sector_return = (sector_weights * date_returns[sector_assets]).sum()
                    sector_returns.loc[date, sector] = sector_return

        return sector_returns.fillna(0)

    def _aggregate_attribution_by_sector(self) -> Dict[str, Dict[str, float]]:
        """Aggregate attribution by sector"""

        sector_attribution = {}

        for sector in self.sector_mapping.unique():
            sector_assets = self.sector_mapping[self.sector_mapping == sector].index

            allocation = 0
            selection = 0
            interaction = 0

            for asset in sector_assets:
                if asset in self.attribution_result.allocation_effect:
                    allocation += self.attribution_result.allocation_effect[asset]
                    selection += self.attribution_result.selection_effect[asset]
                    if asset in self.attribution_result.interaction_effect:
                        interaction += self.attribution_result.interaction_effect[asset]

            sector_attribution[sector] = {
                'allocation': allocation,
                'selection': selection,
                'interaction': interaction
            }

        return sector_attribution

    def _create_time_series_attribution(self) -> None:
        """Create time series of attribution effects"""

        if self.attribution_result is None:
            return

        # This would store period-by-period attribution
        # Implementation depends on specific attribution method
        pass

    def _create_contribution_summary(self) -> None:
        """Create summary of contributions"""

        if self.attribution_result is None:
            return

        contributions = []

        # Add asset-level contributions
        for asset in self.attribution_result.allocation_effect:
            total = (self.attribution_result.allocation_effect.get(asset, 0) +
                    self.attribution_result.selection_effect.get(asset, 0) +
                    self.attribution_result.interaction_effect.get(asset, 0))

            contributions.append({
                'Asset': asset,
                'Allocation': self.attribution_result.allocation_effect.get(asset, 0),
                'Selection': self.attribution_result.selection_effect.get(asset, 0),
                'Interaction': self.attribution_result.interaction_effect.get(asset, 0),
                'Total': total
            })

        # Create DataFrame
        self.attribution_result.contribution_summary = pd.DataFrame(contributions)

    def plot_attribution_results(self) -> None:
        """Plot attribution results"""

        if self.attribution_result is None:
            raise ValueError("Attribution analysis not performed")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Allocation Effect', 'Selection Effect',
                          'Total Contribution', 'Cumulative Attribution'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # Allocation effect
        if self.attribution_result.allocation_effect:
            fig.add_trace(
                go.Bar(
                    x=list(self.attribution_result.allocation_effect.keys()),
                    y=list(self.attribution_result.allocation_effect.values()),
                    name='Allocation Effect'
                ),
                row=1, col=1
            )

        # Selection effect
        if self.attribution_result.selection_effect:
            fig.add_trace(
                go.Bar(
                    x=list(self.attribution_result.selection_effect.keys()),
                    y=list(self.attribution_result.selection_effect.values()),
                    name='Selection Effect'
                ),
                row=1, col=2
            )

        # Total contribution
        if not self.attribution_result.contribution_summary.empty:
            fig.add_trace(
                go.Bar(
                    x=self.attribution_result.contribution_summary['Asset'],
                    y=self.attribution_result.contribution_summary['Total'],
                    name='Total Contribution'
                ),
                row=2, col=1
            )

        # Update layout
        fig.update_layout(
            title_text="Performance Attribution Analysis",
            showlegend=False,
            height=800
        )

        fig.show()

    def get_attribution_summary(self) -> Dict[str, Any]:
        """Get summary of attribution results"""

        if self.attribution_result is None:
            return {}

        summary = {
            'total_return': self.attribution_result.total_return,
            'benchmark_return': self.attribution_result.benchmark_return,
            'active_return': self.attribution_result.active_return,
            'allocation_total': sum(self.attribution_result.allocation_effect.values()),
            'selection_total': sum(self.attribution_result.selection_effect.values()),
            'interaction_total': sum(self.attribution_result.interaction_effect.values())
        }

        # Add sector summary if available
        if self.attribution_result.sector_attribution:
            summary['sector_attribution'] = {}
            for sector, effects in self.attribution_result.sector_attribution.items():
                summary['sector_attribution'][sector] = {
                    'allocation': effects.get('allocation', 0),
                    'selection': effects.get('selection', 0),
                    'total': effects.get('allocation', 0) + effects.get('selection', 0)
                }

        # Add factor summary if available
        if self.attribution_result.factor_attribution:
            summary['factor_attribution'] = self.attribution_result.factor_attribution

        return summary

    def export_attribution_report(self, filepath: str, format: str = 'json') -> None:
        """Export attribution report"""

        if self.attribution_result is None:
            raise ValueError("Attribution analysis not performed")

        if format.lower() == 'json':
            import json

            report = {
                'config': self.config.__dict__,
                'summary': self.get_attribution_summary(),
                'detailed_results': {
                    'allocation_effect': self.attribution_result.allocation_effect,
                    'selection_effect': self.attribution_result.selection_effect,
                    'interaction_effect': self.attribution_result.interaction_effect,
                    'sector_attribution': self.attribution_result.sector_attribution,
                    'factor_attribution': self.attribution_result.factor_attribution
                },
                'contribution_summary': self.attribution_result.contribution_summary.to_dict()
            }

            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)

        elif format.lower() == 'csv':
            # Export contribution summary to CSV
            if not self.attribution_result.contribution_summary.empty:
                self.attribution_result.contribution_summary.to_csv(filepath, index=False)

        else:
            raise ValueError(f"Unsupported format: {format}")


# Utility functions
def create_attribution_config(
    method: AttributionMethod = AttributionMethod.BRINSON_FACHLER,
    **kwargs
) -> AttributionConfig:
    """Create attribution configuration with defaults"""

    config = {
        'method': method,
        'frequency': 'monthly',
        'currency': 'USD',
        'include_interaction': True,
        'include_benchmark_comparison': True
    }

    config.update(kwargs)
    return AttributionConfig(**config)


def create_sector_mapping(assets: List[str]) -> Dict[str, str]:
    """Create simple sector mapping based on asset names"""

    sector_mapping = {}

    for asset in assets:
        if asset.startswith('TECH') or asset in ['AAPL', 'MSFT', 'GOOGL', 'FB', 'AMZN']:
            sector_mapping[asset] = 'Technology'
        elif asset.startswith('FIN') or asset in ['JPM', 'BAC', 'WFC', 'GS']:
            sector_mapping[asset] = 'Financial'
        elif asset.startswith('HEALTH') or asset in ['JNJ', 'PFE', 'UNH']:
            sector_mapping[asset] = 'Healthcare'
        elif asset.startswith('ENERGY') or asset in ['XOM', 'CVX', 'COP']:
            sector_mapping[asset] = 'Energy'
        elif asset.startswith('CONS'):
            sector_mapping[asset] = 'Consumer'
        else:
            sector_mapping[asset] = 'Other'

    return sector_mapping


__all__ = [
    'PerformanceAttributionAnalyzer',
    'AttributionConfig',
    'AttributionResult',
    'AttributionType',
    'AttributionMethod',
    'create_attribution_config',
    'create_sector_mapping'
]