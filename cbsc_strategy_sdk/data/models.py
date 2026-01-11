"""Data models for market data.

Defines Pydantic models for OHLCV bars, symbol information, and real-time tick data.
"""

from datetime import datetime
from typing import Literal, Optional

import pandas as pd
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


class TickData(BaseModel):
    """Real-time market data tick.

    Represents a single update in market price for a symbol,
    typically received from WebSocket streaming.

    Attributes:
        symbol: Trading symbol (e.g., 'AAPL', '0700.HK')
        timestamp: Tick timestamp
        price: Last traded price
        volume: Trade volume
        bid: Current bid price (optional)
        ask: Current ask price (optional)
        bid_size: Bid size/quantity (optional)
        ask_size: Ask size/quantity (optional)
    """

    symbol: str = Field(..., min_length=1, description="Trading symbol")
    timestamp: datetime = Field(..., description="Tick timestamp")
    price: float = Field(..., gt=0, description="Last traded price")
    volume: int = Field(..., ge=0, description="Trade volume")
    bid: Optional[float] = Field(None, gt=0, description="Current bid price")
    ask: Optional[float] = Field(None, gt=0, description="Current ask price")
    bid_size: Optional[int] = Field(None, ge=0, description="Bid size")
    ask_size: Optional[int] = Field(None, ge=0, description="Ask size")

    def to_dict(self) -> dict:
        """Convert tick to dictionary.

        Returns:
            Dictionary representation of tick data
        """
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "price": self.price,
            "volume": self.volume,
            "bid": self.bid,
            "ask": self.ask,
            "bid_size": self.bid_size,
            "ask_size": self.ask_size,
        }

    def to_series(self) -> pd.Series:
        """Convert tick to pandas Series.

        Returns:
            pandas Series with tick data
        """
        return pd.Series({
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "price": self.price,
            "volume": self.volume,
            "bid": self.bid,
            "ask": self.ask,
            "bid_size": self.bid_size,
            "ask_size": self.ask_size,
        })

    def __str__(self) -> str:
        """String representation of tick."""
        return f"{self.symbol} @ {self.price} ({self.timestamp.strftime('%H:%M:%S')})"
