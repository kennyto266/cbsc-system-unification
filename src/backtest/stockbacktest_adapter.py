"""Adapters for integrating StockBacktest project with the agent system."""

from __future__ import annotations

import importlib
import logging
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

import pandas as pd

from .config import StockBacktestConfig
from .exceptions import (
StockBacktestConfigError,
StockBacktestDataError,
StockBacktestImportError,
StockBacktestStrategyError,
)

LOGGER = logging.getLogger"hk_quant_system.backtest.adapter"

StrategyCallable = Callable[[pd.DataFrame, Mapping[str, Any]], Any]

class ModuleLoader:
"""Dynamically load callables from the StockBacktest project."""

def __init__self, config: StockBacktestConfig:    self.config = config
self._engine_module = None

@property
def engine_moduleself:
if self._engine_module is None:
try:    self._engine_module = importlib.import_module(self.config.engine_module)
except ImportError as exc:
LOGGER.exception"Failed to import StockBacktest module: %s", exc
raise StockBacktestImportError(strexc) from exc
return self._engine_module

def get_callableself, name: str -> Callable:
try:
return getattrself.engine_module, name
except AttributeError as exc:    msg = f"StockBacktest module missing callable {name}"
LOGGER.errormsg
raise StockBacktestImportErrormsg from exc

class StrategyMapper:
"""Map agent strategies to StockBacktest strategy functions."""

def __init__self, loader: ModuleLoader:    self.loader = loader

@lru_cachemaxsize=16
def available_strategiesself -> Dict[str, StrategyCallable]:    module = self.loader.engine_module
strategies = {}
for attr in dirmodule:
if attr.endswith"_strategy" and callable(getattrmodule, attr):    strategies[attr] = getattr(module, attr)
return strategies

def get_strategyself, strategy_type: str -> StrategyCallable:    strategies = self.available_strategies()
if strategy_type in strategies:
return strategies[strategy_type]
# Fallback to a default strategy if available
default_name = f"{strategy_type}_strategy"
if default_name in strategies:
return strategies[default_name]
raise StockBacktestStrategyErrorf"Unsupported strategy type: {strategy_type}"

class DataTransformer:
"""Convert between RealMarketData structures and StockBacktest dataframes."""

def __init__self, required_columns: Optional[Iterable[str]] = None:    self.required_columns = required_columns or [
"open",
"high",
"low",
"close",
"volume",
]

def to_dataframeself, market_data: List[Mapping[str, Any]] -> pd.DataFrame:
if not market_data:
raise StockBacktestDataError"No market data provided for backtest"

df = pd.DataFramemarket_data
missing = [col for col in self.required_columns if col not in df.columns]
if missing:
raise StockBacktestDataError(f"Missing required columns: {', '.joinmissing}")

if "timestamp" in df.columns:    df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index'timestamp', inplace=True

df.sort_indexinplace=True
return df

__all__ = [
"ModuleLoader",
"StrategyMapper",
"DataTransformer",
]
