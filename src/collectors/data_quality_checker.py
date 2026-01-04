#!/usr/bin/env python3
"""
Data Quality Checker
數據質量檢查器
Task 8.1 - 數據獲取模塊

Comprehensive data quality validation system with anomaly detection,
quality scoring, and automated data cleaning for financial market data.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import json
import warnings
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"          # 75-89
    FAIR = "fair"          # 60-74
    POOR = "poor"          # < 60

class AnomalyType(Enum):
    """Types of anomalies to detect"""
    PRICE_SPIKE = "price_spike"
    PRICE_GAP = "price_gap"
    VOLUME_ANOMALY = "volume_anomaly"
    MISSING_DATA = "missing_data"
    DUPLICATE_DATA = "duplicate_data"
    FUTURE_DATA = "future_data"
    NEGATIVE_VALUES = "negative_values"
    OUTLIER = "statistical_outlier"

class AlertLevel(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class QualityIssue:
    """Represents a quality issue found in data"""
    issue_type: str
    severity: AlertLevel
    message: str
    timestamp: Optional[datetime] = None
    row_index: Optional[int] = None
    column: Optional[str] = None
    value: Optional[Any] = None
    expected_range: Optional[Tuple[float, float]] = None
    suggestion: Optional[str] = None

@dataclass
class QualityReport:
    """Comprehensive quality report for data"""
    symbol: str
    data_type: str
    total_records: int
    valid_records: int
    quality_score: float
    quality_level: QualityLevel
    issues: List[QualityIssue]
    statistics: Dict[str, Any]
    recommendations: List[str]
    processing_time: float
    timestamp: datetime

@dataclass
class DataQualityConfig:
    """Configuration for data quality checking"""
    # Price validation thresholds
    max_price_change_pct: float = 50.0    # Maximum allowed price change (%)
    min_price: float = 0.01               # Minimum valid price
    max_price: float = 1000000           # Maximum valid price

    # Volume validation thresholds
    max_volume_change_pct: float = 1000.0  # Maximum allowed volume change (%)
    min_volume: int = 0                    # Minimum valid volume

    # Data completeness thresholds
    missing_data_threshold: float = 0.05   # 5% missing data threshold
    duplicate_threshold: float = 0.01      # 1% duplicate threshold

    # Anomaly detection
    outlier_contamination: float = 0.1     # Expected proportion of outliers
    enable_statistical_detection: bool = True
    enable_pattern_detection: bool = True

    # Time-based validation
    max_future_minutes: int = 5           # Maximum future data tolerance
    market_hours_only: bool = True        # Validate market hours

    # Data quality scoring weights
    completeness_weight: float = 0.3
    accuracy_weight: float = 0.3
    consistency_weight: float = 0.2
    timeliness_weight: float = 0.2

    # Alerting thresholds
    critical_threshold: float = 60.0
    warning_threshold: float = 75.0

class DataQualityChecker:
    """
    Comprehensive data quality validation system for financial data
    with anomaly detection and quality scoring.
    """

    def __init__(self, config: DataQualityConfig = None):
        self.config = config or DataQualityConfig()

        # Initialize anomaly detection models
        self.anomaly_models = {}
        self.scalers = {}

        # Quality metrics history
        self.quality_history = {}

        # Known symbols and their characteristics
        self.symbol_profiles = {}

        logger.info("Data quality checker initialized")

    async def check_market_data(
        self,
        data: pd.DataFrame,
        symbol: str,
        data_type: str = "price",
        reference_data: Optional[pd.DataFrame] = None
    ) -> QualityReport:
        """
        Perform comprehensive quality check on market data

        Args:
            data: DataFrame to validate
            symbol: Symbol identifier
            data_type: Type of data (price, volume, etc.)
            reference_data: Historical data for comparison

        Returns:
            QualityReport with detailed validation results
        """
        start_time = time.time()

        issues = []

        try:
            logger.info(f"Starting quality check for {symbol} - {len(data)} records")

            # 1. Basic structure validation
            structure_issues = await self._check_structure(data, data_type)
            issues.extend(structure_issues)

            # 2. Date and time validation
            datetime_issues = await self._check_datetime(data)
            issues.extend(datetime_issues)

            # 3. Price data validation
            if data_type == "price":
                price_issues = await self._check_price_data(data, symbol, reference_data)
                issues.extend(price_issues)

            # 4. Volume data validation
            if "volume" in data.columns:
                volume_issues = await self._check_volume_data(data, symbol, reference_data)
                issues.extend(volume_issues)

            # 5. Data consistency validation
            consistency_issues = await self._check_consistency(data)
            issues.extend(consistency_issues)

            # 6. Missing data analysis
            missing_issues = await self._check_missing_data(data)
            issues.extend(missing_issues)

            # 7. Duplicate data detection
            duplicate_issues = await self._check_duplicates(data)
            issues.extend(duplicate_issues)

            # 8. Statistical anomaly detection
            if self.config.enable_statistical_detection and len(data) > 100:
                anomaly_issues = await self._detect_anomalies(data, symbol)
                issues.extend(anomaly_issues)

            # 9. Pattern-based validation
            if self.config.enable_pattern_detection:
                pattern_issues = await self._check_patterns(data, symbol)
                issues.extend(pattern_issues)

            # Calculate quality score
            quality_score = await self._calculate_quality_score(data, issues)
            quality_level = self._get_quality_level(quality_score)

            # Generate statistics
            statistics = await self._calculate_statistics(data)

            # Generate recommendations
            recommendations = self._generate_recommendations(issues, quality_level)

            # Create report
            processing_time = time.time() - start_time
            report = QualityReport(
                symbol=symbol,
                data_type=data_type,
                total_records=len(data),
                valid_records=len(data) - self._count_invalid_records(issues),
                quality_score=quality_score,
                quality_level=quality_level,
                issues=issues,
                statistics=statistics,
                recommendations=recommendations,
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )

            # Store in history
            await self._store_quality_history(symbol, report)

            logger.info(f"Quality check completed for {symbol} - Score: {quality_score:.1f} ({quality_level.value})")
            return report

        except Exception as e:
            logger.error(f"Quality check failed for {symbol}: {e}")

            # Return error report
            processing_time = time.time() - start_time
            return QualityReport(
                symbol=symbol,
                data_type=data_type,
                total_records=len(data) if data is not None else 0,
                valid_records=0,
                quality_score=0.0,
                quality_level=QualityLevel.POOR,
                issues=[QualityIssue(
                    issue_type="system_error",
                    severity=AlertLevel.CRITICAL,
                    message=f"Quality check system error: {str(e)}"
                )],
                statistics={},
                recommendations=["Fix data quality checking system"],
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )

    async def _check_structure(self, data: pd.DataFrame, data_type: str) -> List[QualityIssue]:
        """Check basic data structure"""
        issues = []

        # Check if data is empty
        if data.empty:
            issues.append(QualityIssue(
                issue_type="empty_data",
                severity=AlertLevel.CRITICAL,
                message="Data is empty",
                suggestion="Load data before validation"
            ))
            return issues

        # Check required columns based on data type
        if data_type == "price":
            required_columns = ["date", "open", "high", "low", "close"]
        else:
            required_columns = ["date"]

        missing_columns = set(required_columns) - set(data.columns)
        if missing_columns:
            issues.append(QualityIssue(
                issue_type="missing_columns",
                severity=AlertLevel.CRITICAL,
                message=f"Missing required columns: {', '.join(missing_columns)}",
                suggestion=f"Add columns: {', '.join(missing_columns)}"
            ))

        # Check data types
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            if col in data.columns:
                try:
                    pd.to_numeric(data[col], errors='raise')
                except:
                    issues.append(QualityIssue(
                        issue_type="invalid_data_type",
                        severity=AlertLevel.ERROR,
                        message=f"Column '{col}' contains non-numeric values",
                        column=col,
                        suggestion="Ensure all numeric columns contain valid numbers"
                    ))

        return issues

    async def _check_datetime(self, data: pd.DataFrame) -> List[QualityIssue]:
        """Check date/time validity"""
        issues = []

        if "date" not in data.columns:
            return issues

        try:
            dates = pd.to_datetime(data["date"])

            # Check for invalid dates
            invalid_dates = dates.isna()
            if invalid_dates.any():
                count = invalid_dates.sum()
                issues.append(QualityIssue(
                    issue_type="invalid_dates",
                    severity=AlertLevel.ERROR,
                    message=f"Found {count} invalid dates",
                    affected_rows=invalid_dates.sum(),
                    suggestion="Remove or correct invalid date values"
                ))

            # Check for future dates
            now = datetime.utcnow()
            future_dates = dates > now + timedelta(minutes=self.config.max_future_minutes)
            if future_dates.any():
                count = future_dates.sum()
                issues.append(QualityIssue(
                    issue_type="future_dates",
                    severity=AlertLevel.WARNING,
                    message=f"Found {count} future dates",
                    affected_rows=count,
                    suggestion="Verify data timestamps and system clock"
                ))

            # Check for duplicates
            duplicate_dates = dates.duplicated()
            if duplicate_dates.any():
                count = duplicate_dates.sum()
                issues.append(QualityIssue(
                    issue_type="duplicate_dates",
                    severity=AlertLevel.WARNING,
                    message=f"Found {count} duplicate dates",
                    affected_rows=count,
                    suggestion="Aggregate or remove duplicate records"
                ))

            # Check chronological order
            if not dates.is_monotonic_increasing:
                issues.append(QualityIssue(
                    issue_type="unordered_dates",
                    severity=AlertLevel.WARNING,
                    message="Data is not in chronological order",
                    suggestion="Sort data by date"
                ))

        except Exception as e:
            issues.append(QualityIssue(
                issue_type="datetime_parsing_error",
                severity=AlertLevel.ERROR,
                message=f"Failed to parse dates: {str(e)}",
                suggestion="Check date format and content"
            ))

        return issues

    async def _check_price_data(
        self,
        data: pd.DataFrame,
        symbol: str,
        reference_data: Optional[pd.DataFrame] = None
    ) -> List[QualityIssue]:
        """Check price data validity"""
        issues = []
        price_columns = ["open", "high", "low", "close"]

        for col in price_columns:
            if col not in data.columns:
                continue

            prices = pd.to_numeric(data[col], errors='coerce')

            # Check for missing values
            missing = prices.isna()
            if missing.any():
                count = missing.sum()
                issues.append(QualityIssue(
                    issue_type="missing_prices",
                    severity=AlertLevel.ERROR,
                    message=f"Found {count} missing values in {col}",
                    column=col,
                    affected_rows=count,
                    suggestion="Fill or interpolate missing price values"
                ))

            # Check for non-positive values
            non_positive = prices <= 0
            if non_positive.any():
                count = non_positive.sum()
                issues.append(QualityIssue(
                    issue_type="non_positive_prices",
                    severity=AlertLevel.ERROR,
                    message=f"Found {count} non-positive values in {col}",
                    column=col,
                    affected_rows=count,
                    suggestion="Remove or correct non-positive prices"
                ))

            # Check for extreme values
            valid_prices = prices.dropna()
            if len(valid_prices) > 0:
                median = valid_prices.median()

                # Check for prices far from median
                extreme_prices = np.abs(valid_prices - median) / median > 5.0
                if extreme_prices.any():
                    count = extreme_prices.sum()
                    issues.append(QualityIssue(
                        issue_type="extreme_prices",
                        severity=AlertLevel.WARNING,
                        message=f"Found {count} extreme values in {col} (> 500% from median)",
                        column=col,
                        affected_rows=count,
                        suggestion="Investigate extreme price movements"
                    ))

        # Check OHLC relationships
        if all(col in data.columns for col in ["open", "high", "low", "close"]):
            # High should be >= all prices
            invalid_high = data["high"] < data[["open", "close"]].max(axis=1)
            if invalid_high.any():
                count = invalid_high.sum()
                issues.append(QualityIssue(
                    issue_type="invalid_ohlc_high",
                    severity=AlertLevel.ERROR,
                    message=f"Found {count} records where high < max(open, close)",
                    affected_rows=count,
                    suggestion="Correct OHLC price relationships"
                ))

            # Low should be <= all prices
            invalid_low = data["low"] > data[["open", "close"]].min(axis=1)
            if invalid_low.any():
                count = invalid_low.sum()
                issues.append(QualityIssue(
                    issue_type="invalid_ohlc_low",
                    severity=AlertLevel.ERROR,
                    message=f"Found {count} records where low > min(open, close)",
                    affected_rows=count,
                    suggestion="Correct OHLC price relationships"
                ))

        # Check for price gaps (if reference data available)
        if reference_data is not None and not data.empty and not reference_data.empty:
            gap_issues = await self._check_price_gaps(data, reference_data, symbol)
            issues.extend(gap_issues)

        return issues

    async def _check_volume_data(
        self,
        data: pd.DataFrame,
        symbol: str,
        reference_data: Optional[pd.DataFrame] = None
    ) -> List[QualityIssue]:
        """Check volume data validity"""
        issues = []

        if "volume" not in data.columns:
            return issues

        volumes = pd.to_numeric(data["volume"], errors='coerce')

        # Check for missing values
        missing = volumes.isna()
        if missing.any():
            count = missing.sum()
            issues.append(QualityIssue(
                issue_type="missing_volume",
                severity=AlertLevel.WARNING,
                message=f"Found {count} missing volume values",
                affected_rows=count,
                suggestion="Fill or interpolate missing volume values"
            ))

        # Check for negative values
        negative = volumes < 0
        if negative.any():
            count = negative.sum()
            issues.append(QualityIssue(
                issue_type="negative_volume",
                severity=AlertLevel.ERROR,
                message=f"Found {count} negative volume values",
                affected_rows=count,
                suggestion="Remove or correct negative volumes"
            ))

        # Check for extreme volume changes
        if len(volumes) > 1:
            volume_changes = volumes.pct_change().abs()
            extreme_changes = volume_changes > (self.config.max_volume_change_pct / 100)

            if extreme_changes.any():
                count = extreme_changes.sum()
                issues.append(QualityIssue(
                    issue_type="extreme_volume_change",
                    severity=AlertLevel.WARNING,
                    message=f"Found {count} extreme volume changes (> {self.config.max_volume_change_pct}%)",
                    affected_rows=count,
                    suggestion="Investigate extreme volume changes"
                ))

        return issues

    async def _check_price_gaps(
        self,
        data: pd.DataFrame,
        reference_data: pd.DataFrame,
        symbol: str
    ) -> List[QualityIssue]:
        """Check for price gaps compared to reference data"""
        issues = []

        try:
            # Get last price from reference data
            if reference_data.empty:
                return issues

            last_ref_price = reference_data.iloc[-1]["close"]
            first_new_price = data.iloc[0]["open"]

            # Calculate gap percentage
            gap_pct = abs(first_new_price - last_ref_price) / last_ref_price * 100

            # Check if gap is too large
            if gap_pct > self.config.max_price_change_pct:
                issues.append(QualityIssue(
                    issue_type="price_gap",
                    severity=AlertLevel.WARNING,
                    message=f"Large price gap detected: {gap_pct:.2f}%",
                    value=gap_pct,
                    expected_range=(0, self.config.max_price_change_pct),
                    suggestion="Verify price continuity and check for stock splits"
                ))

        except Exception as e:
            logger.debug(f"Failed to check price gaps: {e}")

        return issues

    async def _check_consistency(self, data: pd.DataFrame) -> List[QualityIssue]:
        """Check data consistency"""
        issues = []

        # Check for data gaps
        if "date" in data.columns and len(data) > 1:
            dates = pd.to_datetime(data["date"]).sort_values()

            # Calculate date gaps
            date_gaps = dates.diff().dt.days

            # Look for gaps larger than expected (e.g., weekends, holidays)
            large_gaps = date_gaps > 7  # More than a week
            if large_gaps.any():
                count = large_gaps.sum()
                issues.append(QualityIssue(
                    issue_type="data_gaps",
                    severity=AlertLevel.INFO,
                    message=f"Found {count} gaps in data (> 7 days)",
                    affected_rows=count,
                    suggestion="Investigate data gaps for missing data"
                ))

        return issues

    async def _check_missing_data(self, data: pd.DataFrame) -> List[QualityIssue]:
        """Check for missing data patterns"""
        issues = []

        # Calculate missing data percentages
        missing_stats = {}
        for col in data.columns:
            missing_pct = data[col].isna().sum() / len(data) * 100
            missing_stats[col] = missing_pct

            if missing_pct > self.config.missing_data_threshold * 100:
                issues.append(QualityIssue(
                    issue_type="high_missing_rate",
                    severity=AlertLevel.WARNING,
                    message=f"High missing data rate in {col}: {missing_pct:.1f}%",
                    column=col,
                    value=missing_pct,
                    expected_range=(0, self.config.missing_data_threshold * 100),
                    suggestion="Investigate cause of missing data"
                ))

        # Check for consecutive missing values
        if "date" in data.columns:
            for col in data.columns:
                if col == "date":
                    continue

                # Find consecutive missing sequences
                missing_series = data[col].isna()

                # Count consecutive missing values
                consecutive_missing = 0
                max_consecutive = 0

                for is_missing in missing_series:
                    if is_missing:
                        consecutive_missing += 1
                        max_consecutive = max(max_consecutive, consecutive_missing)
                    else:
                        consecutive_missing = 0

                if max_consecutive > 5:  # More than 5 consecutive missing
                    issues.append(QualityIssue(
                        issue_type="consecutive_missing",
                        severity=AlertLevel.WARNING,
                        message=f"Found {max_consecutive} consecutive missing values in {col}",
                        column=col,
                        value=max_consecutive,
                        suggestion="Check data source for continuous data issues"
                    ))

        return issues

    async def _check_duplicates(self, data: pd.DataFrame) -> List[QualityIssue]:
        """Check for duplicate data"""
        issues = []

        if data.empty:
            return issues

        # Check for exact duplicates
        duplicate_rows = data.duplicated()
        if duplicate_rows.any():
            count = duplicate_rows.sum()
            duplicate_pct = count / len(data) * 100

            if duplicate_pct > self.config.duplicate_threshold * 100:
                issues.append(QualityIssue(
                    issue_type="high_duplicate_rate",
                    severity=AlertLevel.WARNING,
                    message=f"High duplicate rate: {duplicate_pct:.1f}%",
                    value=duplicate_pct,
                    expected_range=(0, self.config.duplicate_threshold * 100),
                    suggestion="Remove or aggregate duplicate records"
                ))

        # Check for date-based duplicates
        if "date" in data.columns:
            date_duplicates = data["date"].duplicated()
            if date_duplicates.any():
                count = date_duplicates.sum()
                issues.append(QualityIssue(
                    issue_type="date_duplicates",
                    severity=AlertLevel.INFO,
                    message=f"Found {count} duplicate dates",
                    affected_rows=count,
                    suggestion="Aggregate or remove duplicate date records"
                ))

        return issues

    async def _detect_anomalies(
        self,
        data: pd.DataFrame,
        symbol: str
    ) -> List[QualityIssue]:
        """Detect statistical anomalies using machine learning"""
        issues = []

        try:
            # Prepare numeric features
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return issues

            feature_data = data[numeric_cols].dropna()
            if len(feature_data) < 30:  # Need minimum data points
                return issues

            # Scale features
            if symbol not in self.scalers:
                self.scalers[symbol] = StandardScaler()

            try:
                scaled_features = self.scalers[symbol].fit_transform(feature_data)
            except:
                # Create new scaler if fit fails
                self.scalers[symbol] = StandardScaler()
                scaled_features = self.scalers[symbol].fit_transform(feature_data)

            # Detect anomalies using Isolation Forest
            iso_forest = IsolationForest(
                contamination=self.config.outlier_contamination,
                random_state=42,
                n_estimators=100
            )

            anomaly_labels = iso_forest.fit_predict(scaled_features)
            anomaly_mask = anomaly_labels == -1

            if anomaly_mask.any():
                anomaly_count = anomaly_mask.sum()
                anomaly_pct = anomaly_count / len(feature_data) * 100

                issues.append(QualityIssue(
                    issue_type="statistical_outliers",
                    severity=AlertLevel.INFO,
                    message=f"Detected {anomaly_count} statistical outliers ({anomaly_pct:.1f}%)",
                    value=anomaly_count,
                    suggestion="Review identified outliers for potential data errors"
                ))

                # Store model for future use
                self.anomaly_models[symbol] = iso_forest

        except Exception as e:
            logger.debug(f"Anomaly detection failed: {e}")
            issues.append(QualityIssue(
                issue_type="anomaly_detection_error",
                severity=AlertLevel.WARNING,
                message=f"Anomaly detection failed: {str(e)}",
                suggestion="Check data format for anomaly detection"
            ))

        return issues

    async def _check_patterns(self, data: pd.DataFrame, symbol: str) -> List[QualityIssue]:
        """Check for common data pattern issues"""
        issues = []

        try:
            # Check for suspicious patterns
            if len(data) > 10:
                # Check for flat prices (no movement)
                if "close" in data.columns:
                    close_prices = pd.to_numeric(data["close"], errors='coerce')

                    # Check for sequences with identical prices
                    price_diff = close_prices.diff()
                    flat_periods = (price_diff.abs() < 1e-6).rolling(window=10).sum()

                    if (flat_periods == 10).any():
                        issues.append(QualityIssue(
                            issue_type="flat_prices",
                            severity=AlertLevel.WARNING,
                            message="Detected periods with no price movement",
                            suggestion="Verify data source for stale or frozen prices"
                        ))

                # Check for abnormal volume patterns
                if "volume" in data.columns:
                    volumes = pd.to_numeric(data["volume"], errors='coerce')

                    # Check for zero volume periods
                    zero_volume_periods = (volumes == 0).rolling(window=5).sum()

                    if (zero_volume_periods >= 5).any():
                        issues.append(QualityIssue(
                            issue_type="zero_volume_periods",
                            severity=AlertLevel.WARNING,
                            message="Detected periods with zero volume",
                            suggestion="Verify market status and data source"
                        ))

        except Exception as e:
            logger.debug(f"Pattern checking failed: {e}")

        return issues

    async def _calculate_quality_score(
        self,
        data: pd.DataFrame,
        issues: List[QualityIssue]
    ) -> float:
        """Calculate overall quality score"""
        if data.empty:
            return 0.0

        # Start with perfect score
        score = 100.0

        # Deduct points based on issues
        for issue in issues:
            if issue.severity == AlertLevel.CRITICAL:
                score -= 20
            elif issue.severity == AlertLevel.ERROR:
                score -= 10
            elif issue.severity == AlertLevel.WARNING:
                score -= 5
            elif issue.severity == AlertLevel.INFO:
                score -= 1

        # Apply completeness factor
        completeness = 1.0 - (data.isna().sum().sum() / (len(data) * len(data.columns)))
        score = score * completeness

        # Ensure score is within valid range
        return max(0.0, min(100.0, score))

    def _get_quality_level(self, score: float) -> QualityLevel:
        """Get quality level based on score"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 75:
            return QualityLevel.GOOD
        elif score >= 60:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR

    async def _calculate_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate data statistics"""
        stats = {
            "total_records": len(data),
            "missing_values": data.isna().sum().to_dict(),
            "duplicate_records": data.duplicated().sum(),
            "date_range": None,
            "numeric_stats": {}
        }

        # Date range
        if "date" in data.columns:
            dates = pd.to_datetime(data["date"])
            stats["date_range"] = {
                "start": dates.min().isoformat(),
                "end": dates.max().isoformat(),
                "duration_days": (dates.max() - dates.min()).days
            }

        # Numeric statistics
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            valid_data = data[col].dropna()
            if len(valid_data) > 0:
                stats["numeric_stats"][col] = {
                    "count": len(valid_data),
                    "mean": float(valid_data.mean()),
                    "median": float(valid_data.median()),
                    "std": float(valid_data.std()),
                    "min": float(valid_data.min()),
                    "max": float(valid_data.max()),
                    "missing_pct": float(data[col].isna().sum() / len(data) * 100)
                }

        return stats

    def _generate_recommendations(
        self,
        issues: List[QualityIssue],
        quality_level: QualityLevel
    ) -> List[str]:
        """Generate recommendations based on issues"""
        recommendations = []

        # Group issues by type
        issue_types = {}
        for issue in issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = []
            issue_types[issue.issue_type].append(issue)

        # Generate specific recommendations
        if quality_level == QualityLevel.POOR:
            recommendations.append("URGENT: Address critical data quality issues before processing")

        # Missing data recommendations
        if "missing_data" in issue_types:
            recommendations.append("Implement data validation at source to reduce missing values")

        # Outlier recommendations
        if "statistical_outliers" in issue_types:
            recommendations.append("Review anomaly detection thresholds and investigate outliers")

        # Structure recommendations
        if "missing_columns" in issue_types:
            recommendations.append("Ensure all required data fields are captured")

        # Add issue-specific suggestions
        unique_suggestions = set()
        for issue in issues:
            if issue.suggestion and issue.suggestion not in unique_suggestions:
                recommendations.append(issue.suggestion)
                unique_suggestions.add(issue.suggestion)

        # General recommendations
        if len(issues) > 10:
            recommendations.append("Consider implementing automated data quality monitoring")

        return recommendations

    def _count_invalid_records(self, issues: List[QualityIssue]) -> int:
        """Count total invalid records from issues"""
        return sum(issue.affected_rows or 0 for issue in issues)

    async def _store_quality_history(self, symbol: str, report: QualityReport):
        """Store quality report in history"""
        if symbol not in self.quality_history:
            self.quality_history[symbol] = []

        self.quality_history[symbol].append(report)

        # Keep only last 30 reports
        if len(self.quality_history[symbol]) > 30:
            self.quality_history[symbol] = self.quality_history[symbol][-30:]

    async def get_quality_trend(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Get quality trend for a symbol"""
        if symbol not in self.quality_history:
            return {"trend": "no_data"}

        # Filter recent reports
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_reports = [
            r for r in self.quality_history[symbol]
            if r.timestamp > cutoff_date
        ]

        if len(recent_reports) < 2:
            return {"trend": "insufficient_data"}

        # Calculate trend
        scores = [r.quality_score for r in recent_reports]
        avg_score = np.mean(scores)
        score_std = np.std(scores)

        # Determine trend direction
        if len(scores) >= 5:
            recent_avg = np.mean(scores[-3:])
            older_avg = np.mean(scores[-6:-3])

            if recent_avg > older_avg + 2:
                trend = "improving"
            elif recent_avg < older_avg - 2:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "average_score": avg_score,
            "score_std": score_std,
            "score_range": (min(scores), max(scores)),
            "report_count": len(recent_reports),
            "latest_score": scores[-1]
        }

    async def batch_check(
        self,
        data_dict: Dict[str, pd.DataFrame],
        data_type: str = "price"
    ) -> Dict[str, QualityReport]:
        """Perform quality check on multiple symbols"""
        results = {}

        # Process symbols concurrently
        tasks = []
        for symbol, data in data_dict.items():
            task = self.check_market_data(data, symbol, data_type)
            tasks.append((symbol, task))

        # Execute tasks
        for symbol, task in tasks:
            try:
                report = await task
                results[symbol] = report
            except Exception as e:
                logger.error(f"Failed to check {symbol}: {e}")
                results[symbol] = None

        return results

    async def generate_quality_summary(
        self,
        reports: Dict[str, QualityReport]
    ) -> Dict[str, Any]:
        """Generate summary of quality reports"""
        if not reports:
            return {"message": "No quality reports available"}

        # Calculate aggregate statistics
        total_symbols = len(reports)
        total_records = sum(r.total_records for r in reports.values() if r)
        avg_quality_score = np.mean([r.quality_score for r in reports.values() if r])

        # Count by quality level
        quality_counts = {}
        for report in reports.values():
            if report:
                level = report.quality_level.value
                quality_counts[level] = quality_counts.get(level, 0) + 1

        # Collect common issues
        issue_counts = {}
        for report in reports.values():
            if report:
                for issue in report.issues:
                    issue_type = issue.issue_type
                    if issue_type not in issue_counts:
                        issue_counts[issue_type] = 0
                    issue_counts[issue_type] += 1

        # Generate summary
        summary = {
            "total_symbols": total_symbols,
            "total_records": total_records,
            "average_quality_score": avg_quality_score,
            "quality_distribution": quality_counts,
            "common_issues": sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "generated_at": datetime.utcnow().isoformat()
        }

        return summary

