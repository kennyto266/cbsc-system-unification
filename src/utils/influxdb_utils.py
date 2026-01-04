#!/usr/bin/env python3
"""
InfluxDB Utility Functions
InfluxDB 實用工具函數
Phase 1.2 - 時序數據庫配置

Common utility functions for InfluxDB operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
import numpy as np

from ..services.influxdb_client import InfluxDBManager
from ..config.influxdb_config import get_config, BucketType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketDataWriter:
    """
    Utility class for writing market data to InfluxDB.
    將市場數據寫入 InfluxDB 的實用類。
    """

    def __init__(self, manager: InfluxDBManager):
        self.manager = manager

    async def write_ohlcv(
        self,
        symbol: str,
        exchange: str,
        ohlcv_data: List[Dict[str, Any]],
        timeframe: str = "1m",
        currency: str = "USD"
    ) -> bool:
        """
        Write OHLCV data for a symbol.
        寫入某個股票的 OHLCV 數據。

        Args:
            symbol: Stock symbol (e.g., AAPL)
            exchange: Exchange name (e.g., NASDAQ)
            ohlcv_data: List of OHLCV dictionaries
            timeframe: Timeframe (e.g., 1m, 5m, 1h, 1d)
            currency: Currency code

        Returns:
            bool: Success status
        """
        # Prepare data points
        data_points = []
        for bar in ohlcv_data:
            # Validate data
            if not all(key in bar for key in ['open', 'high', 'low', 'close', 'timestamp']):
                logger.warning(f"Skipping invalid OHLCV bar: {bar}")
                continue

            # High should be >= low, open, close
            if bar['high'] < bar['low']:
                logger.warning(f"Invalid OHLCV data: high < low for {symbol}")
                continue

            data_points.append({
                "measurement": "stock_price",
                "timestamp": bar['timestamp'] if isinstance(bar['timestamp'], datetime) else pd.to_datetime(bar['timestamp']),
                "tags": {
                    "symbol": symbol,
                    "exchange": exchange,
                    "currency": currency,
                    "timeframe": timeframe
                },
                "fields": {
                    "open": float(bar['open']),
                    "high": float(bar['high']),
                    "low": float(bar['low']),
                    "close": float(bar['close']),
                    "volume": int(bar.get('volume', 0)),
                    "vwap": float(bar.get('vwap', 0)),
                    "num_trades": int(bar.get('num_trades', 0))
                }
            })

        # Write to InfluxDB
        return await self.manager.write_market_data(
            data_points,
            measurement="stock_price",
            bucket=BucketType.MARKET_DATA_RAW.value
        )

    async def write_technical_indicator(
        self,
        symbol: str,
        indicator_name: str,
        indicator_type: str,
        values: List[Tuple[datetime, float]],
        exchange: str = "NASDAQ",
        timeframe: str = "1d"
    ) -> bool:
        """
        Write technical indicator values.
        寫入技術指標值。

        Args:
            symbol: Stock symbol
            indicator_name: Indicator name (e.g., SMA_20, RSI_14)
            indicator_type: Indicator type (e.g., ma, rsi, macd)
            values: List of (timestamp, value) tuples
            exchange: Exchange name
            timeframe: Timeframe

        Returns:
            bool: Success status
        """
        data_points = []
        for timestamp, value in values:
            data_points.append({
                "measurement": "technical_indicators",
                "timestamp": timestamp,
                "tags": {
                    "symbol": symbol,
                    "exchange": exchange,
                    "indicator_type": indicator_type,
                    "indicator_name": indicator_name,
                    "timeframe": timeframe
                },
                "fields": {
                    "value": float(value)
                }
            })

        return await self.manager.write_market_data(
            data_points,
            measurement="technical_indicators",
            bucket=BucketType.MARKET_DATA_RAW.value
        )


class StrategyPerformanceWriter:
    """
    Utility class for writing strategy performance data.
    寫入策略績效數據的實用類。
    """

    def __init__(self, manager: InfluxDBManager):
        self.manager = manager

    async def write_daily_returns(
        self,
        strategy_id: str,
        strategy_name: str,
        returns: List[Tuple[datetime, float]],
        benchmark_returns: Optional[List[Tuple[datetime, float]]] = None
    ) -> bool:
        """
        Write daily strategy returns.
        寫入每日策略回報。

        Args:
            strategy_id: Strategy ID
            strategy_name: Strategy name
            returns: List of (date, return) tuples
            benchmark_returns: Optional benchmark returns

        Returns:
            bool: Success status
        """
        data_points = []
        for date, daily_return in returns:
            # Find benchmark return for same date
            benchmark_return = 0.0
            if benchmark_returns:
                for b_date, b_return in benchmark_returns:
                    if b_date.date() == date.date():
                        benchmark_return = b_return
                        break

            data_points.append({
                "measurement": "strategy_returns",
                "timestamp": date,
                "tags": {
                    "strategy_id": strategy_id,
                    "strategy_name": strategy_name,
                    "frequency": "daily",
                    "benchmark": "SPY"
                },
                "fields": {
                    "daily_return": float(daily_return),
                    "benchmark_return": float(benchmark_return),
                    "excess_return": float(daily_return - benchmark_return)
                }
            })

        return await self.manager.write_market_data(
            data_points,
            measurement="strategy_returns",
            bucket=BucketType.STRATEGY_PERFORMANCE.value
        )

    async def write_trade_analysis(
        self,
        strategy_id: str,
        trades: List[Dict[str, Any]]
    ) -> bool:
        """
        Write individual trade analysis.
        寫入單筆交易分析。

        Args:
            strategy_id: Strategy ID
            trades: List of trade dictionaries

        Returns:
            bool: Success status
        """
        data_points = []
        for trade in trades:
            # Calculate return percentage
            if trade.get('entry_price') and trade.get('exit_price'):
                if trade['direction'] == 'long':
                    return_pct = (trade['exit_price'] - trade['entry_price']) / trade['entry_price'] * 100
                else:
                    return_pct = (trade['entry_price'] - trade['exit_price']) / trade['entry_price'] * 100
            else:
                return_pct = 0.0

            data_points.append({
                "measurement": "trade_analysis",
                "timestamp": trade.get('exit_time', datetime.utcnow()),
                "tags": {
                    "strategy_id": strategy_id,
                    "trade_id": trade.get('trade_id', ''),
                    "symbol": trade.get('symbol', ''),
                    "direction": trade.get('direction', 'long'),
                    "exit_reason": trade.get('exit_reason', '')
                },
                "fields": {
                    "entry_price": float(trade.get('entry_price', 0)),
                    "exit_price": float(trade.get('exit_price', 0)),
                    "quantity": float(trade.get('quantity', 0)),
                    "duration": int(trade.get('duration', 0)),
                    "return_pct": float(return_pct),
                    "pnl": float(trade.get('pnl', 0)),
                    "commission": float(trade.get('commission', 0)),
                    "slippage": float(trade.get('slippage', 0))
                }
            })

        return await self.manager.write_market_data(
            data_points,
            measurement="trade_analysis",
            bucket=BucketType.STRATEGY_PERFORMANCE.value
        )


class RiskMetricsWriter:
    """
    Utility class for writing risk metrics.
    寫入風險指標的實用類。
    """

    def __init__(self, manager: InfluxDBManager):
        self.manager = manager

    async def write_var_metrics(
        self,
        strategy_id: str,
        var_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write Value at Risk (VaR) metrics.
        寫入風險值 (VaR) 指標。

        Args:
            strategy_id: Strategy ID
            var_data: VaR calculation results
            timestamp: Calculation timestamp

        Returns:
            bool: Success status
        """
        if not timestamp:
            timestamp = datetime.utcnow()

        # Write 95% VaR
        var_95_data = [{
            "measurement": "strategy_risk",
            "timestamp": timestamp,
            "tags": {
                "strategy_id": strategy_id,
                "risk_type": "VaR",
                "confidence_level": 95,
                "time_horizon": 1,
                "calculation_method": var_data.get('method', 'historical')
            },
            "fields": {
                "value": float(var_data.get('var_95', 0)),
                "historical_var": float(var_data.get('historical_var_95', 0)),
                "parametric_var": float(var_data.get('parametric_var_95', 0)),
                "expected_shortfall": float(var_data.get('expected_shortfall_95', 0))
            }
        }]

        # Write 99% VaR if available
        if 'var_99' in var_data:
            var_99_data = [{
                "measurement": "strategy_risk",
                "timestamp": timestamp,
                "tags": {
                    "strategy_id": strategy_id,
                    "risk_type": "VaR",
                    "confidence_level": 99,
                    "time_horizon": 1,
                    "calculation_method": var_data.get('method', 'historical')
                },
                "fields": {
                    "value": float(var_data.get('var_99', 0)),
                    "expected_shortfall": float(var_data.get('expected_shortfall_99', 0))
                }
            }]
            var_95_data.extend(var_99_data)

        return await self.manager.write_market_data(
            var_95_data,
            measurement="strategy_risk",
            bucket=BucketType.RISK_METRICS.value
        )

    async def write_drawdown_metrics(
        self,
        strategy_id: str,
        drawdown_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write drawdown metrics.
        寫入回撤指標。

        Args:
            strategy_id: Strategy ID
            drawdown_data: Drawdown calculation results
            timestamp: Calculation timestamp

        Returns:
            bool: Success status
        """
        if not timestamp:
            timestamp = datetime.utcnow()

        data_points = [{
            "measurement": "strategy_risk",
            "timestamp": timestamp,
            "tags": {
                "strategy_id": strategy_id,
                "risk_type": "drawdown",
                "time_horizon": 0  # Current state
            },
            "fields": {
                "current_drawdown": float(drawdown_data.get('current_drawdown', 0)),
                "maximum_drawdown": float(drawdown_data.get('maximum_drawdown', 0)),
                "drawdown_duration": int(drawdown_data.get('drawdown_duration', 0)),
                "recovery_factor": float(drawdown_data.get('recovery_factor', 0))
            }
        }]

        return await self.manager.write_market_data(
            data_points,
            measurement="strategy_risk",
            bucket=BucketType.RISK_METRICS.value
        )


class DataQueryHelper:
    """
    Helper class for common data queries.
    常用數據查詢的輔助類。
    """

    def __init__(self, manager: InfluxDBManager):
        self.manager = manager

    async def get_symbol_prices(
        self,
        symbol: str,
        exchange: str = "NASDAQ",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        timeframe: str = "1d",
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get price data for a symbol.
        獲取某個股票的價格數據。

        Args:
            symbol: Stock symbol
            exchange: Exchange name
            start: Start datetime
            end: End datetime
            timeframe: Data timeframe
            fields: Fields to retrieve

        Returns:
            pd.DataFrame: Price data
        """
        # Determine bucket based on timeframe
        if timeframe in ["1m", "5m", "15m", "30m", "1h"]:
            bucket = BucketType.MARKET_DATA_RAW.value
        elif timeframe == "1h":
            bucket = BucketType.MARKET_DATA_HOURLY.value
        else:  # Daily and above
            bucket = BucketType.MARKET_DATA_DAILY.value

        # Build time range
        time_range = None
        if not start and not end:
            time_range = "-1y"  # Default to last year
        elif start and end:
            # Convert to relative time range
            delta = datetime.utcnow() - start
            days = delta.days
            time_range = f"-{days}d"

        # Default fields
        if not fields:
            fields = ["open", "high", "low", "close", "volume"]

        # Query data
        result = await self.manager.query_data(
            bucket=bucket,
            measurement="stock_price",
            time_range=time_range,
            tags={
                "symbol": symbol,
                "exchange": exchange
            },
            fields=fields
        )

        # Pivot to have columns for each field
        if not result.empty and "_field" in result.columns:
            result = result.pivot_table(
                index="_time",
                columns="_field",
                values="_value",
                aggfunc="last"
            )
            result = result.reset_index().rename(columns={"index": "timestamp"})

        return result

    async def get_strategy_performance(
        self,
        strategy_id: str,
        metric: str = "daily_return",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get strategy performance metrics.
        獲取策略績效指標。

        Args:
            strategy_id: Strategy ID
            metric: Metric to retrieve
            start: Start datetime
            end: End datetime

        Returns:
            pd.DataFrame: Performance data
        """
        # Build time range
        time_range = None
        if start:
            delta = datetime.utcnow() - start
            days = delta.days
            time_range = f"-{days}d"

        result = await self.manager.query_data(
            bucket=BucketType.STRATEGY_PERFORMANCE.value,
            measurement="strategy_returns",
            time_range=time_range,
            tags={"strategy_id": strategy_id},
            fields=[metric]
        )

        # Clean up result
        if not result.empty:
            result = result[["_time", "_value"]].rename(
                columns={"_time": "timestamp", "_value": metric}
            )
            result = result.sort_values("timestamp")

        return result

    async def calculate_cumulative_returns(
        self,
        strategy_id: str,
        start_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Calculate cumulative returns for a strategy.
        計算策略的累計回報。

        Args:
            strategy_id: Strategy ID
            start_date: Start date for calculation

        Returns:
            pd.DataFrame: Cumulative returns
        """
        # Get daily returns
        returns_df = await self.get_strategy_performance(
            strategy_id,
            metric="daily_return",
            start=start_date
        )

        if returns_df.empty:
            return pd.DataFrame(columns=["timestamp", "cumulative_return"])

        # Calculate cumulative returns
        returns_df["cumulative_return"] = (1 + returns_df["daily_return"]).cumprod() - 1

        return returns_df


# Utility functions for batch operations
async def batch_write_market_data(
    manager: InfluxDBManager,
    data_batches: List[List[Dict[str, Any]]],
    measurement: str,
    bucket: str
) -> Tuple[int, int]:
    """
    Write multiple batches of market data.
    批量寫入多個市場數據批次。

    Returns:
        Tuple[int, int]: (successful_writes, failed_writes)
    """
    successful = 0
    failed = 0

    for batch in data_batches:
        try:
            success = await manager.write_market_data(
                batch,
                measurement=measurement,
                bucket=bucket
            )
            if success:
                successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Batch write failed: {e}")
            failed += 1

    return successful, failed


async def validate_data_quality(
    manager: InfluxDBManager,
    bucket: str,
    measurement: str,
    symbol: str,
    start: datetime,
    end: datetime
) -> Dict[str, Any]:
    """
    Validate data quality for a symbol.
    驗證某個股票的數據質量。

    Returns:
        Dict with quality metrics
    """
    # Query the data
    query = f'''
from(bucket: "{bucket}")
  |> range(start: {start.isoformat()}, stop: {end.isoformat()})
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> filter(fn: (r) => r.symbol == "{symbol}")
  |> filter(fn: (r) => r._field == "close")
  |> group()
  |> sort(columns: ["_time"])
    '''

    result = await manager.query_data(query)

    quality_report = {
        "symbol": symbol,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_records": len(result),
        "missing_records": 0,
        "duplicate_records": 0,
        "outliers": 0,
        "data_gaps": []
    }

    if not result.empty:
        # Check for missing data (assuming daily data)
        expected_days = (end - start).days
        actual_days = len(result)
        quality_report["missing_records"] = max(0, expected_days - actual_days)

        # Check for outliers (simple statistical method)
        if "_value" in result.columns:
            values = result["_value"].values
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = np.where((values < lower_bound) | (values > upper_bound))[0]
            quality_report["outliers"] = len(outliers)

        # Check for data gaps
        if "_time" in result.columns:
            time_diff = result["_time"].diff()
            large_gaps = time_diff[time_diff > pd.Timedelta(days=2)]
            quality_report["data_gaps"] = [
                {"start": (result.iloc[i]["_time"] - pd.Timedelta(days=1)).isoformat(),
                 "end": result.iloc[i+1]["_time"].isoformat(),
                 "duration_days": gap.days}
                for i, gap in enumerate(large_gaps)
                if i < len(result) - 1
            ]

    return quality_report


# Example usage
async def example_usage():
    """Example of using the utilities"""
    from ..services.influxdb_client import create_influxdb_manager
    from ..config.influxdb_config import get_config
    import os
    from dotenv import load_dotenv

    # Load configuration
    load_dotenv()
    config = get_config()

    # Create manager
    manager = await create_influxdb_manager(config.connection)

    try:
        # Create utility instances
        market_writer = MarketDataWriter(manager)
        query_helper = DataQueryHelper(manager)

        # Write sample OHLCV data
        ohlcv_data = [
            {
                "timestamp": datetime.utcnow() - timedelta(days=i),
                "open": 150.0 + i,
                "high": 155.0 + i,
                "low": 149.0 + i,
                "close": 152.0 + i,
                "volume": 1000000
            }
            for i in range(10, 0, -1)
        ]

        success = await market_writer.write_ohlcv(
            symbol="AAPL",
            exchange="NASDAQ",
            ohlcv_data=ohlcv_data
        )
        print(f"Write OHLCV success: {success}")

        # Query price data
        prices = await query_helper.get_symbol_prices(
            symbol="AAPL",
            start=datetime.utcnow() - timedelta(days=15)
        )
        print(f"Retrieved {len(prices)} price records")

        # Validate data quality
        quality = await validate_data_quality(
            manager=manager,
            bucket=BucketType.MARKET_DATA_RAW.value,
            measurement="stock_price",
            symbol="AAPL",
            start=datetime.utcnow() - timedelta(days=15),
            end=datetime.utcnow()
        )
        print(f"Data quality: {quality}")

    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(example_usage())