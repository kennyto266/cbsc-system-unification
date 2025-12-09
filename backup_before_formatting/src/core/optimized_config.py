"""
优化配置管理类
集中管理所有系统配置，避免硬编码
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class TechnicalAnalysisConfig:
    """技术分析配置"""

    # 移动平均线周期
    SMA_SHORT_PERIOD: int = 20
    SMA_LONG_PERIOD: int = 50

    # EMA周期
    EMA_SHORT_PERIOD: int = 12
    EMA_LONG_PERIOD: int = 26
    EMA_SIGNAL_PERIOD: int = 9

    # RSI配置
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0

    # 布林带配置
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD: float = 2.0

    # ATR配置
    ATR_PERIOD: int = 14

    # 成交量配置
    VOLUME_SMA_PERIOD: int = 20


@dataclass
class BacktestConfig:
    """回测配置"""

    # 默认参数
    DEFAULT_INITIAL_CAPITAL: float = 100000.0
    DEFAULT_COMMISSION: float = 0.001
    DEFAULT_POSITION_SIZE: float = 0.95  # 95 % 资金

    # 风险参数
    RISK_FREE_RATE: float = 0.03  # 3 % 无风险利率
    MAX_POSITION_SIZE: float = 1.0  # 最大仓位100%

    # 数据要求
    MIN_DATA_POINTS: int = 50
    MAX_CACHE_SIZE: int = 1000


@dataclass
class AgentConfig:
    """代理配置"""

    # 执行模式
    PARALLEL_EXECUTION: bool = True
    MAX_CONCURRENT_AGENTS: int = 3

    # 超时设置
    AGENT_LAUNCH_TIMEOUT: int = 30
    AGENT_ANALYSIS_TIMEOUT: int = 90
    STATUS_CHECK_INTERVAL: int = 10

    # API限制
    API_RATE_LIMIT_DELAY: float = 2.0
    CONVERSATION_CHECK_INTERVAL: int = 20


@dataclass
class PerformanceConfig:
    """性能配置"""

    # 缓存设置
    ENABLE_CACHING: bool = True
    CACHE_TTL_SECONDS: int = 300  # 5分钟

    # 内存管理
    MAX_MEMORY_USAGE_MB: int = 512
    CLEANUP_INTERVAL_SECONDS: int = 60

    # 日志级别
    LOG_LEVEL: str = "INFO"
    ENABLE_PERFORMANCE_LOGGING: bool = True


class OptimizedConfig:
    """优化配置管理器"""

    def __init__(self) -> None:
        self.technical = TechnicalAnalysisConfig()
        self.backtest = BacktestConfig()
        self.agent = AgentConfig()
        self.performance = PerformanceConfig()

        # 从环境变量加载配置
        self._load_from_env()

    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        # 技术分析配置
        self.technical.SMA_SHORT_PERIOD = int(
            os.getenv("SMA_SHORT_PERIOD", self.technical.SMA_SHORT_PERIOD)
        )
        self.technical.SMA_LONG_PERIOD = int(
            os.getenv("SMA_LONG_PERIOD", self.technical.SMA_LONG_PERIOD)
        )
        self.technical.RSI_PERIOD = int(
            os.getenv("RSI_PERIOD", self.technical.RSI_PERIOD)
        )

        # 代理配置
        self.agent.PARALLEL_EXECUTION = (
            os.getenv("PARALLEL_EXECUTION", "true").lower() == "true"
        )
        self.agent.MAX_CONCURRENT_AGENTS = int(
            os.getenv("MAX_CONCURRENT_AGENTS", self.agent.MAX_CONCURRENT_AGENTS)
        )

        # 性能配置
        self.performance.LOG_LEVEL = os.getenv("LOG_LEVEL", self.performance.LOG_LEVEL)
        self.performance.ENABLE_CACHING = (
            os.getenv("ENABLE_CACHING", "true").lower() == "true"
        )

    def get_technical_config(self) -> TechnicalAnalysisConfig:
        """获取技术分析配置"""
        return self.technical

    def get_backtest_config(self) -> BacktestConfig:
        """获取回测配置"""
        return self.backtest

    def get_agent_config(self) -> AgentConfig:
        """获取代理配置"""
        return self.agent

    def get_performance_config(self) -> PerformanceConfig:
        """获取性能配置"""
        return self.performance

    def update_config(self, section: str, key: str, value: Any) -> None:
        """动态更新配置"""
        if section == "technical" and hasattr(self.technical, key):
            setattr(self.technical, key, value)
        elif section == "backtest" and hasattr(self.backtest, key):
            setattr(self.backtest, key, value)
        elif section == "agent" and hasattr(self.agent, key):
            setattr(self.agent, key, value)
        elif section == "performance" and hasattr(self.performance, key):
            setattr(self.performance, key, value)
        else:
            raise ValueError(f"无效的配置项: {section}.{key}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "technical": self.technical.__dict__,
            "backtest": self.backtest.__dict__,
            "agent": self.agent.__dict__,
            "performance": self.performance.__dict__,
        }

    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 验证技术分析配置
            assert self.technical.SMA_SHORT_PERIOD > 0
            assert self.technical.SMA_LONG_PERIOD > self.technical.SMA_SHORT_PERIOD
            assert 0 < self.technical.RSI_OVERBOUGHT < 100
            assert 0 < self.technical.RSI_OVERSOLD < self.technical.RSI_OVERBOUGHT

            # 验证回测配置
            assert self.backtest.DEFAULT_INITIAL_CAPITAL > 0
            assert 0 <= self.backtest.DEFAULT_COMMISSION <= 1
            assert 0 < self.backtest.DEFAULT_POSITION_SIZE <= 1

            # 验证代理配置
            assert self.agent.MAX_CONCURRENT_AGENTS > 0
            assert self.agent.AGENT_LAUNCH_TIMEOUT > 0
            assert self.agent.AGENT_ANALYSIS_TIMEOUT > 0

            return True
        except AssertionError:
            return False


# 全局配置实例
config = OptimizedConfig()
