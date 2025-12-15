"""
Performance Analytics Service
Handles calculation of strategy performance metrics
"""

from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from ..models import (
    PerformanceMetricsResponse,
    HistoricalDataPoint,
    RealTimeMetrics
)


class PerformanceService:
    """Service for calculating strategy performance metrics"""

    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate

    async def calculate_performance(
        self,
        strategy_id: str,
        period: str,
        benchmark: Optional[str] = None,
        include_risk_metrics: bool = True,
        db: Session = None
    ) -> PerformanceMetricsResponse:
        """
        Calculate comprehensive performance metrics for a strategy

        Args:
            strategy_id: Strategy identifier
            period: Time period (1D, 1W, 1M, 3M, 6M, 1Y, ALL)
            benchmark: Optional benchmark symbol
            include_risk_metrics: Whether to include risk metrics
            db: Database session

        Returns:
            PerformanceMetricsResponse object
        """
        # Get date range for period
        end_date = datetime.now()
        start_date = self._get_start_date(period, end_date)

        # Fetch trades and positions data
        trades = await self._get_trades(strategy_id, start_date, end_date, db)
        positions = await self._get_positions(strategy_id, start_date, end_date, db)

        if not trades:
            # Return empty metrics if no data
            return PerformanceMetricsResponse(
                strategy_id=strategy_id,
                period=period,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                volatility=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                avg_trade_duration=0.0
            )

        # Calculate daily returns
        daily_returns = self._calculate_daily_returns(trades)
        portfolio_values = self._calculate_portfolio_values(trades, positions)

        # Basic metrics
        total_return = self._calculate_total_return(portfolio_values)
        volatility = self._calculate_volatility(daily_returns)
        max_drawdown = self._calculate_max_drawdown(portfolio_values)

        # Trade-based metrics
        win_rate, profit_factor = self._calculate_trade_metrics(trades)
        avg_trade_duration = self._calculate_avg_duration(trades)

        # Risk-adjusted metrics
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns) if include_risk_metrics else None
        sortino_ratio = self._calculate_sortino_ratio(daily_returns) if include_risk_metrics else None
        calmar_ratio = self._calculate_calmar_ratio(total_return, max_drawdown) if include_risk_metrics else None

        # Benchmark comparison
        beta = None
        alpha = None
        if benchmark and include_risk_metrics:
            beta, alpha = await self._calculate_benchmark_alpha(
                strategy_id, benchmark, start_date, end_date, db
            )

        return PerformanceMetricsResponse(
            strategy_id=strategy_id,
            period=period,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            volatility=volatility,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_trade_duration=avg_trade_duration,
            beta=beta,
            alpha=alpha
        )

    async def get_historical_data(
        self,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str,
        metrics: List[str],
        limit: int,
        offset: int,
        db: Session = None
    ) -> Tuple[List[HistoricalDataPoint], int]:
        """
        Get historical time-series data for a strategy

        Args:
            strategy_id: Strategy identifier
            start_date: Start date
            end_date: End date
            granularity: Data granularity
            metrics: Metrics to include
            limit: Max number of points
            offset: Pagination offset

        Returns:
            Tuple of (data points, total count)
        """
        # Get historical data based on granularity
        if granularity == "daily":
            data = await self._get_daily_data(
                strategy_id, start_date, end_date, metrics, db
            )
        elif granularity == "weekly":
            data = await self._get_weekly_data(
                strategy_id, start_date, end_date, metrics, db
            )
        elif granularity == "monthly":
            data = await self._get_monthly_data(
                strategy_id, start_date, end_date, metrics, db
            )
        else:
            raise ValueError(f"Invalid granularity: {granularity}")

        # Apply pagination
        total_count = len(data)
        paginated_data = data[offset:offset + limit]

        return paginated_data, total_count

    async def get_realtime_metrics(
        self,
        strategy_id: str,
        db: Session = None
    ) -> RealTimeMetrics:
        """
        Get real-time metrics for a strategy

        Args:
            strategy_id: Strategy identifier
            db: Database session

        Returns:
            RealTimeMetrics object
        """
        # Get current positions
        positions = await self._get_current_positions(strategy_id, db)

        # Get today's trades
        today_trades = await self._get_today_trades(strategy_id, db)

        # Calculate metrics
        current_positions = len(positions)
        total_exposure = sum(p['market_value'] for p in positions)
        leverage = total_exposure / max(total_exposure - sum(p['cash'] for p in positions), 1)

        daily_pnl = sum(t['pnl'] for t in today_trades)
        unrealized_pnl = sum(p['unrealized_pnl'] for p in positions)
        realized_pnl = sum(t['realized_pnl'] for t in today_trades)

        market_value = total_exposure

        return RealTimeMetrics(
            strategy_id=strategy_id,
            status="active",  # This should come from strategy status
            current_positions=current_positions,
            total_exposure=total_exposure,
            leverage=leverage,
            daily_pnl=daily_pnl,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            last_updated=datetime.now(),
            market_value=market_value
        )

    def _get_start_date(self, period: str, end_date: datetime) -> datetime:
        """Get start date based on period"""
        periods = {
            "1D": timedelta(days=1),
            "1W": timedelta(weeks=1),
            "1M": timedelta(days=30),
            "3M": timedelta(days=90),
            "6M": timedelta(days=180),
            "1Y": timedelta(days=365),
            "ALL": timedelta(days=3650)  # 10 years
        }
        return end_date - periods.get(period, timedelta(days=30))

    async def _get_trades(
        self,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> List[Dict]:
        """Fetch trades for the strategy"""
        query = text("""
            SELECT
                trade_id,
                symbol,
                side,
                quantity,
                price,
                executed_at,
                pnl,
                commission
            FROM trades
            WHERE strategy_id = :strategy_id
                AND executed_at BETWEEN :start_date AND :end_date
            ORDER BY executed_at ASC
        """)

        result = db.execute(
            query,
            {
                "strategy_id": strategy_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        return [dict(row) for row in result]

    async def _get_positions(
        self,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> List[Dict]:
        """Fetch position snapshots"""
        query = text("""
            SELECT
                date,
                symbol,
                quantity,
                market_value,
                cost_basis
            FROM position_snapshots
            WHERE strategy_id = :strategy_id
                AND date BETWEEN :start_date AND :end_date
            ORDER BY date ASC
        """)

        result = db.execute(
            query,
            {
                "strategy_id": strategy_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        return [dict(row) for row in result]

    def _calculate_daily_returns(self, trades: List[Dict]) -> List[float]:
        """Calculate daily returns from trades"""
        if not trades:
            return []

        # Group trades by date and calculate daily P&L
        daily_pnl = {}
        for trade in trades:
            date = trade['executed_at'].date()
            pnl = trade.get('pnl', 0)
            daily_pnl[date] = daily_pnl.get(date, 0) + pnl

        # Convert to returns
        returns = []
        for date, pnl in sorted(daily_pnl.items()):
            # Simplified return calculation
            daily_return = pnl / 100000  # Assume $100k base portfolio
            returns.append(daily_return)

        return returns

    def _calculate_portfolio_values(self, trades: List[Dict], positions: List[Dict]) -> List[float]:
        """Calculate portfolio value over time"""
        # This is a simplified calculation
        # In practice, you'd aggregate position values

        values = []
        running_value = 100000  # Starting value

        for trade in trades:
            running_value += trade.get('pnl', 0)
            values.append(running_value)

        return values

    def _calculate_total_return(self, portfolio_values: List[float]) -> float:
        """Calculate total return percentage"""
        if len(portfolio_values) < 2:
            return 0.0
        return ((portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]) * 100

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate annualized volatility"""
        if not returns:
            return 0.0

        returns_array = np.array(returns)
        volatility = np.std(returns_array) * np.sqrt(252)  # Annualized
        return volatility * 100

    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown percentage"""
        if len(portfolio_values) < 2:
            return 0.0

        values = np.array(portfolio_values)
        peak = np.maximum.accumulate(values)
        drawdown = (values - peak) / peak * 100
        return np.min(drawdown)

    def _calculate_trade_metrics(self, trades: List[Dict]) -> Tuple[float, float]:
        """Calculate win rate and profit factor"""
        if not trades:
            return 0.0, 0.0

        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]

        win_rate = (len(winning_trades) / len(trades)) * 100

        total_wins = sum(t.get('pnl', 0) for t in winning_trades)
        total_losses = abs(sum(t.get('pnl', 0) for t in losing_trades))

        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

        return win_rate, profit_factor

    def _calculate_avg_duration(self, trades: List[Dict]) -> float:
        """Calculate average trade duration in days"""
        if not trades:
            return 0.0

        # This is simplified - you'd need entry/exit timestamps
        return 2.4  # Placeholder

    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if not returns:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (self.risk_free_rate / 252)

        if np.std(excess_returns) == 0:
            return 0.0

        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return sharpe

    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio"""
        if not returns:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (self.risk_free_rate / 252)

        # Downside deviation
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return float('inf')

        downside_deviation = np.std(downside_returns)

        if downside_deviation == 0:
            return 0.0

        sortino = np.mean(excess_returns) / downside_deviation * np.sqrt(252)
        return sortino

    def _calculate_calmar_ratio(self, total_return: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio"""
        if max_drawdown == 0:
            return 0.0

        # Convert drawdown to positive for calculation
        drawdown_abs = abs(max_drawdown)
        return total_return / drawdown_abs

    async def _calculate_benchmark_alpha(
        self,
        strategy_id: str,
        benchmark: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> Tuple[float, float]:
        """Calculate beta and alpha relative to benchmark"""
        # This would fetch benchmark data and calculate beta/alpha
        # Simplified implementation
        return 0.85, 3.2

    async def _get_daily_data(
        self,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime,
        metrics: List[str],
        db: Session
    ) -> List[HistoricalDataPoint]:
        """Get daily historical data"""
        # Implementation would query daily aggregates
        query = text("""
            SELECT
                date,
                SUM(pnl) as value,
                COUNT(*) as trade_count
            FROM daily_aggregates
            WHERE strategy_id = :strategy_id
                AND date BETWEEN :start_date AND :end_date
            GROUP BY date
            ORDER BY date ASC
        """)

        result = db.execute(
            query,
            {
                "strategy_id": strategy_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        data = []
        for row in result:
            data.append(HistoricalDataPoint(
                date=row['date'],
                value=float(row['value']),
                positions=row['trade_count']
            ))

        return data

    async def _get_weekly_data(
        self,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime,
        metrics: List[str],
        db: Session
    ) -> List[HistoricalDataPoint]:
        """Get weekly aggregated data"""
        # Similar to daily but with GROUP BY week
        # Implementation omitted for brevity
        return await self._get_daily_data(strategy_id, start_date, end_date, metrics, db)

    async def _get_monthly_data(
        self,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime,
        metrics: List[str],
        db: Session
    ) -> List[HistoricalDataPoint]:
        """Get monthly aggregated data"""
        # Similar to daily but with GROUP BY month
        # Implementation omitted for brevity
        return await self._get_daily_data(strategy_id, start_date, end_date, metrics, db)

    async def _get_current_positions(self, strategy_id: str, db: Session) -> List[Dict]:
        """Get current positions for a strategy"""
        query = text("""
            SELECT
                symbol,
                quantity,
                market_value,
                cost_basis,
                unrealized_pnl,
                cash
            FROM current_positions
            WHERE strategy_id = :strategy_id
                AND quantity != 0
        """)

        result = db.execute(query, {"strategy_id": strategy_id})
        return [dict(row) for row in result]

    async def _get_today_trades(self, strategy_id: str, db: Session) -> List[Dict]:
        """Get today's trades for a strategy"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        query = text("""
            SELECT
                trade_id,
                symbol,
                pnl,
                commission,
                realized_pnl
            FROM trades
            WHERE strategy_id = :strategy_id
                AND executed_at >= :today
                AND executed_at < :tomorrow
        """)

        result = db.execute(
            query,
            {
                "strategy_id": strategy_id,
                "today": today,
                "tomorrow": tomorrow
            }
        )
        return [dict(row) for row in result]