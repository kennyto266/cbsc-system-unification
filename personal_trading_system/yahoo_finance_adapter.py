#!/usr/bin/env python3
"""
Yahoo Finance Data Adapter
Optimized adapter for Yahoo Finance with long-term storage integration
"""

try:
    import yfinance as yf
    YAHOO_FINANCE_AVAILABLE = True
except ImportError:
    YAHOO_FINANCE_AVAILABLE = False
    yf = None
    print("Warning: yfinance not available. Install with: pip install yfinance")
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
import time
from pathlib import Path

from long_term_storage import LongTermDataStorage

logger = logging.getLogger(__name__)


class YahooFinanceAdapter:
    """
    Yahoo Finance data adapter with intelligent caching and long-term storage

    Features:
    - Intelligent data caching and retrieval
    - Long-term storage integration
    - Incremental updates support
    - Multi-symbol batch operations
    - Data quality validation
    - Rate limiting and error handling
    """

    def __init__(self, storage: Optional[LongTermDataStorage] = None, cache_ttl_hours: int = 24):
        """
        Initialize Yahoo Finance adapter

        Args:
            storage: LongTermDataStorage instance for persistent storage
            cache_ttl_hours: Cache time-to-live in hours
        """
        if not YAHOO_FINANCE_AVAILABLE:
            raise ImportError("yfinance is required. Install with: pip install yfinance")

        self.storage = storage or LongTermDataStorage()
        self.cache_ttl_hours = cache_ttl_hours
        try:
            self.session = yfinance.utils.get_yf_logger()
        except:
            self.session = None

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests

        logger.info("Yahoo Finance adapter initialized")

    def get_historical_data(
        self,
        symbol: str,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        use_cache: bool = True,
        force_update: bool = False
    ) -> pd.DataFrame:
        """
        Get historical data for a symbol with intelligent caching

        Args:
            symbol: Stock symbol (e.g., '0700.HK')
            start_date: Start date for data
            end_date: End date for data
            use_cache: Whether to use cached data
            force_update: Whether to force update from Yahoo Finance

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Convert dates
            start_date = pd.to_datetime(start_date).date()
            end_date = pd.to_datetime(end_date).date()

            logger.info(f"Getting historical data for {symbol} from {start_date} to {end_date}")

            # Try to load from storage first
            if use_cache and not force_update:
                cached_data = self.storage.load_historical_data(
                    symbol, start_date, end_date, "daily"
                )

                if len(cached_data) > 0:
                    # Check if cached data covers the requested range
                    cache_start = cached_data.index.min().date()
                    cache_end = cached_data.index.max().date()

                    if cache_start <= start_date and cache_end >= end_date:
                        logger.info(f"Using cached data for {symbol} ({len(cached_data)} records)")
                        return cached_data.loc[start_date:end_date]
                    elif len(cached_data) > 0:
                        logger.info(f"Partial cache available for {symbol}, fetching missing data")

            # Fetch from Yahoo Finance
            fresh_data = self._fetch_from_yahoo(symbol, start_date, end_date)

            if len(fresh_data) > 0:
                # Store in long-term storage
                try:
                    self.storage.store_historical_data(symbol, fresh_data, "daily", overwrite=False)
                    logger.info(f"Stored {len(fresh_data)} records for {symbol}")
                except Exception as e:
                    logger.warning(f"Failed to store data for {symbol}: {e}")

                return fresh_data
            else:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            # Return cached data as fallback
            if use_cache:
                cached_data = self.storage.load_historical_data(symbol, start_date, end_date, "daily")
                if len(cached_data) > 0:
                    logger.warning(f"Returning cached fallback data for {symbol}")
                    return cached_data
            return pd.DataFrame()

    def _fetch_from_yahoo(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Fetch data from Yahoo Finance with rate limiting and error handling
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        try:
            self.last_request_time = time.time()

            # Create ticker
            ticker = yf.Ticker(symbol)

            # Fetch historical data
            hist = ticker.history(start=start_date, end=end_date)

            if len(hist) == 0:
                logger.warning(f"No data returned from Yahoo Finance for {symbol}")
                return pd.DataFrame()

            # Standardize column names
            column_mapping = {
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adj_close',
                'Dividends': 'dividends',
                'Stock Splits': 'stock_splits'
            }

            # Keep only OHLCV columns for storage efficiency
            essential_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            available_columns = [col for col in essential_columns if col in hist.columns]

            if not available_columns:
                raise ValueError(f"Essential OHLCV columns not found for {symbol}")

            hist = hist[available_columns].copy()

            # Rename columns to lowercase
            hist = hist.rename(columns=column_mapping)

            # Clean data
            hist = self._clean_data(hist, symbol)

            logger.info(f"Fetched {len(hist)} records from Yahoo Finance for {symbol}")
            return hist

        except Exception as e:
            logger.error(f"Failed to fetch from Yahoo Finance for {symbol}: {e}")
            raise

    def _clean_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Clean and validate the data"""
        # Remove any rows with NaN values in essential columns
        essential_cols = ['open', 'high', 'low', 'close']
        data = data.dropna(subset=essential_cols)

        # Fill missing volume with 0
        if 'volume' in data.columns:
            data['volume'] = data['volume'].fillna(0)

        # Validate price relationships
        invalid_prices = (
            (data['high'] < data['open']) |
            (data['high'] < data['close']) |
            (data['high'] < data['low']) |
            (data['low'] > data['open']) |
            (data['low'] > data['close'])
        )

        if invalid_prices.any():
            logger.warning(f"Found {invalid_prices.sum()} invalid price records for {symbol}")
            # You could choose to remove these records or fix them
            # For now, we'll keep them but log the issue

        # Remove zero or negative prices
        price_filter = (data[['open', 'high', 'low', 'close']] > 0).all(axis=1)
        data = data[price_filter]

        # Convert to appropriate data types
        for col in ['open', 'high', 'low', 'close']:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

        if 'volume' in data.columns:
            data['volume'] = pd.to_numeric(data['volume'], errors='coerce').fillna(0).astype(int)

        return data

    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple symbols

        Args:
            symbols: List of stock symbols
            start_date: Start date for data
            end_date: End date for data
            use_cache: Whether to use cached data

        Returns:
            Dictionary of symbol -> DataFrame
        """
        results = {}

        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"Processing {symbol} ({i+1}/{len(symbols)})")
                data = self.get_historical_data(symbol, start_date, end_date, use_cache)
                results[symbol] = data

                # Small delay between symbols to be respectful to Yahoo Finance
                time.sleep(0.2)

            except Exception as e:
                logger.error(f"Failed to get data for {symbol}: {e}")
                results[symbol] = pd.DataFrame()

        return results

    def update_symbol_data(self, symbol: str, days_back: int = 30) -> bool:
        """
        Update a symbol's data with the most recent data

        Args:
            symbol: Stock symbol to update
            days_back: Number of days to look back for updates

        Returns:
            True if successful, False otherwise
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)

            # Get recent data (forcing refresh from Yahoo)
            recent_data = self.get_historical_data(
                symbol, start_date, end_date, use_cache=False, force_update=True
            )

            if len(recent_data) > 0:
                logger.info(f"Updated {symbol} with {len(recent_data)} recent records")
                return True
            else:
                logger.warning(f"No recent data available for {symbol}")
                return False

        except Exception as e:
            logger.error(f"Failed to update {symbol}: {e}")
            return False

    def get_available_data_range(self, symbol: str) -> Optional[Tuple[date, date]]:
        """
        Get the available data range for a symbol from storage

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (start_date, end_date) or None if no data available
        """
        try:
            data = self.storage.load_historical_data(symbol)
            if len(data) > 0:
                return data.index.min().date(), data.index.max().date()
            return None
        except Exception as e:
            logger.error(f"Failed to get data range for {symbol}: {e}")
            return None

    def get_storage_info(self) -> Dict:
        """Get storage information and statistics"""
        return self.storage.get_storage_statistics()

    def initialize_symbol(
        self,
        symbol: str,
        years_back: int = 10,
        force_update: bool = False
    ) -> bool:
        """
        Initialize a symbol with historical data

        Args:
            symbol: Stock symbol to initialize
            years_back: Number of years of historical data to fetch
            force_update: Whether to force re-download of existing data

        Returns:
            True if successful, False otherwise
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=years_back * 365)

            logger.info(f"Initializing {symbol} with {years_back} years of data")

            # Check existing data range
            existing_range = self.get_available_data_range(symbol)
            if existing_range and not force_update:
                existing_start, existing_end = existing_range
                logger.info(f"Symbol {symbol} already has data from {existing_start} to {existing_end}")

                # Only fetch missing data if needed
                if existing_start <= start_date and existing_end >= end_date:
                    logger.info(f"Symbol {symbol} already has complete data range")
                    return True

            # Fetch and store data
            data = self.get_historical_data(symbol, start_date, end_date, use_cache=False, force_update=True)

            success = len(data) > 0
            if success:
                logger.info(f"Successfully initialized {symbol} with {len(data)} records")
            else:
                logger.error(f"Failed to initialize {symbol}")

            return success

        except Exception as e:
            logger.error(f"Failed to initialize {symbol}: {e}")
            return False

    def batch_initialize_symbols(
        self,
        symbols: List[str],
        years_back: int = 10,
        force_update: bool = False
    ) -> Dict[str, bool]:
        """
        Initialize multiple symbols with historical data

        Args:
            symbols: List of stock symbols to initialize
            years_back: Number of years of historical data to fetch
            force_update: Whether to force re-download of existing data

        Returns:
            Dictionary of symbol -> success status
        """
        results = {}

        for i, symbol in enumerate(symbols):
            logger.info(f"Initializing {symbol} ({i+1}/{len(symbols)})")
            results[symbol] = self.initialize_symbol(symbol, years_back, force_update)

        success_count = sum(results.values())
        logger.info(f"Batch initialization complete: {success_count}/{len(symbols)} successful")

        return results