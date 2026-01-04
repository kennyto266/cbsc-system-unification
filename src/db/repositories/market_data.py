"""
Market Data Repository

Repository class for CBSC market data access.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, func

from .base import BaseRepository
from ..models.market_data import CBSCMarketData

logger = logging.getLogger(__name__)


class CBSCMarketDataRepository(BaseRepository[CBSCMarketData]):
    """Repository for CBSCMarketData model"""

    def __init__(self, session):
        super().__init__(session, CBSCMarketData)

    def get_by_symbol(
        self,
        symbol: str,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 1000
    ) -> List[CBSCMarketData]:
        """Get market data for a symbol"""
        query = self.session.query(CBSCMarketData).filter(
            CBSCMarketData.symbol == symbol
        )

        if start_date:
            query = query.filter(CBSCMarketData.timestamp >= start_date)
        if end_date:
            query = query.filter(CBSCMarketData.timestamp <= end_date)

        return query.order_by(desc(CBSCMarketData.timestamp)).limit(limit).all()

    def get_latest_by_symbol(self, symbol: str) -> Optional[CBSCMarketData]:
        """Get latest market data for a symbol"""
        return (
            self.session.query(CBSCMarketData)
            .filter(CBSCMarketData.symbol == symbol)
            .order_by(desc(CBSCMarketData.timestamp))
            .first()
        )

    def get_latest_for_symbols(self, symbols: List[str]) -> List[CBSCMarketData]:
        """Get latest market data for multiple symbols"""
        return (
            self.session.query(CBSCMarketData)
            .filter(CBSCMarketData.symbol.in_(symbols))
            .distinct(CBSCMarketData.symbol)
            .order_by(CBSCMarketData.symbol, desc(CBSCMarketData.timestamp))
            .all()
        )

    def get_high_sentiment_data(
        self,
        min_sentiment: float = 0.5,
        start_date: datetime = None,
        limit: int = 100
    ) -> List[CBSCMarketData]:
        """Get data with high sentiment score"""
        query = self.session.query(CBSCMarketData).filter(
            CBSCMarketData.sentiment_score >= min_sentiment
        )

        if start_date:
            query = query.filter(CBSCMarketData.timestamp >= start_date)

        return query.order_by(desc(CBSCMarketData.sentiment_score)).limit(limit).all()

    def get_low_sentiment_data(
        self,
        max_sentiment: float = -0.5,
        start_date: datetime = None,
        limit: int = 100
    ) -> List[CBSCMarketData]:
        """Get data with low sentiment score"""
        query = self.session.query(CBSCMarketData).filter(
            CBSCMarketData.sentiment_score <= max_sentiment
        )

        if start_date:
            query = query.filter(CBSCMarketData.timestamp >= start_date)

        return query.order_by(CBSCMarketData.sentiment_score).limit(limit).all()

    def get_bullish_stocks(self, limit: int = 50) -> List[CBSCMarketData]:
        """Get stocks with bullish sentiment"""
        return (
            self.session.query(CBSCMarketData)
            .filter(CBSCMarketData.sentiment_score > 0)
            .order_by(desc(CBSCMarketData.sentiment_score))
            .limit(limit)
            .all()
        )

    def get_bearish_stocks(self, limit: int = 50) -> List[CBSCMarketData]:
        """Get stocks with bearish sentiment"""
        return (
            self.session.query(CBSCMarketData)
            .filter(CBSCMarketData.sentiment_score < 0)
            .order_by(CBSCMarketData.sentiment_score)
            .limit(limit)
            .all()
        )

    def get_top_movers(
        self,
        field: str = "price_change_pct",
        limit: int = 20,
        ascending: bool = False
    ) -> List[CBSCMarketData]:
        """Get top price movers (requires computed field in model or query)"""
        # This requires either a computed column or post-query filtering
        # For now, get latest data and sort in Python
        latest_data = self.get_latest_for_all_symbols()
        return sorted(
            latest_data,
            key=lambda x: abs(getattr(x, field, 0)),
            reverse=not ascending
        )[:limit]

    def get_latest_for_all_symbols(self) -> List[CBSCMarketData]:
        """Get latest market data for all tracked symbols"""
        subquery = (
            self.session.query(
                CBSCMarketData.symbol,
                func.max(CBSCMarketData.timestamp).label('max_timestamp')
            )
            .group_by(CBSCMarketData.symbol)
            .subquery()
        )

        return (
            self.session.query(CBSCMarketData)
            .join(
                subquery,
                and_(
                    CBSCMarketData.symbol == subquery.c.symbol,
                    CBSCMarketData.timestamp == subquery.c.max_timestamp
                )
            )
            .all()
        )

    def get_date_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[CBSCMarketData]:
        """Get market data for a specific date range"""
        return (
            self.session.query(CBSCMarketData)
            .filter(
                and_(
                    CBSCMarketData.symbol == symbol,
                    CBSCMarketData.timestamp >= start_date,
                    CBSCMarketData.timestamp <= end_date
                )
            )
            .order_by(CBSCMarketData.timestamp)
            .all()
        )

    def get_aggregated_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "daily"
    ) -> List[dict]:
        """Get aggregated market data (OHLCV) by interval"""
        # This would require more complex SQL with date truncation
        # Simplified version returns raw data
        data = self.get_date_range(symbol, start_date, end_date)

        # Group by date (for daily aggregation)
        from collections import defaultdict
        grouped = defaultdict(lambda: {
            "open": None,
            "high": float('-inf'),
            "low": float('inf'),
            "close": None,
            "volume": 0,
            "bull_bear_ratio": [],
            "sentiment_score": []
        })

        for record in data:
            date_key = record.timestamp.date()
            group = grouped[date_key]

            if group["open"] is None:
                group["open"] = record.open_price
            group["close"] = record.close_price
            group["high"] = max(group["high"], record.high_price)
            group["low"] = min(group["low"], record.low_price)
            group["volume"] += record.volume
            group["bull_bear_ratio"].append(record.bull_bear_ratio)
            group["sentiment_score"].append(record.sentiment_score)

        # Convert to list of dicts
        result = []
        for date, data in sorted(grouped.items()):
            result.append({
                "date": date,
                "open": data["open"],
                "high": data["high"],
                "low": data["low"],
                "close": data["close"],
                "volume": data["volume"],
                "bull_bear_ratio": sum(data["bull_bear_ratio"]) / len(data["bull_bear_ratio"]),
                "sentiment_score": sum(data["sentiment_score"]) / len(data["sentiment_score"])
            })

        return result

    def get_tracked_symbols(self) -> List[str]:
        """Get list of all tracked symbols"""
        symbols = (
            self.session.query(CBSCMarketData.symbol)
            .distinct()
            .order_by(CBSCMarketData.symbol)
            .all()
        )
        return [s[0] for s in symbols]

    def get_symbol_statistics(self, symbol: str, days: int = 30) -> dict:
        """Get statistics for a symbol over recent period"""
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)
        data = self.get_by_symbol(symbol, start_date=start_date, limit=10000)

        if not data:
            return {}

        return {
            "symbol": symbol,
            "data_points": len(data),
            "avg_sentiment": sum(d.sentiment_score for d in data) / len(data),
            "avg_volume": sum(d.volume for d in data) / len(data),
            "price_range": {
                "high": max(d.high_price for d in data),
                "low": min(d.low_price for d in data)
            },
            "bullish_days": sum(1 for d in data if d.sentiment_score > 0),
            "bearish_days": sum(1 for d in data if d.sentiment_score < 0),
            "latest": data[0].to_dict() if data else None
        }

    def delete_old_data(self, days_to_keep: int = 365) -> int:
        """Delete market data older than specified days"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        count = self.session.query(CBSCMarketData).filter(
            CBSCMarketData.timestamp < cutoff_date
        ).delete(synchronize_session=False)

        self.session.commit()
        logger.info(f"Deleted {count} old market data records")
        return count
