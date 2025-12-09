"""
港股量化交易 AI Agent 系统 - 高频交易引擎

实现高频交易引擎，支持毫秒级交易执行、延迟优化和性能监控。
专为低延迟、高吞吐量的交易场景设计。
"""

import asyncio
import logging
import queue
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ...models.base import BaseModel


class HFTStrategy(str, Enum):
    """高频交易策略类型"""

    MARKET_MAKING = "market_making"
    ARBITRAGE = "arbitrage"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"


@dataclass
class TickData(BaseModel):
    """Tick数据模型"""

    symbol: str
    timestamp: datetime
    bid_price: float
    ask_price: float
    bid_size: int
    ask_size: int
    last_price: float
    last_size: int
    volume: int
    sequence: int = 0


@dataclass
class HFTOrder(BaseModel):
    """高频交易订单"""

    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    price: float
    size: int
    strategy: HFTStrategy
    timestamp: datetime
    priority: int = 0
    time_in_force: str = "IOC"  # Immediate or Cancel
    parent_order_id: Optional[str] = None


@dataclass
class PerformanceMetrics(BaseModel):
    """性能指标"""

    # 延迟指标
    average_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    # 吞吐量指标
    orders_per_second: float = 0.0
    messages_per_second: float = 0.0
    fills_per_second: float = 0.0

    # 成功率指标
    order_fill_rate: float = 0.0
    order_reject_rate: float = 0.0
    system_uptime: float = 0.0

    # 盈亏指标
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    sharpe_ratio: float = 0.0

    # 时间戳
    measurement_time: datetime = field(default_factory=datetime.now)


class LatencyTracker:
    """延迟跟踪器"""

    def __init__(self, max_samples: int = 10000):
        self.max_samples = max_samples
        self.latencies = deque(maxlen=max_samples)
        self.logger = logging.getLogger("hk_quant_system.hft.latency_tracker")

    def record_latency(self, latency_ms: float):
        """记录延迟"""
        self.latencies.append(latency_ms)

    def get_statistics(self) -> Dict[str, float]:
        """获取延迟统计"""
        if not self.latencies:
            return {"average": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}

        latencies_array = np.array(self.latencies)

        return {
            "average": float(np.mean(latencies_array)),
            "p50": float(np.percentile(latencies_array, 50)),
            "p95": float(np.percentile(latencies_array, 95)),
            "p99": float(np.percentile(latencies_array, 99)),
            "max": float(np.max(latencies_array)),
        }


class MarketDataBuffer:
    """市场数据缓冲区"""

    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.tick_buffer: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=buffer_size)
        )
        self.lock = threading.RLock()
        self.logger = logging.getLogger("hk_quant_system.hft.market_data_buffer")

    def add_tick(self, tick: TickData):
        """添加Tick数据"""
        with self.lock:
            self.tick_buffer[tick.symbol].append(tick)

    def get_latest_tick(self, symbol: str) -> Optional[TickData]:
        """获取最新Tick数据"""
        with self.lock:
            if symbol in self.tick_buffer and self.tick_buffer[symbol]:
                return self.tick_buffer[symbol][-1]
            return None

    def get_tick_history(self, symbol: str, count: int = 100) -> List[TickData]:
        """获取Tick历史数据"""
        with self.lock:
            if symbol in self.tick_buffer:
                return list(self.tick_buffer[symbol])[-count:]
            return []

    def get_spread(self, symbol: str) -> Optional[float]:
        """获取买卖价差"""
        latest_tick = self.get_latest_tick(symbol)
        if latest_tick:
            return latest_tick.ask_price - latest_tick.bid_price
        return None


