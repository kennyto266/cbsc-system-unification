"""
Multi-Asset Correlation Analyzer
多資產相關性分析器

提供全面的相關性分析和監控功能：
- 靜態和動態相關性計算
- 相關性矩陣可視化
- 相關性趨勢分析
- 集中度風險評估
- 相關性變化警報
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import warnings

logger = logging.getLogger(__name__)


class CorrelationMethod(str, Enum):
    """相關性計算方法"""
    PEARSON = "pearson"       # 皮爾遜相關係數
    SPEARMAN = "spearman"     # 斯皮爾曼相關係數
    KENDALL = "kendall"       # 肯德爾相關係數
    DYNAMIC = "dynamic"       # 動態相關性


class ClusteringMethod(str, Enum):
    """聚類方法"""
    HIERARCHICAL = "hierarchical"  # 層次聚類
    KMEANS = "kmeans"            # K-means
    DBSCAN = "dbscan"            # DBSCAN


@dataclass
class CorrelationConfig:
    """相關性分析配置"""
    # 計算參數
    method: CorrelationMethod = CorrelationMethod.PEARSON
    lookback_window: int = 252
    min_periods: int = 60

    # 動態相關性參數
    dynamic_window: int = 60
    rolling_window: int = 30

    # 閾值配置
    high_correlation_threshold: float = 0.7
    low_correlation_threshold: float = 0.3
    correlation_change_threshold: float = 0.2

    # 聚類配置
    clustering_method: ClusteringMethod = ClusteringMethod.HIERARCHICAL
    n_clusters: int = 5
    linkage_method: str = "ward"

    # 視覺化配置
    figsize: Tuple[int, int] = (12, 10)
    colormap: str = "RdBu_r"
    save_plots: bool = True
    plot_dir: str = "correlation_plots"


@dataclass
class CorrelationAlert:
    """相關性警報"""
    timestamp: datetime
    alert_type: str  # "spike", "breakdown", "concentration"
    assets: List[str]
    current_value: float
    threshold: float
    severity: str  # "low", "medium", "high", "critical"
    message: str


class CorrelationAnalyzer:
    """多資產相關性分析器"""

    def __init__(self, config: CorrelationConfig):
        """
        初始化相關性分析器

        Args:
            config: 相關性分析配置
        """
        self.config = config
        self.correlation_matrix: Optional[pd.DataFrame] = None
        self.dynamic_correlations: Dict[str, pd.DataFrame] = {}
        self.correlation_trends: Dict[str, pd.Series] = {}
        self.clusters: Dict[int, List[str]] = {}
        self.alerts: List[CorrelationAlert] = []

        # 歷史數據
        self.historical_correlations: List[Dict[str, Any]] = []
        self.correlation_summary: Dict[str, Any] = {}

        logger.info("Correlation Analyzer initialized")

    def calculate_correlation_matrix(
        self,
        returns_data: pd.DataFrame,
        update_history: bool = True
    ) -> pd.DataFrame:
        """
        計算相關性矩陣

        Args:
            returns_data: 收益率數據
            update_history: 是否更新歷史記錄

        Returns:
            相關性矩陣
        """
        try:
            # 數據預處理
            clean_data = self._preprocess_data(returns_data)

            # 計算相關性
            if self.config.method == CorrelationMethod.PEARSON:
                corr_matrix = clean_data.corr(method='pearson')
            elif self.config.method == CorrelationMethod.SPEARMAN:
                corr_matrix = clean_data.corr(method='spearman')
            elif self.config.method == CorrelationMethod.KENDALL:
                corr_matrix = clean_data.corr(method='kendall')
            else:
                corr_matrix = clean_data.corr(method='pearson')

            # 處理缺失值
            corr_matrix = corr_matrix.fillna(0)

            # 確保對稱性
            corr_matrix = (corr_matrix + corr_matrix.T) / 2

            self.correlation_matrix = corr_matrix

            # 更新歷史記錄
            if update_history:
                self._update_correlation_history(corr_matrix)

            # 檢查警報
            self._check_correlation_alerts(corr_matrix)

            # 計算摘要統計
            self._calculate_correlation_summary(corr_matrix)

            logger.info(f"Correlation matrix calculated: {len(corr_matrix)}x{len(corr_matrix)}")
            return corr_matrix

        except Exception as e:
            logger.error(f"Correlation calculation failed: {e}")
            raise

    def calculate_dynamic_correlations(
        self,
        returns_data: pd.DataFrame
    ) -> Dict[str, pd.DataFrame]:
        """
        計算動態相關性

        Args:
            returns_data: 收益率數據

        Returns:
            不同時間窗口的動態相關性字典
        """
        try:
            dynamic_corrs = {}

            # 計算不同窗口的滾動相關性
            for window in [30, 60, 90, 180]:
                if len(returns_data) >= window:
                    rolling_corr = returns_data.rolling(window=window).corr()
                    dynamic_corrs[f"{window}d"] = rolling_corr

            # 計算擴展窗口相關性
            expanding_corr = returns_data.expanding().corr()
            dynamic_corrs["expanding"] = expanding_corr

            self.dynamic_correlations = dynamic_corrs

            # 計算相關性趨勢
            self._calculate_correlation_trends(dynamic_corrs)

            logger.info(f"Dynamic correlations calculated: {len(dynamic_corrs)} windows")
            return dynamic_corrs

        except Exception as e:
            logger.error(f"Dynamic correlation calculation failed: {e}")
            raise

    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """預處理數據"""
        # 去除缺失值過多的列
        min_periods = max(self.config.min_periods, len(data) * 0.5)
        clean_data = data.dropna(axis=1, thresh=min_periods)

        # 去除缺失值過多的行
        clean_data = clean_data.dropna(axis=0, thresh=len(clean_data.columns) * 0.5)

        # 前向填充剩餘缺失值
        clean_data = clean_data.fillna(method='ffill').fillna(method='bfill')

        # 去除常數列
        clean_data = clean_data.loc[:, clean_data.nunique() > 1]

        return clean_data

    def _update_correlation_history(self, corr_matrix: pd.DataFrame):
        """更新相關性歷史記錄"""
        # 提取關鍵統計量
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        ).stack()

        history_entry = {
            "timestamp": datetime.now(),
            "mean_correlation": upper_triangle.mean(),
            "median_correlation": upper_triangle.median(),
            "std_correlation": upper_triangle.std(),
            "max_correlation": upper_triangle.max(),
            "min_correlation": upper_triangle.min(),
            "high_corr_pairs": len(upper_triangle[upper_triangle > self.config.high_correlation_threshold]),
            "low_corr_pairs": len(upper_triangle[upper_triangle < self.config.low_correlation_threshold]),
            "correlation_matrix": corr_matrix.copy()
        }

        self.historical_correlations.append(history_entry)

        # 限制歷史記錄長度
        if len(self.historical_correlations) > 100:
            self.historical_correlations = self.historical_correlations[-100:]

    def _calculate_correlation_trends(self, dynamic_corrs: Dict[str, pd.DataFrame]):
        """計算相關性趨勢"""
        self.correlation_trends = {}

        # 使用60天滾動窗口計算趨勢
        if "60d" in dynamic_corrs:
            rolling_corr = dynamic_corrs["60d"]

            # 對每個資產對計算趨勢
            assets = rolling_corr.index.get_level_values(0).unique()
            for asset1 in assets:
                for asset2 in assets:
                    if asset1 != asset2:
                        pair = f"{asset1}-{asset2}"
                        try:
                            pair_corr = rolling_corr.loc[(asset1, asset2)]
                            if not pair_corr.empty:
                                # 計算趨勢（線性回歸斜率）
                                x = np.arange(len(pair_corr))
                                slope, _, _, _, _ = stats.linregress(x, pair_corr.dropna().values)
                                self.correlation_trends[pair] = slope
                        except:
                            continue

    def _check_correlation_alerts(self, corr_matrix: pd.DataFrame):
        """檢查相關性警報"""
        current_time = datetime.now()
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        ).stack()

        # 檢查高相關性警報
        high_corr_pairs = upper_triangle[upper_triangle > self.config.high_correlation_threshold]
        for (asset1, asset2), corr_value in high_corr_pairs.items():
            alert = CorrelationAlert(
                timestamp=current_time,
                alert_type="high_correlation",
                assets=[asset1, asset2],
                current_value=corr_value,
                threshold=self.config.high_correlation_threshold,
                severity="high" if corr_value > 0.9 else "medium",
                message=f"High correlation detected: {asset1}-{asset2} = {corr_value:.3f}"
            )
            self.alerts.append(alert)

        # 檢查相關性突變（如果有歷史數據）
        if len(self.historical_correlations) > 0:
            prev_corr = self.historical_correlations[-1]["correlation_matrix"]
            change_matrix = abs(corr_matrix - prev_corr)

            high_change_pairs = change_matrix.where(
                np.triu(np.ones(change_matrix.shape), k=1).astype(bool)
            ).stack()

            high_change_pairs = high_change_pairs[
                high_change_pairs > self.config.correlation_change_threshold
            ]

            for (asset1, asset2), change_value in high_change_pairs.items():
                alert = CorrelationAlert(
                    timestamp=current_time,
                    alert_type="correlation_spike",
                    assets=[asset1, asset2],
                    current_value=change_value,
                    threshold=self.config.correlation_change_threshold,
                    severity="critical" if change_value > 0.5 else "medium",
                    message=f"Correlation spike: {asset1}-{asset2} changed by {change_value:.3f}"
                )
                self.alerts.append(alert)

        # 檢查集中度風險
        self._check_concentration_risk(corr_matrix, current_time)

        # 限制警報數量
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def _check_concentration_risk(self, corr_matrix: pd.DataFrame, current_time: datetime):
        """檢查集中度風險"""
        # 使用主成分分析檢查集中度
        try:
            pca = PCA(n_components=min(5, len(corr_matrix)))
            pca.fit(corr_matrix.fillna(0))

            # 第一主成分的方差比例
            first_component_variance = pca.explained_variance_ratio_[0]

            if first_component_variance > 0.5:  # 如果第一主成分解釋超過50%的方差
                alert = CorrelationAlert(
                    timestamp=current_time,
                    alert_type="concentration_risk",
                    assets=list(corr_matrix.columns),
                    current_value=first_component_variance,
                    threshold=0.5,
                    severity="high",
                    message=f"High concentration risk detected: PC1 explains {first_component_variance:.1%} of variance"
                )
                self.alerts.append(alert)

        except Exception as e:
            logger.warning(f"Concentration risk check failed: {e}")

    def _calculate_correlation_summary(self, corr_matrix: pd.DataFrame):
        """計算相關性摘要統計"""
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        ).stack()

        self.correlation_summary = {
            "mean_correlation": upper_triangle.mean(),
            "median_correlation": upper_triangle.median(),
            "std_correlation": upper_triangle.std(),
            "min_correlation": upper_triangle.min(),
            "max_correlation": upper_triangle.max(),
            "total_pairs": len(upper_triangle),
            "high_corr_count": len(upper_triangle[upper_triangle > self.config.high_correlation_threshold]),
            "low_corr_count": len(upper_triangle[upper_triangle < self.config.low_correlation_threshold]),
            "negative_corr_count": len(upper_triangle[upper_triangle < 0]),
            "effective_pairs": len(upper_triangle[abs(upper_triangle) > 0.1])
        }

    def cluster_assets(
        self,
        correlation_matrix: Optional[pd.DataFrame] = None,
        method: Optional[ClusteringMethod] = None
    ) -> Dict[int, List[str]]:
        """
        基於相關性對資產進行聚類

        Args:
            correlation_matrix: 相關性矩陣（可選）
            method: 聚類方法（可選）

        Returns:
            聚類結果字典
        """
        try:
            if correlation_matrix is None:
                correlation_matrix = self.correlation_matrix

            if correlation_matrix is None:
                raise ValueError("No correlation matrix available")

            method = method or self.config.clustering_method

            if method == ClusteringMethod.HIERARCHICAL:
                clusters = self._hierarchical_clustering(correlation_matrix)
            elif method == ClusteringMethod.KMEANS:
                clusters = self._kmeans_clustering(correlation_matrix)
            else:
                clusters = self._hierarchical_clustering(correlation_matrix)

            self.clusters = clusters
            logger.info(f"Assets clustered into {len(clusters)} groups")
            return clusters

        except Exception as e:
            logger.error(f"Asset clustering failed: {e}")
            raise

    def _hierarchical_clustering(
        self,
        correlation_matrix: pd.DataFrame
    ) -> Dict[int, List[str]]:
        """層次聚類"""
        # 將相關性轉換為距離
        distance_matrix = 1 - np.abs(correlation_matrix)

        # 層次聚類
        linkage_matrix = linkage(
            distance_matrix,
            method=self.config.linkage_method
        )

        # 切割聚類
        clusters = fcluster(
            linkage_matrix,
            t=self.config.n_clusters,
            criterion='maxclust'
        )

        # 整理結果
        cluster_dict = {}
        for asset, cluster_id in zip(correlation_matrix.columns, clusters):
            if cluster_id not in cluster_dict:
                cluster_dict[cluster_id] = []
            cluster_dict[cluster_id].append(asset)

        return cluster_dict

    def _kmeans_clustering(
        self,
        correlation_matrix: pd.DataFrame
    ) -> Dict[int, List[str]]:
        """K-means聚類"""
        from sklearn.cluster import KMeans

        # 使用相關性矩陣作為特徵
        features = correlation_matrix.fillna(0).values

        # K-means聚類
        kmeans = KMeans(
            n_clusters=self.config.n_clusters,
            random_state=42
        )
        cluster_labels = kmeans.fit_predict(features)

        # 整理結果
        cluster_dict = {}
        for asset, label in zip(correlation_matrix.columns, cluster_labels):
            if label not in cluster_dict:
                cluster_dict[label] = []
            cluster_dict[label].append(asset)

        return cluster_dict

    def analyze_correlation_changes(
        self,
        window1: int = 60,
        window2: int = 252
    ) -> Dict[str, Any]:
        """
        分析相關性變化

        Args:
            window1: 短期窗口
            window2: 長期窗口

        Returns:
            相關性變化分析結果
        """
        try:
            if not self.dynamic_correlations:
                raise ValueError("No dynamic correlations available")

            # 獲取不同窗口的相關性
            short_term_corr = None
            long_term_corr = None

            if f"{window1}d" in self.dynamic_correlations:
                short_term_corr = self.dynamic_correlations[f"{window1}d"].iloc[-1]

            if f"{window2}d" in self.dynamic_correlations:
                long_term_corr = self.dynamic_correlations[f"{window2}d"].iloc[-1]

            if short_term_corr is None or long_term_corr is None:
                raise ValueError("Required correlation windows not available")

            # 計算變化
            correlation_change = short_term_corr - long_term_corr

            # 提取上三角矩陣
            upper_change = correlation_change.where(
                np.triu(np.ones(correlation_change.shape), k=1).astype(bool)
            ).stack()

            # 分析結果
            analysis = {
                "mean_change": upper_change.mean(),
                "std_change": upper_change.std(),
                "max_increase": upper_change.max(),
                "max_decrease": upper_change.min(),
                "significant_changes": len(upper_change[abs(upper_change) > 0.2]),
                "destabilized_pairs": upper_change[abs(upper_change) > 0.3].to_dict()
            }

            # 識別最不穩定的資產對
            most_volatile = abs(upper_change).nlargest(5)
            analysis["most_volatile_pairs"] = most_volatile.to_dict()

            return analysis

        except Exception as e:
            logger.error(f"Correlation change analysis failed: {e}")
            raise

    def calculate_diversification_ratio(
        self,
        weights: Dict[str, float],
        correlation_matrix: Optional[pd.DataFrame] = None
    ) -> float:
        """
        計算分散化比率

        Args:
            weights: 資產權重
            correlation_matrix: 相關性矩陣（可選）

        Returns:
            分散化比率
        """
        try:
            if correlation_matrix is None:
                correlation_matrix = self.correlation_matrix

            if correlation_matrix is None:
                raise ValueError("No correlation matrix available")

            # 構建權重向量
            assets = list(weights.keys())
            weights_array = np.array([weights.get(asset, 0) for asset in assets])

            # 提取相關的子矩陣
            corr_subset = correlation_matrix.loc[assets, assets]

            # 計算投資組合波動率
            portfolio_variance = weights_array @ corr_subset.values @ weights_array

            # 計算加權平均相關性
            weighted_correlations = []
            for i, asset1 in enumerate(assets):
                for j, asset2 in enumerate(assets):
                    if i != j:
                        weighted_correlations.append(
                            weights_array[i] * weights_array[j] * corr_subset.iloc[i, j]
                        )

            avg_correlation = np.sum(weighted_correlations) / (np.sum(weights_array) ** 2 - np.sum(weights_array ** 2))

            # 分散化比率
            if avg_correlation < 1:
                diversification_ratio = np.sqrt(1 + (len(assets) - 1) * avg_correlation)
            else:
                diversification_ratio = 1.0

            return diversification_ratio

        except Exception as e:
            logger.error(f"Diversification ratio calculation failed: {e}")
            return 1.0

    def generate_correlation_report(self) -> Dict[str, Any]:
        """生成相關性分析報告"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "configuration": {
                    "method": self.config.method.value,
                    "lookback_window": self.config.lookback_window,
                    "high_correlation_threshold": self.config.high_correlation_threshold,
                    "low_correlation_threshold": self.config.low_correlation_threshold
                },
                "current_correlation_summary": self.correlation_summary,
                "clusters": self.clusters,
                "recent_alerts": self.alerts[-10:] if self.alerts else [],
                "correlation_trends": self.correlation_trends
            }

            # 添加歷史趨勢
            if len(self.historical_correlations) > 1:
                recent_history = self.historical_correlations[-10:]
                report["historical_trends"] = {
                    "mean_correlation_trend": [h["mean_correlation"] for h in recent_history],
                    "volatility_trend": [h["std_correlation"] for h in recent_history],
                    "high_corr_count_trend": [h["high_corr_pairs"] for h in recent_history]
                }

            # 添加集中度風險分析
            if self.correlation_matrix is not None:
                pca = PCA(n_components=5)
                pca.fit(self.correlation_matrix.fillna(0))
                report["concentration_analysis"] = {
                    "first_component_variance": pca.explained_variance_ratio_[0],
                    "cumulative_variance_3_components": sum(pca.explained_variance_ratio_[:3]),
                    "effective_dimensions": sum(pca.explained_variance_ratio_ > 0.1)
                }

            return report

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {}

    def plot_correlation_matrix(
        self,
        correlation_matrix: Optional[pd.DataFrame] = None,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        繪製相關性矩陣熱圖

        Args:
            correlation_matrix: 相關性矩陣（可選）
            save_path: 保存路徑（可選）

        Returns:
            matplotlib圖形對象
        """
        try:
            if correlation_matrix is None:
                correlation_matrix = self.correlation_matrix

            if correlation_matrix is None:
                raise ValueError("No correlation matrix available")

            # 創建圖形
            fig, ax = plt.subplots(figsize=self.config.figsize)

            # 繪製熱圖
            sns.heatmap(
                correlation_matrix,
                annot=True,
                cmap=self.config.colormap,
                center=0,
                square=True,
                fmt=".2f",
                ax=ax
            )

            ax.set_title("Asset Correlation Matrix", fontsize=14, fontweight='bold')
            plt.tight_layout()

            # 保存圖形
            if save_path or self.config.save_plots:
                if save_path is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = f"{self.config.plot_dir}/correlation_matrix_{timestamp}.png"

                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Correlation matrix plot saved: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"Correlation matrix plotting failed: {e}")
            raise

    def plot_dynamic_correlations(
        self,
        asset_pairs: List[Tuple[str, str]],
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        繪製動態相關性圖表

        Args:
            asset_pairs: 資產對列表
            save_path: 保存路徑（可選）

        Returns:
            matplotlib圖形對象
        """
        try:
            if not self.dynamic_correlations:
                raise ValueError("No dynamic correlations available")

            fig, axes = plt.subplots(
                len(asset_pairs), 1,
                figsize=(12, 4 * len(asset_pairs)),
                squeeze=False
            )

            for i, (asset1, asset2) in enumerate(asset_pairs):
                ax = axes[i, 0]

                # 繪製不同窗口的動態相關性
                for window_name, corr_data in self.dynamic_correlations.items():
                    if window_name != "expanding":
                        try:
                            pair_corr = corr_data.loc[(asset1, asset2)]
                            pair_corr.plot(
                                ax=ax,
                                label=f"{window_name}",
                                alpha=0.7
                            )
                        except KeyError:
                            continue

                ax.set_title(f"{asset1} - {asset2} Dynamic Correlation")
                ax.set_ylabel("Correlation")
                ax.legend()
                ax.grid(True, alpha=0.3)

            plt.tight_layout()

            # 保存圖形
            if save_path or self.config.save_plots:
                if save_path is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = f"{self.config.plot_dir}/dynamic_correlations_{timestamp}.png"

                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Dynamic correlations plot saved: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"Dynamic correlations plotting failed: {e}")
            raise

    def export_correlation_data(
        self,
        filepath: str,
        format: str = "csv"
    ):
        """
        導出相關性數據

        Args:
            filepath: 文件路徑
            format: 導出格式（csv, json, excel）
        """
        try:
            # 準備導出數據
            export_data = {
                "correlation_matrix": self.correlation_matrix,
                "correlation_summary": self.correlation_summary,
                "clusters": self.clusters,
                "alerts": [
                    {
                        "timestamp": alert.timestamp.isoformat(),
                        "type": alert.alert_type,
                        "assets": alert.assets,
                        "value": alert.current_value,
                        "severity": alert.severity,
                        "message": alert.message
                    }
                    for alert in self.alerts
                ]
            }

            # 根據格式導出
            if format.lower() == "csv":
                # 導出CSV文件
                self.correlation_matrix.to_csv(f"{filepath}_correlation_matrix.csv")
                pd.DataFrame([export_data["correlation_summary"]]).to_csv(
                    f"{filepath}_summary.csv", index=False
                )
            elif format.lower() == "json":
                # 導出JSON文件
                import json
                with open(f"{filepath}.json", "w") as f:
                    # 轉換為可序列化格式
                    json_data = {
                        "correlation_matrix": self.correlation_matrix.to_dict(),
                        "correlation_summary": export_data["correlation_summary"],
                        "clusters": export_data["clusters"],
                        "alerts": export_data["alerts"]
                    }
                    json.dump(json_data, f, indent=2)
            elif format.lower() == "excel":
                # 導出Excel文件
                with pd.ExcelWriter(f"{filepath}.xlsx") as writer:
                    self.correlation_matrix.to_excel(writer, sheet_name="Correlation Matrix")
                    pd.DataFrame([export_data["correlation_summary"]]).to_excel(
                        writer, sheet_name="Summary", index=False
                    )
                    pd.DataFrame(export_data["alerts"]).to_excel(
                        writer, sheet_name="Alerts", index=False
                    )

            logger.info(f"Correlation data exported: {filepath}.{format}")

        except Exception as e:
            logger.error(f"Data export failed: {e}")
            raise