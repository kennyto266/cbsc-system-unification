"""
ML監控和漂移檢測系統
生產級別的機器學習模型監控、性能追蹤和數據漂移檢測

功能:
- 實時模型性能監控
- 數據漂移檢測和警報
- 模型預測品質評估
- 特徵分佈監控
- 異常檢測和警報系統
- 自動化模型性能報告
- A / B測試監控
"""

import asyncio
import json
import logging
import pickle
import uuid
import warnings
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# 統計和機器學習
from scipy import stats
from scipy.spatial.distance import jensenshannon

# 統計檢驗
from scipy.stats import chi2_contingency, ks_2samp, mannwhitneyu
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.preprocessing import StandardScaler

# 漂移檢測庫
try:
    import alibi_detect
    from alibi_detect.cd import ChiSquareDrift, KSDrift, MMDDrift
    from alibi_detect.od import IForest

    ALIBI_DETECT_AVAILABLE = True
except ImportError:
    ALIBI_DETECT_AVAILABLE = False

# 監控和可觀測性
try:
    import evidently
    from evidently.dashboard import Dashboard
    from evidently.metric_preset import (
        ClassificationPreset,
        DataDriftPreset,
        RegressionPreset,
    )
    from evidently.metrics import ColumnDriftMetric, DatasetDriftMetric
    from evidently.report import Report
    from evidently.test_suite import TestSuite

    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False

# 時間序列分析
try:
    import river
    from river import drift
    from river import stats as river_stats

    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False

# 監控和警報
try:
    import prometheus_client
    from prometheus_client import Counter, Gauge, Histogram, start_http_server

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from .feature_store import AdvancedFeatureStore

# 內部模組
from .model_registry import ModelRegistry


