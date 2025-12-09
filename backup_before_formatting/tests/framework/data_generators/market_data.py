"""
Market data generator for testing purposes.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class MarketDataGenerator:
    """Generate realistic market data for testing."""

    def __init__(self):
        self.random = random.Random(42)  # Fixed seed for reproducible tests

    def generate_ohlcv_data(
        self,
        symbol: str,
        start_date: datetime,
        days: int,
        frequency: str = "1min",
        price_range: Tuple[float, float] = (100.0, 500.0),
        volatility: float = 0.02,
        trend: float = 0.0001,
        market_hours_only: bool = True,
    ) -> pd.DataFrame:
        """Generate realistic OHLCV market data."""
        # Determine data points based on frequency
        freq_to_minutes = {
            "1min": 1,
            "5min": 5,
            "15min": 15,
            "30min": 30,
            "1hour": 60,
            "4hour": 240,
            "1day": 1440,
        }

        if frequency not in freq_to_minutes:
            raise ValueError(f"Unsupported frequency: {frequency}")

        minutes_per_point = freq_to_minutes[frequency]

        # Calculate number of data points
        if market_hours_only and frequency in ["1min", "5min", "15min", "30min"]:
            # Market hours: 9:30 AM - 4:00 PM (6.5 hours = 390 minutes)
            trading_minutes_per_day = 390
            data_points = (days * trading_minutes_per_day) // minutes_per_point
        else:
            # 24 hours for other frequencies
            data_points = (days * 24 * 60) // minutes_per_point

        # Generate timestamps
        timestamps = self._generate_timestamps(
            start_date, data_points, frequency, market_hours_only
        )

        # Generate price data using geometric Brownian motion
        base_price = np.random.uniform(*price_range)
        prices = self._generate_price_series(base_price, data_points, volatility, trend)

        # Generate OHLCV from price series
        data = []
        for i, (timestamp, close_price) in enumerate(zip(timestamps, prices)):
            # Generate intrabar price movements
            if i > 0:
                prev_close = prices[i - 1]
            else:
                prev_close = close_price

            # Generate realistic OHLC
            high_offset = np.random.uniform(0, 0.005) * close_price
            low_offset = np.random.uniform(0, 0.005) * close_price

            high = max(close_price, prev_close) + high_offset
            low = min(close_price, prev_close) - low_offset

            # Open should be close to previous close
            open_diff = np.random.normal(0, 0.001) * prev_close
            open_price = max(low, min(high, prev_close + open_diff))

            # Ensure OHLC relationships are valid
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)

            # Generate volume
            base_volume = np.random.uniform(1000, 100000)
            volume_multiplier = 1 + np.random.normal(0, 0.3)
            volume = int(base_volume * volume_multiplier)

            # Add some outliers
            if np.random.random() < 0.01:  # 1% chance of outlier volume
                volume *= np.random.uniform(5, 20)

            data.append(
                {
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close_price, 2),
                    "volume": volume,
                }
            )

        return pd.DataFrame(data)

    def _generate_timestamps(
        self,
        start_date: datetime,
        data_points: int,
        frequency: str,
        market_hours_only: bool,
    ) -> List[datetime]:
        """Generate timestamps for market data."""
        timestamps = []
        current_time = start_date

        freq_to_minutes = {
            "1min": 1,
            "5min": 5,
            "15min": 15,
            "30min": 30,
            "1hour": 60,
            "4hour": 240,
            "1day": 1440,
        }

        minutes_per_point = freq_to_minutes[frequency]

        for _ in range(data_points):
            if market_hours_only and frequency in ["1min", "5min", "15min", "30min"]:
                # Only generate timestamps during market hours (9:30 AM - 4:00 PM)
                if (
                    current_time.hour < 9
                    or current_time.hour > 16
                    or (current_time.hour == 9 and current_time.minute < 30)
                    or (current_time.hour == 16 and current_time.minute > 0)
                ):
                    # Skip to next market day
                    current_time = self._next_market_day(current_time)
                    current_time = current_time.replace(
                        hour=9, minute=30, second=0, microsecond=0
                    )

            timestamps.append(current_time)
            current_time += timedelta(minutes=minutes_per_point)

        return timestamps

    def _next_market_day(self, current_time: datetime) -> datetime:
        """Get next market day (skipping weekends)."""
        next_day = current_time + timedelta(days=1)
        while next_day.weekday() >= 5:  # Saturday=5, Sunday=6
            next_day += timedelta(days=1)
        return next_day

    def _generate_price_series(
        self, initial_price: float, data_points: int, volatility: float, trend: float
    ) -> List[float]:
        """Generate price series using geometric Brownian motion."""
        prices = [initial_price]

        for _ in range(1, data_points):
            # Generate random return
            random_return = np.random.normal(trend, volatility)

            # Apply to price (geometric Brownian motion)
            new_price = prices[-1] * (1 + random_return)

            # Ensure positive price
            new_price = max(new_price, initial_price * 0.1)

            prices.append(new_price)

        return prices

    def generate_multi_asset_data(
        self,
        symbols: List[str],
        start_date: datetime,
        days: int,
        frequency: str = "1min",
        correlation_matrix: Optional[np.ndarray] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Generate correlated market data for multiple assets."""
        num_assets = len(symbols)

        # Generate correlation matrix if not provided
        if correlation_matrix is None:
            # Default: moderate positive correlation
            correlation_matrix = np.full((num_assets, num_assets), 0.3)
            np.fill_diagonal(correlation_matrix, 1.0)

        # Generate correlated random returns
        data_points = self._calculate_data_points(days, frequency)
        returns = self._generate_correlated_returns(
            num_assets, data_points, correlation_matrix
        )

        # Generate price data for each symbol
        market_data = {}
        for i, symbol in enumerate(symbols):
            # Generate base price
            base_price = np.random.uniform(100, 500)

            # Convert returns to prices
            prices = [base_price]
            for j in range(1, data_points):
                new_price = prices[-1] * (1 + returns[j, i])
                new_price = max(new_price, base_price * 0.1)
                prices.append(new_price)

            # Create OHLCV data
            timestamps = self._generate_timestamps(
                start_date, data_points, frequency, True
            )
            ohlcv_data = []

            for k, (timestamp, close_price) in enumerate(zip(timestamps, prices)):
                if k > 0:
                    prev_close = prices[k - 1]
                else:
                    prev_close = close_price

                # Generate OHLC
                high_offset = np.random.uniform(0, 0.005) * close_price
                low_offset = np.random.uniform(0, 0.005) * close_price

                high = max(close_price, prev_close) + high_offset
                low = min(close_price, prev_close) - low_offset

                open_diff = np.random.normal(0, 0.001) * prev_close
                open_price = max(low, min(high, prev_close + open_diff))

                high = max(high, open_price, close_price)
                low = min(low, open_price, close_price)

                volume = int(np.random.uniform(1000, 100000))

                ohlcv_data.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "open": round(open_price, 2),
                        "high": round(high, 2),
                        "low": round(low, 2),
                        "close": round(close_price, 2),
                        "volume": volume,
                    }
                )

            market_data[symbol] = pd.DataFrame(ohlcv_data)

        return market_data

    def _calculate_data_points(self, days: int, frequency: str) -> int:
        """Calculate number of data points for given days and frequency."""
        freq_to_minutes = {
            "1min": 1,
            "5min": 5,
            "15min": 15,
            "30min": 30,
            "1hour": 60,
            "4hour": 240,
            "1day": 1440,
        }

        if frequency not in freq_to_minutes:
            raise ValueError(f"Unsupported frequency: {frequency}")

        # For intraday data, use market hours only (6.5 hours = 390 minutes)
        if frequency in ["1min", "5min", "15min", "30min"]:
            return (days * 390) // freq_to_minutes[frequency]
        else:
            return (days * 24 * 60) // freq_to_minutes[frequency]

    def _generate_correlated_returns(
        self, num_assets: int, data_points: int, correlation_matrix: np.ndarray
    ) -> np.ndarray:
        """Generate correlated random returns using Cholesky decomposition."""
        # Generate uncorrelated random numbers
        uncorrelated = np.random.normal(0, 0.02, (data_points, num_assets))

        # Apply Cholesky decomposition to induce correlation
        try:
            chol_matrix = np.linalg.cholesky(correlation_matrix)
            correlated = uncorrelated @ chol_matrix.T
        except np.linalg.LinAlgError:
            # If correlation matrix is not positive definite, use identity
            correlated = uncorrelated

        return correlated

    def generate_market_regime_scenarios(
        self, symbol: str, start_date: datetime, scenarios: Dict[str, Dict[str, Any]]
    ) -> Dict[str, pd.DataFrame]:
        """Generate market data for different regime scenarios."""
        scenario_data = {}

        for scenario_name, scenario_params in scenarios.items():
            # Extract scenario parameters
            volatility = scenario_params.get("volatility", 0.02)
            trend = scenario_params.get("trend", 0.0)
            days = scenario_params.get("days", 30)
            frequency = scenario_params.get("frequency", "1min")
            price_range = scenario_params.get("price_range", (100, 500))

            # Generate scenario - specific data
            scenario_df = self.generate_ohlcv_data(
                symbol=symbol,
                start_date=start_date,
                days=days,
                frequency=frequency,
                price_range=price_range,
                volatility=volatility,
                trend=trend,
            )

            scenario_data[scenario_name] = scenario_df

        return scenario_data

    def add_market_microstructure_noise(
        self, data: pd.DataFrame, noise_level: float = 0.001
    ) -> pd.DataFrame:
        """Add realistic market microstructure noise to data."""
        noisy_data = data.copy()

        # Add bid - ask bounce
        noisy_data["close"] *= 1 + np.random.normal(0, noise_level, len(data))

        # Add price clustering (round to nearest tick size)
        tick_size = 0.01
        for col in ["open", "high", "low", "close"]:
            noisy_data[col] = (noisy_data[col] / tick_size).round() * tick_size

        # Add realistic volume patterns
        # Higher volume at market open and close
        for idx in noisy_data.index:
            hour = noisy_data.loc[idx, "timestamp"].hour
            if hour in [9, 10, 15, 16]:  # Market open / close hours
                volume_multiplier = np.random.uniform(1.5, 3.0)
            else:
                volume_multiplier = np.random.uniform(0.7, 1.3)

            noisy_data.loc[idx, "volume"] = int(
                noisy_data.loc[idx, "volume"] * volume_multiplier
            )

        return noisy_data
