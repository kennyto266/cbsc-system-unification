#!/usr/bin/env python3
"""
Verifier Interface
验证器接口

Abstract base class for all data authenticity verifiers
所有数据真实性验证器的抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .auth_result import AuthResult, Verdict


class IVerifier(ABC):
    """数据验证器接口"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化验证器

        Args:
            name: 验证器名称
            config: 验证器配置
        """
        self.name = name
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.priority = self.config.get('priority', 0)

    @abstractmethod
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
        pass

    @abstractmethod
    def get_verifier_type(self) -> str:
        """
        获取验证器类型

        Returns:
            str: 验证器类型标识符
        """
        pass

    @abstractmethod
    def get_supported_data_types(self) -> list:
        """
        获取支持的数据类型

        Returns:
            list: 支持的数据类型列表
        """
        pass

    def is_enabled(self) -> bool:
        """检查验证器是否启用"""
        return self.enabled

    def get_name(self) -> str:
        """获取验证器名称"""
        return self.name

    def get_config(self) -> Dict[str, Any]:
        """获取验证器配置"""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        更新验证器配置

        Args:
            new_config: 新配置

        Returns:
            bool: 更新是否成功
        """
        try:
            self.config.update(new_config)
            self.enabled = self.config.get('enabled', True)
            self.priority = self.config.get('priority', 0)
            return True
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康状态
        """
        return {
            'verifier': self.name,
            'type': self.get_verifier_type(),
            'enabled': self.enabled,
            'status': 'healthy' if self.enabled else 'disabled'
        }

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.get_verifier_type()}')"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()