class AlertSeverity(Enum):
    """警報嚴重程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DriftType(Enum):
    """漂移類型"""

    COVARIATE_DRIFT = "covariate"  # 特徵分佈漂移
    PRIOR_DRIFT = "prior"  # 目標變量分佈漂移
    CONCEPT_DRIFT = "concept"  # 特徵 - 目標關係漂移
    PERFORMANCE_DRIFT = "performance"  # 模型性能漂移


class MonitoringMetric(Enum):
    """監控指標"""

    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    MAE = "mae"
    MSE = "mse"
    RMSE = "rmse"
    R2_SCORE = "r2"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    PREDICTION_DRIFT = "prediction_drift"
    FEATURE_DRIFT = "feature_drift"
    DATA_QUALITY = "data_quality"


@dataclass
class Alert:
    """警報"""

    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str = ""
    alert_type: str = ""
    severity: AlertSeverity = AlertSeverity.MEDIUM
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class ModelPerformanceSnapshot:
    """模型性能快照"""

    model_name: str
    timestamp: datetime
    metrics: Dict[str, float]
    sample_count: int
    latency_ms: Optional[float] = None
    error_rate: Optional[float] = None


@dataclass
class DriftDetectionResult:
    """漂移檢測結果"""

    feature_name: str
    drift_type: DriftType
    drift_score: float
    p_value: Optional[float] = None
    threshold: float = 0.05
    detected: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


class DataDriftDetector:
    """數據漂移檢測器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.drift_detector")
        self.config = config or self._default_config()

        # 檢測方法
        self.drift_detectors: Dict[str, Any] = {}
        self.reference_data: Dict[str, pd.DataFrame] = {}

        # 初始化檢測器
        self._initialize_detectors()

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "detection_methods": ["ks", "psi", "jensen_shannon", "chisquare"],
            "drift_threshold": 0.05,
            "window_size": 1000,
            "update_frequency": 100,
            "min_samples": 100,
        }

    def _initialize_detectors(self):
        """初始化漂移檢測器"""
        try:
            if ALIBI_DETECT_AVAILABLE:
                # 初始化Alibi Detect檢測器
                pass

            if RIVER_AVAILABLE:
                # 初始化River漂移檢測器
                pass

            self.logger.info("Drift detectors initialized")

        except Exception as e:
            self.logger.warning(f"Drift detector initialization failed: {str(e)}")

    def set_reference_data(self, feature_name: str, data: pd.Series):
        """設置參考數據"""
        self.reference_data[feature_name] = data.dropna()
        self.logger.info(f"Reference data set for {feature_name}: {len(data)} samples")

    async def detect_drift(
        self, current_data: pd.Series, feature_name: str, method: str = "ks"
    ) -> DriftDetectionResult:
        """檢測數據漂移"""
        try:
            if feature_name not in self.reference_data:
                raise ValueError(f"No reference data for feature {feature_name}")

            reference = self.reference_data[feature_name].dropna()
            current = current_data.dropna()

            if (
                len(reference) < self.config["min_samples"]
                or len(current) < self.config["min_samples"]
            ):
                return DriftDetectionResult(
                    feature_name=feature_name,
                    drift_type=DriftType.COVARIATE_DRIFT,
                    drift_score=0.0,
                    detected=False,
                    details={"error": "Insufficient samples"},
                )

            # 選擇檢測方法
            if method == "ks":
                result = self._ks_drift_test(reference, current, feature_name)
            elif method == "psi":
                result = self._psi_drift_test(reference, current, feature_name)
            elif method == "jensen_shannon":
                result = self._jensen_shannon_drift(reference, current, feature_name)
            elif method == "chisquare":
                result = self._chisquare_drift_test(reference, current, feature_name)
            elif method == "alibi_ks" and ALIBI_DETECT_AVAILABLE:
                result = await self._alibi_ks_drift(reference, current, feature_name)
            else:
                result = DriftDetectionResult(
                    feature_name=feature_name,
                    drift_type=DriftType.COVARIATE_DRIFT,
                    drift_score=0.0,
                    detected=False,
                    details={"error": f"Unsupported method: {method}"},
                )

            self.logger.info(
                f"Drift detection for {feature_name}: detected={result.detected}, score={result.drift_score:.4f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Drift detection failed for {feature_name}: {str(e)}")
            return DriftDetectionResult(
                feature_name=feature_name,
                drift_type=DriftType.COVARIATE_DRIFT,
                drift_score=0.0,
                detected=False,
                details={"error": str(e)},
            )

    def _ks_drift_test(
        self, reference: pd.Series, current: pd.Series, feature_name: str
    ) -> DriftDetectionResult:
        """Kolmogorov - Smirnov漂移檢測"""
        statistic, p_value = ks_2samp(reference, current)
        detected = p_value < self.config["drift_threshold"]

        return DriftDetectionResult(
            feature_name=feature_name,
            drift_type=DriftType.COVARIATE_DRIFT,
            drift_score=statistic,
            p_value=p_value,
            threshold=self.config["drift_threshold"],
            detected=detected,
            details={
                "method": "ks",
                "sample_sizes": {"reference": len(reference), "current": len(current)},
            },
        )

    def _psi_drift_test(
        self,
        reference: pd.Series,
        current: pd.Series,
        feature_name: str,
        bins: int = 10,
    ) -> DriftDetectionResult:
        """Population Stability Index (PSI) 漂移檢測"""
        # 計算分桶邊界
        min_val = min(reference.min(), current.min())
        max_val = max(reference.max(), current.max())
        bin_edges = np.linspace(min_val, max_val, bins + 1)

        # 計算分桶頻率
        ref_counts, _ = np.histogram(reference, bins=bin_edges)
        cur_counts, _ = np.histogram(current, bins=bin_edges)

        # 避免零計數
        ref_counts = np.maximum(ref_counts, 1)
        cur_counts = np.maximum(cur_counts, 1)

        # 計算比例
        ref_percents = ref_counts / len(reference)
        cur_percents = cur_counts / len(current)

        # 計算PSI
        psi = np.sum(
            (ref_percents - cur_percents) * np.log(ref_percents / cur_percents)
        )

        # PSI閾值 (通常 < 0.1 無漂移, 0.1 - 0.25 中等漂移, > 0.25 大漂移)
        detected = psi > 0.1

        return DriftDetectionResult(
            feature_name=feature_name,
            drift_type=DriftType.COVARIATE_DRIFT,
            drift_score=psi,
            threshold=0.1,
            detected=detected,
            details={
                "method": "psi",
                "psi_level": "low" if psi < 0.1 else "medium" if psi < 0.25 else "high",
            },
        )

    def _jensen_shannon_drift(
        self, reference: pd.Series, current: pd.Series, feature_name: str
    ) -> DriftDetectionResult:
        """Jensen - Shannon距離漂移檢測"""
        # 創建直方圖
        min_val = min(reference.min(), current.min())
        max_val = max(reference.max(), current.max())
        bins = 50
        bin_edges = np.linspace(min_val, max_val, bins + 1)

        ref_hist, _ = np.histogram(reference, bins=bin_edges, density=True)
        cur_hist, _ = np.histogram(current, bins=bin_edges, density=True)

        # 計算Jensen - Shannon距離
        js_distance = jensenshannon(ref_hist, cur_hist)
        js_divergence = js_distance ** 2

        # 閾值 (需要經驗確定)
        detected = js_divergence > 0.1

        return DriftDetectionResult(
            feature_name=feature_name,
            drift_type=DriftType.COVARIATE_DRIFT,
            drift_score=js_divergence,
            threshold=0.1,
            detected=detected,
            details={"method": "jensen_shannon", "js_distance": js_distance},
        )

    def _chisquare_drift_test(
        self, reference: pd.Series, current: pd.Series, feature_name: str
    ) -> DriftDetectionResult:
        """卡方檢測漂移檢測"""
        # 離散化數據
        bins = 10
        ref_binned = pd.cut(reference, bins=bins, include_lowest=True)
        cur_binned = pd.cut(current, bins=bins, include_lowest=True)

        # 創建列聯表
        contingency_table = pd.crosstab(
            pd.Series(["reference"] * len(ref_binned)), ref_binned
        )
        cur_table = pd.crosstab(pd.Series(["current"] * len(cur_binned)), cur_binned)

        # 合併表
        combined_table = pd.concat([contingency_table, cur_table])

        # 執行卡方檢驗
        chi2, p_value, _, _ = chi2_contingency(combined_table)

        detected = p_value < self.config["drift_threshold"]

        return DriftDetectionResult(
            feature_name=feature_name,
            drift_type=DriftType.COVARIATE_DRIFT,
            drift_score=chi2,
            p_value=p_value,
            threshold=self.config["drift_threshold"],
            detected=detected,
            details={
                "method": "chisquare",
                "degrees_of_freedom": len(combined_table.columns) - 1,
            },
        )

    async def _alibi_ks_drift(
        self, reference: pd.Series, current: pd.Series, feature_name: str
    ) -> DriftDetectionResult:
        """使用Alibi Detect進行KS漂移檢測"""
        try:
            # 準備數據
            X_ref = reference.values.reshape(-1, 1).astype(np.float32)
            X_test = current.values.reshape(-1, 1).astype(np.float32)

            # 創建檢測器
            cd = KSDrift(X_ref, p_val=self.config["drift_threshold"])

            # 執行檢測
            predictions = cd.predict(X_test)

            drift_score = np.mean(predictions["data"]["p_val"])
            detected = predictions["data"]["is_drift"]

            return DriftDetectionResult(
                feature_name=feature_name,
                drift_type=DriftType.COVARIATE_DRIFT,
                drift_score=drift_score,
                detected=detected,
                details={"method": "alibi_ks", "p_vals": predictions["data"]["p_val"]},
            )

        except Exception as e:
            self.logger.warning(f"Alibi KS drift detection failed: {str(e)}")
            return self._ks_drift_test(reference, current, feature_name)


