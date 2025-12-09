#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-Time Strategy Monitor
实时策略监控系统

Based on Acheng's real-time trading approach, this system provides
continuous monitoring of strategy performance with automatic updates.

Features:
- Real-time performance tracking
- Automatic strategy execution and monitoring
- Performance threshold alerts
- Strategy comparison and ranking
- Live dashboard updates

Author: Strategy Dashboard Team
Date: 2025-11-30
"""

import asyncio
import threading
import time
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import logging
import pandas as pd
import numpy as np
from enum import Enum

from ..strategy_management.strategy_registry import StrategyRegistry, StrategyPerformance

# SECURITY: 安全文件操作
try:
from ..security.secure_file_validator import safe_write_file
except ImportError:
# 後備安全寫入函數
def safe_write_filefile_path, content, base_directory=None, encoding='utf-8':
try:

if '..' in strfile_path or strfile_path.startswith'/' or strfile_path.startswith'\\':
return False
with openfile_path, 'w', encoding=encoding as f:
f.writecontent
return True
except:
return False
from ..analytics.performance_analyzer import StandardPerformanceAnalyzer, PerformanceConfig

logger = logging.getLogger__name__

class AlertLevelstr, Enum:
"""警报级别"""
INFO = "info"
WARNING = "warning"
CRITICAL = "critical"

class StrategyStatusstr, Enum:
"""策略状态"""
ACTIVE = "active"
INACTIVE = "inactive"
WARNING = "warning"
ERROR = "error"

@dataclass
class PerformanceAlert:
"""绩效警报"""
strategy_id: str
alert_level: AlertLevel
message: str
current_value: float
threshold_value: float
timestamp: datetime = fielddefault_factory=datetime.now

@dataclass
class MonitoringConfig:
"""监控配置"""
update_interval: int = 60 # 更新间隔秒
lookback_days: int = 30 # 回看天数
sharpe_threshold: float = 0.5 # 夏普比率阈值
mdd_threshold: float = -0.20 # 最大回撤阈值
min_trades_threshold: int = 10 # 最小交易次数阈值
enable_alerts: bool = True
max_consecutive_losses: int = 5 # 连续亏损阈值
performance_decay_threshold: float = -0.10 # 绩效衰减阈值

class RealTimeStrategyMonitor:
"""
实时策略监控器

基于阿程的实时监控思路，提供持续的性能跟踪和警报
"""

def __init__(
self,
strategy_registry: StrategyRegistry,
config: Optional[MonitoringConfig] = None
):
"""
初始化实时监控器

