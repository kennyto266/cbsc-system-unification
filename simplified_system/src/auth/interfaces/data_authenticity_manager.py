#!/usr / bin / env python3
"""
Data Authenticity Manager
数据真实性管理器

Unified interface for multi - layer data authenticity verification system
多层数据真实性验证系统的统一接口
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from .auth_result import AuthResult, AuthStatus, Verdict, VerificationLayer
from .verifier_interface import IVerifier

# Setup logging
logger = logging.getLogger(__name__)


class DataAuthenticityManager:
    """数据真实性管理器 - 统一认证接口"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据真实性管理器

        Args:
            config: 管理器配置
        """
        self.config = config or {}
        self.verifiers: Dict[str, IVerifier] = {}
        self.execution_history: List[AuthResult] = []
        self.max_history_size = self.config.get("max_history_size", 1000)
        self.default_timeout = self.config.get("default_timeout", 30.0)
        self.parallel_execution = self.config.get("parallel_execution", True)

        # 验证层配置
        self.layer_configs = self.config.get("layers", {})

        logger.info("DataAuthenticityManager initialized")

    def register_verifier(self, verifier: IVerifier) -> bool:
        """
        注册验证器

        Args:
            verifier: 验证器实例

        Returns:
            bool: 注册是否成功
        """
        try:
            verifier_type = verifier.get_verifier_type()
            self.verifiers[verifier_type] = verifier
            logger.info(f"Registered verifier: {verifier.name} ({verifier_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to register verifier {verifier.name}: {e}")
            return False

    def unregister_verifier(self, verifier_type: str) -> bool:
        """
        注销验证器

        Args:
            verifier_type: 验证器类型

        Returns:
            bool: 注销是否成功
        """
        if verifier_type in self.verifiers:
            verifier_name = self.verifiers[verifier_type].name
            del self.verifiers[verifier_type]
            logger.info(f"Unregistered verifier: {verifier_name} ({verifier_type})")
            return True
        return False

    def get_registered_verifiers(self) -> Dict[str, IVerifier]:
        """获取已注册的验证器"""
        return self.verifiers.copy()

    def get_verifier_types(self) -> List[str]:
        """获取验证器类型列表"""
        return list(self.verifiers.keys())

    async def verify_data(
        self,
        data: Any,
        data_id: str,
        data_type: str,
        data_source: str,
        verifier_types: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> AuthResult:
        """
        验证数据真实性

        Args:
            data: 待验证的数据
            data_id: 数据唯一标识
            data_type: 数据类型
            data_source: 数据来源
            verifier_types: 指定的验证器类型列表，如果为None则使用所有可用的验证器
            context: 验证上下文
            timeout: 超时时间

        Returns:
            AuthResult: 综合验证结果
        """
        start_time = time.time()

        # 创建基本验证结果
        result = AuthResult(
            data_id = data_id,
            data_type = data_type,
            data_source = data_source,
            overall_verdict = Verdict.UNKNOWN,
            overall_confidence = 0.0,
            status = AuthStatus.PROCESSING,
            total_execution_time_ms = 0.0,
        )

        try:
            # 确定要使用的验证器
            verifiers_to_use = self._select_verifiers(verifier_types, data_type)

            if not verifiers_to_use:
                logger.warning(
                    f"No suitable verifiers found for data type: {data_type}"
                )
                result.status = AuthStatus.COMPLETED
                result.overall_verdict = Verdict.UNKNOWN
                result.error_message = "No suitable verifiers available"
                return result

            logger.info(
                f"Starting verification for {data_id} using {len(verifiers_to_use)} verifiers"
            )

            # 执行验证
            if self.parallel_execution:
                layers = await self._execute_parallel(
                    verifiers_to_use, data, data_id, context, timeout
                )
            else:
                layers = await self._execute_sequential(
                    verifiers_to_use, data, data_id, context, timeout
                )

            # 添加验证层结果
            for layer in layers:
                result.add_layer(layer)

            # 计算综合结果
            result.overall_verdict, result.overall_confidence = (
                self._calculate_overall_result(layers)
            )
            result.status = AuthStatus.COMPLETED

            logger.info(
                f"Verification completed for {data_id}: {result.overall_verdict.value} "
                f"(confidence: {result.overall_confidence:.3f})"
            )

        except asyncio.TimeoutError:
            result.status = AuthStatus.TIMEOUT
            result.overall_verdict = Verdict.ERROR
            result.error_message = (
                f"Verification timeout after {timeout or self.default_timeout}s"
            )
            logger.error(f"Verification timeout for {data_id}")

        except Exception as e:
            result.status = AuthStatus.FAILED
            result.overall_verdict = Verdict.ERROR
            result.error_message = str(e)
            logger.error(f"Verification failed for {data_id}: {e}")

        finally:
            result.total_execution_time_ms = (time.time() - start_time) * 1000
            self._add_to_history(result)

        return result

    async def verify_batch(
        self,
        data_list: List[Dict[str, Any]],
        verifier_types: Optional[List[str]] = None,
        max_concurrent: int = 10,
    ) -> List[AuthResult]:
        """
        批量验证数据

        Args:
            data_list: 数据列表，每个元素包含 data, data_id, data_type, data_source
            verifier_types: 验证器类型列表
            max_concurrent: 最大并发数

        Returns:
            List[AuthResult]: 验证结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def verify_with_semaphore(item):
            async with semaphore:
                return await self.verify_data(
                    data = item["data"],
                    data_id = item["data_id"],
                    data_type = item["data_type"],
                    data_source = item["data_source"],
                    verifier_types = verifier_types,
                    context = item.get("context"),
                )

        logger.info(f"Starting batch verification of {len(data_list)} items")
        results = await asyncio.gather(
            *[verify_with_semaphore(item) for item in data_list], return_exceptions = True
        )

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch verification failed for item {i}: {result}")
                # 创建错误结果
                error_result = AuthResult(
                    data_id = data_list[i]["data_id"],
                    data_type = data_list[i]["data_type"],
                    data_source = data_list[i]["data_source"],
                    overall_verdict = Verdict.ERROR,
                    overall_confidence = 0.0,
                    status = AuthStatus.FAILED,
                    total_execution_time_ms = 0.0,
                    error_message = str(result),
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        return processed_results

    def _select_verifiers(
        self, verifier_types: Optional[List[str]], data_type: str
    ) -> List[IVerifier]:
        """选择适用的验证器"""
        verifiers = []

        if verifier_types:
            # 使用指定的验证器
            for vtype in verifier_types:
                if vtype in self.verifiers and self.verifiers[vtype].is_enabled():
                    verifiers.append(self.verifiers[vtype])
        else:
            # 使用所有适用的验证器
            for verifier in self.verifiers.values():
                if (
                    verifier.is_enabled()
                    and data_type in verifier.get_supported_data_types()
                ):
                    verifiers.append(verifier)

        # 按优先级排序
        verifiers.sort(key = lambda v: v.priority, reverse = True)
        return verifiers

    async def _execute_parallel(
        self,
        verifiers: List[IVerifier],
        data: Any,
        data_id: str,
        context: Optional[Dict[str, Any]],
        timeout: Optional[float],
    ) -> List[VerificationLayer]:
        """并行执行验证"""
        timeout = timeout or self.default_timeout

        tasks = [
            self._execute_single_verifier(verifier, data, data_id, context)
            for verifier in verifiers
        ]

        results = await asyncio.gather(*tasks, return_exceptions = True)

        # 处理结果和异常
        layers = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Verifier {verifiers[i].name} failed: {result}")
                layer = VerificationLayer(
                    layer_name = verifiers[i].name,
                    layer_type = verifiers[i].get_verifier_type(),
                    verdict = Verdict.ERROR,
                    confidence = 0.0,
                    execution_time_ms = 0.0,
                    error_message = str(result),
                )
            else:
                layer = result
            layers.append(layer)

        return layers

    async def _execute_sequential(
        self,
        verifiers: List[IVerifier],
        data: Any,
        data_id: str,
        context: Optional[Dict[str, Any]],
        timeout: Optional[float],
    ) -> List[VerificationLayer]:
        """顺序执行验证"""
        layers = []

        for verifier in verifiers:
            try:
                layer = await self._execute_single_verifier(
                    verifier, data, data_id, context
                )
                layers.append(layer)
            except Exception as e:
                logger.error(f"Verifier {verifier.name} failed: {e}")
                layer = VerificationLayer(
                    layer_name = verifier.name,
                    layer_type = verifier.get_verifier_type(),
                    verdict = Verdict.ERROR,
                    confidence = 0.0,
                    execution_time_ms = 0.0,
                    error_message = str(e),
                )
                layers.append(layer)

        return layers

    async def _execute_single_verifier(
        self,
        verifier: IVerifier,
        data: Any,
        data_id: str,
        context: Optional[Dict[str, Any]],
    ) -> VerificationLayer:
        """执行单个验证器"""
        start_time = time.time()

        # 执行验证
        auth_result = await verifier.verify(data, data_id, context)

        execution_time = (time.time() - start_time) * 1000

        # 创建验证层
        layer = VerificationLayer(
            layer_name = verifier.get_name(),
            layer_type = verifier.get_verifier_type(),
            verdict = auth_result.overall_verdict,
            confidence = auth_result.overall_confidence,
            execution_time_ms = execution_time,
            details = auth_result.metadata,
            error_message = auth_result.error_message,
        )

        return layer

    def _calculate_overall_result(
        self, layers: List[VerificationLayer]
    ) -> tuple[Verdict, float]:
        """计算综合验证结果"""
        if not layers:
            return Verdict.UNKNOWN, 0.0

        # 权重计算（基于验证器优先级和置信度）
        total_weight = 0.0
        weighted_score = 0.0

        verdict_scores = {
            Verdict.AUTHENTIC: 1.0,
            Verdict.SUSPICIOUS: 0.5,
            Verdict.FALSIFIED: 0.0,
            Verdict.UNKNOWN: 0.25,
            Verdict.ERROR: 0.0,
        }

        for layer in layers:
            weight = layer.confidence * 1.0  # 可以根据验证器优先级调整权重
            score = verdict_scores.get(layer.verdict, 0.0)

            total_weight += weight
            weighted_score += weight * score

        if total_weight == 0:
            return Verdict.UNKNOWN, 0.0

        overall_confidence = weighted_score / total_weight

        # 确定最终结论
        if overall_confidence >= 0.8:
            overall_verdict = Verdict.AUTHENTIC
        elif overall_confidence >= 0.5:
            overall_verdict = Verdict.SUSPICIOUS
        elif overall_confidence >= 0.2:
            overall_verdict = Verdict.UNKNOWN
        else:
            overall_verdict = Verdict.FALSIFIED

        return overall_verdict, overall_confidence

    def _add_to_history(self, result: AuthResult):
        """添加到历史记录"""
        self.execution_history.append(result)

        # 限制历史记录大小
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size :]

    def get_verification_history(self, limit: Optional[int] = None) -> List[AuthResult]:
        """获取验证历史记录"""
        if limit:
            return self.execution_history[-limit:]
        return self.execution_history.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        if not self.execution_history:
            return {
                "total_verifications": 0,
                "authentic_count": 0,
                "suspicious_count": 0,
                "falsified_count": 0,
                "error_count": 0,
                "average_confidence": 0.0,
                "average_execution_time_ms": 0.0,
                "success_rate": 0.0,
                "registered_verifiers": len(self.verifiers),
            }

        total = len(self.execution_history)
        authentic = sum(
            1 for r in self.execution_history if r.overall_verdict == Verdict.AUTHENTIC
        )
        suspicious = sum(
            1 for r in self.execution_history if r.overall_verdict == Verdict.SUSPICIOUS
        )
        falsified = sum(
            1 for r in self.execution_history if r.overall_verdict == Verdict.FALSIFIED
        )
        errors = sum(
            1 for r in self.execution_history if r.overall_verdict == Verdict.ERROR
        )

        avg_confidence = (
            sum(r.overall_confidence for r in self.execution_history) / total
        )
        avg_execution_time = (
            sum(r.total_execution_time_ms for r in self.execution_history) / total
        )

        return {
            "total_verifications": total,
            "authentic_count": authentic,
            "suspicious_count": suspicious,
            "falsified_count": falsified,
            "error_count": errors,
            "success_rate": authentic / total if total > 0 else 0.0,
            "average_confidence": avg_confidence,
            "average_execution_time_ms": avg_execution_time,
            "registered_verifiers": len(self.verifiers),
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        verifier_health = {}

        for vtype, verifier in self.verifiers.items():
            try:
                verifier_health[vtype] = await verifier.health_check()
            except Exception as e:
                verifier_health[vtype] = {
                    "verifier": verifier.name,
                    "type": vtype,
                    "enabled": False,
                    "status": f"error: {str(e)}",
                }

        return {
            "manager_status": "healthy",
            "registered_verifiers": len(self.verifiers),
            "total_verifications": len(self.execution_history),
            "verifier_health": verifier_health,
        }

    async def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up DataAuthenticityManager")

        # 清理验证器资源
        for verifier in self.verifiers.values():
            if hasattr(verifier, "cleanup"):
                try:
                    await verifier.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up verifier {verifier.name}: {e}")

        self.verifiers.clear()
        self.execution_history.clear()

        logger.info("DataAuthenticityManager cleanup completed")
