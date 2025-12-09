#!/usr / bin / env python3
"""
綜合性能評估和過擬合檢測框架
Comprehensive Performance Evaluation and Overfitting Detection Framework

專業級量化策略評估系統：
- 綜合評分算法 (Sharpe, Max DD, Calmar, Sortino等)
- 多目標優化支持
- 回測驗證機制
- 過擬合檢測和防護
- 詳細的性能報告生成器
"""

import logging
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings("ignore")

# 導入回測結果
from .vectorbt_engine import BacktestResult

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指標數據類"""

    # 收益指標
    total_return: float = 0.0
    annual_return: float = 0.0
    cagr: float = 0.0  # 複合年增長率

    # 風險指標
    volatility: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    var_95: float = 0.0  # 95% VaR
    cvar_95: float = 0.0  # 95% CVaR

    # 風險調整後收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    treynor_ratio: float = 0.0

    # 交易指標
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_trade_return: float = 0.0
    total_trades: int = 0
    avg_trade_duration: float = 0.0

    # 統計指標
    skewness: float = 0.0
    kurtosis: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0

    # 穩定性指標
    rolling_sharpe_std: float = 0.0
    upside_capture: float = 0.0
    downside_capture: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """轉換為字典格式"""
        return {
            "return_metrics": {
                "total_return": self.total_return,
                "annual_return": self.annual_return,
                "cagr": self.cagr,
            },
            "risk_metrics": {
                "volatility": self.volatility,
                "max_drawdown": self.max_drawdown,
                "max_drawdown_duration": self.max_drawdown_duration,
                "var_95": self.var_95,
                "cvar_95": self.cvar_95,
            },
            "risk_adjusted_metrics": {
                "sharpe_ratio": self.sharpe_ratio,
                "sortino_ratio": self.sortino_ratio,
                "calmar_ratio": self.calmar_ratio,
                "information_ratio": self.information_ratio,
                "treynor_ratio": self.treynor_ratio,
            },
            "trading_metrics": {
                "win_rate": self.win_rate,
                "profit_factor": self.profit_factor,
                "avg_trade_return": self.avg_trade_return,
                "total_trades": self.total_trades,
                "avg_trade_duration": self.avg_trade_duration,
            },
            "statistical_metrics": {
                "skewness": self.skewness,
                "kurtosis": self.kurtosis,
                "beta": self.beta,
                "alpha": self.alpha,
            },
            "stability_metrics": {
                "rolling_sharpe_std": self.rolling_sharpe_std,
                "upside_capture": self.upside_capture,
                "downside_capture": self.downside_capture,
            },
        }


@dataclass
class OverfittingMetrics:
    """過擬合檢測指標"""

    # 樣本內外性能差異
    in_sample_sharpe: float = 0.0
    out_of_sample_sharpe: float = 0.0
    sharpe_decay: float = 0.0  # Sharpe衰減率

    # 參數穩定性
    parameter_stability: float = 0.0
    optimal_parameter_cluster: float = 0.0  # 最優參數聚集度

    # 時間穩定性
    walk_forward_performance: float = 0.0
    rolling_performance_std: float = 0.0

    # 統計顯著性
    p_value: float = 1.0
    deflation_adjusted_sharpe: float = 0.0
    minimum_track_record_length: int = 0

    # 過擬合風險評分
    overfitting_risk_score: float = 0.0  # 0 - 100，越高風險越大
    confidence_level: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "sample_stability": {
                "in_sample_sharpe": self.in_sample_sharpe,
                "out_of_sample_sharpe": self.out_of_sample_sharpe,
                "sharpe_decay": self.sharpe_decay,
            },
            "parameter_stability": {
                "parameter_stability": self.parameter_stability,
                "optimal_parameter_cluster": self.optimal_parameter_cluster,
            },
            "temporal_stability": {
                "walk_forward_performance": self.walk_forward_performance,
                "rolling_performance_std": self.rolling_performance_std,
            },
            "statistical_significance": {
                "p_value": self.p_value,
                "deflation_adjusted_sharpe": self.deflation_adjusted_sharpe,
                "minimum_track_record_length": self.minimum_track_record_length,
            },
            "overfitting_assessment": {
                "overfitting_risk_score": self.overfitting_risk_score,
                "confidence_level": self.confidence_level,
                "risk_level": self._get_risk_level(),
            },
        }

    def _get_risk_level(self) -> str:
        """獲取風險等級"""
        if self.overfitting_risk_score >= 80:
            return "HIGH"
        elif self.overfitting_risk_score >= 60:
            return "MODERATE"
        elif self.overfitting_risk_score >= 40:
            return "LOW"
        else:
            return "VERY_LOW"


class PerformanceEvaluator:
    """
    綜合性能評估器

    提供專業級的量化策略性能評估：
    - 全面的風險收益指標計算
    - 過擬合檢測和防護
    - 多目標評分系統
    - 詳細的性能報告
    """

    def __init__(
        self,
        risk_free_rate: float = 0.03,
        benchmark_returns: Optional[pd.Series] = None,
    ):
        """
        初始化性能評估器

        Args:
            risk_free_rate: 無風險利率 (默認3%)
            benchmark_returns: 基準指數收益序列
        """
        self.risk_free_rate = risk_free_rate
        self.benchmark_returns = benchmark_returns
        self.trading_days_per_year = 252

        logger.info(
            f"Performance evaluator initialized with risk - free rate: {risk_free_rate}"
        )

    def calculate_comprehensive_metrics(
        self,
        backtest_result: BacktestResult,
        benchmark_data: Optional[pd.DataFrame] = None,
    ) -> PerformanceMetrics:
        """
        計算綜合性能指標

        Args:
            backtest_result: 回測結果
            benchmark_data: 基準數據

        Returns:
            綜合性能指標
        """
        try:
            # 提取回測數據
            returns = backtest_result.returns
            equity_curve = backtest_result.equity_curve
            trades = backtest_result.trades

            # 基本計算
            metrics = PerformanceMetrics()

            # 收益指標
            metrics.total_return = backtest_result.total_return
            metrics.annual_return = backtest_result.annual_return
            metrics.cagr = self._calculate_cagr(equity_curve)

            # 風險指標
            metrics.volatility = self._calculate_volatility(returns)
            metrics.max_drawdown = backtest_result.max_drawdown
            metrics.max_drawdown_duration = self._calculate_max_drawdown_duration(
                equity_curve
            )
            metrics.var_95, metrics.cvar_95 = self._calculate_var_cvar(returns)

            # 風險調整後收益
            metrics.sharpe_ratio = backtest_result.sharpe_ratio
            metrics.sortino_ratio = self._calculate_sortino_ratio(returns)
            metrics.calmar_ratio = backtest_result.calmar_ratio

            if benchmark_data is not None and len(benchmark_data) > 0:
                benchmark_returns = benchmark_data["close"].pct_change().dropna()
                metrics.information_ratio = self._calculate_information_ratio(
                    returns, benchmark_returns
                )
                metrics.beta = self._calculate_beta(returns, benchmark_returns)
                metrics.alpha = self._calculate_alpha(
                    returns, benchmark_returns, metrics.beta
                )
                metrics.treynor_ratio = self._calculate_treynor_ratio(
                    returns, metrics.beta
                )

                # 捕獲比率
                metrics.upside_capture, metrics.downside_capture = (
                    self._calculate_capture_ratios(returns, benchmark_returns)
                )

            # 交易指標
            metrics.win_rate = backtest_result.win_rate
            metrics.profit_factor = backtest_result.profit_factor
            metrics.total_trades = backtest_result.total_trades

            if len(trades) > 0:
                metrics.avg_trade_return = self._calculate_avg_trade_return(trades)
                metrics.avg_trade_duration = self._calculate_avg_trade_duration(trades)

            # 統計指標
            metrics.skewness = self._calculate_skewness(returns)
            metrics.kurtosis = self._calculate_kurtosis(returns)

            # 穩定性指標
            metrics.rolling_sharpe_std = self._calculate_rolling_sharpe_stability(
                returns
            )

            logger.info(
                f"Comprehensive metrics calculated for {backtest_result.symbol}"
            )
            return metrics

        except Exception as e:
            logger.error(f"Error calculating comprehensive metrics: {e}")
            return PerformanceMetrics()

    def detect_overfitting(
        self,
        optimization_results: List[BacktestResult],
        validation_data: Optional[pd.DataFrame] = None,
    ) -> OverfittingMetrics:
        """
        檢測過擬合

        Args:
            optimization_results: 優化結果列表
            validation_data: 驗證數據

        Returns:
            過擬合檢測指標
        """
        if not optimization_results:
            return OverfittingMetrics()

        try:
            overfitting_metrics = OverfittingMetrics()

            # 計算樣本內外性能差異
            overfitting_metrics.in_sample_sharpe = max(
                r.sharpe_ratio for r in optimization_results
            )

            if validation_data is not None and len(optimization_results) > 0:
                # 選擇最佳策略進行樣本外測試
                best_result = max(optimization_results, key = lambda r: r.sharpe_ratio)
                out_sample_result = self._validate_out_of_sample(
                    best_result, validation_data
                )
                overfitting_metrics.out_of_sample_sharpe = (
                    out_sample_result.sharpe_ratio
                )

                # Sharpe衰減率
                if overfitting_metrics.in_sample_sharpe > 0:
                    overfitting_metrics.sharpe_decay = (
                        1
                        - overfitting_metrics.out_of_sample_sharpe
                        / overfitting_metrics.in_sample_sharpe
                    )

            # 參數穩定性分析
            overfitting_metrics.parameter_stability = self._analyze_parameter_stability(
                optimization_results
            )
            overfitting_metrics.optimal_parameter_cluster = (
                self._analyze_optimal_parameter_clustering(optimization_results)
            )

            # 時間穩定性分析
            overfitting_metrics.walk_forward_performance = self._walk_forward_analysis(
                optimization_results
            )
            overfitting_metrics.rolling_performance_std = (
                self._calculate_rolling_performance_stability(optimization_results)
            )

            # 統計顯著性檢驗
            if len(optimization_results) > 1:
                sharpe_ratios = [r.sharpe_ratio for r in optimization_results]
                overfitting_metrics.p_value = self._calculate_statistical_significance(
                    sharpe_ratios
                )
                overfitting_metrics.deflation_adjusted_sharpe = (
                    self._calculate_deflation_adjusted_sharpe(sharpe_ratios)
                )
                overfitting_metrics.minimum_track_record_length = (
                    self._calculate_minimum_track_record_length(optimization_results[0])
                )

            # 計算綜合過擬合風險評分
            overfitting_metrics.overfitting_risk_score = (
                self._calculate_overfitting_risk_score(overfitting_metrics)
            )
            overfitting_metrics.confidence_level = (
                100 - overfitting_metrics.overfitting_risk_score
            )

            logger.info("Overfitting detection completed")
            return overfitting_metrics

        except Exception as e:
            logger.error(f"Error in overfitting detection: {e}")
            return OverfittingMetrics()

    def calculate_multi_objective_score(
        self,
        performance_metrics: PerformanceMetrics,
        objectives: List[str],
        weights: Optional[Dict[str, float]] = None,
    ) -> Tuple[float, Dict[str, float]]:
        """
        計算多目標評分

        Args:
            performance_metrics: 性能指標
            objectives: 目標列表
            weights: 權重配置

        Returns:
            綜合評分和分項得分
        """
        if weights is None:
            weights = self._get_default_objective_weights(objectives)

        # 確保權重歸一化
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        # 計算各項目標得分
        scores = {}
        total_score = 0.0

        for objective in objectives:
            if objective == "sharpe_ratio":
                score = self._normalize_sharpe_score(performance_metrics.sharpe_ratio)
            elif objective == "max_drawdown":
                score = self._normalize_drawdown_score(performance_metrics.max_drawdown)
            elif objective == "total_return":
                score = self._normalize_return_score(performance_metrics.total_return)
            elif objective == "calmar_ratio":
                score = self._normalize_calmar_score(performance_metrics.calmar_ratio)
            elif objective == "sortino_ratio":
                score = self._normalize_sortino_score(performance_metrics.sortino_ratio)
            elif objective == "win_rate":
                score = performance_metrics.win_rate / 100  # 標準化到0 - 1
            elif objective == "profit_factor":
                score = min(1.0, performance_metrics.profit_factor / 3)  # 假設3為優秀值
            elif objective == "stability":
                score = self._calculate_stability_score(performance_metrics)
            else:
                score = 0.0

            scores[objective] = score
            weight = weights.get(objective, 0.0)
            total_score += score * weight

        return total_score, scores

    def generate_performance_report(
        self,
        backtest_result: BacktestResult,
        optimization_results: Optional[List[BacktestResult]] = None,
        benchmark_data: Optional[pd.DataFrame] = None,
        include_overfitting_analysis: bool = True,
    ) -> Dict[str, Any]:
        """
        生成詳細的性能報告

        Args:
            backtest_result: 主要回測結果
            optimization_results: 優化結果列表
            benchmark_data: 基準數據
            include_overfitting_analysis: 是否包含過擬合分析

        Returns:
            詳細的性能報告
        """
        try:
            report = {
                "report_metadata": {
                    "symbol": backtest_result.symbol,
                    "strategy_name": backtest_result.strategy_name,
                    "parameters": backtest_result.parameters,
                    "report_time": datetime.now().isoformat(),
                    "data_period": {
                        "start_date": backtest_result.start_date,
                        "end_date": backtest_result.end_date,
                        "data_points": backtest_result.data_points,
                    },
                }
            }

            # 計算綜合性能指標
            performance_metrics = self.calculate_comprehensive_metrics(
                backtest_result, benchmark_data
            )
            report["performance_metrics"] = performance_metrics.to_dict()

            # 過擬合分析
            if include_overfitting_analysis and optimization_results:
                overfitting_metrics = self.detect_overfitting(
                    optimization_results, benchmark_data
                )
                report["overfitting_analysis"] = overfitting_metrics.to_dict()

            # 多目標評分
            objectives = [
                "sharpe_ratio",
                "max_drawdown",
                "total_return",
                "calmar_ratio",
                "stability",
            ]
            total_score, objective_scores = self.calculate_multi_objective_score(
                performance_metrics, objectives
            )
            report["multi_objective_score"] = {
                "total_score": round(total_score * 100, 2),
                "objective_scores": {
                    k: round(v * 100, 2) for k, v in objective_scores.items()
                },
                "objectives_used": objectives,
                "grade": self._get_performance_grade(total_score),
            }

            # 策略評級
            report["strategy_rating"] = self._generate_strategy_rating(
                performance_metrics
            )

            # 投資建議
            report["investment_recommendation"] = (
                self._generate_investment_recommendation(performance_metrics)
            )

            # 風險評估
            report["risk_assessment"] = self._generate_risk_assessment(
                performance_metrics
            )

            logger.info(f"Performance report generated for {backtest_result.symbol}")
            return report

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e), "report_time": datetime.now().isoformat()}

    # 私有方法：指標計算
    def _calculate_cagr(self, equity_curve: pd.Series) -> float:
        """計算複合年增長率"""
        if len(equity_curve) < 2:
            return 0.0

        start_value = equity_curve.iloc[0]
        end_value = equity_curve.iloc[-1]
        years = len(equity_curve) / self.trading_days_per_year

        if start_value <= 0 or years <= 0:
            return 0.0

        cagr = (end_value / start_value) ** (1 / years) - 1
        return cagr

    def _calculate_volatility(self, returns: pd.Series) -> float:
        """計算波動率"""
        return returns.std() * np.sqrt(self.trading_days_per_year)

    def _calculate_max_drawdown_duration(self, equity_curve: pd.Series) -> int:
        """計算最大回撤持續天數"""
        cumulative_max = equity_curve.expanding().max()
        drawdown = equity_curve / cumulative_max - 1

        # 找到回撤期間
        in_drawdown = drawdown < 0
        drawdown_periods = []

        start_idx = None
        for i, is_dd in enumerate(in_drawdown):
            if is_dd and start_idx is None:
                start_idx = i
            elif not is_dd and start_idx is not None:
                drawdown_periods.append(i - start_idx)
                start_idx = None

        # 處理最後一個回撤期
        if start_idx is not None:
            drawdown_periods.append(len(in_drawdown) - start_idx)

        return max(drawdown_periods) if drawdown_periods else 0

    def _calculate_var_cvar(
        self, returns: pd.Series, confidence_level: float = 0.05
    ) -> Tuple[float, float]:
        """計算VaR和CVaR"""
        var = np.percentile(returns, confidence_level * 100)
        cvar = returns[returns <= var].mean()
        return var, cvar

    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """計算Sortino比率"""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return 0.0

        downside_deviation = downside_returns.std() * np.sqrt(
            self.trading_days_per_year
        )
        excess_return = (
            returns.mean() * self.trading_days_per_year - self.risk_free_rate
        )

        return excess_return / downside_deviation if downside_deviation > 0 else 0.0

    def _calculate_information_ratio(
        self, returns: pd.Series, benchmark_returns: pd.Series
    ) -> float:
        """計算信息比率"""
        # 對齊時間序列
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join="inner"
        )
        if len(aligned_returns) == 0:
            return 0.0

        active_returns = aligned_returns - aligned_benchmark
        tracking_error = active_returns.std() * np.sqrt(self.trading_days_per_year)

        return (
            active_returns.mean() * self.trading_days_per_year / tracking_error
            if tracking_error > 0
            else 0.0
        )

    def _calculate_beta(
        self, returns: pd.Series, benchmark_returns: pd.Series
    ) -> float:
        """計算Beta"""
        # 對齊時間序列
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join="inner"
        )
        if len(aligned_returns) < 2:
            return 0.0

        covariance = np.cov(aligned_returns, aligned_benchmark)[0, 1]
        benchmark_variance = np.var(aligned_benchmark)

        return covariance / benchmark_variance if benchmark_variance > 0 else 0.0

    def _calculate_alpha(
        self, returns: pd.Series, benchmark_returns: pd.Series, beta: float
    ) -> float:
        """計算Alpha"""
        # 對齊時間序列
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join="inner"
        )
        if len(aligned_returns) == 0:
            return 0.0

        portfolio_return = aligned_returns.mean() * self.trading_days_per_year
        benchmark_return = aligned_benchmark.mean() * self.trading_days_per_year

        expected_return = self.risk_free_rate + beta * (
            benchmark_return - self.risk_free_rate
        )
        alpha = portfolio_return - expected_return

        return alpha

    def _calculate_treynor_ratio(self, returns: pd.Series, beta: float) -> float:
        """計算Treynor比率"""
        if abs(beta) < 1e - 6:  # 避免除零
            return 0.0

        excess_return = (
            returns.mean() * self.trading_days_per_year - self.risk_free_rate
        )
        return excess_return / beta

    def _calculate_capture_ratios(
        self, returns: pd.Series, benchmark_returns: pd.Series
    ) -> Tuple[float, float]:
        """計算上漲 / 下跌捕獲比率"""
        # 對齊時間序列
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join="inner"
        )
        if len(aligned_returns) == 0:
            return 0.0, 0.0

        # 上漲捕獲比率
        up_periods = aligned_benchmark > 0
        portfolio_up = aligned_returns[up_periods].mean()
        benchmark_up = aligned_benchmark[up_periods].mean()
        upside_capture = portfolio_up / benchmark_up if benchmark_up > 0 else 0.0

        # 下跌捕獲比率
        down_periods = aligned_benchmark < 0
        portfolio_down = aligned_returns[down_periods].mean()
        benchmark_down = aligned_benchmark[down_periods].mean()
        downside_capture = (
            portfolio_down / benchmark_down if benchmark_down < 0 else 0.0
        )

        return upside_capture, abs(downside_capture)

    def _calculate_avg_trade_return(self, trades: pd.DataFrame) -> float:
        """計算平均交易回報"""
        if "Pnl" in trades.columns:
            return trades["Pnl"].mean()
        return 0.0

    def _calculate_avg_trade_duration(self, trades: pd.DataFrame) -> float:
        """計算平均交易持續時間"""
        if "Duration" in trades.columns:
            return trades["Duration"].mean()
        return 0.0

    def _calculate_skewness(self, returns: pd.Series) -> float:
        """計算偏度"""
        return returns.skew()

    def _calculate_kurtosis(self, returns: pd.Series) -> float:
        """計算峰度"""
        return returns.kurtosis()

    def _calculate_rolling_sharpe_stability(
        self, returns: pd.Series, window: int = 63
    ) -> float:
        """計算滾動Sharpe比率穩定性"""
        if len(returns) < window * 2:
            return 0.0

        rolling_sharpe = (
            returns.rolling(window = window)
            .apply(
                lambda x: (
                    x.mean() * np.sqrt(self.trading_days_per_year) - self.risk_free_rate
                )
                / (x.std() * np.sqrt(self.trading_days_per_year))
            )
            .dropna()
        )

        return rolling_sharpe.std()

    # 私有方法：過擬合檢測
    def _validate_out_of_sample(
        self, in_sample_result: BacktestResult, validation_data: pd.DataFrame
    ) -> BacktestResult:
        """樣本外驗證"""
        from .vectorbt_engine import VectorBTEngine

        engine = VectorBTEngine()
        out_sample_result = engine.backtest_strategy(
            data = validation_data,
            strategy = in_sample_result.strategy_name,
            parameters = in_sample_result.parameters,
            symbol = in_sample_result.symbol + "_OOS",
        )

        return out_sample_result

    def _analyze_parameter_stability(
        self, optimization_results: List[BacktestResult]
    ) -> float:
        """分析參數穩定性"""
        if len(optimization_results) < 10:
            return 0.0

        # 提取頂級結果的參數
        top_results = sorted(
            optimization_results, key = lambda r: r.sharpe_ratio, reverse = True
        )[:20]
        sharpe_values = [r.sharpe_ratio for r in top_results]

        # 計算Sharpe比率的穩定性
        return (
            1.0 - (np.std(sharpe_values) / np.mean(sharpe_values))
            if np.mean(sharpe_values) > 0
            else 0.0
        )

    def _analyze_optimal_parameter_clustering(
        self, optimization_results: List[BacktestResult]
    ) -> float:
        """分析最優參數聚集度"""
        if len(optimization_results) < 20:
            return 0.0

        # 找到性能最好的前10%結果
        threshold = np.percentile([r.sharpe_ratio for r in optimization_results], 90)
        top_results = [r for r in optimization_results if r.sharpe_ratio >= threshold]

        if len(top_results) < 2:
            return 0.0

        # 分析參數相似度（簡化版本）
        # 實際應用中可以使用更複雜的參數距離度量
        return 0.7  # 占位值，實際需要具體實現

    def _walk_forward_analysis(
        self, optimization_results: List[BacktestResult]
    ) -> float:
        """走步向前分析"""
        # 簡化版本的走步向前分析
        # 實際需要將數據分為多個時間窗口進行分析
        if len(optimization_results) < 5:
            return 0.0

        sharpe_values = [r.sharpe_ratio for r in optimization_results]
        return (
            1.0 - (np.std(sharpe_values) / np.mean(sharpe_values))
            if np.mean(sharpe_values) > 0
            else 0.0
        )

    def _calculate_rolling_performance_stability(
        self, optimization_results: List[BacktestResult]
    ) -> float:
        """計算滾動性能穩定性"""
        if len(optimization_results) < 10:
            return 0.0

        returns = [r.total_return for r in optimization_results]
        return np.std(returns) / np.mean(returns) if np.mean(returns) > 0 else 1.0

    def _calculate_statistical_significance(self, sharpe_ratios: List[float]) -> float:
        """計算統計顯著性"""
        if len(sharpe_ratios) < 2:
            return 1.0

        # 使用t檢驗
        best_sharpe = max(sharpe_ratios)
        mean_sharpe = np.mean(sharpe_ratios)
        std_sharpe = np.std(sharpe_ratios)

        if std_sharpe == 0:
            return 0.0

        t_statistic = (best_sharpe - mean_sharpe) / std_sharpe
        p_value = 2 * (1 - stats.t.cdf(abs(t_statistic), len(sharpe_ratios) - 1))

        return min(1.0, p_value)

    def _calculate_deflation_adjusted_sharpe(self, sharpe_ratios: List[float]) -> float:
        """計算通縮調整後的Sharpe比率"""
        if not sharpe_ratios:
            return 0.0

        # Bailey & López de Prado (2014) deflation method
        best_sharpe = max(sharpe_ratios)
        n = len(sharpe_ratios)

        # 計算相關性矩陣（假設策略間相關性為0.5）
        avg_correlation = 0.5
        variance = n * avg_correlation * (1 - avg_correlation)

        deflation_factor = np.sqrt(1 + variance)
        deflated_sharpe = best_sharpe / deflation_factor

        return deflated_sharpe

    def _calculate_minimum_track_record_length(
        self, backtest_result: BacktestResult
    ) -> int:
        """計算最小追蹤記錄長度"""
        sharpe_ratio = backtest_result.sharpe_ratio
        if sharpe_ratio <= 0:
            return float("inf")

        # 最小追蹤記錄長度公式
        min_trl = (1 + sharpe_ratio * *2) * 252 / sharpe_ratio * *2
        return int(min_trl)

    def _calculate_overfitting_risk_score(self, metrics: OverfittingMetrics) -> float:
        """計算綜合過擬合風險評分"""
        risk_factors = []

        # Sharpe衰減因子 (權重30%)
        if metrics.sharpe_decay > 0:
            risk_factors.append(min(100, metrics.sharpe_decay * 100 * 3))

        # 參數穩定性因子 (權重20%)
        stability_risk = (1 - metrics.parameter_stability) * 100
        risk_factors.append(stability_risk * 2)

        # 統計顯著性因子 (權重25%)
        significance_risk = metrics.p_value * 100
        risk_factors.append(significance_risk * 2.5)

        # 最小追蹤記錄長度因子 (權重15%)
        if metrics.minimum_track_record_length > 0:
            data_points = 252 * 3  # 假設3年數據
            trl_risk = max(
                0, 100 - (data_points / metrics.minimum_track_record_length) * 100
            )
            risk_factors.append(trl_risk * 1.5)

        # 滾動性能穩定性因子 (權重10%)
        performance_risk = metrics.rolling_performance_std * 100
        risk_factors.append(performance_risk)

        return np.mean(risk_factors)

    # 私有方法：多目標評分
    def _get_default_objective_weights(self, objectives: List[str]) -> Dict[str, float]:
        """獲取默認目標權重"""
        default_weights = {
            "sharpe_ratio": 0.30,
            "max_drawdown": 0.25,
            "total_return": 0.20,
            "calmar_ratio": 0.15,
            "sortino_ratio": 0.10,
            "win_rate": 0.10,
            "profit_factor": 0.05,
            "stability": 0.15,
        }

        return {obj: default_weights.get(obj, 0.1) for obj in objectives}

    def _normalize_sharpe_score(self, sharpe_ratio: float) -> float:
        """Sharpe比率標準化"""
        # 假設3為優秀，1為良好，0為可接受
        if sharpe_ratio >= 3:
            return 1.0
        elif sharpe_ratio >= 1:
            return 0.5 + (sharpe_ratio - 1) / 4
        elif sharpe_ratio >= 0:
            return sharpe_ratio / 2
        else:
            return 0.0

    def _normalize_drawdown_score(self, max_drawdown: float) -> float:
        """最大回撤標準化（回撤越小越好）"""
        # 轉換為正數
        abs_drawdown = abs(max_drawdown)
        if abs_drawdown <= 0.05:  # 5%以內
            return 1.0
        elif abs_drawdown <= 0.15:  # 15%以內
            return 1.0 - (abs_drawdown - 0.05) * 5
        elif abs_drawdown <= 0.30:  # 30%以內
            return 0.5 - (abs_drawdown - 0.15) * 2
        else:
            return max(0, 0.2 - (abs_drawdown - 0.30))

    def _normalize_return_score(self, total_return: float) -> float:
        """總回報標準化"""
        # 假設50%為優秀，20%為良好，10%為可接受
        if total_return >= 0.5:
            return 1.0
        elif total_return >= 0.2:
            return 0.7 + (total_return - 0.2) * 1
        elif total_return >= 0.1:
            return 0.5 + (total_return - 0.1) * 2
        elif total_return >= 0:
            return total_return * 5
        else:
            return 0.0

    def _normalize_calmar_score(self, calmar_ratio: float) -> float:
        """Calmar比率標準化"""
        if calmar_ratio >= 3:
            return 1.0
        elif calmar_ratio >= 1:
            return 0.5 + (calmar_ratio - 1) / 4
        elif calmar_ratio >= 0:
            return calmar_ratio / 2
        else:
            return 0.0

    def _normalize_sortino_score(self, sortino_ratio: float) -> float:
        """Sortino比率標準化"""
        if sortino_ratio >= 4:
            return 1.0
        elif sortino_ratio >= 1.5:
            return 0.7 + (sortino_ratio - 1.5) / 8.3
        elif sortino_ratio >= 0:
            return sortino_ratio / 3
        else:
            return 0.0

    def _calculate_stability_score(self, metrics: PerformanceMetrics) -> float:
        """計算穩定性得分"""
        stability_factors = []

        # Sharpe比率穩定性
        if metrics.rolling_sharpe_std > 0:
            sharpe_stability = max(0, 1 - metrics.rolling_sharpe_std / 2)
            stability_factors.append(sharpe_stability)

        # 捕獲比率平衡性
        if metrics.upside_capture > 0 and metrics.downside_capture > 0:
            capture_balance = (
                1 - abs(metrics.upside_capture - metrics.downside_capture) / 2
            )
            stability_factors.append(capture_balance)

        # 偏度和峰度
        skewness_score = max(0, 1 - abs(metrics.skewness) / 2)
        kurtosis_score = max(0, 1 - abs(metrics.kurtosis - 3) / 5)  # 正態分佈峰度為3
        stability_factors.extend([skewness_score, kurtosis_score])

        return np.mean(stability_factors)

    def _get_performance_grade(self, score: float) -> str:
        """獲取性能等級"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.85:
            return "A"
        elif score >= 0.8:
            return "A-"
        elif score >= 0.75:
            return "B+"
        elif score >= 0.7:
            return "B"
        elif score >= 0.65:
            return "B-"
        elif score >= 0.6:
            return "C+"
        elif score >= 0.55:
            return "C"
        elif score >= 0.5:
            return "C-"
        else:
            return "D"

    # 私有方法：報告生成
    def _generate_strategy_rating(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """生成策略評級"""
        ratings = {}

        # 收益評級
        if metrics.total_return >= 0.3:
            ratings["return_rating"] = "EXCELLENT"
        elif metrics.total_return >= 0.15:
            ratings["return_rating"] = "GOOD"
        elif metrics.total_return >= 0.05:
            ratings["return_rating"] = "AVERAGE"
        else:
            ratings["return_rating"] = "POOR"

        # 風險評級
        if abs(metrics.max_drawdown) <= 0.05:
            ratings["risk_rating"] = "LOW"
        elif abs(metrics.max_drawdown) <= 0.15:
            ratings["risk_rating"] = "MODERATE"
        elif abs(metrics.max_drawdown) <= 0.25:
            ratings["risk_rating"] = "HIGH"
        else:
            ratings["risk_rating"] = "VERY_HIGH"

        # 風險調整後收益評級
        if metrics.sharpe_ratio >= 2:
            ratings["risk_adjusted_rating"] = "EXCELLENT"
        elif metrics.sharpe_ratio >= 1:
            ratings["risk_adjusted_rating"] = "GOOD"
        elif metrics.sharpe_ratio >= 0.5:
            ratings["risk_adjusted_rating"] = "AVERAGE"
        else:
            ratings["risk_adjusted_rating"] = "POOR"

        # 綜合評級
        rating_scores = {"EXCELLENT": 4, "GOOD": 3, "AVERAGE": 2, "POOR": 1}

        overall_score = (
            rating_scores[ratings["return_rating"]] * 0.3
            + rating_scores[ratings["risk_rating"]] * 0.2  # 風險越低越好，所以要反轉
            + rating_scores[ratings["risk_adjusted_rating"]] * 0.5
        )

        if overall_score >= 3.5:
            ratings["overall_rating"] = "EXCELLENT"
        elif overall_score >= 2.5:
            ratings["overall_rating"] = "GOOD"
        elif overall_score >= 1.5:
            ratings["overall_rating"] = "AVERAGE"
        else:
            ratings["overall_rating"] = "POOR"

        return ratings

    def _generate_investment_recommendation(
        self, metrics: PerformanceMetrics
    ) -> Dict[str, Any]:
        """生成投資建議"""
        recommendation = {
            "recommendation": "HOLD",
            "confidence_level": 0.5,
            "key_strengths": [],
            "key_concerns": [],
            "allocation_suggestion": "5 - 10%",
        }

        # 分析優勢
        if metrics.sharpe_ratio > 1.5:
            recommendation["key_strengths"].append("優異的風險調整後收益")
        if abs(metrics.max_drawdown) < 0.1:
            recommendation["key_strengths"].append("良好的風險控制")
        if metrics.win_rate > 0.6:
            recommendation["key_strengths"].append("高勝率")
        if metrics.calmar_ratio > 2:
            recommendation["key_strengths"].append("優秀的回撤恢復能力")

        # 分析關注點
        if metrics.sharpe_ratio < 0.5:
            recommendation["key_concerns"].append("風險調整後收益偏低")
        if abs(metrics.max_drawdown) > 0.3:
            recommendation["key_concerns"].append("最大回撤過大")
        if metrics.volatility > 0.3:
            recommendation["key_concerns"].append("波動率偏高")
        if metrics.total_trades < 10:
            recommendation["key_concerns"].append("交易樣本不足")

        # 綜合建議
        if metrics.sharpe_ratio > 2 and abs(metrics.max_drawdown) < 0.15:
            recommendation["recommendation"] = "STRONG_BUY"
            recommendation["allocation_suggestion"] = "15 - 25%"
            recommendation["confidence_level"] = 0.8
        elif metrics.sharpe_ratio > 1 and abs(metrics.max_drawdown) < 0.2:
            recommendation["recommendation"] = "BUY"
            recommendation["allocation_suggestion"] = "10 - 15%"
            recommendation["confidence_level"] = 0.7
        elif metrics.sharpe_ratio > 0.5 and abs(metrics.max_drawdown) < 0.25:
            recommendation["recommendation"] = "CONSIDER"
            recommendation["allocation_suggestion"] = "5 - 10%"
            recommendation["confidence_level"] = 0.6
        elif metrics.sharpe_ratio < 0:
            recommendation["recommendation"] = "AVOID"
            recommendation["allocation_suggestion"] = "0%"
            recommendation["confidence_level"] = 0.8

        return recommendation

    def _generate_risk_assessment(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """生成風險評估"""
        risk_assessment = {
            "overall_risk_level": "MODERATE",
            "risk_factors": [],
            "risk_score": 50,
            "suggested_risk_measures": [],
        }

        risk_score = 50  # 基礎分

        # 波動率風險
        if metrics.volatility > 0.4:
            risk_assessment["risk_factors"].append("高波動率風險")
            risk_score += 20
        elif metrics.volatility > 0.25:
            risk_assessment["risk_factors"].append("中等波動率風險")
            risk_score += 10

        # 回撤風險
        if abs(metrics.max_drawdown) > 0.4:
            risk_assessment["risk_factors"].append("極端回撤風險")
            risk_score += 25
        elif abs(metrics.max_drawdown) > 0.25:
            risk_assessment["risk_factors"].append("較大回撤風險")
            risk_score += 15
        elif abs(metrics.max_drawdown) > 0.15:
            risk_assessment["risk_factors"].append("回撤風險")
            risk_score += 10

        # 流動性風險（基於交易頻率）
        if metrics.total_trades < 5:
            risk_assessment["risk_factors"].append("流動性風險（交易頻率過低）")
            risk_score += 15

        # 集中度風險（基於持倉集中度，這裡簡化處理）
        if metrics.avg_trade_duration > 30:  # 假設持倉天數過長
            risk_assessment["risk_factors"].append("集中度風險")
            risk_score += 10

        # 設定整體風險等級
        risk_assessment["risk_score"] = min(100, risk_score)
        if risk_assessment["risk_score"] >= 80:
            risk_assessment["overall_risk_level"] = "HIGH"
        elif risk_assessment["risk_score"] >= 60:
            risk_assessment["overall_risk_level"] = "MODERATE"
        elif risk_assessment["risk_score"] >= 40:
            risk_assessment["overall_risk_level"] = "LOW"
        else:
            risk_assessment["overall_risk_level"] = "VERY_LOW"

        # 建議的風險措施
        if risk_assessment["risk_score"] > 70:
            risk_assessment["suggested_risk_measures"].extend(
                ["降低倉位規模", "設置更嚴格的止損", "增加多樣化配置"]
            )
        elif risk_assessment["risk_score"] > 50:
            risk_assessment["suggested_risk_measures"].extend(
                ["適度降低倉位", "監控回撤水平"]
            )

        return risk_assessment


# 全局實例
performance_evaluator = PerformanceEvaluator()


# 便利函數
def evaluate_strategy_performance(
    backtest_result: BacktestResult, benchmark_data: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """便利函數：評估策略性能"""
    evaluator = PerformanceEvaluator()
    return evaluator.generate_performance_report(
        backtest_result, benchmark_data = benchmark_data
    )


def detect_strategy_overfitting(
    optimization_results: List[BacktestResult],
    validation_data: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """便利函數：檢測策略過擬合"""
    evaluator = PerformanceEvaluator()
    overfitting_metrics = evaluator.detect_overfitting(
        optimization_results, validation_data
    )
    return overfitting_metrics.to_dict()
