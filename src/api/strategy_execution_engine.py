#!/usr/bin/env python3
"""
CBSC策略執行引擎接口 (Task #005)
CBSC Strategy Execution Engine Interface

統一的策略執行引擎，支持多種策略類型的實時和回測執行
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

# 導入策略模型
from .strategy_management_api import (
    Strategy, StrategyType, StrategyParameters, StrategySignal,
    StrategyPerformance, StrategyExecutionResult, StrategyExecutionRequest
)

logger = logging.getLogger(__name__)

# ============================================================================
# 執行引擎配置 (Execution Engine Configuration)
# ============================================================================

class ExecutionMode(str, Enum):
    """執行模式"""
    BACKTEST = "backtest"
    REAL_TIME = "real_time"
    PAPER_TRADING = "paper_trading"
    LIVE_TRADING = "live_trading"

class EngineStatus(str, Enum):
    """引擎狀態"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"

class MarketDataSource(str, Enum):
    """市場數據源"""
    SIMULATED = "simulated"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    QUANDL = "quandl"
    LOCAL_DATABASE = "local_database"
    REAL_TIME_FEED = "real_time_feed"

@dataclass
class EngineConfig:
    """執行引擎配置"""
    engine_id: str
    execution_mode: ExecutionMode
    market_data_source: MarketDataSource
    update_interval: timedelta = timedelta(seconds=1)
    max_concurrent_strategies: int = 10
    risk_management_enabled: bool = True
    performance_tracking: bool = True
    log_level: str = "INFO"
    cache_enabled: bool = True
    cache_ttl: timedelta = timedelta(minutes=5)

# ============================================================================
# 市場數據接口 (Market Data Interface)
# ============================================================================

@dataclass
class MarketData:
    """市場數據"""
    timestamp: datetime
    symbol: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    adjusted_close: Optional[float] = None
    technical_indicators: Dict[str, float] = field(default_factory=dict)
    sentiment_data: Optional[Dict[str, Any]] = None

class MarketDataProvider(ABC):
    """市場數據提供者抽象基類"""

    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[MarketData]:
        """獲取歷史數據"""
        pass

    @abstractmethod
    async def get_real_time_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """獲取實時數據"""
        pass

    @abstractmethod
    async def subscribe_real_time(
        self,
        symbols: List[str],
        callback: Callable[[str, MarketData], None]
    ) -> None:
        """訂閱實時數據"""
        pass

    @abstractmethod
    async def unsubscribe_real_time(self, symbols: List[str]) -> None:
        """取消訂閱實時數據"""
        pass

# ============================================================================
# 策略執行器接口 (Strategy Executor Interface)
# ============================================================================

class StrategyExecutor(ABC):
    """策略執行器抽象基類"""

    def __init__(self, strategy_id: str, strategy_type: StrategyType):
        self.strategy_id = strategy_id
        self.strategy_type = strategy_type
        self.logger = logging.getLogger(f"executor.{strategy_type.value}.{strategy_id}")

    @abstractmethod
    async def initialize(self, parameters: StrategyParameters) -> bool:
        """初始化執行器"""
        pass

    @abstractmethod
    async def execute(
        self,
        market_data: List[MarketData],
        execution_context: Dict[str, Any]
    ) -> List[StrategySignal]:
        """執行策略"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理資源"""
        pass

    @abstractmethod
    def get_required_data_fields(self) -> List[str]:
        """獲取所需的數據字段"""
        pass

# ============================================================================
# CBSC策略執行器實現 (CBSC Strategy Executors)
# ============================================================================

