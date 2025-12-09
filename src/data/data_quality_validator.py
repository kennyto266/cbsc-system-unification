"""
Phase 1: Professional Data Quality Validation and Integrity Checks
Comprehensive data validation system for quantitative trading data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path
import json
import warnings
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import joblib

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class DataQualityScore(Enum):
    """Data quality score categories"""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"          # 75-89
    FAIR = "fair"          # 60-74
    POOR = "poor"          # < 60

@dataclass
class ValidationResult:
    """Result of a validation check"""
    level: ValidationLevel
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    affected_rows: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass
class QualityReport:
    """Comprehensive data quality report"""
    symbol: str
    data_type: str
    total_records: int
    valid_records: int
    quality_score: float
    quality_category: DataQualityScore
    validation_results: List[ValidationResult]
    summary_stats: Dict[str, Any]
    recommendations: List[str]
    validation_timestamp: datetime
    data_quality_trends: Optional[Dict[str, Any]] = None

class ProfessionalDataQualityValidator:
    """Professional data quality validation system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.validation_history = {}
        self.anomaly_detectors = {}

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default validation configuration"""
        return {
            'price_columns': ['open', 'high', 'low', 'close'],
            'volume_column': 'volume',
            'date_column': 'date',
            'required_columns': ['date', 'open', 'high', 'low', 'close', 'volume'],
            'min_price_change_pct': 0.001,  # 0.1% minimum price change
            'max_price_change_pct': 0.50,   # 50% maximum price change
            'min_price': 0.01,
            'max_price': 1000000,
            'min_volume': 0,
            'max_volume_change_pct': 10.0,  # 1000% volume change threshold
            'outlier_detection': {
                'contamination': 0.1,
                'method': 'isolation_forest'
            },
            'missing_data_threshold': 0.05,  # 5% missing data threshold
            'duplicate_threshold': 0.01,     # 1% duplicate threshold
            'gap_analysis': {
                'min_gap_days': 2,
                'max_gap_days': 30
            }
        }

    def validate_market_data(self, data: pd.DataFrame, symbol: str,
                           data_type: str = "price") -> QualityReport:
        """
        Comprehensive validation of market data

        Args:
            data: DataFrame to validate
            symbol: Stock symbol
            data_type: Type of data (price, volume, etc.)

        Returns:
            QualityReport with comprehensive validation results
        """
        try:
            validation_results = []
            summary_stats = {}
            recommendations = []

            logger.info(f"Starting data quality validation for {symbol}")

            # 1. Basic structure validation
            structure_results = self._validate_structure(data, symbol)
            validation_results.extend(structure_results)

            # 2. Date and time validation
            date_results = self._validate_dates(data)
            validation_results.extend(date_results)

            # 3. Price data validation
            price_results = self._validate_prices(data)
            validation_results.extend(price_results)

            # 4. Volume data validation
            volume_results = self._validate_volume(data)
            validation_results.extend(volume_results)

            # 5. Data consistency validation
            consistency_results = self._validate_consistency(data)
            validation_results.extend(consistency_results)

            # 6. Outlier detection
            outlier_results = self._detect_outliers(data, symbol)
            validation_results.extend(outlier_results)

            # 7. Gap analysis
            gap_results = self._analyze_data_gaps(data)
            validation_results.extend(gap_results)

            # 8. Market hours validation
            market_hours_results = self._validate_market_hours(data)
            validation_results.extend(market_hours_results)

            # Calculate summary statistics
            summary_stats = self._calculate_summary_stats(data)

            # Calculate overall quality score
            quality_score = self._calculate_quality_score(validation_results)
            quality_category = self._get_quality_category(quality_score)

            # Generate recommendations
            recommendations = self._generate_recommendations(validation_results)

            # Get quality trends if historical data available
            quality_trends = self._get_quality_trends(symbol, quality_score)

            # Create quality report
            report = QualityReport(
                symbol=symbol,
                data_type=data_type,
                total_records=len(data),
                valid_records=len(data) - sum(r.affected_rows or 0 for r in validation_results
                                              if r.level in [ValidationLevel.CRITICAL, ValidationLevel.ERROR]),
                quality_score=quality_score,
                quality_category=quality_category,
                validation_results=validation_results,
                summary_stats=summary_stats,
                recommendations=recommendations,
                validation_timestamp=datetime.now(),
                data_quality_trends=quality_trends
            )

            # Store validation history
            self._store_validation_history(symbol, report)

            logger.info(f"Data quality validation completed for {symbol}. Score: {quality_score:.1f}")
            return report

        except Exception as e:
            logger.error(f"Error validating data for {symbol}: {e}")
            return QualityReport(
                symbol=symbol,
                data_type=data_type,
                total_records=len(data),
                valid_records=0,
                quality_score=0,
                quality_category=DataQualityScore.POOR,
                validation_results=[
                    ValidationResult(
                        level=ValidationLevel.CRITICAL,
                        message=f"Validation failed: {str(e)}"
                    )
                ],
                summary_stats={},
                recommendations=["Fix validation system errors"],
                validation_timestamp=datetime.now()
            )

    def _validate_structure(self, data: pd.DataFrame, symbol: str) -> List[ValidationResult]:
        """Validate basic data structure"""
        results = []

        # Check required columns
        required_cols = self.config['required_columns']
        missing_cols = set(required_cols) - set(data.columns)
        if missing_cols:
            results.append(ValidationResult(
                level=ValidationLevel.CRITICAL,
                message=f"Missing required columns: {', '.join(missing_cols)}",
                suggestion=f"Add missing columns: {', '.join(missing_cols)}"
            ))

        # Check data types
        expected_types = {
            'date': 'datetime64[ns]',
            'open': 'float64',
            'high': 'float64',
            'low': 'float64',
            'close': 'float64',
            'volume': 'int64'
        }

        for col, expected_type in expected_types.items():
            if col in data.columns:
                if col == 'date':
                    try:
                        pd.to_datetime(data[col])
                    except:
                        results.append(ValidationResult(
                            level=ValidationLevel.ERROR,
                            message=f"Column '{col}' cannot be converted to datetime",
                            suggestion="Ensure date column contains valid date strings or timestamps"
                        ))
                else:
                    try:
                        data[col].astype(expected_type)
                    except:
                        results.append(ValidationResult(
                            level=ValidationLevel.ERROR,
                            message=f"Column '{col}' cannot be converted to {expected_type}",
                            suggestion=f"Ensure {col} contains numeric values"
                        ))

        # Check empty data
        if data.empty:
            results.append(ValidationResult(
                level=ValidationLevel.CRITICAL,
                message="Data is empty",
                suggestion="Load data before validation"
            ))

        return results

    def _validate_dates(self, data: pd.DataFrame) -> List[ValidationResult]:
        """Validate date column"""
        results = []

        if 'date' not in data.columns:
            return results

        try:
            dates = pd.to_datetime(data['date'])

            # Check for invalid dates
            invalid_dates = dates.isna()
            if invalid_dates.any():
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Found {invalid_dates.sum()} invalid dates",
                    affected_rows=invalid_dates.sum(),
                    suggestion="Remove or correct invalid date values"
                ))

            # Check for duplicate dates
            duplicate_dates = dates.duplicated()
            if duplicate_dates.any():
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"Found {duplicate_dates.sum()} duplicate dates",
                    affected_rows=duplicate_dates.sum(),
                    suggestion="Aggregate or remove duplicate date records"
                ))

            # Check date range
            date_range = dates.max() - dates.min()
            if date_range.days < 1:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message="Data covers less than 1 day",
                    suggestion="Ensure data covers meaningful time period"
                ))

            # Check for future dates
            future_dates = dates > datetime.now()
            if future_dates.any():
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Found {future_dates.sum()} future dates",
                    affected_rows=future_dates.sum(),
                    suggestion="Remove future date records"
                ))

        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Date validation failed: {str(e)}",
                suggestion="Check date column format"
            ))

        return results

    def _validate_prices(self, data: pd.DataFrame) -> List[ValidationResult]:
        """Validate price data"""
        results = []
        price_cols = self.config['price_columns']

        for col in price_cols:
            if col not in data.columns:
                continue

            prices = data[col]

            # Check for missing values
            missing_prices = prices.isna()
            if missing_prices.any():
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Found {missing_prices.sum()} missing values in {col}",
                    affected_rows=missing_prices.sum(),
                    suggestion="Fill or interpolate missing price values"
                ))

            # Check for non-positive prices
            non_positive = prices <= 0
            if non_positive.any():
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Found {non_positive.sum()} non-positive values in {col}",
                    affected_rows=non_positive.sum(),
                    suggestion="Remove or correct non-positive price values"
                ))

            # Check for extreme price changes (day-over-day)
            if len(prices) > 1:
                price_changes = prices.pct_change().abs()
                extreme_changes = price_changes > self.config['max_price_change_pct']
                if extreme_changes.any():
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Found {extreme_changes.sum()} extreme price changes in {col} (> {self.config['max_price_change_pct']*100:.1f}%)",
                        affected_rows=extreme_changes.sum(),
                        suggestion="Investigate extreme price movements for data errors"
                    ))

        # Validate price relationships
        if all(col in data.columns for col in ['high', 'low']):
            invalid_range = data['high'] < data['low']
            if invalid_range.any():
                results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    message=f"Found {invalid_range.sum()} records where high < low",
                    affected_rows=invalid_range.sum(),
                    suggestion="Correct high/low price relationships"
                ))

        if all(col in data.columns for col in ['open', 'close', 'high', 'low']):
            invalid_price_range = (
                (data['high'] < data['open']) |
                (data['high'] < data['close']) |
                (data['low'] > data['open']) |
                (data['low'] > data['close'])
            )
            if invalid_price_range.any():
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"Found {invalid_price_range.sum()} records with invalid price range",
                    affected_rows=invalid_price_range.sum(),
                    suggestion="Verify OHLC price relationships"
                ))

        return results

    def _validate_volume(self, data: pd.DataFrame) -> List[ValidationResult]:
        """Validate volume data"""
        results = []
        volume_col = self.config['volume_column']

        if volume_col not in data.columns:
            return results

        volumes = data[volume_col]

        # Check for missing values
        missing_volumes = volumes.isna()
        if missing_volumes.any():
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Found {missing_volumes.sum()} missing volume values",
                affected_rows=missing_volumes.sum(),
                suggestion="Fill or interpolate missing volume values"
            ))

        # Check for negative volumes
        negative_volumes = volumes < 0
        if negative_volumes.any():
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Found {negative_volumes.sum()} negative volume values",
                affected_rows=negative_volumes.sum(),
                suggestion="Remove or correct negative volume values"
            ))

        # Check for extreme volume changes
        if len(volumes) > 1:
            volume_changes = volumes.pct_change().abs()
            extreme_changes = volume_changes > self.config['max_volume_change_pct']
            if extreme_changes.any():
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"Found {extreme_changes.sum()} extreme volume changes (> {self.config['max_volume_change_pct']*100:.1f}%)",
                    affected_rows=extreme_changes.sum(),
                    suggestion="Investigate extreme volume changes"
                ))

        return results

    def _validate_consistency(self, data: pd.DataFrame) -> List[ValidationResult]:
        """Validate data consistency"""
        results = []

        # Check for chronological order
        if 'date' in data.columns:
            dates = pd.to_datetime(data['date'])
            not_chronological = dates.is_monotonic_increasing == False
            if not_chronological:
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message="Data is not in chronological order",
                    suggestion="Sort data by date"
                ))

        # Check for data gaps
        if 'date' in data.columns and len(data) > 1:
            dates = pd.to_datetime(data['date']).sort_values()
            date_gaps = dates.diff().dt.days
            large_gaps = date_gaps > self.config['gap_analysis']['min_gap_days']
            if large_gaps.any():
                results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    message=f"Found {large_gaps.sum()} gaps in data",
                    details={'max_gap_days': date_gaps.max()},
                    suggestion="Investigate data gaps for market holidays or data issues"
                ))

        return results

    def _detect_outliers(self, data: pd.DataFrame, symbol: str) -> List[ValidationResult]:
        """Detect statistical outliers in the data"""
        results = []

        try:
            # Prepare data for outlier detection
            numeric_cols = [col for col in self.config['price_columns'] + [self.config['volume_column']]
                           if col in data.columns]

            if not numeric_cols:
                return results

            # Select clean numeric data
            clean_data = data[numeric_cols].dropna()

            if len(clean_data) < 10:  # Need minimum data points
                return results

            # Use Isolation Forest for outlier detection
            iso_forest = IsolationForest(
                contamination=self.config['outlier_detection']['contamination'],
                random_state=42
            )

            outlier_labels = iso_forest.fit_predict(clean_data)
            outlier_mask = outlier_labels == -1

            if outlier_mask.any():
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"Detected {outlier_mask.sum()} statistical outliers",
                    affected_rows=outlier_mask.sum(),
                    suggestion="Review identified outliers for potential data errors"
                ))

                # Store the trained detector for future use
                self.anomaly_detectors[symbol] = iso_forest

        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Outlier detection failed: {str(e)}",
                suggestion="Check data format for outlier detection"
            ))

        return results

    def _analyze_data_gaps(self, data: pd.DataFrame) -> List[ValidationResult]:
        """Analyze gaps in the data timeline"""
        results = []

        if 'date' not in data.columns or len(data) < 2:
            return results

        try:
            dates = pd.to_datetime(data['date']).sort_values()

            # Calculate expected trading days (excluding weekends)
            expected_days = pd.date_range(
                start=dates.min(),
                end=dates.max(),
                freq='B'  # Business days
            )

            # Find missing days
            missing_days = expected_days.difference(dates)

            if len(missing_days) > 0:
                # Categorize gaps
                short_gaps = 0
                long_gaps = 0

                for gap_start, gap_end in self._find_consecutive_gaps(missing_days):
                    gap_duration = (gap_end - gap_start).days + 1

                    if gap_duration <= 3:  # Short gap (likely holidays)
                        short_gaps += gap_duration
                    else:  # Long gap (potential data issue)
                        long_gaps += gap_duration

                if long_gaps > 0:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Found {long_gaps} days with significant data gaps",
                        details={'long_gaps': long_gaps, 'short_gaps': short_gaps},
                        suggestion="Investigate long data gaps for missing data"
                    ))

        except Exception as e:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Gap analysis failed: {str(e)}",
                suggestion="Check date format and data continuity"
            ))

        return results

    def _find_consecutive_gaps(self, missing_days: pd.DatetimeIndex) -> List[Tuple[datetime, datetime]]:
        """Find consecutive gaps in missing days"""
        gaps = []

        if len(missing_days) == 0:
            return gaps

        current_gap_start = missing_days[0]
        expected_next = missing_days[0] + timedelta(days=1)

        for i in range(1, len(missing_days)):
            if missing_days[i] != expected_next:
                # Gap ended
                gaps.append((current_gap_start, missing_days[i-1]))
                current_gap_start = missing_days[i]

            expected_next = missing_days[i] + timedelta(days=1)

        # Add the last gap
        gaps.append((current_gap_start, missing_days[-1]))

        return gaps

    def _validate_market_hours(self, data: pd.DataFrame) -> List[ValidationResult]:
        """Validate market hours (for intraday data)"""
        results = []

        # This would be relevant for intraday data
        # For daily data, we can skip this validation
        # Implementation would depend on the specific market hours

        return results

    def _calculate_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics"""
        stats = {
            'total_records': len(data),
            'date_range': None,
            'price_stats': {},
            'volume_stats': {},
            'data_completeness': {}
        }

        if 'date' in data.columns:
            dates = pd.to_datetime(data['date'])
            stats['date_range'] = {
                'start': dates.min().isoformat(),
                'end': dates.max().isoformat(),
                'duration_days': (dates.max() - dates.min()).days
            }

        # Price statistics
        for col in self.config['price_columns']:
            if col in data.columns:
                prices = data[col].dropna()
                if len(prices) > 0:
                    stats['price_stats'][col] = {
                        'mean': float(prices.mean()),
                        'median': float(prices.median()),
                        'std': float(prices.std()),
                        'min': float(prices.min()),
                        'max': float(prices.max()),
                        'count': len(prices)
                    }

        # Volume statistics
        volume_col = self.config['volume_column']
        if volume_col in data.columns:
            volumes = data[volume_col].dropna()
            if len(volumes) > 0:
                stats['volume_stats'] = {
                    'mean': float(volumes.mean()),
                    'median': float(volumes.median()),
                    'std': float(volumes.std()),
                    'min': float(volumes.min()),
                    'max': float(volumes.max()),
                    'total': float(volumes.sum()),
                    'count': len(volumes)
                }

        # Data completeness
        for col in data.columns:
            missing_count = data[col].isna().sum()
            stats['data_completeness'][col] = {
                'missing_count': int(missing_count),
                'missing_percentage': float(missing_count / len(data) * 100)
            }

        return stats

    def _calculate_quality_score(self, validation_results: List[ValidationResult]) -> float:
        """Calculate overall quality score based on validation results"""
        if not validation_results:
            return 100.0

        score = 100.0

        # Deduct points based on validation levels
        for result in validation_results:
            if result.level == ValidationLevel.CRITICAL:
                score -= 20
            elif result.level == ValidationLevel.ERROR:
                score -= 10
            elif result.level == ValidationLevel.WARNING:
                score -= 5
            elif result.level == ValidationLevel.INFO:
                score -= 1

        return max(0.0, score)

    def _get_quality_category(self, score: float) -> DataQualityScore:
        """Get quality category based on score"""
        if score >= 90:
            return DataQualityScore.EXCELLENT
        elif score >= 75:
            return DataQualityScore.GOOD
        elif score >= 60:
            return DataQualityScore.FAIR
        else:
            return DataQualityScore.POOR

    def _generate_recommendations(self, validation_results: List[ValidationResult]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Group by validation level
        critical_results = [r for r in validation_results if r.level == ValidationLevel.CRITICAL]
        error_results = [r for r in validation_results if r.level == ValidationLevel.ERROR]
        warning_results = [r for r in validation_results if r.level == ValidationLevel.WARNING]

        # Critical issues first
        if critical_results:
            recommendations.append("URGENT: Fix critical data quality issues before proceeding")
            for result in critical_results:
                if result.suggestion:
                    recommendations.append(f"- {result.suggestion}")

        # Error issues
        if error_results:
            recommendations.append("Address data quality errors to improve reliability")
            for result in error_results:
                if result.suggestion:
                    recommendations.append(f"- {result.suggestion}")

        # Warning issues
        if warning_results:
            recommendations.append("Consider addressing warnings for optimal performance")
            # Add only unique suggestions
            suggestions = set(r.suggestion for r in warning_results if r.suggestion)
            for suggestion in suggestions:
                recommendations.append(f"- {suggestion}")

        # General recommendations
        if len(validation_results) > 10:
            recommendations.append("Consider implementing automated data quality monitoring")

        return recommendations

    def _get_quality_trends(self, symbol: str, current_score: float) -> Optional[Dict[str, Any]]:
        """Get quality trends over time"""
        if symbol not in self.validation_history:
            return None

        history = self.validation_history[symbol]
        if len(history) < 2:
            return None

        scores = [report.quality_score for report in history]
        timestamps = [report.validation_timestamp for report in history]

        # Calculate trend
        recent_scores = scores[-5:]  # Last 5 validations
        if len(recent_scores) >= 2:
            trend = 'improving' if recent_scores[-1] > recent_scores[0] else 'declining'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'recent_scores': recent_scores,
            'average_score': np.mean(scores),
            'score_variance': np.var(scores),
            'current_score': current_score
        }

    def _store_validation_history(self, symbol: str, report: QualityReport):
        """Store validation result in history"""
        if symbol not in self.validation_history:
            self.validation_history[symbol] = []

        self.validation_history[symbol].append(report)

        # Keep only last 20 validations per symbol
        if len(self.validation_history[symbol]) > 20:
            self.validation_history[symbol] = self.validation_history[symbol][-20:]

    def save_quality_report(self, report: QualityReport, file_path: str):
        """Save quality report to file"""
        try:
            # Convert to serializable format
            report_dict = {
                'symbol': report.symbol,
                'data_type': report.data_type,
                'total_records': report.total_records,
                'valid_records': report.valid_records,
                'quality_score': report.quality_score,
                'quality_category': report.quality_category.value,
                'validation_results': [
                    {
                        'level': r.level.value,
                        'message': r.message,
                        'details': r.details,
                        'affected_rows': r.affected_rows,
                        'suggestion': r.suggestion
                    }
                    for r in report.validation_results
                ],
                'summary_stats': report.summary_stats,
                'recommendations': report.recommendations,
                'validation_timestamp': report.validation_timestamp.isoformat(),
                'data_quality_trends': report.data_quality_trends
            }

            with open(file_path, 'w') as f:
                json.dump(report_dict, f, indent=2)

            logger.info(f"Quality report saved to {file_path}")

        except Exception as e:
            logger.error(f"Error saving quality report: {e}")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    validator = ProfessionalDataQualityValidator()

    # Create sample data with some quality issues
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    n_records = len(dates)

    data = pd.DataFrame({
        'date': dates,
        'open': np.random.uniform(100, 500, n_records),
        'high': np.random.uniform(101, 505, n_records),
        'low': np.random.uniform(99, 495, n_records),
        'close': np.random.uniform(100, 500, n_records),
        'volume': np.random.randint(1000000, 10000000, n_records)
    })

    # Introduce some quality issues
    data.loc[10:15, 'close'] = 0  # Zero prices
    data.loc[100, 'high'] = 10000  # Extreme price
    data.loc[200:202] = data.loc[200:202].copy()  # Duplicate dates
    data.loc[300, 'volume'] = -100  # Negative volume

    # Validate data
    report = validator.validate_market_data(data, "0700.HK")

    print(f"Quality Score: {report.quality_score:.1f}")
    print(f"Quality Category: {report.quality_category.value}")
    print(f"Total Issues: {len(report.validation_results)}")
    print(f"Recommendations: {len(report.recommendations)}")

    # Save report
    validator.save_quality_report(report, "quality_report_example.json")