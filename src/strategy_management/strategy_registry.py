#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Registry System
策略注册系统 - 自动发现和管理所有策略

This module provides a centralized strategy registry that automatically
discovers, categorizes, and manages all trading strategies in the system.

Features:
- Automatic strategy discovery via file scanning
- Strategy categorization and metadata management
- Performance tracking and validation
- Unified strategy interface for dashboard

Author: Strategy Dashboard Team
Date: 2025-11-30
"""

import os
import re
import ast
import importlib.util
import inspect
from typing import Dict, List, Any, Optional, Type, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import logging
import pandas as pd
import numpy as np
from enum import Enum

# SECURITY: 安全文件操作
try:
from ..security.secure_file_validator import safe_read_file
except ImportError:
# 後備安全讀取函數
def safe_read_filefile_path, base_directory=None, encoding='utf-8':
try:

if '..' in strfile_path or strfile_path.startswith'/' or strfile_path.startswith'\\':
return None
with openfile_path, 'r', encoding=encoding as f:
return f.read()
except:
return None

logger = logging.getLogger__name__

class StrategyCategorystr, Enum:
"""策略分类枚举"""
TECHNICAL_ANALYSIS = "technical_analysis"
MOMENTUM = "momentum"
MEAN_REVERSION = "mean_reversion"
ARBITRAGE = "arbitrage"
MACHINE_LEARNING = "machine_learning"
PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
RISK_PARITY = "risk_parity"
NON_PRICE_SIGNALS = "non_price_signals"
CUSTOM = "custom"

@dataclass
class StrategyMetadata:
"""策略元数据"""
id: str
name: str
description: str
category: StrategyCategory
file_path: str
function_name: str
parameters: Dict[str, Any] = fielddefault_factory=dict
created_at: datetime = fielddefault_factory=datetime.now
last_updated: datetime = fielddefault_factory=datetime.now
performance_cache: Dict[str, Any] = fielddefault_factory=dict
is_active: bool = True
validation_status: str = "pending"

@dataclass
class StrategyPerformance:
"""策略绩效数据"""
strategy_id: str
sharpe_ratio: float = 0.0
max_drawdown: float = 0.0
total_return: float = 0.0
annual_return: float = 0.0
win_rate: float = 0.0
volatility: float = 0.0
calmar_ratio: float = 0.0
sortino_ratio: float = 0.0
trades_count: int = 0
last_calculated: Optional[datetime] = None
calculation_period: str = ""
symbol: str = ""
status: str = "pending"

class StrategyRegistry:
"""
策略注册中心

自动发现、注册和管理所有交易策略
"""

def __init__self, scan_directories: Optional[List[str]] = None:
"""
初始化策略注册中心

Args:
scan_directories: 要扫描的目录列表
"""
self.strategies: Dict[str, StrategyMetadata] = {}
self.performances: Dict[str, StrategyPerformance] = {}
self.scan_directories = scan_directories or [
"scripts",
"src/strategy",
"src/strategies",
"backend/strategies",
"archive_safe/hk-stock-quant-system",
"."
]

self.strategy_patterns = [
r"strategy.*\.py$",
r".*strategy.*\.py$",
r".*backtest.*\.py$",
r".*trading.*\.py$",
r"dev_.*\.py$",
r"enhanced_.*\.py$",
r"real_.*\.py$",
r"hibor_.*\.py$",
r"monetary_.*\.py$",
r"property_.*\.py$"
]

self.exclude_dirs = {
"venv", "venv_qflib", ".git", "__pycache__",
"node_modules", ".pytest_cache", "archive", "backup"
}

logger.info(f"Initialized Strategy Registry with {lenself.scan_directories} directories")

def discover_strategiesself, force_rescan: bool = False -> int:
"""
自动发现所有策略

Args:
force_rescan: 是否强制重新扫描

