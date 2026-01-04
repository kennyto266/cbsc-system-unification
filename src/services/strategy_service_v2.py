"""
Strategy Service v2.0
Business logic for strategy management operations
Phase 3.2 - 開發策略管理服務
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from uuid import UUID
import logging
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.exc import IntegrityError

from ..models.strategy_models_v2 import (
    Strategy, StrategyVersion, StrategyInstance, Backtest, StrategyPerformance,
    StrategyCategory, StrategyType, StrategyStatus, RiskLevel, TimeFrame
)
from ..models.strategy_validators import (
    StrategyValidator, StrategyValidationError
)
from ..schemas.strategy_schemas import (
    StrategyCreate, StrategyUpdate, StrategyInstanceCreate,
    StrategyFilters, PaginationParams, StrategyInstanceUpdate,
    StrategyCategoryCreate, StrategyCategoryUpdate
)
from ..models.user import User
from ..strategies.strategy_factory_v2 import (
    StrategyFactory, StrategyTemplates
)

logger = logging.getLogger(__name__)


class StrategyService:
    """Strategy management service"""

    def __init__(self, db: Session):
        self.db = db
        self.validator = StrategyValidator(db)

    # Strategy CRUD operations
    def create_strategy(self, strategy_data: StrategyCreate, author_id: UUID) -> Strategy:
        """Create new strategy"""
        try:
            # Validate data
            self.validator.validate_strategy_create(strategy_data, author_id)

            # Create strategy instance
            strategy = Strategy(
                **strategy_data.dict(exclude_unset=True),
                author_id=author_id
            )

            # Set default parameter schema if not provided
            if not strategy.parameter_schema:
                temp_strategy = StrategyFactory.create_strategy_from_config(
                    strategy.strategy_type,
                    strategy.config or {}
                )
                strategy.parameter_schema = temp_strategy.get_parameter_schema()

            # Set default parameters if not provided
            if not strategy.default_parameters:
                temp_strategy = StrategyFactory.create_strategy_from_config(
                    strategy.strategy_type,
                    strategy.config or {}
                )
                strategy.default_parameters = temp_strategy.get_default_parameters()

            self.db.add(strategy)
            self.db.commit()
            self.db.refresh(strategy)

            logger.info(f"Created strategy: {strategy.name} (ID: {strategy.id})")
            return strategy

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create strategy: {e}")
            raise StrategyValidationError("Strategy creation failed due to data integrity error")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create strategy: {e}")
            raise

    def get_strategy(self, strategy_id: UUID, user_id: Optional[UUID] = None) -> Optional[Strategy]:
        """Get strategy by ID with access control"""
        query = self.db.query(Strategy).filter(Strategy.id == strategy_id)

        # Apply access control if user_id provided
        if user_id:
            query = query.filter(
                or_(
                    Strategy.author_id == user_id,
                    Strategy.is_public == True
                )
            )

        strategy = query.first()

        if strategy:
            # Load relationships
            self.db.refresh(strategy, ['category', 'author'])

        return strategy

    def get_strategies(
        self,
        filter_params: Optional[StrategyFilters] = None,
        pagination: Optional[PaginationParams] = None,
        user_id: Optional[UUID] = None
    ) -> Tuple[List[Strategy], int]:
        """Get strategies with filtering and pagination"""
        query = self.db.query(Strategy)

        # Apply access control
        if user_id:
            query = query.filter(
                or_(
                    Strategy.author_id == user_id,
                    Strategy.is_public == True
                )
            )
        else:
            # Public only for unauthenticated users
            query = query.filter(Strategy.is_public == True)

        # Apply filters
        if filter_params:
            if filter_params.search:
                search_term = f"%{filter_params.search}%"
                query = query.filter(
                    or_(
                        Strategy.name.ilike(search_term),
                        Strategy.description.ilike(search_term)
                    )
                )

            if filter_params.strategy_type:
                query = query.filter(Strategy.strategy_type == filter_params.strategy_type)

            if filter_params.status:
                query = query.filter(Strategy.status == filter_params.status)

            if filter_params.category_id:
                query = query.filter(Strategy.category_id == filter_params.category_id)

            if filter_params.risk_level:
                query = query.filter(Strategy.risk_level == filter_params.risk_level)

            if filter_params.is_public is not None:
                query = query.filter(Strategy.is_public == filter_params.is_public)

            if filter_params.is_template is not None:
                query = query.filter(Strategy.is_template == filter_params.is_template)

            if filter_params.featured is not None:
                query = query.filter(Strategy.featured == filter_params.featured)

            if filter_params.tags:
                for tag in filter_params.tags:
                    query = query.filter(Strategy.tags.contains([tag]))

            if filter_params.author_id:
                query = query.filter(Strategy.author_id == filter_params.author_id)

            if filter_params.min_sharpe is not None:
                query = query.filter(Strategy.sharpe_ratio >= filter_params.min_sharpe)

            if filter_params.max_drawdown_max is not None:
                query = query.filter(Strategy.max_drawdown <= filter_params.max_drawdown_max)

            if filter_params.created_after:
                query = query.filter(Strategy.created_at >= filter_params.created_after)

            if filter_params.created_before:
                query = query.filter(Strategy.created_at <= filter_params.created_before)

        # Count total records
        total = query.count()

        # Apply pagination and ordering
        if pagination:
            # Default ordering
            query = query.order_by(desc(Strategy.created_at))
            query = query.offset(pagination.offset).limit(pagination.limit)
        else:
            # Default limit for unpaginated queries
            query = query.limit(100)

        strategies = query.all()

        return strategies, total

    def update_strategy(
        self,
        strategy_id: UUID,
        update_data: StrategyUpdate,
        user_id: UUID
    ) -> Strategy:
        """Update strategy"""
        try:
            # Get strategy
            strategy = self.get_strategy(strategy_id, user_id)
            if not strategy:
                raise StrategyValidationError("Strategy not found or access denied")

            # Validate update
            self.validator.validate_strategy_update(strategy, update_data, user_id)

            # Apply updates
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(strategy, field, value)

            # Update timestamp
            strategy.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(strategy)

            logger.info(f"Updated strategy: {strategy.name} (ID: {strategy.id})")
            return strategy

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update strategy: {e}")
            raise

    def delete_strategy(self, strategy_id: UUID, user_id: UUID) -> bool:
        """Delete strategy"""
        try:
            # Get strategy
            strategy = self.get_strategy(strategy_id, user_id)
            if not strategy:
                raise StrategyValidationError("Strategy not found or access denied")

            # Validate deletion
            self.validator.validate_strategy_deletion(strategy, user_id)

            # Soft delete by archiving
            strategy.status = StrategyStatus.ARCHIVED
            strategy.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Archived strategy: {strategy.name} (ID: {strategy.id})")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete strategy: {e}")
            raise

    def publish_strategy(self, strategy_id: UUID, user_id: UUID) -> Strategy:
        """Publish strategy to public gallery"""
        try:
            strategy = self.get_strategy(strategy_id, user_id)
            if not strategy:
                raise StrategyValidationError("Strategy not found or access denied")

            # Validate publish requirements
            self.validator.validate_strategy_publish(strategy)

            # Update strategy
            strategy.is_public = True
            strategy.status = StrategyStatus.ACTIVE
            strategy.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(strategy)

            logger.info(f"Published strategy: {strategy.name} (ID: {strategy.id})")
            return strategy

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to publish strategy: {e}")
            raise

    # Strategy Version management
    def create_strategy_version(
        self,
        strategy_id: UUID,
        version_data: Dict[str, Any],
        author_id: UUID
    ) -> StrategyVersion:
        """Create new strategy version"""
        try:
            strategy = self.get_strategy(strategy_id, author_id)
            if not strategy:
                raise StrategyValidationError("Strategy not found or access denied")

            # Validate version uniqueness
            existing_version = self.db.query(StrategyVersion).filter(
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.version == version_data['version']
            ).first()

            if existing_version:
                raise StrategyValidationError(f"Version {version_data['version']} already exists")

            # Create version
            version = StrategyVersion(
                strategy_id=strategy_id,
                created_by=author_id,
                **version_data
            )

            self.db.add(version)
            self.db.commit()
            self.db.refresh(version)

            logger.info(f"Created strategy version: {strategy.name} v{version.version}")
            return version

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create strategy version: {e}")
            raise

    def get_strategy_versions(
        self,
        strategy_id: UUID,
        user_id: Optional[UUID] = None
    ) -> List[StrategyVersion]:
        """Get strategy versions"""
        # Check strategy access
        strategy = self.get_strategy(strategy_id, user_id)
        if not strategy:
            return []

        versions = self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id
        ).order_by(desc(StrategyVersion.created_at)).all()

        return versions

    # Strategy Instance management
    async def create_strategy_instance(
        self,
        instance_data: StrategyInstanceCreate,
        user_id: UUID
    ) -> StrategyInstance:
        """Create strategy instance"""
        try:
            # Validate strategy exists and user has access
            strategy = await self.get_strategy(instance_data.strategy_id, user_id)

            # Check for duplicate instance name for this strategy
            existing = await self.db.execute(
                select(StrategyInstance).where(
                    StrategyInstance.strategy_id == instance_data.strategy_id,
                    StrategyInstance.instance_name == instance_data.instance_name,
                    StrategyInstance.created_by == user_id
                )
            )
            if existing.scalar_one_or_none():
                raise StrategyValidationError(
                    f"Instance '{instance_data.instance_name}' already exists for this strategy"
                )

            # Create instance
            instance = StrategyInstance(
                strategy_id=instance_data.strategy_id,
                instance_name=instance_data.instance_name,
                description=instance_data.description,
                config=instance_data.config or {},
                timeframe=instance_data.timeframe,
                capital_allocation=instance_data.capital_allocation,
                status=StrategyStatus.ACTIVE if instance_data.is_enabled else StrategyStatus.PAUSED,
                is_enabled=instance_data.is_enabled,
                created_by=user_id
            )

            # Set initial equity based on capital allocation
            if instance.capital_allocation:
                instance.current_equity = instance.capital_allocation

            self.db.add(instance)
            await self.db.commit()
            await self.db.refresh(instance)

            logger.info(f"Created strategy instance: {instance.instance_name} (ID: {instance.id})")
            return instance

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create strategy instance: {e}")
            raise

    async def get_strategy_instances(
        self,
        user_id: UUID,
        strategy_id: Optional[UUID] = None,
        status: Optional[StrategyStatus] = None,
        timeframe: Optional[TimeFrame] = None,
        include_performance: bool = False,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Get user's strategy instances with pagination and optional performance data"""
        try:
            # Build base query
            conditions = [StrategyInstance.created_by == user_id]

            if strategy_id:
                conditions.append(StrategyInstance.strategy_id == strategy_id)

            if status:
                conditions.append(StrategyInstance.status == status)

            if timeframe:
                conditions.append(StrategyInstance.timeframe == timeframe)

            # Get total count
            count_query = select(func.count(StrategyInstance.id)).where(and_(*conditions))
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Calculate pagination
            offset = (page - 1) * page_size

            # Get instances with strategy info
            query = (
                select(StrategyInstance, Strategy.name.label('strategy_name'))
                .join(Strategy, StrategyInstance.strategy_id == Strategy.id)
                .where(and_(*conditions))
                .order_by(desc(StrategyInstance.created_at))
                .offset(offset)
                .limit(page_size)
            )

            result = await self.db.execute(query)
            rows = result.all()

            # Build response
            instances = []
            for instance, strategy_name in rows:
                instance_data = {
                    'id': instance.id,
                    'strategy_id': instance.strategy_id,
                    'strategy_name': strategy_name,
                    'instance_name': instance.instance_name,
                    'description': instance.description,
                    'config': instance.config,
                    'timeframe': instance.timeframe,
                    'capital_allocation': instance.capital_allocation,
                    'current_equity': instance.current_equity,
                    'status': instance.status,
                    'is_enabled': instance.is_enabled,
                    'last_run_at': instance.last_run_at,
                    'created_at': instance.created_at,
                    'updated_at': instance.updated_at
                }

                # Include performance data if requested
                if include_performance:
                    performance = await self._get_instance_performance(instance.id)
                    instance_data['performance'] = performance

                instances.append(instance_data)

            return {
                'instances': instances,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': (total + page_size - 1) // page_size
                }
            }

        except Exception as e:
            logger.error(f"Failed to get strategy instances: {e}")
            raise

    async def update_strategy_instance(
        self,
        instance_id: UUID,
        update_data: Dict[str, Any],
        user_id: UUID
    ) -> StrategyInstance:
        """Update strategy instance"""
        try:
            # Get instance with access check
            instance = await self.get_strategy_instance_by_id(instance_id, user_id)

            # Check if updating instance name would cause conflict
            if 'instance_name' in update_data:
                existing = await self.db.execute(
                    select(StrategyInstance).where(
                        StrategyInstance.strategy_id == instance.strategy_id,
                        StrategyInstance.instance_name == update_data['instance_name'],
                        StrategyInstance.id != instance_id,
                        StrategyInstance.created_by == user_id
                    )
                )
                if existing.scalar_one_or_none():
                    raise StrategyValidationError(
                        f"Instance name '{update_data['instance_name']}' already exists for this strategy"
                    )

            # Apply updates
            for field, value in update_data.items():
                if hasattr(instance, field) and field not in ['id', 'created_at', 'created_by']:
                    setattr(instance, field, value)

            instance.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(instance)

            logger.info(f"Updated strategy instance: {instance.instance_name} (ID: {instance.id})")
            return instance

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update strategy instance: {e}")
            raise

    async def get_strategy_instance_by_id(self, instance_id: UUID, user_id: UUID) -> StrategyInstance:
        """Get strategy instance by ID with access check"""
        result = await self.db.execute(
            select(StrategyInstance).where(
                StrategyInstance.id == instance_id,
                StrategyInstance.created_by == user_id
            )
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise StrategyNotFoundError(f"Strategy instance {instance_id} not found or access denied")

        return instance

    async def delete_strategy_instance(self, instance_id: UUID, user_id: UUID, force: bool = False) -> bool:
        """Delete strategy instance"""
        try:
            instance = await self.get_strategy_instance_by_id(instance_id, user_id)

            # Check if instance is running
            if instance.status == StrategyStatus.ACTIVE and not force:
                raise StrategyValidationError(
                    "Cannot delete running instance. Stop it first or use force=True"
                )

            # Check for active trades
            if not force:
                active_trades = await self.db.execute(
                    select(func.count(Trade.id)).where(
                        Trade.instance_id == instance_id,
                        Trade.status.in_(["open", "pending"])
                    )
                )
                if active_trades.scalar() > 0:
                    raise StrategyValidationError(
                        "Cannot delete instance with active trades. Close trades first or use force=True"
                    )

            await self.db.delete(instance)
            await self.db.commit()

            logger.info(f"Deleted strategy instance: {instance.instance_name} (ID: {instance.id})")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete strategy instance: {e}")
            raise

    async def start_strategy_instance(self, instance_id: UUID, user_id: UUID) -> StrategyInstance:
        """Start strategy instance"""
        try:
            instance = await self.get_strategy_instance_by_id(instance_id, user_id)

            if instance.status == StrategyStatus.ACTIVE:
                raise StrategyValidationError("Instance is already running")

            if not instance.is_enabled:
                raise StrategyValidationError("Instance is disabled. Enable it first.")

            # Update instance status
            instance.status = StrategyStatus.ACTIVE
            instance.last_run_at = datetime.utcnow()
            instance.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(instance)

            # TODO: Trigger actual strategy execution via task queue
            # This would integrate with the backtest engine or execution engine

            logger.info(f"Started strategy instance: {instance.instance_name} (ID: {instance.id})")
            return instance

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to start strategy instance: {e}")
            raise

    async def stop_strategy_instance(self, instance_id: UUID, user_id: UUID) -> StrategyInstance:
        """Stop strategy instance"""
        try:
            instance = await self.get_strategy_instance_by_id(instance_id, user_id)

            if instance.status != StrategyStatus.ACTIVE:
                raise StrategyValidationError("Instance is not running")

            # Update instance status
            instance.status = StrategyStatus.PAUSED
            instance.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(instance)

            # TODO: Signal execution engine to stop this instance
            # Cancel any pending orders, close positions if configured

            logger.info(f"Stopped strategy instance: {instance.instance_name} (ID: {instance.id})")
            return instance

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to stop strategy instance: {e}")
            raise

    async def get_instance_performance(self, instance_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get strategy instance performance metrics"""
        try:
            # Verify access
            await self.get_strategy_instance_by_id(instance_id, user_id)

            # Get performance from database
            result = await self.db.execute(
                select(StrategyPerformance).where(
                    StrategyPerformance.instance_id == instance_id
                ).order_by(desc(StrategyPerformance.date)).limit(1)
            )
            performance = result.scalar_one_or_none()

            if not performance:
                return {
                    'instance_id': instance_id,
                    'total_return': 0.0,
                    'annual_return': 0.0,
                    'max_drawdown': 0.0,
                    'sharpe_ratio': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'total_trades': 0,
                    'last_updated': datetime.utcnow()
                }

            # Get trade statistics
            trade_stats = await self._get_trade_statistics(instance_id)

            return {
                'instance_id': instance_id,
                'total_return': float(performance.total_return or 0.0),
                'annual_return': float(performance.annual_return or 0.0),
                'max_drawdown': float(performance.max_drawdown or 0.0),
                'sharpe_ratio': float(performance.sharpe_ratio or 0.0),
                'win_rate': float(performance.win_rate or 0.0),
                'profit_factor': float(performance.profit_factor or 0.0),
                'volatility': float(performance.volatility or 0.0),
                'var': float(performance.var_95 or 0.0),
                **trade_stats,
                'last_updated': performance.date
            }

        except Exception as e:
            logger.error(f"Failed to get instance performance: {e}")
            raise

    async def _get_instance_performance(self, instance_id: UUID) -> Dict[str, Any]:
        """Internal method to get instance performance without access check"""
        result = await self.db.execute(
            select(StrategyPerformance).where(
                StrategyPerformance.instance_id == instance_id
            ).order_by(desc(StrategyPerformance.date)).limit(1)
        )
        performance = result.scalar_one_or_none()

        if not performance:
            return {}

        return {
            'total_return': float(performance.total_return or 0.0),
            'annual_return': float(performance.annual_return or 0.0),
            'max_drawdown': float(performance.max_drawdown or 0.0),
            'sharpe_ratio': float(performance.sharpe_ratio or 0.0),
            'win_rate': float(performance.win_rate or 0.0),
            'volatility': float(performance.volatility or 0.0)
        }

    async def _get_trade_statistics(self, instance_id: UUID) -> Dict[str, Any]:
        """Get trade statistics for an instance"""
        # Total trades
        total_trades = await self.db.execute(
            select(func.count(Trade.id)).where(Trade.instance_id == instance_id)
        )
        total_trades = total_trades.scalar() or 0

        # Winning trades
        winning_trades = await self.db.execute(
            select(func.count(Trade.id)).where(
                Trade.instance_id == instance_id,
                Trade.pnl > 0
            )
        )
        winning_trades = winning_trades.scalar() or 0

        # Total PnL
        total_pnl = await self.db.execute(
            select(func.sum(Trade.pnl)).where(Trade.instance_id == instance_id)
        )
        total_pnl = float(total_pnl.scalar() or 0.0)

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'total_pnl': total_pnl
        }

    # Backtest management
    def create_backtest(self, backtest_data: Dict[str, Any], user_id: UUID) -> Backtest:
        """Create backtest"""
        try:
            # Validate backtest creation
            self.validator.validate_backtest_create(backtest_data, user_id)

            # Create backtest
            backtest = Backtest(
                **backtest_data.dict(exclude_unset=True),
                user_id=user_id,
                status="running"
            )

            self.db.add(backtest)
            self.db.commit()
            self.db.refresh(backtest)

            logger.info(f"Created backtest: {backtest.name} (ID: {backtest.id})")
            return backtest

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create backtest: {e}")
            raise

    def get_backtests(
        self,
        user_id: Optional[UUID] = None,
        strategy_id: Optional[UUID] = None,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Backtest]:
        """Get backtests"""
        query = self.db.query(Backtest)

        # Apply filters
        if user_id:
            query = query.filter(Backtest.user_id == user_id)

        if strategy_id:
            query = query.filter(Backtest.strategy_id == strategy_id)

        if filter_params:
            if filter_params.status:
                query = query.filter(Backtest.status == filter_params.status)

            if filter_params.symbols:
                for symbol in filter_params.symbols:
                    query = query.filter(Backtest.symbols.contains([symbol]))

            if filter_params.start_date_after:
                query = query.filter(Backtest.start_date >= filter_params.start_date_after)

            if filter_params.start_date_before:
                query = query.filter(Backtest.start_date <= filter_params.start_date_before)

            if filter_params.min_return is not None:
                query = query.filter(Backtest.total_return >= filter_params.min_return)

            if filter_params.max_drawdown_max is not None:
                query = query.filter(Backtest.max_drawdown <= filter_params.max_drawdown_max)

            if filter_params.min_sharpe is not None:
                query = query.filter(Backtest.sharpe_ratio >= filter_params.min_sharpe)

        backtests = query.order_by(desc(Backtest.created_at)).limit(100).all()
        return backtests

    # Performance tracking
    def record_strategy_performance(
        self,
        strategy_id: UUID,
        performance_data: Dict[str, Any]
    ) -> StrategyPerformance:
        """Record strategy performance"""
        try:
            # Check for existing record
            existing = self.db.query(StrategyPerformance).filter(
                StrategyPerformance.strategy_id == strategy_id,
                StrategyPerformance.date == performance_data['date']
            ).first()

            if existing:
                # Update existing record
                for field, value in performance_data.items():
                    if field != 'date':
                        setattr(existing, field, value)
                performance = existing
            else:
                # Create new record
                performance = StrategyPerformance(
                    strategy_id=strategy_id,
                    **performance_data
                )
                self.db.add(performance)

            self.db.commit()
            return performance

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record performance: {e}")
            raise

    def get_strategy_performance(
        self,
        strategy_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[StrategyPerformance]:
        """Get strategy performance records"""
        query = self.db.query(StrategyPerformance).filter(
            StrategyPerformance.strategy_id == strategy_id
        )

        if start_date:
            query = query.filter(StrategyPerformance.date >= start_date)

        if end_date:
            query = query.filter(StrategyPerformance.date <= end_date)

        performance = query.order_by(desc(StrategyPerformance.date)).all()
        return performance

    # Analytics and statistics
    def get_strategy_statistics(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get strategy statistics"""
        query = self.db.query(Strategy)

        if user_id:
            query = query.filter(Strategy.author_id == user_id)

        total = query.count()
        active = query.filter(Strategy.status == StrategyStatus.ACTIVE).count()
        draft = query.filter(Strategy.status == StrategyStatus.DRAFT).count()
        testing = query.filter(Strategy.status == StrategyStatus.TESTING).count()

        # By type
        by_type = query.with_entities(
            Strategy.strategy_type,
            func.count(Strategy.id)
        ).group_by(Strategy.strategy_type).all()

        # By risk level
        by_risk = query.with_entities(
            Strategy.risk_level,
            func.count(Strategy.id)
        ).group_by(Strategy.risk_level).all()

        return {
            'total': total,
            'active': active,
            'draft': draft,
            'testing': testing,
            'by_type': dict(by_type),
            'by_risk': dict(by_risk)
        }

    # Template management
    def get_strategy_templates(self) -> List[Dict[str, Any]]:
        """Get available strategy templates"""
        return [
            StrategyTemplates.ma_crossover_strategy(),
            StrategyTemplates.rsi_mean_reversion_strategy(),
            StrategyTemplates.momentum_breakout_strategy()
        ]

    def create_strategy_from_template(
        self,
        template_name: str,
        customizations: Dict[str, Any],
        author_id: UUID
    ) -> Strategy:
        """Create strategy from template"""
        templates = {
            'ma_crossover': StrategyTemplates.ma_crossover_strategy,
            'rsi_mean_reversion': StrategyTemplates.rsi_mean_reversion_strategy,
            'momentum_breakout': StrategyTemplates.momentum_breakout_strategy
        }

        if template_name not in templates:
            raise StrategyValidationError(f"Unknown template: {template_name}")

        # Get template
        template = templates[template_name]()

        # Apply customizations
        for key, value in customizations.items():
            if key in template:
                template[key] = value

        # Create strategy
        strategy_data = StrategyCreate(**template)
        return self.create_strategy(strategy_data, author_id)

    # Category CRUD operations
    async def create_category(
        self,
        category_data: StrategyCategoryCreate,
        author_id: UUID
    ) -> StrategyCategory:
        """Create strategy category"""
        # Check if slug already exists
        existing = await self.db.execute(
            select(StrategyCategory).where(StrategyCategory.slug == category_data.slug)
        )
        if existing.scalar_one_or_none():
            raise StrategyValidationError(f"Category slug '{category_data.slug}' already exists")

        # If parent_id provided, verify parent exists
        if category_data.parent_id:
            parent = await self.db.get(StrategyCategory, category_data.parent_id)
            if not parent:
                raise StrategyValidationError(f"Parent category {category_data.parent_id} not found")

        category = StrategyCategory(
            name=category_data.name,
            slug=category_data.slug,
            description=category_data.description,
            parent_id=category_data.parent_id,
            icon=category_data.icon,
            sort_order=category_data.sort_order or 0,
            created_by=author_id
        )

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update_category(
        self,
        category_id: UUID,
        category_data: StrategyCategoryUpdate
    ) -> StrategyCategory:
        """Update strategy category"""
        category = await self.get_category_by_id(category_id)

        # Update fields
        update_data = category_data.model_dump(exclude_unset=True)

        # If updating slug, check for conflicts
        if 'slug' in update_data:
            existing = await self.db.execute(
                select(StrategyCategory).where(
                    StrategyCategory.slug == update_data['slug'],
                    StrategyCategory.id != category_id
                )
            )
            if existing.scalar_one_or_none():
                raise StrategyValidationError(f"Category slug '{update_data['slug']}' already exists")

        # If updating parent_id, verify parent exists and prevent cycles
        if 'parent_id' in update_data:
            if update_data['parent_id']:
                parent = await self.db.get(StrategyCategory, update_data['parent_id'])
                if not parent:
                    raise StrategyValidationError(f"Parent category {update_data['parent_id']} not found")

                # Prevent creating cycles
                if await self._would_create_cycle(category_id, update_data['parent_id']):
                    raise StrategyValidationError("Cannot move category under its own descendant")

        # Apply updates
        for field, value in update_data.items():
            setattr(category, field, value)

        category.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete_category(self, category_id: UUID, force: bool = False) -> bool:
        """Delete strategy category"""
        category = await self.get_category_by_id(category_id)

        # Check if category has strategies
        strategy_count = await self.db.execute(
            select(func.count(Strategy.id))
            .where(Strategy.category_id == category_id)
        )
        strategy_count = strategy_count.scalar()

        # Check if category has subcategories
        subcategory_count = await self.db.execute(
            select(func.count(StrategyCategory.id))
            .where(StrategyCategory.parent_id == category_id)
        )
        subcategory_count = subcategory_count.scalar()

        if not force and (strategy_count > 0 or subcategory_count > 0):
            raise StrategyValidationError(
                f"Cannot delete category '{category.name}': "
                f"contains {strategy_count} strategies and {subcategory_count} subcategories. "
                f"Use force=True to delete anyway."
            )

        if force:
            # Move strategies to parent category or uncategorized
            if strategy_count > 0:
                target_category_id = category.parent_id
                await self.db.execute(
                    update(Strategy)
                    .where(Strategy.category_id == category_id)
                    .values(category_id=target_category_id)
                )

            # Move subcategories to parent category
            if subcategory_count > 0:
                await self.db.execute(
                    update(StrategyCategory)
                    .where(StrategyCategory.parent_id == category_id)
                    .values(parent_id=category.parent_id)
                )

        await self.db.delete(category)
        await self.db.commit()
        return True

    async def get_category_by_id(self, category_id: UUID) -> StrategyCategory:
        """Get category by ID"""
        category = await self.db.get(StrategyCategory, category_id)
        if not category:
            raise StrategyNotFoundError(f"Category {category_id} not found")
        return category

    async def get_category_by_slug(self, slug: str) -> StrategyCategory:
        """Get category by slug"""
        result = await self.db.execute(
            select(StrategyCategory).where(StrategyCategory.slug == slug)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise StrategyNotFoundError(f"Category '{slug}' not found")
        return category

    async def get_categories(
        self,
        parent_id: Optional[UUID] = None,
        include_strategy_count: bool = False,
        include_subtree: bool = False
    ) -> List[Dict[str, Any]]:
        """Get categories with optional strategy counts"""
        query = select(StrategyCategory)

        if parent_id is not None:
            query = query.where(StrategyCategory.parent_id == parent_id)

        result = await self.db.execute(query.order_by(StrategyCategory.sort_order, StrategyCategory.name))
        categories = result.scalars().all()

        # Convert to dict format
        category_data = []
        for category in categories:
            data = {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'parent_id': category.parent_id,
                'icon': category.icon,
                'sort_order': category.sort_order,
                'is_active': category.is_active,
                'created_at': category.created_at,
                'updated_at': category.updated_at
            }

            if include_strategy_count:
                count_query = select(func.count(Strategy.id)).where(
                    Strategy.category_id == category.id,
                    Strategy.is_active == True
                )
                count_result = await self.db.execute(count_query)
                data['strategy_count'] = count_result.scalar()

            if include_subtree:
                data['subcategories'] = await self.get_categories(
                    parent_id=category.id,
                    include_strategy_count=include_strategy_count
                )

            category_data.append(data)

        return category_data

    async def get_category_tree(self, include_strategy_count: bool = False) -> List[Dict[str, Any]]:
        """Get full category tree"""
        return await self.get_categories(
            parent_id=None,
            include_strategy_count=include_strategy_count,
            include_subtree=True
        )

    async def _would_create_cycle(self, category_id: UUID, new_parent_id: UUID) -> bool:
        """Check if moving category to new_parent would create a cycle"""
        # Get all descendants of the category
        descendants = await self.db.execute(
            select(StrategyCategory.id).where(
                StrategyCategory.parent_id == category_id
            ).cte_recursive()
        )

        descendant_ids = [row[0] for row in descendants.fetchall()]
        return new_parent_id in descendant_ids

    async def get_category_statistics(self, category_id: UUID) -> Dict[str, Any]:
        """Get category statistics"""
        category = await self.get_category_by_id(category_id)

        # Strategy count
        strategy_count = await self.db.execute(
            select(func.count(Strategy.id))
            .where(Strategy.category_id == category_id)
        )
        strategy_count = strategy_count.scalar()

        # Subcategory count
        subcategory_count = await self.db.execute(
            select(func.count(StrategyCategory.id))
            .where(StrategyCategory.parent_id == category_id)
        )
        subcategory_count = subcategory_count.scalar()

        # Active strategies
        active_strategies = await self.db.execute(
            select(func.count(Strategy.id))
            .where(
                Strategy.category_id == category_id,
                Strategy.is_active == True
            )
        )
        active_strategies = active_strategies.scalar()

        # Total performance metrics for strategies in this category
        avg_return = await self.db.execute(
            select(func.avg(StrategyPerformance.annual_return))
            .join(Strategy)
            .where(Strategy.category_id == category_id)
        )
        avg_return = avg_return.scalar() or 0.0

        return {
            'category_id': category_id,
            'category_name': category.name,
            'total_strategies': strategy_count,
            'active_strategies': active_strategies,
            'subcategory_count': subcategory_count,
            'average_annual_return': float(avg_return),
            'last_updated': datetime.utcnow()
        }

    # Additional category management methods
    async def batch_update_categories(
        self,
        category_ids: List[UUID],
        updates: Dict[str, Any],
        user_id: UUID
    ) -> List[StrategyCategory]:
        """Batch update multiple categories"""
        try:
            # Get all categories
            result = await self.db.execute(
                select(StrategyCategory).where(StrategyCategory.id.in_(category_ids))
            )
            categories = result.scalars().all()

            updated_categories = []

            for category in categories:
                # Apply updates
                for field, value in updates.items():
                    if field == "sort_order_increment":
                        category.sort_order += value
                    elif field == "sort_order":
                        category.sort_order = value
                    elif hasattr(category, field):
                        setattr(category, field, value)

                category.updated_at = datetime.utcnow()
                updated_categories.append(category)

            await self.db.commit()

            logger.info(f"Batch updated {len(updated_categories)} categories")
            return updated_categories

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to batch update categories: {e}")
            raise

    async def move_category(
        self,
        category_id: UUID,
        new_parent_id: Optional[UUID],
        user_id: UUID
    ) -> StrategyCategory:
        """Move category to new parent"""
        try:
            category = await self.get_category_by_id(category_id)

            if new_parent_id:
                # Get parent category
                parent = await self.get_category_by_id(new_parent_id)

                # Check for cycles
                if await self._would_create_cycle(category_id, new_parent_id):
                    raise StrategyValidationError("Cannot move category under its own descendant")

                category.parent_id = new_parent_id
            else:
                category.parent_id = None

            category.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(category)

            logger.info(f"Moved category {category.name} to new parent")
            return category

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to move category: {e}")
            raise

    async def search_categories(
        self,
        query: str,
        limit: int = 50
    ) -> List[StrategyCategory]:
        """Search categories by name or description"""
        try:
            search_pattern = f"%{query}%"
            result = await self.db.execute(
                select(StrategyCategory)
                .where(
                    or_(
                        StrategyCategory.name.ilike(search_pattern),
                        StrategyCategory.description.ilike(search_pattern)
                    )
                )
                .order_by(StrategyCategory.sort_order, StrategyCategory.name)
                .limit(limit)
            )

            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to search categories: {e}")
            raise

    async def export_categories(
        self,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export categories data"""
        try:
            # Get all categories with strategy counts
            categories = await self.get_categories(include_strategy_count=True)

            # Build export data
            export_data = {
                "categories": [],
                "exported_at": datetime.utcnow().isoformat(),
                "total_count": len(categories)
            }

            for category in categories:
                export_data["categories"].append({
                    "id": str(category["id"]),
                    "name": category["name"],
                    "slug": category["slug"],
                    "description": category["description"],
                    "parent_id": str(category["parent_id"]) if category["parent_id"] else None,
                    "icon": category["icon"],
                    "sort_order": category["sort_order"],
                    "is_active": category["is_active"],
                    "strategy_count": category.get("strategy_count", 0)
                })

            if format.lower() == "json":
                return export_data
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Failed to export categories: {e}")
            raise

    async def import_categories(
        self,
        categories_data: List[Dict[str, Any]],
        user_id: UUID,
        overwrite: bool = False
    ) -> List[StrategyCategory]:
        """Import categories from data"""
        try:
            imported_categories = []

            for category_data in categories_data:
                # Check if category exists by slug
                existing = await self.db.execute(
                    select(StrategyCategory).where(
                        StrategyCategory.slug == category_data.get("slug")
                    )
                )
                existing_category = existing.scalar_one_or_none()

                if existing_category:
                    if overwrite:
                        # Update existing category
                        for field, value in category_data.items():
                            if field in ["name", "description", "icon", "sort_order", "is_active"]:
                                setattr(existing_category, field, value)
                        existing_category.updated_at = datetime.utcnow()
                        imported_categories.append(existing_category)
                    else:
                        continue  # Skip existing category
                else:
                    # Create new category
                    new_category = StrategyCategory(
                        name=category_data.get("name"),
                        slug=category_data.get("slug"),
                        description=category_data.get("description"),
                        icon=category_data.get("icon"),
                        sort_order=category_data.get("sort_order", 0),
                        is_active=category_data.get("is_active", True),
                        parent_id=category_data.get("parent_id"),
                        created_by=user_id
                    )
                    self.db.add(new_category)
                    imported_categories.append(new_category)

            await self.db.commit()

            # Refresh all categories
            for category in imported_categories:
                await self.db.refresh(category)

            logger.info(f"Imported {len(imported_categories)} categories")
            return imported_categories

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to import categories: {e}")
            raise

    async def get_categories_with_pagination(
        self,
        page: int = 1,
        page_size: int = 20,
        parent_id: Optional[UUID] = None,
        include_strategy_count: bool = False
    ) -> Dict[str, Any]:
        """Get categories with pagination"""
        try:
            offset = (page - 1) * page_size

            # Build query
            query = select(StrategyCategory)
            conditions = []

            if parent_id:
                conditions.append(StrategyCategory.parent_id == parent_id)
            else:
                conditions.append(StrategyCategory.parent_id.is_(None))

            if conditions:
                query = query.where(and_(*conditions))

            # Get total count
            count_query = select(func.count(StrategyCategory.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))

            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Get categories
            query = query.order_by(StrategyCategory.sort_order, StrategyCategory.name)
            query = query.offset(offset).limit(page_size)

            result = await self.db.execute(query)
            categories = result.scalars().all()

            # Build response
            category_list = []
            for category in categories:
                category_data = {
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "parent_id": category.parent_id,
                    "icon": category.icon,
                    "sort_order": category.sort_order,
                    "is_active": category.is_active,
                    "created_at": category.created_at,
                    "updated_at": category.updated_at
                }

                if include_strategy_count:
                    # Count strategies
                    strategy_count = await self.db.execute(
                        select(func.count(Strategy.id))
                        .where(Strategy.category_id == category.id)
                    )
                    category_data["strategy_count"] = strategy_count.scalar()

                category_list.append(category_data)

            return {
                "categories": category_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }

        except Exception as e:
            logger.error(f"Failed to get paginated categories: {e}")
            raise

# Alias for backward compatibility
StrategyServiceV2 = StrategyService