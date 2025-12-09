"""
港股量化交易 AI Agent 系统 - 异常检测模块

实现实时异常检测算法、异常模式识别和性能监控，用于辅助数据科学家Agent
识别市场异动、交易异常及数据质量问题。
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from statistics import mean
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from ...models.base import BaseDataModel


class AnomalyDetectionStrategy(str, Enum):
    """异常检测策略类型"""

    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"
    ONE_CLASS_SVM = "one_class_svm"


@dataclass
class AnomalyScore(BaseDataModel):
    """异常分数"""

    symbol: str
    score: float
    strategy: AnomalyDetectionStrategy
    threshold: float
    is_anomaly: bool
    features: Dict[str, float] = field(default_factory=dict)


@dataclass
class AnomalyDetectionResult(BaseDataModel):
    """异常检测结果"""

    symbol: str
    aggregate_score: float
    is_anomaly: bool
    strategy_scores: List[AnomalyScore]
    anomaly_type: str
    severity: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetectionConfig:
    """异常检测配置"""

    window_size: int = 500
    min_training_size: int = 200
    contamination: float = 0.02
    retrain_frequency: int = 300  # 新样本数量达到该阈值后触发重训
    strategies: Tuple[AnomalyDetectionStrategy, ...] = (
        AnomalyDetectionStrategy.ISOLATION_FOREST,
        AnomalyDetectionStrategy.LOCAL_OUTLIER_FACTOR,
        AnomalyDetectionStrategy.ONE_CLASS_SVM,
    )
    score_threshold: float = 0.7  # 综合异常分数阈值
    cooldown_period: timedelta = timedelta(minutes=10)


class AnomalyPatternRecognizer:
    """异常模式识别器，用于识别特定市场异常模式"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def detect_patterns(self, features: Dict[str, float]) -> Tuple[str, str]:
        """基于特征检测异常模式，返回(异常类型, 严重程度)"""

        try:
            price_change = features.get("return_1d", 0.0)
            volume_ratio = features.get("volume_ratio_5d", 1.0)
            volatility = features.get("volatility_5d", 0.0)
            price_gap = features.get("price_gap", 0.0)

            # 极端价格变动
            if abs(price_change) > 0.08 and volume_ratio > 2.0:
                severity = "high" if abs(price_change) > 0.12 else "medium"
                anomaly_type = (
                    "price_spike_up" if price_change > 0 else "price_spike_down"
                )
                return anomaly_type, severity

            # 卷量异常
            if volume_ratio > 3.0:
                severity = "medium" if volume_ratio < 5.0 else "high"
                return "volume_spike", severity

            # 波动率骤升
            if volatility > 0.06:
                severity = "medium" if volatility < 0.1 else "high"
                return "volatility_regime_change", severity

            # 跳空高 / 低开
            if abs(price_gap) > 0.04:
                severity = "medium"
                anomaly_type = "gap_up" if price_gap > 0 else "gap_down"
                return anomaly_type, severity

            # 未识别异常
            return "unknown_anomaly", "low"

        except Exception as exc:
            self.logger.error(f"异常模式识别失败: {exc}")
            return "unknown_anomaly", "low"


