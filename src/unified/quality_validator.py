"""
数据质量验证器

为价格和非价格数据提供全面的质量验证、异常检测和质量评分功能。

Task #31: Data Flow Unification - Price and Non-Price Integration
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    """数据质量等级"""
    EXCELLENT = 5
    GOOD = 4
    ACCEPTABLE = 3
    POOR = 2
    UNACCEPTABLE = 1

class QualityIssue(Enum):
    """质量问题类型"""
    MISSING_VALUES = "missing_values"
    OUTLIERS = "outliers"
    STALE_DATA = "stale_data"
    INCONSISTENT_TIMESTAMPS = "inconsistent_timestamps"
    DUPLICATE_DATA = "duplicate_data"
    INVALID_FORMAT = "invalid_format"
    SOURCE_UNAVAILABLE = "source_unavailable"
    DATA_GAPS = "data_gaps"
    ABNORMAL_PATTERNS = "abnormal_patterns"

@dataclass
class QualityThresholds:
    """质量阈值配置"""
    completeness_threshold: float = 0.95  # 95%完整性要求
    outlier_threshold: float = 3.0        # 3-sigma异常值检测
    staleness_threshold: int = 300        # 5分钟过期阈值
    duplicate_threshold: float = 0.01     # 1%重复阈值
    gap_threshold: int = 60               # 60分钟数据间隙阈值
    timestamp_consistency_threshold: int = 10  # 10秒时间戳一致性阈值

@dataclass
class QualityCheck:
    """质量检查结果"""
    check_name: str
    passed: bool
    score: float
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QualityResult:
    """综合质量评估结果"""
    data_type: str
    symbol: str
    total_points: int
    valid_points: int
    overall_score: float
    quality_level: QualityLevel
    checks: Dict[str, QualityCheck] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class DataQualityValidator:
    """数据质量验证器"""

    def __init__(self, thresholds: Optional[QualityThresholds] = None):
        self.thresholds = thresholds or QualityThresholds()
        self.logger = logging.getLogger(__name__)

        # 数据源特定配置
        self.source_configs = {
            'price': {
                'expected_fields': ['open', 'high', 'low', 'close', 'volume'],
                'outlier_sensitivity': 2.5,
                'staleness_threshold': 60  # 1 minute for price data
            },
            'hkma': {
                'expected_fields': ['value', 'indicator'],
                'outlier_sensitivity': 3.0,
                'staleness_threshold': 86400  # 24 hours for macro data
            },
            'sentiment': {
                'expected_fields': ['sentiment', 'confidence'],
                'outlier_sensitivity': 2.0,
                'staleness_threshold': 1800  # 30 minutes for sentiment
            },
            'alternative': {
                'expected_fields': ['value'],
                'outlier_sensitivity': 2.5,
                'staleness_threshold': 3600  # 1 hour for alternative data
            }
        }

    async def validate_data_quality(
        self,
        data: List[Dict[str, Any]],
        data_type: str,
        symbol: str = "unknown"
    ) -> QualityResult:
        """全面的数据质量验证"""
        try:
            if not data:
                return QualityResult(
                    data_type=data_type,
                    symbol=symbol,
                    total_points=0,
                    valid_points=0,
                    overall_score=0.0,
                    quality_level=QualityLevel.UNACCEPTABLE,
                    checks={},
                    recommendations=["没有可用的数据进行验证"]
                )

            # 基本统计
            total_points = len(data)
            valid_points = len([dp for dp in data if self._is_valid_data_point(dp)])

            # 执行各项质量检查
            checks = await self._run_quality_checks(data, data_type)

            # 计算综合质量评分
            overall_score = self._calculate_overall_score(checks)
            quality_level = self._get_quality_level(overall_score)

            # 生成改进建议
            recommendations = self._generate_recommendations(checks, data_type)

            result = QualityResult(
                data_type=data_type,
                symbol=symbol,
                total_points=total_points,
                valid_points=valid_points,
                overall_score=overall_score,
                quality_level=quality_level,
                checks=checks,
                recommendations=recommendations,
                metadata={
                    'validation_time': datetime.now().isoformat(),
                    'thresholds_used': self.thresholds.__dict__,
                    'source_config': self.source_configs.get(data_type, {})
                }
            )

            # 记录质量问题
            if overall_score < 0.8:
                await self._log_quality_issues(result)

            return result

        except Exception as e:
            self.logger.error(f"数据质量验证失败 {data_type}:{symbol}: {e}")
            return QualityResult(
                data_type=data_type,
                symbol=symbol,
                total_points=0,
                valid_points=0,
                overall_score=0.0,
                quality_level=QualityLevel.UNACCEPTABLE,
                recommendations=[f"验证过程异常: {str(e)}"]
            )

    async def validate_unified_data_point(
        self,
        data_point: Dict[str, Any],
        source_type: str,
        symbol: str
    ) -> QualityCheck:
        """验证单个统一数据点"""
        try:
            issues = []
            score = 1.0

            # 检查必需字段
            required_fields = ['timestamp', 'symbol', 'source', 'data_type', 'value']
            for field in required_fields:
                if field not in data_point or data_point[field] is None:
                    issues.append(f"缺少必需字段: {field}")
                    score -= 0.2

            # 检查数据类型特定字段
            source_config = self.source_configs.get(source_type, {})
            expected_fields = source_config.get('expected_fields', [])
            for field in expected_fields:
                if field not in data_point.get('metadata', {}):
                    issues.append(f"缺少{source_type}数据必需字段: {field}")
                    score -= 0.1

            # 检查时间戳有效性
            timestamp = data_point.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        issues.append("时间戳格式无效")
                        score -= 0.3

                if timestamp and timestamp > datetime.now():
                    issues.append("时间戳在未来")
                    score -= 0.2

            # 检查数值有效性
            value = data_point.get('value')
            if value is not None:
                try:
                    float_value = float(value)
                    if not np.isfinite(float_value):
                        issues.append("数值无效 (NaN或Inf)")
                        score -= 0.5
                except (ValueError, TypeError):
                    issues.append("数值转换失败")
                    score -= 0.5

            passed = score >= 0.7 and len(issues) == 0

            return QualityCheck(
                check_name="data_point_validation",
                passed=passed,
                score=max(0.0, score),
                issues=issues,
                metadata={
                    'source_type': source_type,
                    'symbol': symbol,
                    'fields_checked': required_fields + expected_fields
                }
            )

        except Exception as e:
            self.logger.error(f"数据点验证失败: {e}")
            return QualityCheck(
                check_name="data_point_validation",
                passed=False,
                score=0.0,
                issues=[f"验证异常: {str(e)}"]
            )

    async def _run_quality_checks(
        self,
        data: List[Dict[str, Any]],
        data_type: str
    ) -> Dict[str, QualityCheck]:
        """执行所有质量检查"""
        checks = {}

        # 完整性检查
        checks['completeness'] = self._check_completeness(data)

        # 异常值检查
        checks['outliers'] = await self._check_outliers(data, data_type)

        # 新鲜度检查
        checks['staleness'] = self._check_staleness(data, data_type)

        # 时间戳一致性检查
        checks['timestamp_consistency'] = self._check_timestamp_consistency(data)

        # 重复数据检查
        checks['duplicates'] = self._check_duplicates(data)

        # 数据间隙检查
        checks['data_gaps'] = self._check_data_gaps(data)

        # 格式有效性检查
        checks['format_validity'] = self._check_format_validity(data, data_type)

        # 异常模式检查
        checks['abnormal_patterns'] = await self._check_abnormal_patterns(data, data_type)

        return checks

    def _check_completeness(self, data: List[Dict[str, Any]]) -> QualityCheck:
        """检查数据完整性"""
        try:
            total_points = len(data)
            valid_points = len([dp for dp in data if self._is_valid_data_point(dp)])
            completeness_rate = valid_points / total_points if total_points > 0 else 0

            issues = []
            if completeness_rate < self.thresholds.completeness_threshold:
                issues.append(f"完整性不足: {completeness_rate:.2%} (要求: {self.thresholds.completeness_threshold:.2%})")

            passed = completeness_rate >= self.thresholds.completeness_threshold

            return QualityCheck(
                check_name="completeness",
                passed=passed,
                score=completeness_rate,
                issues=issues,
                metadata={
                    'total_points': total_points,
                    'valid_points': valid_points,
                    'completeness_rate': completeness_rate
                }
            )

        except Exception as e:
            return QualityCheck(
                check_name="completeness",
                passed=False,
                score=0.0,
                issues=[f"完整性检查异常: {str(e)}"]
            )

    async def _check_outliers(
        self,
        data: List[Dict[str, Any]],
        data_type: str
    ) -> QualityCheck:
        """检查异常值"""
        try:
            values = []
            for dp in data:
                if self._is_valid_data_point(dp):
                    value = dp.get('value')
                    if value is not None:
                        try:
                            values.append(float(value))
                        except (ValueError, TypeError):
                            continue

            if len(values) < 10:
                return QualityCheck(
                    check_name="outliers",
                    passed=False,
                    score=0.5,
                    issues=["数据点不足，无法进行异常值检测"],
                    metadata={'sample_size': len(values)}
                )

            # 获取敏感度配置
            source_config = self.source_configs.get(data_type, {})
            sensitivity = source_config.get('outlier_sensitivity', self.thresholds.outlier_threshold)

            # Z-score异常值检测
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 0

            outliers = []
            outlier_indices = []
            for i, value in enumerate(values):
                if std_val > 0:
                    z_score = abs((value - mean_val) / std_val)
                    if z_score > sensitivity:
                        outliers.append(value)
                        outlier_indices.append(i)

            # IQR方法检测异常值
            sorted_values = sorted(values)
            n = len(sorted_values)
            q1 = sorted_values[n // 4]
            q3 = sorted_values[3 * n // 4]
            iqr = q3 - q1

            iqr_outliers = [
                v for v in values
                if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr
            ]

            outlier_percentage = len(outliers) / len(values)
            iqr_outlier_percentage = len(iqr_outliers) / len(values)

            # 综合评分
            max_outlier_percentage = max(outlier_percentage, iqr_outlier_percentage)
            score = max(0.0, 1.0 - (max_outlier_percentage * 2))  # 双倍惩罚

            issues = []
            if outlier_percentage > 0.05:
                issues.append(f"Z-score异常值过多: {outlier_percentage:.2%}")
            if iqr_outlier_percentage > 0.05:
                issues.append(f"IQR异常值过多: {iqr_outlier_percentage:.2%}")

            passed = max_outlier_percentage <= 0.05

            return QualityCheck(
                check_name="outliers",
                passed=passed,
                score=score,
                issues=issues,
                metadata={
                    'sample_size': len(values),
                    'z_score_outliers': len(outliers),
                    'iqr_outliers': len(iqr_outliers),
                    'z_score_outlier_percentage': outlier_percentage,
                    'iqr_outlier_percentage': iqr_outlier_percentage,
                    'mean': mean_val,
                    'std': std_val,
                    'sensitivity_used': sensitivity
                }
            )

        except Exception as e:
            return QualityCheck(
                check_name="outliers",
                passed=False,
                score=0.0,
                issues=[f"异常值检测异常: {str(e)}"]
            )

    def _check_staleness(self, data: List[Dict[str, Any]], data_type: str) -> QualityCheck:
        """检查数据新鲜度"""
        try:
            if not data:
                return QualityCheck(
                    check_name="staleness",
                    passed=False,
                    score=0.0,
                    issues=["没有数据可用于新鲜度检查"]
                )

            # 获取特定数据源的新鲜度阈值
            source_config = self.source_configs.get(data_type, {})
            staleness_threshold = source_config.get('staleness_threshold', self.thresholds.staleness_threshold)

            latest_timestamp = None
            for dp in data:
                timestamp = self._parse_timestamp(dp.get('timestamp'))
                if timestamp:
                    if latest_timestamp is None or timestamp > latest_timestamp:
                        latest_timestamp = timestamp

            if latest_timestamp is None:
                return QualityCheck(
                    check_name="staleness",
                    passed=False,
                    score=0.0,
                    issues=["无法解析任何时间戳"]
                )

            current_time = datetime.now()
            age_seconds = (current_time - latest_timestamp).total_seconds()
            is_stale = age_seconds > staleness_threshold

            # 新鲜度评分（线性衰减）
            freshness_score = max(0.0, 1.0 - (age_seconds / staleness_threshold))

            issues = []
            if is_stale:
                issues.append(f"数据过期: {age_seconds:.0f}秒前 (阈值: {staleness_threshold}秒)")

            return QualityCheck(
                check_name="staleness",
                passed=not is_stale,
                score=freshness_score,
                issues=issues,
                metadata={
                    'latest_timestamp': latest_timestamp.isoformat(),
                    'age_seconds': age_seconds,
                    'staleness_threshold': staleness_threshold,
                    'is_stale': is_stale
                }
            )

        except Exception as e:
            return QualityCheck(
                check_name="staleness",
                passed=False,
                score=0.0,
                issues=[f"新鲜度检查异常: {str(e)}"]
            )

    def _check_timestamp_consistency(self, data: List[Dict[str, Any]]) -> QualityCheck:
        """检查时间戳一致性"""
        try:
            if len(data) < 2:
                return QualityCheck(
                    check_name="timestamp_consistency",
                    passed=True,
                    score=1.0,
                    issues=["数据点不足，无法进行一致性检查"],
                    metadata={'sample_size': len(data)}
                )

            timestamps = []
            for dp in data:
                timestamp = self._parse_timestamp(dp.get('timestamp'))
                if timestamp:
                    timestamps.append(timestamp)

            if len(timestamps) < 2:
                return QualityCheck(
                    check_name="timestamp_consistency",
                    passed=False,
                    score=0.5,
                    issues=["有效时间戳不足"]
                )

            # 检查时间戳排序
            sorted_timestamps = sorted(timestamps)
            is_ordered = timestamps == sorted_timestamps

            # 检查时间戳间隔一致性
            intervals = []
            for i in range(1, len(sorted_timestamps)):
                interval = (sorted_timestamps[i] - sorted_timestamps[i-1]).total_seconds()
                intervals.append(interval)

            interval_consistency = 1.0
            if intervals:
                mean_interval = statistics.mean(intervals)
                std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
                if std_interval > 0:
                    cv = std_interval / mean_interval  # 变异系数
                    interval_consistency = max(0.0, 1.0 - cv)

            # 检查重复时间戳
            unique_timestamps = set(sorted_timestamps)
            duplicate_count = len(timestamps) - len(unique_timestamps)
            duplicate_percentage = duplicate_count / len(timestamps)

            # 综合评分
            order_score = 1.0 if is_ordered else 0.5
            consistency_score = interval_consistency
            duplicate_score = 1.0 - duplicate_percentage

            overall_score = (order_score * 0.4 + consistency_score * 0.3 + duplicate_score * 0.3)

            issues = []
            if not is_ordered:
                issues.append("时间戳未按时间顺序排列")
            if interval_consistency < 0.8:
                issues.append("时间戳间隔不一致")
            if duplicate_percentage > self.thresholds.duplicate_threshold:
                issues.append(f"重复时间戳过多: {duplicate_percentage:.2%}")

            passed = overall_score >= 0.8

            return QualityCheck(
                check_name="timestamp_consistency",
                passed=passed,
                score=overall_score,
                issues=issues,
                metadata={
                    'ordered_correctly': is_ordered,
                    'interval_consistency': interval_consistency,
                    'duplicate_percentage': duplicate_percentage,
                    'mean_interval': statistics.mean(intervals) if intervals else None,
                    'total_timestamps': len(timestamps),
                    'unique_timestamps': len(unique_timestamps)
                }
            )

        except Exception as e:
            return QualityCheck(
                check_name="timestamp_consistency",
                passed=False,
                score=0.0,
                issues=[f"时间戳一致性检查异常: {str(e)}"]
            )

    def _check_duplicates(self, data: List[Dict[str, Any]]) -> QualityCheck:
        """检查重复数据"""
        try:
            if len(data) < 2:
                return QualityCheck(
                    check_name="duplicates",
                    passed=True,
                    score=1.0,
                    metadata={'sample_size': len(data)}
                )

            # 创建数据点的哈希表示
            data_hashes = []
            for dp in data:
                # 使用关键字段创建哈希
                hash_components = [
                    str(dp.get('timestamp', '')),
                    str(dp.get('symbol', '')),
                    str(dp.get('source', '')),
                    str(dp.get('value', '')),
                    str(dp.get('data_type', ''))
                ]
                hash_str = '|'.join(hash_components)
                data_hashes.append(hash(hash_str))

            unique_hashes = set(data_hashes)
            duplicates = len(data_hashes) - len(unique_hashes)
            duplicate_percentage = duplicates / len(data_hashes)

            score = 1.0 - duplicate_percentage
            passed = duplicate_percentage <= self.thresholds.duplicate_threshold

            issues = []
            if duplicate_percentage > self.thresholds.duplicate_threshold:
                issues.append(f"重复数据过多: {duplicate_percentage:.2%}")

            return QualityCheck(
                check_name="duplicates",
                passed=passed,
                score=score,
                issues=issues,
                metadata={
                    'total_points': len(data),
                    'unique_points': len(unique_hashes),
                    'duplicates_found': duplicates,
                    'duplicate_percentage': duplicate_percentage
                }
            )

        except Exception as e:
            return QualityCheck(
                check_name="duplicates",
                passed=False,
                score=0.0,
                issues=[f"重复检查异常: {str(e)}"]
            )

    def _check_data_gaps(self, data: List[Dict[str, Any]]) -> QualityCheck:
        """检查数据间隙"""
        try:
            timestamps = []
            for dp in data:
                timestamp = self._parse_timestamp(dp.get('timestamp'))
                if timestamp:
                    timestamps.append(timestamp)

            if len(timestamps) < 2:
                return QualityCheck(
                    check_name="data_gaps",
                    passed=True,
                    score=1.0,
                    metadata={'sample_size': len(timestamps)}
                )

            # 排序时间戳
            timestamps.sort()

            # 检查时间间隙
            gaps = []
            for i in range(1, len(timestamps)):
                gap_seconds = (timestamps[i] - timestamps[i-1]).total_seconds()
                if gap_seconds > self.thresholds.gap_threshold:
                    gaps.append(gap_seconds)

            gap_count = len(gaps)
            gap_percentage = gap_count / (len(timestamps) - 1)

            # 评分（间隙越少分数越高）
            score = max(0.0, 1.0 - gap_percentage)
            passed = gap_count == 0

            issues = []
            if gap_count > 0:
                avg_gap = statistics.mean(gaps) if gaps else 0
                max_gap = max(gaps) if gaps else 0
                issues.append(f"发现{gap_count}个数据间隙，平均{avg_gap:.0f}秒，最大{max_gap:.0f}秒")

            return QualityCheck(
                check_name="data_gaps",
                passed=passed,
                score=score,
                issues=issues,
                metadata={
                    'gap_count': gap_count,
                    'gap_percentage': gap_percentage,
                    'avg_gap_seconds': statistics.mean(gaps) if gaps else None,
                    'max_gap_seconds': max(gaps) if gaps else None,
                    'gap_threshold': self.thresholds.gap_threshold
                }
            )

        except Exception as e:
            return QualityCheck(
                check_name="data_gaps",
                passed=False,
                score=0.0,
                issues=[f"数据间隙检查异常: {str(e)}"]
            )

    def _check_format_validity(self, data: List[Dict[str, Any]], data_type: str) -> QualityCheck:
        """检查格式有效性"""
        try:
            source_config = self.source_configs.get(data_type, {})
            expected_fields = source_config.get('expected_fields', [])

            valid_points = 0
            format_issues = []

            for dp in data:
                is_valid = True

                # 检查基础字段
                if not all(field in dp for field in ['timestamp', 'value']):
                    is_valid = False
                    format_issues.append("缺少基础字段")

                # 检查数据类型特定字段
                metadata = dp.get('metadata', {})
                for field in expected_fields:
                    if field not in metadata:
                        is_valid = False
                        format_issues.append(f"缺少{data_type}字段: {field}")

                # 检查数值格式
                value = dp.get('value')
                if value is not None:
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        is_valid = False
                        format_issues.append("数值格式无效")

                # 检查时间戳格式
                timestamp = dp.get('timestamp')
                if timestamp and not self._parse_timestamp(timestamp):
                    is_valid = False
                    format_issues.append("时间戳格式无效")

                if is_valid:
                    valid_points += 1

            validity_rate = valid_points / len(data) if data else 0
            score = validity_rate
            passed = validity_rate >= 0.95

            issues = []
            if validity_rate < 0.95:
                issues.append(f"格式有效率: {validity_rate:.2%} (要求: 95%)")

            return QualityCheck(
                check_name="format_validity",
                passed=passed,
                score=score,
                issues=issues,
                metadata={
                    'valid_points': valid_points,
                    'total_points': len(data),
                    'validity_rate': validity_rate,
                    'expected_fields': expected_fields,
                    'format_issues_count': len(set(format_issues))
                }
            )

        except Exception as e:
            return QualityCheck(
                check_name="format_validity",
                passed=False,
                score=0.0,
                issues=[f"格式有效性检查异常: {str(e)}"]
            )

    async def _check_abnormal_patterns(
        self,
        data: List[Dict[str, Any]],
        data_type: str
    ) -> QualityCheck:
        """检查异常模式"""
        try:
            values = []
            for dp in data:
                if self._is_valid_data_point(dp):
                    value = dp.get('value')
                    if value is not None:
                        try:
                            values.append(float(value))
                        except (ValueError, TypeError):
                            continue

            if len(values) < 20:
                return QualityCheck(
                    check_name="abnormal_patterns",
                    passed=True,
                    score=1.0,
                    issues=["数据点不足，无法进行异常模式检测"],
                    metadata={'sample_size': len(values)}
                )

            patterns_found = []

            # 检查连续相等值（可能是数据问题）
            consecutive_equal = 1
            max_consecutive_equal = 1
            for i in range(1, len(values)):
                if values[i] == values[i-1]:
                    consecutive_equal += 1
                    max_consecutive_equal = max(max_consecutive_equal, consecutive_equal)
                else:
                    consecutive_equal = 1

            if max_consecutive_equal > len(values) * 0.1:  # 超过10%的数据点相等
                patterns_found.append(f"连续相等值过多: {max_consecutive_equal}个")

            # 检查单调序列（不自然的趋势）
            increasing_count = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
            decreasing_count = sum(1 for i in range(1, len(values)) if values[i] < values[i-1])

            total_changes = len(values) - 1
            increasing_ratio = increasing_count / total_changes
            decreasing_ratio = decreasing_count / total_changes

            if increasing_ratio > 0.95:
                patterns_found.append(f"单调递增序列: {increasing_ratio:.2%}")
            elif decreasing_ratio > 0.95:
                patterns_found.append(f"单调递减序列: {decreasing_ratio:.2%}")

            # 检查异常波动
            if len(values) > 5:
                # 计算局部波动
                local_volatilities = []
                window = min(5, len(values) // 4)
                for i in range(window, len(values) - window):
                    local_values = values[i-window:i+window+1]
                    if len(local_values) > 1:
                        local_vol = np.std(local_values) / np.mean(local_values) if np.mean(local_values) != 0 else 0
                        local_volatilities.append(local_vol)

                if local_volatilities:
                    avg_vol = np.mean(local_volatilities)
                    if avg_vol > 0.5:  # 高波动阈值
                        patterns_found.append(f"异常高波动: 平均CV = {avg_vol:.3f}")

            # 评分
            pattern_penalty = len(patterns_found) * 0.2
            score = max(0.0, 1.0 - pattern_penalty)
            passed = len(patterns_found) == 0

            return QualityCheck(
                check_name="abnormal_patterns",
                passed=passed,
                score=score,
                issues=patterns_found,
                metadata={
                    'patterns_found': len(patterns_found),
                    'max_consecutive_equal': max_consecutive_equal,
                    'increasing_ratio': increasing_ratio,
                    'decreasing_ratio': decreasing_ratio,
                    'local_volatilities': len(local_volatilities) if 'local_volatilities' in locals() else 0
                }
            )

        except Exception as e:
            return QualityCheck(
                check_name="abnormal_patterns",
                passed=False,
                score=0.0,
                issues=[f"异常模式检测异常: {str(e)}"]
            )

    def _calculate_overall_score(self, checks: Dict[str, QualityCheck]) -> float:
        """计算综合质量评分"""
        if not checks:
            return 0.0

        # 权重配置
        weights = {
            'completeness': 0.25,
            'outliers': 0.20,
            'staleness': 0.15,
            'timestamp_consistency': 0.15,
            'duplicates': 0.10,
            'data_gaps': 0.10,
            'format_validity': 0.05
        }

        weighted_score = 0.0
        total_weight = 0.0

        for check_name, check in checks.items():
            weight = weights.get(check_name, 0.05)
            weighted_score += check.score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _get_quality_level(self, score: float) -> QualityLevel:
        """根据评分获取质量等级"""
        if score >= 0.95:
            return QualityLevel.EXCELLENT
        elif score >= 0.85:
            return QualityLevel.GOOD
        elif score >= 0.70:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.50:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE

    def _generate_recommendations(
        self,
        checks: Dict[str, QualityCheck],
        data_type: str
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []

        for check_name, check in checks.items():
            if not check.passed:
                if check_name == 'completeness':
                    recommendations.append(
                        f"提高{data_type}数据完整性 - 当前完整率: {check.score:.2%}"
                    )
                elif check_name == 'outliers':
                    recommendations.append(
                        f"实施{data_type}数据异常值检测和处理机制"
                    )
                elif check_name == 'staleness':
                    recommendations.append(
                        f"增加{data_type}数据更新频率 - 数据可能过期"
                    )
                elif check_name == 'timestamp_consistency':
                    recommendations.append(
                        f"修复{data_type}数据时间戳一致性问题"
                    )
                elif check_name == 'duplicates':
                    recommendations.append(
                        f"实施{data_type}数据去重机制"
                    )
                elif check_name == 'data_gaps':
                    recommendations.append(
                        f"检查{data_type}数据采集源，减少数据间隙"
                    )
                elif check_name == 'format_validity':
                    recommendations.append(
                        f"标准化{data_type}数据格式和字段结构"
                    )
                elif check_name == 'abnormal_patterns':
                    recommendations.append(
                        f"调查{data_type}数据中的异常模式，可能表示数据问题"
                    )

        # 通用建议
        if recommendations:
            recommendations.append("建立实时数据质量监控和告警系统")
            recommendations.append("实施数据源健康检查和故障转移机制")

        return recommendations

    async def _log_quality_issues(self, result: QualityResult) -> None:
        """记录质量问题"""
        try:
            logger.warning(
                f"数据质量问题 - {result.data_type}:{result.symbol} "
                f"评分: {result.overall_score:.3f} ({result.quality_level.name}) "
                f"建议: {len(result.recommendations)}项"
            )

            # 详细记录每个失败的检查
            for check_name, check in result.checks.items():
                if not check.passed:
                    logger.debug(
                        f"质量检查失败 - {check_name}: "
                        f"评分: {check.score:.3f}, 问题: {check.issues}"
                    )

        except Exception as e:
            logger.error(f"记录质量问题失败: {e}")

    def _is_valid_data_point(self, data_point: Dict[str, Any]) -> bool:
        """检查数据点是否有效"""
        try:
            # 检查必需字段
            if not all(field in data_point for field in ['timestamp', 'value']):
                return False

            # 检查数值
            value = data_point.get('value')
            if value is None:
                return False

            try:
                float_value = float(value)
                if not np.isfinite(float_value):
                    return False
            except (ValueError, TypeError):
                return False

            # 检查时间戳
            timestamp = self._parse_timestamp(data_point.get('timestamp'))
            if timestamp is None:
                return False

            return True

        except Exception:
            return False

    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """解析时间戳"""
        if timestamp is None:
            return None

        try:
            if isinstance(timestamp, datetime):
                return timestamp
            elif isinstance(timestamp, str):
                # 尝试多种时间格式
                formats = [
                    '%Y-%m-%dT%H:%M:%S.%fZ',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%d'
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue
                return None
            else:
                return None

        except Exception:
            return None

# 创建全局数据质量验证器实例
data_quality_validator = DataQualityValidator()

# 导出主要类和实例
__all__ = [
    'DataQualityValidator',
    'data_quality_validator',
    'QualityResult',
    'QualityCheck',
    'QualityLevel',
    'QualityIssue',
    'QualityThresholds'
]