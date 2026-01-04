"""
Strategy Backtesting and Evaluation Tool
策略回測和評估工具

提供完整的策略回測功能：
- 歷史數據回測
- 績效評估
- 風險分析
- 可視化報告
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass, field
import logging
from concurrent.futures import ProcessPoolExecutor
import warnings
warnings.filterwarnings('ignore')

from .quant_strategy_framework import (
    QuantStrategyBase, StrategyManager, Signal, Position
)
from .data_provider import get_data_provider

logger = logging.getLogger('Backtester')

@dataclass
class BacktestConfig:
    """回測配置"""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 1000000
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005  # 0.05%
    benchmark: Optional[str] = None  # 基準標的
    rebalance_frequency: str = 'daily'  # 'daily', 'weekly', 'monthly'
    allow_short: bool = True
    position_limit: float = 1.0  # 最大倉位比例
    stop_loss: Optional[float] = None  # 止損比例
    take_profit: Optional[float] = None  # 止盈比例

@dataclass
class BacktestResult:
    """回測結果"""
    strategy_name: str
    start_date: datetime
    end_date: datetime

    # 績效指標
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0

    # 交易統計
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    # 其他指標
    beta: float = 0.0
    alpha: float = 0.0
    information_ratio: float = 0.0

    # 詳細數據
    equity_curve: pd.Series = field(default_factory=pd.Series)
    positions: List[Dict] = field(default_factory=list)
    trades: List[Dict] = field(default_factory=list)
    daily_returns: pd.Series = field(default_factory=pd.Series)

class BacktestEngine:
    """回測引擎"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.data_provider = get_data_provider()
        self.strategy_manager = StrategyManager()
        self.results: List[BacktestResult] = []

    def add_strategy(self, strategy: QuantStrategyBase):
        """添加策略到回測"""
        self.strategy_manager.register_strategy(strategy)

    async def run_backtest(self, strategy: QuantStrategyBase) -> BacktestResult:
        """運行單個策略回測"""
        logger.info(f"開始回測策略: {strategy.config.name}")

        # 獲取歷史數據
        data = await self.data_provider.get_market_data(
            symbols=strategy.config.symbols,
            start_date=self.config.start_date - timedelta(days=100),  # 多獲取一些數據用於計算指標
            end_date=self.config.end_date,
            timeframe=strategy.config.timeframe
        )

        if data.empty:
            raise ValueError(f"未獲取到數據: {strategy.config.symbols}")

        # 初始化策略
        if not strategy.initialize():
            raise RuntimeError(f"策略初始化失敗: {strategy.config.name}")

        # 準備回測數據
        backtest_data = data.loc[self.config.start_date:self.config.end_date].copy()

        # 初始化回測變量
        capital = self.config.initial_capital
        positions = {}
        trades = []
        equity_curve = []

        # 逐步回測
        for date, row in backtest_data.iterrows():
            # 更新當前價格到持倉
            self._update_positions_price(positions, row, strategy.config.symbols)

            # 生成信號
            signals = strategy.generate_signals(backtest_data.loc[:date])

            # 執行交易
            for signal in signals:
                trade_result = self._execute_trade(
                    signal, positions, capital, row
                )
                if trade_result:
                    trades.append(trade_result)

            # 計算當天總資產
            total_value = self._calculate_total_value(positions, capital)
            equity_curve.append(total_value)

        # 計算績效指標
        result = self._calculate_performance_metrics(
            strategy.config.name,
            equity_curve,
            trades,
            backtest_data
        )

        logger.info(f"策略 {strategy.config.name} 回測完成")
        return result

    def _update_positions_price(self, positions: Dict, row: pd.Series, symbols: List[str]):
        """更新持倉的當前價格"""
        for symbol in symbols:
            close_col = f'close_{symbol}'
            if symbol in positions and close_col in row:
                positions[symbol]['current_price'] = row[close_col]

    def _execute_trade(
        self,
        signal: Signal,
        positions: Dict,
        capital: float,
        row: pd.Series
    ) -> Optional[Dict]:
        """執行交易"""
        symbol = signal.symbol
        close_col = f'close_{symbol}'

        if close_col not in row:
            return None

        price = row[close_col]

        # 計算交易數量
        trade_value = capital * self.config.position_limit * signal.strength
        quantity = trade_value / price

        # 應用滑點
        execution_price = price * (1 + self.config.slippage_rate if signal.signal_type.value == 'buy' else -self.config.slippage_rate)

        # 計算手續費
        commission = trade_value * self.config.commission_rate

        # 執行交易
        if symbol not in positions:
            positions[symbol] = {
                'quantity': 0,
                'avg_price': 0,
                'total_cost': 0
            }

        current_pos = positions[symbol]
        trade_record = {
            'date': signal.timestamp,
            'symbol': symbol,
            'action': signal.signal_type.value,
            'quantity': quantity,
            'price': execution_price,
            'commission': commission,
            'signal_strength': signal.strength
        }

        if signal.signal_type.value in ['buy', 'sell']:
            # 開倉
            new_quantity = current_pos['quantity'] + (quantity if signal.signal_type.value == 'buy' else -quantity)
            current_pos['quantity'] = new_quantity

            if signal.signal_type.value == 'buy':
                current_pos['total_cost'] += quantity * execution_price + commission
            else:
                current_pos['total_cost'] -= quantity * execution_price + commission

            if new_quantity != 0:
                current_pos['avg_price'] = current_pos['total_cost'] / abs(new_quantity)

        elif signal.signal_type.value == 'close':
            # 平倉
            if current_pos['quantity'] != 0:
                pnl = (execution_price - current_pos['avg_price']) * abs(current_pos['quantity'])
                pnl -= commission  # 減去平倉手續費

                trade_record['pnl'] = pnl
                trade_record['avg_price'] = current_pos['avg_price']

                # 重置持倉
                positions[symbol] = {
                    'quantity': 0,
                    'avg_price': 0,
                    'total_cost': 0
                }

        return trade_record

    def _calculate_total_value(self, positions: Dict, cash: float) -> float:
        """計算總資產"""
        total = cash
        for pos in positions.values():
            if pos['quantity'] != 0 and 'current_price' in pos:
                total += pos['quantity'] * pos['current_price']
        return total

    def _calculate_performance_metrics(
        self,
        strategy_name: str,
        equity_curve: List[float],
        trades: List[Dict],
        data: pd.DataFrame
    ) -> BacktestResult:
        """計算績效指標"""
        # 轉換為pandas Series
        equity_series = pd.Series(equity_curve, index=data.index[:len(equity_curve)])

        # 計算收益率
        returns = equity_series.pct_change().dropna()

        # 基本績效指標
        total_return = (equity_series.iloc[-1] / equity_series.iloc[0] - 1)
        days = (equity_series.index[-1] - equity_series.index[0]).days
        annualized_return = (1 + total_return) ** (252 / days) - 1
        volatility = returns.std() * np.sqrt(252)

        # 風險調整收益
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252)
        sortino_ratio = annualized_return / downside_volatility if downside_volatility > 0 else 0

        # 最大回撤
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdowns = cumulative_returns / running_max - 1
        max_drawdown = drawdowns.min()

        # Calmar比率
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 交易統計
        total_trades = len(trades)
        winning_trades = len([t for t in trades if 'pnl' in t and t['pnl'] > 0])
        losing_trades = len([t for t in trades if 'pnl' in t and t['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        avg_win = np.mean([t['pnl'] for t in trades if 'pnl' in t and t['pnl'] > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t['pnl'] for t in trades if 'pnl' in t and t['pnl'] < 0]) if losing_trades > 0 else 0

        gross_profit = sum([t['pnl'] for t in trades if 'pnl' in t and t['pnl'] > 0])
        gross_loss = abs(sum([t['pnl'] for t in trades if 'pnl' in t and t['pnl'] < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # 與基準比較（如果有）
        beta = 0.0
        alpha = 0.0
        information_ratio = 0.0

        if self.config.benchmark and f'close_{self.config.benchmark}' in data.columns:
            benchmark_returns = data[f'close_{self.config.benchmark}'].pct_change().dropna()
            benchmark_returns = benchmark_returns.reindex(returns.index, method='ffill').dropna()

            if len(benchmark_returns) == len(returns):
                covariance = np.cov(returns, benchmark_returns)[0, 1]
                benchmark_variance = np.var(benchmark_returns)
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
                alpha = annualized_return - beta * benchmark_returns.mean() * 252

                tracking_error = (returns - benchmark_returns).std() * np.sqrt(252)
                information_ratio = (annualized_return - benchmark_returns.mean() * 252) / tracking_error if tracking_error > 0 else 0

        return BacktestResult(
            strategy_name=strategy_name,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            beta=beta,
            alpha=alpha,
            information_ratio=information_ratio,
            equity_curve=equity_series,
            trades=trades,
            daily_returns=returns
        )

class BacktestAnalyzer:
    """回測分析器"""

    @staticmethod
    def generate_report(result: BacktestResult, save_path: Optional[str] = None) -> str:
        """生成回測報告"""
        report = f"""
# {result.strategy_name} 回測報告

## 基本信息
- 回測期間: {result.start_date.date()} 至 {result.end_date.date()}
- 初始資金: ${result.config.initial_capital:,.0f}

## 績效指標
- 總收益率: {result.total_return:.2%}
- 年化收益率: {result.annualized_return:.2%}
- 年化波動率: {result.volatility:.2%}
- 夏普比率: {result.sharpe_ratio:.2f}
- 索提諾比率: {result.sortino_ratio:.2f}
- 最大回撤: {result.max_drawdown:.2%}
- 卡爾瑪比率: {result.calmar_ratio:.2f}

## 交易統計
- 總交易次數: {result.total_trades}
- 獲利交易: {result.winning_trades}
- 虧損交易: {result.losing_trades}
- 勝率: {result.win_rate:.2%}
- 平均獲利: ${result.avg_win:,.2f}
- 平均虧損: ${result.avg_loss:,.2f}
- 盈虧比: {result.profit_factor:.2f}

## 風險指標
- Beta: {result.beta:.2f}
- Alpha: {result.alpha:.2%}
- 信息比率: {result.information_ratio:.2f}
"""

        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"報告已保存至: {save_path}")

        return report

    @staticmethod
    def plot_results(results: List[BacktestResult], save_path: Optional[str] = None):
        """繪製回測結果"""
        plt.style.use('seaborn')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # 1. 淨值曲線
        ax1 = axes[0, 0]
        for result in results:
            ax1.plot(result.equity_curve.index, result.equity_curve.values, label=result.strategy_name)
        ax1.set_title('淨值曲線')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('淨值')
        ax1.legend()
        ax1.grid(True)

        # 2. 回撤曲線
        ax2 = axes[0, 1]
        for result in results:
            cumulative_returns = (1 + result.daily_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdowns = cumulative_returns / running_max - 1
            ax2.fill_between(drawdowns.index, drawdowns.values, 0, alpha=0.3, label=result.strategy_name)
        ax2.set_title('回撤曲線')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('回撤')
        ax2.legend()
        ax2.grid(True)

        # 3. 績效指標對比
        ax3 = axes[1, 0]
        metrics = ['年化收益率', '夏普比率', '最大回撤', '勝率']
        x = np.arange(len(metrics))
        width = 0.2

        for i, result in enumerate(results):
            values = [
                result.annualized_return,
                result.sharpe_ratio,
                -result.max_drawdown,  # 回撤取負值以便比較
                result.win_rate
            ]
            ax3.bar(x + i * width, values, width, label=result.strategy_name)

        ax3.set_title('關鍵指標對比')
        ax3.set_xticks(x + width * len(results) / 2)
        ax3.set_xticklabels(metrics)
        ax3.legend()
        ax3.grid(True, axis='y')

        # 4. 收益分布
        ax4 = axes[1, 1]
        for result in results:
            ax4.hist(result.daily_returns, bins=50, alpha=0.5, label=result.strategy_name, density=True)
        ax4.set_title('日收益率分布')
        ax4.set_xlabel('收益率')
        ax4.set_ylabel('頻率')
        ax4.legend()
        ax4.grid(True)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"圖表已保存至: {save_path}")

        plt.show()

    @staticmethod
    def compare_strategies(results: List[BacktestResult]) -> pd.DataFrame:
        """比較多個策略"""
        comparison_data = []

        for result in results:
            comparison_data.append({
                '策略名稱': result.strategy_name,
                '總收益率': f"{result.total_return:.2%}",
                '年化收益率': f"{result.annualized_return:.2%}",
                '波動率': f"{result.volatility:.2%}",
                '夏普比率': f"{result.sharpe_ratio:.2f}",
                '最大回撤': f"{result.max_drawdown:.2%}",
                '交易次數': result.total_trades,
                '勝率': f"{result.win_rate:.2%}",
                '盈虧比': f"{result.profit_factor:.2f}"
            })

        return pd.DataFrame(comparison_data)

class PortfolioBacktester:
    """投資組合回測器"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.backtest_engine = BacktestEngine(config)

    async def run_portfolio_backtest(self, strategies: List[QuantStrategyBase], weights: List[float]) -> BacktestResult:
        """運行投資組合回測"""
        if len(strategies) != len(weights):
            raise ValueError("策略數量必須與權重數量相同")

        if abs(sum(weights) - 1.0) > 0.01:
            raise ValueError("權重總和必須為1")

        logger.info("開始投資組合回測")

        # 分配資金
        strategy_configs = []
        for strategy, weight in zip(strategies, weights):
            config = strategy.config
            config.initial_capital = self.config.initial_capital * weight
            strategy_configs.append(config)

        # 運行各策略回測
        results = []
        for strategy in strategies:
            result = await self.backtest_engine.run_backtest(strategy)
            results.append(result)

        # 合併結果
        portfolio_equity = None
        for result, weight in zip(results, weights):
            if portfolio_equity is None:
                portfolio_equity = result.equity_curve * weight
            else:
                portfolio_equity += result.equity_curve * weight

        # 創建投資組合結果
        portfolio_result = BacktestResult(
            strategy_name="投資組合",
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            equity_curve=portfolio_equity
        )

        # 計算組合績效指標
        returns = portfolio_equity.pct_change().dropna()
        portfolio_result.total_return = (portfolio_equity.iloc[-1] / portfolio_equity.iloc[0] - 1)
        days = (portfolio_equity.index[-1] - portfolio_equity.index[0]).days
        portfolio_result.annualized_return = (1 + portfolio_result.total_return) ** (252 / days) - 1
        portfolio_result.volatility = returns.std() * np.sqrt(252)
        portfolio_result.sharpe_ratio = portfolio_result.annualized_return / portfolio_result.volatility
        portfolio_result.daily_returns = returns

        # 計算最大回撤
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdowns = cumulative_returns / running_max - 1
        portfolio_result.max_drawdown = drawdowns.min()
        portfolio_result.calmar_ratio = portfolio_result.annualized_return / abs(portfolio_result.max_drawdown)

        logger.info("投資組合回測完成")
        return portfolio_result

# 便捷函數
async def quick_backtest(
    strategy: QuantStrategyBase,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 1000000
) -> BacktestResult:
    """快速回測便捷函數"""
    config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital
    )

    backtester = BacktestEngine(config)
    return await backtester.run_backtest(strategy)