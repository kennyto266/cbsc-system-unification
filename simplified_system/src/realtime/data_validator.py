#!/usr/bin/env python3
"""
多源數據驗證系統 - Multi-Source Data Validation System
驗證和對賬來自不同數據源的實時市場數據
Validate and reconcile real-time market data from multiple sources
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
import hashlib
import aioredis
from collections import defaultdict, deque
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSourceType(Enum):
    """數據源類型"""
    PRIMARY = "primary"        # 主要數據源 (最可靠)
    SECONDARY = "secondary"    # 次要數據源
    BACKUP = "backup"          # 備用數據源
    REFERENCE = "reference"    # 參考數據源

class ValidationLevel(Enum):
    """驗證級別"""
    STRICT = "strict"          # 嚴格模式，任何差異都報警
    MODERATE = "moderate"      # 適中模式，重大差異報警
    LOOSE = "loose"            # 寬鬆模式，只報告嚴重問題

@dataclass
class DataPoint:
    """數據點"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    source: str
    source_type: DataSourceType
    confidence: float = 1.0
    checksum: str = ""

    def __post_init__(self):
        """生成數據點校驗和"""
        content = f"{self.symbol}{self.timestamp.isoformat()}{self.price}{self.volume}"
        self.checksum = hashlib.md5(content.encode()).hexdigest()[:8]

@dataclass
class ValidationResult:
    """驗證結果"""
    symbol: str
    timestamp: datetime
    validation_level: ValidationLevel
    sources: List[str]
    consensus_price: Optional[float] = None
    price_variance: float = 0.0
    max_price_diff: float = 0.0
    validation_passed: bool = True
    warnings: List[str] = None
    errors: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

class DataQualityMetrics:
    """數據質量指標"""

    def __init__(self):
        self.metrics = {
            "total_validations": 0,
            "failed_validations": 0,
            "warning_count": 0,
            "error_count": 0,
            "avg_price_variance": 0.0,
            "max_price_variance": 0.0,
            "source_reliability": {},
            "consensus_success_rate": 0.0,
            "validation_time_ms": 0.0,
            "data_staleness_seconds": 0.0,
            "last_update": datetime.now()
        }

class SourceReliabilityTracker:
    """數據源可靠性跟蹤器"""

    def __init__(self):
        self.source_stats = defaultdict(lambda: {
            "success_count": 0,
            "error_count": 0,
            "total_latency": 0.0,
            "success_rate": 0.0,
            "avg_latency_ms": 0.0,
            "last_success": None,
            "consecutive_failures": 0,
            "reliability_score": 1.0
        })

    def record_success(self, source: str, latency: float):
        """記錄成功提交"""
        stats = self.source_stats[source]
        stats["success_count"] += 1
        stats["total_latency"] += latency
        stats["last_success"] = datetime.now()
        stats["consecutive_failures"] = max(0, stats["consecutive_failures"] - 1)

        # 更新統計指標
        total = stats["success_count"] + stats["error_count"]
        if total > 0:
            stats["success_rate"] = stats["success_count"] / total
            stats["avg_latency_ms"] = (stats["total_latency"] / stats["success_count"]) * 1000

        # 更新可靠性評分 (基於成功率和延遲)
        reliability = stats["success_rate"]
        if stats["avg_latency_ms"] > 100:  # 延遲超過100ms影響評分
            reliability *= 0.8
        stats["reliability_score"] = reliability

    def record_error(self, source: str):
        """記錄錯誤"""
        stats = self.source_stats[source]
        stats["error_count"] += 1
        stats["consecutive_failures"] += 1

        # 更新統計指標
        total = stats["success_count"] + stats["error_count"]
        if total > 0:
            stats["success_rate"] = stats["success_count"] / total

        # 連續失敗會嚴重影響可靠性
        if stats["consecutive_failures"] > 5:
            stats["reliability_score"] *= 0.5
        elif stats["consecutive_failures"] > 10:
            stats["reliability_score"] *= 0.1

    def get_most_reliable_source(self, sources: List[str]) -> Optional[str]:
        """獲取最可靠的數據源"""
        if not sources:
            return None

        available_sources = [s for s in sources if s in self.source_stats]
        if not available_sources:
            return sources[0]  # 如果沒有統計數據，返回第一個

        # 基於可靠性和連續失敗選擇
        best_source = None
        best_score = -1

        for source in available_sources:
            stats = self.source_stats[source]
            score = stats["reliability_score"]

            # 嚴懲罰連續失敗的源
            if stats["consecutive_failures"] > 3:
                score *= 0.1

            if score > best_score:
                best_score = score
                best_source = source

        return best_source

    def get_source_stats(self) -> Dict[str, Any]:
        """獲取數據源統計"""
        return {source: dict(stats) for source, stats in self.source_stats.items()}

