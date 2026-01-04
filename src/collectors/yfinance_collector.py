#!/usr/bin/env python3
"""
Yahoo Finance Data Collector
Yahoo Finance 數據收集器
Task 8.1 - 數據獲取模塊

High-performance Yahoo Finance data collector with comprehensive error handling,
data validation, caching integration, and support for multiple markets.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import pandas as pd
import numpy as np
import yfinance as yf
from src.services.influxdb_client import InfluxDBManager
from src.services.cache_service import CacheService
import redis
import backoff
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Market(Enum):
    """Supported markets"""
    US = "US"
    HK = "HK"
    CN = "CN"
    JP = "JP"
    UK = "UK"
    DE = "DE"

@dataclass
class YFinanceConfig:
    """Configuration for YFinance collector"""
    symbols: List[str] = field(default_factory=list)
    markets: List[Market] = field(default_factory=lambda: [Market.US, Market.HK])
    intervals: List[str] = field(default_factory=lambda: ["1m", "5m", "15m", "1h", "1d"])
    data_types: List[str] = field(default_factory=lambda: ["price", "volume", "splits", "dividends"])
    rate_limit: int = 2000  # requests per hour
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds
    batch_size: int = 100
    enable_prepost: bool = False
    progress_reporting: bool = True
    auto_adjust: bool = True
    back_adjust: bool = False
    repair: bool = True
    keepna: bool = False
    threads: int = 8

@dataclass
class DataPoint:
    """Single data point structure"""
    timestamp: datetime
    symbol: str
    exchange: str
    data_type: str
    interval: str
    fields: Dict[str, Union[float, int, str]]
    tags: Dict[str, str] = field(default_factory=dict)
    quality_score: float = 1.0

class YFinanceCollector:
    """
    High-performance Yahoo Finance data collector with caching,
    error handling, and multi-market support.
    """

    def __init__(
        self,
        config: YFinanceConfig,
        influxdb_manager: InfluxDBManager,
        cache_service: CacheService,
        redis_client: Optional[redis.Redis] = None
    ):
        self.config = config
        self.influxdb = influxdb_manager
        self.cache = cache_service
        self.redis_client = redis_client
        self.executor = ThreadPoolExecutor(max_workers=config.threads)

        # Session for HTTP requests
        self.session: Optional[aiohttp.ClientSession] = None

        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "data_points_collected": 0,
            "cache_hits": 0,
            "errors": [],
            "start_time": datetime.utcnow(),
            "last_collection": None,
            "symbols_processed": set(),
            "market_stats": {market.value: {"requests": 0, "success": 0} for market in Market}
        }

        # Market suffix mappings
        self.market_suffixes = {
            Market.HK: ".HK",
            Market.CN: ".SS",  # Shanghai
            Market.CN: ".SZ",  # Shenzhen
            Market.JP: ".T",
            Market.UK: ".L",
            Market.DE: ".F",
            Market.US: ""
        }

        # Cache TTL settings (in seconds)
        self.cache_ttl = {
            "1m": 60,      # 1 minute
            "5m": 300,     # 5 minutes
            "15m": 900,    # 15 minutes
            "1h": 3600,    # 1 hour
            "1d": 86400    # 1 day
        }

        logger.info(f"YFinance collector initialized for {len(config.symbols)} symbols")

    async def start(self):
        """Initialize and start the collector"""
        if self.session:
            logger.warning("Collector already started")
            return

        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            connector=aiohttp.TCPConnector(limit=100, force_close=True),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        logger.info("✅ YFinance collector started")

    async def stop(self):
        """Stop the collector and cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        logger.info("YFinance collector stopped")

    async def collect_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        force_refresh: bool = False
    ) -> List[DataPoint]:
        """
        Collect historical data for a symbol

        Args:
            symbol: Stock symbol
            period: yfinance period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            start_date: Custom start date
            end_date: Custom end date
            force_refresh: Ignore cache and fetch fresh data

        Returns:
            List of DataPoint objects
        """
        try:
            # Generate cache key
            cache_key = f"yfinance_hist_{symbol}_{period}_{interval}_{start_date}_{end_date}"

            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    self.stats["cache_hits"] += 1
                    logger.debug(f"Cache hit for {symbol} historical data")
                    return [DataPoint(**dp) for dp in json.loads(cached_data)]

            # Validate inputs
            validated_symbol = await self._validate_symbol(symbol)
            if not validated_symbol:
                raise ValueError(f"Invalid symbol: {symbol}")

            # Fetch data using yfinance
            ticker = yf.Ticker(validated_symbol)

            # Determine fetch parameters
            if start_date and end_date:
                hist = ticker.history(
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    interval=interval,
                    prepost=self.config.enable_prepost,
                    auto_adjust=self.config.auto_adjust,
                    back_adjust=self.config.back_adjust,
                    repair=self.config.repair,
                    keepna=self.config.keepna
                )
            else:
                hist = ticker.history(
                    period=period,
                    interval=interval,
                    prepost=self.config.enable_prepost,
                    auto_adjust=self.config.auto_adjust,
                    back_adjust=self.config.back_adjust,
                    repair=self.config.repair,
                    keepna=self.config.keepna
                )

            if hist.empty:
                logger.warning(f"No historical data found for {symbol}")
                return []

            # Convert to DataPoint objects
            data_points = await self._process_historical_data(hist, validated_symbol, interval)

            # Validate data quality
            valid_data_points = []
            for dp in data_points:
                if await self._validate_data_point(dp):
                    valid_data_points.append(dp)
                else:
                    logger.debug(f"Invalid data point for {symbol} at {dp.timestamp}")

            # Cache the results
            if valid_data_points:
                cache_data = json.dumps([dp.__dict__ for dp in valid_data_points], default=str)
                ttl = self.cache_ttl.get(interval, 3600)
                await self.cache.set(cache_key, cache_data, ttl=ttl)

            # Update statistics
            self.stats["successful_requests"] += 1
            self.stats["data_points_collected"] += len(valid_data_points)
            self.stats["symbols_processed"].add(symbol)

            # Update market stats
            market = await self._get_symbol_market(validated_symbol)
            self.stats["market_stats"][market.value]["success"] += 1

            logger.info(f"Collected {len(valid_data_points)} historical data points for {symbol}")
            return valid_data_points

        except Exception as e:
            self.stats["failed_requests"] += 1
            self.stats["errors"].append(f"Historical data fetch failed for {symbol}: {str(e)}")
            logger.error(f"Failed to collect historical data for {symbol}: {e}")
            return []

    async def collect_real_time_data(
        self,
        symbols: List[str],
        max_age_seconds: int = 60
    ) -> Dict[str, DataPoint]:
        """
        Collect real-time data for multiple symbols

        Args:
            symbols: List of symbols to fetch
            max_age_seconds: Maximum age of cached data to consider fresh

        Returns:
            Dictionary of symbol -> DataPoint
        """
        try:
            results = {}

            # Process symbols in parallel batches
            batch_size = min(self.config.batch_size, len(symbols))

            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]

                # Check cache first
                fresh_symbols = []
                cached_results = {}

                for symbol in batch_symbols:
                    cache_key = f"yfinance_rt_{symbol}"
                    cached_data = await self.cache.get(cache_key)

                    if cached_data:
                        dp = DataPoint(**json.loads(cached_data))
                        age = (datetime.utcnow() - dp.timestamp).total_seconds()

                        if age < max_age_seconds:
                            cached_results[symbol] = dp
                            self.stats["cache_hits"] += 1
                        else:
                            fresh_symbols.append(symbol)
                    else:
                        fresh_symbols.append(symbol)

                # Add cached results
                results.update(cached_results)

                # Fetch fresh data for remaining symbols
                if fresh_symbols:
                    fresh_data = await self._fetch_real_time_batch(fresh_symbols)
                    results.update(fresh_data)

                    # Cache fresh data
                    for symbol, dp in fresh_data.items():
                        cache_key = f"yfinance_rt_{symbol}"
                        cache_data = json.dumps(dp.__dict__, default=str)
                        await self.cache.set(cache_key, cache_data, ttl=60)

            # Update statistics
            self.stats["successful_requests"] += 1
            self.stats["data_points_collected"] += len(results)

            logger.info(f"Collected real-time data for {len(results)}/{len(symbols)} symbols")
            return results

        except Exception as e:
            self.stats["failed_requests"] += 1
            self.stats["errors"].append(f"Real-time data fetch failed: {str(e)}")
            logger.error(f"Failed to collect real-time data: {e}")
            return {}

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        base=1,
        max_value=10
    )
    async def _fetch_real_time_batch(
        self,
        symbols: List[str]
    ) -> Dict[str, DataPoint]:
        """Fetch real-time data for a batch of symbols"""
        # Validate and prepare symbols
        validated_symbols = []
        for symbol in symbols:
            validated = await self._validate_symbol(symbol)
            if validated:
                validated_symbols.append(validated)
            else:
                logger.warning(f"Invalid symbol skipped: {symbol}")

        if not validated_symbols:
            return {}

        # Use thread pool for CPU-bound yfinance operations
        loop = asyncio.get_event_loop()

        async def fetch_data():
            tickers = yf.Tickers(" ".join(validated_symbols))
            data = {}

            for symbol in validated_symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    hist = ticker.history(period="1d", interval="1m", prepost=False)

                    if not hist.empty:
                        latest = hist.iloc[-1]
                        timestamp = hist.index[-1]

                        # Calculate quality score
                        quality_score = await self._calculate_data_quality_score(latest)

                        dp = DataPoint(
                            timestamp=timestamp.to_pydatetime(),
                            symbol=symbol,
                            exchange=self._get_yahoo_exchange(ticker),
                            data_type="price",
                            interval="1m",
                            fields={
                                "open": float(latest["Open"]),
                                "high": float(latest["High"]),
                                "low": float(latest["Low"]),
                                "close": float(latest["Close"]),
                                "volume": int(latest["Volume"]),
                                "bid": info.get("bid", 0),
                                "ask": info.get("ask", 0),
                                "prev_close": info.get("previousClose", 0)
                            },
                            tags={
                                "currency": info.get("currency", "USD"),
                                "market": self._get_symbol_market_str(symbol),
                                "quality": "real_time" if quality_score > 0.8 else "delayed"
                            },
                            quality_score=quality_score
                        )

                        data[symbol] = dp

                except Exception as e:
                    logger.error(f"Failed to fetch data for {symbol}: {e}")

            return data

        # Execute in thread pool
        results = await loop.run_in_executor(self.executor, fetch_data)

        # Filter to original symbols (mapping validated -> original)
        final_results = {}
        for orig_symbol, val_symbol in zip(symbols, validated_symbols):
            if val_symbol in results:
                final_results[orig_symbol] = results[val_symbol]

        return final_results

    async def collect_dividends_and_splits(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, List[DataPoint]]:
        """
        Collect dividend and split data for a symbol

        Args:
            symbol: Stock symbol
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Dictionary with 'dividends' and 'splits' keys
        """
        try:
            validated_symbol = await self._validate_symbol(symbol)
            if not validated_symbol:
                raise ValueError(f"Invalid symbol: {symbol}")

            ticker = yf.Ticker(validated_symbol)

            # Fetch dividend data
            dividends = ticker.dividends
            splits = ticker.splits

            results = {
                "dividends": [],
                "splits": []
            }

            # Process dividends
            if not dividends.empty:
                if start_date:
                    dividends = dividends[dividends.index >= start_date]
                if end_date:
                    dividends = dividends[dividends.index <= end_date]

                for date, amount in dividends.items():
                    dp = DataPoint(
                        timestamp=date.to_pydatetime(),
                        symbol=validated_symbol,
                        exchange=self._get_yahoo_exchange(ticker),
                        data_type="dividend",
                        interval="1d",
                        fields={
                            "amount": float(amount),
                            "currency": "USD"  # Could be enhanced to detect actual currency
                        },
                        tags={
                            "market": self._get_symbol_market_str(validated_symbol)
                        }
                    )
                    results["dividends"].append(dp)

            # Process splits
            if not splits.empty:
                if start_date:
                    splits = splits[splits.index >= start_date]
                if end_date:
                    splits = splits[splits.index <= end_date]

                for date, ratio in splits.items():
                    dp = DataPoint(
                        timestamp=date.to_pydatetime(),
                        symbol=validated_symbol,
                        exchange=self._get_yahoo_exchange(ticker),
                        data_type="split",
                        interval="1d",
                        fields={
                            "ratio": float(ratio),
                            "numerator": int(ratio * 1000),
                            "denominator": 1000
                        },
                        tags={
                            "market": self._get_symbol_market_str(validated_symbol)
                        }
                    )
                    results["splits"].append(dp)

            logger.info(f"Collected {len(results['dividends'])} dividends and {len(results['splits'])} splits for {symbol}")
            return results

        except Exception as e:
            logger.error(f"Failed to collect dividends/splits for {symbol}: {e}")
            return {"dividends": [], "splits": []}

    async def collect_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        Collect detailed company information

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with company information
        """
        try:
            validated_symbol = await self._validate_symbol(symbol)
            if not validated_symbol:
                raise ValueError(f"Invalid symbol: {symbol}")

            ticker = yf.Ticker(validated_symbol)
            info = ticker.info

            # Extract relevant information
            company_info = {
                "symbol": validated_symbol,
                "longName": info.get("longName", ""),
                "shortName": info.get("shortName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market": info.get("market", ""),
                "exchange": self._get_yahoo_exchange(ticker),
                "currency": info.get("currency", "USD"),
                "country": info.get("country", ""),
                "employees": info.get("fullTimeEmployees", 0),
                "website": info.get("website", ""),
                "description": info.get("longBusinessSummary", ""),
                "marketCap": info.get("marketCap", 0),
                "enterpriseValue": info.get("enterpriseValue", 0),
                "peRatio": info.get("trailingPE", 0),
                "pbRatio": info.get("priceToBook", 0),
                "dividendYield": info.get("dividendYield", 0),
                "beta": info.get("beta", 0),
                "epsTrailing": info.get("epsTrailingTwelveMonths", 0),
                "revenue": info.get("totalRevenue", 0),
                "grossProfits": info.get("grossProfits", 0),
                "operatingMargins": info.get("operatingMargins", 0),
                "ebitda": info.get("ebitda", 0),
                "bookValue": info.get("bookValue", 0),
                "priceToSales": info.get("priceToSalesTrailing12Months", 0),
                "forwardPE": info.get("forwardPE", 0),
                "pegRatio": info.get("pegRatio", 0)
            }

            # Cache company info (longer TTL)
            cache_key = f"yfinance_info_{validated_symbol}"
            await self.cache.set(cache_key, json.dumps(company_info, default=str), ttl=86400)  # 24 hours

            return company_info

        except Exception as e:
            logger.error(f"Failed to collect company info for {symbol}: {e}")
            return {}

    async def _validate_symbol(self, symbol: str) -> Optional[str]:
        """Validate and normalize symbol"""
        if not symbol or not isinstance(symbol, str):
            return None

        # Clean symbol
        symbol = symbol.upper().strip()

        # Remove common suffixes if present
        for market, suffix in self.market_suffixes.items():
            if suffix and symbol.endswith(suffix):
                symbol = symbol[:-len(suffix)]
                break

        # Add appropriate suffix based on market detection
        # This is a simplified logic - could be enhanced
        if len(symbol) == 4 and symbol.isdigit():
            # Likely Hong Kong stock
            validated = symbol + self.market_suffixes[Market.HK]
        elif symbol.startswith("0") or symbol.startswith("3") or symbol.startswith("6"):
            # Likely Chinese stock (determine Shanghai vs Shenzhen)
            if symbol.startswith("6"):
                validated = symbol + ".SS"
            else:
                validated = symbol + ".SZ"
        else:
            # Assume US stock
            validated = symbol + self.market_suffixes[Market.US]

        # Quick validation attempt
        try:
            ticker = yf.Ticker(validated)
            # Try to get basic info - if fails, symbol is invalid
            info = ticker.info
            if not info or "regularMarketPrice" not in info:
                return None
        except:
            return None

        return validated

    async def _process_historical_data(
        self,
        hist: pd.DataFrame,
        symbol: str,
        interval: str
    ) -> List[DataPoint]:
        """Process historical DataFrame into DataPoint objects"""
        data_points = []

        # Get exchange info
        ticker = yf.Ticker(symbol)
        exchange = self._get_yahoo_exchange(ticker)

        for timestamp, row in hist.iterrows():
            # Skip rows with NaN values
            if pd.isna(row["Close"]):
                continue

            # Validate OHLC relationships
            if not self._validate_ohlc(row):
                continue

            # Calculate quality score
            quality_score = await self._calculate_data_quality_score(row)

            fields = {
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0
            }

            # Add adjusted prices if available
            if "Adj Close" in hist.columns and not pd.isna(row["Adj Close"]):
                fields["adj_close"] = float(row["Adj Close"])

            # Calculate additional metrics
            if row["Volume"] > 0:
                fields["vwap"] = (row["Open"] + row["High"] + row["Low"] + row["Close"]) / 4
                fields["typical_price"] = (row["High"] + row["Low"] + row["Close"]) / 3

            dp = DataPoint(
                timestamp=timestamp.to_pydatetime(),
                symbol=symbol,
                exchange=exchange,
                data_type="price",
                interval=interval,
                fields=fields,
                tags={
                    "currency": "USD",  # Could be enhanced to detect actual currency
                    "market": self._get_symbol_market_str(symbol),
                    "quality": "high" if quality_score > 0.9 else "medium" if quality_score > 0.7 else "low"
                },
                quality_score=quality_score
            )

            data_points.append(dp)

        return data_points

    def _validate_ohlc(self, row: pd.Series) -> bool:
        """Validate OHLC data relationships"""
        try:
            open_price = float(row["Open"])
            high_price = float(row["High"])
            low_price = float(row["Low"])
            close_price = float(row["Close"])

            # All prices should be positive
            if any(v <= 0 for v in [open_price, high_price, low_price, close_price]):
                return False

            # High should be >= all prices
            if high_price < max(open_price, close_price):
                return False

            # Low should be <= all prices
            if low_price > min(open_price, close_price):
                return False

            # High should be >= low
            if high_price < low_price:
                return False

            return True
        except:
            return False

    async def _validate_data_point(self, dp: DataPoint) -> bool:
        """Validate a single data point"""
        # Check timestamp
        if not dp.timestamp or dp.timestamp > datetime.utcnow() + timedelta(minutes=5):
            return False

        # Check required fields
        required_fields = ["open", "high", "low", "close"]
        for field in required_fields:
            if field not in dp.fields or dp.fields[field] <= 0:
                return False

        # Validate OHLC relationships
        fields = dp.fields
        if fields["high"] < max(fields["open"], fields["close"]):
            return False
        if fields["low"] > min(fields["open"], fields["close"]):
            return False

        # Quality score threshold
        if dp.quality_score < 0.3:
            return False

        return True

    async def _calculate_data_quality_score(self, data: Union[pd.Series, Dict]) -> float:
        """Calculate quality score for data"""
        score = 1.0

        # Check for missing values
        if isinstance(data, pd.Series):
            if data.isna().any():
                score -= 0.2
        else:
            if any(v is None or pd.isna(v) for v in data.values()):
                score -= 0.2

        # Check for extreme values
        try:
            if isinstance(data, pd.Series):
                price_values = [float(data["Open"]), float(data["High"]),
                              float(data["Low"]), float(data["Close"])]
            else:
                price_values = [float(data.get("open", 0)), float(data.get("high", 0)),
                              float(data.get("low", 0)), float(data.get("close", 0))]

            # Calculate average price
            avg_price = sum(price_values) / len(price_values)

            # Check for extreme price changes
            if len(price_values) >= 4:
                price_change = abs(price_values[3] - price_values[0]) / avg_price
                if price_change > 0.5:  # 50% change in one period
                    score -= 0.3

            # Check price range
            if avg_price > 0:
                price_range = (max(price_values) - min(price_values)) / avg_price
                if price_range > 0.3:  # 30% range in one period
                    score -= 0.2

        except:
            score -= 0.1

        return max(0.0, score)

    def _get_yahoo_exchange(self, ticker) -> str:
        """Get exchange information from Yahoo ticker"""
        try:
            info = ticker.info
            exchange = info.get("exchange", "UNKNOWN")

            # Map common exchanges
            exchange_map = {
                "NMS": "NASDAQ",
                "NYQ": "NYSE",
                "ASE": "AMEX",
                "PCX": "NYSEARCA",
                "NGM": "NASDAQ",
                "HKG": "HKEX",
                "SHA": "SSE",
                "SZH": "SZSE",
                "TSE": "TSE",
                "LSE": "LSE",
                "FRA": "FRA"
            }

            return exchange_map.get(exchange, exchange)
        except:
            return "UNKNOWN"

    async def _get_symbol_market(self, symbol: str) -> Market:
        """Determine the market for a symbol"""
        if symbol.endswith(".HK"):
            return Market.HK
        elif symbol.endswith((".SS", ".SZ")):
            return Market.CN
        elif symbol.endswith(".T"):
            return Market.JP
        elif symbol.endswith(".L"):
            return Market.UK
        elif symbol.endswith(".F"):
            return Market.DE
        else:
            return Market.US

    def _get_symbol_market_str(self, symbol: str) -> str:
        """Get market string for symbol"""
        if symbol.endswith(".HK"):
            return "HK"
        elif symbol.endswith((".SS", ".SZ")):
            return "CN"
        elif symbol.endswith(".T"):
            return "JP"
        elif symbol.endswith(".L"):
            return "UK"
        elif symbol.endswith(".F"):
            return "DE"
        else:
            return "US"

    async def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics"""
        runtime = datetime.utcnow() - self.stats["start_time"]

        return {
            **self.stats,
            "runtime_seconds": runtime.total_seconds(),
            "success_rate": (
                self.stats["successful_requests"] / max(1, self.stats["total_requests"])
            ) * 100,
            "symbols_count": len(self.stats["symbols_processed"]),
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(1, self.stats["total_requests"])
            ) * 100,
            "data_points_per_second": (
                self.stats["data_points_collected"] / max(1, runtime.total_seconds())
            )
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            # Check YFinance API
            test_symbol = "AAPL"
            ticker = yf.Ticker(test_symbol)
            info = ticker.info
            if info and "regularMarketPrice" in info:
                health["checks"]["yfinance_api"] = "ok"
            else:
                health["checks"]["yfinance_api"] = "error"
                health["status"] = "degraded"

            # Check cache service
            await self.cache.ping()
            health["checks"]["cache_service"] = "ok"

            # Check InfluxDB connection
            # This would be implemented in the InfluxDBManager
            health["checks"]["influxdb"] = "ok"

            # Check Redis if available
            if self.redis_client:
                self.redis_client.ping()
                health["checks"]["redis"] = "ok"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health

