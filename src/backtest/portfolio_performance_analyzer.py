"""
Portfolio Performance Analyzer
投資組合性能分析器

提供全面的投資組合性能評估和分析報告：
- 風險收益分析
- 歸因分析
- 情景分析和壓力測試
- 相對基準比較
- 可視化報告生成
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """分析類型"""
    PERFORMANCE = "performance"          # 性能分析
    RISK = "risk"                       # 風險分析
    ATTRIBUTION = "attribution"         # 歸因分析
    STRESS_TEST = "stress_test"         # 壓力測試
    SCENARIO = "scenario"               # 情景分析
    COMPARISON = "comparison"           # 比較分析


@dataclass
class AnalysisConfig:
    """分析配置"""
    # 分析類型
    analysis_types: List[AnalysisType] = field(default_factory=lambda: [
        AnalysisType.PERFORMANCE,
        AnalysisType.RISK,
        AnalysisType.ATTRIBUTION
    ])

    # 基準配置
    benchmark_symbols: List[str] = field(default_factory=list)
    risk_free_rate: float = 0.02

    # 時間配置
    analysis_periods: Dict[str, Tuple[date, date]] = field(default_factory=dict)

    # 報告配置
    include_charts: bool = True
    chart_style: str = "seaborn"
    figsize: Tuple[int, int] = (12, 8)
    save_reports: bool = True
    report_dir: str = "portfolio_reports"

    # 壓力測試配置
    stress_scenarios: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "market_crash": {"shock": -0.30, "duration": 21},
        "interest_rate_spike": {"shock": 0.02, "duration": 30},
        "volatility_spike": {"shock": 2.0, "duration": 10}
    })


@dataclass
class PerformanceMetrics:
    """性能指標"""
    # 收益指標
    total_return: float
    annualized_return: float
    cagr: float
    rolling_returns: Dict[str, float]

    # 風險指標
    volatility: float
    downside_volatility: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    max_drawdown: float
    max_drawdown_duration: int

    # 風險調整收益指標
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    treynor_ratio: float

    # 其他指標
    beta: float
    alpha: float
    tracking_error: float
    active_share: float

    # 尾部風險指標
    skewness: float
    kurtosis: float
    tail_ratio: float


@dataclass
class AttributionResult:
    """歸因分析結果"""
    asset_allocation_effect: Dict[str, float]
    security_selection_effect: Dict[str, float]
    interaction_effect: Dict[str, float]
    total_effect: float

    # 按時間分解
    monthly_attribution: List[Dict[str, Any]]
    quarterly_attribution: List[Dict[str, Any]]
    yearly_attribution: List[Dict[str, Any]]


class PortfolioPerformanceAnalyzer:
    """投資組合性能分析器"""

    def __init__(self, config: AnalysisConfig):
        """
        初始化性能分析器

        Args:
            config: 分析配置
        """
        self.config = config

        # 內部狀態
        self.portfolio_data: Optional[pd.DataFrame] = None
        self.benchmark_data: Dict[str, pd.DataFrame] = {}
        self.weights_history: List[Dict[str, Any]] = []

        # 分析結果
        self.performance_metrics: Optional[PerformanceMetrics] = None
        self.attribution_results: Optional[AttributionResult] = None
        self.stress_test_results: Dict[str, Any] = {}
        self.comparison_results: Dict[str, Any] = {}

        logger.info("Portfolio Performance Analyzer initialized")

    def load_data(
        self,
        portfolio_values: pd.Series,
        weights_history: List[Dict[str, Any]],
        benchmark_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> None:
        """
        加載分析數據

        Args:
            portfolio_values: 投資組合價值序列
            weights_history: 權重歷史
            benchmark_data: 基準數據（可選）
        """
        try:
            # 準備投資組合數據
            self.portfolio_data = pd.DataFrame({
                'value': portfolio_values,
                'return': portfolio_values.pct_change()
            })

            self.weights_history = weights_history

            # 加載基準數據
            if benchmark_data:
                self.benchmark_data = benchmark_data
            elif self.config.benchmark_symbols:
                # 這裡應該從外部數據源加載基準數據
                logger.warning("Benchmark symbols provided but no data loader")

            logger.info(f"Data loaded: {len(self.portfolio_data)} observations")

        except Exception as e:
            logger.error(f"Data loading failed: {e}")
            raise

    def run_analysis(self) -> Dict[str, Any]:
        """
        運行完整分析

        Returns:
            分析結果字典
        """
        try:
            logger.info("Starting portfolio performance analysis")

            results = {}

            # 運行各類分析
            for analysis_type in self.config.analysis_types:
                if analysis_type == AnalysisType.PERFORMANCE:
                    results[analysis_type.value] = self._analyze_performance()
                elif analysis_type == AnalysisType.RISK:
                    results[analysis_type.value] = self._analyze_risk()
                elif analysis_type == AnalysisType.ATTRIBUTION:
                    results[analysis_type.value] = self._analyze_attribution()
                elif analysis_type == AnalysisType.STRESS_TEST:
                    results[analysis_type.value] = self._run_stress_tests()
                elif analysis_type == AnalysisType.SCENARIO:
                    results[analysis_type.value] = self._run_scenario_analysis()
                elif analysis_type == AnalysisType.COMPARISON:
                    results[analysis_type.value] = self._compare_with_benchmarks()

            # 生成綜合報告
            results['summary'] = self._generate_summary_report(results)

            # 生成可視化報告
            if self.config.include_charts:
                results['charts'] = self._generate_charts()

            logger.info("Analysis completed successfully")
            return results

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    def _analyze_performance(self) -> Dict[str, Any]:
        """性能分析"""
        try:
            returns = self.portfolio_data['return'].dropna()

            # 基本收益指標
            total_return = (self.portfolio_data['value'].iloc[-1] / self.portfolio_data['value'].iloc[0]) - 1
            n_days = len(returns)
            annualized_return = (1 + total_return) ** (252 / n_days) - 1
            cagr = (self.portfolio_data['value'].iloc[-1] / self.portfolio_data['value'].iloc[0]) ** (252 / n_days) - 1

            # 滾動收益
            rolling_returns = {}
            for window in [30, 60, 90, 252]:
                rolling_returns[f"{window}d"] = returns.rolling(window).mean().iloc[-1] * 252

            # 風險指標
            volatility = returns.std() * np.sqrt(252)
            downside_returns = returns[returns < 0]
            downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0

            # VaR和CVaR
            var_95 = returns.quantile(0.05)
            var_99 = returns.quantile(0.01)
            cvar_95 = returns[returns <= var_95].mean()
            cvar_99 = returns[returns <= var_99].mean()

            # 回撤分析
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            # 最大回撤持續時間
            drawdown_duration = 0
            max_duration = 0
            for dd in drawdown:
                if dd < 0:
                    drawdown_duration += 1
                    max_duration = max(max_duration, drawdown_duration)
                else:
                    drawdown_duration = 0

            # 風險調整收益
            excess_return = annualized_return - self.config.risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

            # 基準相關指標
            beta = alpha = information_ratio = treynor_ratio = 0
            if self.benchmark_data:
                # 使用第一個基準
                benchmark_name = list(self.benchmark_data.keys())[0]
                benchmark_df = self.benchmark_data[benchmark_name]
                benchmark_returns = benchmark_df['return'].reindex(returns.index).dropna()

                if len(benchmark_returns) > 0:
                    # Beta
                    covariance = np.cov(returns.reindex(benchmark_returns.index), benchmark_returns)[0, 1]
                    benchmark_variance = np.var(benchmark_returns)
                    beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

                    # Alpha
                    benchmark_return = (benchmark_df['value'].iloc[-1] / benchmark_df['value'].iloc[0]) - 1
                    benchmark_annual_return = (1 + benchmark_return) ** (252 / len(benchmark_returns)) - 1
                    alpha = annualized_return - (self.config.risk_free_rate + beta * (benchmark_annual_return - self.config.risk_free_rate))

                    # Information Ratio
                    excess_returns = returns.reindex(benchmark_returns.index) - benchmark_returns
                    tracking_error = excess_returns.std() * np.sqrt(252)
                    information_ratio = excess_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0

                    # Treynor Ratio
                    treynor_ratio = excess_return / beta if beta != 0 else 0

            # 尾部風險指標
            skewness = stats.skew(returns)
            kurtosis = stats.kurtosis(returns)
            tail_ratio = abs(returns.quantile(0.95)) / abs(returns.quantile(0.05)) if returns.quantile(0.05) != 0 else 0

            # 主動份額
            active_share = self._calculate_active_share()

            # 保存結果
            self.performance_metrics = PerformanceMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                cagr=cagr,
                rolling_returns=rolling_returns,
                volatility=volatility,
                downside_volatility=downside_volatility,
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                cvar_99=cvar_99,
                max_drawdown=max_drawdown,
                max_drawdown_duration=max_duration,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                information_ratio=information_ratio,
                treynor_ratio=treynor_ratio,
                beta=beta,
                alpha=alpha,
                tracking_error=tracking_error if 'tracking_error' in locals() else 0,
                active_share=active_share,
                skewness=skewness,
                kurtosis=kurtosis,
                tail_ratio=tail_ratio
            )

            return {
                "metrics": self.performance_metrics.__dict__,
                "monthly_returns": self._calculate_periodic_returns('M'),
                "yearly_returns": self._calculate_periodic_returns('Y'),
                "best_worst_periods": self._find_best_worst_periods()
            }

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            raise

    def _analyze_risk(self) -> Dict[str, Any]:
        """風險分析"""
        try:
            returns = self.portfolio_data['return'].dropna()

            risk_analysis = {
                "volatility_analysis": self._analyze_volatility(returns),
                "drawdown_analysis": self._analyze_drawdowns(returns),
                "correlation_analysis": self._analyze_correlations(),
                "concentration_analysis": self._analyze_concentration(),
                "regime_analysis": self._analyze_market_regimes(returns)
            }

            return risk_analysis

        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            raise

    def _analyze_attribution(self) -> Dict[str, Any]:
        """歸因分析"""
        try:
            # 計算資產配置效應
            allocation_effect = self._calculate_allocation_effect()

            # 計算證券選擇效應
            selection_effect = self._calculate_selection_effect()

            # 交互效應
            interaction_effect = self._calculate_interaction_effect()

            # 保存結果
            self.attribution_results = AttributionResult(
                asset_allocation_effect=allocation_effect,
                security_selection_effect=selection_effect,
                interaction_effect=interaction_effect,
                total_effect=sum(allocation_effect.values()) + sum(selection_effect.values()) + sum(interaction_effect.values()),
                monthly_attribution=self._calculate_periodic_attribution('M'),
                quarterly_attribution=self._calculate_periodic_attribution('Q'),
                yearly_attribution=self._calculate_periodic_attribution('Y')
            )

            return {
                "summary": {
                    "allocation_effect": allocation_effect,
                    "selection_effect": selection_effect,
                    "interaction_effect": interaction_effect,
                    "total_attribution": self.attribution_results.total_effect
                },
                "periodic_breakdown": {
                    "monthly": self.attribution_results.monthly_attribution,
                    "quarterly": self.attribution_results.quarterly_attribution,
                    "yearly": self.attribution_results.yearly_attribution
                }
            }

        except Exception as e:
            logger.error(f"Attribution analysis failed: {e}")
            raise

    def _run_stress_tests(self) -> Dict[str, Any]:
        """壓力測試"""
        try:
            stress_results = {}

            for scenario_name, scenario_params in self.config.stress_scenarios.items():
                result = self._apply_stress_scenario(scenario_name, scenario_params)
                stress_results[scenario_name] = result

            self.stress_test_results = stress_results
            return stress_results

        except Exception as e:
            logger.error(f"Stress testing failed: {e}")
            raise

    def _run_scenario_analysis(self) -> Dict[str, Any]:
        """情景分析"""
        try:
            # 定義各種市場情景
            scenarios = {
                "bull_market": {"return": 0.20, "volatility": 0.15},
                "bear_market": {"return": -0.20, "volatility": 0.30},
                "high_volatility": {"return": 0.05, "volatility": 0.40},
                "low_volatility": {"return": 0.08, "volatility": 0.10},
                "stagnation": {"return": 0.02, "volatility": 0.20}
            }

            scenario_results = {}
            for scenario_name, params in scenarios.items():
                result = self._simulate_scenario(scenario_name, params)
                scenario_results[scenario_name] = result

            return scenario_results

        except Exception as e:
            logger.error(f"Scenario analysis failed: {e}")
            raise

    def _compare_with_benchmarks(self) -> Dict[str, Any]:
        """與基準比較"""
        try:
            if not self.benchmark_data:
                return {"message": "No benchmark data available"}

            comparison_results = {}

            for benchmark_name, benchmark_df in self.benchmark_data.items():
                comparison = self._compare_with_single_benchmark(benchmark_df)
                comparison_results[benchmark_name] = comparison

            self.comparison_results = comparison_results
            return comparison_results

        except Exception as e:
            logger.error(f"Benchmark comparison failed: {e}")
            raise

    def _calculate_active_share(self) -> float:
        """計算主動份額"""
        if not self.weights_history or not self.benchmark_data:
            return 0.0

        # 使用最新權重
        latest_weights = self.weights_history[-1]['weights']

        # 假設基準權重（實際應該從基準數據計算）
        benchmark_weights = {asset: 1.0/len(self.benchmark_data) for asset in self.benchmark_data.keys()}

        # 計算主動份額
        active_share = 0.0
        all_assets = set(latest_weights.keys()) | set(benchmark_weights.keys())

        for asset in all_assets:
            portfolio_weight = latest_weights.get(asset, 0)
            benchmark_weight = benchmark_weights.get(asset, 0)
            active_share += abs(portfolio_weight - benchmark_weight)

        return active_share / 2

    def _calculate_periodic_returns(self, period: str) -> List[float]:
        """計算週期性收益"""
        returns = self.portfolio_data['return'].dropna()
        periodic_returns = returns.resample(period).apply(lambda x: (1 + x).prod() - 1)
        return periodic_returns.tolist()

    def _find_best_worst_periods(self) -> Dict[str, Any]:
        """找出最佳和最差時期"""
        returns = self.portfolio_data['return'].dropna()

        # 日收益率
        best_day = returns.max()
        worst_day = returns.min()

        # 月收益率
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        best_month = monthly_returns.max()
        worst_month = monthly_returns.min()

        # 年收益率
        yearly_returns = returns.resample('Y').apply(lambda x: (1 + x).prod() - 1)
        best_year = yearly_returns.max()
        worst_year = yearly_returns.min()

        return {
            "daily": {"best": best_day, "worst": worst_day},
            "monthly": {"best": best_month, "worst": worst_month},
            "yearly": {"best": best_year, "worst": worst_year}
        }

    def _analyze_volatility(self, returns: pd.Series) -> Dict[str, Any]:
        """波動率分析"""
        # 滾動波動率
        rolling_vol = returns.rolling(window=30).std() * np.sqrt(252)

        return {
            "current_volatility": returns.std() * np.sqrt(252),
            "volatility_trend": rolling_vol.iloc[-1] - rolling_vol.iloc[0],
            "volatility_regime": self._classify_volatility_regime(rolling_vol.iloc[-1]),
            "volatility_clustering": self._detect_volatility_clustering(returns)
        }

    def _analyze_drawdowns(self, returns: pd.Series) -> Dict[str, Any]:
        """回撤分析"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        # 找出所有回撤期
        drawdown_periods = []
        in_drawdown = False
        start_date = None
        max_dd = 0

        for date, dd in drawdown.items():
            if dd < 0 and not in_drawdown:
                in_drawdown = True
                start_date = date
                max_dd = dd
            elif dd >= 0 and in_drawdown:
                in_drawdown = False
                drawdown_periods.append({
                    "start": start_date,
                    "end": date,
                    "depth": max_dd,
                    "duration": (date - start_date).days
                })
            elif dd < max_dd:
                max_dd = dd

        return {
            "max_drawdown": drawdown.min(),
            "max_drawdown_duration": max([p["duration"] for p in drawdown_periods]) if drawdown_periods else 0,
            "drawdown_periods": drawdown_periods[:5],  # 前5個最大回撤
            "recovery_time": self._calculate_average_recovery_time(drawdown)
        }

    def _analyze_correlations(self) -> Dict[str, Any]:
        """相關性分析（如果有資產級別數據）"""
        # 簡化實現，實際需要資產級別收益率數據
        return {
            "average_correlation": "N/A - requires asset level data",
            "correlation_trend": "N/A"
        }

    def _analyze_concentration(self) -> Dict[str, Any]:
        """集中度分析"""
        if not self.weights_history:
            return {"message": "No weights history available"}

        latest_weights = self.weights_history[-1]['weights']
        weights_array = list(latest_weights.values())

        # Herfindahl-Hirschman Index (HHI)
        hhi = sum([w**2 for w in weights_array])

        # 有效資產數量
        effective_n = 1 / hhi if hhi > 0 else 0

        # 最大權重
        max_weight = max(weights_array) if weights_array else 0

        return {
            "hhi": hhi,
            "effective_assets": effective_n,
            "max_weight": max_weight,
            "concentration_level": self._classify_concentration(hhi)
        }

    def _analyze_market_regimes(self, returns: pd.Series) -> Dict[str, Any]:
        """市場狀態分析"""
        # 使用簡單的基於波動率和收益率的狀態分類
        rolling_return = returns.rolling(window=60).mean() * 252
        rolling_vol = returns.rolling(window=60).std() * np.sqrt(252)

        current_return = rolling_return.iloc[-1] if not rolling_return.empty else 0
        current_vol = rolling_vol.iloc[-1] if not rolling_vol.empty else 0

        if current_return > 0.10 and current_vol < 0.20:
            regime = "bull"
        elif current_return < -0.05:
            regime = "bear"
        elif current_vol > 0.30:
            regime = "high_volatility"
        else:
            regime = "neutral"

        return {
            "current_regime": regime,
            "regime_transitions": "N/A - requires more sophisticated analysis"
        }

    def _calculate_allocation_effect(self) -> Dict[str, float]:
        """計算資產配置效應"""
        # 簡化實現
        return {"allocation_effect": 0.0}

    def _calculate_selection_effect(self) -> Dict[str, float]:
        """計算證券選擇效應"""
        # 簡化實現
        return {"selection_effect": 0.0}

    def _calculate_interaction_effect(self) -> Dict[str, float]:
        """計算交互效應"""
        # 簡化實現
        return {"interaction_effect": 0.0}

    def _calculate_periodic_attribution(self, period: str) -> List[Dict[str, Any]]:
        """計算週期性歸因"""
        # 簡化實現
        return []

    def _apply_stress_scenario(self, scenario_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """應用壓力情景"""
        shock = params.get("shock", 0)
        duration = params.get("duration", 1)

        # 計算壓力情景下的投資組合價值
        current_value = self.portfolio_data['value'].iloc[-1]
        stressed_value = current_value * (1 + shock)

        return {
            "scenario": scenario_name,
            "shock": shock,
            "duration": duration,
            "current_value": current_value,
            "stressed_value": stressed_value,
            "loss": current_value - stressed_value,
            "loss_percentage": abs(shock) * 100
        }

    def _simulate_scenario(self, scenario_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """模擬情景"""
        expected_return = params.get("return", 0)
        volatility = params.get("volatility", 0.2)

        # 蒙特卡羅模擬
        n_simulations = 1000
        n_periods = 252  # 一年

        simulated_returns = np.random.normal(
            expected_return / 252,
            volatility / np.sqrt(252),
            (n_simulations, n_periods)
        )

        # 計算終值分布
        final_values = (1 + simulated_returns).prod(axis=1)

        return {
            "scenario": scenario_name,
            "parameters": params,
            "expected_final_value": final_values.mean(),
            "percentile_5": np.percentile(final_values, 5),
            "percentile_95": np.percentile(final_values, 95),
            "probability_of_loss": (final_values < 1).mean()
        }

    def _compare_with_single_benchmark(self, benchmark_df: pd.DataFrame) -> Dict[str, Any]:
        """與單個基準比較"""
        portfolio_returns = self.portfolio_data['return'].reindex(benchmark_df.index).dropna()
        benchmark_returns = benchmark_df['return'].reindex(portfolio_returns.index).dropna()

        if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
            return {"message": "Insufficient overlapping data"}

        # 對齊數據
        portfolio_returns, benchmark_returns = portfolio_returns.align(benchmark_returns, join='inner')

        # 計算超額收益
        excess_returns = portfolio_returns - benchmark_returns

        # 計算指標
        tracking_error = excess_returns.std() * np.sqrt(252)
        information_ratio = excess_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0

        # Beta
        covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

        # Alpha
        portfolio_total_return = (self.portfolio_data['value'].iloc[-1] / self.portfolio_data['value'].iloc[0]) - 1
        benchmark_total_return = (benchmark_df['value'].iloc[-1] / benchmark_df['value'].iloc[0]) - 1
        alpha = portfolio_total_return - beta * benchmark_total_return

        # 上行/下行捕獲率
        up_periods = benchmark_returns > 0
        down_periods = benchmark_returns < 0

        upside_capture = 0
        downside_capture = 0

        if up_periods.sum() > 0:
            upside_capture = (
                portfolio_returns[up_periods].mean() / benchmark_returns[up_periods].mean()
            )

        if down_periods.sum() > 0:
            downside_capture = (
                portfolio_returns[down_periods].mean() / benchmark_returns[down_periods].mean()
            )

        return {
            "tracking_error": tracking_error,
            "information_ratio": information_ratio,
            "beta": beta,
            "alpha": alpha,
            "upside_capture": upside_capture,
            "downside_capture": downside_capture,
            "correlation": portfolio_returns.corr(benchmark_returns)
        }

    def _generate_summary_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成摘要報告"""
        summary = {
            "analysis_date": datetime.now().isoformat(),
            "period_analyzed": {
                "start": self.portfolio_data.index[0].date() if not self.portfolio_data.empty else None,
                "end": self.portfolio_data.index[-1].date() if not self.portfolio_data.empty else None
            },
            "key_metrics": {},
            "risk_assessment": {},
            "performance_vs_benchmark": {}
        }

        # 提取關鍵指標
        if AnalysisType.PERFORMANCE.value in results:
            summary["key_metrics"] = results[AnalysisType.PERFORMANCE.value]["metrics"]

        if AnalysisType.RISK.value in results:
            summary["risk_assessment"] = results[AnalysisType.RISK.value]

        if AnalysisType.COMPARISON.value in results:
            summary["performance_vs_benchmark"] = results[AnalysisType.COMPARISON.value]

        return summary

    def _generate_charts(self) -> Dict[str, str]:
        """生成圖表"""
        charts = {}

        try:
            # 設置圖表樣式
            plt.style.use(self.config.chart_style)

            # 1. 投資組合價值走勢圖
            fig, ax = plt.subplots(figsize=self.config.figsize)
            self.portfolio_data['value'].plot(ax=ax, label='Portfolio')
            ax.set_title('Portfolio Value Over Time')
            ax.set_ylabel('Value')
            ax.legend()
            plt.tight_layout()
            chart_path = f"{self.config.report_dir}/portfolio_value.png"
            plt.savefig(chart_path)
            plt.close()
            charts['portfolio_value'] = chart_path

            # 2. 回撤圖
            fig, ax = plt.subplots(figsize=self.config.figsize)
            cumulative = (1 + self.portfolio_data['return']).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            drawdown.plot(ax=ax, color='red', alpha=0.5)
            ax.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.3)
            ax.set_title('Portfolio Drawdown')
            ax.set_ylabel('Drawdown')
            plt.tight_layout()
            chart_path = f"{self.config.report_dir}/drawdown.png"
            plt.savefig(chart_path)
            plt.close()
            charts['drawdown'] = chart_path

            # 3. 滾動收益圖
            fig, ax = plt.subplots(figsize=self.config.figsize)
            rolling_returns = self.portfolio_data['return'].rolling(window=30).mean() * 252
            rolling_returns.plot(ax=ax)
            ax.set_title('30-Day Rolling Annualized Return')
            ax.set_ylabel('Return (%)')
            plt.tight_layout()
            chart_path = f"{self.config.report_dir}/rolling_returns.png"
            plt.savefig(chart_path)
            plt.close()
            charts['rolling_returns'] = chart_path

            # 4. 權重分布圖
            if self.weights_history:
                fig, ax = plt.subplots(figsize=self.config.figsize)
                latest_weights = self.weights_history[-1]['weights']
                assets = list(latest_weights.keys())
                weights = list(latest_weights.values())
                ax.pie(weights, labels=assets, autopct='%1.1f%%')
                ax.set_title('Current Portfolio Weights')
                plt.tight_layout()
                chart_path = f"{self.config.report_dir}/weights_distribution.png"
                plt.savefig(chart_path)
                plt.close()
                charts['weights_distribution'] = chart_path

            logger.info(f"Charts generated: {len(charts)}")
            return charts

        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return {}

    def export_report(
        self,
        filepath: str,
        format: str = "json"
    ) -> None:
        """
        導出分析報告

        Args:
            filepath: 文件路徑
            format: 導出格式（json, html, pdf）
        """
        try:
            # 運行分析
            results = self.run_analysis()

            if format.lower() == "json":
                # JSON報告
                import json
                with open(f"{filepath}.json", "w") as f:
                    json.dump(results, f, indent=2, default=str)
            elif format.lower() == "html":
                # HTML報告
                self._generate_html_report(results, f"{filepath}.html")
            elif format.lower() == "pdf":
                # PDF報告（需要額外依賴）
                self._generate_pdf_report(results, f"{filepath}.pdf")

            logger.info(f"Report exported: {filepath}.{format}")

        except Exception as e:
            logger.error(f"Report export failed: {e}")
            raise

    def _generate_html_report(self, results: Dict[str, Any], filepath: str):
        """生成HTML報告"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Portfolio Performance Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; }
                .metric { display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Portfolio Performance Report</h1>
                <p>Generated on: {date}</p>
            </div>

            <div class="section">
                <h2>Performance Summary</h2>
                {performance_metrics}
            </div>

            <div class="section">
                <h2>Risk Analysis</h2>
                {risk_analysis}
            </div>

            <div class="section">
                <h2>Charts</h2>
                {charts}
            </div>
        </body>
        </html>
        """

        # 格式化性能指標
        performance_html = ""
        if 'performance' in results and 'metrics' in results['performance']:
            for key, value in results['performance']['metrics'].items():
                performance_html += f'<div class="metric"><strong>{key}:</strong> {value:.4f}</div>'

        # 格式化風險分析
        risk_html = "<p>Risk analysis results would be displayed here</p>"

        # 格式化圖表
        charts_html = ""
        if 'charts' in results:
            for chart_name, chart_path in results['charts'].items():
                charts_html += f'<img src="{chart_path}" alt="{chart_name}" style="max-width: 100%; margin: 10px;">'

        # 生成HTML
        html_content = html_template.format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            performance_metrics=performance_html,
            risk_analysis=risk_html,
            charts=charts_html
        )

        with open(filepath, "w") as f:
            f.write(html_content)

    def _generate_pdf_report(self, results: Dict[str, Any], filepath: str):
        """生成PDF報告（需要reportlab或其他PDF庫）"""
        # 簡化實現 - 實際需要安裝並使用PDF生成庫
        logger.warning("PDF generation not implemented - would require additional dependencies")

    def _classify_volatility_regime(self, volatility: float) -> str:
        """分類波動率狀態"""
        if volatility < 0.10:
            return "low"
        elif volatility < 0.20:
            return "normal"
        elif volatility < 0.30:
            return "high"
        else:
            return "extreme"

    def _detect_volatility_clustering(self, returns: pd.Series) -> bool:
        """檢測波動率聚集"""
        # 使用簡單的方法：檢查高波動率後是否跟隨高波動率
        squared_returns = returns ** 2
        lagged_correlation = squared_returns.autocorr(lag=1)
        return lagged_correlation > 0.2

    def _classify_concentration(self, hhi: float) -> str:
        """分類集中度"""
        if hhi < 0.1:
            return "low"
        elif hhi < 0.2:
            return "moderate"
        elif hhi < 0.3:
            return "high"
        else:
            return "very_high"

    def _calculate_average_recovery_time(self, drawdown: pd.Series) -> float:
        """計算平均恢復時間"""
        recovery_times = []
        in_drawdown = False
        drawdown_start = None

        for date, dd in drawdown.items():
            if dd < 0 and not in_drawdown:
                in_drawdown = True
                drawdown_start = date
            elif dd >= 0 and in_drawdown:
                in_drawdown = False
                recovery_time = (date - drawdown_start).days
                recovery_times.append(recovery_time)

        return np.mean(recovery_times) if recovery_times else 0