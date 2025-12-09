"""
訂單管理器 - 管理交易訂單的生命週期

追蹤訂單狀態、執行情況和歷史記錄
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .base_trading_api import Order, OrderSide, OrderStatus, OrderType


class OrderManager:
    """訂單管理器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.trading.order_manager")
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.is_running = False

    async def add_order(self, order: Order) -> bool:
        """添加訂單到管理器"""
        try:
            self.orders[order.order_id] = order
            self.logger.info(f"Added order to manager: {order.order_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add order: {e}")
            return False

    async def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """更新訂單狀態"""
        try:
            if order_id in self.orders:
                self.orders[order_id].status = status
                self.orders[order_id].updated_at = datetime.now()
                self.logger.info(f"Updated order status: {order_id} -> {status}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update order status: {e}")
            return False

    async def get_order(self, order_id: str) -> Optional[Order]:
        """獲取訂單"""
        return self.orders.get(order_id)

    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """根據狀態獲取訂單"""
        return [order for order in self.orders.values() if order.status == status]

    async def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """根據標的獲取訂單"""
        return [order for order in self.orders.values() if order.symbol == symbol]

    async def cancel_order(self, order_id: str) -> bool:
        """取消訂單"""
        try:
            if order_id in self.orders:
                self.orders[order_id].status = OrderStatus.CANCELLED
                self.orders[order_id].updated_at = datetime.now()
                self.logger.info(f"Cancelled order: {order_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {e}")
            return False

    async def archive_completed_orders(self) -> None:
        """歸檔已完成的訂單"""
        try:
            completed_orders = []
            for order_id, order in self.orders.items():
                if order.status in [
                    OrderStatus.FILLED,
                    OrderStatus.CANCELLED,
                    OrderStatus.REJECTED,
                ]:
                    completed_orders.append(order_id)
                    self.order_history.append(order)

            for order_id in completed_orders:
                del self.orders[order_id]

            if completed_orders:
                self.logger.info(f"Archived {len(completed_orders)} completed orders")
        except Exception as e:
            self.logger.error(f"Failed to archive completed orders: {e}")

    async def get_order_statistics(self) -> Dict[str, Any]:
        """獲取訂單統計信息"""
        try:
            total_orders = len(self.orders) + len(self.order_history)
            active_orders = len(self.orders)
            completed_orders = len(self.order_history)

            status_counts = {}
            for order in list(self.orders.values()) + self.order_history:
                status = order.status
                status_counts[status] = status_counts.get(status, 0) + 1

            return {
                "total_orders": total_orders,
                "active_orders": active_orders,
                "completed_orders": completed_orders,
                "status_counts": status_counts,
            }
        except Exception as e:
            self.logger.error(f"Failed to get order statistics: {e}")
            return {}

    async def start(self) -> bool:
        """啟動訂單管理器"""
        try:
            self.logger.info("Starting order manager...")
            self.is_running = True

            # 啟動定期歸檔任務
            asyncio.create_task(self._periodic_archive())

            return True
        except Exception as e:
            self.logger.error(f"Failed to start order manager: {e}")
            return False

    async def stop(self) -> bool:
        """停止訂單管理器"""
        try:
            self.logger.info("Stopping order manager...")
            self.is_running = False
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop order manager: {e}")
            return False

    async def _periodic_archive(self) -> None:
        """定期歸檔任務"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # 每5分鐘歸檔一次
                await self.archive_completed_orders()
            except Exception as e:
                self.logger.error(f"Error in periodic archive: {e}")

    async def cleanup(self) -> None:
        """清理資源"""
        try:
            await self.stop()
            self.orders.clear()
            self.order_history.clear()
            self.logger.info("Order manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during order manager cleanup: {e}")
