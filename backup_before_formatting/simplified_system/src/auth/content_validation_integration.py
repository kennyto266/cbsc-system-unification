#!/usr/bin/env python3
"""
Phase 3: Content Validation Layer Integration
第三阶段：内容验证层集成

Main integration module that brings together all content validation components
主要内容验证组件集成模块

This module provides a unified interface for:
- Data Integrity Verification (Task 11)
- Time Series Verification (Task 12)
- Business Rules Validation (Task 13)
- Cross-Market Validation (Task 14)
- Statistical Anomaly Detection (Task 15)
- Cross-Source Validation (Tasks 16 & 18)
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from .interfaces.data_authenticity_manager import DataAuthenticityManager
from .interfaces.auth_result import AuthResult, Verdict
from .verifiers.content_validation_layer import (
    ContentValidationFactory,
    DataIntegrityVerifier,
    TimeSeriesVerifier,
    BusinessRulesValidator
)
from .verifiers.statistical_anomaly_detector import (
    StatisticalAnomalyDetector,
    create_statistical_anomaly_detector
)
from .verifiers.cross_market_validator import (
    CrossMarketValidator,
    create_cross_market_validator
)
from .verifiers.cross_source_validator import (
    CrossSourceValidator,
    create_cross_source_validator
)

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class ContentValidationConfig:
    """内容验证配置"""
    enable_integrity_verification: bool = True
    enable_timeseries_verification: bool = True
    enable_business_rules_validation: bool = True
    enable_statistical_anomaly_detection: bool = True
    enable_cross_market_validation: bool = True
    enable_cross_source_validation: bool = True

    # 性能配置
    parallel_execution: bool = True
    max_concurrent_verifiers: int = 3
    timeout_per_verifier: float = 30.0  # seconds

    # 阈值配置
    overall_confidence_threshold: float = 0.8  # 总体置信度阈值
    anomaly_rate_threshold: float = 0.1        # 异常率阈值
    consistency_threshold: float = 0.85         # 一致性阈值

    # 香港市场特定配置
    hk_market_specific_rules: bool = True
    hk_trading_hours_validation: bool = True
    hk_currency_validation: bool = True


@dataclass
class ValidationSummary:
    """验证摘要"""
    total_verifiers_run: int
    passed_verifiers: int
    failed_verifiers: int
    overall_confidence: float
    total_anomalies: int
    total_execution_time_ms: float
    verdict: Verdict
    verifier_results: Dict[str, Any] = field(default_factory=dict)
    summary_details: Dict[str, Any] = field(default_factory=dict)


class ContentValidationLayer:
    """内容验证层 - 主要集成类"""

    def __init__(self, config: Optional[ContentValidationConfig] = None):
        """
        初始化内容验证层

        Args:
            config: 内容验证配置
        """
        self.config = config or ContentValidationConfig()
        self.verifiers = {}
        self.factory = ContentValidationFactory()

        # 初始化验证器
        self._initialize_verifiers()

        # 统计信息
        self.validation_history = []
        self.performance_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'average_execution_time_ms': 0.0,
            'verifier_usage': {}
        }

        logger.info("Content Validation Layer initialized")

    def _initialize_verifiers(self):
        """初始化所有验证器"""
        try:
            if self.config.enable_integrity_verification:
                self.verifiers['data_integrity'] = self.factory.create_integrity_verifier(
                    self._get_integrity_config()
                )

            if self.config.enable_timeseries_verification:
                self.verifiers['timeseries'] = self.factory.create_timeseries_verifier(
                    self._get_timeseries_config()
                )

            if self.config.enable_business_rules_validation:
                self.verifiers['business_rules'] = self.factory.create_business_rules_verifier(
                    self._get_business_rules_config()
                )

            if self.config.enable_statistical_anomaly_detection:
                self.verifiers['statistical_anomaly'] = create_statistical_anomaly_detector(
                    self._get_anomaly_detection_config()
                )

            if self.config.enable_cross_market_validation:
                self.verifiers['cross_market'] = create_cross_market_validator(
                    self._get_cross_market_config()
                )

            if self.config.enable_cross_source_validation:
                self.verifiers['cross_source'] = create_cross_source_validator(
                    self._get_cross_source_config()
                )

            logger.info(f"Initialized {len(self.verifiers)} verifiers: {list(self.verifiers.keys())}")

        except Exception as e:
            logger.error(f"Failed to initialize verifiers: {str(e)}")
            raise

    async def validate_content(
        self,
        data: Any,
        data_id: str,
        data_type: str,
        data_source: str,
        context: Optional[Dict[str, Any]] = None,
        specific_verifiers: Optional[List[str]] = None
    ) -> ValidationSummary:
        """
        执行内容验证

        Args:
            data: 待验证的数据
            data_id: 数据唯一标识
            data_type: 数据类型
            data_source: 数据来源
            context: 验证上下文
            specific_verifiers: 指定使用的验证器列表，如果为None则使用所有可用的验证器

        Returns:
            ValidationSummary: 验证摘要
        """
        start_time = time.time()

        try:
            # 确定要使用的验证器
            verifiers_to_use = self._select_verifiers(data_type, specific_verifiers)

            if not verifiers_to_use:
                logger.warning(f"No suitable verifiers found for data type: {data_type}")
                return self._create_empty_summary(data_id, data_type, data_source, start_time)

            logger.info(f"Starting content validation for {data_id} using {len(verifiers_to_use)} verifiers")

            # 准备上下文
            validation_context = self._prepare_context(data_type, data_source, context)

            # 执行验证
            if self.config.parallel_execution and len(verifiers_to_use) > 1:
                results = await self._execute_parallel_validation(
                    data, data_id, verifiers_to_use, validation_context
                )
            else:
                results = await self._execute_sequential_validation(
                    data, data_id, verifiers_to_use, validation_context
                )

            # 处理验证结果
            summary = await self._process_validation_results(
                results, data_id, data_type, data_source, start_time
            )

            # 更新统计信息
            self._update_performance_stats(summary)

            # 添加到历史记录
            self.validation_history.append({
                'timestamp': datetime.now(),
                'data_id': data_id,
                'data_type': data_type,
                'data_source': data_source,
                'summary': summary
            })

            logger.info(f"Content validation completed for {data_id}: {summary.verdict.value} "
                       f"(confidence: {summary.overall_confidence:.3f})")

            return summary

        except Exception as e:
            logger.error(f"Content validation failed for {data_id}: {str(e)}")
            execution_time = (time.time() - start_time) * 1000

            error_summary = ValidationSummary(
                total_verifiers_run=0,
                passed_verifiers=0,
                failed_verifiers=1,
                overall_confidence=0.0,
                total_anomalies=0,
                total_execution_time_ms=execution_time,
                verdict=Verdict.ERROR,
                summary_details={'error': str(e)}
            )

            self._update_performance_stats(error_summary)
            return error_summary

    def _select_verifiers(self, data_type: str, specific_verifiers: Optional[List[str]]) -> List[str]:
        """选择要使用的验证器"""
        if specific_verifiers:
            # 使用指定的验证器
            selected = [v for v in specific_verifiers if v in self.verifiers]
        else:
            # 根据数据类型自动选择
            selected = []

            # 数据完整性验证（对所有数据类型都适用）
            if 'data_integrity' in self.verifiers:
                selected.append('data_integrity')

            # 时间序列验证（适用于时间序列数据）
            if data_type in ['stock_data', 'economic_data', 'government_data'] and 'timeseries' in self.verifiers:
                selected.append('timeseries')

            # 业务规则验证（根据数据类型）
            if data_type in ['stock_data', 'government_data', 'economic_data'] and 'business_rules' in self.verifiers:
                selected.append('business_rules')

            # 统计异常检测（适用于数值数据）
            if data_type in ['stock_data', 'economic_data'] and 'statistical_anomaly' in self.verifiers:
                selected.append('statistical_anomaly')

            # 跨市场验证（适用于市场数据）
            if data_type in ['stock_data', 'forex_data'] and 'cross_market' in self.verifiers:
                selected.append('cross_market')

            # 跨源验证（适用于多源数据）
            if 'cross_source' in self.verifiers:
                selected.append('cross_source')

        return selected

    def _prepare_context(self, data_type: str, data_source: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """准备验证上下文"""
        prepared_context = {
            'data_type': data_type,
            'data_source': data_source,
            'hk_market_specific': self.config.hk_market_specific_rules,
            'validation_timestamp': datetime.now().isoformat()
        }

        # 添加用户提供的上下文
        if context:
            prepared_context.update(context)

        # 添加香港市场特定信息
        if self.config.hk_market_specific_rules and data_type == 'stock_data':
            prepared_context.update({
                'market': 'HK',
                'currency': 'HKD',
                'trading_hours_validation': self.config.hk_trading_hours_validation,
                'currency_validation': self.config.hk_currency_validation
            })

        return prepared_context

    async def _execute_parallel_validation(
        self, data: Any, data_id: str, verifiers: List[str], context: Dict[str, Any]
    ) -> List[AuthResult]:
        """并行执行验证"""
        semaphore = asyncio.Semaphore(self.config.max_concurrent_verifiers)

        async def run_verifier(verifier_name: str):
            async with semaphore:
                try:
                    verifier = self.verifiers[verifier_name]
                    result = await verifier.verify(data, data_id, context)
                    result.verifier_type = verifier_name
                    return result
                except asyncio.TimeoutError:
                    logger.error(f"Verifier {verifier_name} timed out for {data_id}")
                    return self._create_timeout_result(verifier_name, data_id, context)
                except Exception as e:
                    logger.error(f"Verifier {verifier_name} failed for {data_id}: {str(e)}")
                    return self._create_error_result(verifier_name, data_id, context, str(e))

        tasks = [run_verifier(v) for v in verifiers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception in verifier {verifiers[i]}: {result}")
                processed_results.append(self._create_error_result(verifiers[i], data_id, context, str(result)))
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_sequential_validation(
        self, data: Any, data_id: str, verifiers: List[str], context: Dict[str, Any]
    ) -> List[AuthResult]:
        """顺序执行验证"""
        results = []

        for verifier_name in verifiers:
            try:
                verifier = self.verifiers[verifier_name]
                result = await verifier.verify(data, data_id, context)
                result.verifier_type = verifier_name
                results.append(result)

            except asyncio.TimeoutError:
                logger.error(f"Verifier {verifier_name} timed out for {data_id}")
                results.append(self._create_timeout_result(verifier_name, data_id, context))

            except Exception as e:
                logger.error(f"Verifier {verifier_name} failed for {data_id}: {str(e)}")
                results.append(self._create_error_result(verifier_name, data_id, context, str(e)))

        return results

    async def _process_validation_results(
        self, results: List[AuthResult], data_id: str, data_type: str, data_source: str, start_time: float
    ) -> ValidationSummary:
        """处理验证结果"""
        total_execution_time_ms = (time.time() - start_time) * 1000

        # 统计结果
        total_verifiers = len(results)
        passed_verifiers = sum(1 for r in results if r.overall_verdict == Verdict.AUTHENTIC)
        failed_verifiers = total_verifiers - passed_verifiers

        # 计算总体置信度
        confidences = [r.overall_confidence for r in results if r.overall_confidence > 0]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # 统计异常数量
        total_anomalies = 0
        verifier_results = {}

        for result in results:
            verifier_results[result.verifier_type] = {
                'verdict': result.overall_verdict.value,
                'confidence': result.overall_confidence,
                'execution_time_ms': result.total_execution_time_ms,
                'metadata': result.metadata
            }

            # 统计异常
            if 'total_anomalies' in result.metadata:
                total_anomalies += result.metadata['total_anomalies']
            elif 'anomaly_results' in result.metadata:
                for anomaly_result in result.metadata['anomaly_results']:
                    total_anomalies += anomaly_result.get('anomaly_count', 0)

        # 确定最终结论
        if overall_confidence >= self.config.overall_confidence_threshold and failed_verifiers == 0:
            verdict = Verdict.AUTHENTIC
        elif overall_confidence >= 0.6 and failed_verifiers <= total_verifiers * 0.2:
            verdict = Verdict.SUSPICIOUS
        else:
            verdict = Verdict.FALSIFIED

        # 创建摘要详情
        summary_details = {
            'data_type': data_type,
            'data_source': data_source,
            'confidence_threshold': self.config.overall_confidence_threshold,
            'anomaly_rate': total_anomalies / (total_verifiers * 10) if total_verifiers > 0 else 0,  # 估计值
            'consistency_score': passed_verifiers / total_verifiers if total_verifiers > 0 else 0,
            'performance_breakdown': {
                'avg_verifier_time_ms': total_execution_time_ms / total_verifiers if total_verifiers > 0 else 0,
                'fastest_verifier': min(verifier_results.items(), key=lambda x: x[1]['execution_time_ms'])[0] if verifier_results else None,
                'slowest_verifier': max(verifier_results.items(), key=lambda x: x[1]['execution_time_ms'])[0] if verifier_results else None
            }
        }

        summary = ValidationSummary(
            total_verifiers_run=total_verifiers,
            passed_verifiers=passed_verifiers,
            failed_verifiers=failed_verifiers,
            overall_confidence=overall_confidence,
            total_anomalies=total_anomalies,
            total_execution_time_ms=total_execution_time_ms,
            verdict=verdict,
            verifier_results=verifier_results,
            summary_details=summary_details
        )

        return summary

    def _create_timeout_result(self, verifier_name: str, data_id: str, context: Dict[str, Any]) -> AuthResult:
        """创建超时结果"""
        return AuthResult(
            data_id=data_id,
            data_type=context.get('data_type', 'unknown'),
            data_source=context.get('data_source', 'unknown'),
            overall_verdict=Verdict.ERROR,
            overall_confidence=0.0,
            status="timeout",
            total_execution_time_ms=self.config.timeout_per_verifier * 1000,
            error_message=f"Verifier {verifier_name} timed out after {self.config.timeout_per_verifier} seconds"
        )

    def _create_error_result(self, verifier_name: str, data_id: str, context: Dict[str, Any], error_msg: str) -> AuthResult:
        """创建错误结果"""
        return AuthResult(
            data_id=data_id,
            data_type=context.get('data_type', 'unknown'),
            data_source=context.get('data_source', 'unknown'),
            overall_verdict=Verdict.ERROR,
            overall_confidence=0.0,
            status="failed",
            total_execution_time_ms=0,
            error_message=f"Verifier {verifier_name} failed: {error_msg}"
        )

    def _create_empty_summary(self, data_id: str, data_type: str, data_source: str, start_time: float) -> ValidationSummary:
        """创建空摘要"""
        execution_time_ms = (time.time() - start_time) * 1000
        return ValidationSummary(
            total_verifiers_run=0,
            passed_verifiers=0,
            failed_verifiers=0,
            overall_confidence=0.0,
            total_anomalies=0,
            total_execution_time_ms=execution_time_ms,
            verdict=Verdict.UNKNOWN,
            summary_details={'message': 'No suitable verifiers available'}
        )

    def _update_performance_stats(self, summary: ValidationSummary):
        """更新性能统计"""
        self.performance_stats['total_validations'] += 1

        if summary.verdict != Verdict.ERROR:
            self.performance_stats['successful_validations'] += 1
        else:
            self.performance_stats['failed_validations'] += 1

        # 更新平均执行时间
        total_time = (self.performance_stats['average_execution_time_ms'] *
                     (self.performance_stats['total_validations'] - 1) +
                     summary.total_execution_time_ms)
        self.performance_stats['average_execution_time_ms'] = total_time / self.performance_stats['total_validations']

        # 更新验证器使用统计
        for verifier_name in summary.verifier_results:
            if verifier_name not in self.performance_stats['verifier_usage']:
                self.performance_stats['verifier_usage'][verifier_name] = 0
            self.performance_stats['verifier_usage'][verifier_name] += 1

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.performance_stats.copy()

    def get_validation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取验证历史"""
        if limit:
            return self.validation_history[-limit:]
        return self.validation_history.copy()

    # 配置获取方法
    def _get_integrity_config(self) -> Dict[str, Any]:
        """获取数据完整性验证配置"""
        return {
            'expected_hashes': self.config.get('expected_hashes', {}),
            'data_type': self.config.get('data_type', 'unknown')
        }

    def _get_timeseries_config(self) -> Dict[str, Any]:
        """获取时间序列验证配置"""
        return {
            'max_allowed_gap_hours': self.config.get('max_allowed_gap_hours', 24),
            'duplicate_threshold_seconds': self.config.get('duplicate_threshold_seconds', 1),
            'data_type': self.config.get('data_type', 'unknown')
        }

    def _get_business_rules_config(self) -> Dict[str, Any]:
        """获取业务规则验证配置"""
        return {
            'hk_market_specific': self.config.hk_market_specific_rules,
            'trading_hours_validation': self.config.hk_trading_hours_validation,
            'currency_validation': self.config.hk_currency_validation,
            'data_type': self.config.get('data_type', 'unknown')
        }

    def _get_anomaly_detection_config(self) -> Dict[str, Any]:
        """获取异常检测配置"""
        return {
            'z_score_threshold': self.config.get('z_score_threshold', 3.0),
            'iqr_multiplier': self.config.get('iqr_multiplier', 1.5),
            'isolation_forest_contamination': self.config.get('isolation_forest_contamination', 0.1),
            'volatility_window': self.config.get('volatility_window', 20),
            'volatility_threshold': self.config.get('volatility_threshold', 2.0),
            'min_samples_for_analysis': self.config.get('min_samples_for_analysis', 30)
        }

    def _get_cross_market_config(self) -> Dict[str, Any]:
        """获取跨市场验证配置"""
        return {
            'correlation_threshold': self.config.get('correlation_threshold', 0.7),
            'arbitrage_threshold': self.config.get('arbitrage_threshold', 0.01),
            'exchange_rate_tolerance': self.config.get('exchange_rate_tolerance', 0.02),
            'min_data_points': self.config.get('min_data_points', 50),
            'price_column': self.config.get('price_column', 'close')
        }

    def _get_cross_source_config(self) -> Dict[str, Any]:
        """获取跨源验证配置"""
        return {
            'default_tolerance': self.config.get('default_tolerance', 0.01),
            'conflict_resolution_strategy': self.config.get('conflict_resolution_strategy', 'weighted_average'),
            'min_sources_for_comparison': self.config.get('min_sources_for_comparison', 2),
            'max_sources_for_comparison': self.config.get('max_sources_for_comparison', 10),
            'price_tolerance': self.config.get('price_tolerance', 0.005),
            'volume_tolerance': self.config.get('volume_tolerance', 0.05)
        }

    async def update_config(self, new_config: ContentValidationConfig):
        """更新配置"""
        old_config = self.config
        self.config = new_config

        # 重新初始化验证器（如果配置有重大变化）
        if (old_config.enable_integrity_verification != new_config.enable_integrity_verification or
            old_config.enable_timeseries_verification != new_config.enable_timeseries_verification or
            old_config.enable_business_rules_validation != new_config.enable_business_rules_validation or
            old_config.enable_statistical_anomaly_detection != new_config.enable_statistical_anomaly_detection or
            old_config.enable_cross_market_validation != new_config.enable_cross_market_validation or
            old_config.enable_cross_source_validation != new_config.enable_cross_source_validation):

            await self._reinitialize_verifiers()

        logger.info("Content validation configuration updated")

    async def _reinitialize_verifiers(self):
        """重新初始化验证器"""
        self.verifiers.clear()
        self._initialize_verifiers()


