"""
CBSC (Callable Bull/Bear Contracts) Data Reader Service
Integrates HKEX CBBC data into the CBSC quantitative trading system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CBBCCandle:
    """Represents a single CBBC data point"""
    timestamp: datetime
    bull_price: float
    bear_price: float
    bull_bear_ratio: float
    fear_greed_index: Optional[float]
    rsi_signal: Optional[float]
    realized_volatility: Optional[float]
    volume: Optional[float]


@dataclass
class MarketSentiment:
    """Market sentiment indicators derived from CBBC data"""
    sentiment_score: float  # -1 (extreme fear) to 1 (extreme greed)
    momentum_indicator: float
    volatility_regime: str  # low, medium, high
    market_phase: str  # accumulation, distribution, trending
    confidence_level: float


class CBBCDataReader:
    """CBSC Data Reader for processing and analyzing CBBC market data"""

    def __init__(self, data_path: str = None):
        """
        Initialize CBBC Data Reader

        Args:
            data_path: Path to the CBSC CSV data file
        """
        self.data_path = data_path or "acquired_data/cbsc_real_data_20251205_205342.csv"
        self._data: Optional[pd.DataFrame] = None
        self._processed_data: Optional[pd.DataFrame] = None

    async def load_data(self) -> bool:
        """
        Load CBSC data from CSV file

        Returns:
            bool: True if data loaded successfully
        """
        try:
            # Check if file exists
            if not Path(self.data_path).exists():
                logger.error(f"Data file not found: {self.data_path}")
                return False

            # Load CSV data
            self._data = pd.read_csv(self.data_path)

            # Convert date column
            self._data['Date'] = pd.to_datetime(self._data['Date'])
            self._data.set_index('Date', inplace=True)

            # Sort by date
            self._data.sort_index(inplace=True)

            logger.info(f"Loaded {len(self._data)} records from {self.data_path}")
            logger.info(f"Date range: {self._data.index[0]} to {self._data.index[-1]}")

            return True

        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            return False

    def preprocess_data(self) -> None:
        """Preprocess the loaded data for analysis"""
        if self._data is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        # Create a copy for processing
        self._processed_data = self._data.copy()

        # Fill missing values
        numeric_columns = self._processed_data.select_dtypes(include=[np.number]).columns
        self._processed_data[numeric_columns] = self._processed_data[numeric_columns].fillna(method='ffill')

        # Calculate additional indicators
        self._processed_data['Price_Change'] = self._processed_data['HSIF_Close'].pct_change()

        # Calculate rolling statistics
        window = 20
        self._processed_data['Rolling_Mean'] = self._processed_data['HSIF_Close'].rolling(window=window).mean()
        self._processed_data['Rolling_Std'] = self._processed_data['HSIF_Close'].rolling(window=window).std()

        # Calculate Bollinger Bands
        self._processed_data['BB_Upper'] = self._processed_data['Rolling_Mean'] + (self._processed_data['Rolling_Std'] * 2)
        self._processed_data['BB_Lower'] = self._processed_data['Rolling_Mean'] - (self._processed_data['Rolling_Std'] * 2)

        logger.info("Data preprocessing completed")

    def calculate_market_sentiment(self, lookback_days: int = 5) -> MarketSentiment:
        """
        Calculate market sentiment indicators

        Args:
            lookback_days: Number of days to look back for sentiment analysis

        Returns:
            MarketSentiment: Current market sentiment indicators
        """
        if self._processed_data is None:
            raise ValueError("Data not processed. Call preprocess_data() first.")

        # Get recent data
        recent_data = self._processed_data.tail(lookback_days)

        # Calculate sentiment score based on Bull/Bear ratio
        # Higher ratio = more bullish sentiment
        avg_bull_bear_ratio = recent_data['Bull_Bear_Ratio'].mean()
        sentiment_score = np.clip(np.log(avg_bull_bear_ratio) / 10, -1, 1)

        # Calculate momentum
        price_momentum = recent_data['Price_Change'].mean()
        momentum_indicator = np.clip(price_momentum * 10, -1, 1)

        # Determine volatility regime
        avg_volatility = recent_data['Realized_Volatility'].fillna(0).mean()
        if avg_volatility < 0.15:
            volatility_regime = "low"
        elif avg_volatility < 0.3:
            volatility_regime = "medium"
        else:
            volatility_regime = "high"

        # Determine market phase based on price and Bollinger Bands
        current_price = recent_data['HSIF_Close'].iloc[-1]
        bb_upper = recent_data['BB_Upper'].iloc[-1]
        bb_lower = recent_data['BB_Lower'].iloc[-1]
        rolling_mean = recent_data['Rolling_Mean'].iloc[-1]

        if current_price > bb_upper:
            market_phase = "overbought"
        elif current_price < bb_lower:
            market_phase = "oversold"
        elif current_price > rolling_mean:
            market_phase = "uptrend"
        else:
            market_phase = "downtrend"

        # Calculate confidence level based on data consistency
        confidence_level = min(0.95, len(recent_data) / lookback_days)

        return MarketSentiment(
            sentiment_score=sentiment_score,
            momentum_indicator=momentum_indicator,
            volatility_regime=volatility_regime,
            market_phase=market_phase,
            confidence_level=confidence_level
        )

    def get_trading_signals(self) -> Dict[str, str]:
        """
        Generate trading signals based on CBBC data

        Returns:
            Dict containing trading signals
        """
        if self._processed_data is None:
            raise ValueError("Data not processed. Call preprocess_data() first.")

        # Get current sentiment
        sentiment = self.calculate_market_sentiment()

        # Get latest data point
        latest = self._processed_data.iloc[-1]

        signals = {}

        # Bull/Bear ratio signal
        if latest['Bull_Bear_Ratio'] > 1.5:
            signals['bull_bear_signal'] = "STRONG_BULLISH"
        elif latest['Bull_Bear_Ratio'] > 1.0:
            signals['bull_bear_signal'] = "BULLISH"
        elif latest['Bull_Bear_Ratio'] > 0.7:
            signals['bull_bear_signal'] = "NEUTRAL"
        else:
            signals['bull_bear_signal'] = "BEARISH"

        # RSI signal
        if latest['RSI_Signal'] and not pd.isna(latest['RSI_Signal']):
            if latest['RSI_Signal'] > 70:
                signals['rsi_signal'] = "OVERBOUGHT"
            elif latest['RSI_Signal'] < 30:
                signals['rsi_signal'] = "OVERSOLD"
            else:
                signals['rsi_signal'] = "NEUTRAL"
        else:
            signals['rsi_signal'] = "NO_DATA"

        # Volatility signal
        if latest['Realized_Volatility'] and not pd.isna(latest['Realized_Volatility']):
            if latest['Realized_Volatility'] > 0.3:
                signals['volatility_signal'] = "HIGH_VOLATILITY"
            elif latest['Realized_Volatility'] > 0.15:
                signals['volatility_signal'] = "MEDIUM_VOLATILITY"
            else:
                signals['volatility_signal'] = "LOW_VOLATILITY"
        else:
            signals['volatility_signal'] = "NO_DATA"

        # Overall recommendation
        sentiment_strength = abs(sentiment.sentiment_score)
        if sentiment.sentiment_score > 0.5 and sentiment_strength > 0.3:
            signals['overall_signal'] = "BUY"
        elif sentiment.sentiment_score < -0.5 and sentiment_strength > 0.3:
            signals['overall_signal'] = "SELL"
        else:
            signals['overall_signal'] = "HOLD"

        return signals

    def get_risk_metrics(self) -> Dict[str, float]:
        """
        Calculate risk metrics based on CBBC data

        Returns:
            Dict containing risk metrics
        """
        if self._processed_data is None:
            raise ValueError("Data not processed. Call preprocess_data() first.")

        # Calculate volatility metrics
        returns = self._processed_data['HSIF_Return'].dropna()

        # Annualized volatility
        annualized_vol = returns.std() * np.sqrt(252)

        # Maximum drawdown
        rolling_max = self._processed_data['HSIF_Close'].expanding().max()
        drawdown = (self._processed_data['HSIF_Close'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # Sharpe ratio (assuming risk-free rate of 2%)
        sharpe_ratio = (returns.mean() * 252 - 0.02) / (returns.std() * np.sqrt(252))

        # Value at Risk (95% confidence)
        var_95 = returns.quantile(0.05)

        return {
            'annualized_volatility': annualized_vol,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'value_at_risk_95': var_95,
            'current_volatility_regime': self._processed_data['Realized_Volatility'].iloc[-1] or 0
        }

    def export_data_for_strategy(self, output_path: str) -> None:
        """
        Export processed data for use in trading strategies

        Args:
            output_path: Path to save the exported data
        """
        if self._processed_data is None:
            raise ValueError("Data not processed. Call preprocess_data() first.")

        # Select relevant columns for strategy
        export_columns = [
            'HSIF_Close',
            'HSIF_Return',
            'Bull_Price',
            'Bear_Price',
            'Bull_Bear_Ratio',
            'Fear_Greed_Index',
            'RSI_Signal',
            'Realized_Volatility',
            'Price_Change',
            'Rolling_Mean',
            'BB_Upper',
            'BB_Lower',
            'Volume'
        ]

        self._processed_data[export_columns].to_csv(output_path)
        logger.info(f"Data exported to {output_path}")

    async def update_data(self, new_data_path: str = None) -> bool:
        """
        Update data with new information

        Args:
            new_data_path: Path to new data file

        Returns:
            bool: True if update successful
        """
        try:
            if new_data_path:
                self.data_path = new_data_path

            return await self.load_data()

        except Exception as e:
            logger.error(f"Failed to update data: {str(e)}")
            return False


# Factory function for dependency injection
def create_cbbc_reader(data_path: str = None) -> CBBCDataReader:
    """Create and return CBBCDataReader instance"""
    return CBBCDataReader(data_path=data_path)


# Singleton instance for global access
_cbbc_reader_instance: Optional[CBBCDataReader] = None


def get_cbbc_reader() -> CBBCDataReader:
    """Get singleton CBBCDataReader instance"""
    global _cbbc_reader_instance
    if _cbbc_reader_instance is None:
        _cbbc_reader_instance = CBBCDataReader()
    return _cbbc_reader_instance