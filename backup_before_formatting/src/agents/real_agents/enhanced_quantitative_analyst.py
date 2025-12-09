"""
增強型量化分析師 - 真實AI模型驅動

使用機器學習模型進行真實的量化分析
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ...data_adapters.base_adapter import RealMarketData
from ...data_adapters.data_service import DataService
from .base_real_agent import BaseRealAgent, RealAgentConfig, RealAgentStatus
from .enhanced_ml_models import EnhancedMLModels, TechnicalIndicatorEngine
from .real_data_analyzer import AnalysisResult, SignalStrength


class EnhancedQuantitativeAnalyst(BaseRealAgent):
    """增強型量化分析師Agent"""

    def __init__(self, config: RealAgentConfig):
        super().__init__(config)
        self.logger = logging.getLogger(
            f"hk_quant_system.enhanced_quant_analyst.{config.agent_id}"
        )

        # 初始化組件
        self.ml_models = EnhancedMLModels()
        self.technical_engine = TechnicalIndicatorEngine()
        self.data_service = DataService()

        # 分析配置
        self.analysis_symbols = config.config.get(
            "analysis_symbols", ["AAPL", "MSFT", "GOOGL"]
        )
        self.lookback_days = config.config.get("lookback_days", 252)
        self.min_data_points = config.config.get("min_data_points", 100)

        # 模型狀態
        self.models_trained = False
        self.last_model_update = None
        self.model_update_interval = timedelta(hours=24)  # 每24小時更新模型

    async def _initialize_specific(self) -> bool:
        """初始化Agent特定組件"""
        try:
            self.logger.info("Initializing enhanced quantitative analyst...")

            # 初始化數據服務
            if not await self.data_service.initialize():
                self.logger.error("Failed to initialize data service")
                return False

            # 加載或訓練模型
            await self._load_or_train_models()

            # 初始化技術分析引擎
            self.logger.info("Technical analysis engine initialized")

            self.logger.info("Enhanced quantitative analyst initialized successfully")
            return True

        except Exception as e:
            self.logger.exception(
                f"Failed to initialize enhanced quantitative analyst: {e}"
            )
            return False

    async def _load_or_train_models(self) -> None:
        """加載或訓練模型"""
        try:
            # 嘗試加載現有模型
            models_path = f"models/{self.config.agent_id}"
            if await self.ml_models.load_models(models_path):
                self.logger.info("Loaded existing ML models")
                self.models_trained = True
                return

            # 如果沒有現有模型，訓練新模型
            self.logger.info("No existing models found, training new models...")
            await self._train_models()

        except Exception as e:
            self.logger.error(f"Error loading / training models: {e}")

    async def _train_models(self) -> None:
        """訓練機器學習模型"""
        try:
            self.logger.info("Training ML models...")

            # 獲取訓練數據
            training_data = await self._get_training_data()
            if training_data.empty:
                self.logger.error("No training data available")
                return

            # 訓練價格預測模型
            price_model = await self.ml_models.create_price_prediction_model(
                training_data
            )
            if price_model:
                self.logger.info("Price prediction model trained successfully")

            # 訓練信號分類模型
            signal_model = await self.ml_models.create_signal_classification_model(
                training_data
            )
            if signal_model:
                self.logger.info("Signal classification model trained successfully")

            # 訓練波動率預測模型
            volatility_model = await self.ml_models.create_volatility_prediction_model(
                training_data
            )
            if volatility_model:
                self.logger.info("Volatility prediction model trained successfully")

            # 保存模型
            models_path = f"models/{self.config.agent_id}"
            await self.ml_models.save_models(models_path)

            self.models_trained = True
            self.last_model_update = datetime.now()
            self.logger.info("All ML models trained and saved successfully")

        except Exception as e:
            self.logger.exception(f"Error training models: {e}")

    async def _get_training_data(self) -> pd.DataFrame:
        """獲取訓練數據"""
        try:
            all_data = []

            for symbol in self.analysis_symbols:
                self.logger.info(f"Fetching training data for {symbol}...")

                # 獲取歷史數據
                end_date = datetime.now().date()
                start_date = end_date - timedelta(
                    days=self.lookback_days * 2
                )  # 獲取更多數據用於訓練

                market_data = await self.data_service.get_market_data(
                    symbol=symbol, start_date=start_date, end_date=end_date
                )

                if not market_data:
                    self.logger.warning(f"No data found for {symbol}")
                    continue

                # 轉換為DataFrame
                symbol_data = []
                for data_point in market_data:
                    symbol_data.append(
                        {
                            "timestamp": data_point.timestamp,
                            "symbol": data_point.symbol,
                            "open": float(data_point.open_price),
                            "high": float(data_point.high_price),
                            "low": float(data_point.low_price),
                            "close": float(data_point.close_price),
                            "volume": data_point.volume,
                        }
                    )

                symbol_df = pd.DataFrame(symbol_data)
                symbol_df.set_index("timestamp", inplace=True)
                symbol_df.sort_index(inplace=True)

                all_data.append(symbol_df)

            if not all_data:
                self.logger.error("No training data collected")
                return pd.DataFrame()

            # 合併所有數據
            combined_data = pd.concat(all_data, ignore_index=False)
            combined_data.sort_index(inplace=True)

            self.logger.info(f"Collected {len(combined_data)} training data points")
            return combined_data

        except Exception as e:
            self.logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()

    async def _enhance_analysis(
        self, base_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """使用AI模型增強分析"""
        try:
            if not self.models_trained:
                self.logger.warning("Models not trained, using base analysis only")
                return base_result

            # 檢查是否需要更新模型
            if (
                self.last_model_update is None
                or datetime.now() - self.last_model_update > self.model_update_interval
            ):
                await self._train_models()

            # 轉換市場數據為DataFrame
            df_data = []
            for data_point in market_data:
                df_data.append(
                    {
                        "timestamp": data_point.timestamp,
                        "symbol": data_point.symbol,
                        "open": float(data_point.open_price),
                        "high": float(data_point.high_price),
                        "low": float(data_point.low_price),
                        "close": float(data_point.close_price),
                        "volume": data_point.volume,
                    }
                )

            df = pd.DataFrame(df_data)
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            if len(df) < self.min_data_points:
                self.logger.warning("Insufficient data for ML analysis")
                return base_result

            # 使用AI模型進行預測
            enhanced_insights = base_result.insights.copy()
            enhanced_warnings = base_result.warnings.copy()

            # 預測價格方向
            direction_prediction = await self.ml_models.predict_price_direction(df)
            if direction_prediction["confidence"] > 0.6:
                signal_text = f"AI預測: {direction_prediction['signal']} (置信度: {direction_prediction['confidence']:.2%})"
                enhanced_insights.append(signal_text)

            # 預測未來收益率
            return_prediction = await self.ml_models.predict_future_return(df)
            if return_prediction["confidence"] > 0.5:
                direction_text = f"AI預測收益率: {return_prediction['prediction']:.2%} ({return_prediction['direction']})"
                enhanced_insights.append(direction_text)

            # 計算增強的技術指標
            enhanced_indicators = await self._calculate_enhanced_indicators(df)

            # 更新信號強度和置信度
            enhanced_signal_strength = self._calculate_enhanced_signal_strength(
                base_result.signal_strength, direction_prediction, return_prediction
            )

            enhanced_confidence = self._calculate_enhanced_confidence(
                base_result.confidence,
                direction_prediction["confidence"],
                return_prediction["confidence"],
            )

            # 創建增強的分析結果
            enhanced_result = AnalysisResult(
                timestamp=base_result.timestamp,
                symbols_analyzed=base_result.symbols_analyzed,
                technical_indicators={
                    **base_result.technical_indicators,
                    **enhanced_indicators,
                },
                signal_strength=enhanced_signal_strength,
                signal_direction=base_result.signal_direction,
                confidence=enhanced_confidence,
                market_regime=base_result.market_regime,
                risk_metrics=base_result.risk_metrics,
                data_quality=base_result.data_quality,
                analysis_quality=base_result.analysis_quality,
                insights=enhanced_insights,
                warnings=enhanced_warnings,
            )

            return enhanced_result

        except Exception as e:
            self.logger.error(f"Error enhancing analysis: {e}")
            return base_result

    async def _calculate_enhanced_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算增強的技術指標"""
        try:
            enhanced_indicators = {}

            # 計算高級技術指標
            for symbol in df["symbol"].unique():
                symbol_data = df[df["symbol"] == symbol]

                if len(symbol_data) < 20:
                    continue

                symbol_indicators = {}

                # 計算多個週期的移動平均線
                for period in [5, 10, 20, 50, 200]:
                    if len(symbol_data) >= period:
                        sma = self.technical_engine.calculate_sma(
                            symbol_data["close"], period
                        )
                        symbol_indicators[f"sma_{period}"] = (
                            float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None
                        )

                # 計算MACD
                macd_line, signal_line, histogram = (
                    self.technical_engine.calculate_macd(symbol_data["close"])
                )
                symbol_indicators["macd"] = (
                    float(macd_line.iloc[-1])
                    if not pd.isna(macd_line.iloc[-1])
                    else None
                )
                symbol_indicators["macd_signal"] = (
                    float(signal_line.iloc[-1])
                    if not pd.isna(signal_line.iloc[-1])
                    else None
                )
                symbol_indicators["macd_histogram"] = (
                    float(histogram.iloc[-1])
                    if not pd.isna(histogram.iloc[-1])
                    else None
                )

                # 計算布林帶
                bb_upper, bb_middle, bb_lower = (
                    self.technical_engine.calculate_bollinger_bands(
                        symbol_data["close"]
                    )
                )
                symbol_indicators["bb_upper"] = (
                    float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None
                )
                symbol_indicators["bb_middle"] = (
                    float(bb_middle.iloc[-1])
                    if not pd.isna(bb_middle.iloc[-1])
                    else None
                )
                symbol_indicators["bb_lower"] = (
                    float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None
                )

                # 計算RSI
                rsi = self.technical_engine.calculate_rsi(symbol_data["close"])
                symbol_indicators["rsi"] = (
                    float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
                )

                # 計算ATR
                atr = self.technical_engine.calculate_atr(
                    symbol_data["high"], symbol_data["low"], symbol_data["close"]
                )
                symbol_indicators["atr"] = (
                    float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None
                )

                enhanced_indicators[symbol] = symbol_indicators

            return enhanced_indicators

        except Exception as e:
            self.logger.error(f"Error calculating enhanced indicators: {e}")
            return {}

    def _calculate_enhanced_signal_strength(
        self, base_strength: float, direction_pred: Dict, return_pred: Dict
    ) -> float:
        """計算增強的信號強度"""
        try:
            # 基礎信號強度
            enhanced_strength = base_strength

            # AI預測增強
            direction_confidence = direction_pred.get("confidence", 0)
            return_confidence = return_pred.get("confidence", 0)

            # 如果AI預測置信度高，增強信號強度
            if direction_confidence > 0.7:
                enhanced_strength += 0.1
            elif direction_confidence > 0.5:
                enhanced_strength += 0.05

            if return_confidence > 0.7:
                enhanced_strength += 0.1
            elif return_confidence > 0.5:
                enhanced_strength += 0.05

            # 確保信號強度在合理範圍內
            return min(max(enhanced_strength, 0.0), 1.0)

        except Exception as e:
            self.logger.error(f"Error calculating enhanced signal strength: {e}")
            return base_strength

    def _calculate_enhanced_confidence(
        self,
        base_confidence: float,
        direction_confidence: float,
        return_confidence: float,
    ) -> float:
        """計算增強的置信度"""
        try:
            # 基礎置信度
            enhanced_confidence = base_confidence

            # AI預測置信度加權平均
            ai_confidence = (direction_confidence + return_confidence) / 2

            # 如果AI置信度高，提升整體置信度
            if ai_confidence > 0.7:
                enhanced_confidence = max(enhanced_confidence, ai_confidence * 0.8)
            elif ai_confidence > 0.5:
                enhanced_confidence = max(enhanced_confidence, ai_confidence * 0.6)

            # 確保置信度在合理範圍內
            return min(max(enhanced_confidence, 0.0), 1.0)

        except Exception as e:
            self.logger.error(f"Error calculating enhanced confidence: {e}")
            return base_confidence

    async def _enhance_signals(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """使用AI模型增強交易信號"""
        try:
            enhanced_signals = []

            for signal in base_signals:
                enhanced_signal = signal.copy()

                # 使用AI模型驗證信號
                symbol = signal.get("symbol")
                if symbol and self.models_trained:
                    # 獲取該標的的最新數據進行AI驗證
                    market_data = await self.data_service.get_market_data(symbol)
                    if market_data:
                        # 轉換為DataFrame
                        df_data = []
                        for data_point in market_data[-100:]:  # 使用最近100個數據點
                            df_data.append(
                                {
                                    "timestamp": data_point.timestamp,
                                    "symbol": data_point.symbol,
                                    "open": float(data_point.open_price),
                                    "high": float(data_point.high_price),
                                    "low": float(data_point.low_price),
                                    "close": float(data_point.close_price),
                                    "volume": data_point.volume,
                                }
                            )

                        df = pd.DataFrame(df_data)
                        df.set_index("timestamp", inplace=True)

                        if len(df) >= self.min_data_points:
                            # AI預測驗證
                            direction_pred = (
                                await self.ml_models.predict_price_direction(df)
                            )
                            return_pred = await self.ml_models.predict_future_return(df)

                            # 如果AI預測與信號方向一致，增強信號
                            if (
                                signal["signal_type"] == "buy"
                                and direction_pred["signal"] == "buy"
                            ) or (
                                signal["signal_type"] == "sell"
                                and direction_pred["signal"] == "sell"
                            ):
                                enhanced_signal["strength"] = min(
                                    enhanced_signal["strength"] + 0.1, 1.0
                                )
                                enhanced_signal["confidence"] = min(
                                    enhanced_signal["confidence"] + 0.1, 1.0
                                )
                                enhanced_signal["ai_validated"] = True
                                enhanced_signal["ai_confidence"] = direction_pred[
                                    "confidence"
                                ]
                            else:
                                enhanced_signal["ai_validated"] = False
                                enhanced_signal["ai_confidence"] = direction_pred[
                                    "confidence"
                                ]

                enhanced_signals.append(enhanced_signal)

            return enhanced_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals: {e}")
            return base_signals

    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """執行交易信號（模擬）"""
        try:
            # 在真實系統中，這裡會連接到實際的交易API
            # 目前返回模擬執行結果

            execution_result = {
                "signal_id": signal.get("id", f"signal_{datetime.now().timestamp()}"),
                "symbol": signal.get("symbol"),
                "signal_type": signal.get("signal_type"),
                "executed": True,
                "execution_time": datetime.now(),
                "execution_price": signal.get("current_price", 0),
                "position_size": signal.get("position_size", 0),
                "ai_validated": signal.get("ai_validated", False),
                "ai_confidence": signal.get("ai_confidence", 0),
                "status": "completed",
            }

            self.logger.info(
                f"Executed signal: {signal.get('symbol')} {signal.get('signal_type')}"
            )
            return execution_result

        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            return {
                "signal_id": signal.get("id", f"signal_{datetime.now().timestamp()}"),
                "symbol": signal.get("symbol"),
                "signal_type": signal.get("signal_type"),
                "executed": False,
                "execution_time": datetime.now(),
                "error": str(e),
                "status": "failed",
            }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取Agent性能指標"""
        try:
            base_metrics = await super().get_performance_metrics()

            # 添加AI模型相關指標
            ai_metrics = {
                "models_trained": self.models_trained,
                "last_model_update": self.last_model_update,
                "available_models": (
                    list(self.ml_models.models.keys()) if self.ml_models.models else []
                ),
                "model_performance": self.ml_models.get_model_info(),
                "analysis_symbols": self.analysis_symbols,
                "lookback_days": self.lookback_days,
            }

            return {**base_metrics, **ai_metrics}

        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return await super().get_performance_metrics()

    async def cleanup(self) -> None:
        """清理資源"""
        try:
            self.logger.info("Cleaning up enhanced quantitative analyst...")

            # 清理數據服務
            if hasattr(self.data_service, "cleanup"):
                await self.data_service.cleanup()

            # 清理ML模型
            if hasattr(self.ml_models, "cleanup"):
                await self.ml_models.cleanup()

            await super().cleanup()

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
