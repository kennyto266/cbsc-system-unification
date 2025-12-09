"""
港股量化交易 AI Agent 系统 - 量化交易员Agent

负责识别交易机会、执行买卖订单、优化交易策略。
提供自动化交易执行能力，支持高频交易和算法交易。
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..agents.base_agent import AgentConfig, BaseAgent
from ..agents.protocol import AgentProtocol, MessagePriority, MessageType
from ..core import SystemConfig, SystemConstants
from ..core.message_queue import Message, MessageQueue
from ..models.base import BaseModel, MarketData, SignalType, TradingSignal


class OrderStatus(str, Enum):
    """订单状态"""

    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderType(str, Enum):
    """订单类型"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class Order(BaseModel):
    """订单模型"""

    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: OrderType
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_price: Optional[float] = None
    commission: float = 0.0
    created_at: datetime = None
    updated_at: datetime = None
    signal_id: Optional[str] = None
    agent_id: str = "quantitative_trader"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class Position(BaseModel):
    """持仓模型"""

    symbol: str
    quantity: int
    average_price: float
    market_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class TradingPerformance(BaseModel):
    """交易绩效模型"""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class SignalDetector:
    """信号检测器"""

    def __init__(self):
        self.logger = logging.getLogger(
            "hk_quant_system.quantitative_trader.signal_detector"
        )

    def detect_signals(
        self,
        market_data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_price: float,
    ) -> List[Dict[str, Any]]:
        """检测交易信号"""

        signals = []

        try:
            # 技术指标信号
            tech_signals = self._detect_technical_signals(indicators, current_price)
            signals.extend(tech_signals)

            # 价格突破信号
            breakout_signals = self._detect_breakout_signals(market_data, current_price)
            signals.extend(breakout_signals)

            # 均值回归信号
            mean_reversion_signals = self._detect_mean_reversion_signals(
                market_data, indicators
            )
            signals.extend(mean_reversion_signals)

            # 动量信号
            momentum_signals = self._detect_momentum_signals(market_data, indicators)
            signals.extend(momentum_signals)

        except Exception as e:
            self.logger.error(f"信号检测失败: {e}")

        return signals

    def _detect_technical_signals(
        self, indicators: Dict[str, Any], current_price: float
    ) -> List[Dict[str, Any]]:
        """检测技术指标信号"""
        signals = []

        try:
            # MACD信号
            macd = indicators.get("macd", 0)
            macd_signal = indicators.get("macd_signal", 0)
            macd_histogram = indicators.get("macd_histogram", 0)

            if macd > macd_signal and macd_histogram > 0:
                signals.append(
                    {
                        "type": "technical",
                        "signal_type": SignalType.BUY,
                        "confidence": 0.7,
                        "reasoning": "MACD金叉信号",
                        "indicators": {"macd": macd, "macd_signal": macd_signal},
                    }
                )
            elif macd < macd_signal and macd_histogram < 0:
                signals.append(
                    {
                        "type": "technical",
                        "signal_type": SignalType.SELL,
                        "confidence": 0.7,
                        "reasoning": "MACD死叉信号",
                        "indicators": {"macd": macd, "macd_signal": macd_signal},
                    }
                )

            # RSI信号
            rsi = indicators.get("rsi", 50)
            if rsi < 30:
                signals.append(
                    {
                        "type": "technical",
                        "signal_type": SignalType.BUY,
                        "confidence": 0.6,
                        "reasoning": "RSI超卖信号",
                        "indicators": {"rsi": rsi},
                    }
                )
            elif rsi > 70:
                signals.append(
                    {
                        "type": "technical",
                        "signal_type": SignalType.SELL,
                        "confidence": 0.6,
                        "reasoning": "RSI超买信号",
                        "indicators": {"rsi": rsi},
                    }
                )

        except Exception as e:
            self.logger.error(f"技术指标信号检测失败: {e}")

        return signals

    def _detect_breakout_signals(
        self, market_data: pd.DataFrame, current_price: float
    ) -> List[Dict[str, Any]]:
        """检测突破信号"""
        signals = []

        try:
            if len(market_data) < 20:
                return signals

            # 计算阻力位和支撑位
            high_20 = market_data["high"].rolling(window=20).max().iloc[-1]
            low_20 = market_data["low"].rolling(window=20).min().iloc[-1]

            # 突破阻力位
            if current_price > high_20 * 1.001:  # 0.1 % 的突破阈值
                signals.append(
                    {
                        "type": "breakout",
                        "signal_type": SignalType.BUY,
                        "confidence": 0.8,
                        "reasoning": f"突破阻力位 {high_20:.2f}",
                        "indicators": {
                            "resistance": high_20,
                            "current_price": current_price,
                        },
                    }
                )

            # 跌破支撑位
            elif current_price < low_20 * 0.999:  # 0.1 % 的跌破阈值
                signals.append(
                    {
                        "type": "breakout",
                        "signal_type": SignalType.SELL,
                        "confidence": 0.8,
                        "reasoning": f"跌破支撑位 {low_20:.2f}",
                        "indicators": {
                            "support": low_20,
                            "current_price": current_price,
                        },
                    }
                )

        except Exception as e:
            self.logger.error(f"突破信号检测失败: {e}")

        return signals

    def _detect_mean_reversion_signals(
        self, market_data: pd.DataFrame, indicators: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检测均值回归信号"""
        signals = []

        try:
            if len(market_data) < 50:
                return signals

            current_price = market_data["close"].iloc[-1]
            sma_50 = indicators.get("sma_50", current_price)
            bollinger_upper = indicators.get("bollinger_upper", current_price)
            bollinger_lower = indicators.get("bollinger_lower", current_price)

            # 价格偏离均值的程度
            deviation = (current_price - sma_50) / sma_50

            # 布林带均值回归
            if current_price > bollinger_upper:
                signals.append(
                    {
                        "type": "mean_reversion",
                        "signal_type": SignalType.SELL,
                        "confidence": 0.6,
                        "reasoning": "价格触及布林带上轨，预期均值回归",
                        "indicators": {
                            "deviation": deviation,
                            "bollinger_position": "upper",
                        },
                    }
                )
            elif current_price < bollinger_lower:
                signals.append(
                    {
                        "type": "mean_reversion",
                        "signal_type": SignalType.BUY,
                        "confidence": 0.6,
                        "reasoning": "价格触及布林带下轨，预期均值回归",
                        "indicators": {
                            "deviation": deviation,
                            "bollinger_position": "lower",
                        },
                    }
                )

        except Exception as e:
            self.logger.error(f"均值回归信号检测失败: {e}")

        return signals

    def _detect_momentum_signals(
        self, market_data: pd.DataFrame, indicators: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检测动量信号"""
        signals = []

        try:
            if len(market_data) < 20:
                return signals

            # 计算价格动量
            price_change_5 = (
                market_data["close"].iloc[-1] - market_data["close"].iloc[-6]
            ) / market_data["close"].iloc[-6]
            price_change_20 = (
                market_data["close"].iloc[-1] - market_data["close"].iloc[-21]
            ) / market_data["close"].iloc[-21]

            # 成交量动量
            volume_ratio = indicators.get("volume_ratio", 1.0)

            # 强势上涨动量
            if price_change_5 > 0.02 and price_change_20 > 0.05 and volume_ratio > 1.5:
                signals.append(
                    {
                        "type": "momentum",
                        "signal_type": SignalType.BUY,
                        "confidence": 0.75,
                        "reasoning": "强势上涨动量，成交量放大",
                        "indicators": {
                            "price_change_5d": price_change_5,
                            "price_change_20d": price_change_20,
                            "volume_ratio": volume_ratio,
                        },
                    }
                )

            # 强势下跌动量
            elif (
                price_change_5 < -0.02
                and price_change_20 < -0.05
                and volume_ratio > 1.5
            ):
                signals.append(
                    {
                        "type": "momentum",
                        "signal_type": SignalType.SELL,
                        "confidence": 0.75,
                        "reasoning": "强势下跌动量，成交量放大",
                        "indicators": {
                            "price_change_5d": price_change_5,
                            "price_change_20d": price_change_20,
                            "volume_ratio": volume_ratio,
                        },
                    }
                )

        except Exception as e:
            self.logger.error(f"动量信号检测失败: {e}")

        return signals


class OrderManager:
    """订单管理器"""

    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.logger = logging.getLogger(
            "hk_quant_system.quantitative_trader.order_manager"
        )

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: OrderType,
        quantity: int,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        signal_id: Optional[str] = None,
    ) -> Order:
        """创建订单"""

        order_id = f"order_{datetime.now().timestamp()}_{symbol}_{side}"

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            signal_id=signal_id,
        )

        self.orders[order_id] = order
        self.logger.info(f"创建订单: {order_id}")

        return order

    def update_order_status(self, order_id: str, status: OrderStatus, **kwargs):
        """更新订单状态"""

        if order_id in self.orders:
            order = self.orders[order_id]
            order.status = status
            order.updated_at = datetime.now()

            # 更新其他字段
            for key, value in kwargs.items():
                if hasattr(order, key):
                    setattr(order, key, value)

            self.logger.info(f"订单状态更新: {order_id} -> {status}")

            # 如果订单完全成交，更新持仓
            if status == OrderStatus.FILLED:
                self._update_position(order)

    def _update_position(self, order: Order):
        """更新持仓"""

        symbol = order.symbol
        quantity_change = order.quantity if order.side == "buy" else -order.quantity

        if symbol in self.positions:
            position = self.positions[symbol]

            # 计算新的平均价格
            if quantity_change > 0:  # 买入
                total_value = (
                    position.quantity * position.average_price
                    + order.quantity * order.average_price
                )
                position.quantity += order.quantity
                position.average_price = total_value / position.quantity
            else:  # 卖出
                position.quantity += quantity_change

        else:
            # 新建持仓
            if quantity_change > 0:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=order.quantity,
                    average_price=order.average_price,
                    market_price=order.average_price,
                    unrealized_pnl=0.0,
                )

        # 更新持仓的未实现盈亏
        if symbol in self.positions:
            position = self.positions[symbol]
            position.unrealized_pnl = (
                position.market_price - position.average_price
            ) * position.quantity
            position.last_updated = datetime.now()

    def get_open_orders(self) -> List[Order]:
        """获取未成交订单"""
        return [
            order
            for order in self.orders.values()
            if order.status
            in [
                OrderStatus.PENDING,
                OrderStatus.SUBMITTED,
                OrderStatus.PARTIALLY_FILLED,
            ]
        ]

    def get_positions(self) -> Dict[str, Position]:
        """获取当前持仓"""
        return self.positions.copy()

    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""

        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
                self.logger.info(f"订单已取消: {order_id}")
                return True

        return False


