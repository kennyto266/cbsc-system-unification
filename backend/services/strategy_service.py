"""
Strategy service - handles strategy business logic.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from models.strategy import Strategy
from models.user import User
from schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse
)


class StrategyService:
    """Strategy business logic service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        data: StrategyCreate
    ) -> Strategy:
        """
        Create a new strategy.

        Args:
            user_id: Owner user ID
            data: Strategy creation data

        Returns:
            Created strategy
        """
        strategy = Strategy(
            user_id=user_id,
            name=data.name,
            description=data.description,
            category=data.category.value,
            config=data.config,
            status=data.status.value
        )

        self.db.add(strategy)
        await self.db.commit()
        await self.db.refresh(strategy)

        return strategy

    async def get_by_id(
        self,
        strategy_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Strategy]:
        """
        Get strategy by ID.

        Args:
            strategy_id: Strategy ID
            user_id: Optional user ID for ownership check

        Returns:
            Strategy object or None
        """
        strategy = await self.db.get(Strategy, strategy_id)
        if strategy and (user_id is None or strategy.user_id == user_id):
            return strategy
        return None

    async def list(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Strategy]:
        """
        List strategies with optional filters.

        Args:
            user_id: Optional user ID filter
            status: Optional status filter
            category: Optional category filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of strategies
        """
        query = select(Strategy)

        if user_id is not None:
            query = query.where(Strategy.user_id == user_id)
        if status is not None:
            query = query.where(Strategy.status == status)
        if category is not None:
            query = query.where(Strategy.category == category)

        query = query.offset(skip).limit(limit)
        query = query.order_by(Strategy.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        strategy_id: int,
        user_id: int,
        data: StrategyUpdate
    ) -> Optional[Strategy]:
        """
        Update strategy.

        Args:
            strategy_id: Strategy ID
            user_id: Owner user ID
            data: Update data

        Returns:
            Updated strategy or None
        """
        strategy = await self.get_by_id(strategy_id, user_id)
        if not strategy:
            return None

        # Update fields
        if data.name is not None:
            strategy.name = data.name
        if data.description is not None:
            strategy.description = data.description
        if data.category is not None:
            strategy.category = data.category.value
        if data.config is not None:
            strategy.config = data.config
        if data.status is not None:
            strategy.status = data.status.value

        await self.db.commit()
        await self.db.refresh(strategy)

        return strategy

    async def delete(
        self,
        strategy_id: int,
        user_id: int
    ) -> bool:
        """
        Delete strategy.

        Args:
            strategy_id: Strategy ID
            user_id: Owner user ID

        Returns:
            True if deleted
        """
        strategy = await self.get_by_id(strategy_id, user_id)
        if not strategy:
            return False

        await self.db.delete(strategy)
        await self.db.commit()

        return True

    async def toggle_status(
        self,
        strategy_id: int,
        user_id: int,
        is_active: bool
    ) -> Optional[Strategy]:
        """
        Toggle strategy active status.

        Args:
            strategy_id: Strategy ID
            user_id: Owner user ID
            is_active: Desired active state

        Returns:
            Updated strategy or None
        """
        strategy = await self.get_by_id(strategy_id, user_id)
        if not strategy:
            return None

        strategy.status = "active" if is_active else "paused"
        await self.db.commit()
        await self.db.refresh(strategy)

        return strategy

    async def batch_operation(
        self,
        strategy_ids: List[int],
        user_id: int,
        operation: str
    ) -> Dict[int, bool]:
        """
        Perform batch operation on strategies.

        Args:
            strategy_ids: List of strategy IDs
            user_id: Owner user ID
            operation: Operation to perform (start, stop, delete)

        Returns:
            Dictionary mapping strategy IDs to operation result
        """
        results = {}

        for strategy_id in strategy_ids:
            strategy = await self.get_by_id(strategy_id, user_id)
            if not strategy:
                results[strategy_id] = False
                continue

            try:
                if operation == "start":
                    strategy.status = "active"
                elif operation == "stop":
                    strategy.status = "paused"
                elif operation == "delete":
                    await self.db.delete(strategy)

                results[strategy_id] = True
            except Exception:
                results[strategy_id] = False

        await self.db.commit()
        return results
