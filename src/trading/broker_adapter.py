"""
Broker Adapter Module
券商適配器模塊

Provides unified interface for different brokers (Futu, Interactive Brokers, etc.)
with connection pooling, retry mechanisms, and error handling.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import json
import aiohttp
import backoff

from ..models.trading_models_v2 import (
    Order, OrderStatus, OrderType, OrderSide,
    Position, PositionStatus
)


class BrokerType(str, Enum):
    """券商類型枚舉"""
    FUTU = "futu"
    INTERACTIVE_BROKERS = "interactive_brokers"
    BINANCE = "binance"
    HUOBI = "huobi"
    SIMULATION = "simulation"


class ConnectionStatus(str, Enum):
    """連接狀態枚舉"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class BrokerConfig:
    """券商配置"""
    broker_type: BrokerType
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    account_id: Optional[str] = None
    environment: str = "simulation"  # simulation, paper, live
    timeout: int = 30
    max_connections: int = 5
    retry_attempts: int = 3
    retry_delay: float = 1.0
    rate_limit: int = 10  # requests per second
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderResponse:
    """訂單響應"""
    success: bool
    broker_order_id: Optional[str] = None
    message: Optional[str] = None
    status: Optional[OrderStatus] = None
    filled_quantity: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    timestamp: Optional[datetime] = None


@dataclass
class PositionInfo:
    """倉位信息"""
    symbol: str
    quantity: Decimal
    side: str  # LONG, SHORT
    market_value: Decimal
    average_price: Decimal
    unrealized_pnl: Decimal
    percentage: float


