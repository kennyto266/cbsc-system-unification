#!/usr/bin/env python3
"""
Performance Optimized Indicators Adapter
Simplified System - Performance Optimized Technical Indicators

This module provides a drop-in replacement for the existing CoreIndicators
with Phase 3 performance optimizations while maintaining API compatibility.
"""

import sys
import os
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Union, Tuple, Any
from pathlib import Path

# Add Phase 3 optimizer to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from phase3_performance_optimizer import (
    OptimizedTechnicalIndicators,
    PerformanceMonitor,
    create_performance_optimizer
)

logger = logging.getLogger(__name__)

class PerformanceOptimizedCoreIndicators:
    """
    Performance-optimized drop-in replacement for CoreIndicators

    This class maintains 100% API compatibility with the original CoreIndicators
    while adding significant performance improvements through:

    - Intelligent caching with memory management
    - Batch processing for multiple indicators
    - Parallel computation capabilities
    - Vectorized operations
    - Memory-efficient algorithms
    """

    def __init__(self, enable_optimizations: bool = True,
                 cache_size_mb: int = 100,
                 enable_parallel: bool = True,
                 batch_size: int = 1000):
        """
        Initialize performance-optimized indicators engine

        Args:
            enable_optimizations: Whether to enable performance optimizations
            cache_size_mb: Cache size limit in MB
            enable_parallel: Enable parallel processing
            batch_size: Batch size for processing
        """
        self.enable_optimizations = enable_optimizations

        if enable_optimizations:
            # Initialize optimized engine
            self.optimized_engine = OptimizedTechnicalIndicators(
                use_cache=True,
                enable_parallel=enable_parallel,
                cache_size_mb=cache_size_mb,
                batch_size=batch_size
            )

            # Initialize performance monitor
            self.monitor = PerformanceMonitor()
            self.monitor.start_monitoring()

            logger.info(f"PerformanceOptimizedCoreIndicators initialized with optimizations: "
                       f"cache={cache_size_mb}MB, parallel={enable_parallel}, batch_size={batch_size}")
        else:
            # Fallback to basic implementation
            self.optimized_engine = None
            self.monitor = None
            logger.info("PerformanceOptimizedCoreIndicators initialized without optimizations")

    # ==================== Original API Compatibility ====================

    def calculate_sma(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average (SMA)

        Args:
            prices: Price series
            period: Period for SMA, default 20

        Returns:
            SMA series
        """
        if not self.enable_optimizations:
            return self._calculate_sma_basic(prices, period)

        try:
            # Use optimized implementation
            result_array = self.optimized_engine._calculate_sma_vectorized(
                prices.values.astype(np.float64), period
            )
            return pd.Series(result_array, index=prices.index)
        except Exception as e:
            logger.error(f"Optimized SMA calculation failed: {e}, falling back to basic method")
            return self._calculate_sma_basic(prices, period)

    def calculate_ema(self, prices: pd.Series, period: int = 26) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA)

        Args:
            prices: Price series
            period: Period for EMA, default 26

        Returns:
            EMA series
        """
        if not self.enable_optimizations:
            return self._calculate_ema_basic(prices, period)

        try:
            # Use optimized implementation
            result_array = self.optimized_engine._calculate_ema_vectorized(
                prices.values.astype(np.float64), period
            )
            return pd.Series(result_array, index=prices.index)
        except Exception as e:
            logger.error(f"Optimized EMA calculation failed: {e}, falling back to basic method")
            return self._calculate_ema_basic(prices, period)

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)

        Args:
            prices: Price series
            period: Period for RSI, default 14

        Returns:
            RSI series
        """
        if not self.enable_optimizations:
            return self._calculate_rsi_basic(prices, period)

        try:
            # Use optimized implementation
            result_array = self.optimized_engine.calculate_rsi_optimized(prices, period)
            return pd.Series(result_array, index=prices.index)
        except Exception as e:
            logger.error(f"Optimized RSI calculation failed: {e}, falling back to basic method")
            return self._calculate_rsi_basic(prices, period)

    def calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Calculate MACD indicator

        Args:
            prices: Price series
            fast: Fast period, default 12
            slow: Slow period, default 26
            signal: Signal period, default 9

        Returns:
            Dictionary containing MACD, signal, and histogram series
        """
        if not self.enable_optimizations:
            return self._calculate_macd_basic(prices, fast, slow, signal)

        try:
            # Use optimized implementation
            results_dict = self.optimized_engine.calculate_macd_optimized(
                prices.values, fast, slow, signal
            )

            # Convert back to pandas Series
            return {
                'macd': pd.Series(results_dict['macd'], index=prices.index),
                'signal': pd.Series(results_dict['signal'], index=prices.index),
                'histogram': pd.Series(results_dict['histogram'], index=prices.index)
            }
        except Exception as e:
            logger.error(f"Optimized MACD calculation failed: {e}, falling back to basic method")
            return self._calculate_macd_basic(prices, fast, slow, signal)

    def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands

        Args:
            prices: Price series
            period: Period for bands, default 20
            std_dev: Standard deviation multiplier, default 2.0

        Returns:
            Dictionary containing upper, middle, and lower bands
        """
        if not self.enable_optimizations:
            return self._calculate_bollinger_basic(prices, period, std_dev)

        try:
            # Use optimized implementation
            middle = self.calculate_sma(prices, period)
            rolling_std = prices.rolling(window=period, min_periods=1).std()
            upper = middle + (rolling_std * std_dev)
            lower = middle - (rolling_std * std_dev)

            return {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }
        except Exception as e:
            logger.error(f"Optimized Bollinger Bands calculation failed: {e}, falling back to basic method")
            return self._calculate_bollinger_basic(prices, period, std_dev)

    def calculate_stochastic(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """
        Calculate Stochastic Oscillator

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            k_period: %K period, default 14
            d_period: %D period, default 3

        Returns:
            Dictionary containing %K and %D series
        """
        if not self.enable_optimizations:
            return self._calculate_stochastic_basic(high, low, close, k_period, d_period)

        try:
            # Use vectorized implementation
            lowest_low = low.rolling(window=k_period, min_periods=1).min()
            highest_high = high.rolling(window=k_period, min_periods=1).max()

            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-10))
            d_percent = k_percent.rolling(window=d_period, min_periods=1).mean()

            return {
                'k': k_percent,
                'd': d_percent
            }
        except Exception as e:
            logger.error(f"Optimized Stochastic calculation failed: {e}, falling back to basic method")
            return self._calculate_stochastic_basic(high, low, close, k_period, d_period)

    def calculate_williams_r(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Williams %R

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Period for Williams %R, default 14

        Returns:
            Williams %R series
        """
        if not self.enable_optimizations:
            return self._calculate_williams_r_basic(high, low, close, period)

        try:
            # Use vectorized implementation
            highest_high = high.rolling(window=period, min_periods=1).max()
            lowest_low = low.rolling(window=period, min_periods=1).min()

            williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low + 1e-10))
            return williams_r
        except Exception as e:
            logger.error(f"Optimized Williams %R calculation failed: {e}, falling back to basic method")
            return self._calculate_williams_r_basic(high, low, close, period)

    def calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range (ATR)

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Period for ATR, default 14

        Returns:
            ATR series
        """
        if not self.enable_optimizations:
            return self._calculate_atr_basic(high, low, close, period)

        try:
            # Use vectorized implementation
            high_low = high - low
            high_close = np.abs(high - close.shift(1))
            low_close = np.abs(low - close.shift(1))

            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(window=period, min_periods=1).mean()

            return atr
        except Exception as e:
            logger.error(f"Optimized ATR calculation failed: {e}, falling back to basic method")
            return self._calculate_atr_basic(high, low, close, period)

    def calculate_volume_ma(self, volume: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Volume Moving Average

        Args:
            volume: Volume series
            period: Period for MA, default 20

        Returns:
            Volume MA series
        """
        if not self.enable_optimizations:
            return self._calculate_volume_ma_basic(volume, period)

        try:
            # Use optimized SMA calculation
            result_array = self.optimized_engine._calculate_sma_vectorized(
                volume.values.astype(np.float64), period
            )
            return pd.Series(result_array, index=volume.index)
        except Exception as e:
            logger.error(f"Optimized Volume MA calculation failed: {e}, falling back to basic method")
            return self._calculate_volume_ma_basic(volume, period)

    # ==================== Enhanced Batch Processing Methods ====================

    def calculate_multiple_indicators(self, data: pd.DataFrame,
                                    indicators_config: List[Dict[str, Any]]) -> Dict[str, pd.Series]:
        """
        Calculate multiple indicators in batch for optimal performance

        Args:
            data: DataFrame with OHLCV data
            indicators_config: List of indicator configurations

        Returns:
            Dictionary of indicator results
        """
        if not self.enable_optimizations or not self.optimized_engine:
            return self._calculate_multiple_indicators_basic(data, indicators_config)

        try:
            # Use optimized batch processing
            results_dict = self.optimized_engine.calculate_multiple_indicators_batch(
                data, indicators_config
            )

            # Convert numpy arrays back to pandas Series
            results = {}
            for indicator_name, values in results_dict.items():
                if isinstance(values, dict):
                    # Handle nested dictionaries (like MACD results)
                    for sub_key, sub_values in values.items():
                        combined_name = f"{indicator_name}_{sub_key}"
                        results[combined_name] = pd.Series(sub_values, index=data.index)
                else:
                    results[indicator_name] = pd.Series(values, index=data.index)

            return results
        except Exception as e:
            logger.error(f"Batch processing failed: {e}, falling back to sequential calculation")
            return self._calculate_multiple_indicators_basic(data, indicators_config)

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report

        Returns:
            Performance metrics and statistics
        """
        if not self.enable_optimizations:
            return {"optimization_enabled": False}

        try:
            report = {
                "optimization_enabled": True,
                "engine_performance": self.optimized_engine.get_performance_report(),
                "system_metrics": self.monitor.get_current_metrics() if self.monitor else {},
                "cache_stats": self.optimized_engine.batch_processor.cache.get_stats() if self.optimized_engine.batch_processor else {}
            }
            return report
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"optimization_enabled": True, "error": str(e)}

    def optimize_memory(self) -> None:
        """Optimize memory usage"""
        if self.enable_optimizations and self.optimized_engine:
            self.optimized_engine.optimize_memory()

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.monitor:
            self.monitor.stop_monitoring()
        if self.optimized_engine:
            self.optimized_engine.optimize_memory()

    # ==================== Fallback Basic Implementations ====================

    def _calculate_sma_basic(self, prices: pd.Series, period: int) -> pd.Series:
        """Basic SMA implementation as fallback"""
        return prices.rolling(window=period, min_periods=1).mean()

    def _calculate_ema_basic(self, prices: pd.Series, period: int) -> pd.Series:
        """Basic EMA implementation as fallback"""
        return prices.ewm(span=period, adjust=False).mean()

    def _calculate_rsi_basic(self, prices: pd.Series, period: int) -> pd.Series:
        """Basic RSI implementation as fallback"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd_basic(self, prices: pd.Series, fast: int, slow: int, signal: int) -> Dict[str, pd.Series]:
        """Basic MACD implementation as fallback"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }

    def _calculate_bollinger_basic(self, prices: pd.Series, period: int, std_dev: float) -> Dict[str, pd.Series]:
        """Basic Bollinger Bands implementation as fallback"""
        middle = prices.rolling(window=period, min_periods=1).mean()
        rolling_std = prices.rolling(window=period, min_periods=1).std()
        upper = middle + (rolling_std * std_dev)
        lower = middle - (rolling_std * std_dev)

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }

    def _calculate_stochastic_basic(self, high: pd.Series, low: pd.Series, close: pd.Series,
                                   k_period: int, d_period: int) -> Dict[str, pd.Series]:
        """Basic Stochastic implementation as fallback"""
        lowest_low = low.rolling(window=k_period, min_periods=1).min()
        highest_high = high.rolling(window=k_period, min_periods=1).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period, min_periods=1).mean()

        return {
            'k': k_percent,
            'd': d_percent
        }

    def _calculate_williams_r_basic(self, high: pd.Series, low: pd.Series, close: pd.Series,
                                    period: int) -> pd.Series:
        """Basic Williams %R implementation as fallback"""
        highest_high = high.rolling(window=period, min_periods=1).max()
        lowest_low = low.rolling(window=period, min_periods=1).min()
        return -100 * ((highest_high - close) / (highest_high - lowest_low))

    def _calculate_atr_basic(self, high: pd.Series, low: pd.Series, close: pd.Series,
                            period: int) -> pd.Series:
        """Basic ATR implementation as fallback"""
        high_low = high - low
        high_close = np.abs(high - close.shift(1))
        low_close = np.abs(low - close.shift(1))
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(window=period, min_periods=1).mean()

    def _calculate_volume_ma_basic(self, volume: pd.Series, period: int) -> pd.Series:
        """Basic Volume MA implementation as fallback"""
        return volume.rolling(window=period, min_periods=1).mean()

    def _calculate_multiple_indicators_basic(self, data: pd.DataFrame,
                                           indicators_config: List[Dict[str, Any]]) -> Dict[str, pd.Series]:
        """Basic sequential calculation as fallback"""
        results = {}

        for config in indicators_config:
            indicator_type = config.get('type', 'sma')
            indicator_name = config.get('name', indicator_type)
            params = config.get('params', {})

            try:
                if indicator_type == 'rsi':
                    results[indicator_name] = self.calculate_rsi(data['close'], **params)
                elif indicator_type == 'macd':
                    macd_results = self.calculate_macd(data['close'], **params)
                    for key, series in macd_results.items():
                        results[f"{indicator_name}_{key}"] = series
                elif indicator_type == 'sma':
                    results[indicator_name] = self.calculate_sma(data['close'], **params)
                elif indicator_type == 'ema':
                    results[indicator_name] = self.calculate_ema(data['close'], **params)
                elif indicator_type == 'bollinger':
                    bb_results = self.calculate_bollinger_bands(data['close'], **params)
                    for key, series in bb_results.items():
                        results[f"{indicator_name}_{key}"] = series
                elif indicator_type == 'stochastic':
                    stoch_results = self.calculate_stochastic(data['high'], data['low'], data['close'], **params)
                    for key, series in stoch_results.items():
                        results[f"{indicator_name}_{key}"] = series
                elif indicator_type == 'williams_r':
                    results[indicator_name] = self.calculate_williams_r(data['high'], data['low'], data['close'], **params)
                elif indicator_type == 'atr':
                    results[indicator_name] = self.calculate_atr(data['high'], data['low'], data['close'], **params)
                elif indicator_type == 'volume_ma':
                    results[indicator_name] = self.calculate_volume_ma(data['volume'], **params)
                else:
                    logger.warning(f"Unknown indicator type: {indicator_type}")

            except Exception as e:
                logger.error(f"Error calculating {indicator_name}: {e}")
                results[indicator_name] = pd.Series([np.nan] * len(data), index=data.index)

        return results

# Factory function for easy integration and backward compatibility
def create_optimized_core_indicators(enable_optimizations: bool = True,
                                   cache_size_mb: int = 100,
                                   enable_parallel: bool = True,
                                   batch_size: int = 1000) -> 'PerformanceOptimizedCoreIndicators':
    """
    Factory function to create optimized core indicators

    This function provides the same interface as the original CoreIndicators
    constructor while adding performance optimization capabilities.

    Args:
        enable_optimizations: Enable performance optimizations
        cache_size_mb: Cache size in MB
        enable_parallel: Enable parallel processing
        batch_size: Batch size for processing

    Returns:
        PerformanceOptimizedCoreIndicators instance
    """
    return PerformanceOptimizedCoreIndicators(
        enable_optimizations=enable_optimizations,
        cache_size_mb=cache_size_mb,
        enable_parallel=enable_parallel,
        batch_size=batch_size
    )

# Backward compatibility alias
CoreIndicatorsOptimized = PerformanceOptimizedCoreIndicators