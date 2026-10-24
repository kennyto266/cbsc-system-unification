"""
Performance calculation service for analytics API
"""
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
import logging

from ..models.analytics import (
    PerformanceMetrics,
    ReturnsData,
    TimeSeriesPoint,
    Timeframe
)

logger = logging.getLogger(__name__)


@dataclass
class CalculationConfig:
    """Configuration for performance calculations"""
    risk_free_rate: float = 0.02  # 2% annual risk-free rate
    trading_days: int = 252  # Trading days per year
    benchmark_symbol: str = "SPY"  # Default benchmark


class PerformanceCalculationService:
    """Service for calculating strategy performance metrics"""

    def __init__(self, config: CalculationConfig = None):
        self.config = config or CalculationConfig()

    async def calculate_performance_metrics(
        self,
        strategy_id: str,
        returns_data: List[Tuple[date, float]],
        trades_data: Optional[List[Dict]] = None
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics for a strategy

        Args:
            strategy_id: Strategy identifier
            returns_data: List of (date, return) tuples
            trades_data: Optional list of trade data

        Returns:
            PerformanceMetrics object with calculated metrics
        """
        try:
            if not returns_data:
                raise ValueError("No returns data provided")

            # Convert to pandas for calculations
            df = pd.DataFrame(returns_data, columns=['date', 'return'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

            # Calculate basic metrics
            total_return = self._calculate_total_return(df['return'])
            annualized_return = self._calculate_annualized_return(df['return'])
            volatility = self._calculate_volatility(df['return'])

            # Risk-adjusted metrics
            sharpe_ratio = self._calculate_sharpe_ratio(df['return'], volatility)
            sortino_ratio = self._calculate_sortino_ratio(df['return'])
            max_drawdown = self._calculate_max_drawdown(df['return'])
            var_95 = self._calculate_var(df['return'], 0.95)

            # Trading metrics
            win_rate = None
            profit_factor = None
            avg_trade_return = None
            total_trades = None
            winning_trades = None

            if trades_data:
                trading_metrics = self._calculate_trading_metrics(trades_data)
                win_rate = trading_metrics['win_rate']
                profit_factor = trading_metrics['profit_factor']
                avg_trade_return = trading_metrics['avg_return']
                total_trades = trading_metrics['total_trades']
                winning_trades = trading_metrics['winning_trades']

            # Time-based returns
            daily_return = df['return'].iloc[-1] if len(df) > 0 else None
            weekly_return = self._calculate_period_return(df['return'], 7)
            monthly_return = self._calculate_period_return(df['return'], 30)

            return PerformanceMetrics(
                strategy_id=strategy_id,
                strategy_name="",  # Will be filled by caller
                total_return=Decimal(str(total_return)),
                annualized_return=Decimal(str(annualized_return)),
                daily_return=Decimal(str(daily_return)) if daily_return else None,
                weekly_return=Decimal(str(weekly_return)) if weekly_return else None,
                monthly_return=Decimal(str(monthly_return)) if monthly_return else None,
                volatility=Decimal(str(volatility)),
                sharpe_ratio=Decimal(str(sharpe_ratio)) if sharpe_ratio else None,
                sortino_ratio=Decimal(str(sortino_ratio)) if sortino_ratio else None,
                max_drawdown=Decimal(str(max_drawdown)),
                var_95=Decimal(str(var_95)) if var_95 else None,
                win_rate=Decimal(str(win_rate)) if win_rate else None,
                profit_factor=Decimal(str(profit_factor)) if profit_factor else None,
                avg_trade_return=Decimal(str(avg_trade_return)) if avg_trade_return else None,
                total_trades=total_trades,
                winning_trades=winning_trades,
                inception_date=df.index[0].date(),
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            raise

    def _calculate_total_return(self, returns: pd.Series) -> float:
        """Calculate total cumulative return"""
        return (1 + returns).prod() - 1

    def _calculate_annualized_return(self, returns: pd.Series) -> float:
        """Calculate annualized return"""
        total_return = self._calculate_total_return(returns)
        years = len(returns) / self.config.trading_days
        if years == 0:
            return 0
        return (1 + total_return) ** (1 / years) - 1

    def _calculate_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility"""
        return returns.std() * np.sqrt(self.config.trading_days)

    def _calculate_sharpe_ratio(self, returns: pd.Series, volatility: float) -> Optional[float]:
        """Calculate Sharpe ratio"""
        if volatility == 0:
            return None
        excess_return = self._calculate_annualized_return(returns) - self.config.risk_free_rate
        return excess_return / volatility

    def _calculate_sortino_ratio(self, returns: pd.Series) -> Optional[float]:
        """Calculate Sortino ratio (downside deviation)"""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return None

        downside_deviation = downside_returns.std() * np.sqrt(self.config.trading_days)
        if downside_deviation == 0:
            return None

        excess_return = self._calculate_annualized_return(returns) - self.config.risk_free_rate
        return excess_return / downside_deviation

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def _calculate_var(self, returns: pd.Series, confidence: float) -> float:
        """Calculate Value at Risk"""
        return returns.quantile(1 - confidence)

    def _calculate_trading_metrics(self, trades_data: List[Dict]) -> Dict:
        """Calculate trading-specific metrics"""
        if not trades_data:
            return {}

        returns = [trade.get('return', 0) for trade in trades_data]
        positive_returns = [r for r in returns if r > 0]
        negative_returns = [r for r in returns if r < 0]

        win_rate = len(positive_returns) / len(returns) if returns else 0

        avg_win = np.mean(positive_returns) if positive_returns else 0
        avg_loss = abs(np.mean(negative_returns)) if negative_returns else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')

        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor if profit_factor != float('inf') else None,
            'avg_return': np.mean(returns) if returns else 0,
            'total_trades': len(trades_data),
            'winning_trades': len(positive_returns)
        }

    def _calculate_period_return(self, returns: pd.Series, days: int) -> Optional[float]:
        """Calculate return for a specific period"""
        if len(returns) < days:
            return None
        period_returns = returns.tail(days)
        return self._calculate_total_return(period_returns)

    async def generate_returns_series(
        self,
        strategy_id: str,
        price_data: List[Tuple[date, float]],
        benchmark_data: Optional[List[Tuple[date, float]]] = None,
        timeframe: Timeframe = Timeframe.DAY
    ) -> ReturnsData:
        """
        Generate returns data series from price data

        Args:
            strategy_id: Strategy identifier
            price_data: List of (date, price) tuples
            benchmark_data: Optional benchmark price data
            timeframe: Data frequency

        Returns:
            ReturnsData with time series returns
        """
        try:
            if not price_data:
                raise ValueError("No price data provided")

            # Convert to DataFrame
            df = pd.DataFrame(price_data, columns=['date', 'price'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

            # Calculate returns
            df['return'] = df['price'].pct_change()
            df = df.dropna()

            # Handle benchmark data
            benchmark_df = None
            if benchmark_data:
                benchmark_df = pd.DataFrame(benchmark_data, columns=['date', 'price'])
                benchmark_df['date'] = pd.to_datetime(benchmark_df['date'])
                benchmark_df.set_index('date', inplace=True)
                benchmark_df.sort_index(inplace=True)
                benchmark_df['return'] = benchmark_df['price'].pct_change()
                benchmark_df = benchmark_df.dropna()

            # Create time series points
            time_series = []
            for date, row in df.iterrows():
                point = TimeSeriesPoint(
                    date=date.date(),
                    value=Decimal(str(row['return'])),
                    benchmark=Decimal(str(benchmark_df.loc[date, 'return'])) if benchmark_df is not None and date in benchmark_df.index else None
                )
                time_series.append(point)

            # Calculate summary statistics
            returns_series = df['return']
            total_return = self._calculate_total_return(returns_series)
            annualized_return = self._calculate_annualized_return(returns_series)
            volatility = self._calculate_volatility(returns_series)
            sharpe_ratio = self._calculate_sharpe_ratio(returns_series, volatility)
            max_drawdown = self._calculate_max_drawdown(returns_series)

            return ReturnsData(
                strategy_id=strategy_id,
                timeframe=timeframe,
                data=time_series,
                total_return=Decimal(str(total_return)),
                annualized_return=Decimal(str(annualized_return)),
                volatility=Decimal(str(volatility)),
                sharpe_ratio=Decimal(str(sharpe_ratio)) if sharpe_ratio else None,
                max_drawdown=Decimal(str(max_drawdown))
            )

        except Exception as e:
            logger.error(f"Error generating returns series: {e}")
            raise


# Cache service for performance metrics
class PerformanceCacheService:
    """Cache service for performance calculations"""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.local_cache = {}

    async def get_cached_metrics(self, strategy_id: str, date: date) -> Optional[PerformanceMetrics]:
        """Get cached performance metrics"""
        cache_key = f"perf_metrics:{strategy_id}:{date.isoformat()}"

        # Try Redis first
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return PerformanceMetrics.parse_raw(cached)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        # Fallback to local cache
        return self.local_cache.get(cache_key)

    async def cache_metrics(
        self,
        strategy_id: str,
        date: date,
        metrics: PerformanceMetrics,
        ttl: int = 300  # 5 minutes
    ):
        """Cache performance metrics"""
        cache_key = f"perf_metrics:{strategy_id}:{date.isoformat()}"

        # Cache in Redis
        if self.redis:
            try:
                await self.redis.setex(cache_key, ttl, metrics.json())
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        # Cache locally
        self.local_cache[cache_key] = metrics