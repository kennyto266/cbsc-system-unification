"""
Risk Management Service v2.0
Integrates real-time risk monitoring with new architecture
Phase 5.1 - 實施回測引擎集成
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, UUID
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database import get_db
from ..models.strategy_models import Strategy, StrategyInstance
from ..risk_monitor.risk_engine import RiskEngine
from ..risk_monitor.config import RiskConfig
from ..risk_monitor.influxdb_connector import InfluxDBConnector
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class RiskManagementServiceV2:
    """Enhanced risk management service integrated with real-time monitoring"""

    def __init__(self, db: Session):
        """Initialize risk management service"""
        self.db = db
        self.risk_engines: Dict[str, RiskEngine] = {}
        self.cache_service = CacheService()

        # Initialize default configuration
        self.default_config = RiskConfig(
            calculation_interval=30,  # 30 seconds
            var_confidence_levels=[0.95, 0.99],
            es_confidence_levels=[0.95, 0.99],
            volatility_windows=[10, 20, 30],
            max_drawdown_window=252,  # 1 year
            volatility_target=0.15,  # 15% annual volatility
            rebalance_threshold=0.05,  # 5% deviation
            alert_enabled=True,
            dynamic_adjustment_enabled=True,
            influxdb_host="localhost",
            influxdb_port=8086,
            influxdb_database="risk_metrics",
            websocket_host="0.0.0.0",
            websocket_port=8765,
            websocket_max_connections=100
        )

    async def initialize_risk_monitoring(
        self,
        strategy_instance_id: UUID,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize real-time risk monitoring for a strategy instance

        Args:
            strategy_instance_id: Strategy instance to monitor
            config: Optional risk configuration overrides

        Returns:
            Initialization status and configuration
        """
        try:
            # Get strategy instance
            instance = self.db.query(StrategyInstance).filter(
                StrategyInstance.id == strategy_instance_id
            ).first()

            if not instance:
                raise ValueError(f"Strategy instance {strategy_instance_id} not found")

            # Create risk configuration
            risk_config = self._create_risk_config(config)

            # Initialize risk engine
            risk_engine = RiskEngine(risk_config)

            # Add portfolio to monitoring
            portfolio_info = {
                "strategy_instance_id": str(strategy_instance_id),
                "strategy_id": str(instance.strategy_id),
                "user_id": str(instance.user_id),
                "initial_capital": float(instance.parameters.get("initial_capital", 100000)),
                "positions": {},  # Will be updated from execution data
                "last_update": datetime.utcnow()
            }

            risk_engine.add_portfolio(str(strategy_instance_id), portfolio_info)

            # Store engine
            self.risk_engines[str(strategy_instance_id)] = risk_engine

            # Start monitoring
            monitor_task = await risk_engine.start()

            # Cache initialization status
            await self.cache_service.set(
                f"risk_monitor:{strategy_instance_id}",
                {
                    "status": "active",
                    "initialized_at": datetime.utcnow().isoformat(),
                    "config": risk_config.__dict__
                },
                ttl=3600
            )

            logger.info(f"Risk monitoring initialized for instance {strategy_instance_id}")

            return {
                "status": "success",
                "instance_id": str(strategy_instance_id),
                "monitoring_active": True,
                "config": risk_config.__dict__
            }

        except Exception as e:
            logger.error(f"Failed to initialize risk monitoring: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def stop_risk_monitoring(
        self,
        strategy_instance_id: UUID
    ) -> Dict[str, Any]:
        """
        Stop real-time risk monitoring for a strategy instance

        Args:
            strategy_instance_id: Strategy instance to stop monitoring

        Returns:
            Stop status
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.risk_engines:
                return {
                    "status": "warning",
                    "message": "Risk monitoring not active for this instance",
                    "instance_id": instance_key
                }

            # Stop risk engine
            risk_engine = self.risk_engines[instance_key]
            await risk_engine.stop()

            # Remove from monitoring
            risk_engine.remove_portfolio(instance_key)
            del self.risk_engines[instance_key]

            # Clear cache
            await self.cache_service.delete(f"risk_monitor:{strategy_instance_id}")

            logger.info(f"Risk monitoring stopped for instance {strategy_instance_id}")

            return {
                "status": "success",
                "instance_id": instance_key,
                "monitoring_active": False
            }

        except Exception as e:
            logger.error(f"Failed to stop risk monitoring: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def get_real_time_risk_metrics(
        self,
        strategy_instance_id: UUID,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get real-time risk metrics for a strategy instance

        Args:
            strategy_instance_id: Strategy instance
            force_refresh: Force recalculation of metrics

        Returns:
            Current risk metrics
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.risk_engines:
                return {
                    "status": "error",
                    "message": "Risk monitoring not active for this instance",
                    "instance_id": instance_key
                }

            risk_engine = self.risk_engines[instance_key]

            # Get current metrics
            metrics = risk_engine.get_portfolio_risk_metrics(instance_key)

            if not metrics or force_refresh:
                # Force refresh calculation
                metrics = await risk_engine.run_risk_calculation(
                    instance_key,
                    force_refresh=True
                )

            # Get additional context
            summary = risk_engine.get_risk_summary()
            active_alerts = risk_engine.alert_system.get_active_alerts()

            return {
                "status": "success",
                "instance_id": instance_key,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics or {},
                "active_alerts": [alert.to_dict() for alert in active_alerts],
                "monitoring_summary": summary
            }

        except Exception as e:
            logger.error(f"Failed to get risk metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def update_portfolio_positions(
        self,
        strategy_instance_id: UUID,
        positions: Dict[str, Dict[str, Any]],
        total_value: float
    ) -> Dict[str, Any]:
        """
        Update portfolio positions for risk monitoring

        Args:
            strategy_instance_id: Strategy instance
            positions: Current positions {symbol: {quantity, avg_price, market_value}}
            total_value: Total portfolio value

        Returns:
            Update status
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.risk_engines:
                return {
                    "status": "error",
                    "message": "Risk monitoring not active for this instance",
                    "instance_id": instance_key
                }

            risk_engine = self.risk_engines[instance_key]

            # Update portfolio info
            portfolio_info = risk_engine.portfolios.get(instance_key, {})
            portfolio_info.update({
                "positions": positions,
                "total_value": total_value,
                "last_update": datetime.utcnow()
            })

            # Store updated portfolio data to InfluxDB for historical tracking
            if risk_engine.influxdb:
                timestamp = datetime.utcnow()

                # Write position data
                for symbol, position in positions.items():
                    risk_engine.influxdb.write_position_data(
                        strategy_instance_id=instance_key,
                        symbol=symbol,
                        timestamp=timestamp,
                        quantity=position.get("quantity", 0),
                        price=position.get("market_price", 0),
                        value=position.get("market_value", 0)
                    )

                # Write portfolio value
                risk_engine.influxdb.write_portfolio_value(
                    strategy_instance_id=instance_key,
                    timestamp=timestamp,
                    total_value=total_value,
                    positions_value=sum(p.get("market_value", 0) for p in positions.values()),
                    cash=total_value - sum(p.get("market_value", 0) for p in positions.values())
                )

            return {
                "status": "success",
                "instance_id": instance_key,
                "updated_positions": len(positions),
                "total_value": total_value
            }

        except Exception as e:
            logger.error(f"Failed to update portfolio positions: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def configure_risk_alerts(
        self,
        strategy_instance_id: UUID,
        alert_config: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Configure risk alerts for a strategy instance

        Args:
            strategy_instance_id: Strategy instance
            alert_config: Alert configuration {name: {type, thresholds, ...}}

        Returns:
            Configuration status
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.risk_engines:
                return {
                    "status": "error",
                    "message": "Risk monitoring not active for this instance",
                    "instance_id": instance_key
                }

            risk_engine = self.risk_engines[instance_key]

            # Configure alert thresholds
            risk_engine.configure_alert_thresholds(alert_config)

            # Cache configuration
            await self.cache_service.set(
                f"risk_alerts:{strategy_instance_id}",
                {
                    "config": alert_config,
                    "updated_at": datetime.utcnow().isoformat()
                },
                ttl=3600
            )

            return {
                "status": "success",
                "instance_id": instance_key,
                "configured_alerts": len(alert_config)
            }

        except Exception as e:
            logger.error(f"Failed to configure risk alerts: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def get_risk_report(
        self,
        strategy_instance_id: UUID,
        hours: int = 24,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate risk report for a strategy instance

        Args:
            strategy_instance_id: Strategy instance
            hours: Number of hours of historical data
            format: Report format (json, csv)

        Returns:
            Risk report
        """
        try:
            instance_key = str(strategy_instance_id)

            if instance_key not in self.risk_engines:
                return {
                    "status": "error",
                    "message": "Risk monitoring not active for this instance",
                    "instance_id": instance_key
                }

            risk_engine = self.risk_engines[instance_key]

            # Export report
            report_data = risk_engine.export_risk_report(
                instance_key,
                format=format,
                hours=hours
            )

            return {
                "status": "success",
                "instance_id": instance_key,
                "format": format,
                "period_hours": hours,
                "generated_at": datetime.utcnow().isoformat(),
                "report": report_data
            }

        except Exception as e:
            logger.error(f"Failed to generate risk report: {e}")
            return {
                "status": "error",
                "error": str(e),
                "instance_id": str(strategy_instance_id)
            }

    async def get_monitoring_status(
        self,
        strategy_instance_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get monitoring status for one or all strategy instances

        Args:
            strategy_instance_id: Specific instance (optional)

        Returns:
            Monitoring status
        """
        try:
            if strategy_instance_id:
                # Get status for specific instance
                instance_key = str(strategy_instance_id)
                if instance_key in self.risk_engines:
                    risk_engine = self.risk_engines[instance_key]
                    return {
                        "status": "success",
                        "instance_id": instance_key,
                        "monitoring_active": True,
                        "summary": risk_engine.get_risk_summary(),
                        "last_update": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "inactive",
                        "instance_id": instance_key,
                        "monitoring_active": False
                    }
            else:
                # Get status for all instances
                active_instances = []
                for instance_key, risk_engine in self.risk_engines.items():
                    summary = risk_engine.get_risk_summary()
                    active_instances.append({
                        "instance_id": instance_key,
                        "summary": summary
                    })

                return {
                    "status": "success",
                    "total_active": len(self.risk_engines),
                    "instances": active_instances,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get monitoring status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _create_risk_config(self, config_overrides: Optional[Dict[str, Any]]) -> RiskConfig:
        """Create risk configuration with overrides"""
        config_dict = self.default_config.__dict__.copy()

        if config_overrides:
            config_dict.update(config_overrides)

        return RiskConfig(**config_dict)

    async def cleanup_instance_data(self, strategy_instance_id: UUID):
        """Clean up data for a strategy instance"""
        try:
            instance_key = str(strategy_instance_id)

            # Stop monitoring if active
            if instance_key in self.risk_engines:
                await self.stop_risk_monitoring(strategy_instance_id)

            # Clear cache entries
            await self.cache_service.delete(f"risk_monitor:{strategy_instance_id}")
            await self.cache_service.delete(f"risk_alerts:{strategy_instance_id}")

            logger.info(f"Cleaned up risk data for instance {strategy_instance_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup instance data: {e}")