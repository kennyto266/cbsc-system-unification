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

LOGGER = logging.getLogger("hk_quant_system.backtest.adapter")


StrategyCallable = Callable[[pd.DataFrame, Mapping[str, Any]], Any]


class ModuleLoader:
    """Dynamically load callables from the StockBacktest project."""

    def __init__(self, config: StockBacktestConfig):
        self.config = config
        self._engine_module = None

    @property
    def engine_module(self):
        if self._engine_module is None:
            try:
                self._engine_module = importlib.import_module(self.config.engine_module)
            except ImportError as exc:
                LOGGER.exception("Failed to import StockBacktest module: %s", exc)
                raise StockBacktestImportError(str(exc)) from exc
        return self._engine_module

    def get_callable(self, name: str) -> Callable:
        try:
            return getattr(self.engine_module, name)
        except AttributeError as exc:
            msg = f"StockBacktest module missing callable {name}"
            LOGGER.error(msg)
            raise StockBacktestImportError(msg) from exc


class StrategyMapper:
    """Map agent strategies to StockBacktest strategy functions."""

    def __init__(self, loader: ModuleLoader):
        self.loader = loader

    @lru_cache(maxsize=16)
    def available_strategies(self) -> Dict[str, StrategyCallable]:
        module = self.loader.engine_module
        strategies = {}
        for attr in dir(module):
            if attr.endswith("_strategy") and callable(getattr(module, attr)):
                strategies[attr] = getattr(module, attr)
        return strategies

    def get_strategy(self, strategy_type: str) -> StrategyCallable:
        strategies = self.available_strategies()
        if strategy_type in strategies:
            return strategies[strategy_type]
        # Fallback to a default strategy if available
        default_name = f"{strategy_type}_strategy"
        if default_name in strategies:
            return strategies[default_name]
        raise StockBacktestStrategyError(f"Unsupported strategy type: {strategy_type}")


class DataTransformer:
    """Convert between RealMarketData structures and StockBacktest dataframes."""

    def __init__(self, required_columns: Optional[Iterable[str]] = None):
        self.required_columns = required_columns or [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

    def to_dataframe(self, market_data: List[Mapping[str, Any]]) -> pd.DataFrame:
        if not market_data:
            raise StockBacktestDataError("No market data provided for backtest")

        df = pd.DataFrame(market_data)
        missing = [col for col in self.required_columns if col not in df.columns]
        if missing:
            raise StockBacktestDataError(
                f"Missing required columns: {', '.join(missing)}"
            )

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)

        df.sort_index(inplace=True)
        return df


__all__ = [
    "ModuleLoader",
    "StrategyMapper",
    "DataTransformer",
]