class ModelPerformanceMonitor:
    """模型性能監控器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.performance_monitor")
        self.config = config or self._default_config()

        # 性能歷史
        self.performance_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )

        # Prometheus指標
        self.prometheus_metrics = {}
        if PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()

        # 性能閾值
        self.performance_thresholds = self.config.get("thresholds", {})

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "evaluation_window": 100,  # 評估窗口大小
            "alert_thresholds": {
                "accuracy_drop": 0.1,  # 準確率下降閾值
                "error_rate_increase": 0.05,  # 錯誤率增加閾值
                "latency_increase": 100,  # 延遲增加閾值 (ms)
                "drift_threshold": 0.05,  # 漂移檢測閾值
            },
            "monitoring_metrics": [
                "accuracy",
                "precision",
                "recall",
                "f1_score",
                "mae",
                "mse",
                "rmse",
                "r2_score",
                "latency",
                "throughput",
                "error_rate",
            ],
        }

    def _init_prometheus_metrics(self):
        """初始化Prometheus指標"""
        try:
            self.prometheus_metrics = {
                "predictions_total": Counter(
                    "ml_model_predictions_total",
                    "Total number of predictions",
                    ["model_name", "status"],
                ),
                "prediction_latency": Histogram(
                    "ml_model_prediction_latency_seconds",
                    "Prediction latency in seconds",
                    ["model_name"],
                ),
                "model_accuracy": Gauge(
                    "ml_model_accuracy", "Model accuracy", ["model_name"]
                ),
                "model_error_rate": Gauge(
                    "ml_model_error_rate", "Model error rate", ["model_name"]
                ),
                "drift_detection_score": Gauge(
                    "ml_drift_detection_score",
                    "Drift detection score",
                    ["model_name", "feature"],
                ),
            }
        except Exception as e:
            self.logger.warning(f"Prometheus metrics initialization failed: {str(e)}")

    async def record_prediction(
        self,
        model_name: str,
        prediction: Any,
        ground_truth: Optional[Any] = None,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """記錄預測和計算性能指標"""
        try:
            timestamp = datetime.now()

            # 基礎指標
            metrics = {
                "timestamp": timestamp.timestamp(),
                "latency_ms": latency_ms or 0,
                "prediction_count": 1,
            }

            # 計算預測質量指標
            if ground_truth is not None:
                prediction_quality = self._calculate_prediction_quality(
                    prediction, ground_truth
                )
                metrics.update(prediction_quality)

            # 更新性能歷史
            snapshot = ModelPerformanceSnapshot(
                model_name=model_name,
                timestamp=timestamp,
                metrics=metrics,
                sample_count=1,
                latency_ms=latency_ms,
            )

            self.performance_history[model_name].append(snapshot)

            # 更新Prometheus指標
            if PROMETHEUS_AVAILABLE and self.prometheus_metrics:
                self._update_prometheus_metrics(model_name, metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to record prediction: {str(e)}")
            return {}

    def _calculate_prediction_quality(
        self, prediction: Any, ground_truth: Any
    ) -> Dict[str, float]:
        """計算預測質量指標"""
        try:
            # 將預測和真實值轉換為數值數組
            y_true = np.array([ground_truth])
            y_pred = np.array([prediction])

            metrics = {}

            # 分類指標
            if len(np.unique(y_true)) <= 10:  # 假設是分類問題
                metrics["accuracy"] = accuracy_score(y_true, y_pred)
                metrics["precision"] = precision_score(
                    y_true, y_pred, average="weighted", zero_division=0
                )
                metrics["recall"] = recall_score(
                    y_true, y_pred, average="weighted", zero_division=0
                )
                metrics["f1_score"] = f1_score(
                    y_true, y_pred, average="weighted", zero_division=0
                )
            else:  # 回歸指標
                metrics["mae"] = mean_absolute_error(y_true, y_pred)
                metrics["mse"] = mean_squared_error(y_true, y_pred)
                metrics["rmse"] = np.sqrt(metrics["mse"])
                metrics["r2_score"] = r2_score(y_true, y_pred)

            return metrics

        except Exception as e:
            self.logger.warning(f"Prediction quality calculation failed: {str(e)}")
            return {}

    def _update_prometheus_metrics(self, model_name: str, metrics: Dict[str, float]):
        """更新Prometheus指標"""
        try:
            # 預測計數
            self.prometheus_metrics["predictions_total"].labels(
                model_name=model_name, status="success"
            ).inc()

            # 延遲
            if "latency_ms" in metrics:
                self.prometheus_metrics["prediction_latency"].labels(
                    model_name=model_name
                ).observe(
                    metrics["latency_ms"] / 1000
                )  # 轉換為秒

            # 準確率
            if "accuracy" in metrics:
                self.prometheus_metrics["model_accuracy"].labels(
                    model_name=model_name
                ).set(metrics["accuracy"])

            # 錯誤率 (簡化計算)
            if "accuracy" in metrics:
                error_rate = 1 - metrics["accuracy"]
                self.prometheus_metrics["model_error_rate"].labels(
                    model_name=model_name
                ).set(error_rate)

        except Exception as e:
            self.logger.warning(f"Prometheus metrics update failed: {str(e)}")

    async def evaluate_model_performance(
        self, model_name: str, evaluation_window: Optional[int] = None
    ) -> Dict[str, Any]:
        """評估模型性能"""
        try:
            if evaluation_window is None:
                evaluation_window = self.config["evaluation_window"]

            history = self.performance_history.get(model_name, deque())
            if len(history) == 0:
                return {"error": "No performance data available"}

            # 獲取最近的數據
            recent_snapshots = list(history)[-evaluation_window:]

            # 聚合指標
            aggregated_metrics = self._aggregate_performance_metrics(recent_snapshots)

            # 性能趨勢分析
            trends = self._analyze_performance_trends(recent_snapshots)

            # 異常檢測
            anomalies = self._detect_performance_anomalies(recent_snapshots)

            return {
                "model_name": model_name,
                "evaluation_window": evaluation_window,
                "sample_count": len(recent_snapshots),
                "metrics": aggregated_metrics,
                "trends": trends,
                "anomalies": anomalies,
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Model performance evaluation failed: {str(e)}")
            return {"error": str(e)}

    def _aggregate_performance_metrics(
        self, snapshots: List[ModelPerformanceSnapshot]
    ) -> Dict[str, float]:
        """聚合性能指標"""
        if not snapshots:
            return {}

        # 收集所有指標
        all_metrics = defaultdict(list)
        for snapshot in snapshots:
            for metric, value in snapshot.metrics.items():
                if isinstance(value, (int, float)):
                    all_metrics[metric].append(value)

        # 計算統計量
        aggregated = {}
        for metric, values in all_metrics.items():
            if values:
                aggregated[f"{metric}_mean"] = np.mean(values)
                aggregated[f"{metric}_std"] = np.std(values)
                aggregated[f"{metric}_min"] = np.min(values)
                aggregated[f"{metric}_max"] = np.max(values)
                aggregated[f"{metric}_median"] = np.median(values)

        return aggregated

    def _analyze_performance_trends(
        self, snapshots: List[ModelPerformanceSnapshot]
    ) -> Dict[str, Any]:
        """分析性能趨勢"""
        if len(snapshots) < 10:
            return {"message": "Insufficient data for trend analysis"}

        trends = {}
        key_metrics = ["accuracy", "mae", "mse", "r2_score", "latency_ms"]

        for metric in key_metrics:
            values = []
            for snapshot in snapshots:
                if metric in snapshot.metrics:
                    values.append(snapshot.metrics[metric])

            if len(values) >= 5:
                # 計算趨勢 (簡單線性回歸斜率)
                x = np.arange(len(values))
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x, values
                )

                trends[metric] = {
                    "slope": slope,
                    "direction": (
                        "improving"
                        if slope > 0
                        else "degrading" if slope < 0 else "stable"
                    ),
                    "strength": abs(slope),
                    "significance": p_value < 0.05,
                }

        return trends

    def _detect_performance_anomalies(
        self, snapshots: List[ModelPerformanceSnapshot]
    ) -> List[Dict[str, Any]]:
        """檢測性能異常"""
        anomalies = []

        if len(snapshots) < 20:
            return anomalies

        # 使用Isolation Forest檢測異常
        features = []
        for snapshot in snapshots:
            feature_vector = [
                snapshot.metrics.get("accuracy", 0),
                snapshot.metrics.get("latency_ms", 0),
                snapshot.metrics.get("mae", 0),
                snapshot.metrics.get("r2_score", 0),
            ]
            features.append(feature_vector)

        if features:
            try:
                clf = IsolationForest(contamination=0.1, random_state=42)
                anomaly_labels = clf.fit_predict(features)

                for i, (snapshot, is_anomaly) in enumerate(
                    zip(snapshots, anomaly_labels)
                ):
                    if is_anomaly == -1:  # 異常點
                        anomalies.append(
                            {
                                "timestamp": snapshot.timestamp.isoformat(),
                                "metrics": snapshot.metrics,
                                "anomaly_score": clf.decision_function([features[i]])[
                                    0
                                ],
                            }
                        )

            except Exception as e:
                self.logger.warning(f"Anomaly detection failed: {str(e)}")

        return anomalies


class AlertManager:
    """警報管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.alert_manager")
        self.config = config or self._default_config()

        # 警報存儲
        self.alerts: deque = deque(maxlen=10000)
        self.active_alerts: Dict[str, Alert] = {}

        # 通知渠道
        self.notification_channels: Dict[str, Callable] = {}

        # 警報規則
        self.alert_rules: Dict[str, Dict[str, Any]] = {}

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "alert_retention_days": 30,
            "max_alerts_per_hour": 100,
            "notification_cooldown_minutes": 15,
            "severity_thresholds": {
                "critical": 0.9,
                "high": 0.7,
                "medium": 0.5,
                "low": 0.3,
            },
        }

    def add_notification_channel(self, name: str, channel_func: Callable):
        """添加通知渠道"""
        self.notification_channels[name] = channel_func
        self.logger.info(f"Notification channel added: {name}")

    def create_alert_rule(
        self,
        rule_name: str,
        condition: Callable[[Dict[str, Any]], bool],
        severity: AlertSeverity,
        message_template: str,
    ):
        """創建警報規則"""
        self.alert_rules[rule_name] = {
            "condition": condition,
            "severity": severity,
            "message_template": message_template,
            "created_at": datetime.now(),
        }
        self.logger.info(f"Alert rule created: {rule_name}")

    async def evaluate_alert_conditions(
        self, metrics: Dict[str, Any], model_name: str = ""
    ):
        """評估警報條件"""
        try:
            for rule_name, rule in self.alert_rules.items():
                try:
                    if rule["condition"](metrics):
                        await self._trigger_alert(
                            rule_name=rule_name,
                            model_name=model_name,
                            severity=rule["severity"],
                            message=rule["message_template"].format(**metrics),
                            metrics=metrics,
                        )
                except Exception as e:
                    self.logger.error(
                        f"Alert rule evaluation failed for {rule_name}: {str(e)}"
                    )

        except Exception as e:
            self.logger.error(f"Alert condition evaluation failed: {str(e)}")

    async def _trigger_alert(
        self,
        rule_name: str,
        model_name: str,
        severity: AlertSeverity,
        message: str,
        metrics: Dict[str, Any],
    ):
        """觸發警報"""
        try:
            # 檢查冷卻期
            alert_key = f"{rule_name}_{model_name}"
            if alert_key in self.active_alerts:
                last_alert_time = self.active_alerts[alert_key].timestamp
                cooldown = timedelta(
                    minutes=self.config["notification_cooldown_minutes"]
                )
                if datetime.now() - last_alert_time < cooldown:
                    return  # 在冷卻期內

            # 創建警報
            alert = Alert(
                model_name=model_name,
                alert_type=rule_name,
                severity=severity,
                message=message,
                metrics=metrics,
            )

            # 存儲警報
            self.alerts.append(alert)
            self.active_alerts[alert_key] = alert

            # 發送通知
            await self._send_notifications(alert)

            self.logger.warning(
                f"Alert triggered: {rule_name} for {model_name} - {message}"
            )

        except Exception as e:
            self.logger.error(f"Alert triggering failed: {str(e)}")

    async def _send_notifications(self, alert: Alert):
        """發送通知"""
        try:
            notification_data = {
                "alert_id": alert.alert_id,
                "model_name": alert.model_name,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metrics": alert.metrics,
            }

            # 發送到所有通知渠道
            for channel_name, channel_func in self.notification_channels.items():
                try:
                    await channel_func(notification_data)
                except Exception as e:
                    self.logger.error(
                        f"Notification failed for {channel_name}: {str(e)}"
                    )

        except Exception as e:
            self.logger.error(f"Notification sending failed: {str(e)}")

    def resolve_alert(self, alert_id: str):
        """解決警報"""
        try:
            # 在活躍警報中查找並標記為已解決
            for key, alert in self.active_alerts.items():
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    self.logger.info(f"Alert resolved: {alert_id}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Alert resolution failed: {str(e)}")
            return False

    def get_active_alerts(
        self, severity_filter: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """獲取活躍警報"""
        active_alerts = [
            alert for alert in self.active_alerts.values() if not alert.resolved
        ]

        if severity_filter:
            active_alerts = [
                alert for alert in active_alerts if alert.severity == severity_filter
            ]

        return sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)


