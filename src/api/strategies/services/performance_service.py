"""
Performance Analytics Service
性能分析服務

負責處理策略性能指標、分析和報告生成
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging

from ..repositories.strategy_repository import StrategyRepository
from ..repositories.execution_repository import ExecutionRepository
from ..utils.cache import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指標數據類"""
    strategy_id: str
    user_id: int
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    profitable_trades: int
    losing_trades: int
    avg_trade_return: float
    volatility: float
    calmar_ratio: float
    sortino_ratio: float
    var_95: float  # 95% Value at Risk
    cvar_95: float  # 95% Conditional Value at Risk
    time_range: str
    last_updated: datetime


@dataclass
class TradeRecord:
    """交易記錄數據類"""
    execution_id: str
    trade_id: str
    timestamp: datetime
    symbol: str
    action: str  # BUY or SELL
    quantity: float
    price: float
    value: float
    commission: float
    pnl: float
    strategy_id: str
    user_id: int


class PerformanceService:
    """
    性能分析服務
    提供全面的策略性能分析功能
    """

    def __init__(
        self,
        strategy_repo: StrategyRepository,
        execution_repo: ExecutionRepository,
        cache_manager: CacheManager
    ):
        self.strategy_repo = strategy_repo
        self.execution_repo = execution_repo
        self.cache = cache_manager
        self.metrics_cache_ttl = 300  # 5分鐘緩存

    async def calculate_strategy_performance(
        self,
        strategy_id: str,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PerformanceMetrics:
        """
        計算策略性能指標
        """
        # 檢查緩存
        cache_key = f"performance:{strategy_id}:{user_id}:{start_date}:{end_date}"
        cached_metrics = await self.cache.get(cache_key)
        if cached_metrics:
            return PerformanceMetrics(**cached_metrics)

        try:
            # 獲取交易記錄
            trades = await self._get_trade_records(strategy_id, user_id, start_date, end_date)

            if not trades:
                # 返回空指標
                return self._create_empty_metrics(strategy_id, user_id)

            # 計算基礎指標
            total_return, trades_data = self._calculate_returns(trades)

            # 計算統計指標
            returns_series = pd.Series([t['return'] for t in trades_data])

            # 性能指標
            annualized_return = self._calculate_annualized_return(
                total_return, start_date, end_date
            )
            sharpe_ratio = self._calculate_sharpe_ratio(returns_series)
            sortino_ratio = self._calculate_sortino_ratio(returns_series)
            max_drawdown = self._calculate_max_drawdown(returns_series)
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

            # 交易統計
            win_rate = self._calculate_win_rate(trades_data)
            profit_factor = self._calculate_profit_factor(trades_data)
            avg_trade_return = returns_series.mean()

            # 風險指標
            volatility = returns_series.std() * np.sqrt(252)  # 年化波動率
            var_95 = returns_series.quantile(0.05)
            cvar_95 = returns_series[returns_series <= var_95].mean()

            # 創建性能指標對象
            metrics = PerformanceMetrics(
                strategy_id=strategy_id,
                user_id=user_id,
                total_return=total_return,
                annualized_return=annualized_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
                total_trades=len(trades_data),
                profitable_trades=len([t for t in trades_data if t['return'] > 0]),
                losing_trades=len([t for t in trades_data if t['return'] < 0]),
                avg_trade_return=avg_trade_return,
                volatility=volatility,
                calmar_ratio=calmar_ratio,
                sortino_ratio=sortino_ratio,
                var_95=var_95,
                cvar_95=cvar_95,
                time_range=self._get_time_range_text(start_date, end_date),
                last_updated=datetime.utcnow()
            )

            # 緩存結果
            await self.cache.set(cache_key, metrics.__dict__, ttl=self.metrics_cache_ttl)

            return metrics

        except Exception as e:
            logger.error(f"計算策略性能失敗: {e}")
            raise

    async def get_performance_comparison(
        self,
        strategy_ids: List[str],
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        獲取多個策略的對比分析
        """
        metrics_list = []

        for strategy_id in strategy_ids:
            try:
                metrics = await self.calculate_strategy_performance(
                    strategy_id, user_id, start_date, end_date
                )
                metrics_list.append(metrics)
            except Exception as e:
                logger.error(f"獲取策略 {strategy_id} 性能失敗: {e}")
                continue

        if not metrics_list:
            raise ValueError("沒有可用的策略性能數據")

        # 生成對比報告
        comparison = {
            "strategies": [m.strategy_id for m in metrics_list],
            "metrics": {
                "total_return": {m.strategy_id: m.total_return for m in metrics_list},
                "sharpe_ratio": {m.strategy_id: m.sharpe_ratio for m in metrics_list},
                "max_drawdown": {m.strategy_id: m.max_drawdown for m in metrics_list},
                "win_rate": {m.strategy_id: m.win_rate for m in metrics_list},
                "profit_factor": {m.strategy_id: m.profit_factor for m in metrics_list}
            },
            "rankings": self._rank_strategies(metrics_list),
            "correlation_matrix": await self._calculate_correlation_matrix(
                strategy_ids, user_id, start_date, end_date
            )
        }

        return comparison

    async def generate_performance_report(
        self,
        strategy_id: str,
        user_id: int,
        report_type: str = "summary",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        生成性能報告
        """
        metrics = await self.calculate_strategy_performance(
            strategy_id, user_id, start_date, end_date
        )

        if report_type == "summary":
            return self._generate_summary_report(metrics)
        elif report_type == "detailed":
            return await self._generate_detailed_report(
                strategy_id, user_id, metrics, start_date, end_date
            )
        elif report_type == "monthly":
            return await self._generate_monthly_report(
                strategy_id, user_id, start_date, end_date
            )
        else:
            raise ValueError(f"不支持的報告類型: {report_type}")

    async def _get_trade_records(
        self,
        strategy_id: str,
        user_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[TradeRecord]:
        """
        獲取交易記錄
        """
        # 從執行倉庫獲取交易數據
        executions = await self.execution_repo.get_strategy_executions(
            strategy_id, user_id, start_date, end_date
        )

        trades = []
        for execution in executions:
            execution_trades = await self.execution_repo.get_execution_trades(
                execution.id
            )
            for trade_data in execution_trades:
                trades.append(TradeRecord(
                    execution_id=execution.id,
                    trade_id=trade_data.get('trade_id'),
                    timestamp=trade_data.get('timestamp'),
                    symbol=trade_data.get('symbol'),
                    action=trade_data.get('action'),
                    quantity=trade_data.get('quantity'),
                    price=trade_data.get('price'),
                    value=trade_data.get('value'),
                    commission=trade_data.get('commission', 0),
                    pnl=trade_data.get('pnl', 0),
                    strategy_id=strategy_id,
                    user_id=user_id
                ))

        return trades

    def _calculate_returns(
        self,
        trades: List[TradeRecord]
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        計算回報率和交易數據
        """
        if not trades:
            return 0.0, []

        # 按時間排序
        trades.sort(key=lambda x: x.timestamp)

        # 計算每個交易的回報率
        trades_data = []
        total_pnl = 0
        total_value = 0

        for i, trade in enumerate(trades):
            if trade.action == "SELL" and i > 0:
                # 找到對應的買入交易
                buy_price = None
                for j in range(i - 1, -1, -1):
                    if trades[j].action == "BUY" and trades[j].symbol == trade.symbol:
                        buy_price = trades[j].price
                        break

                if buy_price:
                    trade_return = (trade.price - buy_price) / buy_price
                    trades_data.append({
                        'timestamp': trade.timestamp,
                        'return': trade_return,
                        'pnl': trade.pnl,
                        'value': trade.value
                    })
                    total_pnl += trade.pnl
                    total_value += trade.value

        total_return = total_pnl / total_value if total_value > 0 else 0

        return total_return, trades_data

    def _calculate_annualized_return(
        self,
        total_return: float,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> float:
        """
        計算年化回報率
        """
        if not start_date or not end_date:
            return total_return * 252  # 假設每日回報

        days = (end_date - start_date).days
        if days <= 0:
            return 0

        years = days / 365.25
        return (1 + total_return) ** (1 / years) - 1

    def _calculate_sharpe_ratio(
        self,
        returns_series: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        計算夏普比率
        """
        if len(returns_series) < 2:
            return 0

        excess_returns = returns_series - risk_free_rate / 252

        if excess_returns.std() == 0:
            return 0

        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)

    def _calculate_sortino_ratio(
        self,
        returns_series: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        計算索提諾比率（只考慮下行風險）
        """
        if len(returns_series) < 2:
            return 0

        excess_returns = returns_series - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return float('inf') if excess_returns.mean() > 0 else 0

        return excess_returns.mean() / downside_returns.std() * np.sqrt(252)

    def _calculate_max_drawdown(self, returns_series: pd.Series) -> float:
        """
        計算最大回撤
        """
        if len(returns_series) == 0:
            return 0

        cumulative = (1 + returns_series).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        return drawdown.min()

    def _calculate_win_rate(self, trades_data: List[Dict[str, Any]]) -> float:
        """
        計算勝率
        """
        if not trades_data:
            return 0

        winning_trades = len([t for t in trades_data if t['return'] > 0])
        return winning_trades / len(trades_data)

    def _calculate_profit_factor(
        self,
        trades_data: List[Dict[str, Any]]
    ) -> float:
        """
        計算盈利因子（總盈利/總虧損）
        """
        if not trades_data:
            return 0

        gross_profit = sum(t['pnl'] for t in trades_data if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in trades_data if t['pnl'] < 0))

        return gross_profit / gross_loss if gross_loss > 0 else float('inf')

    def _create_empty_metrics(self, strategy_id: str, user_id: int) -> PerformanceMetrics:
        """
        創建空的性能指標
        """
        return PerformanceMetrics(
            strategy_id=strategy_id,
            user_id=user_id,
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            total_trades=0,
            profitable_trades=0,
            losing_trades=0,
            avg_trade_return=0.0,
            volatility=0.0,
            calmar_ratio=0.0,
            sortino_ratio=0.0,
            var_95=0.0,
            cvar_95=0.0,
            time_range="無數據",
            last_updated=datetime.utcnow()
        )

    def _get_time_range_text(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> str:
        """
        獲取時間範圍文本描述
        """
        if not start_date or not end_date:
            return "全部"

        days = (end_date - start_date).days
        if days <= 7:
            return "1周"
        elif days <= 30:
            return "1月"
        elif days <= 90:
            return "3月"
        elif days <= 365:
            return "1年"
        else:
            return f"{days}天"

    def _rank_strategies(
        self,
        metrics_list: List[PerformanceMetrics]
    ) -> Dict[str, Dict[str, int]]:
        """
        對策略進行排名
        """
        rankings = {}

        # 按不同指標排名
        metrics_to_rank = [
            ("total_return", "總回報率"),
            ("sharpe_ratio", "夏普比率"),
            ("max_drawdown", "最大回撤（越小越好）"),
            ("win_rate", "勝率"),
            ("profit_factor", "盈利因子")
        ]

        for metric_key, metric_name in metrics_to_rank:
            if metric_key == "max_drawdown":
                # 回撤越小越好
                sorted_metrics = sorted(metrics_list, key=lambda x: getattr(x, metric_key))
            else:
                # 其他指標越大越好
                sorted_metrics = sorted(metrics_list, key=lambda x: getattr(x, metric_key), reverse=True)

            rankings[metric_name] = {
                m.strategy_id: i + 1 for i, m in enumerate(sorted_metrics)
            }

        return rankings

    async def _calculate_correlation_matrix(
        self,
        strategy_ids: List[str],
        user_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """
        計算策略回報率相關性矩陣
        """
        returns_data = {}

        for strategy_id in strategy_ids:
            try:
                trades = await self._get_trade_records(
                    strategy_id, user_id, start_date, end_date
                )
                _, trades_data = self._calculate_returns(trades)

                if trades_data:
                    df = pd.DataFrame(trades_data)
                    df.set_index('timestamp', inplace=True)
                    returns_data[strategy_id] = df['return']
            except Exception as e:
                logger.error(f"計算策略 {strategy_id} 相關性失敗: {e}")
                continue

        if len(returns_data) < 2:
            return {"error": "需要至少2個策略的數據"}

        # 創建相關性矩陣
        df_returns = pd.DataFrame(returns_data)
        correlation_matrix = df_returns.corr()

        return {
            "strategies": list(returns_data.keys()),
            "matrix": correlation_matrix.to_dict(),
            "avg_correlation": correlation_matrix.values[
                np.triu_indices_from(correlation_matrix.values, k=1)
            ].mean()
        }

    def _generate_summary_report(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """
        生成摘要報告
        """
        return {
            "strategy_id": metrics.strategy_id,
            "summary": {
                "總回報率": f"{metrics.total_return:.2%}",
                "年化回報率": f"{metrics.annualized_return:.2%}",
                "夏普比率": f"{metrics.sharpe_ratio:.2f}",
                "最大回撤": f"{metrics.max_drawdown:.2%}",
                "勝率": f"{metrics.win_rate:.2%}",
                "盈利因子": f"{metrics.profit_factor:.2f}",
                "總交易次數": metrics.total_trades
            },
            "risk_metrics": {
                "波動率": f"{metrics.volatility:.2%}",
                "索提諾比率": f"{metrics.sortino_ratio:.2f}",
                "卡爾瑪比率": f"{metrics.calmar_ratio:.2f}",
                "VaR(95%)": f"{metrics.var_95:.2%}",
                "CVaR(95%)": f"{metrics.cvar_95:.2%}"
            },
            "last_updated": metrics.last_updated.isoformat()
        }

    async def _generate_detailed_report(
        self,
        strategy_id: str,
        user_id: int,
        metrics: PerformanceMetrics,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """
        生成詳細報告
        """
        # 獲取詳細交易數據
        trades = await self._get_trade_records(
            strategy_id, user_id, start_date, end_date
        )

        # 按月分組統計
        monthly_stats = self._calculate_monthly_stats(trades)

        # 按標的分組統計
        symbol_stats = self._calculate_symbol_stats(trades)

        return {
            "summary": self._generate_summary_report(metrics),
            "monthly_performance": monthly_stats,
            "symbol_performance": symbol_stats,
            "trade_analysis": {
                "avg_trade_duration": self._calculate_avg_trade_duration(trades),
                "best_trade": self._find_best_trade(trades),
                "worst_trade": self._find_worst_trade(trades),
                "consecutive_wins": self._calculate_consecutive_wins(trades),
                "consecutive_losses": self._calculate_consecutive_losses(trades)
            }
        }

    def _calculate_monthly_stats(
        self,
        trades: List[TradeRecord]
    ) -> List[Dict[str, Any]]:
        """
        計算月度統計
        """
        if not trades:
            return []

        df = pd.DataFrame([{
            'date': t.timestamp.replace(day=1),
            'pnl': t.pnl,
            'return': t.pnl / t.value if t.value > 0 else 0
        } for t in trades if t.action == 'SELL'])

        monthly_stats = df.groupby('date').agg({
            'pnl': 'sum',
            'return': 'mean'
        }).reset_index()

        return monthly_stats.to_dict('records')

    def _calculate_symbol_stats(
        self,
        trades: List[TradeRecord]
    ) -> List[Dict[str, Any]]:
        """
        計算標的統計
        """
        if not trades:
            return []

        symbol_trades = {}
        for trade in trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = {
                    'pnl': 0,
                    'trades': 0,
                    'wins': 0
                }

            symbol_trades[trade.symbol]['pnl'] += trade.pnl
            symbol_trades[trade.symbol]['trades'] += 1
            if trade.pnl > 0:
                symbol_trades[trade.symbol]['wins'] += 1

        stats = []
        for symbol, data in symbol_trades.items():
            stats.append({
                'symbol': symbol,
                'total_pnl': data['pnl'],
                'trades': data['trades'],
                'win_rate': data['wins'] / data['trades'] if data['trades'] > 0 else 0
            })

        return sorted(stats, key=lambda x: x['total_pnl'], reverse=True)

    def _calculate_avg_trade_duration(self, trades: List[TradeRecord]) -> float:
        """計算平均持倉時間（天）"""
        # 簡化實現，實際需要匹配買賣對
        return 0.0

    def _find_best_trade(self, trades: List[TradeRecord]) -> Dict[str, Any]:
        """找到最佳交易"""
        sell_trades = [t for t in trades if t.action == 'SELL']
        if not sell_trades:
            return {}

        best = max(sell_trades, key=lambda x: x.pnl)
        return {
            'symbol': best.symbol,
            'pnl': best.pnl,
            'return': best.pnl / best.value if best.value > 0 else 0,
            'date': best.timestamp.isoformat()
        }

    def _find_worst_trade(self, trades: List[TradeRecord]) -> Dict[str, Any]:
        """找到最差交易"""
        sell_trades = [t for t in trades if t.action == 'SELL']
        if not sell_trades:
            return {}

        worst = min(sell_trades, key=lambda x: x.pnl)
        return {
            'symbol': worst.symbol,
            'pnl': worst.pnl,
            'return': worst.pnl / worst.value if worst.value > 0 else 0,
            'date': worst.timestamp.isoformat()
        }

    def _calculate_consecutive_wins(self, trades: List[TradeRecord]) -> int:
        """計算最大連續盈利次數"""
        max_consecutive = 0
        current = 0

        for trade in trades:
            if trade.action == 'SELL' and trade.pnl > 0:
                current += 1
                max_consecutive = max(max_consecutive, current)
            elif trade.action == 'SELL':
                current = 0

        return max_consecutive

    def _calculate_consecutive_losses(self, trades: List[TradeRecord]) -> int:
        """計算最大連續虧損次數"""
        max_consecutive = 0
        current = 0

        for trade in trades:
            if trade.action == 'SELL' and trade.pnl < 0:
                current += 1
                max_consecutive = max(max_consecutive, current)
            elif trade.action == 'SELL':
                current = 0

        return max_consecutive

    async def _generate_monthly_report(
        self,
        strategy_id: str,
        user_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """
        生成月度報告
        """
        # 獲取月度性能數據
        monthly_data = await self._get_monthly_performance_data(
            strategy_id, user_id, start_date, end_date
        )

        return {
            "strategy_id": strategy_id,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "monthly_data": monthly_data,
            "summary": {
                "total_months": len(monthly_data),
                "profitable_months": len([m for m in monthly_data if m['return'] > 0]),
                "avg_monthly_return": np.mean([m['return'] for m in monthly_data]) if monthly_data else 0,
                "best_month": max(monthly_data, key=lambda x: x['return']) if monthly_data else None,
                "worst_month": min(monthly_data, key=lambda x: x['return']) if monthly_data else None
            }
        }

    async def _get_monthly_performance_data(
        self,
        strategy_id: str,
        user_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """
        獲取月度性能數據
        """
        # 這裡應該從數據庫獲取預計算的月度數據
        # 簡化實現
        return []