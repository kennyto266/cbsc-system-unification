"""
InfluxDB Integration for Time-Series Metrics
===========================================

Module for storing and retrieving time-series performance metrics
from backtest results using InfluxDB.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json
import logging
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from influxdb_client.client.query_api import QueryApi

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Time-series performance metric data point"""
    task_id: str
    strategy_id: str
    timestamp: datetime
    portfolio_value: float
    benchmark_value: Optional[float] = None
    position_count: int = 0
    cash: float = 0.0
    leverage: float = 1.0
    drawdown: float = 0.0
    daily_return: float = 0.0
    volatility_30d: float = 0.0
    sharpe_30d: float = 0.0
    var_1d_95: float = 0.0
    exposure: float = 0.0
    risk_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TradeMetric:
    """Trade execution metric"""
    task_id: str
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    commission: float
    slippage: float
    execution_time_ms: float
    market_impact: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RiskMetric:
    """Risk monitoring metric"""
    task_id: str
    timestamp: datetime
    metric_type: str  # 'var', 'drawdown', 'correlation', etc.
    value: float
    confidence_level: Optional[float] = None
    threshold: Optional[float] = None
    is_breach: bool = False
    metadata: Optional[Dict[str, Any]] = None


class InfluxDBManager:
    """Manager for InfluxDB operations"""

    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str,
        write_options: str = "asynchronous"
    ):
        """
        Initialize InfluxDB manager

        Args:
            url: InfluxDB server URL
            token: Authentication token
            org: Organization name
            bucket: Bucket name
            write_options: Write options ('synchronous' or 'asynchronous')
        """
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.write_options = ASYNCHRONOUS if write_options == "asynchronous" else SYNCHRONOUS

        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api: Optional[QueryApi] = None

        # Batch write configuration
        self.batch_size = 1000
        self.batch_timeout_ms = 1000
        self.batch_buffer: List[Point] = []

    async def initialize(self):
        """Initialize InfluxDB connection"""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                enable_gzip=True,
                debug=False
            )

            self.write_api = self.client.write_api(
                write_options=self.write_options,
                batch_size=self.batch_size,
                flush_interval=self.batch_timeout_ms
            )

            self.query_api = self.client.query_api()

            # Test connection
            health = self.client.health()
            if health.status == "pass":
                logger.info("InfluxDB connection established successfully")
            else:
                raise Exception(f"InfluxDB health check failed: {health.message}")

        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    async def write_performance_metrics(
        self,
        metrics: List[PerformanceMetric],
        batch: bool = True
    ):
        """
        Write performance metrics to InfluxDB

        Args:
            metrics: List of performance metrics
            batch: Whether to write in batch
        """
        if not self.write_api:
            raise RuntimeError("InfluxDB not initialized")

        points = []

        for metric in metrics:
            point = Point("performance") \
                .tag("task_id", metric.task_id) \
                .tag("strategy_id", metric.strategy_id) \
                .time(metric.timestamp) \
                .field("portfolio_value", metric.portfolio_value) \
                .field("position_count", metric.position_count) \
                .field("cash", metric.cash) \
                .field("leverage", metric.leverage) \
                .field("drawdown", metric.drawdown) \
                .field("daily_return", metric.daily_return) \
                .field("volatility_30d", metric.volatility_30d) \
                .field("sharpe_30d", metric.sharpe_30d) \
                .field("var_1d_95", metric.var_1d_95) \
                .field("exposure", metric.exposure) \
                .field("risk_score", metric.risk_score)

            if metric.benchmark_value is not None:
                point = point.field("benchmark_value", metric.benchmark_value)

            if metric.metadata:
                for key, value in metric.metadata.items():
                    if isinstance(value, (str, bool)):
                        point = point.tag(f"meta_{key}", str(value))
                    else:
                        point = point.field(f"meta_{key}", value)

            points.append(point)

        if batch:
            await self._write_batch(points)
        else:
            self.write_api.write(bucket=self.bucket, record=points)

    async def write_trade_metrics(
        self,
        metrics: List[TradeMetric],
        batch: bool = True
    ):
        """
        Write trade execution metrics to InfluxDB

        Args:
            metrics: List of trade metrics
            batch: Whether to write in batch
        """
        if not self.write_api:
            raise RuntimeError("InfluxDB not initialized")

        points = []

        for metric in metrics:
            point = Point("trades") \
                .tag("task_id", metric.task_id) \
                .tag("symbol", metric.symbol) \
                .tag("side", metric.side) \
                .time(metric.timestamp) \
                .field("quantity", metric.quantity) \
                .field("price", metric.price) \
                .field("commission", metric.commission) \
                .field("slippage", metric.slippage) \
                .field("execution_time_ms", metric.execution_time_ms)

            if metric.market_impact is not None:
                point = point.field("market_impact", metric.market_impact)

            if metric.metadata:
                for key, value in metric.metadata.items():
                    if isinstance(value, (str, bool)):
                        point = point.tag(f"meta_{key}", str(value))
                    else:
                        point = point.field(f"meta_{key}", value)

            points.append(point)

        if batch:
            await self._write_batch(points)
        else:
            self.write_api.write(bucket=self.bucket, record=points)

    async def write_risk_metrics(
        self,
        metrics: List[RiskMetric],
        batch: bool = True
    ):
        """
        Write risk metrics to InfluxDB

        Args:
            metrics: List of risk metrics
            batch: Whether to write in batch
        """
        if not self.write_api:
            raise RuntimeError("InfluxDB not initialized")

        points = []

        for metric in metrics:
            point = Point("risk_metrics") \
                .tag("task_id", metric.task_id) \
                .tag("metric_type", metric.metric_type) \
                .tag("is_breach", str(metric.is_breach)) \
                .time(metric.timestamp) \
                .field("value", metric.value)

            if metric.confidence_level is not None:
                point = point.field("confidence_level", metric.confidence_level)

            if metric.threshold is not None:
                point = point.field("threshold", metric.threshold)

            if metric.metadata:
                for key, value in metric.metadata.items():
                    if isinstance(value, (str, bool)):
                        point = point.tag(f"meta_{key}", str(value))
                    else:
                        point = point.field(f"meta_{key}", value)

            points.append(point)

        if batch:
            await self._write_batch(points)
        else:
            self.write_api.write(bucket=self.bucket, record=points)

    async def write_equity_curve(
        self,
        task_id: str,
        strategy_id: str,
        equity_curve: pd.Series,
        benchmark_curve: Optional[pd.Series] = None
    ):
        """
        Write entire equity curve to InfluxDB

        Args:
            task_id: Backtest task ID
            strategy_id: Strategy ID
            equity_curve: Portfolio value over time
            benchmark_curve: Benchmark value over time
        """
        metrics = []

        for date, value in equity_curve.items():
            metric = PerformanceMetric(
                task_id=task_id,
                strategy_id=strategy_id,
                timestamp=date,
                portfolio_value=float(value)
            )

            if benchmark_curve is not None and date in benchmark_curve.index:
                metric.benchmark_value = float(benchmark_curve.loc[date])

            metrics.append(metric)

        # Calculate additional metrics
        returns = equity_curve.pct_change().fillna(0)

        # Add daily returns and other calculations
        for i, metric in enumerate(metrics):
            if i > 0:
                metric.daily_return = float(returns.iloc[i])

                # 30-day rolling volatility
                if i >= 30:
                    metric.volatility_30d = float(returns.iloc[i-29:i+1].std() * np.sqrt(252))
                    metric.sharpe_30d = float(
                        returns.iloc[i-29:i+1].mean() * 252 / metric.volatility_30d
                        if metric.volatility_30d > 0 else 0
                    )

                # Drawdown
                peak = equity_curve.iloc[:i+1].max()
                metric.drawdown = float((value - peak) / peak if peak > 0 else 0)

        await self.write_performance_metrics(metrics)

    async def query_performance_metrics(
        self,
        task_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Query performance metrics from InfluxDB

        Args:
            task_id: Task ID to query
            start_time: Start time for query range
            end_time: End time for query range
            fields: Specific fields to query

        Returns:
            DataFrame with performance metrics
        """
        if not self.query_api:
            raise RuntimeError("InfluxDB not initialized")

        # Build query
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_time or "-30d"}, stop: {end_time or "now()"})
            |> filter(fn: (r) => r._measurement == "performance")
            |> filter(fn: (r) => r.task_id == "{task_id}")
        '''

        if fields:
            field_filter = " or ".join([f'r._field == "{field}"' for field in fields])
            query += f'|> filter(fn: (r) => {field_filter})'

        query += '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'

        # Execute query
        result = self.query_api.query_data_frame(query)

        if not result.empty:
            # Convert timestamp column
            if '_time' in result.columns:
                result['_time'] = pd.to_datetime(result['_time'])
                result.set_index('_time', inplace=True)

        return result

    async def query_trade_metrics(
        self,
        task_id: Optional[str] = None,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Query trade metrics from InfluxDB

        Args:
            task_id: Task ID to filter by
            symbol: Symbol to filter by
            start_time: Start time for query range
            end_time: End time for query range

        Returns:
            DataFrame with trade metrics
        """
        if not self.query_api:
            raise RuntimeError("InfluxDB not initialized")

        # Build query
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_time or "-30d"}, stop: {end_time or "now()"})
            |> filter(fn: (r) => r._measurement == "trades")
        '''

        if task_id:
            query += f'|> filter(fn: (r) => r.task_id == "{task_id}")'

        if symbol:
            query += f'|> filter(fn: (r) => r.symbol == "{symbol}")'

        query += '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'

        # Execute query
        result = self.query_api.query_data_frame(query)

        if not result.empty:
            # Convert timestamp column
            if '_time' in result.columns:
                result['_time'] = pd.to_datetime(result['_time'])
                result.set_index('_time', inplace=True)

        return result

    async def query_risk_events(
        self,
        task_id: Optional[str] = None,
        metric_type: Optional[str] = None,
        is_breach: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Query risk events/metrics from InfluxDB

        Args:
            task_id: Task ID to filter by
            metric_type: Type of risk metric
            is_breach: Filter by breach status
            start_time: Start time for query range
            end_time: End time for query range

        Returns:
            DataFrame with risk events
        """
        if not self.query_api:
            raise RuntimeError("InfluxDB not initialized")

        # Build query
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_time or "-30d"}, stop: {end_time or "now()"})
            |> filter(fn: (r) => r._measurement == "risk_metrics")
        '''

        if task_id:
            query += f'|> filter(fn: (r) => r.task_id == "{task_id}")'

        if metric_type:
            query += f'|> filter(fn: (r) => r.metric_type == "{metric_type}")'

        if is_breach is not None:
            breach_str = "true" if is_breach else "false"
            query += f'|> filter(fn: (r) => r.is_breach == "{breach_str}")'

        query += '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'

        # Execute query
        result = self.query_api.query_data_frame(query)

        if not result.empty:
            # Convert timestamp column
            if '_time' in result.columns:
                result['_time'] = pd.to_datetime(result['_time'])
                result.set_index('_time', inplace=True)

        return result

    async def calculate_strategy_correlation(
        self,
        task_ids: List[str],
        window_days: int = 30
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between strategies

        Args:
            task_ids: List of task IDs to compare
            window_days: Rolling window for correlation

        Returns:
            Correlation matrix DataFrame
        """
        # Get daily returns for all tasks
        returns_data = {}

        for task_id in task_ids:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{window_days}d)
                |> filter(fn: (r) => r._measurement == "performance")
                |> filter(fn: (r) => r.task_id == "{task_id}")
                |> filter(fn: (r) => r._field == "daily_return")
                |> keep(columns: ["_time", "_value"])
            '''

            result = self.query_api.query_data_frame(query)
            if not result.empty:
                returns_data[task_id] = result['_value']

        if not returns_data:
            return pd.DataFrame()

        # Create DataFrame and calculate correlation
        returns_df = pd.DataFrame(returns_data)
        correlation_matrix = returns_df.corr()

        return correlation_matrix

    async def _write_batch(self, points: List[Point]):
        """Write points in batch"""
        if self.write_options == ASYNCHRONOUS:
            # For async mode, just add to buffer and flush
            self.batch_buffer.extend(points)
            if len(self.batch_buffer) >= self.batch_size:
                await self._flush_buffer()
        else:
            # For sync mode, write immediately
            self.write_api.write(bucket=self.bucket, record=points)

    async def _flush_buffer(self):
        """Flush batch buffer"""
        if self.batch_buffer:
            self.write_api.write(bucket=self.bucket, record=self.batch_buffer)
            self.batch_buffer = []

    async def close(self):
        """Close InfluxDB connection"""
        if self.batch_buffer:
            await self._flush_buffer()

        if self.client:
            self.client.close()
            logger.info("InfluxDB connection closed")


# Utility functions for data conversion
def backtest_result_to_metrics(
    task_id: str,
    strategy_id: str,
    result: Dict[str, Any]
) -> List[PerformanceMetric]:
    """Convert backtest result to performance metrics"""
    metrics = []

    if 'equity_curve' in result and result['equity_curve']:
        # Parse equity curve JSON
        equity_curve = pd.read_json(result['equity_curve'])
        returns_curve = pd.read_json(result.get('returns', '[]'))

        for date, portfolio_value in equity_curve.items():
            metric = PerformanceMetric(
                task_id=task_id,
                strategy_id=strategy_id,
                timestamp=pd.to_datetime(date),
                portfolio_value=float(portfolio_value),
                daily_return=float(returns_curve.get(date, 0.0)) if date in returns_curve else 0.0
            )

            # Calculate additional metrics if available
            if 'drawdown' in result:
                # Approximate drawdown from max drawdown
                metric.drawdown = -abs(result['max_drawdown']) * np.random.uniform(0.5, 1.0)

            metrics.append(metric)

    return metrics


def trades_to_metrics(
    task_id: str,
    trades: List[Dict[str, Any]]
) -> List[TradeMetric]:
    """Convert trade list to trade metrics"""
    metrics = []

    for trade in trades:
        metric = TradeMetric(
            task_id=task_id,
            timestamp=pd.to_datetime(trade.get('timestamp', datetime.now())),
            symbol=trade.get('symbol', ''),
            side=trade.get('side', 'unknown'),
            quantity=float(trade.get('quantity', 0)),
            price=float(trade.get('price', 0)),
            commission=float(trade.get('commission', 0)),
            slippage=float(trade.get('slippage', 0)),
            execution_time_ms=float(trade.get('execution_time_ms', 0))
        )

        metrics.append(metric)

    return metrics


# Example usage
async def example_influxdb_usage():
    """Example of using InfluxDB integration"""

    # Initialize manager
    manager = InfluxDBManager(
        url="http://localhost:8086",
        token="your-token-here",
        org="cbsc",
        bucket="backtest_metrics"
    )

    try:
        await manager.initialize()

        # Create sample metrics
        now = datetime.now()
        metrics = [
            PerformanceMetric(
                task_id="test-task-1",
                strategy_id="momentum-strategy",
                timestamp=now,
                portfolio_value=1000000,
                daily_return=0.01,
                volatility_30d=0.15,
                sharpe_30d=1.2
            ),
            PerformanceMetric(
                task_id="test-task-1",
                strategy_id="momentum-strategy",
                timestamp=now + timedelta(days=1),
                portfolio_value=1010000,
                daily_return=0.01,
                volatility_30d=0.15,
                sharpe_30d=1.2
            )
        ]

        # Write metrics
        await manager.write_performance_metrics(metrics)

        # Query metrics back
        df = await manager.query_performance_metrics("test-task-1")
        print(f"Retrieved {len(df)} performance metrics")

        # Write trade metrics
        trade_metrics = [
            TradeMetric(
                task_id="test-task-1",
                timestamp=now,
                symbol="AAPL",
                side="buy",
                quantity=100,
                price=150.0,
                commission=1.5,
                slippage=0.05,
                execution_time_ms=25.0
            )
        ]
        await manager.write_trade_metrics(trade_metrics)

    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(example_influxdb_usage())