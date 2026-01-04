"""
Real-Time Trading Engine Core Module
實時交易執行引擎核心模塊

This module implements the core trading engine with low-latency execution,
real-time risk management, and broker adapter integration.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import json
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from .broker_adapter import BrokerAdapter, BrokerAdapterFactory
from .order_manager_v2 import OrderManagerV2 as OrderManager
from .position_manager_v2 import PositionManagerV2 as PositionManager
from .risk_manager import RiskManager
from .execution_service import ExecutionService, ExecutionResult
from ..core.database import get_db_session
from ..models.trading_models_v2 import (
    TradingSession, Order, Position, OrderStatus,
    PositionStatus, TradingSignal
)
from ..cache.redis_client import RedisClient
from ..messaging.kafka_producer import KafkaProducer
from ..monitoring.metrics import MetricsCollector


class TradingEngineStatus(Enum):
    """交易引擎狀態枚舉"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class RealTimeTradingEngine:
    """
    實時交易執行引擎

    負責接收策略信號，執行風險檢查，並通過券商適配器執行交易。
    設計目標：
    - 低延遲：< 10ms P99
    - 高吞吐：支持 10,000 TPS
    - 高可用：99.99%
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("trading_engine")

        # Core components
        self.status = TradingEngineStatus.STOPPED
        self.order_manager = OrderManager(config)
        self.position_manager = PositionManager(config)
        self.risk_manager = RiskManager(config)
        self.execution_service = ExecutionService(config)

        # Broker adapters
        self.broker_adapters: Dict[str, BrokerAdapter] = {}
        self.broker_factory = BrokerAdapterFactory()

        # Trading sessions
        self.active_sessions: Dict[UUID, TradingSession] = {}
        self.session_locks: Dict[UUID, asyncio.Lock] = {}

        # Performance optimization
        self.signal_queue = asyncio.Queue(maxsize=10000)
        self.batch_processor = BatchProcessor(config)
        self.memory_cache = LRUCache(maxsize=1000)

        # External connections
        self.redis_client = RedisClient(config.get('redis_url', 'redis://localhost:6379'))
        self.kafka_producer = KafkaProducer(config.get('kafka_brokers', 'localhost:9092'))
        self.metrics = MetricsCollector(config.get('prometheus_port', 3005))

        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Background tasks
        self.background_tasks: List[asyncio.Task] = []

    async def start(self) -> bool:
        """啟動交易引擎"""
        try:
            self.logger.info("Starting real-time trading engine...")
            self.status = TradingEngineStatus.STARTING

            # Initialize components
            await self._initialize_components()

            # Load active trading sessions
            await self._load_active_sessions()

            # Start background tasks
            await self._start_background_tasks()

            self.status = TradingEngineStatus.RUNNING
            self.logger.info("Trading engine started successfully")

            # Record metrics
            self.metrics.increment_counter('trading_engine_start_total')
            return True

        except Exception as e:
            self.logger.error(f"Failed to start trading engine: {e}")
            self.status = TradingEngineStatus.ERROR
            self.metrics.increment_counter('trading_engine_start_errors')
            return False

    async def stop(self) -> bool:
        """停止交易引擎"""
        try:
            self.logger.info("Stopping trading engine...")
            self.status = TradingEngineStatus.STOPPING

            # Stop accepting new signals
            await self.signal_queue.put(None)

            # Cancel all background tasks
            for task in self.background_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Close all trading sessions
            for session_id in list(self.active_sessions.keys()):
                await self.close_trading_session(session_id, emergency=True)

            # Disconnect all broker adapters
            for adapter in self.broker_adapters.values():
                await adapter.disconnect()

            # Close connections
            await self.redis_client.close()
            await self.kafka_producer.close()

            # Shutdown thread pool
            self.executor.shutdown(wait=True)

            self.status = TradingEngineStatus.STOPPED
            self.logger.info("Trading engine stopped successfully")

            # Record metrics
            self.metrics.increment_counter('trading_engine_stop_total')
            return True

        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")
            self.status = TradingEngineStatus.ERROR
            return False

    async def process_trading_signal(self, signal: TradingSignal) -> ExecutionResult:
        """
        處理交易信號
        這是引擎的核心方法，執行完整的交易流程
        """
        start_time = time.perf_counter()

        try:
            # Add to signal queue
            await self.signal_queue.put(signal)

            # Process signal immediately for low latency
            result = await self._process_signal_internal(signal)

            # Record execution time
            execution_time = (time.perf_counter() - start_time) * 1000
            result.execution_time_ms = execution_time

            # Update metrics
            self.metrics.histogram('signal_processing_duration_ms', execution_time)
            self.metrics.increment_counter('signals_processed_total')

            return result

        except Exception as e:
            self.logger.error(f"Error processing trading signal: {e}")
            self.metrics.increment_counter('signal_processing_errors')

            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

    async def _process_signal_internal(self, signal: TradingSignal) -> ExecutionResult:
        """內部信號處理邏輯"""
        # Validate signal
        if not self._validate_signal(signal):
            return ExecutionResult(
                success=False,
                error_message="Invalid trading signal"
            )

        # Check if session exists and is active
        session = self.active_sessions.get(signal.session_id)
        if not session or session.status != 'ACTIVE':
            return ExecutionResult(
                success=False,
                error_message=f"Trading session {signal.session_id} not found or inactive"
            )

        # Pre-trade risk check
        risk_result = await self.risk_manager.pre_trade_risk_check(signal, session)
        if not risk_result.passed:
            return ExecutionResult(
                success=False,
                error_message=f"Risk check failed: {risk_result.reason}"
            )

        # Create order
        order = await self.order_manager.create_order_from_signal(signal, session)

        # Execute order
        execution_result = await self.execution_service.execute_order(order)

        # Update positions
        if execution_result.success:
            await self.position_manager.update_positions(order, execution_result)

        # Publish results
        await self._publish_execution_result(order, execution_result)

        # Update cache
        await self._update_cache(session.id, execution_result)

        return execution_result

    async def create_trading_session(
        self,
        strategy_instance_id: UUID,
        broker_config: Dict[str, Any],
        initial_capital: Decimal,
        risk_config: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """創建新的交易會話"""
        session_id = uuid4()

        # Create broker adapter
        broker_name = broker_config['broker_name']
        adapter = self.broker_factory.create_adapter(broker_name, broker_config)

        # Connect and authenticate
        if not await adapter.connect():
            raise Exception(f"Failed to connect to broker {broker_name}")

        # Create session in database
        async with get_db_session() as db:
            session = TradingSession(
                id=session_id,
                strategy_instance_id=strategy_instance_id,
                broker_id=broker_name,
                status='INITIALIZING',
                initial_capital=initial_capital,
                allocated_capital=Decimal(0),
                available_capital=initial_capital,
                metadata={
                    'broker_config': broker_config,
                    'risk_config': risk_config or {}
                }
            )
            db.add(session)
            await db.commit()

        # Store session
        self.active_sessions[session_id] = session
        self.session_locks[session_id] = asyncio.Lock()
        self.broker_adapters[broker_name] = adapter

        self.logger.info(f"Created trading session {session_id} for broker {broker_name}")

        return session_id

    async def start_trading_session(self, session_id: UUID) -> bool:
        """啟動交易會話"""
        async with self.session_locks.get(session_id, asyncio.Lock()):
            session = self.active_sessions.get(session_id)
            if not session:
                return False

            # Update status
            session.status = 'ACTIVE'
            session.trading_started_at = datetime.utcnow()

            # Save to database
            async with get_db_session() as db:
                db.add(session)
                await db.commit()

            # Initialize positions
            await self.position_manager.initialize_positions(session)

            self.logger.info(f"Started trading session {session_id}")
            return True

    async def close_trading_session(
        self,
        session_id: UUID,
        emergency: bool = False,
        close_positions: bool = True
    ) -> bool:
        """關閉交易會話"""
        async with self.session_locks.get(session_id, asyncio.Lock()):
            session = self.active_sessions.get(session_id)
            if not session:
                return False

            # Close positions if requested
            if close_positions:
                await self.position_manager.close_all_positions(session, emergency)

            # Cancel all pending orders
            await self.order_manager.cancel_all_orders(session, emergency)

            # Update status
            session.status = 'STOPPED'
            session.stopped_at = datetime.utcnow()

            # Save to database
            async with get_db_session() as db:
                db.add(session)
                await db.commit()

            # Remove from active sessions
            del self.active_sessions[session_id]
            del self.session_locks[session_id]

            self.logger.info(f"Closed trading session {session_id}")
            return True

    def _validate_signal(self, signal: TradingSignal) -> bool:
        """驗證交易信號"""
        if not signal.symbol or not signal.side or signal.quantity <= 0:
            return False

        if signal.side not in ['BUY', 'SELL']:
            return False

        if signal.order_type not in ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT']:
            return False

        return True

    async def _initialize_components(self) -> None:
        """初始化所有組件"""
        # Initialize order manager
        await self.order_manager.initialize()

        # Initialize position manager
        await self.position_manager.initialize()

        # Initialize risk manager
        await self.risk_manager.initialize()

        # Initialize execution service
        await self.execution_service.initialize()

    async def _load_active_sessions(self) -> None:
        """加載活躍的交易會話"""
        async with get_db_session() as db:
            sessions = await db.query(TradingSession).filter(
                TradingSession.status == 'ACTIVE'
            ).all()

            for session in sessions:
                self.active_sessions[session.id] = session
                self.session_locks[session.id] = asyncio.Lock()

    async def _start_background_tasks(self) -> None:
        """啟動後台任務"""
        # Signal processing task
        self.background_tasks.append(
            asyncio.create_task(self._process_signal_queue())
        )

        # Risk monitoring task
        self.background_tasks.append(
            asyncio.create_task(self._monitor_risk())
        )

        # Position monitoring task
        self.background_tasks.append(
            asyncio.create_task(self._monitor_positions())
        )

        # Health check task
        self.background_tasks.append(
            asyncio.create_task(self._health_check())
        )

    async def _process_signal_queue(self) -> None:
        """處理信號隊列的後台任務"""
        while True:
            try:
                signal = await self.signal_queue.get()
                if signal is None:  # Shutdown signal
                    break

                # Process signal
                await self._process_signal_internal(signal)

            except Exception as e:
                self.logger.error(f"Error in signal queue processor: {e}")

    async def _monitor_risk(self) -> None:
        """風險監控後台任務"""
        while True:
            try:
                for session_id, session in self.active_sessions.items():
                    # Calculate real-time risk metrics
                    risk_metrics = await self.risk_manager.calculate_risk_metrics(session)

                    # Check risk thresholds
                    if risk_metrics.has_alerts:
                        await self._handle_risk_alert(session_id, risk_metrics.alerts)

                    # Update cache
                    await self.redis_client.set(
                        f"risk_metrics:{session_id}",
                        risk_metrics.to_dict(),
                        ttl=60
                    )

                await asyncio.sleep(1)  # Update every second

            except Exception as e:
                self.logger.error(f"Error in risk monitor: {e}")
                await asyncio.sleep(5)

    async def _monitor_positions(self) -> None:
        """倉位監控後台任務"""
        while True:
            try:
                for session_id, session in self.active_sessions.items():
                    # Update position values with current market prices
                    await self.position_manager.update_market_values(session)

                    # Check position limits
                    positions = await self.position_manager.get_positions(session)
                    for position in positions:
                        if position.risk_level > 0.8:  # 80% risk level
                            await self._handle_position_alert(session_id, position)

                await asyncio.sleep(0.5)  # Update twice per second

            except Exception as e:
                self.logger.error(f"Error in position monitor: {e}")
                await asyncio.sleep(5)

    async def _health_check(self) -> None:
        """健康檢查後台任務"""
        while True:
            try:
                # Check broker connections
                for broker_name, adapter in self.broker_adapters.items():
                    if not await adapter.is_connected():
                        self.logger.warning(f"Broker {broker_name} disconnected")
                        await self._handle_broker_disconnection(broker_name)

                # Check component health
                components_health = {
                    'order_manager': self.order_manager.is_healthy(),
                    'position_manager': self.position_manager.is_healthy(),
                    'risk_manager': self.risk_manager.is_healthy(),
                    'execution_service': self.execution_service.is_healthy()
                }

                # Update health status
                health_status = all(components_health.values())
                self.metrics.gauge('trading_engine_health', 1 if health_status else 0)

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error in health check: {e}")
                await asyncio.sleep(30)

    async def _handle_risk_alert(self, session_id: UUID, alerts: List[Dict]) -> None:
        """處理風險告警"""
        for alert in alerts:
            self.logger.warning(f"Risk alert for session {session_id}: {alert}")

            # Publish alert
            await self.kafka_producer.publish(
                topic='risk_alerts',
                message={
                    'session_id': str(session_id),
                    'alert': alert,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            # Send notification
            if alert['severity'] == 'CRITICAL':
                await self._emergency_stop_session(session_id, alert['reason'])

    async def _handle_position_alert(self, session_id: UUID, position) -> None:
        """處理倉位告警"""
        self.logger.warning(f"Position alert for session {session_id}: {position}")

        # Check if position should be reduced
        if position.risk_level > 0.95:  # 95% risk level
            await self._reduce_position(session_id, position, 0.5)  # Reduce by 50%

    async def _handle_broker_disconnection(self, broker_name: str) -> None:
        """處理券商連接斷開"""
        self.logger.error(f"Broker {broker_name} disconnected")

        # Mark all orders through this broker as failed
        await self.order_manager.mark_orders_failed_by_broker(broker_name)

        # Try to reconnect
        adapter = self.broker_adapters.get(broker_name)
        if adapter:
            retry_count = 0
            while not await adapter.connect() and retry_count < 5:
                await asyncio.sleep(5)
                retry_count += 1

    async def _emergency_stop_session(self, session_id: UUID, reason: str) -> None:
        """緊急停止交易會話"""
        self.logger.error(f"Emergency stopping session {session_id}: {reason}")

        # Pause trading
        await self.pause_trading_session(session_id)

        # Send emergency alert
        await self.kafka_producer.publish(
            topic='emergency_alerts',
            message={
                'session_id': str(session_id),
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    async def _reduce_position(self, session_id: UUID, position, ratio: float) -> None:
        """減少倉位"""
        # Create closing order
        closing_quantity = position.quantity * Decimal(ratio)

        # Determine order side
        side = 'SELL' if position.side == 'LONG' else 'BUY'

        # Create and submit order
        order = Order(
            session_id=session_id,
            symbol=position.symbol,
            side=side,
            order_type='MARKET',
            quantity=closing_quantity,
            reason='Position reduction due to high risk'
        )

        await self.execution_service.execute_order(order)

    async def pause_trading_session(self, session_id: UUID) -> bool:
        """暫停交易會話"""
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        session.status = 'PAUSED'

        async with get_db_session() as db:
            db.add(session)
            await db.commit()

        self.logger.info(f"Paused trading session {session_id}")
        return True

    async def resume_trading_session(self, session_id: UUID) -> bool:
        """恢復交易會話"""
        session = self.active_sessions.get(session_id)
        if not session or session.status != 'PAUSED':
            return False

        # Check if risk metrics are acceptable
        risk_metrics = await self.risk_manager.calculate_risk_metrics(session)
        if not risk_metrics.is_acceptable:
            return False

        session.status = 'ACTIVE'

        async with get_db_session() as db:
            db.add(session)
            await db.commit()

        self.logger.info(f"Resumed trading session {session_id}")
        return True

    async def _publish_execution_result(
        self,
        order: Order,
        result: ExecutionResult
    ) -> None:
        """發布執行結果"""
        message = {
            'order_id': str(order.id),
            'broker_order_id': result.broker_order_id,
            'status': 'FILLED' if result.success else 'FAILED',
            'executed_quantity': float(result.executed_quantity),
            'average_price': float(result.average_price) if result.average_price else None,
            'execution_time_ms': result.execution_time_ms,
            'error_message': result.error_message,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Publish to Kafka
        await self.kafka_producer.publish('order_executions', message)

        # Update Redis cache
        await self.redis_client.set(
            f"order_status:{order.id}",
            json.dumps(message),
            ttl=300  # 5 minutes
        )

    async def _update_cache(self, session_id: UUID, result: ExecutionResult) -> None:
        """更新緩存"""
        # Update session metrics
        session_metrics = await self.redis_client.get(f"session_metrics:{session_id}") or {}

        session_metrics['last_execution'] = {
            'time': datetime.utcnow().isoformat(),
            'success': result.success,
            'execution_time_ms': result.execution_time_ms
        }

        # Update total trades
        session_metrics['total_trades'] = session_metrics.get('total_trades', 0) + 1

        await self.redis_client.set(
            f"session_metrics:{session_id}",
            session_metrics,
            ttl=300
        )

    def get_engine_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        return {
            'status': self.status.value,
            'active_sessions': len(self.active_sessions),
            'total_orders_processed': self.order_manager.total_orders_processed,
            'average_execution_time_ms': self.execution_service.average_execution_time,
            'queue_size': self.signal_queue.qsize(),
            'broker_connections': {
                name: adapter.is_connected()
                for name, adapter in self.broker_adapters.items()
            },
            'health_metrics': {
                'order_manager': self.order_manager.is_healthy(),
                'position_manager': self.position_manager.is_healthy(),
                'risk_manager': self.risk_manager.is_healthy(),
                'execution_service': self.execution_service.is_healthy()
            }
        }


class BatchProcessor:
    """批量處理器"""

    def __init__(self, config: Dict[str, Any]):
        self.batch_size = config.get('batch_size', 100)
        self.batch_timeout = config.get('batch_timeout', 0.1)  # 100ms
        self.signal_queue = asyncio.Queue(maxsize=10000)

    async def process_batch(self, signals: List[TradingSignal]) -> List[ExecutionResult]:
        """批量處理信號"""
        # Group signals by session
        session_groups = self._group_by_session(signals)

        results = []

        # Process each session group
        for session_id, session_signals in session_groups.items():
            # Sort by timestamp
            session_signals.sort(key=lambda s: s.timestamp)

            # Process sequentially within session
            for signal in session_signals:
                # Process signal
                result = await self._process_single_signal(signal)
                results.append(result)

        return results

    def _group_by_session(self, signals: List[TradingSignal]) -> Dict[UUID, List[TradingSignal]]:
        """按會話分組信號"""
        groups = {}
        for signal in signals:
            if signal.session_id not in groups:
                groups[signal.session_id] = []
            groups[signal.session_id].append(signal)
        return groups

    async def _process_single_signal(self, signal: TradingSignal) -> ExecutionResult:
        """處理單個信號"""
        # This would be implemented to call the main engine
        pass


class LRUCache:
    """LRU 緩存實現"""

    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self.cache = {}
        self.access_order = []

    def get(self, key: str) -> Any:
        """獲取緩存項"""
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        """設置緩存項"""
        if key in self.cache:
            # Update existing
            self.cache[key] = value
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new
            if len(self.cache) >= self.maxsize:
                # Remove least recently used
                oldest = self.access_order.pop(0)
                del self.cache[oldest]

            self.cache[key] = value
            self.access_order.append(key)