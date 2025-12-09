#!/usr/bin/env python3
"""
Authentication Result Classes
认证结果类

Define data structures for authentication results and status
定义认证结果和状态的数据结构
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


class AuthStatus(Enum):
    """认证状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Verdict(Enum):
    """认证结论枚举"""
    AUTHENTIC = "authentic"      # 真实
    SUSPICIOUS = "suspicious"    # 可疑
    FALSIFIED = "falsified"      # 伪造
    UNKNOWN = "unknown"          # 未知
    ERROR = "error"              # 错误


@dataclass
class VerificationLayer:
    """单一验证层结果"""
    layer_name: str
    layer_type: str
    verdict: Verdict
    confidence: float  # 0.0 - 1.0
    execution_time_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AuthResult:
    """认证结果"""
    data_id: str
    data_type: str
    data_source: str
    overall_verdict: Verdict
    overall_confidence: float  # 0.0 - 1.0
    status: AuthStatus
    total_execution_time_ms: float

    # 分层结果
    layers: List[VerificationLayer] = field(default_factory=list)

    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    # 统计信息
    passed_layers: int = 0
    failed_layers: int = 0
    total_layers: int = 0

    def __post_init__(self):
        """初始化后处理"""
        self.total_layers = len(self.layers)
        self.passed_layers = sum(1 for layer in self.layers
                                if layer.verdict == Verdict.AUTHENTIC)
        self.failed_layers = self.total_layers - self.passed_layers

    def add_layer(self, layer: VerificationLayer):
        """添加验证层结果"""
        self.layers.append(layer)
        self.total_layers = len(self.layers)

        if layer.verdict == Verdict.AUTHENTIC:
            self.passed_layers += 1
        else:
            self.failed_layers += 1

    def get_layer_by_type(self, layer_type: str) -> Optional[VerificationLayer]:
        """根据类型获取验证层"""
        for layer in self.layers:
            if layer.layer_type == layer_type:
                return layer
        return None

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_layers == 0:
            return 0.0
        return self.passed_layers / self.total_layers

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'data_id': self.data_id,
            'data_type': self.data_type,
            'data_source': self.data_source,
            'overall_verdict': self.overall_verdict.value,
            'overall_confidence': self.overall_confidence,
            'status': self.status.value,
            'total_execution_time_ms': self.total_execution_time_ms,
            'timestamp': self.timestamp.isoformat(),
            'layers': [
                {
                    'layer_name': layer.layer_name,
                    'layer_type': layer.layer_type,
                    'verdict': layer.verdict.value,
                    'confidence': layer.confidence,
                    'execution_time_ms': layer.execution_time_ms,
                    'details': layer.details,
                    'error_message': layer.error_message,
                    'timestamp': layer.timestamp.isoformat()
                }
                for layer in self.layers
            ],
            'metadata': self.metadata,
            'error_message': self.error_message,
            'passed_layers': self.passed_layers,
            'failed_layers': self.failed_layers,
            'total_layers': self.total_layers,
            'success_rate': self.get_success_rate()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthResult':
        """从字典创建实例"""
        result = cls(
            data_id=data['data_id'],
            data_type=data['data_type'],
            data_source=data['data_source'],
            overall_verdict=Verdict(data['overall_verdict']),
            overall_confidence=data['overall_confidence'],
            status=AuthStatus(data['status']),
            total_execution_time_ms=data['total_execution_time_ms'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {}),
            error_message=data.get('error_message')
        )

        # 添加验证层
        for layer_data in data.get('layers', []):
            layer = VerificationLayer(
                layer_name=layer_data['layer_name'],
                layer_type=layer_data['layer_type'],
                verdict=Verdict(layer_data['verdict']),
                confidence=layer_data['confidence'],
                execution_time_ms=layer_data['execution_time_ms'],
                details=layer_data.get('details', {}),
                error_message=layer_data.get('error_message'),
                timestamp=datetime.fromisoformat(layer_data['timestamp'])
            )
            result.add_layer(layer)

        return result