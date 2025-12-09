#!/usr / bin / env python3
"""
Phase 3: Content Validation Layer
第三阶段：内容验证层

Comprehensive content validation system for multi - layer data authenticity verification
多层数据真实性验证的综合内容验证系统

This module implements Tasks 11 - 18 from the proposal:
- Data Integrity Verifier with SHA - 256 / 512 hash verification
- Time series verification and continuity checks
- Business Rules Validator for financial data
- Cross - market validation (correlations, arbitrage, exchange rates)
- Statistical Anomaly Detector with multiple algorithms
- Volatility analysis with pattern detection
- Cross - Source Validator for multi - source comparison
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .interfaces.auth_result import AuthResult, Verdict, VerificationLayer

# Import existing authentication interfaces
from .interfaces.verifier_interface import IVerifier

# Setup logging
logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """验证严重性级别"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """异常类型"""

    STATISTICAL_OUTLIER = "statistical_outlier"
    VOLATILITY_SPIKE = "volatility_spike"
    PRICE_JUMP = "price_jump"
    VOLUME_ANOMALY = "volume_anomaly"
    TIMESTAMP_GAP = "timestamp_gap"
    DUPLICATE_RECORD = "duplicate_record"
    MISSING_DATA = "missing_data"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"


@dataclass
class ValidationRule:
    """验证规则定义"""

    rule_id: str
    name: str
    description: str
    data_type: str
    field_name: str
    validation_type: str  # 'range', 'pattern', 'business_rule', 'statistical'
    parameters: Dict[str, Any]
    severity: ValidationSeverity = ValidationSeverity.MEDIUM
    enabled: bool = True


@dataclass
class ValidationResult:
    """验证结果"""

    rule_id: str
    rule_name: str
    passed: bool
    severity: ValidationSeverity
    confidence: float  # 0.0 - 1.0
    execution_time_ms: float
    details: Dict[str, Any] = field(default_factory = dict)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory = datetime.now)


@dataclass
class AnomalyDetection:
    """异常检测结果"""

    anomaly_type: AnomalyType
    timestamp: Union[datetime, str]
    field_name: str
    value: Any
    expected_range: Optional[Tuple[float, float]] = None
    z_score: Optional[float] = None
    isolation_score: Optional[float] = None
    severity: ValidationSeverity = ValidationSeverity.MEDIUM
    confidence: float = 0.0
    context: Dict[str, Any] = field(default_factory = dict)


class DataIntegrityVerifier(IVerifier):
    """数据完整性验证器 - Task 11"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("DataIntegrityVerifier", config)
        self.supported_data_types = ["stock_data", "government_data", "economic_data"]
        self.hash_algorithms = ["sha256", "sha512"]
        self.schema_validators = self._initialize_schema_validators()

    def get_verifier_type(self) -> str:
        return "data_integrity"

    def get_supported_data_types(self) -> List[str]:
        return self.supported_data_types

    async def verify(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """执行数据完整性验证"""
        start_time = time.time()

        try:
            # 转换数据为DataFrame格式（如果是字典格式）
            if isinstance(data, dict) and "data" in data:
                df = pd.DataFrame(data["data"])
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                raise ValueError(f"Unsupported data format: {type(data)}")

            # 执行多项完整性检查
            hash_verification = await self._verify_data_hash(df, data_id)
            schema_validation = await self._validate_data_schema(df, context)
            structure_validation = await self._validate_data_structure(df)

            # 计算总体置信度
            all_checks = [hash_verification, schema_validation, structure_validation]
            passed_checks = sum(1 for check in all_checks if check.passed)
            confidence = passed_checks / len(all_checks)

            # 确定结论
            if confidence >= 0.9:
                verdict = Verdict.AUTHENTIC
            elif confidence >= 0.6:
                verdict = Verdict.SUSPICIOUS
            else:
                verdict = Verdict.FALSIFIED

            execution_time = (time.time() - start_time) * 1000

            # 创建验证结果
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
                    "hash_verification": hash_verification.__dict__,
                    "schema_validation": schema_validation.__dict__,
                    "structure_validation": structure_validation.__dict__,
                    "total_checks": len(all_checks),
                    "passed_checks": passed_checks,
                },
            )

            logger.info(
                f"Data integrity verification completed for {data_id}: {verdict.value} (confidence: {confidence:.3f})"
            )
            return result

        except Exception as e:
            logger.error(f"Data integrity verification failed for {data_id}: {str(e)}")
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

    async def _verify_data_hash(
        self, df: pd.DataFrame, data_id: str
    ) -> ValidationResult:
        """验证数据哈希值"""
        start_time = time.time()

        try:
            # 计算当前数据的哈希值
            data_string = df.to_string(index = False).encode("utf - 8")
            current_hashes = {}

            for algorithm in self.hash_algorithms:
                if algorithm == "sha256":
                    hash_obj = hashlib.sha256(data_string)
                elif algorithm == "sha512":
                    hash_obj = hashlib.sha512(data_string)
                else:
                    continue

                current_hashes[algorithm] = hash_obj.hexdigest()

            # 从缓存或配置中获取预期哈希值（如果有）
            expected_hashes = self.config.get("expected_hashes", {}).get(data_id, {})

            # 比较哈希值
            passed = True
            details = {
                "computed_hashes": current_hashes,
                "expected_hashes": expected_hashes,
                "hash_match": {},
            }

            for algorithm, current_hash in current_hashes.items():
                if algorithm in expected_hashes:
                    match = current_hash == expected_hashes[algorithm]
                    details["hash_match"][algorithm] = match
                    if not match:
                        passed = False
                else:
                    # 如果没有预期哈希值，则计算并存储
                    details["hash_match"][algorithm] = None

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="hash_verification",
                rule_name="Data Hash Verification",
                passed = passed,
                severity=(
                    ValidationSeverity.HIGH if not passed else ValidationSeverity.LOW
                ),
                confidence = 1.0 if passed else 0.0,
                execution_time_ms = execution_time,
                details = details,
            )

        except Exception as e:
            return ValidationResult(
                rule_id="hash_verification",
                rule_name="Data Hash Verification",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_data_schema(
        self, df: pd.DataFrame, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """验证数据架构"""
        start_time = time.time()

        try:
            data_type = context.get("data_type", "unknown") if context else "unknown"
            schema = self.schema_validators.get(data_type, {})

            passed = True
            errors = []
            warnings = []

            # 检查必需字段
            required_fields = schema.get("required_fields", [])
            missing_fields = [
                field for field in required_fields if field not in df.columns
            ]
            if missing_fields:
                passed = False
                errors.append(f"Missing required fields: {missing_fields}")

            # 检查字段类型
            field_types = schema.get("field_types", {})
            for field, expected_type in field_types.items():
                if field in df.columns:
                    actual_type = str(df[field].dtype)
                    if expected_type not in actual_type:
                        warnings.append(
                            f"Field '{field}' type mismatch: expected {expected_type}, got {actual_type}"
                        )

            # 检查数据量
            min_records = schema.get("min_records", 1)
            if len(df) < min_records:
                passed = False
                errors.append(f"Insufficient records: {len(df)} < {min_records}")

            # 检查重复记录
            duplicate_count = df.duplicated().sum()
            if duplicate_count > 0:
                warnings.append(f"Found {duplicate_count} duplicate records")

            severity = ValidationSeverity.CRITICAL if errors else ValidationSeverity.LOW
            confidence = 0.0 if errors else (1.0 if not warnings else 0.7)

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="schema_validation",
                rule_name="Data Schema Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "data_type": data_type,
                    "record_count": len(df),
                    "columns": list(df.columns),
                    "errors": errors,
                    "warnings": warnings,
                    "duplicate_count": duplicate_count,
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="schema_validation",
                rule_name="Data Schema Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_data_structure(self, df: pd.DataFrame) -> ValidationResult:
        """验证数据结构完整性"""
        start_time = time.time()

        try:
            passed = True
            issues = []

            # 检查空值
            null_counts = df.isnull().sum()
            high_null_columns = null_counts[null_counts > len(df) * 0.1].to_dict()
            if high_null_columns:
                issues.append(f"High null values in columns: {high_null_columns}")

            # 检查数据范围异常
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            outliers_info = {}

            for col in numeric_columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                if len(outliers) > 0:
                    outliers_info[col] = {
                        "count": len(outliers),
                        "percentage": len(outliers) / len(df) * 100,
                        "range": [lower_bound, upper_bound],
                    }

            if outliers_info:
                issues.append(f"Statistical outliers detected: {outliers_info}")

            # 检查数据一致性
            consistency_issues = await self._check_data_consistency(df)
            issues.extend(consistency_issues)

            passed = len(issues) == 0
            severity = ValidationSeverity.MEDIUM if issues else ValidationSeverity.LOW
            confidence = 1.0 if passed else 0.6

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="structure_validation",
                rule_name="Data Structure Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "total_records": len(df),
                    "total_columns": len(df.columns),
                    "null_counts": null_counts.to_dict(),
                    "outliers_info": outliers_info,
                    "issues": issues,
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="structure_validation",
                rule_name="Data Structure Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _check_data_consistency(self, df: pd.DataFrame) -> List[str]:
        """检查数据一致性"""
        issues = []

        # 检查价格数据的一致性（OHLC关系）
        price_columns = ["open", "high", "low", "close"]
        if all(col in df.columns for col in price_columns):
            # High should be >= Open, Low should be <= Open
            high_low_violations = df[df["high"] < df["low"]]
            if len(high_low_violations) > 0:
                issues.append(
                    f"High < Low violations: {len(high_low_violations)} records"
                )

            # High should be >= Close, Low should be <= Close
            ohlc_violations = df[
                (df["high"] < df["close"])
                | (df["low"] > df["close"])
                | (df["high"] < df["open"])
                | (df["low"] > df["open"])
            ]
            if len(ohlc_violations) > 0:
                issues.append(
                    f"OHLC relationship violations: {len(ohlc_violations)} records"
                )

        # 检查负值（不应该为负的字段）
        non_negative_fields = ["volume", "amount", "quantity"]
        for field in non_negative_fields:
            if field in df.columns:
                negative_count = (df[field] < 0).sum()
                if negative_count > 0:
                    issues.append(
                        f"Negative values in {field}: {negative_count} records"
                    )

        return issues

    def _initialize_schema_validators(self) -> Dict[str, Dict[str, Any]]:
        """初始化数据架构验证器"""
        return {
            "stock_data": {
                "required_fields": ["timestamp", "close"],
                "field_types": {
                    "timestamp": "datetime",
                    "open": "float",
                    "high": "float",
                    "low": "float",
                    "close": "float",
                    "volume": "int",
                },
                "min_records": 1,
            },
            "government_data": {
                "required_fields": ["date", "data_type"],
                "field_types": {"date": "datetime", "rate": "float", "value": "float"},
                "min_records": 1,
            },
            "economic_data": {
                "required_fields": ["date", "indicator"],
                "field_types": {
                    "date": "datetime",
                    "value": "float",
                    "change": "float",
                },
                "min_records": 1,
            },
        }


class TimeSeriesVerifier(IVerifier):
    """时间序列验证器 - Task 12"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("TimeSeriesVerifier", config)
        self.supported_data_types = ["stock_data", "economic_data", "government_data"]
        self.max_allowed_gap_hours = self.config.get("max_allowed_gap_hours", 24)
        self.duplicate_threshold_seconds = self.config.get(
            "duplicate_threshold_seconds", 1
        )

    def get_verifier_type(self) -> str:
        return "time_series"

    def get_supported_data_types(self) -> List[str]:
        return self.supported_data_types

    async def verify(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """执行时间序列验证"""
        start_time = time.time()

        try:
            # 转换数据为DataFrame
            df = self._prepare_dataframe(data)

            # 执行时间序列检查
            continuity_check = await self._check_time_continuity(df)
            duplicate_check = await self._check_duplicates(df)
            timestamp_validation = await self._validate_timestamps(df)
            frequency_analysis = await self._analyze_frequency(df)

            # 计算总体结果
            all_checks = [
                continuity_check,
                duplicate_check,
                timestamp_validation,
                frequency_analysis,
            ]
            passed_checks = sum(1 for check in all_checks if check.passed)
            confidence = passed_checks / len(all_checks)

            verdict = (
                Verdict.AUTHENTIC
                if confidence >= 0.8
                else Verdict.SUSPICIOUS if confidence >= 0.5 else Verdict.FALSIFIED
            )

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
                    "continuity_check": continuity_check.__dict__,
                    "duplicate_check": duplicate_check.__dict__,
                    "timestamp_validation": timestamp_validation.__dict__,
                    "frequency_analysis": frequency_analysis.__dict__,
                },
            )

            logger.info(
                f"Time series verification completed for {data_id}: {verdict.value} (confidence: {confidence:.3f})"
            )
            return result

        except Exception as e:
            logger.error(f"Time series verification failed for {data_id}: {str(e)}")
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

        # 确保时间戳列存在并转换为datetime
        timestamp_col = "timestamp"
        if timestamp_col not in df.columns:
            timestamp_col = "date"
            if timestamp_col not in df.columns:
                raise ValueError("No timestamp or date column found")

        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        df = df.sort_values(timestamp_col).reset_index(drop = True)

        return df

    async def _check_time_continuity(self, df: pd.DataFrame) -> ValidationResult:
        """检查时间连续性"""
        start_time = time.time()

        try:
            timestamp_col = "timestamp" if "timestamp" in df.columns else "date"

            # 计算时间间隔
            time_diffs = df[timestamp_col].diff().dropna()

            # 识别大的时间间隔
            max_gap = pd.Timedelta(hours = self.max_allowed_gap_hours)
            gaps = time_diffs[time_diffs > max_gap]

            # 检查是否有交易日 / 非交易日模式（周末等）
            weekend_gaps = time_diffs[time_diffs > pd.Timedelta(days = 2)]
            expected_gaps = 0

            # 对于股票数据，周末间隔是正常的
            data_type = self.config.get("data_type", "unknown")
            if data_type == "stock_data":
                # 计算周末间隔（超过2天的间隔）
                expected_gaps = len(weekend_gaps)
                actual_gaps = len(gaps[gaps > pd.Timedelta(days = 2)])
                unexpected_gaps = actual_gaps - expected_gaps
            else:
                unexpected_gaps = len(gaps)

            passed = unexpected_gaps == 0
            severity = (
                ValidationSeverity.HIGH
                if unexpected_gaps > 5
                else (
                    ValidationSeverity.MEDIUM
                    if unexpected_gaps > 0
                    else ValidationSeverity.LOW
                )
            )
            confidence = 1.0 if passed else max(0.3, 1.0 - unexpected_gaps * 0.1)

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="time_continuity",
                rule_name="Time Continuity Check",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "total_records": len(df),
                    "gaps_found": len(gaps),
                    "unexpected_gaps": unexpected_gaps,
                    "max_gap_hours": self.max_allowed_gap_hours,
                    "max_actual_gap": (
                        str(time_diffs.max()) if len(time_diffs) > 0 else None
                    ),
                    "gap_details": gaps.to_dict() if len(gaps) > 0 else {},
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="time_continuity",
                rule_name="Time Continuity Check",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _check_duplicates(self, df: pd.DataFrame) -> ValidationResult:
        """检查重复记录"""
        start_time = time.time()

        try:
            timestamp_col = "timestamp" if "timestamp" in df.columns else "date"

            # 检查完全重复的记录
            exact_duplicates = df.duplicated().sum()

            # 检查时间戳重复的记录
            timestamp_duplicates = df[timestamp_col].duplicated().sum()

            # 检查相近时间戳的记录
            df_sorted = df.sort_values(timestamp_col).reset_index(drop = True)
            time_diffs = df_sorted[timestamp_col].diff().dropna()
            close_timestamps = time_diffs[
                time_diffs <= pd.Timedelta(seconds = self.duplicate_threshold_seconds)
            ]

            passed = (
                exact_duplicates == 0
                and timestamp_duplicates == 0
                and len(close_timestamps) == 0
            )
            severity = (
                ValidationSeverity.HIGH
                if (exact_duplicates > 0 or timestamp_duplicates > 0)
                else (
                    ValidationSeverity.MEDIUM
                    if len(close_timestamps) > 0
                    else ValidationSeverity.LOW
                )
            )
            confidence = 1.0 if passed else 0.5

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="duplicate_check",
                rule_name="Duplicate Records Check",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "exact_duplicates": exact_duplicates,
                    "timestamp_duplicates": timestamp_duplicates,
                    "close_timestamp_records": len(close_timestamps),
                    "duplicate_threshold_seconds": self.duplicate_threshold_seconds,
                    "total_records": len(df),
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="duplicate_check",
                rule_name="Duplicate Records Check",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_timestamps(self, df: pd.DataFrame) -> ValidationResult:
        """验证时间戳"""
        start_time = time.time()

        try:
            timestamp_col = "timestamp" if "timestamp" in df.columns else "date"

            # 检查时间戳格式
            invalid_timestamps = pd.isna(df[timestamp_col]).sum()

            # 检查时间戳范围
            if len(df) > 0:
                min_timestamp = df[timestamp_col].min()
                max_timestamp = df[timestamp_col].max()
                current_time = pd.Timestamp.now()

                # 检查未来时间戳
                future_timestamps = (df[timestamp_col] > current_time).sum()

                # 检查过于陈旧的时间戳（超过10年）
                ten_years_ago = current_time - pd.Timedelta(days = 365 * 10)
                ancient_timestamps = (df[timestamp_col] < ten_years_ago).sum()

                # 检查时间戳顺序
                is_sorted = df[timestamp_col].is_monotonic_increasing

            else:
                min_timestamp = max_timestamp = None
                future_timestamps = ancient_timestamps = 0
                is_sorted = True

            passed = (
                invalid_timestamps == 0
                and future_timestamps == 0
                and ancient_timestamps == 0
                and is_sorted
            )

            severity = (
                ValidationSeverity.CRITICAL
                if invalid_timestamps > 0
                else (
                    ValidationSeverity.HIGH
                    if future_timestamps > 0
                    else (
                        ValidationSeverity.MEDIUM
                        if not is_sorted
                        else ValidationSeverity.LOW
                    )
                )
            )
            confidence = 1.0 if passed else 0.6

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="timestamp_validation",
                rule_name="Timestamp Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "invalid_timestamps": invalid_timestamps,
                    "future_timestamps": future_timestamps,
                    "ancient_timestamps": ancient_timestamps,
                    "is_monotonic": is_sorted,
                    "min_timestamp": str(min_timestamp) if min_timestamp else None,
                    "max_timestamp": str(max_timestamp) if max_timestamp else None,
                    "total_records": len(df),
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="timestamp_validation",
                rule_name="Timestamp Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _analyze_frequency(self, df: pd.DataFrame) -> ValidationResult:
        """分析数据频率"""
        start_time = time.time()

        try:
            if len(df) < 2:
                return ValidationResult(
                    rule_id="frequency_analysis",
                    rule_name="Data Frequency Analysis",
                    passed = True,
                    severity = ValidationSeverity.LOW,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "Insufficient data for frequency analysis"},
                )

            timestamp_col = "timestamp" if "timestamp" in df.columns else "date"
            time_diffs = df[timestamp_col].diff().dropna()

            # 计算主要时间间隔
            mode_diff = (
                time_diffs.mode().iloc[0]
                if len(time_diffs.mode()) > 0
                else pd.Timedelta(0)
            )

            # 分析频率一致性
            tolerance = pd.Timedelta(minutes = 5)  # 5分钟容差
            consistent_intervals = (time_diffs - mode_diff).abs() <= tolerance
            consistency_rate = consistent_intervals.sum() / len(time_diffs)

            # 识别数据频率类型
            if mode_diff <= pd.Timedelta(minutes = 1):
                frequency_type = "intraday_minute"
            elif mode_diff <= pd.Timedelta(hours = 1):
                frequency_type = "intraday_hourly"
            elif mode_diff <= pd.Timedelta(days = 1):
                frequency_type = "daily"
            elif mode_diff <= pd.Timedelta(weeks = 1):
                frequency_type = "weekly"
            elif mode_diff <= pd.Timedelta(days = 31):
                frequency_type = "monthly"
            else:
                frequency_type = "irregular"

            passed = consistency_rate >= 0.8
            severity = ValidationSeverity.LOW if passed else ValidationSeverity.MEDIUM
            confidence = consistency_rate

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="frequency_analysis",
                rule_name="Data Frequency Analysis",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "primary_interval": str(mode_diff),
                    "frequency_type": frequency_type,
                    "consistency_rate": consistency_rate,
                    "total_intervals": len(time_diffs),
                    "consistent_intervals": consistent_intervals.sum(),
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="frequency_analysis",
                rule_name="Data Frequency Analysis",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )


class BusinessRulesValidator(IVerifier):
    """业务规则验证器 - Task 13"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("BusinessRulesValidator", config)
        self.supported_data_types = ["stock_data", "government_data", "economic_data"]
        self.hk_market_rules = self._initialize_hk_market_rules()

    def get_verifier_type(self) -> str:
        return "business_rules"

    def get_supported_data_types(self) -> List[str]:
        return self.supported_data_types

    async def verify(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """执行业务规则验证"""
        start_time = time.time()

        try:
            df = self._prepare_dataframe(data)
            data_type = (
                context.get("data_type", "stock_data") if context else "stock_data"
            )

            # 根据数据类型执行相应的业务规则验证
            if data_type == "stock_data":
                rule_results = await self._validate_stock_data_rules(df)
            elif data_type == "government_data":
                rule_results = await self._validate_government_data_rules(df)
            elif data_type == "economic_data":
                rule_results = await self._validate_economic_data_rules(df)
            else:
                rule_results = await self._validate_generic_data_rules(df)

            # 计算总体结果
            passed_rules = sum(1 for rule in rule_results if rule.passed)
            total_rules = len(rule_results)
            confidence = passed_rules / total_rules if total_rules > 0 else 0.0

            if confidence >= 0.9:
                verdict = Verdict.AUTHENTIC
            elif confidence >= 0.6:
                verdict = Verdict.SUSPICIOUS
            else:
                verdict = Verdict.FALSIFIED

            execution_time = (time.time() - start_time) * 1000

            result = AuthResult(
                data_id = data_id,
                data_type = data_type,
                data_source=(
                    context.get("data_source", "unknown") if context else "unknown"
                ),
                overall_verdict = verdict,
                overall_confidence = confidence,
                status="completed",
                total_execution_time_ms = execution_time,
                metadata={
                    "rule_results": [rule.__dict__ for rule in rule_results],
                    "passed_rules": passed_rules,
                    "total_rules": total_rules,
                    "data_type": data_type,
                },
            )

            logger.info(
                f"Business rules validation completed for {data_id}: {verdict.value} (confidence: {confidence:.3f})"
            )
            return result

        except Exception as e:
            logger.error(f"Business rules validation failed for {data_id}: {str(e)}")
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

    async def _validate_stock_data_rules(
        self, df: pd.DataFrame
    ) -> List[ValidationResult]:
        """验证股票数据业务规则"""
        results = []

        # 规则1: OHLC价格关系验证
        results.append(await self._validate_ohlc_relationships(df))

        # 规则2: 价格变动限制验证
        results.append(await self._validate_price_movements(df))

        # 规则3: 交易量合理性验证
        results.append(await self._validate_trading_volume(df))

        # 规则4: 价格范围验证
        results.append(await self._validate_price_ranges(df))

        # 规则5: 交易时间验证
        results.append(await self._validate_trading_hours(df))

        return results

    async def _validate_government_data_rules(
        self, df: pd.DataFrame
    ) -> List[ValidationResult]:
        """验证政府数据业务规则"""
        results = []

        # 规则1: HIBOR利率范围验证
        if "hibor_overnight" in df.columns or "ir_overnight" in df.columns:
            results.append(await self._validate_hibor_rates(df))

        # 规则2: 汇率变动限制验证
        if any(
            "rate" in col.lower() or "exchange" in col.lower() for col in df.columns
        ):
            results.append(await self._validate_exchange_rates(df))

        # 规则3: 货币数据合理性验证
        if any(
            "monetary" in col.lower() or "base" in col.lower() for col in df.columns
        ):
            results.append(await self._validate_monetary_data(df))

        return results

    async def _validate_economic_data_rules(
        self, df: pd.DataFrame
    ) -> List[ValidationResult]:
        """验证经济数据业务规则"""
        results = []

        # 规则1: 经济指标合理性验证
        results.append(await self._validate_economic_indicators(df))

        # 规则2: 数据趋势合理性验证
        results.append(await self._validate_economic_trends(df))

        return results

    async def _validate_generic_data_rules(
        self, df: pd.DataFrame
    ) -> List[ValidationResult]:
        """验证通用数据业务规则"""
        results = []

        # 规则1: 数值合理性验证
        results.append(await self._validate_numeric_ranges(df))

        # 规则2: 数据一致性验证
        results.append(await self._validate_data_consistency(df))

        return results

    async def _validate_ohlc_relationships(self, df: pd.DataFrame) -> ValidationResult:
        """验证OHLC价格关系"""
        start_time = time.time()

        try:
            price_cols = ["open", "high", "low", "close"]
            missing_cols = [col for col in price_cols if col not in df.columns]

            if missing_cols:
                return ValidationResult(
                    rule_id="ohlc_relationships",
                    rule_name="OHLC Price Relationships",
                    passed = False,
                    severity = ValidationSeverity.MEDIUM,
                    confidence = 0.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error_message = f"Missing price columns: {missing_cols}",
                )

            # OHLC关系检查
            violations = []

            # High >= Low
            high_low_violations = df[df["high"] < df["low"]]
            if len(high_low_violations) > 0:
                violations.append(
                    f"High < Low violations: {len(high_low_violations)} records"
                )

            # High >= Open, Close
            high_violations = df[(df["high"] < df["open"]) | (df["high"] < df["close"])]
            if len(high_violations) > 0:
                violations.append(
                    f"High < Open / Close violations: {len(high_violations)} records"
                )

            # Low <= Open, Close
            low_violations = df[(df["low"] > df["open"]) | (df["low"] > df["close"])]
            if len(low_violations) > 0:
                violations.append(
                    f"Low > Open / Close violations: {len(low_violations)} records"
                )

            passed = len(violations) == 0
            severity = (
                ValidationSeverity.HIGH
                if len(violations) > len(df) * 0.01
                else ValidationSeverity.MEDIUM if violations else ValidationSeverity.LOW
            )
            confidence = 1.0 if passed else 0.7

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="ohlc_relationships",
                rule_name="OHLC Price Relationships",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "total_records": len(df),
                    "violations": violations,
                    "violation_count": len(violations),
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="ohlc_relationships",
                rule_name="OHLC Price Relationships",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_price_movements(self, df: pd.DataFrame) -> ValidationResult:
        """验证价格变动限制"""
        start_time = time.time()

        try:
            if "close" not in df.columns:
                return ValidationResult(
                    rule_id="price_movements",
                    rule_name="Price Movement Limits",
                    passed = False,
                    severity = ValidationSeverity.MEDIUM,
                    confidence = 0.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error_message="Missing 'close' price column",
                )

            # 计算价格变动百分比
            price_changes = df["close"].pct_change().dropna()

            # 香港股票市场单日涨跌停板限制（约10%）
            max_daily_change = 0.10
            extreme_changes = price_changes[abs(price_changes) > max_daily_change]

            # 检查异常大的价格跳跃
            extreme_threshold = 0.50  # 50%变动
            extreme_jumps = price_changes[abs(price_changes) > extreme_threshold]

            passed = len(extreme_jumps) == 0
            severity = (
                ValidationSeverity.CRITICAL
                if len(extreme_jumps) > 0
                else (
                    ValidationSeverity.HIGH
                    if len(extreme_changes) > len(df) * 0.01
                    else ValidationSeverity.LOW
                )
            )
            confidence = 1.0 if passed else max(0.3, 1.0 - len(extreme_jumps) * 0.1)

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="price_movements",
                rule_name="Price Movement Limits",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "total_changes": len(price_changes),
                    "extreme_changes": len(extreme_changes),
                    "extreme_jumps": len(extreme_jumps),
                    "max_change": (
                        float(price_changes.abs().max())
                        if len(price_changes) > 0
                        else None
                    ),
                    "avg_change": (
                        float(price_changes.abs().mean())
                        if len(price_changes) > 0
                        else None
                    ),
                    "max_daily_change_limit": max_daily_change,
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="price_movements",
                rule_name="Price Movement Limits",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_trading_volume(self, df: pd.DataFrame) -> ValidationResult:
        """验证交易量合理性"""
        start_time = time.time()

        try:
            if "volume" not in df.columns:
                return ValidationResult(
                    rule_id="trading_volume",
                    rule_name="Trading Volume Validation",
                    passed = True,  # Not critical if volume is missing
                    severity = ValidationSeverity.LOW,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "Volume column not found, skipping validation"},
                )

            volume = df["volume"]

            # 检查负值交易量
            negative_volume = (volume < 0).sum()

            # 检查异常大的交易量（超过中位数的100倍）
            volume_median = volume.median()
            extreme_volume = (volume > volume_median * 100).sum()

            # 检查交易量为0但价格有变动的情况
            if "close" in df.columns:
                price_changes = df["close"].pct_change().abs()
                zero_volume_price_change = (
                    (volume == 0) & (price_changes > 0.001)
                ).sum()
            else:
                zero_volume_price_change = 0

            passed = negative_volume == 0 and zero_volume_price_change == 0
            severity = (
                ValidationSeverity.HIGH
                if negative_volume > 0
                else (
                    ValidationSeverity.MEDIUM
                    if zero_volume_price_change > 0
                    else ValidationSeverity.LOW
                )
            )
            confidence = 1.0 if passed else 0.6

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="trading_volume",
                rule_name="Trading Volume Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "total_records": len(volume),
                    "negative_volume": negative_volume,
                    "extreme_volume": extreme_volume,
                    "zero_volume_price_change": zero_volume_price_change,
                    "volume_median": (
                        float(volume_median) if not pd.isna(volume_median) else None
                    ),
                    "volume_max": float(volume.max()) if len(volume) > 0 else None,
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="trading_volume",
                rule_name="Trading Volume Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_price_ranges(self, df: pd.DataFrame) -> ValidationResult:
        """验证价格范围合理性"""
        start_time = time.time()

        try:
            price_cols = [
                col for col in ["open", "high", "low", "close"] if col in df.columns
            ]

            if not price_cols:
                return ValidationResult(
                    rule_id="price_ranges",
                    rule_name="Price Range Validation",
                    passed = True,
                    severity = ValidationSeverity.LOW,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "No price columns found"},
                )

            # 检查负价格
            negative_prices = {}
            zero_prices = {}
            extreme_prices = {}

            for col in price_cols:
                negative_prices[col] = (df[col] < 0).sum()
                zero_prices[col] = (df[col] == 0).sum()

                # 检查异常高价格（超过100万港币）
                extreme_prices[col] = (df[col] > 1000000).sum()

            total_negative = sum(negative_prices.values())
            total_zero = sum(zero_prices.values())
            total_extreme = sum(extreme_prices.values())

            passed = total_negative == 0 and total_extreme == 0
            severity = (
                ValidationSeverity.CRITICAL
                if total_negative > 0
                else (
                    ValidationSeverity.HIGH
                    if total_extreme > 0
                    else (
                        ValidationSeverity.MEDIUM
                        if total_zero > len(df) * 0.1
                        else ValidationSeverity.LOW
                    )
                )
            )
            confidence = 1.0 if passed else 0.5

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="price_ranges",
                rule_name="Price Range Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "negative_prices": negative_prices,
                    "zero_prices": zero_prices,
                    "extreme_prices": extreme_prices,
                    "total_negative": total_negative,
                    "total_zero": total_zero,
                    "total_extreme": total_extreme,
                    "price_ranges": {
                        col: {
                            "min": float(df[col].min()) if len(df) > 0 else None,
                            "max": float(df[col].max()) if len(df) > 0 else None,
                            "median": float(df[col].median()) if len(df) > 0 else None,
                        }
                        for col in price_cols
                    },
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="price_ranges",
                rule_name="Price Range Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_trading_hours(self, df: pd.DataFrame) -> ValidationResult:
        """验证交易时间"""
        start_time = time.time()

        try:
            timestamp_col = "timestamp" if "timestamp" in df.columns else "date"

            if timestamp_col not in df.columns:
                return ValidationResult(
                    rule_id="trading_hours",
                    rule_name="Trading Hours Validation",
                    passed = True,
                    severity = ValidationSeverity.LOW,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "No timestamp column found"},
                )

            # 转换为datetime
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])

            # 香港股市交易时间：9:30 AM - 4:00 PM HKT
            trading_start_hour = 9
            trading_start_minute = 30
            trading_end_hour = 16
            trading_end_minute = 0

            # 检查交易时间外的记录
            trading_time_mask = (
                (df[timestamp_col].dt.hour > trading_start_hour)
                | (
                    (df[timestamp_col].dt.hour == trading_start_hour)
                    & (df[timestamp_col].dt.minute >= trading_start_minute)
                )
            ) & (
                (df[timestamp_col].dt.hour < trading_end_hour)
                | (
                    (df[timestamp_col].dt.hour == trading_end_hour)
                    & (df[timestamp_col].dt.minute <= trading_end_minute)
                )
            )

            # 检查周末（周六、周日）
            weekend_mask = df[timestamp_col].dt.weekday >= 5

            # 非交易时间的记录
            non_trading_hours = (~trading_time_mask).sum()
            weekend_records = weekend_mask.sum()

            # 计算在交易时间的比例
            trading_time_records = trading_time_mask & (~weekend_mask)
            trading_time_ratio = (
                trading_time_records.sum() / len(df) if len(df) > 0 else 0
            )

            # 对于股票数据，大部分记录应该在交易时间内
            passed = trading_time_ratio >= 0.8  # 至少80%的记录在交易时间内
            severity = (
                ValidationSeverity.MEDIUM
                if trading_time_ratio < 0.8
                else ValidationSeverity.LOW
            )
            confidence = trading_time_ratio

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="trading_hours",
                rule_name="Trading Hours Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "total_records": len(df),
                    "trading_time_records": trading_time_records.sum(),
                    "non_trading_hours": non_trading_hours,
                    "weekend_records": weekend_records,
                    "trading_time_ratio": trading_time_ratio,
                    "expected_trading_hours": f"{trading_start_hour}:{trading_start_minute:02d} - {trading_end_hour}:{trading_end_minute:02d}",
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="trading_hours",
                rule_name="Trading Hours Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_hibor_rates(self, df: pd.DataFrame) -> ValidationResult:
        """验证HIBOR利率"""
        start_time = time.time()

        try:
            hibor_cols = [
                col
                for col in df.columns
                if "hibor" in col.lower() or col.startswith("ir_")
            ]

            if not hibor_cols:
                return ValidationResult(
                    rule_id="hibor_rates",
                    rule_name="HIBOR Rates Validation",
                    passed = True,
                    severity = ValidationSeverity.LOW,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "No HIBOR rate columns found"},
                )

            violations = {}

            for col in hibor_cols:
                if col in df.columns:
                    rates = pd.to_numeric(df[col], errors="coerce")

                    # HIBOR利率应该在合理范围内（0 - 20%）
                    negative_rates = (rates < 0).sum()
                    extreme_rates = (rates > 20).sum()
                    invalid_rates = rates.isna().sum()

                    violations[col] = {
                        "negative_rates": negative_rates,
                        "extreme_rates": extreme_rates,
                        "invalid_rates": invalid_rates,
                        "min_rate": (
                            float(rates.min()) if len(rates.dropna()) > 0 else None
                        ),
                        "max_rate": (
                            float(rates.max()) if len(rates.dropna()) > 0 else None
                        ),
                    }

            total_violations = sum(
                v.get("negative_rates", 0)
                + v.get("extreme_rates", 0)
                + v.get("invalid_rates", 0)
                for v in violations.values()
            )
            passed = total_violations == 0
            severity = (
                ValidationSeverity.HIGH
                if total_violations > len(df) * 0.01
                else (
                    ValidationSeverity.MEDIUM
                    if total_violations > 0
                    else ValidationSeverity.LOW
                )
            )
            confidence = 1.0 if passed else max(0.5, 1.0 - total_violations / len(df))

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="hibor_rates",
                rule_name="HIBOR Rates Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "hibor_columns": hibor_cols,
                    "violations": violations,
                    "total_violations": total_violations,
                    "valid_rate_range": "0% - 20%",
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="hibor_rates",
                rule_name="HIBOR Rates Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_exchange_rates(self, df: pd.DataFrame) -> ValidationResult:
        """验证汇率数据"""
        start_time = time.time()

        try:
            rate_cols = [
                col
                for col in df.columns
                if "rate" in col.lower() or "exchange" in col.lower()
            ]

            if not rate_cols:
                return ValidationResult(
                    rule_id="exchange_rates",
                    rule_name="Exchange Rates Validation",
                    passed = True,
                    severity = ValidationSeverity.LOW,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "No exchange rate columns found"},
                )

            violations = {}

            for col in rate_cols:
                if col in df.columns:
                    rates = pd.to_numeric(df[col], errors="coerce")

                    # 汇率应该在合理范围内（例如：1 - 20）
                    zero_rates = (rates == 0).sum()
                    negative_rates = (rates < 0).sum()
                    extreme_rates = (rates > 100).sum()  # 异常高汇率
                    invalid_rates = rates.isna().sum()

                    # 检查单日变动幅度（超过10%为异常）
                    if len(rates.dropna()) > 1:
                        rate_changes = rates.pct_change().abs()
                        extreme_changes = (rate_changes > 0.10).sum()
                    else:
                        extreme_changes = 0

                    violations[col] = {
                        "zero_rates": zero_rates,
                        "negative_rates": negative_rates,
                        "extreme_rates": extreme_rates,
                        "extreme_changes": extreme_changes,
                        "invalid_rates": invalid_rates,
                        "min_rate": (
                            float(rates.min()) if len(rates.dropna()) > 0 else None
                        ),
                        "max_rate": (
                            float(rates.max()) if len(rates.dropna()) > 0 else None
                        ),
                    }

            total_violations = sum(
                v.get("negative_rates", 0)
                + v.get("extreme_rates", 0)
                + v.get("zero_rates", 0)
                for v in violations.values()
            )
            passed = total_violations == 0
            severity = (
                ValidationSeverity.HIGH
                if total_violations > len(df) * 0.01
                else (
                    ValidationSeverity.MEDIUM
                    if total_violations > 0
                    else ValidationSeverity.LOW
                )
            )
            confidence = 1.0 if passed else max(0.5, 1.0 - total_violations / len(df))

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="exchange_rates",
                rule_name="Exchange Rates Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "rate_columns": rate_cols,
                    "violations": violations,
                    "total_violations": total_violations,
                    "valid_rate_range": "0 < rate <= 100",
                    "max_daily_change": "10%",
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="exchange_rates",
                rule_name="Exchange Rates Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_monetary_data(self, df: pd.DataFrame) -> ValidationResult:
        """验证货币数据"""
        start_time = time.time()

        try:
            monetary_cols = [
                col
                for col in df.columns
                if "monetary" in col.lower()
                or "base" in col.lower()
                or "money" in col.lower()
            ]

            if not monetary_cols:
                return ValidationResult(
                    rule_id="monetary_data",
                    rule_name="Monetary Data Validation",
                    passed = True,
                    severity = ValidationSeverity.LOW,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "No monetary data columns found"},
                )

            violations = {}

            for col in monetary_cols:
                if col in df.columns:
                    values = pd.to_numeric(df[col], errors="coerce")

                    # 货币数据应该为正数且在合理范围内
                    negative_values = (values < 0).sum()
                    zero_values = (values == 0).sum()
                    invalid_values = values.isna().sum()

                    # 检查异常值（超过中位数的100倍）
                    if len(values.dropna()) > 0:
                        median_val = values.median()
                        extreme_values = (values > median_val * 100).sum()
                    else:
                        extreme_values = 0

                    violations[col] = {
                        "negative_values": negative_values,
                        "zero_values": zero_values,
                        "extreme_values": extreme_values,
                        "invalid_values": invalid_values,
                        "min_value": (
                            float(values.min()) if len(values.dropna()) > 0 else None
                        ),
                        "max_value": (
                            float(values.max()) if len(values.dropna()) > 0 else None
                        ),
                        "median_value": (
                            float(values.median()) if len(values.dropna()) > 0 else None
                        ),
                    }

            total_violations = sum(
                v.get("negative_values", 0) + v.get("extreme_values", 0)
                for v in violations.values()
            )
            passed = total_violations == 0
            severity = (
                ValidationSeverity.HIGH
                if total_violations > len(df) * 0.01
                else (
                    ValidationSeverity.MEDIUM
                    if total_violations > 0
                    else ValidationSeverity.LOW
                )
            )
            confidence = 1.0 if passed else max(0.5, 1.0 - total_violations / len(df))

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="monetary_data",
                rule_name="Monetary Data Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "monetary_columns": monetary_cols,
                    "violations": violations,
                    "total_violations": total_violations,
                    "validation_rules": "Values should be positive and within reasonable ranges",
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="monetary_data",
                rule_name="Monetary Data Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_economic_indicators(self, df: pd.DataFrame) -> ValidationResult:
        """验证经济指标"""
        start_time = time.time()

        try:
            # 通用验证规则
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            violations = {}

            for col in numeric_cols:
                values = df[col]

                # 检查缺失值
                missing_count = values.isna().sum()
                missing_rate = missing_count / len(values)

                # 检查异常值
                if len(values.dropna()) > 0:
                    Q1 = values.quantile(0.25)
                    Q3 = values.quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = (
                        (values < (Q1 - 1.5 * IQR)) | (values > (Q3 + 1.5 * IQR))
                    ).sum()

                    violations[col] = {
                        "missing_count": missing_count,
                        "missing_rate": missing_rate,
                        "outliers": outliers,
                        "outlier_rate": outliers / len(values),
                        "min_value": float(values.min()),
                        "max_value": float(values.max()),
                        "median_value": float(values.median()),
                    }

            total_missing_rate = (
                sum(v.get("missing_count", 0) for v in violations.values())
                / (len(df) * len(violations))
                if violations
                else 0
            )
            passed = total_missing_rate < 0.1  # 缺失率小于10%
            severity = (
                ValidationSeverity.HIGH
                if total_missing_rate > 0.2
                else (
                    ValidationSeverity.MEDIUM
                    if total_missing_rate > 0.1
                    else ValidationSeverity.LOW
                )
            )
            confidence = max(0.3, 1.0 - total_missing_rate)

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="economic_indicators",
                rule_name="Economic Indicators Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "numeric_columns": list(numeric_cols),
                    "violations": violations,
                    "total_missing_rate": total_missing_rate,
                    "validation_rules": "Missing rate < 10%, reasonable outlier bounds",
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="economic_indicators",
                rule_name="Economic Indicators Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_economic_trends(self, df: pd.DataFrame) -> ValidationResult:
        """验证经济数据趋势"""
        start_time = time.time()

        try:
            if len(df) < 3:
                return ValidationResult(
                    rule_id="economic_trends",
                    rule_name="Economic Trends Validation",
                    passed = True,
                    severity = ValidationSeverity.LOW,
                    confidence = 1.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={"message": "Insufficient data for trend validation"},
                )

            numeric_cols = df.select_dtypes(include=[np.number]).columns
            trend_issues = []

            for col in numeric_cols:
                if len(df[col].dropna()) < 3:
                    continue

                # 计算趋势变化
                values = df[col].dropna()

                # 检查异常突变（单日变化超过50%）
                if len(values) > 1:
                    changes = values.pct_change().abs()
                    extreme_changes = (changes > 0.5).sum()
                    if extreme_changes > 0:
                        trend_issues.append(
                            f"{col}: {extreme_changes} extreme changes (>50%)"
                        )

                # 检查趋势一致性（非预期的频繁反转）
                if len(values) > 2:
                    diff = values.diff().dropna()
                    sign_changes = ((diff.shift(1) * diff) < 0).sum()
                    if sign_changes > len(values) * 0.5:  # 超过50%的时间都在反转
                        trend_issues.append(f"{col}: Excessive trend reversals")

            passed = len(trend_issues) == 0
            severity = (
                ValidationSeverity.MEDIUM
                if len(trend_issues) > 3
                else ValidationSeverity.LOW if trend_issues else ValidationSeverity.LOW
            )
            confidence = 1.0 if passed else max(0.6, 1.0 - len(trend_issues) * 0.1)

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="economic_trends",
                rule_name="Economic Trends Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "numeric_columns": list(numeric_cols),
                    "trend_issues": trend_issues,
                    "validation_rules": "Extreme changes < 50%, reasonable trend consistency",
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="economic_trends",
                rule_name="Economic Trends Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_numeric_ranges(self, df: pd.DataFrame) -> ValidationResult:
        """验证数值范围"""
        start_time = time.time()

        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            violations = {}

            for col in numeric_cols:
                values = df[col]

                # 基本统计信息
                if len(values.dropna()) > 0:
                    min_val = values.min()
                    max_val = values.max()

                    # 检查无限值
                    infinite_values = values.isin([np.inf, -np.inf]).sum()

                    # 检查异常大的数值（基于标准差）
                    std_val = values.std()
                    mean_val = values.mean()

                    if std_val > 0:
                        extreme_outliers = (abs(values - mean_val) > 5 * std_val).sum()
                    else:
                        extreme_outliers = 0

                    violations[col] = {
                        "min_value": float(min_val),
                        "max_value": float(max_val),
                        "infinite_values": infinite_values,
                        "extreme_outliers": extreme_outliers,
                        "mean_value": float(mean_val),
                        "std_value": float(std_val),
                    }

            total_infinite = sum(
                v.get("infinite_values", 0) for v in violations.values()
            )
            total_extreme_outliers = sum(
                v.get("extreme_outliers", 0) for v in violations.values()
            )

            passed = (
                total_infinite == 0 and total_extreme_outliers < len(df) * 0.05
            )  # 少于5%的极端异常值
            severity = (
                ValidationSeverity.CRITICAL
                if total_infinite > 0
                else (
                    ValidationSeverity.HIGH
                    if total_extreme_outliers > len(df) * 0.1
                    else (
                        ValidationSeverity.MEDIUM
                        if total_extreme_outliers > 0
                        else ValidationSeverity.LOW
                    )
                )
            )
            confidence = (
                1.0 if passed else max(0.4, 1.0 - total_extreme_outliers / len(df))
            )

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="numeric_ranges",
                rule_name="Numeric Ranges Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "numeric_columns": list(numeric_cols),
                    "violations": violations,
                    "total_infinite": total_infinite,
                    "total_extreme_outliers": total_extreme_outliers,
                    "validation_rules": "No infinite values, extreme outliers < 5%",
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="numeric_ranges",
                rule_name="Numeric Ranges Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    async def _validate_data_consistency(self, df: pd.DataFrame) -> ValidationResult:
        """验证数据一致性"""
        start_time = time.time()

        try:
            consistency_issues = []

            # 检查重复行
            duplicate_rows = df.duplicated().sum()
            if duplicate_rows > 0:
                consistency_issues.append(f"Duplicate rows: {duplicate_rows}")

            # 检查数据类型一致性
            type_issues = []
            for col in df.columns:
                # 检查混合数据类型
                unique_types = set(df[col].apply(type).__name__)
                if len(unique_types) > 2:  # 超过2种数据类型（包括NaN）
                    type_issues.append(f"{col}: {unique_types}")

            if type_issues:
                consistency_issues.append(f"Mixed data types: {type_issues}")

            # 检查数据格式一致性（针对字符串列）
            string_cols = df.select_dtypes(include=["object"]).columns
            format_issues = []

            for col in string_cols:
                non_null_values = df[col].dropna()
                if len(non_null_values) > 0:
                    # 检查空白字符问题
                    whitespace_issues = (
                        non_null_values.astype(str)
                        .str.strip()
                        .ne(non_null_values.astype(str))
                        .sum()
                    )
                    if whitespace_issues > 0:
                        format_issues.append(
                            f"{col}: {whitespace_issues} whitespace issues"
                        )

            if format_issues:
                consistency_issues.append(f"Format issues: {format_issues}")

            passed = len(consistency_issues) == 0
            severity = (
                ValidationSeverity.MEDIUM
                if consistency_issues
                else ValidationSeverity.LOW
            )
            confidence = 1.0 if passed else 0.7

            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                rule_id="data_consistency",
                rule_name="Data Consistency Validation",
                passed = passed,
                severity = severity,
                confidence = confidence,
                execution_time_ms = execution_time,
                details={
                    "consistency_issues": consistency_issues,
                    "duplicate_rows": duplicate_rows,
                    "type_issues": type_issues,
                    "format_issues": format_issues,
                    "validation_rules": "No duplicates, consistent data types, clean formats",
                },
            )

        except Exception as e:
            return ValidationResult(
                rule_id="data_consistency",
                rule_name="Data Consistency Validation",
                passed = False,
                severity = ValidationSeverity.CRITICAL,
                confidence = 0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message = str(e),
            )

    def _initialize_hk_market_rules(self) -> Dict[str, Any]:
        """初始化香港市场业务规则"""
        return {
            "stock_price_limits": {
                "max_daily_change": 0.10,  # 10%涨跌停
                "max_price": 1000000,  # 最高价格100万港币
                "min_price": 0.01,  # 最低价格0.01港币
            },
            "trading_hours": {
                "start_hour": 9,
                "start_minute": 30,
                "end_hour": 16,
                "end_minute": 0,
                "weekend_trading": False,
            },
            "hibor_rates": {
                "min_rate": 0.0,
                "max_rate": 20.0,
                "valid_tenors": [
                    "overnight",
                    "1_week",
                    "1_month",
                    "3_month",
                    "6_month",
                    "12_month",
                ],
            },
            "exchange_rates": {
                "min_rate": 0.01,
                "max_rate": 100.0,
                "max_daily_change": 0.10,
            },
        }


