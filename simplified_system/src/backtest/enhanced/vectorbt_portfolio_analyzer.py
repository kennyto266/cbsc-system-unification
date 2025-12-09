#!/usr / bin / env python3
"""
Simplified System - 高級投資組合分析器
基於Python Algorithmic Trading Cookbook的專業級投資組合分析

提供機構級別的投資組合分析功能：
- 詳細的績效歸因分析
- 風險指標計算（VaR、CVaR等）
- 多資產相關性分析
- 專業級分析報告生成
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    import vectorbt as vbt

    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt")
    vbt = None

logger = logging.getLogger(__name__)


@dataclass
class PortfolioAnalysisConfig:
    """投資組合分析配置"""

    # 分析週期
    analysis_period: str = "1Y"  # 1年
    benchmark_symbol: Optional[str] = None  # 基準指數

    # 風險計算參數
    var_confidence_levels: List[float] = field(default_factory = lambda: [0.95, 0.99])
    cvar_confidence_levels: List[float] = field(default_factory = lambda: [0.95, 0.99])

    # 績效分析參數
    risk_free_rate: float = 0.03  # 3%無風險利率
    trading_days_per_year: int = 252

    # 可視化參數
    figsize: Tuple[int, int] = (12, 8)
    style: str = "seaborn - v0_8"


@dataclass
class RiskMetrics:
    """風險指標"""

    max_drawdown: float = 0.0
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    cvar_99: float = 0.0
    volatility: float = 0.0
    beta: Optional[float] = None
    tracking_error: Optional[float] = None


@dataclass
class PerformanceMetrics:
    """績效指標"""

    total_return: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_trade_return: float = 0.0


class AdvancedPortfolioAnalyzer:
    """
    高級投資組合分析器

    提供專業級的投資組合分析功能，包括：
    - 詳細的風險指標計算
    - 績效歸因分析
    - 可視化報告生成
    - 與基準的比較分析
    """

    def __init__(self, config: Optional[PortfolioAnalysisConfig] = None):
        """
        初始化投資組合分析器

        Args:
            config: 分析配置
        """
        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required for portfolio analysis")

        self.config = config or PortfolioAnalysisConfig()

        # 設置可視化樣式
        plt.style.use(self.config.style)
        sns.set_palette("husl")

        logger.info("初始化高級投資組合分析器")

    def analyze_portfolio(
        self, portfolio: "vbt.Portfolio", benchmark_prices: Optional[pd.Series] = None
    ) -> Dict[str, Any]:
        """
        全面分析投資組合

        Args:
            portfolio: VectorBT投資組合對象
            benchmark_prices: 基準價格數據

        Returns:
            Dict[str, Any]: 分析結果
        """
        logger.info("開始投資組合全面分析")

        start_time = datetime.now()

        # 基本績效分析
        performance = self._analyze_performance(portfolio)

        # 風險指標計算
        risk_metrics = self._calculate_risk_metrics(portfolio)

        # 回撤分析
        drawdown_analysis = self._analyze_drawdowns(portfolio)

        # 基準比較分析
        benchmark_analysis = self._compare_with_benchmark(portfolio, benchmark_prices)

        # 交易統計分析
        trade_analysis = self._analyze_trades(portfolio)

        # 月度績效分析
        monthly_analysis = self._analyze_monthly_performance(portfolio)

        analysis_time = (datetime.now() - start_time).total_seconds()

        result = {
            "portfolio": portfolio,
            "performance": performance,
            "risk_metrics": risk_metrics,
            "drawdown_analysis": drawdown_analysis,
            "benchmark_analysis": benchmark_analysis,
            "trade_analysis": trade_analysis,
            "monthly_analysis": monthly_analysis,
            "analysis_time": analysis_time,
        }

        logger.info(f"投資組合分析完成，耗時: {analysis_time:.2f}秒")
        return result

    def _analyze_performance(self, portfolio: "vbt.Portfolio") -> PerformanceMetrics:
        """分析投資組合績效"""
        returns = portfolio.returns()

        # 基本指標
        total_return = portfolio.total_return()
        annualized_return = portfolio.total_return() * (
            self.config.trading_days_per_year / len(returns)
        )
        sharpe_ratio = portfolio.sharpe_ratio()
        sortino_ratio = portfolio.sortino_ratio()
        calmar_ratio = (
            portfolio.total_return() / abs(portfolio.max_drawdown())
            if portfolio.max_drawdown() != 0
            else 0
        )

        # 交易統計
        win_rate = portfolio.win_rate()
        profit_factor = portfolio.profit_factor()
        avg_trade_return = (
            portfolio.trades.returns().mean()
            if hasattr(portfolio.trades, "returns")
            else 0
        )

        return PerformanceMetrics(
            total_return = total_return,
            annualized_return = annualized_return,
            sharpe_ratio = sharpe_ratio,
            sortino_ratio = sortino_ratio,
            calmar_ratio = calmar_ratio,
            win_rate = win_rate,
            profit_factor = profit_factor,
            avg_trade_return = avg_trade_return,
        )

    def _calculate_risk_metrics(self, portfolio: "vbt.Portfolio") -> RiskMetrics:
        """計算風險指標"""
        returns = portfolio.returns()

        # 基本風險指標
        max_drawdown = portfolio.max_drawdown()
        volatility = returns.std() * np.sqrt(self.config.trading_days_per_year)

        # VaR計算
        var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
        var_99 = np.percentile(returns, 1) if len(returns) > 0 else 0

        # CVaR計算
        var_95_threshold = np.percentile(returns, 5)
        var_99_threshold = np.percentile(returns, 1)
        cvar_95 = (
            returns[returns <= var_95_threshold].mean()
            if len(returns[returns <= var_95_threshold]) > 0
            else 0
        )
        cvar_99 = (
            returns[returns <= var_99_threshold].mean()
            if len(returns[returns <= var_99_threshold]) > 0
            else 0
        )

        return RiskMetrics(
            max_drawdown = abs(max_drawdown),
            var_95 = abs(var_95),
            var_99 = abs(var_99),
            cvar_95 = abs(cvar_95),
            cvar_99 = abs(cvar_99),
            volatility = volatility,
        )

    def _analyze_drawdowns(self, portfolio: "vbt.Portfolio") -> Dict[str, Any]:
        """分析回撤"""
        drawdown = portfolio.drawdown()

        # 回撤統計
        max_dd = drawdown.max()
        avg_dd = drawdown.mean()
        dd_duration = portfolio.drawdowns.duration
        dd_recovery = portfolio.drawdowns.recovery_time

        analysis = {
            "max_drawdown": max_dd,
            "average_drawdown": avg_dd,
            "max_drawdown_duration": dd_duration.max() if len(dd_duration) > 0 else 0,
            "average_recovery_time": dd_recovery.mean() if len(dd_recovery) > 0 else 0,
            "current_drawdown": drawdown.iloc[-1],
            "drawdown_periods": len(portfolio.drawdowns),
        }

        return analysis

    def _compare_with_benchmark(
        self, portfolio: "vbt.Portfolio", benchmark_prices: Optional[pd.Series]
    ) -> Dict[str, Any]:
        """與基準比較"""
        if benchmark_prices is None:
            return {"error": "未提供基準數據"}

        try:
            # 計算基準回報
            benchmark_returns = benchmark_prices.pct_change().dropna()
            portfolio_returns = portfolio.returns()

            # 對齊數據
            common_index = portfolio_returns.index.intersection(benchmark_returns.index)
            if len(common_index) == 0:
                return {"error": "投資組合與基準數據時間範圍不匹配"}

            portfolio_aligned = portfolio_returns.loc[common_index]
            benchmark_aligned = benchmark_returns.loc[common_index]

            # 計算相關性
            correlation = portfolio_aligned.corr(benchmark_aligned)

            # 計算Beta
            covariance = portfolio_aligned.cov(benchmark_aligned)
            benchmark_variance = benchmark_aligned.var()
            beta = covariance / benchmark_variance if benchmark_variance != 0 else 1.0

            # 計算Alpha
            risk_free_daily = (
                self.config.risk_free_rate / self.config.trading_days_per_year
            )
            portfolio_excess = portfolio_aligned - risk_free_daily
            benchmark_excess = benchmark_aligned - risk_free_daily

            alpha = portfolio_excess.mean() - beta * benchmark_excess.mean()
            alpha_annual = alpha * self.config.trading_days_per_year

            # 計算跟蹤誤差
            tracking_error = (portfolio_aligned - benchmark_aligned).std() * np.sqrt(
                self.config.trading_days_per_year
            )
            information_ratio = (
                alpha_annual / tracking_error if tracking_error != 0 else 0
            )

            # 上行 / 下行捕獲比率
            up_market = benchmark_aligned > 0
            down_market = benchmark_aligned < 0

            up_capture = (
                portfolio_aligned[up_market].mean()
                / benchmark_aligned[up_market].mean()
                if up_market.any()
                else 0
            )
            down_capture = (
                portfolio_aligned[down_market].mean()
                / benchmark_aligned[down_market].mean()
                if down_market.any()
                else 0
            )

            return {
                "correlation": correlation,
                "beta": beta,
                "alpha_annual": alpha_annual,
                "tracking_error": tracking_error,
                "information_ratio": information_ratio,
                "up_capture_ratio": up_capture,
                "down_capture_ratio": down_capture,
                "portfolio_return": portfolio_aligned.sum(),
                "benchmark_return": benchmark_aligned.sum(),
                "excess_return": portfolio_aligned.sum() - benchmark_aligned.sum(),
            }

        except Exception as e:
            logger.error(f"基準比較分析失敗: {e}")
            return {"error": f"基準比較分析失敗: {str(e)}"}

    def _analyze_trades(self, portfolio: "vbt.Portfolio") -> Dict[str, Any]:
        """分析交易統計"""
        if not hasattr(portfolio, "trades") or portfolio.trades is None:
            return {"error": "無法獲取交易數據"}

        trades = portfolio.trades

        # 基本交易統計
        total_trades = len(trades)
        winning_trades = (
            len(trades[trades.return_series > 0])
            if hasattr(trades, "return_series")
            else 0
        )
        losing_trades = total_trades - winning_trades

        # 收益統計
        if hasattr(trades, "return_series"):
            returns = trades.return_series
            avg_win = returns[returns > 0].mean() if winning_trades > 0 else 0
            avg_loss = abs(returns[returns < 0].mean()) if losing_trades > 0 else 0
            profit_factor = avg_win / avg_loss if avg_loss != 0 else float("inf")
        else:
            avg_win = avg_loss = profit_factor = 0

        # 持有期統計
        if hasattr(trades, "duration"):
            avg_holding_period = trades.duration.mean()
            max_holding_period = trades.duration.max()
        else:
            avg_holding_period = max_holding_period = 0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "avg_holding_period": avg_holding_period,
            "max_holding_period": max_holding_period,
        }

    def _analyze_monthly_performance(self, portfolio: "vbt.Portfolio") -> pd.DataFrame:
        """分析月度績效"""
        returns = portfolio.returns()

        # 計算月度回報
        monthly_returns = returns.resample("M").apply(lambda x: (1 + x).prod() - 1)

        # 計算統計指標
        monthly_stats = pd.DataFrame(
            {
                "return": monthly_returns,
                "cumulative": (1 + monthly_returns).cumprod() - 1,
                "positive": monthly_returns > 0,
            }
        )

        # 添加年度統計
        monthly_stats["year"] = monthly_stats.index.year
        yearly_stats = monthly_stats.groupby("year")["return"].agg(
            ["mean", "std", "sum"]
        )

        return {
            "monthly_returns": monthly_returns,
            "monthly_stats": monthly_stats,
            "yearly_stats": yearly_stats,
            "positive_months": monthly_stats["positive"].sum(),
            "total_months": len(monthly_stats),
            "monthly_win_rate": monthly_stats["positive"].mean(),
        }

    def generate_comprehensive_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        生成綜合分析報告

        Args:
            analysis_result: 分析結果

        Returns:
            str: 綜合報告
        """
        report = f"""
# 投資組合綜合分析報告

## 績效指標
- 總回報: {analysis_result['performance'].total_return:.2%}
- 年化回報: {analysis_result['performance'].annualized_return:.2%}
- Sharpe比率: {analysis_result['performance'].sharpe_ratio:.3f}
- Sortino比率: {analysis_result['performance'].sortino_ratio:.3f}
- Calmar比率: {analysis_result['performance'].calmar_ratio:.3f}
- 勝率: {analysis_result['performance'].win_rate:.2%}
- 盈利因子: {analysis_result['performance'].profit_factor:.2f}

## 風險指標
- 最大回撤: {analysis_result['risk_metrics'].max_drawdown:.2%}
- 年化波動率: {analysis_result['risk_metrics'].volatility:.2%}
- VaR (95%): {analysis_result['risk_metrics'].var_95:.2%}
- VaR (99%): {analysis_result['risk_metrics'].var_99:.2%}
- CVaR (95%): {analysis_result['risk_metrics'].cvar_95:.2%}
- CVaR (99%): {analysis_result['risk_metrics'].cvar_99:.2%}

## 回撤分析
- 最大回撤: {analysis_result['drawdown_analysis']['max_drawdown']:.2%}
- 平均回撤: {analysis_result['drawdown_analysis']['average_drawdown']:.2%}
- 最長回撤持續時間: {analysis_result['drawdown_analysis']['max_drawdown_duration']:.0f} 天
- 平均恢復時間: {analysis_result['drawdown_analysis']['average_recovery_time']:.0f} 天
- 當前回撤: {analysis_result['drawdown_analysis']['current_drawdown']:.2%}

## 基準比較
"""

        benchmark_analysis = analysis_result["benchmark_analysis"]
        if "error" not in benchmark_analysis:
            report += f"""
- 相關係數: {benchmark_analysis['correlation']:.3f}
- Beta: {benchmark_analysis['beta']:.3f}
- Alpha (年化): {benchmark_analysis['alpha_annual']:.2%}
- 跟蹤誤差: {benchmark_analysis['tracking_error']:.2%}
- 信息比率: {benchmark_analysis['information_ratio']:.3f}
- 上行捕獲比率: {benchmark_analysis['up_capture_ratio']:.3f}
- 下行捕獲比率: {benchmark_analysis['down_capture_ratio']:.3f}
- 超額收益: {benchmark_analysis['excess_return']:.2%}
"""
        else:
            report += f"- {benchmark_analysis['error']}\n"

        # 交易統計
        trade_analysis = analysis_result["trade_analysis"]
        if "error" not in trade_analysis:
            report += f"""
## 交易統計
- 總交易次數: {trade_analysis['total_trades']}
- 獲利交易: {trade_analysis['winning_trades']}
- 虧損交易: {trade_analysis['losing_trades']}
- 平均持倉期: {trade_analysis['avg_holding_period']:.1f} 天
- 平均獲利: {trade_analysis['avg_win']:.2%}
- 平均虧損: {trade_analysis['avg_loss']:.2%}
- 盈利因子: {trade_analysis['profit_factor']:.2f}
"""

        # 月度分析
        monthly_analysis = analysis_result["monthly_analysis"]
        report += f"""
## 月度分析
- 正收益月份: {monthly_analysis['positive_months']}/{monthly_analysis['total_months']}
- 月度勝率: {monthly_analysis['monthly_win_rate']:.2%}

## 分析時間
- 總分析時間: {analysis_result['analysis_time']:.2f} 秒
- 分析生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def create_performance_visualization(self, analysis_result: Dict[str, Any]) -> None:
        """
        創建績效可視化圖表

        Args:
            analysis_result: 分析結果
        """
        try:
            portfolio = analysis_result["portfolio"]

            # 創建子圖
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle("投資組合績效分析", fontsize = 16, fontweight="bold")

            # 1. 累計收益曲線
            portfolio.value().plot(ax = axes[0, 0], title="累計收益")
            axes[0, 0].set_ylabel("投資組合價值")
            axes[0, 0].grid(True)

            # 2. 回撤曲線
            portfolio.drawdown().plot(ax = axes[0, 1], title="回撤分析", color="red")
            axes[0, 1].set_ylabel("回撤 (%)")
            axes[0, 1].grid(True)

            # 3. 月度收益分布
            monthly_returns = analysis_result["monthly_analysis"]["monthly_returns"]
            monthly_returns.plot(kind="bar", ax = axes[1, 0], title="月度收益")
            axes[1, 0].set_ylabel("月度收益 (%)")
            axes[1, 0].tick_params(axis="x", rotation = 45)
            axes[1, 0].grid(True)

            # 4. 收益分布直方圖
            portfolio.returns().hist(
                bins = 50, ax = axes[1, 1], title="日收益分布", alpha = 0.7
            )
            axes[1, 1].set_xlabel("日收益")
            axes[1, 1].set_ylabel("頻率")
            axes[1, 1].grid(True)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            logger.error(f"可視化創建失敗: {e}")