class DirectRSIExecutor(StrategyExecutor):
    """直接RSI策略執行器"""

    def __init__(self, strategy_id: str):
        super().__init__(strategy_id, StrategyType.DIRECT_RSI)
        self.rsi_period = 14
        self.oversold_threshold = 30
        self.overbought_threshold = 70
        self.rsi_values = []

    async def initialize(self, parameters: StrategyParameters) -> bool:
        """初始化RSI執行器"""
        try:
            self.rsi_period = parameters.rsi_period or 14
            self.oversold_threshold = parameters.oversold_threshold or 30
            self.overbought_threshold = parameters.overbought_threshold or 70
            self.rsi_values = []
            self.logger.info(f"RSI執行器初始化成功: 週期={self.rsi_period}, 超賣={self.oversold_threshold}, 超買={self.overbought_threshold}")
            return True
        except Exception as e:
            self.logger.error(f"RSI執行器初始化失敗: {e}")
            return False

    async def execute(
        self,
        market_data: List[MarketData],
        execution_context: Dict[str, Any]
    ) -> List[StrategySignal]:
        """執行直接RSI策略"""
        signals = []

        try:
            if not market_data:
                return signals

            # 計算RSI
            for data in market_data:
                close_price = data.close_price
                if not self.rsi_values:
                    self.rsi_values.append(close_price)
                else:
                    self.rsi_values.append(close_price)

                # 保持RSI週期長度
                if len(self.rsi_values) > self.rsi_period:
                    self.rsi_values.pop(0)

                # 計算RSI
                if len(self.rsi_values) >= self.rsi_period:
                    rsi = self._calculate_rsi(self.rsi_values)

                    # 生成信號
                    signal_type, strength, confidence = self._generate_signal(rsi)

                    if signal_type != "hold":
                        signal = StrategySignal(
                            signal_id=f"rsi_{self.strategy_id}_{data.timestamp.strftime('%Y%m%d_%H%M%S')}",
                            strategy_type=self.strategy_type,
                            signal_type=signal_type,
                            strength=strength,
                            confidence=confidence,
                            timestamp=data.timestamp,
                            market_data={
                                "price": close_price,
                                "volume": data.volume,
                                "rsi": rsi,
                                "high": data.high_price,
                                "low": data.low_price
                            },
                            parameters=StrategyParameters(
                                rsi_period=self.rsi_period,
                                oversold_threshold=self.oversold_threshold,
                                overbought_threshold=self.overbought_threshold
                            ),
                            metadata={
                                "execution_context": execution_context,
                                "signal_source": "direct_rsi"
                            }
                        )
                        signals.append(signal)

        except Exception as e:
            self.logger.error(f"RSI策略執行失敗: {e}")

        return signals

    async def cleanup(self) -> None:
        """清理資源"""
        self.rsi_values.clear()

    def get_required_data_fields(self) -> List[str]:
        """獲取所需的數據字段"""
        return ["close_price", "volume", "high_price", "low_price"]

    def _calculate_rsi(self, prices: List[float]) -> float:
        """計算RSI指標"""
        if len(prices) < 2:
            return 50.0

        # 計算價格變化
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # 分離漲跌
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]

        # 計算平均漲跌幅
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0

        # 避免除零
        if avg_loss == 0:
            return 100.0

        # 計算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _generate_signal(self, rsi: float) -> tuple:
        """基於RSI生成信號"""
        if rsi <= self.oversold_threshold:
            # 超賣，買入信號
            strength = (self.oversold_threshold - rsi) / self.oversold_threshold * 100
            confidence = min(90, 60 + strength * 0.3)
            return ("buy", strength, confidence)
        elif rsi >= self.overbought_threshold:
            # 超買，賣出信號
            strength = (rsi - self.overbought_threshold) / (100 - self.overbought_threshold) * 100
            confidence = min(90, 60 + strength * 0.3)
            return ("sell", strength, confidence)
        else:
            # 持有信號
            return ("hold", 50.0, 50.0)

