"""
跨源数据验证系统

该模块提供多数据源数据一致性验证功能，包括：
- 多数据源对齐和比较
- 数据一致性检查
- 差异检测和报告
- 优先级策略和容错机制
- 数据合并规则
- 可配置的验证策略
- 实时和批处理验证
"""

import asyncio
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pydantic import BaseModel, Field, validator

# 配置日志
logger = logging.getLogger(__name__)


class VerificationLevel(str, Enum):
    """验证级别"""

    STRICT = "strict"  # 严格验证 - 任何差异都报告
    MODERATE = "moderate"  # 中等验证 - 重要字段差异才报告
    RELAXED = "relaxed"  # 宽松验证 - 只报告重大差异


class DataSourcePriority(str, Enum):
    """数据源优先级"""

    CRITICAL = 1  # 关键数据源
    HIGH = 2  # 高优先级
    MEDIUM = 3  # 中等优先级
    LOW = 4  # 低优先级


class DifferenceType(str, Enum):
    """差异类型"""

    VALUE_MISMATCH = "value_mismatch"  # 数值不匹配
    MISSING_DATA = "missing_data"  # 缺失数据
    EXTRA_DATA = "extra_data"  # 额外数据
    TYPE_MISMATCH = "type_mismatch"  # 类型不匹配
    RANGE_OUTLIER = "range_outlier"  # 范围异常
    TIMESTAMP_MISMATCH = "timestamp_mismatch"  # 时间戳不匹配


@dataclass
class DataSource:
    """数据源定义"""

    name: str
    priority: DataSourcePriority
    data: pd.DataFrame
    metadata: Dict[str, Any] = field(default_factory=dict)
    reliability_score: float = 1.0
    last_updated: Optional[datetime] = None


@dataclass
class VerificationRule:
    """验证规则"""

    rule_name: str
    field_name: str
    comparison_type: str  # 'exact', 'tolerance', 'percentage', 'range'
    threshold: Optional[float] = None
    tolerance: Optional[float] = None
    enabled: bool = True


@dataclass
class DataDifference:
    """数据差异记录"""

    difference_id: str
    source1: str
    source2: str
    difference_type: DifferenceType
    field_name: str
    timestamp: Optional[pd.Timestamp]
    value1: Any
    value2: Any
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """验证结果"""

    verification_id: str
    timestamp: datetime
    total_differences: int
    critical_differences: int
    major_differences: int
    minor_differences: int
    data_sources: List[str]
    differences: List[DataDifference]
    consensus_data: Optional[pd.DataFrame] = None
    quality_score: float = 0.0
    processing_time: float = 0.0


class VerificationConfig(BaseModel):
    """验证配置"""

    verification_level: VerificationLevel = VerificationLevel.MODERATE
    max_workers: int = 4
    enable_parallel: bool = True
    tolerance_percentage: float = 0.01  # 1% 默认容忍度
    missing_data_threshold: float = 0.05  # 5% 缺失数据阈值
    outlier_threshold: float = 3.0  # Z - score 阈值
    consensus_method: str = (
        "majority_vote"  # 'majority_vote', 'priority', 'average', 'median'
    )
    output_format: str = "json"  # 'json', 'csv', 'html'
    save_visualization: bool = True
    auto_merge: bool = False
    merge_on_disagreement: bool = False
    validation_rules: List[VerificationRule] = Field(default_factory=list)
    exclude_fields: List[str] = Field(default_factory=list)
    time_window: Optional[int] = None  # 小时数

    class Config:
        use_enum_values = True


