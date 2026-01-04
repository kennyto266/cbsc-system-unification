"""
Business Metrics Collector
業務指標收集器

提供業務級別的指標收集，包括策略執行、交易、回測和用戶活躍度。

Usage:
    ```python
    from src.monitoring import get_business_monitor

    monitor = get_business_monitor()

    # Record business events
    monitor.record_strategy_execution("momentum", "success", 123.45)
    monitor.record_trade("AAPL", "buy", 100, 150.0)

    # Get business summary
    summary = monitor.get_summary()
    ```
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
from datetime import datetime, timedelta


class StrategyStatus(Enum):
    """策略狀態"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TradeSide(Enum):
    """交易方向"""
    BUY = "buy"
    SELL = "sell"


class BacktestStatus(Enum):
    """回測狀態"""
    COMPLETED = "completed"
    FAILED = "failed"
    RUNNING = "running"
    CANCELLED = "cancelled"


@dataclass
class StrategyExecution:
    """策略執行記錄"""
    timestamp: float
    strategy_type: str
    strategy_id: str
    status: StrategyStatus
    duration_seconds: float
    signals_generated: int
    trades_executed: int
    profit_loss: float = 0.0
    error_message: str = ""


@dataclass
class TradeRecord:
    """交易記錄"""
    timestamp: float
    symbol: str
    side: TradeSide
    quantity: float
    price: float
    value: float
    currency: str
    strategy_id: str
    order_id: str
    commission: float = 0.0


@dataclass
class BacktestExecution:
    """回測執行記錄"""
    timestamp: float
    backtest_id: str
    strategy_type: str
    status: BacktestStatus
    duration_seconds: float
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    return_percent: float
    sharpe_ratio: float = 0.0
    max_drawdown_percent: float = 0.0
    total_trades: int = 0


@dataclass
class UserActivity:
    """用戶活動記錄"""
    timestamp: float
    user_id: str
    action: str
    resource: str
    success: bool
    duration_ms: float = 0.0


@dataclass
class BusinessSnapshot:
    """業務快照"""
    timestamp: float
    total_strategies_run: int
    active_strategies: int
    total_trades: int
    total_trading_value: float
    total_profit_loss: float
    active_users_24h: int
    backtests_completed_24h: int


