"""
Volatility Indicators Implementation - Phase 2.3
波动率指标独立实现文件
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union

class IndicatorResult:
    """Indicator result wrapper class"""
    def __init__(self, name: str, values, parameters: Dict[str, Any],
                 metadata: Optional[Dict[str, Any]] = None,
                 signals: Optional[pd.Series] = None):
        self.name = name
        self.values = values
        self.parameters = parameters
        self.metadata = metadata or {}
        self.signals = signals if signals is not None else pd.Series()

class VolatilityIndicators:
    """Volatility Indicators Calculator - Phase 2.3"""

    def __init__(self):
        self.performance_cache = {}

    def calculate_bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: float = 2.0) -> IndicatorResult:
        """
        Calculate Bollinger Bands

        Parameters:
        -----------
        data : pd.Series
            Price data
        period : int, default 20
            Moving average period
        std_dev : float, default 2.0
            Standard deviation multiplier

        Returns:
        --------
        IndicatorResult
            Bollinger Bands with upper, middle, lower bands
        """
        try:
            # Middle band: Simple Moving Average
            sma = data.rolling(window=period).mean()

            # Standard deviation
            rolling_std = data.rolling(window=period).std()

            # Upper and lower bands
            upper_band = sma + (rolling_std * std_dev)
            lower_band = sma - (rolling_std * std_dev)

            # %B indicator (price position within bands)
            percent_b = (data - lower_band) / (upper_band - lower_band)

            # Bandwidth (band width)
            bandwidth = (upper_band - lower_band) / sma

            values = {
                'upper': upper_band,
                'middle': sma,
                'lower': lower_band,
                'percent_b': percent_b,
                'bandwidth': bandwidth
            }

            parameters = {
                'period': period,
                'std_dev': std_dev
            }

            return IndicatorResult(
                name="Bollinger_Bands",
                values=values,
                parameters=parameters,
                signals=self._generate_bollinger_signals(data, upper_band, lower_band, percent_b)
            )

        except Exception as e:
            raise ValueError(f"Bollinger Bands calculation failed: {e}")

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> IndicatorResult:
        """
        Calculate Average True Range

        Parameters:
        -----------
        high : pd.Series
            High price data
        low : pd.Series
            Low price data
        close : pd.Series
            Close price data
        period : int, default 14
            ATR period

        Returns:
        --------
        IndicatorResult
            ATR indicator values
        """
        try:
            # Calculate True Range
            tr1 = high - low  # Current high minus low
            tr2 = abs(high - close.shift(1))  # Current high minus previous close
            tr3 = abs(low - close.shift(1))   # Current low minus previous close

            # True Range is the maximum of the three
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # ATR is the moving average of True Range
            atr = true_range.rolling(window=period).mean()

            # ATR percentage (percentage of close price)
            atr_percent = (atr / close) * 100

            values = pd.Series(atr, index=close.index)
            metadata = {
                'true_range': true_range,
                'atr_percent': atr_percent
            }

            parameters = {'period': period}

            return IndicatorResult(
                name="ATR",
                values=values,
                parameters=parameters,
                metadata=metadata,
                signals=self._generate_atr_signals(atr, atr_percent)
            )

        except Exception as e:
            raise ValueError(f"ATR calculation failed: {e}")

    def calculate_keltner_channels(self, high: pd.Series, low: pd.Series, close: pd.Series,
                                 ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0) -> IndicatorResult:
        """
        Calculate Keltner Channels

        Parameters:
        -----------
        high : pd.Series
            High price data
        low : pd.Series
            Low price data
        close : pd.Series
            Close price data
        ema_period : int, default 20
            EMA period
        atr_period : int, default 10
            ATR period
        multiplier : float, default 2.0
            ATR multiplier

        Returns:
        --------
        IndicatorResult
            Keltner Channels indicator
        """
        try:
            # Middle line: EMA
            middle_line = close.ewm(span=ema_period, adjust=False).mean()

            # Calculate ATR
            atr_result = self.calculate_atr(high, low, close, atr_period)
            atr = atr_result.values

            # Upper and lower channels
            upper_channel = middle_line + (atr * multiplier)
            lower_channel = middle_line - (atr * multiplier)

            # Channel position (price position relative to channel)
            channel_position = (close - lower_channel) / (upper_channel - lower_channel)

            # Channel width
            channel_width = (upper_channel - lower_channel) / middle_line

            values = {
                'upper': upper_channel,
                'middle': middle_line,
                'lower': lower_channel,
                'channel_position': channel_position,
                'channel_width': channel_width
            }

            parameters = {
                'ema_period': ema_period,
                'atr_period': atr_period,
                'multiplier': multiplier
            }

            return IndicatorResult(
                name="Keltner_Channels",
                values=values,
                parameters=parameters,
                signals=self._generate_keltner_signals(close, upper_channel, lower_channel, channel_position)
            )

        except Exception as e:
            raise ValueError(f"Keltner Channels calculation failed: {e}")

    def calculate_donchian_channels(self, high: pd.Series, low: pd.Series, period: int = 20) -> IndicatorResult:
        """
        Calculate Donchian Channels

        Parameters:
        -----------
        high : pd.Series
            High price data
        low : pd.Series
            Low price data
        period : int, default 20
            Channel period

        Returns:
        --------
        IndicatorResult
            Donchian Channels indicator
        """
        try:
            # Upper channel: highest high over period
            upper_channel = high.rolling(window=period).max()

            # Lower channel: lowest low over period
            lower_channel = low.rolling(window=period).min()

            # Middle channel: average of upper and lower
            middle_channel = (upper_channel + lower_channel) / 2

            # Channel width
            channel_width = (upper_channel - lower_channel) / middle_channel

            # Price position in channel (using middle price)
            price_position = (high + low) / 2
            channel_position = (price_position - lower_channel) / (upper_channel - lower_channel)

            values = {
                'upper': upper_channel,
                'middle': middle_channel,
                'lower': lower_channel,
                'channel_width': channel_width,
                'channel_position': channel_position
            }

            parameters = {'period': period}

            return IndicatorResult(
                name="Donchian_Channels",
                values=values,
                parameters=parameters,
                signals=self._generate_donchian_signals(high, low, upper_channel, lower_channel)
            )

        except Exception as e:
            raise ValueError(f"Donchian Channels calculation failed: {e}")

    def calculate_all_volatility_indicators(self, data: pd.DataFrame) -> dict:
        """
        Batch calculate all volatility indicators

        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with OHLC data

        Returns:
        --------
        dict
            All volatility indicator results
        """
        results = {}

        try:
            # Bollinger Bands (multiple parameters)
            for period, std_dev in [(10, 1.5), (20, 2.0), (20, 2.5), (50, 2.0)]:
                bb_result = self.calculate_bollinger_bands(data['close'], period, std_dev)
                results[f'BB_{period}_{std_dev}'] = bb_result

            # ATR (multiple periods)
            for period in [7, 14, 21]:
                atr_result = self.calculate_atr(data['high'], data['low'], data['close'], period)
                results[f'ATR_{period}'] = atr_result

            # Keltner Channels (multiple parameters)
            for ema_period, multiplier in [(20, 2.0), (20, 2.5), (10, 1.5)]:
                kc_result = self.calculate_keltner_channels(
                    data['high'], data['low'], data['close'],
                    ema_period=ema_period, atr_period=10, multiplier=multiplier
                )
                results[f'KC_{ema_period}_{multiplier}'] = kc_result

            # Donchian Channels (multiple periods)
            for period in [10, 20, 50]:
                dc_result = self.calculate_donchian_channels(data['high'], data['low'], period)
                results[f'DC_{period}'] = dc_result

        except Exception as e:
            raise ValueError(f"Batch calculation of volatility indicators failed: {e}")

        return results

    def get_indicator_performance_metrics(self, indicator_result: IndicatorResult) -> dict:
        """
        Get performance metrics for an indicator result

        Parameters:
        -----------
        indicator_result : IndicatorResult
            Indicator result to analyze

        Returns:
        --------
        dict
            Performance metrics
        """
        if isinstance(indicator_result.values, dict):
            # For multi-value indicators like Bollinger Bands
            main_values = indicator_result.values.get('upper', pd.Series())
        else:
            # For single-value indicators like ATR
            main_values = indicator_result.values

        return {
            'mean': main_values.mean(),
            'std': main_values.std(),
            'min': main_values.min(),
            'max': main_values.max(),
            'valid_count': main_values.count(),
            'total_count': len(main_values),
            'signal_ratio': indicator_result.signals.sum() / len(indicator_result.signals) if len(indicator_result.signals) > 0 else 0
        }

    # ========================================
    # Signal Generation Methods
    # ========================================

    def _generate_bollinger_signals(self, price, upper_band, lower_band, percent_b):
        """Generate Bollinger Bands trading signals"""
        signals = pd.Series(0, index=price.index)

        # Price breaks below lower band - buy signal
        signals[(price < lower_band) & (price.shift(1) >= lower_band.shift(1))] = 1

        # Price breaks above upper band - sell signal
        signals[(price > upper_band) & (price.shift(1) <= upper_band.shift(1))] = -1

        # %B indicator signals
        signals[(percent_b < 0.05) & (percent_b.shift(1) >= 0.05)] = 1  # Oversold
        signals[(percent_b > 0.95) & (percent_b.shift(1) <= 0.95)] = -1  # Overbought

        return signals

    def _generate_atr_signals(self, atr, atr_percent, threshold_multiplier=2.0):
        """Generate ATR-related signals"""
        signals = pd.Series(0, index=atr.index)

        # ATR unusually high (possible market turning points)
        atr_threshold = atr_percent.rolling(window=20).mean() * threshold_multiplier
        signals[atr_percent > atr_threshold] = 1  # High volatility opportunity

        # ATR unusually low (possible pre-breakout consolidation)
        atr_low_threshold = atr_percent.rolling(window=20).mean() * 0.5
        signals[atr_percent < atr_low_threshold] = -1  # Low volatility consolidation

        return signals

    def _generate_keltner_signals(self, price, upper_channel, lower_channel, channel_position):
        """Generate Keltner Channels signals"""
        signals = pd.Series(0, index=price.index)

        # Break above upper channel
        signals[(price > upper_channel) & (price.shift(1) <= upper_channel.shift(1))] = 1

        # Break below lower channel
        signals[(price < lower_channel) & (price.shift(1) >= lower_channel.shift(1))] = -1

        # Channel position signals
        signals[(channel_position < 0.1) & (channel_position.shift(1) >= 0.1)] = 1  # Near lower band
        signals[(channel_position > 0.9) & (channel_position.shift(1) <= 0.9)] = -1  # Near upper band

        return signals

    def _generate_donchian_signals(self, high, low, upper_channel, lower_channel):
        """Generate Donchian Channels signals"""
        signals = pd.Series(0, index=high.index)

        # Breakout above 20-day high - buy signal
        buy_breakout = (high > upper_channel) & (high.shift(1) <= upper_channel.shift(1))
        signals[buy_breakout] = 1

        # Breakout below 20-day low - sell signal
        sell_breakout = (low < lower_channel) & (low.shift(1) >= lower_channel.shift(1))
        signals[sell_breakout] = -1

        return signals


def test_volatility_indicators():
    """Test volatility indicators implementation"""

    # Create test data with OHLC format
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    # Simulate realistic price data
    base_price = 100
    close_data = []
    high_data = []
    low_data = []

    for i in range(len(dates)):
        # Add trend and cyclical components
        trend = base_price + i * 0.01
        cycle = 5 * np.sin(2 * np.pi * i / 50)
        noise = np.random.normal(0, 1.5)

        close = trend + cycle + noise
        high = close + abs(np.random.normal(0, 0.8))
        low = close - abs(np.random.normal(0, 0.8))

        close_data.append(close)
        high_data.append(high)
        low_data.append(low)

    # Create series
    close_series = pd.Series(close_data, index=dates)
    high_series = pd.Series(high_data, index=dates)
    low_series = pd.Series(low_data, index=dates)

    # Create indicator calculator
    calculator = VolatilityIndicators()

    print("Testing Volatility Indicators - Phase 2.3")
    print("=" * 60)

    # Test Bollinger Bands
    print("\n1. Bollinger Bands:")
    try:
        bb_result = calculator.calculate_bollinger_bands(close_series, period=20, std_dev=2.0)
        print(f"   Bollinger Bands: SUCCESS")
        print(f"   Upper Mean: {bb_result.values['upper'].mean():.2f}")
        print(f"   Middle Mean: {bb_result.values['middle'].mean():.2f}")
        print(f"   Lower Mean: {bb_result.values['lower'].mean():.2f}")
        print(f"   Percent B Mean: {bb_result.values['percent_b'].mean():.3f}")
        print(f"   Bandwidth Mean: {bb_result.values['bandwidth'].mean():.3f}")
        print(f"   Valid points: {bb_result.values['upper'].count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test ATR
    print("\n2. Average True Range (ATR):")
    try:
        atr_result = calculator.calculate_atr(high_series, low_series, close_series, period=14)
        print(f"   ATR: SUCCESS")
        print(f"   ATR Mean: {atr_result.values.mean():.4f}")
        print(f"   ATR Std: {atr_result.values.std():.4f}")
        print(f"   ATR Percent Mean: {atr_result.metadata['atr_percent'].mean():.2f}%")
        print(f"   Valid points: {atr_result.values.count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test Keltner Channels
    print("\n3. Keltner Channels:")
    try:
        kc_result = calculator.calculate_keltner_channels(
            high_series, low_series, close_series,
            ema_period=20, atr_period=10, multiplier=2.0
        )
        print(f"   Keltner Channels: SUCCESS")
        print(f"   Upper Mean: {kc_result.values['upper'].mean():.2f}")
        print(f"   Middle Mean: {kc_result.values['middle'].mean():.2f}")
        print(f"   Lower Mean: {kc_result.values['lower'].mean():.2f}")
        print(f"   Channel Position Mean: {kc_result.values['channel_position'].mean():.3f}")
        print(f"   Channel Width Mean: {kc_result.values['channel_width'].mean():.3f}")
        print(f"   Valid points: {kc_result.values['upper'].count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test Donchian Channels
    print("\n4. Donchian Channels:")
    try:
        dc_result = calculator.calculate_donchian_channels(high_series, low_series, period=20)
        print(f"   Donchian Channels: SUCCESS")
        print(f"   Upper Mean: {dc_result.values['upper'].mean():.2f}")
        print(f"   Middle Mean: {dc_result.values['middle'].mean():.2f}")
        print(f"   Lower Mean: {dc_result.values['lower'].mean():.2f}")
        print(f"   Channel Width Mean: {dc_result.values['channel_width'].mean():.3f}")
        print(f"   Channel Position Mean: {dc_result.values['channel_position'].mean():.3f}")
        print(f"   Valid points: {dc_result.values['upper'].count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test Batch Calculation
    print("\n5. Batch Volatility Indicators Test:")
    try:
        # Create DataFrame for batch calculation
        test_data = pd.DataFrame({
            'high': high_series,
            'low': low_series,
            'close': close_series
        })

        all_results = calculator.calculate_all_volatility_indicators(test_data)
        print(f"   Calculated indicators: {len(all_results)}")

        for name, result in list(all_results.items())[:8]:  # Show first 8
            if hasattr(result, 'values'):
                if isinstance(result.values, dict):
                    valid_count = result.values.get('upper', pd.Series()).count() if 'upper' in result.values else 0
                else:
                    valid_count = result.values.count()
                print(f"   {name}: Valid points {valid_count}")

        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    print("\n" + "=" * 60)
    print("Phase 2.3 Volatility Indicators Test Complete!")
    print("All 4 volatility indicator types implemented successfully!")
    print("Status: ALL TESTS PASSED")
    return True


if __name__ == "__main__":
    success = test_volatility_indicators()
    if success:
        print("\n[SUCCESS] Phase 2.3 completed successfully!")
    else:
        print("\n[FAILED] Phase 2.3 failed!")