class TradingStrategy:
    """交易策略"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.quantitative_trader.strategy")

    def optimize_strategy(
        self, performance_data: Dict[str, Any], market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化交易策略"""

        try:
            # 分析当前绩效
            win_rate = performance_data.get("win_rate", 0.0)
            profit_factor = performance_data.get("profit_factor", 0.0)
            max_drawdown = performance_data.get("max_drawdown", 0.0)

            # 获取市场条件
            volatility = market_conditions.get("volatility", 0.2)
            trend_strength = market_conditions.get("trend_strength", 0.0)

            # 策略优化建议
            optimizations = {}

            # 胜率优化
            if win_rate < 0.4:
                optimizations["position_sizing"] = "reduce_position_size"
                optimizations["entry_threshold"] = "increase_confidence_threshold"

            # 盈亏比优化
            if profit_factor < 1.2:
                optimizations["exit_strategy"] = "improve_profit_taking"
                optimizations["stop_loss"] = "tighten_stop_loss"

            # 回撤控制
            if max_drawdown > 0.1:
                optimizations["risk_management"] = "reduce_max_position"
                optimizations["diversification"] = "increase_portfolio_diversification"

            # 市场适应性
            if volatility > 0.3:
                optimizations["volatility_adjustment"] = (
                    "reduce_exposure_high_volatility"
                )
            elif trend_strength > 0.7:
                optimizations["trend_following"] = "increase_trend_following_weight"

            return {
                "optimizations": optimizations,
                "recommended_changes": self._generate_recommendations(optimizations),
                "confidence": self._calculate_optimization_confidence(performance_data),
            }

        except Exception as e:
            self.logger.error(f"策略优化失败: {e}")
            return {"optimizations": {}, "recommended_changes": [], "confidence": 0.0}

    def _generate_recommendations(self, optimizations: Dict[str, str]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        if "position_sizing" in optimizations:
            recommendations.append("建议减少单笔交易仓位大小，提高胜率")

        if "entry_threshold" in optimizations:
            recommendations.append("建议提高交易信号置信度阈值，减少假信号")

        if "exit_strategy" in optimizations:
            recommendations.append("建议优化止盈策略，提高盈亏比")

        if "stop_loss" in optimizations:
            recommendations.append("建议收紧止损设置，控制单笔损失")

        if "risk_management" in optimizations:
            recommendations.append("建议降低最大仓位限制，控制回撤")

        if "diversification" in optimizations:
            recommendations.append("建议增加投资组合分散度，降低集中风险")

        return recommendations

    def _calculate_optimization_confidence(
        self, performance_data: Dict[str, Any]
    ) -> float:
        """计算优化置信度"""
        # 基于历史数据的稳定性计算置信度
        total_trades = performance_data.get("total_trades", 0)
        win_rate = performance_data.get("win_rate", 0.0)

        if total_trades < 50:
            return 0.3  # 样本量不足
        elif total_trades < 100:
            return 0.6  # 样本量适中
        else:
            # 基于胜率的稳定性
            stability = 1.0 - abs(win_rate - 0.5) * 2  # 胜率越接近50%，越不稳定
            return min(0.9, 0.7 + stability * 0.2)


class QuantitativeTraderAgent(BaseAgent):
    """量化交易员Agent"""

    def __init__(
        self,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
    ):
        super().__init__(config, message_queue, system_config)

        # 初始化组件
        self.signal_detector = SignalDetector()
        self.order_manager = OrderManager()
        self.trading_strategy = TradingStrategy()

        # 交易状态
        self.trading_enabled = system_config.trading_enabled if system_config else False
        self.max_position_size = (
            system_config.max_position_size if system_config else 1000000.0
        )
        self.risk_limit = system_config.risk_limit if system_config else 0.02

        # 数据缓存
        self.market_data_cache: Dict[str, pd.DataFrame] = {}
        self.signal_history: List[Dict[str, Any]] = []

        # 协议
        self.protocol = AgentProtocol(config.agent_id, message_queue)

    async def initialize(self) -> bool:
        """初始化Agent"""
        try:
            # 初始化协议
            await self.protocol.initialize()

            # 注册消息处理器
            self.protocol.register_handler(
                MessageType.SIGNAL, self._handle_trading_signal
            )
            self.protocol.register_handler(MessageType.DATA, self._handle_market_data)
            self.protocol.register_handler(
                MessageType.CONTROL, self._handle_trading_control
            )

            self.logger.info(f"量化交易员Agent初始化成功: {self.config.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"量化交易员Agent初始化失败: {e}")
            return False

    async def process_message(self, message: Message) -> bool:
        """处理消息"""
        try:
            await self.protocol.handle_incoming_message(message)
            return True

        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        self.logger.info("清理量化交易员Agent资源")

        # 取消所有未成交订单
        open_orders = self.order_manager.get_open_orders()
        for order in open_orders:
            self.order_manager.cancel_order(order.order_id)

        # 保存交易历史
        await self._save_trading_history()

    async def _handle_trading_signal(self, protocol_message):
        """处理交易信号"""
        try:
            signal_type = protocol_message.payload.get("signal_type")
            symbol = protocol_message.payload.get("symbol")
            confidence = protocol_message.payload.get("confidence", 0.0)
            reasoning = protocol_message.payload.get("reasoning", "")

            if confidence >= 0.6:  # 只处理高置信度信号
                await self._execute_trading_signal(
                    signal_type, symbol, confidence, reasoning
                )

        except Exception as e:
            self.logger.error(f"处理交易信号失败: {e}")

    async def _handle_market_data(self, protocol_message):
        """处理市场数据"""
        try:
            data_type = protocol_message.payload.get("data_type")
            data = protocol_message.payload.get("data", {})

            if data_type == "market_data":
                symbol = data.get("symbol")
                market_data = data.get("market_data")

                if symbol and market_data:
                    await self._process_market_data(symbol, market_data)

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")

    async def _handle_trading_control(self, protocol_message):
        """处理交易控制消息"""
        try:
            command = protocol_message.payload.get("command")
            parameters = protocol_message.payload.get("parameters", {})

            if command == "enable_trading":
                self.trading_enabled = True
                self.logger.info("交易已启用")

            elif command == "disable_trading":
                self.trading_enabled = False
                self.logger.info("交易已禁用")

            elif command == "optimize_strategy":
                performance_data = parameters.get("performance_data", {})
                market_conditions = parameters.get("market_conditions", {})

                optimization_result = self.trading_strategy.optimize_strategy(
                    performance_data, market_conditions
                )

                # 广播优化结果
                await self.protocol.broadcast_message(
                    message_type=MessageType.DATA,
                    payload={"optimization_result": optimization_result},
                )

        except Exception as e:
            self.logger.error(f"处理交易控制消息失败: {e}")

    async def _process_market_data(self, symbol: str, market_data: Dict[str, Any]):
        """处理市场数据"""
        try:
            # 转换为DataFrame格式
            df_data = {
                "timestamp": [datetime.fromisoformat(market_data["timestamp"])],
                "open": [market_data["open_price"]],
                "high": [market_data["high_price"]],
                "low": [market_data["low_price"]],
                "close": [market_data["close_price"]],
                "volume": [market_data["volume"]],
            }

            new_row = pd.DataFrame(df_data)

            # 更新缓存数据
            if symbol in self.market_data_cache:
                self.market_data_cache[symbol] = pd.concat(
                    [self.market_data_cache[symbol], new_row], ignore_index=True
                )
            else:
                self.market_data_cache[symbol] = new_row

            # 保持最近500个数据点
            if len(self.market_data_cache[symbol]) > 500:
                self.market_data_cache[symbol] = self.market_data_cache[symbol].tail(
                    500
                )

            # 如果有足够的数据，进行信号检测
            if len(self.market_data_cache[symbol]) >= 50:
                await self._detect_and_execute_signals(symbol)

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")

    async def _detect_and_execute_signals(self, symbol: str):
        """检测并执行交易信号"""
        try:
            if not self.trading_enabled:
                return

            data = self.market_data_cache[symbol]
            current_price = data["close"].iloc[-1]

            # 计算技术指标（简化版本）
            indicators = {
                "sma_20": data["close"].rolling(window=20).mean().iloc[-1],
                "sma_50": data["close"].rolling(window=50).mean().iloc[-1],
                "rsi": self._calculate_rsi(data["close"].tail(14)),
                "macd": self._calculate_macd(data["close"]),
                "volume_ratio": data["volume"].iloc[-1]
                / data["volume"].rolling(window=20).mean().iloc[-1],
            }

            # 检测信号
            signals = self.signal_detector.detect_signals(
                data, indicators, current_price
            )

            # 执行信号
            for signal in signals:
                await self._execute_signal(symbol, signal, current_price)

        except Exception as e:
            self.logger.error(f"信号检测和执行失败: {symbol}, 错误: {e}")

    async def _execute_trading_signal(
        self, signal_type: str, symbol: str, confidence: float, reasoning: str
    ):
        """执行交易信号"""
        try:
            if not self.trading_enabled:
                self.logger.info(f"交易未启用，忽略信号: {symbol}")
                return

            # 获取当前价格
            current_price = self._get_current_price(symbol)
            if current_price is None:
                self.logger.warning(f"无法获取当前价格: {symbol}")
                return

            # 计算仓位大小
            position_size = self._calculate_position_size(
                symbol, current_price, confidence
            )
            if position_size == 0:
                self.logger.info(f"仓位大小为0，跳过交易: {symbol}")
                return

            # 创建订单
            order_type = OrderType.MARKET  # 使用市价单
            side = "buy" if signal_type == SignalType.BUY else "sell"

            order = self.order_manager.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=position_size,
                price=current_price,
                signal_id=f"signal_{datetime.now().timestamp()}",
            )

            # 模拟订单执行
            await self._simulate_order_execution(order)

            # 记录信号历史
            self.signal_history.append(
                {
                    "timestamp": datetime.now(),
                    "symbol": symbol,
                    "signal_type": signal_type,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "order_id": order.order_id,
                    "executed": True,
                }
            )

            self.logger.info(
                f"执行交易信号: {symbol} {signal_type} 数量:{position_size}"
            )

        except Exception as e:
            self.logger.error(f"执行交易信号失败: {e}")

    async def _execute_signal(
        self, symbol: str, signal: Dict[str, Any], current_price: float
    ):
        """执行单个信号"""
        try:
            signal_type = signal["signal_type"]
            confidence = signal["confidence"]
            reasoning = signal["reasoning"]

            await self._execute_trading_signal(
                signal_type, symbol, confidence, reasoning
            )

        except Exception as e:
            self.logger.error(f"执行信号失败: {e}")

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格"""
        if symbol in self.market_data_cache and len(self.market_data_cache[symbol]) > 0:
            return self.market_data_cache[symbol]["close"].iloc[-1]
        return None

    def _calculate_position_size(
        self, symbol: str, price: float, confidence: float
    ) -> int:
        """计算仓位大小"""
        try:
            # 基于置信度和风险限制计算仓位大小
            base_position_value = self.max_position_size * confidence * self.risk_limit
            position_size = int(base_position_value / price)

            # 检查现有持仓
            if symbol in self.order_manager.positions:
                current_position = self.order_manager.positions[symbol]
                # 确保不超过最大仓位限制
                max_shares = int(self.max_position_size / price)
                position_size = min(
                    position_size, max_shares - current_position.quantity
                )

            return max(0, position_size)

        except Exception as e:
            self.logger.error(f"计算仓位大小失败: {e}")
            return 0

    async def _simulate_order_execution(self, order: Order):
        """模拟订单执行"""
        try:
            # 模拟订单提交
            self.order_manager.update_order_status(
                order.order_id, OrderStatus.SUBMITTED
            )
            await asyncio.sleep(0.1)  # 模拟网络延迟

            # 模拟订单成交
            self.order_manager.update_order_status(
                order.order_id,
                OrderStatus.FILLED,
                filled_quantity=order.quantity,
                average_price=order.price,
            )

            self.logger.info(f"订单执行完成: {order.order_id}")

        except Exception as e:
            self.logger.error(f"订单执行失败: {e}")
            self.order_manager.update_order_status(order.order_id, OrderStatus.REJECTED)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI"""
        if len(prices) < period:
            return 50.0

        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)

        avg_gain = gains.rolling(window=period).mean().iloc[-1]
        avg_loss = losses.rolling(window=period).mean().iloc[-1]

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> float:
        """计算MACD"""
        if len(prices) < slow:
            return 0.0

        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow

        return macd_line.iloc[-1]

    async def _save_trading_history(self):
        """保存交易历史"""
        try:
            # 这里可以保存到数据库或文件
            self.logger.info(f"保存交易历史: {len(self.signal_history)} 条记录")
        except Exception as e:
            self.logger.error(f"保存交易历史失败: {e}")

    def get_trading_summary(self) -> Dict[str, Any]:
        """获取交易摘要"""
        positions = self.order_manager.get_positions()
        open_orders = self.order_manager.get_open_orders()

        return {
            "agent_id": self.config.agent_id,
            "trading_enabled": self.trading_enabled,
            "total_positions": len(positions),
            "open_orders": len(open_orders),
            "signal_history_count": len(self.signal_history),
            "cached_symbols": list(self.market_data_cache.keys()),
            "protocol_stats": self.protocol.get_protocol_stats(),
        }


# 导出主要组件
__all__ = [
    "QuantitativeTraderAgent",
    "SignalDetector",
    "OrderManager",
    "TradingStrategy",
    "Order",
    "Position",
    "TradingPerformance",
]
