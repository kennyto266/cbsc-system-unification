"""
Execution Service Module
執行服務模塊

Handles order execution with intelligent routing,
optimization strategies, and comprehensive monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from uuid import UUID
from enum import Enum
from dataclasses import dataclass, field
import time
import statistics

from ..models.trading_models_v2 import (
    Order, OrderStatus, OrderType, OrderSide
)
from .broker_adapter import BrokerAdapter, OrderResponse


@dataclass
class ExecutionResult:
    """執行結果"""
    success: bool
    order_id: Optional[UUID] = None
    broker_order_id: Optional[str] = None
    executed_quantity: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    commission: Optional[Decimal] = None


class ExecutionAlgorithm(str, Enum):
    """執行算法"""
    MARKET = "market"
    LIMIT = "limit"
    TWAP = "twap"  # Time-Weighted Average Price
    VWAP = "vwap"  # Volume-Weighted Average Price
    POV = "pov"    # Percentage of Volume
    ICEBERG = "iceberg"
    PEG = "peg"


class ExecutionPriority(str, Enum):
    """執行優先級"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ExecutionParams:
    """執行參數"""
    algorithm: ExecutionAlgorithm = ExecutionAlgorithm.MARKET
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    max_participation_rate: Optional[float] = None  # For POV algorithm
    time_limit: Optional[int] = None  # In seconds
    price_tolerance: Optional[float] = None  # Price tolerance percentage
    min_fill_size: Optional[Decimal] = None
    max_fill_size: Optional[Decimal] = None
    slice_count: Optional[int] = None  # For algorithmic execution
    slice_interval: Optional[float] = None  # Seconds between slices


@dataclass
class ExecutionReport:
    """執行報告"""
    order_id: UUID
    algorithm: ExecutionAlgorithm
    start_time: datetime
    end_time: datetime
    total_quantity: Decimal
    filled_quantity: Decimal
    average_price: Optional[Decimal]
    vwap: Optional[Decimal]
    twap: Optional[Decimal]
    slippage: Optional[float]
    commission: Optional[Decimal]
    slices: List[Dict] = field(default_factory=list)
    efficiency_score: Optional[float] = None


@dataclass
class LiquidityAnalysis:
    """流動性分析"""
    symbol: str
    bid_ask_spread: Optional[float]
    average_volume: Optional[float]
    depth: Dict[float, Decimal] = field(default_factory=dict)
    impact_factor: Optional[float]
    optimal_size: Optional[Decimal]