class OrderBook:
    """订单簿"""

    def __init__(self):
        self.buy_orders: List[HFTOrder] = []
        self.sell_orders: List[HFTOrder] = []
        self.lock = threading.RLock()
        self.logger = logging.getLogger("hk_quant_system.hft.order_book")

    def add_order(self, order: HFTOrder):
        """添加订单"""
        with self.lock:
            if order.side == "buy":
                self.buy_orders.append(order)
                self.buy_orders.sort(
                    key=lambda x: (-x.price, x.timestamp)
                )  # 价格优先，时间优先
            else:
                self.sell_orders.append(order)
                self.sell_orders.sort(
                    key=lambda x: (x.price, x.timestamp)
                )  # 价格优先，时间优先

    def remove_order(self, order_id: str) -> bool:
        """移除订单"""
        with self.lock:
            # 从买单中移除
            for i, order in enumerate(self.buy_orders):
                if order.order_id == order_id:
                    self.buy_orders.pop(i)
                    return True

            # 从卖单中移除
            for i, order in enumerate(self.sell_orders):
                if order.order_id == order_id:
                    self.sell_orders.pop(i)
                    return True

            return False

    def get_best_bid_ask(self, symbol: str) -> Optional[Tuple[float, float]]:
        """获取最优买卖价"""
        with self.lock:
            best_bid = None
            best_ask = None

            # 查找指定symbol的最优买单
            for order in self.buy_orders:
                if order.symbol == symbol:
                    best_bid = order.price
                    break

            # 查找指定symbol的最优卖单
            for order in self.sell_orders:
                if order.symbol == symbol:
                    best_ask = order.price
                    break

            if best_bid is not None and best_ask is not None:
                return (best_bid, best_ask)

            return None

    def get_order_count(self, symbol: str) -> Tuple[int, int]:
        """获取订单数量"""
        with self.lock:
            buy_count = sum(1 for order in self.buy_orders if order.symbol == symbol)
            sell_count = sum(1 for order in self.sell_orders if order.symbol == symbol)
            return (buy_count, sell_count)


