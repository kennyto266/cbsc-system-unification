#!/usr / bin / env python3
"""
Statistical Anomaly Detector - Task 15
统计异常检测器 - 任务15

Advanced statistical anomaly detection with multiple algorithms
多算法高级统计异常检测

This module implements sophisticated anomaly detection including:
- IQR - based outlier detection
- Z - score analysis
- Isolation Forest
- Volatility pattern detection
- Distribution analysis (skewness, kurtosis, multimodal detection)
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import jarque_bera, normaltest
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .content_validation_layer import AnomalyDetection, AnomalyType, ValidationSeverity
from .interfaces.auth_result import AuthResult, Verdict

# Import authentication interfaces
from .interfaces.verifier_interface import IVerifier

# Setup logging
logger = logging.getLogger(__name__)


class DetectionMethod(str, Enum):
    """检测方法"""

    IQR = "iqr"
    Z_SCORE = "z_score"
    ISOLATION_FOREST = "isolation_forest"
    DBSCAN = "dbscan"
    VOLATILITY = "volatility"
    DISTRIBUTION = "distribution"


@dataclass
class AnomalyResult:
    """异常检测结果"""

    method: DetectionMethod
    anomalies_detected: List[AnomalyDetection]
    total_records: int
    anomaly_count: int
    anomaly_rate: float
    confidence: float
    execution_time_ms: float
    details: Dict[str, Any] = field(default_factory = dict)


class StatisticalAnomalyDetector(IVerifier):
    """统计异常检测器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("StatisticalAnomalyDetector", config)
        self.supported_data_types = ["stock_data", "economic_data", "government_data"]

        # 配置参数
        self.z_score_threshold = self.config.get("z_score_threshold", 3.0)
        self.iqr_multiplier = self.config.get("iqr_multiplier", 1.5)
        self.isolation_forest_contamination = self.config.get(
            "isolation_forest_contamination", 0.1
        )
        self.volatility_window = self.config.get("volatility_window", 20)
        self.volatility_threshold = self.config.get("volatility_threshold", 2.0)
        self.min_samples_for_analysis = self.config.get("min_samples_for_analysis", 30)

    def get_verifier_type(self) -> str:
        return "statistical_anomaly"

    def get_supported_data_types(self) -> List[str]:
        return self.supported_data_types

    async def verify(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """执行统计异常检测"""
        start_time = time.time()

        try:
            # 准备数据
            df = self._prepare_dataframe(data)

            if len(df) < self.min_samples_for_analysis:
                return AuthResult(
                    data_id = data_id,
                    data_type=(
                        context.get("data_type", "unknown") if context else "unknown"
                    ),
                    data_source=(
                        context.get("data_source", "unknown") if context else "unknown"
                    ),
                    overall_verdict = Verdict.UNKNOWN,
                    overall_confidence = 0.5,
                    status="completed",
                    total_execution_time_ms=(time.time() - start_time) * 1000,
                    metadata={
                        "message": f"Insufficient data for anomaly detection. Minimum {self.min_samples_for_analysis} records required.",
                        "actual_records": len(df),
                    },
                )

            # 执行多种异常检测方法
            anomaly_results = await self._run_all_detection_methods(df)

            # 聚合结果
            all_anomalies = []
            for result in anomaly_results:
                all_anomalies.extend(result.anomalies_detected)

            # 计算综合置信度
            avg_anomaly_rate = np.mean([r.anomaly_rate for r in anomaly_results])
            avg_confidence = np.mean([r.confidence for r in anomaly_results])

            # 确定最终结论
            if avg_anomaly_rate > 0.2:  # 超过20%的异常率
                verdict = Verdict.FALSIFIED
                confidence = max(0.1, 1.0 - avg_anomaly_rate)
            elif avg_anomaly_rate > 0.05:  # 5%-20%的异常率
                verdict = Verdict.SUSPICIOUS
                confidence = 0.6
            else:
                verdict = Verdict.AUTHENTIC
                confidence = avg_confidence

            execution_time = (time.time() - start_time) * 1000

            result = AuthResult(
                data_id = data_id,
                data_type = context.get("data_type", "unknown") if context else "unknown",
                data_source=(
                    context.get("data_source", "unknown") if context else "unknown"
                ),
                overall_verdict = verdict,
                overall_confidence = confidence,
                status="completed",
                total_execution_time_ms = execution_time,
                metadata={
                    "anomaly_results": [r.__dict__ for r in anomaly_results],
                    "total_anomalies": len(all_anomalies),
                    "avg_anomaly_rate": avg_anomaly_rate,
                    "methods_used": [r.method.value for r in anomaly_results],
                    "summary": {
                        "total_records": len(df),
                        "total_anomalies": len(all_anomalies),
                        "overall_anomaly_rate": (
                            len(all_anomalies) / len(df) if len(df) > 0 else 0
                        ),
                    },
                },
            )

            logger.info(
                f"Statistical anomaly detection completed for {data_id}: {verdict.value} "
                f"(confidence: {confidence:.3f}, anomalies: {len(all_anomalies)})"
            )
            return result

        except Exception as e:
            logger.error(
                f"Statistical anomaly detection failed for {data_id}: {str(e)}"
            )
            execution_time = (time.time() - start_time) * 1000
            return AuthResult(
                data_id = data_id,
                data_type="unknown",
                data_source="unknown",
                overall_verdict = Verdict.ERROR,
                overall_confidence = 0.0,
                status="failed",
                total_execution_time_ms = execution_time,
                error_message = str(e),
            )

    def _prepare_dataframe(self, data: Any) -> pd.DataFrame:
        """准备DataFrame"""
        if isinstance(data, dict) and "data" in data:
            df = pd.DataFrame(data["data"])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError(f"Unsupported data format: {type(data)}")

        return df

    async def _run_all_detection_methods(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """运行所有检测方法"""
        results = []

        # 1. IQR异常检测
        iqr_result = await self._detect_iqr_anomalies(df)
        results.append(iqr_result)

        # 2. Z - score异常检测
        zscore_result = await self._detect_zscore_anomalies(df)
        results.append(zscore_result)

        # 3. Isolation Forest异常检测
        isolation_result = await self._detect_isolation_forest_anomalies(df)
        results.append(isolation_result)

        # 4. 波动率异常检测
        volatility_result = await self._detect_volatility_anomalies(df)
        results.append(volatility_result)

        # 5. 分布异常检测
        distribution_result = await self._detect_distribution_anomalies(df)
        results.append(distribution_result)

        return results

    async def _detect_iqr_anomalies(self, df: pd.DataFrame) -> AnomalyResult:
        """IQR异常检测"""
        start_time = time.time()

        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            anomalies = []

            for col in numeric_cols:
                values = df[col].dropna()
                if len(values) < 10:  # 需要足够的数据点
                    continue

                # 计算IQR
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - self.iqr_multiplier * IQR
                upper_bound = Q3 + self.iqr_multiplier * IQR

                # 识别异常值
                outlier_mask = (values < lower_bound) | (values > upper_bound)
                outlier_indices = values[outlier_mask].index

                for idx in outlier_indices:
                    timestamp = (
                        df.loc[idx, "timestamp"]
                        if "timestamp" in df.columns
                        else df.loc[idx, "date"] if "date" in df.columns else idx
                    )

                    anomaly = AnomalyDetection(
                        anomaly_type = AnomalyType.STATISTICAL_OUTLIER,
                        timestamp = timestamp,
                        field_name = col,
                        value = df.loc[idx, col],
                        expected_range=(lower_bound, upper_bound),
                        severity=(
                            ValidationSeverity.HIGH
                            if outlier_mask.sum() > len(values) * 0.05
                            else ValidationSeverity.MEDIUM
                        ),
                        confidence = 0.8,
                        context={
                            "method": "IQR",
                            "iqr_multiplier": self.iqr_multiplier,
                            "Q1": Q1,
                            "Q3": Q3,
                            "IQR": IQR,
                        },
                    )
                    anomalies.append(anomaly)

            anomaly_rate = (
                len(anomalies) / (len(df) * len(numeric_cols))
                if len(numeric_cols) > 0
                else 0
            )
            confidence = max(0.3, 1.0 - anomaly_rate)

            execution_time = (time.time() - start_time) * 1000

            return AnomalyResult(
                method = DetectionMethod.IQR,
                anomalies_detected = anomalies,
                total_records = len(df),
                anomaly_count = len(anomalies),
                anomaly_rate = anomaly_rate,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "columns_analyzed": list(numeric_cols),
                    "iqr_multiplier": self.iqr_multiplier,
                    "anomalies_per_column": {
                        col: sum(1 for a in anomalies if a.field_name == col)
                        for col in numeric_cols
                    },
                },
            )

        except Exception as e:
            logger.error(f"IQR anomaly detection failed: {str(e)}")
            return AnomalyResult(
                method = DetectionMethod.IQR,
                anomalies_detected=[],
                total_records = len(df),
                anomaly_count = 0,
                anomaly_rate = 0.0,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _detect_zscore_anomalies(self, df: pd.DataFrame) -> AnomalyResult:
        """Z - score异常检测"""
        start_time = time.time()

        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            anomalies = []

            for col in numeric_cols:
                values = df[col].dropna()
                if len(values) < 10 or values.std() == 0:
                    continue

                # 计算Z - score
                z_scores = np.abs(stats.zscore(values))
                outlier_mask = z_scores > self.z_score_threshold
                outlier_indices = values[outlier_mask].index

                for idx in outlier_indices:
                    timestamp = (
                        df.loc[idx, "timestamp"]
                        if "timestamp" in df.columns
                        else df.loc[idx, "date"] if "date" in df.columns else idx
                    )

                    anomaly = AnomalyDetection(
                        anomaly_type = AnomalyType.STATISTICAL_OUTLIER,
                        timestamp = timestamp,
                        field_name = col,
                        value = df.loc[idx, col],
                        z_score = z_scores[values.index.get_loc(idx)],
                        severity=(
                            ValidationSeverity.HIGH
                            if z_scores[values.index.get_loc(idx)] > 4
                            else ValidationSeverity.MEDIUM
                        ),
                        confidence = 0.85,
                        context={
                            "method": "Z - Score",
                            "threshold": self.z_score_threshold,
                            "mean": values.mean(),
                            "std": values.std(),
                        },
                    )
                    anomalies.append(anomaly)

            anomaly_rate = (
                len(anomalies) / (len(df) * len(numeric_cols))
                if len(numeric_cols) > 0
                else 0
            )
            confidence = max(0.4, 1.0 - anomaly_rate)

            execution_time = (time.time() - start_time) * 1000

            return AnomalyResult(
                method = DetectionMethod.Z_SCORE,
                anomalies_detected = anomalies,
                total_records = len(df),
                anomaly_count = len(anomalies),
                anomaly_rate = anomaly_rate,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "columns_analyzed": list(numeric_cols),
                    "z_score_threshold": self.z_score_threshold,
                    "max_z_score": (
                        float(max([a.z_score or 0 for a in anomalies]))
                        if anomalies
                        else None
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Z - score anomaly detection failed: {str(e)}")
            return AnomalyResult(
                method = DetectionMethod.Z_SCORE,
                anomalies_detected=[],
                total_records = len(df),
                anomaly_count = 0,
                anomaly_rate = 0.0,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _detect_isolation_forest_anomalies(
        self, df: pd.DataFrame
    ) -> AnomalyResult:
        """Isolation Forest异常检测"""
        start_time = time.time()

        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return AnomalyResult(
                    method = DetectionMethod.ISOLATION_FOREST,
                    anomalies_detected=[],
                    total_records = len(df),
                    anomaly_count = 0,
                    anomaly_rate = 0.0,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "No numeric columns for analysis"},
                )

            # 准备数据
            feature_data = df[numeric_cols].dropna()
            if len(feature_data) < 20:
                return AnomalyResult(
                    method = DetectionMethod.ISOLATION_FOREST,
                    anomalies_detected=[],
                    total_records = len(df),
                    anomaly_count = 0,
                    anomaly_rate = 0.0,
                    confidence = 0.5,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "Insufficient data for Isolation Forest"},
                )

            # 标准化数据
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(feature_data)

            # 训练Isolation Forest
            iso_forest = IsolationForest(
                contamination = self.isolation_forest_contamination,
                random_state = 42,
                n_estimators = 100,
            )
            anomaly_labels = iso_forest.fit_predict(scaled_data)
            anomaly_scores = iso_forest.decision_function(scaled_data)

            # 识别异常（-1表示异常）
            anomaly_mask = anomaly_labels == -1
            anomaly_indices = feature_data[anomaly_mask].index

            anomalies = []
            for idx in anomaly_indices:
                timestamp = (
                    df.loc[idx, "timestamp"]
                    if "timestamp" in df.columns
                    else df.loc[idx, "date"] if "date" in df.columns else idx
                )

                # 获取最异常的特征
                feature_values = df.loc[idx, numeric_cols]
                most_anomalous_feature = numeric_cols[
                    np.argmax(np.abs(feature_values.values - feature_values.mean()))
                ]

                anomaly = AnomalyDetection(
                    anomaly_type = AnomalyType.STATISTICAL_OUTLIER,
                    timestamp = timestamp,
                    field_name = most_anomalous_feature,
                    value = df.loc[idx, most_anomalous_feature],
                    isolation_score = float(
                        anomaly_scores[feature_data.index.get_loc(idx)]
                    ),
                    severity=(
                        ValidationSeverity.HIGH
                        if anomaly_scores[feature_data.index.get_loc(idx)] < -0.5
                        else ValidationSeverity.MEDIUM
                    ),
                    confidence = 0.9,
                    context={
                        "method": "Isolation Forest",
                        "contamination": self.isolation_forest_contamination,
                        "all_features": {
                            col: df.loc[idx, col]
                            for col in numeric_cols
                            if not pd.isna(df.loc[idx, col])
                        },
                    },
                )
                anomalies.append(anomaly)

            anomaly_rate = len(anomalies) / len(df)
            confidence = max(
                0.5, 1.0 - abs(anomaly_rate - self.isolation_forest_contamination)
            )

            execution_time = (time.time() - start_time) * 1000

            return AnomalyResult(
                method = DetectionMethod.ISOLATION_FOREST,
                anomalies_detected = anomalies,
                total_records = len(df),
                anomaly_count = len(anomalies),
                anomaly_rate = anomaly_rate,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "columns_analyzed": list(numeric_cols),
                    "contamination_rate": self.isolation_forest_contamination,
                    "actual_anomaly_rate": anomaly_rate,
                    "features_used": len(numeric_cols),
                },
            )

        except Exception as e:
            logger.error(f"Isolation Forest anomaly detection failed: {str(e)}")
            return AnomalyResult(
                method = DetectionMethod.ISOLATION_FOREST,
                anomalies_detected=[],
                total_records = len(df),
                anomaly_count = 0,
                anomaly_rate = 0.0,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _detect_volatility_anomalies(self, df: pd.DataFrame) -> AnomalyResult:
        """波动率异常检测"""
        start_time = time.time()

        try:
            # 主要针对价格数据
            price_cols = ["close", "price", "value", "rate"]
            available_price_cols = [col for col in price_cols if col in df.columns]

            if not available_price_cols:
                return AnomalyResult(
                    method = DetectionMethod.VOLATILITY,
                    anomalies_detected=[],
                    total_records = len(df),
                    anomaly_count = 0,
                    anomaly_rate = 0.0,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={
                        "message": "No price / volume columns for volatility analysis"
                    },
                )

            anomalies = []

            for col in available_price_cols:
                if len(df[col].dropna()) < self.volatility_window + 1:
                    continue

                # 计算收益率
                returns = df[col].pct_change().dropna()

                # 计算滚动波动率
                rolling_vol = returns.rolling(window = self.volatility_window).std()

                # 计算波动率的统计特性
                vol_mean = rolling_vol.mean()
                vol_std = rolling_vol.std()

                # 识别异常波动率（超过均值 + threshold * 标准差）
                volatility_threshold = vol_mean + self.volatility_threshold * vol_std
                extreme_volatility_mask = rolling_vol > volatility_threshold

                extreme_indices = rolling_vol[extreme_volatility_mask].index

                for idx in extreme_indices:
                    timestamp = (
                        df.loc[idx, "timestamp"]
                        if "timestamp" in df.columns
                        else df.loc[idx, "date"] if "date" in df.columns else idx
                    )

                    # 检查对应的绝对价格变动
                    if idx > 0:
                        price_change_pct = (
                            abs(
                                (df.loc[idx, col] - df.loc[idx - 1, col])
                                / df.loc[idx - 1, col]
                            )
                            if df.loc[idx - 1, col] != 0
                            else 0
                        )
                    else:
                        price_change_pct = 0

                    anomaly = AnomalyDetection(
                        anomaly_type = AnomalyType.VOLATILITY_SPIKE,
                        timestamp = timestamp,
                        field_name = f"{col}_volatility",
                        value = rolling_vol.loc[idx],
                        severity=(
                            ValidationSeverity.CRITICAL
                            if price_change_pct > 0.1
                            else ValidationSeverity.HIGH
                        ),
                        confidence = 0.8,
                        context={
                            "method": "Volatility Analysis",
                            "rolling_window": self.volatility_window,
                            "volatility_threshold": volatility_threshold,
                            "price_change_pct": price_change_pct,
                            "current_volatility": rolling_vol.loc[idx],
                            "avg_volatility": vol_mean,
                        },
                    )
                    anomalies.append(anomaly)

            anomaly_rate = len(anomalies) / len(df)
            confidence = max(0.4, 1.0 - anomaly_rate)

            execution_time = (time.time() - start_time) * 1000

            return AnomalyResult(
                method = DetectionMethod.VOLATILITY,
                anomalies_detected = anomalies,
                total_records = len(df),
                anomaly_count = len(anomalies),
                anomaly_rate = anomaly_rate,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "price_columns_analyzed": available_price_cols,
                    "volatility_window": self.volatility_window,
                    "volatility_threshold": self.volatility_threshold,
                    "max_volatility": (
                        float(rolling_vol.max()) if "rolling_vol" in locals() else None
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Volatility anomaly detection failed: {str(e)}")
            return AnomalyResult(
                method = DetectionMethod.VOLATILITY,
                anomalies_detected=[],
                total_records = len(df),
                anomaly_count = 0,
                anomaly_rate = 0.0,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _detect_distribution_anomalies(self, df: pd.DataFrame) -> AnomalyResult:
        """分布异常检测"""
        start_time = time.time()

        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            anomalies = []

            for col in numeric_cols:
                values = df[col].dropna()
                if len(values) < 20:
                    continue

                # 1. 正态性检验
                try:
                    if len(values) >= 8:  # Jarque - Bera需要至少8个样本
                        jb_stat, jb_pvalue = jarque_bera(values)
                        is_normal_jb = jb_pvalue > 0.05
                    else:
                        is_normal_jb = False
                        jb_pvalue = None

                    if len(values) >= 8:  # D'Agostino's normality test
                        da_stat, da_pvalue = normaltest(values)
                        is_normal_da = da_pvalue > 0.05
                    else:
                        is_normal_da = False
                        da_pvalue = None
                except Exception:
                    is_normal_jb = is_normal_da = False
                    jb_pvalue = da_pvalue = None

                # 2. 偏度和峰度分析
                skewness = stats.skew(values)
                kurtosis = stats.kurtosis(values)

                # 异常的偏度（绝对值大于2）
                if abs(skewness) > 2:
                    # 找到导致偏度的极端值
                    if skewness > 0:  # 正偏
                        extreme_value = values.max()
                        extreme_idx = values.idxmax()
                    else:  # 负偏
                        extreme_value = values.min()
                        extreme_idx = values.idxmin()

                    timestamp = (
                        df.loc[extreme_idx, "timestamp"]
                        if "timestamp" in df.columns
                        else (
                            df.loc[extreme_idx, "date"]
                            if "date" in df.columns
                            else extreme_idx
                        )
                    )

                    anomaly = AnomalyDetection(
                        anomaly_type = AnomalyType.STATISTICAL_OUTLIER,
                        timestamp = timestamp,
                        field_name = col,
                        value = extreme_value,
                        severity = ValidationSeverity.MEDIUM,
                        confidence = 0.7,
                        context={
                            "method": "Distribution Analysis",
                            "skewness": skewness,
                            "threshold": 2.0,
                            "distribution_test": "skewness_analysis",
                        },
                    )
                    anomalies.append(anomaly)

                # 异常的峰度（绝对值大于7）
                if abs(kurtosis) > 7:
                    # 找到导致异常峰度的值
                    mean_val = values.mean()
                    std_val = values.std()

                    # 找到距离均值最远的点
                    z_scores = np.abs((values - mean_val) / std_val)
                    extreme_idx = values.index[z_scores.argmax()]
                    extreme_value = values.loc[extreme_idx]

                    timestamp = (
                        df.loc[extreme_idx, "timestamp"]
                        if "timestamp" in df.columns
                        else (
                            df.loc[extreme_idx, "date"]
                            if "date" in df.columns
                            else extreme_idx
                        )
                    )

                    anomaly = AnomalyDetection(
                        anomaly_type = AnomalyType.STATISTICAL_OUTLIER,
                        timestamp = timestamp,
                        field_name = col,
                        value = extreme_value,
                        severity = ValidationSeverity.MEDIUM,
                        confidence = 0.7,
                        context={
                            "method": "Distribution Analysis",
                            "kurtosis": kurtosis,
                            "threshold": 7.0,
                            "distribution_test": "kurtosis_analysis",
                        },
                    )
                    anomalies.append(anomaly)

                # 3. 多模态检测（如果数据不支持正态分布）
                if not (is_normal_jb or is_normal_da):
                    try:
                        # 使用DBSCAN检测潜在的集群
                        data_reshaped = values.values.reshape(-1, 1)
                        scaler = StandardScaler()
                        scaled_data = scaler.fit_transform(data_reshaped)

                        dbscan = DBSCAN(eps = 0.5, min_samples = max(5, len(values) // 10))
                        clusters = dbscan.fit_predict(scaled_data)

                        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)

                        # 如果发现多个集群，可能存在多模态分布
                        if n_clusters > 2:
                            # 将每个小集群标记为异常
                            cluster_sizes = pd.Series(
                                clusters[clusters != -1]
                            ).value_counts()
                            small_clusters = cluster_sizes[
                                cluster_sizes < len(values) * 0.1
                            ].index

                            for cluster in small_clusters:
                                cluster_indices = values.index[clusters == cluster]
                                for idx in cluster_indices:
                                    timestamp = (
                                        df.loc[idx, "timestamp"]
                                        if "timestamp" in df.columns
                                        else (
                                            df.loc[idx, "date"]
                                            if "date" in df.columns
                                            else idx
                                        )
                                    )

                                    anomaly = AnomalyDetection(
                                        anomaly_type = AnomalyType.STATISTICAL_OUTLIER,
                                        timestamp = timestamp,
                                        field_name = col,
                                        value = df.loc[idx, col],
                                        severity = ValidationSeverity.LOW,
                                        confidence = 0.6,
                                        context={
                                            "method": "Distribution Analysis",
                                            "cluster_id": int(cluster),
                                            "cluster_size": len(cluster_indices),
                                            "total_clusters": n_clusters,
                                            "distribution_test": "multimodal_detection",
                                        },
                                    )
                                    anomalies.append(anomaly)

                    except Exception as cluster_error:
                        logger.debug(
                            f"Clustering analysis failed for {col}: {str(cluster_error)}"
                        )

            anomaly_rate = (
                len(anomalies) / (len(df) * len(numeric_cols))
                if len(numeric_cols) > 0
                else 0
            )
            confidence = max(0.5, 1.0 - anomaly_rate)

            execution_time = (time.time() - start_time) * 1000

            return AnomalyResult(
                method = DetectionMethod.DISTRIBUTION,
                anomalies_detected = anomalies,
                total_records = len(df),
                anomaly_count = len(anomalies),
                anomaly_rate = anomaly_rate,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "columns_analyzed": list(numeric_cols),
                    "distribution_tests": [
                        "jarque_bera",
                        "normaltest",
                        "skewness",
                        "kurtosis",
                    ],
                    "anomalies_by_type": {
                        "skewness": sum(
                            1
                            for a in anomalies
                            if a.context.get("distribution_test") == "skewness_analysis"
                        ),
                        "kurtosis": sum(
                            1
                            for a in anomalies
                            if a.context.get("distribution_test") == "kurtosis_analysis"
                        ),
                        "multimodal": sum(
                            1
                            for a in anomalies
                            if a.context.get("distribution_test")
                            == "multimodal_detection"
                        ),
                    },
                },
            )

        except Exception as e:
            logger.error(f"Distribution anomaly detection failed: {str(e)}")
            return AnomalyResult(
                method = DetectionMethod.DISTRIBUTION,
                anomalies_detected=[],
                total_records = len(df),
                anomaly_count = 0,
                anomaly_rate = 0.0,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )


# Factory function
def create_statistical_anomaly_detector(
    config: Optional[Dict[str, Any]] = None,
) -> StatisticalAnomalyDetector:
    """创建统计异常检测器"""
    return StatisticalAnomalyDetector(config)


# Export
__all__ = [
    "StatisticalAnomalyDetector",
    "DetectionMethod",
    "AnomalyResult",
    "create_statistical_anomaly_detector",
]
