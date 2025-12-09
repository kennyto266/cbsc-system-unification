"""StockBacktest project integration."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core import SystemConfig
from ..data_adapters.base_adapter import RealMarketData
from .config import StockBacktestConfig
from .engine_interface import (
    BacktestEngineConfig,
    BacktestMetrics,
    BacktestStatus,
    BaseBacktestEngine,
    StrategyPerformance,
)
from .exceptions import (
    StockBacktestConfigError,
    StockBacktestDataError,
    StockBacktestError,
    StockBacktestStrategyError,
)
from .stockbacktest_adapter import DataTransformer, ModuleLoader, StrategyMapper


class StockBacktestIntegration(BaseBacktestEngine):
    """Concrete implementation integrating the legacy StockBacktest project."""

    def __init__(
        self,
        config: BacktestEngineConfig,
        stockbacktest_path: Optional[str] = None,
        stockbacktest_config: Optional[StockBacktestConfig] = None,
    ) -> None:
        super().__init__(config)
        self._stock_config = stockbacktest_config or StockBacktestConfig.from_env(
            stockbacktest_path
        )
        self._loader = ModuleLoader(self._stock_config)
        self._strategy_mapper = StrategyMapper(self._loader)
        self._data_transformer = DataTransformer()
        self._performance_callable = None
        self._engine_callable = None
        self._strategy_cache: Dict[str, BacktestMetrics] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def initialize(self) -> bool:
        try:
            base_path: Path = self._stock_config.base_path
            if not base_path.exists():
                msg = f"StockBacktest directory not found: {base_path}"
                self.logger.error(msg)
                if self._stock_config.strict_import:
                    raise StockBacktestConfigError(msg)
                return False

            if str(base_path) not in sys.path:
                sys.path.insert(0, str(base_path))

            # Ensure performance callable is available
            self._engine_callable = self._loader.get_callable(
                self._stock_config.engine_callable_name
            )
            try:
                self._performance_callable = self._loader.get_callable(
                    self._stock_config.performance_callable_name
                )
            except StockBacktestError:
                self.logger.warning(
                    "Performance callable '%s' not found, proceeding without it",
                    self._stock_config.performance_callable_name,
                )

            self.logger.info("StockBacktest integration initialized successfully")
            self.set_status(BacktestStatus.COMPLETED)
            return True
        except StockBacktestError:
            if self._stock_config.strict_import:
                raise
            self.logger.exception("Failed to initialize StockBacktest integration")
            return False

    async def cleanup(self) -> None:
        self._strategy_cache.clear()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def validate_strategy(self, strategy: Dict[str, Any]) -> bool:
        required_fields = {"name", "type", "parameters"}
        missing = required_fields - set(strategy.keys())
        if missing:
            raise StockBacktestStrategyError(
                f"Strategy missing required fields: {', '.join(missing)}"
            )

        self._strategy_mapper.get_strategy(strategy["type"])  # ensure mapping exists
        return True

    async def get_performance_summary(
        self, strategy_id: str
    ) -> Optional[StrategyPerformance]:
        cached = self._strategy_cache.get(strategy_id)
        return cached.performance if cached else None

    async def run_backtest(
        self,
        strategy: Dict[str, Any],
        market_data: List[RealMarketData],
    ) -> BacktestMetrics:
        if not market_data:
            raise StockBacktestDataError("No market data provided for backtest")

        self.set_status(BacktestStatus.RUNNING)

        df_market = self._data_transformer.to_dataframe(
            [data.model_dump() for data in market_data]
        )
        strategy_callable = self._strategy_mapper.get_strategy(strategy["type"])

        try:
            engine_result = self._engine_callable(
                df_market,
                strategy_callable,
                float(self.config.initial_capital),
            )
        except Exception as exc:
            self.set_status(BacktestStatus.FAILED)
            raise StockBacktestStrategyError(str(exc)) from exc

        performance = await self._build_performance(strategy, engine_result)
        metrics = BacktestMetrics(
            performance=performance,
            risk_metrics=self._extract_risk_metrics(engine_result),
            trade_analysis=self._extract_trade_analysis(engine_result),
            portfolio_analysis=self._extract_portfolio_metrics(engine_result),
        )

        strategy_id = strategy.get(
            "id", f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self._strategy_cache[strategy_id] = metrics
        self.set_status(BacktestStatus.COMPLETED)
        return metrics

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _build_performance(
        self,
        strategy: Dict[str, Any],
        engine_result: Dict[str, Any],
    ) -> StrategyPerformance:
        # fallback to generic calculator if stockbacktest did not provide detailed metrics
        portfolio_values = engine_result.get("portfolio_values")
        if not portfolio_values:
            raise StockBacktestDataError("StockBacktest engine returned empty portfolio values")

        portfolio_series = pd.Series(portfolio_values)
        returns = portfolio_series.pct_change().dropna()

        from .strategy_performance import PerformanceCalculator

        calculator = PerformanceCalculator()
        performance = calculator.calculate_performance_metrics(
            returns,
            risk_free_rate=float(self.config.risk_free_rate),
        )
        performance.strategy_id = strategy.get(
            "id", f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        performance.strategy_name = strategy.get("name", "Unknown Strategy")
        performance.strategy_type = strategy.get("type", "custom")
        performance.backtest_period = f"{returns.index[0].date()} to {returns.index[-1].date()}"
        performance.start_date = returns.index[0].date()
        performance.end_date = returns.index[-1].date()
        performance.validation_status = "calculated"
        return performance

    def _extract_risk_metrics(self, engine_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "total_return": engine_result.get("total_return"),
            "max_drawdown": engine_result.get("max_drawdown"),
            "sharpe_ratio": engine_result.get("sharpe_ratio"),
            "win_rate": engine_result.get("win_rate"),
        }

    def _extract_trade_analysis(self, engine_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "trade_count": engine_result.get("trade_count"),
            "trade_log": engine_result.get("trade_log"),
        }

    def _extract_portfolio_metrics(self, engine_result: Dict[str, Any]) -> Dict[str, Any]:
        final_value = engine_result.get("final_value")
        return {
            "final_value": final_value,
            "capital_base": float(self.config.initial_capital),
        }

