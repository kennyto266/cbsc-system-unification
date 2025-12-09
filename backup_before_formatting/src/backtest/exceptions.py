"""Custom exceptions for StockBacktest integration."""


class StockBacktestError(Exception):
    """Base error for the StockBacktest integration."""


class StockBacktestImportError(StockBacktestError):
    """Raised when StockBacktest modules cannot be imported."""


class StockBacktestConfigError(StockBacktestError):
    """Raised when configuration for StockBacktest is invalid."""


class StockBacktestDataError(StockBacktestError):
    """Raised when required data for StockBacktest is missing or invalid."""


class StockBacktestStrategyError(StockBacktestError):
    """Raised when strategy mapping or execution fails."""


__all__ = [
    "StockBacktestError",
    "StockBacktestImportError",
    "StockBacktestConfigError",
    "StockBacktestDataError",
    "StockBacktestStrategyError",
]
