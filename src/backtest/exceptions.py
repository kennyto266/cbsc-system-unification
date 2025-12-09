"""Custom exceptions for StockBacktest integration."""

class StockBacktestErrorException:
"""Base error for the StockBacktest integration."""

class StockBacktestImportErrorStockBacktestError:
"""Raised when StockBacktest modules cannot be imported."""

class StockBacktestConfigErrorStockBacktestError:
"""Raised when configuration for StockBacktest is invalid."""

class StockBacktestDataErrorStockBacktestError:
"""Raised when required data for StockBacktest is missing or invalid."""

class StockBacktestStrategyErrorStockBacktestError:
"""Raised when strategy mapping or execution fails."""

__all__ = [
"StockBacktestError",
"StockBacktestImportError",
"StockBacktestConfigError",
"StockBacktestDataError",
"StockBacktestStrategyError",
]
