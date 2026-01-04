#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Strategy Service
統一策略服務

整合來自三個管理器的功能:
- StrategyManager: 基礎 CRUD 操作
- CBSCStrategyManager: CBSC 業務邏輯
- PersonalStrategyManager: 用戶個人化功能

Architecture Goal: 單一服務入口，消除代碼重複
Performance Goal: 保持現有性能水平
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar, Generic
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_

from ..models.strategy_models_v2 import (
    Strategy, StrategyType, StrategyStatus, RiskLevel,
    StrategyVersion, StrategyInstance, Backtest, StrategyPerformance
)
from ..core.events.event_bus import EventBus, get_event_bus, EventTypes
from ..core.events.event_bus import Event
from .interfaces import IStrategyService, ServiceResponse

logger = logging.getLogger(__name__)

T = TypeVar('T')


class UnifiedStrategyService(IStrategyService):
    """
    Unified strategy service combining all strategy management functionality
    統一策略服務，整合所有策略管理功能
    """

    def __init__(self, db: AsyncSession, event_bus: Optional[EventBus] = None):
        """
        Initialize unified strategy service

        Args:
            db: Database session
            event_bus: Event bus for publishing events
        """
        self.db = db
        self.event_bus = event_bus or get_event_bus()
        self._cache: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize service"""
        logger.info("UnifiedStrategyService initialized")

    async def shutdown(self) -> None:
        """Shutdown service"""
        logger.info("UnifiedStrategyService shut down")
        self._cache.clear()

    def health_check(self) -> bool:
        """Check service health"""
        return True

    # ========== Strategy CRUD ==========

    async def create_strategy(
        self,
        user_id: int,
        name: str,
        strategy_type: StrategyType,
        config: Dict[str, Any],
        description: Optional[str] = None,
        risk_level: Optional[RiskLevel] = RiskLevel.MEDIUM
    ) -> ServiceResponse[Dict]:
        """
        Create new strategy
        創建新策略

        Args:
            user_id: User ID
            name: Strategy name
            strategy_type: Strategy type
            config: Strategy configuration
            description: Strategy description
            risk_level: Risk level

        Returns:
            ServiceResponse with created strategy data
        """
        try:
            # Generate strategy ID
            strategy_id = uuid4()

            # Create strategy instance
            strategy = Strategy(
                id=strategy_id,
                user_id=user_id,
                name=name,
                description=description or "",
                strategy_type=strategy_type,
                risk_level=risk_level,
                parameters=config,
                status=StrategyStatus.DRAFT,
                is_public=False,
                is_template=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            self.db.add(strategy)
            await self.db.flush()

            # Publish event
            await self._publish_event(
                EventTypes.STRATEGY_CREATED,
                {
                    "strategy_id": str(strategy_id),
                    "user_id": user_id,
                    "name": name
                }
            )

            # Clear cache
            self._clear_user_cache(user_id)

            return ServiceResponse.success_response(
                data=self._strategy_to_dict(strategy),
                message=f"Strategy '{name}' created successfully"
            )

        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to create strategy"
            )

    async def get_strategy(
        self,
        strategy_id: UUID,
        user_id: Optional[int] = None
    ) -> ServiceResponse[Dict]:
        """
        Get strategy by ID
        獲取策略詳情

        Args:
            strategy_id: Strategy ID
            user_id: User ID for permission check

        Returns:
            ServiceResponse with strategy data
        """
        try:
            # Check cache first
            cache_key = f"strategy:{strategy_id}"
            if cache_key in self._cache:
                return ServiceResponse.success_response(
                    data=self._cache[cache_key]
                )

            # Query strategy
            query = select(Strategy).where(Strategy.id == strategy_id)

            # Apply permission filter
            if user_id:
                query = query.where(
                    or_(
                        Strategy.user_id == user_id,
                        Strategy.is_public == True
                    )
                )

            result = await self.db.execute(query)
            strategy = result.scalar_one_or_none()

            if not strategy:
                return ServiceResponse.error_response(
                    error="Strategy not found",
                    message=f"Strategy {strategy_id} not found"
                )

            strategy_dict = self._strategy_to_dict(strategy)

            # Cache result
            self._cache[cache_key] = strategy_dict

            return ServiceResponse.success_response(data=strategy_dict)

        except Exception as e:
            logger.error(f"Error getting strategy: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to get strategy"
            )

    async def list_strategies(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> ServiceResponse[List[Dict]]:
        """
        List user's strategies
        獲取用戶策略列表

        Args:
            user_id: User ID
            skip: Number of results to skip
            limit: Maximum number of results
            filters: Optional filters

        Returns:
            ServiceResponse with list of strategies
        """
        try:
            # Build query
            query = select(Strategy).where(
                or_(
                    Strategy.user_id == user_id,
                    Strategy.is_public == True
                )
            )

            # Apply filters if provided
            if filters:
                if "status" in filters:
                    query = query.where(Strategy.status == filters["status"])
                if "strategy_type" in filters:
                    query = query.where(Strategy.strategy_type == filters["strategy_type"])
                if "risk_level" in filters:
                    query = query.where(Strategy.risk_level == filters["risk_level"])
                if "is_public" in filters:
                    query = query.where(Strategy.is_public == filters["is_public"])
                if "is_template" in filters:
                    query = query.where(Strategy.is_template == filters["is_template"])

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Order by updated_at desc
            query = query.order_by(Strategy.updated_at.desc())

            # Execute query
            result = await self.db.execute(query)
            strategies = result.scalars().all()

            # Convert to dict
            strategies_list = [self._strategy_to_dict(s) for s in strategies]

            return ServiceResponse.success_response(
                data=strategies_list,
                message=f"Found {len(strategies_list)} strategies"
            )

        except Exception as e:
            logger.error(f"Error listing strategies: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to list strategies"
            )

    async def update_strategy(
        self,
        strategy_id: UUID,
        user_id: int,
        updates: Dict[str, Any]
    ) -> ServiceResponse[Dict]:
        """
        Update strategy
        更新策略

        Args:
            strategy_id: Strategy ID
            user_id: User ID
            updates: Updates to apply

        Returns:
            ServiceResponse with updated strategy
        """
        try:
            # Verify user owns strategy
            strategy = await self._verify_ownership(strategy_id, user_id)
            if not strategy:
                return ServiceResponse.error_response(
                    error="Permission denied",
                    message="You don't have permission to update this strategy"
                )

            # Apply updates
            for key, value in updates.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)

            strategy.updated_at = datetime.now(timezone.utc)

            # Create new version
            version = StrategyVersion(
                id=uuid4(),
                strategy_id=strategy_id,
                version_number=strategy.version_count + 1,
                parameters=strategy.parameters,
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(version)

            await self.db.commit()

            # Publish event
            await self._publish_event(
                EventTypes.STRATEGY_UPDATED,
                {
                    "strategy_id": str(strategy_id),
                    "user_id": user_id,
                    "updates": updates
                }
            )

            # Clear cache
            self._clear_user_cache(user_id)
            self._clear_cache(f"strategy:{strategy_id}")

            return ServiceResponse.success_response(
                data=self._strategy_to_dict(strategy),
                message="Strategy updated successfully"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating strategy: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to update strategy"
            )

    async def delete_strategy(
        self,
        strategy_id: UUID,
        user_id: int
    ) -> ServiceResponse[None]:
        """
        Delete strategy
        刪除策略

        Args:
            strategy_id: Strategy ID
            user_id: User ID

        Returns:
            ServiceResponse indicating success/failure
        """
        try:
            # Verify user owns strategy
            strategy = await self._verify_ownership(strategy_id, user_id)
            if not strategy:
                return ServiceResponse.error_response(
                    error="Permission denied",
                    message="You don't have permission to delete this strategy"
                )

            # Delete strategy
            await self.db.execute(
                delete(Strategy).where(Strategy.id == strategy_id)
            )
            await self.db.commit()

            # Publish event
            await self._publish_event(
                EventTypes.STRATEGY_DELETED,
                {
                    "strategy_id": str(strategy_id),
                    "user_id": user_id
                }
            )

            # Clear cache
            self._clear_user_cache(user_id)
            self._clear_cache(f"strategy:{strategy_id}")

            return ServiceResponse.success_response(
                message="Strategy deleted successfully"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting strategy: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to delete strategy"
            )

    # ========== Strategy Execution ==========

    async def execute_strategy(
        self,
        strategy_id: UUID,
        user_id: int
    ) -> ServiceResponse[Dict]:
        """
        Execute strategy
        執行策略

        Args:
            strategy_id: Strategy ID
            user_id: User ID

        Returns:
            ServiceResponse with execution result
        """
        try:
            # Verify ownership
            strategy = await self._verify_ownership(strategy_id, user_id)
            if not strategy:
                return ServiceResponse.error_response(
                    error="Strategy not found",
                    message="Strategy not found or permission denied"
                )

            # Create strategy instance
            instance = StrategyInstance(
                id=uuid4(),
                strategy_id=strategy_id,
                user_id=user_id,
                status="running",
                started_at=datetime.now(timezone.utc)
            )
            self.db.add(instance)
            await self.db.flush()

            # Publish event
            await self._publish_event(
                EventTypes.STRATEGY_EXECUTION_STARTED,
                {
                    "strategy_id": str(strategy_id),
                    "instance_id": str(instance.id),
                    "user_id": user_id
                }
            )

            await self.db.commit()

            # TODO: Trigger actual strategy execution in background

            return ServiceResponse.success_response(
                data={
                    "instance_id": str(instance.id),
                    "strategy_id": str(strategy_id),
                    "status": "running",
                    "started_at": instance.started_at.isoformat()
                },
                message="Strategy execution started"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error executing strategy: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to execute strategy"
            )

    async def stop_strategy(
        self,
        strategy_id: UUID,
        user_id: int
    ) -> ServiceResponse[None]:
        """
        Stop strategy execution
        停止策略執行

        Args:
            strategy_id: Strategy ID
            user_id: User ID

        Returns:
            ServiceResponse indicating success/failure
        """
        try:
            # Find running instance
            query = select(StrategyInstance).where(
                and_(
                    StrategyInstance.strategy_id == strategy_id,
                    StrategyInstance.user_id == user_id,
                    StrategyInstance.status == "running"
                )
            )
            result = await self.db.execute(query)
            instance = result.scalar_one_or_none()

            if not instance:
                return ServiceResponse.error_response(
                    error="No running instance found",
                    message="Strategy is not currently running"
                )

            # Stop instance
            instance.status = "stopped"
            instance.stopped_at = datetime.now(timezone.utc)
            await self.db.commit()

            # Publish event
            await self._publish_event(
                EventTypes.STRATEGY_EXECUTION_COMPLETED,
                {
                    "strategy_id": str(strategy_id),
                    "instance_id": str(instance.id),
                    "user_id": user_id,
                    "status": "stopped"
                }
            )

            return ServiceResponse.success_response(
                message="Strategy stopped successfully"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error stopping strategy: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to stop strategy"
            )

    async def get_strategy_status(
        self,
        strategy_id: UUID,
        user_id: int
    ) -> ServiceResponse[Dict]:
        """
        Get strategy execution status
        獲取策略執行狀態

        Args:
            strategy_id: Strategy ID
            user_id: User ID

        Returns:
            ServiceResponse with status data
        """
        try:
            # Get latest instance
            query = select(StrategyInstance).where(
                and_(
                    StrategyInstance.strategy_id == strategy_id,
                    StrategyInstance.user_id == user_id
                )
            ).order_by(StrategyInstance.created_at.desc())

            result = await self.db.execute(query)
            instance = result.scalar_one_or_none()

            if not instance:
                return ServiceResponse.error_response(
                    error="No instance found",
                    message="Strategy has no execution instances"
                )

            status_data = {
                "instance_id": str(instance.id),
                "strategy_id": str(instance.strategy_id),
                "status": instance.status,
                "started_at": instance.started_at.isoformat() if instance.started_at else None,
                "stopped_at": instance.stopped_at.isoformat() if instance.stopped_at else None,
                "performance": instance.performance_data if hasattr(instance, 'performance_data') else None
            }

            return ServiceResponse.success_response(data=status_data)

        except Exception as e:
            logger.error(f"Error getting strategy status: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to get strategy status"
            )

    # ========== Strategy Performance ==========

    async def get_strategy_performance(
        self,
        strategy_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ServiceResponse[List[Dict]]:
        """
        Get strategy performance metrics
        獲取策略績效指標

        Args:
            strategy_id: Strategy ID
            start_date: Start date filter
            end_date: End date filter

        Returns:
            ServiceResponse with performance data
        """
        try:
            # Query performance records
            query = select(StrategyPerformance).where(
                StrategyPerformance.strategy_id == strategy_id
            )

            if start_date:
                query = query.where(StrategyPerformance.date >= start_date)
            if end_date:
                query = query.where(StrategyPerformance.date <= end_date)

            query = query.order_by(StrategyPerformance.date.desc())

            result = await self.db.execute(query)
            performances = result.scalars().all()

            performance_list = []
            for perf in performances:
                performance_list.append({
                    "date": perf.date.isoformat(),
                    "return": perf.total_return,
                    "sharpe_ratio": perf.sharpe_ratio,
                    "max_drawdown": perf.max_drawdown,
                    "win_rate": perf.win_rate,
                    "profit_factor": perf.profit_factor
                })

            return ServiceResponse.success_response(
                data=performance_list,
                message=f"Found {len(performance_list)} performance records"
            )

        except Exception as e:
            logger.error(f"Error getting strategy performance: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to get strategy performance"
            )

    # ========== Helper Methods ==========

    async def _verify_ownership(
        self,
        strategy_id: UUID,
        user_id: int
    ) -> Optional[Strategy]:
        """Verify user owns strategy"""
        query = select(Strategy).where(
            and_(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _strategy_to_dict(self, strategy: Strategy) -> Dict[str, Any]:
        """Convert strategy to dictionary"""
        return {
            "id": str(strategy.id),
            "user_id": strategy.user_id,
            "name": strategy.name,
            "description": strategy.description,
            "strategy_type": strategy.strategy_type.value,
            "risk_level": strategy.risk_level.value,
            "parameters": strategy.parameters,
            "status": strategy.status.value,
            "is_public": strategy.is_public,
            "is_template": strategy.is_template,
            "created_at": strategy.created_at.isoformat(),
            "updated_at": strategy.updated_at.isoformat(),
            "version_count": strategy.version_count
        }

    async def _publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish event to event bus"""
        try:
            event = Event(
                event_type=event_type,
                source="UnifiedStrategyService",
                data=data
            )
            await self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"Error publishing event: {e}")

    def _clear_user_cache(self, user_id: int) -> None:
        """Clear user-specific cache"""
        keys_to_clear = [k for k in self._cache.keys() if k.startswith(f"user:{user_id}")]
        for key in keys_to_clear:
            del self._cache[key]

    def _clear_cache(self, pattern: str) -> None:
        """Clear cache by pattern"""
        if pattern in self._cache:
            del self._cache[pattern]

    # ========== Strategy Templates ==========

    async def clone_template(
        self,
        template_id: UUID,
        user_id: int,
        new_name: str,
        description: Optional[str] = None
    ) -> ServiceResponse[Dict]:
        """
        Clone strategy template
        克隆策略模板

        Args:
            template_id: Template strategy ID
            user_id: User ID
            new_name: Name for cloned strategy
            description: Optional custom description

        Returns:
            ServiceResponse with cloned strategy data
        """
        try:
            # Get template
            template_response = await self.get_strategy(template_id)
            if not template_response.success:
                return ServiceResponse.error_response(
                    error="Template not found",
                    message=f"Template {template_id} not found"
                )

            template_data = template_response.data

            # Verify it's a template
            if not template_data.get("is_template"):
                return ServiceResponse.error_response(
                    error="Invalid template",
                    message="Strategy is not marked as a template"
                )

            # Create clone
            new_strategy_id = uuid4()
            strategy = Strategy(
                id=new_strategy_id,
                user_id=user_id,
                name=new_name,
                description=description or template_data.get("description", ""),
                strategy_type=StrategyType(template_data["strategy_type"]),
                risk_level=RiskLevel(template_data["risk_level"]),
                parameters=template_data["parameters"],
                status=StrategyStatus.DRAFT,
                is_public=False,
                is_template=False,  # Clone is not a template
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            self.db.add(strategy)
            await self.db.commit()

            # Publish event
            await self._publish_event(
                EventTypes.STRATEGY_CREATED,
                {
                    "strategy_id": str(new_strategy_id),
                    "user_id": user_id,
                    "name": new_name,
                    "cloned_from": str(template_id)
                }
            )

            # Clear cache
            self._clear_user_cache(user_id)

            return ServiceResponse.success_response(
                data=self._strategy_to_dict(strategy),
                message=f"Template '{template_data['name']}' cloned successfully"
            )

        except Exception as e:
            logger.error(f"Error cloning template: {e}")
            await self.db.rollback()
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to clone template"
            )

    # ========== Strategy Signals ==========

    async def get_signals(
        self,
        strategy_id: UUID,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> ServiceResponse[List[Dict]]:
        """
        Get strategy signal history
        獲取策略信號歷史

        Args:
            strategy_id: Strategy ID
            user_id: User ID
            limit: Maximum number of signals
            offset: Offset for pagination

        Returns:
            ServiceResponse with signal history
        """
        try:
            # Verify ownership
            strategy = await self._verify_ownership(strategy_id, user_id)
            if not strategy:
                return ServiceResponse.error_response(
                    error="Permission denied",
                    message="Strategy not found or permission denied"
                )

            # Query signals from instances
            query = select(StrategyInstance).where(
                and_(
                    StrategyInstance.strategy_id == strategy_id,
                    StrategyInstance.user_id == user_id
                )
            ).order_by(StrategyInstance.created_at.desc())

            result = await self.db.execute(query)
            instances = result.scalars().all()

            signals = []
            for instance in instances:
                if hasattr(instance, 'last_signal') and instance.last_signal:
                    signals.append({
                        "instance_id": str(instance.id),
                        "signal": instance.last_signal,
                        "created_at": instance.last_signal_at.isoformat() if instance.last_signal_at else None
                    })

            # Apply pagination
            signals = signals[offset:offset + limit]

            return ServiceResponse.success_response(
                data=signals,
                message=f"Found {len(signals)} signals"
            )

        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to get signal history"
            )

    # ========== CBSC Risk Metrics ==========

    async def get_risk_metrics(
        self,
        strategy_id: UUID,
        user_id: int
    ) -> ServiceResponse[Dict]:
        """
        Get CBSC-specific risk metrics
        獲取 CBSC 風險指標

        Args:
            strategy_id: Strategy ID
            user_id: User ID

        Returns:
            ServiceResponse with risk metrics
        """
        try:
            # Verify ownership
            strategy = await self._verify_ownership(strategy_id, user_id)
            if not strategy:
                return ServiceResponse.error_response(
                    error="Permission denied",
                    message="Strategy not found or permission denied"
                )

            # Get performance data
            perf_response = await self.get_strategy_performance(strategy_id)
            if not perf_response.success:
                return ServiceResponse.error_response(
                    error="No performance data",
                    message="Cannot calculate risk metrics without performance data"
                )

            performances = perf_response.data

            # Calculate risk metrics
            # TODO: Implement advanced risk calculation
            risk_metrics = {
                "strategy_id": str(strategy_id),
                "var_95": None,  # Value at Risk at 95% confidence
                "var_99": None,  # Value at Risk at 99% confidence
                "expected_shortfall": None,  # Expected Shortfall
                "beta": None,  # Beta coefficient
                "correlation_matrix": {},  # Correlation matrix
                "risk_contribution": {},  # Risk contribution by position
                "historical_drawdowns": [],  # Historical drawdown periods
                "stress_test_results": {},  # Stress test results
                "message": "Advanced risk metrics calculation not yet implemented"
            }

            return ServiceResponse.success_response(
                data=risk_metrics,
                message="Risk metrics retrieved"
            )

        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to get risk metrics"
            )

    # ========== Execution Report ==========

    async def get_execution_report(
        self,
        strategy_id: UUID,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ServiceResponse[Dict]:
        """
        Get detailed execution report
        獲取詳細執行報告

        Args:
            strategy_id: Strategy ID
            user_id: User ID
            start_date: Start date for report
            end_date: End date for report

        Returns:
            ServiceResponse with execution report
        """
        try:
            # Verify ownership
            strategy = await self._verify_ownership(strategy_id, user_id)
            if not strategy:
                return ServiceResponse.error_response(
                    error="Permission denied",
                    message="Strategy not found or permission denied"
                )

            # TODO: Implement comprehensive execution report generation
            report = {
                "strategy_id": str(strategy_id),
                "strategy_name": strategy.name,
                "period": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "trades": [],  # All trades executed
                "signals": [],  # Signal analysis
                "performance_attribution": {},  # Performance attribution
                "slippage_analysis": {},  # Slippage analysis
                "commission_summary": {},  # Commission summary
                "message": "Detailed execution report generation not yet implemented"
            }

            return ServiceResponse.success_response(
                data=report,
                message="Execution report generated"
            )

        except Exception as e:
            logger.error(f"Error generating execution report: {e}")
            return ServiceResponse.error_response(
                error=str(e),
                message="Failed to generate execution report"
            )