class ConsensusEngine:
    """共識引擎 - 計算數據共識"""

    def __init__(self, reliability_tracker: SourceReliabilityTracker):
        self.reliability_tracker = reliability_tracker

    def calculate_consensus_price(self, data_points: List[DataPoint]) -> Tuple[float, float]:
        """計算共識價格和信心度"""
        if not data_points:
            return 0.0, 0.0

        # 加權平均，權重基於源可靠性
        weighted_sum = 0.0
        total_weight = 0.0

        for dp in data_points:
            reliability = self.reliability_tracker.source_stats[dp.source]["reliability_score"]
            weight = reliability * dp.confidence
            weighted_sum += dp.price * weight
            total_weight += weight

        if total_weight == 0:
            # 退化為簡單平均
            prices = [dp.price for dp in data_points]
            consensus_price = statistics.mean(prices)
            confidence = 0.5
        else:
            consensus_price = weighted_sum / total_weight
            confidence = min(total_weight / len(data_points), 1.0)

        return consensus_price, confidence

    def detect_outliers(self, data_points: List[DataPoint], consensus_price: float) -> List[DataPoint]:
        """檢測異常值"""
        outliers = []
        prices = [dp.price for dp in data_points]

        if len(prices) < 3:
            return outliers

        # 使用IQR方法檢測異常值
        prices_array = np.array(prices)
        q1, q3 = np.percentile(prices_array, [25, 75])
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        for dp in data_points:
            if dp.price < lower_bound or dp.price > upper_bound:
                # 進一步檢查與共識價格的偏差
                deviation = abs(dp.price - consensus_price) / consensus_price
                if deviation > 0.05:  # 偏差超過5%
                    outliers.append(dp)

        return outliers