class BrokerAdapter(ABC):
    """券商適配器抽象基類"""

    def __init__(self, config: BrokerConfig):
        self.config = config
        self.logger = logging.getLogger(f"broker_adapter.{config.broker_type.value}")
        self.status = ConnectionStatus.DISCONNECTED
        self.connection_pool: Optional[aiohttp.TCPConnector] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_error: Optional[str] = None
        self.last_heartbeat: Optional[datetime] = None
        self.request_semaphore = asyncio.Semaphore(config.rate_limit)
        self._metrics = {
            'requests_total': 0,
            'errors_total': 0,
            'reconnects_total': 0,
            'last_request_time': None
        }

    async def initialize(self) -> bool:
        """初始化適配器"""
        try:
            self.status = ConnectionStatus.CONNECTING

            # Create connection pool
            self.connection_pool = aiohttp.TCPConnector(
                limit=self.config.max_connections,
                limit_per_host=self.config.max_connections,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )

            # Create session
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                connector=self.connection_pool,
                timeout=timeout
            )

            # Initialize broker-specific connection
            success = await self._connect()

            if success:
                self.status = ConnectionStatus.CONNECTED
                self.last_heartbeat = datetime.utcnow()
                self.logger.info(f"Connected to {self.config.broker_type.value}")
                return True
            else:
                self.status = ConnectionStatus.ERROR
                return False

        except Exception as e:
            self.logger.error(f"Failed to initialize broker adapter: {e}")
            self.status = ConnectionStatus.ERROR
            self.last_error = str(e)
            return False

    async def disconnect(self) -> None:
        """斷開連接"""
        try:
            await self._disconnect()

            if self.session:
                await self.session.close()
                self.session = None

            if self.connection_pool:
                await self.connection_pool.close()
                self.connection_pool = None

            self.status = ConnectionStatus.DISCONNECTED
            self.logger.info("Disconnected from broker")

        except Exception as e:
            self.logger.error(f"Error disconnecting from broker: {e}")

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        jitter=backoff.full_jitter
    )
    async def submit_order(self, order: Order) -> OrderResponse:
        """提交訂單"""
        async with self.request_semaphore:
            self._metrics['requests_total'] += 1
            self._metrics['last_request_time'] = datetime.utcnow()

            try:
                if self.status != ConnectionStatus.CONNECTED:
                    if not await self._reconnect():
                        return OrderResponse(
                            success=False,
                            message="Not connected to broker"
                        )

                # Submit order to broker
                response = await self._submit_order_internal(order)

                # Update last heartbeat
                self.last_heartbeat = datetime.utcnow()

                return response

            except Exception as e:
                self.logger.error(f"Error submitting order: {e}")
                self._metrics['errors_total'] += 1
                self.last_error = str(e)

                # Try to reconnect on error
                if self.status == ConnectionStatus.CONNECTED:
                    await self._reconnect()

                return OrderResponse(
                    success=False,
                    message=str(e)
                )

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        jitter=backoff.full_jitter
    )
    async def cancel_order(self, broker_order_id: str) -> bool:
        """取消訂單"""
        async with self.request_semaphore:
            try:
                if self.status != ConnectionStatus.CONNECTED:
                    return False

                success = await self._cancel_order_internal(broker_order_id)
                self.last_heartbeat = datetime.utcnow()
                return success

            except Exception as e:
                self.logger.error(f"Error cancelling order: {e}")
                self._metrics['errors_total'] += 1
                return False

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        jitter=backoff.full_jitter
    )
    async def get_order_status(self, broker_order_id: str) -> Optional[OrderStatus]:
        """獲取訂單狀態"""
        async with self.request_semaphore:
            try:
                if self.status != ConnectionStatus.CONNECTED:
                    return None

                status = await self._get_order_status_internal(broker_order_id)
                self.last_heartbeat = datetime.utcnow()
                return status

            except Exception as e:
                self.logger.error(f"Error getting order status: {e}")
                self._metrics['errors_total'] += 1
                return None

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        jitter=backoff.full_jitter
    )
    async def get_positions(self) -> List[PositionInfo]:
        """獲取所有倉位"""
        async with self.request_semaphore:
            try:
                if self.status != ConnectionStatus.CONNECTED:
                    return []

                positions = await self._get_positions_internal()
                self.last_heartbeat = datetime.utcnow()
                return positions

            except Exception as e:
                self.logger.error(f"Error getting positions: {e}")
                self._metrics['errors_total'] += 1
                return []

    async def get_account_info(self) -> Dict[str, Any]:
        """獲取賬戶信息"""
        try:
            if self.status != ConnectionStatus.CONNECTED:
                return {}

            info = await self._get_account_info_internal()
            self.last_heartbeat = datetime.utcnow()
            return info

        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return {}

    async def is_connected(self) -> bool:
        """檢查是否連接"""
        if self.status != ConnectionStatus.CONNECTED:
            return False

        # Check if connection is still alive
        try:
            await self._ping()
            return True
        except:
            self.status = ConnectionStatus.ERROR
            return False

    async def _reconnect(self) -> bool:
        """重新連接"""
        self.status = ConnectionStatus.RECONNECTING
        self._metrics['reconnects_total'] += 1

        try:
            # Disconnect first
            await self._disconnect()

            # Wait before reconnecting
            await asyncio.sleep(self.config.retry_delay)

            # Reconnect
            success = await self._connect()

            if success:
                self.status = ConnectionStatus.CONNECTED
                self.last_heartbeat = datetime.utcnow()
                self.logger.info("Successfully reconnected to broker")
                return True
            else:
                self.status = ConnectionStatus.ERROR
                return False

        except Exception as e:
            self.logger.error(f"Failed to reconnect: {e}")
            self.status = ConnectionStatus.ERROR
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """獲取適配器指標"""
        return {
            'status': self.status.value,
            'last_error': self.last_error,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'metrics': self._metrics.copy()
        }

    # Abstract methods to be implemented by specific broker adapters
    @abstractmethod
    async def _connect(self) -> bool:
        """建立連接"""
        pass

    @abstractmethod
    async def _disconnect(self) -> None:
        """斷開連接"""
        pass

    @abstractmethod
    async def _submit_order_internal(self, order: Order) -> OrderResponse:
        """內部訂單提交"""
        pass

    @abstractmethod
    async def _cancel_order_internal(self, broker_order_id: str) -> bool:
        """內部取消訂單"""
        pass

    @abstractmethod
    async def _get_order_status_internal(self, broker_order_id: str) -> Optional[OrderStatus]:
        """內部獲取訂單狀態"""
        pass

    @abstractmethod
    async def _get_positions_internal(self) -> List[PositionInfo]:
        """內部獲取倉位"""
        pass

    @abstractmethod
    async def _get_account_info_internal(self) -> Dict[str, Any]:
        """內部獲取賬戶信息"""
        pass

    @abstractmethod
    async def _ping(self) -> None:
        """心跳檢測"""
        pass


