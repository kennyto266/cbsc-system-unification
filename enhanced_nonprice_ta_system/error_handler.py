#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Error Handler
增強錯誤處理系統 - 基於OpenSpec enhance-nonprice-ta-system提案

提供智能重試、錯誤恢復、後備機制等功能
"""

import time
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum
import asyncio
import requests
from functools import wraps

class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """錯誤分類"""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    DATA_ERROR = "data_error"
    CALCULATION_ERROR = "calculation_error"
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_ERROR = "configuration_error"

@dataclass
class ErrorRecord:
    """錯誤記錄"""
    timestamp: float = field(default_factory=time.time)
    error_type: str = ""
    error_message: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.SYSTEM_ERROR
    traceback_info: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    resolved: bool = False

class RetryStrategy:
    """重試策略配置"""

    def __init__(self,
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """計算重試延遲"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 50-100% 的延遲

        return delay

class FallbackDataGenerator:
    """後備數據生成器"""

    def __init__(self):
        self.fallback_configs = {
            'HB': {'default': 3.5, 'volatility': 0.2},  # HIBOR利率
            'MB': {'default': 2000000, 'volatility': 50000},  # 貨幣基礎
            'GD': {'default': 100, 'volatility': 2.0},  # GDP
            'RT': {'default': 120, 'volatility': 5.0},  # 零售
            'PT': {'default': 180, 'volatility': 8.0},  # 物業
            'TR': {'default': 400, 'volatility': 15.0},  # 貿易
            'TS': {'default': 30000, 'volatility': 1000},  # 旅遊
            'CP': {'default': 105, 'volatility': 1.0},  # CPI
            'UE': {'default': 3.2, 'volatility': 0.3}   # 失業率
        }

    def generate_fallback_data(self, source_code: str, length: int) -> List[float]:
        """生成後備數據"""
        config = self.fallback_configs.get(source_code, {
            'default': 100.0,
            'volatility': 5.0
        })

        import numpy as np
        default_value = config['default']
        volatility = config['volatility']

        # 生成帶有輕微隨機波動的數據
        noise = np.random.normal(0, volatility, length)
        data = [default_value + x for x in noise]

        return data

