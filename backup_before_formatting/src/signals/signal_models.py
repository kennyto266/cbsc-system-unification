"""
交易信號模型
定義所有交易信號的數據結構和類型
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np


class SignalType(Enum):
    """信號類型"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class SignalStrength(Enum):
    """信號強度"""

    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


class SignalSource(Enum):
    """信號來源"""

    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    QUANTITATIVE = "quantitative"
    ML = "machine_learning"
    HYBRID = "hybrid"


@dataclass
class TradingSignal:
    """
    交易信號基礎模型

    這是系統中所有交易信號的統一表示
    """

    # 基本信息
    symbol: str
    timestamp: datetime
    signal_type: SignalType
    strength: SignalStrength

    # 價格信息
    current_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

    # 信心度 (0 - 100)
    confidence: float = 0.0

    # 持有期間 (天)
    holding_period: Optional[int] = None

    # 信號來源
    source: Optional[SignalSource] = None

    # 理由和因素
    reasons: List[str] = None
    factors: Dict[str, float] = None

    # 風險指標
    risk_score: float = 0.0
    volatility: float = 0.0

    # 預期收益
    expected_return: Optional[float] = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []
        if self.factors is None:
            self.factors = {}

    @property
    def is_buy_signal(self) -> bool:
        """是否為買入信號"""
        return self.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]

    @property
    def is_sell_signal(self) -> bool:
        """是否為賣出信號"""
        return self.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]

    @property
    def is_strong_signal(self) -> bool:
        """是否為強信號"""
        return self.signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL]

    @property
    def signal_score(self) -> float:
        """信號綜合分數 (0 - 100)"""
        # 基礎分數
        base_score = self.strength.value * 20

        # 信心度權重
        confidence_score = self.confidence

        # 風險調整
        risk_adjustment = (5 - self.risk_score) * 5

        # 總分
        total = base_score + confidence_score + risk_adjustment

        # 限制在 0 - 100 範圍
        return max(0, min(100, total))

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "signal_type": self.signal_type.value,
            "strength": self.strength.name,
            "current_price": self.current_price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "confidence": self.confidence,
            "holding_period": self.holding_period,
            "source": self.source.value if self.source else None,
            "reasons": self.reasons,
            "factors": self.factors,
            "risk_score": self.risk_score,
            "volatility": self.volatility,
            "expected_return": self.expected_return,
            "signal_score": self.signal_score,
        }


@dataclass
class MultiFactorSignal:
    """
    多因子信號模型

    整合多個因子生成綜合信號
    """

    symbol: str
    timestamp: datetime

    # 各因子貢獻
    technical_score: float
    fundamental_score: float
    sentiment_score: float
    quantitative_score: float
    ml_score: float

    # 權重
    weights: Dict[str, float] = None

    # 最終信號
    final_signal: TradingSignal = None

    def __post_init__(self):
        if self.weights is None:
            self.weights = {
                "technical": 0.25,
                "fundamental": 0.20,
                "sentiment": 0.15,
                "quantitative": 0.25,
                "ml": 0.15,
            }

        # 計算加權綜合分數
        weighted_score = (
            self.weights["technical"] * self.technical_score
            + self.weights["fundamental"] * self.fundamental_score
            + self.weights["sentiment"] * self.sentiment_score
            + self.weights["quantitative"] * self.quantitative_score
            + self.weights["ml"] * self.ml_score
        )

        # 轉換為TradingSignal
        self.final_signal = self._score_to_signal(weighted_score, self.symbol)

    def _score_to_signal(self, score: float, symbol: str) -> TradingSignal:
        """將分數轉換為交易信號"""
        # 定義閾值
        strong_buy_threshold = 75
        buy_threshold = 60
        hold_lower = 40
        hold_upper = 60
        sell_threshold = 40
        strong_sell_threshold = 25

        if score >= strong_buy_threshold:
            signal_type = SignalType.STRONG_BUY
            strength = SignalStrength.VERY_STRONG
        elif score >= buy_threshold:
            signal_type = SignalType.BUY
            strength = SignalStrength.STRONG
        elif hold_lower <= score < hold_upper:
            signal_type = SignalType.HOLD
            strength = SignalStrength.MODERATE
        elif score >= sell_threshold:
            signal_type = SignalType.SELL
            strength = SignalStrength.WEAK
        else:
            signal_type = SignalType.STRONG_SELL
            strength = SignalStrength.VERY_STRONG

        return TradingSignal(
            symbol=symbol,
            timestamp=self.timestamp,
            signal_type=signal_type,
            strength=strength,
            current_price=0.0,  # 會在生成時設置
            confidence=min(100, max(0, abs(score - 50) * 2)),  # 距離50越遠信心越高
            source=SignalSource.HYBRID,
            factors={
                "technical": self.technical_score,
                "fundamental": self.fundamental_score,
                "sentiment": self.sentiment_score,
                "quantitative": self.quantitative_score,
                "ml": self.ml_score,
                "weighted_average": score,
            },
        )