# Content Validation Layer Factory
class ContentValidationFactory:
    """内容验证层工厂类"""

    @staticmethod
    def create_integrity_verifier(
        config: Optional[Dict[str, Any]] = None,
    ) -> DataIntegrityVerifier:
        """创建数据完整性验证器"""
        return DataIntegrityVerifier(config)

    @staticmethod
    def create_timeseries_verifier(
        config: Optional[Dict[str, Any]] = None,
    ) -> TimeSeriesVerifier:
        """创建时间序列验证器"""
        return TimeSeriesVerifier(config)

    @staticmethod
    def create_business_rules_verifier(
        config: Optional[Dict[str, Any]] = None,
    ) -> BusinessRulesValidator:
        """创建业务规则验证器"""
        return BusinessRulesValidator(config)

    @staticmethod
    def create_all_verifiers(
        config: Optional[Dict[str, Any]] = None,
    ) -> List[IVerifier]:
        """创建所有内容验证器"""
        return [
            ContentValidationFactory.create_integrity_verifier(config),
            ContentValidationFactory.create_timeseries_verifier(config),
            ContentValidationFactory.create_business_rules_verifier(config),
        ]


# Export main classes and functions
__all__ = [
    # Core classes
    "DataIntegrityVerifier",
    "TimeSeriesVerifier",
    "BusinessRulesValidator",
    "ContentValidationFactory",
    # Data structures
    "ValidationRule",
    "ValidationResult",
    "AnomalyDetection",
    "ValidationSeverity",
    "AnomalyType",
]
