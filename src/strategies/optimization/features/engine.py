# src/strategies/optimization/features/engine.py
import pandas as pd
import numpy as np
from typing import List, Optional
from .technical import TechnicalIndicators


class FeatureEngine:
    """Feature engineering pipeline for quantitative strategies"""

    def __init__(self):
        """Initialize feature engine with technical indicators"""
        self.technical = TechnicalIndicators()

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create all features from OHLCV data

        Args:
            data: DataFrame with OHLCV columns (open, high, low, close, volume)

        Returns:
            DataFrame with original data plus all features
        """
        df = data.copy()

        # Add different feature types
        df = self._add_technical_features(df)
        df = self._add_price_features(df)
        df = self._add_volume_features(df)
        df = self._add_statistical_features(df)

        return df

    def _add_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicator features"""

        # Moving averages
        df['sma_20'] = self.technical.sma(df['close'], 20)
        df['sma_50'] = self.technical.sma(df['close'], 50)
        df['ema_12'] = self.technical.ema(df['close'], 12)
        df['ema_26'] = self.technical.ema(df['close'], 26)

        # RSI
        df['rsi_14'] = self.technical.rsi(df['close'], 14)

        # MACD
        macd = self.technical.macd(df['close'])
        df['macd'] = macd['macd']
        df['macd_signal'] = macd['signal']
        df['macd_hist'] = macd['histogram']

        # Bollinger Bands
        bb = self.technical.bollinger_bands(df['close'])
        df['bb_upper'] = bb['upper']
        df['bb_middle'] = bb['middle']
        df['bb_lower'] = bb['lower']
        df['bb_width'] = (bb['upper'] - bb['lower']) / bb['middle']

        # ATR
        df['atr_14'] = self.technical.atr(df['high'], df['low'], df['close'], 14)

        # Stochastic
        stoch = self.technical.stoch(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch['k']
        df['stoch_d'] = stoch['d']

        return df

    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""

        # Returns
        df['returns_1d'] = df['close'].pct_change(1)
        df['returns_5d'] = df['close'].pct_change(5)
        df['returns_20d'] = df['close'].pct_change(20)

        # Log returns
        df['log_returns_1d'] = np.log(df['close'] / df['close'].shift(1))

        # Price position (where close is in current bar's range)
        df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])

        # Gap (open vs previous close)
        df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)

        return df

    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features"""

        # Volume moving average
        df['volume_sma_20'] = df['volume'].rolling(20).mean()

        # Volume ratio (current / average)
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']

        # Volume change
        df['volume_change'] = df['volume'].pct_change(1)

        # Price-Volume Trend (PVT)
        price_change = df['close'].pct_change(1)
        df['pvt'] = (price_change * df['volume']).cumsum()

        return df

    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add statistical features"""

        returns = df['returns_1d']

        # Volatility (rolling std of returns)
        df['volatility_20d'] = returns.rolling(20).std()

        # Skewness
        df['skew_20d'] = returns.rolling(20).skew()

        # Kurtosis
        df['kurtosis_20d'] = returns.rolling(20).kurt()

        # Z-score (on close prices, not returns)
        rolling_mean = df['close'].rolling(20).mean()
        rolling_std = df['close'].rolling(20).std()
        df['zscore_20d'] = (df['close'] - rolling_mean) / rolling_std

        return df

    def select_features(self,
                       features: pd.DataFrame,
                       method: str = 'all',
                       threshold: float = 0.01) -> List[str]:
        """
        Select features using various methods

        Args:
            features: DataFrame with all features
            method: Selection method - 'variance', 'correlation', or 'all'
            threshold: Threshold for selection method

        Returns:
            List of selected feature names
        """
        if method == 'all':
            # Return all features
            selected = features.columns.tolist()

        elif method == 'variance':
            # Select features with variance above threshold
            variance = features.var()
            selected = variance[variance > threshold].index.tolist()

        elif method == 'correlation':
            # Select features, removing highly correlated ones
            corr_matrix = features.corr().abs()

            # Find highly correlated pairs
            upper_triangle = corr_matrix.where(
                np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
            )

            # Find columns to drop
            to_drop = [col for col in upper_triangle.columns
                      if any(upper_triangle[col] > threshold)]

            # Select remaining features
            selected = [col for col in features.columns if col not in to_drop]

        else:
            raise ValueError(f"Unknown selection method: {method}")

        return selected
