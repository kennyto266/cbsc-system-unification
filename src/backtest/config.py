"""StockBacktest integration configuration utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

DEFAULT_STOCKBACKTEST_PATH = Path(
    os.environ.get(
        "STOCKBACKTEST_PATH",
        r"C:\Users\Penguin8n\Desktop\StockBacktest",
    )
)


class StockBacktestConfig(BaseModel):
    """Configuration container for StockBacktest integration."""

    base_path: Path = Field(default=DEFAULT_STOCKBACKTEST_PATH)
    engine_module: str = Field(
        default="回測系統.01_核心系統.backtest_engine",
        description="Module containing the backtest entry point",
    )
    engine_callable_name: str = Field(
        default="run_backtest",
        description="Callable function used to execute a single backtest run",
    )
    performance_callable_name: str = Field(
        default="calculate_performance",
        description="Callable function used to calculate performance metrics",
    )

    class Config:
        arbitrary_types_allowed = True


def get_stockbacktest_config(
    base_path: Optional[Path] = None,
    engine_module: Optional[str] = None,
    engine_callable_name: Optional[str] = None,
) -> StockBacktestConfig:
    """Create a StockBacktestConfig with optional overrides."""
    return StockBacktestConfig(
        base_path=base_path or DEFAULT_STOCKBACKTEST_PATH,
        engine_module=engine_module or "回測系統.01_核心系統.backtest_engine",
        engine_callable_name=engine_callable_name or "run_backtest",
    )