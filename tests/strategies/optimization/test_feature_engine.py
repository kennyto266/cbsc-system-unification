# tests/strategies/optimization/test_feature_engine.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.features.engine import FeatureEngine


class TestFeatureEngine:
    """Test FeatureEngine class"""

    def test_feature_engine_initialization(self):
        """Verify engine initializes with technical indicator"""
        # Create sample OHLCV data
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'open': np.random.randn(n).cumsum() + 100,
            'high': np.random.randn(n).cumsum() + 102,
            'low': np.random.randn(n).cumsum() + 98,
            'close': np.random.randn(n).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, n)
        })

        # Ensure high >= close >= low
        data['high'] = data[['open', 'close']].max(axis=1) + np.random.rand(n) * 2
        data['low'] = data[['open', 'close']].min(axis=1) - np.random.rand(n) * 2

        engine = FeatureEngine()

        # Verify it has technical indicator instance
        assert hasattr(engine, 'technical')
        assert engine.technical is not None

        # Verify it's the correct type
        from src.strategies.optimization.features.technical import TechnicalIndicators
        assert isinstance(engine.technical, TechnicalIndicators)

    def test_feature_engine_create_features(self):
        """Verify create_features generates expected features"""
        # Create sample OHLCV data
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            'open': np.random.randn(n).cumsum() + 100,
            'high': np.random.randn(n).cumsum() + 102,
            'low': np.random.randn(n).cumsum() + 98,
            'close': np.random.randn(n).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, n)
        })

        # Ensure high >= close >= low
        data['high'] = data[['open', 'close']].max(axis=1) + np.random.rand(n) * 2
        data['low'] = data[['open', 'close']].min(axis=1) - np.random.rand(n) * 2

        engine = FeatureEngine()
        features = engine.create_features(data)

        # Verify output is DataFrame
        assert isinstance(features, pd.DataFrame)

        # Verify technical features
        technical_features = [
            'sma_20', 'sma_50', 'ema_12', 'ema_26',
            'rsi_14',
            'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
            'atr_14',
            'stoch_k', 'stoch_d'
        ]
        for feature in technical_features:
            assert feature in features.columns, f"Missing technical feature: {feature}"

        # Verify price features
        price_features = [
            'returns_1d', 'returns_5d', 'returns_20d',
            'log_returns_1d',
            'price_position',
            'gap'
        ]
        for feature in price_features:
            assert feature in features.columns, f"Missing price feature: {feature}"

        # Verify volume features
        volume_features = [
            'volume_sma_20', 'volume_ratio',
            'volume_change',
            'pvt'
        ]
        for feature in volume_features:
            assert feature in features.columns, f"Missing volume feature: {feature}"

        # Verify statistical features
        statistical_features = [
            'volatility_20d',
            'skew_20d', 'kurtosis_20d',
            'zscore_20d'
        ]
        for feature in statistical_features:
            assert feature in features.columns, f"Missing statistical feature: {feature}"

        # Verify original columns are preserved
        for col in data.columns:
            assert col in features.columns, f"Missing original column: {col}"