class BusinessMetricsCollector:
    """
    業務指標收集器

    收集業務級別的指標，包括策略執行、交易、回測和用戶活動。

    Attributes:
        history_size: 歷史數據保留數量
    """

    def __init__(self, history_size: int = 10000):
        self.history_size = history_size

        # History storage
        self._strategy_executions: deque = deque(maxlen=history_size)
        self._trades: deque = deque(maxlen=history_size)
        self._backtests: deque = deque(maxlen=history_size)
        self._user_activities: deque = deque(maxlen=history_size)

        # Current state
        self._active_strategies: Dict[str, Dict[str, Any]] = {}
        self._active_users: Dict[str, float] = {}  # user_id -> last_activity_time

        # Aggregated metrics
        self._strategy_counts: Dict[str, Dict[str, int]] = {}  # strategy_type -> status -> count
        self._symbol_volume: Dict[str, Dict[str, float]] = {}  # symbol -> side -> volume
        self._daily_pnl: Dict[str, float] = {}  # date -> profit_loss

    # Strategy Execution Methods
    def record_strategy_execution(self,
                                  strategy_type: str,
                                  strategy_id: str,
                                  status: StrategyStatus,
                                  duration_seconds: float,
                                  signals_generated: int = 0,
                                  trades_executed: int = 0,
                                  profit_loss: float = 0.0,
                                  error_message: str = ""):
        """記錄策略執行"""
        execution = StrategyExecution(
            timestamp=time.time(),
            strategy_type=strategy_type,
            strategy_id=strategy_id,
            status=status,
            duration_seconds=duration_seconds,
            signals_generated=signals_generated,
            trades_executed=trades_executed,
            profit_loss=profit_loss,
            error_message=error_message
        )

        self._strategy_executions.append(execution)
        self._update_strategy_counts(strategy_type, status)

        # Update daily PnL
        if profit_loss != 0:
            date = datetime.fromtimestamp(execution.timestamp).strftime('%Y-%m-%d')
            self._daily_pnl[date] = self._daily_pnl.get(date, 0) + profit_loss

    def strategy_started(self, strategy_id: str, strategy_type: str, config: Dict[str, Any] = None):
        """標記策略開始執行"""
        self._active_strategies[strategy_id] = {
            "type": strategy_type,
            "start_time": time.time(),
            "config": config or {}
        }

    def strategy_stopped(self, strategy_id: str, status: StrategyStatus = StrategyStatus.CANCELLED):
        """標記策略停止"""
        if strategy_id in self._active_strategies:
            strategy_info = self._active_strategies[strategy_id]
            duration = time.time() - strategy_info["start_time"]

            self.record_strategy_execution(
                strategy_type=strategy_info["type"],
                strategy_id=strategy_id,
                status=status,
                duration_seconds=duration
            )

            del self._active_strategies[strategy_id]

    # Trade Methods
    def record_trade(self,
                     symbol: str,
                     side: TradeSide,
                     quantity: float,
                     price: float,
                     strategy_id: str,
                     order_id: str,
                     currency: str = "HKD",
                     commission: float = 0.0):
        """記錄交易"""
        value = quantity * price
        trade = TradeRecord(
            timestamp=time.time(),
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            value=value,
            currency=currency,
            strategy_id=strategy_id,
            order_id=order_id,
            commission=commission
        )

        self._trades.append(trade)
        self._update_symbol_volume(symbol, side, quantity)

    # Backtest Methods
    def record_backtest(self,
                        backtest_id: str,
                        strategy_type: str,
                        status: BacktestStatus,
                        duration_seconds: float,
                        start_date: str,
                        end_date: str,
                        initial_capital: float,
                        final_value: float,
                        sharpe_ratio: float = 0.0,
                        max_drawdown_percent: float = 0.0,
                        total_trades: int = 0):
        """記錄回測執行"""
        return_percent = ((final_value - initial_capital) / initial_capital) * 100

        backtest = BacktestExecution(
            timestamp=time.time(),
            backtest_id=backtest_id,
            strategy_type=strategy_type,
            status=status,
            duration_seconds=duration_seconds,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=final_value,
            return_percent=return_percent,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_percent=max_drawdown_percent,
            total_trades=total_trades
        )

        self._backtests.append(backtest)

    # User Activity Methods
    def record_user_activity(self,
                             user_id: str,
                             action: str,
                             resource: str,
                             success: bool,
                             duration_ms: float = 0.0):
        """記錄用戶活動"""
        activity = UserActivity(
            timestamp=time.time(),
            user_id=user_id,
            action=action,
            resource=resource,
            success=success,
            duration_ms=duration_ms
        )

        self._user_activities.append(activity)
        self._active_users[user_id] = activity.timestamp

    def record_login(self, user_id: str, success: bool):
        """記錄用戶登錄"""
        self.record_user_activity(user_id, "login", "auth", success)

    def record_strategy_access(self, user_id: str, strategy_id: str):
        """記錄策略訪問"""
        self.record_user_activity(user_id, "view", f"strategy:{strategy_id}", True)

    def record_backtest_run(self, user_id: str, backtest_id: str):
        """記錄回測運行"""
        self.record_user_activity(user_id, "run", f"backtest:{backtest_id}", True)

    # Analytics Methods
    def get_strategy_summary(self) -> Dict[str, Any]:
        """獲取策略執行摘要"""
        summary = {
            "total_executions": len(self._strategy_executions),
            "active_strategies": len(self._active_strategies),
            "by_type": {},
            "by_status": {
                "success": 0,
                "failed": 0,
                "timeout": 0,
                "cancelled": 0
            },
            "avg_duration_seconds": 0,
            "total_pnl": 0
        }

        if self._strategy_executions:
            durations = [e.duration_seconds for e in self._strategy_executions]
            summary["avg_duration_seconds"] = sum(durations) / len(durations)
            summary["total_pnl"] = sum(e.profit_loss for e in self._strategy_executions)

        for execution in self._strategy_executions:
            # Count by type
            if execution.strategy_type not in summary["by_type"]:
                summary["by_type"][execution.strategy_type] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0
                }
            summary["by_type"][execution.strategy_type]["total"] += 1
            summary["by_type"][execution.strategy_type][execution.status.value] += 1

            # Count by status
            summary["by_status"][execution.status.value] += 1

        return summary

    def get_trading_summary(self) -> Dict[str, Any]:
        """獲取交易摘要"""
        summary = {
            "total_trades": len(self._trades),
            "total_value": 0,
            "total_commission": 0,
            "by_symbol": {},
            "by_side": {
                "buy": {"count": 0, "value": 0},
                "sell": {"count": 0, "value": 0}
            }
        }

        for trade in self._trades:
            summary["total_value"] += trade.value
            summary["total_commission"] += trade.commission

            # By symbol
            if trade.symbol not in summary["by_symbol"]:
                summary["by_symbol"][trade.symbol] = {
                    "count": 0,
                    "value": 0,
                    "volume": 0
                }
            summary["by_symbol"][trade.symbol]["count"] += 1
            summary["by_symbol"][trade.symbol]["value"] += trade.value
            summary["by_symbol"][trade.symbol]["volume"] += trade.quantity

            # By side
            summary["by_side"][trade.side.value]["count"] += 1
            summary["by_side"][trade.side.value]["value"] += trade.value

        return summary

    def get_backtest_summary(self) -> Dict[str, Any]:
        """獲取回測摘要"""
        summary = {
            "total_backtests": len(self._backtests),
            "completed": 0,
            "failed": 0,
            "avg_return_percent": 0,
            "avg_duration_seconds": 0,
            "by_strategy_type": {}
        }

        completed_backtests = [b for b in self._backtests if b.status == BacktestStatus.COMPLETED]
        if completed_backtests:
            summary["avg_return_percent"] = sum(b.return_percent for b in completed_backtests) / len(completed_backtests)
            summary["avg_duration_seconds"] = sum(b.duration_seconds for b in self._backtests) / len(self._backtests)

        for backtest in self._backtests:
            if backtest.status == BacktestStatus.COMPLETED:
                summary["completed"] += 1
            else:
                summary["failed"] += 1

            if backtest.strategy_type not in summary["by_strategy_type"]:
                summary["by_strategy_type"][backtest.strategy_type] = {
                    "count": 0,
                    "avg_return": 0
                }
            type_summary = summary["by_strategy_type"][backtest.strategy_type]
            type_summary["count"] += 1
            if backtest.status == BacktestStatus.COMPLETED:
                type_summary["avg_return"] = (
                    (type_summary["avg_return"] * (type_summary["count"] - 1) + backtest.return_percent)
                    / type_summary["count"]
                )

        return summary

    def get_user_summary(self) -> Dict[str, Any]:
        """獲取用戶活動摘要"""
        # Clean up inactive users (>24 hours)
        cutoff_time = time.time() - 86400
        self._active_users = {
            user_id: last_time
            for user_id, last_time in self._active_users.items()
            if last_time > cutoff_time
        }

        summary = {
            "total_activities": len(self._user_activities),
            "active_users_24h": len(self._active_users),
            "by_action": {},
            "success_rate": 0
        }

        successful = sum(1 for a in self._user_activities if a.success)
        if self._user_activities:
            summary["success_rate"] = successful / len(self._user_activities)

        for activity in self._user_activities:
            if activity.action not in summary["by_action"]:
                summary["by_action"][activity.action] = {"count": 0, "success": 0}
            summary["by_action"][activity.action]["count"] += 1
            if activity.success:
                summary["by_action"][activity.action]["success"] += 1

        return summary

    def get_daily_pnl(self, days: int = 30) -> List[Dict[str, Any]]:
        """獲取每日盈虧"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        return [
            {"date": date, "pnl": pnl}
            for date, pnl in sorted(self._daily_pnl.items())
            if date >= cutoff_date
        ]

    def get_top_performing_strategies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取表現最好的策略"""
        strategy_pnl: Dict[str, float] = {}

        for execution in self._strategy_executions:
            if execution.strategy_id not in strategy_pnl:
                strategy_pnl[execution.strategy_id] = 0
            strategy_pnl[execution.strategy_id] += execution.profit_loss

        sorted_strategies = sorted(
            [{"strategy_id": sid, "total_pnl": pnl} for sid, pnl in strategy_pnl.items()],
            key=lambda x: x["total_pnl"],
            reverse=True
        )

        return sorted_strategies[:limit]

    def get_summary(self) -> Dict[str, Any]:
        """獲取完整業務摘要"""
        return {
            "timestamp": time.time(),
            "strategies": self.get_strategy_summary(),
            "trading": self.get_trading_summary(),
            "backtests": self.get_backtest_summary(),
            "users": self.get_user_summary(),
            "daily_pnl": self.get_daily_pnl()
        }

    # Internal helper methods
    def _update_strategy_counts(self, strategy_type: str, status: StrategyStatus):
        """更新策略計數"""
        if strategy_type not in self._strategy_counts:
            self._strategy_counts[strategy_type] = {
                "success": 0,
                "failed": 0,
                "timeout": 0,
                "cancelled": 0
            }
        self._strategy_counts[strategy_type][status.value] += 1

    def _update_symbol_volume(self, symbol: str, side: TradeSide, quantity: float):
        """更新交易量統計"""
        if symbol not in self._symbol_volume:
            self._symbol_volume[symbol] = {"buy": 0, "sell": 0}
        self._symbol_volume[symbol][side.value] += quantity


# Global singleton
_business_monitor: Optional[BusinessMetricsCollector] = None


def get_business_monitor(history_size: int = 10000) -> BusinessMetricsCollector:
    """獲取全局業務監控單例"""
    global _business_monitor
    if _business_monitor is None:
        _business_monitor = BusinessMetricsCollector(history_size)
    return _business_monitor