class HFTStrategyEngine:
    """高频交易策略引擎"""

    def __init__(self):
        self.strategies: Dict[HFTStrategy, Callable] = {}
        self.logger = logging.getLogger("hk_quant_system.hft.strategy_engine")
        self._initialize_strategies()

    def _initialize_strategies(self):
        """初始化策略"""
        self.strategies[HFTStrategy.MARKET_MAKING] = self._market_making_strategy
        self.strategies[HFTStrategy.ARBITRAGE] = self._arbitrage_strategy
        self.strategies[HFTStrategy.MOMENTUM] = self._momentum_strategy
        self.strategies[HFTStrategy.MEAN_REVERSION] = self._mean_reversion_strategy
        self.strategies[HFTStrategy.STATISTICAL_ARBITRAGE] = (
            self._statistical_arbitrage_strategy
        )

    def generate_signals(
        self, strategy: HFTStrategy, market_data: MarketDataBuffer, symbol: str
    ) -> List[HFTOrder]:
        """生成交易信号"""
        try:
            if strategy in self.strategies:
                return self.strategies[strategy](market_data, symbol)
            else:
                self.logger.warning(f"未知策略: {strategy}")
                return []
        except Exception as e:
            self.logger.error(f"策略执行失败: {strategy}, 错误: {e}")
            return []

    def _market_making_strategy(
        self, market_data: MarketDataBuffer, symbol: str
    ) -> List[HFTOrder]:
        """做市策略"""
        orders = []

        try:
            latest_tick = market_data.get_latest_tick(symbol)
            if not latest_tick:
                return orders

            # 获取价差
            spread = latest_tick.ask_price - latest_tick.bid_price
            mid_price = (latest_tick.bid_price + latest_tick.ask_price) / 2

            # 做市参数
            tick_size = 0.01  # 最小价格变动
            base_size = 1000  # 基础订单大小

            # 如果价差足够大，进行做市
            if spread >= tick_size * 2:
                # 买单（略低于中间价）
                buy_price = mid_price - tick_size
                buy_order = HFTOrder(
                    order_id=f"mm_buy_{int(time.time() * 1000)}",
                    symbol=symbol,
                    side="buy",
                    price=buy_price,
                    size=base_size,
                    strategy=HFTStrategy.MARKET_MAKING,
                    timestamp=datetime.now(),
                )
                orders.append(buy_order)

                # 卖单（略高于中间价）
                sell_price = mid_price + tick_size
                sell_order = HFTOrder(
                    order_id=f"mm_sell_{int(time.time() * 1000)}",
                    symbol=symbol,
                    side="sell",
                    price=sell_price,
                    size=base_size,
                    strategy=HFTStrategy.MARKET_MAKING,
                    timestamp=datetime.now(),
                )
                orders.append(sell_order)

        except Exception as e:
            self.logger.error(f"做市策略执行失败: {e}")

        return orders

    def _arbitrage_strategy(
        self, market_data: MarketDataBuffer, symbol: str
    ) -> List[HFTOrder]:
        """套利策略"""
        orders = []

        try:
            # 获取多个交易所的价格（这里简化处理）
            latest_tick = market_data.get_latest_tick(symbol)
            if not latest_tick:
                return orders

            # 模拟另一个交易所的价格
            other_exchange_price = latest_tick.last_price * (
                1 + np.random.normal(0, 0.001)
            )

            # 价格差异阈值
            arbitrage_threshold = 0.002  # 0.2%

            price_diff = abs(other_exchange_price - latest_tick.last_price)
            price_diff_pct = price_diff / latest_tick.last_price

            if price_diff_pct > arbitrage_threshold:
                # 执行套利
                if other_exchange_price > latest_tick.last_price:
                    # 在本地买入，在其他交易所卖出
                    order = HFTOrder(
                        order_id=f"arb_buy_{int(time.time() * 1000)}",
                        symbol=symbol,
                        side="buy",
                        price=latest_tick.ask_price,
                        size=1000,
                        strategy=HFTStrategy.ARBITRAGE,
                        timestamp=datetime.now(),
                    )
                    orders.append(order)
                else:
                    # 在本地卖出，在其他交易所买入
                    order = HFTOrder(
                        order_id=f"arb_sell_{int(time.time() * 1000)}",
                        symbol=symbol,
                        side="sell",
                        price=latest_tick.bid_price,
                        size=1000,
                        strategy=HFTStrategy.ARBITRAGE,
                        timestamp=datetime.now(),
                    )
                    orders.append(order)

        except Exception as e:
            self.logger.error(f"套利策略执行失败: {e}")

        return orders

    def _momentum_strategy(
        self, market_data: MarketDataBuffer, symbol: str
    ) -> List[HFTOrder]:
        """动量策略"""
        orders = []

        try:
            tick_history = market_data.get_tick_history(symbol, 10)
            if len(tick_history) < 5:
                return orders

            # 计算价格动量
            recent_prices = [tick.last_price for tick in tick_history[-5:]]
            price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]

            # 动量阈值
            momentum_threshold = 0.001  # 0.1%

            if price_change > momentum_threshold:
                # 上涨动量，买入
                latest_tick = tick_history[-1]
                order = HFTOrder(
                    order_id=f"mom_buy_{int(time.time() * 1000)}",
                    symbol=symbol,
                    side="buy",
                    price=latest_tick.ask_price,
                    size=500,
                    strategy=HFTStrategy.MOMENTUM,
                    timestamp=datetime.now(),
                )
                orders.append(order)
            elif price_change < -momentum_threshold:
                # 下跌动量，卖出
                latest_tick = tick_history[-1]
                order = HFTOrder(
                    order_id=f"mom_sell_{int(time.time() * 1000)}",
                    symbol=symbol,
                    side="sell",
                    price=latest_tick.bid_price,
                    size=500,
                    strategy=HFTStrategy.MOMENTUM,
                    timestamp=datetime.now(),
                )
                orders.append(order)

        except Exception as e:
            self.logger.error(f"动量策略执行失败: {e}")

        return orders

    def _mean_reversion_strategy(
        self, market_data: MarketDataBuffer, symbol: str
    ) -> List[HFTOrder]:
        """均值回归策略"""
        orders = []

        try:
            tick_history = market_data.get_tick_history(symbol, 20)
            if len(tick_history) < 10:
                return orders

            # 计算移动平均
            prices = [tick.last_price for tick in tick_history]
            sma = np.mean(prices[-10:])
            current_price = prices[-1]

            # 计算偏离程度
            deviation = (current_price - sma) / sma

            # 均值回归阈值
            reversion_threshold = 0.002  # 0.2%

            if deviation > reversion_threshold:
                # 价格高于均值，卖出
                latest_tick = tick_history[-1]
                order = HFTOrder(
                    order_id=f"mr_sell_{int(time.time() * 1000)}",
                    symbol=symbol,
                    side="sell",
                    price=latest_tick.bid_price,
                    size=300,
                    strategy=HFTStrategy.MEAN_REVERSION,
                    timestamp=datetime.now(),
                )
                orders.append(order)
            elif deviation < -reversion_threshold:
                # 价格低于均值，买入
                latest_tick = tick_history[-1]
                order = HFTOrder(
                    order_id=f"mr_buy_{int(time.time() * 1000)}",
                    symbol=symbol,
                    side="buy",
                    price=latest_tick.ask_price,
                    size=300,
                    strategy=HFTStrategy.MEAN_REVERSION,
                    timestamp=datetime.now(),
                )
                orders.append(order)

        except Exception as e:
            self.logger.error(f"均值回归策略执行失败: {e}")

        return orders

    def _statistical_arbitrage_strategy(
        self, market_data: MarketDataBuffer, symbol: str
    ) -> List[HFTOrder]:
        """统计套利策略"""
        orders = []

        try:
            # 这里简化实现，实际需要更复杂的统计模型
            tick_history = market_data.get_tick_history(symbol, 50)
            if len(tick_history) < 20:
                return orders

            prices = [tick.last_price for tick in tick_history]

            # 计算统计指标
            mean_price = np.mean(prices[-20:])
            std_price = np.std(prices[-20:])
            current_price = prices[-1]

            # Z - score
            z_score = (current_price - mean_price) / std_price if std_price > 0 else 0

            # 统计套利阈值
            z_threshold = 2.0  # 2个标准差

            if z_score > z_threshold:
                # 价格过高，卖出
                latest_tick = tick_history[-1]
                order = HFTOrder(
                    order_id=f"stat_arb_sell_{int(time.time() * 1000)}",
                    symbol=symbol,
                    side="sell",
                    price=latest_tick.bid_price,
                    size=200,
                    strategy=HFTStrategy.STATISTICAL_ARBITRAGE,
                    timestamp=datetime.now(),
                )
                orders.append(order)
            elif z_score < -z_threshold:
                # 价格过低，买入
                latest_tick = tick_history[-1]
                order = HFTOrder(
                    order_id=f"stat_arb_buy_{int(time.time() * 1000)}",
                    symbol=symbol,
                    side="buy",
                    price=latest_tick.ask_price,
                    size=200,
                    strategy=HFTStrategy.STATISTICAL_ARBITRAGE,
                    timestamp=datetime.now(),
                )
                orders.append(order)

        except Exception as e:
            self.logger.error(f"统计套利策略执行失败: {e}")

        return orders