class ExecutionService:
    """
    執行服務

    負責：
    - 智能訂單路由
    - 算法交易執行
    - 滑點控制
    - 流動性分析
    - 執行優化
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("execution_service")

        # Execution tracking
        self.active_orders: Dict[UUID, Order] = {}
        self.execution_reports: Dict[UUID, ExecutionReport] = {}
        self.liquidity_cache: Dict[str, LiquidityAnalysis] = {}

        # Performance metrics
        self.execution_times: List[float] = []
        self.slippage_history: List[float] = []
        self.fill_rates: Dict[str, float] = {}

        # Algorithm instances
        self.algorithm_handlers = {
            ExecutionAlgorithm.MARKET: self._execute_market,
            ExecutionAlgorithm.LIMIT: self._execute_limit,
            ExecutionAlgorithm.TWAP: self._execute_twap,
            ExecutionAlgorithm.VWAP: self._execute_vwap,
            ExecutionAlgorithm.ICEBERG: self._execute_iceberg
        }

        # Execution parameters
        self.default_params = ExecutionParams(
            algorithm=ExecutionAlgorithm.MARKET,
            price_tolerance=config.get('default_price_tolerance', 0.1),  # 0.1%
            time_limit=config.get('default_time_limit', 300),  # 5 minutes
            max_participation_rate=config.get('max_participation_rate', 0.2)  # 20%
        )

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._running = False
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> None:
        """初始化執行服務"""
        self.logger.info("Initializing execution service...")

        self._running = False
        self._shutdown_event.clear()

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._monitor_executions()),
            asyncio.create_task(self._update_liquidity()),
            asyncio.create_task(self._optimize_algorithms())
        ]

        self.logger.info("Execution service initialized")

    async def shutdown(self) -> None:
        """關閉執行服務"""
        self.logger.info("Shutting down execution service...")

        self._running = False
        self._shutdown_event.set()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.logger.info("Execution service shutdown complete")

    async def execute_order(
        self,
        order: Order,
        broker_adapter: BrokerAdapter,
        params: Optional[ExecutionParams] = None
    ) -> ExecutionResult:
        """執行訂單"""
        start_time = time.perf_counter()

        # Use default params if none provided
        exec_params = params or self.default_params

        # Create execution report
        report = ExecutionReport(
            order_id=order.id,
            algorithm=exec_params.algorithm,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            total_quantity=order.quantity,
            filled_quantity=Decimal('0'),
            average_price=None
        )

        try:
            # Add to active orders
            self.active_orders[order.id] = order

            # Analyze liquidity
            liquidity = await self._analyze_liquidity(order.symbol)

            # Optimize execution based on liquidity
            optimized_params = await self._optimize_execution(order, liquidity, exec_params)

            # Execute using appropriate algorithm
            handler = self.algorithm_handlers.get(optimized_params.algorithm, self._execute_market)
            result = await handler(order, broker_adapter, optimized_params)

            # Update report
            report.end_time = datetime.utcnow()
            report.filled_quantity = result.executed_quantity or Decimal('0')
            report.average_price = result.average_price
            report.commission = result.commission

            # Calculate metrics
            if result.success:
                report.slippage = await self._calculate_slippage(order, result)
                report.efficiency_score = await self._calculate_efficiency_score(order, result, report)

                # Update performance metrics
                execution_time = (time.perf_counter() - start_time) * 1000
                self.execution_times.append(execution_time)
                if report.slippage:
                    self.slippage_history.append(report.slippage)

            # Store report
            self.execution_reports[order.id] = report

            # Log execution
            self.logger.info(
                f"Executed order {order.id}: {result.executed_quantity} @ {result.average_price}, "
                f"algorithm={optimized_params.algorithm.value}, slippage={report.slippage}%"
            )

            return result

        except Exception as e:
            self.logger.error(f"Error executing order {order.id}: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        finally:
            # Remove from active orders
            self.active_orders.pop(order.id, None)

    async def execute_child_orders(
        self,
        parent_order: Order,
        child_orders: List[Order],
        broker_adapter: BrokerAdapter
    ) -> List[ExecutionResult]:
        """執行子訂單（用於算法交易）"""
        results = []

        # Execute child orders concurrently with rate limiting
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent executions

        async def execute_child(child_order: Order) -> ExecutionResult:
            async with semaphore:
                return await self.execute_order(child_order, broker_adapter)

        tasks = [execute_child(order) for order in child_orders]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return only ExecutionResults
        execution_results = []
        for result in results:
            if isinstance(result, ExecutionResult):
                execution_results.append(result)
            else:
                self.logger.error(f"Child order execution failed: {result}")

        return execution_results

    async def get_best_price(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal
    ) -> Tuple[Optional[Decimal], Optional[LiquidityAnalysis]]:
        """獲取最佳價格"""
        try:
            # Get liquidity analysis
            liquidity = await self._analyze_liquidity(symbol)

            if not liquidity or not liquidity.depth:
                return None, liquidity

            # Calculate impact-adjusted price
            if side == OrderSide.BUY:
                # Aggregate ask side
                price_levels = sorted(
                    [(price, qty) for price, qty in liquidity.depth.items()],
                    key=lambda x: x[0]
                )
                accumulated_qty = Decimal('0')
                total_cost = Decimal('0')

                for price, qty in price_levels:
                    if accumulated_qty >= quantity:
                        break
                    fill_qty = min(qty, quantity - accumulated_qty)
                    total_cost += price * fill_qty
                    accumulated_qty += fill_qty

                avg_price = total_cost / quantity if quantity > 0 else None
            else:
                # Aggregate bid side
                price_levels = sorted(
                    [(price, qty) for price, qty in liquidity.depth.items()],
                    key=lambda x: -x[0]
                )
                accumulated_qty = Decimal('0')
                total_cost = Decimal('0')

                for price, qty in price_levels:
                    if accumulated_qty >= quantity:
                        break
                    fill_qty = min(qty, quantity - accumulated_qty)
                    total_cost += price * fill_qty
                    accumulated_qty += fill_qty

                avg_price = total_cost / quantity if quantity > 0 else None

            return avg_price, liquidity

        except Exception as e:
            self.logger.error(f"Error getting best price: {e}")
            return None, None

    async def get_execution_report(self, order_id: UUID) -> Optional[ExecutionReport]:
        """獲取執行報告"""
        return self.execution_reports.get(order_id)

    async def _execute_market(
        self,
        order: Order,
        broker_adapter: BrokerAdapter,
        params: ExecutionParams
    ) -> ExecutionResult:
        """市價單執行"""
        try:
            # Check if we need to split large orders
            liquidity = await self._analyze_liquidity(order.symbol)
            if liquidity and liquidity.optimal_size and order.quantity > liquidity.optimal_size:
                # Split order
                return await self._execute_with_splitting(order, broker_adapter, params)

            # Submit market order
            response = await broker_adapter.submit_order(order)

            return ExecutionResult(
                success=response.success,
                order_id=order.id,
                broker_order_id=response.broker_order_id,
                executed_quantity=response.filled_quantity,
                average_price=response.average_price,
                error_message=response.message
            )

        except Exception as e:
            self.logger.error(f"Error in market execution: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )

    async def _execute_limit(
        self,
        order: Order,
        broker_adapter: BrokerAdapter,
        params: ExecutionParams
    ) -> ExecutionResult:
        """限價單執行"""
        try:
            # Enhanced limit order with price improvement
            if not order.price:
                # Get current market price
                market_price, _ = await self.get_best_price(
                    order.symbol,
                    OrderSide.BUY if order.side == 'BUY' else OrderSide.SELL,
                    order.quantity
                )

                if market_price:
                    # Adjust price based on side and tolerance
                    tolerance = params.price_tolerance or 0.001
                    if order.side == 'BUY':
                        order.price = market_price * (1 + tolerance)
                    else:
                        order.price = market_price * (1 - tolerance)

            # Submit limit order
            response = await broker_adapter.submit_order(order)

            # Monitor for partial fills
            if response.success and response.status == OrderStatus.SUBMITTED:
                # Would monitor for fills
                pass

            return ExecutionResult(
                success=response.success,
                order_id=order.id,
                broker_order_id=response.broker_order_id,
                executed_quantity=response.filled_quantity,
                average_price=response.average_price,
                error_message=response.message
            )

        except Exception as e:
            self.logger.error(f"Error in limit execution: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )

    async def _execute_twap(
        self,
        order: Order,
        broker_adapter: BrokerAdapter,
        params: ExecutionParams
    ) -> ExecutionResult:
        """TWAP算法執行"""
        try:
            # Calculate slice parameters
            time_limit = params.time_limit or 300  # Default 5 minutes
            slice_count = params.slice_count or 10
            slice_interval = time_limit / slice_count
            slice_size = order.quantity / slice_count

            # Create child orders
            child_orders = []
            for i in range(slice_count):
                child_order = Order(
                    id=uuid4(),
                    portfolio_id=order.portfolio_id,
                    broker_account_id=order.broker_account_id,
                    symbol=order.symbol,
                    side=order.side,
                    order_type=OrderType.MARKET,
                    quantity=slice_size,
                    parent_order_id=order.id
                )
                child_orders.append(child_order)

            # Execute with delay
            results = []
            for i, child_order in enumerate(child_orders):
                result = await self.execute_order(child_order, broker_adapter)
                results.append(result)

                if i < len(child_orders) - 1:  # Don't sleep after last slice
                    await asyncio.sleep(slice_interval)

            # Aggregate results
            total_filled = sum(r.executed_quantity or Decimal('0') for r in results)
            total_cost = sum(
                (r.average_price or Decimal('0')) * (r.executed_quantity or Decimal('0'))
                for r in results
            )
            avg_price = total_cost / total_filled if total_filled > 0 else None

            return ExecutionResult(
                success=any(r.success for r in results),
                order_id=order.id,
                executed_quantity=total_filled,
                average_price=avg_price
            )

        except Exception as e:
            self.logger.error(f"Error in TWAP execution: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )

    async def _execute_vwap(
        self,
        order: Order,
        broker_adapter: BrokerAdapter,
        params: ExecutionParams
    ) -> ExecutionResult:
        """VWAP算法執行"""
        try:
            # Get historical volume profile
            volume_profile = await self._get_volume_profile(order.symbol)

            if not volume_profile:
                # Fall back to TWAP
                return await self._execute_twap(order, broker_adapter, params)

            # Calculate slice sizes based on volume profile
            total_volume = sum(volume_profile.values())
            child_orders = []

            for time_bucket, volume_ratio in volume_profile.items():
                slice_size = order.quantity * Decimal(str(volume_ratio))
                child_order = Order(
                    id=uuid4(),
                    portfolio_id=order.portfolio_id,
                    broker_account_id=order.broker_account_id,
                    symbol=order.symbol,
                    side=order.side,
                    order_type=OrderType.MARKET,
                    quantity=slice_size,
                    parent_order_id=order.id
                )
                child_orders.append((child_order, time_bucket))

            # Execute according to volume schedule
            results = []
            for child_order, time_bucket in child_orders:
                # Wait until time bucket
                # In production, this would sync with market time
                result = await self.execute_order(child_order, broker_adapter)
                results.append(result)

            # Aggregate results
            total_filled = sum(r.executed_quantity or Decimal('0') for r in results)
            total_cost = sum(
                (r.average_price or Decimal('0')) * (r.executed_quantity or Decimal('0'))
                for r in results
            )
            avg_price = total_cost / total_filled if total_filled > 0 else None

            return ExecutionResult(
                success=any(r.success for r in results),
                order_id=order.id,
                executed_quantity=total_filled,
                average_price=avg_price
            )

        except Exception as e:
            self.logger.error(f"Error in VWAP execution: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )

    async def _execute_iceberg(
        self,
        order: Order,
        broker_adapter: BrokerAdapter,
        params: ExecutionParams
    ) -> ExecutionResult:
        """冰山算法執行"""
        try:
            # Hide large order size
            display_size = params.min_fill_size or (order.quantity / Decimal('10'))
            remaining_quantity = order.quantity
            results = []

            while remaining_quantity > 0:
                # Create slice
                slice_size = min(display_size, remaining_quantity)
                slice_order = Order(
                    id=uuid4(),
                    portfolio_id=order.portfolio_id,
                    broker_account_id=order.broker_account_id,
                    symbol=order.symbol,
                    side=order.side,
                    order_type=OrderType.LIMIT,
                    quantity=slice_size,
                    price=order.price,
                    parent_order_id=order.id,
                    is_iceberg=True
                )

                # Execute slice
                result = await self.execute_order(slice_order, broker_adapter)
                results.append(result)

                if result.executed_quantity:
                    remaining_quantity -= result.executed_quantity
                else:
                    # No fill, might need to adjust price
                    break

                # Small delay between slices
                await asyncio.sleep(0.1)

            # Aggregate results
            total_filled = sum(r.executed_quantity or Decimal('0') for r in results)
            total_cost = sum(
                (r.average_price or Decimal('0')) * (r.executed_quantity or Decimal('0'))
                for r in results
            )
            avg_price = total_cost / total_filled if total_filled > 0 else None

            return ExecutionResult(
                success=any(r.success for r in results),
                order_id=order.id,
                executed_quantity=total_filled,
                average_price=avg_price
            )

        except Exception as e:
            self.logger.error(f"Error in iceberg execution: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )

    async def _analyze_liquidity(self, symbol: str) -> Optional[LiquidityAnalysis]:
        """分析流動性"""
        try:
            # Check cache first
            if symbol in self.liquidity_cache:
                cached = self.liquidity_cache[symbol]
                # Check if cache is fresh (within 1 minute)
                if (datetime.utcnow() - cached.timestamp).total_seconds() < 60:
                    return cached

            # Get order book data
            # This would typically fetch from market data service
            # For now, return mock data

            analysis = LiquidityAnalysis(
                symbol=symbol,
                bid_ask_spread=0.01,  # Mock spread
                average_volume=1000000,  # Mock volume
                impact_factor=0.001,  # Mock impact
                optimal_size=Decimal('10000')  # Mock optimal size
            )
            analysis.timestamp = datetime.utcnow()

            # Cache the analysis
            self.liquidity_cache[symbol] = analysis

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing liquidity: {e}")
            return None

    async def _optimize_execution(
        self,
        order: Order,
        liquidity: Optional[LiquidityAnalysis],
        params: ExecutionParams
    ) -> ExecutionParams:
        """優化執行參數"""
        try:
            if not liquidity:
                return params

            # Determine optimal algorithm based on order size and liquidity
            order_value = order.quantity * (order.price or Decimal('100'))

            # Large orders benefit from algorithmic execution
            if liquidity.optimal_size and order.quantity > liquidity.optimal_size * 5:
                # Very large order - use TWAP
                params.algorithm = ExecutionAlgorithm.TWAP
                params.slice_count = 20
                params.time_limit = 600  # 10 minutes

            elif liquidity.optimal_size and order.quantity > liquidity.optimal_size * 2:
                # Medium-large order - use VWAP if volume data available
                volume_profile = await self._get_volume_profile(order.symbol)
                if volume_profile:
                    params.algorithm = ExecutionAlgorithm.VWAP
                else:
                    params.algorithm = ExecutionAlgorithm.TWAP
                    params.slice_count = 10

            elif order.order_type == OrderType.LIMIT:
                # Limit order - use limit algorithm
                params.algorithm = ExecutionAlgorithm.LIMIT

            # Adjust price tolerance based on spread
            if liquidity.bid_ask_spread:
                params.price_tolerance = min(params.price_tolerance or 0.1, liquidity.bid_ask_spread * 2)

            return params

        except Exception as e:
            self.logger.error(f"Error optimizing execution: {e}")
            return params

    async def _execute_with_splitting(
        self,
        order: Order,
        broker_adapter: BrokerAdapter,
        params: ExecutionParams
    ) -> ExecutionResult:
        """分拆執行大單"""
        try:
            liquidity = await self._analyze_liquidity(order.symbol)
            if not liquidity or not liquidity.optimal_size:
                # Can't determine optimal size, execute as is
                return await self._execute_market(order, broker_adapter, params)

            # Calculate number of slices
            slice_count = int(order.quantity / liquidity.optimal_size) + 1
            slice_size = order.quantity / slice_count

            results = []
            for i in range(slice_count):
                # Create slice order
                slice_order = Order(
                    id=uuid4(),
                    portfolio_id=order.portfolio_id,
                    broker_account_id=order.broker_account_id,
                    symbol=order.symbol,
                    side=order.side,
                    order_type=order.order_type,
                    quantity=slice_size,
                    price=order.price,
                    parent_order_id=order.id
                )

                # Execute slice
                result = await self.execute_order(slice_order, broker_adapter)
                results.append(result)

                # Small delay to avoid market impact
                await asyncio.sleep(0.1)

            # Aggregate results
            total_filled = sum(r.executed_quantity or Decimal('0') for r in results)
            total_cost = sum(
                (r.average_price or Decimal('0')) * (r.executed_quantity or Decimal('0'))
                for r in results
            )
            avg_price = total_cost / total_filled if total_filled > 0 else None

            return ExecutionResult(
                success=any(r.success for r in results),
                order_id=order.id,
                executed_quantity=total_filled,
                average_price=avg_price
            )

        except Exception as e:
            self.logger.error(f"Error in split execution: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )

    async def _calculate_slippage(
        self,
        order: Order,
        result: ExecutionResult
    ) -> Optional[float]:
        """計算滑點"""
        try:
            if not result.average_price or not order.price:
                return None

            if order.side == 'BUY':
                slippage = (result.average_price - order.price) / order.price * 100
            else:
                slippage = (order.price - result.average_price) / order.price * 100

            return float(slippage)

        except Exception as e:
            self.logger.error(f"Error calculating slippage: {e}")
            return None

    async def _calculate_efficiency_score(
        self,
        order: Order,
        result: ExecutionResult,
        report: ExecutionReport
    ) -> Optional[float]:
        """計算執行效率分數"""
        try:
            # Simple efficiency based on fill rate and slippage
            fill_rate = float(result.executed_quantity / order.quantity)

            # Slippage penalty (0.1% slippage = 1 point penalty)
            slippage_penalty = abs(report.slippage or 0) * 10

            # Time penalty (1 second = 0.1 point penalty)
            execution_time = (report.end_time - report.start_time).total_seconds()
            time_penalty = execution_time * 0.1

            # Calculate score (0-100)
            score = max(0, 100 - slippage_penalty - time_penalty)
            score *= fill_rate  # Adjust by fill rate

            return min(100, max(0, score))

        except Exception as e:
            self.logger.error(f"Error calculating efficiency score: {e}")
            return None

    async def _get_volume_profile(self, symbol: str) -> Optional[Dict]:
        """獲取成交量分布"""
        # This would fetch historical volume data
        # For now, return None
        return None

    async def _monitor_executions(self) -> None:
        """監控執行後台任務"""
        self.logger.info("Starting execution monitor...")

        while not self._shutdown_event.is_set():
            try:
                # Monitor active orders
                for order_id, order in list(self.active_orders.items()):
                    # Check for timeouts
                    # Check for partial fills
                    # Update status
                    pass

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                self.logger.error(f"Error in execution monitor: {e}")
                await asyncio.sleep(1)

    async def _update_liquidity(self) -> None:
        """更新流動性數據後台任務"""
        self.logger.info("Starting liquidity updater...")

        while not self._shutdown_event.is_set():
            try:
                # Update liquidity for active symbols
                for symbol in list(self.liquidity_cache.keys()):
                    await self._analyze_liquidity(symbol)

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f"Error updating liquidity: {e}")
                await asyncio.sleep(30)

    async def _optimize_algorithms(self) -> None:
        """優化算法參數後台任務"""
        self.logger.info("Starting algorithm optimizer...")

        while not self._shutdown_event.is_set():
            try:
                # Analyze performance metrics
                # Adjust algorithm parameters
                # Learn from execution history

                await asyncio.sleep(3600)  # Optimize every hour

            except Exception as e:
                self.logger.error(f"Error in algorithm optimizer: {e}")
                await asyncio.sleep(3600)

    @property
    def average_execution_time(self) -> float:
        """平均執行時間"""
        if self.execution_times:
            return statistics.mean(self.execution_times)
        return 0

    def is_healthy(self) -> bool:
        """檢查服務是否健康"""
        # Check average execution time
        if self.average_execution_time > 5000:  # More than 5 seconds
            return False

        # Check slippage
        if self.slippage_history and statistics.mean(self.slippage_history) > 1.0:  # More than 1%
            return False

        return True