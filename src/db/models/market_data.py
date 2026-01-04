"""
Market Data ORM Models

Database models for CBSC market data and sentiment analysis.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Float, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy

from .base import BaseModel


class CBSCMarketData(BaseModel):
    """CBSC Market Data ORM model

    Stores market data with CBSC-specific sentiment indicators including
    bull/bear ratio, sentiment score, price impact, and confidence levels.
    """
    __tablename__ = "cbsc_market_data"

    # Symbol and timestamp
    symbol = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Price data
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)

    # Volume data
    volume = Column(Float, nullable=False)
    turnover = Column(Float)  # Trading turnover amount

    # CBSC-specific sentiment indicators
    bull_bear_ratio = Column(Float, nullable=False)  # Bull/bear warrant ratio
    sentiment_score = Column(Float, nullable=False)  # Sentiment score (-1 to 1)
    price_impact = Column(Float, nullable=False)     # Price impact indicator
    confidence_level = Column(Float, nullable=False) # Confidence level (0 to 1)

    # Additional market context
    bid_price = Column(Float)
    ask_price = Column(Float)
    bid_volume = Column(Float)
    ask_volume = Column(Float)

    # Technical indicators (optional)
    ma5 = Column(Float)   # 5-period moving average
    ma10 = Column(Float)  # 10-period moving average
    ma20 = Column(Float)  # 20-period moving average
    rsi = Column(Float)   # Relative Strength Index
    macd = Column(Float)  # MACD value

    # Extended data (JSON for flexibility)
    extended_data = Column(JSONB)  # Additional CBSC metrics

    # Data quality metadata
    data_quality_score = Column(Float)  # Quality score (0-1)
    is_complete = Column(sqlalchemy.Boolean, default=True)  # Data completeness flag

    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_market_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_market_timestamp_sentiment', 'timestamp', 'sentiment_score'),
        Index('idx_market_symbol_date', 'symbol', 'timestamp'),  # Date-based queries
        Index('idx_market_sentiment_range', 'sentiment_score'),  # Sentiment range queries
        CheckConstraint('high_price >= low_price', name='ck_price_high_low'),
        CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1', name='ck_sentiment_range'),
        CheckConstraint('confidence_level >= 0 AND confidence_level <= 1', name='ck_confidence_range'),
    )

    @property
    def price_range(self) -> float:
        """Calculate daily price range"""
        return self.high_price - self.low_price

    @property
    def price_change_pct(self) -> float:
        """Calculate price change percentage"""
        if self.open_price and self.open_price > 0:
            return ((self.close_price - self.open_price) / self.open_price) * 100
        return 0

    @property
    def is_bullish(self) -> bool:
        """Check if sentiment is bullish"""
        return self.sentiment_score > 0

    @property
    def sentiment_strength(self) -> str:
        """Get sentiment strength category"""
        abs_score = abs(self.sentiment_score)
        if abs_score >= 0.7:
            return "strong"
        elif abs_score >= 0.3:
            return "moderate"
        else:
            return "weak"

    @property
    def trading_volume_category(self) -> str:
        """Categorize trading volume"""
        if self.volume > 10_000_000:
            return "high"
        elif self.volume > 1_000_000:
            return "medium"
        else:
            return "low"

    def get_price_distance_from_ma(self, ma_period: int = 20) -> Optional[float]:
        """Get percentage distance from moving average"""
        ma = getattr(self, f'ma{ma_period}', None)
        if ma and ma > 0:
            return ((self.close_price - ma) / ma) * 100
        return None

    def is_oversold(self) -> bool:
        """Check if RSI indicates oversold"""
        if self.rsi is not None:
            return self.rsi < 30
        return False

    def is_overbought(self) -> bool:
        """Check if RSI indicates overbought"""
        if self.rsi is not None:
            return self.rsi > 70
        return False

    def to_dict(self) -> dict:
        """Convert to dictionary with computed properties"""
        base_dict = super().to_dict()
        base_dict.update({
            'price_range': self.price_range,
            'price_change_pct': self.price_change_pct,
            'is_bullish': self.is_bullish,
            'sentiment_strength': self.sentiment_strength,
            'trading_volume_category': self.trading_volume_category,
        })
        return base_dict

    def __repr__(self):
        return (
            f"<CBSCMarketData(symbol='{self.symbol}', "
            f"timestamp={self.timestamp}, close={self.close_price:.2f}, "
            f"sentiment={self.sentiment_score:.2f})>"
        )