Args:
strategy_registry: 策略注册中心
config: 监控配置
"""
self.registry = strategy_registry
self.config = config or MonitoringConfig()
self.performance_analyzer = StandardPerformanceAnalyzer(
PerformanceConfiglookback_days=self.config.lookback_days
)

self.is_monitoring = False
self.monitoring_thread: Optional[threading.Thread] = None

self.live_performances: Dict[str, Dict[str, Any]] = {}
self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
self.alerts: List[PerformanceAlert] = []
self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []

self.last_update_time = None
self.total_updates = 0
self.start_time = None

logger.infof"Initialized real-time monitor with {self.config.update_interval}s interval"

def start_monitoringself:
"""开始监控"""
if self.is_monitoring:
logger.warning"Monitoring is already running"
return

self.is_monitoring = True
self.start_time = datetime.now()

self.monitoring_thread = threading.Threadtarget=self._monitoring_loop, daemon=True
self.monitoring_thread.start()

logger.info"Started real-time strategy monitoring"

def stop_monitoringself:
"""停止监控"""
if not self.is_monitoring:
return

self.is_monitoring = False

if self.monitoring_thread and self.monitoring_thread.is_alive():    self.monitoring_thread.join(timeout=5)

logger.info"Stopped real-time strategy monitoring"

def _monitoring_loopself:
"""监控主循环"""
logger.info"Starting monitoring loop"

while self.is_monitoring:
try:

self._update_all_strategies()

if self.config.enable_alerts:
self._check_alert_conditions()

self.last_update_time = datetime.now()
self.total_updates += 1

time.sleepself.config.update_interval

except Exception as e:
logger.errorf"Error in monitoring loop: {e}"
time.sleepself.config.update_interval

logger.info"Monitoring loop ended"

def _update_all_strategiesself:
"""更新所有策略的绩效"""
strategies = self.registry.get_all_strategies()

for strategy in strategies:
try:
# 获取或计算策略绩效
performance_data = self._calculate_strategy_performancestrategy
strategy_id = strategy.id

self.live_performances[strategy_id] = performance_data

if strategy_id not in self.performance_history:    self.performance_history[strategy_id] = []

history_entry = {
"timestamp": datetime.now().isoformat(),
**performance_data
}
self.performance_history[strategy_id].appendhistory_entry

# 保持历史记录在合理范围内
max_history = 1000
if lenself.performance_history[strategy_id] > max_history:    self.performance_history[strategy_id] = self.performance_history[strategy_id][-max_history:]

# 更新注册表中的绩效
self._update_registry_performancestrategy_id, performance_data

except Exception as e:
logger.errorf"Failed to update performance for strategy {strategy.id}: {e}"

def _calculate_strategy_performanceself, strategy -> Dict[str, Any]:
"""计算策略绩效"""
try:
# 模拟实时数据 实际应用中应该从数据源获取
current_time = datetime.now()

# 生成模拟收益率数据
base_return = np.random.normal0.001, 0.02 # 日均收益率
if strategy.category.value == "machine_learning":    base_return *= 1.2  # ML策略稍微好一些
elif strategy.category.value == "technical_analysis":    base_return *= 0.9

strategy_id = strategy.id
if strategy_id in self.performance_history and lenself.performance_history[strategy_id] > 10:
# 基于历史数据生成更真实的模拟
recent_returns = [
entry.get"daily_return", 0
for entry in self.performance_history[strategy_id][-10:]
]
mean_return = np.meanrecent_returns
std_return = np.stdrecent_returns
base_return = np.random.normalmean_return, std_return

if strategy_id in self.live_performances:    prev_total_return = self.live_performances[strategy_id].get("total_return", 0)
total_return = prev_total_return + base_return
else:    total_return = base_return

annual_return = total_return * 252 / max(1, len(self.performance_history.getstrategy_id, []))
volatility = 0.15 # 简化假设
sharpe_ratio = annual_return - 0.03 / volatility if volatility > 0 else 0

# 最大回撤 简化计算
max_drawdown = min-0.05, total_return * -0.5 if total_return < 0 else -0.02

trades_count = len(self.performance_history.getstrategy_id, [])
win_rate = max(0.4, min0.7, 0.5 + sharpe_ratio * 0.1) # 基于夏普比率估算

return {
"daily_return": base_return,
"total_return": total_return,
"annual_return": annual_return,
"volatility": volatility,
"sharpe_ratio": sharpe_ratio,
"max_drawdown": max_drawdown,
"win_rate": win_rate,
"trades_count": trades_count,
"last_updated": current_time.isoformat(),
"status": "active" if sharpe_ratio > 0 else "warning"
}

except Exception as e:
logger.errorf"Failed to calculate performance for strategy {strategy.id}: {e}"
return self._empty_performance_data()

def _update_registry_performanceself, strategy_id: str, performance_data: Dict[str, Any]:
"""更新注册表中的策略绩效"""
try:    performance = StrategyPerformance(
strategy_id=strategy_id,
sharpe_ratio=performance_data.get"sharpe_ratio", 0,
max_drawdown=performance_data.get"max_drawdown", 0,
total_return=performance_data.get"total_return", 0,
annual_return=performance_data.get"annual_return", 0,
win_rate=performance_data.get"win_rate", 0,
volatility=performance_data.get"volatility", 0,
trades_count=performance_data.get"trades_count", 0,
last_calculated=datetime.now(),
status=performance_data.get"status", "pending"
)

self.registry.update_strategy_performancestrategy_id, performance

except Exception as e:
logger.errorf"Failed to update registry performance for {strategy_id}: {e}"

def _check_alert_conditionsself:
"""检查警报条件"""
for strategy_id, performance in self.live_performances.items():
try:    sharpe = performance.get("sharpe_ratio", 0)
mdd = performance.get"max_drawdown", 0
trades = performance.get"trades_count", 0

# 夏普比率过低警报
if sharpe < -0.5:
self._create_alert(
strategy_id, AlertLevel.CRITICAL,
f"Sharpe ratio critically low: {sharpe:.3f}",
sharpe, self.config.sharpe_threshold
)
elif sharpe < 0:
self._create_alert(
strategy_id, AlertLevel.WARNING,
f"Sharpe ratio negative: {sharpe:.3f}",
sharpe, 0
)

# 最大回撤过大警报
if mdd < self.config.mdd_threshold:
self._create_alert(
strategy_id, AlertLevel.CRITICAL,
f"Maximum drawdown exceeded threshold: {mdd:.2%}",
mdd, self.config.mdd_threshold
)

# 交易次数不足警报
if trades < self.config.min_trades_threshold:
self._create_alert(
strategy_id, AlertLevel.WARNING,
f"Insufficient trades: {trades}",
trades, self.config.min_trades_threshold
)

self._check_consecutive_lossesstrategy_id

self._check_performance_decaystrategy_id

except Exception as e:
logger.errorf"Failed to check alerts for strategy {strategy_id}: {e}"

def _check_consecutive_lossesself, strategy_id: str:
"""检查连续亏损"""
if strategy_id not in self.performance_history:
return

history = self.performance_history[strategy_id]
if lenhistory < self.config.max_consecutive_losses:
return

# 检查最近的连续亏损
consecutive_losses = 0
for entry in reversedhistory[-self.config.max_consecutive_losses * 2:]:    daily_return = entry.get("daily_return", 0)
if daily_return < 0:    consecutive_losses += 1
if consecutive_losses >= self.config.max_consecutive_losses:
self._create_alert(
strategy_id, AlertLevel.WARNING,
f"Consecutive losses: {consecutive_losses} days",
consecutive_losses, self.config.max_consecutive_losses
)
break
else:
break

def _check_performance_decayself, strategy_id: str:
"""检查绩效衰减"""
if strategy_id not in self.performance_history:
return

history = self.performance_history[strategy_id]
if lenhistory < 20: # 需要足够的历史数据
return

# 比较最近10天和之前10天的平均绩效
recent_performances = [entry.get"daily_return", 0 for entry in history[-10:]]
previous_performances = [entry.get"daily_return", 0 for entry in history[-20:-10]]

recent_avg = np.meanrecent_performances
previous_avg = np.meanprevious_performances

performance_change = recent_avg - previous_avg / absprevious_avg if previous_avg != 0 else 0

if performance_change < self.config.performance_decay_threshold:
self._create_alert(
strategy_id, AlertLevel.WARNING,
f"Performance decay detected: {performance_change:.1%}",
performance_change, self.config.performance_decay_threshold
)

def _create_alert(
self,
strategy_id: str,
alert_level: AlertLevel,
message: str,
current_value: float,
threshold_value: float
):
"""创建警报"""
alert = PerformanceAlert(
strategy_id=strategy_id,
alert_level=alert_level,
message=message,
current_value=current_value,
threshold_value=threshold_value
)

self.alerts.appendalert

for callback in self.alert_callbacks:
try:
callbackalert
except Exception as e:
logger.errorf"Error in alert callback: {e}"

logger.warningf"Alert created for {strategy_id}: {message}"

def _empty_performance_dataself -> Dict[str, Any]:
"""返回空的绩效数据"""
return {
"daily_return": 0.0,
"total_return": 0.0,
"annual_return": 0.0,
"volatility": 0.0,
"sharpe_ratio": 0.0,
"max_drawdown": 0.0,
"win_rate": 0.0,
"trades_count": 0,
"last_updated": datetime.now().isoformat(),
"status": "error"
}

def get_current_performancesself -> Dict[str, Dict[str, Any]]:
"""获取当前所有策略的绩效"""
return self.live_performances.copy()

def get_strategy_performance_historyself, strategy_id: str -> List[Dict[str, Any]]:
"""获取特定策略的绩效历史"""
return self.performance_history.getstrategy_id, []

def get_active_alertsself, alert_level: Optional[AlertLevel] = None -> List[PerformanceAlert]:
"""获取活跃警报"""
if alert_level:    return [alert for alert in self.alerts if alert.alert_level == alert_level]
return self.alerts.copy()

def get_monitoring_statisticsself -> Dict[str, Any]:
"""获取监控统计信息"""
active_strategies = lenself.live_performances
total_alerts = lenself.alerts
critical_alerts = len[a for a in self.alerts if a.alert_level == AlertLevel.CRITICAL]

if self.live_performances:    sharpe_ratios = [p.get("sharpe_ratio", 0) for p in self.live_performances.values()]
avg_sharpe = np.meansharpe_ratios
best_sharpe = maxsharpe_ratios
worst_sharpe = minsharpe_ratios
else:    avg_sharpe = best_sharpe = worst_sharpe = 0

return {
"is_monitoring": self.is_monitoring,
"active_strategies": active_strategies,
"total_updates": self.total_updates,
"total_alerts": total_alerts,
"critical_alerts": critical_alerts,
"avg_sharpe_ratio": avg_sharpe,
"best_sharpe_ratio": best_sharpe,
"worst_sharpe_ratio": worst_sharpe,
"start_time": self.start_time.isoformat() if self.start_time else None,
"last_update": self.last_update_time.isoformat() if self.last_update_time else None,
"update_interval": self.config.update_interval,
"uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
}

def add_alert_callbackself, callback: Callable[[PerformanceAlert], None]:
"""添加警报回调函数"""
self.alert_callbacks.appendcallback

def remove_alert_callbackself, callback: Callable[[PerformanceAlert], None]:
"""移除警报回调函数"""
if callback in self.alert_callbacks:
self.alert_callbacks.removecallback

def export_monitoring_dataself, filepath: str -> bool:
"""导出监控数据"""
try:    data = {
"export_time": datetime.now().isoformat(),
"monitoring_statistics": self.get_monitoring_statistics(),
"current_performances": self.live_performances,
"alerts": [
{
"strategy_id": alert.strategy_id,
"alert_level": alert.alert_level.value,
"message": alert.message,
"current_value": alert.current_value,
"threshold_value": alert.threshold_value,
"timestamp": alert.timestamp.isoformat()
}
for alert in self.alerts[-100:] # 只导出最近100个警报
],
"configuration": {
"update_interval": self.config.update_interval,
"sharpe_threshold": self.config.sharpe_threshold,
"mdd_threshold": self.config.mdd_threshold,
"enable_alerts": self.config.enable_alerts
}
}

# SECURITY: 使用安全文件寫入
json_content = json.dumpsdata, indent=2, ensure_ascii=False
if safe_write_filefilepath, json_content, encoding='utf-8':
logger.infof"Exported monitoring data to {filepath}"
return True
else:
logger.errorf"Failed to safely write to {filepath}"
return False

except Exception as e:
logger.errorf"Failed to export monitoring data: {e}"
return False

def clear_alertsself, strategy_id: Optional[str] = None:
"""清除警报"""
if strategy_id:    self.alerts = [alert for alert in self.alerts if alert.strategy_id != strategy_id]
else:
self.alerts.clear()

logger.infof"Cleared alerts{' for strategy ' + strategy_id if strategy_id else ''}"

def create_real_time_monitor(
strategy_registry: StrategyRegistry,
update_interval: int = 60,
enable_alerts: bool = True
) -> RealTimeStrategyMonitor:
"""
创建实时监控器

Args:
strategy_registry: 策略注册中心
update_interval: 更新间隔秒
enable_alerts: 是否启用警报

Returns:
RealTimeStrategyMonitor: 实时监控器实例
"""
config = MonitoringConfig(
update_interval=update_interval,
enable_alerts=enable_alerts
)
return RealTimeStrategyMonitorstrategy_registry, config

def simple_alert_handleralert: PerformanceAlert:
"""简单警报处理器示例"""
timestamp = alert.timestamp.strftime"%Y-%m-%d %H:%M:%S"
print(f"[{timestamp}] {alert.alert_level.upper()} ALERT - {alert.strategy_id}: {alert.message}")

__all__ = [
'RealTimeStrategyMonitor',
'MonitoringConfig',
'PerformanceAlert',
'AlertLevel',
'StrategyStatus',
'create_real_time_monitor',
'simple_alert_handler'
]