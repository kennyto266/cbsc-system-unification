"""
Phase 1: Yahoo Finance API Integration for 10+ Year Historical Data
Professional-grade data infrastructure with robust error handling and caching
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp
from dataclasses import dataclass
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class DataConfig:
    """Configuration for data fetching"""
    cache_dir: str = "data/cache"
    parquet_dir: str = "data/parquet"
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.5
    chunk_size: int = 1000
    max_workers: int = 4

class ProfessionalYahooFinanceAdapter:
    """Professional Yahoo Finance API adapter with advanced features"""

    def __init__(self, config: DataConfig = None):
        self.config = config or DataConfig()
        self.session = requests.Session()
        self._setup_directories()

    def _setup_directories(self):
        """Setup required directories"""
        Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.parquet_dir).mkdir(parents=True, exist_ok=True)

    def fetch_long_term_data(self, symbol: str, period: str = "10y") -> pd.DataFrame:
        """
        Fetch long-term historical data with robust error handling

        Args:
            symbol: Stock symbol (e.g., "0700.HK")
            period: Time period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")

        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)

            # Fetch historical data
            data = ticker.history(period=period, auto_adjust=False, repair=True)

            if data.empty:
                logger.warning(f"No data found for symbol {symbol}")
                return pd.DataFrame()

            # Data cleaning and validation
            data = self._clean_and_validate_data(data, symbol)

            # Add metadata
            data['symbol'] = symbol
            data['data_source'] = 'yahoo_finance'
            data['fetch_timestamp'] = datetime.now()

            logger.info(f"Successfully fetched {len(data)} records for {symbol} ({period})")
            return data

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def _clean_and_validate_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Clean and validate the fetched data"""
        # Remove any rows with NaN values in critical columns
        critical_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        data = data.dropna(subset=critical_columns)

        # Validate price relationships
        invalid_prices = (data['High'] < data['Low']) | (data['High'] < data['Close']) | \
                        (data['Low'] > data['Close']) | (data['High'] < data['Open']) | \
                        (data['Low'] > data['Open'])

        if invalid_prices.any():
            logger.warning(f"Found {invalid_prices.sum()} invalid price records for {symbol}")
            data = data[~invalid_prices]

        # Validate volume
        data = data[data['Volume'] >= 0]

        # Reset index to make Date a column
        data = data.reset_index()

        # Ensure proper data types
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

        return data

    def fetch_multiple_symbols(self, symbols: List[str], period: str = "10y") -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols in parallel

        Args:
            symbols: List of stock symbols
            period: Time period for data

        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.fetch_long_term_data, symbol, period): symbol
                for symbol in symbols
            }

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if not data.empty:
                        results[symbol] = data
                    time.sleep(self.config.rate_limit_delay)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {e}")

        return results

    def save_to_parquet(self, data: pd.DataFrame, symbol: str, mode: str = 'yearly'):
        """
        Save data to parquet format with partitioning

        Args:
            data: DataFrame to save
            symbol: Stock symbol
            mode: Partitioning mode ('yearly', 'monthly', 'single')
        """
        if data.empty:
            return

        try:
            if mode == 'yearly':
                # Partition by year
                data['year'] = pd.to_datetime(data['Date']).dt.year
                for year, year_data in data.groupby('year'):
                    year_data = year_data.drop('year', axis=1)
                    file_path = Path(self.config.parquet_dir) / f"{symbol}_{year}.parquet"
                    year_data.to_parquet(file_path, index=False)

            elif mode == 'monthly':
                # Partition by year-month
                data['year_month'] = pd.to_datetime(data['Date']).dt.to_period('M')
                for period, period_data in data.groupby('year_month'):
                    period_data = period_data.drop('year_month', axis=1)
                    file_path = Path(self.config.parquet_dir) / f"{symbol}_{period}.parquet"
                    period_data.to_parquet(file_path, index=False)

            else:  # single file
                file_path = Path(self.config.parquet_dir) / f"{symbol}.parquet"
                data.to_parquet(file_path, index=False)

            logger.info(f"Successfully saved {len(data)} records for {symbol} to parquet")

        except Exception as e:
            logger.error(f"Error saving parquet for {symbol}: {e}")

    def load_from_parquet(self, symbol: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load data from parquet files

        Args:
            symbol: Stock symbol
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame with the requested data
        """
        try:
            parquet_dir = Path(self.config.parquet_dir)
            parquet_files = list(parquet_dir.glob(f"{symbol}_*.parquet"))

            if not parquet_files:
                logger.warning(f"No parquet files found for {symbol}")
                return pd.DataFrame()

            # Load all parquet files for the symbol
        dfs = []
            for file_path in sorted(parquet_files):
                try:
                    df = pd.read_parquet(file_path)
                    dfs.append(df)
                except Exception as e:
                    logger.warning(f"Error loading {file_path}: {e}")

            if not dfs:
                return pd.DataFrame()

            # Combine all dataframes
            combined_data = pd.concat(dfs, ignore_index=True)
            combined_data = combined_data.drop_duplicates(subset=['Date'])
            combined_data = combined_data.sort_values('Date')

            # Apply date filters
            if start_date:
                combined_data = combined_data[combined_data['Date'] >= start_date]
            if end_date:
                combined_data = combined_data[combined_data['Date'] <= end_date]

            logger.info(f"Loaded {len(combined_data)} records for {symbol} from parquet")
            return combined_data

        except Exception as e:
            logger.error(f"Error loading parquet for {symbol}: {e}")
            return pd.DataFrame()

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive symbol information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Extract relevant information
            symbol_info = {
                'symbol': symbol,
                'shortName': info.get('shortName', ''),
                'longName': info.get('longName', ''),
                'currency': info.get('currency', 'HKD'),
                'exchange': info.get('exchange', 'HKEX'),
                'market': info.get('market', ''),
                'country': info.get('country', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'marketCap': info.get('marketCap', 0),
                'sharesOutstanding': info.get('sharesOutstanding', 0),
                'bookValue': info.get('bookValue', 0),
                'priceToBook': info.get('priceToBook', 0),
                'forwardPE': info.get('forwardPE', 0),
                'trailingPE': info.get('trailingPE', 0),
                'dividendYield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'epsTrailingTwelveMonths': info.get('epsTrailingTwelveMonths', 0),
                'epsForward': info.get('epsForward', 0),
                'priceEpsCurrentYear': info.get('priceEpsCurrentYear', 0),
                'lastDividendValue': info.get('lastDividendValue', 0),
                'lastDividendDate': info.get('lastDividendDate', None),
                'exDividendDate': info.get('exDividendDate', None),
                'payoutRatio': info.get('payoutRatio', 0),
                'returnOnAssets': info.get('returnOnAssets', 0),
                'returnOnEquity': info.get('returnOnEquity', 0),
                'revenueGrowth': info.get('revenueGrowth', 0),
                'earningsGrowth': info.get('earningsGrowth', 0),
                'currentRatio': info.get('currentRatio', 0),
                'debtToEquity': info.get('debtToEquity', 0),
                'revenuePerShare': info.get('revenuePerShare', 0),
                'fiftyDayAverage': info.get('fiftyDayAverage', 0),
                'twoHundredDayAverage': info.get('twoHundredDayAverage', 0),
                'trailingAnnualDividendRate': info.get('trailingAnnualDividendRate', 0),
                'trailingAnnualDividendYield': info.get('trailingAnnualDividendYield', 0),
                'lastSplitFactor': info.get('lastSplitFactor', None),
                'lastSplitDate': info.get('lastSplitDate', None),
                'lastFiscalYearEnd': info.get('lastFiscalYearEnd', None),
                'nextFiscalYearEnd': info.get('nextFiscalYearEnd', None),
                'mostRecentQuarter': info.get('mostRecentQuarter', None),
                'enterpriseValue': info.get('enterpriseValue', 0),
                'profitMargins': info.get('profitMargins', 0),
                'operatingMargins': info.get('operatingMargins', 0),
                'grossMargins': info.get('grossMargins', 0),
                'ebitdaMargins': info.get('ebitdaMargins', 0),
                'operatingCashflow': info.get('operatingCashflow', 0),
                'revenueQuarterlyGrowth': info.get('revenueQuarterlyGrowth', 0),
                'earningsQuarterlyGrowth': info.get('earningsQuarterlyGrowth', 0),
                'sharesPercentSharesOut': info.get('sharesPercentSharesOut', 0),
                'heldPercentInstitutions': info.get('heldPercentInstitutions', 0),
                'heldPercentInsiders': info.get('heldPercentInsiders', 0),
                'shortRatio': info.get('shortRatio', 0),
                'shortPercentOfFloat': info.get('shortPercentOfFloat', 0),
                'lastCapGain': info.get('lastCapGain', 0),
                'quoteType': info.get('quoteType', ''),
                'validate_timestamp': datetime.now().isoformat()
            }

            return symbol_info

        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return {}

    def validate_data_quality(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Validate data quality and return quality metrics

        Args:
            data: DataFrame to validate
            symbol: Stock symbol

        Returns:
            Dictionary with quality metrics
        """
        if data.empty:
            return {'valid': False, 'errors': ['Empty data']}

        errors = []
        warnings = []

        # Check for missing values
        missing_data = data.isnull().sum()
        for col, missing_count in missing_data.items():
            if missing_count > 0:
                if col in ['Open', 'High', 'Low', 'Close']:
                    errors.append(f"Missing {missing_count} values in {col}")
                else:
                    warnings.append(f"Missing {missing_count} values in {col}")

        # Check for duplicate dates
        duplicate_dates = data.duplicated(subset=['Date']).sum()
        if duplicate_dates > 0:
            warnings.append(f"Found {duplicate_dates} duplicate dates")

        # Check for gaps in data
        if len(data) > 1:
            data_sorted = data.sort_values('Date')
            date_gaps = pd.date_range(
                start=data_sorted['Date'].min(),
                end=data_sorted['Date'].max(),
                freq='D'
            )
            expected_trading_days = len(date_gaps[date_gaps.dayofweek < 5])  # Weekdays only
            actual_days = len(data)

            if actual_days < expected_trading_days * 0.8:  # Less than 80% expected
                warnings.append(f"Data may have gaps: {actual_days} vs expected ~{expected_trading_days}")

        # Check for price anomalies
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in data.columns:
                price_anomalies = data[col] <= 0
                if price_anomalies.any():
                    errors.append(f"Found {price_anomalies.sum()} non-positive prices in {col}")

        # Check volume
        if 'Volume' in data.columns:
            volume_anomalies = data['Volume'] < 0
            if volume_anomalies.any():
                errors.append(f"Found {volume_anomalies.sum()} negative volume values")

        # Price consistency checks
        price_cols = ['Open', 'High', 'Low', 'Close']
        if all(col in data.columns for col in price_cols):
            invalid_high_low = data['High'] < data['Low']
            if invalid_high_low.any():
                errors.append(f"Found {invalid_high_low.sum()} cases where High < Low")

            invalid_range = (data['High'] < data['Open']) | (data['High'] < data['Close']) | \
                           (data['Low'] > data['Open']) | (data['Low'] > data['Close'])
            if invalid_range.any():
                warnings.append(f"Found {invalid_range.sum()} cases with invalid price ranges")

        quality_score = 100
        quality_score -= len(errors) * 10
        quality_score -= len(warnings) * 2

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'quality_score': max(0, quality_score),
            'total_records': len(data),
            'date_range': f"{data['Date'].min()} to {data['Date'].max()}" if not data.empty else None,
            'validation_timestamp': datetime.now().isoformat()
        }

# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    adapter = ProfessionalYahooFinanceAdapter()

    # Test with a Hong Kong stock
    symbol = "0700.HK"  # Tencent

    # Fetch 10-year data
    data = adapter.fetch_long_term_data(symbol, period="10y")
    print(f"Fetched {len(data)} records for {symbol}")

    if not data.empty:
        # Validate data quality
        quality_report = adapter.validate_data_quality(data, symbol)
        print(f"Data Quality Report: {quality_report}")

        # Save to parquet
        adapter.save_to_parquet(data, symbol, mode='yearly')

        # Get symbol information
        info = adapter.get_symbol_info(symbol)
        print(f"Symbol Info: {json.dumps(info, indent=2, default=str)}")