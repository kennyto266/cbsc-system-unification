"""
Legacy Strategy Adapter
Adapts existing strategy implementations to new architecture
Phase 4.1 - 重構現有策略類型
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from ..strategy_factory_v2 import BaseStrategy, TechnicalStrategy, MomentumStrategy, VolumeStrategy
from ..base import BaseSignal

logger = logging.getLogger(__name__)


class LegacyStrategyAdapter:
    """Adapter to bridge old strategy implementations with new architecture"""

    @staticmethod
    def adapt_ma_crossover(config: Dict[str, Any]) -> TechnicalStrategy:
        """Adapt MA Crossover strategy to new architecture"""
        # Extract parameters from old config
        parameters = config.get('parameters', {})

        # Convert to new config format
        new_config = {
            'indicators': [
                {
                    'type': 'ma',
                    'parameters': {
                        'period': parameters.get('fast_period', 10),
                        'ma_type': parameters.get('ma_type', 'sma')
                    }
                },
                {
                    'type': 'ma',
                    'parameters': {
                        'period': parameters.get('slow_period', 30),
                        'ma_type': parameters.get('ma_type', 'sma')
                    }
                }
            ],
            'signal_rules': [
                {
                    'condition': 'ma_crossover',
                    'fast_ma': 0,  # Index of fast MA in indicators list
                    'slow_ma': 1,  # Index of slow MA in indicators list
                    'threshold': parameters.get('signal_threshold', 0.001)
                }
            ]
        }

        # Create new strategy instance
        strategy = TechnicalStrategy(new_config)

        # Set parameters
        strategy.set_parameters({
            'ma_period_1': parameters.get('fast_period', 10),
            'ma_type_1': parameters.get('ma_type', 'sma'),
            'ma_period_2': parameters.get('slow_period', 30),
            'ma_type_2': parameters.get('ma_type', 'sma'),
            'signal_threshold': parameters.get('signal_threshold', 0.001)
        })

        return strategy

    @staticmethod
    def adapt_rsi_strategy(config: Dict[str, Any]) -> TechnicalStrategy:
        """Adapt RSI strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'indicators': [
                {
                    'type': 'rsi',
                    'parameters': {
                        'period': parameters.get('period', 14),
                        'overbought': parameters.get('overbought_threshold', 70),
                        'oversold': parameters.get('oversold_threshold', 30)
                    }
                }
            ],
            'signal_rules': [
                {
                    'condition': 'rsi_extremes',
                    'overbought': parameters.get('overbought_threshold', 70),
                    'oversold': parameters.get('oversold_threshold', 30)
                }
            ]
        }

        strategy = TechnicalStrategy(new_config)

        strategy.set_parameters({
            'rsi_period': parameters.get('period', 14),
            'rsi_overbought': parameters.get('overbought_threshold', 70),
            'rsi_oversold': parameters.get('oversold_threshold', 30)
        })

        return strategy

    @staticmethod
    def adapt_macd_strategy(config: Dict[str, Any]) -> TechnicalStrategy:
        """Adapt MACD strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'indicators': [
                {
                    'type': 'macd',
                    'parameters': {
                        'fast': parameters.get('fast_period', 12),
                        'slow': parameters.get('slow_period', 26),
                        'signal': parameters.get('signal_period', 9)
                    }
                }
            ],
            'signal_rules': [
                {
                    'condition': 'macd_crossover',
                    'signal_line': True  # Use signal line crossover
                }
            ]
        }

        strategy = TechnicalStrategy(new_config)

        strategy.set_parameters({
            'macd_fast': parameters.get('fast_period', 12),
            'macd_slow': parameters.get('slow_period', 26),
            'macd_signal': parameters.get('signal_period', 9)
        })

        return strategy

    @staticmethod
    def adapt_bollinger_bands_strategy(config: Dict[str, Any]) -> TechnicalStrategy:
        """Adapt Bollinger Bands strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'indicators': [
                {
                    'type': 'bb',
                    'parameters': {
                        'period': parameters.get('period', 20),
                        'std_dev': parameters.get('std_dev', 2.0)
                    }
                }
            ],
            'signal_rules': [
                {
                    'condition': 'bb_squeeze',
                    'threshold': parameters.get('squeeze_threshold', 0.1)
                },
                {
                    'condition': 'bb_breakout',
                    'confirmation_periods': parameters.get('confirmation_periods', 2)
                }
            ]
        }

        strategy = TechnicalStrategy(new_config)

        strategy.set_parameters({
            'bb_period': parameters.get('period', 20),
            'bb_std_dev': parameters.get('std_dev', 2.0),
            'bb_squeeze_threshold': parameters.get('squeeze_threshold', 0.1)
        })

        return strategy

    @staticmethod
    def adapt_adx_strategy(config: Dict[str, Any]) -> MomentumStrategy:
        """Adapt ADX strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'adx_period': parameters.get('period', 14),
            'trend_threshold': parameters.get('trend_threshold', 25),
            'use_di_crossover': True,
            'momentum_calculation': 'price_based'
        }

        strategy = MomentumStrategy(new_config)

        strategy.set_parameters({
            'lookback_period': parameters.get('period', 14),
            'momentum_threshold': parameters.get('trend_threshold', 25) / 100,
            'adx_trend_threshold': parameters.get('trend_threshold', 25)
        })

        return strategy

    @staticmethod
    def adapt_sar_strategy(config: Dict[str, Any]) -> MomentumStrategy:
        """Adapt Parabolic SAR strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'sar_acceleration': parameters.get('acceleration', 0.02),
            'sar_maximum': parameters.get('maximum', 0.2),
            'momentum_type': 'sar_based'
        }

        strategy = MomentumStrategy(new_config)

        strategy.set_parameters({
            'lookback_period': 1,  # SAR is self-contained
            'momentum_threshold': 0,
            'sar_acceleration': parameters.get('acceleration', 0.02),
            'sar_maximum': parameters.get('maximum', 0.2)
        })

        return strategy

    @staticmethod
    def adapt_aroon_strategy(config: Dict[str, Any]) -> MomentumStrategy:
        """Adapt Aroon strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'aroon_period': parameters.get('period', 25),
            'trend_threshold': parameters.get('trend_threshold', 70),
            'oscillator_mode': True
        }

        strategy = MomentumStrategy(new_config)

        strategy.set_parameters({
            'lookback_period': parameters.get('period', 25),
            'momentum_threshold': parameters.get('trend_threshold', 70) / 100,
            'aroon_period': parameters.get('period', 25)
        })

        return strategy

    @staticmethod
    def adapt_vpt_strategy(config: Dict[str, Any]) -> VolumeStrategy:
        """Adapt Volume Price Trend strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'volume_ma_period': parameters.get('volume_ma_period', 20),
            'price_change_threshold': parameters.get('price_change_threshold', 0.01),
            'volume_confirmation': True
        }

        strategy = VolumeStrategy(new_config)

        strategy.set_parameters({
            'volume_ma_period': parameters.get('volume_ma_period', 20),
            'volume_multiplier': parameters.get('volume_multiplier', 1.2),
            'vpt_price_threshold': parameters.get('price_change_threshold', 0.01)
        })

        return strategy

    @staticmethod
    def adapt_obv_strategy(config: Dict[str, Any]) -> VolumeStrategy:
        """Adapt On-Balance Volume strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'obv_ma_period': parameters.get('ma_period', 10),
            'divergence_detection': True,
            'trend_confirmation': True
        }

        strategy = VolumeStrategy(new_config)

        strategy.set_parameters({
            'volume_ma_period': parameters.get('ma_period', 10),
            'volume_multiplier': parameters.get('signal_threshold', 1.0),
            'obv_ma_period': parameters.get('ma_period', 10)
        })

        return strategy

    @staticmethod
    def adapt_vwap_strategy(config: Dict[str, Any]) -> VolumeStrategy:
        """Adapt VWAP strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'vwap_period': parameters.get('period', 'daily'),  # daily, weekly, monthly
            'std_dev_bands': parameters.get('std_dev_bands', 2),
            'band_trading': True
        }

        strategy = VolumeStrategy(new_config)

        strategy.set_parameters({
            'volume_ma_period': 20,  # Default for general volume analysis
            'volume_multiplier': parameters.get('deviation_threshold', 1.0),
            'vwap_period': parameters.get('period', 'daily'),
            'vwap_std_dev': parameters.get('std_dev_bands', 2)
        })

        return strategy

    @staticmethod
    def adapt_mfi_strategy(config: Dict[str, Any]) -> VolumeStrategy:
        """Adapt Money Flow Index strategy to new architecture"""
        parameters = config.get('parameters', {})

        new_config = {
            'mfi_period': parameters.get('period', 14),
            'overbought': parameters.get('overbought', 80),
            'oversold': parameters.get('oversold', 20),
            'volume_weighted': True
        }

        strategy = VolumeStrategy(new_config)

        strategy.set_parameters({
            'volume_ma_period': parameters.get('period', 14),
            'volume_multiplier': 1.0,
            'mfi_period': parameters.get('period', 14),
            'mfi_overbought': parameters.get('overbought', 80),
            'mfi_oversold': parameters.get('oversold', 20)
        })

        return strategy

    @staticmethod
    def migrate_strategy_config(
        old_strategy_type: str,
        old_config: Dict[str, Any]
    ) -> BaseStrategy:
        """
        Migrate old strategy configuration to new architecture

        Args:
            old_strategy_type: Type of old strategy (e.g., 'ma_crossover', 'rsi')
            old_config: Old configuration dictionary

        Returns:
            New strategy instance
        """
        migration_map = {
            'ma_crossover': LegacyStrategyAdapter.adapt_ma_crossover,
            'rsi': LegacyStrategyAdapter.adapt_rsi_strategy,
            'macd': LegacyStrategyAdapter.adapt_macd_strategy,
            'bollinger_bands': LegacyStrategyAdapter.adapt_bollinger_bands_strategy,
            'adx': LegacyStrategyAdapter.adapt_adx_strategy,
            'sar': LegacyStrategyAdapter.adapt_sar_strategy,
            'aroon': LegacyStrategyAdapter.adapt_aroon_strategy,
            'vpt': LegacyStrategyAdapter.adapt_vpt_strategy,
            'obv': LegacyStrategyAdapter.adapt_obv_strategy,
            'vwap': LegacyStrategyAdapter.adapt_vwap_strategy,
            'mfi': LegacyStrategyAdapter.adapt_mfi_strategy,
        }

        if old_strategy_type not in migration_map:
            raise ValueError(f"Unknown strategy type: {old_strategy_type}")

        adapter_func = migration_map[old_strategy_type]
        new_strategy = adapter_func(old_config)

        logger.info(f"Migrated strategy {old_strategy_type} to new architecture")
        return new_strategy