class SentimentMomentumExecutor(StrategyExecutor):
    """情緒動量策略執行器"""

    def __init__(self, strategy_id: str):
        super().__init__(strategy_id, StrategyType.SENTIMENT_MOMENTUM)
        self.fast_period = 12
        self.slow_period = 26
        self.signal_period = 9
        self.sentiment_values = []
        self.macd_line = []
        self.signal_line = []

    async def initialize(self, parameters: StrategyParameters) -> bool:
        """初始化情緒動量執行器"""
        try:
            self.fast_period = parameters.fast_period or 12
            self.slow_period = parameters.slow_period or 26
            self.signal_period = parameters.signal_period or 9
            self.sentiment_values = []
            self.macd_line = []
            self.signal_line = []
            self.logger.info(f"情緒動量執行器初始化成功: 快速={self.fast_period}, 慢速={self.slow_period}")
            return True
        except Exception as e:
            self.logger.error(f"情緒動量執行器初始化失敗: {e}")
            return False

    async def execute(
        self,
        market_data: List[MarketData],
        execution_context: Dict[str, Any]
    ) -> List[StrategySignal]:
        """執行情緒動量策略"""
        signals = []

        try:
            if not market_data:
                return signals

            # 提取情緒數據
            for data in market_data:
                sentiment_strength = 0.0
                if data.sentiment_data and "sentiment_strength" in data.sentiment_data:
                    sentiment_strength = data.sentiment_data["sentiment_strength"]

                self.sentiment_values.append(sentiment_strength)

                # 保持最大週期長度
                if len(self.sentiment_values) > self.slow_period:
                    self.sentiment_values.pop(0)

                # 計算MACD風格的情緒動量
                if len(self.sentiment_values) >= self.slow_period:
                    macd_val = self._calculate_macd()
                    signal_val = self._calculate_signal_line()

                    # 生成信號
                    signal_type, strength, confidence = self._generate_macd_signal(macd_val, signal_val)

                    if signal_type != "hold":
                        signal = StrategySignal(
                            signal_id=f"sentiment_{self.strategy_id}_{data.timestamp.strftime('%Y%m%d_%H%M%S')}",
                            strategy_type=self.strategy_type,
                            signal_type=signal_type,
                            strength=strength,
                            confidence=confidence,
                            timestamp=data.timestamp,
                            market_data={
                                "price": data.close_price,
                                "volume": data.volume,
                                "sentiment_strength": sentiment_strength,
                                "macd": macd_val,
                                "signal_line": signal_val
                            },
                            parameters=StrategyParameters(
                                fast_period=self.fast_period,
                                slow_period=self.slow_period,
                                signal_period=self.signal_period
                            ),
                            metadata={
                                "execution_context": execution_context,
                                "signal_source": "sentiment_momentum"
                            }
                        )
                        signals.append(signal)

        except Exception as e:
            self.logger.error(f"情緒動量策略執行失敗: {e}")

        return signals

    async def cleanup(self) -> None:
        """清理資源"""
        self.sentiment_values.clear()
        self.macd_line.clear()
        self.signal_line.clear()

    def get_required_data_fields(self) -> List[str]:
        """獲取所需的數據字段"""
        return ["close_price", "volume", "sentiment_data"]

    def _calculate_macd(self) -> float:
        """計算MACD線"""
        if len(self.sentiment_values) < self.slow_period:
            return 0.0

        # 計算快速EMA
        fast_ema = self._calculate_ema(self.sentiment_values[-self.fast_period:])

        # 計算慢速EMA
        slow_ema = self._calculate_ema(self.sentiment_values[-self.slow_period:])

        return fast_ema - slow_ema

    def _calculate_ema(self, values: List[float], period: int = None) -> float:
        """計算EMA"""
        if not values:
            return 0.0

        if period is None:
            period = len(values)

        alpha = 2 / (period + 1)
        ema = values[0]

        for value in values[1:]:
            ema = alpha * value + (1 - alpha) * ema

        return ema

    def _calculate_signal_line(self) -> float:
        """計算信號線"""
        if not self.macd_line:
            return 0.0

        # 添加新的MACD值
        current_macd = self._calculate_macd()
        self.macd_line.append(current_macd)

        # 保持信號週期長度
        if len(self.macd_line) > self.signal_period:
            self.macd_line.pop(0)

        # 計算信號線（MACD的EMA）
        return self._calculate_ema(self.macd_line, self.signal_period)

    def _generate_macd_signal(self, macd: float, signal: float) -> tuple:
        """基於MACD生成信號"""
        diff = macd - signal

        if diff > 0.01:  # MACD在信號線上方
            strength = min(100, abs(diff) * 100)
            confidence = min(90, 60 + strength * 0.2)
            return ("buy", strength, confidence)
        elif diff < -0.01:  # MACD在信號線下方
            strength = min(100, abs(diff) * 100)
            confidence = min(90, 60 + strength * 0.2)
            return ("sell", strength, confidence)
        else:
            return ("hold", 50.0, 50.0)

# ============================================================================
# 策略執行引擎主類 (Strategy Execution Engine Main Class)
# ============================================================================

