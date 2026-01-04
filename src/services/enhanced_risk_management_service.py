"""
Enhanced Risk Management Service v3.0
Advanced real-time risk monitoring with position sizing and portfolio risk limits
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, UUID, Tuple
from uuid import uuid4
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..database import get_db
from ..models.strategy_models import Strategy, StrategyInstance
from ..models.risk_models_v2 import (
    RiskMonitoring, RiskMetric, RiskAlert, RiskPosition,
    RiskThreshold, RiskAlertLevel, RiskAlertType
)
from .cache_service import CacheService
from ..websocket.unified_websocket_manager import UnifiedWebSocketManager

logger = logging.getLogger(__name__)


class RiskLimitType(str, Enum):
    """Risk limit types"""
    MAX_POSITION_SIZE = "max_position_size"
    MAX_PORTFOLIO_EXPOSURE = "max_portfolio_exposure"
    MAX_SECTOR_EXPOSURE = "max_sector_exposure"
    MAX_CORRELATION = "max_correlation"
    MAX_TURNOVER = "max_turnover"
    VAR_LIMIT = "var_limit"
    DRAWDOWN_LIMIT = "drawdown_limit"
    LEVERAGE_LIMIT = "leverage_limit"


class PositionSizeMethod(str, Enum):
    """Position sizing methods"""
    FIXED_DOLLAR = "fixed_dollar"
    PERCENTAGE_CAPITAL = "percentage_capital"
    VOLATILITY_TARGET = "volatility_target"
    KELLY_CRITERION = "kelly_criterion"
    RISK_PARITY = "risk_parity"


@dataclass
class RiskLimit:
    """Risk limit configuration"""
    user_id: UUID
    strategy_instance_id: Optional[UUID]
    limit_type: RiskLimitType
    limit_value: float
    current_value: float
    utilization_percent: float
    warning_threshold: float = 0.8
    is_active: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.utilization_percent = (self.current_value / self.limit_value) * 100 if self.limit_value > 0 else 0


@dataclass
class PositionSizingConfig:
    """Position sizing configuration"""
    method: PositionSizeMethod
    base_amount: float
    risk_factor: float = 0.02  # Default 2% risk
    max_position_pct: float = 0.10  # Max 10% per position
    volatility_lookback: int = 20
    confidence_level: float = 0.95

    # Method-specific parameters
    fixed_amount: Optional[float] = None
    percentage_of_capital: Optional[float] = None
    target_volatility: Optional[float] = None
    kelly_fraction: Optional[float] = 0.25


class EnhancedRiskManagementService:
    """Enhanced risk management service with advanced features"""

    def __init__(self, db: Session):
        """Initialize enhanced risk management service"""
        self.db = db
        self.cache_service = CacheService()
        self.websocket_manager = UnifiedWebSocketManager()

        # Redis for real-time data
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=5,  # Use dedicated DB for risk management
            decode_responses=True
        )

        # Risk limits storage
        self.risk_limits: Dict[str, RiskLimit] = {}
        self.position_configs: Dict[UUID, PositionSizingConfig] = {}

        # Initialize default risk limits
        self._initialize_default_limits()

        # Background tasks
        self._monitoring_task = None
        self._running = False

    def _initialize_default_limits(self):
        """Initialize default risk limits for new users"""
        default_limits = {
            RiskLimitType.MAX_POSITION_SIZE: 0.10,  # 10% of portfolio
            RiskLimitType.MAX_PORTFOLIO_EXPOSURE: 1.0,  # 100% of capital
            RiskLimitType.MAX_SECTOR_EXPOSURE: 0.30,  # 30% in one sector
            RiskLimitType.MAX_CORRELATION: 0.70,  # 70% max correlation
            RiskLimitType.MAX_TURNOVER: 0.50,  # 50% monthly turnover
            RiskLimitType.VAR_LIMIT: 0.02,  # 2% daily VaR
            RiskLimitType.DRAWDOWN_LIMIT: 0.15,  # 15% max drawdown
            RiskLimitType.LEVERAGE_LIMIT: 2.0  # 2x max leverage
        }

        for limit_type, value in default_limits.items():
            self.risk_limits[limit_type.value] = RiskLimit(
                user_id=UUID('00000000-0000-0000-0000-000000000000'),  # System defaults
                strategy_instance_id=None,
                limit_type=limit_type,
                limit_value=value,
                current_value=0.0,
                warning_threshold=0.8
            )

    async def start_monitoring(self):
        """Start background risk monitoring"""
        if self._running:
            logger.warning("Risk monitoring is already running")
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Enhanced risk monitoring started")

    async def stop_monitoring(self):
        """Stop background risk monitoring"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Enhanced risk monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop for real-time risk assessment"""
        while self._running:
            try:
                # Get all active strategy instances
                active_instances = self.db.query(StrategyInstance).filter(
                    StrategyInstance.is_active == True
                ).all()

                # Process each instance
                for instance in active_instances:
                    await self._process_instance_risk(instance)

                # Sleep for next cycle (30 seconds)
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _process_instance_risk(self, instance: StrategyInstance):
        """Process risk for a strategy instance"""
        try:
            instance_id = str(instance.id)

            # Get current positions
            positions = await self._get_current_positions(instance_id)

            # Calculate portfolio metrics
            portfolio_metrics = await self._calculate_portfolio_metrics(
                instance_id, positions
            )

            # Check risk limits
            limit_breaches = await self._check_risk_limits(
                instance.user_id, instance_id, portfolio_metrics
            )

            # Update position sizing recommendations
            sizing_recommendations = await self._calculate_position_sizing(
                instance, positions, portfolio_metrics
            )

            # Store metrics in cache
            await self.cache_service.set(
                f"risk_metrics:{instance_id}",
                portfolio_metrics,
                ttl=300  # 5 minutes
            )

            # Broadcast updates via WebSocket
            await self.websocket_manager.broadcast_to_user(
                instance.user_id,
                "risk_update",
                {
                    "instance_id": instance_id,
                    "metrics": portfolio_metrics,
                    "limit_breaches": limit_breaches,
                    "sizing_recommendations": sizing_recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            # Log risk alerts
            for breach in limit_breaches:
                if breach['severity'] in ['warning', 'critical']:
                    await self._create_risk_alert(
                        instance.user_id,
                        instance_id,
                        breach['limit_type'],
                        breach
                    )

        except Exception as e:
            logger.error(f"Error processing risk for instance {instance.id}: {e}")

    async def _get_current_positions(self, instance_id: str) -> List[Dict]:
        """Get current positions for a strategy instance"""
        try:
            # Try to get from Redis cache first
            cached_positions = self.redis_client.get(f"positions:{instance_id}")
            if cached_positions:
                return json.loads(cached_positions)

            # Query from database if not in cache
            positions = self.db.query(RiskPosition).filter(
                RiskPosition.strategy_instance_id == instance_id
            ).all()

            position_list = []
            for pos in positions:
                position_list.append({
                    "symbol": pos.symbol,
                    "quantity": float(pos.quantity),
                    "market_value": float(pos.market_value),
                    "unrealized_pnl": float(pos.unrealized_pnl),
                    "position_weight": float(pos.position_weight),
                    "sector": pos.sector,
                    "asset_type": pos.asset_type
                })

            # Cache in Redis for 1 minute
            self.redis_client.setex(
                f"positions:{instance_id}",
                60,
                json.dumps(position_list)
            )

            return position_list

        except Exception as e:
            logger.error(f"Error getting positions for instance {instance_id}: {e}")
            return []

    async def _calculate_portfolio_metrics(
        self, instance_id: str, positions: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate comprehensive portfolio risk metrics"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_positions": len(positions),
            "total_exposure": 0.0,
            "cash_exposure": 0.0,
            "sector_exposure": {},
            "asset_type_exposure": {},
            "concentration_metrics": {},
            "risk_metrics": {}
        }

        if not positions:
            return metrics

        # Calculate basic exposures
        total_market_value = sum(p['market_value'] for p in positions)
        metrics['total_exposure'] = total_market_value

        # Sector exposure
        for pos in positions:
            sector = pos.get('sector', 'Unknown')
            if sector not in metrics['sector_exposure']:
                metrics['sector_exposure'][sector] = 0
            metrics['sector_exposure'][sector] += pos['market_value']

        # Convert to percentages
        for sector in metrics['sector_exposure']:
            metrics['sector_exposure'][sector] = (
                metrics['sector_exposure'][sector] / total_market_value
            ) if total_market_value > 0 else 0

        # Asset type exposure
        for pos in positions:
            asset_type = pos.get('asset_type', 'Unknown')
            if asset_type not in metrics['asset_type_exposure']:
                metrics['asset_type_exposure'][asset_type] = 0
            metrics['asset_type_exposure'][asset_type] += pos['market_value']

        # Convert to percentages
        for asset_type in metrics['asset_type_exposure']:
            metrics['asset_type_exposure'][asset_type] = (
                metrics['asset_type_exposure'][asset_type] / total_market_value
            ) if total_market_value > 0 else 0

        # Concentration metrics
        position_weights = [p['position_weight'] for p in positions if p['position_weight']]
        if position_weights:
            metrics['concentration_metrics'] = {
                "max_position_weight": max(position_weights),
                "top_5_concentration": sum(sorted(position_weights, reverse=True)[:5]),
                "herfindahl_index": sum(w**2 for w in position_weights)
            }

        # Get historical returns for risk calculations
        returns_data = await self._get_historical_returns(instance_id)

        if returns_data is not None and len(returns_data) > 20:
            # Calculate risk metrics
            metrics['risk_metrics'] = await self._calculate_risk_metrics(
                returns_data, total_market_value
            )

        return metrics

    async def _calculate_risk_metrics(
        self, returns: pd.Series, portfolio_value: float
    ) -> Dict[str, float]:
        """Calculate advanced risk metrics"""
        metrics = {}

        try:
            # VaR calculations
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            metrics['var_95_daily'] = float(var_95 * portfolio_value)
            metrics['var_99_daily'] = float(var_99 * portfolio_value)

            # Expected Shortfall
            es_95 = returns[returns <= var_95].mean()
            es_99 = returns[returns <= var_99].mean()
            metrics['es_95_daily'] = float(es_95 * portfolio_value)
            metrics['es_99_daily'] = float(es_99 * portfolio_value)

            # Volatility
            metrics['volatility_daily'] = float(returns.std())
            metrics['volatility_annualized'] = float(returns.std() * np.sqrt(252))

            # Maximum drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            metrics['max_drawdown'] = float(drawdown.min())
            metrics['current_drawdown'] = float(drawdown.iloc[-1] if len(drawdown) > 0 else 0)

            # Sharpe ratio (assuming 2% risk-free rate)
            risk_free_daily = 0.02 / 252
            excess_returns = returns - risk_free_daily
            if excess_returns.std() > 0:
                metrics['sharpe_ratio'] = float(
                    excess_returns.mean() / excess_returns.std() * np.sqrt(252)
                )
            else:
                metrics['sharpe_ratio'] = 0

            # Sortino ratio
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0 and downside_returns.std() > 0:
                metrics['sortino_ratio'] = float(
                    (returns.mean() - risk_free_daily) / downside_returns.std() * np.sqrt(252)
                )
            else:
                metrics['sortino_ratio'] = 0

            # Calmar ratio (if drawdown < 0)
            if metrics['max_drawdown'] < 0:
                annual_return = (1 + returns.mean()) ** 252 - 1
                metrics['calmar_ratio'] = float(annual_return / abs(metrics['max_drawdown']))
            else:
                metrics['calmar_ratio'] = 0

            # Beta and Alpha (relative to market benchmark)
            market_returns = await self._get_market_returns()
            if market_returns is not None and len(market_returns) == len(returns):
                covariance = np.cov(returns, market_returns)[0, 1]
                market_variance = np.var(market_returns)
                if market_variance > 0:
                    metrics['beta'] = float(covariance / market_variance)
                    # Alpha calculation
                    market_return = market_returns.mean() * 252
                    portfolio_return = returns.mean() * 252
                    metrics['alpha'] = float(
                        portfolio_return - (0.02 + metrics['beta'] * (market_return - 0.02))
                    )
                else:
                    metrics['beta'] = 1.0
                    metrics['alpha'] = 0.0
            else:
                metrics['beta'] = 1.0
                metrics['alpha'] = 0.0

        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")

        return metrics

    async def _get_historical_returns(self, instance_id: str) -> Optional[pd.Series]:
        """Get historical returns for a strategy instance"""
        try:
            # This would typically query InfluxDB or another time-series database
            # For now, return mock data
            np.random.seed(hash(instance_id) % 2**32)
            returns = np.random.normal(0.001, 0.02, 100)  # 100 days of returns
            return pd.Series(returns)
        except Exception as e:
            logger.error(f"Error getting historical returns: {e}")
            return None

    async def _get_market_returns(self) -> Optional[pd.Series]:
        """Get market benchmark returns (e.g., S&P 500)"""
        try:
            # This would fetch from market data provider
            # For now, return mock data
            np.random.seed(42)
            returns = np.random.normal(0.0005, 0.01, 100)
            return pd.Series(returns)
        except Exception as e:
            logger.error(f"Error getting market returns: {e}")
            return None

    async def _check_risk_limits(
        self, user_id: UUID, instance_id: str, metrics: Dict[str, Any]
    ) -> List[Dict]:
        """Check if current metrics exceed risk limits"""
        breaches = []

        # Check position limits
        concentration = metrics.get('concentration_metrics', {})
        max_position = concentration.get('max_position_weight', 0)

        position_limit = self.risk_limits.get(RiskLimitType.MAX_POSITION_SIZE.value)
        if position_limit and max_position > position_limit.limit_value:
            severity = 'critical' if max_position > position_limit.limit_value * 1.2 else 'warning'
            breaches.append({
                'limit_type': RiskLimitType.MAX_POSITION_SIZE.value,
                'current_value': max_position,
                'limit_value': position_limit.limit_value,
                'utilization': (max_position / position_limit.limit_value) * 100,
                'severity': severity,
                'message': f"Maximum position size of {max_position:.2%} exceeds limit of {position_limit.limit_value:.2%}"
            })

        # Check sector concentration
        sector_exposure = metrics.get('sector_exposure', {})
        sector_limit = self.risk_limits.get(RiskLimitType.MAX_SECTOR_EXPOSURE.value)
        if sector_limit:
            for sector, exposure in sector_exposure.items():
                if exposure > sector_limit.limit_value:
                    severity = 'critical' if exposure > sector_limit.limit_value * 1.1 else 'warning'
                    breaches.append({
                        'limit_type': RiskLimitType.MAX_SECTOR_EXPOSURE.value,
                        'current_value': exposure,
                        'limit_value': sector_limit.limit_value,
                        'utilization': (exposure / sector_limit.limit_value) * 100,
                        'severity': severity,
                        'sector': sector,
                        'message': f"Sector '{sector}' exposure of {exposure:.2%} exceeds limit of {sector_limit.limit_value:.2%}"
                    })

        # Check VaR limits
        risk_metrics = metrics.get('risk_metrics', {})
        var_99 = abs(risk_metrics.get('var_99_daily', 0))
        var_limit = self.risk_limits.get(RiskLimitType.VAR_LIMIT.value)
        if var_limit and var_99 > var_limit.limit_value:
            severity = 'critical' if var_99 > var_limit.limit_value * 1.5 else 'warning'
            breaches.append({
                'limit_type': RiskLimitType.VAR_LIMIT.value,
                'current_value': var_99,
                'limit_value': var_limit.limit_value,
                'utilization': (var_99 / var_limit.limit_value) * 100,
                'severity': severity,
                'message': f"99% VaR of ${var_99:,.2f} exceeds limit of ${var_limit.limit_value:,.2f}"
            })

        # Check drawdown limits
        current_drawdown = abs(risk_metrics.get('current_drawdown', 0))
        drawdown_limit = self.risk_limits.get(RiskLimitType.DRAWDOWN_LIMIT.value)
        if drawdown_limit and current_drawdown > drawdown_limit.limit_value:
            severity = 'critical' if current_drawdown > drawdown_limit.limit_value * 1.2 else 'warning'
            breaches.append({
                'limit_type': RiskLimitType.DRAWDOWN_LIMIT.value,
                'current_value': current_drawdown,
                'limit_value': drawdown_limit.limit_value,
                'utilization': (current_drawdown / drawdown_limit.limit_value) * 100,
                'severity': severity,
                'message': f"Current drawdown of {current_drawdown:.2%} exceeds limit of {drawdown_limit.limit_value:.2%}"
            })

        return breaches

    async def _calculate_position_sizing(
        self, instance: StrategyInstance, positions: List[Dict], metrics: Dict[str, Any]
    ) -> List[Dict]:
        """Calculate position sizing recommendations"""
        recommendations = []

        # Get or create position sizing config
        config = self.position_configs.get(instance.id)
        if not config:
            config = PositionSizingConfig(
                method=PositionSizeMethod.PERCENTAGE_CAPITAL,
                base_amount=100000,  # Default base capital
                max_position_pct=0.10
            )
            self.position_configs[instance.id] = config

        # Get portfolio metrics
        total_exposure = metrics.get('total_exposure', 0)
        risk_metrics = metrics.get('risk_metrics', {})
        volatility = risk_metrics.get('volatility_annualized', 0.15)

        # Calculate recommendations based on method
        if config.method == PositionSizeMethod.PERCENTAGE_CAPITAL:
            # Fixed percentage of capital per position
            position_size = config.base_amount * config.percentage_of_capital

        elif config.method == PositionSizeMethod.VOLATILITY_TARGET:
            # Size based on volatility targeting
            if volatility > 0:
                position_size = (config.base_amount * config.risk_factor) / volatility
            else:
                position_size = 0

        elif config.method == PositionSizeMethod.KELLY_CRITERION:
            # Kelly criterion sizing (simplified)
            expected_return = risk_metrics.get('sharpe_ratio', 0) * volatility
            if volatility > 0:
                kelly_fraction = expected_return / (volatility ** 2)
                position_size = config.base_amount * kelly_fraction * (config.kelly_fraction or 0.25)
            else:
                position_size = 0

        elif config.method == PositionSizeMethod.RISK_PARITY:
            # Equal risk contribution
            num_positions = max(1, len(positions))
            position_size = config.base_amount / num_positions

        else:  # FIXED_DOLLAR
            position_size = config.fixed_amount or config.base_amount

        # Apply maximum position limit
        max_position = config.base_amount * config.max_position_pct
        position_size = min(position_size, max_position)

        # Create recommendation for each existing position
        for pos in positions:
            current_value = pos.get('market_value', 0)
            recommended_value = position_size

            action = None
            if current_value > recommended_value * 1.1:
                action = 'reduce'
            elif current_value < recommended_value * 0.9:
                action = 'increase'

            if action:
                recommendations.append({
                    'symbol': pos['symbol'],
                    'action': action,
                    'current_value': current_value,
                    'recommended_value': recommended_value,
                    'difference': recommended_value - current_value,
                    'method': config.method.value,
                    'reasoning': f"Based on {config.method.value} with {config.risk_factor:.1%} risk factor"
                })

        return recommendations

    async def _create_risk_alert(
        self, user_id: UUID, instance_id: str, limit_type: str, breach: Dict
    ) -> str:
        """Create a risk alert in the database"""
        try:
            alert = RiskAlert(
                monitoring_id=None,  # Will be linked when monitoring is set up
                alert_level=breach['severity'],
                alert_type=limit_type,
                title=f"Risk Limit Breach: {limit_type.replace('_', ' ').title()}",
                message=breach['message'],
                metric_name=limit_type,
                threshold_value=breach['limit_value'],
                actual_value=breach['current_value'],
                deviation_percent=breach['utilization'] - 100,
                context={
                    'instance_id': instance_id,
                    'utilization': breach['utilization'],
                    'limit_type': limit_type
                },
                created_at=datetime.utcnow()
            )

            self.db.add(alert)
            self.db.commit()

            logger.warning(
                f"Risk alert created for user {user_id}, instance {instance_id}: "
                f"{breach['severity']} - {breach['message']}"
            )

            # Send immediate notification via WebSocket
            await self.websocket_manager.broadcast_to_user(
                user_id,
                "risk_alert",
                {
                    "alert_id": str(alert.id),
                    "severity": breach['severity'],
                    "type": limit_type,
                    "message": breach['message'],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            return str(alert.id)

        except Exception as e:
            logger.error(f"Error creating risk alert: {e}")
            self.db.rollback()
            return None

    async def set_risk_limit(
        self, user_id: UUID, limit_type: RiskLimitType, limit_value: float,
        strategy_instance_id: Optional[UUID] = None
    ) -> bool:
        """Set a custom risk limit for a user or strategy"""
        try:
            limit = RiskLimit(
                user_id=user_id,
                strategy_instance_id=strategy_instance_id,
                limit_type=limit_type,
                limit_value=limit_value,
                current_value=0.0
            )

            self.risk_limits[f"{user_id}:{limit_type.value}"] = limit

            # Store in database for persistence
            db_limit = RiskThreshold(
                user_id=user_id,
                strategy_instance_id=strategy_instance_id,
                name=f"{limit_type.value}_limit",
                metric_type=limit_type.value,
                description=f"Custom limit for {limit_type.value}",
                error_threshold=limit_value * 0.9,
                critical_threshold=limit_value,
                comparison_operator="greater_than",
                enabled=True
            )

            self.db.add(db_limit)
            self.db.commit()

            logger.info(f"Risk limit set for user {user_id}: {limit_type.value} = {limit_value}")
            return True

        except Exception as e:
            logger.error(f"Error setting risk limit: {e}")
            self.db.rollback()
            return False

    async def configure_position_sizing(
        self, strategy_instance_id: UUID, config: PositionSizingConfig
    ) -> bool:
        """Configure position sizing for a strategy instance"""
        try:
            self.position_configs[strategy_instance_id] = config

            # Store in cache
            await self.cache_service.set(
                f"position_config:{strategy_instance_id}",
                asdict(config),
                ttl=3600
            )

            logger.info(f"Position sizing configured for instance {strategy_instance_id}")
            return True

        except Exception as e:
            logger.error(f"Error configuring position sizing: {e}")
            return False

    async def get_real_time_risk_dashboard(self, user_id: UUID) -> Dict[str, Any]:
        """Get comprehensive real-time risk dashboard data"""
        try:
            # Get all user's strategy instances
            instances = self.db.query(StrategyInstance).filter(
                StrategyInstance.user_id == user_id,
                StrategyInstance.is_active == True
            ).all()

            dashboard = {
                "user_id": str(user_id),
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_instances": len(instances),
                    "active_alerts": 0,
                    "risk_score": 0,
                    "total_exposure": 0
                },
                "instances": [],
                "risk_limits": [],
                "alerts": []
            }

            # Process each instance
            for instance in instances:
                instance_id = str(instance.id)

                # Get cached metrics
                metrics = await self.cache_service.get(f"risk_metrics:{instance_id}")

                # Get monitoring status
                monitoring = self.db.query(RiskMonitoring).filter(
                    RiskMonitoring.strategy_instance_id == instance.id
                ).first()

                instance_data = {
                    "id": instance_id,
                    "name": instance.name,
                    "strategy_name": instance.strategy.name if instance.strategy else "Unknown",
                    "monitoring_active": monitoring.is_active if monitoring else False,
                    "metrics": metrics or {},
                    "last_update": metrics.get('timestamp') if metrics else None
                }

                dashboard["instances"].append(instance_data)

                # Update summary
                if metrics:
                    dashboard["summary"]["total_exposure"] += metrics.get('total_exposure', 0)

            # Get risk limits
            user_limits = []
            for key, limit in self.risk_limits.items():
                if str(limit.user_id) == str(user_id):
                    user_limits.append({
                        "type": limit.limit_type.value,
                        "limit_value": limit.limit_value,
                        "current_value": limit.current_value,
                        "utilization": limit.utilization_percent,
                        "status": "warning" if limit.utilization_percent > 80 else "normal"
                    })

            dashboard["risk_limits"] = user_limits

            # Get active alerts
            alerts = self.db.query(RiskAlert).join(RiskMonitoring).filter(
                RiskMonitoring.strategy_instance_id.in_([i.id for i in instances]),
                RiskAlert.is_active == True
            ).order_by(RiskAlert.created_at.desc()).limit(10).all()

            dashboard["alerts"] = [
                {
                    "id": str(alert.id),
                    "level": alert.alert_level,
                    "type": alert.alert_type,
                    "message": alert.message,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in alerts
            ]

            dashboard["summary"]["active_alerts"] = len(dashboard["alerts"])

            # Calculate risk score (simplified)
            risk_score = 0
            for alert in dashboard["alerts"]:
                if alert["level"] == "critical":
                    risk_score += 10
                elif alert["level"] == "error":
                    risk_score += 5
                elif alert["level"] == "warning":
                    risk_score += 2

            dashboard["summary"]["risk_score"] = min(100, risk_score)

            return dashboard

        except Exception as e:
            logger.error(f"Error getting risk dashboard: {e}")
            return {}

    async def get_portfolio_recommendations(self, user_id: UUID) -> List[Dict]:
        """Get AI-powered risk management recommendations"""
        try:
            recommendations = []

            # Get risk dashboard for context
            dashboard = await self.get_real_time_risk_dashboard(user_id)

            # Analyze risk metrics and generate recommendations
            for instance in dashboard.get("instances", []):
                metrics = instance.get("metrics", {})
                risk_metrics = metrics.get("risk_metrics", {})

                # Volatility recommendations
                volatility = risk_metrics.get("volatility_annualized", 0)
                if volatility > 0.25:  # High volatility
                    recommendations.append({
                        "type": "risk_reduction",
                        "priority": "high",
                        "instance_id": instance["id"],
                        "instance_name": instance["name"],
                        "title": "High Portfolio Volatility Detected",
                        "description": f"Portfolio volatility of {volatility:.1%} exceeds recommended levels",
                        "actions": [
                            "Consider reducing position sizes",
                            "Add low-volatility assets",
                            "Implement volatility targeting"
                        ],
                        "expected_impact": "Reduce volatility by 20-30%"
                    })

                # Concentration recommendations
                concentration = metrics.get("concentration_metrics", {})
                top_5 = concentration.get("top_5_concentration", 0)
                if top_5 > 0.60:  # High concentration
                    recommendations.append({
                        "type": "diversification",
                        "priority": "medium",
                        "instance_id": instance["id"],
                        "instance_name": instance["name"],
                        "title": "Portfolio Concentration Risk",
                        "description": f"Top 5 positions represent {top_5:.1%} of portfolio",
                        "actions": [
                            "Reduce size of largest positions",
                            "Add positions in uncorrelated assets",
                            "Consider sector diversification"
                        ],
                        "expected_impact": "Improve diversification ratio"
                    })

                # Sharpe ratio recommendations
                sharpe = risk_metrics.get("sharpe_ratio", 0)
                if sharpe < 0.5:  # Low risk-adjusted return
                    recommendations.append({
                        "type": "performance",
                        "priority": "medium",
                        "instance_id": instance["id"],
                        "instance_name": instance["name"],
                        "title": "Low Risk-Adjusted Returns",
                        "description": f"Sharpe ratio of {sharpe:.2f} is below optimal levels",
                        "actions": [
                            "Review strategy parameters",
                            "Consider factor tilts",
                            "Optimize entry/exit rules"
                        ],
                        "expected_impact": "Improve Sharpe ratio to >1.0"
                    })

                # Drawdown recommendations
                current_dd = abs(risk_metrics.get("current_drawdown", 0))
                if current_dd > 0.10:  # Significant drawdown
                    recommendations.append({
                        "type": "risk_control",
                        "priority": "high",
                        "instance_id": instance["id"],
                        "instance_name": instance["name"],
                        "title": "Significant Drawdown Detected",
                        "description": f"Current drawdown of {current_dd:.1%} requires attention",
                        "actions": [
                            "Implement tighter stop-losses",
                            "Reduce position sizes temporarily",
                            "Review market regime changes"
                        ],
                        "expected_impact": "Limit further losses and aid recovery"
                    })

            # Sort by priority
            priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            recommendations.sort(
                key=lambda x: priority_order.get(x["priority"], 0),
                reverse=True
            )

            return recommendations[:20]  # Return top 20 recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []