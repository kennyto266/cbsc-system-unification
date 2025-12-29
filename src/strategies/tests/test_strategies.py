"""
Tests for trading strategies
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..ma_crossover import MACrossoverStrategy, EnhancedMACrossoverStrategy
from ..rsi_strategy import RSIStrategy, EnhancedRSIStrategy


class TestMACrossoverStrategy:
    """Test cases for MA Crossover Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        # Create 100 days of price data
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")

        # Generate trending price data
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5) + np.linspace(0, 20, 100)

        # Add some noise
        prices = prices + np.random.randn(100) * 0.1

        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(100) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(100) * 0.005)),
            'low': prices * (1 - np.abs(np.random.randn(100) * 0.005)),
            'close': prices,
            'volume': np.random.randint(10000, 100000, 100)
        }, index=dates)

        return data

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = MACrossoverStrategy(short_window=10, long_window=30)

        assert strategy.short_window == 10
        assert strategy.long_window == 30
        assert strategy.ma_type == 'sma'
        assert "MA_Crossover_10_30" in strategy.name

    def test_invalid_parameters(self):
        """Test invalid parameter handling"""
        with pytest.raises(ValueError):
            MACrossoverStrategy(short_window=30, long_window=10)  # Short >= Long

        with pytest.raises(ValueError):
            MACrossoverStrategy(ma_type='invalid')

    def test_sma_calculation(self, sample_data):
        """Test SMA calculation"""
        strategy = MACrossoverStrategy(short_window=10, long_window=30)

        short_ma = strategy.calculate_ma(sample_data['close'], 10, 'sma')
        long_ma = strategy.calculate_ma(sample_data['close'], 30, 'sma')

        # Check lengths
        assert len(short_ma) == len(sample_data)
        assert len(long_ma) == len(sample_data)

        # Check that initial values are NaN for SMA
        assert pd.isna(short_ma.iloc[0])
        assert pd.isna(long_ma.iloc[0])

        # Check that later values are not NaN
        assert not pd.isna(short_ma.iloc[20])
        assert not pd.isna(long_ma.iloc[40])

    def test_ema_calculation(self, sample_data):
        """Test EMA calculation"""
        strategy = MACrossoverStrategy(ma_type='ema')

        ema = strategy.calculate_ma(sample_data['close'], 20, 'ema')

        # EMA should have values from the beginning
        assert not pd.isna(ema.iloc[0])
        assert len(ema) == len(sample_data)

    def test_signal_generation(self, sample_data):
        """Test signal generation"""
        strategy = MACrossoverStrategy(short_window=10, long_window=30)
        signals = strategy.generate_signals(sample_data)

        # Check signals format
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)

        # Check signal values
        unique_signals = signals.unique()
        assert all(s in [-1, 0, 1] for s in unique_signals)

    def test_performance_metrics(self, sample_data):
        """Test performance metrics calculation"""
        strategy = MACrossoverStrategy(short_window=10, long_window=30)
        metrics = strategy.calculate_performance_metrics(sample_data)

        # Check required metrics
        required_keys = [
            'total_return', 'annual_return', 'volatility', 'sharpe_ratio',
            'total_signals', 'buy_signals', 'sell_signals', 'signal_frequency'
        ]

        for key in required_keys:
            assert key in metrics
            assert isinstance(metrics[key], (int, float))

    def test_enhanced_strategy_initialization(self):
        """Test enhanced strategy initialization"""
        strategy = EnhancedMACrossoverStrategy(
            stop_loss=0.05,
            take_profit=0.10,
            position_size=0.5
        )

        assert strategy.stop_loss == 0.05
        assert strategy.take_profit == 0.10
        assert strategy.position_size == 0.5
        assert strategy.current_position == 0
        assert strategy.entry_price is None


