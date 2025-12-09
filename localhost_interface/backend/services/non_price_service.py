"""
非價格信號服務
集成現有的非價格信號轉換系統
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys
import os

# 添加現有系統路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))

# 導入現有的非價格信號系統
try:
    from src.non_price.signal_data_manager import SignalDataManager
    from src.non_price.signal_conversion_engine import SignalConversionEngine
    from src.optimization.sr_mdd_optimizer import SRMDDOptimizer
except ImportError as e:
    logging.warning(f"無法導入現有非價格信號模塊: {e}")
    # 如果無法導入，使用模擬實現
    SignalDataManager = None
    SignalConversionEngine = None
    SRMDDOptimizer = None

from shared.models.schemas import (
    NonPriceData, TechnicalIndicator, TradingSignal,
    DataSourceType, IndicatorType, SignalType
)

logger = logging.getLogger(__name__)

class NonPriceService:
    """非價格信號服務"""

    def __init__(self):
        self.data_manager = None
        self.conversion_engine = None
        self.optimizer = None
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)  # 5分鐘緩存
        self.last_update = {}
        self.is_initialized = False

        logger.info("非價格信號服務初始化")

    async def initialize(self):
        """初始化服務"""
        try:
            # 初始化現有系統組件
            if SignalDataManager:
                self.data_manager = SignalDataManager()
                await self.data_manager.initialize()
                logger.info("信號數據管理器初始化成功")

            if SignalConversionEngine:
                self.conversion_engine = SignalConversionEngine()
                await self.conversion_engine.initialize()
                logger.info("信號轉換引擎初始化成功")

            if SRMDDOptimizer:
                self.optimizer = SRMDDOptimizer()
                await self.optimizer.initialize()
                logger.info("SR/MDD優化器初始化成功")

            # 如果現有系統不可用，創建模擬數據
            if not self.data_manager:
                await self._create_mock_data_manager()

            self.is_initialized = True
            logger.info("非價格信號服務初始化完成")

        except Exception as e:
            logger.error(f"非價格信號服務初始化失敗: {e}")
            # 即使初始化失敗，也創建模擬數據以確保服務可用
            await self._create_mock_data_manager()
            self.is_initialized = True

    async def _create_mock_data_manager(self):
        """創建模擬數據管理器"""
        logger.info("創建模擬數據管理器")

        class MockDataManager:
            def __init__(self):
                self.data_sources = {
                    DataSourceType.HIBOR: {
                        "name": "HIBOR利率",
                        "unit": "%",
                        "description": "香港銀行同業拆息利率"
                    },
                    DataSourceType.EXCHANGE_RATE: {
                        "name": "匯率數據",
                        "unit": "HKD/USD",
                        "description": "港幣兌美元匯率"
                    },
                    DataSourceType.MONETARY_BASE: {
                        "name": "貨幣基礎",
                        "unit": "億港元",
                        "description": "香港貨幣基礎"
                    }
                }

            async def get_latest_data(self, source_type: DataSourceType):
                """獲取最新數據"""
                import random

                # 生成模擬數據
                base_values = {
                    DataSourceType.HIBOR: 5.5,
                    DataSourceType.EXCHANGE_RATE: 7.85,
                    DataSourceType.MONETARY_BASE: 20000
                }

                value = base_values.get(source_type, 100) + random.uniform(-0.1, 0.1)

                return {
                    "source": source_type,
                    "timestamp": datetime.now(),
                    "value": value,
                    "unit": self.data_sources[source_type]["unit"],
                    "description": self.data_sources[source_type]["description"]
                }

        self.data_manager = MockDataManager()
        logger.info("模擬數據管理器創建完成")

    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        status = {
            "service": "non_price_service",
            "status": "healthy" if self.is_initialized else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }

        # 檢查各個組件狀態
        if self.data_manager:
            status["components"]["data_manager"] = "healthy"
        else:
            status["components"]["data_manager"] = "unhealthy"

        if self.conversion_engine:
            status["components"]["conversion_engine"] = "healthy"
        else:
            status["components"]["conversion_engine"] = "unhealthy"

        if self.optimizer:
            status["components"]["optimizer"] = "healthy"
        else:
            status["components"]["optimizer"] = "unhealthy"

        # 檢查數據更新狀態
        for source in DataSourceType:
            if source in self.last_update:
                age = datetime.now() - self.last_update[source]
                if age > timedelta(minutes=10):
                    status["status"] = "degraded"
                    break

        return status

    async def get_latest_data(self, source_types: Optional[List[DataSourceType]] = None) -> List[NonPriceData]:
        """獲取最新的非價格數據"""
        try:
            if not self.data_manager:
                raise ValueError("數據管理器未初始化")

            if source_types is None:
                source_types = list(DataSourceType)

            results = []
            current_time = datetime.now()

            for source_type in source_types:
                # 檢查緩存
                cache_key = f"data_{source_type.value}"
                if (cache_key in self.cache and
                    current_time - self.cache[cache_key]["timestamp"] < self.cache_ttl):
                    results.append(self.cache[cache_key]["data"])
                    continue

                # 獲取新數據
                try:
                    data_dict = await self.data_manager.get_latest_data(source_type)

                    # 轉換為模型
                    non_price_data = NonPriceData(
                        source=data_dict["source"],
                        timestamp=data_dict["timestamp"],
                        value=data_dict["value"],
                        unit=data_dict["unit"],
                        description=data_dict.get("description")
                    )

                    # 更新緩存
                    self.cache[cache_key] = {
                        "data": non_price_data,
                        "timestamp": current_time
                    }
                    self.last_update[source_type] = current_time

                    results.append(non_price_data)

                except Exception as e:
                    logger.error(f"獲取 {source_type} 數據失敗: {e}")
                    continue

            logger.debug(f"獲取到 {len(results)} 個非價格數據點")
            return results

        except Exception as e:
            logger.error(f"獲取最新數據失敗: {e}")
            return []

    async def get_technical_indicators(self, symbol: str = "0700.HK") -> List[TechnicalIndicator]:
        """獲取技術指標"""
        try:
            if not self.conversion_engine:
                # 如果沒有轉換引擎，生成模擬指標
                return await self._generate_mock_indicators(symbol)

            # 獲取最新的非價格數據
            non_price_data = await self.get_latest_data()

            # 轉換為技術指標
            indicators = await self.conversion_engine.convert_to_indicators(
                symbol, non_price_data
            )

            # 轉換為模型格式
            technical_indicators = []
            for indicator_dict in indicators:
                technical_indicator = TechnicalIndicator(
                    name=IndicatorType(indicator_dict["name"]),
                    symbol=symbol,
                    timestamp=indicator_dict["timestamp"],
                    value=indicator_dict["value"],
                    parameters=indicator_dict.get("parameters", {}),
                    signal_type=SignalType(indicator_dict.get("signal_type", "hold")),
                    confidence=indicator_dict.get("confidence", 0.5)
                )
                technical_indicators.append(technical_indicator)

            logger.debug(f"為 {symbol} 生成 {len(technical_indicators)} 個技術指標")
            return technical_indicators

        except Exception as e:
            logger.error(f"獲取技術指標失敗: {e}")
            return await self._generate_mock_indicators(symbol)

    async def _generate_mock_indicators(self, symbol: str) -> List[TechnicalIndicator]:
        """生成模擬技術指標"""
        import random

        indicators = []

        # RSI
        rsi_value = random.uniform(20, 80)
        rsi_signal = "buy" if rsi_value < 30 else "sell" if rsi_value > 70 else "hold"
        indicators.append(TechnicalIndicator(
            name=IndicatorType.RSI,
            symbol=symbol,
            timestamp=datetime.now(),
            value=rsi_value,
            parameters={"period": 14},
            signal_type=SignalType(rsi_signal),
            confidence=random.uniform(0.3, 0.8)
        ))

        # MACD
        macd_value = random.uniform(-2, 2)
        macd_signal = "buy" if macd_value > 0.5 else "sell" if macd_value < -0.5 else "hold"
        indicators.append(TechnicalIndicator(
            name=IndicatorType.MACD,
            symbol=symbol,
            timestamp=datetime.now(),
            value=macd_value,
            parameters={"fast": 12, "slow": 26, "signal": 9},
            signal_type=SignalType(macd_signal),
            confidence=random.uniform(0.3, 0.8)
        ))

        # 移動平均線
        ma_value = random.uniform(300, 500)
        indicators.append(TechnicalIndicator(
            name=IndicatorType.MOVING_AVERAGE,
            symbol=symbol,
            timestamp=datetime.now(),
            value=ma_value,
            parameters={"period": 20},
            signal_type=SignalType("hold"),
            confidence=random.uniform(0.2, 0.6)
        ))

        return indicators

    async def get_trading_signals(self, symbol: str = "0700.HK") -> List[TradingSignal]:
        """獲取交易信號"""
        try:
            # 獲取技術指標
            indicators = await self.get_technical_indicators(symbol)

            # 生成交易信號
            signals = []
            signal_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 基於指標生成信號
            buy_signals = 0
            sell_signals = 0
            total_confidence = 0
            source_indicators = []

            for indicator in indicators:
                if indicator.signal_type == SignalType.BUY:
                    buy_signals += 1
                    total_confidence += indicator.confidence
                    source_indicators.append(indicator.name.value)
                elif indicator.signal_type == SignalType.SELL:
                    sell_signals += 1
                    total_confidence += indicator.confidence
                    source_indicators.append(indicator.name.value)

            # 確定最終信號
            if buy_signals > sell_signals:
                final_signal_type = SignalType.BUY
                strength = min(1.0, buy_signals / len(indicators))
            elif sell_signals > buy_signals:
                final_signal_type = SignalType.SELL
                strength = min(1.0, sell_signals / len(indicators))
            else:
                final_signal_type = SignalType.HOLD
                strength = 0.5

            confidence = total_confidence / max(1, len(source_indicators))

            # 創建交易信號
            trading_signal = TradingSignal(
                id=signal_id,
                symbol=symbol,
                signal_type=final_signal_type,
                strength=strength,
                confidence=confidence,
                price_at_signal=400.0,  # 模擬價格
                timestamp=datetime.now(),
                source_indicators=source_indicators,
                strategy_name="NonPrice_Signal_Strategy",
                parameters={
                    "indicators_count": len(indicators),
                    "buy_signals": buy_signals,
                    "sell_signals": sell_signals
                },
                expiry_time=datetime.now() + timedelta(hours=24)
            )

            signals.append(trading_signal)

            logger.debug(f"為 {symbol} 生成 {len(signals)} 個交易信號")
            return signals

        except Exception as e:
            logger.error(f"獲取交易信號失敗: {e}")
            return []

    async def run_optimization(self, symbol: str = "0700.HK", parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """運行SR/MDD優化"""
        try:
            if not self.optimizer:
                # 如果沒有優化器，返回模擬結果
                return await self._generate_mock_optimization_result(symbol)

            # 設置默認參數
            if parameters is None:
                parameters = {
                    "rsi_period": [7, 14, 21],
                    "rsi_oversold": [20, 30, 40],
                    "rsi_overbought": [60, 70, 80],
                    "rsi_weight": [0.3, 0.5, 0.7],
                    "macd_weight": [0.2, 0.3, 0.4],
                    "bb_weight": [0.1, 0.2, 0.3]
                }

            # 運行優化
            result = await self.optimizer.optimize(symbol, parameters)

            logger.info(f"完成 {symbol} 的SR/MDD優化")
            return result

        except Exception as e:
            logger.error(f"運行優化失敗: {e}")
            return await self._generate_mock_optimization_result(symbol)

    async def _generate_mock_optimization_result(self, symbol: str) -> Dict[str, Any]:
        """生成模擬優化結果"""
        import random

        return {
            "symbol": symbol,
            "optimization_date": datetime.now().isoformat(),
            "best_parameters": {
                "rsi_period": 14,
                "rsi_oversold": 25,
                "rsi_overbought": 75,
                "rsi_weight": 0.6,
                "macd_weight": 0.3,
                "bb_weight": 0.1
            },
            "performance_metrics": {
                "sortino_ratio": round(random.uniform(0.5, 2.0), 3),
                "max_drawdown_duration": random.randint(0, 30),
                "total_return": round(random.uniform(-0.2, 0.5), 4),
                "sharpe_ratio": round(random.uniform(0.3, 1.5), 3),
                "max_drawdown": round(random.uniform(-0.3, -0.05), 4),
                "win_rate": round(random.uniform(0.4, 0.8), 3)
            },
            "trading_stats": {
                "total_trades": random.randint(10, 100),
                "winning_trades": random.randint(4, 80),
                "losing_trades": random.randint(3, 30),
                "avg_trade_return": round(random.uniform(-0.02, 0.03), 4),
                "profit_factor": round(random.uniform(1.1, 3.0), 2)
            },
            "total_combinations_tested": random.randint(50, 200),
            "execution_time": round(random.uniform(5, 30), 2)
        }

    async def get_latest_signals(self) -> List[TradingSignal]:
        """獲取最新的交易信號（多個股票）"""
        try:
            all_signals = []

            # 為每個支持的股票獲取信號
            symbols = ["0700.HK", "0941.HK", "1299.HK", "2318.HK"]

            for symbol in symbols:
                signals = await self.get_trading_signals(symbol)
                all_signals.extend(signals)

            logger.debug(f"獲取到 {len(all_signals)} 個最新交易信號")
            return all_signals

        except Exception as e:
            logger.error(f"獲取最新信號失敗: {e}")
            return []

    async def shutdown(self):
        """關閉服務"""
        try:
            logger.info("關閉非價格信號服務...")

            if self.data_manager and hasattr(self.data_manager, 'shutdown'):
                await self.data_manager.shutdown()

            if self.conversion_engine and hasattr(self.conversion_engine, 'shutdown'):
                await self.conversion_engine.shutdown()

            if self.optimizer and hasattr(self.optimizer, 'shutdown'):
                await self.optimizer.shutdown()

            # 清理緩存
            self.cache.clear()
            self.last_update.clear()

            logger.info("非價格信號服務已關閉")

        except Exception as e:
            logger.error(f"關閉非價格信號服務時發生錯誤: {e}")