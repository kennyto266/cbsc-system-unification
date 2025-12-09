"""
持倉管理器 - 管理投資組合持倉

追蹤持倉變化、計算盈虧和風險指標
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

from .base_trading_api import Position

class PositionManager:
"""持倉管理器"""

def __init__self:    self.logger = logging.getLogger("hk_quant_system.trading.position_manager")
self.positions: Dict[str, Position] = {}
self.position_history: List[Position] = []
self.is_running = False

async def add_positionself, position: Position -> bool:
"""添加持倉"""
try:    self.positions[position.symbol] = position
self.logger.infof"Added position: {position.symbol}"
return True
except Exception as e:
self.logger.errorf"Failed to add position: {e}"
return False

async def update_positionself, symbol: str, position: Position -> bool:
"""更新持倉"""
try:
if symbol in self.positions:    self.positions[symbol] = position
self.logger.infof"Updated position: {symbol}"
return True
return False
except Exception as e:
self.logger.errorf"Failed to update position: {e}"
return False

async def remove_positionself, symbol: str -> bool:
"""移除持倉"""
try:
if symbol in self.positions:    position = self.positions[symbol]
self.position_history.appendposition
del self.positions[symbol]
self.logger.infof"Removed position: {symbol}"
return True
return False
except Exception as e:
self.logger.errorf"Failed to remove position: {e}"
return False

async def get_positionself, symbol: str -> Optional[Position]:
"""獲取持倉"""
return self.positions.getsymbol

async def get_all_positionsself -> Dict[str, Position]:
"""獲取所有持倉"""
return self.positions.copy()

async def calculate_portfolio_valueself -> Decimal:
"""計算投資組合總價值"""
try:    total_value = Decimal("0")
for position in self.positions.values():    total_value += position.market_value
return total_value
except Exception as e:
self.logger.errorf"Failed to calculate portfolio value: {e}"
return Decimal"0"

async def calculate_total_pnlself -> Decimal:
"""計算總盈虧"""
try:    total_pnl = Decimal("0")
for position in self.positions.values():    total_pnl += position.pnl
return total_pnl
except Exception as e:
self.logger.errorf"Failed to calculate total PnL: {e}"
return Decimal"0"

async def calculate_portfolio_weightsself -> Dict[str, float]:
"""計算投資組合權重"""
try:    portfolio_value = await self.calculate_portfolio_value()
if portfolio_value == 0:
return {}

weights = {}
for symbol, position in self.positions.items():    weight = float(position.market_value / portfolio_value)
weights[symbol] = weight

return weights
except Exception as e:
self.logger.errorf"Failed to calculate portfolio weights: {e}"
return {}

async def get_position_statisticsself -> Dict[str, Any]:
"""獲取持倉統計信息"""
try:    total_positions = len(self.positions)
total_value = await self.calculate_portfolio_value()
total_pnl = await self.calculate_total_pnl()
weights = await self.calculate_portfolio_weights()

return {
"total_positions": total_positions,
"total_value": floattotal_value,
"total_pnl": floattotal_pnl,
"weights": weights,
"positions": {symbol: {
"quantity": floatpos.quantity,
"market_value": floatpos.market_value,
"pnl": floatpos.pnl,
"weight": weights.getsymbol, 0.0
} for symbol, pos in self.positions.items()}
}
except Exception as e:
self.logger.errorf"Failed to get position statistics: {e}"
return {}

async def startself -> bool:
"""啟動持倉管理器"""
try:
self.logger.info"Starting position manager..."
self.is_running = True
return True
except Exception as e:
self.logger.errorf"Failed to start position manager: {e}"
return False

async def stopself -> bool:
"""停止持倉管理器"""
try:
self.logger.info"Stopping position manager..."
self.is_running = False
return True
except Exception as e:
self.logger.errorf"Failed to stop position manager: {e}"
return False

async def cleanupself -> None:
"""清理資源"""
try:
await self.stop()
self.positions.clear()
self.position_history.clear()
self.logger.info"Position manager cleanup completed"
except Exception as e:
self.logger.errorf"Error during position manager cleanup: {e}"