class MultiSourceDataValidator:
    """多源數據驗證器"""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.validation_level = validation_level
        self.reliability_tracker = SourceReliabilityTracker()
        self.consensus_engine = ConsensusEngine(self.reliability_tracker)
        self.quality_metrics = DataQualityMetrics()

        # 數據收集窗口
        self.data_window = defaultdict(lambda: deque(maxlen=100))
        self.validation_history = deque(maxlen=1000)

        # 配置參數
        self.config = {
            "min_sources_for_validation": 2,
            "price_variance_threshold": 0.001,  # 0.1%
            "max_price_diff_threshold": 0.005,   # 0.5%
            "stale_data_threshold_seconds": 60,
            "outlier_detection_enabled": True,
            "consensus_threshold": 0.6  # 60%以上源達成共識
        }

    def add_data_point(self, data_point: DataPoint) -> Optional[ValidationResult]:
        """添加數據點並進行驗證"""
        start_time = time.perf_counter()

        try:
            # 記錄源性能
            self.reliability_tracker.record_success(data_point.source, 0.0)

            # 添加到數據窗口
            self.data_window[data_point.symbol].append(data_point)

            # 執行驗證
            validation_result = self._validate_data_point(data_point)

            # 更新質量指標
            self._update_quality_metrics(validation_result, start_time)

            # 記錄驗證歷史
            self.validation_history.append(validation_result)

            return validation_result

        except Exception as e:
            logger.error(f"Error validating data point: {e}")
            self.reliability_tracker.record_error(data_point.source)
            return None

    def _validate_data_point(self, data_point: DataPoint) -> ValidationResult:
        """驗證單個數據點"""
        symbol = data_point.symbol
        current_time = datetime.now()

        # 獲取同時間窗口內的其他數據點
        recent_data = self._get_recent_data_points(
            symbol, current_time, window_seconds=30
        )

        if len(recent_data) < self.config["min_sources_for_validation"] - 1:
            # 數據源不足，無法進行全面驗證
            return ValidationResult(
                symbol=symbol,
                timestamp=current_time,
                validation_level=self.validation_level,
                sources=[data_point.source],
                consensus_price=data_point.price,
                validation_passed=True,
                warnings=["Insufficient data sources for validation"],
                metadata={"data_sources_count": len(recent_data)}
            )

        # 計算共識價格
        consensus_price, consensus_confidence = self.consensus_engine.calculate_consensus_price(
            recent_data + [data_point]
        )

        # 檢測異常值
        outliers = []
        if self.config["outlier_detection_enabled"]:
            outliers = self.consensus_engine.detect_outliers(
                recent_data + [data_point], consensus_price
            )

        # 計算價格方差
        all_prices = [dp.price for dp in recent_data + [data_point]]
        price_variance = np.var(all_prices) if len(all_prices) > 1 else 0

        # 計算最大價格差異
        price_diffs = [abs(dp.price - consensus_price) / consensus_price for dp in all_prices]
        max_price_diff = max(price_diffs) if price_diffs else 0

        # 執行驗證規則
        warnings = []
        errors = []
        validation_passed = True

        # 檢查價格方差
        if price_variance > self.config["price_variance_threshold"]:
            if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.MODERATE]:
                warnings.append(f"High price variance: {price_variance:.4f}")
            elif self.validation_level == ValidationLevel.STRICT:
                validation_passed = False

        # 檢查最大價格差異
        if max_price_diff > self.config["max_price_diff_threshold"]:
            if self.validation_level == ValidationLevel.STRICT:
                errors.append(f"Price difference too large: {max_price_diff:.3f}")
                validation_passed = False
            else:
                warnings.append(f"Large price difference: {max_price_diff:.3f}")

        # 檢查數據新鮮度
        data_staleness = (current_time - data_point.timestamp).total_seconds()
        if data_staleness > self.config["stale_data_threshold_seconds"]:
            if self.validation_level == ValidationLevel.STRICT:
                errors.append(f"Stale data: {data_staleness} seconds old")
                validation_passed = False
            else:
                warnings.append(f"Potentially stale data: {data_staleness} seconds old")

        # 檢查異常值
        if outliers:
            outlier_sources = [dp.source for dp in outliers]
            if data_point in outliers:
                if self.validation_level == ValidationLevel.STRICT:
                    errors.append(f"Detected as outlier among sources: {outlier_sources}")
                    validation_passed = False
                else:
                    warnings.append(f"Potential outlier (sources: {outlier_sources})")

        return ValidationResult(
            symbol=symbol,
            timestamp=current_time,
            validation_level=self.validation_level,
            sources=[dp.source for dp in recent_data + [data_point]],
            consensus_price=consensus_price,
            price_variance=price_variance,
            max_price_diff=max_price_diff,
            validation_passed=validation_passed,
            warnings=warnings,
            errors=errors,
            metadata={
                "consensus_confidence": consensus_confidence,
                "data_staleness_seconds": data_staleness,
                "outliers_detected": len(outliers),
                "total_data_points": len(recent_data) + 1,
                "current_source_type": data_point.source_type.value
            }
        )

    def _get_recent_data_points(self, symbol: str, current_time: datetime, window_seconds: int) -> List[DataPoint]:
        """獲取指定時間窗口內的數據點"""
        if symbol not in self.data_window:
            return []

        recent_data = []
        cutoff_time = current_time - timedelta(seconds=window_seconds)

        for dp in self.data_window[symbol]:
            if dp.timestamp >= cutoff_time:
                recent_data.append(dp)

        return recent_data

    def _update_quality_metrics(self, validation_result: ValidationResult, start_time: float):
        """更新質量指標"""
        processing_time = (time.perf_counter() - start_time) * 1000

        self.quality_metrics["total_validations"] += 1
        self.quality_metrics["validation_time_ms"] = processing_time
        self.quality_metrics["last_update"] = datetime.now()

        if not validation_result.validation_passed:
            self.quality_metrics["failed_validations"] += 1

        self.quality_metrics["warning_count"] += len(validation_result.warnings)
        self.quality_metrics["error_count"] += len(validation_result.errors)

        # 更新平均價格方差
        if self.quality_metrics["total_validations"] == 1:
            self.quality_metrics["avg_price_variance"] = validation_result.price_variance
        else:
            total = self.quality_metrics["total_validations"]
            current_avg = self.quality_metrics["avg_price_variance"]
            self.quality_metrics["avg_price_variance"] = (current_avg * (total - 1) + validation_result.price_variance) / total

        # 更新最大價格方差
        self.quality_metrics["max_price_variance"] = max(
            self.quality_metrics["max_price_variance"],
            validation_result.price_variance
        )

    def get_quality_report(self) -> Dict[str, Any]:
        """獲取質量報告"""
        recent_validations = list(self.validation_history)[-100:]

        success_rate = 0.0
        if recent_validations:
            successful = sum(1 for vr in recent_validations if vr.validation_passed)
            success_rate = successful / len(recent_validations)

        return {
            "overall_metrics": self.quality_metrics.metrics,
            "success_rate": success_rate,
            "source_reliability": self.reliability_tracker.get_source_stats(),
            "recent_validations_count": len(recent_validations),
            "validation_level": self.validation_level.value,
            "configuration": self.config
        }

    def get_source_recommendations(self, symbol: str = None) -> Dict[str, Any]:
        """獲取數據源推薦"""
        recommendations = {
            "most_reliable": [],
            "avoid_sources": [],
            "improve_sources": []
        }

        source_stats = self.reliability_tracker.get_source_stats()

        # 找出最可靠的源
        reliable_sources = []
        for source, stats in source_stats.items():
            if stats["reliability_score"] > 0.8 and stats["consecutive_failures"] == 0:
                reliable_sources.append((source, stats["reliability_score"]))

        # 按可靠性排序
        reliable_sources.sort(key=lambda x: x[1], reverse=True)
        recommendations["most_reliable"] = [source for source, _ in reliable_sources[:3]]

        # 找出需要避免的源
        for source, stats in source_stats.items():
            if stats["consecutive_failures"] > 5 or stats["reliability_score"] < 0.3:
                recommendations["avoid_sources"].append(source)
            elif stats["reliability_score"] < 0.6:
                recommendations["improve_sources"].append(source)

        return recommendations

