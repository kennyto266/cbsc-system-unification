#!/usr/bin/env python3
"""
Simplified System - Real-time Signal Generator
简化系统 - 实时交易信号生成器

基于实时数据生成技术交易信号
Generates technical trading signals based on real-time data
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np

from .data_stream import RealTimeDataStreamer, get_streamer, StockTick, TechnicalIndicators
from .event_processor import EventProcessor, get_event_processor, Event, EventType, EventPriority

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信号类型枚举"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"
    NEUTRAL = "NEUTRAL"

class SignalSource(Enum):
    """信号源枚举"""
    RSI = "RSI"
    MACD = "MACD"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"
    MOVING_AVERAGE = "MOVING_AVERAGE"
    VOLUME = "VOLUME"
    MOMENTUM = "MOMENTUM"
    VOLATILITY = "VOLATILITY"
    COMBINED = "COMBINED"

class SignalStrength(Enum):
    """信号强度枚举"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4

@dataclass
class TradingSignal:
    """交易信号数据结构"""
    symbol: str
    signal_type: SignalType
    signal_source: SignalSource
    signal_strength: SignalStrength
    timestamp: datetime
    price: float
    confidence: float  # 0-1之间的置信度
    indicators: Dict[str, float]  # 相关指标值
    reason: str  # 信号原因说明
    target_price: Optional[float] = None  # 目标价格
    stop_loss: Optional[float] = None  # 止损价格
    time_horizon: Optional[str] = None  # 时间周期
    expiration: Optional[datetime] = None  # 信号过期时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type.value,
            'signal_source': self.signal_source.value,
            'signal_strength': self.signal_strength.value,
            'timestamp': self.timestamp.isoformat(),
            'price': self.price,
            'confidence': self.confidence,
            'indicators': self.indicators,
            'reason': self.reason,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'time_horizon': self.time_horizon,
            'expiration': self.expiration.isoformat() if self.expiration else None
        }

@dataclass
class SignalStatistics:
    """信号统计信息"""
    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    successful_signals: int = 0
    failed_signals: int = 0
    average_confidence: float = 0.0
    last_signal_time: Optional[datetime] = None

