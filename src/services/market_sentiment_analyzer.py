"""
Market Sentiment Analyzer Service
Analyzes market sentiment using CBBC data and generates trading insights
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from enum import Enum
import json
from collections import deque

logger = logging.getLogger(__name__)


class SentimentLevel(Enum):
    """Sentiment levels enumeration"""
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"


class MarketPhase(Enum):
    """Market phase enumeration"""
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"
    SIDEWAYS = "sideways"


class VolatilityRegime(Enum):
    """Volatility regime enumeration"""
    LOW = "low"
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"


@dataclass
class SentimentMetrics:
    """Container for sentiment metrics"""
    fear_greed_score: float  # 0-100 scale
    bull_bear_momentum: float
    volume_profile: Dict[str, float]
    volatility_trend: float
    support_resistance_levels: Dict[str, float]
    market_breadth: float


@dataclass
class TradingRecommendation:
    """Trading recommendation based on sentiment analysis"""
    action: str  # BUY, SELL, HOLD, CAUTION
    confidence: float  # 0-1 scale
    entry_zone: Optional[Tuple[float, float]]
    exit_zone: Optional[Tuple[float, float]]
    stop_loss: Optional[float]
    target_price: Optional[float]
    position_size: str  # SMALL, MEDIUM, LARGE
    holding_period: str  # SHORT, MEDIUM, LONG


class MarketSentimentAnalyzer:
    """Analyzes market sentiment using various indicators and patterns"""

    def __init__(self, lookback_window: int = 20, sentiment_history_size: int = 50):
        """
        Initialize Market Sentiment Analyzer

        Args:
            lookback_window: Number of periods for rolling calculations
            sentiment_history_size: Size of sentiment history to maintain
        """
        self.lookback_window = lookback_window
        self.sentiment_history = deque(maxlen=sentiment_history_size)
        self.sentiment_weights = {
            'bull_bear_ratio': 0.30,
            'fear_greed_index': 0.25,
            'rsi_signal': 0.20,
            'volume_trend': 0.15,
            'volatility': 0.10
        }

    def analyze_sentiment(self, data: pd.DataFrame) -> SentimentMetrics:
        """
        Analyze market sentiment from CBBC data

        Args:
            data: DataFrame with CBSC data

        Returns:
            SentimentMetrics: Current sentiment metrics
        """
        if data.empty:
            raise ValueError("Data cannot be empty")

        # Calculate Fear & Greed Score (0-100)
        fear_greed_score = self._calculate_fear_greed_score(data)

        # Calculate Bull/Bear Momentum
        bull_bear_momentum = self._calculate_momentum(data['Bull_Bear_Ratio'])

        # Analyze Volume Profile
        volume_profile = self._analyze_volume_profile(data)

        # Calculate Volatility Trend
        volatility_trend = self._calculate_volatility_trend(data['Realized_Volatility'])

        # Identify Support/Resistance Levels
        support_resistance = self._identify_support_resistance(data)

        # Calculate Market Breadth
        market_breadth = self._calculate_market_breadth(data)

        metrics = SentimentMetrics(
            fear_greed_score=fear_greed_score,
            bull_bear_momentum=bull_bear_momentum,
            volume_profile=volume_profile,
            volatility_trend=volatility_trend,
            support_resistance_levels=support_resistance,
            market_breadth=market_breadth
        )

        # Store in history
        self.sentiment_history.append({
            'timestamp': datetime.now(),
            'metrics': metrics
        })

        return metrics

    def get_current_sentiment_level(self, metrics: SentimentMetrics) -> SentimentLevel:
        """
        Determine current sentiment level

        Args:
            metrics: Current sentiment metrics

        Returns:
            SentimentLevel: Current sentiment level
        """
        score = metrics.fear_greed_score

        if score < 20:
            return SentimentLevel.EXTREME_FEAR
        elif score < 40:
            return SentimentLevel.FEAR
        elif score < 60:
            return SentimentLevel.NEUTRAL
        elif score < 80:
            return SentimentLevel.GREED
        else:
            return SentimentLevel.EXTREME_GREED

    def identify_market_phase(self, data: pd.DataFrame) -> MarketPhase:
        """
        Identify current market phase based on price and volume patterns

        Args:
            data: DataFrame with price and volume data

        Returns:
            MarketPhase: Current market phase
        """
        if len(data) < self.lookback_window:
            return MarketPhase.SIDEWAYS

        # Calculate moving averages
        short_ma = data['HSIF_Close'].rolling(10).mean()
        long_ma = data['HSIF_Close'].rolling(self.lookback_window).mean()

        # Get recent values
        current_price = data['HSIF_Close'].iloc[-1]
        current_short_ma = short_ma.iloc[-1]
        current_long_ma = long_ma.iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].rolling(self.lookback_window).mean().iloc[-1]

        # Determine phase based on moving averages
        if current_short_ma > current_long_ma:
            if current_price > current_short_ma:
                if current_volume > avg_volume * 1.2:
                    return MarketPhase.MARKUP
                else:
                    return MarketPhase.ACCUMULATION
            else:
                return MarketPhase.DISTRIBUTION
        else:
            if current_price < current_short_ma:
                if current_volume > avg_volume * 1.2:
                    return MarketPhase.MARKDOWN
                else:
                    return MarketPhase.SIDEWAYS
            else:
                return MarketPhase.SIDEWAYS

    def assess_volatility_regime(self, data: pd.DataFrame) -> VolatilityRegime:
        """
        Assess current volatility regime

        Args:
            data: DataFrame with volatility data

        Returns:
            VolatilityRegime: Current volatility regime
        """
        if 'Realized_Volatility' not in data.columns:
            return VolatilityRegime.NORMAL

        current_vol = data['Realized_Volatility'].iloc[-1]
        avg_vol = data['Realized_Volatility'].rolling(self.lookback_window).mean().iloc[-1]

        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1

        if vol_ratio < 0.8:
            return VolatilityRegime.LOW
        elif vol_ratio < 1.2:
            return VolatilityRegime.NORMAL
        elif vol_ratio < 1.5:
            return VolatilityRegime.ELEVATED
        else:
            return VolatilityRegime.HIGH

    def generate_trading_recommendation(self,
                                      data: pd.DataFrame,
                                      metrics: SentimentMetrics) -> TradingRecommendation:
        """
        Generate trading recommendation based on sentiment analysis

        Args:
            data: Market data
            metrics: Sentiment metrics

        Returns:
            TradingRecommendation: Trading recommendation
        """
        # Get current values
        current_price = data['HSIF_Close'].iloc[-1]
        support_level = metrics.support_resistance_levels['support']
        resistance_level = metrics.support_resistance_levels['resistance']
        sentiment_level = self.get_current_sentiment_level(metrics)
        market_phase = self.identify_market_phase(data)
        vol_regime = self.assess_volatility_regime(data)

        # Initialize recommendation
        recommendation = TradingRecommendation(
            action="HOLD",
            confidence=0.0,
            entry_zone=None,
            exit_zone=None,
            stop_loss=None,
            target_price=None,
            position_size="SMALL",
            holding_period="SHORT"
        )

        # Generate recommendation based on sentiment and market conditions
        if sentiment_level == SentimentLevel.EXTREME_FEAR:
            if market_phase in [MarketPhase.MARKDOWN, MarketPhase.SIDEWAYS]:
                recommendation.action = "BUY"
                recommendation.confidence = 0.7
                recommendation.position_size = "MEDIUM"
                recommendation.holding_period = "MEDIUM"
            else:
                recommendation.action = "CAUTION"
                recommendation.confidence = 0.8

        elif sentiment_level == SentimentLevel.FEAR:
            if market_phase == MarketPhase.ACCUMULATION:
                recommendation.action = "BUY"
                recommendation.confidence = 0.6
                recommendation.position_size = "SMALL"
            else:
                recommendation.action = "HOLD"

        elif sentiment_level == SentimentLevel.NEUTRAL:
            if market_phase == MarketPhase.MARKUP:
                recommendation.action = "BUY"
                recommendation.confidence = 0.5
                recommendation.position_size = "SMALL"
            elif market_phase == MarketPhase.MARKDOWN:
                recommendation.action = "SELL"
                recommendation.confidence = 0.5
            else:
                recommendation.action = "HOLD"

        elif sentiment_level == SentimentLevel.GREED:
            if market_phase == MarketPhase.DISTRIBUTION:
                recommendation.action = "SELL"
                recommendation.confidence = 0.6
                recommendation.position_size = "MEDIUM"
            else:
                recommendation.action = "CAUTION"
                recommendation.confidence = 0.7

        elif sentiment_level == SentimentLevel.EXTREME_GREED:
            if market_phase in [MarketPhase.MARKUP, MarketPhase.DISTRIBUTION]:
                recommendation.action = "SELL"
                recommendation.confidence = 0.8
                recommendation.position_size = "LARGE"
            else:
                recommendation.action = "CAUTION"
                recommendation.confidence = 0.9

        # Set entry/exit zones based on support/resistance
        if recommendation.action == "BUY":
            entry_range = current_price * 0.02  # 2% range
            recommendation.entry_zone = (current_price - entry_range, current_price + entry_range)
            recommendation.exit_zone = (resistance_level * 0.98, resistance_level)
            recommendation.stop_loss = support_level * 0.98
            recommendation.target_price = resistance_level

        elif recommendation.action == "SELL":
            entry_range = current_price * 0.02
            recommendation.entry_zone = (current_price - entry_range, current_price + entry_range)
            recommendation.exit_zone = (support_level, support_level * 1.02)
            recommendation.stop_loss = resistance_level * 1.02
            recommendation.target_price = support_level

        # Adjust confidence based on volatility
        if vol_regime == VolatilityRegime.HIGH:
            recommendation.confidence *= 0.7  # Reduce confidence in high volatility
        elif vol_regime == VolatilityRegime.LOW:
            recommendation.confidence *= 1.2  # Increase confidence in low volatility

        # Cap confidence at 0.95
        recommendation.confidence = min(0.95, recommendation.confidence)

        return recommendation

    def get_sentiment_summary(self, metrics: SentimentMetrics) -> Dict:
        """
        Get a summary of current sentiment analysis

        Args:
            metrics: Current sentiment metrics

        Returns:
            Dict: Sentiment summary
        """
        sentiment_level = self.get_current_sentiment_level(metrics)
        sentiment_strength = abs(metrics.fear_greed_score - 50) / 50

        return {
            'sentiment_level': sentiment_level.value,
            'sentiment_score': metrics.fear_greed_score,
            'sentiment_strength': sentiment_strength,
            'momentum_direction': 'bullish' if metrics.bull_bear_momentum > 0 else 'bearish',
            'volume_trend': 'increasing' if metrics.volume_profile['trend'] > 0 else 'decreasing',
            'key_support': metrics.support_resistance_levels['support'],
            'key_resistance': metrics.support_resistance_levels['resistance'],
            'market_breadth': metrics.market_breadth,
            'timestamp': datetime.now().isoformat()
        }

    # Private helper methods
    def _calculate_fear_greed_score(self, data: pd.DataFrame) -> float:
        """Calculate Fear & Greed Index score (0-100)"""
        # Combine multiple indicators into Fear & Greed score
        components = []

        # 1. Bull/Bear Ratio component
        if 'Bull_Bear_Ratio' in data.columns:
            ratio = data['Bull_Bear_Ratio'].iloc[-1]
            score = np.clip(50 + (np.log(ratio) * 20), 0, 100)
            components.append(score)

        # 2. Fear Greed Index component (if available)
        if 'Fear_Greed_Index' in data.columns and not pd.isna(data['Fear_Greed_Index'].iloc[-1]):
            components.append(data['Fear_Greed_Index'].iloc[-1])

        # 3. RSI component
        if 'RSI_Signal' in data.columns and not pd.isna(data['RSI_Signal'].iloc[-1]):
            rsi = data['RSI_Signal'].iloc[-1]
            rsi_score = np.clip(rsi, 0, 100)
            components.append(rsi_score)

        # Weighted average
        return np.mean(components) if components else 50

    def _calculate_momentum(self, series: pd.Series) -> float:
        """Calculate momentum indicator"""
        if len(series) < 2:
            return 0

        # Simple momentum calculation
        current = series.iloc[-1]
        past = series.iloc[-min(5, len(series))]

        return (current - past) / past if past > 0 else 0

    def _analyze_volume_profile(self, data: pd.DataFrame) -> Dict[str, float]:
        """Analyze volume profile"""
        if 'Volume' not in data.columns:
            return {'trend': 0, 'current': 0, 'average': 0}

        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].rolling(self.lookback_window).mean().iloc[-1]

        # Calculate trend
        volume_trend = (current_volume - avg_volume) / avg_volume if avg_volume > 0 else 0

        return {
            'trend': volume_trend,
            'current': current_volume,
            'average': avg_volume,
            'ratio': current_volume / avg_volume if avg_volume > 0 else 1
        }

    def _calculate_volatility_trend(self, series: pd.Series) -> float:
        """Calculate volatility trend"""
        if len(series) < self.lookback_window:
            return 0

        recent_vol = series.iloc[-1]
        avg_vol = series.rolling(self.lookback_window).mean().iloc[-1]

        return (recent_vol - avg_vol) / avg_vol if avg_vol > 0 else 0

    def _identify_support_resistance(self, data: pd.DataFrame) -> Dict[str, float]:
        """Identify key support and resistance levels"""
        if len(data) < 20:
            return {'support': 0, 'resistance': 0}

        # Use recent highs and lows
        recent_data = data.tail(20)

        resistance = recent_data['HSIF_Close'].max()
        support = recent_data['HSIF_Close'].min()

        # Adjust with moving averages
        ma = data['HSIF_Close'].rolling(self.lookback_window).mean().iloc[-1]

        support = min(support, ma)
        resistance = max(resistance, ma)

        return {
            'support': support,
            'resistance': resistance
        }

    def _calculate_market_breadth(self, data: pd.DataFrame) -> float:
        """Calculate market breadth indicator"""
        # Simplified market breadth based on price action
        if len(data) < self.lookback_window:
            return 0

        price_changes = data['HSIF_Close'].pct_change().tail(self.lookback_window)
        up_days = (price_changes > 0).sum()
        total_days = len(price_changes)

        return up_days / total_days if total_days > 0 else 0.5


# Factory function
def create_sentiment_analyzer(lookback_window: int = 20) -> MarketSentimentAnalyzer:
    """Create and return MarketSentimentAnalyzer instance"""
    return MarketSentimentAnalyzer(lookback_window=lookback_window)


# Singleton instance
_sentiment_analyzer_instance: Optional[MarketSentimentAnalyzer] = None


def get_sentiment_analyzer() -> MarketSentimentAnalyzer:
    """Get singleton MarketSentimentAnalyzer instance"""
    global _sentiment_analyzer_instance
    if _sentiment_analyzer_instance is None:
        _sentiment_analyzer_instance = MarketSentimentAnalyzer()
    return _sentiment_analyzer_instance