class CrossSourceVerifier:
    """
    跨源数据验证器

    提供完整的多数据源数据一致性验证、差异检测、报告和合并功能。
    """

    def __init__(self, config: Optional[VerificationConfig] = None):
        """
        初始化验证器

        Args:
            config: 验证配置，如果为None则使用默认配置
        """
        self.config = config or VerificationConfig()
        self.differences_cache: Dict[str, List[DataDifference]] = {}
        self.verification_history: List[VerificationResult] = []
        self.consensus_cache: Dict[str, pd.DataFrame] = {}

        logger.info(
            f"CrossSourceVerifier initialized with level: {self.config.verification_level}"
        )

    def add_data_source(
        self,
        name: str,
        data: pd.DataFrame,
        priority: DataSourcePriority = DataSourcePriority.MEDIUM,
        reliability_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        添加数据源

        Args:
            name: 数据源名称
            data: 数据框
            priority: 优先级
            reliability_score: 可靠性评分 (0 - 1)
            metadata: 元数据
        """
        if data.empty:
            raise ValueError(f'Data for source "{name}" is empty')

        if reliability_score < 0 or reliability_score > 1:
            raise ValueError(
                f"Reliability score must be between 0 and 1, got {reliability_score}"
            )

        logger.info(
            f"Added data source: {name}, {len(data)} records, priority: {priority}"
        )

    async def verify_sources(
        self,
        sources: List[DataSource],
        symbol: Optional[str] = None,
        date_range: Optional[Tuple[str, str]] = None,
    ) -> VerificationResult:
        """
        验证多个数据源的一致性

        Args:
            sources: 数据源列表
            symbol: 股票代码（可选）
            date_range: 日期范围（可选，格式：('YYYY - MM - DD', 'YYYY - MM - DD')）

        Returns:
            VerificationResult: 验证结果
        """
        start_time = datetime.now()
        verification_id = self._generate_verification_id()

        logger.info(
            f"Starting verification {verification_id} for {len(sources)} sources"
        )

        # 预处理数据
        processed_sources = await self._preprocess_sources(sources, symbol, date_range)

        # 检测差异
        differences = await self._detect_differences(processed_sources)

        # 生成一致性数据
        consensus_data = await self._generate_consensus_data(
            processed_sources, differences
        )

        # 计算质量评分
        quality_score = self._calculate_quality_score(differences, processed_sources)

        # 创建结果
        result = VerificationResult(
            verification_id=verification_id,
            timestamp=start_time,
            total_differences=len(differences),
            critical_differences=len(
                [d for d in differences if d.severity == "critical"]
            ),
            major_differences=len([d for d in differences if d.severity == "major"]),
            minor_differences=len([d for d in differences if d.severity == "minor"]),
            data_sources=[s.name for s in sources],
            differences=differences,
            consensus_data=consensus_data,
            quality_score=quality_score,
            processing_time=(datetime.now() - start_time).total_seconds(),
        )

        # 缓存结果
        self.verification_history.append(result)
        self.differences_cache[verification_id] = differences

        # 自动合并（如果配置了）
        if self.config.auto_merge and consensus_data is not None:
            logger.info("Auto - merging data based on consensus")

        logger.info(
            f"Verification complete: {len(differences)} differences found, "
            f"quality score: {quality_score:.2f}"
        )

        return result

    async def _preprocess_sources(
        self,
        sources: List[DataSource],
        symbol: Optional[str],
        date_range: Optional[Tuple[str, str]],
    ) -> List[DataSource]:
        """预处理数据源"""
        processed = []

        for source in sources:
            data = source.data.copy()

            # 确保时间戳列为datetime类型
            if "timestamp" in data.columns:
                data["timestamp"] = pd.to_datetime(data["timestamp"])

            # 过滤日期范围
            if date_range and "timestamp" in data.columns:
                start_date = pd.to_datetime(date_range[0])
                end_date = pd.to_datetime(date_range[1])
                data = data[
                    (data["timestamp"] >= start_date) & (data["timestamp"] <= end_date)
                ]

            # 填充缺失的列
            for col in data.columns:
                if col not in ["timestamp", "date"]:
                    if data[col].dtype in ["float64", "int64"]:
                        data[col] = (
                            data[col].fillna(method="ffill").fillna(method="bfill")
                        )

            # 更新时间戳
            source.data = data.sort_values(
                "timestamp" if "timestamp" in data.columns else data.index
            )
            source.last_updated = datetime.now()

            processed.append(source)

        return processed

    async def _detect_differences(
        self, sources: List[DataSource]
    ) -> List[DataDifference]:
        """检测数据源之间的差异"""
        differences = []

        if len(sources) < 2:
            logger.warning("Need at least 2 data sources for comparison")
            return differences

        # 获取所有共同列
        common_columns = set(sources[0].data.columns)
        for source in sources[1:]:
            common_columns &= set(source.data.columns)

        # 排除指定字段
        common_columns -= set(self.config.exclude_fields)

        logger.info(
            f"Comparing {len(common_columns)} common columns across {len(sources)} sources"
        )

        # 并行检测差异（如果启用）
        if self.config.enable_parallel and len(sources) > 2:
            differences = await self._detect_differences_parallel(
                sources, list(common_columns)
            )
        else:
            differences = await self._detect_differences_sequential(
                sources, list(common_columns)
            )

        return differences

    async def _detect_differences_parallel(
        self, sources: List[DataSource], columns: List[str]
    ) -> List[DataDifference]:
        """并行检测差异"""
        differences = []
        tasks = []

        # 创建任务
        for i, col in enumerate(columns):
            task = self._detect_column_differences(sources, col)
            tasks.append(task)

        # 执行任务
        results = await asyncio.gather(*tasks)

        # 合并结果
        for result in results:
            differences.extend(result)

        return differences

    async def _detect_differences_sequential(
        self, sources: List[DataSource], columns: List[str]
    ) -> List[DataDifference]:
        """顺序检测差异"""
        differences = []

        for col in columns:
            col_diff = await self._detect_column_differences(sources, col)
            differences.extend(col_diff)

        return differences

    async def _detect_column_differences(
        self, sources: List[DataSource], column: str
    ) -> List[DataDifference]:
        """检测特定列的差异"""
        differences = []

        # 对每个数据源组合进行比较
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                source1, source2 = sources[i], sources[j]
                diff = await self._compare_sources_column(source1, source2, column)
                if diff:
                    differences.append(diff)

        return differences

    async def _compare_sources_column(
        self, source1: DataSource, source2: DataSource, column: str
    ) -> Optional[DataDifference]:
        """比较两个数据源的特定列"""
        data1 = source1.data
        data2 = source2.data

        # 确保时间戳列存在
        timestamp_col = (
            "timestamp"
            if "timestamp" in data1.columns
            else data1.index.name or data1.index.names[0]
        )
        ts_col = (
            "timestamp"
            if "timestamp" in data2.columns
            else data2.index.name or data2.index.names[0]
        )

        # 合并数据
        merged = pd.merge(
            data1[[timestamp_col, column]].rename(columns={timestamp_col: "ts1"}),
            data2[[ts_col, column]].rename(columns={ts_col: "ts2"}),
            left_on="ts1",
            right_on="ts2",
            how="outer",
            indicator=True,
        )

        # 检查缺失数据
        missing_in_1 = merged["_merge"] == "right_only"
        missing_in_2 = merged["_merge"] == "left_only"

        if missing_in_1.any():
            diff = DataDifference(
                difference_id=self._generate_difference_id(),
                source1=source1.name,
                source2=source2.name,
                difference_type=DifferenceType.MISSING_DATA,
                field_name=column,
                timestamp=(
                    merged.loc[missing_in_1, "ts2"].iloc[0]
                    if not missing_in_1.empty
                    else None
                ),
                value1=None,
                value2=(
                    merged.loc[missing_in_1, column].iloc[0]
                    if not missing_in_1.empty
                    else None
                ),
                severity=self._determine_severity("missing"),
                message=f"Data missing in {source1.name} but present in {source2.name}",
            )
            return diff

        if missing_in_2.any():
            diff = DataDifference(
                difference_id=self._generate_difference_id(),
                source1=source1.name,
                source2=source2.name,
                difference_type=DifferenceType.MISSING_DATA,
                field_name=column,
                timestamp=(
                    merged.loc[missing_in_2, "ts1"].iloc[0]
                    if not missing_in_2.empty
                    else None
                ),
                value1=(
                    merged.loc[missing_in_2, column].iloc[0]
                    if not missing_in_2.empty
                    else None
                ),
                value2=None,
                severity=self._determine_severity("missing"),
                message=f"Data missing in {source2.name} but present in {source1.name}",
            )
            return diff

        # 对齐数据（内连接）
        aligned = pd.merge(
            data1[[timestamp_col, column]].rename(columns={timestamp_col: "ts1"}),
            data2[[ts_col, column]].rename(columns={ts_col: "ts2"}),
            left_on="ts1",
            right_on="ts2",
            how="inner",
        )

        if aligned.empty:
            return None

        # 检查数值差异
        val1 = aligned[f"{column}_x"]
        val2 = aligned[f"{column}_y"]

        # 计算差异
        if aligned[column + "_x"].dtype in ["float64", "int64"] and aligned[
            column + "_y"
        ].dtype in ["float64", "int64"]:
            # 数值类型比较
            diff_mask = (
                val1 - val2
            ).abs() > self.config.tolerance_percentage * val2.abs()
        else:
            # 字符串 / 其他类型比较
            diff_mask = val1 != val2

        if diff_mask.any():
            # 获取第一个差异
            first_diff_idx = diff_mask.idxmax() if diff_mask.any() else None
            if first_diff_idx is not None:
                diff = DataDifference(
                    difference_id=self._generate_difference_id(),
                    source1=source1.name,
                    source2=source2.name,
                    difference_type=DifferenceType.VALUE_MISMATCH,
                    field_name=column,
                    timestamp=aligned.loc[first_diff_idx, "ts1"],
                    value1=val1.loc[first_diff_idx],
                    value2=val2.loc[first_diff_idx],
                    severity=self._determine_severity("value"),
                    message=f"Value mismatch in {column}: {val1.loc[first_diff_idx]} vs {val2.loc[first_diff_idx]}",
                )
                return diff

        return None

    async def _generate_consensus_data(
        self, sources: List[DataSource], differences: List[DataDifference]
    ) -> Optional[pd.DataFrame]:
        """生成一致性数据"""
        if not sources:
            return None

        # 获取主数据源
        primary_source = self._get_primary_source(sources)

        consensus = primary_source.data.copy()

        # 根据差异修复数据
        for diff in differences:
            if diff.difference_type == DifferenceType.VALUE_MISMATCH:
                # 使用优先级策略选择值
                better_value = self._select_better_value(diff, sources)
                if better_value is not None:
                    # 更新共识数据
                    mask = (
                        consensus["timestamp"] == diff.timestamp
                        if "timestamp" in consensus.columns
                        else consensus.index == diff.timestamp
                    )
                    consensus.loc[mask, diff.field_name] = better_value

        return consensus

    def _get_primary_source(self, sources: List[DataSource]) -> DataSource:
        """获取主数据源（优先级最高）"""
        # 按优先级排序
        sorted_sources = sorted(sources, key=lambda s: s.priority.value)
        return sorted_sources[0]

    def _select_better_value(
        self, difference: DataDifference, sources: List[DataSource]
    ) -> Any:
        """根据优先级选择更好的值"""
        source1 = next((s for s in sources if s.name == difference.source1), None)
        source2 = next((s for s in sources if s.name == difference.source2), None)

        if not source1 or not source2:
            return None

        # 比较可靠性
        if source1.reliability_score > source2.reliability_score:
            return difference.value1
        elif source2.reliability_score > source1.reliability_score:
            return difference.value2

        # 相同可靠性，使用平均值或中位数
        if self.config.consensus_method == "average":
            try:
                return (float(difference.value1) + float(difference.value2)) / 2
            except (ValueError, TypeError):
                return difference.value1
        elif self.config.consensus_method == "median":
            try:
                return np.median([float(difference.value1), float(difference.value2)])
            except (ValueError, TypeError):
                return difference.value1

        # 默认返回第一个值
        return difference.value1

    def _determine_severity(self, diff_type: str) -> str:
        """确定差异严重性"""
        if self.config.verification_level == VerificationLevel.STRICT:
            return "medium" if diff_type in ["value", "missing"] else "low"
        elif self.config.verification_level == VerificationLevel.MODERATE:
            return "major" if diff_type == "value" else "minor"
        else:  # RELAXED
            return "minor" if diff_type == "value" else "low"

    def _calculate_quality_score(
        self, differences: List[DataDifference], sources: List[DataSource]
    ) -> float:
        """计算数据质量评分"""
        if not sources:
            return 0.0

        total_records = sum(len(s.data) for s in sources)
        if total_records == 0:
            return 0.0

        # 计算差异率
        diff_rate = len(differences) / total_records

        # 根据差异类型加权
        critical_penalty = (
            len([d for d in differences if d.severity == "critical"]) * 0.1
        )
        major_penalty = len([d for d in differences if d.severity == "major"]) * 0.05
        minor_penalty = len([d for d in differences if d.severity == "minor"]) * 0.01

        # 基础质量评分
        base_score = 1.0 - diff_rate
        quality_score = base_score - critical_penalty - major_penalty - minor_penalty

        return max(0.0, min(1.0, quality_score))

    def _generate_verification_id(self) -> str:
        """生成验证ID"""
        timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        hash_obj = hashlib.sha256(str(timestamp).encode())
        return f"VER_{timestamp}_{hash_obj.hexdigest()[:8]}"

    def _generate_difference_id(self) -> str:
        """生成差异ID"""
        timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        random_suffix = np.random.randint(1000, 9999)
        return f"DIFF_{timestamp}_{random_suffix}"

    async def batch_verify(
        self, verification_tasks: List[Dict[str, Any]]
    ) -> List[VerificationResult]:
        """
        批量验证多个数据集

        Args:
            verification_tasks: 验证任务列表，每个任务包含sources等参数

        Returns:
            验证结果列表
        """
        logger.info(f"Starting batch verification for {len(verification_tasks)} tasks")

        if self.config.enable_parallel:
            # 并行执行
            tasks = []
            for task in verification_tasks:
                sources = task["sources"]
                task_result = self.verify_sources(
                    sources, task.get("symbol"), task.get("date_range")
                )
                tasks.append(task_result)

            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 顺序执行
            results = []
            for task in verification_tasks:
                sources = task["sources"]
                result = await self.verify_sources(
                    sources, task.get("symbol"), task.get("date_range")
                )
                results.append(result)

        logger.info(f"Batch verification complete: {len(results)} results")

        return results

    def generate_report(
        self, result: VerificationResult, output_path: Optional[str] = None
    ) -> str:
        """
        生成验证报告

        Args:
            result: 验证结果
            output_path: 输出路径，如果为None则返回字符串

        Returns:
            报告内容或输出文件路径
        """
        report = self._format_report(result)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf - 8") as f:
                f.write(report)
            logger.info(f"Report saved to {output_path}")
            return output_path

        return report

    def _format_report(self, result: VerificationResult) -> str:
        """格式化报告"""
        report = """
跨源数据验证报告
================

验证ID: {result.verification_id}
验证时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
处理时间: {result.processing_time:.2f} 秒

数据源:
{chr(10).join(f"  - {name}" for name in result.data_sources)}

差异统计:
  总差异数: {result.total_differences}
  严重差异: {result.critical_differences}
  主要差异: {result.major_differences}
  次要差异: {result.minor_differences}
  质量评分: {result.quality_score:.2%}

差异详情:
"""

        for diff in result.differences:
            report += """
  [{diff.severity.upper()}] {diff.source1} vs {diff.source2}
  字段: {diff.field_name}
  类型: {diff.difference_type}
  消息: {diff.message}
"""

        if result.consensus_data is not None:
            report += """
共识数据统计:
  记录数: {len(result.consensus_data)}
  列数: {len(result.consensus_data.columns)}
"""

        return report

    def visualize_differences(
        self, result: VerificationResult, output_dir: str = "verification_reports"
    ) -> List[str]:
        """
        生成差异可视化图表

        Args:
            result: 验证结果
            output_dir: 输出目录

        Returns:
            生成的图表文件路径列表
        """
        if not self.config.save_visualization:
            return []

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_files = []

        # 差异类型分布图
        fig, ax = plt.subplots(figsize=(10, 6))
        diff_counts = {}
        for diff in result.differences:
            diff_type = diff.difference_type
            diff_counts[diff_type] = diff_counts.get(diff_type, 0) + 1

        if diff_counts:
            labels = list(diff_counts.keys())
            sizes = list(diff_counts.values())
            ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.set_title("差异类型分布")
            output_file = f"{output_dir}/diff_types_{result.verification_id}.png"
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()
            output_files.append(output_file)

        # 严重性分布图
        fig, ax = plt.subplots(figsize=(10, 6))
        severity_counts = {}
        for diff in result.differences:
            severity = diff.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        if severity_counts:
            labels = list(severity_counts.keys())
            sizes = list(severity_counts.values())
            colors = ["red", "orange", "yellow", "green"]
            ax.bar(labels, sizes, color=colors[: len(labels)])
            ax.set_title("差异严重性分布")
            ax.set_ylabel("数量")
            plt.xticks(rotation=45)
            output_file = f"{output_dir}/severity_{result.verification_id}.png"
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()
            output_files.append(output_file)

        # 数据源比较热力图
        if len(result.data_sources) > 1:
            comparison_matrix = self._create_comparison_matrix(
                result.differences, result.data_sources
            )
            if not comparison_matrix.empty:
                fig, ax = plt.subplots(figsize=(10, 8))
                sns.heatmap(comparison_matrix, annot=True, cmap="Reds", ax=ax)
                ax.set_title("数据源差异热力图")
                output_file = f"{output_dir}/heatmap_{result.verification_id}.png"
                plt.savefig(output_file, dpi=300, bbox_inches="tight")
                plt.close()
                output_files.append(output_file)

        logger.info(
            f"Generated {len(output_files)} visualization files in {output_dir}"
        )

        return output_files

    def _create_comparison_matrix(
        self, differences: List[DataDifference], sources: List[str]
    ) -> pd.DataFrame:
        """创建数据源比较矩阵"""
        matrix = pd.DataFrame(0, index=sources, columns=sources)

        for diff in differences:
            if diff.source1 in sources and diff.source2 in sources:
                # 权重差异严重性
                weight = 1
                if diff.severity == "critical":
                    weight = 4
                elif diff.severity == "major":
                    weight = 3
                elif diff.severity == "minor":
                    weight = 2

                matrix.loc[diff.source1, diff.source2] += weight
                matrix.loc[diff.source2, diff.source1] += weight

        return matrix

    def export_results(
        self, result: VerificationResult, output_path: str, format: str = "json"
    ) -> str:
        """
        导出验证结果

        Args:
            result: 验证结果
            output_path: 输出路径
            format: 格式 ('json', 'csv', 'xlsx')

        Returns:
            输出文件路径
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            result_dict = {
                "verification_id": result.verification_id,
                "timestamp": result.timestamp.isoformat(),
                "total_differences": result.total_differences,
                "critical_differences": result.critical_differences,
                "major_differences": result.major_differences,
                "minor_differences": result.minor_differences,
                "data_sources": result.data_sources,
                "quality_score": result.quality_score,
                "processing_time": result.processing_time,
                "differences": [
                    {
                        "id": d.difference_id,
                        "source1": d.source1,
                        "source2": d.source2,
                        "type": d.difference_type,
                        "field": d.field_name,
                        "severity": d.severity,
                        "message": d.message,
                        "value1": str(d.value1) if d.value1 is not None else None,
                        "value2": str(d.value2) if d.value2 is not None else None,
                    }
                    for d in result.differences
                ],
            }

            with open(output_path, "w", encoding="utf - 8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)

        elif format == "csv":
            diff_df = pd.DataFrame(
                [
                    {
                        "ID": d.difference_id,
                        "Source1": d.source1,
                        "Source2": d.source2,
                        "Type": d.difference_type,
                        "Field": d.field_name,
                        "Severity": d.severity,
                        "Message": d.message,
                        "Value1": d.value1,
                        "Value2": d.value2,
                    }
                    for d in result.differences
                ]
            )
            diff_df.to_csv(output_path, index=False, encoding="utf - 8 - sig")

        elif format == "xlsx":
            with pd.ExcelWriter(output_path) as writer:
                # 差异详情
                diff_df = pd.DataFrame(
                    [
                        {
                            "ID": d.difference_id,
                            "Source1": d.source1,
                            "Source2": d.source2,
                            "Type": d.difference_type,
                            "Field": d.field_name,
                            "Severity": d.severity,
                            "Message": d.message,
                            "Value1": d.value1,
                            "Value2": d.value2,
                        }
                        for d in result.differences
                    ]
                )
                diff_df.to_excel(writer, sheet_name="Differences", index=False)

                # 摘要
                summary_df = pd.DataFrame(
                    [
                        {"Metric": "Verification ID", "Value": result.verification_id},
                        {"Metric": "Timestamp", "Value": result.timestamp},
                        {
                            "Metric": "Total Differences",
                            "Value": result.total_differences,
                        },
                        {
                            "Metric": "Critical Differences",
                            "Value": result.critical_differences,
                        },
                        {
                            "Metric": "Major Differences",
                            "Value": result.major_differences,
                        },
                        {
                            "Metric": "Minor Differences",
                            "Value": result.minor_differences,
                        },
                        {
                            "Metric": "Quality Score",
                            "Value": f"{result.quality_score:.2%}",
                        },
                        {
                            "Metric": "Processing Time",
                            "Value": f"{result.processing_time:.2f}s",
                        },
                    ]
                )
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

                # 共识数据（如果存在）
                if result.consensus_data is not None:
                    result.consensus_data.to_excel(writer, sheet_name="ConsensusData")

        logger.info(f"Results exported to {output_path} in {format} format")

        return output_path

    def get_verification_history(self) -> List[VerificationResult]:
        """获取验证历史"""
        return self.verification_history

    def clear_cache(self) -> None:
        """清除缓存"""
        self.differences_cache.clear()
        self.consensus_cache.clear()
        logger.info("Cache cleared")


# 便捷函数
def quick_verify(
    sources_data: List[Dict[str, Any]],
    level: VerificationLevel = VerificationLevel.MODERATE,
) -> VerificationResult:
    """
    快速验证多个数据源

    Args:
        sources_data: 数据源信息列表
        level: 验证级别

    Returns:
        验证结果
    """
    config = VerificationConfig(verification_level=level)
    verifier = CrossSourceVerifier(config)

    sources = [
        DataSource(
            name=source["name"],
            data=source["data"],
            priority=DataSourcePriority(source.get("priority", "medium")),
            reliability_score=source.get("reliability_score", 1.0),
        )
        for source in sources_data
    ]

    return asyncio.run(verifier.verify_sources(sources))


def compare_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    name1: str = "DataFrame1",
    name2: str = "DataFrame2",
    tolerance: float = 0.01,
) -> VerificationResult:
    """
    比较两个数据框

    Args:
        df1: 第一个数据框
        df2: 第二个数据框
        name1: 第一个数据框名称
        name2: 第二个数据框名称
        tolerance: 容忍度

    Returns:
        验证结果
    """
    config = VerificationConfig(
        verification_level=VerificationLevel.STRICT, tolerance_percentage=tolerance
    )
    verifier = CrossSourceVerifier(config)

    sources = [
        DataSource(name=name1, data=df1, priority=DataSourcePriority.HIGH),
        DataSource(name=name2, data=df2, priority=DataSourcePriority.MEDIUM),
    ]

    return asyncio.run(verifier.verify_sources(sources))


if __name__ == "__main__":
    # 示例用法
    logging.basicConfig(level=logging.INFO)

    # 创建示例数据
    dates = pd.date_range("2023 - 01 - 01", periods=100, freq="D")
    np.random.seed(42)

    df1 = pd.DataFrame(
        {
            "timestamp": dates,
            "price": 100 + np.cumsum(np.random.randn(100) * 0.5),
            "volume": np.random.randint(1000, 10000, 100),
        }
    )

    df2 = df1.copy()
    df2.loc[10:15, "price"] *= 1.02  # 引入差异
    df2.loc[50, "volume"] = np.nan  # 引入缺失

    # 执行验证
    result = compare_dataframes(df1, df2, "Source1", "Source2", tolerance=0.01)

    # 生成报告
    verifier = CrossSourceVerifier()
    report = verifier.generate_report(result)
    print(report)

    # 导出结果
    verifier.export_results(result, "verification_results.json", "json")
    verifier.visualize_differences(result)
