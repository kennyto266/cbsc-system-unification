"""
Market Data Adapter
市場數據適配器

Unified interface for accessing market data from multiple sources including
InfluxDB, Yahoo Finance, Alpha Vantage, and other data providers.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
import yfinance as yf
import requests
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class MarketDataConfig:
    """Configuration for market data adapter"""
    primary_source: str = "yahoo"  # yahoo, alpha_vantage, polygon, influxdb
    fallback_sources: List[str] = None
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    rate_limit: int = 100  # requests per minute
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    def __post_init__(self):
        if self.fallback_sources is None:
            self.fallback_sources = ["influxdb"]


class DataSource(ABC):
    """Abstract base class for market data sources"""

    @abstractmethod
    async def get_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Get price data for a symbol"""
        pass

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price for a symbol"""
        pass

    @abstractmethod
    async def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """Get price data for multiple symbols"""
        pass


class YahooFinanceSource(DataSource):
    """Yahoo Finance data source"""

    def __init__(self, config: MarketDataConfig):
        self.config = config

    async def get_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Get price data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)

            # Map interval strings
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "1d": "1d",
                "1wk": "1wk",
                "1mo": "1mo"
            }

            yf_interval = interval_map.get(interval, "1d")

            # For intraday data, limit to last 60 days
            if interval in ["1m", "5m", "15m", "30m"]:
                period = "60d"
            elif interval == "1h":
                period = "730d"  # 2 years max for 1h
            else:
                period = "max"

            hist = ticker.history(
                period=period,
                interval=yf_interval,
                start=start_date,
                end=end_date,
                prepost=False,
                threads=True
            )

            if hist.empty:
                return None

            # Clean and format data
            hist = hist.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adj_close'
            })

            # Add technical indicators
            hist['returns'] = hist['close'].pct_change()
            hist['log_returns'] = np.log(hist['close'] / hist['close'].shift(1))

            # Add moving averages
            hist['sma_20'] = hist['close'].rolling(window=20).mean()
            hist['sma_50'] = hist['close'].rolling(window=50).mean()
            hist['sma_200'] = hist['close'].rolling(window=200).mean()

            # Add volatility
            hist['volatility_20'] = hist['returns'].rolling(window=20).std() * np.sqrt(252)

            # Add ATR (Average True Range)
            high_low = hist['high'] - hist['low']
            high_close = np.abs(hist['high'] - hist['close'].shift(1))
            low_close = np.abs(hist['low'] - hist['close'].shift(1))
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            hist['atr'] = true_range.rolling(window=14).mean()

            # Get additional info
            info = ticker.info
            hist.attrs = {
                'symbol': symbol,
                'name': info.get('shortName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'Unknown')
            }

            return hist

        except Exception as e:
            logger.error(f"Failed to get price data for {symbol} from Yahoo Finance: {e}")
            return None

    async def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get the most recent price data
            hist = ticker.history(period="1d", interval="1d")

            if hist.empty:
                return None

            latest = hist.iloc[-1]

            return {
                'symbol': symbol,
                'price': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']),
                'change': float(latest['Close'] - latest['Open']),
                'change_percent': float((latest['Close'] - latest['Open']) / latest['Open'] * 100),
                'timestamp': hist.index[-1].to_pydatetime(),
                'name': info.get('shortName', symbol),
                'currency': info.get('currency', 'USD')
            }

        except Exception as e:
            logger.error(f"Failed to get latest price for {symbol} from Yahoo Finance: {e}")
            return None

    async def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols"""
        results = {}

        # Batch requests to improve performance
        batch_size = 50
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]

            # Use yfinance multi-ticker download
            tickers = yf.Tickers(batch)

            # Get historical data
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "1d": "1d",
                "1wk": "1wk",
                "1mo": "1mo"
            }

            yf_interval = interval_map.get(interval, "1d")

            try:
                hist_dict = tickers.history(
                    period="max",
                    interval=yf_interval,
                    start=start_date,
                    end=end_date,
                    prepost=False,
                    threads=True
                )

                # Process each symbol
                for symbol in batch:
                    if symbol in hist_dict.columns.get_level_values(0):
                        data = hist_dict[symbol]

                        if not data.empty:
                            # Clean column names
                            data.columns = data.columns.str.lower()

                            # Calculate basic indicators
                            data['returns'] = data['close'].pct_change()
                            data['volatility'] = data['returns'].rolling(window=20).std()

                            results[symbol] = data

            except Exception as e:
                logger.error(f"Failed to get batch data: {e}")

                # Fallback to individual requests
                for symbol in batch:
                    if symbol not in results:
                        data = await self.get_price_data(symbol, start_date, end_date, interval)
                        if data is not None:
                            results[symbol] = data

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)

        return results


