"""
Strategy management service
策略管理服務
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, cast, Numeric
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..database.strategy_models import (
    Strategy, StrategyConfig, StrategyCategory, BacktestResult,
    PerformanceRecord, User
)
from ..models.strategy_models import (
    Strategy as StrategySchema, StrategyConfig as StrategyConfigSchema,
    BacktestResult as BacktestSchema, PerformanceRecord as PerformanceSchema,
    StrategyType, RiskTolerance, BacktestType,
    StrategyCreateRequest, StrategyUpdateRequest,
    StrategyConfigCreateRequest, StrategyConfigUpdateRequest,
    PaginatedResponse, StrategyResponse, StrategyConfigResponse
)

class StrategyService:
    """Strategy management service"""

    def __init__(self, db: Session):
        self.db = db

    # Strategy CRUD operations
    def create_strategy(self, request: StrategyCreateRequest) -> Strategy:
        """Create a new strategy"""
        try:
            strategy = Strategy(
                **request.strategy_data.dict()
            )
            self.db.add(strategy)
            self.db.commit()
            self.db.refresh(strategy)
            return strategy
        except IntegrityError as e:
            self.db.rollback()
            if "unique" in str(e).lower():
                raise ValueError("Strategy code must be unique")
            raise ValueError(f"Integrity error: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Database error: {str(e)}")

    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get strategy by ID"""
        try:
            return self.db.query(Strategy).filter(
                and_(Strategy.id == strategy_id, Strategy.is_deleted == False)
            ).first()
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    def get_strategy_by_code(self, code: str) -> Optional[Strategy]:
        """Get strategy by code"""
        try:
            return self.db.query(Strategy).filter(
                and_(Strategy.code == code, Strategy.is_deleted == False)
            ).first()
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    def list_strategies(
        self,
        user_id: Optional[str] = None,
        strategy_type: Optional[StrategyType] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None
    ) -> PaginatedResponse:
        """List strategies with pagination and filtering"""
        try:
            query = self.db.query(Strategy).filter(Strategy.is_deleted == False)

            # Apply filters
            if user_id:
                query = query.filter(Strategy.author_id == user_id)
            if strategy_type:
                query = query.filter(Strategy.strategy_type == strategy_type.value)
            if is_active is not None:
                query = query.filter(Strategy.is_active == is_active)
            if search:
                search_filter = or_(
                    Strategy.name.ilike(f"%{search}%"),
                    Strategy.code.ilike(f"%{search}%"),
                    Strategy.description.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            offset = (page - 1) * size
            strategies = query.order_by(Strategy.created_at.desc()).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=strategies,
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size,
                has_next=offset + size < total,
                has_prev=page > 1
            )
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    def update_strategy(self, strategy_id: str, request: StrategyUpdateRequest) -> Strategy:
        """Update strategy"""
        try:
            strategy = self.get_strategy(strategy_id)
            if not strategy:
                raise ValueError("Strategy not found")

            # Update only provided fields
            update_data = request.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(strategy, field):
                    setattr(strategy, field, value)

            strategy.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(strategy)
            return strategy
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Database error: {str(e)}")

    def delete_strategy(self, strategy_id: str, deleted_by: str) -> bool:
        """Soft delete strategy"""
        try:
            strategy = self.get_strategy(strategy_id)
            if not strategy:
                raise ValueError("Strategy not found")

            strategy.is_deleted = True
            strategy.deleted_at = datetime.utcnow()
            strategy.deleted_by = deleted_by
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Database error: {str(e)}")

    # Strategy Config CRUD operations
    def create_strategy_config(self, request: StrategyConfigCreateRequest, user_id: str) -> StrategyConfig:
        """Create strategy configuration"""
        try:
            # Validate strategy exists
            strategy = self.get_strategy(request.config_data.strategy_id)
            if not strategy:
                raise ValueError("Strategy not found")

            config_data = request.config_data.dict()
            config_data['user_id'] = user_id

            config = StrategyConfig(**config_data)
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            return config
        except IntegrityError as e:
            self.db.rollback()
            if "unique" in str(e).lower():
                raise ValueError("Configuration name must be unique for this strategy and user")
            raise ValueError(f"Integrity error: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Database error: {str(e)}")

    def get_strategy_config(self, config_id: str, user_id: str) -> Optional[StrategyConfig]:
        """Get strategy configuration by ID"""
        try:
            return self.db.query(StrategyConfig).filter(
                and_(
                    StrategyConfig.id == config_id,
                    StrategyConfig.user_id == user_id,
                    StrategyConfig.is_deleted == False
                )
            ).first()
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    def list_strategy_configs(
        self,
        user_id: str,
        strategy_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        risk_tolerance: Optional[RiskTolerance] = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """List strategy configurations"""
        try:
            query = self.db.query(StrategyConfig).filter(
                and_(StrategyConfig.user_id == user_id, StrategyConfig.is_deleted == False)
            )

            if strategy_id:
                query = query.filter(StrategyConfig.strategy_id == strategy_id)
            if is_active is not None:
                query = query.filter(StrategyConfig.is_active == is_active)
            if risk_tolerance:
                query = query.filter(StrategyConfig.risk_tolerance == risk_tolerance.value)

            total = query.count()
            offset = (page - 1) * size
            configs = query.order_by(StrategyConfig.created_at.desc()).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=configs,
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size,
                has_next=offset + size < total,
                has_prev=page > 1
            )
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    def update_strategy_config(self, config_id: str, request: StrategyConfigUpdateRequest, user_id: str) -> StrategyConfig:
        """Update strategy configuration"""
        try:
            config = self.get_strategy_config(config_id, user_id)
            if not config:
                raise ValueError("Configuration not found")

            update_data = request.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(config, field):
                    setattr(config, field, value)

            config.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(config)
            return config
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Database error: {str(e)}")

    def delete_strategy_config(self, config_id: str, user_id: str) -> bool:
        """Soft delete strategy configuration"""
        try:
            config = self.get_strategy_config(config_id, user_id)
            if not config:
                raise ValueError("Configuration not found")

            config.is_deleted = True
            config.deleted_at = datetime.utcnow()
            config.deleted_by = user_id
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Database error: {str(e)}")

    # Backtest operations
    def create_backtest_result(self, request: Dict[str, Any], user_id: str) -> BacktestResult:
        """Create backtest result"""
        try:
            backtest_data = request.copy()
            backtest_data['user_id'] = user_id

            backtest = BacktestResult(**backtest_data)
            self.db.add(backtest)
            self.db.commit()
            self.db.refresh(backtest)
            return backtest
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Database error: {str(e)}")

    def get_backtest_result(self, backtest_id: str, user_id: str) -> Optional[BacktestResult]:
        """Get backtest result by ID"""
        try:
            return self.db.query(BacktestResult).filter(
                and_(
                    BacktestResult.id == backtest_id,
                    BacktestResult.user_id == user_id,
                    BacktestResult.is_deleted == False
                )
            ).first()
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    def list_backtest_results(
        self,
        user_id: str,
        strategy_id: Optional[str] = None,
        backtest_type: Optional[BacktestType] = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """List backtest results"""
        try:
            query = self.db.query(BacktestResult).filter(
                and_(BacktestResult.user_id == user_id, BacktestResult.is_deleted == False)
            )

            if strategy_id:
                query = query.filter(BacktestResult.strategy_id == strategy_id)
            if backtest_type:
                query = query.filter(BacktestResult.backtest_type == backtest_type.value)

            total = query.count()
            offset = (page - 1) * size
            results = query.order_by(BacktestResult.created_at.desc()).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=results,
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size,
                has_next=offset + size < total,
                has_prev=page > 1
            )
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    # Performance records operations
    def create_performance_record(self, record_data: Dict[str, Any]) -> PerformanceRecord:
        """Create performance record"""
        try:
            record = PerformanceRecord(**record_data)
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Database error: {str(e)}")

    def get_latest_performance_record(self, strategy_id: str, user_id: str) -> Optional[PerformanceRecord]:
        """Get latest performance record for strategy"""
        try:
            return self.db.query(PerformanceRecord).filter(
                and_(
                    PerformanceRecord.strategy_id == strategy_id,
                    PerformanceRecord.user_id == user_id,
                    PerformanceRecord.is_deleted == False
                )
            ).order_by(PerformanceRecord.record_time.desc()).first()
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    def get_performance_history(
        self,
        strategy_id: str,
        user_id: str,
        start_date: date,
        end_date: date,
        page: int = 1,
        size: int = 100
    ) -> PaginatedResponse:
        """Get performance history for date range"""
        try:
            query = self.db.query(PerformanceRecord).filter(
                and_(
                    PerformanceRecord.strategy_id == strategy_id,
                    PerformanceRecord.user_id == user_id,
                    PerformanceRecord.record_date >= start_date,
                    PerformanceRecord.record_date <= end_date,
                    PerformanceRecord.is_deleted == False
                )
            )

            total = query.count()
            offset = (page - 1) * size
            records = query.order_by(PerformanceRecord.record_time.asc()).offset(offset).limit(size).all()

            return PaginatedResponse(
                items=records,
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size,
                has_next=offset + size < total,
                has_prev=page > 1
            )
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    # Analytics operations
    def get_strategy_summary(self, strategy_id: str, user_id: str) -> Dict[str, Any]:
        """Get strategy summary with latest performance"""
        try:
            strategy = self.get_strategy(strategy_id)
            if not strategy:
                raise ValueError("Strategy not found")

            # Get latest config
            config = self.db.query(StrategyConfig).filter(
                and_(
                    StrategyConfig.strategy_id == strategy_id,
                    StrategyConfig.user_id == user_id,
                    StrategyConfig.is_active == True,
                    StrategyConfig.is_deleted == False
                )
            ).first()

            # Get latest performance record
            latest_record = self.get_latest_performance_record(strategy_id, user_id)

            # Get latest backtest result
            latest_backtest = self.db.query(BacktestResult).filter(
                and_(
                    BacktestResult.strategy_id == strategy_id,
                    BacktestResult.user_id == user_id,
                    BacktestResult.is_deleted == False
                )
            ).order_by(BacktestResult.created_at.desc()).first()

            # Get total backtests count
            total_backtests = self.db.query(BacktestResult).filter(
                and_(
                    BacktestResult.strategy_id == strategy_id,
                    BacktestResult.user_id == user_id,
                    BacktestResult.is_deleted == False
                )
            ).count()

            return {
                "strategy": strategy,
                "latest_config": config,
                "latest_performance": latest_record,
                "latest_backtest": latest_backtest,
                "total_backtests": total_backtests
            }
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    def get_strategy_performance_metrics(self, strategy_id: str, user_id: str) -> Dict[str, Any]:
        """Calculate performance metrics for strategy"""
        try:
            strategy = self.get_strategy(strategy_id)
            if not strategy:
                raise ValueError("Strategy not found")

            # Get performance records for calculation
            records = self.db.query(PerformanceRecord).filter(
                and_(
                    PerformanceRecord.strategy_id == strategy_id,
                    PerformanceRecord.user_id == user_id,
                    PerformanceRecord.is_deleted == False
                )
            ).order_by(PerformanceRecord.record_time.asc()).all()

            if not records:
                return {
                    "strategy_id": strategy_id,
                    "strategy_name": strategy.name,
                    "metrics": {}
                }

            # Calculate metrics
            first_record = records[0]
            latest_record = records[-1]

            total_return = latest_record.cumulative_return_pct
            current_value = latest_record.portfolio_value

            # Calculate annualized return
            days_diff = (latest_record.record_date - first_record.record_date).days
            annualized_return = None
            if days_diff > 0:
                annualized_return = float((1 + total_return) ** (365.25 / days_diff) - 1)

            # Get max drawdown from records
            max_drawdown = min(r.running_max_drawdown for r in records)

            # Calculate Sharpe ratio if we have enough data
            sharpe_ratio = None
            if len(records) > 30:  # At least 30 days
                returns = [r.daily_return_pct for r in records]
                if returns:
                    import numpy as np
                    avg_return = np.mean(returns) * 252  # Annualized
                    std_return = np.std(returns) * np.sqrt(252)  # Annualized
                    if std_return > 0:
                        sharpe_ratio = avg_return / std_return

            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "metrics": {
                    "current_value": float(current_value),
                    "total_return": float(total_return),
                    "annualized_return": annualized_return,
                    "max_drawdown": float(max_drawdown),
                    "sharpe_ratio": sharpe_ratio,
                    "volatility": float(latest_record.running_volatility) if latest_record.running_volatility else None,
                    "record_count": len(records),
                    "period_days": days_diff,
                    "last_updated": latest_record.record_time
                }
            }
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    # Strategy Categories
    def list_strategy_categories(self, is_active: bool = True) -> List[StrategyCategory]:
        """List strategy categories"""
        try:
            return self.db.query(StrategyCategory).filter(
                StrategyCategory.is_active == is_active
            ).order_by(StrategyCategory.level, StrategyCategory.name).all()
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")

    def get_strategy_category_by_name(self, name: str) -> Optional[StrategyCategory]:
        """Get strategy category by name"""
        try:
            return self.db.query(StrategyCategory).filter(
                and_(StrategyCategory.name == name, StrategyCategory.is_active == True)
            ).first()
        except SQLAlchemyError as e:
            raise ValueError(f"Database error: {str(e)}")