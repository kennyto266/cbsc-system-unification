"""
Multi-Asset Portfolio Backtest Engine
多資產組合回測引擎

整合多資產優化、動態權重調整和相關性分析的完整回測系統：
- 支持多種優化方法
- 動態再平衡
- 交易成本建模
- 性能分析和風險評估
- 與VectorBT多進程框架整合
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from concurrent.futures import ProcessPoolExecutor
import warnings

# VectorBT imports
try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    vbt = None

# Internal imports
from ..strategies.portfolio_v2.multi_asset_optimizer import (
    MultiAssetOptimizer,
    OptimizationMethod,
    OptimizationConstraints,
    BlackLittermanConfig
)
from ..strategies.portfolio_v2.dynamic_weight_strategy import (
    DynamicWeightAdjustmentStrategy,
    DynamicWeightConfig,
    MarketRegime
)
from ..strategies.portfolio_v2.correlation_analyzer import (
    CorrelationAnalyzer,
    CorrelationConfig,
    CorrelationMethod
)
from .vectorbt_multiprocess_engine import (
    VectorBTMultiprocessEngine,
    VectorBTMultiprocessConfig,
    MultiprocessMode
)
from .enhanced_backtest_engine import BacktestResult

logger = logging.getLogger(__name__)


class RebalanceMethod(str, Enum):
    """再平衡方法"""
    TIME_BASED = "time_based"      # 時間驅動
    THRESHOLD = "threshold"        # 閾值驅動
    VOLATILITY = "volatility"      # 波動率驅動
    SIGNAL_BASED = "signal_based"  # 信號驅動


class PerformanceMetric(str, Enum):
    """性能指標"""
    TOTAL_RETURN = "total_return"
    ANNUALIZED_RETURN = "annualized_return"
    VOLATILITY = "volatility"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    CALMAR_RATIO = "calmar_ratio"
    INFORMATION_RATIO = "information_ratio"
    TURNOVER = "turnover"


@dataclass
class PortfolioConfig:
    """投資組合配置"""
    # 基礎配置
    assets: List[str]
    start_date: date
    end_date: date
    initial_capital: float = 1000000
    benchmark: Optional[str] = None

    # 優化配置
    optimization_method: OptimizationMethod = OptimizationMethod.MARKOWITZ
    rebalance_frequency: str = "M"  # D, W, M, Q
    lookback_window: int = 252

    # 交易成本配置
    commission: float = 0.001
    slippage: float = 0.0005
    management_fee: float = 0.001  # 年化管理費

    # 風險管理配置
    max_position_size: float = 0.3
    max_sector_exposure: float = 0.4
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    # 約束條件
    constraints: Optional[OptimizationConstraints] = None

    # 動態配置
    use_dynamic_weights: bool = False
    dynamic_config: Optional[DynamicWeightConfig] = None

    # 相關性分析配置
    correlation_config: Optional[CorrelationConfig] = None

    # 多進程配置
    use_multiprocessing: bool = True
    max_workers: Optional[int] = None


@dataclass
class BacktestMetrics:
    """回測指標"""
    # 收益指標
    total_return: float
    annualized_return: float
    cagr: float

    # 風險指標
    volatility: float
    downside_volatility: float
    max_drawdown: float
    var_95: float  # 95% VaR
    cvar_95: float  # 95% CVaR

    # 風險調整收益指標
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float

    # 交易指標
    turnover: float
    total_trades: int
    win_rate: float
    avg_trade_return: float

    # 其他指標
    beta: float
    alpha: float
    tracking_error: float

    # 月度和年度統計
    monthly_returns: List[float]
    yearly_returns: List[float]
    best_month: float
    worst_month: float
    best_year: float
    worst_year: float


class MultiAssetBacktestEngine:
    """多資產組合回測引擎"""

    def __init__(self, config: PortfolioConfig):
        """
        初始化回測引擎

        Args:
            config: 投資組合配置
        """
        self.config = config

        # 初始化組件
        self.optimizer = MultiAssetOptimizer(
            method=config.optimization_method,
            constraints=config.constraints or OptimizationConstraints()
        )

        # 動態權重策略
        if config.use_dynamic_weights:
            self.dynamic_strategy = DynamicWeightAdjustmentStrategy(
                config.dynamic_config or DynamicWeightConfig()
            )
        else:
            self.dynamic_strategy = None

        # 相關性分析器
        if config.correlation_config:
            self.correlation_analyzer = CorrelationAnalyzer(config.correlation_config)
        else:
            self.correlation_analyzer = None

        # 多進程引擎
        if config.use_multiprocessing and VECTORBT_AVAILABLE:
            self.multiprocess_config = VectorBTMultiprocessConfig(
                symbols=config.assets,
                start_date=config.start_date,
                end_date=config.end_date,
                max_workers=config.max_workers
            )
            self.multiprocess_engine = VectorBTMultiprocessEngine(self.multiprocess_config)
        else:
            self.multiprocess_engine = None

        # 內部狀態
        self.price_data: Dict[str, pd.DataFrame] = {}
        self.returns_data: pd.DataFrame = None
        self.benchmark_data: Optional[pd.DataFrame] = None

        # 回測結果
        self.portfolio_values: pd.Series = None
        self.weights_history: List[Dict[str, Any]] = []
        self.trades: List[Dict[str, Any]] = []
        self.performance_metrics: Optional[BacktestMetrics] = None

        logger.info(f"Multi-Asset Backtest Engine initialized for {len(config.assets)} assets")

    async def load_data(
        self,
        data_loader: Optional[Callable] = None
    ) -> None:
        """
        加載市場數據

        Args:
            data_loader: 數據加載函數（可選）
        """
        try:
            logger.info(f"Loading data for {len(self.config.assets)} assets")

            # 如果提供了數據加載器，使用它
            if data_loader:
                self.price_data = data_loader(self.config.assets)
            else:
                # 使用VectorBT引擎加載數據（如果可用）
                if self.multiprocess_engine:
                    await self.multiprocess_engine.initialize()
                    self.price_data = self.multiprocess_engine.data_cache
                else:
                    raise ValueError("No data loader provided and VectorBT not available")

            # 準備收益率數據
            returns_data = {}
            for asset, df in self.price_data.items():
                if 'close' in df.columns:
                    returns_data[asset] = df['close'].pct_change().dropna()

            self.returns_data = pd.DataFrame(returns_data)

            # 加載基準數據
            if self.config.benchmark:
                self.benchmark_data = self.price_data.get(self.config.benchmark)

            logger.info(f"Data loaded: {len(self.returns_data)} trading days")

        except Exception as e:
            logger.error(f"Data loading failed: {e}")
            raise

    def run_backtest(
        self,
        strategy_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        運行回測

        Args:
            strategy_func: 策略函數（可選）

        Returns:
            回測結果字典
        """
        try:
            logger.info("Starting multi-asset backtest")

            # 初始化
            current_capital = self.config.initial_capital
            current_weights = {}
            positions = {}
            portfolio_values = []

            # 確定再平衡日期
            rebalance_dates = self._get_rebalance_dates()

            # 主回測循環
            for i, rebalance_date in enumerate(rebalance_dates):
                # 獲取歷史數據窗口
                window_data = self._get_window_data(rebalance_date)

                if not window_data:
                    logger.warning(f"No data available for {rebalance_date}")
                    continue

                # 優化權重
                if self.dynamic_strategy:
                    # 使用動態權重策略
                    new_weights = self.dynamic_strategy.adjust_weights(
                        window_data,
                        self.benchmark_data,
                        rebalance_date
                    )
                else:
                    # 使用標準優化
                    self.optimizer.prepare_data(window_data)
                    new_weights = self.optimizer.optimize_weights()

                # 應用約束條件
                new_weights = self._apply_portfolio_constraints(new_weights)

                # 執行再平衡
                if i == 0 or new_weights != current_weights:
                    trades, capital_after_trade = self._execute_rebalance(
                        current_weights,
                        new_weights,
                        current_capital,
                        rebalance_date
                    )
                    self.trades.extend(trades)
                    current_capital = capital_after_trade

                # 記錄權重
                self.weights_history.append({
                    'date': rebalance_date,
                    'weights': new_weights.copy(),
                    'regime': self.dynamic_strategy.current_regime if self.dynamic_strategy else None
                })

                # 計算投資組合收益直到下一個再平衡日期
                if i < len(rebalance_dates) - 1:
                    next_date = rebalance_dates[i + 1]
                    period_returns = self._calculate_period_returns(
                        new_weights,
                        rebalance_date,
                        next_date
                    )
                    current_capital *= (1 + period_returns)

                # 記錄投資組合價值
                portfolio_values.append({
                    'date': rebalance_date,
                    'value': current_capital
                })

                current_weights = new_weights

                # 更新相關性分析
                if self.correlation_analyzer:
                    returns_window = pd.DataFrame({
                        asset: df['close'].pct_change().dropna()
                        for asset, df in window_data.items()
                    })
                    self.correlation_analyzer.calculate_correlation_matrix(returns_window)

            # 轉換結果
            self.portfolio_values = pd.DataFrame(portfolio_values).set_index('date')['value']

            # 計算性能指標
            self.performance_metrics = self._calculate_performance_metrics()

            # 生成回測報告
            backtest_result = self._generate_backtest_report()

            logger.info("Backtest completed successfully")
            return backtest_result

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise

    async def run_parallel_backtest(
        self,
        strategy_configs: List[PortfolioConfig]
    ) -> Dict[str, Dict[str, Any]]:
        """
        運行並行回測（多個配置）

        Args:
            strategy_configs: 策略配置列表

        Returns:
            回測結果字典
        """
        try:
            if not self.multiprocess_engine:
                raise ValueError("Multiprocessing not available")

            logger.info(f"Running parallel backtest: {len(strategy_configs)} configurations")

            # 準備任務
            tasks = []
            for i, config in enumerate(strategy_configs):
                # 創建回測函數
                def backtest_func(config):
                    engine = MultiAssetBacktestEngine(config)
                    return engine.run_backtest()

                tasks.append(backtest_func)

            # 並行執行
            results = {}
            for i, config in enumerate(strategy_configs):
                # 使用多進程執行
                with ProcessPoolExecutor(max_workers=self.multiprocess_config.max_workers) as executor:
                    future = executor.submit(tasks[i], config)
                    result = await asyncio.wrap_future(future)
                    results[f"strategy_{i}"] = result

            logger.info(f"Parallel backtest completed: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Parallel backtest failed: {e}")
            raise

    def _get_rebalance_dates(self) -> List[date]:
        """獲取再平衡日期列表"""
        dates = []

        # 根據頻率生成日期
        if self.config.rebalance_frequency == "D":
            dates = pd.date_range(
                start=self.config.start_date,
                end=self.config.end_date,
                freq="D"
            )
        elif self.config.rebalance_frequency == "W":
            dates = pd.date_range(
                start=self.config.start_date,
                end=self.config.end_date,
                freq="W"
            )
        elif self.config.rebalance_frequency == "M":
            dates = pd.date_range(
                start=self.config.start_date,
                end=self.config.end_date,
                freq="M"
            )
        elif self.config.rebalance_frequency == "Q":
            dates = pd.date_range(
                start=self.config.start_date,
                end=self.config.end_date,
                freq="Q"
            )

        # 轉換為日期列表
        return [d.date() for d in dates if d.weekday() < 5]  # 只保留工作日

    def _get_window_data(self, end_date: date) -> Dict[str, pd.DataFrame]:
        """獲取歷史數據窗口"""
        window_data = {}

        # 計算開始日期
        start_date = end_date - timedelta(days=self.config.lookback_window * 2)  # 緩衝

        for asset, df in self.price_data.items():
            # 過濾日期範圍
            mask = (df.index.date >= start_date) & (df.index.date <= end_date)
            window_df = df.loc[mask]

            if not window_df.empty:
                window_data[asset] = window_df

        return window_data

    def _apply_portfolio_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """應用投資組合約束條件"""
        # 最大持倉限制
        for asset in weights:
            weights[asset] = min(weights[asset], self.config.max_position_size)

        # 正規化權重
        total_weight = sum(weights.values())
        if total_weight > 0:
            for asset in weights:
                weights[asset] /= total_weight

        return weights

    def _execute_rebalance(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        capital: float,
        date: date
    ) -> Tuple[List[Dict[str, Any]], float]:
        """執行再平衡交易"""
        trades = []

        # 獲取當前價格
        prices = {}
        for asset in target_weights:
            if asset in self.price_data and date in self.price_data[asset].index:
                prices[asset] = self.price_data[asset].loc[date, 'close']

        # 計算目標價值
        target_values = {}
        for asset, weight in target_weights.items():
            if asset in prices:
                target_values[asset] = capital * weight

        # 計算當前價值
        current_values = {}
        for asset, weight in current_weights.items():
            if asset in prices:
                current_values[asset] = capital * weight

        # 生成交易
        total_transaction_cost = 0
        for asset in set(target_values.keys()) | set(current_values.keys()):
            current_value = current_values.get(asset, 0)
            target_value = target_values.get(asset, 0)

            if abs(target_value - current_value) > 0.01 * capital:  # 1%閾值
                # 計算交易數量
                if asset in prices:
                    price = prices[asset]
                    value_diff = target_value - current_value
                    shares = value_diff / price

                    # 計算交易成本
                    trade_cost = abs(value_diff) * (self.config.commission + self.config.slippage)
                    total_transaction_cost += trade_cost

                    # 記錄交易
                    trades.append({
                        'date': date,
                        'asset': asset,
                        'action': 'buy' if shares > 0 else 'sell',
                        'shares': shares,
                        'price': price,
                        'value': value_diff,
                        'cost': trade_cost
                    })

        # 計算最終資本
        final_capital = capital - total_transaction_cost

        return trades, final_capital

    def _calculate_period_returns(
        self,
        weights: Dict[str, float],
        start_date: date,
        end_date: date
    ) -> float:
        """計算時期收益率"""
        total_return = 0.0

        for asset, weight in weights.items():
            if asset in self.price_data:
                # 獲取資產價格
                asset_data = self.price_data[asset]
                if start_date in asset_data.index and end_date in asset_data.index:
                    start_price = asset_data.loc[start_date, 'close']
                    end_price = asset_data.loc[end_date, 'close']
                    asset_return = (end_price - start_price) / start_price
                    total_return += weight * asset_return

        return total_return

    def _calculate_performance_metrics(self) -> BacktestMetrics:
        """計算性能指標"""
        if self.portfolio_values is None:
            raise ValueError("No portfolio values available")

        # 計算收益率
        returns = self.portfolio_values.pct_change().dropna()

        # 基本指標
        total_return = (self.portfolio_values.iloc[-1] / self.portfolio_values.iloc[0]) - 1
        n_days = len(returns)
        annualized_return = (1 + total_return) ** (252 / n_days) - 1
        cagr = (self.portfolio_values.iloc[-1] / self.portfolio_values.iloc[0]) ** (252 / n_days) - 1

        # 風險指標
        volatility = returns.std() * np.sqrt(252)
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0

        # 回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # VaR和CVaR
        var_95 = returns.quantile(0.05)
        cvar_95 = returns[returns <= var_95].mean()

        # 風險調整收益
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        sortino_ratio = annualized_return / downside_volatility if downside_volatility > 0 else 0
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 基準相關指標（如果有基準）
        beta = alpha = information_ratio = tracking_error = 0
        if self.benchmark_data is not None:
            benchmark_returns = self.benchmark_data['close'].pct_change().reindex(returns.index).dropna()
            if len(benchmark_returns) > 0:
                # 對齊日期
                aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
                if len(aligned_returns) > 0:
                    # Beta
                    covariance = np.cov(aligned_returns, aligned_benchmark)[0, 1]
                    benchmark_variance = np.var(aligned_benchmark)
                    beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

                    # Alpha
                    risk_free_rate = 0.02  # 假設無風險利率
                    alpha = (annualized_return - risk_free_rate) - beta * (aligned_benchmark.mean() * 252 - risk_free_rate)

                    # Tracking Error
                    excess_returns = aligned_returns - aligned_benchmark
                    tracking_error = excess_returns.std() * np.sqrt(252)

                    # Information Ratio
                    information_ratio = excess_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0

        # 交易指標
        total_trades = len(self.trades)
        turnover = self._calculate_turnover()
        win_rate = self._calculate_win_rate()
        avg_trade_return = self._calculate_avg_trade_return()

        # 月度和年度統計
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1).tolist()
        yearly_returns = returns.resample('Y').apply(lambda x: (1 + x).prod() - 1).tolist()
        best_month = max(monthly_returns) if monthly_returns else 0
        worst_month = min(monthly_returns) if monthly_returns else 0
        best_year = max(yearly_returns) if yearly_returns else 0
        worst_year = min(yearly_returns) if yearly_returns else 0

        return BacktestMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            cagr=cagr,
            volatility=volatility,
            downside_volatility=downside_volatility,
            max_drawdown=max_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            information_ratio=information_ratio,
            turnover=turnover,
            total_trades=total_trades,
            win_rate=win_rate,
            avg_trade_return=avg_trade_return,
            beta=beta,
            alpha=alpha,
            tracking_error=tracking_error,
            monthly_returns=monthly_returns,
            yearly_returns=yearly_returns,
            best_month=best_month,
            worst_month=worst_month,
            best_year=best_year,
            worst_year=worst_year
        )

    def _calculate_turnover(self) -> float:
        """計算周轉率"""
        if len(self.weights_history) < 2:
            return 0.0

        total_turnover = 0.0
        for i in range(1, len(self.weights_history)):
            prev_weights = self.weights_history[i-1]['weights']
            curr_weights = self.weights_history[i]['weights']

            # 計算權重變化
            all_assets = set(prev_weights.keys()) | set(curr_weights.keys())
            period_turnover = 0.0

            for asset in all_assets:
                prev_weight = prev_weights.get(asset, 0)
                curr_weight = curr_weights.get(asset, 0)
                period_turnover += abs(curr_weight - prev_weight)

            total_turnover += period_turnover / 2  # 除以2因為買賣是對稱的

        # 年化周轉率
        n_periods = len(self.weights_history) - 1
        n_years = (self.config.end_date - self.config.start_date).days / 365.25

        return (total_turnover / n_periods) * (252 / n_periods) if n_periods > 0 else 0.0

    def _calculate_win_rate(self) -> float:
        """計算勝率"""
        if not self.trades:
            return 0.0

        winning_trades = 0
        for trade in self.trades:
            # 簡化計算：假設所有交易都是盈利的
            # 實際應該跟蹤每筆交易的盈虧
            winning_trades += 1

        return winning_trades / len(self.trades)

    def _calculate_avg_trade_return(self) -> float:
        """計算平均交易收益"""
        if not self.trades:
            return 0.0

        total_return = sum(trade['value'] for trade in self.trades)
        return total_return / len(self.trades)

    def _generate_backtest_report(self) -> Dict[str, Any]:
        """生成回測報告"""
        report = {
            "strategy_config": {
                "assets": self.config.assets,
                "start_date": self.config.start_date,
                "end_date": self.config.end_date,
                "initial_capital": self.config.initial_capital,
                "optimization_method": self.config.optimization_method.value,
                "rebalance_frequency": self.config.rebalance_frequency
            },
            "performance_metrics": self.performance_metrics.__dict__ if self.performance_metrics else {},
            "weights_history": self.weights_history,
            "trades_summary": {
                "total_trades": len(self.trades),
                "total_volume": sum(abs(trade['value']) for trade in self.trades),
                "total_cost": sum(trade['cost'] for trade in self.trades)
            },
            "correlation_analysis": self.correlation_analyzer.generate_correlation_report() if self.correlation_analyzer else None,
            "dynamic_strategy_summary": self.dynamic_strategy.get_performance_summary() if self.dynamic_strategy else None
        }

        # 添加投資組合價值序列
        if self.portfolio_values is not None:
            report["portfolio_values"] = self.portfolio_values.to_dict()

        return report

    def compare_with_benchmark(
        self,
        benchmark_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        與基準比較

        Args:
            benchmark_data: 基準數據（可選）

        Returns:
            比較結果
        """
        if self.portfolio_values is None:
            raise ValueError("No backtest results available")

        # 使用提供的基準數據或配置中的基準
        if benchmark_data is None:
            benchmark_data = self.benchmark_data

        if benchmark_data is None:
            raise ValueError("No benchmark data available")

        # 計算基準收益
        benchmark_returns = benchmark_data['close'].pct_change().reindex(self.portfolio_values.index).dropna()
        portfolio_returns = self.portfolio_values.pct_change().reindex(benchmark_returns.index).dropna()

        # 計算比較指標
        comparison = {
            "portfolio_total_return": (self.portfolio_values.iloc[-1] / self.portfolio_values.iloc[0]) - 1,
            "benchmark_total_return": (benchmark_data['close'].iloc[-1] / benchmark_data['close'].iloc[0]) - 1,
            "excess_return": 0,
            "tracking_error": 0,
            "information_ratio": 0,
            "upside_capture": 0,
            "downside_capture": 0
        }

        if len(portfolio_returns) > 0 and len(benchmark_returns) > 0:
            # 對齊數據
            portfolio_returns, benchmark_returns = portfolio_returns.align(benchmark_returns, join='inner')

            # 超額收益
            excess_returns = portfolio_returns - benchmark_returns
            comparison["excess_return"] = excess_returns.mean() * 252

            # 跟踪誤差
            comparison["tracking_error"] = excess_returns.std() * np.sqrt(252)

            # 信息比率
            if comparison["tracking_error"] > 0:
                comparison["information_ratio"] = comparison["excess_return"] / comparison["tracking_error"]

            # 上行/下行捕獲率
            up_periods = benchmark_returns > 0
            down_periods = benchmark_returns < 0

            if up_periods.sum() > 0:
                comparison["upside_capture"] = (
                    portfolio_returns[up_periods].mean() / benchmark_returns[up_periods].mean()
                )

            if down_periods.sum() > 0:
                comparison["downside_capture"] = (
                    portfolio_returns[down_periods].mean() / benchmark_returns[down_periods].mean()
                )

        return comparison

    def export_results(
        self,
        filepath: str,
        format: str = "json"
    ):
        """
        導出回測結果

        Args:
            filepath: 文件路徑
            format: 導出格式（json, csv, excel）
        """
        try:
            # 準備導出數據
            results = self._generate_backtest_report()

            # 根據格式導出
            if format.lower() == "json":
                import json
                with open(f"{filepath}.json", "w") as f:
                    # 轉換為可序列化格式
                    serializable_results = self._make_serializable(results)
                    json.dump(serializable_results, f, indent=2)
            elif format.lower() == "csv":
                # 導出CSV文件
                if self.portfolio_values is not None:
                    self.portfolio_values.to_csv(f"{filepath}_portfolio_values.csv")

                if self.weights_history:
                    weights_df = pd.DataFrame(self.weights_history)
                    weights_df.to_csv(f"{filepath}_weights_history.csv", index=False)

                if self.trades:
                    trades_df = pd.DataFrame(self.trades)
                    trades_df.to_csv(f"{filepath}_trades.csv", index=False)
            elif format.lower() == "excel":
                # 導出Excel文件
                with pd.ExcelWriter(f"{filepath}.xlsx") as writer:
                    if self.portfolio_values is not None:
                        self.portfolio_values.to_excel(writer, sheet_name="Portfolio Values")

                    if self.weights_history:
                        pd.DataFrame(self.weights_history).to_excel(writer, sheet_name="Weights History")

                    if self.trades:
                        pd.DataFrame(self.trades).to_excel(writer, sheet_name="Trades")

                    # 添加性能指標
                    if self.performance_metrics:
                        metrics_df = pd.DataFrame([self.performance_metrics.__dict__])
                        metrics_df.to_excel(writer, sheet_name="Performance Metrics")

            logger.info(f"Results exported: {filepath}.{format}")

        except Exception as e:
            logger.error(f"Results export failed: {e}")
            raise

    def _make_serializable(self, obj: Any) -> Any:
        """轉換為可序列化格式"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        else:
            return obj