"""
持倉管理器 - 管理投資組合持倉

追蹤持倉變化、計算盈虧和風險指標
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .base_trading_api import Position


class PositionManager:
    """持倉管理器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.trading.position_manager")
        self.positions: Dict[str, Position] = {}
        self.position_history: List[Position] = []
        self.is_running = False

    async def add_position(self, position: Position) -> bool:
        """添加持倉"""
        try:
            self.positions[position.symbol] = position
            self.logger.info(f"Added position: {position.symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add position: {e}")
            return False

    async def update_position(self, symbol: str, position: Position) -> bool:
        """更新持倉"""
        try:
            if symbol in self.positions:
                self.positions[symbol] = position
                self.logger.info(f"Updated position: {symbol}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update position: {e}")
            return False

    async def remove_position(self, symbol: str) -> bool:
        """移除持倉"""
        try:
            if symbol in self.positions:
                position = self.positions[symbol]
                self.position_history.append(position)
                del self.positions[symbol]
                self.logger.info(f"Removed position: {symbol}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove position: {e}")
            return False

    async def get_position(self, symbol: str) -> Optional[Position]:
        """獲取持倉"""
        return self.positions.get(symbol)

    async def get_all_positions(self) -> Dict[str, Position]:
        """獲取所有持倉"""
        return self.positions.copy()

    async def calculate_portfolio_value(self) -> Decimal:
        """計算投資組合總價值"""
        try:
            total_value = Decimal("0")
            for position in self.positions.values():
                total_value += position.market_value
            return total_value
        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio value: {e}")
            return Decimal("0")

    async def calculate_total_pnl(self) -> Decimal:
        """計算總盈虧"""
        try:
            total_pnl = Decimal("0")
            for position in self.positions.values():
                total_pnl += position.pnl
            return total_pnl
        except Exception as e:
            self.logger.error(f"Failed to calculate total PnL: {e}")
            return Decimal("0")

    async def calculate_portfolio_weights(self) -> Dict[str, float]:
        """計算投資組合權重"""
        try:
            portfolio_value = await self.calculate_portfolio_value()
            if portfolio_value == 0:
                return {}

            weights = {}
            for symbol, position in self.positions.items():
                weight = float(position.market_value / portfolio_value)
                weights[symbol] = weight

            return weights
        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio weights: {e}")
            return {}

    async def get_position_statistics(self) -> Dict[str, Any]:
        """獲取持倉統計信息"""
        try:
            total_positions = len(self.positions)
            total_value = await self.calculate_portfolio_value()
            total_pnl = await self.calculate_total_pnl()
            weights = await self.calculate_portfolio_weights()

            return {
                "total_positions": total_positions,
                "total_value": float(total_value),
                "total_pnl": float(total_pnl),
                "weights": weights,
                "positions": {
                    symbol: {
                        "quantity": float(pos.quantity),
                        "market_value": float(pos.market_value),
                        "pnl": float(pos.pnl),
                        "weight": weights.get(symbol, 0.0),
                    }
                    for symbol, pos in self.positions.items()
                },
            }
        except Exception as e:
            self.logger.error(f"Failed to get position statistics: {e}")
            return {}

    async def start(self) -> bool:
        """啟動持倉管理器"""
        try:
            self.logger.info("Starting position manager...")
            self.is_running = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to start position manager: {e}")
            return False

    async def stop(self) -> bool:
        """停止持倉管理器"""
        try:
            self.logger.info("Stopping position manager...")
            self.is_running = False
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop position manager: {e}")
            return False

    async def cleanup(self) -> None:
        """清理資源"""
        try:
            await self.stop()
            self.positions.clear()
            self.position_history.clear()
            self.logger.info("Position manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during position manager cleanup: {e}")
