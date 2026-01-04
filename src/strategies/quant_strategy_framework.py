"""
Quantitative Strategy Development Framework
量化策略開發框架

提供完整的量化策略開發基礎設施，包括：
- 策略基類和接口定義
- 數據管理模塊
- 信號生成器
- 風險管理集成
- 績效評估工具
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger('QuantStrategy')

class StrategyType(Enum):
    """策略類型枚舉"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    TREND_FOLLOWING = "trend_following"
    PAIR_TRADING = "pair_trading"
    STATISTICAL = "statistical"
    ML_PREDICTIVE = "ml_predictive"
    OPTIONS = "options"
    VOLATILITY = "volatility"

class SignalType(Enum):
    """信號類型枚舉"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"
    REDUCE = "reduce"
    INCREASE = "increase"

@dataclass
class Signal:
    """交易信號數據結構"""
    symbol: str
    signal_type: SignalType
    strength: float  # 信號強度 0-1
    price: float
    timestamp: datetime
    confidence: float  # 信號置信度 0-1
    metadata: Dict[str, Any] = None  # 額外的策略特定數據

@dataclass
class Position:
    """持倉信息"""
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    last_update: datetime = None

@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    strategy_type: StrategyType
    symbols: List[str]
    timeframe: str  # '1m', '5m', '15m', '1h', '1d'
    initial_capital: float
    max_position_size: float
    risk_limit: float
    parameters: Dict[str, Any] = None

class QuantStrategyBase(ABC):
    """量化策略基類"""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.signals_history: List[Signal] = []
        self.performance_metrics: Dict[str, float] = {}
        self.is_initialized = False

        # 日誌記錄器
        self.logger = logging.getLogger(f"Strategy.{config.name}")

        # 初始化策略參數
        self.parameters = config.parameters or {}

    @abstractmethod
    def initialize(self) -> bool:
        """初始化策略，加載必要的數據和模型"""
        pass

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """根據市場數據生成交易信號"""
        pass

    @abstractmethod
    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """根據信號和風險管理計算倉位大小"""
        pass

    def update_position(self, symbol: str, quantity: float, price: float):
        """更新持倉"""
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                current_price=price,
                unrealized_pnl=0.0,
                last_update=datetime.now()
            )
        else:
            position = self.positions[symbol]
            old_quantity = position.quantity
            old_avg_price = position.avg_price

            # 計算新的平均價格
            if (old_quantity > 0 and quantity > 0) or (old_quantity < 0 and quantity < 0):
                # 加倉或減倉
                position.avg_price = (
                    (old_avg_price * abs(old_quantity) + price * abs(quantity - old_quantity)) /
                    abs(quantity)
                )
            else:
                # 平倉或反手
                position.avg_price = price if quantity != 0 else old_avg_price

            position.quantity = quantity
            position.current_price = price
            position.last_update = datetime.now()

            # 計算已實現損益
            if old_quantity * quantity < 0:  # 有部分平倉
                realized_quantity = min(abs(old_quantity), abs(quantity))
                position.realized_pnl += (price - old_avg_price) * realized_quantity

    def calculate_portfolio_value(self) -> float:
        """計算投資組合總價值"""
        total = 0.0
        for position in self.positions.values():
            total += position.quantity * position.current_price + position.realized_pnl
        return total

    def get_risk_metrics(self) -> Dict[str, float]:
        """計算風險指標"""
        portfolio_value = self.calculate_portfolio_value()
        total_exposure = sum(abs(pos.quantity * pos.current_price) for pos in self.positions.values())

        return {
            "portfolio_value": portfolio_value,
            "total_exposure": total_exposure,
            "exposure_ratio": total_exposure / portfolio_value if portfolio_value > 0 else 0,
            "position_count": len([pos for pos in self.positions.values() if pos.quantity != 0]),
            "unrealized_pnl": sum(pos.unrealized_pnl for pos in self.positions.values()),
            "realized_pnl": sum(pos.realized_pnl for pos in self.positions.values())
        }

    def validate_signal(self, signal: Signal) -> bool:
        """驗證信號有效性"""
        # 檢查信號強度
        if not (0 <= signal.strength <= 1):
            return False

        # 檢查信號置信度
        if not (0 <= signal.confidence <= 1):
            return False

        # 檢查倉位限制
        portfolio_value = self.calculate_portfolio_value()
        proposed_size = self.calculate_position_size(signal, portfolio_value)

        if abs(proposed_size * signal.price) > self.config.max_position_size * portfolio_value:
            self.logger.warning(f"信號超過最大倉位限制: {proposed_size}")
            return False

        return True

    def execute_trade(self, signal: Signal) -> Dict[str, Any]:
        """執行交易（模擬）"""
        if not self.validate_signal(signal):
            return {"status": "rejected", "reason": "Invalid signal"}

        portfolio_value = self.calculate_portfolio_value()
        position_size = self.calculate_position_size(signal, portfolio_value)

        # 執行交易邏輯
        if signal.signal_type == SignalType.BUY:
            self.update_position(signal.symbol, position_size, signal.price)
        elif signal.signal_type == SignalType.SELL:
            self.update_position(signal.symbol, -position_size, signal.price)
        elif signal.signal_type == SignalType.CLOSE:
            self.update_position(signal.symbol, 0, signal.price)

        # 記錄信號
        self.signals_history.append(signal)

        return {
            "status": "executed",
            "symbol": signal.symbol,
            "signal_type": signal.signal_type.value,
            "position_size": position_size,
            "price": signal.price,
            "timestamp": signal.timestamp
        }

    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            "name": self.config.name,
            "type": self.config.strategy_type.value,
            "symbols": self.config.symbols,
            "timeframe": self.config.timeframe,
            "parameters": self.parameters,
            "is_initialized": self.is_initialized,
            "positions": {symbol: {
                "quantity": pos.quantity,
                "avg_price": pos.avg_price,
                "unrealized_pnl": pos.unrealized_pnl,
                "realized_pnl": pos.realized_pnl
            } for symbol, pos in self.positions.items()},
            "risk_metrics": self.get_risk_metrics(),
            "signal_count": len(self.signals_history)
        }

class StrategyManager:
    """策略管理器 - 管理多個策略的執行"""

    def __init__(self):
        self.strategies: Dict[str, QuantStrategyBase] = {}
        self.data_provider = None
        self.risk_manager = None

    def register_strategy(self, strategy: QuantStrategyBase):
        """註冊策略"""
        self.strategies[strategy.config.name] = strategy
        self.logger.info(f"已註冊策略: {strategy.config.name}")

    def initialize_all(self) -> bool:
        """初始化所有策略"""
        success = True
        for name, strategy in self.strategies.items():
            try:
                if strategy.initialize():
                    strategy.is_initialized = True
                    self.logger.info(f"策略 {name} 初始化成功")
                else:
                    self.logger.error(f"策略 {name} 初始化失敗")
                    success = False
            except Exception as e:
                self.logger.error(f"策略 {name} 初始化出錯: {str(e)}")
                success = False

        return success

    def run_strategies(self, data: pd.DataFrame) -> Dict[str, List[Dict]]:
        """運行所有策略"""
        results = {}

        for name, strategy in self.strategies.items():
            if not strategy.is_initialized:
                self.logger.warning(f"策略 {name} 未初始化，跳過執行")
                continue

            try:
                # 生成信號
                signals = strategy.generate_signals(data)

                # 執行信號
                executions = []
                for signal in signals:
                    execution = strategy.execute_trade(signal)
                    executions.append(execution)

                results[name] = executions

            except Exception as e:
                self.logger.error(f"策略 {name} 執行出錯: {str(e)}")
                results[name] = [{"status": "error", "error": str(e)}]

        return results

    def get_all_positions(self) -> Dict[str, Dict]:
        """獲取所有策略的持倉"""
        all_positions = {}

        for name, strategy in self.strategies.items():
            positions = {}
            for symbol, pos in strategy.positions.items():
                if pos.quantity != 0:  # 只顯示非零持倉
                    positions[symbol] = {
                        "quantity": pos.quantity,
                        "avg_price": pos.avg_price,
                        "current_price": pos.current_price,
                        "unrealized_pnl": pos.unrealized_pnl,
                        "realized_pnl": pos.realized_pnl
                    }

            if positions:
                all_positions[name] = positions

        return all_positions

    def calculate_portfolio_summary(self) -> Dict[str, float]:
        """計算投資組合總覽"""
        total_value = 0.0
        total_unrealized = 0.0
        total_realized = 0.0
        total_exposure = 0.0

        for strategy in self.strategies.values():
            risk_metrics = strategy.get_risk_metrics()
            total_value += risk_metrics["portfolio_value"]
            total_unrealized += risk_metrics["unrealized_pnl"]
            total_realized += risk_metrics["realized_pnl"]
            total_exposure += risk_metrics["total_exposure"]

        return {
            "total_portfolio_value": total_value,
            "total_unrealized_pnl": total_unrealized,
            "total_realized_pnl": total_realized,
            "total_exposure": total_exposure,
            "exposure_ratio": total_exposure / total_value if total_value > 0 else 0,
            "total_pnl": total_unrealized + total_realized
        }

# 工具函數
def create_strategy_config(
    name: str,
    strategy_type: StrategyType,
    symbols: List[str],
    initial_capital: float = 1000000,
    max_position_size: float = 0.1,
    risk_limit: float = 0.02,
    **kwargs
) -> StrategyConfig:
    """創建策略配置"""
    return StrategyConfig(
        name=name,
        strategy_type=strategy_type,
        symbols=symbols,
        timeframe=kwargs.get('timeframe', '1d'),
        initial_capital=initial_capital,
        max_position_size=max_position_size,
        risk_limit=risk_limit,
        parameters=kwargs
    )

def validate_strategy_parameters(params: Dict[str, Any], required_params: List[str]) -> bool:
    """驗證策略參數"""
    for param in required_params:
        if param not in params:
            logger.error(f"缺少必需參數: {param}")
            return False
    return True