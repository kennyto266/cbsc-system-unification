"""Data models for market data.

Defines Pydantic models for OHLCV bars and symbol information.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class OHLCVBar(BaseModel):
    """OHLCV (Open, High, Low, Close, Volume) data bar.

    Attributes:
        timestamp: Bar timestamp
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume
    """

    timestamp: datetime = Field(..., description="Bar timestamp")
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="Highest price")
    low: float = Field(..., gt=0, description="Lowest price")
    close: float = Field(..., gt=0, description="Closing price")
    volume: float = Field(..., ge=0, description="Trading volume")

    def model_post_init(self, __context: object) -> None:
        """Validate price relationships after initialization."""
        if self.high < max(self.open, self.close):
            raise ValueError("high must be >= max(open, close)")
        if self.low > min(self.open, self.close):
            raise ValueError("low must be <= min(open, close)")


class SymbolInfo(BaseModel):
    """Information about a tradable symbol.

    Attributes:
        symbol: Trading symbol (e.g., 'AAPL', '0700.HK')
        name: Full name of the symbol
        exchange: Exchange where symbol is traded
        type: Type of instrument (stock, etf, futures, etc.)
    """

    symbol: str = Field(..., min_length=1, description="Trading symbol")
    name: str = Field(..., min_length=1, description="Full name")
    exchange: str = Field(..., min_length=1, description="Exchange code")
    type: Literal["stock", "etf", "futures", "forex", "crypto", "index"] = Field(
        ..., description="Instrument type"
    )

    def __str__(self) -> str:
        """String representation of symbol."""
        return f"{self.symbol} ({self.name}) - {self.exchange}"
