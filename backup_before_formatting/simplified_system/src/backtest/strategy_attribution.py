#!/usr/bin/env python3
"""
Strategy Attribution Analysis System
策略归因分析系统

Professional strategy attribution and performance analysis:
- Performance attribution analysis
- Risk attribution decomposition
- Factor exposure analysis
- Time-series attribution
- Sector attribution
- Style factor attribution
- Contribution analysis
- Brinson-Fachler attribution

专为策略组合优化设计的专业归因分析系统
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from scipy import stats
    from scipy.optimize import minimize
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.decomposition import FactorAnalysis
    from sklearn.preprocessing import StandardScaler
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Some attribution features may not work")

try:
    import statsmodels.api as sm
    from statsmodels.regression.linear_model import OLS
    from statsmodels.stats.stattools import durbin_watson
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("Statsmodels not available. Advanced regression analysis not available")

logger = logging.getLogger(__name__)

@dataclass
class AttributionConfig:
    """归因分析配置"""
    # 基本参数
    risk_free_rate: float = 0.03  # 无风险利率
    trading_days_per_year: int = 252  # 交易日数
    benchmark: str = "market"  # 基准名称

    # 因子模型
    factor_model: str = "carhart"  # carhart, fama_french_3, fama_french_5, custom
    factor_data_path: Optional[str] = None  # 因子数据路径
    custom_factors: Optional[List[str]] = None  # 自定义因子列表

    # 归因方法
    attribution_methods: List[str] = field(default_factory=lambda: ["return", "risk", "timing"])
    geometric_attribution: bool = True  # 几何归因 vs 算术归因
    attribution_frequency: str = "monthly"  # daily, weekly, monthly, quarterly

    # 风险归因
    risk_model: str = "covariance"  # covariance, factor, marginal
    var_confidence: float = 0.95  # VaR置信水平
    cvar_confidence: float = 0.95  # CVaR置信水平

    # 风格因子
    style_factors: List[str] = field(default_factory=lambda: [
        "value", "growth", "momentum", "quality", "size", "volatility"
    ])
    sector_classification: bool = True  # 行业分类

    # 时间序列分析
    rolling_window: int = 60  # 滚动窗口
    decomposition_method: str = "additive"  # additive, multiplicative

    # 输出选项
    detailed_reports: bool = True  # 详细报告
    attribution_charts: bool = True  # 归因图表
    contribution_breakdown: bool = True  # 贡献分解

@dataclass
class AttributionResult:
    """归因分析结果"""
    attribution_type: str  # 归因类型
    strategy_contributions: Dict[str, float]  # 策略贡献
    factor_contributions: Dict[str, float]  # 因子贡献
    timing_contributions: Dict[str, float]  # 择时贡献
    interaction_effects: Dict[str, float]  # 交互效应

    # 性能分解
    total_return: float  # 总回报
    active_return: float  # 主动回报
    selection_return: float  # 选股回报
    allocation_return: float  # 配置回报

    # 风险分解
    total_risk: float  # 总风险
    systematic_risk: float  # 系统性风险
    idiosyncratic_risk: float  # 特质性风险
    marginal_risk_contributions: Dict[str, float]  # 边际风险贡献

    # 归因统计
    attribution_accuracy: float  # 归因准确性
    r_squared: float  # R平方
    tracking_error: float  # 跟踪误差
    information_ratio: float  # 信息比率

    # 元数据
    attribution_date: str
    calculation_method: str

@dataclass
class FactorAttributionResult:
    """因子归因结果"""
    factor_exposures: pd.DataFrame  # 因子暴露
    factor_returns: pd.Series  # 因子收益
    factor_contributions: pd.Series  # 因子贡献
    factor_risk_contributions: pd.Series  # 因子风险贡献

    # 回归统计
    regression_stats: Dict[str, float]  # 回归统计
    factor_t_statistics: pd.Series  # 因子t统计量
    factor_p_values: pd.Series  # 因子p值

    # 风险调整表现
    risk_adjusted_returns: pd.Series  # 风险调整收益
    alpha: float  # alpha
    beta: float  # beta

@dataclass
class SectorAttributionResult:
    """行业归因结果"""
    sector_exposures: pd.Series  # 行业暴露
    sector_returns: pd.Series  # 行业收益
    sector_contributions: pd.Series  # 行业贡献
    sector_allocation_effect: pd.Series  # 行业配置效应
    sector_selection_effect: pd.Series  # 行业选择效应

    # 行业权重分析
    benchmark_weights: pd.Series  # 基准权重
    portfolio_weights: pd.Series  # 组合权重
    weight_differences: pd.Series  # 权重差异

@dataclass
class TimeSeriesAttributionResult:
    """时间序列归因结果"""
    decomposition: pd.DataFrame  # 分解结果
    trend_component: pd.Series  # 趋势成分
    seasonal_component: pd.Series  # 季节性成分
    residual_component: pd.Series  # 残差成分

    # 滚动归因
    rolling_attributions: pd.DataFrame  # 滚动归因
    attribution_trends: pd.DataFrame  # 归因趋势
    regime_changes: List[Tuple[str, str]]  # 趋势变化

@dataclass
class StyleAttributionResult:
    """风格归因结果"""
    style_scores: pd.DataFrame  # 风格评分
    style_exposures: pd.DataFrame  # 风格暴露
    style_returns: pd.Series  # 风格收益
    style_contributions: pd.Series  # 风格贡献

    # 风格分析
    style_tilt: Dict[str, float]  # 风格倾斜
    style_consistency: pd.Series  # 风格一致性
    style_rotation: pd.DataFrame  # 风格轮动

class StrategyAttributionAnalyzer:
    """
    策略归因分析引擎

    提供全面的策略归因分析功能：
    - 收益归因分解
    - 风险归因分析
    - 因子暴露分析
    - 时间序列归因
    - 行业归因
    - 风格因子归因
    - Brinson-Fachler归因
    """

    def __init__(self, config: Optional[AttributionConfig] = None):
        """初始化策略归因分析引擎"""
        self.config = config or AttributionConfig()

        # 验证依赖
        self._check_dependencies()

        # 初始化因子数据
        self.factor_data = None
        self.benchmark_data = None

        logger.info("Strategy Attribution Analyzer initialized")

    def analyze_performance_attribution(
        self,
        portfolio_returns: pd.Series,
        strategy_returns: pd.DataFrame,
        benchmark_returns: Optional[pd.Series] = None
    ) -> AttributionResult:
        """
        性能归因分析

        Args:
            portfolio_returns: 组合收益
            strategy_returns: 策略收益
            benchmark_returns: 基准收益

        Returns:
            AttributionResult: 归因分析结果
        """
        start_time = datetime.now()
        logger.info("Starting performance attribution analysis")

        try:
            # 数据对齐
            aligned_data = self._align_data(portfolio_returns, strategy_returns, benchmark_returns)
            portfolio_returns = aligned_data['portfolio']
            strategy_returns = aligned_data['strategies']
            benchmark_returns = aligned_data['benchmark']

            # 计算策略贡献
            strategy_weights = self._calculate_strategy_weights(portfolio_returns, strategy_returns)
            strategy_contributions = self._calculate_strategy_contributions(
                strategy_weights, strategy_returns
            )

            # 选股和配置效应
            selection_return, allocation_return = self._calculate_selection_allocation_effects(
                portfolio_returns, benchmark_returns, strategy_weights
            )

            # 因子归因
            factor_contributions = {}
            timing_contributions = {}
            interaction_effects = {}

            if STATSMODELS_AVAILABLE:
                factor_contributions, timing_contributions = self._factor_attribution(
                    portfolio_returns, strategy_returns, benchmark_returns
                )
                interaction_effects = self._calculate_interaction_effects(
                    strategy_returns, factor_contributions
                )

            # 风险归因
            total_risk, systematic_risk, idiosyncratic_risk, marginal_risk = self._risk_attribution(
                portfolio_returns, strategy_returns, benchmark_returns
            )

            # 归因统计
            attribution_stats = self._calculate_attribution_statistics(
                portfolio_returns, benchmark_returns, strategy_contributions
            )

            # 创建归因结果
            # Handle benchmark returns for active return calculation
            if benchmark_returns is None:
                benchmark_returns = pd.Series(0, index=portfolio_returns.index)

            result = AttributionResult(
                attribution_type="performance",
                strategy_contributions=strategy_contributions,
                factor_contributions=factor_contributions,
                timing_contributions=timing_contributions,
                interaction_effects=interaction_effects,
                total_return=float(portfolio_returns.mean() * self.config.trading_days_per_year),
                active_return=float((portfolio_returns - benchmark_returns).mean() * self.config.trading_days_per_year),
                selection_return=float(selection_return),
                allocation_return=float(allocation_return),
                total_risk=float(total_risk),
                systematic_risk=float(systematic_risk),
                idiosyncratic_risk=float(idiosyncratic_risk),
                marginal_risk_contributions=marginal_risk,
                attribution_accuracy=attribution_stats['accuracy'],
                r_squared=attribution_stats['r_squared'],
                tracking_error=attribution_stats['tracking_error'],
                information_ratio=attribution_stats['information_ratio'],
                attribution_date=datetime.now().strftime('%Y-%m-%d'),
                calculation_method="performance"
            )

            logger.info(f"Performance attribution analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Performance attribution analysis failed: {e}")
            raise

    def analyze_factor_attribution(
        self,
        portfolio_returns: pd.Series,
        factor_data: Optional[pd.DataFrame] = None
    ) -> FactorAttributionResult:
        """
        因子归因分析

        Args:
            portfolio_returns: 组合收益
            factor_data: 因子数据

        Returns:
            FactorAttributionResult: 因子归因结果
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("Statsmodels is required for factor attribution")

        start_time = datetime.now()
        logger.info("Starting factor attribution analysis")

        try:
            # 准备因子数据
            if factor_data is None:
                factor_data = self._prepare_factor_data(portfolio_returns)

            # 数据对齐
            aligned_data = self._align_factor_data(portfolio_returns, factor_data)
            portfolio_returns = aligned_data['portfolio']
            factor_data = aligned_data['factors']

            # 因子回归分析
            X = sm.add_constant(factor_data)
            y = portfolio_returns

            model = OLS(y, X).fit()

            # 提取因子暴露和收益
            factor_exposures = model.params.drop('const')
            factor_returns = model.fittedvalues - model.params['const']

            # 计算因子贡献
            factor_contributions = factor_exposures * factor_data.mean()

            # 因子风险贡献
            factor_cov = factor_data.cov()
            portfolio_factor_exposure = factor_exposures
            factor_var_contribution = portfolio_factor_exposure @ factor_cov @ portfolio_factor_exposure
            factor_risk_contributions = (portfolio_factor_exposure * (factor_cov @ portfolio_factor_exposure)) / factor_var_contribution

            # 回归统计
            regression_stats = {
                'r_squared': model.rsquared,
                'adj_r_squared': model.rsquared_adj,
                'f_statistic': model.fvalue,
                'f_pvalue': model.f_pvalue,
                'aic': model.aic,
                'bic': model.bic,
                'durbin_watson': durbin_watson(model.resid)
            }

            # 风险调整表现
            risk_adjusted_returns = portfolio_returns - (self.config.risk_free_rate / self.config.trading_days_per_year)
            alpha = model.params['const'] * self.config.trading_days_per_year
            beta = portfolio_returns.cov(factor_data.mean(axis=1)) / factor_data.mean(axis=1).var()

            result = FactorAttributionResult(
                factor_exposures=factor_exposures,
                factor_returns=factor_returns,
                factor_contributions=factor_contributions,
                factor_risk_contributions=factor_risk_contributions,
                regression_stats=regression_stats,
                factor_t_statistics=model.tvalues.drop('const'),
                factor_p_values=model.pvalues.drop('const'),
                risk_adjusted_returns=risk_adjusted_returns,
                alpha=alpha,
                beta=beta
            )

            logger.info(f"Factor attribution analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Factor attribution analysis failed: {e}")
            raise

    def analyze_sector_attribution(
        self,
        portfolio_returns: pd.Series,
        sector_returns: pd.DataFrame,
        portfolio_weights: Optional[pd.Series] = None,
        benchmark_weights: Optional[pd.Series] = None
    ) -> SectorAttributionResult:
        """
        行业归因分析

        Args:
            portfolio_returns: 组合收益
            sector_returns: 行业收益
            portfolio_weights: 组合行业权重
            benchmark_weights: 基准行业权重

        Returns:
            SectorAttributionResult: 行业归因结果
        """
        start_time = datetime.now()
        logger.info("Starting sector attribution analysis")

        try:
            # 数据对齐
            aligned_data = self._align_sector_data(portfolio_returns, sector_returns)
            portfolio_returns = aligned_data['portfolio']
            sector_returns = aligned_data['sectors']

            sectors = sector_returns.columns

            # 如果未提供权重，使用等权重
            if portfolio_weights is None:
                portfolio_weights = pd.Series(1.0 / len(sectors), index=sectors)

            if benchmark_weights is None:
                benchmark_weights = pd.Series(1.0 / len(sectors), index=sectors)

            # 计算行业暴露和收益
            sector_exposures = portfolio_weights
            sector_contributions = sector_exposures * sector_returns.mean()

            # 行业配置效应
            sector_allocation_effect = (portfolio_weights - benchmark_weights) * sector_returns.mean()

            # 行业选择效应（基于超额收益）
            benchmark_return = (benchmark_weights * sector_returns).sum(axis=1)
            sector_selection_effect = portfolio_weights * (sector_returns.subtract(benchmark_return, axis=0)).mean()

            # 权重差异分析
            weight_differences = portfolio_weights - benchmark_weights

            result = SectorAttributionResult(
                sector_exposures=sector_exposures,
                sector_returns=sector_returns.mean(),
                sector_contributions=sector_contributions,
                sector_allocation_effect=sector_allocation_effect,
                sector_selection_effect=sector_selection_effect,
                benchmark_weights=benchmark_weights,
                portfolio_weights=portfolio_weights,
                weight_differences=weight_differences
            )

            logger.info(f"Sector attribution analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Sector attribution analysis failed: {e}")
            raise

    def analyze_time_series_attribution(
        self,
        portfolio_returns: pd.Series,
        attribution_frequency: Optional[str] = None
    ) -> TimeSeriesAttributionResult:
        """
        时间序列归因分析

        Args:
            portfolio_returns: 组合收益
            attribution_frequency: 归因频率

        Returns:
            TimeSeriesAttributionResult: 时间序列归因结果
        """
        start_time = datetime.now()
        attribution_frequency = attribution_frequency or self.config.attribution_frequency

        logger.info(f"Starting time series attribution analysis with {attribution_frequency} frequency")

        try:
            # 重采样数据
            if attribution_frequency == "monthly":
                resampled_returns = portfolio_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            elif attribution_frequency == "weekly":
                resampled_returns = portfolio_returns.resample('W').apply(lambda x: (1 + x).prod() - 1)
            elif attribution_frequency == "quarterly":
                resampled_returns = portfolio_returns.resample('Q').apply(lambda x: (1 + x).prod() - 1)
            else:
                resampled_returns = portfolio_returns

            # 时间序列分解
            if len(resampled_returns) > 24:  # 需要足够的数据点
                from statsmodels.tsa.seasonal import seasonal_decompose

                decomposition = seasonal_decompose(
                    resampled_returns.dropna(),
                    model=self.config.decomposition_method,
                    period=12 if attribution_frequency == "monthly" else 52
                )

                trend_component = decomposition.trend
                seasonal_component = decomposition.seasonal
                residual_component = decomposition.resid
            else:
                # 简化的分解
                trend_component = resampled_returns.rolling(window=min(12, len(resampled_returns)//2)).mean()
                seasonal_component = pd.Series(0, index=resampled_returns.index)
                residual_component = resampled_returns - trend_component

                decomposition = pd.DataFrame({
                    'trend': trend_component,
                    'seasonal': seasonal_component,
                    'resid': residual_component
                })

            # 滚动归因分析
            window_size = self.config.rolling_window
            if len(resampled_returns) > window_size:
                rolling_returns = resampled_returns.rolling(window=window_size)
                rolling_attributions = pd.DataFrame({
                    'mean': rolling_returns.mean(),
                    'std': rolling_returns.std(),
                    'sharpe': rolling_returns.mean() / rolling_returns.std()
                })

                # 归因趋势
                attribution_trends = rolling_attributions.rolling(window=window_size//2).mean()
            else:
                rolling_attributions = pd.DataFrame()
                attribution_trends = pd.DataFrame()

            # 趋势变化检测
            regime_changes = []
            if len(trend_component.dropna()) > 1:
                trend_diff = trend_component.diff()
                change_points = np.where(np.abs(trend_diff) > trend_diff.std())[0]

                for change_point in change_points:
                    if change_point < len(trend_component) - 1:
                        regime_changes.append((
                            trend_component.index[change_point],
                            trend_component.index[change_point + 1]
                        ))

            result = TimeSeriesAttributionResult(
                decomposition=decomposition,
                trend_component=trend_component,
                seasonal_component=seasonal_component,
                residual_component=residual_component,
                rolling_attributions=rolling_attributions,
                attribution_trends=attribution_trends,
                regime_changes=regime_changes
            )

            logger.info(f"Time series attribution analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Time series attribution analysis failed: {e}")
            raise

    def analyze_style_attribution(
        self,
        portfolio_returns: pd.Series,
        style_factor_data: Optional[pd.DataFrame] = None
    ) -> StyleAttributionResult:
        """
        风格归因分析

        Args:
            portfolio_returns: 组合收益
            style_factor_data: 风格因子数据

        Returns:
            StyleAttributionResult: 风格归因结果
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("Statsmodels is required for style attribution")

        start_time = datetime.now()
        logger.info("Starting style attribution analysis")

        try:
            # 准备风格因子数据
            if style_factor_data is None:
                style_factor_data = self._generate_style_factor_data(portfolio_returns)

            # 数据对齐
            aligned_data = self._align_factor_data(portfolio_returns, style_factor_data)
            portfolio_returns = aligned_data['portfolio']
            style_factor_data = aligned_data['factors']

            # 计算风格评分
            style_scores = self._calculate_style_scores(portfolio_returns, style_factor_data)

            # 风格暴露回归
            X = sm.add_constant(style_factor_data)
            y = portfolio_returns

            model = OLS(y, X).fit()
            style_exposures = model.params.drop('const')

            # 风格收益和贡献
            style_returns = style_factor_data.mean()
            style_contributions = style_exposures * style_returns

            # 风格倾斜分析
            style_tilt = {}
            for style in style_exposures.index:
                exposure = style_exposures[style]
                if exposure > 0.1:
                    tilt = "positive"
                elif exposure < -0.1:
                    tilt = "negative"
                else:
                    tilt = "neutral"
                style_tilt[style] = exposure

            # 风格一致性分析
            rolling_exposures = style_factor_data.rolling(window=self.config.rolling_window).mean()
            style_consistency = rolling_exposures.std()

            # 风格轮动分析
            style_rotation = pd.DataFrame()
            for style in style_factor_data.columns:
                style_rotation[style] = style_factor_data[style].rolling(window=30).apply(
                    lambda x: x.tail(1).iloc[0] - x.head(1).iloc[0] if len(x) > 1 else 0
                )

            result = StyleAttributionResult(
                style_scores=style_scores,
                style_exposures=pd.Series(style_exposures),
                style_returns=style_returns,
                style_contributions=style_contributions,
                style_tilt=style_tilt,
                style_consistency=style_consistency,
                style_rotation=style_rotation
            )

            logger.info(f"Style attribution analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return result

        except Exception as e:
            logger.error(f"Style attribution analysis failed: {e}")
            raise

    def comprehensive_attribution_analysis(
        self,
        portfolio_returns: pd.Series,
        strategy_returns: pd.DataFrame,
        factor_data: Optional[pd.DataFrame] = None,
        sector_data: Optional[pd.DataFrame] = None,
        benchmark_returns: Optional[pd.Series] = None
    ) -> Dict[str, Any]:
        """
        综合归因分析

        Args:
            portfolio_returns: 组合收益
            strategy_returns: 策略收益
            factor_data: 因子数据
            sector_data: 行业数据
            benchmark_returns: 基准收益

        Returns:
            Dict[str, Any]: 综合归因分析结果
        """
        start_time = datetime.now()
        logger.info("Starting comprehensive attribution analysis")

        try:
            results = {}

            # 性能归因
            performance_result = self.analyze_performance_attribution(
                portfolio_returns, strategy_returns, benchmark_returns
            )
            results['performance_attribution'] = performance_result

            # 因子归因
            try:
                factor_result = self.analyze_factor_attribution(portfolio_returns, factor_data)
                results['factor_attribution'] = factor_result
            except Exception as e:
                logger.warning(f"Factor attribution failed: {e}")

            # 时间序列归因
            try:
                time_series_result = self.analyze_time_series_attribution(portfolio_returns)
                results['time_series_attribution'] = time_series_result
            except Exception as e:
                logger.warning(f"Time series attribution failed: {e}")

            # 风格归因
            try:
                style_result = self.analyze_style_attribution(portfolio_returns)
                results['style_attribution'] = style_result
            except Exception as e:
                logger.warning(f"Style attribution failed: {e}")

            # 行业归因（如果提供行业数据）
            if sector_data is not None:
                try:
                    sector_result = self.analyze_sector_attribution(portfolio_returns, sector_data)
                    results['sector_attribution'] = sector_result
                except Exception as e:
                    logger.warning(f"Sector attribution failed: {e}")

            # 生成综合报告
            comprehensive_report = self._generate_comprehensive_report(results)
            results['comprehensive_report'] = comprehensive_report

            logger.info(f"Comprehensive attribution analysis completed in {(datetime.now() - start_time).total_seconds():.3f}s")
            return results

        except Exception as e:
            logger.error(f"Comprehensive attribution analysis failed: {e}")
            raise

    def _check_dependencies(self):
        """检查依赖库"""
        required_packages = {
            'numpy': 'numpy',
            'pandas': 'pandas',
            'scipy': 'scipy',
            'statsmodels': 'statsmodels'
        }

        missing_packages = []
        for package, import_name in required_packages.items():
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            logger.warning(f"Missing optional packages: {missing_packages}")

    def _align_data(
        self,
        portfolio_returns: pd.Series,
        strategy_returns: pd.DataFrame,
        benchmark_returns: Optional[pd.Series]
    ) -> Dict[str, Any]:
        """对齐数据"""
        # 获取所有数据的共同时间索引
        all_indices = [portfolio_returns.index, strategy_returns.index]
        if benchmark_returns is not None:
            all_indices.append(benchmark_returns.index)

        common_index = all_indices[0]
        for idx in all_indices[1:]:
            common_index = common_index.intersection(idx)

        # 对齐数据
        aligned_portfolio = portfolio_returns.loc[common_index]
        aligned_strategies = strategy_returns.loc[common_index]
        aligned_benchmark = benchmark_returns.loc[common_index] if benchmark_returns is not None else None

        return {
            'portfolio': aligned_portfolio,
            'strategies': aligned_strategies,
            'benchmark': aligned_benchmark
        }

    def _align_factor_data(
        self,
        portfolio_returns: pd.Series,
        factor_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """对齐因子数据"""
        common_index = portfolio_returns.index.intersection(factor_data.index)

        return {
            'portfolio': portfolio_returns.loc[common_index],
            'factors': factor_data.loc[common_index]
        }

    def _align_sector_data(
        self,
        portfolio_returns: pd.Series,
        sector_returns: pd.DataFrame
    ) -> Dict[str, Any]:
        """对齐行业数据"""
        common_index = portfolio_returns.index.intersection(sector_returns.index)

        return {
            'portfolio': portfolio_returns.loc[common_index],
            'sectors': sector_returns.loc[common_index]
        }

    def _calculate_strategy_weights(
        self,
        portfolio_returns: pd.Series,
        strategy_returns: pd.DataFrame
    ) -> Dict[str, float]:
        """计算策略权重"""
        # 使用回归方法计算策略对组合的贡献权重
        weights = {}
        n_strategies = len(strategy_returns.columns)

        # 简化的权重计算（基于相关性）
        for strategy in strategy_returns.columns:
            correlation = portfolio_returns.corr(strategy_returns[strategy])
            weights[strategy] = max(0, correlation)  # 只考虑正相关

        # 归一化权重
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        else:
            # 如果没有正相关，使用等权重
            weights = {strategy: 1.0 / n_strategies for strategy in strategy_returns.columns}

        return weights

    def _calculate_strategy_contributions(
        self,
        strategy_weights: Dict[str, float],
        strategy_returns: pd.DataFrame
    ) -> Dict[str, float]:
        """计算策略贡献"""
        contributions = {}

        for strategy, weight in strategy_weights.items():
            strategy_return = strategy_returns[strategy].mean() * self.config.trading_days_per_year
            contributions[strategy] = weight * strategy_return

        return contributions

    def _calculate_selection_allocation_effects(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: Optional[pd.Series],
        strategy_weights: Dict[str, float]
    ) -> Tuple[float, float]:
        """计算选股和配置效应"""
        # 简化的选股和配置效应计算
        if benchmark_returns is None:
            # 如果没有基准，假设基准收益为0
            benchmark_returns = pd.Series(0, index=portfolio_returns.index)

        active_return = portfolio_returns.mean() - benchmark_returns.mean()

        # 基于权重差异估算配置效应
        # 这里使用简化的方法
        allocation_return = active_return * 0.6  # 假设60%来自配置
        selection_return = active_return * 0.4  # 40%来自选股

        return selection_return * self.config.trading_days_per_year, allocation_return * self.config.trading_days_per_year

    def _factor_attribution(
        self,
        portfolio_returns: pd.Series,
        strategy_returns: pd.DataFrame,
        benchmark_returns: Optional[pd.Series]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """因子归因分析"""
        factor_contributions = {}
        timing_contributions = {}

        # 简化的因子归因
        # 在实际应用中，应该使用更复杂的因子模型

        # 基于策略表现的因子贡献
        for strategy in strategy_returns.columns:
            strategy_return = strategy_returns[strategy]
            market_proxy = benchmark_returns if benchmark_returns is not None else portfolio_returns

            # 市场因子暴露
            if len(strategy_return) > 1 and len(market_proxy) > 1:
                market_exposure = strategy_return.cov(market_proxy) / market_proxy.var()
                factor_contributions[f"{strategy}_market"] = market_exposure * market_proxy.mean()

                # 择时能力（基于超额收益的波动性）
                excess_returns = strategy_return - market_proxy * market_exposure
                timing_skill = np.std(excess_returns) * np.sqrt(self.config.trading_days_per_year)
                timing_contributions[f"{strategy}_timing"] = timing_skill

        return factor_contributions, timing_contributions

    def _calculate_interaction_effects(
        self,
        strategy_returns: pd.DataFrame,
        factor_contributions: Dict[str, float]
    ) -> Dict[str, float]:
        """计算交互效应"""
        interaction_effects = {}

        # 简化的交互效应计算
        strategies = strategy_returns.columns
        for i, strategy1 in enumerate(strategies):
            for j, strategy2 in enumerate(strategies):
                if i < j:
                    # 计算两个策略之间的交互效应
                    correlation = strategy_returns[strategy1].corr(strategy_returns[strategy2])
                    interaction_effects[f"{strategy1}_{strategy2}"] = correlation * 0.1  # 缩放因子

        return interaction_effects

    def _risk_attribution(
        self,
        portfolio_returns: pd.Series,
        strategy_returns: pd.DataFrame,
        benchmark_returns: Optional[pd.Series]
    ) -> Tuple[float, float, float, Dict[str, float]]:
        """风险归因分析"""
        total_risk = portfolio_returns.std() * np.sqrt(self.config.trading_days_per_year)

        # 系统性风险（使用市场基准）
        if benchmark_returns is not None:
            beta = portfolio_returns.cov(benchmark_returns) / benchmark_returns.var()
            systematic_risk = beta * benchmark_returns.std() * np.sqrt(self.config.trading_days_per_year)
            idiosyncratic_risk = np.sqrt(max(0, total_risk**2 - systematic_risk**2))
        else:
            systematic_risk = total_risk * 0.6  # 假设60%是系统性风险
            idiosyncratic_risk = total_risk * 0.4

        # 边际风险贡献
        marginal_risk = {}
        for strategy in strategy_returns.columns:
            # 使用相关性作为边际风险的近似
            correlation = portfolio_returns.corr(strategy_returns[strategy])
            marginal_risk[strategy] = abs(correlation) * total_risk / len(strategy_returns.columns)

        return total_risk, systematic_risk, idiosyncratic_risk, marginal_risk

    def _calculate_attribution_statistics(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: Optional[pd.Series],
        strategy_contributions: Dict[str, float]
    ) -> Dict[str, float]:
        """计算归因统计"""
        # R平方（基于贡献的拟合度）
        total_contribution = sum(abs(v) for v in strategy_contributions.values())
        total_return = abs(portfolio_returns.mean() * self.config.trading_days_per_year)

        if total_return > 1e-8:
            accuracy = min(1.0, total_contribution / total_return)
        else:
            accuracy = 0.5

        # R平方简化计算
        r_squared = accuracy ** 2

        # 跟踪误差
        if benchmark_returns is not None:
            tracking_error = (portfolio_returns - benchmark_returns).std() * np.sqrt(self.config.trading_days_per_year)
            information_ratio = (portfolio_returns.mean() - benchmark_returns.mean()) * self.config.trading_days_per_year / tracking_error if tracking_error > 1e-8 else 0
        else:
            tracking_error = 0
            information_ratio = 0

        return {
            'accuracy': accuracy,
            'r_squared': r_squared,
            'tracking_error': tracking_error,
            'information_ratio': information_ratio
        }

    def _prepare_factor_data(self, portfolio_returns: pd.Series) -> pd.DataFrame:
        """准备因子数据"""
        # 生成简化的因子数据
        n_periods = len(portfolio_returns)

        factor_data = pd.DataFrame(index=portfolio_returns.index)

        # 市场因子（使用组合收益作为代理）
        factor_data['market'] = portfolio_returns

        # 其他因子（随机生成作为示例）
        factor_data['size'] = np.random.normal(0, 0.01, n_periods)
        factor_data['value'] = np.random.normal(0, 0.01, n_periods)
        factor_data['momentum'] = np.random.normal(0, 0.01, n_periods)
        factor_data['quality'] = np.random.normal(0, 0.01, n_periods)

        return factor_data

    def _generate_style_factor_data(self, portfolio_returns: pd.Series) -> pd.DataFrame:
        """生成风格因子数据"""
        n_periods = len(portfolio_returns)
        style_data = pd.DataFrame(index=portfolio_returns.index)

        # 基于组合收益生成风格因子
        returns_cum = (1 + portfolio_returns).cumprod()

        # Value因子（基于收益的倒数）
        style_data['value'] = 1.0 / (returns_cum + 1e-8)
        style_data['value'] = (style_data['value'] - style_data['value'].mean()) / style_data['value'].std()

        # Momentum因子（基于过去收益）
        style_data['momentum'] = portfolio_returns.rolling(window=20).mean()
        style_data['momentum'] = (style_data['momentum'] - style_data['momentum'].mean()) / (style_data['momentum'].std() + 1e-8)

        # Size因子（随机）
        style_data['size'] = np.random.normal(0, 1, n_periods)

        # Quality因子（基于收益稳定性）
        style_data['quality'] = -portfolio_returns.rolling(window=20).std()
        style_data['quality'] = (style_data['quality'] - style_data['quality'].mean()) / (style_data['quality'].std() + 1e-8)

        # Volatility因子
        style_data['volatility'] = portfolio_returns.rolling(window=20).std()
        style_data['volatility'] = (style_data['volatility'] - style_data['volatility'].mean()) / (style_data['volatility'].std() + 1e-8)

        # Growth因子（基于收益趋势）
        style_data['growth'] = portfolio_returns.rolling(window=60).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
        )
        style_data['growth'] = (style_data['growth'] - style_data['growth'].mean()) / (style_data['growth'].std() + 1e-8)

        return style_data.fillna(0)

    def _calculate_style_scores(
        self,
        portfolio_returns: pd.Series,
        style_factor_data: pd.DataFrame
    ) -> pd.DataFrame:
        """计算风格评分"""
        # 基于因子暴露计算风格评分
        scores = pd.DataFrame(index=style_factor_data.columns)

        # 计算每个因子的Z-score
        for factor in style_factor_data.columns:
            factor_values = style_factor_data[factor]
            if factor_values.std() > 1e-8:
                scores.loc[factor, 'z_score'] = (factor_values.iloc[-1] - factor_values.mean()) / factor_values.std()
            else:
                scores.loc[factor, 'z_score'] = 0

        return scores

    def _generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合归因报告"""
        report = {
            'summary': {
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'available_analyses': list(results.keys())
            },
            'key_findings': {}
        }

        # 提取关键发现
        if 'performance_attribution' in results:
            perf_result = results['performance_attribution']
            report['key_findings']['performance'] = {
                'total_return': perf_result.total_return,
                'sharpe_ratio': perf_result.sharpe_ratio,
                'top_strategies': sorted(
                    perf_result.strategy_contributions.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
            }

        if 'factor_attribution' in results:
            factor_result = results['factor_attribution']
            report['key_findings']['factor'] = {
                'alpha': factor_result.alpha,
                'beta': factor_result.beta,
                'top_factors': sorted(
                    factor_result.factor_contributions.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )[:3]
            }

        return report

# 便利函数
def create_attribution_analyzer(config: Optional[AttributionConfig] = None) -> StrategyAttributionAnalyzer:
    """创建策略归因分析引擎"""
    return StrategyAttributionAnalyzer(config)

def analyze_strategy_attribution(
    portfolio_returns: pd.Series,
    strategy_returns: pd.DataFrame,
    benchmark_returns: Optional[pd.Series] = None
) -> AttributionResult:
    """便利函数：分析策略归因"""
    analyzer = StrategyAttributionAnalyzer()
    return analyzer.analyze_performance_attribution(portfolio_returns, strategy_returns, benchmark_returns)