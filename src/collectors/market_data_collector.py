#!/usr/bin/env python3
"""
Market Data Collector
市場數據收集器
Phase 1.2 - 時序數據庫配置

High-performance market data collector with support for multiple data sources,
real-time streaming, and automatic data validation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
import aiohttp
import aiofiles
import json
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import yfinance as yf
from src.services.influxdb_client import InfluxDBManager, InfluxDBConfig
import redis
import backoff
from tenacity import retry, stop_after_attempt, wait_exponential
import schedule
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataSourceConfig:
    """Configuration for market data source"""
    name: str
    enabled: bool = True
    rate_limit: int = 100  # requests per minute
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    priority: int = 1  # lower number = higher priority
    api_key: Optional[str] = None
    base_url: Optional[str] = None

@dataclass
class CollectorConfig:
    """Market data collector configuration"""
    symbols: List[str] = field(default_factory=list)
    exchanges: List[str] = field(default_factory=lambda: ["NASDAQ", "NYSE"])
    data_sources: Dict[str, DataSourceConfig] = field(default_factory=dict)
    collection_interval: int = 60  # seconds
    market_hours_only: bool = True
    batch_size: int = 100
    validation_enabled: bool = True
    cache_ttl: int = 60  # seconds

class MarketDataCollector:
    """
    High-performance market data collector supporting multiple sources
    and real-time streaming capabilities.
    """

    def __init__(
        self,
        config: CollectorConfig,
        influxdb_manager: InfluxDBManager,
        redis_client: Optional[redis.Redis] = None
    ):
        self.config = config
        self.influxdb = influxdb_manager
        self.redis_client = redis_client
        self.session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            "collections": 0,
            "successful_writes": 0,
            "failed_writes": 0,
            "data_points": 0,
            "last_collection": None,
            "errors": []
        }

        # Initialize data sources
        self._init_data_sources()

        logger.info(f"Market data collector initialized with {len(config.symbols)} symbols")

    def _init_data_sources(self):
        """Initialize default data sources"""
        default_sources = {
            "yahoo": DataSourceConfig(
                name="yahoo",
                enabled=True,
                rate_limit=2000,
                timeout=10,
                priority=1
            ),
            "alpha_vantage": DataSourceConfig(
                name="alpha_vantage",
                enabled=False,  # Requires API key
                rate_limit=5,
                timeout=30,
                priority=2,
                base_url="https://www.alphavantage.co/query"
            ),
            "polygon": DataSourceConfig(
                name="polygon",
                enabled=False,  # Requires API key
                rate_limit=5,
                timeout=30,
                priority=2,
                base_url="https://api.polygon.io"
            )
        }

        # Merge with user configuration
        self.data_sources = {**default_sources, **self.config.data_sources}

    async def start(self):
        """Start the data collector"""
        if self._running:
            logger.warning("Collector is already running")
            return

        self._running = True
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        )

        # Start collection task
        self._collection_task = asyncio.create_task(self._collection_loop())

        logger.info("✅ Market data collector started")

    async def stop(self):
        """Stop the data collector"""
        if not self._running:
            return

        self._running = False

        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.close()

        logger.info("Market data collector stopped")

    async def _collection_loop(self):
        """Main collection loop"""
        logger.info("Starting market data collection loop")

        while self._running:
            try:
                # Check if market is open
                if self.config.market_hours_only and not self._is_market_open():
                    logger.debug("Market is closed, waiting...")
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue

                # Collect data for all symbols
                await self._collect_all_symbols()

                # Wait for next collection
                await asyncio.sleep(self.config.collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                self.stats["errors"].append(str(e))
                await asyncio.sleep(60)  # Wait 1 minute on error

    def _is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        # Simple check: Monday-Friday, 9:30 AM - 4:00 PM EST
        if now.weekday() >= 5:  # Weekend
            return False

        # Convert to EST (simplified)
        est_time = now - timedelta(hours=5)
        market_open = est_time.replace(hour=9, minute=30, second=0)
        market_close = est_time.replace(hour=16, minute=0, second=0)

        return market_open <= est_time <= market_close

    async def _collect_all_symbols(self):
        """Collect data for all configured symbols"""
        start_time = time.time()
        batch_data = []

        for symbol in self.config.symbols:
            try:
                # Get data from best available source
                data = await self._get_symbol_data(symbol)
                if data:
                    batch_data.extend(data)

                # Rate limiting
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Failed to collect data for {symbol}: {e}")
                self.stats["errors"].append(f"{symbol}: {str(e)}")

        # Write batch to InfluxDB
        if batch_data:
            success = await self.influxdb.write_market_data(
                batch_data,
                measurement="stock_price",
                bucket="market_data_raw"
            )

            if success:
                self.stats["successful_writes"] += 1
                self.stats["data_points"] += len(batch_data)
                logger.debug(f"Successfully wrote {len(batch_data)} data points")
            else:
                self.stats["failed_writes"] += 1

        # Update statistics
        self.stats["collections"] += 1
        self.stats["last_collection"] = datetime.utcnow().isoformat()

        collection_time = time.time() - start_time
        logger.info(f"Collection completed in {collection_time:.2f}s - {len(batch_data)} data points")

    async def _get_symbol_data(self, symbol: str) -> Optional[List[Dict]]:
        """Get data for a symbol from the best available source"""
        # Try sources in priority order
        sorted_sources = sorted(
            [s for s in self.data_sources.values() if s.enabled],
            key=lambda x: x.priority
        )

        for source in sorted_sources:
            try:
                if source.name == "yahoo":
                    data = await self._fetch_from_yahoo(symbol)
                elif source.name == "alpha_vantage":
                    data = await self._fetch_from_alpha_vantage(symbol, source.api_key)
                elif source.name == "polygon":
                    data = await self._fetch_from_polygon(symbol, source.api_key)
                else:
                    continue

                if data and self._validate_data(data):
                    logger.debug(f"Got data for {symbol} from {source.name}")
                    return data

            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} from {source.name}: {e}")
                continue

        return None

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def _fetch_from_yahoo(self, symbol: str) -> Optional[List[Dict]]:
        """Fetch data from Yahoo Finance"""
        try:
            # Use yfinance library
            ticker = yf.Ticker(symbol)

            # Get historical data (last 1 day with 1-minute interval)
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)

            hist = ticker.history(
                start=start_time.strftime("%Y-%m-%d"),
                end=end_time.strftime("%Y-%m-%d"),
                interval="1m",
                prepost=False
            )

            if hist.empty:
                return None

            # Convert to InfluxDB format
            data_points = []
            for timestamp, row in hist.iterrows():
                if pd.isna(row["Close"]):
                    continue

                # Validate OHLC relationships
                if not self._validate_ohlc(row):
                    continue

                data_point = {
                    "timestamp": timestamp.to_pydatetime(),
                    "tags": {
                        "symbol": symbol,
                        "exchange": self._get_yahoo_exchange(ticker),
                        "currency": "USD",
                        "data_source": "yahoo",
                        "quality": "real_time"
                    },
                    "fields": {
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0
                    }
                }

                # Calculate VWAP if we have volume
                if row["Volume"] > 0:
                    vwap = (row["Open"] + row["High"] + row["Low"] + row["Close"]) / 4
                    data_point["fields"]["vwap"] = float(vwap)

                data_points.append(data_point)

            return data_points

        except Exception as e:
            logger.error(f"Yahoo Finance fetch error for {symbol}: {e}")
            return None

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
                "NGM": "NASDAQ"
            }

            return exchange_map.get(exchange, exchange)
        except:
            return "UNKNOWN"

    async def _fetch_from_alpha_vantage(self, symbol: str, api_key: str) -> Optional[List[Dict]]:
        """Fetch data from Alpha Vantage"""
        if not api_key:
            return None

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": "1min",
            "outputsize": "compact",
            "apikey": api_key
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                time_series = data.get("Time Series (1min)", {})

                if not time_series:
                    return None

                data_points = []
                for timestamp_str, values in time_series.items():
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                    # Parse values
                    open_price = float(values["1. open"])
                    high_price = float(values["2. high"])
                    low_price = float(values["3. low"])
                    close_price = float(values["4. close"])
                    volume = int(values["5. volume"])

                    # Validate OHLC
                    if not self._validate_ohlc_values(open_price, high_price, low_price, close_price):
                        continue

                    data_point = {
                        "timestamp": timestamp,
                        "tags": {
                            "symbol": symbol,
                            "exchange": "UNKNOWN",  # Alpha Vantage doesn't provide exchange
                            "currency": "USD",
                            "data_source": "alpha_vantage",
                            "quality": "real_time"
                        },
                        "fields": {
                            "open": open_price,
                            "high": high_price,
                            "low": low_price,
                            "close": close_price,
                            "volume": volume
                        }
                    }

                    data_points.append(data_point)

                return data_points

        except Exception as e:
            logger.error(f"Alpha Vantage fetch error for {symbol}: {e}")
            return None

    async def _fetch_from_polygon(self, symbol: str, api_key: str) -> Optional[List[Dict]]:
        """Fetch data from Polygon.io"""
        if not api_key:
            return None

        # Polygon requires symbol with exchange suffix (e.g., AAPL:NASDAQ)
        # For simplicity, we'll try common exchanges
        exchanges = ["XNAS", "XNYS"]

        for exchange in exchanges:
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}:{exchange}/range/1/minute/{self._yesterday_date()}/{self._today_date()}"
            params = {
                "apikey": api_key,
                "unadjusted": "true"
            }

            try:
                async with self.session.get(url, params=params) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()
                    results = data.get("results", [])

                    if not results:
                        continue

                    data_points = []
                    for result in results:
                        timestamp = datetime.fromtimestamp(result["t"] / 1000)

                        data_point = {
                            "timestamp": timestamp,
                            "tags": {
                                "symbol": symbol,
                                "exchange": "NASDAQ" if exchange == "XNAS" else "NYSE",
                                "currency": "USD",
                                "data_source": "polygon",
                                "quality": "real_time"
                            },
                            "fields": {
                                "open": float(result["o"]),
                                "high": float(result["h"]),
                                "low": float(result["l"]),
                                "close": float(result["c"]),
                                "volume": int(result["v"])
                            }
                        }

                        # Validate OHLC
                        if self._validate_ohlc({
                            "Open": result["o"],
                            "High": result["h"],
                            "Low": result["l"],
                            "Close": result["c"]
                        }):
                            data_points.append(data_point)

                    if data_points:
                        return data_points

            except Exception as e:
                logger.debug(f"Polygon fetch error for {symbol} on {exchange}: {e}")
                continue

        return None

    def _yesterday_date(self) -> str:
        """Get yesterday's date in YYYY-MM-DD format"""
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    def _today_date(self) -> str:
        """Get today's date in YYYY-MM-DD format"""
        return datetime.now().strftime("%Y-%m-%d")

    def _validate_data(self, data: List[Dict]) -> bool:
        """Validate collected data"""
        if not data:
            return False

        # Check for required fields
        required_fields = ["timestamp", "tags", "fields"]
        for point in data[:5]:  # Check first 5 points
            if not all(field in point for field in required_fields):
                return False

            required_tag_fields = ["symbol", "exchange"]
            if not all(tag in point["tags"] for tag in required_tag_fields):
                return False

            required_data_fields = ["open", "high", "low", "close", "volume"]
            if not all(field in point["fields"] for field in required_data_fields):
                return False

        return True

    def _validate_ohlc(self, row) -> bool:
        """Validate OHLC data relationships"""
        try:
            open_price = float(row["Open"])
            high_price = float(row["High"])
            low_price = float(row["Low"])
            close_price = float(row["Close"])

            return self._validate_ohlc_values(open_price, high_price, low_price, close_price)
        except:
            return False

    def _validate_ohlc_values(self, open_price: float, high_price: float,
                             low_price: float, close_price: float) -> bool:
        """Validate OHLC value relationships"""
        # All values should be positive
        if any(v <= 0 for v in [open_price, high_price, low_price, close_price]):
            return False

        # High should be >= others
        if high_price < max(open_price, close_price):
            return False

        # Low should be <= others
        if low_price > min(open_price, close_price):
            return False

        # High should be >= low
        if high_price < low_price:
            return False

        return True

    async def collect_technical_indicators(self, symbol: str, indicators: List[str]) -> Dict:
        """Collect technical indicators for a symbol"""
        try:
            # Get historical data for technical analysis
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y", interval="1d")

            if hist.empty:
                return {}

            indicator_results = {}

            # Simple Moving Averages
            if "SMA" in indicators:
                for period in [20, 50, 200]:
                    sma = hist["Close"].rolling(window=period).mean()
                    if not sma.empty:
                        latest_sma = sma.iloc[-1]
                        if not pd.isna(latest_sma):
                            indicator_results[f"SMA_{period}"] = {
                                "value": float(latest_sma),
                                "timestamp": hist.index[-1].to_pydatetime(),
                                "signal": "neutral"
                            }

            # Relative Strength Index
            if "RSI" in indicators:
                rsi = self._calculate_rsi(hist["Close"], 14)
                if not pd.isna(rsi):
                    signal = "neutral"
                    if rsi < 30:
                        signal = "oversold"
                    elif rsi > 70:
                        signal = "overbought"

                    indicator_results["RSI_14"] = {
                        "value": float(rsi),
                        "timestamp": hist.index[-1].to_pydatetime(),
                        "signal": signal,
                        "confidence": abs(50 - rsi) / 50  # Confidence based on distance from neutral
                    }

            # Bollinger Bands
            if "BOLLINGER" in indicators:
                bb = self._calculate_bollinger_bands(hist["Close"], 20, 2)
                if all(key in bb for key in ["upper", "middle", "lower"]):
                    current_price = hist["Close"].iloc[-1]
                    signal = "neutral"
                    if current_price < bb["lower"]:
                        signal = "buy"
                    elif current_price > bb["upper"]:
                        signal = "sell"

                    indicator_results["BOLLINGER_20"] = {
                        "value": float(current_price),
                        "upper_band": float(bb["upper"]),
                        "middle_band": float(bb["middle"]),
                        "lower_band": float(bb["lower"]),
                        "timestamp": hist.index[-1].to_pydatetime(),
                        "signal": signal,
                        "confidence": min(
                            abs(current_price - bb["upper"]) / (bb["upper"] - bb["middle"]),
                            abs(current_price - bb["lower"]) / (bb["middle"] - bb["lower"])
                        )
                    }

            # Write indicators to InfluxDB
            if indicator_results:
                indicator_data = []
                for indicator_name, data in indicator_results.items():
                    data_point = {
                        "timestamp": data["timestamp"],
                        "tags": {
                            "symbol": symbol,
                            "indicator_type": indicator_name.split("_")[0],
                            "indicator_name": indicator_name,
                            "exchange": self._get_yahoo_exchange(yf.Ticker(symbol))
                        },
                        "fields": {
                            "value": data["value"],
                            "signal": data.get("signal", "neutral"),
                            "confidence": data.get("confidence", 0.5)
                        }
                    }

                    # Add band values for Bollinger Bands
                    if "upper_band" in data:
                        data_point["fields"]["upper_band"] = data["upper_band"]
                        data_point["fields"]["lower_band"] = data["lower_band"]
                        data_point["fields"]["middle_band"] = data["middle_band"]

                    indicator_data.append(data_point)

                await self.influxdb.write_market_data(
                    indicator_data,
                    measurement="technical_indicators",
                    bucket="market_data_raw"
                )

            return indicator_results

        except Exception as e:
            logger.error(f"Failed to collect indicators for {symbol}: {e}")
            return {}

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()

        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)

        latest = len(prices) - 1
        return {
            "upper": upper_band.iloc[latest],
            "middle": sma.iloc[latest],
            "lower": lower_band.iloc[latest]
        }

    async def get_market_overview(self) -> Dict:
        """Get market overview data"""
        try:
            # Get major indices
            indices = ["^GSPC", "^DJI", "^IXIC"]  # S&P 500, Dow Jones, NASDAQ
            overview = {}

            for index in indices:
                ticker = yf.Ticker(index)
                info = ticker.info

                overview[index] = {
                    "name": info.get("shortName", index),
                    "price": info.get("regularMarketPrice", 0),
                    "change": info.get("regularMarketChange", 0),
                    "change_percent": info.get("regularMarketChangePercent", 0),
                    "volume": info.get("regularMarketVolume", 0)
                }

            return overview

        except Exception as e:
            logger.error(f"Failed to get market overview: {e}")
            return {}

    def get_statistics(self) -> Dict:
        """Get collector statistics"""
        return {
            **self.stats,
            "running": self._running,
            "symbols_count": len(self.config.symbols),
            "data_sources": [name for name, config in self.data_sources.items() if config.enabled]
        }


# Example usage
async def main():
    """Example usage of market data collector"""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Create configuration
    collector_config = CollectorConfig(
        symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        collection_interval=300,  # 5 minutes
        market_hours_only=True
    )

    # Create InfluxDB manager
    influxdb_config = InfluxDBConfig(
        url=os.getenv("INFLUXDB_URL", "http://localhost:8086"),
        token=os.getenv("INFLUXDB_TOKEN", ""),
        org="cbsc"
    )

    influxdb_manager = await create_influxdb_manager(influxdb_config)

    try:
        # Create collector
        redis_client = redis.Redis(host="localhost", port=6379, db=0)
        collector = MarketDataCollector(
            config=collector_config,
            influxdb_manager=influxdb_manager,
            redis_client=redis_client
        )

        # Start collector
        await collector.start()

        # Run for a while
        await asyncio.sleep(300)  # 5 minutes

        # Get statistics
        stats = collector.get_statistics()
        print(f"Collector statistics: {stats}")

        # Stop collector
        await collector.stop()

    finally:
        await influxdb_manager.close()


if __name__ == "__main__":
    asyncio.run(main())