class TestRSIStrategy:
    """Test cases for RSI Strategy"""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data with trend"""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")

        # Create oscillating price data for RSI testing
        t = np.linspace(0, 4*np.pi, 100)
        prices = 100 + 10 * np.sin(t) + np.cumsum(np.random.randn(100) * 0.2)

        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(100) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(100) * 0.005)),
            'low': prices * (1 - np.abs(np.random.randn(100) * 0.005)),
            'close': prices,
            'volume': np.random.randint(10000, 100000, 100)
        }, index=dates)

        return data

    def test_initialization(self):
        """Test strategy initialization"""
        strategy = RSIStrategy(
            rsi_period=14,
            oversold_threshold=30,
            overbought_threshold=70
        )

        assert strategy.rsi_period == 14
        assert strategy.oversold_threshold == 30
        assert strategy.overbought_threshold == 70
        assert strategy.use_trend_filter == True

    def test_invalid_parameters(self):
        """Test invalid parameter handling"""
        with pytest.raises(ValueError):
            RSIStrategy(rsi_period=1)  # Period too short

        with pytest.raises(ValueError):
            RSIStrategy(oversold_threshold=40, overbought_threshold=30)  # Invalid range

    def test_rsi_calculation(self, sample_data):
        """Test RSI calculation"""
        strategy = RSIStrategy()
        rsi = strategy.calculate_rsi(sample_data['close'], 14)

        # Check RSI bounds
        assert rsi.min() >= 0
        assert rsi.max() <= 100

        # Check length
        assert len(rsi) == len(sample_data)

        # Check that RSI has some variation
        assert rsi.std() > 0

    def test_rsi_calculation_with_constant_prices(self):
        """Test RSI calculation with constant prices"""
        prices = pd.Series([100] * 50)
        strategy = RSIStrategy()
        rsi = strategy.calculate_rsi(prices, 14)

        # RSI should be 50 for constant prices (after initial period)
        assert abs(rsi.iloc[-1] - 50) < 1

    def test_signal_generation(self, sample_data):
        """Test signal generation"""
        strategy = RSIStrategy(oversold_threshold=30, overbought_threshold=70)
        signals = strategy.generate_signals(sample_data)

        # Check signals format
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)

        # Check signal values
        unique_signals = signals.unique()
        assert all(s in [-1, 0, 1] for s in unique_signals)

    def test_trend_filter(self, sample_data):
        """Test trend filter functionality"""
        strategy_with_filter = RSIStrategy(use_trend_filter=True)
        strategy_without_filter = RSIStrategy(use_trend_filter=False)

        signals_with = strategy_with_filter.generate_signals(sample_data)
        signals_without = strategy_without_filter.generate_signals(sample_data)

        # Signals should be different with and without trend filter
        assert not signals_with.equals(signals_without)

    def test_performance_metrics(self, sample_data):
        """Test performance metrics calculation"""
        strategy = RSIStrategy()
        metrics = strategy.calculate_performance_metrics(sample_data)

        # Check required metrics
        required_keys = [
            'total_return', 'annual_return', 'volatility', 'sharpe_ratio',
            'total_signals', 'buy_signals', 'sell_signals', 'signal_frequency',
            'rsi_mean', 'rsi_std'
        ]

        for key in required_keys:
            assert key in metrics

    def test_enhanced_rsi_strategy(self, sample_data):
        """Test enhanced RSI strategy"""
        strategy = EnhancedRSIStrategy(
            use_divergence=True,
            dynamic_thresholds=True,
            volume_confirmation=True
        )

        signals = strategy.generate_signals(sample_data)

        # Check that enhanced features are enabled
        assert strategy.use_divergence == True
        assert strategy.dynamic_thresholds == True
        assert strategy.volume_confirmation == True

        # Check signal format
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)


class TestStrategyOptimization:
    """Test strategy optimization functions"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for optimization"""
        dates = pd.date_range(start="2023-01-01", periods=200, freq="D")
        np.random.seed(42)

        # Create trending data with some volatility
        trend = np.linspace(100, 150, 200)
        noise = np.random.randn(200) * 2
        prices = trend + noise

        data = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(50000, 200000, 200)
        }, index=dates)

        return data

    def test_ma_optimization(self, sample_data):
        """Test MA parameter optimization"""
        from ..ma_crossover import optimize_ma_parameters

        # Optimize with small ranges for testing
        result = optimize_ma_parameters(
            sample_data,
            short_range=range(5, 11, 5),
            long_range=range(20, 31, 10),
            ma_types=['sma']
        )

        # Check result structure
        assert 'best_params' in result
        assert 'all_results' in result

        # Check best params
        best_params = result['best_params']
        assert best_params is not None
        assert 'short_window' in best_params
        assert 'long_window' in best_params
        assert 'sharpe_ratio' in best_params

    def test_rsi_optimization(self, sample_data):
        """Test RSI parameter optimization"""
        from ..rsi_strategy import optimize_rsi_parameters

        # Optimize with small ranges for testing
        result = optimize_rsi_parameters(
            sample_data,
            rsi_range=range(10, 15, 2),
            oversold_range=range(25, 31, 5),
            overbought_range=range(70, 76, 5)
        )

        # Check result structure
        assert 'best_params' in result
        assert 'all_results' in result

        # Check best params
        best_params = result['best_params']
        assert best_params is not None
        assert 'rsi_period' in best_params
        assert 'oversold_threshold' in best_params
        assert 'overbought_threshold' in best_params