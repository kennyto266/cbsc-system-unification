"""Data fetchers for retrieving market data from various sources"""
import yfinance as yf
import pandas as pd
import requests
from typing import Optional, Dict, Any, List


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
            print(f"Error fetching {ticker}: {e}")
            return None


class HKEXFetcher:
    """Fetch market data from existing HKEX database"""

    def __init__(self):
        """Initialize HKEX fetcher with existing database connection"""
        self.db_connection = None  # Will use existing connection from src/api
        self.base_url = "http://localhost:3007/api/market"

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
            print(f"Error getting HKEX stock list: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting HKEX stock list: {e}")
            return None

    def fetch(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for HKEX stock

        Args:
            symbol: Stock symbol (e.g., '0700.HK')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            params = {
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date
            }
            response = requests.get(
                f"{self.base_url}/history",
                params=params,
                timeout=10
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
            print(f"Error fetching HKEX data for {symbol}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching HKEX data for {symbol}: {e}")
            return None