class FutuBrokerAdapter(BrokerAdapter):
    """富途券商適配器"""

    def __init__(self, config: BrokerConfig):
        super().__init__(config)
        self.futu_client = None
        self.unlock_password = config.additional_params.get('unlock_password')

    async def _connect(self) -> bool:
        """連接到富途"""
        try:
            # Import Futu API
            from futu import *

            # Create quote and trade contexts
            quote_ctx = OpenQuoteContext(host=self.config.host, port=self.config.port)
            trade_ctx = OpenSecTradeContext(
                host=self.config.host,
                port=self.config.port,
                security_firm=SecurityFirm.FUTUSECURITIES
            )

            # Test connection
            _, ret = await quote_ctx.get_global_state()
            if ret != RET_OK:
                return False

            # Unlock trade if password provided
            if self.unlock_password:
                _, ret = await trade_ctx.unlock_trade(self.unlock_password)
                if ret != RET_OK:
                    self.logger.error("Failed to unlock Futu trade")
                    return False

            self.futu_client = {
                'quote_ctx': quote_ctx,
                'trade_ctx': trade_ctx
            }

            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Futu: {e}")
            return False

    async def _disconnect(self) -> None:
        """斷開富途連接"""
        if self.futu_client:
            try:
                if 'quote_ctx' in self.futu_client:
                    await self.futu_client['quote_ctx'].close()
                if 'trade_ctx' in self.futu_client:
                    await self.futu_client['trade_ctx'].close()
            except Exception as e:
                self.logger.error(f"Error closing Futu connections: {e}")
            finally:
                self.futu_client = None

    async def _submit_order_internal(self, order: Order) -> OrderResponse:
        """提交訂單到富途"""
        if not self.futu_client:
            return OrderResponse(success=False, message="Not connected to Futu")

        try:
            from futu import *

            # Convert order to Futu format
            order_side = TrdSide.BUY if order.side == 'BUY' else TrdSide.SELL

            # Place order
            ret_code, ret_data = await self.futu_client['trade_ctx'].place_order(
                price=order.price,
                qty=order.quantity,
                code=order.symbol,
                trd_side=order_side,
                trd_env=TrdEnv.SIMULATE if self.config.environment == 'simulation' else TrdEnv.REAL,
                order_type=OrderType.MARKET if order.order_type == 'MARKET' else OrderType.LIMIT
            )

            if ret_code == RET_OK:
                return OrderResponse(
                    success=True,
                    broker_order_id=ret_data['order_id'][0],
                    status=OrderStatus.SUBMITTED
                )
            else:
                return OrderResponse(
                    success=False,
                    message=f"Futu error: {ret_code}"
                )

        except Exception as e:
            return OrderResponse(
                success=False,
                message=str(e)
            )

    async def _cancel_order_internal(self, broker_order_id: str) -> bool:
        """取消富途訂單"""
        if not self.futu_client:
            return False

        try:
            from futu import *

            ret_code, _ = await self.futu_client['trade_ctx'].cancel_order(
                order_id_list=[broker_order_id]
            )

            return ret_code == RET_OK

        except Exception as e:
            self.logger.error(f"Error cancelling Futu order: {e}")
            return False

    async def _get_order_status_internal(self, broker_order_id: str) -> Optional[OrderStatus]:
        """獲取富途訂單狀態"""
        if not self.futu_client:
            return None

        try:
            from futu import *

            ret_code, ret_data = await self.futu_client['trade_ctx'].order_list_query(
                order_id=broker_order_id
            )

            if ret_code == RET_OK and len(ret_data) > 0:
                status = ret_data['order_status'][0]

                # Map Futu status to our status
                if status == OrderStatus.SUBMITTED:
                    return OrderStatus.SUBMITTED
                elif status == OrderStatus.FILLED:
                    return OrderStatus.FILLED
                elif status == OrderStatus.CANCELLED:
                    return OrderStatus.CANCELLED
                elif status == OrderStatus.REJECTED:
                    return OrderStatus.REJECTED

            return None

        except Exception as e:
            self.logger.error(f"Error getting Futu order status: {e}")
            return None

    async def _get_positions_internal(self) -> List[PositionInfo]:
        """獲取富途倉位"""
        if not self.futu_client:
            return []

        try:
            from futu import *

            ret_code, ret_data = await self.futu_client['trade_ctx'].position_list_query(
                pl_ratio_min=0,
                code='',
                pl_ratio_max=1,
                trd_env=TrdEnv.SIMULATE if self.config.environment == 'simulation' else TrdEnv.REAL
            )

            positions = []
            if ret_code == RET_OK:
                for _, row in ret_data.iterrows():
                    position = PositionInfo(
                        symbol=row['code'],
                        quantity=row['qty'],
                        side='LONG' if row['qty'] > 0 else 'SHORT',
                        market_value=row['market_val'],
                        average_price=row['cost_price'],
                        unrealized_pnl=row['unrealized_pl'],
                        percentage=row['pl_ratio'] * 100
                    )
                    positions.append(position)

            return positions

        except Exception as e:
            self.logger.error(f"Error getting Futu positions: {e}")
            return []

    async def _get_account_info_internal(self) -> Dict[str, Any]:
        """獲取富途賬戶信息"""
        if not self.futu_client:
            return {}

        try:
            from futu import *

            ret_code, ret_data = await self.futu_client['trade_ctx'].acc_info_query(
                trd_env=TrdEnv.SIMULATE if self.config.environment == 'simulation' else TrdEnv.REAL
            )

            if ret_code == RET_OK and len(ret_data) > 0:
                return {
                    'total_cash': ret_data['cash'][0],
                    'total_assets': ret_data['total_assets'][0],
                    'buying_power': ret_data['max_withdraw'][0],
                    'margin_ratio': ret_data['margin_ratio'][0]
                }

            return {}

        except Exception as e:
            self.logger.error(f"Error getting Futu account info: {e}")
            return {}

    async def _ping(self) -> None:
        """富途心跳檢測"""
        if not self.futu_client:
            raise ConnectionError("Not connected to Futu")

        # Query global state as ping
        _, ret = await self.futu_client['quote_ctx'].get_global_state()
        if ret != RET_OK:
            raise ConnectionError("Futu ping failed")