# 使用示例
async def demo_data_validator():
    """演示數據驗證器"""
    validator = MultiSourceDataValidator(ValidationLevel.MODERATE)

    # 模擬來自多個數據源的數據
    sources = ["source_A", "source_B", "source_C", "source_D"]
    source_types = [DataSourceType.PRIMARY, DataSourceType.SECONDARY, DataSourceType.BACKUP, DataSourceType.REFERENCE]

    try:
        for i in range(50):
            symbol = "0700.HK"
            base_price = 300.0 + np.random.normal(0, 2)

            for j, (source, source_type) in enumerate(zip(sources, source_types)):
                # 添加一些隨機變化來模擬真實世界的數據差異
                price_variation = np.random.normal(0, 0.1) if source_type != DataSourceType.PRIMARY else np.random.normal(0, 0.05)
                price = base_price * (1 + price_variation)

                data_point = DataPoint(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=price,
                    volume=np.random.randint(1000, 50000),
                    source=source,
                    source_type=source_type,
                    confidence=0.9 if source_type == DataSourceType.PRIMARY else 0.7
                )

                result = validator.add_data_point(data_point)
                if result and not result.validation_passed:
                    print(f"Validation failed for {source}: {result.errors}")

            await asyncio.sleep(0.1)  # 100ms間隔

        # 生成質量報告
        report = validator.get_quality_report()
        print(f"Data Quality Report:")
        print(json.dumps(report, indent=2, default=str))

        # 生成源推薦
        recommendations = validator.get_source_recommendations()
        print(f"Source Recommendations:")
        print(json.dumps(recommendations, indent=2, default=str))

    finally:
        # 清理資源
        pass

if __name__ == "__main__":
    asyncio.run(demo_data_validator())