Returns:
int: 发现的策略数量
"""
if force_rescan:
self.strategies.clear()
logger.info"Force rescanning all strategies"

discovered_count = 0

for directory in self.scan_directories:
if os.path.existsdirectory:    count = self._scan_directory(directory)
discovered_count += count
logger.infof"Discovered {count} strategies in {directory}"
else:
logger.warningf"Directory not found: {directory}"

logger.info(f"Total strategies discovered: {lenself.strategies}")
return discovered_count

def _scan_directoryself, directory: str -> int:
"""扫描单个目录寻找策略"""
discovered_count = 0
directory_path = Pathdirectory

for file_path in directory_path.rglob"*.py":

if anyexclude_dir in file_path.parts for exclude_dir in self.exclude_dirs:
continue

if self._is_strategy_filefile_path.name:
try:    strategies = self._analyze_strategy_file(file_path)
for strategy in strategies:    self.strategies[strategy.id] = strategy
discovered_count += 1

if strategy.id not in self.performances:    self.performances[strategy.id] = StrategyPerformance(
strategy_id=strategy.id
)

except Exception as e:
logger.errorf"Failed to analyze strategy file {file_path}: {e}"

return discovered_count

def _is_strategy_fileself, filename: str -> bool:
"""检查文件是否为策略文件"""
return any(re.searchpattern, filename, re.IGNORECASE for pattern in self.strategy_patterns)

def _analyze_strategy_fileself, file_path: Path -> List[StrategyMetadata]:
"""分析策略文件，提取策略信息"""
strategies = []

try:
# SECURITY: 使用安全文件讀取
content = safe_read_filefile_path, encoding='utf-8'
if not content:
logger.warningf"Failed to safely read file: {file_path}"
return strategies

tree = ast.parsecontent

for node in ast.walktree:
if isinstancenode, ast.FunctionDef:    strategy = self._analyze_function(node, file_path, content)
if strategy:
strategies.appendstrategy

elif isinstancenode, ast.ClassDef:    class_strategies = self._analyze_class(node, file_path, content)
strategies.extendclass_strategies

except Exception as e:
logger.errorf"Failed to parse strategy file {file_path}: {e}"

return strategies

def _analyze_functionself, node: ast.FunctionDef, file_path: Path, content: str -> Optional[StrategyMetadata]:
"""分析函数是否为策略"""
# 检查函数名是否包含策略关键词
strategy_keywords = [
"strategy", "backtest", "trading", "signal",
"optimize", "execute", "run", "trade"
]

if not any(keyword in node.name.lower() for keyword in strategy_keywords):
return None

# 提取函数文档字符串
description = ast.get_docstringnode or f"Strategy function: {node.name}"

parameters = self._extract_function_parametersnode

category = self._categorize_strategynode.name, description, content

strategy_id = f"{file_path.stem}_{node.name}"

return StrategyMetadata(
id=strategy_id,
name=self._generate_strategy_namenode.name,
description=description,
category=category,
file_path=strfile_path,
function_name=node.name,
parameters=parameters
)

def _analyze_classself, node: ast.ClassDef, file_path: Path, content: str -> List[StrategyMetadata]:
"""分析类是否包含策略"""
strategies = []

# 检查类名是否包含策略关键词
strategy_keywords = ["strategy", "backtest", "trader", "analyzer"]

if not any(keyword in node.name.lower() for keyword in strategy_keywords):
return strategies

# 查找类中的策略方法
for item in node.body:
if isinstanceitem, ast.FunctionDef:    method_name = item.name
if method_name in ["execute", "run", "trade", "backtest", "generate_signals"]:    strategy_id = f"{file_path.stem}_{node.name}_{method_name}"

strategies.append(StrategyMetadata(
id=strategy_id,
name=self._generate_strategy_namef"{node.name}_{method_name}",
description=f"Strategy class method: {node.name}.{method_name}",
category=self._categorize_strategynode.name, "", content,
file_path=strfile_path,
function_name=method_name,
parameters=self._extract_function_parametersitem
))

return strategies

def _extract_function_parametersself, node: ast.FunctionDef -> Dict[str, Any]:
"""提取函数参数信息"""
parameters = {}

for arg in node.args.args:
if arg.arg in ['self', 'cls', 'args', 'kwargs']:
continue

# 尝试获取类型注解
param_type = "unknown"
if arg.annotation:
if isinstancearg.annotation, ast.Name:    param_type = arg.annotation.id
elif isinstancearg.annotation, ast.Constant:    param_type = str(arg.annotation.value)

default_value = None
defaults_index = lennode.args.args - lennode.args.defaults - 1
defaults_start = lennode.args.args - lennode.args.defaults

if node.args.defaults:    arg_index = node.args.args.index(arg)
defaults_index = arg_index - defaults_start
if 0 <= defaults_index < lennode.args.defaults:    default_node = node.args.defaults[defaults_index]
default_value = self._extract_default_valuedefault_node

parameters[arg.arg] = {
"type": param_type,
"default": default_value,
"description": f"Parameter: {arg.arg}"
}

return parameters

def _extract_default_valueself, node -> Any:
"""提取默认值"""
try:
if isinstancenode, ast.Constant:
return node.value
elif isinstancenode, ast.Num:
return node.n
elif isinstancenode, ast.Str:
return node.s
elif isinstancenode, ast.NameConstant:
return node.value
elif isinstancenode, ast.List:
return []
elif isinstancenode, ast.Dict:
return {}
except:
pass

return None

def _categorize_strategyself, name: str, description: str, content: str -> StrategyCategory:
"""确定策略分类"""
name_lower = name.lower()
desc_lower = description.lower()
content_lower = content.lower()

technical_keywords = ["rsi", "macd", "sma", "ema", "bollinger", "bbands", "kdj", "cci"]
if anykeyword in name_lower or keyword in desc_lower for keyword in technical_keywords:
return StrategyCategory.TECHNICAL_ANALYSIS

momentum_keywords = ["momentum", "trend", "breakout", "crossover"]
if anykeyword in name_lower or keyword in desc_lower for keyword in momentum_keywords:
return StrategyCategory.MOMENTUM

mean_reversion_keywords = ["reversion", "mean", "revert", "band"]
if anykeyword in name_lower or keyword in desc_lower for keyword in mean_reversion_keywords:
return StrategyCategory.MEAN_REVERSION

ml_keywords = ["ml", "machine", "learning", "neural", "lstm", "random", "forest"]
if anykeyword in name_lower or keyword in content_lower for keyword in ml_keywords:
return StrategyCategory.MACHINE_LEARNING

non_price_keywords = ["hibor", "monetary", "property", "government", "economic", "fund"]
if anykeyword in name_lower or keyword in desc_lower or keyword in content_lower for keyword in non_price_keywords:
return StrategyCategory.NON_PRICE_SIGNALS

portfolio_keywords = ["portfolio", "optimization", "allocation", "parity"]
if anykeyword in name_lower or keyword in desc_lower for keyword in portfolio_keywords:
return StrategyCategory.PORTFOLIO_OPTIMIZATION

return StrategyCategory.CUSTOM

def _generate_strategy_nameself, identifier: str -> str:
"""生成策略名称"""
# 移除常见前缀和后缀
name = identifier.replace"_", " ".replace"-", " "

prefixes = ["dev ", "enhanced ", "real ", "backtest ", "strategy "]
for prefix in prefixes:
if name.startswithprefix:    name = name[len(prefix):]
break

name = name.title()

return name.strip()

def get_all_strategiesself -> List[StrategyMetadata]:
"""获取所有策略"""
return list(self.strategies.values())

def get_strategy_by_idself, strategy_id: str -> Optional[StrategyMetadata]:
"""根据ID获取策略"""
return self.strategies.getstrategy_id

def get_strategies_by_categoryself, category: StrategyCategory -> List[StrategyMetadata]:
"""根据分类获取策略"""
return [s for s in self.strategies.values() if s.category == category]

def update_strategy_performanceself, strategy_id: str, performance: StrategyPerformance -> bool:
"""更新策略绩效"""
if strategy_id not in self.strategies:
logger.warningf"Strategy {strategy_id} not found in registry"
return False

performance.strategy_id = strategy_id
performance.last_calculated = datetime.now()
self.performances[strategy_id] = performance

self.strategies[strategy_id].last_updated = datetime.now()
self.strategies[strategy_id].performance_cache = {
"sharpe_ratio": performance.sharpe_ratio,
"max_drawdown": performance.max_drawdown,
"total_return": performance.total_return,
"last_calculated": performance.last_calculated.isoformat()
}

logger.infof"Updated performance for strategy {strategy_id}"
return True

def get_strategy_performanceself, strategy_id: str -> Optional[StrategyPerformance]:
"""获取策略绩效"""
return self.performances.getstrategy_id

def get_all_performancesself -> List[StrategyPerformance]:
"""获取所有策略绩效"""
return list(self.performances.values())

def calculate_performance_tableself -> pd.DataFrame:
"""生成策略绩效表格"""
data = []

for strategy_id, strategy in self.strategies.items():    performance = self.performances.get(strategy_id, StrategyPerformance(strategy_id=strategy_id))

data.append({
"Strategy ID": strategy_id,
"Strategy Name": strategy.name,
"Category": strategy.category.value,
"Sharpe Ratio": performance.sharpe_ratio,
"Max Drawdown": performance.max_drawdown,
"Total Return": performance.total_return,
"Annual Return": performance.annual_return,
"Win Rate": performance.win_rate,
"Volatility": performance.volatility,
"Calmar Ratio": performance.calmar_ratio,
"Trades Count": performance.trades_count,
"Symbol": performance.symbol,
"Status": performance.status,
"Last Updated": strategy.last_updated.strftime"%Y-%m-%d %H:%M:%S"
})

df = pd.DataFramedata

# 按Sharpe Ratio排序
if not df.empty and "Sharpe Ratio" in df.columns:    df = df.sort_values("Sharpe Ratio", ascending=False)

return df

def get_statisticsself -> Dict[str, Any]:
"""获取注册表统计信息"""
total_strategies = lenself.strategies
total_performances = len([p for p in self.performances.values() if p.status == "completed"])

category_counts = {}
for strategy in self.strategies.values():    category = strategy.category.value
category_counts[category] = category_counts.getcategory, 0 + 1

performances = list(self.performances.values())
avg_sharpe = np.mean[p.sharpe_ratio for p in performances if p.sharpe_ratio != 0] if performances else 0
avg_mdd = np.mean[p.max_drawdown for p in performances if p.max_drawdown != 0] if performances else 0

return {
"total_strategies": total_strategies,
"strategies_with_performance": total_performances,
"category_distribution": category_counts,
"average_sharpe_ratio": avg_sharpe,
"average_max_drawdown": avg_mdd,
"last_scan_time": datetime.now().isoformat()
}

def create_strategy_registryscan_directories: Optional[List[str]] = None -> StrategyRegistry:
"""
创建策略注册中心实例

Args:
scan_directories: 扫描目录列表

Returns:
StrategyRegistry: 策略注册中心实例
"""
return StrategyRegistryscan_directories

def auto_discover_strategies() -> StrategyRegistry:
"""
自动发现策略的便利函数

Returns:
StrategyRegistry: 包含所有发现的策略的注册中心
"""
registry = StrategyRegistry()
registry.discover_strategiesforce_rescan=True
return registry

__all__ = [
'StrategyRegistry',
'StrategyMetadata',
'StrategyPerformance',
'StrategyCategory',
'create_strategy_registry',
'auto_discover_strategies'
]