# Example usage
async def main():
    """Example usage of data quality checker"""
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta

    # Create sample data with quality issues
    dates = pd.date_range('2020-01-01', periods=100, freq='D')

    # Generate mostly normal data with some issues
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.01)

    # Introduce quality issues
    prices[10] = 0  # Zero price
    prices[20] = 10000  # Extreme price
    prices[30:35] = prices[29]  # Flat period
    prices[40] = None  # Missing value

    volumes = np.random.randint(1000000, 10000000, 100)
    volumes[50] = -100  # Negative volume

    data = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': volumes
    })

    # Create checker
    config = DataQualityConfig(
        max_price_change_pct=20.0,
        outlier_contamination=0.05
    )

    checker = DataQualityChecker(config)

    # Run quality check
    report = await checker.check_market_data(data, "EXAMPLE", "price")

    # Print results
    print(f"Quality Score: {report.quality_score:.1f}")
    print(f"Quality Level: {report.quality_level.value}")
    print(f"Total Issues: {len(report.issues)}")
    print(f"Valid Records: {report.valid_records}/{report.total_records}")
    print("\nRecommendations:")
    for rec in report.recommendations:
        print(f"- {rec}")

    # Get quality trend
    trend = await checker.get_quality_trend("EXAMPLE")
    print(f"\nQuality Trend: {trend}")


if __name__ == "__main__":
    import time
    asyncio.run(main())