# 工厂函数
def create_content_validation_layer(config: Optional[ContentValidationConfig] = None) -> ContentValidationLayer:
    """创建内容验证层"""
    return ContentValidationLayer(config)


# 与DataAuthenticityManager集成的便捷函数
def integrate_with_data_authenticity_manager(manager: DataAuthenticityManager, config: Optional[ContentValidationConfig] = None):
    """将内容验证层集成到数据真实性管理器"""
    content_validator = create_content_validation_layer(config)

    async def content_verification_wrapper(data: Any, data_id: str, context: Optional[Dict[str, Any]] = None):
        """内容验证包装器"""
        data_type = context.get('data_type', 'unknown') if context else 'unknown'
        data_source = context.get('data_source', 'unknown') if context else 'unknown'

        summary = await content_validator.validate_content(
            data, data_id, data_type, data_source, context
        )

        # 转换为AuthResult格式
        return AuthResult(
            data_id=data_id,
            data_type=data_type,
            data_source=data_source,
            overall_verdict=summary.verdict,
            overall_confidence=summary.overall_confidence,
            status="completed",
            total_execution_time_ms=summary.total_execution_time_ms,
            metadata={
                'validation_summary': summary.__dict__,
                'total_verifiers': summary.total_verifiers_run,
                'passed_verifiers': summary.passed_verifiers
            }
        )

    # 注册到管理器
    from .interfaces.verifier_interface import IVerifier

    class ContentVerificationWrapper(IVerifier):
        def __init__(self):
            super().__init__("ContentValidationLayer", {})

        async def verify(self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None):
            return await content_verification_wrapper(data, data_id, context)

        def get_verifier_type(self) -> str:
            return "content_validation_layer"

        def get_supported_data_types(self) -> List[str]:
            return ["stock_data", "government_data", "economic_data", "forex_data", "commodity_data"]

    wrapper = ContentVerificationWrapper()
    manager.register_verifier(wrapper)

    logger.info("Content validation layer integrated with DataAuthenticityManager")
    return content_validator


# Export
__all__ = [
    'ContentValidationLayer',
    'ContentValidationConfig',
    'ValidationSummary',
    'create_content_validation_layer',
    'integrate_with_data_authenticity_manager'
]