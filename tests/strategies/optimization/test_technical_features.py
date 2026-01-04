# tests/strategies/optimization/test_technical_features.py
import pytest
import pandas as pd
import numpy as np
from src.strategies.optimization.features.technical import TechnicalIndicators


def test_technical_indicators_initialization():
    """Test TechnicalIndicators class can be initialized"""
    indicators = TechnicalIndicators()
    assert indicators is not None
    assert hasattr(indicators, 'use_talib')


def test_sma_calculation():
    """Test Simple Moving Average calculation with 20-period"""
    # Create sample data
    np.random.seed(42)
    data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })

    indicators = TechnicalIndicators()
    sma = indicators.sma(data['close'], period=20)

    assert sma is not None
    assert len(sma) == len(data)
    # First 19 values should be NaN (pandas default behavior)
    assert sma.isna().sum() == 19
    # Last value should be close to mean
    assert not pd.isna(sma.iloc[-1])


def test_rsi_calculation():
    """Test RSI calculation and verify it's between 0-100"""
    # Create sample data with upward trend
    np.random.seed(42)
    data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })

    indicators = TechnicalIndicators()
    rsi = indicators.rsi(data['close'], period=14)

    assert rsi is not None
    assert len(rsi) == len(data)
    # RSI should be between 0 and 100 (ignoring NaN values)
    valid_rsi = rsi.dropna()
    assert valid_rsi.min() >= 0
    assert valid_rsi.max() <= 100


def test_ema_calculation():
    """Test Exponential Moving Average calculation"""
    np.random.seed(42)
    data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })

    indicators = TechnicalIndicators()
    ema = indicators.ema(data['close'], period=20)

    assert ema is not None
    assert len(ema) == len(data)
    # EMA should have fewer NaN than SMA (starts from first data point)
    assert not pd.isna(ema.iloc[-1])


def test_bollinger_bands():
    """Test Bollinger Bands calculation"""
    np.random.seed(42)
    data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })

    indicators = TechnicalIndicators()
    bb = indicators.bollinger_bands(data['close'], period=20, std_dev=2.0)

    assert bb is not None
    assert isinstance(bb, pd.DataFrame)
    assert 'upper' in bb.columns
    assert 'middle' in bb.columns
    assert 'lower' in bb.columns
    assert len(bb) == len(data)
    # Upper band should be >= middle >= lower band
    valid_data = bb.dropna()
    assert (valid_data['upper'] >= valid_data['middle']).all()
    assert (valid_data['middle'] >= valid_data['lower']).all()


def test_macd():
    """Test MACD calculation"""
    np.random.seed(42)
    data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100
    })

    indicators = TechnicalIndicators()
    macd_result = indicators.macd(data['close'], fast=12, slow=26, signal=9)

    assert macd_result is not None
    assert isinstance(macd_result, pd.DataFrame)
    assert 'macd' in macd_result.columns
    assert 'signal' in macd_result.columns
    assert 'histogram' in macd_result.columns
    assert len(macd_result) == len(data)
    # Histogram should equal macd - signal
    valid_data = macd_result.dropna()
    assert np.allclose(
        valid_data['histogram'],
        valid_data['macd'] - valid_data['signal'],
        rtol=1e-10
    )


def test_atr():
    """Test Average True Range calculation"""
    np.random.seed(42)
    data = pd.DataFrame({
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'close': np.random.randn(100).cumsum() + 100
    })

    indicators = TechnicalIndicators()
    atr = indicators.atr(data['high'], data['low'], data['close'], period=14)

    assert atr is not None
    assert len(atr) == len(data)
    # ATR should be non-negative
    valid_atr = atr.dropna()
    assert (valid_atr >= 0).all()


def test_stoch():
    """Test Stochastic Oscillator calculation"""
    np.random.seed(42)
    data = pd.DataFrame({
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'close': np.random.randn(100).cumsum() + 100
    })

    indicators = TechnicalIndicators()
    stoch = indicators.stoch(data['high'], data['low'], data['close'],
                             k_period=14, d_period=3)

    assert stoch is not None
    assert isinstance(stoch, pd.DataFrame)
    assert 'k' in stoch.columns
    assert 'd' in stoch.columns
    assert len(stoch) == len(data)
    # Stochastic values should be between 0 and 100
    valid_data = stoch.dropna()
    assert (valid_data['k'] >= 0).all() and (valid_data['k'] <= 100).all()
    assert (valid_data['d'] >= 0).all() and (valid_data['d'] <= 100).all()
