"""
Background Tasks Service
Handles background calculations for analytics data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .services.performance import PerformanceService
from .services.portfolio import PortfolioService
from .cache import get_cache
from ..database import get_db_context

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manages background calculations for analytics"""

    def __init__(self):
        self.performance_service = PerformanceService()
        self.portfolio_service = PortfolioService()
        self.cache = get_cache()
        self.running_tasks: Dict[str, asyncio.Task] = {}

    async def start_background_calculations(self):
        """Start background calculation workers"""
        logger.info("Starting background calculation workers")

        # Start periodic tasks
        asyncio.create_task(self._periodic_performance_updates())
        asyncio.create_task(self._periodic_portfolio_updates())
        asyncio.create_task(self._cache_cleanup())

    async def calculate_metrics_background(
        self,
        strategy_id: str,
        period: str,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Calculate and cache strategy performance metrics in background

        Args:
            strategy_id: Strategy identifier
            period: Time period
            priority: Task priority (0=low, 1=medium, 2=high)

        Returns:
            Calculation results
        """
        task_key = f"perf:{strategy_id}:{period}"

        # Check if already running
        if task_key in self.running_tasks:
            logger.info(f"Calculation already running for {task_key}")
            return {"status": "already_running", "key": task_key}

        try:
            with get_db_context() as db:
                # Calculate metrics
                metrics = await self.performance_service.calculate_performance(
                    strategy_id=strategy_id,
                    period=period,
                    db=db
                )

                # Cache the result
                cache_key = f"perf:{strategy_id}:{period}"
                await self.cache.set(cache_key, metrics.dict())

                logger.info(f"Background calculation completed for {task_key}")
                return {
                    "status": "completed",
                    "key": task_key,
                    "metrics": metrics.dict()
                }

        except Exception as e:
            logger.error(f"Background calculation failed for {task_key}: {e}")
            return {
                "status": "failed",
                "key": task_key,
                "error": str(e)
            }
        finally:
            # Clean up task tracking
            if task_key in self.running_tasks:
                del self.running_tasks[task_key]

    async def calculate_portfolio_analytics_background(
        self,
        user_id: str,
        include_correlations: bool = False,
        risk_level: str = "95%"
    ) -> Dict[str, Any]:
        """
        Calculate portfolio analytics in background

        Args:
            user_id: User identifier
            include_correlations: Whether to include correlation matrix
            risk_level: VaR confidence level

        Returns:
            Calculation results
        """
        task_key = f"portfolio:{user_id}"

        try:
            with get_db_context() as db:
                # Calculate portfolio analytics
                analytics = await self.portfolio_service.get_portfolio_analytics(
                    user_id=user_id,
                    include_correlations=include_correlations,
                    risk_level=risk_level,
                    db=db
                )

                # Cache the result
                cache_key = f"portfolio:{user_id}"
                await self.cache.set(cache_key, analytics.dict())

                logger.info(f"Background portfolio calculation completed for {user_id}")
                return {
                    "status": "completed",
                    "key": task_key,
                    "analytics": analytics.dict()
                }

        except Exception as e:
            logger.error(f"Background portfolio calculation failed for {user_id}: {e}")
            return {
                "status": "failed",
                "key": task_key,
                "error": str(e)
            }

    async def _periodic_performance_updates(self):
        """Periodic task to update performance metrics"""
        while True:
            try:
                logger.debug("Starting periodic performance updates")

                # Get active strategies
                with get_db_context() as db:
                    active_strategies = await self._get_active_strategies(db)

                # Update metrics for each strategy
                for strategy in active_strategies:
                    strategy_id = strategy['strategy_id']

                    # Update common periods
                    periods = ["1D", "1W", "1M"]
                    for period in periods:
                        asyncio.create_task(
                            self.calculate_metrics_background(strategy_id, period)
                        )

                # Wait before next update
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Error in periodic performance updates: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _periodic_portfolio_updates(self):
        """Periodic task to update portfolio analytics"""
        while True:
            try:
                logger.debug("Starting periodic portfolio updates")

                # Get active users
                with get_db_context() as db:
                    active_users = await self._get_active_users(db)

                # Update portfolio for each user
                for user in active_users:
                    user_id = user['user_id']
                    asyncio.create_task(
                        self.calculate_portfolio_analytics_background(user_id)
                    )

                # Wait before next update
                await asyncio.sleep(900)  # 15 minutes

            except Exception as e:
                logger.error(f"Error in periodic portfolio updates: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _cache_cleanup(self):
        """Periodic cache cleanup"""
        while True:
            try:
                logger.debug("Starting cache cleanup")

                # Clean up expired entries (handled by Redis TTL)
                await self.cache.cleanup_expired()

                # Wait before next cleanup
                await asyncio.sleep(3600)  # 1 hour

            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _get_active_strategies(self, db) -> List[Dict]:
        """Get list of active strategies"""
        from sqlalchemy import text

        query = text("""
            SELECT DISTINCT strategy_id
            FROM strategies
            WHERE status IN ('active', 'paused')
                AND last_activity > DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)

        result = db.execute(query)
        return [dict(row) for row in result]

    async def _get_active_users(self, db) -> List[Dict]:
        """Get list of active users"""
        from sqlalchemy import text

        query = text("""
            SELECT DISTINCT user_id
            FROM strategies
            WHERE status IN ('active', 'paused')
                AND last_activity > DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)

        result = db.execute(query)
        return [dict(row) for row in result]

    async def get_task_status(self, task_key: str) -> Dict[str, Any]:
        """
        Get status of background task

        Args:
            task_key: Task identifier

        Returns:
            Task status information
        """
        if task_key in self.running_tasks:
            task = self.running_tasks[task_key]
            return {
                "status": "running",
                "task_id": id(task),
                "done": task.done(),
                "cancelled": task.cancelled()
            }
        else:
            # Check if result is cached
            cached_result = await self.cache.get(task_key)
            if cached_result:
                return {
                    "status": "completed",
                    "cached": True,
                    "cached_at": cached_result.get("cached_at")
                }
            else:
                return {
                    "status": "not_found"
                }

    async def cancel_task(self, task_key: str) -> bool:
        """
        Cancel a running background task

        Args:
            task_key: Task identifier

        Returns:
            True if cancelled, False if not found
        """
        if task_key in self.running_tasks:
            task = self.running_tasks[task_key]
            task.cancel()
            del self.running_tasks[task_key]
            logger.info(f"Cancelled task: {task_key}")
            return True
        return False

    async def get_running_tasks(self) -> List[Dict[str, Any]]:
        """
        Get list of all running tasks

        Returns:
            List of running task information
        """
        tasks = []
        for task_key, task in self.running_tasks.items():
            tasks.append({
                "key": task_key,
                "task_id": id(task),
                "done": task.done(),
                "cancelled": task.cancelled()
            })
        return tasks

    async def schedule_immediate_update(
        self,
        strategy_id: str,
        periods: List[str] = None
    ):
        """
        Schedule immediate update for strategy metrics

        Args:
            strategy_id: Strategy to update
            periods: List of periods to update (default: common periods)
        """
        if periods is None:
            periods = ["1D", "1W", "1M"]

        logger.info(f"Scheduling immediate update for strategy {strategy_id}")

        for period in periods:
            task_key = f"perf:{strategy_id}:{period}"

            # Cancel existing task if running
            if task_key in self.running_tasks:
                await self.cancel_task(task_key)

            # Invalidate cache
            await self.cache.delete(task_key)

            # Start new calculation
            asyncio.create_task(
                self.calculate_metrics_background(strategy_id, period, priority=2)
            )


# Singleton instance
_task_manager: BackgroundTaskManager = None


def get_task_manager() -> BackgroundTaskManager:
    """Get singleton task manager instance"""
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
    return _task_manager


# Celery task definitions (if using Celery)
try:
    from celery import Celery

    celery_app = Celery('analytics')

    @celery_app.task(bind=True)
    def calculate_strategy_metrics_task(self, strategy_id: str, period: str):
        """Celery task for calculating strategy metrics"""
        manager = get_task_manager()
        result = asyncio.run(
            manager.calculate_metrics_background(strategy_id, period)
        )
        return result

    @celery_app.task(bind=True)
    def calculate_portfolio_analytics_task(self, user_id: str):
        """Celery task for calculating portfolio analytics"""
        manager = get_task_manager()
        result = asyncio.run(
            manager.calculate_portfolio_analytics_background(user_id)
        )
        return result

except ImportError:
    # Celery not installed, tasks will run with asyncio
    pass


def calculate_metrics_background(strategy_id: str, period: str):
    """
    Background task entry point

    This function can be called from the API router to schedule
    background calculations without requiring Celery.
    """
    manager = get_task_manager()
    return asyncio.run(
        manager.calculate_metrics_background(strategy_id, period)
    )