"""
智能交易信號生成器
整合多種分析方法生成綜合交易信號
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..data_adapters.base_adapter import BaseAdapter
from ..ml.prediction_engine import MLPredictionEngine, ModelType, PredictionHorizon
from .signal_combiner import SignalCombiner
from .signal_models import (
    MultiFactorSignal,
    SentimentSignal,
    SignalSource,
    SignalStrength,
    SignalType,
    TechnicalSignal,
    TradingSignal,
)


class IntelligentSignalGenerator:
    """
    智能交易信號生成器

    功能:
    - 多因子信號分析 (技術 + 基本面 + 情緒 + 量化 + 機器學習)
    - 動態權重調整
    - 實時信號生成
    - 批量信號處理
    """

    def __init__(
        self,
        data_adapter: BaseAdapter,
        ml_engine: Optional[MLPredictionEngine] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.data_adapter = data_adapter
        self.ml_engine = ml_engine
        self.config = config or self._default_config()
        self.logger = logging.getLogger("hk_quant_system.signal_generator")

        # 信號組合器
        self.signal_combiner = SignalCombiner(self.config.get("combiner_config"))

        # 技術分析工具
        self.technical_analyzer = TechnicalAnalyzer()

        # 情緒分析工具
        self.sentiment_analyzer = SentimentAnalyzer()

        # 量化分析工具
        self.quant_analyzer = QuantitativeAnalyzer()

        # 信號緩存
        self._signal_cache: Dict[str, TradingSignal] = {}
        self._cache_expiry = 300  # 5分鐘

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "signal_generation": {
                "enabled_sources": [
                    SignalSource.TECHNICAL,
                    SignalSource.FUNDAMENTAL,
                    SignalSource.SENTIMENT,
                    SignalSource.QUANTITATIVE,
                    SignalSource.ML,
                ],
                "min_confidence": 50.0,
                "signal_freshness_hours": 1,
            },
            "technical_analysis": {
                "indicators": [
                    "rsi",
                    "macd",
                    "bb",
                    "sma",
                    "ema",
                    "atr",
                    "stochastic",
                    "adx",
                    "obv",
                    "mfi",
                ],
                "timeframes": ["1d", "1h"],
                "lookback_period": 60,
            },
            "combiner_config": {
                "weights": {
                    SignalSource.TECHNICAL: 0.25,
                    SignalSource.FUNDAMENTAL: 0.20,
                    SignalSource.SENTIMENT: 0.15,
                    SignalSource.QUANTITATIVE: 0.25,
                    SignalSource.ML: 0.15,
                },
                "consensus_threshold": 0.6,
                "volatility_adjustment": True,
            },
        }

    async def generate_signal(
        self, symbol: str, use_cache: bool = True
    ) -> TradingSignal:
        """
        生成綜合交易信號

        Args:
            symbol: 股票代碼 (例如: "0700.hk")
            use_cache: 是否使用緩存

        Returns:
            綜合交易信號
        """
        cache_key = f"{symbol}_signal"

        # 檢查緩存
        if use_cache and cache_key in self._signal_cache:
            cached_signal = self._signal_cache[cache_key]
            if self._is_cache_valid(cached_signal):
                self.logger.info(f"返回緩存的信號: {symbol}")
                return cached_signal

        self.logger.info(f"開始生成信號: {symbol}")

        try:
            # 獲取當前價格
            current_price = await self._get_current_price(symbol)

            # 獲取市場數據
            market_data = await self._get_market_data(symbol)

            # 生成各類信號
            signals = await self._generate_all_signals(
                symbol, current_price, market_data
            )

            # 過濾啟用的信號源
            enabled_sources = self.config["signal_generation"]["enabled_sources"]
            filtered_signals = [
                s
                for s in signals
                if s and (not s.source or s.source in enabled_sources)
            ]

            if not filtered_signals:
                self.logger.warning(f"沒有生成有效信號: {symbol}")
                return self._create_default_signal(symbol, current_price)

            # 組合信號
            final_signal = self.signal_combiner.combine_signals(
                symbol, filtered_signals, current_price
            )

            # 緩存結果
            self._signal_cache[cache_key] = final_signal

            self.logger.info(
                f"信號生成完成: {symbol} = {final_signal.signal_type.value}, "
                f"strength={final_signal.strength.name}, "
                f"confidence={final_signal.confidence:.1f}"
            )

            return final_signal

        except Exception as e:
            self.logger.error(f"信號生成失敗: {symbol}, error={str(e)}")
            # 返回默認信號
            current_price = await self._get_current_price(symbol)
            return self._create_default_signal(symbol, current_price)

    async def generate_signals(
        self, symbols: List[str], use_cache: bool = True
    ) -> Dict[str, TradingSignal]:
        """
        批量生成交易信號

        Args:
            symbols: 股票代碼列表
            use_cache: 是否使用緩存

        Returns:
            信號字典
        """
        self.logger.info(f"開始批量生成信號: {len(symbols)} 個股票")

        # 為每個股票生成信號
        tasks = []
        for symbol in symbols:
            task = self.generate_signal(symbol, use_cache)
            tasks.append((symbol, task))

        # 並行執行
        results = {}
        for symbol, task in tasks:
            try:
                signal = await task
                results[symbol] = signal
            except Exception as e:
                self.logger.error(f"批量信號生成失敗 {symbol}: {str(e)}")
                results[symbol] = None

        success_count = sum(1 for s in results.values() if s is not None)
        self.logger.info(f"批量信號生成完成: 成功 {success_count}/{len(symbols)}")

        return results

    async def _generate_all_signals(
        self, symbol: str, current_price: float, market_data: Dict[str, Any]
    ) -> List[Optional[TradingSignal]]:
        """生成所有類型的信號"""
        signals = []

        # 1. 技術分析信號
        if (
            SignalSource.TECHNICAL
            in self.config["signal_generation"]["enabled_sources"]
        ):
            technical_signal = await self._generate_technical_signal(
                symbol, current_price, market_data
            )
            signals.append(technical_signal)

        # 2. 情緒分析信號
        if (
            SignalSource.SENTIMENT
            in self.config["signal_generation"]["enabled_sources"]
        ):
            sentiment_signal = await self._generate_sentiment_signal(
                symbol, current_price, market_data
            )
            signals.append(sentiment_signal)

        # 3. 量化分析信號
        if (
            SignalSource.QUANTITATIVE
            in self.config["signal_generation"]["enabled_sources"]
        ):
            quant_signal = await self._generate_quantitative_signal(
                symbol, current_price, market_data
            )
            signals.append(quant_signal)

        # 4. 機器學習信號
        if SignalSource.ML in self.config["signal_generation"]["enabled_sources"]:
            ml_signal = await self._generate_ml_signal(
                symbol, current_price, market_data
            )
            signals.append(ml_signal)

        # 5. 基本面分析信號
        if (
            SignalSource.FUNDAMENTAL
            in self.config["signal_generation"]["enabled_sources"]
        ):
            fundamental_signal = await self._generate_fundamental_signal(
                symbol, current_price, market_data
            )
            signals.append(fundamental_signal)

        return signals

    async def _generate_technical_signal(
        self, symbol: str, current_price: float, market_data: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """生成技術分析信號"""
        try:
            # 獲取歷史數據
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

            data = await self.data_adapter.fetch_data(symbol, start_date, end_date)
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            if len(df) < 30:
                self.logger.warning(f"歷史數據不足: {symbol}, 數據點: {len(df)}")
                return None

            # 計算技術指標
            indicators = self.technical_analyzer.calculate_indicators(df)

            # 生成技術信號
            tech_signal = TechnicalSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                current_price=current_price,
                rsi=indicators.get("rsi", 50),
                macd=indicators.get("macd", 0),
                macd_signal=indicators.get("macd_signal", 0),
                bb_position=indicators.get("bb_position", 0.5),
                sma_5=indicators.get("sma_5", current_price),
                sma_20=indicators.get("sma_20", current_price),
                sma_60=indicators.get("sma_60", current_price),
                atr=indicators.get("atr", 0),
                stochastic_k=indicators.get("stochastic_k", 50),
                stochastic_d=indicators.get("stochastic_d", 50),
                adx=indicators.get("adx", 25),
            )

            return tech_signal.signal

        except Exception as e:
            self.logger.error(f"技術分析信號生成失敗: {str(e)}")
            return None

    async def _generate_sentiment_signal(
        self, symbol: str, current_price: float, market_data: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """生成情緒分析信號"""
        try:
            # 模擬情緒數據 (實際中會從新聞API、社交媒體API獲取)
            sentiment_data = await self._get_sentiment_data(symbol)

            # 生成情緒信號
            sentiment_signal = SentimentSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                current_price=current_price,
                news_sentiment=sentiment_data["news_sentiment"],
                social_sentiment=sentiment_data["social_sentiment"],
                analyst_rating=sentiment_data["analyst_rating"],
                insider_activity=sentiment_data["insider_activity"],
                short_interest=sentiment_data["short_interest"],
            )

            return sentiment_signal.signal

        except Exception as e:
            self.logger.error(f"情緒分析信號生成失敗: {str(e)}")
            return None

    async def _generate_quantitative_signal(
        self, symbol: str, current_price: float, market_data: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """生成量化分析信號"""
        try:
            # 獲取歷史數據
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

            data = await self.data_adapter.fetch_data(symbol, start_date, end_date)
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            if len(df) < 30:
                return None

            # 量化分析
            quant_metrics = self.quant_analyzer.analyze(df)

            # 生成量化信號
            quant_signal = TradingSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                signal_type=quant_metrics["signal_type"],
                strength=quant_metrics["strength"],
                current_price=current_price,
                confidence=quant_metrics["confidence"],
                source=SignalSource.QUANTITATIVE,
                reasons=quant_metrics["reasons"],
                factors=quant_metrics["factors"],
                risk_score=quant_metrics["risk_score"],
                volatility=quant_metrics["volatility"],
                expected_return=quant_metrics["expected_return"],
            )

            return quant_signal

        except Exception as e:
            self.logger.error(f"量化分析信號生成失敗: {str(e)}")
            return None

    async def _generate_ml_signal(
        self, symbol: str, current_price: float, market_data: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """生成機器學習信號"""
        try:
            if not self.ml_engine:
                self.logger.warning("機器學習引擎未初始化，跳過ML信號")
                return None

            # 使用ML引擎進行預測
            prediction = await self.ml_engine.predict_price(
                symbol=symbol,
                model_type=ModelType.HYBRID,
                horizon=PredictionHorizon.SHORT_TERM,
                days_ahead=5,
            )

            if not prediction:
                return None

            # 將預測轉換為信號
            if prediction.confidence > 0.6:
                if prediction.trend_direction == "up":
                    signal_type = SignalType.BUY
                    strength = (
                        SignalStrength.STRONG
                        if prediction.confidence > 0.8
                        else SignalStrength.MODERATE
                    )
                else:
                    signal_type = SignalType.SELL
                    strength = (
                        SignalStrength.STRONG
                        if prediction.confidence > 0.8
                        else SignalStrength.MODERATE
                    )
            else:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK

            # 計算預期收益
            current_return = (
                prediction.predicted_price - current_price
            ) / current_price
            expected_return = current_return * (prediction.confidence / 100)

            ml_signal = TradingSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                signal_type=signal_type,
                strength=strength,
                current_price=current_price,
                target_price=prediction.predicted_price,
                confidence=prediction.confidence * 100,
                source=SignalSource.ML,
                reasons=[
                    f"ML預測趨勢: {prediction.trend_direction}",
                    f"預測價格: {prediction.predicted_price:.2f}",
                    f"模型: {prediction.model_used}",
                ],
                factors={
                    "ml_confidence": prediction.confidence,
                    "ml_predicted_price": prediction.predicted_price,
                    "ml_volatility": prediction.volatility,
                    "ml_trend": prediction.trend_direction,
                },
                risk_score=(
                    3
                    if prediction.risk_level == "high"
                    else 2 if prediction.risk_level == "medium" else 1
                ),
                volatility=prediction.volatility,
                expected_return=expected_return,
            )

            return ml_signal

        except Exception as e:
            self.logger.error(f"機器學習信號生成失敗: {str(e)}")
            return None

    async def _generate_fundamental_signal(
        self, symbol: str, current_price: float, market_data: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """生成基本面分析信號"""
        try:
            # 獲取基本面數據 (模擬)
            fundamental_data = await self._get_fundamental_data(symbol)

            # 簡化的基本面分析
            pe_ratio = fundamental_data["pe_ratio"]
            pb_ratio = fundamental_data["pb_ratio"]
            debt_to_equity = fundamental_data["debt_to_equity"]
            roe = fundamental_data["roe"]
            revenue_growth = fundamental_data["revenue_growth"]

            # 計算基本面分數
            score = 50  # 基準分

            # PE比率分析
            if pe_ratio < 15:
                score += 15  # 低估值
            elif pe_ratio > 30:
                score -= 15  # 高估值

            # PB比率分析
            if pb_ratio < 1:
                score += 10  # 帳面價值折價
            elif pb_ratio > 3:
                score -= 10

            # ROE分析
            score += min(20, max(-20, (roe - 10) * 2))

            # 債務比率分析
            if debt_to_equity < 0.3:
                score += 10  # 低負債
            elif debt_to_equity > 1:
                score -= 15  # 高負債

            # 收入增長分析
            score += min(15, max(-15, revenue_growth * 10))

            # 轉換為信號
            if score >= 65:
                signal_type = SignalType.BUY
                strength = (
                    SignalStrength.STRONG if score >= 80 else SignalStrength.MODERATE
                )
            elif score >= 45:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
            else:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG if score <= 35 else SignalStrength.WEAK

            reasons = []
            if pe_ratio < 15:
                reasons.append(f"PE比率較低 ({pe_ratio:.1f})")
            if pb_ratio < 1:
                reasons.append(f"PB比率較低 ({pb_ratio:.1f})")
            if roe > 15:
                reasons.append(f"ROE較高 ({roe:.1f}%)")
            if debt_to_equity < 0.3:
                reasons.append("債務比率健康")

            fundamental_signal = TradingSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                signal_type=signal_type,
                strength=strength,
                current_price=current_price,
                confidence=min(100, abs(score - 50) * 2),
                source=SignalSource.FUNDAMENTAL,
                reasons=reasons,
                factors={
                    "pe_ratio": pe_ratio,
                    "pb_ratio": pb_ratio,
                    "debt_to_equity": debt_to_equity,
                    "roe": roe,
                    "revenue_growth": revenue_growth,
                    "fundamental_score": score,
                },
                risk_score=(
                    3 if debt_to_equity > 0.8 else 2 if debt_to_equity > 0.5 else 1
                ),
            )

            return fundamental_signal

        except Exception as e:
            self.logger.error(f"基本面分析信號生成失敗: {str(e)}")
            return None

    async def _get_current_price(self, symbol: str) -> float:
        """獲取當前價格"""
        try:
            # 獲取最新數據
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = datetime.now().strftime("%Y-%m-%d")

            data = await self.data_adapter.fetch_data(symbol, start_date, end_date)
            if data and len(data) > 0:
                return float(data[-1]["close"])
            else:
                # 如果沒有數據，返回模擬價格
                return 100.0
        except Exception as e:
            self.logger.error(f"獲取當前價格失敗: {symbol}, {str(e)}")
            return 100.0

    async def _get_market_data(self, symbol: str) -> Dict[str, Any]:
        """獲取市場數據"""
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            data = await self.data_adapter.fetch_data(symbol, start_date, end_date)
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            return {
                "dataframe": df,
                "latest": df.iloc[-1].to_dict() if len(df) > 0 else {},
                "volatility": (
                    df["close"].pct_change().std() * np.sqrt(252)
                    if len(df) > 1
                    else 0.2
                ),
            }
        except Exception as e:
            self.logger.error(f"獲取市場數據失敗: {symbol}, {str(e)}")
            return {"dataframe": pd.DataFrame(), "latest": {}, "volatility": 0.2}

    async def _get_sentiment_data(self, symbol: str) -> Dict[str, float]:
        """獲取情緒數據 (模擬)"""
        # 實際實現中，這裡會從新聞API、社交媒體API獲取真實數據
        # 現在返回模擬數據
        import random

        random.seed(hash(symbol) % 1000)

        return {
            "news_sentiment": random.uniform(-50, 50),
            "social_sentiment": random.uniform(-50, 50),
            "analyst_rating": random.uniform(2.5, 4.5),
            "insider_activity": random.uniform(-0.5, 0.5),
            "short_interest": random.uniform(0.02, 0.15),
        }

    async def _get_fundamental_data(self, symbol: str) -> Dict[str, float]:
        """獲取基本面數據 (模擬)"""
        # 實際實現中，這裡會從財務數據API獲取真實數據
        import random

        random.seed(hash(symbol) % 1000)

        return {
            "pe_ratio": random.uniform(8, 40),
            "pb_ratio": random.uniform(0.5, 5),
            "debt_to_equity": random.uniform(0.1, 1.2),
            "roe": random.uniform(5, 25),
            "revenue_growth": random.uniform(-0.2, 0.4),
        }

    def _is_cache_valid(self, signal: TradingSignal) -> bool:
        """檢查緩存是否有效"""
        expiry_hours = self.config["signal_generation"]["signal_freshness_hours"]
        age_hours = (datetime.now() - signal.timestamp).total_seconds() / 3600
        return age_hours < expiry_hours

    def _create_default_signal(
        self, symbol: str, current_price: float
    ) -> TradingSignal:
        """創建默認信號"""
        return TradingSignal(
            symbol=symbol,
            timestamp=datetime.now(),
            signal_type=SignalType.HOLD,
            strength=SignalStrength.WEAK,
            current_price=current_price,
            confidence=0,
            source=None,
            reasons=["數據不足或分析失敗"],
            factors={},
            risk_score=3,
        )

    def clear_cache(self):
        """清除信號緩存"""
        self._signal_cache.clear()
        self.signal_combiner.clear_history()
        self.logger.info("信號緩存已清除")


class TechnicalAnalyzer:
    """技術分析工具"""

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """計算技術指標"""
        indicators = {}

        try:
            # RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            indicators["rsi"] = 100 - (100 / (1 + rs)).iloc[-1]

            # MACD
            ema_12 = df["close"].ewm(span=12).mean()
            ema_26 = df["close"].ewm(span=26).mean()
            macd = ema_12 - ema_26
            indicators["macd"] = macd.iloc[-1]
            indicators["macd_signal"] = macd.ewm(span=9).mean().iloc[-1]

            # 布林帶
            bb_middle = df["close"].rolling(20).mean()
            bb_std = df["close"].rolling(20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            current_price = df["close"].iloc[-1]
            if bb_upper.iloc[-1] != bb_lower.iloc[-1]:
                indicators["bb_position"] = (current_price - bb_lower.iloc[-1]) / (
                    bb_upper.iloc[-1] - bb_lower.iloc[-1]
                )
            else:
                indicators["bb_position"] = 0.5

            # 移動平均線
            indicators["sma_5"] = df["close"].rolling(5).mean().iloc[-1]
            indicators["sma_20"] = df["close"].rolling(20).mean().iloc[-1]
            indicators["sma_60"] = df["close"].rolling(60).mean().iloc[-1]

            # ATR
            high_low = df["high"] - df["low"]
            high_close = np.abs(df["high"] - df["close"].shift())
            low_close = np.abs(df["low"] - df["close"].shift())
            ranges = np.maximum(high_low, np.maximum(high_close, low_close))
            indicators["atr"] = ranges.rolling(14).mean().iloc[-1]

            # 隨機指標
            low_14 = df["low"].rolling(14).min()
            high_14 = df["high"].rolling(14).max()
            k_percent = 100 * ((df["close"] - low_14) / (high_14 - low_14))
            indicators["stochastic_k"] = k_percent.iloc[-1]
            indicators["stochastic_d"] = k_percent.rolling(3).mean().iloc[-1]

            # ADX (簡化)
            indicators["adx"] = 25.0

        except Exception as e:
            self.logger.error(f"技術指標計算失敗: {str(e)}")
            # 返回默認值
            return {
                "rsi": 50.0,
                "macd": 0.0,
                "macd_signal": 0.0,
                "bb_position": 0.5,
                "sma_5": df["close"].iloc[-1],
                "sma_20": df["close"].iloc[-1],
                "sma_60": df["close"].iloc[-1],
                "atr": df["close"].iloc[-1] * 0.02,
                "stochastic_k": 50.0,
                "stochastic_d": 50.0,
                "adx": 25.0,
            }

        return indicators


class SentimentAnalyzer:
    """情緒分析工具"""

    def analyze_sentiment(
        self, news_data: List[Dict], social_data: List[Dict]
    ) -> Dict[str, float]:
        """分析情緒"""
        # 簡化實現
        return {"overall_sentiment": 0.0, "confidence": 0.7}


class QuantitativeAnalyzer:
    """量化分析工具"""

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """量化分析"""
        try:
            # 計算收益率
            returns = df["close"].pct_change().dropna()

            # 計算波動率
            volatility = returns.std() * np.sqrt(252)

            # 計算夏普比率 (假設無風險利率為2%)
            mean_return = returns.mean() * 252
            risk_free_rate = 0.02
            sharpe_ratio = (
                (mean_return - risk_free_rate) / volatility if volatility > 0 else 0
            )

            # 計算最大回撤
            cumulative_returns = (1 + returns).cumprod()
            peak = cumulative_returns.cummax()
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = drawdown.min()

            # 簡化的交易信號
            score = 50

            # 趨勢分析
            if len(df) >= 20:
                ma_short = df["close"].rolling(5).mean().iloc[-1]
                ma_long = df["close"].rolling(20).mean().iloc[-1]

                if ma_short > ma_long:
                    score += 20
                else:
                    score -= 20

            # 動量分析
            if returns.iloc[-1] > 0:
                score += 10
            else:
                score -= 10

            # 波動率調整
            if volatility > 0.3:  # 高波動率
                score -= 10

            # 轉換為信號
            if score >= 65:
                signal_type = SignalType.BUY
                strength = (
                    SignalStrength.STRONG if score >= 80 else SignalStrength.MODERATE
                )
            elif score >= 45:
                signal_type = SignalType.HOLD
                strength = SignalStrength.WEAK
            else:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG if score <= 35 else SignalStrength.WEAK

            reasons = []
            if ma_short > ma_long:
                reasons.append("短期均線高於長期均線")
            if returns.iloc[-1] > 0:
                reasons.append("近期上漲動量")
            if volatility < 0.2:
                reasons.append("低波動率")

            return {
                "signal_type": signal_type,
                "strength": strength,
                "confidence": min(100, abs(score - 50) * 2),
                "reasons": reasons,
                "factors": {
                    "volatility": volatility,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": max_drawdown,
                    "quant_score": score,
                },
                "risk_score": 3 if volatility > 0.3 else 2 if volatility > 0.2 else 1,
                "volatility": volatility,
                "expected_return": mean_return * 0.5,  # 保守估計
            }

        except Exception as e:
            self.logger.error(f"量化分析失敗: {str(e)}")
            return {
                "signal_type": SignalType.HOLD,
                "strength": SignalStrength.WEAK,
                "confidence": 0,
                "reasons": ["量化分析失敗"],
                "factors": {},
                "risk_score": 3,
                "volatility": 0.2,
                "expected_return": 0,
            }