class SimulationBrokerAdapter(BrokerAdapter):
    """模擬券商適配器"""

    def __init__(self, config: BrokerConfig):
        super().__init__(config)
        self.orders: Dict[str, Dict] = {}
        self.positions: Dict[str, PositionInfo] = {}
        self.account_cash = Decimal('1000000')  # Default 1M cash
        self.market_prices: Dict[str, Decimal] = {}

    async def _connect(self) -> bool:
        """模擬連接"""
        # Simulate connection delay
        await asyncio.sleep(0.1)
        return True

    async def _disconnect(self) -> None:
        """模擬斷開"""
        pass

    async def _submit_order_internal(self, order: Order) -> OrderResponse:
        """模擬訂單提交"""
        # Simulate processing delay
        await asyncio.sleep(0.01)

        order_id = str(uuid4())

        # Simulate market order execution
        if order.order_type == 'MARKET':
            price = self.market_prices.get(order.symbol, Decimal('100'))  # Default price
            success = True
            status = OrderStatus.FILLED
            filled_quantity = order.quantity
        else:
            # Limit order simulation
            price = order.price
            current_price = self.market_prices.get(order.symbol, Decimal('100'))

            if (order.side == 'BUY' and price >= current_price) or \
               (order.side == 'SELL' and price <= current_price):
                success = True
                status = OrderStatus.FILLED
                filled_quantity = order.quantity
            else:
                success = True
                status = OrderStatus.SUBMITTED
                filled_quantity = Decimal('0')

        # Store order
        self.orders[order_id] = {
            'order': order,
            'status': status,
            'filled_quantity': filled_quantity,
            'average_price': price if filled_quantity > 0 else None
        }

        # Update positions
        if filled_quantity > 0:
            self._update_position(order.symbol, order.side, filled_quantity, price)

        return OrderResponse(
            success=success,
            broker_order_id=order_id,
            status=status,
            filled_quantity=filled_quantity,
            average_price=price if filled_quantity > 0 else None
        )

    async def _cancel_order_internal(self, broker_order_id: str) -> bool:
        """模擬取消訂單"""
        if broker_order_id in self.orders:
            self.orders[broker_order_id]['status'] = OrderStatus.CANCELLED
            return True
        return False

    async def _get_order_status_internal(self, broker_order_id: str) -> Optional[OrderStatus]:
        """獲取模擬訂單狀態"""
        order_info = self.orders.get(broker_order_id)
        return order_info['status'] if order_info else None

    async def _get_positions_internal(self) -> List[PositionInfo]:
        """獲取模擬倉位"""
        return list(self.positions.values())

    async def _get_account_info_internal(self) -> Dict[str, Any]:
        """獲取模擬賬戶信息"""
        total_value = self.account_cash
        for position in self.positions.values():
            total_value += position.market_value

        return {
            'total_cash': float(self.account_cash),
            'total_assets': float(total_value),
            'buying_power': float(self.account_cash),
            'margin_ratio': 0.0
        }

    async def _ping(self) -> None:
        """模擬心跳"""
        pass

    def set_market_price(self, symbol: str, price: Decimal) -> None:
        """設置市場價格（用於測試）"""
        self.market_prices[symbol] = price

    def _update_position(self, symbol: str, side: str, quantity: Decimal, price: Decimal) -> None:
        """更新倉位"""
        key = symbol
        position = self.positions.get(key)

        if not position:
            # New position
            self.positions[key] = PositionInfo(
                symbol=symbol,
                quantity=quantity if side == 'BUY' else -quantity,
                side='LONG' if side == 'BUY' else 'SHORT',
                market_value=quantity * price,
                average_price=price,
                unrealized_pnl=Decimal('0'),
                percentage=0.0
            )
        else:
            # Update existing position
            current_qty = position.quantity
            new_qty = quantity if side == 'BUY' else -quantity
            total_qty = current_qty + new_qty

            if abs(total_qty) < 0.0001:  # Position closed
                del self.positions[key]
            else:
                # Calculate new average price
                total_cost = (position.average_price * abs(current_qty) + price * abs(new_qty))
                avg_price = total_cost / abs(total_qty)

                position.quantity = total_qty
                position.side = 'LONG' if total_qty > 0 else 'SHORT'
                position.average_price = avg_price
                position.market_value = abs(total_qty) * self.market_prices.get(symbol, price)


class BrokerAdapterFactory:
    """券商適配器工廠"""

    @staticmethod
    def create_adapter(broker_type: str, config: Dict[str, Any]) -> BrokerAdapter:
        """創建券商適配器"""
        broker_config = BrokerConfig(
            broker_type=BrokerType(broker_type.lower()),
            host=config.get('host'),
            port=config.get('port'),
            username=config.get('username'),
            password=config.get('password'),
            api_key=config.get('api_key'),
            secret_key=config.get('secret_key'),
            account_id=config.get('account_id'),
            environment=config.get('environment', 'simulation'),
            timeout=config.get('timeout', 30),
            max_connections=config.get('max_connections', 5),
            retry_attempts=config.get('retry_attempts', 3),
            retry_delay=config.get('retry_delay', 1.0),
            rate_limit=config.get('rate_limit', 10),
            additional_params=config.get('additional_params', {})
        )

        if broker_type.lower() == 'futu':
            return FutuBrokerAdapter(broker_config)
        elif broker_type.lower() == 'simulation':
            return SimulationBrokerAdapter(broker_config)
        else:
            raise ValueError(f"Unsupported broker type: {broker_type}")