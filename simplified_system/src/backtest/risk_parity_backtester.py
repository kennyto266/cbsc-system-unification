#!/usr / bin / env python3
"""
Risk Parity Backtesting Engine
风险平价回测引擎

Comprehensive backtesting framework for risk parity strategies
风险平价策略综合回测框架

Features:
- Risk parity strategy backtesting
- Multiple risk budgeting approaches
- Dynamic rebalancing
- Performance attribution
- Risk analysis
- Comparison with other strategies
"""

import logging
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    logging.warning(
        "Matplotlib not available. Install with: pip install matplotlib seaborn"
    )

try:
    from .mpt_optimizer import MPTOptimizer
    from .risk_budgeting import RiskBudgetConfig, RiskBudgetingFramework
    from .risk_contribution import RiskContributionCalculator, RiskContributionConfig
    from .risk_metrics import AdvancedRiskMetrics
    from .risk_parity_optimizer import RiskParityConfig, RiskParityOptimizer
except ImportError:
    # Fallback for direct module execution
    import mpt_optimizer
    import risk_budgeting
    import risk_contribution
    import risk_metrics
    import risk_parity_optimizer

    RiskParityOptimizer = risk_parity_optimizer.RiskParityOptimizer
    RiskParityConfig = risk_parity_optimizer.RiskParityConfig
    RiskBudgetingFramework = risk_budgeting.RiskBudgetingFramework
    RiskBudgetConfig = risk_budgeting.RiskBudgetConfig
    RiskContributionCalculator = risk_contribution.RiskContributionCalculator
    RiskContributionConfig = risk_contribution.RiskContributionConfig
    MPTOptimizer = mpt_optimizer.MPTOptimizer
    AdvancedRiskMetrics = risk_metrics.AdvancedRiskMetrics

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """回测配置"""

    # 基本参数
    start_date: str  # 回测开始日期
    end_date: str  # 回测结束日期

    # 再平衡参数
    rebalance_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    rebalance_threshold: float = 0.05  # 再平衡阈值

    # 窗口参数
    lookback_window: int = 252  # 优化窗口
    min_observations: int = 60  # 最小观察数

    # 约束条件
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_leverage: float = 1.5

    # 交易成本
    trading_cost: float = 0.001  # 交易成本
    slippage: float = 0.0005  # 滑点

    # 基准
    benchmark: str = "equal_weight"  # equal_weight, max_sharpe, min_vol

    # 分析选项
    calculate_attribution: bool = True  # 计算归因
    calculate_contributions: bool = True  # 计算风险贡献
    plot_results: bool = True  # 绘制结果


@dataclass
class BacktestResult:
    """回测结果"""

    # 基本结果
    dates: List[str]
    portfolio_returns: pd.Series
    portfolio_values: pd.Series
    weights_history: pd.DataFrame

    # 性能指标
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float

    # 风险指标
    var_95: float
    cvar_95: float
    sortino_ratio: float
    information_ratio: float

    # 交易指标
    turnover: float
    trading_costs: float
    number_of_rebalances: int

    # 元数据
    strategy_name: str
    backtest_period: str
    calculation_time: float

    # 详细分析
    risk_contribution_history: Optional[pd.DataFrame] = None
    performance_attribution: Optional[Dict[str, Any]] = None
    factor_exposures: Optional[pd.DataFrame] = None

    # 基准比较
    benchmark_returns: Optional[pd.Series] = None
    excess_returns: Optional[pd.Series] = None
    tracking_error: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "basic_results": {
                "total_return": round(self.total_return * 100, 2),
                "annualized_return": round(self.annualized_return * 100, 2),
                "volatility": round(self.volatility * 100, 2),
                "sharpe_ratio": round(self.sharpe_ratio, 3),
                "max_drawdown": round(self.max_drawdown * 100, 2),
                "calmar_ratio": round(self.calmar_ratio, 3),
            },
            "risk_metrics": {
                "var_95": round(self.var_95 * 100, 2),
                "cvar_95": round(self.cvar_95 * 100, 2),
                "sortino_ratio": round(self.sortino_ratio, 3),
                "information_ratio": round(self.information_ratio, 3),
            },
            "trading_metrics": {
                "turnover": round(self.turnover, 4),
                "trading_costs": round(self.trading_costs, 4),
                "number_of_rebalances": self.number_of_rebalances,
            },
            "benchmark_comparison": {
                "tracking_error": (
                    round(self.tracking_error, 4) if self.tracking_error else None
                ),
                "excess_return": (
                    round(self.excess_returns.mean() * 252 * 100, 2)
                    if self.excess_returns is not None
                    else None
                ),
            },
            "metadata": {
                "strategy_name": self.strategy_name,
                "backtest_period": self.backtest_period,
                "calculation_time": round(self.calculation_time, 3),
            },
        }


