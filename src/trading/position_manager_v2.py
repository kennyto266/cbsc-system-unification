"""
Enhanced Position Manager v2.0
增強版倉位管理器

Manages portfolio positions with real-time updates, risk calculations,
and automatic position reconciliation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from uuid import UUID
from enum import Enum
from dataclasses import dataclass, field
import threading
from collections import defaultdict

from ..models.trading_models_v2 import (
    Position, PositionStatus, Order, Portfolio
)
from ..core.database import get_db_session
from .broker_adapter import BrokerAdapter, PositionInfo


class PositionSide(str, Enum):
    """倉位方向"""
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


@dataclass
class PositionUpdate:
    """倉位更新"""
    symbol: str
    quantity: Decimal
    price: Optional[Decimal] = None
    side: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RiskMetrics:
    """風險指標"""
    var_95: Optional[Decimal] = None  # Value at Risk 95%
    max_drawdown: Optional[Decimal] = None
    sharpe_ratio: Optional[float] = None
    volatility: Optional[float] = None
    beta: Optional[float] = None
    correlation: Dict[str, float] = field(default_factory=dict)
    sector_exposure: Dict[str, Decimal] = field(default_factory=dict)


class PositionManagerV2:
    """
    增強版倉位管理器

    負責：
    - 實時倉位追蹤
    - 自動倉位對賬
    - 風險計算
    - 市值更新
    - 倉位優化建議
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("position_manager_v2")

        # Position tracking
        self.positions: Dict[UUID, Position] = {}
        self.position_by_symbol: Dict[str, List[Position]] = defaultdict(list)
        self.portfolio_positions: Dict[UUID, Dict[str, Position]] = defaultdict(dict)

        # Market data cache
        self.market_prices: Dict[str, Decimal] = {}
        self.price_history: Dict[str, List[Tuple[datetime, Decimal]]] = defaultdict(list)

        # Thread safety
        self._lock = threading.RLock()
        self._async_lock = asyncio.Lock()

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Risk metrics cache
        self.risk_metrics: Dict[UUID, RiskMetrics] = {}
        self.risk_update_interval = config.get('risk_update_interval', 300)  # 5 minutes

        # Position reconciliation
        self.last_reconciliation: Dict[UUID, datetime] = {}
        self.reconciliation_interval = config.get('reconciliation_interval', 60)  # 1 minute

        # Metrics
        self.update_count = 0
        self.error_count = 0
        self.reconciliation_count = 0

    async def initialize(self) -> None:
        """初始化倉位管理器"""
        self.logger.info("Initializing enhanced position manager v2...")

        self._running = False
        self._shutdown_event.clear()

        # Load existing positions from database
        await self._load_positions_from_db()

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._update_market_values()),
            asyncio.create_task(self._reconcile_positions()),
            asyncio.create_task(self._calculate_risk_metrics()),
            asyncio.create_task(self._cleanup_old_data())
        ]

        self.logger.info("Enhanced position manager v2 initialized")

    async def shutdown(self) -> None:
        """關閉倉位管理器"""
        self.logger.info("Shutting down enhanced position manager v2...")

        self._running = False
        self._shutdown_event.set()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Save final state
        await self._save_positions_to_db()

        self.logger.info("Enhanced position manager v2 shutdown complete")

    async def initialize_positions(self, portfolio) -> None:
        """初始化投資組合倉位"""
        try:
            # Load positions for this portfolio
            async with get_db_session() as db:
                positions = await db.query(Position).filter(
                    Position.portfolio_id == portfolio.id,
                    Position.status == PositionStatus.OPEN
                ).all()

                for position in positions:
                    await self._add_position_to_memory(position)

            self.logger.info(f"Initialized {len(positions)} positions for portfolio {portfolio.id}")

        except Exception as e:
            self.logger.error(f"Error initializing positions: {e}")

    async def update_positions(self, order: Order, execution_result) -> None:
        """根據訂單執行結果更新倉位"""
        try:
            if not execution_result.success:
                return

            symbol = order.symbol
            executed_quantity = execution_result.executed_quantity
            average_price = execution_result.average_price

            # Create position update
            update = PositionUpdate(
                symbol=symbol,
                quantity=executed_quantity,
                price=average_price,
                side=order.side
            )

            # Apply update
            await self._apply_position_update(order.portfolio_id, update)

            self.update_count += 1

        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
            self.error_count += 1

    async def update_market_values(self, portfolio) -> None:
        """更新投資組合倉位市值"""
        try:
            positions = await self.get_positions(portfolio)

            for position in positions:
                if position.status == PositionStatus.OPEN:
                    # Get current market price
                    current_price = await self._get_market_price(position.symbol)
                    if current_price:
                        position.current_price = current_price
                        position.market_value = abs(position.quantity) * current_price

                        # Calculate unrealized P&L
                        if position.side == 'LONG':
                            position.unrealized_pnl = (
                                (current_price - position.entry_price) * position.quantity
                            )
                        else:
                            position.unrealized_pnl = (
                                (position.entry_price - current_price) * abs(position.quantity)
                            )

                        position.unrealized_pnl_percent = (
                            position.unrealized_pnl / (position.total_cost or 1) * 100
                        )

            # Save updated positions
            async with get_db_session() as db:
                for position in positions:
                    db.add(position)
                await db.commit()

        except Exception as e:
            self.logger.error(f"Error updating market values: {e}")

    async def close_position(
        self,
        portfolio_id: UUID,
        symbol: str,
        reason: str = "Manual close"
    ) -> bool:
        """關閉指定倉位"""
        try:
            positions = self.portfolio_positions.get(portfolio_id, {}).get(symbol, [])

            if not positions:
                self.logger.warning(f"No position found for {symbol} in portfolio {portfolio_id}")
                return False

            # Mark all positions as closed
            for position in positions:
                position.status = PositionStatus.CLOSED
                position.closed_at = datetime.utcnow()
                position.exit_reason = reason

            # Update memory
            del self.portfolio_positions[portfolio_id][symbol]

            # Save to database
            async with get_db_session() as db:
                for position in positions:
                    db.add(position)
                await db.commit()

            self.logger.info(f"Closed position for {symbol} in portfolio {portfolio_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False

    async def close_all_positions(
        self,
        portfolio,
        emergency: bool = False
    ) -> int:
        """關閉所有倉位"""
        closed_count = 0

        try:
            positions = await self.get_positions(portfolio)

            for position in positions:
                if position.status == PositionStatus.OPEN:
                    reason = "Emergency close" if emergency else "Bulk close"
                    if await self.close_position(portfolio.id, position.symbol, reason):
                        closed_count += 1

            self.logger.info(f"Closed {closed_count} positions for portfolio {portfolio.id}")
            return closed_count

        except Exception as e:
            self.logger.error(f"Error closing all positions: {e}")
            return closed_count

    async def get_positions(self, portfolio) -> List[Position]:
        """獲取投資組合所有倉位"""
        portfolio_id = portfolio.id if isinstance(portfolio, Portfolio) else portfolio
        return list(self.portfolio_positions.get(portfolio_id, {}).values())

    async def get_position(self, portfolio_id: UUID, symbol: str) -> Optional[Position]:
        """獲取指定倉位"""
        positions = self.portfolio_positions.get(portfolio_id, {})
        return positions.get(symbol)

    async def get_portfolio_value(self, portfolio) -> Decimal:
        """獲取投資組合總市值"""
        try:
            positions = await self.get_positions(portfolio)
            total_value = sum(
                position.market_value for position in positions
                if position.market_value
            )
            return total_value or Decimal('0')
        except Exception as e:
            self.logger.error(f"Error calculating portfolio value: {e}")
            return Decimal('0')

    async def get_total_pnl(self, portfolio) -> Dict[str, Decimal]:
        """獲取總盈虧"""
        try:
            positions = await self.get_positions(portfolio)

            unrealized_pnl = sum(
                position.unrealized_pnl for position in positions
                if position.unrealized_pnl
            )

            realized_pnl = sum(
                position.realized_pnl for position in positions
                if position.realized_pnl
            )

            total_pnl = unrealized_pnl + realized_pnl

            return {
                'unrealized_pnl': unrealized_pnl or Decimal('0'),
                'realized_pnl': realized_pnl or Decimal('0'),
                'total_pnl': total_pnl or Decimal('0')
            }
        except Exception as e:
            self.logger.error(f"Error calculating total PnL: {e}")
            return {
                'unrealized_pnl': Decimal('0'),
                'realized_pnl': Decimal('0'),
                'total_pnl': Decimal('0')
            }

    async def get_risk_metrics(self, portfolio) -> RiskMetrics:
        """獲取投資組合風險指標"""
        portfolio_id = portfolio.id if isinstance(portfolio, Portfolio) else portfolio

        # Return cached metrics if available and recent
        cached = self.risk_metrics.get(portfolio_id)
        if cached:
            return cached

        # Calculate new metrics
        metrics = await self._calculate_portfolio_risk_metrics(portfolio_id)
        self.risk_metrics[portfolio_id] = metrics

        return metrics

    async def get_position_concentration(self, portfolio) -> Dict[str, float]:
        """獲取倉位集中度"""
        try:
            positions = await self.get_positions(portfolio)
            total_value = await self.get_portfolio_value(portfolio)

            if total_value == 0:
                return {}

            concentration = {}
            for position in positions:
                if position.market_value:
                    concentration[position.symbol] = float(
                        position.market_value / total_value
                    )

            return concentration
        except Exception as e:
            self.logger.error(f"Error calculating position concentration: {e}")
            return {}

    async def reconcile_with_broker(
        self,
        portfolio,
        broker_adapter: BrokerAdapter
    ) -> Tuple[int, int]:
        """與券商對賬倉位"""
        matched = 0
        mismatches = 0

        try:
            # Get positions from broker
            broker_positions = await broker_adapter.get_positions()
            broker_position_map = {
                pos.symbol: pos for pos in broker_positions
            }

            # Get our positions
            our_positions = await self.get_positions(portfolio)
            our_position_map = {
                pos.symbol: pos for pos in our_positions
            }

            # Reconcile
            for symbol, broker_pos in broker_position_map.items():
                our_pos = our_position_map.get(symbol)

                if our_pos:
                    # Compare positions
                    if abs(our_pos.quantity - broker_pos.quantity) < Decimal('0.0001'):
                        matched += 1
                    else:
                        mismatches += 1
                        self.logger.warning(
                            f"Position mismatch for {symbol}: "
                            f"Our={our_pos.quantity}, Broker={broker_pos.quantity}"
                        )
                else:
                    # Broker has position we don't
                    mismatches += 1
                    self.logger.warning(f"Missing position for {symbol}")

            # Check for positions we have but broker doesn't
            for symbol in our_position_map:
                if symbol not in broker_position_map:
                    mismatches += 1
                    self.logger.warning(f"Extra position for {symbol}")

            self.last_reconciliation[portfolio.id] = datetime.utcnow()
            self.reconciliation_count += 1

            self.logger.info(
                f"Reconciliation for portfolio {portfolio.id}: "
                f"Matched={matched}, Mismatches={mismatches}"
            )

        except Exception as e:
            self.logger.error(f"Error reconciling positions: {e}")

        return matched, mismatches

    async def _apply_position_update(self, portfolio_id: UUID, update: PositionUpdate) -> None:
        """應用倉位更新"""
        async with self._async_lock:
            # Get existing position
            positions = self.portfolio_positions.get(portfolio_id, {})
            position = positions.get(update.symbol)

            if not position:
                # Create new position
                position = Position(
                    id=uuid4(),
                    portfolio_id=portfolio_id,
                    symbol=update.symbol,
                    quantity=update.quantity,
                    entry_price=update.price or Decimal('0'),
                    current_price=update.price or Decimal('0'),
                    market_value=update.quantity * (update.price or Decimal('0')),
                    side='LONG' if update.quantity > 0 else 'SHORT',
                    status=PositionStatus.OPEN,
                    opened_at=datetime.utcnow()
                )

                position.total_cost = position.quantity * position.entry_price
                position.average_cost = position.entry_price
                position.commission_paid = Decimal('0')

            else:
                # Update existing position
                if update.side == 'BUY':
                    # Adding to position
                    old_quantity = position.quantity
                    old_cost = position.total_cost or Decimal('0')

                    new_quantity = old_quantity + update.quantity
                    new_cost = old_cost + (update.quantity * update.price)

                    position.quantity = new_quantity
                    position.total_cost = new_cost
                    position.average_cost = new_cost / new_quantity if new_quantity != 0 else Decimal('0')
                    position.entry_price = position.average_cost

                elif update.side == 'SELL':
                    # Reducing position
                    old_quantity = position.quantity
                    realized_pnl = Decimal('0')

                    if old_quantity > 0:  # Long position
                        realized_pnl = (update.price - position.average_cost) * update.quantity
                    else:  # Short position
                        realized_pnl = (position.average_cost - update.price) * update.quantity

                    position.quantity += update.quantity  # update.quantity is negative for sells
                    position.realized_pnl = (position.realized_pnl or Decimal('0')) + realized_pnl

                    # Check if position is closed
                    if abs(position.quantity) < Decimal('0.0001'):
                        position.status = PositionStatus.CLOSED
                        position.closed_at = datetime.utcnow()

                # Update current price and market value
                position.current_price = update.price or position.current_price
                if position.current_price:
                    position.market_value = abs(position.quantity) * position.current_price

            # Store position
            positions[update.symbol] = position
            self.portfolio_positions[portfolio_id] = positions

            # Also store in main positions dict
            self.positions[position.id] = position

            # Save to database
            async with get_db_session() as db:
                db.add(position)
                await db.commit()

    async def _get_market_price(self, symbol: str) -> Optional[Decimal]:
        """獲取市場價格"""
        # Check cache first
        if symbol in self.market_prices:
            # Check if price is recent (within last 5 seconds)
            last_update = self.price_history.get(symbol, [])
            if last_update:
                last_time = last_update[-1][0]
                if (datetime.utcnow() - last_time).total_seconds() < 5:
                    return self.market_prices[symbol]

        # This would typically fetch from market data service
        # For now, return cached price or None
        return self.market_prices.get(symbol)

    async def _add_position_to_memory(self, position: Position) -> None:
        """添加倉位到內存"""
        with self._lock:
            self.positions[position.id] = position

            portfolio_positions = self.portfolio_positions[position.portfolio_id]
            portfolio_positions[position.symbol] = position

    async def _load_positions_from_db(self) -> None:
        """從數據庫加載倉位"""
        try:
            async with get_db_session() as db:
                # Load open positions
                positions = await db.query(Position).filter(
                    Position.status == PositionStatus.OPEN
                ).all()

                for position in positions:
                    await self._add_position_to_memory(position)

            self.logger.info(f"Loaded {len(positions)} positions from database")

        except Exception as e:
            self.logger.error(f"Error loading positions from database: {e}")

    async def _save_positions_to_db(self) -> None:
        """保存倉位到數據庫"""
        try:
            async with get_db_session() as db:
                for position in self.positions.values():
                    db.add(position)
                await db.commit()

            self.logger.info(f"Saved {len(self.positions)} positions to database")

        except Exception as e:
            self.logger.error(f"Error saving positions to database: {e}")

    async def _update_market_values(self) -> None:
        """定期更新市值後台任務"""
        self.logger.info("Starting market value updater...")

        while not self._shutdown_event.is_set():
            try:
                # Update all portfolio positions
                for portfolio_id in list(self.portfolio_positions.keys()):
                    # This would get the portfolio object
                    # For now, we'll use the ID directly
                    await self.update_market_values(portfolio_id)

                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                self.logger.error(f"Error in market value updater: {e}")
                await asyncio.sleep(5)

    async def _reconcile_positions(self) -> None:
        """定期對賬後台任務"""
        self.logger.info("Starting position reconciler...")

        while not self._shutdown_event.is_set():
            try:
                # This would get broker adapters for each portfolio
                # For now, just log reconciliation attempts
                for portfolio_id in list(self.portfolio_positions.keys()):
                    last_reconcile = self.last_reconciliation.get(portfolio_id)
                    if not last_reconcile or \
                       (datetime.utcnow() - last_reconcile).total_seconds() > self.reconciliation_interval:
                        # Would reconcile with broker here
                        pass

                await asyncio.sleep(self.reconciliation_interval)

            except Exception as e:
                self.logger.error(f"Error in position reconciler: {e}")
                await asyncio.sleep(self.reconciliation_interval)

    async def _calculate_risk_metrics(self) -> None:
        """定期計算風險指標後台任務"""
        self.logger.info("Starting risk metrics calculator...")

        while not self._shutdown_event.is_set():
            try:
                for portfolio_id in list(self.portfolio_positions.keys()):
                    # Calculate risk metrics
                    await self._calculate_portfolio_risk_metrics(portfolio_id)

                await asyncio.sleep(self.risk_update_interval)

            except Exception as e:
                self.logger.error(f"Error in risk metrics calculator: {e}")
                await asyncio.sleep(self.risk_update_interval)

    async def _calculate_portfolio_risk_metrics(self, portfolio_id: UUID) -> RiskMetrics:
        """計算投資組合風險指標"""
        try:
            positions = list(self.portfolio_positions.get(portfolio_id, {}).values())

            if not positions:
                return RiskMetrics()

            # Calculate basic metrics
            total_value = sum(
                pos.market_value for pos in positions if pos.market_value
            )

            # Calculate portfolio volatility (simplified)
            returns = []
            for position in positions:
                if position.unrealized_pnl_percent:
                    returns.append(float(position.unrealized_pnl_percent))

            volatility = None
            if len(returns) > 1:
                mean_return = sum(returns) / len(returns)
                variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
                volatility = variance ** 0.5

            # Calculate concentration risk
            concentration_risk = 0
            for position in positions:
                if position.market_value and total_value > 0:
                    weight = position.market_value / total_value
                    concentration_risk += weight ** 2

            # Calculate Sharpe ratio (simplified, assuming risk-free rate = 0)
            total_pnl = sum(
                pos.unrealized_pnl or Decimal('0') + (pos.realized_pnl or Decimal('0'))
                for pos in positions
            )
            sharpe_ratio = None
            if volatility and volatility > 0:
                sharpe_ratio = float(total_pnl) / volatility

            metrics = RiskMetrics(
                volatility=volatility,
                sharpe_ratio=sharpe_ratio
            )

            # Add sector exposure if available
            # This would typically map symbols to sectors
            metrics.sector_exposure = {}  # Would be populated

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics()

    async def _cleanup_old_data(self) -> None:
        """清理舊數據後台任務"""
        self.logger.info("Starting data cleanup...")

        while not self._shutdown_event.is_set():
            try:
                # Clean up old price history (keep last 1000 points per symbol)
                for symbol in list(self.price_history.keys()):
                    history = self.price_history[symbol]
                    if len(history) > 1000:
                        self.price_history[symbol] = history[-1000:]

                # Clean up old risk metrics (keep for 1 hour)
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                for portfolio_id in list(self.risk_metrics.keys()):
                    last_reconcile = self.last_reconciliation.get(portfolio_id)
                    if last_reconcile and last_reconcile < cutoff_time:
                        del self.risk_metrics[portfolio_id]

                await asyncio.sleep(3600)  # Cleanup every hour

            except Exception as e:
                self.logger.error(f"Error in data cleanup: {e}")
                await asyncio.sleep(3600)

    def is_healthy(self) -> bool:
        """檢查管理器是否健康"""
        # Check error rate
        if self.update_count > 0:
            error_rate = self.error_count / self.update_count
            if error_rate > 0.05:  # More than 5% error rate
                return False

        return True

    def get_metrics(self) -> Dict[str, Any]:
        """獲取管理器指標"""
        return {
            'positions_tracked': len(self.positions),
            'portfolios': len(self.portfolio_positions),
            'update_count': self.update_count,
            'error_count': self.error_count,
            'reconciliation_count': self.reconciliation_count,
            'market_prices_cached': len(self.market_prices),
            'error_rate': self.error_count / max(1, self.update_count)
        }