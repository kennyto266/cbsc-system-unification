#!/usr / bin / env python3
"""
Cross - Source Validator - Task 16 & 18
跨源验证器 - 任务16和18

Cross - source validation for multi - source comparison and integration with existing cross_source_verification system
多源比较验证，与现有cross_source_verification系统集成

This module implements:
- Task 16: Cross - Source Validator for multi - source comparison
- Task 18: Integration with existing cross_source_verification system
- Multi - source price comparison within tolerance thresholds
- Reliability scoring system for data sources
- Conflict resolution strategies (weighted average, majority vote)
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .content_validation_layer import (
    AnomalyDetection,
    AnomalyType,
    ValidationResult,
    ValidationSeverity,
)
from .interfaces.auth_result import AuthResult, Verdict

# Import authentication interfaces
from .interfaces.verifier_interface import IVerifier

# Import existing cross - source verification system
try:
    from src.data.cross_source_verification import (
        CrossSourceVerifier,
        DataSource,
        DataSourcePriority,
        VerificationConfig,
        VerificationLevel,
    )

    CROSS_SOURCE_AVAILABLE = True
except ImportError:
    logger.warning(
        "Cross - source verification system not available, using fallback implementation"
    )
    CROSS_SOURCE_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(str, Enum):
    """冲突解决策略"""

    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    PRIORITY_OVERRIDE = "priority_override"
    MEDIAN = "median"
    TRIMMED_MEAN = "trimmed_mean"


class DataSourceReliability(str, Enum):
    """数据源可靠性等级"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class SourceComparisonResult:
    """数据源比较结果"""

    source1_name: str
    source2_name: str
    field_name: str
    similarity_score: float  # 0.0 - 1.0
    differences_detected: int
    total_comparisons: int
    confidence: float
    tolerance_threshold: float
    resolution_strategy: ConflictResolutionStrategy
    resolved_value: Optional[Any] = None
    conflicts: List[Dict[str, Any]] = field(default_factory = list)


@dataclass
class DataSourceMetadata:
    """数据源元数据"""

    name: str
    reliability_score: float  # 0.0 - 1.0
    priority: int  # 1 = high, 2 = medium, 3 = low
    last_updated: Optional[datetime] = None
    data_quality_score: Optional[float] = None
    historical_accuracy: Optional[float] = None
    response_time_ms: Optional[float] = None
    update_frequency: Optional[str] = None
    coverage: Optional[Dict[str, Any]] = None