@dataclass
class TechnicalSignal:
    """
    技術分析信號

    基於技術指標生成信號
    """

    symbol: str
    timestamp: datetime
    current_price: float

    # 技術指標值
    rsi: float
    macd: float
    macd_signal: float
    bb_position: float  # 布林帶位置 (0 - 1)
    sma_5: float
    sma_20: float
    sma_60: float
    atr: float
    stochastic_k: float
    stochastic_d: float
    adx: float

    # 生成的信號
    signal: TradingSignal = None

    def __post_init__(self):
        self.signal = self._generate_signal()

    def _generate_signal(self) -> TradingSignal:
        """生成技術分析信號"""
        score = 0
        reasons = []

        # RSI 分析
        if self.rsi < 30:
            score += 25
            reasons.append("RSI超賣 (< 30)")
        elif self.rsi > 70:
            score -= 25
            reasons.append("RSI超買 (> 70)")
        else:
            score += (50 - abs(self.rsi - 50)) / 2  # 接近50較中性

        # MACD 分析
        if self.macd > self.macd_signal:
            score += 20
            reasons.append("MACD金叉")
        else:
            score -= 20
            reasons.append("MACD死叉")

        # 布林帶分析
        if self.bb_position < 0.2:
            score += 20
            reasons.append("價格接近布林帶下軌")
        elif self.bb_position > 0.8:
            score -= 20
            reasons.append("價格接近布林帶上軌")
        else:
            score += (50 - abs(self.bb_position - 0.5) * 100) / 5

        # 移動平均線分析
        if self.current_price > self.sma_5 > self.sma_20 > self.sma_60:
            score += 15
            reasons.append("多頭排列")
        elif self.current_price < self.sma_5 < self.sma_20 < self.sma_60:
            score -= 15
            reasons.append("空頭排列")
        elif self.current_price > self.sma_20:
            score += 5
        else:
            score -= 5

        # 隨機指標分析
        if self.stochastic_k < 20:
            score += 10
            reasons.append("隨機指標超賣")
        elif self.stochastic_k > 80:
            score -= 10
            reasons.append("隨機指標超買")

        # ADX 分析 (趨勢強度)
        if self.adx > 25:
            if score > 0:
                score += 5  # 強趨勢強化買入
            elif score < 0:
                score -= 5  # 強趨勢強化賣出

        # 轉換為TradingSignal
        if score >= 60:
            signal_type = SignalType.BUY
            strength = SignalStrength.STRONG if score >= 80 else SignalStrength.MODERATE
        elif score >= 40:
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK if score < 45 else SignalStrength.MODERATE
        else:
            signal_type = SignalType.SELL
            strength = SignalStrength.STRONG if score <= 20 else SignalStrength.WEAK

        return TradingSignal(
            symbol=self.symbol,
            timestamp=self.timestamp,
            signal_type=signal_type,
            strength=strength,
            current_price=self.current_price,
            confidence=min(100, abs(score)),
            source=SignalSource.TECHNICAL,
            reasons=reasons,
            factors={
                "rsi": self.rsi,
                "macd": self.macd,
                "bb_position": self.bb_position,
                "adx": self.adx,
                "sma_ratio": self.current_price / self.sma_20,
                "technical_score": score,
            },
        )


@dataclass
class SentimentSignal:
    """
    情緒分析信號

    基於新聞、社交媒體情緒生成信號
    """

    symbol: str
    timestamp: datetime
    current_price: float

    # 情緒指標
    news_sentiment: float  # -100 (極度悲觀) 到 100 (極度樂觀)
    social_sentiment: float
    analyst_rating: float  # 1 - 5 星評級
    insider_activity: float  # 內部人交易活躍度
    short_interest: float  # 做空比例

    # 生成的信號
    signal: TradingSignal = None

    def __post_init__(self):
        self.signal = self._generate_signal()

    def _generate_signal(self) -> TradingSignal:
        """生成情緒分析信號"""
        score = 50  # 中性基準

        # 新聞情緒分析 (權重30%)
        if self.news_sentiment > 50:
            score += (self.news_sentiment - 50) * 0.3
        elif self.news_sentiment < -50:
            score += (self.news_sentiment + 50) * 0.3

        # 社交媒體情緒 (權重20%)
        if self.social_sentiment > 50:
            score += (self.social_sentiment - 50) * 0.2
        elif self.social_sentiment < -50:
            score += (self.social_sentiment + 50) * 0.2

        # 分析師評級 (權重30%)
        if self.analyst_rating >= 4:
            score += (self.analyst_rating - 3) * 15
        elif self.analyst_rating <= 2:
            score -= (3 - self.analyst_rating) * 15

        # 內部人活動 (權重10%)
        score += self.insider_activity * 10

        # 做空比例 (權重10%)
        if self.short_interest > 0.1:  # 做空比例超過10%
            score -= self.short_interest * 50

        # 限制範圍
        score = max(-100, min(100, score))

        # 轉換為TradingSignal
        if score >= 60:
            signal_type = SignalType.BUY
            strength = SignalStrength.STRONG if score >= 80 else SignalStrength.MODERATE
        elif score >= 40:
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK
        else:
            signal_type = SignalType.SELL
            strength = SignalStrength.STRONG if score <= 20 else SignalStrength.WEAK

        reasons = []
        if self.news_sentiment > 50:
            reasons.append("新聞情緒樂觀")
        if self.social_sentiment > 50:
            reasons.append("社交媒體情緒正面")
        if self.analyst_rating >= 4:
            reasons.append("分析師評級較高")
        if self.short_interest > 0.1:
            reasons.append(f"做空比例較高 ({self.short_interest:.1%})")

        return TradingSignal(
            symbol=self.symbol,
            timestamp=self.timestamp,
            signal_type=signal_type,
            strength=strength,
            current_price=self.current_price,
            confidence=min(100, abs(score)),
            source=SignalSource.SENTIMENT,
            reasons=reasons,
            factors={
                "news_sentiment": self.news_sentiment,
                "social_sentiment": self.social_sentiment,
                "analyst_rating": self.analyst_rating,
                "insider_activity": self.insider_activity,
                "short_interest": self.short_interest,
                "sentiment_score": score,
            },
        )