class InfluxDBSource(DataSource):
    """InfluxDB data source"""

    def __init__(self, config: MarketDataConfig, influxdb_manager=None):
        self.config = config
        self.influxdb_manager = influxdb_manager

    async def get_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Get price data from InfluxDB"""
        if not self.influxdb_manager:
            logger.error("InfluxDB manager not configured")
            return None

        try:
            # Convert interval to InfluxDB aggregation window
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "1d": "1d",
                "1wk": "1w",
                "1mo": "1mo"
            }

            window = interval_map.get(interval, "1d")

            # Query InfluxDB
            query = f'''
            from(bucket: "market_data")
                |> range(start: {start_date.isoformat()}, stop: {end_date.isoformat()})
                |> filter(fn: (r) => r["_measurement"] == "stock_price")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
                |> filter(fn: (r) => r["_field"] == "close" or r["_field"] == "high" or r["_field"] == "low" or r["_field"] == "open" or r["_field"] == "volume")
                |> aggregateWindow(every: {window}, fn: last, createEmpty: false)
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''

            # Execute query (implementation depends on InfluxDB client)
            # This is a placeholder - actual implementation would use the InfluxDB query API
            logger.warning("InfluxDB query not fully implemented")
            return None

        except Exception as e:
            logger.error(f"Failed to get price data for {symbol} from InfluxDB: {e}")
            return None

    async def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price from InfluxDB"""
        # Implementation similar to get_price_data with latest() query
        logger.warning("InfluxDB latest price query not implemented")
        return None

    async def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols from InfluxDB"""
        # Implementation would query multiple symbols in one request
        logger.warning("InfluxDB multiple symbols query not implemented")
        return {}


class AlphaVantageSource(DataSource):
    """Alpha Vantage data source"""

    def __init__(self, config: MarketDataConfig):
        self.config = config
        self.base_url = "https://www.alphavantage.co/query"

    async def get_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Get price data from Alpha Vantage"""
        if not self.config.api_key:
            logger.error("Alpha Vantage API key not configured")
            return None

        try:
            # Map intervals to Alpha Vantage functions
            function_map = {
                "1m": "TIME_SERIES_INTRADAY",
                "5m": "TIME_SERIES_INTRADAY",
                "15m": "TIME_SERIES_INTRADAY",
                "30m": "TIME_SERIES_INTRADAY",
                "60m": "TIME_SERIES_INTRADAY",
                "1d": "TIME_SERIES_DAILY",
                "1wk": "TIME_SERIES_WEEKLY",
                "1mo": "TIME_SERIES_MONTHLY"
            }

            function = function_map.get(interval, "TIME_SERIES_DAILY")

            params = {
                "function": function,
                "symbol": symbol,
                "apikey": self.config.api_key,
                "outputsize": "full"
            }

            # Add interval for intraday data
            if interval in ["1m", "5m", "15m", "30m", "60m"]:
                params["interval"] = interval

            # Make request
            async with requests.Session() as session:
                response = await session.get(self.base_url, params=params, timeout=self.config.timeout)
                response.raise_for_status()
                data = response.json()

            # Parse response based on function
            if function == "TIME_SERIES_INTRADAY":
                key = f"Time Series ({interval})"
            elif function == "TIME_SERIES_DAILY":
                key = "Time Series (Daily)"
            elif function == "TIME_SERIES_WEEKLY":
                key = "Weekly Time Series"
            elif function == "TIME_SERIES_MONTHLY":
                key = "Monthly Time Series"
            else:
                key = "Time Series"

            if key not in data:
                logger.error(f"Invalid response from Alpha Vantage for {symbol}")
                return None

            # Convert to DataFrame
            df_data = []
            for date_str, values in data[key].items():
                df_data.append({
                    'date': pd.to_datetime(date_str),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })

            df = pd.DataFrame(df_data)
            df.set_index('date', inplace=True)

            # Filter by date range
            df = df[(df.index >= start_date) & (df.index <= end_date)]

            # Sort by date
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"Failed to get price data for {symbol} from Alpha Vantage: {e}")
            return None

    async def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price from Alpha Vantage"""
        # Use global quote endpoint
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.config.api_key
            }

            async with requests.Session() as session:
                response = await session.get(self.base_url, params=params, timeout=self.config.timeout)
                response.raise_for_status()
                data = response.json()

            if "Global Quote" not in data:
                return None

            quote = data["Global Quote"]

            return {
                'symbol': symbol,
                'price': float(quote['05. price']),
                'open': float(quote['02. open']),
                'high': float(quote['03. high']),
                'low': float(quote['04. low']),
                'volume': int(quote['06. volume']),
                'change': float(quote['09. change']),
                'change_percent': float(quote['10. change percent'].rstrip('%')),
                'timestamp': datetime.strptime(quote['07. latest trading day'], '%Y-%m-%d')
            }

        except Exception as e:
            logger.error(f"Failed to get latest price for {symbol} from Alpha Vantage: {e}")
            return None

    async def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols from Alpha Vantage"""
        results = {}

        # Alpha Vantage has strict rate limits, so process sequentially with delays
        for symbol in symbols:
            data = await self.get_price_data(symbol, start_date, end_date, interval)
            if data is not None:
                results[symbol] = data

            # Rate limiting delay
            await asyncio.sleep(12)  # Alpha Vantage free tier: 5 calls per minute

        return results


