"""
Backtest service - handles backtest business logic.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from models.backtest import Backtest
from models.strategy import Strategy
from schemas.backtest import (
    BacktestCreate,
    BacktestUpdate,
    BacktestMetrics
)


class BacktestService:
    """Backtest business logic service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        data: BacktestCreate
    ) -> Optional[Backtest]:
        """
        Create a new backtest.

        Args:
            user_id: Owner user ID
            data: Backtest creation data

        Returns:
            Created backtest or None if strategy doesn't exist
        """
        # Verify strategy exists and belongs to user
        strategy = await self.db.get(Strategy, data.strategy_id)
        if not strategy or strategy.user_id != user_id:
            return None

        backtest = Backtest(
            user_id=user_id,
            strategy_id=data.strategy_id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            initial_capital=data.initial_capital,
            config=data.config,
            status="pending"
        )

        self.db.add(backtest)
        await self.db.commit()
        await self.db.refresh(backtest)

        return backtest

    async def get_by_id(
        self,
        backtest_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Backtest]:
        """
        Get backtest by ID.

        Args:
            backtest_id: Backtest ID
            user_id: Optional user ID for ownership check

        Returns:
            Backtest object or None
        """
        backtest = await self.db.get(Backtest, backtest_id)
        if backtest and (user_id is None or backtest.user_id == user_id):
            return backtest
        return None

    async def list(
        self,
        user_id: Optional[int] = None,
        strategy_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Backtest]:
        """
        List backtests with optional filters.

        Args:
            user_id: Optional user ID filter
            strategy_id: Optional strategy ID filter
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of backtests
        """
        query = select(Backtest)

        if user_id is not None:
            query = query.where(Backtest.user_id == user_id)
        if strategy_id is not None:
            query = query.where(Backtest.strategy_id == strategy_id)
        if status is not None:
            query = query.where(Backtest.status == status)

        query = query.offset(skip).limit(limit)
        query = query.order_by(Backtest.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        backtest_id: int,
        user_id: int,
        data: BacktestUpdate
    ) -> Optional[Backtest]:
        """
        Update backtest.

        Args:
            backtest_id: Backtest ID
            user_id: Owner user ID
            data: Update data

        Returns:
            Updated backtest or None
        """
        backtest = await self.get_by_id(backtest_id, user_id)
        if not backtest:
            return None

        # Can only update pending backtests
        if backtest.status != "pending":
            raise ValueError("Can only update pending backtests")

        if data.name is not None:
            backtest.name = data.name
        if data.config is not None:
            backtest.config = data.config

        await self.db.commit()
        await self.db.refresh(backtest)

        return backtest

    async def delete(
        self,
        backtest_id: int,
        user_id: int
    ) -> bool:
        """
        Delete backtest.

        Args:
            backtest_id: Backtest ID
            user_id: Owner user ID

        Returns:
            True if deleted
        """
        backtest = await self.get_by_id(backtest_id, user_id)
        if not backtest:
            return False

        await self.db.delete(backtest)
        await self.db.commit()

        return True

    async def start(
        self,
        backtest_id: int,
        user_id: int,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Backtest]:
        """
        Start backtest execution.

        Args:
            backtest_id: Backtest ID
            user_id: Owner user ID
            config: Optional config overrides

        Returns:
            Updated backtest or None
        """
        backtest = await self.get_by_id(backtest_id, user_id)
        if not backtest:
            return None

        if backtest.status != "pending":
            raise ValueError("Backtest is not in pending status")

        backtest.status = "running"
        backtest.started_at = datetime.utcnow()

        if config:
            backtest.config.update(config)

        await self.db.commit()
        await self.db.refresh(backtest)

        # TODO: Trigger async backtest execution

        return backtest

    async def complete(
        self,
        backtest_id: int,
        metrics: BacktestMetrics
    ) -> Optional[Backtest]:
        """
        Mark backtest as completed with results.

        Args:
            backtest_id: Backtest ID
            metrics: Performance metrics

        Returns:
            Updated backtest or None
        """
        backtest = await self.db.get(Backtest, backtest_id)
        if not backtest:
            return None

        backtest.status = "completed"
        backtest.completed_at = datetime.utcnow()
        backtest.metrics = metrics.model_dump()

        await self.db.commit()
        await self.db.refresh(backtest)

        return backtest

    async def fail(
        self,
        backtest_id: int,
        error_message: str
    ) -> Optional[Backtest]:
        """
        Mark backtest as failed.

        Args:
            backtest_id: Backtest ID
            error_message: Error message

        Returns:
            Updated backtest or None
        """
        backtest = await self.db.get(Backtest, backtest_id)
        if not backtest:
            return None

        backtest.status = "failed"
        backtest.completed_at = datetime.utcnow()
        backtest.error_message = error_message

        await self.db.commit()
        await self.db.refresh(backtest)

        return backtest

    async def cancel(
        self,
        backtest_id: int,
        user_id: int
    ) -> Optional[Backtest]:
        """
        Cancel running backtest.

        Args:
            backtest_id: Backtest ID
            user_id: Owner user ID

        Returns:
            Updated backtest or None
        """
        backtest = await self.get_by_id(backtest_id, user_id)
        if not backtest:
            return None

        if backtest.status != "running":
            raise ValueError("Backtest is not running")

        backtest.status = "cancelled"
        backtest.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(backtest)

        return backtest