class StrategyMigrationService:
    """Service for migrating existing strategies to new architecture"""

    def __init__(self, db_session):
        self.db = db_session

    def migrate_all_strategies(self) -> Dict[str, Any]:
        """Migrate all existing strategies to new architecture"""
        migration_results = {
            'total': 0,
            'migrated': 0,
            'failed': 0,
            'errors': []
        }

        try:
            # Get all strategies from old system
            from ...models.database import Strategy as OldStrategy
            old_strategies = self.db.query(OldStrategy).all()

            migration_results['total'] = len(old_strategies)

            for old_strategy in old_strategies:
                try:
                    # Migrate to new architecture
                    new_strategy = self.migrate_individual_strategy(old_strategy)
                    if new_strategy:
                        migration_results['migrated'] += 1
                        logger.info(f"Migrated strategy: {old_strategy.name}")
                except Exception as e:
                    migration_results['failed'] += 1
                    migration_results['errors'].append({
                        'strategy': old_strategy.name,
                        'error': str(e)
                    })
                    logger.error(f"Failed to migrate strategy {old_strategy.name}: {e}")

        except Exception as e:
            logger.error(f"Strategy migration failed: {e}")
            migration_results['errors'].append({
                'strategy': 'global',
                'error': str(e)
            })

        return migration_results

    def migrate_individual_strategy(self, old_strategy) -> Optional[BaseStrategy]:
        """Migrate individual strategy"""
        try:
            # Parse old configuration
            old_config = old_strategy.config or {}

            # Determine strategy type from old strategy
            old_type = self.determine_strategy_type(old_strategy)

            # Migrate to new architecture
            new_strategy = LegacyStrategyAdapter.migrate_strategy_config(
                old_type,
                old_config
            )

            # Save new strategy configuration
            self.save_new_strategy(old_strategy, new_strategy, old_type)

            return new_strategy

        except Exception as e:
            logger.error(f"Failed to migrate strategy {old_strategy.name}: {e}")
            return None

    def determine_strategy_type(self, old_strategy) -> str:
        """Determine strategy type from old strategy"""
        # Try to determine from strategy name or config
        name_lower = old_strategy.name.lower()

        if 'ma' in name_lower or 'moving average' in name_lower:
            return 'ma_crossover'
        elif 'rsi' in name_lower:
            return 'rsi'
        elif 'macd' in name_lower:
            return 'macd'
        elif 'bollinger' in name_lower or 'bb' in name_lower:
            return 'bollinger_bands'
        elif 'adx' in name_lower:
            return 'adx'
        elif 'sar' in name_lower:
            return 'sar'
        elif 'aroon' in name_lower:
            return 'aroon'
        elif 'vpt' in name_lower or 'volume price' in name_lower:
            return 'vpt'
        elif 'obv' in name_lower:
            return 'obv'
        elif 'vwap' in name_lower:
            return 'vwap'
        elif 'mfi' in name_lower:
            return 'mfi'
        else:
            # Default to MA crossover
            return 'ma_crossover'

    def save_new_strategy(self, old_strategy, new_strategy, strategy_type: str):
        """Save new strategy to database"""
        try:
            from ...models.strategy_models_v2 import (
                Strategy as NewStrategy, StrategyType
            )

            # Map old types to new types
            type_mapping = {
                'ma_crossover': StrategyType.TECHNICAL,
                'rsi': StrategyType.TECHNICAL,
                'macd': StrategyType.TECHNICAL,
                'bollinger_bands': StrategyType.TECHNICAL,
                'adx': StrategyType.MOMENTUM,
                'sar': StrategyType.MOMENTUM,
                'aroon': StrategyType.MOMENTUM,
                'vpt': StrategyType.VOLUME,
                'obv': StrategyType.VOLUME,
                'vwap': StrategyType.VOLUME,
                'mfi': StrategyType.VOLUME,
            }

            # Create new strategy record
            new_strategy_record = NewStrategy(
                name=old_strategy.name,
                slug=self.create_slug(old_strategy.name),
                description=old_strategy.description,
                strategy_type=type_mapping.get(strategy_type, StrategyType.TECHNICAL),
                config=new_strategy.config,
                default_parameters=new_strategy.get_default_parameters(),
                parameter_schema=new_strategy.get_parameter_schema(),
                author_id=old_strategy.user_id,
                status='active' if old_strategy.is_active else 'inactive',
                created_at=old_strategy.created_at,
                updated_at=datetime.utcnow()
            )

            self.db.add(new_strategy_record)
            self.db.commit()

            logger.info(f"Saved new strategy: {new_strategy_record.name}")

        except Exception as e:
            self.db.rollback()
            raise e

    def create_slug(self, name: str) -> str:
        """Create URL-friendly slug from name"""
        import re
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower())
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug