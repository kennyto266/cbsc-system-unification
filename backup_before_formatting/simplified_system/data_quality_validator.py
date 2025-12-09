#!/usr/bin/env python3
"""
數據質量驗證框架 - 嚴格的數據驗證規則引擎
Data Quality Validation Framework - Strict Data Validation Rules Engine

提供全面的數據質量檢查，包括：
- 政府數據質量驗證
- 股票數據完整性檢查
- 數據異常檢測
- 自動化數據清理
"""

import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationRule:
    """驗證規則定義"""
    name: str
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    rule_type: str  # 'range', 'logic', 'completeness', 'consistency', 'outlier'
    parameters: Dict[str, Any]
    enabled: bool = True

@dataclass
class ValidationResult:
    """驗證結果"""
    rule_name: str
    passed: bool
    severity: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    suggested_fix: Optional[str] = None

@dataclass
class DataQualityReport:
    """數據質量報告"""
    data_source: str
    validation_timestamp: datetime
    total_records: int
    valid_records: int
    quality_score: float  # 0-100
    critical_issues: List[ValidationResult]
    high_issues: List[ValidationResult]
    medium_issues: List[ValidationResult]
    low_issues: List[ValidationResult]
    summary: Dict[str, Any] = field(default_factory=dict)

class DataQualityValidator:
    """數據質量驗證器主類"""

    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
        self.outlier_threshold = 3.0  # 3 sigma for outlier detection

    def _initialize_validation_rules(self) -> Dict[str, List[ValidationRule]]:
        """初始化驗證規則"""
        return {
            'government_data': [
                # HIBOR利率驗證規則
                ValidationRule(
                    name="hibor_rate_range",
                    description="HIBOR利率應在合理範圍內 (0-5%)",
                    severity="critical",
                    rule_type="range",
                    parameters={
                        "min_value": 0.0,
                        "max_value": 5.0,
                        "fields": ["ir_overnight", "ir_1_week", "ir_1_month", "ir_3_month", "ir_6_month", "ir_1_year"]
                    }
                ),
                ValidationRule(
                    name="hibor_completeness",
                    description="HIBOR數據應包含必要的期限利率",
                    severity="high",
                    rule_type="completeness",
                    parameters={
                        "required_fields": ["end_of_day", "ir_overnight"],
                        "min_completeness_rate": 0.95
                    }
                ),
                ValidationRule(
                    name="hibor_temporal_consistency",
                    description="HIBOR利率應按時間順序排列",
                    severity="medium",
                    rule_type="consistency",
                    parameters={
                        "date_field": "end_of_day",
                        "max_gap_days": 7
                    }
                ),

                # 匯率數據驗證規則
                ValidationRule(
                    name="exchange_rate_range",
                    description="匯率應在合理範圍內",
                    severity="critical",
                    rule_type="range",
                    parameters={
                        "fields": {"usd": [7.0, 8.0], "cny": [1.0, 1.5], "eur": [8.0, 10.0]},
                        "allow_small_deviation": 0.1
                    }
                ),
                ValidationRule(
                    name="exchange_rate_completeness",
                    description="匯率數據應包含主要貨幣",
                    severity="high",
                    rule_type="completeness",
                    parameters={
                        "required_fields": ["end_of_day"],
                        "expected_currencies": ["usd", "cny"],
                        "min_completeness_rate": 0.9
                    }
                ),

                # 貨幣基礎數據驗證規則
                ValidationRule(
                    name="monetary_base_positive",
                    description="貨幣基礎數據應為正數且合理",
                    severity="critical",
                    rule_type="range",
                    parameters={
                        "min_value": 1000000,  # 100萬
                        "max_value": 10000000000000,  # 1萬億
                        "fields": ["monetary_base", "deposits", "certificates_of_indebtedness"]
                    }
                ),
                ValidationRule(
                    name="data_volume_check",
                    description="政府數據應包含足夠的歷史記錄",
                    severity="high",
                    rule_type="completeness",
                    parameters={
                        "min_records": 30,  # 至少30天數據
                        "ideal_records": 365  # 理想情況下1年數據
                    }
                )
            ],

            'stock_data': [
                # OHLCV數據邏輯驗證
                ValidationRule(
                    name="ohlc_logic",
                    description="OHLC數據應符合邏輯關係 (high >= low, close在[low,high]範圍內)",
                    severity="critical",
                    rule_type="logic",
                    parameters={
                        "conditions": [
                            "high >= low",
                            "high >= open",
                            "high >= close",
                            "low <= open",
                            "low <= close",
                            "open > 0",
                            "close > 0",
                            "high > 0",
                            "low > 0"
                        ]
                    }
                ),
                # 價格異常跳變檢測
                ValidationRule(
                    name="price_spike_detection",
                    description="檢測單日超過20%的價格異常波動",
                    severity="high",
                    rule_type="outlier",
                    parameters={
                        "max_daily_change_pct": 20.0,
                        "price_fields": ["open", "high", "low", "close"],
                        "window_size": 5
                    }
                ),
                # 成交量異常檢測
                ValidationRule(
                    name="volume_anomaly_detection",
                    description="檢測成交量異常（超過平均值5倍）",
                    severity="medium",
                    rule_type="outlier",
                    parameters={
                        "volume_multiplier": 5.0,
                        "min_avg_volume": 1000,
                        "window_days": 20
                    }
                ),
                # 價格合理性檢查
                ValidationRule(
                    name="price_reasonableness",
                    description="股價應在合理範圍內",
                    severity="high",
                    rule_type="range",
                    parameters={
                        "min_price": 0.01,  # 最小價格1分
                        "max_price": 10000,  # 最大價格1萬
                        "price_fields": ["open", "high", "low", "close"]
                    }
                ),
                # 數據完整性檢查
                ValidationRule(
                    name="data_completeness",
                    description="股票數據應包含必要的OHLCV字段",
                    severity="critical",
                    rule_type="completeness",
                    parameters={
                        "required_fields": ["open", "high", "low", "close"],
                        "optional_fields": ["volume"],
                        "min_completeness_rate": 0.98
                    }
                ),
                # 交易日歷驗證
                ValidationRule(
                    name="trading_day_validation",
                    description="檢查交易日連續性，識別缺失的交易日",
                    severity="medium",
                    rule_type="consistency",
                    parameters={
                        "max_consecutive_missing_days": 3,
                        "exclude_weekends": True,
                        "exclude_holidays": True
                    }
                )
            ]
        }

    def validate_government_data(self, data: List[Dict[str, Any]], data_type: str) -> DataQualityReport:
        """驗證政府數據質量"""
        logger.info(f"開始驗證政府數據: {data_type}, 記錄數: {len(data)}")

        validation_results = []
        rules = self.validation_rules.get('government_data', [])

        # 通用數據量檢查
        volume_result = self._check_data_volume(data)
        validation_results.append(volume_result)

        # 根據數據類型執行特定驗證
        if data_type.lower() == 'hibor':
            hibor_results = self._validate_hibor_data(data)
            validation_results.extend(hibor_results)
        elif data_type.lower() in ['exchange_rate', 'exchange_rates']:
            exchange_results = self._validate_exchange_rate_data(data)
            validation_results.extend(exchange_results)
        elif data_type.lower() in ['monetary_base', 'monetary']:
            monetary_results = self._validate_monetary_base_data(data)
            validation_results.extend(monetary_results)

        # 生成質量報告
        return self._generate_quality_report(
            data_source=f"government_{data_type}",
            total_records=len(data),
            validation_results=validation_results,
            data=data
        )

    def validate_stock_data(self, data: Union[pd.DataFrame, Dict[str, Any]]) -> DataQualityReport:
        """驗證股票數據質量"""
        logger.info("開始驗證股票數據")

        # 轉換數據格式
        if isinstance(data, dict):
            df = self._convert_stock_dict_to_dataframe(data)
        else:
            df = data.copy()

        validation_results = []
        rules = self.validation_rules.get('stock_data', [])

        # 執行股票數據驗證規則
        for rule in rules:
            if rule.enabled:
                result = self._apply_validation_rule(df, rule)
                validation_results.append(result)

        # 計算有效記錄數
        valid_records = len(df)
        for result in validation_results:
            if not result.passed and result.severity == 'critical':
                # 根據嚴重問題估算無效記錄
                if 'invalid_count' in result.details:
                    valid_records -= result.details['invalid_count']

        valid_records = max(0, valid_records)

        return self._generate_quality_report(
            data_source="stock_data",
            total_records=len(df),
            validation_results=validation_results,
            data=df
        )

    def _check_data_volume(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """檢查數據量是否足夠"""
        record_count = len(data)
        min_records = 30
        ideal_records = 365

        if record_count >= ideal_records:
            passed = True
            message = f"數據量充足: {record_count}條記錄"
            suggested_fix = None
        elif record_count >= min_records:
            passed = True
            message = f"數據量可接受: {record_count}條記錄（建議收集更多歷史數據）"
            suggested_fix = "建議擴展數據收集範圍以獲得更好的分析結果"
        else:
            passed = False
            message = f"數據量不足: {record_count}條記錄，最少需要{min_records}條"
            suggested_fix = "檢查API參數配置，擴大數據收集時間範圍"

        return ValidationResult(
            rule_name="data_volume_check",
            passed=passed,
            severity="high" if not passed else "low",
            message=message,
            details={"record_count": record_count, "min_required": min_records, "ideal": ideal_records},
            suggested_fix=suggested_fix
        )

    def _validate_hibor_data(self, data: List[Dict[str, Any]]) -> List[ValidationResult]:
        """驗證HIBOR數據"""
        results = []

        if not data:
            results.append(ValidationResult(
                rule_name="hibor_data_empty",
                passed=False,
                severity="critical",
                message="HIBOR數據為空",
                suggested_fix="檢查API連接和數據解析邏輯"
            ))
            return results

        df = pd.DataFrame(data)

        # 檢查利率範圍
        rate_fields = ['ir_overnight', 'ir_1_week', 'ir_1_month', 'ir_3_month', 'ir_6_month', 'ir_1_year']
        available_rate_fields = [field for field in rate_fields if field in df.columns]

        if available_rate_fields:
            rate_violations = 0
            total_rate_checks = 0

            for field in available_rate_fields:
                if pd.api.types.is_numeric_dtype(df[field]):
                    # 檢查利率範圍 (0-5%)
                    out_of_range = ((df[field] < 0) | (df[field] > 5)).sum()
                    rate_violations += out_of_range
                    total_rate_checks += len(df)

            if total_rate_checks > 0:
                violation_rate = rate_violations / total_rate_checks
                passed = violation_rate < 0.05  # 允許5%的違規

                results.append(ValidationResult(
                    rule_name="hibor_rate_range",
                    passed=passed,
                    severity="critical" if not passed else "low",
                    message=f"HIBOR利率範圍檢查: {rate_violations}/{total_rate_checks} 超出範圍",
                    details={
                        "violations": rate_violations,
                        "total_checks": total_rate_checks,
                        "violation_rate": violation_rate
                    },
                    suggested_fix="檢查API返回的利率單位是否正確" if not passed else None
                ))

        # 檢查數據完整性
        required_fields = ['end_of_day', 'ir_overnight']
        missing_fields = [field for field in required_fields if field not in df.columns]

        if missing_fields:
            results.append(ValidationResult(
                rule_name="hibor_completeness",
                passed=False,
                severity="high",
                message=f"缺少必要字段: {missing_fields}",
                details={"missing_fields": missing_fields},
                suggested_fix="檢查API響應解析邏輯，確保正確提取所有字段"
            ))

        return results

    def _validate_exchange_rate_data(self, data: List[Dict[str, Any]]) -> List[ValidationResult]:
        """驗證匯率數據"""
        results = []

        if not data:
            results.append(ValidationResult(
                rule_name="exchange_data_empty",
                passed=False,
                severity="critical",
                message="匯率數據為空",
                suggested_fix="檢查API連接和數據解析邏輯"
            ))
            return results

        df = pd.DataFrame(data)

        # 檢查匯率範圍
        rate_ranges = {
            'usd': [7.0, 8.0],
            'cny': [1.0, 1.5],
            'eur': [8.0, 10.0]
        }

        for currency, (min_rate, max_rate) in rate_ranges.items():
            if currency in df.columns:
                if pd.api.types.is_numeric_dtype(df[currency]):
                    out_of_range = ((df[currency] < min_rate) | (df[currency] > max_rate)).sum()
                    total_checks = len(df)

                    if total_checks > 0 and out_of_range > 0:
                        results.append(ValidationResult(
                            rule_name=f"exchange_rate_range_{currency}",
                            passed=False,
                            severity="high",
                            message=f"{currency.upper()}匯率有{out_of_range}條記錄超出合理範圍[{min_rate}, {max_rate}]",
                            details={
                                "currency": currency,
                                "out_of_range": out_of_range,
                                "total_checks": total_checks,
                                "range": [min_rate, max_rate]
                            },
                            suggested_fix=f"檢查{currency}匯率數據的單位和格式"
                        ))

        return results

    def _validate_monetary_base_data(self, data: List[Dict[str, Any]]) -> List[ValidationResult]:
        """驗證貨幣基礎數據"""
        results = []

        if not data:
            results.append(ValidationResult(
                rule_name="monetary_data_empty",
                passed=False,
                severity="critical",
                message="貨幣基礎數據為空",
                suggested_fix="檢查API連接和數據解析邏輯"
            ))
            return results

        df = pd.DataFrame(data)

        # 檢查貨幣基礎數據是否為正數且合理
        monetary_fields = ['monetary_base', 'deposits', 'certificates_of_indebtedness']
        available_fields = [field for field in monetary_fields if field in df.columns]

        for field in available_fields:
            if pd.api.types.is_numeric_dtype(df[field]):
                negative_values = (df[field] < 0).sum()
                zero_values = (df[field] == 0).sum()

                if negative_values > 0:
                    results.append(ValidationResult(
                        rule_name=f"monetary_negative_{field}",
                        passed=False,
                        severity="critical",
                        message=f"{field}有{negative_values}條負值記錄",
                        details={
                            "field": field,
                            "negative_count": negative_values
                        },
                        suggested_fix="檢查數據單位和API返回格式"
                    ))

                if zero_values > len(df) * 0.1:  # 超過10%的零值
                    results.append(ValidationResult(
                        rule_name=f"monetary_excessive_zeros_{field}",
                        passed=False,
                        severity="high",
                        message=f"{field}有{zero_values}條零值記錄（可能數據缺失）",
                        details={
                            "field": field,
                            "zero_count": zero_values,
                            "zero_percentage": zero_values / len(df)
                        },
                        suggested_fix="檢查API返回的數據完整性"
                    ))

        return results

    def _apply_validation_rule(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """應用驗證規則到股票數據"""

        if rule.rule_type == "logic":
            return self._apply_logic_validation(df, rule)
        elif rule.rule_type == "outlier":
            return self._apply_outlier_validation(df, rule)
        elif rule.rule_type == "range":
            return self._apply_range_validation(df, rule)
        elif rule.rule_type == "completeness":
            return self._apply_completeness_validation(df, rule)
        elif rule.rule_type == "consistency":
            return self._apply_consistency_validation(df, rule)
        else:
            return ValidationResult(
                rule_name=rule.name,
                passed=True,
                severity="low",
                message=f"未知的規則類型: {rule.rule_type}"
            )

    def _apply_logic_validation(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """應用邏輯驗證"""
        conditions = rule.parameters.get("conditions", [])
        violations = []
        total_checks = 0

        for condition in conditions:
            if condition == "high >= low":
                if 'high' in df.columns and 'low' in df.columns:
                    invalid = (df['high'] < df['low']).sum()
                    if invalid > 0:
                        violations.append(f"high < low: {invalid}條記錄")
                    total_checks += len(df)

            elif condition == "high >= open":
                if 'high' in df.columns and 'open' in df.columns:
                    invalid = (df['high'] < df['open']).sum()
                    if invalid > 0:
                        violations.append(f"high < open: {invalid}條記錄")
                    total_checks += len(df)

            elif condition == "high >= close":
                if 'high' in df.columns and 'close' in df.columns:
                    invalid = (df['high'] < df['close']).sum()
                    if invalid > 0:
                        violations.append(f"high < close: {invalid}條記錄")
                    total_checks += len(df)

            elif condition == "low <= open":
                if 'low' in df.columns and 'open' in df.columns:
                    invalid = (df['low'] > df['open']).sum()
                    if invalid > 0:
                        violations.append(f"low > open: {invalid}條記錄")
                    total_checks += len(df)

            elif condition == "low <= close":
                if 'low' in df.columns and 'close' in df.columns:
                    invalid = (df['low'] > df['close']).sum()
                    if invalid > 0:
                        violations.append(f"low > close: {invalid}條記錄")
                    total_checks += len(df)

            elif " > 0" in condition:
                field = condition.split(" > 0")[0].strip()
                if field in df.columns:
                    invalid = (df[field] <= 0).sum()
                    if invalid > 0:
                        violations.append(f"{field} <= 0: {invalid}條記錄")
                    total_checks += len(df)

        passed = len(violations) == 0
        severity = "critical" if not passed else "low"

        return ValidationResult(
            rule_name=rule.name,
            passed=passed,
            severity=severity,
            message=f"OHLC邏輯檢查: {'通過' if passed else f'失敗 - {; .join(violations)}'}",
            details={
                "violations": violations,
                "total_checks": total_checks
            },
            suggested_fix="檢查數據源和數據處理邏輯" if not passed else None
        )

    def _apply_outlier_validation(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """應用異常值檢測驗證"""
        if rule.name == "price_spike_detection":
            return self._detect_price_spikes(df, rule)
        elif rule.name == "volume_anomaly_detection":
            return self._detect_volume_anomalies(df, rule)

        return ValidationResult(
            rule_name=rule.name,
            passed=True,
            severity="low",
            message="未知的異常檢測規則"
        )

    def _detect_price_spikes(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """檢測價格異常跳變"""
        max_change_pct = rule.parameters.get("max_daily_change_pct", 20.0)
        price_fields = rule.parameters.get("price_fields", ["close"])

        anomalies = []

        for field in price_fields:
            if field in df.columns:
                # 計算日變化百分比
                pct_change = df[field].pct_change().abs() * 100
                spike_days = (pct_change > max_change_pct).sum()

                if spike_days > 0:
                    max_spike = pct_change.max()
                    anomalies.append({
                        "field": field,
                        "spike_days": spike_days,
                        "max_spike_pct": max_spike
                    })

        passed = len(anomalies) == 0
        severity = "high" if not passed else "low"

        message = f"價格跳變檢測: {'通過' if passed else f'發現異常跳變'}"
        if not passed:
            anomaly_summary = [f"{a['field']}: {a['spike_days']}天, 最大{a['max_spike_pct']:.1f}%"
                             for a in anomalies]
            message += f" - {; .join(anomaly_summary)}"

        return ValidationResult(
            rule_name=rule.name,
            passed=passed,
            severity=severity,
            message=message,
            details={
                "anomalies": anomalies,
                "max_change_pct": max_change_pct
            },
            suggested_fix="檢查除權除息、股票分割等公司行為或數據錯誤" if not passed else None
        )

    def _detect_volume_anomalies(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """檢測成交量異常"""
        if 'volume' not in df.columns:
            return ValidationResult(
                rule_name=rule.name,
                passed=True,
                severity="low",
                message="缺少成交量數據，跳過異常檢測"
            )

        volume_multiplier = rule.parameters.get("volume_multiplier", 5.0)
        min_avg_volume = rule.parameters.get("min_avg_volume", 1000)
        window_days = rule.parameters.get("window_days", 20)

        # 計算移動平均
        rolling_avg = df['volume'].rolling(window=window_days).mean()
        volume_ratio = df['volume'] / rolling_avg

        # 檢測異常
        anomaly_days = (volume_ratio > volume_multiplier).sum()
        passed = anomaly_days == 0

        # 檢查平均成交量
        avg_volume = df['volume'].mean()
        sufficient_volume = avg_volume >= min_avg_volume

        if not sufficient_volume:
            passed = False

        severity = "medium" if not passed else "low"
        message = f"成交量異常檢測: {'通過' if passed else f'發現{anomaly_days}天異常'}"
        if not sufficient_volume:
            message += f"，平均成交量過低: {avg_volume:.0f}"

        return ValidationResult(
            rule_name=rule.name,
            passed=passed,
            severity=severity,
            message=message,
            details={
                "anomaly_days": anomaly_days,
                "avg_volume": avg_volume,
                "min_required_avg": min_avg_volume
            },
            suggested_fix="檢查數據單位或特殊事件影響" if not passed else None
        )

    def _apply_range_validation(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """應用範圍驗證"""
        if rule.name == "price_reasonableness":
            return self._validate_price_ranges(df, rule)

        return ValidationResult(
            rule_name=rule.name,
            passed=True,
            severity="low",
            message="未知的範圍驗證規則"
        )

    def _validate_price_ranges(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """驗證價格範圍合理性"""
        min_price = rule.parameters.get("min_price", 0.01)
        max_price = rule.parameters.get("max_price", 10000)
        price_fields = rule.parameters.get("price_fields", ["open", "high", "low", "close"])

        violations = {}
        total_violations = 0

        for field in price_fields:
            if field in df.columns:
                # 檢查價格範圍
                out_of_range = ((df[field] < min_price) | (df[field] > max_price)).sum()
                if out_of_range > 0:
                    violations[field] = out_of_range
                    total_violations += out_of_range

        passed = total_violations == 0
        severity = "high" if not passed else "low"

        message = f"價格範圍檢查: {'通過' if passed else f'{total_violations}條記錄超出範圍[{min_price}, {max_price}]'}"

        return ValidationResult(
            rule_name=rule.name,
            passed=passed,
            severity=severity,
            message=message,
            details={
                "violations": violations,
                "total_violations": total_violations,
                "price_range": [min_price, max_price]
            },
            suggested_fix="檢查數據單位（如是否為分而非元）或數據源錯誤" if not passed else None
        )

    def _apply_completeness_validation(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """應用完整性驗證"""
        required_fields = rule.parameters.get("required_fields", [])
        optional_fields = rule.parameters.get("optional_fields", [])
        min_completeness_rate = rule.parameters.get("min_completeness_rate", 0.98)

        all_fields = required_fields + optional_fields
        available_fields = [field for field in all_fields if field in df.columns]

        # 檢查必要字段
        missing_required = [field for field in required_fields if field not in df.columns]

        # 計算完整性
        total_required_cells = len(df) * len(required_fields)
        missing_values = 0

        for field in required_fields:
            if field in df.columns:
                missing_values += df[field].isnull().sum()

        completeness_rate = 1 - (missing_values / total_required_cells) if total_required_cells > 0 else 0

        passed = (len(missing_required) == 0) and (completeness_rate >= min_completeness_rate)
        severity = "critical" if not passed else "low"

        message = f"數據完整性檢查: {completeness_rate:.1%}，缺失{missing_values}個值"
        if missing_required:
            message += f"，缺少字段: {missing_required}"

        return ValidationResult(
            rule_name=rule.name,
            passed=passed,
            severity=severity,
            message=message,
            details={
                "completeness_rate": completeness_rate,
                "missing_values": missing_values,
                "missing_required_fields": missing_required,
                "available_fields": available_fields
            },
            suggested_fix="檢查數據解析邏輯和API返回格式" if not passed else None
        )

    def _apply_consistency_validation(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """應用一致性驗證"""
        if rule.name == "trading_day_validation":
            return self._validate_trading_days(df, rule)

        return ValidationResult(
            rule_name=rule.name,
            passed=True,
            severity="low",
            message="未知的一致性驗證規則"
        )

    def _validate_trading_days(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """驗證交易日連續性"""
        if not isinstance(df.index, pd.DatetimeIndex):
            # 嘗試轉換索引為日期
            try:
                df.index = pd.to_datetime(df.index)
            except:
                return ValidationResult(
                    rule_name=rule.name,
                    passed=True,
                    severity="low",
                    message="無法解析日期索引，跳過交易日驗證"
                )

        max_consecutive_missing = rule.parameters.get("max_consecutive_missing_days", 3)
        exclude_weekends = rule.parameters.get("exclude_weekends", True)

        # 生成日期範圍
        date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')

        # 排除週末
        if exclude_weekends:
            trading_days = date_range[date_range.dayofweek < 5]
        else:
            trading_days = date_range

        # 找出缺失的交易日
        missing_days = trading_days.difference(df.index)

        # 檢查連續缺失天數
        consecutive_missing = 0
        max_consecutive = 0

        for day in trading_days:
            if day not in df.index:
                consecutive_missing += 1
                max_consecutive = max(max_consecutive, consecutive_missing)
            else:
                consecutive_missing = 0

        passed = max_consecutive <= max_consecutive_missing
        severity = "medium" if not passed else "low"

        message = f"交易日連續性: {len(missing_days)}天缺失，最大連續缺失{max_consecutive}天"

        return ValidationResult(
            rule_name=rule.name,
            passed=passed,
            severity=severity,
            message=message,
            details={
                "missing_days": len(missing_days),
                "max_consecutive_missing": max_consecutive,
                "missing_dates": [str(d) for d in missing_days[:10]]  # 最多顯示10個
            },
            suggested_fix="檢查數據源是否遗漏交易日數據" if not passed else None
        )

    def _convert_stock_dict_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """將股票字典數據轉換為DataFrame"""
        if 'data' in data and 'close' in data['data']:
            # 處理中央API格式
            close_data = data['data']['close']
            df = pd.DataFrame.from_dict(close_data, orient='index', columns=['close'])
            df.index = pd.to_datetime(df.index)
            df.index.name = 'date'
            df = df.sort_index()

            # 如果只有收盤價，用收盤價填充其他OHLC字段
            if 'close' in df.columns:
                df['open'] = df['close']
                df['high'] = df['close']
                df['low'] = df['close']
                df['volume'] = 0  # 預設為0，因為沒有成交量數據

            return df
        else:
            # 嘗試直接轉換
            return pd.DataFrame(data)

    def _generate_quality_report(self, data_source: str, total_records: int,
                                validation_results: List[ValidationResult],
                                data: Any = None) -> DataQualityReport:
        """生成數據質量報告"""

        # 分類驗證結果
        critical_issues = [r for r in validation_results if r.severity == 'critical' and not r.passed]
        high_issues = [r for r in validation_results if r.severity == 'high' and not r.passed]
        medium_issues = [r for r in validation_results if r.severity == 'medium' and not r.passed]
        low_issues = [r for r in validation_results if r.severity == 'low' and not r.passed]

        # 計算質量評分
        critical_penalty = len(critical_issues) * 30
        high_penalty = len(high_issues) * 15
        medium_penalty = len(medium_issues) * 5
        low_penalty = len(low_issues) * 1

        quality_score = max(0, 100 - critical_penalty - high_penalty - medium_penalty - low_penalty)

        # 估算有效記錄數
        valid_records = total_records
        for issue in critical_issues:
            if 'invalid_count' in issue.details:
                valid_records -= issue.details['invalid_count']

        valid_records = max(0, valid_records)

        # 生成摘要
        summary = {
            "total_validations": len(validation_results),
            "passed_validations": len([r for r in validation_results if r.passed]),
            "failed_validations": len([r for r in validation_results if not r.passed]),
            "critical_count": len(critical_issues),
            "high_count": len(high_issues),
            "medium_count": len(medium_issues),
            "low_count": len(low_issues)
        }

        return DataQualityReport(
            data_source=data_source,
            validation_timestamp=datetime.now(),
            total_records=total_records,
            valid_records=valid_records,
            quality_score=quality_score,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            summary=summary
        )

    def generate_fix_suggestions(self, report: DataQualityReport) -> List[str]:
        """生成數據修復建議"""
        suggestions = []

        # 收集所有建議
        all_issues = report.critical_issues + report.high_issues + report.medium_issues
        for issue in all_issues:
            if issue.suggested_fix:
                suggestions.append(f"- {issue.suggested_fix}")

        # 根據質量評分添加通用建議
        if report.quality_score < 50:
            suggestions.append("- 數據質量嚴重不足，建議重新收集數據")
        elif report.quality_score < 70:
            suggestions.append("- 數據質量較差，需要重點關注並修復關鍵問題")
        elif report.quality_score < 85:
            suggestions.append("- 數據質量一般，建議修復發現的問題以提高分析準確性")

        # 去重並返回
        return list(set(suggestions))

    def save_report(self, report: DataQualityReport, output_dir: str = "data_quality_reports") -> str:
        """保存質量報告到文件"""
        Path(output_dir).mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report.data_source}_quality_report_{timestamp}.json"
        filepath = Path(output_dir) / filename

        # 轉換為可序列化的格式
        report_dict = {
            "data_source": report.data_source,
            "validation_timestamp": report.validation_timestamp.isoformat(),
            "total_records": report.total_records,
            "valid_records": report.valid_records,
            "quality_score": report.quality_score,
            "summary": report.summary,
            "critical_issues": [
                {
                    "rule_name": r.rule_name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "message": r.message,
                    "details": r.details,
                    "suggested_fix": r.suggested_fix
                }
                for r in report.critical_issues
            ],
            "high_issues": [
                {
                    "rule_name": r.rule_name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "message": r.message,
                    "details": r.details,
                    "suggested_fix": r.suggested_fix
                }
                for r in report.high_issues
            ],
            "medium_issues": [
                {
                    "rule_name": r.rule_name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "message": r.message,
                    "details": r.details,
                    "suggested_fix": r.suggested_fix
                }
                for r in report.medium_issues
            ],
            "low_issues": [
                {
                    "rule_name": r.rule_name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "message": r.message,
                    "details": r.details,
                    "suggested_fix": r.suggested_fix
                }
                for r in report.low_issues
            ],
            "fix_suggestions": self.generate_fix_suggestions(report)
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)

        logger.info(f"數據質量報告已保存: {filepath}")
        return str(filepath)

# 全局驗證器實例
validator = DataQualityValidator()

# 便捷函數
def validate_government_data(data: List[Dict[str, Any]], data_type: str) -> DataQualityReport:
    """驗證政府數據質量"""
    return validator.validate_government_data(data, data_type)

def validate_stock_data(data: Union[pd.DataFrame, Dict[str, Any]]) -> DataQualityReport:
    """驗證股票數據質量"""
    return validator.validate_stock_data(data)

def quick_data_quality_check(data: Any, data_type: str) -> Tuple[bool, float, List[str]]:
    """快速數據質量檢查"""
    if data_type in ['hibor', 'exchange_rate', 'monetary_base', 'government']:
        report = validate_government_data(data, data_type)
    else:
        report = validate_stock_data(data)

    is_healthy = report.quality_score >= 70 and len(report.critical_issues) == 0
    key_issues = [issue.message for issue in report.critical_issues + report.high_issues]

    return is_healthy, report.quality_score, key_issues

if __name__ == "__main__":
    # 測試代碼
    print("數據質量驗證框架測試")

    # 測試樣本數據
    sample_hibor_data = [
        {"end_of_day": "2024-01-01", "ir_overnight": 3.5, "ir_1_month": 4.0},
        {"end_of_day": "2024-01-02", "ir_overnight": 3.6, "ir_1_month": 4.1},
        {"end_of_day": "2024-01-03", "ir_overnight": -1.0, "ir_1_month": 4.2}  # 異常數據
    ]

    sample_stock_data = {
        "data": {
            "close": {
                "2024-01-01": 100.0,
                "2024-01-02": 105.0,
                "2024-01-03": 30.0  # 異常跳變
            }
        }
    }

    # 測試政府數據驗證
    print("\n=== 政府數據驗證測試 ===")
    hibor_report = validate_government_data(sample_hibor_data, "hibor")
    print(f"HIBOR數據質量評分: {hibor_report.quality_score:.1f}")
    print(f"嚴重問題: {len(hibor_report.critical_issues)}")
    for issue in hibor_report.critical_issues:
        print(f"  - {issue.message}")

    # 測試股票數據驗證
    print("\n=== 股票數據驗證測試 ===")
    stock_report = validate_stock_data(sample_stock_data)
    print(f"股票數據質量評分: {stock_report.quality_score:.1f}")
    print(f"嚴重問題: {len(stock_report.critical_issues)}")
    for issue in stock_report.critical_issues:
        print(f"  - {issue.message}")

    print("\n✅ 數據質量驗證框架測試完成")