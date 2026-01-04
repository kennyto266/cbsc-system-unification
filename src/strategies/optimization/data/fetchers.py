"""Data fetchers for retrieving market data from various sources"""
import logging
import re
from datetime import datetime

import pandas as pd
import requests
import yfinance as yf
from typing import Optional, Dict, Any, List

from ..config import OptimizationConfig

# Setup logger
logger = logging.getLogger(__name__)


class YahooFinanceFetcher:
    """Fetch stock data from Yahoo Finance API"""

    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com"

    def fetch(self, ticker: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a ticker

        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)

            if data.empty:
                return None

            # Standardize column names
            data.columns = [col.lower().replace(' ', '_') for col in data.columns]

            return data

        except Exception as e:
            logger.error(f"Error fetching {ticker}: {e}")
            return None


class HKEXFetcher:
    """Fetch market data from existing HKEX database"""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize HKEX fetcher with configurable base URL

        Args:
            base_url: Optional base URL for HKEX API (uses config default if not provided)
        """
        self.db_connection = None  # Will use existing connection from src/api
        self.base_url = base_url or OptimizationConfig.get_hkex_base_url()

    @staticmethod
    def _validate_date_format(date_str: str) -> bool:
        """
        Validate date string is in YYYY-MM-DD format

        Args:
            date_str: Date string to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False

        try:
            datetime.strptime(date_str, OptimizationConfig.DATE_FORMAT)
            return True
        except ValueError:
            return False

    @staticmethod
    def _validate_symbol(symbol: str) -> bool:
        """
        Validate symbol is non-empty string

        Args:
            symbol: Stock symbol to validate

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If symbol is invalid
        """
        if not symbol or not isinstance(symbol, str):
            return False
        return len(symbol.strip()) > 0

    def get_stock_list(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of available stocks from HKEX

        Returns:
            List of stock dictionaries or None if failed
        """
        try:
            # Try to use existing API endpoint first
            response = requests.get(f"{self.base_url}/stocks", timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('stocks', data.get('data', []))

            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting HKEX stock list: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting HKEX stock list: {e}")
            return None

    def fetch(self, symbol: str, start: str, end: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for HKEX stock

        Args:
            symbol: Stock symbol (e.g., '0700.HK')
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if failed

        Raises:
            ValueError: If symbol or dates are invalid
        """
        # Input validation
        if not self._validate_symbol(symbol):
            raise ValueError(f"Invalid symbol: '{symbol}'. Must be non-empty string.")

        if not self._validate_date_format(start):
            raise ValueError(
                f"Invalid start date format: '{start}'. "
                f"Expected format: {OptimizationConfig.DATE_FORMAT}"
            )

        if not self._validate_date_format(end):
            raise ValueError(
                f"Invalid end date format: '{end}'. "
                f"Expected format: {OptimizationConfig.DATE_FORMAT}"
            )

        try:
            params = {
                'symbol': symbol,
                'start': start,
                'end': end
            }
            response = requests.get(
                f"{self.base_url}/history",
                params=params,
                timeout=OptimizationConfig.REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                # Handle different response formats
                if 'data' in data:
                    records = data['data']
                elif 'prices' in data:
                    records = data['prices']
                else:
                    records = data

                if not records:
                    return None

                df = pd.DataFrame(records)

                # Standardize column names and format
                if 'timestamp' in df.columns:
                    df['date'] = pd.to_datetime(df['timestamp'])
                elif 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                elif 'time' in df.columns:
                    df['date'] = pd.to_datetime(df['time'])

                if 'date' in df.columns:
                    df.set_index('date', inplace=True)

                return df

            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching HKEX data for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching HKEX data for {symbol}: {e}")
            return None