class CBSCStrategyExecutionEngine:
    """CBSC策略執行引擎"""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.status = EngineStatus.IDLE
        self.logger = logging.getLogger(f"engine.{config.engine_id}")

        # 執行器註冊表
        self.executors: Dict[str, StrategyExecutor] = {}
        self.running_strategies: Dict[str, asyncio.Task] = {}

        # 市場數據提供者
        self.market_data_provider: Optional[MarketDataProvider] = None

        # 性能追蹤
        self.performance_tracker: Dict[str, StrategyPerformance] = {}

        # 事件回調
        self.signal_callbacks: List[Callable[[StrategySignal], None]] = []
        self.error_callbacks: List[Callable[[str, Exception], None]] = []

    async def initialize(self, market_data_provider: MarketDataProvider) -> bool:
        """初始化執行引擎"""
        try:
            self.status = EngineStatus.INITIALIZING
            self.market_data_provider = market_data_provider

            self.logger.info(f"策略執行引擎初始化開始: {self.config.engine_id}")

            # 註冊內置執行器
            self._register_builtin_executors()

            self.status = EngineStatus.IDLE
            self.logger.info("策略執行引擎初始化完成")
            return True

        except Exception as e:
            self.status = EngineStatus.ERROR
            self.logger.error(f"策略執行引擎初始化失敗: {e}")
            return False

    def _register_builtin_executors(self):
        """註冊內置執行器"""
        # 這裡可以註冊更多的執行器類型
        self.logger.info("內置執行器註冊完成")

    async def start_strategy(
        self,
        strategy: Strategy,
        execution_request: StrategyExecutionRequest
    ) -> bool:
        """啟動策略執行"""
        try:
            if self.status != EngineStatus.IDLE:
                raise RuntimeError(f"引擎狀態不正確: {self.status}")

            if strategy.id in self.running_strategies:
                raise ValueError(f"策略已在運行: {strategy.id}")

            if len(self.running_strategies) >= self.config.max_concurrent_strategies:
                raise RuntimeError(f"超出最大並發策略數量: {self.config.max_concurrent_strategies}")

            # 創建執行器
            executor = self._create_executor(strategy)
            if not executor:
                raise ValueError(f"不支持的策略類型: {strategy.strategy_type}")

            # 初始化執行器
            if not await executor.initialize(strategy.parameters):
                raise RuntimeError("執行器初始化失敗")

            # 啟動執行任務
            task = asyncio.create_task(
                self._execute_strategy_loop(executor, strategy, execution_request)
            )

            self.running_strategies[strategy.id] = task
            self.executors[strategy.id] = executor

            self.logger.info(f"策略啟動成功: {strategy.id}")
            return True

        except Exception as e:
            self.logger.error(f"啟動策略失敗: {e}")
            await self._notify_error(strategy.id, e)
            return False

    async def stop_strategy(self, strategy_id: str) -> bool:
        """停止策略執行"""
        try:
            if strategy_id not in self.running_strategies:
                raise ValueError(f"策略未在運行: {strategy_id}")

            # 取消執行任務
            task = self.running_strategies[strategy_id]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # 清理執行器
            if strategy_id in self.executors:
                await self.executors[strategy_id].cleanup()
                del self.executors[strategy_id]

            # 移除運行記錄
            del self.running_strategies[strategy_id]

            self.logger.info(f"策略停止成功: {strategy_id}")
            return True

        except Exception as e:
            self.logger.error(f"停止策略失敗: {e}")
            await self._notify_error(strategy_id, e)
            return False

    def _create_executor(self, strategy: Strategy) -> Optional[StrategyExecutor]:
        """創建策略執行器"""
        try:
            if strategy.strategy_type == StrategyType.DIRECT_RSI:
                return DirectRSIExecutor(strategy.id)
            elif strategy.strategy_type == StrategyType.SENTIMENT_MOMENTUM:
                return SentimentMomentumExecutor(strategy.id)
            else:
                self.logger.warning(f"不支持的策略類型: {strategy.strategy_type}")
                return None
        except Exception as e:
            self.logger.error(f"創建執行器失敗: {e}")
            return None

    async def _execute_strategy_loop(
        self,
        executor: StrategyExecutor,
        strategy: Strategy,
        execution_request: StrategyExecutionRequest
    ):
        """策略執行循環"""
        try:
            self.logger.info(f"開始執行策略: {strategy.id}")

            # 獲取市場數據
            if self.config.execution_mode == ExecutionMode.BACKTEST:
                market_data = await self._get_backtest_data(execution_request)
            else:
                market_data = await self._get_realtime_data(execution_request)

            # 執行策略
            signals = await executor.execute(market_data, {
                "execution_mode": self.config.execution_mode,
                "execution_request": execution_request
            })

            # 處理信號
            for signal in signals:
                await self._process_signal(signal)

            self.logger.info(f"策略執行完成: {strategy.id}, 生成信號: {len(signals)}")

        except asyncio.CancelledError:
            self.logger.info(f"策略執行被取消: {strategy.id}")
        except Exception as e:
            self.logger.error(f"策略執行失敗: {e}")
            await self._notify_error(strategy.id, e)

    async def _get_backtest_data(self, execution_request: StrategyExecutionRequest) -> List[MarketData]:
        """獲取回測數據"""
        # 模擬回測數據
        data = []
        start_date = execution_request.start_time or datetime.now() - timedelta(days=30)
        end_date = execution_request.end_time or datetime.now()

        current_date = start_date
        base_price = 150.0

        while current_date <= end_date:
            # 生成模擬市場數據
            price_change = np.random.normal(0, 0.02)  # 2% 日波動
            base_price *= (1 + price_change)

            market_data = MarketData(
                timestamp=current_date,
                symbol="HSI",
                open_price=base_price,
                high_price=base_price * (1 + abs(np.random.normal(0, 0.01))),
                low_price=base_price * (1 - abs(np.random.normal(0, 0.01))),
                close_price=base_price,
                volume=int(np.random.normal(1000000, 200000)),
                sentiment_data={
                    "sentiment_strength": np.random.uniform(-1, 1)
                }
            )
            data.append(market_data)
            current_date += timedelta(days=1)

        return data

    async def _get_realtime_data(self, execution_request: StrategyExecutionRequest) -> List[MarketData]:
        """獲取實時數據"""
        # 模擬實時數據
        data = []
        current_time = datetime.now()
        base_price = 18500.0

        for i in range(60):  # 最近60個數據點
            price_change = np.random.normal(0, 0.001)  # 0.1% 波動
            base_price *= (1 + price_change)

            market_data = MarketData(
                timestamp=current_time - timedelta(minutes=i),
                symbol="HSI",
                open_price=base_price,
                high_price=base_price * (1 + abs(np.random.normal(0, 0.0005))),
                low_price=base_price * (1 - abs(np.random.normal(0, 0.0005))),
                close_price=base_price,
                volume=int(np.random.normal(500000, 100000)),
                sentiment_data={
                    "sentiment_strength": np.random.uniform(-1, 1)
                }
            )
            data.append(market_data)

        return data

    async def _process_signal(self, signal: StrategySignal):
        """處理策略信號"""
        try:
            self.logger.info(f"處理信號: {signal.signal_id} - {signal.signal_type}")

            # 通知信號回調
            for callback in self.signal_callbacks:
                try:
                    callback(signal)
                except Exception as e:
                    self.logger.error(f"信號回調執行失敗: {e}")

        except Exception as e:
            self.logger.error(f"處理信號失敗: {e}")

    async def _notify_error(self, strategy_id: str, error: Exception):
        """通知錯誤"""
        try:
            for callback in self.error_callbacks:
                try:
                    callback(strategy_id, error)
                except Exception as e:
                    self.logger.error(f"錯誤回調執行失敗: {e}")
        except Exception as e:
            self.logger.error(f"通知錯誤失敗: {e}")

    def add_signal_callback(self, callback: Callable[[StrategySignal], None]):
        """添加信號回調"""
        self.signal_callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[str, Exception], None]):
        """添加錯誤回調"""
        self.error_callbacks.append(callback)

    async def get_engine_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        return {
            "engine_id": self.config.engine_id,
            "status": self.status,
            "running_strategies": list(self.running_strategies.keys()),
            "max_concurrent_strategies": self.config.max_concurrent_strategies,
            "execution_mode": self.config.execution_mode,
            "market_data_source": self.config.market_data_source
        }

    async def cleanup(self):
        """清理引擎資源"""
        try:
            self.logger.info("開始清理執行引擎資源")

            # 停止所有運行中的策略
            for strategy_id in list(self.running_strategies.keys()):
                await self.stop_strategy(strategy_id)

            # 清理執行器
            for executor in self.executors.values():
                await executor.cleanup()

            self.executors.clear()
            self.running_strategies.clear()

            self.status = EngineStatus.IDLE
            self.logger.info("執行引擎資源清理完成")

        except Exception as e:
            self.logger.error(f"清理執行引擎資源失敗: {e}")

# ============================================================================
# 導出 (Exports)
# ============================================================================

__all__ = [
    "ExecutionMode",
    "EngineStatus",
    "MarketDataSource",
    "EngineConfig",
    "MarketData",
    "MarketDataProvider",
    "StrategyExecutor",
    "DirectRSIExecutor",
    "SentimentMomentumExecutor",
    "CBSCStrategyExecutionEngine"
]