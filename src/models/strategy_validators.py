"""
Strategy Validators
Data validation and business rules for strategy management
Phase 3.1 - 實現策略數據模型
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import re
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .strategy_models_v2 import (
    Strategy, StrategyVersion, StrategyInstance, Backtest,
    StrategyType, StrategyStatus, RiskLevel
)
from ..schemas.strategy_schemas import (
    StrategyCreate, StrategyUpdate, StrategyInstanceCreate,
    TimeFrame
)


class StrategyValidationError(Exception):
    """Strategy validation error"""
    pass


class StrategyValidator:
    """Strategy data validator with business rules"""

    def __init__(self, db: Session):
        self.db = db

    # Strategy validation
    def validate_strategy_create(self, strategy_data: StrategyCreate, author_id: UUID) -> None:
        """Validate strategy creation data"""
        self._validate_basic_strategy_fields(strategy_data)
        self._validate_strategy_type_config(strategy_data)
        self._validate_slug_uniqueness(strategy_data.slug)
        self._validate_user_limits(author_id)

    def validate_strategy_update(
        self,
        strategy: Strategy,
        update_data: StrategyUpdate,
        author_id: UUID
    ) -> None:
        """Validate strategy update data"""
        # Check ownership
        if strategy.author_id != author_id:
            raise StrategyValidationError("Only strategy author can update strategy")

        # Validate status transitions
        if 'status' in update_data:
            self._validate_status_transition(strategy.status, update_data.status)

        # Validate basic fields
        self._validate_basic_strategy_fields(update_data, is_update=True)

        # Check slug uniqueness if changing
        if 'slug' in update_data and update_data.slug != strategy.slug:
            self._validate_slug_uniqueness(update_data.slug)

        # Validate config if updating
        if 'config' in update_data or 'strategy_type' in update_data:
            new_type = update_data.get('strategy_type', strategy.strategy_type)
            new_config = update_data.get('config', strategy.config)
            temp_strategy = Strategy(strategy_type=new_type, config=new_config)
            self._validate_strategy_type_config_obj(temp_strategy)

    def validate_strategy_deletion(self, strategy: Strategy, user_id: UUID) -> None:
        """Validate strategy can be deleted"""
        # Check ownership
        if strategy.author_id != user_id:
            raise StrategyValidationError("Only strategy author can delete strategy")

        # Check if strategy has active instances
        active_instances = self.db.query(StrategyInstance).filter(
            StrategyInstance.strategy_id == strategy.id,
            StrategyInstance.status.in_(['running', 'paused'])
        ).count()

        if active_instances > 0:
            raise StrategyValidationError(
                f"Cannot delete strategy with {active_instances} active instances"
            )

        # Check if strategy is featured (only admin can delete featured)
        if strategy.featured:
            raise StrategyValidationError("Cannot delete featured strategy")

    def validate_strategy_publish(self, strategy: Strategy) -> None:
        """Validate strategy can be published"""
        if strategy.status != StrategyStatus.DRAFT:
            raise StrategyValidationError("Only draft strategies can be published")

        # Check required fields
        if not strategy.description:
            raise StrategyValidationError("Description is required for public strategies")

        if not strategy.config:
            raise StrategyValidationError("Configuration is required for public strategies")

        if not strategy.parameter_schema:
            raise StrategyValidationError("Parameter schema is required for public strategies")

        # Validate performance data exists
        if not strategy.sharpe_ratio or not strategy.max_drawdown:
            raise StrategyValidationError("Performance metrics required for public strategies")

        # Check if strategy has been backtested
        backtest_count = self.db.query(Backtest).filter(
            Backtest.strategy_id == strategy.id,
            Backtest.status == 'completed'
        ).count()

        if backtest_count == 0:
            raise StrategyValidationError("Strategy must have at least one completed backtest")

    # Strategy Instance validation
    def validate_instance_create(
        self,
        instance_data: StrategyInstanceCreate,
        user_id: UUID
    ) -> None:
        """Validate strategy instance creation"""
        # Get strategy
        strategy = self.db.query(Strategy).filter(
            Strategy.id == instance_data.strategy_id
        ).first()

        if not strategy:
            raise StrategyValidationError("Strategy not found")

        # Check if user has access to strategy
        if not strategy.is_public and strategy.author_id != user_id:
            raise StrategyValidationError("User does not have access to this strategy")

        # Validate capital allocation
        if instance_data.capital_allocation:
            if strategy.min_capital and instance_data.capital_allocation < strategy.min_capital:
                raise StrategyValidationError(
                    f"Capital allocation must be at least {strategy.min_capital}"
                )

            # Validate reasonable maximum
            if instance_data.capital_allocation > 100000000:  # 100M
                raise StrategyValidationError("Capital allocation too high")

        # Validate parameters against schema
        if instance_data.parameters and strategy.parameter_schema:
            self._validate_parameters_against_schema(
                instance_data.parameters,
                strategy.parameter_schema
            )

        # Validate symbols
        if instance_data.symbols:
            self._validate_trading_symbols(instance_data.symbols)

        # Validate user instance limits
        self._validate_user_instance_limits(user_id)

    def validate_instance_update(
        self,
        instance: StrategyInstance,
        update_data: Dict[str, Any],
        user_id: UUID
    ) -> None:
        """Validate strategy instance update"""
        # Check ownership
        if instance.user_id != user_id:
            raise StrategyValidationError("Only instance owner can update instance")

        # Can't update certain fields if instance is running
        if instance.status == 'running':
            restricted_fields = ['strategy_id', 'capital_allocation', 'parameters']
            for field in restricted_fields:
                if field in update_data:
                    raise StrategyValidationError(
                        f"Cannot update {field} while instance is running"
                    )

        # Validate capital allocation
        if 'capital_allocation' in update_data:
            strategy = self.db.query(Strategy).filter(
                Strategy.id == instance.strategy_id
            ).first()

            if strategy.min_capital and update_data['capital_allocation'] < strategy.min_capital:
                raise StrategyValidationError(
                    f"Capital allocation must be at least {strategy.min_capital}"
                )

    # Backtest validation
    def validate_backtest_create(self, backtest_data: Dict[str, Any], user_id: UUID) -> None:
        """Validate backtest creation"""
        # Get strategy
        strategy = self.db.query(Strategy).filter(
            Strategy.id == backtest_data.strategy_id
        ).first()

        if not strategy:
            raise StrategyValidationError("Strategy not found")

        # Check user access
        if not strategy.is_public and strategy.author_id != user_id:
            raise StrategyValidationError("User does not have access to this strategy")

        # Validate date range
        self._validate_backtest_date_range(backtest_data.start_date, backtest_data.end_date)

        # Validate symbols
        if backtest_data.symbols:
            self._validate_trading_symbols(backtest_data.symbols)

        # Validate parameters
        if backtest_data.parameters and strategy.parameter_schema:
            self._validate_parameters_against_schema(
                backtest_data.parameters,
                strategy.parameter_schema
            )

        # Check user's backtest limits
        self._validate_user_backtest_limits(user_id)

    def validate_backtest_date_range(self, start_date: date, end_date: date) -> None:
        """Validate backtest date range"""
        self._validate_backtest_date_range(start_date, end_date)

    # Helper validation methods
    def _validate_basic_strategy_fields(
        self,
        data: Union[StrategyCreate, StrategyUpdate],
        is_update: bool = False
    ) -> None:
        """Validate basic strategy fields"""
        # Validate name
        if hasattr(data, 'name') and data.name:
            if len(data.name.strip()) < 3:
                raise StrategyValidationError("Strategy name must be at least 3 characters")

        # Validate slug format
        if hasattr(data, 'slug') and data.slug:
            if not re.match(r'^[a-z0-9-]+$', data.slug):
                raise StrategyValidationError(
                    "Slug must contain only lowercase letters, numbers, and hyphens"
                )

        # Validate description length
        if hasattr(data, 'description') and data.description:
            if len(data.description) > 2000:
                raise StrategyValidationError("Description too long (max 2000 characters)")

        # Validate expected return range
        if hasattr(data, 'expected_return') and data.expected_return is not None:
            if not -100 <= data.expected_return <= 1000:
                raise StrategyValidationError("Expected return must be between -100% and 1000%")

        # Validate drawdown range
        if hasattr(data, 'max_drawdown') and data.max_drawdown is not None:
            if not 0 <= data.max_drawdown <= 100:
                raise StrategyValidationError("Max drawdown must be between 0% and 100%")

        # Validate Sharpe ratio range
        if hasattr(data, 'sharpe_ratio') and data.sharpe_ratio is not None:
            if not -10 <= data.sharpe_ratio <= 10:
                raise StrategyValidationError("Sharpe ratio must be between -10 and 10")

        # Validate win rate range
        if hasattr(data, 'win_rate') and data.win_rate is not None:
            if not 0 <= data.win_rate <= 100:
                raise StrategyValidationError("Win rate must be between 0% and 100%")

    def _validate_strategy_type_config(self, strategy_data: StrategyCreate) -> None:
        """Validate strategy type specific configuration"""
        temp_strategy = Strategy(
            strategy_type=strategy_data.strategy_type,
            config=strategy_data.config or {}
        )
        self._validate_strategy_type_config_obj(temp_strategy)

    def _validate_strategy_type_config_obj(self, strategy: Strategy) -> None:
        """Validate strategy configuration based on type"""
        config = strategy.config or {}

        if strategy.strategy_type == StrategyType.TECHNICAL:
            self._validate_technical_strategy_config(config)
        elif strategy.strategy_type == StrategyType.MOMENTUM:
            self._validate_momentum_strategy_config(config)
        elif strategy.strategy_type == StrategyType.VOLUME:
            self._validate_volume_strategy_config(config)
        elif strategy.strategy_type == StrategyType.PORTFOLIO:
            self._validate_portfolio_strategy_config(config)
        elif strategy.strategy_type == StrategyType.FUNDAMENTAL:
            self._validate_fundamental_strategy_config(config)

    def _validate_technical_strategy_config(self, config: Dict[str, Any]) -> None:
        """Validate technical indicator strategy configuration"""
        required_indicators = config.get('indicators', [])
        if not required_indicators:
            raise StrategyValidationError("Technical strategies must specify indicators")

        # Validate each indicator config
        for indicator in required_indicators:
            if not indicator.get('type'):
                raise StrategyValidationError("Indicator must specify type")

            if not indicator.get('parameters'):
                raise StrategyValidationError("Indicator must specify parameters")

    def _validate_momentum_strategy_config(self, config: Dict[str, Any]) -> None:
        """Validate momentum strategy configuration"""
        lookback_period = config.get('lookback_period')
        if lookback_period and not 1 <= lookback_period <= 500:
            raise StrategyValidationError("Lookback period must be between 1 and 500")

        momentum_threshold = config.get('momentum_threshold')
        if momentum_threshold and not -1 <= momentum_threshold <= 1:
            raise StrategyValidationError("Momentum threshold must be between -1 and 1")

    def _validate_volume_strategy_config(self, config: Dict[str, Any]) -> None:
        """Validate volume strategy configuration"""
        volume_ma_period = config.get('volume_ma_period')
        if volume_ma_period and not 5 <= volume_ma_period <= 200:
            raise StrategyValidationError("Volume MA period must be between 5 and 200")

        volume_multiplier = config.get('volume_multiplier')
        if volume_multiplier and not 0.5 <= volume_multiplier <= 5:
            raise StrategyValidationError("Volume multiplier must be between 0.5 and 5")

    def _validate_portfolio_strategy_config(self, config: Dict[str, Any]) -> None:
        """Validate portfolio strategy configuration"""
        rebalance_frequency = config.get('rebalance_frequency')
        valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
        if rebalance_frequency and rebalance_frequency not in valid_frequencies:
            raise StrategyValidationError(f"Rebalance frequency must be one of: {valid_frequencies}")

        assets = config.get('assets', [])
        if not assets:
            raise StrategyValidationError("Portfolio strategies must specify assets")

    def _validate_fundamental_strategy_config(self, config: Dict[str, Any]) -> None:
        """Validate fundamental strategy configuration"""
        economic_indicators = config.get('economic_indicators', [])
        if not economic_indicators:
            raise StrategyValidationError("Fundamental strategies must specify economic indicators")

    def _validate_slug_uniqueness(self, slug: str) -> None:
        """Validate strategy slug uniqueness"""
        existing = self.db.query(Strategy).filter(Strategy.slug == slug).first()
        if existing:
            raise StrategyValidationError(f"Strategy slug '{slug}' already exists")

    def _validate_status_transition(self, current_status: str, new_status: str) -> None:
        """Validate strategy status transitions"""
        valid_transitions = {
            StrategyStatus.DRAFT: [StrategyStatus.ACTIVE, StrategyStatus.TESTING, StrategyStatus.ARCHIVED],
            StrategyStatus.TESTING: [StrategyStatus.ACTIVE, StrategyStatus.DRAFT, StrategyStatus.ARCHIVED],
            StrategyStatus.ACTIVE: [StrategyStatus.INACTIVE, StrategyStatus.ARCHIVED],
            StrategyStatus.INACTIVE: [StrategyStatus.ACTIVE, StrategyStatus.ARCHIVED],
            StrategyStatus.ARCHIVED: [StrategyStatus.DRAFT, StrategyStatus.ACTIVE]
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise StrategyValidationError(
                f"Invalid status transition from {current_status} to {new_status}"
            )

    def _validate_user_limits(self, user_id: UUID) -> None:
        """Validate user strategy limits"""
        # Check user's strategy count
        strategy_count = self.db.query(Strategy).filter(
            Strategy.author_id == user_id
        ).count()

        # Example limit: 100 strategies per user
        if strategy_count >= 100:
            raise StrategyValidationError("User has reached maximum strategy limit")

    def _validate_user_instance_limits(self, user_id: UUID) -> None:
        """Validate user instance limits"""
        # Check user's instance count
        instance_count = self.db.query(StrategyInstance).filter(
            StrategyInstance.user_id == user_id
        ).count()

        # Example limit: 50 instances per user
        if instance_count >= 50:
            raise StrategyValidationError("User has reached maximum instance limit")

    def _validate_user_backtest_limits(self, user_id: UUID) -> None:
        """Validate user backtest limits"""
        # Check backtests in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        backtest_count = self.db.query(Backtest).filter(
            Backtest.user_id == user_id,
            Backtest.created_at >= yesterday
        ).count()

        # Example limit: 10 backtests per day
        if backtest_count >= 10:
            raise StrategyValidationError("User has reached daily backtest limit")

    def _validate_parameters_against_schema(
        self,
        parameters: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> None:
        """Validate parameters against JSON schema"""
        # This is a simplified validation
        # In production, use jsonschema library
        required_params = schema.get('required', [])
        param_properties = schema.get('properties', {})

        # Check required parameters
        for param in required_params:
            if param not in parameters:
                raise StrategyValidationError(f"Required parameter missing: {param}")

        # Check parameter types and constraints
        for param, value in parameters.items():
            if param in param_properties:
                param_schema = param_properties[param]
                param_type = param_schema.get('type')

                if param_type == 'number':
                    if not isinstance(value, (int, float)):
                        raise StrategyValidationError(f"Parameter {param} must be a number")

                    # Check constraints
                    minimum = param_schema.get('minimum')
                    maximum = param_schema.get('maximum')
                    if minimum is not None and value < minimum:
                        raise StrategyValidationError(f"Parameter {param} below minimum")
                    if maximum is not None and value > maximum:
                        raise StrategyValidationError(f"Parameter {param} above maximum")

                elif param_type == 'string':
                    if not isinstance(value, str):
                        raise StrategyValidationError(f"Parameter {param} must be a string")

                    # Check enum values
                    enum_values = param_schema.get('enum')
                    if enum_values and value not in enum_values:
                        raise StrategyValidationError(
                            f"Parameter {param} must be one of: {enum_values}"
                        )

                elif param_type == 'array':
                    if not isinstance(value, list):
                        raise StrategyValidationError(f"Parameter {param} must be an array")

    def _validate_trading_symbols(self, symbols: List[str]) -> None:
        """Validate trading symbols"""
        if len(symbols) > 100:
            raise StrategyValidationError("Too many symbols (max 100)")

        for symbol in symbols:
            if not re.match(r'^[A-Z0-9.-]+$', symbol):
                raise StrategyValidationError(f"Invalid symbol format: {symbol}")

    def _validate_backtest_date_range(self, start_date: date, end_date: date) -> None:
        """Validate backtest date range"""
        # Check range length (max 10 years)
        max_range = timedelta(days=365 * 10)
        if end_date - start_date > max_range:
            raise StrategyValidationError("Backtest range too long (max 10 years)")

        # Check minimum range (at least 1 month)
        min_range = timedelta(days=30)
        if end_date - start_date < min_range:
            raise StrategyValidationError("Backtest range too short (min 30 days)")

        # Check dates are not too far in the past
        earliest_date = date(2000, 1, 1)
        if start_date < earliest_date:
            raise StrategyValidationError("Start date too early (earliest: 2000-01-01)")

        # Check end date is not in future
        if end_date > date.today():
            raise StrategyValidationError("End date cannot be in the future")