#!/usr/bin/env python3
"""
Advanced Risk Metrics Calculator
進階風險指標計算器

Professional risk analysis and metrics calculation
專業風險分析和指標計算
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import logging
from scipy import stats
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class RiskMetricsConfig:
    """風險指標配置"""
    # 計算參數
    confidence_levels: List[float] = None  # 置信水平
    lookback_periods: List[int] = None  # 回看期數

    # 風險測量
    var_method: str = "historical"  # historical, parametric, monte_carlo
    monte_carlo_simulations: int = 10000  # Monte Carlo模擬次數

    # 基準設定
    benchmark_return: float = 0.03  # 年化基準回報率 (3%)
    risk_free_rate: float = 0.03  # 年化無風險利率 (3%)

    # 時間設定
    trading_days_per_year: int = 252

    def __post_init__(self):
        if self.confidence_levels is None:
            self.confidence_levels = [0.90, 0.95, 0.99]
        if self.lookback_periods is None:
            self.lookback_periods = [20, 60, 252]  # 1月, 3月, 1年

@dataclass
class RiskMetrics:
    """風險指標結果"""
    # 基本統計
    mean_return: float
    volatility: float
    skewness: float
    kurtosis: float
    downside_volatility: float

    # VaR相關
    var_90: float
    var_95: float
    var_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float

    # 夏普比率變種
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    treynor_ratio: float

    # 回撤相關
    max_drawdown: float
    average_drawdown: float
    drawdown_duration: int
    recovery_time: int

    # 市場風險
    beta: float
    alpha: float
    tracking_error: float
    up_capture: float
    down_capture: float

    # 其他風險指標
    sterling_ratio: float
    burke_ratio: float
    pain_index: float
    ulcer_index: float
    martin_ratio: float

    # 尾部風險
    tail_ratio: float
    conditional_value_at_risk: float

    # 元數據
    calculation_date: str
    data_points: int
    time_period: str

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'basic_statistics': {
                'mean_return': round(self.mean_return * 100, 2),
                'volatility': round(self.volatility * 100, 2),
                'skewness': round(self.skewness, 3),
                'kurtosis': round(self.kurtosis, 3),
                'downside_volatility': round(self.downside_volatility * 100, 2)
            },
            'var_metrics': {
                'var_90': round(self.var_90 * 100, 2),
                'var_95': round(self.var_95 * 100, 2),
                'var_99': round(self.var_99 * 100, 2),
                'expected_shortfall_95': round(self.expected_shortfall_95 * 100, 2),
                'expected_shortfall_99': round(self.expected_shortfall_99 * 100, 2)
            },
            'sharpe_variants': {
                'sharpe_ratio': round(self.sharpe_ratio, 3),
                'sortino_ratio': round(self.sortino_ratio, 3),
                'calmar_ratio': round(self.calmar_ratio, 3),
                'information_ratio': round(self.information_ratio, 3),
                'treynor_ratio': round(self.treynor_ratio, 3)
            },
            'drawdown_metrics': {
                'max_drawdown': round(self.max_drawdown * 100, 2),
                'average_drawdown': round(self.average_drawdown * 100, 2),
                'drawdown_duration_days': self.drawdown_duration,
                'recovery_time_days': self.recovery_time
            },
            'market_risk': {
                'beta': round(self.beta, 3),
                'alpha': round(self.alpha * 100, 2),
                'tracking_error': round(self.tracking_error * 100, 2),
                'up_capture': round(self.up_capture * 100, 1),
                'down_capture': round(self.down_capture * 100, 1)
            },
            'other_metrics': {
                'sterling_ratio': round(self.sterling_ratio, 3),
                'burke_ratio': round(self.burke_ratio, 3),
                'pain_index': round(self.pain_index * 100, 2),
                'ulcer_index': round(self.ulcer_index * 100, 2),
                'martin_ratio': round(self.martin_ratio, 3)
            },
            'tail_risk': {
                'tail_ratio': round(self.tail_ratio, 3),
                'conditional_value_at_risk': round(self.conditional_value_at_risk * 100, 2)
            },
            'metadata': {
                'calculation_date': self.calculation_date,
                'data_points': self.data_points,
                'time_period': self.time_period
            }
        }

class AdvancedRiskMetrics:
    """
    進階風險指標計算器

    Features:
    - Value at Risk (VaR) 和 Expected Shortfall (ES)
    - 多種夏普比率變種
    - 回撤分析
    - 市場風險指標 (Beta, Alpha等)
    - 尾部風險測量
    - 痛苦指標和其他專業指標
    """

    def __init__(self, config: Optional[RiskMetricsConfig] = None):
        """初始化風險指標計算器"""
        self.config = config or RiskMetricsConfig()
        logger.info("Advanced Risk Metrics calculator initialized")

    def calculate_risk_metrics(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        portfolio_value: Optional[pd.Series] = None
    ) -> RiskMetrics:
        """
        計算全面風險指標

        Args:
            returns: 投資組合回報率序列
            benchmark_returns: 基準回報率序列 (可選)
            portfolio_value: 投資組合價值序列 (可選)

        Returns:
            RiskMetrics: 完整風險指標結果
        """
        try:
            logger.info(f"Calculating risk metrics for {len(returns)} data points")

            # 基本統計
            basic_stats = self._calculate_basic_statistics(returns)

            # VaR和ES
            var_metrics = self._calculate_var_es(returns)

            # 夏普比率變種
            sharpe_metrics = self._calculate_sharpe_variants(returns, benchmark_returns)

            # 回撤分析
            drawdown_metrics = self._calculate_drawdown_metrics(portfolio_value if portfolio_value is not None else returns)

            # 市場風險
            market_risk = self._calculate_market_risk(returns, benchmark_returns)

            # 其他專業指標
            other_metrics = self._calculate_other_metrics(returns, portfolio_value)

            # 尾部風險
            tail_risk = self._calculate_tail_risk(returns)

            # 創建結果
            risk_metrics = RiskMetrics(
                mean_return=basic_stats['mean'],
                volatility=basic_stats['volatility'],
                skewness=basic_stats['skewness'],
                kurtosis=basic_stats['kurtosis'],
                downside_volatility=basic_stats['downside_volatility'],
                var_90=var_metrics['var_90'],
                var_95=var_metrics['var_95'],
                var_99=var_metrics['var_99'],
                expected_shortfall_95=var_metrics['es_95'],
                expected_shortfall_99=var_metrics['es_99'],
                sharpe_ratio=sharpe_metrics['sharpe'],
                sortino_ratio=sharpe_metrics['sortino'],
                calmar_ratio=sharpe_metrics['calmar'],
                information_ratio=sharpe_metrics['information'],
                treynor_ratio=sharpe_metrics['treynor'],
                max_drawdown=drawdown_metrics['max_dd'],
                average_drawdown=drawdown_metrics['avg_dd'],
                drawdown_duration=drawdown_metrics['duration'],
                recovery_time=drawdown_metrics['recovery'],
                beta=market_risk['beta'],
                alpha=market_risk['alpha'],
                tracking_error=market_risk['tracking_error'],
                up_capture=market_risk['up_capture'],
                down_capture=market_risk['down_capture'],
                sterling_ratio=other_metrics['sterling'],
                burke_ratio=other_metrics['burke'],
                pain_index=other_metrics['pain_index'],
                ulcer_index=other_metrics['ulcer_index'],
                martin_ratio=other_metrics['martin'],
                tail_ratio=tail_risk['tail_ratio'],
                conditional_value_at_risk=tail_risk['cvar'],
                calculation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data_points=len(returns),
                time_period=f"{returns.index[0].strftime('%Y-%m-%d')} to {returns.index[-1].strftime('%Y-%m-%d')}"
            )

            logger.info("Risk metrics calculation completed")
            return risk_metrics

        except Exception as e:
            logger.error(f"Risk metrics calculation failed: {e}")
            raise

    def _calculate_basic_statistics(self, returns: pd.Series) -> Dict[str, float]:
        """計算基本統計指標"""
        mean_return = returns.mean() * self.config.trading_days_per_year
        volatility = returns.std() * np.sqrt(self.config.trading_days_per_year)
        skewness = stats.skew(returns.dropna())
        kurtosis = stats.kurtosis(returns.dropna())

        # 下行波動率
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_volatility = downside_returns.std() * np.sqrt(self.config.trading_days_per_year)
        else:
            downside_volatility = 0.0

        return {
            'mean': mean_return,
            'volatility': volatility,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'downside_volatility': downside_volatility
        }

    def _calculate_var_es(self, returns: pd.Series) -> Dict[str, float]:
        """計算VaR和Expected Shortfall"""
        returns_array = returns.dropna().values

        # Historical VaR
        var_90 = np.percentile(returns_array, 10)
        var_95 = np.percentile(returns_array, 5)
        var_99 = np.percentile(returns_array, 1)

        # Expected Shortfall (Conditional VaR)
        es_95 = returns_array[returns_array <= var_95].mean()
        es_99 = returns_array[returns_array <= var_99].mean()

        return {
            'var_90': var_90,
            'var_95': var_95,
            'var_99': var_99,
            'es_95': es_95,
            'es_99': es_99
        }

    def _calculate_sharpe_variants(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series]
    ) -> Dict[str, float]:
        """計算夏普比率變種"""
        excess_returns = returns - self.config.risk_free_rate / self.config.trading_days_per_year

        # 基本夏普比率
        if returns.std() > 0:
            sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(self.config.trading_days_per_year)
        else:
            sharpe_ratio = 0.0

        # Sortino比率
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = excess_returns.mean() / (downside_returns.std() * np.sqrt(self.config.trading_days_per_year))
        else:
            sortino_ratio = 0.0

        # Calmar比率 (需要最大回撤)
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        if max_drawdown != 0:
            calmar_ratio = excess_returns.mean() * self.config.trading_days_per_year / abs(max_drawdown)
        else:
            calmar_ratio = 0.0

        # Information Ratio
        if benchmark_returns is not None:
            active_returns = returns - benchmark_returns
            if active_returns.std() > 0:
                information_ratio = active_returns.mean() / active_returns.std() * np.sqrt(self.config.trading_days_per_year)
            else:
                information_ratio = 0.0
        else:
            information_ratio = 0.0

        # Treynor比率 (需要Beta)
        if benchmark_returns is not None:
            beta = self._calculate_beta(returns, benchmark_returns)
            if beta != 0:
                treynor_ratio = excess_returns.mean() * self.config.trading_days_per_year / beta
            else:
                treynor_ratio = 0.0
        else:
            treynor_ratio = 0.0

        return {
            'sharpe': sharpe_ratio,
            'sortino': sortino_ratio,
            'calmar': calmar_ratio,
            'information': information_ratio,
            'treynor': treynor_ratio
        }

    def _calculate_drawdown_metrics(self, values: pd.Series) -> Dict[str, Any]:
        """計算回撤指標"""
        if values is None or len(values) == 0:
            return {
                'max_dd': 0.0,
                'avg_dd': 0.0,
                'duration': 0,
                'recovery': 0
            }

        # 計算回撤
        name_str = str(values.name) if values.name is not None else ""
        if 'close' in name_str.lower() or 'price' in name_str.lower() or values.name is None:
            # 如果是價格序列，計算回撤
            running_max = values.expanding().max()
            drawdown = (values - running_max) / running_max
        else:
            # 如果是回報序列，先計算累積回報
            cumulative_returns = (1 + values).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max

        # 最大回撤
        max_dd = drawdown.min()

        # 平均回撤 (僅考慮負回撤)
        negative_drawdowns = drawdown[drawdown < 0]
        avg_dd = negative_drawdowns.mean() if len(negative_drawdowns) > 0 else 0.0

        # 最大回撤持續時間
        max_dd_idx = drawdown.idxmin()
        start_of_drawdown = drawdown[:max_dd_idx][drawdown == 0].last_valid_index()
        if start_of_drawdown is not None:
            duration = (max_dd_idx - start_of_drawdown).days
        else:
            duration = 0

        # 恢復時間 (簡化版本)
        recovery_time = duration  # 實際應用中需要更復雜的計算

        return {
            'max_dd': max_dd,
            'avg_dd': avg_dd,
            'duration': duration,
            'recovery': recovery_time
        }

    def _calculate_market_risk(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series]
    ) -> Dict[str, float]:
        """計算市場風險指標"""
        if benchmark_returns is None:
            return {
                'beta': 1.0,
                'alpha': 0.0,
                'tracking_error': 0.0,
                'up_capture': 0.0,
                'down_capture': 0.0
            }

        # 對齊數據
        aligned_data = pd.concat([returns, benchmark_returns], axis=1, join='inner')
        aligned_returns = aligned_data.iloc[:, 0]
        aligned_benchmark = aligned_data.iloc[:, 1]

        # Beta和Alpha
        beta = self._calculate_beta(aligned_returns, aligned_benchmark)
        alpha = (aligned_returns.mean() * self.config.trading_days_per_year -
                self.config.risk_free_rate -
                beta * (aligned_benchmark.mean() * self.config.trading_days_per_year - self.config.risk_free_rate))

        # Tracking Error
        active_returns = aligned_returns - aligned_benchmark
        tracking_error = active_returns.std() * np.sqrt(self.config.trading_days_per_year)

        # 上行/下行捕獲比率
        up_periods = aligned_benchmark > 0
        down_periods = aligned_benchmark < 0

        if up_periods.sum() > 0:
            up_capture = (aligned_returns[up_periods].mean() / aligned_benchmark[up_periods].mean() if aligned_benchmark[up_periods].mean() != 0 else 0)
        else:
            up_capture = 0.0

        if down_periods.sum() > 0:
            down_capture = (aligned_returns[down_periods].mean() / aligned_benchmark[down_periods].mean() if aligned_benchmark[down_periods].mean() != 0 else 0)
        else:
            down_capture = 0.0

        return {
            'beta': beta,
            'alpha': alpha,
            'tracking_error': tracking_error,
            'up_capture': up_capture,
            'down_capture': down_capture
        }

    def _calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """計算Beta"""
        # 對齊數據
        aligned_data = pd.concat([returns, benchmark_returns], axis=1, join='inner').dropna()

        if len(aligned_data) < 2:
            return 1.0

        x = aligned_data.iloc[:, 1]  # benchmark
        y = aligned_data.iloc[:, 0]  # portfolio

        if x.var() == 0:
            return 1.0

        beta = np.cov(x, y)[0, 1] / x.var()
        return beta

    def _calculate_other_metrics(
        self,
        returns: pd.Series,
        portfolio_value: Optional[pd.Series]
    ) -> Dict[str, float]:
        """計算其他專業指標"""
        # Sterling比率 (10%以年化回報率)
        excess_return = returns.mean() * self.config.trading_days_per_year - 0.10
        avg_drawdown = self._calculate_average_drawdown(portfolio_value if portfolio_value is not None else returns)

        if avg_drawdown != 0:
            sterling_ratio = excess_return / abs(avg_drawdown)
        else:
            sterling_ratio = 0.0

        # Burke比率
        sqrt_drawdown_sums = self._calculate_burke_ratio(portfolio_value if portfolio_value is not None else returns)
        if sqrt_drawdown_sums != 0:
            burke_ratio = excess_return / sqrt_drawdown_sums
        else:
            burke_ratio = 0.0

        # Pain Index
        pain_index = self._calculate_pain_index(portfolio_value if portfolio_value is not None else returns)

        # Ulcer Index
        ulcer_index = self._calculate_ulcer_index(portfolio_value if portfolio_value is not None else returns)

        # Martin比率
        if ulcer_index != 0:
            martin_ratio = excess_return / ulcer_index
        else:
            martin_ratio = 0.0

        return {
            'sterling': sterling_ratio,
            'burke': burke_ratio,
            'pain_index': pain_index,
            'ulcer_index': ulcer_index,
            'martin': martin_ratio
        }

    def _calculate_average_drawdown(self, values: pd.Series) -> float:
        """計算平均回撤"""
        name_str = str(values.name) if values.name is not None else ""
        if 'close' in name_str.lower() or 'price' in name_str.lower() or values.name is None:
            running_max = values.expanding().max()
            drawdown = (values - running_max) / running_max
        else:
            cumulative_returns = (1 + values).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max

        negative_drawdowns = drawdown[drawdown < 0]
        return negative_drawdowns.mean() if len(negative_drawdowns) > 0 else 0.0

    def _calculate_burke_ratio(self, values: pd.Series) -> float:
        """計算Burke比率中的平方根回撤和"""
        name_str = str(values.name) if values.name is not None else ""
        if 'close' in name_str.lower() or 'price' in name_str.lower() or values.name is None:
            running_max = values.expanding().max()
            drawdown = (values - running_max) / running_max
        else:
            cumulative_returns = (1 + values).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max

        negative_drawdowns = drawdown[drawdown < 0]
        if len(negative_drawdowns) > 0:
            return np.sqrt(np.sum(negative_drawdowns ** 2))
        else:
            return 0.0

    def _calculate_pain_index(self, values: pd.Series) -> float:
        """計算Pain Index"""
        name_str = str(values.name) if values.name is not None else ""
        if 'close' in name_str.lower() or 'price' in name_str.lower() or values.name is None:
            running_max = values.expanding().max()
            drawdown = (values - running_max) / running_max
        else:
            cumulative_returns = (1 + values).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max

        return drawdown[drawdown < 0].sum() / len(drawdown) if len(drawdown[drawdown < 0]) > 0 else 0.0

    def _calculate_ulcer_index(self, values: pd.Series) -> float:
        """計算Ulcer Index"""
        name_str = str(values.name) if values.name is not None else ""
        if 'close' in name_str.lower() or 'price' in name_str.lower() or values.name is None:
            running_max = values.expanding().max()
            drawdown = (values - running_max) / running_max
        else:
            cumulative_returns = (1 + values).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max

        squared_drawdowns = drawdown ** 2
        return np.sqrt(squared_drawdowns.mean())

    def _calculate_tail_risk(self, returns: pd.Series) -> Dict[str, float]:
        """計算尾部風險指標"""
        returns_array = returns.dropna().values

        # Tail Ratio (95th percentile vs 5th percentile)
        tail_95 = np.percentile(returns_array, 95)
        tail_5 = np.percentile(returns_array, 5)

        if tail_5 != 0:
            tail_ratio = abs(tail_95 / tail_5)
        else:
            tail_ratio = float('inf')

        # Conditional Value at Risk (CVaR)
        var_95 = np.percentile(returns_array, 5)
        cvar = returns_array[returns_array <= var_95].mean()

        return {
            'tail_ratio': tail_ratio,
            'cvar': cvar
        }

# 便利函數
def calculate_risk_metrics(
    returns: pd.Series,
    benchmark_returns: Optional[pd.Series] = None,
    portfolio_value: Optional[pd.Series] = None
) -> RiskMetrics:
    """便利函數：計算風險指標"""
    calculator = AdvancedRiskMetrics()
    return calculator.calculate_risk_metrics(returns, benchmark_returns, portfolio_value)

def calculate_portfolio_risk(
    portfolio_returns: pd.Series,
    market_returns: Optional[pd.Series] = None
) -> Dict[str, float]:
    """便利函數：計算投資組合風險"""
    risk_metrics = calculate_risk_metrics(portfolio_returns, market_returns)
    return risk_metrics.to_dict()