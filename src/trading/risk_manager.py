"""
Risk Manager Module
風險管理器模塊

Provides comprehensive risk management including:
- Pre-trade risk checks
- Real-time position monitoring
- Portfolio risk metrics
- Dynamic position sizing
- Stop-loss and take-profit management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from uuid import UUID
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from ..models.trading_models_v2 import (
    Position, Order, Portfolio, TradingSignal
)
from ..core.database import get_db_session


class RiskLevel(str, Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """告警類型"""
    POSITION_SIZE = "position_size"
    LOSS_LIMIT = "loss_limit"
    CORRELATION = "correlation"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    CONCENTRATION = "concentration"


@dataclass
class RiskLimits:
    """風險限制"""
    max_position_size: Optional[Decimal] = None  # Maximum position size per symbol
    max_portfolio_risk: Optional[float] = None   # Maximum portfolio risk (0-1)
    max_correlation: Optional[float] = None      # Maximum correlation between positions
    max_drawdown: Optional[float] = None         # Maximum drawdown (0-1)
    daily_loss_limit: Optional[Decimal] = None   # Daily loss limit
    var_limit: Optional[float] = None            # VaR limit (0-1)
    max_leverage: Optional[float] = None         # Maximum leverage


@dataclass
class RiskAlert:
    """風險告警"""
    alert_id: str
    type: AlertType
    severity: RiskLevel
    symbol: Optional[str] = None
    portfolio_id: Optional[UUID] = None
    message: str = ""
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RiskCheckResult:
    """風險檢查結果"""
    passed: bool
    alerts: List[RiskAlert] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    position_size_adjusted: Optional[Decimal] = None
    recommended_action: Optional[str] = None


@dataclass
class PortfolioRisk:
    """投資組合風險"""
    portfolio_id: UUID
    total_exposure: Decimal
    net_exposure: Decimal
    gross_exposure: Decimal
    leverage: float
    var_1d: Optional[float] = None  # 1-day VaR
    var_5d: Optional[float] = None  # 5-day VaR
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    beta: Optional[float] = None
    correlation_matrix: Optional[Dict] = None
    sector_exposure: Dict[str, Decimal] = field(default_factory=dict)
    currency_exposure: Dict[str, Decimal] = field(default_factory=dict)


class RiskManager:
    """
    風險管理器

    負責：
    - 交易前風險檢查
    - 實時風險監控
    - 動態倉位調整
    - 止損管理
    - 風險報告生成
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("risk_manager")

        # Risk limits
        self.default_limits = RiskLimits(
            max_position_size=Decimal(str(config.get('max_position_size', 1000000))),
            max_portfolio_risk=config.get('max_portfolio_risk', 0.02),
            max_correlation=config.get('max_correlation', 0.7),
            max_drawdown=config.get('max_drawdown', 0.15),
            daily_loss_limit=Decimal(str(config.get('daily_loss_limit', 50000))),
            var_limit=config.get('var_limit', 0.02),
            max_leverage=config.get('max_leverage', 2.0)
        )
        self.portfolio_limits: Dict[UUID, RiskLimits] = {}

        # Risk tracking
        self.portfolio_risk: Dict[UUID, PortfolioRisk] = {}
        self.alert_history: List[RiskAlert] = []
        self.daily_pnl: Dict[UUID, Decimal] = defaultdict(Decimal)
        self.high_water_marks: Dict[UUID, Decimal] = {}

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Market data for risk calculations
        self.price_history: Dict[str, List[Tuple[datetime, Decimal]]] = defaultdict(list)
        self.volatility_cache: Dict[str, float] = {}
        self.correlation_cache: Dict[Tuple[str, str], float] = {}

        # Risk metrics
        self.risk_update_interval = config.get('risk_update_interval', 60)  # seconds
        self.var_confidence = config.get('var_confidence', 0.95)
        self.var_period = config.get('var_period', 1)  # days

    async def initialize(self) -> None:
        """初始化風險管理器"""
        self.logger.info("Initializing risk manager...")

        self._running = False
        self._shutdown_event.clear()

        # Load portfolio limits
        await self._load_portfolio_limits()

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._update_risk_metrics()),
            asyncio.create_task(self._monitor_risk_alerts()),
            asyncio.create_task(self._calculate_daily_pnl()),
            asyncio.create_task(self._cleanup_old_data())
        ]

        self.logger.info("Risk manager initialized")

    async def shutdown(self) -> None:
        """關閉風險管理器"""
        self.logger.info("Shutting down risk manager...")

        self._running = False
        self._shutdown_event.set()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.logger.info("Risk manager shutdown complete")

    async def pre_trade_risk_check(self, signal: TradingSignal, portfolio) -> RiskCheckResult:
        """交易前風險檢查"""
        try:
            portfolio_id = portfolio.id if isinstance(portfolio, Portfolio) else portfolio
            limits = self.portfolio_limits.get(portfolio_id, self.default_limits)

            result = RiskCheckResult(passed=True)

            # Check 1: Position size limit
            if limits.max_position_size:
                if signal.quantity * (signal.price or Decimal('100')) > limits.max_position_size:
                    result.passed = False
                    result.alerts.append(RiskAlert(
                        alert_id=f"pos_size_{signal.symbol}",
                        type=AlertType.POSITION_SIZE,
                        severity=RiskLevel.HIGH,
                        symbol=signal.symbol,
                        message=f"Position size exceeds limit: {signal.quantity}",
                        current_value=float(signal.quantity * (signal.price or Decimal('100'))),
                        threshold=float(limits.max_position_size)
                    ))

            # Check 2: Daily loss limit
            if limits.daily_loss_limit:
                daily_loss = self.daily_pnl.get(portfolio_id, Decimal('0'))
                if daily_loss < -limits.daily_loss_limit:
                    result.passed = False
                    result.alerts.append(RiskAlert(
                        alert_id="daily_loss",
                        type=AlertType.LOSS_LIMIT,
                        severity=RiskLevel.CRITICAL,
                        portfolio_id=portfolio_id,
                        message=f"Daily loss limit exceeded: {daily_loss}",
                        current_value=float(abs(daily_loss)),
                        threshold=float(limits.daily_loss_limit)
                    ))

            # Check 3: Portfolio concentration
            concentration = await self._calculate_concentration(portfolio_id, signal)
            if concentration > 0.3:  # More than 30% in one position
                result.warnings.append(
                    f"High concentration risk: {concentration:.2%} in {signal.symbol}"
                )

            # Check 4: Correlation risk
            if signal.symbol in self.correlation_cache:
                avg_correlation = np.mean([
                    corr for (s1, s2), corr in self.correlation_cache.items()
                    if s1 == signal.symbol or s2 == signal.symbol
                ])
                if avg_correlation > 0.8:
                    result.warnings.append(
                        f"High correlation risk: {avg_correlation:.2f}"
                    )

            # Adjust position size if needed
            if result.passed and limits.max_position_size:
                max_allowed = limits.max_position_size / (signal.price or Decimal('100'))
                if signal.quantity > max_allowed:
                    result.position_size_adjusted = min(max_allowed, signal.quantity)
                    result.recommended_action = "Reduce position size to meet risk limits"

            return result

        except Exception as e:
            self.logger.error(f"Error in pre-trade risk check: {e}")
            return RiskCheckResult(
                passed=False,
                alerts=[RiskAlert(
                    alert_id="system_error",
                    type=AlertType.LOSS_LIMIT,
                    severity=RiskLevel.CRITICAL,
                    message=f"Risk check failed: {str(e)}"
                )]
            )

    async def calculate_risk_metrics(self, portfolio) -> PortfolioRisk:
        """計算投資組合風險指標"""
        try:
            portfolio_id = portfolio.id if isinstance(portfolio, Portfolio) else portfolio

            # Get current positions
            positions = await self._get_portfolio_positions(portfolio_id)

            # Calculate exposures
            total_exposure = sum(
                abs(pos.market_value or Decimal('0')) for pos in positions
            )
            long_exposure = sum(
                pos.market_value or Decimal('0') for pos in positions
                if pos.side == 'LONG'
            )
            short_exposure = sum(
                abs(pos.market_value or Decimal('0')) for pos in positions
                if pos.side == 'SHORT'
            )

            net_exposure = long_exposure - short_exposure
            gross_exposure = long_exposure + short_exposure

            # Calculate leverage
            portfolio_value = await self._get_portfolio_value(portfolio_id)
            leverage = float(gross_exposure / portfolio_value) if portfolio_value > 0 else 0

            # Calculate VaR
            var_1d = await self._calculate_var(portfolio_id, 1)
            var_5d = await self._calculate_var(portfolio_id, 5)

            # Calculate max drawdown
            max_drawdown = await self._calculate_max_drawdown(portfolio_id)

            # Calculate Sharpe ratio
            sharpe_ratio = await self._calculate_sharpe_ratio(portfolio_id)

            # Calculate beta
            beta = await self._calculate_portfolio_beta(portfolio_id)

            # Create risk object
            risk = PortfolioRisk(
                portfolio_id=portfolio_id,
                total_exposure=total_exposure,
                net_exposure=net_exposure,
                gross_exposure=gross_exposure,
                leverage=leverage,
                var_1d=var_1d,
                var_5d=var_5d,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                beta=beta
            )

            # Store for monitoring
            self.portfolio_risk[portfolio_id] = risk

            return risk

        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return PortfolioRisk(portfolio_id=portfolio_id, **{
                'total_exposure': Decimal('0'),
                'net_exposure': Decimal('0'),
                'gross_exposure': Decimal('0'),
                'leverage': 0
            })

    async def check_position_risk(self, position: Position) -> List[RiskAlert]:
        """檢查單個倉位風險"""
        alerts = []

        try:
            # Check stop-loss
            if position.unrealized_pnl and position.unrealized_pnl < 0:
                loss_pct = abs(float(position.unrealized_pnl_percent or 0))
                if loss_pct > 10:  # More than 10% loss
                    alerts.append(RiskAlert(
                        alert_id=f"stop_loss_{position.id}",
                        type=AlertType.LOSS_LIMIT,
                        severity=RiskLevel.HIGH,
                        symbol=position.symbol,
                        message=f"Position loss exceeds 10%: {loss_pct:.2f}%",
                        current_value=loss_pct,
                        threshold=10.0
                    ))

            # Check position size relative to portfolio
            portfolio_value = await self._get_portfolio_value(position.portfolio_id)
            if portfolio_value > 0 and position.market_value:
                concentration = float(position.market_value / portfolio_value)
                if concentration > 0.2:  # More than 20% of portfolio
                    alerts.append(RiskAlert(
                        alert_id=f"concentration_{position.id}",
                        type=AlertType.CONCENTRATION,
                        severity=RiskLevel.MEDIUM,
                        symbol=position.symbol,
                        message=f"High concentration: {concentration:.2%}",
                        current_value=concentration,
                        threshold=0.2
                    ))

        except Exception as e:
            self.logger.error(f"Error checking position risk: {e}")

        return alerts

    async def set_stop_loss(
        self,
        position_id: UUID,
        stop_loss_pct: float,
        trailing: bool = False
    ) -> bool:
        """設置止損"""
        try:
            # This would typically create a stop-loss order
            # For now, just log the action
            self.logger.info(
                f"Setting stop loss for position {position_id}: {stop_loss_pct}%"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error setting stop loss: {e}")
            return False

    async def set_take_profit(
        self,
        position_id: UUID,
        take_profit_pct: float
    ) -> bool:
        """設置止盈"""
        try:
            # This would typically create a take-profit order
            self.logger.info(
                f"Setting take profit for position {position_id}: {take_profit_pct}%"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error setting take profit: {e}")
            return False

    async def get_risk_summary(self, portfolio_id: UUID) -> Dict[str, Any]:
        """獲取風險摘要"""
        try:
            risk = self.portfolio_risk.get(portfolio_id)
            if not risk:
                return {}

            limits = self.portfolio_limits.get(portfolio_id, self.default_limits)
            daily_pnl = self.daily_pnl.get(portfolio_id, Decimal('0'))

            # Calculate risk score
            risk_score = self._calculate_risk_score(risk, limits, daily_pnl)

            return {
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'leverage': risk.leverage,
                'var_1d': risk.var_1d,
                'max_drawdown': risk.max_drawdown,
                'daily_pnl': float(daily_pnl),
                'utilization': {
                    'position_size': 'N/A',  # Would calculate
                    'var': f"{risk.var_1d:.2%}" if risk.var_1d else 'N/A',
                    'leverage': f"{risk.leverage:.2f}x",
                    'correlation': 'N/A'  # Would calculate
                },
                'alerts_count': len([
                    a for a in self.alert_history[-100:]
                    if a.portfolio_id == portfolio_id
                ])
            }

        except Exception as e:
            self.logger.error(f"Error getting risk summary: {e}")
            return {}

    async def _load_portfolio_limits(self) -> None:
        """加載投資組合風險限制"""
        try:
            # This would load from database
            # For now, use default limits for all
            pass
        except Exception as e:
            self.logger.error(f"Error loading portfolio limits: {e}")

    async def _calculate_concentration(self, portfolio_id: UUID, signal: TradingSignal) -> float:
        """計算集中度風險"""
        try:
            # Get existing position for symbol
            existing_position = await self._get_position(portfolio_id, signal.symbol)
            existing_quantity = existing_position.quantity if existing_position else Decimal('0')

            # Calculate new total position
            new_quantity = existing_quantity + signal.quantity
            new_value = new_quantity * (signal.price or Decimal('100'))

            # Get portfolio value
            portfolio_value = await self._get_portfolio_value(portfolio_id)

            if portfolio_value > 0:
                return float(new_value / portfolio_value)
            return 0

        except Exception as e:
            self.logger.error(f"Error calculating concentration: {e}")
            return 0

    async def _calculate_var(self, portfolio_id: UUID, days: int) -> Optional[float]:
        """計算VaR (Value at Risk)"""
        try:
            positions = await self._get_portfolio_positions(portfolio_id)
            if not positions:
                return None

            # Get historical returns for each position
            returns_matrix = []
            weights = []

            for position in positions:
                # Get price history and calculate returns
                symbol = position.symbol
                if symbol in self.price_history and len(self.price_history[symbol]) > days:
                    prices = [p for _, p in self.price_history[symbol][-days-1:]]
                    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                    returns_matrix.append(returns)
                    weights.append(float(position.market_value or Decimal('0')))

            if not returns_matrix:
                return None

            # Calculate portfolio returns
            portfolio_returns = []
            for i in range(len(returns_matrix[0])):
                portfolio_return = sum(
                    returns_matrix[j][i] * weights[j] for j in range(len(returns_matrix))
                ) / sum(weights) if sum(weights) > 0 else 0
                portfolio_returns.append(portfolio_return)

            # Calculate VaR
            if portfolio_returns:
                var_percentile = (1 - self.var_confidence) * 100
                var = np.percentile(portfolio_returns, var_percentile)
                portfolio_value = await self._get_portfolio_value(portfolio_id)
                return abs(var * portfolio_value) if portfolio_value > 0 else None

            return None

        except Exception as e:
            self.logger.error(f"Error calculating VaR: {e}")
            return None

    async def _calculate_max_drawdown(self, portfolio_id: UUID) -> Optional[float]:
        """計算最大回撤"""
        try:
            # Get historical portfolio values
            # This would typically be stored somewhere
            # For now, return None
            return None
        except Exception as e:
            self.logger.error(f"Error calculating max drawdown: {e}")
            return None

    async def _calculate_sharpe_ratio(self, portfolio_id: UUID) -> Optional[float]:
        """計算夏普比率"""
        try:
            # Get historical returns and risk-free rate
            # This would typically be calculated from historical data
            return None
        except Exception as e:
            self.logger.error(f"Error calculating Sharpe ratio: {e}")
            return None

    async def _calculate_portfolio_beta(self, portfolio_id: UUID) -> Optional[float]:
        """計算投資組合Beta"""
        try:
            # Calculate weighted average of position betas
            positions = await self._get_portfolio_positions(portfolio_id)
            if not positions:
                return None

            total_value = sum(pos.market_value or Decimal('0') for pos in positions)
            if total_value == 0:
                return None

            # This would typically get beta from market data
            # For now, return None
            return None
        except Exception as e:
            self.logger.error(f"Error calculating portfolio beta: {e}")
            return None

    async def _get_portfolio_positions(self, portfolio_id: UUID) -> List[Position]:
        """獲取投資組合倉位"""
        # This would typically query the position manager
        return []

    async def _get_position(self, portfolio_id: UUID, symbol: str) -> Optional[Position]:
        """獲取指定倉位"""
        positions = await self._get_portfolio_positions(portfolio_id)
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None

    async def _get_portfolio_value(self, portfolio_id: UUID) -> Decimal:
        """獲取投資組合價值"""
        # This would typically query the portfolio manager
        return Decimal('0')

    def _calculate_risk_score(self, risk: PortfolioRisk, limits: RiskLimits, daily_pnl: Decimal) -> float:
        """計算風險分數 (0-100)"""
        score = 0

        # Leverage risk
        if limits.max_leverage and risk.leverage > limits.max_leverage:
            score += 30 * (risk.leverage / limits.max_leverage - 1)

        # VaR risk
        if limits.var_limit and risk.var_1d and risk.var_1d > limits.var_limit:
            score += 25 * (risk.var_1d / limits.var_limit - 1)

        # Drawdown risk
        if limits.max_drawdown and risk.max_drawdown and risk.max_drawdown > limits.max_drawdown:
            score += 20 * (risk.max_drawdown / limits.max_drawdown - 1)

        # Daily loss risk
        if limits.daily_loss_limit and daily_pnl < -limits.daily_loss_limit:
            score += 25 * (abs(daily_pnl) / limits.daily_loss_limit - 1)

        return min(100, max(0, score))

    def _get_risk_level(self, risk_score: float) -> str:
        """獲取風險等級"""
        if risk_score > 70:
            return "CRITICAL"
        elif risk_score > 50:
            return "HIGH"
        elif risk_score > 30:
            return "MEDIUM"
        else:
            return "LOW"

    async def _update_risk_metrics(self) -> None:
        """定期更新風險指標後台任務"""
        self.logger.info("Starting risk metrics updater...")

        while not self._shutdown_event.is_set():
            try:
                # Update risk for all portfolios
                # This would get all active portfolios
                # For now, just sleep
                await asyncio.sleep(self.risk_update_interval)

            except Exception as e:
                self.logger.error(f"Error updating risk metrics: {e}")
                await asyncio.sleep(self.risk_update_interval)

    async def _monitor_risk_alerts(self) -> None:
        """監控風險告警後台任務"""
        self.logger.info("Starting risk alert monitor...")

        while not self._shutdown_event.is_set():
            try:
                # Check for new alerts
                # This would scan all positions and portfolios
                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error monitoring risk alerts: {e}")
                await asyncio.sleep(10)

    async def _calculate_daily_pnl(self) -> None:
        """計算日盈虧後台任務"""
        self.logger.info("Starting daily P&L calculator...")

        while not self._shutdown_event.is_set():
            try:
                # Calculate daily P&L for each portfolio
                # This would run at market close
                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                self.logger.error(f"Error calculating daily P&L: {e}")
                await asyncio.sleep(3600)

    async def _cleanup_old_data(self) -> None:
        """清理舊數據後台任務"""
        self.logger.info("Starting data cleanup...")

        while not self._shutdown_event.is_set():
            try:
                # Clean up old price history
                cutoff_date = datetime.utcnow() - timedelta(days=365)
                for symbol in list(self.price_history.keys()):
                    self.price_history[symbol] = [
                        (date, price) for date, price in self.price_history[symbol]
                        if date > cutoff_date
                    ]

                # Clean up old alerts (keep last 1000)
                if len(self.alert_history) > 1000:
                    self.alert_history = self.alert_history[-1000:]

                await asyncio.sleep(86400)  # Cleanup daily

            except Exception as e:
                self.logger.error(f"Error in data cleanup: {e}")
                await asyncio.sleep(86400)

    def is_healthy(self) -> bool:
        """檢查管理器是否健康"""
        return True  # Would check various health metrics