class AnomalyDetector:
    """异常检测核心类，实现多策略融合的实时异常检测"""

    def __init__(self, config: AnomalyDetectionConfig):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.anomaly_detector")
        self.scaler = StandardScaler()
        self.feature_buffer: Deque[Dict[str, float]] = deque(maxlen=config.window_size)
        self.detectors: Dict[AnomalyDetectionStrategy, Any] = {}
        self.last_retrain_time = datetime.utcnow()
        self.samples_since_retrain = 0
        self.pattern_recognizer = AnomalyPatternRecognizer(self.logger)

    def add_sample(self, feature_row: Dict[str, float]):
        """新增样本并维护滑动窗口"""

        self.feature_buffer.append(feature_row)
        self.samples_since_retrain += 1

    def _prepare_training_data(self) -> Optional[pd.DataFrame]:
        """准备训练数据"""
        if len(self.feature_buffer) < self.config.min_training_size:
            self.logger.debug("训练数据不足，无法训练异常检测模型")
            return None

        df = pd.DataFrame(self.feature_buffer)
        df = df.replace([np.inf, -np.inf], np.nan).dropna()

        if df.empty:
            self.logger.warning("清洗后训练数据为空，无法训练")
            return None

        return df

    def train_if_needed(self):
        """按需训练或重训练模型"""
        if (
            not self.detectors
            or self.samples_since_retrain >= self.config.retrain_frequency
        ):
            training_df = self._prepare_training_data()
            if training_df is None:
                return

            scaled_data = self.scaler.fit_transform(training_df.values)

            self.detectors = {}
            for strategy in self.config.strategies:
                try:
                    if strategy == AnomalyDetectionStrategy.ISOLATION_FOREST:
                        model = IsolationForest(
                            n_estimators=200,
                            contamination=self.config.contamination,
                            random_state=42,
                        )
                        model.fit(scaled_data)
                    elif strategy == AnomalyDetectionStrategy.LOCAL_OUTLIER_FACTOR:
                        model = LocalOutlierFactor(
                            n_neighbors=20,
                            contamination=self.config.contamination,
                            novelty=True,
                        )
                        model.fit(scaled_data)
                    elif strategy == AnomalyDetectionStrategy.ONE_CLASS_SVM:
                        model = OneClassSVM(
                            kernel="rbf",
                            gamma="scale",
                            nu=self.config.contamination,
                        )
                        model.fit(scaled_data)
                    else:
                        continue

                    self.detectors[strategy] = model
                    self.logger.info(f"训练异常检测模型完成: {strategy.value}")
                except Exception as exc:
                    self.logger.error(f"训练模型失败: {strategy.value}, 错误: {exc}")

            self.samples_since_retrain = 0
            self.last_retrain_time = datetime.utcnow()

    def detect_anomaly(
        self, symbol: str, feature_row: Dict[str, float]
    ) -> Optional[AnomalyDetectionResult]:
        """检测单个样本是否异常"""

        if not self.detectors:
            self.logger.debug("模型尚未训练，无法检测异常")
            return None

        features_df = pd.DataFrame([feature_row])
        features_df = (
            features_df.replace([np.inf, -np.inf], np.nan)
            .fillna(method="ffill")
            .fillna(method="bfill")
        )

        if features_df.isnull().any().any():
            self.logger.warning("特征缺失值仍存在，跳过异常检测")
            return None

        scaled_features = self.scaler.transform(features_df)
        strategy_scores: List[AnomalyScore] = []

        aggregated_score = 0.0
        num_strategies = 0

        for strategy, model in self.detectors.items():
            try:
                if strategy == AnomalyDetectionStrategy.LOCAL_OUTLIER_FACTOR:
                    # LOF 的 decision_function 越小越异常
                    score = -float(model.decision_function(scaled_features)[0])
                else:
                    # IsolationForest 和 OneClassSVM decision_function 越小越异常
                    score = -float(model.decision_function(scaled_features)[0])

                threshold = self._estimate_threshold(strategy)
                is_anomaly = score >= threshold
                aggregated_score += min(score / max(threshold, 1e-6), 1.5)
                num_strategies += 1

                strategy_scores.append(
                    AnomalyScore(
                        id=f"score-{strategy.value}-{datetime.utcnow().timestamp()}",
                        symbol=symbol,
                        strategy=strategy,
                        score=score,
                        threshold=threshold,
                        is_anomaly=is_anomaly,
                        timestamp=datetime.utcnow(),
                        features=feature_row,
                    )
                )
            except Exception as exc:
                self.logger.error(f"异常评分失败: {strategy.value}, 错误: {exc}")

        if num_strategies == 0:
            return None

        aggregated_score /= num_strategies
        is_anomaly = aggregated_score >= self.config.score_threshold

        anomaly_type, severity = self.pattern_recognizer.detect_patterns(feature_row)

        result = AnomalyDetectionResult(
            id=f"anomaly-{symbol}-{datetime.utcnow().timestamp()}",
            symbol=symbol,
            aggregate_score=aggregated_score,
            is_anomaly=is_anomaly,
            strategy_scores=strategy_scores,
            anomaly_type=anomaly_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            metadata={
                "window_size": len(self.feature_buffer),
                "strategies": [s.value for s in self.detectors.keys()],
            },
        )

        return result

    def _estimate_threshold(self, strategy: AnomalyDetectionStrategy) -> float:
        """估算各策略的异常阈值"""

        # 根据策略类型设定经验阈值，可进一步动态自适应
        if strategy == AnomalyDetectionStrategy.ISOLATION_FOREST:
            return 0.6
        if strategy == AnomalyDetectionStrategy.LOCAL_OUTLIER_FACTOR:
            return 1.2
        if strategy == AnomalyDetectionStrategy.ONE_CLASS_SVM:
            return 0.8
        return 1.0