class RiskParityBacktester:
    """
    风险平价回测引擎

    提供完整的风险平价策略回测功能:
    - 多种风险平价方法
    - 动态再平衡
    - 交易成本处理
    - 性能归因
    - 风险分析
    - 基准比较
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """初始化回测引擎"""
        self.config = config or BacktestConfig(
            start_date="2020 - 01 - 01", end_date="2024 - 12 - 31"
        )

        # 初始化组件
        rp_config = RiskParityConfig(
            min_weight = self.config.min_weight,
            max_weight = self.config.max_weight,
            leverage_limit = self.config.max_leverage,
            trading_cost = self.config.trading_cost,
        )
        self.rp_optimizer = RiskParityOptimizer(rp_config)

        rb_config = RiskBudgetConfig(
            min_weight = self.config.min_weight,
            max_weight = self.config.max_weight,
            max_leverage = self.config.max_leverage,
            rebalance_threshold = self.config.rebalance_threshold,
        )
        self.risk_budgeting = RiskBudgetingFramework(rb_config)

        rc_config = RiskContributionConfig()
        self.risk_contribution = RiskContributionCalculator(rc_config)

        self.risk_calculator = AdvancedRiskMetrics()

        logger.info("Risk Parity Backtester initialized")

    def backtest_equal_risk_parity(
        self, returns: pd.DataFrame, name: str = "Equal Risk Parity"
    ) -> BacktestResult:
        """
        等风险平价策略回测

        Args:
            returns: 资产回报率
            name: 策略名称

        Returns:
            BacktestResult: 回测结果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting equal risk parity backtest: {name}")

            # 准备数据
            filtered_returns = self._prepare_data(returns)

            # 创建等风险预算
            assets = list(filtered_returns.columns)
            self.risk_budgeting.create_equal_risk_budget(assets, "equal_budget")

            # 执行回测
            result = self._execute_backtest(filtered_returns, "equal_budget", name)

            result.calculation_time = time.time() - start_time

            logger.info(
                f"Equal risk parity backtest completed: {result.calculation_time:.2f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Equal risk parity backtest failed: {e}")
            raise

    def backtest_risk_budgeting(
        self,
        returns: pd.DataFrame,
        risk_allocations: Dict[str, float],
        name: str = "Custom Risk Budgeting",
    ) -> BacktestResult:
        """
        自定义风险预算策略回测

        Args:
            returns: 资产回报率
            risk_allocations: 风险分配
            name: 策略名称

        Returns:
            BacktestResult: 回测结果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting risk budgeting backtest: {name}")

            # 准备数据
            filtered_returns = self._prepare_data(returns)

            # 创建自定义风险预算
            assets = list(filtered_returns.columns)
            budget_name = f"custom_budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.risk_budgeting.create_custom_risk_budget(
                assets, risk_allocations, budget_name
            )

            # 执行回测
            result = self._execute_backtest(filtered_returns, budget_name, name)

            result.calculation_time = time.time() - start_time

            logger.info(
                f"Risk budgeting backtest completed: {result.calculation_time:.2f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Risk budgeting backtest failed: {e}")
            raise

    def backtest_hierarchical_risk_parity(
        self,
        returns: pd.DataFrame,
        linkage_method: str = "ward",
        name: str = "Hierarchical Risk Parity",
    ) -> BacktestResult:
        """
        层次风险平价策略回测

        Args:
            returns: 资产回报率
            linkage_method: 连接方法
            name: 策略名称

        Returns:
            BacktestResult: 回测结果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting hierarchical risk parity backtest: {name}")

            # 准备数据
            filtered_returns = self._prepare_data(returns)

            # 执行层次风险平价回测
            result = self._execute_hrp_backtest(filtered_returns, linkage_method, name)

            result.calculation_time = time.time() - start_time

            logger.info(
                f"Hierarchical risk parity backtest completed: {result.calculation_time:.2f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Hierarchical risk parity backtest failed: {e}")
            raise

    def compare_strategies(
        self, returns: pd.DataFrame, strategies: List[Tuple[str, Dict[str, Any]]]
    ) -> pd.DataFrame:
        """
        比较多个策略

        Args:
            returns: 资产回报率
            strategies: 策略列表 [(strategy_type, params), ...]

        Returns:
            pd.DataFrame: 策略比较结果
        """
        comparison_results = []

        for strategy_type, params in strategies:
            try:
                if strategy_type == "equal_risk_parity":
                    result = self.backtest_equal_risk_parity(
                        returns, params.get("name", "Equal Risk Parity")
                    )
                elif strategy_type == "risk_budgeting":
                    result = self.backtest_risk_budgeting(
                        returns,
                        params["risk_allocations"],
                        params.get("name", "Risk Budgeting"),
                    )
                elif strategy_type == "hierarchical_risk_parity":
                    result = self.backtest_hierarchical_risk_parity(
                        returns,
                        params.get("linkage_method", "ward"),
                        params.get("name", "Hierarchical RP"),
                    )
                else:
                    logger.warning(f"Unknown strategy type: {strategy_type}")
                    continue

                comparison_results.append(
                    {
                        "strategy_name": result.strategy_name,
                        "total_return": result.total_return,
                        "annualized_return": result.annualized_return,
                        "volatility": result.volatility,
                        "sharpe_ratio": result.sharpe_ratio,
                        "max_drawdown": result.max_drawdown,
                        "calmar_ratio": result.calmar_ratio,
                        "turnover": result.turnover,
                        "trading_costs": result.trading_costs,
                        "number_of_rebalances": result.number_of_rebalances,
                    }
                )

            except Exception as e:
                logger.warning(f"Strategy comparison failed for {strategy_type}: {e}")
                continue

        comparison_df = pd.DataFrame(comparison_results)

        # 按夏普比率排序
        if "sharpe_ratio" in comparison_df.columns:
            comparison_df = comparison_df.sort_values("sharpe_ratio", ascending = False)

        return comparison_df.reset_index(drop = True)

    def _prepare_data(self, returns: pd.DataFrame) -> pd.DataFrame:
        """准备回测数据"""
        # 过滤日期范围
        mask = (returns.index >= self.config.start_date) & (
            returns.index <= self.config.end_date
        )
        filtered_returns = returns.loc[mask].copy()

        # 移除数据不足的资产
        valid_assets = []
        for asset in filtered_returns.columns:
            asset_returns = filtered_returns[asset]
            valid_ratio = asset_returns.notna().sum() / len(asset_returns)
            if valid_ratio >= 0.95:  # 至少95%的数据有效
                valid_assets.append(asset)

        filtered_returns = (
            filtered_returns[valid_assets].fillna(method="ffill").fillna(0)
        )

        logger.info(
            f"Prepared data: {len(filtered_returns)} periods, {len(filtered_returns.columns)} assets"
        )

        return filtered_returns

    def _execute_backtest(
        self, returns: pd.DataFrame, budget_name: str, strategy_name: str
    ) -> BacktestResult:
        """执行回测"""
        # 确定再平衡日期
        rebalance_dates = self._get_rebalance_dates(returns)

        # 初始化
        dates = returns.index.tolist()
        assets = returns.columns.tolist()
        num_assets = len(assets)

        # 权重历史
        weights_history = pd.DataFrame(index = dates, columns = assets, dtype = float)
        portfolio_returns = pd.Series(index = dates, dtype = float)
        portfolio_values = pd.Series(index = dates, dtype = float)

        # 初始权重 (等权重)
        current_weights = np.ones(num_assets) / num_assets
        weights_history.iloc[0] = current_weights

        # 初始投资组合价值
        portfolio_values.iloc[0] = 1.0

        # 执行回测
        for i in range(1, len(dates)):
            current_date = dates[i]

            # 检查是否需要再平衡
            if current_date in rebalance_dates or i == 1:
                # 获取优化窗口数据
                window_end = i
                window_start = max(0, i - self.config.lookback_window)

                window_returns = returns.iloc[window_start:window_end]

                if len(window_returns) >= self.config.min_observations:
                    try:
                        # 获取新的最优权重
                        allocation = self.risk_budgeting.allocate_portfolio(
                            window_returns, budget_name
                        )
                        new_weights = allocation.weights

                        # 应用约束
                        new_weights = np.clip(
                            new_weights, self.config.min_weight, self.config.max_weight
                        )
                        new_weights = new_weights / np.sum(new_weights)

                        # 计算交易成本
                        trades = np.abs(new_weights - current_weights).sum()
                        if trades > self.config.rebalance_threshold:
                            trading_cost = trades * self.config.trading_cost
                            current_weights = new_weights
                        else:
                            trading_cost = 0.0

                    except Exception as e:
                        logger.warning(f"Optimization failed at {current_date}: {e}")
                        trading_cost = 0.0
                else:
                    trading_cost = 0.0
            else:
                trading_cost = 0.0

            # 更新权重历史
            weights_history.iloc[i] = current_weights

            # 计算投资组合回报
            daily_return = np.dot(current_weights, returns.iloc[i].values)
            portfolio_returns.iloc[i] = daily_return
            portfolio_values.iloc[i] = portfolio_values.iloc[i - 1] * (
                1 + daily_return - trading_cost
            )

        # 计算性能指标
        performance_metrics = self._calculate_performance_metrics(
            portfolio_returns, portfolio_values
        )

        # 计算风险指标
        risk_metrics = self._calculate_risk_metrics(portfolio_returns)

        # 计算交易指标
        trading_metrics = self._calculate_trading_metrics(weights_history)

        # 计算基准比较
        benchmark_results = self._calculate_benchmark_comparison(
            returns, portfolio_returns
        )

        # 计算风险贡献历史
        contribution_history = None
        if self.config.calculate_contributions:
            try:
                contribution_history = self._calculate_contribution_history(
                    returns, weights_history
                )
            except Exception as e:
                logger.warning(f"Contribution history calculation failed: {e}")

        # 创建结果
        result = BacktestResult(
            dates = dates,
            portfolio_returns = portfolio_returns,
            portfolio_values = portfolio_values,
            weights_history = weights_history,
            total_return = performance_metrics["total_return"],
            annualized_return = performance_metrics["annualized_return"],
            volatility = performance_metrics["volatility"],
            sharpe_ratio = performance_metrics["sharpe_ratio"],
            max_drawdown = performance_metrics["max_drawdown"],
            calmar_ratio = performance_metrics["calmar_ratio"],
            var_95 = risk_metrics["var_95"],
            cvar_95 = risk_metrics["cvar_95"],
            sortino_ratio = risk_metrics["sortino_ratio"],
            information_ratio = risk_metrics["information_ratio"],
            turnover = trading_metrics["turnover"],
            trading_costs = trading_metrics["total_costs"],
            number_of_rebalances = trading_metrics["rebalances"],
            risk_contribution_history = contribution_history,
            benchmark_returns = benchmark_results["benchmark_returns"],
            excess_returns = benchmark_results["excess_returns"],
            tracking_error = benchmark_results["tracking_error"],
            strategy_name = strategy_name,
            backtest_period = f"{self.config.start_date} to {self.config.end_date}",
            calculation_time = 0.0,  # 将在外部设置
        )

        return result

    def _execute_hrp_backtest(
        self, returns: pd.DataFrame, linkage_method: str, strategy_name: str
    ) -> BacktestResult:
        """执行层次风险平价回测"""
        # 确定再平衡日期
        rebalance_dates = self._get_rebalance_dates(returns)

        # 初始化
        dates = returns.index.tolist()
        assets = returns.columns.tolist()
        num_assets = len(assets)

        # 权重历史
        weights_history = pd.DataFrame(index = dates, columns = assets, dtype = float)
        portfolio_returns = pd.Series(index = dates, dtype = float)
        portfolio_values = pd.Series(index = dates, dtype = float)

        # 初始权重 (等权重)
        current_weights = np.ones(num_assets) / num_assets
        weights_history.iloc[0] = current_weights
        portfolio_values.iloc[0] = 1.0

        # 执行回测
        for i in range(1, len(dates)):
            current_date = dates[i]

            # 检查是否需要再平衡
            if current_date in rebalance_dates or i == 1:
                # 获取优化窗口数据
                window_end = i
                window_start = max(0, i - self.config.lookback_window)

                window_returns = returns.iloc[window_start:window_end]

                if len(window_returns) >= self.config.min_observations:
                    try:
                        # 使用层次风险平价优化
                        result = self.rp_optimizer.optimize_hierarchical_risk_parity(
                            window_returns, linkage_method
                        )
                        new_weights = result.weights

                        # 应用约束
                        new_weights = np.clip(
                            new_weights, self.config.min_weight, self.config.max_weight
                        )
                        new_weights = new_weights / np.sum(new_weights)

                        # 计算交易成本
                        trades = np.abs(new_weights - current_weights).sum()
                        if trades > self.config.rebalance_threshold:
                            trading_cost = trades * self.config.trading_cost
                            current_weights = new_weights
                        else:
                            trading_cost = 0.0

                    except Exception as e:
                        logger.warning(
                            f"HRP optimization failed at {current_date}: {e}"
                        )
                        trading_cost = 0.0
                else:
                    trading_cost = 0.0
            else:
                trading_cost = 0.0

            # 更新权重历史
            weights_history.iloc[i] = current_weights

            # 计算投资组合回报
            daily_return = np.dot(current_weights, returns.iloc[i].values)
            portfolio_returns.iloc[i] = daily_return
            portfolio_values.iloc[i] = portfolio_values.iloc[i - 1] * (
                1 + daily_return - trading_cost
            )

        # 计算指标 (与标准回测相同)
        performance_metrics = self._calculate_performance_metrics(
            portfolio_returns, portfolio_values
        )
        risk_metrics = self._calculate_risk_metrics(portfolio_returns)
        trading_metrics = self._calculate_trading_metrics(weights_history)
        benchmark_results = self._calculate_benchmark_comparison(
            returns, portfolio_returns
        )

        # 创建结果
        result = BacktestResult(
            dates = dates,
            portfolio_returns = portfolio_returns,
            portfolio_values = portfolio_values,
            weights_history = weights_history,
            total_return = performance_metrics["total_return"],
            annualized_return = performance_metrics["annualized_return"],
            volatility = performance_metrics["volatility"],
            sharpe_ratio = performance_metrics["sharpe_ratio"],
            max_drawdown = performance_metrics["max_drawdown"],
            calmar_ratio = performance_metrics["calmar_ratio"],
            var_95 = risk_metrics["var_95"],
            cvar_95 = risk_metrics["cvar_95"],
            sortino_ratio = risk_metrics["sortino_ratio"],
            information_ratio = risk_metrics["information_ratio"],
            turnover = trading_metrics["turnover"],
            trading_costs = trading_metrics["total_costs"],
            number_of_rebalances = trading_metrics["rebalances"],
            benchmark_returns = benchmark_results["benchmark_returns"],
            excess_returns = benchmark_results["excess_returns"],
            tracking_error = benchmark_results["tracking_error"],
            strategy_name = strategy_name,
            backtest_period = f"{self.config.start_date} to {self.config.end_date}",
            calculation_time = 0.0,
        )

        return result

    def _get_rebalance_dates(self, returns: pd.DataFrame) -> List[pd.Timestamp]:
        """获取再平衡日期"""
        rebalance_dates = []

        if self.config.rebalance_frequency == "daily":
            # 每日再平衡
            rebalance_dates = returns.index.tolist()
        elif self.config.rebalance_frequency == "weekly":
            # 每周再平衡 (周一)
            for date in returns.index:
                if date.weekday() == 0:  # 周一
                    rebalance_dates.append(date)
        elif self.config.rebalance_frequency == "monthly":
            # 每月再平衡 (月初)
            for date in returns.index:
                if date.day == 1:  # 月初
                    rebalance_dates.append(date)
        elif self.config.rebalance_frequency == "quarterly":
            # 每季度再平衡 (季初)
            for date in returns.index:
                if date.month in [1, 4, 7, 10] and date.day == 1:  # 季初
                    rebalance_dates.append(date)

        return rebalance_dates

    def _calculate_performance_metrics(
        self, portfolio_returns: pd.Series, portfolio_values: pd.Series
    ) -> Dict[str, float]:
        """计算性能指标"""
        # 总回报
        total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1

        # 年化回报率
        days = len(portfolio_returns)
        annualized_return = (1 + total_return) ** (252 / days) - 1

        # 波动率
        volatility = portfolio_returns.std() * np.sqrt(252)

        # 夏普比率 (假设无风险利率为3%)
        risk_free_rate = 0.03
        excess_return = annualized_return - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0

        # 最大回撤
        running_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - running_max) / running_max
        max_drawdown = drawdown.min()

        # Calmar比率
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "calmar_ratio": calmar_ratio,
        }

    def _calculate_risk_metrics(self, portfolio_returns: pd.Series) -> Dict[str, float]:
        """计算风险指标"""
        try:
            # VaR和CVaR
            var_95 = np.percentile(portfolio_returns, 5)
            cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()

            # Sortino比率
            downside_returns = portfolio_returns[portfolio_returns < 0]
            if len(downside_returns) > 0:
                downside_volatility = downside_returns.std() * np.sqrt(252)
                excess_return = portfolio_returns.mean() * 252 - 0.03
                sortino_ratio = (
                    excess_return / downside_volatility
                    if downside_volatility > 0
                    else 0
                )
            else:
                sortino_ratio = 0

            # Information Ratio (相对于等权重基准)
            equal_weight_returns = portfolio_returns * 0  # 占位符，实际应用中需要基准
            if len(equal_weight_returns) > 0:
                active_returns = portfolio_returns - equal_weight_returns
                tracking_error = active_returns.std() * np.sqrt(252)
                information_ratio = (
                    active_returns.mean() * 252 / tracking_error
                    if tracking_error > 0
                    else 0
                )
            else:
                information_ratio = 0

            return {
                "var_95": var_95,
                "cvar_95": cvar_95,
                "sortino_ratio": sortino_ratio,
                "information_ratio": information_ratio,
            }

        except Exception as e:
            logger.warning(f"Risk metrics calculation failed: {e}")
            return {
                "var_95": 0.0,
                "cvar_95": 0.0,
                "sortino_ratio": 0.0,
                "information_ratio": 0.0,
            }

    def _calculate_trading_metrics(
        self, weights_history: pd.DataFrame
    ) -> Dict[str, Any]:
        """计算交易指标"""
        # 计算权重变化
        weight_changes = weights_history.diff().abs().sum(axis = 1)

        # 年化换手率
        annual_turnover = weight_changes.mean() * 252

        # 总交易成本
        total_costs = weight_changes.sum() * self.config.trading_cost

        # 再平衡次数
        rebalances = (weight_changes > 0).sum()

        return {
            "turnover": annual_turnover,
            "total_costs": total_costs,
            "rebalances": rebalances,
        }

    def _calculate_benchmark_comparison(
        self, asset_returns: pd.DataFrame, portfolio_returns: pd.Series
    ) -> Dict[str, Any]:
        """计算基准比较"""
        try:
            # 等权重基准
            num_assets = len(asset_returns.columns)
            benchmark_weights = np.ones(num_assets) / num_assets
            benchmark_returns = (asset_returns * benchmark_weights).sum(axis = 1)

            # 超额回报
            excess_returns = portfolio_returns - benchmark_returns

            # 跟踪误差
            tracking_error = excess_returns.std() * np.sqrt(252)

            return {
                "benchmark_returns": benchmark_returns,
                "excess_returns": excess_returns,
                "tracking_error": tracking_error,
            }

        except Exception as e:
            logger.warning(f"Benchmark comparison failed: {e}")
            return {
                "benchmark_returns": None,
                "excess_returns": None,
                "tracking_error": None,
            }

    def _calculate_contribution_history(
        self, returns: pd.DataFrame, weights_history: pd.DataFrame
    ) -> pd.DataFrame:
        """计算风险贡献历史"""
        contribution_data = []

        # 每月计算一次风险贡献
        monthly_dates = weights_history.index[
            weights_history.index.to_period("M").drop_duplicates()
        ]

        for date in monthly_dates:
            if date in weights_history.index:
                # 获取当前权重
                current_weights = weights_history.loc[date].values

                # 获取历史数据
                end_idx = weights_history.index.get_loc(date)
                start_idx = max(0, end_idx - self.config.lookback_window)

                historical_returns = returns.iloc[start_idx:end_idx]

                if len(historical_returns) >= self.config.min_observations:
                    try:
                        # 计算风险贡献
                        analysis = (
                            self.risk_contribution.calculate_marginal_contributions(
                                historical_returns, current_weights
                            )
                        )

                        # 记录结果
                        contribution_data.append(
                            {
                                "date": date,
                                **{
                                    f"{asset}_contribution": mc.component_contribution
                                    for asset, mc in zip(
                                        returns.columns, analysis.marginal_contributions
                                    )
                                },
                                "portfolio_volatility": analysis.portfolio_volatility,
                                "diversification_ratio": analysis.diversification_ratio,
                            }
                        )

                    except Exception as e:
                        logger.warning(
                            f"Contribution calculation failed at {date}: {e}"
                        )
                        continue

        return (
            pd.DataFrame(contribution_data).set_index("date")
            if contribution_data
            else pd.DataFrame()
        )

    def plot_results(
        self, result: BacktestResult, save_path: Optional[str] = None
    ) -> None:
        """绘制回测结果"""
        if not PLOTTING_AVAILABLE:
            logger.warning("Matplotlib not available for plotting")
            return

        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f"{result.strategy_name} Backtest Results", fontsize = 16)

            # 投资组合价值
            axes[0, 0].plot(result.portfolio_values.index, result.portfolio_values)
            axes[0, 0].set_title("Portfolio Value")
            axes[0, 0].set_ylabel("Portfolio Value")
            axes[0, 0].grid(True)

            # 累积回报
            cumulative_returns = (1 + result.portfolio_returns).cumprod()
            axes[0, 1].plot(cumulative_returns.index, cumulative_returns)
            axes[0, 1].set_title("Cumulative Returns")
            axes[0, 1].set_ylabel("Cumulative Return")
            axes[0, 1].grid(True)

            # 权重分布
            weights_to_plot = result.weights_history.iloc[::30]  # 每月采样一次
            axes[1, 0].stack().unstack().plot(kind="area", stacked = True, ax = axes[1, 0])
            axes[1, 0].set_title("Asset Weights Over Time")
            axes[1, 0].set_ylabel("Weight")
            axes[1, 0].legend(bbox_to_anchor=(1.05, 1), loc="upper left")

            # 回撤
            running_max = result.portfolio_values.expanding().max()
            drawdown = (result.portfolio_values - running_max) / running_max
            axes[1, 1].fill_between(
                drawdown.index, drawdown.values, 0, color="red", alpha = 0.3
            )
            axes[1, 1].plot(drawdown.index, drawdown.values, color="red")
            axes[1, 1].set_title("Drawdown")
            axes[1, 1].set_ylabel("Drawdown")
            axes[1, 1].grid(True)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi = 300, bbox_inches="tight")
                logger.info(f"Plot saved to {save_path}")

            plt.show()

        except Exception as e:
            logger.error(f"Plotting failed: {e}")


# 便利函数
def run_risk_parity_backtest(
    returns: pd.DataFrame, strategy_type: str = "equal_risk_parity", **kwargs
) -> BacktestResult:
    """便利函数：运行风险平价回测"""
    config = BacktestConfig(**kwargs)
    backtester = RiskParityBacktester(config)

    if strategy_type == "equal_risk_parity":
        return backtester.backtest_equal_risk_parity(returns)
    elif strategy_type == "hierarchical_risk_parity":
        return backtester.backtest_hierarchical_risk_parity(returns)
    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")


# 需要导入time模块
import time
