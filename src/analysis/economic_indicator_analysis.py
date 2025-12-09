"""
Phase 2: Professional Economic Indicator Analysis and Correlation Studies
Advanced economic analysis with HKMA government data integration
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
import warnings
from scipy import stats
from scipy.stats import pearsonr, spearmanr, kendalltau
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from statsmodels.tsa.stattools import grangercausalitytests, coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from statsmodels.stats.diagnostic import acorr_ljungbox
import networkx as nx
from matplotlib import cm
import seaborn as sns

logger = logging.getLogger(__name__)

@dataclass
class EconomicIndicator:
    """Economic indicator definition"""
    name: str
    source: str
    description: str
    frequency: str  # 'daily', 'monthly', 'quarterly'
    unit: str
    category: str  # 'monetary', 'exchange_rate', 'liquidity', etc.

@dataclass
class CorrelationResult:
    """Correlation analysis result"""
    indicator1: str
    indicator2: str
    pearson_correlation: float
    pearson_pvalue: float
    spearman_correlation: float
    spearman_pvalue: float
    kendall_correlation: float
    kendall_pvalue: float
    sample_size: int
    is_significant: bool
    effect_size: str

@dataclass
class EconomicAnalysisReport:
    """Comprehensive economic analysis report"""
    analysis_date: datetime
    data_period: str
    indicators_summary: Dict[str, Any]
    correlation_analysis: Dict[str, List[CorrelationResult]]
    factor_analysis: Dict[str, Any]
    clustering_analysis: Dict[str, Any]
    causality_analysis: Dict[str, Any]
    market_impact_analysis: Dict[str, Any]
    recommendations: List[str]
    visualization_paths: List[str]

class ProfessionalEconomicAnalysis:
    """Professional economic indicator analysis system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.indicators = self._initialize_indicators()
        self.scaler = StandardScaler()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'correlation_threshold': 0.5,
            'significance_level': 0.05,
            'min_sample_size': 30,
            'lookback_periods': [30, 60, 90, 180, 365],  # days
            'factor_analysis_components': 5,
            'clustering_range': range(2, 8),
            'causality_lags': [1, 2, 3, 5, 10],
            'visualization_dir': 'visualizations/economic_analysis',
            'market_symbols': ['0700.HK', '0941.HK', '1299.HK'],  # Key HK stocks
        }

    def _initialize_indicators(self) -> Dict[str, EconomicIndicator]:
        """Initialize economic indicator definitions"""
        return {
            'hibor_1m': EconomicIndicator(
                name='1-Month HIBOR',
                source='HKMA',
                description='1-Month Hong Kong Interbank Offered Rate',
                frequency='daily',
                unit='%',
                category='interest_rates'
            ),
            'hibor_3m': EconomicIndicator(
                name='3-Month HIBOR',
                source='HKMA',
                description='3-Month Hong Kong Interbank Offered Rate',
                frequency='daily',
                unit='%',
                category='interest_rates'
            ),
            'exchange_rate_eeri': EconomicIndicator(
                name='Effective Exchange Rate Index',
                source='HKMA',
                description='Hong Kong Effective Exchange Rate Index',
                frequency='daily',
                unit='index',
                category='exchange_rates'
            ),
            'monetary_base': EconomicIndicator(
                name='Monetary Base',
                source='HKMA',
                description='Total Monetary Base',
                frequency='daily',
                unit='HKD',
                category='monetary'
            ),
            'aggregate_balance': EconomicIndicator(
                name='Aggregate Balance',
                source='HKMA',
                description='Banking System Aggregate Balance',
                frequency='daily',
                unit='HKD',
                category='liquidity'
            ),
            'efbn_yield': EconomicIndicator(
                name='EFBN Yield',
                source='HKMA',
                description='Exchange Fund Bills and Notes Yield',
                frequency='daily',
                unit='%',
                category='government_securities'
            ),
            'rmb_liquidity': EconomicIndicator(
                name='RMB Liquidity Facility',
                source='HKMA',
                description='RMB Liquidity Facility Usage',
                frequency='daily',
                unit='RMB',
                category='currency'
            )
        }

    def analyze_economic_indicators(self, economic_data: Dict[str, pd.DataFrame],
                                  market_data: Optional[Dict[str, pd.DataFrame]] = None) -> EconomicAnalysisReport:
        """
        Perform comprehensive economic indicator analysis

        Args:
            economic_data: Dictionary of economic indicators data
            market_data: Optional market data for correlation analysis

        Returns:
            EconomicAnalysisReport with comprehensive analysis
        """
        logger.info("Starting comprehensive economic indicator analysis")

        try:
            # Data preparation
            prepared_economic_data = self._prepare_economic_data(economic_data)
            aligned_data = self._align_indicators(prepared_economic_data)

            # Indicators summary
            indicators_summary = self._summarize_indicators(aligned_data)

            # Correlation analysis
            correlation_analysis = self._analyze_correlations(aligned_data, market_data)

            # Factor analysis
            factor_analysis = self._perform_factor_analysis(aligned_data)

            # Clustering analysis
            clustering_analysis = self._perform_clustering_analysis(aligned_data)

            # Causality analysis
            causality_analysis = self._analyze_causality(aligned_data)

            # Market impact analysis
            market_impact_analysis = self._analyze_market_impact(aligned_data, market_data)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                indicators_summary, correlation_analysis, factor_analysis,
                clustering_analysis, causality_analysis, market_impact_analysis
            )

            # Create visualizations
            visualization_paths = self._create_visualizations(
                aligned_data, correlation_analysis, factor_analysis, clustering_analysis
            )

            # Create comprehensive report
            report = EconomicAnalysisReport(
                analysis_date=datetime.now(),
                data_period=f"{aligned_data.index.min()} to {aligned_data.index.max()}",
                indicators_summary=indicators_summary,
                correlation_analysis=correlation_analysis,
                factor_analysis=factor_analysis,
                clustering_analysis=clustering_analysis,
                causality_analysis=causality_analysis,
                market_impact_analysis=market_impact_analysis,
                recommendations=recommendations,
                visualization_paths=visualization_paths
            )

            logger.info("Economic indicator analysis completed successfully")
            return report

        except Exception as e:
            logger.error(f"Error in economic indicator analysis: {e}")
            raise

    def _prepare_economic_data(self, economic_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Prepare and clean economic data"""
        prepared = {}

        for indicator_name, data in economic_data.items():
            if data.empty:
                logger.warning(f"No data for indicator {indicator_name}")
                continue

            try:
                # Make a copy to avoid modifying original data
                processed_data = data.copy()

                # Standardize date column name
                if 'end_of_date' in processed_data.columns:
                    processed_data = processed_data.rename(columns={'end_of_date': 'date'})
                elif 'Date' in processed_data.columns:
                    processed_data = processed_data.rename(columns={'Date': 'date'})

                # Ensure date is datetime
                processed_data['date'] = pd.to_datetime(processed_data['date'])

                # Sort by date
                processed_data = processed_data.sort_values('date')

                # Set date as index
                processed_data = processed_data.set_index('date')

                # Extract numeric values and clean
                numeric_columns = processed_data.select_dtypes(include=[np.number]).columns

                for col in numeric_columns:
                    # Convert to numeric, handle errors
                    processed_data[col] = pd.to_numeric(processed_data[col], errors='coerce')

                # Forward fill missing values (common in economic data)
                processed_data = processed_data.fillna(method='ffill').fillna(method='bfill')

                # Remove any remaining NaN values
                processed_data = processed_data.dropna()

                # Add to prepared data
                prepared[indicator_name] = processed_data

                logger.info(f"Prepared {indicator_name}: {len(processed_data)} records")

            except Exception as e:
                logger.error(f"Error preparing {indicator_name}: {e}")
                continue

        return prepared

    def _align_indicators(self, economic_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Align all economic indicators to common timeline"""
        if not economic_data:
            raise ValueError("No economic data available")

        # Find common date range
        all_dates = []
        for data in economic_data.values():
            all_dates.append(data.index)

        common_dates = pd.date_range(
            start=max(dates.min() for dates in all_dates),
            end=min(dates.max() for dates in all_dates),
            freq='D'
        )

        # Create aligned dataframe
        aligned_df = pd.DataFrame(index=common_dates)

        for indicator_name, data in economic_data.items():
            if data.empty:
                continue

            # Extract main numeric column
            numeric_columns = data.select_dtypes(include=[np.number]).columns

            if len(numeric_columns) > 0:
                # Use first numeric column as main indicator
                main_col = numeric_columns[0]
                aligned_df[indicator_name] = data[main_col].reindex(common_dates, method='ffill')

            # Add additional numeric columns with suffix
            for col in numeric_columns[1:]:
                aligned_df[f"{indicator_name}_{col}"] = data[col].reindex(common_dates, method='ffill')

        # Drop any remaining NaN values
        aligned_df = aligned_df.dropna()

        logger.info(f"Aligned {len(economic_data)} indicators to {len(aligned_df)} common dates")

        return aligned_df

    def _summarize_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Summarize economic indicators"""
        summary = {
            'total_indicators': len(data.columns),
            'data_period': {
                'start': data.index.min().strftime('%Y-%m-%d'),
                'end': data.index.max().strftime('%Y-%m-%d'),
                'duration_days': (data.index.max() - data.index.min()).days
            },
            'indicators': {}
        }

        for col in data.columns:
            if col in self.indicators:
                indicator_info = self.indicators[col]
            else:
                indicator_info = None

            series = data[col].dropna()

            indicator_summary = {
                'description': indicator_info.description if indicator_info else col,
                'category': indicator_info.category if indicator_info else 'other',
                'unit': indicator_info.unit if indicator_info else 'unknown',
                'mean': float(series.mean()),
                'median': float(series.median()),
                'std': float(series.std()),
                'min': float(series.min()),
                'max': float(series.max()),
                'skewness': float(stats.skew(series)),
                'kurtosis': float(stats.kurtosis(series)),
                'observations': len(series),
                'missing_percentage': float(data[col].isna().sum() / len(data) * 100)
            }

            # Calculate growth rates
            if len(series) > 1:
                growth_rates = series.pct_change().dropna()
                if len(growth_rates) > 0:
                    indicator_summary.update({
                        'avg_growth_rate': float(growth_rates.mean()),
                        'volatility': float(growth_rates.std()),
                        'positive_growth_periods': int((growth_rates > 0).sum()),
                        'negative_growth_periods': int((growth_rates < 0).sum())
                    })

            summary['indicators'][col] = indicator_summary

        return summary

    def _analyze_correlations(self, economic_data: pd.DataFrame,
                           market_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, List[CorrelationResult]]:
        """Analyze correlations between economic indicators"""
        logger.info("Analyzing correlations between indicators")

        correlation_results = {}

        # Economic indicators correlations
        correlations = self._calculate_correlation_matrix(economic_data)
        correlation_results['economic_indicators'] = correlations

        # Market correlations if market data provided
        if market_data:
            market_correlations = self._analyze_market_correlations(economic_data, market_data)
            correlation_results['market_correlations'] = market_correlations

        # Lagged correlations
        lagged_correlations = self._analyze_lagged_correlations(economic_data)
        correlation_results['lagged_correlations'] = lagged_correlations

        return correlation_results

    def _calculate_correlation_matrix(self, data: pd.DataFrame) -> List[CorrelationResult]:
        """Calculate correlation matrix for all indicator pairs"""
        results = []
        columns = data.columns

        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                col1, col2 = columns[i], columns[j]

                series1 = data[col1].dropna()
                series2 = data[col2].dropna()

                if len(series1) < self.config['min_sample_size'] or len(series2) < self.config['min_sample_size']:
                    continue

                # Align series
                aligned_series1, aligned_series2 = series1.align(series2, join='inner')

                if len(aligned_series1) < self.config['min_sample_size']:
                    continue

                # Calculate correlations
                pearson_corr, pearson_p = pearsonr(aligned_series1, aligned_series2)
                spearman_corr, spearman_p = spearmanr(aligned_series1, aligned_series2)
                kendall_corr, kendall_p = kendalltau(aligned_series1, aligned_series2)

                # Determine significance
                is_significant = (pearson_p < self.config['significance_level'] and
                                abs(pearson_corr) > self.config['correlation_threshold'])

                # Effect size
                abs_corr = abs(pearson_corr)
                if abs_corr < 0.1:
                    effect_size = 'negligible'
                elif abs_corr < 0.3:
                    effect_size = 'small'
                elif abs_corr < 0.5:
                    effect_size = 'medium'
                else:
                    effect_size = 'large'

                result = CorrelationResult(
                    indicator1=col1,
                    indicator2=col2,
                    pearson_correlation=pearson_corr,
                    pearson_pvalue=pearson_p,
                    spearman_correlation=spearman_corr,
                    spearman_pvalue=spearman_p,
                    kendall_correlation=kendall_corr,
                    kendall_pvalue=kendall_p,
                    sample_size=len(aligned_series1),
                    is_significant=is_significant,
                    effect_size=effect_size
                )

                results.append(result)

        return results

    def _analyze_market_correlations(self, economic_data: pd.DataFrame,
                                   market_data: Dict[str, pd.DataFrame]) -> Dict[str, List[CorrelationResult]]:
        """Analyze correlations between economic indicators and market data"""
        results = {}

        for symbol, market_df in market_data.items():
            if market_df.empty or 'close' not in market_df.columns:
                continue

            market_returns = market_df['close'].pct_change().dropna()
            market_correlations = []

            for col in economic_data.columns:
                economic_series = economic_data[col].dropna()

                # Align series
                aligned_market, aligned_economic = market_returns.align(economic_series, join='inner')

                if len(aligned_market) < self.config['min_sample_size']:
                    continue

                # Calculate correlations
                pearson_corr, pearson_p = pearsonr(aligned_market, aligned_economic)
                spearman_corr, spearman_p = spearmanr(aligned_market, aligned_economic)
                kendall_corr, kendall_p = kendalltau(aligned_market, aligned_economic)

                result = CorrelationResult(
                    indicator1=f"{symbol}_returns",
                    indicator2=col,
                    pearson_correlation=pearson_corr,
                    pearson_pvalue=pearson_p,
                    spearman_correlation=spearman_corr,
                    spearman_pvalue=spearman_p,
                    kendall_correlation=kendall_corr,
                    kendall_pvalue=kendall_p,
                    sample_size=len(aligned_market),
                    is_significant=pearson_p < self.config['significance_level'],
                    effect_size='medium' if abs(pearson_corr) > 0.3 else 'small'
                )

                market_correlations.append(result)

            results[symbol] = market_correlations

        return results

    def _analyze_lagged_correlations(self, data: pd.DataFrame) -> Dict[str, List[CorrelationResult]]:
        """Analyze lagged correlations between indicators"""
        results = {}

        for lag in [1, 5, 10, 20]:  # Different lag periods
            lagged_results = []
            columns = data.columns

            for i in range(len(columns)):
                for j in range(len(columns)):
                    if i == j:
                        continue

                    col1, col2 = columns[i], columns[j]

                    # Create lagged series
                    series1 = data[col1].dropna()
                    series2 = data[col2].dropna().shift(lag)

                    # Align series
                    aligned_series1, aligned_series2 = series1.align(series2, join='inner')

                    if len(aligned_series1) < self.config['min_sample_size']:
                        continue

                    # Calculate correlation
                    if len(aligned_series1) > 1:
                        pearson_corr, pearson_p = pearsonr(aligned_series1, aligned_series2)

                        result = CorrelationResult(
                            indicator1=col1,
                            indicator2=f"{col2}_lag_{lag}",
                            pearson_correlation=pearson_corr,
                            pearson_pvalue=pearson_p,
                            spearman_correlation=0,  # Not calculated for lagged
                            spearman_pvalue=0,
                            kendall_correlation=0,
                            kendall_pvalue=0,
                            sample_size=len(aligned_series1),
                            is_significant=pearson_p < self.config['significance_level'],
                            effect_size='medium' if abs(pearson_corr) > 0.3 else 'small'
                        )

                        lagged_results.append(result)

            results[f'lag_{lag}'] = lagged_results

        return results

    def _perform_factor_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform factor analysis on economic indicators"""
        logger.info("Performing factor analysis")

        try:
            # Standardize data
            scaled_data = self.scaler.fit_transform(data)

            # PCA Analysis
            n_components = min(self.config['factor_analysis_components'], len(data.columns))
            pca = PCA(n_components=n_components)
            pca_results = pca.fit_transform(scaled_data)

            # Factor Analysis
            factor_analysis = FactorAnalysis(n_components=n_components, random_state=42)
            factor_results = factor_analysis.fit_transform(scaled_data)

            # Create results dictionary
            analysis_results = {
                'pca': {
                    'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
                    'cumulative_variance_ratio': np.cumsum(pca.explained_variance_ratio_).tolist(),
                    'components': pca.components_.tolist(),
                    'loadings': self._calculate_loadings(data, pca)
                },
                'factor_analysis': {
                    'components': factor_analysis.components_.tolist(),
                    'loadings': self._calculate_loadings(data, factor_analysis),
                    'uniqueness': factor_analysis.noise_variance_.tolist()
                },
                'n_factors': n_components,
                'interpretation': self._interpret_factors(data, pca)
            }

            return analysis_results

        except Exception as e:
            logger.error(f"Error in factor analysis: {e}")
            return {'error': str(e)}

    def _calculate_loadings(self, data: pd.DataFrame, model) -> pd.DataFrame:
        """Calculate factor loadings"""
        loadings = pd.DataFrame(
            model.components_.T,
            index=data.columns,
            columns=[f'Factor_{i+1}' for i in range(model.components_.shape[0])]
        )
        return loadings.to_dict()

    def _interpret_factors(self, data: pd.DataFrame, pca: PCA) -> Dict[str, Any]:
        """Interpret PCA factors"""
        interpretations = {}

        loadings = pd.DataFrame(
            pca.components_.T,
            index=data.columns,
            columns=[f'PC_{i+1}' for i in range(pca.components_.shape[0])]
        )

        for col in loadings.columns:
            top_features = loadings[col].abs().nlargest(3).index.tolist()
            interpretations[col] = {
                'top_indicators': top_features,
                'explained_variance': float(pca.explained_variance_ratio_[int(col.split('_')[1]) - 1])
            }

        return interpretations

    def _perform_clustering_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform clustering analysis on economic indicators"""
        logger.info("Performing clustering analysis")

        try:
            # Standardize data
            scaled_data = self.scaler.fit_transform(data)

            # Find optimal number of clusters
            silhouette_scores = []
            inertias = []

            for k in self.config['clustering_range']:
                if k >= len(data.columns):
                    break

                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(scaled_data)

                silhouette_avg = silhouette_score(scaled_data, cluster_labels)
                silhouette_scores.append(silhouette_avg)
                inertias.append(kmeans.inertia_)

            # Select optimal k (highest silhouette score)
            optimal_k = self.config['clustering_range'][np.argmax(silhouette_scores)]

            # Final clustering
            kmeans_final = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            cluster_labels = kmeans_final.fit_predict(scaled_data)

            # Create cluster assignments
            clusters = {}
            for i, indicator in enumerate(data.columns):
                cluster_id = int(cluster_labels[i])
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(indicator)

            # Calculate cluster characteristics
            cluster_characteristics = {}
            for cluster_id, indicators in clusters.items():
                cluster_data = data[indicators]
                cluster_characteristics[cluster_id] = {
                    'indicators': indicators,
                    'count': len(indicators),
                    'avg_correlation': self._calculate_avg_cluster_correlation(cluster_data),
                    'centroid': kmeans_final.cluster_centers_[cluster_id].tolist()
                }

            results = {
                'optimal_clusters': optimal_k,
                'silhouette_scores': silhouette_scores,
                'inertias': inertias,
                'clusters': cluster_characteristics,
                'cluster_labels': cluster_labels.tolist()
            }

            return results

        except Exception as e:
            logger.error(f"Error in clustering analysis: {e}")
            return {'error': str(e)}

    def _calculate_avg_cluster_correlation(self, cluster_data: pd.DataFrame) -> float:
        """Calculate average correlation within cluster"""
        if cluster_data.shape[1] < 2:
            return 0.0

        correlation_matrix = cluster_data.corr()
        # Get upper triangle (excluding diagonal)
        upper_triangle = correlation_matrix.where(
            np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)
        )
        return upper_triangle.stack().mean()

    def _analyze_causality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze causality relationships between indicators"""
        logger.info("Performing causality analysis")

        causality_results = {}

        columns = data.columns
        for i in range(len(columns)):
            for j in range(len(columns)):
                if i == j:
                    continue

                col1, col2 = columns[i], columns[j]

                # Prepare data for Granger causality test
                test_data = data[[col1, col2]].dropna()

                if len(test_data) < 50:  # Minimum data for causality test
                    continue

                try:
                    # Perform Granger causality test for different lags
                    pair_key = f"{col1}_vs_{col2}"
                    causality_results[pair_key] = {}

                    for lag in self.config['causality_lags']:
                        if lag >= len(test_data) // 2:
                            continue

                        try:
                            result = grangercausalitytests(test_data, lag, verbose=False)

                            # Extract p-values from F-test
                            f_pvalue = result[0][0]['ssr_ftest'][1]

                            causality_results[pair_key][f'lag_{lag}'] = {
                                'f_statistic': float(result[0][0]['ssr_ftest'][0]),
                                'p_value': float(f_pvalue),
                                'is_significant': f_pvalue < self.config['significance_level']
                            }

                        except Exception as e:
                            logger.warning(f"Error in Granger test for {col1} vs {col2} lag {lag}: {e}")

                except Exception as e:
                    logger.warning(f"Error in causality analysis for {col1} vs {col2}: {e}")

        return causality_results

    def _analyze_market_impact(self, economic_data: pd.DataFrame,
                             market_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """Analyze economic indicators' impact on market"""
        if not market_data:
            return {'message': 'No market data provided for impact analysis'}

        impact_analysis = {}

        for symbol, market_df in market_data.items():
            if market_df.empty or 'close' not in market_df.columns:
                continue

            # Calculate market returns
            market_returns = market_df['close'].pct_change().dropna()

            symbol_impact = {}

            for indicator in economic_data.columns:
                indicator_series = economic_data[indicator].dropna()

                # Align series
                aligned_returns, aligned_indicator = market_returns.align(indicator_series, join='inner')

                if len(aligned_returns) < self.config['min_sample_size']:
                    continue

                # Calculate correlation
                correlation, p_value = pearsonr(aligned_returns, aligned_indicator)

                # Calculate regression coefficients
                from sklearn.linear_model import LinearRegression
                X = aligned_indicator.values.reshape(-1, 1)
                y = aligned_returns.values

                model = LinearRegression()
                model.fit(X, y)

                # Calculate volatility impact
                indicator_volatility = aligned_indicator.pct_change().std()
                market_volatility = aligned_returns.std()

                symbol_impact[indicator] = {
                    'correlation': float(correlation),
                    'p_value': float(p_value),
                    'beta': float(model.coef_[0]),
                    'alpha': float(model.intercept_),
                    'r_squared': float(model.score(X, y)),
                    'volatility_ratio': float(indicator_volatility / market_volatility) if market_volatility > 0 else 0,
                    'impact_strength': 'strong' if abs(correlation) > 0.5 else 'moderate' if abs(correlation) > 0.3 else 'weak'
                }

            impact_analysis[symbol] = symbol_impact

        return impact_analysis

    def _generate_recommendations(self, indicators_summary: Dict[str, Any],
                                correlation_analysis: Dict[str, Any],
                                factor_analysis: Dict[str, Any],
                                clustering_analysis: Dict[str, Any],
                                causality_analysis: Dict[str, Any],
                                market_impact_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []

        # Correlation-based recommendations
        if 'economic_indicators' in correlation_analysis:
            significant_correlations = [
                corr for corr in correlation_analysis['economic_indicators']
                if corr.is_significant and corr.effect_size in ['medium', 'large']
            ]

            if significant_correlations:
                recommendations.append(
                    f"Found {len(significant_correlations)} significant correlations between economic indicators. "
                    "Consider these relationships in trading strategy development."
                )

        # Factor analysis recommendations
        if 'interpretation' in factor_analysis:
            factors = factor_analysis['interpretation']
            if factors:
                recommendations.append(
                    f"Factor analysis identified {len(factors)} key factors driving economic indicator movements. "
                    "Focus on the primary factors with highest explained variance."
                )

        # Clustering recommendations
        if 'optimal_clusters' in clustering_analysis:
            optimal_clusters = clustering_analysis['optimal_clusters']
            recommendations.append(
                f"Optimal clustering suggests {optimal_clusters} distinct groups of economic indicators. "
                "Use representative indicators from each cluster to reduce dimensionality."
            )

        # Causality recommendations
        if causality_analysis:
            significant_causality = [
                key for key, value in causality_analysis.items()
                if any(result.get('is_significant', False) for result in value.values())
            ]

            if significant_causality:
                recommendations.append(
                    f"Found {len(significant_causality)} significant causal relationships. "
                    "Leading indicators can be used for predictive modeling."
                )

        # Market impact recommendations
        if market_impact_analysis:
            strong_impacts = []
            for symbol, impacts in market_impact_analysis.items():
                strong_impact_indicators = [
                    ind for ind, impact in impacts.items()
                    if impact['impact_strength'] == 'strong'
                ]
                strong_impacts.extend(strong_impact_indicators)

            if strong_impacts:
                recommendations.append(
                    f"Identified {len(strong_impacts)} economic indicators with strong market impact. "
                    "Prioritize these indicators in market analysis and strategy development."
                )

        # General recommendations
        recommendations.extend([
            "Regularly update economic data to maintain analysis relevance.",
            "Combine multiple indicators for robust economic signals.",
            "Consider regime-specific behavior of economic indicators.",
            "Validate findings with out-of-sample testing before implementation."
        ])

        return recommendations

    def _create_visualizations(self, data: pd.DataFrame,
                             correlation_analysis: Dict[str, Any],
                             factor_analysis: Dict[str, Any],
                             clustering_analysis: Dict[str, Any]) -> List[str]:
        """Create visualization files"""
        visualization_paths = []

        try:
            # Create visualization directory
            viz_dir = Path(self.config['visualization_dir'])
            viz_dir.mkdir(parents=True, exist_ok=True)

            # Correlation heatmap
            if 'economic_indicators' in correlation_analysis:
                corr_matrix = data.corr()
                fig = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu',
                    zmid=0
                ))
                fig.update_layout(title='Economic Indicators Correlation Matrix')
                corr_path = viz_dir / 'correlation_heatmap.html'
                fig.write_html(str(corr_path))
                visualization_paths.append(str(corr_path))

            # PCA explained variance
            if 'pca' in factor_analysis:
                explained_variance = factor_analysis['pca']['explained_variance_ratio']
                fig = go.Figure(data=[
                    go.Bar(x=[f'PC_{i+1}' for i in range(len(explained_variance))],
                           y=explained_variance)
                ])
                fig.update_layout(title='PCA Explained Variance Ratio')
                pca_path = viz_dir / 'pca_variance.html'
                fig.write_html(str(pca_path))
                visualization_paths.append(str(pca_path))

            # Time series plot
            fig = go.Figure()
            for col in data.columns[:5]:  # Plot first 5 indicators
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data[col],
                    mode='lines',
                    name=col
                ))
            fig.update_layout(title='Economic Indicators Time Series')
            ts_path = viz_dir / 'time_series.html'
            fig.write_html(str(ts_path))
            visualization_paths.append(str(ts_path))

            logger.info(f"Created {len(visualization_paths)} visualizations")

        except Exception as e:
            logger.error(f"Error creating visualizations: {e}")

        return visualization_paths

    def save_analysis_report(self, report: EconomicAnalysisReport, file_path: str):
        """Save analysis report to JSON file"""
        try:
            report_dict = {
                'analysis_date': report.analysis_date.isoformat(),
                'data_period': report.data_period,
                'indicators_summary': report.indicators_summary,
                'correlation_analysis': {
                    category: [
                        {
                            'indicator1': corr.indicator1,
                            'indicator2': corr.indicator2,
                            'pearson_correlation': corr.pearson_correlation,
                            'pearson_pvalue': corr.pearson_pvalue,
                            'is_significant': corr.is_significant,
                            'effect_size': corr.effect_size
                        }
                        for corr in correlations
                    ]
                    for category, correlations in report.correlation_analysis.items()
                },
                'factor_analysis': report.factor_analysis,
                'clustering_analysis': report.clustering_analysis,
                'causality_analysis': report.causality_analysis,
                'market_impact_analysis': report.market_impact_analysis,
                'recommendations': report.recommendations,
                'visualization_paths': report.visualization_paths
            }

            with open(file_path, 'w') as f:
                json.dump(report_dict, f, indent=2)

            logger.info(f"Analysis report saved to {file_path}")

        except Exception as e:
            logger.error(f"Error saving analysis report: {e}")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create sample economic data
    dates = pd.date_range('2020-01-01', '2024-01-01', freq='D')
    n_days = len(dates)

    # Generate sample economic indicators
    np.random.seed(42)
    economic_data = {
        'hibor_1m': pd.DataFrame({
            'date': dates,
            'value': np.random.normal(2.0, 0.5, n_days)
        }).set_index('date'),
        'exchange_rate_eeri': pd.DataFrame({
            'date': dates,
            'value': np.random.normal(100, 5, n_days)
        }).set_index('date'),
        'monetary_base': pd.DataFrame({
            'date': dates,
            'value': np.random.normal(1000000, 100000, n_days)
        }).set_index('date')
    }

    # Create sample market data
    market_data = {
        '0700.HK': pd.DataFrame({
            'date': dates,
            'close': np.random.normal(400, 50, n_days).cumsum()
        }).set_index('date')
    }

    # Initialize analysis
    analyzer = ProfessionalEconomicAnalysis()

    # Run analysis
    report = analyzer.analyze_economic_indicators(economic_data, market_data)

    # Print summary
    print(f"Analysis completed on {report.analysis_date}")
    print(f"Data period: {report.data_period}")
    print(f"Total indicators: {report.indicators_summary['total_indicators']}")
    print(f"Recommendations: {len(report.recommendations)}")

    # Save report
    analyzer.save_analysis_report(report, "economic_analysis_report.json")
    print("Analysis report saved to economic_analysis_report.json")