class RealTimeAnomalyMonitor:
    """实时异常监控器，负责缓存异常结果并提供统计"""

    def __init__(self, cooldown: timedelta):
        self.logger = logging.getLogger("hk_quant_system.anomaly_monitor")
        self.cooldown = cooldown
        self.recent_anomalies: Dict[str, datetime] = {}
        self.anomaly_history: Deque[AnomalyDetectionResult] = deque(maxlen=1000)

    def should_alert(self, result: AnomalyDetectionResult) -> bool:
        """判断是否需要触发告警，避免短时间重复告警"""

        last_alert_time = self.recent_anomalies.get(result.symbol)
        now = datetime.utcnow()

        if last_alert_time and now - last_alert_time < self.cooldown:
            self.logger.debug(f"{result.symbol} 处于冷却期，跳过告警")
            return False

        if result.is_anomaly:
            self.recent_anomalies[result.symbol] = now
            self.anomaly_history.append(result)
            return True

        return False

    def get_statistics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """获取指定时间窗口内的异常统计"""

        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_results = [r for r in self.anomaly_history if r.timestamp >= cutoff]

        if not recent_results:
            return {
                "total_anomalies": 0,
                "symbols": [],
                "average_score": 0.0,
                "severity_distribution": {},
            }

        severity_counts: Dict[str, int] = {}
        for res in recent_results:
            severity_counts[res.severity] = severity_counts.get(res.severity, 0) + 1

        return {
            "total_anomalies": len(recent_results),
            "symbols": list({res.symbol for res in recent_results}),
            "average_score": mean(res.aggregate_score for res in recent_results),
            "severity_distribution": severity_counts,
        }


class AnomalyDetectionEngine:
    """异步异常检测引擎，负责协调数据接收、检测与告警"""

    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        self.config = config or AnomalyDetectionConfig()
        self.detector = AnomalyDetector(self.config)
        self.monitor = RealTimeAnomalyMonitor(self.config.cooldown_period)
        self.logger = logging.getLogger("hk_quant_system.anomaly_engine")
        self.lock = asyncio.Lock()

    async def process_feature_row(
        self, symbol: str, feature_row: Dict[str, float]
    ) -> Optional[AnomalyDetectionResult]:
        """处理单条特征记录，支持异步调用"""

        async with self.lock:
            self.detector.add_sample(feature_row)
            self.detector.train_if_needed()
            result = self.detector.detect_anomaly(symbol, feature_row)

        if result and self.monitor.should_alert(result):
            self.logger.warning(
                "检测到异常: %s, score=%.3f, type=%s, severity=%s",
                result.symbol,
                result.aggregate_score,
                result.anomaly_type,
                result.severity,
            )
            return result

        return result

    async def process_batch(
        self, symbol: str, feature_rows: List[Dict[str, float]]
    ) -> List[AnomalyDetectionResult]:
        """批量处理特征记录"""

        results: List[AnomalyDetectionResult] = []
        for row in feature_rows:
            res = await self.process_feature_row(symbol, row)
            if res:
                results.append(res)
        return results

    def get_monitor_statistics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """获取异常监控统计"""
        return self.monitor.get_statistics(window_minutes)


__all__ = [
    "AnomalyDetectionConfig",
    "AnomalyDetectionEngine",
    "AnomalyDetectionResult",
    "AnomalyDetectionStrategy",
    "AnomalyPatternRecognizer",
    "AnomalyScore",
    "RealTimeAnomalyMonitor",
]