class CrossSourceValidator(IVerifier):
    """跨源验证器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("CrossSourceValidator", config)
        self.supported_data_types = ["stock_data", "government_data", "economic_data"]

        # 配置参数
        self.default_tolerance = self.config.get("default_tolerance", 0.01)  # 1%
        self.conflict_resolution_strategy = ConflictResolutionStrategy(
            self.config.get("conflict_resolution_strategy", "weighted_average")
        )
        self.min_sources_for_comparison = self.config.get(
            "min_sources_for_comparison", 2
        )
        self.max_sources_for_comparison = self.config.get(
            "max_sources_for_comparison", 10
        )

        # 数据源可靠性评分
        self.source_reliability = self._initialize_source_reliability()

        # 初始化现有系统（如果可用）
        if CROSS_SOURCE_AVAILABLE:
            self.legacy_verifier = CrossSourceVerifier(
                VerificationConfig(
                    verification_level = VerificationLevel.MODERATE,
                    tolerance_percentage = self.default_tolerance,
                    consensus_method = self.conflict_resolution_strategy.value,
                )
            )
        else:
            self.legacy_verifier = None

    def get_verifier_type(self) -> str:
        return "cross_source"

    def get_supported_data_types(self) -> List[str]:
        return self.supported_data_types

    async def verify(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """执行跨源验证"""
        start_time = time.time()

        try:
            # 解析多源数据
            sources_data = self._parse_multi_source_data(data, context)

            if len(sources_data) < self.min_sources_for_comparison:
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
                        "message": f"Insufficient data sources for comparison. Minimum {self.min_sources_for_comparison} required.",
                        "sources_provided": len(sources_data),
                    },
                )

            # 限制数据源数量
            sources_data = sources_data[: self.max_sources_for_comparison]

            # 执行跨源比较
            comparison_results = await self._perform_cross_source_comparison(
                sources_data, context
            )

            # 如果存在现有系统，使用它进行验证
            if self.legacy_verifier:
                legacy_results = await self._integrate_with_legacy_system(
                    sources_data, context
                )
            else:
                legacy_results = None

            # 计算综合结果
            overall_similarity = np.mean(
                [r.similarity_score for r in comparison_results]
            )
            total_conflicts = sum(r.differences_detected for r in comparison_results)
            total_comparisons = sum(r.total_comparisons for r in comparison_results)

            # 确定最终结论
            if overall_similarity >= 0.9 and total_conflicts == 0:
                verdict = Verdict.AUTHENTIC
                confidence = overall_similarity
            elif (
                overall_similarity >= 0.7 and total_conflicts < total_comparisons * 0.05
            ):
                verdict = Verdict.SUSPICIOUS
                confidence = 0.6
            else:
                verdict = Verdict.FALSIFIED
                confidence = max(0.2, overall_similarity)

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
                    "sources_count": len(sources_data),
                    "comparison_results": [r.__dict__ for r in comparison_results],
                    "overall_similarity": overall_similarity,
                    "total_conflicts": total_conflicts,
                    "total_comparisons": total_comparisons,
                    "conflict_resolution_strategy": self.conflict_resolution_strategy.value,
                    "legacy_integration": legacy_results is not None,
                    "source_reliability_scores": {
                        s.name: s.reliability_score
                        for s in self._get_source_metadata(sources_data)
                    },
                },
            )

            logger.info(
                f"Cross - source validation completed for {data_id}: {verdict.value} "
                f"(confidence: {confidence:.3f}, sources: {len(sources_data)})"
            )
            return result

        except Exception as e:
            logger.error(f"Cross - source validation failed for {data_id}: {str(e)}")
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

    def _parse_multi_source_data(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, pd.DataFrame, DataSourceMetadata]]:
        """解析多源数据"""
        sources_data = []

        # 情况1: 数据本身就是多源格式
        if isinstance(data, dict) and "sources" in data:
            for source_info in data["sources"]:
                if "data" in source_info and "name" in source_info:
                    df = pd.DataFrame(source_info["data"])
                    metadata = self._extract_source_metadata(source_info)
                    sources_data.append((source_info["name"], df, metadata))

        # 情况2: 数据是列表格式，每个元素是一个数据源
        elif isinstance(data, list):
            for source_item in data:
                if (
                    isinstance(source_item, dict)
                    and "data" in source_item
                    and "name" in source_item
                ):
                    df = pd.DataFrame(source_item["data"])
                    metadata = self._extract_source_metadata(source_item)
                    sources_data.append((source_item["name"], df, metadata))

        # 情况3: context中包含多源信息
        elif context and "data_sources" in context:
            for source_info in context["data_sources"]:
                if "data" in source_info and "name" in source_info:
                    df = pd.DataFrame(source_info["data"])
                    metadata = self._extract_source_metadata(source_info)
                    sources_data.append((source_info["name"], df, metadata))

        # 情况4: 单一数据源，但需要与历史数据比较
        elif isinstance(data, dict) and "data" in data:
            df = pd.DataFrame(data["data"])
            source_name = data.get(
                "source",
                context.get("data_source", "unknown") if context else "unknown",
            )
            metadata = self._extract_source_metadata(data)
            sources_data.append((source_name, df, metadata))

        return sources_data

    def _extract_source_metadata(
        self, source_info: Dict[str, Any]
    ) -> DataSourceMetadata:
        """提取数据源元数据"""
        name = source_info.get("name", "unknown")

        # 获取预定义的可靠性评分
        predefined_reliability = self.source_reliability.get(name, 0.5)

        metadata = DataSourceMetadata(
            name = name,
            reliability_score = source_info.get(
                "reliability_score", predefined_reliability
            ),
            priority = source_info.get("priority", 2),  # 默认中等优先级
            last_updated=(
                pd.to_datetime(source_info["last_updated"])
                if "last_updated" in source_info
                else None
            ),
            data_quality_score = source_info.get("data_quality_score"),
            historical_accuracy = source_info.get("historical_accuracy"),
            response_time_ms = source_info.get("response_time_ms"),
            update_frequency = source_info.get("update_frequency"),
            coverage = source_info.get("coverage"),
        )

        return metadata

    async def _perform_cross_source_comparison(
        self,
        sources_data: List[Tuple[str, pd.DataFrame, DataSourceMetadata]],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[SourceComparisonResult]:
        """执行跨源比较"""
        results = []

        # 两两比较所有数据源
        for i in range(len(sources_data)):
            for j in range(i + 1, len(sources_data)):
                source1_name, df1, metadata1 = sources_data[i]
                source2_name, df2, metadata2 = sources_data[j]

                comparison_result = await self._compare_two_sources(
                    source1_name, df1, metadata1, source2_name, df2, metadata2, context
                )
                results.append(comparison_result)

        return results

    async def _compare_two_sources(
        self,
        name1: str,
        df1: pd.DataFrame,
        metadata1: DataSourceMetadata,
        name2: str,
        df2: pd.DataFrame,
        metadata2: DataSourceMetadata,
        context: Optional[Dict[str, Any]] = None,
    ) -> SourceComparisonResult:
        """比较两个数据源"""
        start_time = time.time()

        try:
            # 获取共同的列
            common_columns = set(df1.columns) & set(df2.columns)
            common_columns.discard("timestamp")
            common_columns.discard("date")

            if not common_columns:
                return SourceComparisonResult(
                    source1_name = name1,
                    source2_name = name2,
                    field_name="all",
                    similarity_score = 0.0,
                    differences_detected = 0,
                    total_comparisons = 0,
                    confidence = 0.0,
                    tolerance_threshold = self.default_tolerance,
                    resolution_strategy = self.conflict_resolution_strategy,
                )

            total_comparisons = 0
            total_differences = 0
            field_similarities = []
            all_conflicts = []

            # 对每个共同列进行比较
            for column in common_columns:
                if df1[column].dtype in ["object", "string"] or df2[column].dtype in [
                    "object",
                    "string",
                ]:
                    # 字符串列比较
                    similarity, differences, conflicts = (
                        await self._compare_string_columns(
                            df1, df2, column, metadata1, metadata2
                        )
                    )
                else:
                    # 数值列比较
                    similarity, differences, conflicts = (
                        await self._compare_numeric_columns(
                            df1, df2, column, metadata1, metadata2
                        )
                    )

                field_similarities.append(similarity)
                total_comparisons += differences["total"]
                total_differences += differences["different"]
                all_conflicts.extend(conflicts)

            # 计算总体相似度
            overall_similarity = (
                np.mean(field_similarities) if field_similarities else 0.0
            )
            confidence = min(metadata1.reliability_score, metadata2.reliability_score)

            (time.time() - start_time) * 1000

            return SourceComparisonResult(
                source1_name = name1,
                source2_name = name2,
                field_name="overall",
                similarity_score = overall_similarity,
                differences_detected = total_differences,
                total_comparisons = total_comparisons,
                confidence = confidence,
                tolerance_threshold = self.default_tolerance,
                resolution_strategy = self.conflict_resolution_strategy,
                conflicts = all_conflicts,
            )

        except Exception as e:
            logger.error(f"Comparison failed between {name1} and {name2}: {str(e)}")
            return SourceComparisonResult(
                source1_name = name1,
                source2_name = name2,
                field_name="error",
                similarity_score = 0.0,
                differences_detected = 0,
                total_comparisons = 0,
                confidence = 0.0,
                tolerance_threshold = self.default_tolerance,
                resolution_strategy = self.conflict_resolution_strategy,
                error_message = str(e),
            )

    async def _compare_numeric_columns(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        column: str,
        metadata1: DataSourceMetadata,
        metadata2: DataSourceMetadata,
    ) -> Tuple[float, Dict[str, int], List[Dict[str, Any]]]:
        """比较数值列"""
        try:
            # 对齐时间戳（如果存在）
            aligned_data = self._align_dataframes(df1, df2)
            if aligned_data is None:
                return 0.0, {"total": 0, "different": 0}, []

            aligned_df1, aligned_df2 = aligned_data
            if column not in aligned_df1.columns or column not in aligned_df2.columns:
                return 0.0, {"total": 0, "different": 0}, []

            series1 = aligned_df1[column].dropna()
            series2 = aligned_df2[column].dropna()

            # 进一步对齐
            common_index = series1.index.intersection(series2.index)
            series1 = series1.loc[common_index]
            series2 = series2.loc[common_index]

            if len(series1) == 0:
                return 0.0, {"total": 0, "different": 0}, []

            # 计算差异
            tolerance = self._get_column_tolerance(column)
            diff_mask = np.abs(series1 - series2) > tolerance * np.abs(series2)
            differences = diff_mask.sum()
            total = len(series1)

            # 计算相似度
            similarity = 1.0 - (differences / total) if total > 0 else 1.0

            # 记录冲突
            conflicts = []
            if differences > 0:
                diff_indices = series1.index[diff_mask]
                for idx in diff_indices[:10]:  # 限制记录的冲突数量
                    conflict = {
                        "timestamp": idx,
                        "column": column,
                        "value1": float(series1.loc[idx]),
                        "value2": float(series2.loc[idx]),
                        "difference_pct": float(
                            abs(series1.loc[idx] - series2.loc[idx]) / series2.loc[idx]
                        ),
                        "tolerance": tolerance,
                        "resolved_value": self._resolve_conflict(
                            series1.loc[idx], series2.loc[idx], metadata1, metadata2
                        ),
                    }
                    conflicts.append(conflict)

            return similarity, {"total": total, "different": differences}, conflicts

        except Exception as e:
            logger.error(f"Numeric column comparison failed for {column}: {str(e)}")
            return 0.0, {"total": 0, "different": 0}, []

    async def _compare_string_columns(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        column: str,
        metadata1: DataSourceMetadata,
        metadata2: DataSourceMetadata,
    ) -> Tuple[float, Dict[str, int], List[Dict[str, Any]]]:
        """比较字符串列"""
        try:
            aligned_data = self._align_dataframes(df1, df2)
            if aligned_data is None:
                return 0.0, {"total": 0, "different": 0}, []

            aligned_df1, aligned_df2 = aligned_data
            if column not in aligned_df1.columns or column not in aligned_df2.columns:
                return 0.0, {"total": 0, "different": 0}, []

            series1 = aligned_df1[column].dropna()
            series2 = aligned_df2[column].dropna()

            common_index = series1.index.intersection(series2.index)
            series1 = series1.loc[common_index]
            series2 = series2.loc[common_index]

            if len(series1) == 0:
                return 0.0, {"total": 0, "different": 0}, []

            # 字符串比较
            differences = (series1 != series2).sum()
            total = len(series1)
            similarity = 1.0 - (differences / total) if total > 0 else 1.0

            # 记录冲突
            conflicts = []
            if differences > 0:
                diff_mask = series1 != series2
                diff_indices = series1.index[diff_mask]
                for idx in diff_indices[:10]:
                    conflict = {
                        "timestamp": idx,
                        "column": column,
                        "value1": str(series1.loc[idx]),
                        "value2": str(series2.loc[idx]),
                        "resolved_value": self._resolve_conflict(
                            series1.loc[idx], series2.loc[idx], metadata1, metadata2
                        ),
                    }
                    conflicts.append(conflict)

            return similarity, {"total": total, "different": differences}, conflicts

        except Exception as e:
            logger.error(f"String column comparison failed for {column}: {str(e)}")
            return 0.0, {"total": 0, "different": 0}, []

    def _align_dataframes(
        self, df1: pd.DataFrame, df2: pd.DataFrame
    ) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
        """对齐两个DataFrame"""
        try:
            # 尝试找到时间戳列
            timestamp_col1 = (
                "timestamp"
                if "timestamp" in df1.columns
                else "date" if "date" in df1.columns else None
            )
            timestamp_col2 = (
                "timestamp"
                if "timestamp" in df2.columns
                else "date" if "date" in df2.columns else None
            )

            if timestamp_col1 and timestamp_col2:
                df1_copy = df1.copy()
                df2_copy = df2.copy()
                df1_copy[timestamp_col1] = pd.to_datetime(df1_copy[timestamp_col1])
                df2_copy[timestamp_col2] = pd.to_datetime(df2_copy[timestamp_col2])

                # 找到共同的时间戳
                common_timestamps = set(df1_copy[timestamp_col1]) & set(
                    df2_copy[timestamp_col2]
                )

                if len(common_timestamps) > 0:
                    df1_aligned = df1_copy[
                        df1_copy[timestamp_col1].isin(common_timestamps)
                    ]
                    df2_aligned = df2_copy[
                        df2_copy[timestamp_col2].isin(common_timestamps)
                    ]
                    return df1_aligned, df2_aligned
                else:
                    return None
            else:
                # 如果没有时间戳，尝试按索引对齐
                if len(df1) == len(df2):
                    return df1, df2
                else:
                    return None

        except Exception as e:
            logger.error(f"Data alignment failed: {str(e)}")
            return None

    def _get_column_tolerance(self, column: str) -> float:
        """获取列的容差阈值"""
        # 为不同的列类型设置不同的容差
        if "price" in column.lower() or "rate" in column.lower():
            return self.config.get("price_tolerance", 0.005)  # 0.5%
        elif "volume" in column.lower():
            return self.config.get("volume_tolerance", 0.05)  # 5%
        elif "percentage" in column.lower() or "ratio" in column.lower():
            return self.config.get("percentage_tolerance", 0.02)  # 2%
        else:
            return self.default_tolerance

    def _resolve_conflict(
        self,
        value1: Any,
        value2: Any,
        metadata1: DataSourceMetadata,
        metadata2: DataSourceMetadata,
    ) -> Any:
        """解决数据冲突"""
        if (
            self.conflict_resolution_strategy
            == ConflictResolutionStrategy.MAJORITY_VOTE
        ):
            # 简化版本：选择可靠性更高的数据源
            return (
                value1
                if metadata1.reliability_score > metadata2.reliability_score
                else value2
            )

        elif self.conflict_resolution_strategy == ConflictResolution.WEIGHTED_AVERAGE:
            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                total_weight = metadata1.reliability_score + metadata2.reliability_score
                if total_weight > 0:
                    return (
                        value1 * metadata1.reliability_score
                        + value2 * metadata2.reliability_score
                    ) / total_weight
                else:
                    return (value1 + value2) / 2
            else:
                return (
                    value1
                    if metadata1.reliability_score > metadata2.reliability_score
                    else value2
                )

        elif self.conflict_resolution_strategy == ConflictResolution.PRIORITY_OVERRIDE:
            return value1 if metadata1.priority < metadata2.priority else value2

        elif self.conflict_resolution_strategy == ConflictResolution.MEDIAN:
            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                return (value1 + value2) / 2
            else:
                return value1

        else:  # TRIMMED_MEAN 或其他
            return (
                value1
                if metadata1.reliability_score > metadata2.reliability_score
                else value2
            )

    async def _integrate_with_legacy_system(
        self,
        sources_data: List[Tuple[str, pd.DataFrame, DataSourceMetadata]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """与现有跨源验证系统集成"""
        if not self.legacy_verifier:
            return None

        try:
            # 转换为现有系统格式
            legacy_sources = []
            for name, df, metadata in sources_data:
                # 根据优先级确定枚举值
                if metadata.priority == 1:
                    priority = DataSourcePriority.CRITICAL
                elif metadata.priority == 2:
                    priority = DataSourcePriority.HIGH
                elif metadata.priority == 3:
                    priority = DataSourcePriority.MEDIUM
                else:
                    priority = DataSourcePriority.LOW

                legacy_source = DataSource(
                    name = name,
                    priority = priority,
                    data = df,
                    reliability_score = metadata.reliability_score,
                    last_updated = metadata.last_updated,
                )
                legacy_sources.append(legacy_source)

            # 执行验证
            legacy_result = await self.legacy_verifier.verify_sources(
                legacy_sources,
                symbol = context.get("symbol") if context else None,
                date_range = context.get("date_range") if context else None,
            )

            return {
                "verification_id": legacy_result.verification_id,
                "total_differences": legacy_result.total_differences,
                "quality_score": legacy_result.quality_score,
                "processing_time": legacy_result.processing_time,
            }

        except Exception as e:
            logger.error(f"Legacy system integration failed: {str(e)}")
            return None

    def _get_source_metadata(
        self, sources_data: List[Tuple[str, pd.DataFrame, DataSourceMetadata]]
    ) -> List[DataSourceMetadata]:
        """获取所有数据源的元数据"""
        return [metadata for _, _, metadata in sources_data]

    def _initialize_source_reliability(self) -> Dict[str, float]:
        """初始化数据源可靠性评分"""
        # 香港数据源的默认可靠性评分
        default_reliability = {
            # 官方数据源（高可靠性）
            "hkma": 0.95,  # 香港金融管理局
            "hkex": 0.90,  # 香港交易所
            "censusandstatistics": 0.85,  # 政府统计处
            "info.gov.hk": 0.80,  # 香港政府资讯中心
            # 商业数据源（中等可靠性）
            "bloomberg": 0.85,
            "reuters": 0.85,
            "factset": 0.80,
            # 开源数据源（较低可靠性）
            "yahoo": 0.70,
            "alpha_vantage": 0.65,
            "quandl": 0.60,
            # API数据源
            "central_api": 0.75,  # 中央API
            "futu_api": 0.70,  # 富途API
            # 默认值
            "unknown": 0.50,
        }

        return default_reliability

    async def update_source_reliability(
        self, source_name: str, reliability_score: float
    ):
        """更新数据源可靠性评分"""
        if 0.0 <= reliability_score <= 1.0:
            self.source_reliability[source_name] = reliability_score
            logger.info(
                f"Updated reliability score for {source_name}: {reliability_score}"
            )
        else:
            logger.warning(
                f"Invalid reliability score for {source_name}: {reliability_score}"
            )

    async def get_source_reliability_scores(self) -> Dict[str, float]:
        """获取所有数据源的可靠性评分"""
        return self.source_reliability.copy()


# Factory function
def create_cross_source_validator(
    config: Optional[Dict[str, Any]] = None,
) -> CrossSourceValidator:
    """创建跨源验证器"""
    return CrossSourceValidator(config)


# Export
__all__ = [
    "CrossSourceValidator",
    "ConflictResolutionStrategy",
    "SourceComparisonResult",
    "DataSourceMetadata",
    "DataSourceReliability",
    "create_cross_source_validator",
]