class EnhancedErrorHandler:
    """
    增強錯誤處理器
    提供智能重試、後備機制、錯誤分析等功能
    """

    def __init__(self,
                 retry_strategy: Optional[RetryStrategy] = None,
                 enable_fallback: bool = True):
        self.retry_strategy = retry_strategy or RetryStrategy()
        self.enable_fallback = enable_fallback
        self.fallback_generator = FallbackDataGenerator()

        # 錯誤記錄
        self.error_history: List[ErrorRecord] = []
        self.error_stats: Dict[str, int] = {}

        # 設置日誌
        self.logger = logging.getLogger('EnhancedErrorHandler')
        self.logger.setLevel(logging.WARNING)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def record_error(self,
                    error: Exception,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.SYSTEM_ERROR,
                    context: Optional[Dict[str, Any]] = None):
        """記錄錯誤"""
        record = ErrorRecord(
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            traceback_info=traceback.format_exc(),
            context=context or {}
        )

        self.error_history.append(record)

        # 更新統計
        error_key = f"{category.value}_{record.error_type}"
        self.error_stats[error_key] = self.error_stats.get(error_key, 0) + 1

        # 記錄日誌
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(severity, logging.WARNING)

        self.logger.log(log_level,
                       f"[{severity.value.upper()}] {category.value}: {record.error_message}")

        # 限制歷史記錄數量
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]

    def get_error_summary(self) -> Dict[str, Any]:
        """獲取錯誤總結"""
        total_errors = len(self.error_history)
        severity_counts = {}
        category_counts = {}

        for record in self.error_history:
            severity_counts[record.severity.value] = severity_counts.get(record.severity.value, 0) + 1
            category_counts[record.category.value] = category_counts.get(record.category.value, 0) + 1

        recent_errors = [r for r in self.error_history
                        if time.time() - r.timestamp < 3600]  # 最近1小時

        return {
            'total_errors': total_errors,
            'recent_errors_1h': len(recent_errors),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'error_types': dict(self.error_stats),
            'most_common_error': max(self.error_stats.items(), key=lambda x: x[1])[0] if self.error_stats else None
        }

    @contextmanager
    def handle_api_errors(self, context_name: str, fallback_data_func: Optional[Callable] = None):
        """API錯誤處理上下文管理器"""
        for attempt in range(self.retry_strategy.max_retries + 1):
            try:
                yield
                return  # 成功執行，退出重試循環

            except requests.exceptions.RequestException as e:
                self.record_error(e,
                                severity=ErrorSeverity.HIGH,
                                category=ErrorCategory.NETWORK_ERROR,
                                context={'context': context_name, 'attempt': attempt})

                if attempt == self.retry_strategy.max_retries:
                    # 最後一次重試失敗，使用後備機制
                    if self.enable_fallback and fallback_data_func:
                        self.logger.warning(f"[FALLBACK] {context_name}: 使用後備數據")
                        fallback_data_func()
                        return
                    else:
                        raise

                # 等待重試
                delay = self.retry_strategy.get_delay(attempt)
                self.logger.info(f"[RETRY] {context_name}: 第{attempt + 1}次重試，延遲 {delay:.1f}秒")
                time.sleep(delay)

            except Exception as e:
                self.record_error(e,
                                severity=ErrorSeverity.CRITICAL,
                                category=ErrorCategory.API_ERROR,
                                context={'context': context_name, 'attempt': attempt})
                raise

    def safe_execute(self,
                    func: Callable,
                    *args,
                    context: str = "unknown",
                    fallback_value: Any = None,
                    **kwargs) -> Any:
        """安全執行函數，帶錯誤處理和後備值"""
        try:
            return func(*args, **kwargs)

        except Exception as e:
            self.record_error(e,
                            severity=ErrorSeverity.MEDIUM,
                            category=ErrorCategory.CALCULATION_ERROR,
                            context={'function': func.__name__, 'context': context})

            if fallback_value is not None:
                self.logger.warning(f"[FALLBACK] {context}: 使用後備值")
                return fallback_value
            else:
                raise

    def retry_with_backoff(self,
                          func: Callable,
                          max_retries: Optional[int] = None,
                          context: str = "retry_operation") -> Callable:
        """重試裝飾器"""
        if max_retries is None:
            max_retries = self.retry_strategy.max_retries

        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    self.record_error(e,
                                    severity=ErrorSeverity.MEDIUM,
                                    category=ErrorCategory.SYSTEM_ERROR,
                                    context={
                                        'function': func.__name__,
                                        'attempt': attempt,
                                        'context': context
                                    })

                    if attempt == max_retries:
                        break

                    delay = self.retry_strategy.get_delay(attempt)
                    self.logger.info(f"[RETRY] {context}: 第{attempt + 1}次重試，延遲 {delay:.1f}秒")
                    time.sleep(delay)

            raise last_exception

        return wrapper

    def validate_data_integrity(self,
                               data: List[float],
                               source_name: str,
                               expected_range: Optional[Tuple[float, float]] = None) -> bool:
        """驗證數據完整性"""
        try:
            if not data or len(data) == 0:
                raise ValueError("數據為空")

            # 檢查數據類型
            if not all(isinstance(x, (int, float)) for x in data):
                raise ValueError("數據包含非數值類型")

            # 檢查無效值
            invalid_count = sum(1 for x in data if x != x or x == float('inf') or x == float('-inf'))
            if invalid_count > 0:
                raise ValueError(f"數據包含 {invalid_count} 個無效值 (NaN/Inf)")

            # 檢查範圍
            if expected_range:
                min_val, max_val = expected_range
                out_of_range = sum(1 for x in data if not (min_val <= x <= max_val))
                if out_of_range > len(data) * 0.1:  # 超過10%的數據超出範圍
                    raise ValueError(f"{out_of_range} 個數據點超出預期範圍 [{min_val}, {max_val}]")

            return True

        except Exception as e:
            self.record_error(e,
                            severity=ErrorSeverity.MEDIUM,
                            category=ErrorCategory.DATA_ERROR,
                            context={'source': source_name, 'data_length': len(data)})
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        summary = self.get_error_summary()

        # 計算健康分數
        health_score = 100.0

        # 錯誤率扣分
        if summary['recent_errors_1h'] > 10:
            health_score -= 20
        elif summary['recent_errors_1h'] > 5:
            health_score -= 10

        # 嚴重錯誤扣分
        critical_count = summary['severity_breakdown'].get('critical', 0)
        if critical_count > 0:
            health_score -= critical_count * 15

        # 高頻錯誤扣分
        high_count = summary['severity_breakdown'].get('high', 0)
        if high_count > 5:
            health_score -= 10

        health_score = max(0, health_score)

        # 健康狀態
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 60:
            status = "fair"
        elif health_score >= 40:
            status = "poor"
        else:
            status = "critical"

        return {
            'health_score': health_score,
            'status': status,
            'error_summary': summary,
            'recommendations': self._get_health_recommendations(summary)
        }

    def _get_health_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """獲取健康改善建議"""
        recommendations = []

        if summary['recent_errors_1h'] > 10:
            recommendations.append("最近1小時錯誤過多，建議檢查系統穩定性")

        if summary['severity_breakdown'].get('critical', 0) > 0:
            recommendations.append("存在嚴重錯誤，需要立即處理")

        network_errors = summary['category_breakdown'].get('network_error', 0)
        if network_errors > 3:
            recommendations.append("網絡錯誤頻繁，建議檢查網絡連接和API端點")

        api_errors = summary['category_breakdown'].get('api_error', 0)
        if api_errors > 3:
            recommendations.append("API錯誤較多，建議檢查API調用邏輯")

        data_errors = summary['category_breakdown'].get('data_error', 0)
        if data_errors > 2:
            recommendations.append("數據質量問題，建議增強數據驗證")

        if not recommendations:
            recommendations.append("系統運行良好")

        return recommendations

    def export_error_report(self, filename: Optional[str] = None) -> str:
        """導出錯誤報告"""
        import time
        import json

        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"error_report_{timestamp}.json"

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'health_status': self.get_health_status(),
            'error_summary': self.get_error_summary(),
            'recent_errors': [
                {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r.timestamp)),
                    'error_type': r.error_type,
                    'error_message': r.error_message,
                    'severity': r.severity.value,
                    'category': r.category.value,
                    'context': r.context
                }
                for r in self.error_history[-50:]  # 最近50個錯誤
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"錯誤報告已導出: {filename}")
        return filename