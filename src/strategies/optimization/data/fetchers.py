"""Data fetchers for retrieving market data from various sources"""
import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any


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