class SignalGenerator:
    """
    实时交易信号生成器
    基于多种技术指标生成交易信号
    """

    def __init__(self, signal_timeout_minutes: int = 30):
        self.streamer = get_streamer()
        self.event_processor = get_event_processor()

        # 信号配置
        self.signal_timeout = timedelta(minutes=signal_timeout_minutes)

        # 信号缓存
        self._latest_signals: Dict[str, TradingSignal] = {}
        self._signal_history: List[TradingSignal] = []
        self.max_history_length = 1000

        # 信号统计
        self._statistics: Dict[str, SignalStatistics] = {}

        # 技术指标参数配置
        self.rsi_config = {
            'oversold': 30,
            'overbought': 70,
            'period': 14
        }

        self.macd_config = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        }

        self.bollinger_config = {
            'period': 20,
            'std_dev': 2
        }

        self.ma_config = {
            'short_period': 20,
            'long_period': 50
        }

        # 运行状态
        self._running = False
        self._generation_task: Optional[asyncio.Task] = None

        logger.info("Real-time Signal Generator initialized")

    async def start(self) -> None:
        """启动信号生成器"""
        if self._running:
            logger.warning("Signal generator is already running")
            return

        self._running = True

        logger.info("Starting real-time signal generation...")

        # 启动信号生成循环
        self._generation_task = asyncio.create_task(self._signal_generation_loop())

        logger.info("Signal generator started successfully")

    async def stop(self) -> None:
        """停止信号生成器"""
        if not self._running:
            return

        self._running = False

        if self._generation_task:
            self._generation_task.cancel()
            try:
                await self._generation_task
            except asyncio.CancelledError:
                pass

        logger.info("Signal generator stopped")

    async def _signal_generation_loop(self) -> None:
        """信号生成主循环"""
        logger.info("Starting signal generation loop")

        while self._running:
            try:
                # 获取所有监控的股票
                if hasattr(self.streamer, '_watched_symbols'):
                    symbols = self.streamer._watched_symbols
                else:
                    symbols = []

                # 并行生成所有股票的信号
                tasks = []
                for symbol in symbols:
                    task = asyncio.create_task(self._generate_signals_for_symbol(symbol))
                    tasks.append(task)

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                # 等待下一次生成
                await asyncio.sleep(5)  # 每5秒检查一次

            except Exception as e:
                logger.error(f"Error in signal generation loop: {e}")
                await asyncio.sleep(5)

        logger.info("Signal generation loop stopped")

    async def _generate_signals_for_symbol(self, symbol: str) -> None:
        """为单个股票生成信号"""
        try:
            # 获取最新数据
            tick = self.streamer.get_latest_tick(symbol)
            indicators = self.streamer.get_latest_indicators(symbol)

            if not tick or not indicators:
                return

            # 生成各类信号
            signals = []

            # RSI信号
            rsi_signal = self._generate_rsi_signal(symbol, tick, indicators)
            if rsi_signal:
                signals.append(rsi_signal)

            # MACD信号
            macd_signal = self._generate_macd_signal(symbol, tick, indicators)
            if macd_signal:
                signals.append(macd_signal)

            # 布林带信号
            bb_signal = self._generate_bollinger_signal(symbol, tick, indicators)
            if bb_signal:
                signals.append(bb_signal)

            # 移动平均线信号
            ma_signal = self._generate_ma_signal(symbol, tick, indicators)
            if ma_signal:
                signals.append(ma_signal)

            # 生成综合信号
            if len(signals) >= 2:
                combined_signal = self._generate_combined_signal(symbol, tick, signals)
                if combined_signal:
                    signals.append(combined_signal)

            # 处理生成的信号
            for signal in signals:
                await self._process_signal(signal)

        except Exception as e:
            logger.error(f"Error generating signals for {symbol}: {e}")

    def _generate_rsi_signal(self, symbol: str, tick: StockTick, indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """生成RSI信号"""
        if indicators.rsi is None:
            return None

        rsi = indicators.rsi
        price = tick.price

        if rsi < self.rsi_config['oversold']:
            signal_type = SignalType.BUY
            signal_strength = SignalStrength.STRONG if rsi < 20 else SignalStrength.MODERATE
            confidence = min(0.9, (self.rsi_config['oversold'] - rsi) / 20)
            reason = f"RSI超卖: {rsi:.2f} < {self.rsi_config['oversold']}"

        elif rsi > self.rsi_config['overbought']:
            signal_type = SignalType.SELL
            signal_strength = SignalStrength.STRONG if rsi > 80 else SignalStrength.MODERATE
            confidence = min(0.9, (rsi - self.rsi_config['overbought']) / 20)
            reason = f"RSI超买: {rsi:.2f} > {self.rsi_config['overbought']}"

        else:
            return None

        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            signal_source=SignalSource.RSI,
            signal_strength=signal_strength,
            timestamp=datetime.now(),
            price=price,
            confidence=confidence,
            indicators={'rsi': rsi},
            reason=reason,
            target_price=self._calculate_target_price(signal_type, price, confidence),
            stop_loss=self._calculate_stop_loss(signal_type, price, confidence),
            time_horizon="短期",
            expiration=datetime.now() + timedelta(hours=1)
        )

    def _generate_macd_signal(self, symbol: str, tick: StockTick, indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """生成MACD信号"""
        if indicators.macd is None or indicators.macd_signal is None:
            return None

        macd = indicators.macd
        macd_signal_line = indicators.macd_signal
        price = tick.price

        # MACD金叉死叉判断
        if macd > macd_signal_line:
            # 检查是否为金叉（之前MACD在信号线下方）
            # 这里需要历史数据，简化处理
            if macd - macd_signal_line > 0.01:  # 差值足够大
                signal_type = SignalType.BUY
                signal_strength = SignalStrength.MODERATE
                confidence = min(0.8, abs(macd - macd_signal_line) * 10)
                reason = f"MACD金叉: MACD({macd:.4f}) > Signal({macd_signal_line:.4f})"

        elif macd < macd_signal_line:
            if macd_signal_line - macd > 0.01:
                signal_type = SignalType.SELL
                signal_strength = SignalStrength.MODERATE
                confidence = min(0.8, abs(macd - macd_signal_line) * 10)
                reason = f"MACD死叉: MACD({macd:.4f}) < Signal({macd_signal_line:.4f})"
            else:
                return None
        else:
            return None

        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            signal_source=SignalSource.MACD,
            signal_strength=signal_strength,
            timestamp=datetime.now(),
            price=price,
            confidence=confidence,
            indicators={'macd': macd, 'macd_signal': macd_signal_line},
            reason=reason,
            target_price=self._calculate_target_price(signal_type, price, confidence),
            stop_loss=self._calculate_stop_loss(signal_type, price, confidence),
            time_horizon="中期",
            expiration=datetime.now() + timedelta(hours=4)
        )

    def _generate_bollinger_signal(self, symbol: str, tick: StockTick, indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """生成布林带信号"""
        if not all([indicators.bollinger_upper, indicators.bollinger_lower]):
            return None

        price = tick.price
        bb_upper = indicators.bollinger_upper
        bb_lower = indicators.bollinger_lower
        bb_middle = (bb_upper + bb_lower) / 2

        if price <= bb_lower:
            signal_type = SignalType.BUY
            signal_strength = SignalStrength.MODERATE
            confidence = min(0.8, (bb_lower - price) / price * 100)
            reason = f"价格触及布林带下轨: {price:.2f} <= {bb_lower:.2f}"

        elif price >= bb_upper:
            signal_type = SignalType.SELL
            signal_strength = SignalStrength.MODERATE
            confidence = min(0.8, (price - bb_upper) / price * 100)
            reason = f"价格触及布林带上轨: {price:.2f} >= {bb_upper:.2f}"

        elif price < bb_middle * 0.98:  # 接近下轨
            signal_type = SignalType.BUY
            signal_strength = SignalStrength.WEAK
            confidence = 0.5
            reason = f"价格接近布林带下轨: {price:.2f}"

        elif price > bb_middle * 1.02:  # 接近上轨
            signal_type = SignalType.SELL
            signal_strength = SignalStrength.WEAK
            confidence = 0.5
            reason = f"价格接近布林带上轨: {price:.2f}"

        else:
            return None

        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            signal_source=SignalSource.BOLLINGER_BANDS,
            signal_strength=signal_strength,
            timestamp=datetime.now(),
            price=price,
            confidence=confidence,
            indicators={
                'bollinger_upper': bb_upper,
                'bollinger_lower': bb_lower,
                'bollinger_middle': bb_middle
            },
            reason=reason,
            target_price=self._calculate_target_price(signal_type, price, confidence),
            stop_loss=self._calculate_stop_loss(signal_type, price, confidence),
            time_horizon="短期",
            expiration=datetime.now() + timedelta(hours=2)
        )

    def _generate_ma_signal(self, symbol: str, tick: StockTick, indicators: TechnicalIndicators) -> Optional[TradingSignal]:
        """生成移动平均线信号"""
        if indicators.sma_20 is None:
            return None

        price = tick.price
        sma_20 = indicators.sma_20

        # 简单的移动平均线信号
        if price > sma_20 * 1.02:  # 价格高于均线2%
            signal_type = SignalType.BUY
            signal_strength = SignalStrength.WEAK
            confidence = min(0.7, (price - sma_20) / sma_20 * 50)
            reason = f"价格高于均线: {price:.2f} > {sma_20:.2f}"

        elif price < sma_20 * 0.98:  # 价格低于均线2%
            signal_type = SignalType.SELL
            signal_strength = SignalStrength.WEAK
            confidence = min(0.7, (sma_20 - price) / sma_20 * 50)
            reason = f"价格低于均线: {price:.2f} < {sma_20:.2f}"

        else:
            return None

        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            signal_source=SignalSource.MOVING_AVERAGE,
            signal_strength=signal_strength,
            timestamp=datetime.now(),
            price=price,
            confidence=confidence,
            indicators={'sma_20': sma_20},
            reason=reason,
            target_price=self._calculate_target_price(signal_type, price, confidence),
            stop_loss=self._calculate_stop_loss(signal_type, price, confidence),
            time_horizon="中期",
            expiration=datetime.now() + timedelta(hours=6)
        )

    def _generate_combined_signal(self, symbol: str, tick: StockTick, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """生成综合信号"""
        if len(signals) < 2:
            return None

        # 统计买卖信号数量
        buy_count = sum(1 for s in signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY])
        sell_count = sum(1 for s in signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL])

        # 计算加权置信度
        total_confidence = sum(s.confidence * s.signal_strength.value for s in signals)
        total_weight = sum(s.signal_strength.value for s in signals)
        avg_confidence = total_confidence / total_weight if total_weight > 0 else 0

        # 确定综合信号类型
        if buy_count > sell_count:
            signal_type = SignalType.STRONG_BUY if buy_count >= 3 else SignalType.BUY
            signal_strength = SignalStrength.STRONG if buy_count >= 3 else SignalStrength.MODERATE
        elif sell_count > buy_count:
            signal_type = SignalType.STRONG_SELL if sell_count >= 3 else SignalType.SELL
            signal_strength = SignalStrength.STRONG if sell_count >= 3 else SignalStrength.MODERATE
        else:
            return None  # 信号冲突，不生成综合信号

        # 生成原因说明
        source_names = [s.signal_source.value for s in signals]
        reason = f"综合信号: {signal_type.value} (来源: {', '.join(source_names)})"

        # 合并指标数据
        combined_indicators = {}
        for signal in signals:
            combined_indicators.update(signal.indicators)

        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            signal_source=SignalSource.COMBINED,
            signal_strength=signal_strength,
            timestamp=datetime.now(),
            price=tick.price,
            confidence=avg_confidence,
            indicators=combined_indicators,
            reason=reason,
            target_price=self._calculate_target_price(signal_type, tick.price, avg_confidence),
            stop_loss=self._calculate_stop_loss(signal_type, tick.price, avg_confidence),
            time_horizon="综合",
            expiration=datetime.now() + timedelta(hours=3)
        )

    def _calculate_target_price(self, signal_type: SignalType, current_price: float, confidence: float) -> Optional[float]:
        """计算目标价格"""
        if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            # 买入信号的目标价格更高
            return current_price * (1 + confidence * 0.05)  # 最多上涨5%
        elif signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            # 卖出信号的目标价格更低
            return current_price * (1 - confidence * 0.05)  # 最多下跌5%
        return None

    def _calculate_stop_loss(self, signal_type: SignalType, current_price: float, confidence: float) -> Optional[float]:
        """计算止损价格"""
        if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            # 买入信号的止损价格更低
            return current_price * (1 - confidence * 0.03)  # 最多下跌3%
        elif signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            # 卖出信号的止损价格更高
            return current_price * (1 + confidence * 0.03)  # 最多上涨3%
        return None

    async def _process_signal(self, signal: TradingSignal) -> None:
        """处理生成的信号"""
        try:
            # 更新缓存
            self._latest_signals[signal.symbol] = signal

            # 添加到历史记录
            self._signal_history.append(signal)
            if len(self._signal_history) > self.max_history_length:
                self._signal_history.pop(0)

            # 更新统计信息
            self._update_statistics(signal)

            # 发布信号事件
            await self._publish_signal_event(signal)

            logger.info(f"Generated signal: {signal.symbol} - {signal.signal_type.value} ({signal.confidence:.2f})")

        except Exception as e:
            logger.error(f"Error processing signal: {e}")

    def _update_statistics(self, signal: TradingSignal) -> None:
        """更新信号统计信息"""
        symbol = signal.symbol

        if symbol not in self._statistics:
            self._statistics[symbol] = SignalStatistics()

        stats = self._statistics[symbol]
        stats.total_signals += 1
        stats.last_signal_time = signal.timestamp

        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            stats.buy_signals += 1
        elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            stats.sell_signals += 1
        else:
            stats.hold_signals += 1

        # 更新平均置信度
        stats.average_confidence = (
            (stats.average_confidence * (stats.total_signals - 1) + signal.confidence) /
            stats.total_signals
        )

    async def _publish_signal_event(self, signal: TradingSignal) -> None:
        """发布信号事件"""
        try:
            await self.event_processor.publish_technical_signal(
                symbol=signal.symbol,
                signal_type=signal.signal_type.value,
                signal_value=signal.confidence,
                confidence=signal.confidence,
                source="signal_generator"
            )
        except Exception as e:
            logger.error(f"Error publishing signal event: {e}")

    def get_latest_signal(self, symbol: str) -> Optional[TradingSignal]:
        """获取股票的最新信号"""
        signal = self._latest_signals.get(symbol)
        if signal and signal.expiration and datetime.now() > signal.expiration:
            # 信号已过期
            del self._latest_signals[symbol]
            return None
        return signal

    def get_signal_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[TradingSignal]:
        """获取信号历史"""
        history = self._signal_history
        if symbol:
            history = [s for s in history if s.symbol == symbol]
        return history[-limit:]

    def get_statistics(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """获取信号统计信息"""
        if symbol:
            return asdict(self._statistics.get(symbol, SignalStatistics()))
        else:
            return {sym: asdict(stats) for sym, stats in self._statistics.items()}

    def get_active_signals(self) -> Dict[str, TradingSignal]:
        """获取所有有效信号"""
        active_signals = {}
        current_time = datetime.now()

        for symbol, signal in self._latest_signals.items():
            if not signal.expiration or current_time <= signal.expiration:
                active_signals[symbol] = signal

        return active_signals

    def update_config(self, config: Dict[str, Any]) -> None:
        """更新信号生成配置"""
        if 'rsi' in config:
            self.rsi_config.update(config['rsi'])
        if 'macd' in config:
            self.macd_config.update(config['macd'])
        if 'bollinger' in config:
            self.bollinger_config.update(config['bollinger'])
        if 'moving_average' in config:
            self.ma_config.update(config['moving_average'])

        logger.info("Signal generator configuration updated")

# 全局信号生成器实例
_signal_generator = None

def get_signal_generator() -> SignalGenerator:
    """获取全局信号生成器实例"""
    global _signal_generator
    if _signal_generator is None:
        _signal_generator = SignalGenerator()
    return _signal_generator

if __name__ == "__main__":
    async def test_signal_generator():
        """测试信号生成器"""
        generator = SignalGenerator()

        # 启动生成器
        await generator.start()

        # 运行30秒
        await asyncio.sleep(30)

        # 获取最新信号
        symbols = ["0700.HK", "0941.HK"]
        for symbol in symbols:
            signal = generator.get_latest_signal(symbol)
            if signal:
                print(f"Latest signal for {symbol}: {signal.to_dict()}")

        # 获取统计信息
        stats = generator.get_statistics()
        print(f"Statistics: {stats}")

        # 获取活跃信号
        active_signals = generator.get_active_signals()
        print(f"Active signals: {len(active_signals)}")

        # 停止生成器
        await generator.stop()

    # 运行测试
    asyncio.run(test_signal_generator())