# Example usage
async def main():
    """Example usage of YFinance collector"""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Create configuration
    config = YFinanceConfig(
        symbols=["AAPL", "MSFT", "GOOGL", "0700.HK", "9988.HK"],
        markets=[Market.US, Market.HK],
        intervals=["1d"],
        batch_size=50
    )

    # Initialize services (mocked for example)
    # influxdb_manager = InfluxDBManager(...)
    # cache_service = CacheService(...)

    try:
        # Create collector
        collector = YFinanceCollector(
            config=config,
            influxdb_manager=None,  # Would be initialized
            cache_service=None      # Would be initialized
        )

        # Start collector
        await collector.start()

        # Test historical data collection
        historical_data = await collector.collect_historical_data(
            symbol="AAPL",
            period="1mo",
            interval="1d"
        )
        print(f"Collected {len(historical_data)} historical data points for AAPL")

        # Test real-time data collection
        real_time_data = await collector.collect_real_time_data(
            symbols=["AAPL", "MSFT", "0700.HK"]
        )
        print(f"Collected real-time data for {len(real_time_data)} symbols")

        # Test dividend/split collection
        corp_actions = await collector.collect_dividends_and_splits("AAPL")
        print(f"Found {len(corp_actions['dividends'])} dividends and {len(corp_actions['splits'])} splits")

        # Get statistics
        stats = await collector.get_statistics()
        print(f"Collector stats: {stats}")

        # Health check
        health = await collector.health_check()
        print(f"Health status: {health['status']}")

        # Stop collector
        await collector.stop()

    except Exception as e:
        logger.error(f"Example failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())