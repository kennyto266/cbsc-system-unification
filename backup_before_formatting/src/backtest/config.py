"""StockBacktest integration configuration utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

DEFAULT_STOCKBACKTEST_PATH = Path(
    os.environ.get(
        "STOCKBACKTEST_PATH",
        r"C:\\Users\\Penguin8n\\Desktop\\StockBacktest",
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
        description="Call - able function used to execute a single backtest run",
    )
    performance_callable_name: str = Field(
        default="calculate_performance",
        description="Optional helper function returning additional performance metrics",
    )
    default_symbol: str = Field(default="0001.HK")
    default_capital_base: float = Field(default=1_000_000.0)
    strict_import: bool = Field(
        default=False,
        description="Raise errors if importing StockBacktest modules fails",
    )

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_env(cls, base_path: Optional[str] = None) -> "StockBacktestConfig":
        """Construct config from environment variables with optional overrides."""

        env_path = Path(base_path) if base_path else DEFAULT_STOCKBACKTEST_PATH

        overrides = dict(
            base_path=env_path,
            engine_module=os.environ.get(
                "STOCKBACKTEST_ENGINE_MODULE",
                "回測系統.01_核心系統.backtest_engine",
            ),
            engine_callable_name=os.environ.get(
                "STOCKBACKTEST_ENGINE_CALLABLE",
                "run_backtest",
            ),
            performance_callable_name=os.environ.get(
                "STOCKBACKTEST_PERFORMANCE_CALLABLE",
                "calculate_performance",
            ),
            default_symbol=os.environ.get(
                "STOCKBACKTEST_DEFAULT_SYMBOL",
                "0001.HK",
            ),
        )

        try:
            overrides["default_capital_base"] = float(
                os.environ.get("STOCKBACKTEST_CAPITAL_BASE", 1_000_000.0)
            )
        except ValueError:
            overrides["default_capital_base"] = 1_000_000.0

        strict = os.environ.get("STOCKBACKTEST_STRICT_IMPORT", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        overrides["strict_import"] = strict

        return cls(**overrides)


__all__ = [
    "StockBacktestConfig",
    "DEFAULT_STOCKBACKTEST_PATH",
]
