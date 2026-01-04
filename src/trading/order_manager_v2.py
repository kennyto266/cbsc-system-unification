"""
Enhanced Order Manager v2.0
增強版訂單管理器

Provides comprehensive order lifecycle management with:
- Connection pooling
- Retry mechanisms with exponential backoff
- Comprehensive error handling
- Batch processing support
- Performance metrics
- Thread safety
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass
import json
from collections import defaultdict
import threading
import time
from contextlib import asynccontextmanager

from ..models.trading_models_v2 import (
    Order, OrderStatus, OrderType, OrderSide, Portfolio
)
from ..core.database import get_db_session
from .broker_adapter import BrokerAdapter, OrderResponse


class OrderPriority(str, Enum):
    """訂單優先級"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class OrderUpdate:
    """訂單更新"""
    order_id: UUID
    status: OrderStatus
    filled_quantity: Optional[Decimal] = None
    remaining_quantity: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    message: Optional[str] = None
    timestamp: datetime = None


@dataclass
class OrderMetrics:
    """訂單指標"""
    total_orders: int = 0
    successful_orders: int = 0
    failed_orders: int = 0
    retried_orders: int = 0
    average_execution_time_ms: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0
    last_update: datetime = None


class OrderManagerV2:
    """
    增強版訂單管理器

    負責管理訂單的完整生命週期，包括：
    - 訂單創建和驗證
    - 提交到券商
    - 狀態追蹤和更新
    - 重試邏輯
    - 批量操作
    - 性能監控
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("order_manager_v2")

        # Order tracking
        self.orders: Dict[UUID, Order] = {}
        self.order_status: Dict[UUID, OrderStatus] = {}
        self.broker_order_map: Dict[str, UUID] = {}  # broker_order_id -> order_id
        self.pending_orders: Dict[UUID, Order] = {}
        self.retry_counts: Dict[UUID, int] = defaultdict(int)
        self.order_timers: Dict[UUID, asyncio.Task] = {}

        # Thread safety
        self._lock = threading.RLock()
        self._async_lock = asyncio.Lock()

        # Connection pool for broker adapters
        self.adapter_pool: Dict[str, List[BrokerAdapter]] = {}
        self.pool_size = config.get('adapter_pool_size', 3)

        # Batch processing
        self.batch_queue = asyncio.Queue(maxsize=1000)
        self.batch_size = config.get('order_batch_size', 50)
        self.batch_timeout = config.get('batch_timeout', 0.5)  # seconds

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Metrics
        self.metrics = OrderMetrics()
        self.execution_times: List[float] = []

        # Rate limiting
        self.rate_limiters: Dict[str, asyncio.Semaphore] = {}
        self.default_rate_limit = config.get('default_rate_limit', 10)

    async def initialize(self) -> None:
        """初始化訂單管理器"""
        self.logger.info("Initializing enhanced order manager v2...")

        self._running = False
        self._shutdown_event.clear()

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._process_batch_queue()),
            asyncio.create_task(self._monitor_pending_orders()),
            asyncio.create_task(self._sync_with_database()),
            asyncio.create_task(self._update_metrics()),
            asyncio.create_task(self._cleanup_resources())
        ]

        self.logger.info("Enhanced order manager v2 initialized")

    async def shutdown(self) -> None:
        """關閉訂單管理器"""
        self.logger.info("Shutting down enhanced order manager v2...")

        self._running = False
        self._shutdown_event.set()

        # Cancel all order timers
        for timer in self.order_timers.values():
            timer.cancel()
        self.order_timers.clear()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Process remaining batched orders
        await self._process_remaining_batches()

        # Close adapter connections
        for adapters in self.adapter_pool.values():
            for adapter in adapters:
                await adapter.disconnect()

        self.logger.info("Enhanced order manager v2 shutdown complete")

    @asynccontextmanager
    async def get_adapter(self, broker_name: str) -> BrokerAdapter:
        """獲取券商適配器（從連接池）"""
        if broker_name not in self.adapter_pool:
            self.adapter_pool[broker_name] = []

        adapters = self.adapter_pool[broker_name]
        adapter = None

        # Try to get available adapter
        for a in adapters:
            if await a.is_connected():
                adapter = a
                break

        # If no available adapter, create new one
        if not adapter and len(adapters) < self.pool_size:
            # Create new adapter
            # This would get the broker config
            # adapter = await self._create_adapter(broker_name)
            # adapters.append(adapter)
            pass

        if not adapter:
            raise Exception(f"No available adapters for broker {broker_name}")

        try:
            yield adapter
        except Exception as e:
            self.logger.error(f"Error using adapter for {broker_name}: {e}")
            # Try to reconnect adapter
            await adapter._reconnect()
            raise

    async def create_order_from_signal(self, signal, session) -> Order:
        """從交易信號創建訂單"""
        start_time = time.perf_counter()

        order = Order(
            id=uuid4(),
            portfolio_id=session.portfolio_id if hasattr(session, 'portfolio_id') else uuid4(),
            broker_account_id=session.broker_id,
            symbol=signal.symbol,
            side=signal.side,
            order_type=signal.order_type,
            quantity=signal.quantity,
            price=signal.price,
            submitted_at=datetime.utcnow(),
            status=OrderStatus.PENDING
        )

        # Store in memory
        with self._lock:
            self.orders[order.id] = order
            self.order_status[order.id] = OrderStatus.PENDING

        # Save to database
        async with get_db_session() as db:
            db.add(order)
            await db.commit()

        # Update metrics
        execution_time = (time.perf_counter() - start_time) * 1000
        self._update_execution_time(execution_time)

        self.logger.info(f"Created order {order.id} for {signal.symbol}")
        return order

    async def submit_order(
        self,
        order: Order,
        broker_adapter: BrokerAdapter,
        priority: OrderPriority = OrderPriority.NORMAL
    ) -> bool:
        """提交訂單到券商"""
        start_time = time.perf_counter()

        try:
            # Validate order
            if not self._validate_order(order):
                await self._mark_order_failed(order, "Order validation failed")
                return False

            # Check retry limit
            max_retries = self.config.get('max_retries', 3)
            if self.retry_counts[order.id] >= max_retries:
                self.logger.error(f"Order {order.id} exceeded retry limit")
                await self._mark_order_failed(order, "Maximum retry limit exceeded")
                return False

            # Submit based on priority
            if priority in [OrderPriority.HIGH, OrderPriority.URGENT]:
                # Submit immediately
                success = await self._submit_single_order_with_retry(order, broker_adapter)
            else:
                # Add to batch queue
                await self.batch_queue.put((order, broker_adapter))
                success = True

            # Update metrics
            execution_time = (time.perf_counter() - start_time) * 1000
            self._update_execution_time(execution_time)

            return success

        except Exception as e:
            self.logger.error(f"Error submitting order {order.id}: {e}")
            self.metrics.failed_orders += 1
            return False

    async def submit_order_with_timeout(
        self,
        order: Order,
        broker_adapter: BrokerAdapter,
        timeout: float = 30.0
    ) -> Tuple[bool, Optional[str]]:
        """帶超時的訂單提交"""
        try:
            async with asyncio.timeout(timeout):
                success = await self.submit_order(order, broker_adapter)
                return success, None
        except asyncio.TimeoutError:
            self.logger.error(f"Order {order.id} submission timed out after {timeout}s")
            return False, "Submission timeout"
        except Exception as e:
            return False, str(e)

    async def _submit_single_order_with_retry(
        self,
        order: Order,
        broker_adapter: BrokerAdapter
    ) -> bool:
        """提交單個訂單（帶重試）"""
        retry_count = self.retry_counts[order.id]
        max_retries = self.config.get('max_retries', 3)
        base_delay = self.config.get('retry_base_delay', 1.0)

        while retry_count <= max_retries:
            try:
                # Update status to submitted
                await self._update_order_status(order.id, OrderStatus.SUBMITTED)

                # Submit to broker
                response = await broker_adapter.submit_order(order)

                if response.success:
                    # Update with broker response
                    order.broker_order_id = response.broker_order_id
                    order.submitted_at = datetime.utcnow()

                    # Map broker order ID to our order ID
                    if response.broker_order_id:
                        self.broker_order_map[response.broker_order_id] = order.id

                    # Update status
                    new_status = response.status or OrderStatus.SUBMITTED
                    await self._update_order_status(
                        order.id,
                        new_status,
                        response.filled_quantity,
                        order.remaining_quantity,
                        response.average_price,
                        response.message
                    )

                    # Update metrics
                    self.metrics.total_orders += 1
                    if response.filled_quantity and response.filled_quantity > 0:
                        self.metrics.successful_orders += 1

                    # Set timeout monitoring
                    if order.status == OrderStatus.SUBMITTED:
                        self._set_order_timeout_monitor(order, broker_adapter)

                    return True
                else:
                    # Failed to submit
                    retry_count += 1
                    self.retry_counts[order.id] = retry_count
                    self.metrics.retried_orders += 1

                    if retry_count <= max_retries:
                        # Exponential backoff
                        delay = base_delay * (2 ** (retry_count - 1))
                        self.logger.warning(
                            f"Order {order.id} failed, retry {retry_count}/{max_retries} in {delay}s"
                        )
                        await asyncio.sleep(delay)
                    else:
                        await self._mark_order_failed(order, response.message)
                        self.metrics.failed_orders += 1

            except Exception as e:
                self.logger.error(f"Error submitting order {order.id}: {e}")
                retry_count += 1
                self.retry_counts[order.id] = retry_count

                if retry_count <= max_retries:
                    delay = base_delay * (2 ** (retry_count - 1))
                    await asyncio.sleep(delay)

        return False

    async def cancel_order(
        self,
        order_id: UUID,
        broker_adapter: BrokerAdapter,
        reason: str = "User request"
    ) -> bool:
        """取消訂單"""
        try:
            with self._lock:
                order = self.orders.get(order_id)
                if not order:
                    self.logger.warning(f"Order {order_id} not found")
                    return False

            # Check if order can be cancelled
            if order.status not in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                self.logger.warning(f"Cannot cancel order {order_id} in status {order.status}")
                return False

            # Cancel timeout monitor
            if order_id in self.order_timers:
                self.order_timers[order_id].cancel()
                del self.order_timers[order_id]

            # Cancel with broker
            if order.broker_order_id:
                success = await broker_adapter.cancel_order(order.broker_order_id)
            else:
                success = True  # Not yet submitted to broker

            if success:
                # Update order status
                await self._update_order_status(
                    order_id,
                    OrderStatus.CANCELLED,
                    message=reason
                )

                self.logger.info(f"Cancelled order {order_id}")
                return True
            else:
                self.logger.error(f"Failed to cancel order {order_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    async def cancel_all_orders(
        self,
        portfolio_id: Optional[UUID] = None,
        broker_adapter: Optional[BrokerAdapter] = None,
        emergency: bool = False
    ) -> int:
        """取消所有訂單"""
        cancelled_count = 0

        try:
            async with self._async_lock:
                orders_to_cancel = []

                for order_id, order in self.orders.items():
                    # Filter by portfolio if specified
                    if portfolio_id and order.portfolio_id != portfolio_id:
                        continue

                    # Check if order can be cancelled
                    if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                        orders_to_cancel.append(order)

                # Cancel all timeout monitors
                for order_id in [o.id for o in orders_to_cancel]:
                    if order_id in self.order_timers:
                        self.order_timers[order_id].cancel()
                        del self.order_timers[order_id]

                # Cancel orders
                if emergency and broker_adapter:
                    # Cancel all at once if possible
                    cancelled_count = await self._emergency_cancel_all(
                        orders_to_cancel,
                        broker_adapter
                    )
                else:
                    # Cancel concurrently
                    tasks = []
                    for order in orders_to_cancel:
                        task = self.cancel_order(
                            order.id,
                            broker_adapter,
                            reason="Bulk cancellation"
                        )
                        tasks.append(task)

                    if tasks:
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        cancelled_count = sum(1 for r in results if r is True)

            self.logger.info(f"Cancelled {cancelled_count} orders")
            return cancelled_count

        except Exception as e:
            self.logger.error(f"Error cancelling all orders: {e}")
            return cancelled_count

    async def get_order_status(self, order_id: UUID) -> Optional[OrderStatus]:
        """獲取訂單狀態"""
        with self._lock:
            return self.order_status.get(order_id)

    async def get_orders_by_status(
        self,
        status: OrderStatus,
        portfolio_id: Optional[UUID] = None
    ) -> List[Order]:
        """根據狀態獲取訂單列表"""
        orders = []

        with self._lock:
            for order in self.orders.values():
                if order.status == status:
                    if portfolio_id is None or order.portfolio_id == portfolio_id:
                        orders.append(order)

        return orders

    async def get_pending_orders(self, portfolio_id: Optional[UUID] = None) -> List[Order]:
        """獲取待處理訂單"""
        return await self.get_orders_by_status(OrderStatus.PENDING, portfolio_id)

    async def update_order_from_broker(
        self,
        broker_order_id: str,
        update: OrderUpdate
    ) -> bool:
        """根據券商更新更新訂單"""
        try:
            # Find order
            order_id = self.broker_order_map.get(broker_order_id)
            if not order_id:
                self.logger.warning(f"Broker order {broker_order_id} not found")
                return False

            # Cancel timeout monitor if order is complete
            if update.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                if order_id in self.order_timers:
                    self.order_timers[order_id].cancel()
                    del self.order_timers[order_id]

            # Update order
            await self._update_order_status(
                order_id,
                update.status,
                update.filled_quantity,
                update.remaining_quantity,
                update.average_price,
                update.message
            )

            return True

        except Exception as e:
            self.logger.error(f"Error updating order from broker: {e}")
            return False

    def _validate_order(self, order: Order) -> bool:
        """驗證訂單"""
        # Check basic fields
        if not order.symbol or not order.side or not order.order_type:
            self.logger.error(f"Invalid order: missing required fields")
            return False

        if order.quantity <= 0:
            self.logger.error(f"Invalid order: quantity must be positive")
            return False

        if order.order_type == OrderType.LIMIT and not order.price:
            self.logger.error(f"Invalid order: limit order must have price")
            return False

        # Check order size limits
        max_order_size = self.config.get('max_order_size', 1000000)
        if order.quantity > max_order_size:
            self.logger.error(f"Invalid order: quantity exceeds limit {max_order_size}")
            return False

        # Check for duplicate orders
        with self._lock:
            for existing_order in self.orders.values():
                if (existing_order.symbol == order.symbol and
                    existing_order.side == order.side and
                    existing_order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]):
                    # Potential duplicate
                    time_diff = abs((order.submitted_at - existing_order.submitted_at).total_seconds())
                    if time_diff < 1.0:  # Within 1 second
                        self.logger.warning(f"Potential duplicate order detected: {order.id}")
                        return False

        return True

    async def _update_order_status(
        self,
        order_id: UUID,
        status: OrderStatus,
        filled_quantity: Optional[Decimal] = None,
        remaining_quantity: Optional[Decimal] = None,
        average_price: Optional[Decimal] = None,
        message: Optional[str] = None
    ) -> None:
        """更新訂單狀態"""
        async with self._async_lock:
            order = self.orders.get(order_id)
            if not order:
                return

            # Update order
            order.status = status
            self.order_status[order_id] = status

            if filled_quantity is not None:
                order.filled_quantity = filled_quantity

            if remaining_quantity is not None:
                order.remaining_quantity = remaining_quantity

            if average_price is not None:
                order.average_fill_price = average_price

            # Update timestamps
            if status == OrderStatus.FILLED:
                order.filled_at = datetime.utcnow()
            elif status == OrderStatus.CANCELLED:
                order.cancelled_at = datetime.utcnow()

            # Remove from pending if completed
            if status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                self.pending_orders.pop(order_id, None)
                self.retry_counts.pop(order_id, None)

            # Save to database
            async with get_db_session() as db:
                db.add(order)
                await db.commit()

            # Log update
            self.logger.info(f"Updated order {order_id} to {status.value}")

    async def _mark_order_failed(self, order: Order, message: str) -> None:
        """標記訂單失敗"""
        await self._update_order_status(
            order.id,
            OrderStatus.REJECTED,
            message=message
        )

        self.metrics.failed_orders += 1
        self.logger.error(f"Order {order.id} failed: {message}")

    def _set_order_timeout_monitor(self, order: Order, broker_adapter: BrokerAdapter) -> None:
        """設置訂單超時監控"""
        timeout_seconds = self.config.get('order_timeout_seconds', 300)  # 5 minutes default

        async def check_order_timeout():
            try:
                await asyncio.sleep(timeout_seconds)

                # Check if order still exists and is pending
                if order.id in self.orders and order.status == OrderStatus.SUBMITTED:
                    self.logger.warning(f"Order {order.id} timed out, checking status...")

                    # Get current status from broker
                    if order.broker_order_id:
                        status = await broker_adapter.get_order_status(order.broker_order_id)
                        if status and status != order.status:
                            await self._update_order_status(order.id, status)
                        else:
                            # Still pending, consider cancelling
                            await self.cancel_order(
                                order.id,
                                broker_adapter,
                                reason="Order timeout"
                            )

            except asyncio.CancelledError:
                pass
            except Exception as e:
                self.logger.error(f"Error in order timeout monitor: {e}")

        # Create and store task
        task = asyncio.create_task(check_order_timeout())
        self.order_timers[order.id] = task

    def _update_execution_time(self, execution_time: float) -> None:
        """更新執行時間統計"""
        self.execution_times.append(execution_time)

        # Keep only last 1000 execution times
        if len(self.execution_times) > 1000:
            self.execution_times = self.execution_times[-1000:]

        # Update average
        self.metrics.average_execution_time_ms = sum(self.execution_times) / len(self.execution_times)

    async def _process_batch_queue(self) -> None:
        """處理批量訂單隊列"""
        self.logger.info("Starting batch order processor...")

        while not self._shutdown_event.is_set():
            try:
                # Collect batch
                batch = []
                deadline = asyncio.get_event_loop().time() + self.batch_timeout

                while len(batch) < self.batch_size:
                    timeout = max(0, deadline - asyncio.get_event_loop().time())
                    try:
                        item = await asyncio.wait_for(
                            self.batch_queue.get(),
                            timeout=timeout
                        )
                        if item is None:  # Shutdown signal
                            break
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break

                # Process batch if not empty
                if batch:
                    await self._process_order_batch(batch)

            except Exception as e:
                self.logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(1)

    async def _process_order_batch(self, batch: List[Tuple[Order, BrokerAdapter]]) -> None:
        """處理訂單批次"""
        # Process concurrently within the batch
        tasks = []
        for order, adapter in batch:
            task = self._submit_single_order_with_retry(order, adapter)
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results
        success_count = sum(1 for r in results if r is True)
        self.logger.info(f"Processed batch of {len(batch)} orders, {success_count} successful")

    async def _monitor_pending_orders(self) -> None:
        """監控待處理訂單"""
        self.logger.info("Starting pending order monitor...")

        while not self._shutdown_event.is_set():
            try:
                async with self._async_lock:
                    # Check for stale pending orders
                    stale_threshold = datetime.utcnow() - timedelta(
                        seconds=self.config.get('stale_order_timeout', 300)
                    )

                    for order_id, order in list(self.pending_orders.items()):
                        if order.submitted_at and order.submitted_at < stale_threshold:
                            self.logger.warning(f"Found stale order {order_id}")
                            # Could trigger retry or cancellation here

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Error monitoring pending orders: {e}")
                await asyncio.sleep(30)

    async def _sync_with_database(self) -> None:
        """與數據庫同步"""
        self.logger.info("Starting database sync...")

        while not self._shutdown_event.is_set():
            try:
                # Load any new orders from database
                async with get_db_session() as db:
                    # Query recent orders not in memory
                    # This is a simplified version
                    pass

                await asyncio.sleep(60)  # Sync every minute

            except Exception as e:
                self.logger.error(f"Error syncing with database: {e}")
                await asyncio.sleep(60)

    async def _update_metrics(self) -> None:
        """更新指標"""
        self.logger.info("Starting metrics updater...")

        while not self._shutdown_event.is_set():
            try:
                # Update rates
                total = self.metrics.total_orders
                if total > 0:
                    self.metrics.success_rate = self.metrics.successful_orders / total
                    self.metrics.error_rate = self.metrics.failed_orders / total

                self.metrics.last_update = datetime.utcnow()

                await asyncio.sleep(10)  # Update every 10 seconds

            except Exception as e:
                self.logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(10)

    async def _cleanup_resources(self) -> None:
        """清理資源"""
        self.logger.info("Starting resource cleanup...")

        while not self._shutdown_event.is_set():
            try:
                # Clean up completed timers
                completed_timers = [
                    order_id for order_id, task in self.order_timers.items()
                    if task.done()
                ]
                for order_id in completed_timers:
                    del self.order_timers[order_id]

                # Clean up old execution times
                if len(self.execution_times) > 10000:
                    self.execution_times = self.execution_times[-5000:]

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in resource cleanup: {e}")
                await asyncio.sleep(300)

    async def _process_remaining_batches(self) -> None:
        """處理剩餘的批量訂單"""
        # Process all remaining orders in batch queue
        remaining_items = []

        while not self.batch_queue.empty():
            try:
                item = self.batch_queue.get_nowait()
                if item is not None:
                    remaining_items.append(item)
            except asyncio.QueueEmpty:
                break

        if remaining_items:
            await self._process_order_batch(remaining_items)

    async def _emergency_cancel_all(
        self,
        orders: List[Order],
        broker_adapter: BrokerAdapter
    ) -> int:
        """緊急取消所有訂單"""
        cancelled = 0

        # Cancel all as quickly as possible
        tasks = []
        for order in orders:
            if order.broker_order_id:
                task = broker_adapter.cancel_order(order.broker_order_id)
                tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, bool) and result:
                    cancelled += 1
                    await self._update_order_status(
                        orders[i].id,
                        OrderStatus.CANCELLED,
                        message="Emergency cancellation"
                    )

        return cancelled

    def is_healthy(self) -> bool:
        """檢查管理器是否健康"""
        # Check if background tasks are running
        if not self._running:
            return False

        # Check error rates
        if self.metrics.total_orders > 0:
            error_rate = self.metrics.error_rate
            if error_rate > 0.1:  # More than 10% error rate
                return False

        # Check pending order count
        if len(self.pending_orders) > 1000:  # Too many pending orders
            return False

        return True

    def get_metrics(self) -> OrderMetrics:
        """獲取管理器指標"""
        # Update rates before returning
        total = self.metrics.total_orders
        if total > 0:
            self.metrics.success_rate = self.metrics.successful_orders / total
            self.metrics.error_rate = self.metrics.failed_orders / total

        return self.metrics

    def get_detailed_metrics(self) -> Dict[str, Any]:
        """獲取詳細指標"""
        return {
            'orders': {
                'total': self.metrics.total_orders,
                'successful': self.metrics.successful_orders,
                'failed': self.metrics.failed_orders,
                'retried': self.metrics.retried_orders,
                'pending': len(self.pending_orders),
                'with_timers': len(self.order_timers)
            },
            'performance': {
                'average_execution_time_ms': self.metrics.average_execution_time_ms,
                'success_rate': self.metrics.success_rate,
                'error_rate': self.metrics.error_rate,
                'last_update': self.metrics.last_update.isoformat() if self.metrics.last_update else None
            },
            'resources': {
                'adapter_pools': {
                    name: len(adapters) for name, adapters in self.adapter_pool.items()
                },
                'execution_times_sample_size': len(self.execution_times)
            }
        }