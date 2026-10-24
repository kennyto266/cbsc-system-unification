"""
优化配置管理类
集中管理所有系统配置，避免硬编码
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os
from pathlib import Path

@dataclass
class TechnicalAnalysisConfig:
"""技术分析配置"""

SMA_SHORT_PERIOD: int = 20
SMA_LONG_PERIOD: int = 50

EMA_SHORT_PERIOD: int = 12
EMA_LONG_PERIOD: int = 26
EMA_SIGNAL_PERIOD: int = 9

RSI_PERIOD: int = 14
RSI_OVERBOUGHT: float = 70.0
RSI_OVERSOLD: float = 30.0

BOLLINGER_PERIOD: int = 20
BOLLINGER_STD: float = 2.0

ATR_PERIOD: int = 14

VOLUME_SMA_PERIOD: int = 20

@dataclass
class BacktestConfig:
"""回测配置"""

DEFAULT_INITIAL_CAPITAL: float = 100000.0
DEFAULT_COMMISSION: float = 0.001
DEFAULT_POSITION_SIZE: float = 0.95 # 95%资金

RISK_FREE_RATE: float = 0.03 # 3%无风险利率
MAX_POSITION_SIZE: float = 1.0 # 最大仓位100%

MIN_DATA_POINTS: int = 50
MAX_CACHE_SIZE: int = 1000

@dataclass
class AgentConfig:
"""代理配置"""

PARALLEL_EXECUTION: bool = True
MAX_CONCURRENT_AGENTS: int = 3

AGENT_LAUNCH_TIMEOUT: int = 30
AGENT_ANALYSIS_TIMEOUT: int = 90
STATUS_CHECK_INTERVAL: int = 10

API_RATE_LIMIT_DELAY: float = 2.0
CONVERSATION_CHECK_INTERVAL: int = 20

@dataclass
class PerformanceConfig:
"""性能配置"""

ENABLE_CACHING: bool = True
CACHE_TTL_SECONDS: int = 300 # 5分钟

MAX_MEMORY_USAGE_MB: int = 512
CLEANUP_INTERVAL_SECONDS: int = 60

LOG_LEVEL: str = "INFO"
ENABLE_PERFORMANCE_LOGGING: bool = True

class OptimizedConfig:
"""优化配置管理器"""

def __init__self:    self.technical = TechnicalAnalysisConfig()
self.backtest = BacktestConfig()
self.agent = AgentConfig()
self.performance = PerformanceConfig()

# 从环境变量加载配置
self._load_from_env()

def _load_from_envself:
"""从环境变量加载配置"""

self.technical.SMA_SHORT_PERIOD = int(os.getenv'SMA_SHORT_PERIOD', self.technical.SMA_SHORT_PERIOD)
self.technical.SMA_LONG_PERIOD = int(os.getenv'SMA_LONG_PERIOD', self.technical.SMA_LONG_PERIOD)
self.technical.RSI_PERIOD = int(os.getenv'RSI_PERIOD', self.technical.RSI_PERIOD)

self.agent.PARALLEL_EXECUTION = os.getenv'PARALLEL_EXECUTION', 'true'.lower() == 'true'
self.agent.MAX_CONCURRENT_AGENTS = int(os.getenv'MAX_CONCURRENT_AGENTS', self.agent.MAX_CONCURRENT_AGENTS)

self.performance.LOG_LEVEL = os.getenv'LOG_LEVEL', self.performance.LOG_LEVEL
self.performance.ENABLE_CACHING = os.getenv'ENABLE_CACHING', 'true'.lower() == 'true'

def get_technical_configself -> TechnicalAnalysisConfig:
"""获取技术分析配置"""
return self.technical

def get_backtest_configself -> BacktestConfig:
"""获取回测配置"""
return self.backtest

def get_agent_configself -> AgentConfig:
"""获取代理配置"""
return self.agent

def get_performance_configself -> PerformanceConfig:
"""获取性能配置"""
return self.performance

def update_configself, section: str, key: str, value: Any:
"""动态更新配置"""
if section == 'technical' and hasattrself.technical, key:
setattrself.technical, key, value
elif section == 'backtest' and hasattrself.backtest, key:
setattrself.backtest, key, value
elif section == 'agent' and hasattrself.agent, key:
setattrself.agent, key, value
elif section == 'performance' and hasattrself.performance, key:
setattrself.performance, key, value
else:
raise ValueErrorf"无效的配置项: {section}.{key}"

def to_dictself -> Dict[str, Any]:
"""转换为字典格式"""
return {
'technical': self.technical.__dict__,
'backtest': self.backtest.__dict__,
'agent': self.agent.__dict__,
'performance': self.performance.__dict__
}

def validate_configself -> bool:
"""验证配置有效性"""
try:
# 验证技术分析配置
assert self.technical.SMA_SHORT_PERIOD > 0
assert self.technical.SMA_LONG_PERIOD > self.technical.SMA_SHORT_PERIOD
assert 0 < self.technical.RSI_OVERBOUGHT < 100
assert 0 < self.technical.RSI_OVERSOLD < self.technical.RSI_OVERBOUGHT

assert self.backtest.DEFAULT_INITIAL_CAPITAL > 0
assert 0 <= self.backtest.DEFAULT_COMMISSION <= 1
assert 0 < self.backtest.DEFAULT_POSITION_SIZE <= 1

assert self.agent.MAX_CONCURRENT_AGENTS > 0
assert self.agent.AGENT_LAUNCH_TIMEOUT > 0
assert self.agent.AGENT_ANALYSIS_TIMEOUT > 0

return True
except AssertionError:
return False

config = OptimizedConfig()
