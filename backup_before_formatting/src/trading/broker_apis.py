"""
券商API集成 - 支持多個主要券商

包括Interactive Brokers、TD Ameritrade、ETRADE、Fidelity等
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import aiohttp

from .base_trading_api import (
    AccountInfo,
    BaseTradingAPI,
    MarketData,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)


class InteractiveBrokersAPI(BaseTradingAPI):
    """Interactive Brokers API集成"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.ibkr.com / v1")
        self.api_key = config.get("api_key")
        self.session_id = None
        self._session = None

    async def connect(self) -> bool:
        """連接到Interactive Brokers"""
        try:
            self.logger.info("Connecting to Interactive Brokers...")

            self._session = aiohttp.ClientSession()

            # 測試連接
            async with self._session.get(f"{self.base_url}/status") as response:
                if response.status == 200:
                    self._connected = True
                    self.logger.info("Connected to Interactive Brokers successfully")
                    return True
                else:
                    self.logger.error(f"Connection failed: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """斷開連接"""
        try:
            if self._session:
                await self._session.close()
                self._session = None
            self._connected = False
            self._authenticated = False
            return True
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """身份驗證"""
        try:
            if not self._session:
                await self.connect()

            auth_data = {
                "username": credentials.get("username"),
                "password": credentials.get("password"),
                "api_key": self.api_key,
            }

            async with self._session.post(
                f"{self.base_url}/auth", json=auth_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.session_id = data.get("session_id")
                    self._authenticated = True
                    self.logger.info("Authenticated with Interactive Brokers")
                    return True
                else:
                    self.logger.error(f"Authentication failed: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False

    async def get_account_info(self) -> Optional[AccountInfo]:
        """獲取賬戶信息"""
        try:
            if not self.is_connected():
                return None

            headers = {"Authorization": f"Bearer {self.session_id}"}
            async with self._session.get(
                f"{self.base_url}/accounts", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    account_data = data.get("accounts", [{}])[0]

                    return AccountInfo(
                        account_id=account_data.get("account_id", ""),
                        account_type=account_data.get("account_type", ""),
                        buying_power=Decimal(str(account_data.get("buying_power", 0))),
                        cash=Decimal(str(account_data.get("cash", 0))),
                        equity=Decimal(str(account_data.get("equity", 0))),
                        margin_used=Decimal(str(account_data.get("margin_used", 0))),
                        margin_available=Decimal(
                            str(account_data.get("margin_available", 0))
                        ),
                        day_trading_buying_power=Decimal(
                            str(account_data.get("day_trading_buying_power", 0))
                        ),
                    )
                else:
                    self.logger.error(f"Failed to get account info: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None

    async def get_positions(self) -> List[Position]:
        """獲取持倉信息"""
        try:
            if not self.is_connected():
                return []

            headers = {"Authorization": f"Bearer {self.session_id}"}
            async with self._session.get(
                f"{self.base_url}/positions", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    positions = []

                    for pos_data in data.get("positions", []):
                        position = Position(
                            symbol=pos_data.get("symbol", ""),
                            quantity=Decimal(str(pos_data.get("quantity", 0))),
                            average_price=Decimal(
                                str(pos_data.get("average_price", 0))
                            ),
                            current_price=(
                                Decimal(str(pos_data.get("current_price", 0)))
                                if pos_data.get("current_price")
                                else None
                            ),
                            market_value=(
                                Decimal(str(pos_data.get("market_value", 0)))
                                if pos_data.get("market_value")
                                else None
                            ),
                            unrealized_pnl=(
                                Decimal(str(pos_data.get("unrealized_pnl", 0)))
                                if pos_data.get("unrealized_pnl")
                                else None
                            ),
                            realized_pnl=(
                                Decimal(str(pos_data.get("realized_pnl", 0)))
                                if pos_data.get("realized_pnl")
                                else None
                            ),
                        )
                        positions.append(position)

                    return positions
                else:
                    self.logger.error(f"Failed to get positions: {response.status}")
                    return []

        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    async def get_orders(
        self, status_filter: Optional[OrderStatus] = None
    ) -> List[Order]:
        """獲取訂單列表"""
        try:
            if not self.is_connected():
                return []

            headers = {"Authorization": f"Bearer {self.session_id}"}
            params = {}
            if status_filter:
                params["status"] = status_filter.value

            async with self._session.get(
                f"{self.base_url}/orders", headers=headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    orders = []

                    for order_data in data.get("orders", []):
                        order = Order(
                            order_id=order_data.get("order_id", ""),
                            symbol=order_data.get("symbol", ""),
                            side=OrderSide(order_data.get("side", "buy")),
                            order_type=OrderType(
                                order_data.get("order_type", "market")
                            ),
                            quantity=Decimal(str(order_data.get("quantity", 0))),
                            price=(
                                Decimal(str(order_data.get("price", 0)))
                                if order_data.get("price")
                                else None
                            ),
                            stop_price=(
                                Decimal(str(order_data.get("stop_price", 0)))
                                if order_data.get("stop_price")
                                else None
                            ),
                            status=OrderStatus(order_data.get("status", "pending")),
                            filled_quantity=Decimal(
                                str(order_data.get("filled_quantity", 0))
                            ),
                            average_fill_price=(
                                Decimal(str(order_data.get("average_fill_price", 0)))
                                if order_data.get("average_fill_price")
                                else None
                            ),
                            commission=(
                                Decimal(str(order_data.get("commission", 0)))
                                if order_data.get("commission")
                                else None
                            ),
                            created_at=datetime.fromisoformat(
                                order_data.get("created_at", datetime.now().isoformat())
                            ),
                            updated_at=datetime.fromisoformat(
                                order_data.get("updated_at", datetime.now().isoformat())
                            ),
                            client_order_id=order_data.get("client_order_id"),
                        )
                        orders.append(order)

                    return orders
                else:
                    self.logger.error(f"Failed to get orders: {response.status}")
                    return []

        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []

    async def place_order(self, order: Order) -> Optional[str]:
        """下單"""
        try:
            if not self.is_connected():
                return None

            # 驗證訂單
            errors = await self.validate_order(order)
            if errors:
                self.logger.error(f"Order validation failed: {errors}")
                return None

            headers = {"Authorization": f"Bearer {self.session_id}"}
            order_data = {
                "symbol": order.symbol,
                "side": order.side.value,
                "order_type": order.order_type.value,
                "quantity": float(order.quantity),
                "price": float(order.price) if order.price else None,
                "stop_price": float(order.stop_price) if order.stop_price else None,
                "client_order_id": order.client_order_id,
            }

            async with self._session.post(
                f"{self.base_url}/orders", headers=headers, json=order_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    order_id = data.get("order_id")
                    self.logger.info(f"Order placed successfully: {order_id}")
                    return order_id
                else:
                    self.logger.error(f"Failed to place order: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """取消訂單"""
        try:
            if not self.is_connected():
                return False

            headers = {"Authorization": f"Bearer {self.session_id}"}
            async with self._session.delete(
                f"{self.base_url}/orders/{order_id}", headers=headers
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Order cancelled successfully: {order_id}")
                    return True
                else:
                    self.logger.error(f"Failed to cancel order: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False

    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> bool:
        """修改訂單"""
        try:
            if not self.is_connected():
                return False

            headers = {"Authorization": f"Bearer {self.session_id}"}
            async with self._session.patch(
                f"{self.base_url}/orders/{order_id}",
                headers=headers,
                json=modifications,
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Order modified successfully: {order_id}")
                    return True
                else:
                    self.logger.error(f"Failed to modify order: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error modifying order: {e}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """獲取訂單狀態"""
        try:
            if not self.is_connected():
                return None

            headers = {"Authorization": f"Bearer {self.session_id}"}
            async with self._session.get(
                f"{self.base_url}/orders/{order_id}", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return OrderStatus(data.get("status", "pending"))
                else:
                    self.logger.error(f"Failed to get order status: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return None

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """獲取市場數據"""
        try:
            if not self.is_connected():
                return None

            headers = {"Authorization": f"Bearer {self.session_id}"}
            async with self._session.get(
                f"{self.base_url}/market - data/{symbol}", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    return MarketData(
                        symbol=symbol,
                        bid_price=(
                            Decimal(str(data.get("bid_price", 0)))
                            if data.get("bid_price")
                            else None
                        ),
                        ask_price=(
                            Decimal(str(data.get("ask_price", 0)))
                            if data.get("ask_price")
                            else None
                        ),
                        last_price=(
                            Decimal(str(data.get("last_price", 0)))
                            if data.get("last_price")
                            else None
                        ),
                        volume=data.get("volume"),
                        high_price=(
                            Decimal(str(data.get("high_price", 0)))
                            if data.get("high_price")
                            else None
                        ),
                        low_price=(
                            Decimal(str(data.get("low_price", 0)))
                            if data.get("low_price")
                            else None
                        ),
                        open_price=(
                            Decimal(str(data.get("open_price", 0)))
                            if data.get("open_price")
                            else None
                        ),
                    )
                else:
                    self.logger.error(f"Failed to get market data: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return None

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> List[Dict[str, Any]]:
        """獲取歷史數據"""
        try:
            if not self.is_connected():
                return []

            headers = {"Authorization": f"Bearer {self.session_id}"}
            params = {
                "symbol": symbol,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "interval": interval,
            }

            async with self._session.get(
                f"{self.base_url}/historical - data", headers=headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    self.logger.error(
                        f"Failed to get historical data: {response.status}"
                    )
                    return []

        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return []


class TDAmeritradeAPI(BaseTradingAPI):
    """TD Ameritrade API集成"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.tdameritrade.com / v1")
        self.client_id = config.get("client_id")
        self.access_token = None
        self._session = None

    async def connect(self) -> bool:
        """連接到TD Ameritrade"""
        try:
            self.logger.info("Connecting to TD Ameritrade...")

            self._session = aiohttp.ClientSession()
            self._connected = True
            self.logger.info("Connected to TD Ameritrade successfully")
            return True

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """斷開連接"""
        try:
            if self._session:
                await self._session.close()
                self._session = None
            self._connected = False
            self._authenticated = False
            return True
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """身份驗證"""
        try:
            if not self._session:
                await self.connect()

            # TD Ameritrade使用OAuth 2.0
            auth_data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "code": credentials.get("auth_code"),
                "redirect_uri": credentials.get("redirect_uri"),
            }

            async with self._session.post(
                f"{self.base_url}/oauth / token", data=auth_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get("access_token")
                    self._authenticated = True
                    self.logger.info("Authenticated with TD Ameritrade")
                    return True
                else:
                    self.logger.error(f"Authentication failed: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False

    async def get_account_info(self) -> Optional[AccountInfo]:
        """獲取賬戶信息"""
        try:
            if not self.is_connected():
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self._session.get(
                f"{self.base_url}/accounts", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    account_data = data.get("securitiesAccount", {})

                    return AccountInfo(
                        account_id=account_data.get("accountId", ""),
                        account_type=account_data.get("type", ""),
                        buying_power=Decimal(str(account_data.get("buyingPower", 0))),
                        cash=Decimal(
                            str(
                                account_data.get("cash", {}).get(
                                    "cashAvailableForTrading", 0
                                )
                            )
                        ),
                        equity=Decimal(str(account_data.get("currentEquity", 0))),
                        margin_used=Decimal(str(account_data.get("marginUsed", 0))),
                        margin_available=Decimal(
                            str(account_data.get("marginAvailable", 0))
                        ),
                        day_trading_buying_power=Decimal(
                            str(account_data.get("dayTradingBuyingPower", 0))
                        ),
                    )
                else:
                    self.logger.error(f"Failed to get account info: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None

    async def get_positions(self) -> List[Position]:
        """獲取持倉信息"""
        try:
            if not self.is_connected():
                return []

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self._session.get(
                f"{self.base_url}/accounts / positions", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    positions = []

                    for pos_data in data.get("positions", []):
                        instrument = pos_data.get("instrument", {})
                        position = Position(
                            symbol=instrument.get("symbol", ""),
                            quantity=Decimal(str(pos_data.get("longQuantity", 0))),
                            average_price=Decimal(str(pos_data.get("averagePrice", 0))),
                            current_price=(
                                Decimal(str(pos_data.get("currentDayProfitLoss", 0)))
                                if pos_data.get("currentDayProfitLoss")
                                else None
                            ),
                            market_value=(
                                Decimal(str(pos_data.get("marketValue", 0)))
                                if pos_data.get("marketValue")
                                else None
                            ),
                            unrealized_pnl=(
                                Decimal(str(pos_data.get("unrealizedProfitLoss", 0)))
                                if pos_data.get("unrealizedProfitLoss")
                                else None
                            ),
                            realized_pnl=(
                                Decimal(str(pos_data.get("realizedProfitLoss", 0)))
                                if pos_data.get("realizedProfitLoss")
                                else None
                            ),
                        )
                        positions.append(position)

                    return positions
                else:
                    self.logger.error(f"Failed to get positions: {response.status}")
                    return []

        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    async def get_orders(
        self, status_filter: Optional[OrderStatus] = None
    ) -> List[Order]:
        """獲取訂單列表"""
        try:
            if not self.is_connected():
                return []

            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {}
            if status_filter:
                params["status"] = status_filter.value

            async with self._session.get(
                f"{self.base_url}/orders", headers=headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    orders = []

                    for order_data in data.get("orders", []):
                        order = Order(
                            order_id=order_data.get("orderId", ""),
                            symbol=order_data.get("symbol", ""),
                            side=OrderSide(
                                order_data.get("orderLegCollection", [{}])[0].get(
                                    "instruction", "buy"
                                )
                            ),
                            order_type=OrderType(order_data.get("orderType", "market")),
                            quantity=Decimal(str(order_data.get("quantity", 0))),
                            price=(
                                Decimal(str(order_data.get("price", 0)))
                                if order_data.get("price")
                                else None
                            ),
                            status=OrderStatus(order_data.get("status", "pending")),
                            filled_quantity=Decimal(
                                str(order_data.get("filledQuantity", 0))
                            ),
                            created_at=datetime.fromisoformat(
                                order_data.get(
                                    "enteredTime", datetime.now().isoformat()
                                )
                            ),
                            updated_at=datetime.fromisoformat(
                                order_data.get("closeTime", datetime.now().isoformat())
                            ),
                        )
                        orders.append(order)

                    return orders
                else:
                    self.logger.error(f"Failed to get orders: {response.status}")
                    return []

        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []

    async def place_order(self, order: Order) -> Optional[str]:
        """下單"""
        try:
            if not self.is_connected():
                return None

            # 驗證訂單
            errors = await self.validate_order(order)
            if errors:
                self.logger.error(f"Order validation failed: {errors}")
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            order_data = {
                "orderType": order.order_type.value.upper(),
                "session": "NORMAL",
                "duration": "DAY",
                "orderStrategyType": "SINGLE",
                "orderLegCollection": [
                    {
                        "instruction": order.side.value.upper(),
                        "quantity": int(order.quantity),
                        "instrument": {"symbol": order.symbol, "assetType": "EQUITY"},
                    }
                ],
            }

            if order.order_type == OrderType.LIMIT and order.price:
                order_data["price"] = float(order.price)

            async with self._session.post(
                f"{self.base_url}/orders", headers=headers, json=order_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    order_id = data.get("orderId")
                    self.logger.info(f"Order placed successfully: {order_id}")
                    return order_id
                else:
                    self.logger.error(f"Failed to place order: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """取消訂單"""
        try:
            if not self.is_connected():
                return False

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self._session.delete(
                f"{self.base_url}/orders/{order_id}", headers=headers
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Order cancelled successfully: {order_id}")
                    return True
                else:
                    self.logger.error(f"Failed to cancel order: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False

    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> bool:
        """修改訂單"""
        try:
            if not self.is_connected():
                return False

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self._session.patch(
                f"{self.base_url}/orders/{order_id}",
                headers=headers,
                json=modifications,
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Order modified successfully: {order_id}")
                    return True
                else:
                    self.logger.error(f"Failed to modify order: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Error modifying order: {e}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """獲取訂單狀態"""
        try:
            if not self.is_connected():
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self._session.get(
                f"{self.base_url}/orders/{order_id}", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return OrderStatus(data.get("status", "pending"))
                else:
                    self.logger.error(f"Failed to get order status: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return None

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """獲取市場數據"""
        try:
            if not self.is_connected():
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self._session.get(
                f"{self.base_url}/marketdata/{symbol}/quotes", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    quote_data = data.get(symbol, {})

                    return MarketData(
                        symbol=symbol,
                        bid_price=(
                            Decimal(str(quote_data.get("bidPrice", 0)))
                            if quote_data.get("bidPrice")
                            else None
                        ),
                        ask_price=(
                            Decimal(str(quote_data.get("askPrice", 0)))
                            if quote_data.get("askPrice")
                            else None
                        ),
                        last_price=(
                            Decimal(str(quote_data.get("lastPrice", 0)))
                            if quote_data.get("lastPrice")
                            else None
                        ),
                        volume=quote_data.get("totalVolume"),
                        high_price=(
                            Decimal(str(quote_data.get("highPrice", 0)))
                            if quote_data.get("highPrice")
                            else None
                        ),
                        low_price=(
                            Decimal(str(quote_data.get("lowPrice", 0)))
                            if quote_data.get("lowPrice")
                            else None
                        ),
                        open_price=(
                            Decimal(str(quote_data.get("openPrice", 0)))
                            if quote_data.get("openPrice")
                            else None
                        ),
                    )
                else:
                    self.logger.error(f"Failed to get market data: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return None

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> List[Dict[str, Any]]:
        """獲取歷史數據"""
        try:
            if not self.is_connected():
                return []

            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {
                "symbol": symbol,
                "startDate": int(start_date.timestamp() * 1000),
                "endDate": int(end_date.timestamp() * 1000),
                "frequencyType": "daily" if interval == "1d" else "minute",
                "frequency": 1,
            }

            async with self._session.get(
                f"{self.base_url}/marketdata/{symbol}/pricehistory",
                headers=headers,
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("candles", [])
                else:
                    self.logger.error(
                        f"Failed to get historical data: {response.status}"
                    )
                    return []

        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return []


# 其他券商API的簡化實現
class ETRADEAPI(BaseTradingAPI):
    """ETRADE API集成（簡化實現）"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger.warning("ETRADE API implementation is simplified")

    async def connect(self) -> bool:
        self._connected = True
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        return True

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        self._authenticated = True
        return True

    async def get_account_info(self) -> Optional[AccountInfo]:
        return AccountInfo(account_id="demo", account_type="demo")

    async def get_positions(self) -> List[Position]:
        return []

    async def get_orders(
        self, status_filter: Optional[OrderStatus] = None
    ) -> List[Order]:
        return []

    async def place_order(self, order: Order) -> Optional[str]:
        return f"etrade_{order.symbol}_{datetime.now().timestamp()}"

    async def cancel_order(self, order_id: str) -> bool:
        return True

    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> bool:
        return True

    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        return OrderStatus.FILLED

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        return MarketData(symbol=symbol, last_price=Decimal("100.00"))

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> List[Dict[str, Any]]:
        return []


class FidelityAPI(BaseTradingAPI):
    """Fidelity API集成（簡化實現）"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger.warning("Fidelity API implementation is simplified")

    async def connect(self) -> bool:
        self._connected = True
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        return True

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        self._authenticated = True
        return True

    async def get_account_info(self) -> Optional[AccountInfo]:
        return AccountInfo(account_id="demo", account_type="demo")

    async def get_positions(self) -> List[Position]:
        return []

    async def get_orders(
        self, status_filter: Optional[OrderStatus] = None
    ) -> List[Order]:
        return []

    async def place_order(self, order: Order) -> Optional[str]:
        return f"fidelity_{order.symbol}_{datetime.now().timestamp()}"

    async def cancel_order(self, order_id: str) -> bool:
        return True

    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> bool:
        return True

    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        return OrderStatus.FILLED

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        return MarketData(symbol=symbol, last_price=Decimal("100.00"))

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> List[Dict[str, Any]]:
        return []