class HFTEngine:
    """高频交易引擎"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.logger = logging.getLogger("hk_quant_system.hft.engine")

        # 核心组件
        self.market_data_buffer = MarketDataBuffer()
        self.order_book = OrderBook()
        self.strategy_engine = HFTStrategyEngine()
        self.latency_tracker = LatencyTracker()

        # 性能监控
        self.performance_metrics = PerformanceMetrics()
        self.start_time = datetime.now()

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # 运行状态
        self.running = False
        self.tasks = []

        # 统计信息
        self.order_count = 0
        self.fill_count = 0
        self.reject_count = 0
        self.total_pnl = 0.0

        # 活跃策略
        self.active_strategies: List[HFTStrategy] = [
            HFTStrategy.MARKET_MAKING,
            HFTStrategy.MOMENTUM,
            HFTStrategy.MEAN_REVERSION,
        ]

    async def start(self):
        """启动高频交易引擎"""
        try:
            self.running = True
            self.logger.info("启动高频交易引擎")

            # 启动市场数据处理任务
            market_data_task = asyncio.create_task(self._market_data_processing_loop())
            self.tasks.append(market_data_task)

            # 启动策略执行任务
            strategy_task = asyncio.create_task(self._strategy_execution_loop())
            self.tasks.append(strategy_task)

            # 启动订单管理任务
            order_management_task = asyncio.create_task(self._order_management_loop())
            self.tasks.append(order_management_task)

            # 启动性能监控任务
            performance_task = asyncio.create_task(self._performance_monitoring_loop())
            self.tasks.append(performance_task)

            self.logger.info("高频交易引擎启动成功")

        except Exception as e:
            self.logger.error(f"启动高频交易引擎失败: {e}")
            raise

    async def stop(self):
        """停止高频交易引擎"""
        try:
            self.running = False
            self.logger.info("停止高频交易引擎")

            # 取消所有任务
            for task in self.tasks:
                if not task.done():
                    task.cancel()

            # 等待任务完成
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)

            # 关闭线程池
            self.executor.shutdown(wait=True)

            self.logger.info("高频交易引擎已停止")

        except Exception as e:
            self.logger.error(f"停止高频交易引擎失败: {e}")

    async def process_tick_data(self, tick: TickData):
        """处理Tick数据"""
        try:
            start_time = time.time()

            # 添加到市场数据缓冲区
            self.market_data_buffer.add_tick(tick)

            # 记录延迟
            latency_ms = (time.time() - start_time) * 1000
            self.latency_tracker.record_latency(latency_ms)

        except Exception as e:
            self.logger.error(f"处理Tick数据失败: {e}")

    async def _market_data_processing_loop(self):
        """市场数据处理循环"""
        while self.running:
            try:
                # 这里可以添加市场数据的实时处理逻辑
                await asyncio.sleep(0.001)  # 1毫秒间隔
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"市场数据处理循环异常: {e}")
                await asyncio.sleep(0.01)

    async def _strategy_execution_loop(self):
        """策略执行循环"""
        while self.running:
            try:
                # 获取所有活跃的symbol
                symbols = list(self.market_data_buffer.tick_buffer.keys())

                for symbol in symbols:
                    for strategy in self.active_strategies:
                        # 生成交易信号
                        orders = self.strategy_engine.generate_signals(
                            strategy, self.market_data_buffer, symbol
                        )

                        # 提交订单
                        for order in orders:
                            await self._submit_order(order)

                await asyncio.sleep(0.001)  # 1毫秒间隔

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"策略执行循环异常: {e}")
                await asyncio.sleep(0.01)

    async def _order_management_loop(self):
        """订单管理循环"""
        while self.running:
            try:
                # 检查订单簿中的订单
                # 这里可以添加订单匹配、过期检查等逻辑
                await asyncio.sleep(0.001)  # 1毫秒间隔

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"订单管理循环异常: {e}")
                await asyncio.sleep(0.01)

    async def _performance_monitoring_loop(self):
        """性能监控循环"""
        while self.running:
            try:
                # 更新性能指标
                await self._update_performance_metrics()

                await asyncio.sleep(1.0)  # 每秒更新一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"性能监控循环异常: {e}")
                await asyncio.sleep(1.0)

    async def _submit_order(self, order: HFTOrder):
        """提交订单"""
        try:
            start_time = time.time()

            # 添加到订单簿
            self.order_book.add_order(order)
            self.order_count += 1

            # 模拟订单执行
            await self._simulate_order_execution(order)

            # 记录延迟
            latency_ms = (time.time() - start_time) * 1000
            self.latency_tracker.record_latency(latency_ms)

        except Exception as e:
            self.logger.error(f"提交订单失败: {e}")

    async def _simulate_order_execution(self, order: HFTOrder):
        """模拟订单执行"""
        try:
            # 模拟订单执行概率
            fill_probability = 0.8  # 80 % 的订单会被执行

            if np.random.random() < fill_probability:
                # 订单成交
                self.fill_count += 1

                # 计算盈亏（简化）
                pnl = np.random.normal(0, 10)  # 模拟随机盈亏
                self.total_pnl += pnl

                # 从订单簿移除
                self.order_book.remove_order(order.order_id)

            else:
                # 订单被拒绝
                self.reject_count += 1
                self.order_book.remove_order(order.order_id)

        except Exception as e:
            self.logger.error(f"模拟订单执行失败: {e}")

    async def _update_performance_metrics(self):
        """更新性能指标"""
        try:
            # 获取延迟统计
            latency_stats = self.latency_tracker.get_statistics()

            # 计算运行时间
            uptime = (datetime.now() - self.start_time).total_seconds()

            # 计算每秒指标
            if uptime > 0:
                orders_per_second = self.order_count / uptime
                fills_per_second = self.fill_count / uptime
            else:
                orders_per_second = 0.0
                fills_per_second = 0.0

            # 计算成功率
            fill_rate = self.fill_count / max(1, self.order_count)
            reject_rate = self.reject_count / max(1, self.order_count)

            # 更新性能指标
            self.performance_metrics = PerformanceMetrics(
                average_latency_ms=latency_stats["average"],
                p50_latency_ms=latency_stats["p50"],
                p95_latency_ms=latency_stats["p95"],
                p99_latency_ms=latency_stats["p99"],
                max_latency_ms=latency_stats["max"],
                orders_per_second=orders_per_second,
                messages_per_second=orders_per_second,  # 简化处理
                fills_per_second=fills_per_second,
                order_fill_rate=fill_rate,
                order_reject_rate=reject_rate,
                system_uptime=uptime,
                total_pnl=self.total_pnl,
                daily_pnl=self.total_pnl,  # 简化处理
                sharpe_ratio=0.0,  # 需要更复杂的计算
                measurement_time=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"更新性能指标失败: {e}")

    def get_performance_metrics(self) -> PerformanceMetrics:
        """获取性能指标"""
        return self.performance_metrics

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "running": self.running,
            "active_strategies": [
                strategy.value for strategy in self.active_strategies
            ],
            "total_orders": self.order_count,
            "total_fills": self.fill_count,
            "total_rejects": self.reject_count,
            "total_pnl": self.total_pnl,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "cached_symbols": list(self.market_data_buffer.tick_buffer.keys()),
        }

    def add_strategy(self, strategy: HFTStrategy):
        """添加策略"""
        if strategy not in self.active_strategies:
            self.active_strategies.append(strategy)
            self.logger.info(f"添加策略: {strategy}")

    def remove_strategy(self, strategy: HFTStrategy):
        """移除策略"""
        if strategy in self.active_strategies:
            self.active_strategies.remove(strategy)
            self.logger.info(f"移除策略: {strategy}")


# 导出主要组件
__all__ = [
    "HFTEngine",
    "HFTStrategyEngine",
    "MarketDataBuffer",
    "OrderBook",
    "LatencyTracker",
    "PerformanceMetrics",
    "HFTOrder",
    "TickData",
    "HFTStrategy",
]
