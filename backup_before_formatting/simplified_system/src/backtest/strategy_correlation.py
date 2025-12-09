#!/usr/bin/env python3
"""
Strategy Correlation Analysis System
策略相关性分析系统

Advanced correlation and cointegration analysis for trading strategies:
- Pearson, Spearman, Kendall correlation analysis
- Rolling window correlation analysis
- Cointegration testing
- Lead-lag relationship analysis
- Correlation regime detection
- Principal component analysis
- Hierarchical clustering
- Dynamic correlation networks

专为策略组合优化设计的专业相关性分析系统
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from scipy import stats
    from scipy.stats import pearsonr, spearmanr, kendalltau
    from scipy.spatial.distance import pdist, squareform
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    import networkx as nx
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Some correlation features may not work")

try:
    import statsmodels.api as sm
    from statsmodels.tsa.stattools import coint, adfuller
    from statsmodels.stats.diagnostic import acorr_ljungbox
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("Statsmodels not available. Advanced time series analysis not available")

logger = logging.getLogger(__name__)

@dataclass
class CorrelationConfig:
    """相关性分析配置"""
    # 基本参数
    correlation_methods: List[str] = field(default_factory=lambda: ["pearson", "spearman"])
    significance_level: float = 0.05  # 显著性水平
    min_periods: int = 30  # 最小观测期数

    # 滚动窗口
    rolling_window: int = 60  # 滚动窗口大小
    rolling_step: int = 5  # 滚动步长

    # 协整分析
    cointegration_method: str = "engle_granger"  # engle_granger, johansen
    max_lag: int = 10  # 最大滞后阶数

    # 聚类分析
    clustering_method: str = "agglomerative"  # agglomerative, kmeans
    n_clusters: Optional[int] = None  # 聚类数量
    linkage_method: str = "average"  # average, complete, ward

    # 主成分分析
    pca_components: Optional[int] = None  # 主成分数量
    variance_threshold: float = 0.8  # 方差解释阈值

    # 网络分析
    correlation_threshold: float = 0.5  # 相关性阈值
    network_layout: str = "spring"  # spring, circular, kamada_kawai

    # 趋势检测
    regime_detection: bool = True  # 启用趋势检测
    regime_window: int = 120  # 趋势检测窗口

@dataclass
class CorrelationResult:
    """相关性分析结果"""
    correlation_matrix: pd.DataFrame  # 相关性矩阵
    p_values: pd.DataFrame  # p值矩阵
    significant_correlations: pd.DataFrame  # 显著相关性
    method: str  # 相关性方法

@dataclass
class RollingCorrelationResult:
    """滚动相关性结果"""
    rolling_correlations: Dict[str, pd.DataFrame]  # 滚动相关性
    correlation_volatility: pd.DataFrame  # 相关性波动率
    correlation_trends: pd.DataFrame  # 相关性趋势
    stability_metrics: Dict[str, float]  # 稳定性指标

@dataclass
class CointegrationResult:
    """协整分析结果"""
    cointegration_matrix: pd.DataFrame  # 协整矩阵
    test_statistics: pd.DataFrame  # 检验统计量
    p_values: pd.DataFrame  # p值
    cointegration_vectors: Dict[str, np.ndarray]  # 协整向量
    error_correction_terms: Dict[str, pd.Series]  # 误差修正项

@dataclass
class LeadLagResult:
    """领先滞后关系结果"""
    lead_lag_matrix: pd.DataFrame  # 领先滞后矩阵
    optimal_lags: pd.DataFrame  # 最优滞后
    granger_causality: Dict[str, Dict[str, float]]  # Granger因果关系
    impulse_response: Dict[str, pd.DataFrame]  # 脉冲响应

@dataclass
class PCAResult:
    """主成分分析结果"""
    principal_components: pd.DataFrame  # 主成分
    explained_variance_ratio: np.ndarray  # 解释方差比率
    component_loadings: pd.DataFrame  # 成分载荷
    cumulative_variance: np.ndarray  # 累积方差

@dataclass
class ClusteringResult:
    """聚类分析结果"""
    cluster_labels: np.ndarray  # 聚类标签
    cluster_centers: Optional[np.ndarray]  # 聚类中心
    silhouette_score: float  # 轮廓系数
    dendrogram: Optional[Any]  # 树状图
    optimal_clusters: int  # 最优聚类数

@dataclass
class NetworkResult:
    """网络分析结果"""
    graph: Any  # 网络图
    centrality_measures: Dict[str, Dict[str, float]]  # 中心性度量
    community_structure: Dict[str, List[str]]  # 社区结构
    network_metrics: Dict[str, float]  # 网络指标

@dataclass
class RegimeDetectionResult:
    """趋势检测结果"""
    regimes: np.ndarray  # 趋势标签
    regime_transitions: List[Tuple[int, int, str]]  # 趋势转换
    regime_correlations: Dict[str, pd.DataFrame]  # 趋势相关性
    stability_periods: List[Tuple[int, int]]  # 稳定期

class StrategyCorrelationAnalyzer:
    """
    策略相关性分析引擎

    提供全面的策略相关性分析功能：
    - 多种相关性分析方法
    - 滚动窗口相关性分析
    - 协整检验和长期关系分析
    - 领先滞后关系识别
    - 聚类和分类
    - 网络分析
    - 趋势检测
    """

    def __init__(self, config: Optional[CorrelationConfig] = None):
        """初始化策略相关性分析引擎"""
        self.config = config or CorrelationConfig()

        # 验证依赖
        self._check_dependencies()

        logger.info("Strategy Correlation Analyzer initialized")

    def analyze_correlations(
        self,
        returns_data: pd.DataFrame,
        methods: Optional[List[str]] = None
    ) -> Dict[str, CorrelationResult]:
        """
        分析策略相关性

        Args:
            returns_data: 策略收益数据
            methods: 相关性方法列表

        Returns:
            Dict[str, CorrelationResult]: 相关性分析结果
        """
        start_time = datetime.now()
        logger.info(f"Starting correlation analysis for {returns_data.shape[1]} strategies")

        try:
            methods = methods or self.config.correlation_methods
            results = {}

            for method in methods:
                logger.info(f"Calculating {method} correlation")
                result = self._calculate_correlation(returns_data, method)
                results[method] = result

            logger.info(f"Correlation analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return results

        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            raise

    def rolling_correlation_analysis(
        self,
        returns_data: pd.DataFrame,
        window: Optional[int] = None,
        step: Optional[int] = None
    ) -> RollingCorrelationResult:
        """
        滚动窗口相关性分析

        Args:
            returns_data: 策略收益数据
            window: 滚动窗口大小
            step: 滚动步长

        Returns:
            RollingCorrelationResult: 滚动相关性结果
        """
        start_time = datetime.now()
        window = window or self.config.rolling_window
        step = step or self.config.rolling_step

        logger.info(f"Starting rolling correlation analysis with window={window}, step={step}")

        try:
            n_strategies = returns_data.shape[1]
            strategy_names = returns_data.columns

            # 初始化结果存储
            rolling_correlations = {}
            correlation_volatility = pd.DataFrame(
                index=strategy_names,
                columns=strategy_names,
                dtype=float
            )
            correlation_trends = pd.DataFrame(
                index=strategy_names,
                columns=strategy_names,
                dtype=float
            )

            # 计算滚动相关性
            for i, strategy1 in enumerate(strategy_names):
                for j, strategy2 in enumerate(strategy_names):
                    if i <= j:  # 只计算上三角矩阵
                        pair_key = f"{strategy1}_{strategy2}"
                        rolling_corr = []

                        dates = []
                        for start_idx in range(0, len(returns_data) - window + 1, step):
                            end_idx = start_idx + window
                            window_data = returns_data.iloc[start_idx:end_idx]

                            if len(window_data) >= self.config.min_periods:
                                if i == j:
                                    corr = 1.0
                                else:
                                    corr, _ = pearsonr(
                                        window_data[strategy1].dropna(),
                                        window_data[strategy2].dropna()
                                    )
                                    if np.isnan(corr):
                                        corr = 0.0

                                rolling_corr.append(corr)
                                dates.append(returns_data.index[end_idx - 1])

                        # 转换为DataFrame
                        if rolling_corr:
                            rolling_correlations[pair_key] = pd.Series(
                                rolling_corr, index=dates, name=f"{strategy1}_vs_{strategy2}"
                            )

                            # 计算波动率和趋势
                            correlation_volatility.loc[strategy1, strategy2] = np.std(rolling_corr)
                            correlation_volatility.loc[strategy2, strategy1] = correlation_volatility.loc[strategy1, strategy2]

                            # 线性趋势
                            if len(rolling_corr) > 1:
                                x = np.arange(len(rolling_corr))
                                trend_slope, _, _, _, _ = stats.linregress(x, rolling_corr)
                                correlation_trends.loc[strategy1, strategy2] = trend_slope
                                correlation_trends.loc[strategy2, strategy1] = trend_slope

            # 计算稳定性指标
            stability_metrics = self._calculate_correlation_stability(rolling_correlations)

            result = RollingCorrelationResult(
                rolling_correlations=rolling_correlations,
                correlation_volatility=correlation_volatility,
                correlation_trends=correlation_trends,
                stability_metrics=stability_metrics
            )

            logger.info(f"Rolling correlation analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Rolling correlation analysis failed: {e}")
            raise

    def cointegration_analysis(
        self,
        price_data: pd.DataFrame,
        method: Optional[str] = None
    ) -> CointegrationResult:
        """
        协整分析

        Args:
            price_data: 价格数据
            method: 协整检验方法

        Returns:
            CointegrationResult: 协整分析结果
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("Statsmodels is required for cointegration analysis")

        start_time = datetime.now()
        method = method or self.config.cointegration_method

        logger.info(f"Starting cointegration analysis using {method} method")

        try:
            n_assets = price_data.shape[1]
            asset_names = price_data.columns

            # 初始化结果矩阵
            cointegration_matrix = pd.DataFrame(
                index=asset_names,
                columns=asset_names,
                dtype=float
            )
            test_statistics = pd.DataFrame(
                index=asset_names,
                columns=asset_names,
                dtype=float
            )
            p_values = pd.DataFrame(
                index=asset_names,
                columns=asset_names,
                dtype=float
            )

            cointegration_vectors = {}
            error_correction_terms = {}

            # 两两协整检验
            for i, asset1 in enumerate(asset_names):
                for j, asset2 in enumerate(asset_names):
                    if i < j:  # 只计算上三角矩阵
                        try:
                            series1 = price_data[asset1].dropna()
                            series2 = price_data[asset2].dropna()

                            # 对齐时间序列
                            common_index = series1.index.intersection(series2.index)
                            if len(common_index) < self.config.min_periods:
                                continue

                            series1 = series1.loc[common_index]
                            series2 = series2.loc[common_index]

                            if method == "engle_granger":
                                # Engle-Granger协整检验
                                coint_stat, pvalue, crit_value = coint(
                                    series1, series2, maxlag=self.config.max_lag
                                )

                                cointegration_matrix.loc[asset1, asset2] = 1 if pvalue < self.config.significance_level else 0
                                cointegration_matrix.loc[asset2, asset1] = cointegration_matrix.loc[asset1, asset2]
                                test_statistics.loc[asset1, asset2] = coint_stat
                                test_statistics.loc[asset2, asset1] = coint_stat
                                p_values.loc[asset1, asset2] = pvalue
                                p_values.loc[asset2, asset1] = pvalue

                                # 计算协整向量（简化版本）
                                if pvalue < self.config.significance_level:
                                    # 线性回归得到协整向量
                                    X = sm.add_constant(series2)
                                    model = sm.OLS(series1, X).fit()
                                    coint_vector = np.array([-model.params[1], 1.0])  # [beta, 1]
                                    cointegration_vectors[f"{asset1}_{asset2}"] = coint_vector

                                    # 误差修正项
                                    error_term = series1 - model.params[1] * series2
                                    error_correction_terms[f"{asset1}_{asset2}"] = error_term

                        except Exception as e:
                            logger.warning(f"Cointegration test failed for {asset1}-{asset2}: {e}")
                            continue

            result = CointegrationResult(
                cointegration_matrix=cointegration_matrix,
                test_statistics=test_statistics,
                p_values=p_values,
                cointegration_vectors=cointegration_vectors,
                error_correction_terms=error_correction_terms
            )

            logger.info(f"Cointegration analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Cointegration analysis failed: {e}")
            raise

    def lead_lag_analysis(
        self,
        returns_data: pd.DataFrame,
        max_lag: Optional[int] = None
    ) -> LeadLagResult:
        """
        领先滞后关系分析

        Args:
            returns_data: 收益数据
            max_lag: 最大滞后阶数

        Returns:
            LeadLagResult: 领先滞后关系结果
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("Statsmodels is required for lead-lag analysis")

        start_time = datetime.now()
        max_lag = max_lag or self.config.max_lag

        logger.info(f"Starting lead-lag analysis with max lag={max_lag}")

        try:
            n_strategies = returns_data.shape[1]
            strategy_names = returns_data.columns

            # 初始化结果矩阵
            lead_lag_matrix = pd.DataFrame(
                index=strategy_names,
                columns=strategy_names,
                dtype=float
            )
            optimal_lags = pd.DataFrame(
                index=strategy_names,
                columns=strategy_names,
                dtype=int
            )

            granger_causality = {}
            impulse_response = {}

            # 两两领先滞后分析
            for i, strategy1 in enumerate(strategy_names):
                granger_causality[strategy1] = {}
                impulse_response[strategy1] = {}

                for j, strategy2 in enumerate(strategy_names):
                    if i != j:
                        try:
                            series1 = returns_data[strategy1].dropna()
                            series2 = returns_data[strategy2].dropna()

                            # 对齐时间序列
                            common_index = series1.index.intersection(series2.index)
                            if len(common_index) < self.config.min_periods * 2:
                                continue

                            series1 = series1.loc[common_index]
                            series2 = series2.loc[common_index]

                            # 交叉相关分析
                            best_corr = 0.0
                            best_lag = 0
                            best_direction = 0  # 1: strategy1 leads, -1: strategy2 leads

                            for lag in range(1, max_lag + 1):
                                # strategy1 领先 strategy2
                                if len(series1) > lag:
                                    corr1, _ = pearsonr(series1[:-lag], series2[lag:])
                                    if abs(corr1) > abs(best_corr):
                                        best_corr = corr1
                                        best_lag = lag
                                        best_direction = 1

                                # strategy2 领先 strategy1
                                if len(series2) > lag:
                                    corr2, _ = pearsonr(series2[:-lag], series1[lag:])
                                    if abs(corr2) > abs(best_corr):
                                        best_corr = corr2
                                        best_lag = lag
                                        best_direction = -1

                            lead_lag_matrix.loc[strategy1, strategy2] = best_corr * best_direction
                            optimal_lags.loc[strategy1, strategy2] = best_lag * best_direction

                            # Granger因果关系检验
                            if len(series1) > max_lag and len(series2) > max_lag:
                                try:
                                    # 检验 strategy1 是否 Granger 引起 strategy2
                                    gc_test_12 = sm.tsa.stattools.grangercausalitytests(
                                        pd.concat([series2, series1], axis=1).dropna(),
                                        maxlag=max_lag,
                                        verbose=False
                                    )
                                    f_stat_12 = gc_test_12[max_lag][0]['ssr_ftest'][0]
                                    p_value_12 = gc_test_12[max_lag][0]['ssr_ftest'][1]

                                    # 检验 strategy2 是否 Granger 引起 strategy1
                                    gc_test_21 = sm.tsa.stattools.grangercausalitytests(
                                        pd.concat([series1, series2], axis=1).dropna(),
                                        maxlag=max_lag,
                                        verbose=False
                                    )
                                    f_stat_21 = gc_test_21[max_lag][0]['ssr_ftest'][0]
                                    p_value_21 = gc_test_21[max_lag][0]['ssr_ftest'][1]

                                    granger_causality[strategy1][strategy2] = {
                                        'f_stat': f_stat_12,
                                        'p_value': p_value_12,
                                        'direction': '1->2' if p_value_12 < p_value_21 else '2->1'
                                    }

                                except Exception as e:
                                    logger.warning(f"Granger causality test failed for {strategy1}-{strategy2}: {e}")

                        except Exception as e:
                            logger.warning(f"Lead-lag analysis failed for {strategy1}-{strategy2}: {e}")

            result = LeadLagResult(
                lead_lag_matrix=lead_lag_matrix,
                optimal_lags=optimal_lags,
                granger_causality=granger_causality,
                impulse_response=impulse_response
            )

            logger.info(f"Lead-lag analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Lead-lag analysis failed: {e}")
            raise

    def pca_analysis(
        self,
        returns_data: pd.DataFrame,
        n_components: Optional[int] = None
    ) -> PCAResult:
        """
        主成分分析

        Args:
            returns_data: 收益数据
            n_components: 主成分数量

        Returns:
            PCAResult: 主成分分析结果
        """
        if not SCIPY_AVAILABLE:
            raise ImportError("SciPy is required for PCA analysis")

        start_time = datetime.now()
        n_components = n_components or self.config.pca_components

        logger.info(f"Starting PCA analysis with {n_components} components")

        try:
            # 数据标准化
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(returns_data.fillna(0))

            # PCA分析
            if n_components is None:
                # 自动确定成分数量（基于方差解释阈值）
                pca = PCA()
                pca.fit(scaled_data)
                cumsum_variance = np.cumsum(pca.explained_variance_ratio_)
                n_components = np.argmax(cumsum_variance >= self.config.variance_threshold) + 1

            pca = PCA(n_components=n_components)
            principal_components = pca.fit_transform(scaled_data)

            # 转换为DataFrame
            pc_df = pd.DataFrame(
                principal_components,
                index=returns_data.index,
                columns=[f"PC_{i+1}" for i in range(n_components)]
            )

            # 成分载荷
            component_loadings = pd.DataFrame(
                pca.components_.T,
                index=returns_data.columns,
                columns=[f"PC_{i+1}" for i in range(n_components)]
            )

            result = PCAResult(
                principal_components=pc_df,
                explained_variance_ratio=pca.explained_variance_ratio_,
                component_loadings=component_loadings,
                cumulative_variance=np.cumsum(pca.explained_variance_ratio_)
            )

            logger.info(f"PCA analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"PCA analysis failed: {e}")
            raise

    def clustering_analysis(
        self,
        correlation_matrix: pd.DataFrame,
        n_clusters: Optional[int] = None
    ) -> ClusteringResult:
        """
        聚类分析

        Args:
            correlation_matrix: 相关性矩阵
            n_clusters: 聚类数量

        Returns:
            ClusteringResult: 聚类分析结果
        """
        if not SCIPY_AVAILABLE:
            raise ImportError("SciPy is required for clustering analysis")

        start_time = datetime.now()
        n_clusters = n_clusters or self.config.n_clusters

        logger.info(f"Starting clustering analysis with {n_clusters} clusters")

        try:
            # 转换相关性为距离
            distance_matrix = 1 - correlation_matrix.abs()

            # 自动确定最优聚类数
            if n_clusters is None:
                silhouette_scores = []
                k_range = range(2, min(10, len(correlation_matrix) // 2))

                for k in k_range:
                    clustering = AgglomerativeClustering(
                        n_clusters=k,
                        linkage=self.config.linkage_method,
                        affinity='precomputed'
                    )
                    labels = clustering.fit_predict(distance_matrix)
                    score = silhouette_score(distance_matrix, labels, metric='precomputed')
                    silhouette_scores.append(score)

                if silhouette_scores:
                    optimal_k = k_range[np.argmax(silhouette_scores)]
                else:
                    optimal_k = 3
            else:
                optimal_k = n_clusters

            # 执行聚类
            clustering = AgglomerativeClustering(
                n_clusters=optimal_k,
                linkage=self.config.linkage_method,
                affinity='precomputed'
            )
            cluster_labels = clustering.fit_predict(distance_matrix)

            # 计算轮廓系数
            silhouette_avg = silhouette_score(distance_matrix, cluster_labels, metric='precomputed')

            # 聚类中心（基于相关性）
            cluster_centers = []
            for i in range(optimal_k):
                cluster_indices = np.where(cluster_labels == i)[0]
                if len(cluster_indices) > 0:
                    cluster_corr = correlation_matrix.iloc[cluster_indices, cluster_indices]
                    center = cluster_corr.mean(axis=1).values
                    cluster_centers.append(center)

            result = ClusteringResult(
                cluster_labels=cluster_labels,
                cluster_centers=np.array(cluster_centers) if cluster_centers else None,
                silhouette_score=silhouette_avg,
                dendrogram=None,  # 需要matplotlib来绘制
                optimal_clusters=optimal_k
            )

            logger.info(f"Clustering analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Clustering analysis failed: {e}")
            raise

    def network_analysis(
        self,
        correlation_matrix: pd.DataFrame,
        threshold: Optional[float] = None
    ) -> NetworkResult:
        """
        网络分析

        Args:
            correlation_matrix: 相关性矩阵
            threshold: 相关性阈值

        Returns:
            NetworkResult: 网络分析结果
        """
        try:
            threshold = threshold or self.config.correlation_threshold

            logger.info(f"Starting network analysis with threshold={threshold}")

            # 创建网络图
            G = nx.Graph()

            # 添加节点
            strategies = correlation_matrix.columns.tolist()
            G.add_nodes_from(strategies)

            # 添加边（基于相关性阈值）
            for i, strategy1 in enumerate(strategies):
                for j, strategy2 in enumerate(strategies):
                    if i < j:
                        corr_value = abs(correlation_matrix.loc[strategy1, strategy2])
                        if corr_value >= threshold:
                            G.add_edge(
                                strategy1,
                                strategy2,
                                weight=corr_value,
                                correlation=correlation_matrix.loc[strategy1, strategy2]
                            )

            # 计算中心性度量
            centrality_measures = {
                'degree_centrality': nx.degree_centrality(G),
                'betweenness_centrality': nx.betweenness_centrality(G),
                'closeness_centrality': nx.closeness_centrality(G),
                'eigenvector_centrality': nx.eigenvector_centrality(G, max_iter=1000)
            }

            # 社区检测
            try:
                communities = nx.community.greedy_modularity_communities(G)
                community_structure = {
                    f"community_{i}": list(community) for i, community in enumerate(communities)
                }
            except:
                community_structure = {}

            # 网络指标
            network_metrics = {
                'density': nx.density(G),
                'average_clustering': nx.average_clustering(G),
                'connected_components': nx.number_connected_components(G),
                'largest_component_size': len(max(nx.connected_components(G), key=len)) if nx.is_connected(G) else 0
            }

            result = NetworkResult(
                graph=G,
                centrality_measures=centrality_measures,
                community_structure=community_structure,
                network_metrics=network_metrics
            )

            logger.info("Network analysis completed")
            return result

        except Exception as e:
            logger.error(f"Network analysis failed: {e}")
            raise

    def regime_detection(
        self,
        returns_data: pd.DataFrame,
        window: Optional[int] = None
    ) -> RegimeDetectionResult:
        """
        趋势检测

        Args:
            returns_data: 收益数据
            window: 检测窗口大小

        Returns:
            RegimeDetectionResult: 趋势检测结果
        """
        start_time = datetime.now()
        window = window or self.config.regime_window

        logger.info(f"Starting regime detection with window={window}")

        try:
            n_strategies = returns_data.shape[1]
            strategy_names = returns_data.columns

            # 计算滚动相关性
            rolling_correlations = []
            dates = []

            for start_idx in range(0, len(returns_data) - window + 1, window // 4):
                end_idx = start_idx + window
                window_data = returns_data.iloc[start_idx:end_idx]

                if len(window_data) >= self.config.min_periods:
                    corr_matrix = window_data.corr()
                    # 取上三角矩阵的平均相关性
                    mask = np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
                    avg_correlation = corr_matrix.where(mask).stack().mean()
                    rolling_correlations.append(avg_correlation)
                    dates.append(returns_data.index[end_idx - 1])

            if not rolling_correlations:
                return RegimeDetectionResult(
                    regimes=np.array([]),
                    regime_transitions=[],
                    regime_correlations={},
                    stability_periods=[]
                )

            # 趋势标记（基于相关性水平）
            correlations = np.array(rolling_correlations)
            percentiles = np.percentile(correlations, [33, 67])

            regimes = np.zeros(len(correlations))
            regimes[correlations < percentiles[0]] = 0  # 低相关性趋势
            regimes[(correlations >= percentiles[0]) & (correlations < percentiles[1])] = 1  # 中等相关性趋势
            regimes[correlations >= percentiles[1]] = 2  # 高相关性趋势

            # 趋势转换
            regime_transitions = []
            for i in range(1, len(regimes)):
                if regimes[i] != regimes[i-1]:
                    regime_transitions.append((dates[i-1], dates[i], f"Regime {int(regimes[i-1])} -> Regime {int(regimes[i])}"))

            # 趋势相关性矩阵
            regime_correlations = {}
            for regime_id in np.unique(regimes):
                regime_mask = regimes == regime_id
                if np.sum(regime_mask) > 0:
                    # 获取该趋势期的原始数据
                    regime_periods = []
                    start_regime = None

                    for i, is_regime in enumerate(regime_mask):
                        if is_regime and start_regime is None:
                            start_regime = i
                        elif not is_regime and start_regime is not None:
                            regime_periods.append((dates[start_regime], dates[i-1]))
                            start_regime = None

                    if start_regime is not None:
                        regime_periods.append((dates[start_regime], dates[-1]))

                    # 计算该趋势期的相关性
                    regime_returns = []
                    for start_date, end_date in regime_periods:
                        period_data = returns_data.loc[start_date:end_date]
                        regime_returns.append(period_data)

                    if regime_returns:
                        all_regime_returns = pd.concat(regime_returns)
                        regime_corr = all_regime_returns.corr()
                        regime_correlations[f"Regime_{int(regime_id)}"] = regime_corr

            # 稳定期识别
            stability_periods = []
            for i in range(len(regimes) - 1):
                if regimes[i] == regimes[i + 1] and i + 1 < len(dates):
                    stability_periods.append((dates[i], dates[i + 1]))

            result = RegimeDetectionResult(
                regimes=regimes,
                regime_transitions=regime_transitions,
                regime_correlations=regime_correlations,
                stability_periods=stability_periods
            )

            logger.info(f"Regime detection completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Regime detection failed: {e}")
            raise

    def _check_dependencies(self):
        """检查依赖库"""
        required_packages = {
            'numpy': 'numpy',
            'pandas': 'pandas',
            'scipy': 'scipy',
            'statsmodels': 'statsmodels'
        }

        missing_packages = []
        for package, import_name in required_packages.items():
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            logger.warning(f"Missing optional packages: {missing_packages}")

    def _calculate_correlation(
        self,
        returns_data: pd.DataFrame,
        method: str
    ) -> CorrelationResult:
        """计算相关性"""
        # 移除NaN值
        clean_data = returns_data.dropna()

        if len(clean_data) < self.config.min_periods:
            logger.warning(f"Insufficient data for correlation calculation: {len(clean_data)} < {self.config.min_periods}")
            return CorrelationResult(
                correlation_matrix=pd.DataFrame(),
                p_values=pd.DataFrame(),
                significant_correlations=pd.DataFrame(),
                method=method
            )

        n_strategies = clean_data.shape[1]
        strategy_names = clean_data.columns

        # 初始化矩阵
        correlation_matrix = pd.DataFrame(
            index=strategy_names,
            columns=strategy_names,
            dtype=float
        )
        p_values = pd.DataFrame(
            index=strategy_names,
            columns=strategy_names,
            dtype=float
        )

        # 计算相关性
        for i, strategy1 in enumerate(strategy_names):
            for j, strategy2 in enumerate(strategy_names):
                if i <= j:
                    if i == j:
                        correlation_matrix.loc[strategy1, strategy2] = 1.0
                        p_values.loc[strategy1, strategy2] = 0.0
                    else:
                        series1 = clean_data[strategy1]
                        series2 = clean_data[strategy2]

                        if method == "pearson":
                            corr, p_val = pearsonr(series1, series2)
                        elif method == "spearman":
                            corr, p_val = spearmanr(series1, series2)
                        elif method == "kendall":
                            corr, p_val = kendalltau(series1, series2)
                        else:
                            raise ValueError(f"Unknown correlation method: {method}")

                        correlation_matrix.loc[strategy1, strategy2] = corr
                        correlation_matrix.loc[strategy2, strategy1] = corr
                        p_values.loc[strategy1, strategy2] = p_val
                        p_values.loc[strategy2, strategy1] = p_val

        # 识别显著相关性
        significant_mask = (p_values < self.config.significance_level) & (correlation_matrix.abs() > 0.3)
        significant_correlations = correlation_matrix.where(significant_mask)

        return CorrelationResult(
            correlation_matrix=correlation_matrix,
            p_values=p_values,
            significant_correlations=significant_correlations,
            method=method
        )

    def _calculate_correlation_stability(
        self,
        rolling_correlations: Dict[str, pd.Series]
    ) -> Dict[str, float]:
        """计算相关性稳定性指标"""
        stability_metrics = {}

        for pair_key, corr_series in rolling_correlations.items():
            if len(corr_series) > 1:
                # 计算变异系数
                mean_corr = np.mean(corr_series)
                std_corr = np.std(corr_series)

                if abs(mean_corr) > 1e-8:
                    cv = std_corr / abs(mean_corr)
                    stability = 1.0 / (1.0 + cv)  # 转换为稳定性评分
                else:
                    stability = 0.5

                stability_metrics[pair_key] = stability

        return stability_metrics

# 便利函数
def create_correlation_analyzer(config: Optional[CorrelationConfig] = None) -> StrategyCorrelationAnalyzer:
    """创建策略相关性分析引擎"""
    return StrategyCorrelationAnalyzer(config)

def analyze_strategy_correlations(
    returns_data: pd.DataFrame,
    methods: Optional[List[str]] = None
) -> Dict[str, CorrelationResult]:
    """便利函数：分析策略相关性"""
    analyzer = StrategyCorrelationAnalyzer()
    return analyzer.analyze_correlations(returns_data, methods)