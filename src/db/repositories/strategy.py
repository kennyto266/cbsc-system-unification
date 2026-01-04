"""
Strategy Repositories

Repository classes for strategy-related data access.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.strategy import Strategy, StrategyParameter, StrategyPerformance, StrategySignal

logger = logging.getLogger(__name__)


class StrategyRepository(BaseRepository[Strategy]):
    """Repository for Strategy model"""

    def __init__(self, session: Session):
        super().__init__(session, Strategy)

    def get_by_name(self, name: str) -> Optional[Strategy]:
        """Get strategy by name"""
        return self.session.query(Strategy).filter(
            Strategy.name == name,
            Strategy.is_deleted == False
        ).first()

    def get_by_creator(
        self,
        creator_id: str,
        skip: int = 0,
        limit: int = 100,
        is_active: bool = None
    ) -> List[Strategy]:
        """Get strategies by creator"""
        query = self.session.query(Strategy).filter(
            Strategy.creator_id == creator_id,
            Strategy.is_deleted == False
        )

        if is_active is not None:
            query = query.filter(Strategy.is_active == is_active)

        return query.order_by(desc(Strategy.created_at)).offset(skip).limit(limit).all()

    def get_by_type(
        self,
        strategy_type: str,
        is_public: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Strategy]:
        """Get strategies by type"""
        return (
            self.session.query(Strategy)
            .filter(
                and_(
                    Strategy.strategy_type == strategy_type,
                    Strategy.is_public == is_public,
                    Strategy.is_active == True,
                    Strategy.is_deleted == False
                )
            )
            .order_by(desc(Strategy.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_strategies(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 100,
        strategy_type: str = None
    ) -> List[Strategy]:
        """Search strategies by keyword in name or description"""
        query = self.session.query(Strategy).filter(
            and_(
                Strategy.is_active == True,
                Strategy.is_public == True,
                Strategy.is_deleted == False,
                or_(
                    Strategy.name.ilike(f"%{keyword}%"),
                    Strategy.description.ilike(f"%{keyword}%")
                )
            )
        )

        if strategy_type:
            query = query.filter(Strategy.strategy_type == strategy_type)

        return query.order_by(desc(Strategy.created_at)).offset(skip).limit(limit).all()

    def get_active_strategies(self, skip: int = 0, limit: int = 100) -> List[Strategy]:
        """Get all active strategies"""
        return (
            self.session.query(Strategy)
            .filter(
                and_(
                    Strategy.is_active == True,
                    Strategy.is_deleted == False
                )
            )
            .order_by(desc(Strategy.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_public_strategies(self, skip: int = 0, limit: int = 100) -> List[Strategy]:
        """Get all public strategies"""
        return (
            self.session.query(Strategy)
            .filter(
                and_(
                    Strategy.is_public == True,
                    Strategy.is_active == True,
                    Strategy.is_deleted == False
                )
            )
            .order_by(desc(Strategy.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def activate(self, id: str) -> Optional[Strategy]:
        """Activate strategy"""
        return self.update(id, {"is_active": True})

    def deactivate(self, id: str) -> Optional[Strategy]:
        """Deactivate strategy"""
        return self.update(id, {"is_active": False})

    def publish(self, id: str) -> Optional[Strategy]:
        """Make strategy public"""
        return self.update(id, {"is_public": True})

    def unpublish(self, id: str) -> Optional[Strategy]:
        """Make strategy private"""
        return self.update(id, {"is_public": False})


class StrategyParameterRepository(BaseRepository[StrategyParameter]):
    """Repository for StrategyParameter model"""

    def __init__(self, session: Session):
        super().__init__(session, StrategyParameter)

    def get_by_strategy(self, strategy_id: str) -> List[StrategyParameter]:
        """Get all parameters for a strategy"""
        return (
            self.session.query(StrategyParameter)
            .filter(StrategyParameter.strategy_id == strategy_id)
            .all()
        )

    def get_optimized_parameters(self, strategy_id: str) -> List[StrategyParameter]:
        """Get optimized parameters for a strategy"""
        return (
            self.session.query(StrategyParameter)
            .filter(
                and_(
                    StrategyParameter.strategy_id == strategy_id,
                    StrategyParameter.is_optimized == True
                )
            )
            .all()
        )

    def bulk_update_for_strategy(
        self,
        strategy_id: str,
        parameters: List[Dict[str, Any]]
    ) -> List[StrategyParameter]:
        """Update all parameters for a strategy"""
        # Delete existing parameters
        self.session.query(StrategyParameter).filter(
            StrategyParameter.strategy_id == strategy_id
        ).delete()

        # Create new parameters
        new_params = []
        for param in parameters:
            param["strategy_id"] = strategy_id
            new_params.append(self.create(param))

        self.session.commit()
        return new_params


class StrategyPerformanceRepository(BaseRepository[StrategyPerformance]):
    """Repository for StrategyPerformance model"""

    def __init__(self, session: Session):
        super().__init__(session, StrategyPerformance)

    def get_by_strategy(
        self,
        strategy_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 1000
    ) -> List[StrategyPerformance]:
        """Get performance records for a strategy"""
        query = self.session.query(StrategyPerformance).filter(
            StrategyPerformance.strategy_id == strategy_id
        )

        if start_date:
            query = query.filter(StrategyPerformance.date >= start_date)
        if end_date:
            query = query.filter(StrategyPerformance.date <= end_date)

        return query.order_by(StrategyPerformance.date).limit(limit).all()

    def get_latest(self, strategy_id: str) -> Optional[StrategyPerformance]:
        """Get latest performance record for a strategy"""
        return (
            self.session.query(StrategyPerformance)
            .filter(StrategyPerformance.strategy_id == strategy_id)
            .order_by(desc(StrategyPerformance.date))
            .first()
        )

    def get_by_backtest(self, backtest_id: str) -> List[StrategyPerformance]:
        """Get all performance records for a backtest"""
        return (
            self.session.query(StrategyPerformance)
            .filter(StrategyPerformance.backtest_id == backtest_id)
            .order_by(StrategyPerformance.date)
            .all()
        )

    def get_top_performers(
        self,
        metric: str = "sharpe_ratio",
        limit: int = 10,
        min_return: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Get top performing strategies"""
        if not hasattr(StrategyPerformance, metric):
            raise ValueError(f"Invalid metric: {metric}")

        query = (
            self.session.query(
                StrategyPerformance.strategy_id,
                func.avg(getattr(StrategyPerformance, metric)).label(metric),
                func.avg(StrategyPerformance.total_return).label('avg_return'),
                func.count(StrategyPerformance.id).label('performance_count')
            )
            .filter(StrategyPerformance.total_return >= min_return)
            .group_by(StrategyPerformance.strategy_id)
            .order_by(desc(metric))
            .limit(limit)
        )

        results = []
        for row in query.all():
            results.append({
                "strategy_id": row.strategy_id,
                metric: float(getattr(row, metric)),
                "avg_return": float(row.avg_return),
                "performance_count": row.performance_count
            })
        return results

    def get_performance_summary(
        self,
        strategy_id: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, float]:
        """Get performance summary for a strategy"""
        query = self.session.query(StrategyPerformance).filter(
            StrategyPerformance.strategy_id == strategy_id
        )

        if start_date:
            query = query.filter(StrategyPerformance.date >= start_date)
        if end_date:
            query = query.filter(StrategyPerformance.date <= end_date)

        performances = query.all()

        if not performances:
            return {}

        return {
            "total_return": max(p.total_return for p in performances),
            "max_drawdown": min(p.max_drawdown for p in performances),
            "sharpe_ratio": max(p.sharpe_ratio for p in performances),
            "win_rate": max(p.win_rate for p in performances),
            "volatility": sum(p.volatility for p in performances) / len(performances),
            "performance_count": len(performances),
            "avg_return": sum(p.total_return for p in performances) / len(performances)
        }


