"""
交易管理器 - 統一管理多個交易API

協調多個券商和交易所的交易操作
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

from .base_trading_api import BaseTradingAPI, OrderType, OrderStatus, OrderSide, Order, Position, AccountInfo, MarketData


class TradingManager:
    """交易管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.trading.manager")
        self.apis: Dict[str, BaseTradingAPI] = {}
        self.is_running = False
    
    async def add_api(self, name: str, api: BaseTradingAPI) -> bool:
        """添加交易API"""
        try:
            self.apis[name] = api
            await api.connect()
            await api.authenticate()
            self.logger.info(f"Added trading API: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add trading API {name}: {e}")
            return False
    
    async def remove_api(self, name: str) -> bool:
        """移除交易API"""
        try:
            if name in self.apis:
                await self.apis[name].disconnect()
                del self.apis[name]
                self.logger.info(f"Removed trading API: {name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove trading API {name}: {e}")
            return False
    
    async def get_all_accounts(self) -> Dict[str, AccountInfo]:
        """獲取所有賬戶信息"""
        accounts = {}
        for name, api in self.apis.items():
            try:
                account_info = await api.get_account_info()
                if account_info:
                    accounts[name] = account_info
            except Exception as e:
                self.logger.error(f"Failed to get account info from {name}: {e}")
        return accounts
    
    async def get_all_positions(self) -> Dict[str, List[Position]]:
        """獲取所有持倉"""
        positions = {}
        for name, api in self.apis.items():
            try:
                api_positions = await api.get_positions()
                positions[name] = api_positions
            except Exception as e:
                self.logger.error(f"Failed to get positions from {name}: {e}")
        return positions
    
    async def place_order_on_api(self, api_name: str, order: Order) -> Optional[str]:
        """在指定API下單"""
        try:
            if api_name not in self.apis:
                self.logger.error(f"API {api_name} not found")
                return None
            
            api = self.apis[api_name]
            order_id = await api.place_order(order)
            if order_id:
                self.logger.info(f"Order placed on {api_name}: {order_id}")
            return order_id
        except Exception as e:
            self.logger.error(f"Failed to place order on {api_name}: {e}")
            return None
    
    async def cancel_order_on_api(self, api_name: str, order_id: str) -> bool:
        """在指定API取消訂單"""
        try:
            if api_name not in self.apis:
                self.logger.error(f"API {api_name} not found")
                return False
            
            api = self.apis[api_name]
            success = await api.cancel_order(order_id)
            if success:
                self.logger.info(f"Order cancelled on {api_name}: {order_id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to cancel order on {api_name}: {e}")
            return False
    
    async def get_market_data_from_api(self, api_name: str, symbol: str) -> Optional[MarketData]:
        """從指定API獲取市場數據"""
        try:
            if api_name not in self.apis:
                self.logger.error(f"API {api_name} not found")
                return None
            
            api = self.apis[api_name]
            return await api.get_market_data(symbol)
        except Exception as e:
            self.logger.error(f"Failed to get market data from {api_name}: {e}")
            return None
    
    async def start(self) -> bool:
        """啟動交易管理器"""
        try:
            self.logger.info("Starting trading manager...")
            self.is_running = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to start trading manager: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止交易管理器"""
        try:
            self.logger.info("Stopping trading manager...")
            self.is_running = False
            
            # 斷開所有API連接
            for name, api in self.apis.items():
                try:
                    await api.disconnect()
                except Exception as e:
                    self.logger.error(f"Error disconnecting {name}: {e}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop trading manager: {e}")
            return False
    
    async def cleanup(self) -> None:
        """清理資源"""
        try:
            await self.stop()
            self.apis.clear()
            self.logger.info("Trading manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during trading manager cleanup: {e}")