#!/usr/bin/env python3
"""
Base Authenticator
基础认证器

Abstract base class for implementing data authenticity verifiers
实现数据真实性验证器的抽象基类
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from interfaces.verifier_interface import IVerifier
from interfaces.auth_result import AuthResult, AuthStatus, Verdict

# Setup logging
logger = logging.getLogger(__name__)


class BaseAuthenticator(IVerifier, ABC):
    """基础认证器抽象类"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化基础认证器

        Args:
            name: 认证器名称
            config: 认证器配置
        """
        super().__init__(name, config)

        # 性能统计
        self.stats = {
            'total_verifications': 0,
            'successful_verifications': 0,
            'failed_verifications': 0,
            'average_execution_time_ms': 0.0,
            'total_execution_time_ms': 0.0
        }

        # 认证器特定的配置
        self.timeout = self.config.get('timeout', 30.0)
        self.retry_count = self.config.get('retry_count', 3)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.cache_ttl_seconds = self.config.get('cache_ttl_seconds', 3600)

        # 缓存
        self._cache = {}

        logger.info(f"BaseAuthenticator {name} initialized")

    async def verify(self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None) -> AuthResult:
        """
        执行数据验证

        Args:
            data: 待验证的数据
            data_id: 数据ID
            context: 验证上下文

        Returns:
            AuthResult: 验证结果
        """
        start_time = time.time()

        # 创建基本结果对象
        result = AuthResult(
            data_id=data_id,
            data_type=self._get_data_type(data),
            data_source=self._get_data_source(data, context),
            overall_verdict=Verdict.UNKNOWN,
            overall_confidence=0.0,
            status=AuthStatus.PROCESSING,
            total_execution_time_ms=0.0
        )

        try:
            # 更新统计
            self.stats['total_verifications'] += 1

            # 检查缓存
            if self.cache_enabled:
                cached_result = self._get_cached_result(data_id, data)
                if cached_result:
                    logger.debug(f"Using cached result for {data_id}")
                    return cached_result

            # 预处理数据
            processed_data = await self._preprocess_data(data, context)

            # 执行实际验证
            verification_result = await self._do_verify(processed_data, data_id, context)

            # 后处理结果
            await self._postprocess_result(verification_result, data, context)

            result = verification_result
            result.status = AuthStatus.COMPLETED

            # 更新成功统计
            self.stats['successful_verifications'] += 1

            # 缓存结果
            if self.cache_enabled and result.overall_verdict != Verdict.ERROR:
                self._cache_result(data_id, data, result)

            logger.info(f"Verification completed for {data_id}: {result.overall_verdict.value}")

        except Exception as e:
            result.status = AuthStatus.FAILED
            result.overall_verdict = Verdict.ERROR
            result.error_message = str(e)
            self.stats['failed_verifications'] += 1
            logger.error(f"Verification failed for {data_id}: {e}")

        finally:
            # 更新执行时间统计
            execution_time = (time.time() - start_time) * 1000
            result.total_execution_time_ms = execution_time
            self._update_execution_stats(execution_time)

        return result

    @abstractmethod
    async def _do_verify(self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None) -> AuthResult:
        """
        执行实际验证逻辑（子类实现）

        Args:
            data: 预处理后的数据
            data_id: 数据ID
            context: 验证上下文

        Returns:
            AuthResult: 验证结果
        """
        pass

    async def _preprocess_data(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        数据预处理（子类可重写）

        Args:
            data: 原始数据
            context: 上下文

        Returns:
            Any: 预处理后的数据
        """
        return data

    async def _postprocess_result(self, result: AuthResult, data: Any, context: Optional[Dict[str, Any]] = None):
        """
        结果后处理（子类可重写）

        Args:
            result: 验证结果
            data: 原始数据
            context: 上下文
        """
        pass

    def _get_data_type(self, data: Any) -> str:
        """
        获取数据类型（子类可重写）

        Args:
            data: 数据

        Returns:
            str: 数据类型
        """
        return type(data).__name__

    def _get_data_source(self, data: Any, context: Optional[Dict[str, Any]] = None) -> str:
        """
        获取数据源（子类可重写）

        Args:
            data: 数据
            context: 上下文

        Returns:
            str: 数据源
        """
        if context and 'source' in context:
            return context['source']
        return 'unknown'

    def _get_cache_key(self, data_id: str, data: Any) -> str:
        """
        生成缓存键（子类可重写）

        Args:
            data_id: 数据ID
            data: 数据

        Returns:
            str: 缓存键
        """
        import hashlib
        data_hash = hashlib.md5(str(data).encode()).hexdigest()
        return f"{self.get_verifier_type()}:{data_id}:{data_hash}"

    def _get_cached_result(self, data_id: str, data: Any) -> Optional[AuthResult]:
        """
        获取缓存结果

        Args:
            data_id: 数据ID
            data: 数据

        Returns:
            Optional[AuthResult]: 缓存的结果
        """
        cache_key = self._get_cache_key(data_id, data)

        if cache_key in self._cache:
            cached_item = self._cache[cache_key]

            # 检查缓存是否过期
            if time.time() - cached_item['timestamp'] < self.cache_ttl_seconds:
                return cached_item['result']
            else:
                # 清理过期缓存
                del self._cache[cache_key]

        return None

    def _cache_result(self, data_id: str, data: Any, result: AuthResult):
        """
        缓存结果

        Args:
            data_id: 数据ID
            data: 数据
            result: 验证结果
        """
        cache_key = self._get_cache_key(data_id, data)

        self._cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }

        # 限制缓存大小
        max_cache_size = 1000
        if len(self._cache) > max_cache_size:
            # 删除最旧的缓存项
            oldest_key = min(self._cache.keys(),
                           key=lambda k: self._cache[k]['timestamp'])
            del self._cache[oldest_key]

    def _update_execution_stats(self, execution_time_ms: float):
        """
        更新执行统计

        Args:
            execution_time_ms: 执行时间（毫秒）
        """
        self.stats['total_execution_time_ms'] += execution_time_ms
        total_verifications = self.stats['total_verifications']

        if total_verifications > 0:
            self.stats['average_execution_time_ms'] = (
                self.stats['total_execution_time_ms'] / total_verifications
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取认证器统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'authenticator': self.name,
            'type': self.get_verifier_type(),
            'enabled': self.enabled,
            'total_verifications': self.stats['total_verifications'],
            'successful_verifications': self.stats['successful_verifications'],
            'failed_verifications': self.stats['failed_verifications'],
            'success_rate': (
                self.stats['successful_verifications'] /
                max(1, self.stats['total_verifications'])
            ),
            'average_execution_time_ms': self.stats['average_execution_time_ms'],
            'cache_enabled': self.cache_enabled,
            'cache_size': len(self._cache)
        }

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info(f"Cache cleared for {self.name}")

    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            'total_verifications': 0,
            'successful_verifications': 0,
            'failed_verifications': 0,
            'average_execution_time_ms': 0.0,
            'total_execution_time_ms': 0.0
        }
        logger.info(f"Statistics reset for {self.name}")

    async def cleanup(self):
        """清理资源"""
        logger.info(f"Cleaning up {self.name}")
        self.clear_cache()
        self.reset_statistics()

    def __str__(self) -> str:
        """字符串表示"""
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"type='{self.get_verifier_type()}', "
                f"enabled={self.enabled}, "
                f"verifications={self.stats['total_verifications']})")

    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()