class StrategySignalRepository(BaseRepository[StrategySignal]):
    """Repository for StrategySignal model"""

    def __init__(self, session: Session):
        super().__init__(session, StrategySignal)

    def get_by_strategy(
        self,
        strategy_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[StrategySignal]:
        """Get signals for a strategy"""
        query = self.session.query(StrategySignal).filter(
            StrategySignal.strategy_id == strategy_id
        )

        if start_date:
            query = query.filter(StrategySignal.timestamp >= start_date)
        if end_date:
            query = query.filter(StrategySignal.timestamp <= end_date)

        return query.order_by(desc(StrategySignal.timestamp)).limit(limit).all()

    def get_by_symbol(
        self,
        symbol: str,
        signal_type: str = None,
        start_date: datetime = None,
        limit: int = 100
    ) -> List[StrategySignal]:
        """Get signals for a symbol"""
        query = self.session.query(StrategySignal).filter(
            StrategySignal.symbol == symbol
        )

        if signal_type:
            query = query.filter(StrategySignal.signal_type == signal_type)
        if start_date:
            query = query.filter(StrategySignal.timestamp >= start_date)

        return query.order_by(desc(StrategySignal.timestamp)).limit(limit).all()

    def get_valid_signals(
        self,
        strategy_id: str = None,
        symbol: str = None
    ) -> List[StrategySignal]:
        """Get all valid (non-expired) signals"""
        from datetime import timedelta

        expiry_threshold = datetime.now(timezone.utc) - timedelta(hours=24)

        query = self.session.query(StrategySignal).filter(
            StrategySignal.timestamp > expiry_threshold
        )

        if strategy_id:
            query = query.filter(StrategySignal.strategy_id == strategy_id)
        if symbol:
            query = query.filter(StrategySignal.symbol == symbol)

        return query.order_by(desc(StrategySignal.timestamp)).all()

    def get_buy_signals(
        self,
        strategy_id: str = None,
        min_confidence: float = 50.0,
        limit: int = 50
    ) -> List[StrategySignal]:
        """Get recent buy signals with minimum confidence"""
        query = self.session.query(StrategySignal).filter(
            and_(
                StrategySignal.signal_type == "buy",
                StrategySignal.confidence >= min_confidence
            )
        )

        if strategy_id:
            query = query.filter(StrategySignal.strategy_id == strategy_id)

        return query.order_by(
            desc(StrategySignal.confidence),
            desc(StrategySignal.timestamp)
        ).limit(limit).all()

    def get_sell_signals(
        self,
        strategy_id: str = None,
        min_confidence: float = 50.0,
        limit: int = 50
    ) -> List[StrategySignal]:
        """Get recent sell signals with minimum confidence"""
        query = self.session.query(StrategySignal).filter(
            and_(
                StrategySignal.signal_type == "sell",
                StrategySignal.confidence >= min_confidence
            )
        )

        if strategy_id:
            query = query.filter(StrategySignal.strategy_id == strategy_id)

        return query.order_by(
            desc(StrategySignal.confidence),
            desc(StrategySignal.timestamp)
        ).limit(limit).all()

    def get_unexecuted_signals(self, limit: int = 100) -> List[StrategySignal]:
        """Get all unexecuted signals"""
        return (
            self.session.query(StrategySignal)
            .filter(StrategySignal.is_executed == False)
            .order_by(desc(StrategySignal.timestamp))
            .limit(limit)
            .all()
        )

    def mark_as_executed(
        self,
        signal_id: str,
        execution_price: float
    ) -> Optional[StrategySignal]:
        """Mark signal as executed"""
        return self.update(signal_id, {
            "is_executed": True,
            "executed_at": datetime.now(timezone.utc),
            "execution_price": execution_price
        })

    def get_signal_statistics(self, strategy_id: str) -> Dict[str, Any]:
        """Get signal statistics for a strategy"""
        signals = self.get_by_strategy(strategy_id, limit=10000)

        if not signals:
            return {}

        buy_signals = [s for s in signals if s.signal_type == "buy"]
        sell_signals = [s for s in signals if s.signal_type == "sell"]
        executed_signals = [s for s in signals if s.is_executed]

        return {
            "total_signals": len(signals),
            "buy_signals": len(buy_signals),
            "sell_signals": len(sell_signals),
            "executed_signals": len(executed_signals),
            "execution_rate": len(executed_signals) / len(signals) if signals else 0,
            "avg_confidence": sum(s.confidence for s in signals) / len(signals) if signals else 0
        }