class MLMonitoringSystem:
    """ML監控系統主類"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.ml_monitoring")
        self.config = config or {}

        # 初始化組件
        self.drift_detector = DataDriftDetector(config.get("drift_detection", {}))
        self.performance_monitor = ModelPerformanceMonitor(
            config.get("performance_monitoring", {})
        )
        self.alert_manager = AlertManager(config.get("alert_management", {}))

        # 監控狀態
        self.monitoring_active = False
        self.monitored_models: Dict[str, Dict[str, Any]] = {}

        # 數據存儲
        self.storage_dir = Path(self.config.get("storage_dir", "ml_monitoring_data"))
        self.storage_dir.mkdir(exist_ok=True)

        # 設置默認警報規則
        self._setup_default_alert_rules()

    def _setup_default_alert_rules(self):
        """設置默認警報規則"""
        # 性能下降警報
        self.alert_manager.create_alert_rule(
            rule_name="accuracy_drop",
            condition=lambda metrics: metrics.get("accuracy", 1.0) < 0.8,
            severity=AlertSeverity.HIGH,
            message="Model accuracy dropped to {accuracy:.2%}",
        )

        # 延遲警報
        self.alert_manager.create_alert_rule(
            rule_name="high_latency",
            condition=lambda metrics: metrics.get("latency_ms", 0) > 1000,
            severity=AlertSeverity.MEDIUM,
            message="Model latency is {latency_ms:.0f}ms",
        )

        # 漂移警報
        self.alert_manager.create_alert_rule(
            rule_name="drift_detected",
            condition=lambda metrics: metrics.get("drift_score", 0) > 0.1,
            severity=AlertSeverity.HIGH,
            message="Data drift detected with score {drift_score:.3f}",
        )

    async def start_monitoring(self):
        """啟動監控"""
        try:
            self.monitoring_active = True

            # 啟動Prometheus HTTP服務器 (如果可用)
            if PROMETHEUS_AVAILABLE:
                start_http_server(8000)
                self.logger.info("Prometheus metrics server started on port 8000")

            # 啟動監控任務
            monitoring_tasks = [
                asyncio.create_task(self._performance_monitoring_loop()),
                asyncio.create_task(self._drift_monitoring_loop()),
                asyncio.create_task(self._alert_monitoring_loop()),
            ]

            self.logger.info("ML monitoring system started")

            # 等待所有任務完成
            await asyncio.gather(*monitoring_tasks)

        except Exception as e:
            self.logger.error(f"Monitoring system startup failed: {str(e)}")
            self.monitoring_active = False

    async def stop_monitoring(self):
        """停止監控"""
        self.monitoring_active = False
        self.logger.info("ML monitoring system stopped")

    def add_model_monitoring(
        self,
        model_name: str,
        reference_data: Optional[pd.DataFrame] = None,
        monitoring_config: Optional[Dict[str, Any]] = None,
    ):
        """添加模型監控"""
        try:
            model_config = {
                "model_name": model_name,
                "monitoring_config": monitoring_config or {},
                "reference_data": reference_data,
                "added_at": datetime.now(),
            }

            self.monitored_models[model_name] = model_config

            # 設置參考數據用於漂移檢測
            if reference_data is not None:
                for column in reference_data.select_dtypes(include=[np.number]).columns:
                    self.drift_detector.set_reference_data(
                        column, reference_data[column]
                    )

            self.logger.info(f"Model monitoring added: {model_name}")

        except Exception as e:
            self.logger.error(f"Failed to add model monitoring: {str(e)}")

    async def _performance_monitoring_loop(self):
        """性能監控循環"""
        while self.monitoring_active:
            try:
                for model_name, model_config in self.monitored_models.items():
                    # 評估模型性能
                    performance = (
                        await self.performance_monitor.evaluate_model_performance(
                            model_name
                        )
                    )

                    # 檢查警報條件
                    await self.alert_manager.evaluate_alert_conditions(
                        performance.get("metrics", {}), model_name
                    )

                # 每5分鐘檢查一次
                await asyncio.sleep(300)

            except Exception as e:
                self.logger.error(f"Performance monitoring loop error: {str(e)}")
                await asyncio.sleep(60)  # 出錯後等待1分鐘

    async def _drift_monitoring_loop(self):
        """漂移監控循環"""
        while self.monitoring_active:
            try:
                for model_name, model_config in self.monitored_models.items():
                    # 獲取當前數據 (這裡需要從數據源獲取)
                    # current_data = await self._get_current_data(model_name)
                    # drift_results = await self._check_data_drift(current_data)

                    pass  # 佔位符實現

                # 每30分鐘檢查一次漂移
                await asyncio.sleep(1800)

            except Exception as e:
                self.logger.error(f"Drift monitoring loop error: {str(e)}")
                await asyncio.sleep(300)

    async def _alert_monitoring_loop(self):
        """警報監控循環"""
        while self.monitoring_active:
            try:
                # 清理過期的警報
                await self._cleanup_expired_alerts()

                # 每10分鐘檢查一次
                await asyncio.sleep(600)

            except Exception as e:
                self.logger.error(f"Alert monitoring loop error: {str(e)}")
                await asyncio.sleep(120)

    async def _cleanup_expired_alerts(self):
        """清理過期警報"""
        try:
            retention_days = self.alert_manager.config.get("alert_retention_days", 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            # 清理活躍警報中的過期警報
            expired_keys = []
            for key, alert in self.alert_manager.active_alerts.items():
                if alert.timestamp < cutoff_date:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.alert_manager.active_alerts[key]

        except Exception as e:
            self.logger.error(f"Alert cleanup failed: {str(e)}")

    def generate_monitoring_report(
        self, model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成監控報告"""
        try:
            report = {
                "generated_at": datetime.now().isoformat(),
                "system_status": "active" if self.monitoring_active else "inactive",
                "monitored_models": list(self.monitored_models.keys()),
            }

            if model_name and model_name in self.monitored_models:
                # 特定模型的報告
                performance = asyncio.run(
                    self.performance_monitor.evaluate_model_performance(model_name)
                )
                report["model_performance"] = performance

                # 活躍警報
                model_alerts = self.alert_manager.get_active_alerts()
                model_alerts = [
                    alert for alert in model_alerts if alert.model_name == model_name
                ]
                report["active_alerts"] = [
                    {
                        "alert_id": alert.alert_id,
                        "type": alert.alert_type,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                    }
                    for alert in model_alerts
                ]

            else:
                # 所有模型的摘要報告
                all_active_alerts = self.alert_manager.get_active_alerts()
                report["total_active_alerts"] = len(all_active_alerts)
                report["alerts_by_severity"] = {}
                for alert in all_active_alerts:
                    severity = alert.severity.value
                    report["alerts_by_severity"][severity] = (
                        report["alerts_by_severity"].get(severity, 0) + 1
                    )

            return report

        except Exception as e:
            self.logger.error(f"Monitoring report generation failed: {str(e)}")
            return {"error": str(e)}


# 全局監控系統實例
ml_monitoring_system = MLMonitoringSystem()