class MarketDataAdapter:
    """
    Unified market data adapter with support for multiple data sources,
    caching, and automatic fallback.
    """

    def __init__(self, config: MarketDataConfig, influxdb_manager=None):
        """
        Initialize market data adapter

        Args:
            config: Configuration for data sources
            influxdb_manager: InfluxDB manager instance (optional)
        """
        self.config = config
        self.cache = {} if config.cache_enabled else None
        self.cache_ttl = config.cache_ttl

        # Initialize data sources
        self.sources = {}

        # Primary source
        if config.primary_source == "yahoo":
            self.sources["yahoo"] = YahooFinanceSource(config)
        elif config.primary_source == "influxdb" and influxdb_manager:
            self.sources["influxdb"] = InfluxDBSource(config, influxdb_manager)
        elif config.primary_source == "alpha_vantage":
            self.sources["alpha_vantage"] = AlphaVantageSource(config)

        # Fallback sources
        for source_name in config.fallback_sources:
            if source_name not in self.sources:
                if source_name == "yahoo":
                    self.sources["yahoo"] = YahooFinanceSource(config)
                elif source_name == "influxdb" and influxdb_manager:
                    self.sources["influxdb"] = InfluxDBSource(config, influxdb_manager)
                elif source_name == "alpha_vantage":
                    self.sources["alpha_vantage"] = AlphaVantageSource(config)

        logger.info(f"Market data adapter initialized with sources: {list(self.sources.keys())}")

    async def get_price_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Get price data for a symbol with automatic fallback

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)

        Returns:
            DataFrame with price data or None if not found
        """
        # Check cache first
        cache_key = f"{symbol}_{start_date}_{end_date}_{interval}"
        if self.cache is not None and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cache_entry['data']

        # Try each source in order
        data = None
        source_used = None

        for source_name, source in self.sources.items():
            try:
                data = await source.get_price_data(symbol, start_date, end_date, interval)
                if data is not None and not data.empty:
                    source_used = source_name
                    break

            except Exception as e:
                logger.warning(f"Failed to get data from {source_name} for {symbol}: {e}")
                continue

        # Cache successful result
        if data is not None and self.cache is not None:
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now(),
                'source': source_used
            }

        if data is not None:
            logger.debug(f"Got {len(data)} rows of data for {symbol} from {source_used}")
        else:
            logger.warning(f"No data found for {symbol}")

        return data

    async def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price with automatic fallback"""
        for source_name, source in self.sources.items():
            try:
                price_data = await source.get_latest_price(symbol)
                if price_data is not None:
                    price_data['source'] = source_name
                    return price_data

            except Exception as e:
                logger.warning(f"Failed to get latest price from {source_name} for {symbol}: {e}")
                continue

        return None

    async def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols efficiently"""
        results = {}

        # Group symbols by preferred source
        source_priorities = list(self.sources.keys())

        # Try to use multi-symbol functionality if available
        if source_priorities:
            primary_source = self.sources[source_priorities[0]]

            try:
                multi_results = await primary_source.get_multiple_symbols(
                    symbols, start_date, end_date, interval
                )

                if multi_results:
                    results.update(multi_results)
                    logger.info(f"Got data for {len(multi_results)} symbols from {source_priorities[0]}")

                    # Get remaining symbols individually
                    remaining_symbols = [s for s in symbols if s not in results]

                    if remaining_symbols:
                        for symbol in remaining_symbols:
                            data = await self.get_price_data(symbol, start_date, end_date, interval)
                            if data is not None:
                                results[symbol] = data

                    return results

            except Exception as e:
                logger.warning(f"Multi-symbol query failed: {e}")

        # Fallback to individual requests
        for symbol in symbols:
            if symbol not in results:
                data = await self.get_price_data(symbol, start_date, end_date, interval)
                if data is not None:
                    results[symbol] = data

        return results

    async def get_technical_indicators(
        self,
        symbol: str,
        indicators: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Get technical indicators for a symbol

        Args:
            symbol: Stock symbol
            indicators: List of indicator names (SMA, EMA, RSI, MACD, BOLLINGER)
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with technical indicators
        """
        # Get price data first
        price_data = await self.get_price_data(symbol, start_date, end_date, "1d")

        if price_data is None or price_data.empty:
            return pd.DataFrame()

        indicators_df = pd.DataFrame(index=price_data.index)

        try:
            # Simple Moving Averages
            if any("SMA" in ind for ind in indicators):
                for ind in indicators:
                    if ind.startswith("SMA_"):
                        period = int(ind.split("_")[1])
                        indicators_df[f"SMA_{period}"] = price_data['close'].rolling(window=period).mean()

            # Exponential Moving Averages
            if any("EMA" in ind for ind in indicators):
                for ind in indicators:
                    if ind.startswith("EMA_"):
                        period = int(ind.split("_")[1])
                        indicators_df[f"EMA_{period}"] = price_data['close'].ewm(span=period).mean()

            # RSI
            if "RSI" in indicators:
                indicators_df["RSI"] = self._calculate_rsi(price_data['close'])

            # MACD
            if "MACD" in indicators:
                macd_line, signal_line, histogram = self._calculate_macd(price_data['close'])
                indicators_df["MACD"] = macd_line
                indicators_df["MACD_signal"] = signal_line
                indicators_df["MACD_histogram"] = histogram

            # Bollinger Bands
            if "BOLLINGER" in indicators:
                upper, middle, lower = self._calculate_bollinger_bands(price_data['close'])
                indicators_df["BB_upper"] = upper
                indicators_df["BB_middle"] = middle
                indicators_df["BB_lower"] = lower

            # Stochastic Oscillator
            if "STOCH" in indicators:
                stoch_k, stoch_d = self._calculate_stochastic(price_data)
                indicators_df["STOCH_K"] = stoch_k
                indicators_df["STOCH_D"] = stoch_d

            # ADX
            if "ADX" in indicators:
                adx = self._calculate_adx(price_data)
                indicators_df["ADX"] = adx

            # ATR
            if "ATR" in indicators:
                indicators_df["ATR"] = price_data.get('atr', self._calculate_atr(price_data))

        except Exception as e:
            logger.error(f"Failed to calculate indicators for {symbol}: {e}")

        return indicators_df

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD indicator"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2):
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    def _calculate_stochastic(self, data: pd.DataFrame, k_period: int = 14, d_period: int = 3):
        """Calculate Stochastic Oscillator"""
        low_min = data['low'].rolling(window=k_period).min()
        high_max = data['high'].rolling(window=k_period).max()

        k_percent = 100 * ((data['close'] - low_min) / (high_max - low_min))
        k_percent = k_percent.rolling(window=d_period).mean()
        d_percent = k_percent.rolling(window=d_period).mean()

        return k_percent, d_percent

    def _calculate_adx(self, data: pd.DataFrame, period: int = 14):
        """Calculate ADX indicator"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift(1))
        low_close = np.abs(data['low'] - data['close'].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        up = data['high'] - data['high'].shift(1)
        down = data['low'].shift(1) - data['low']

        plus_dm = np.where((up > down) & (up > 0), up, 0)
        minus_dm = np.where((down > up) & (down > 0), down, 0)

        plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr)

        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14):
        """Calculate ATR indicator"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift(1))
        low_close = np.abs(data['low'] - data['close'].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    def clear_cache(self):
        """Clear data cache"""
        if self.cache is not None:
            self.cache.clear()
            logger.info("Market data cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.cache is not None:
            return {
                'cache_size': len(self.cache),
                'cache_enabled': True,
                'cache_ttl': self.cache_ttl
            }
        else:
            return {
                'cache_size': 0,
                'cache_enabled': False,
                'cache_ttl': None
            }


# Global instance
_market_adapter = None


def get_market_adapter(config: Optional[MarketDataConfig] = None, influxdb_manager=None) -> MarketDataAdapter:
    """Get or create global market adapter instance"""
    global _market_adapter

    if _market_adapter is None or config is not None:
        if config is None:
            config = MarketDataConfig()
        _market_adapter = MarketDataAdapter(config, influxdb_manager)

    return _market_adapter


__all__ = [
    'MarketDataAdapter',
    'MarketDataConfig',
    'DataSource',
    'YahooFinanceSource',
    'AlphaVantageSource',
    'InfluxDBSource',
    'get_market_adapter'
]