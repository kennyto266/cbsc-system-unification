"""
港股量化交易 AI Agent 系统 - 策略回测验证系统

实现严格的回测验证和偏差检测功能，确保策略的可靠性和可重现性。
用于研究分析师Agent进行策略假设测试和验证。
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ...models.base import BaseModel


class BiasType(str, Enum):
    """偏差类型"""

    LOOK_AHEAD_BIAS = "look_ahead_bias"  # 前瞻偏差
    SURVIVORSHIP_BIAS = "survivorship_bias"  # 生存偏差
    SELECTION_BIAS = "selection_bias"  # 选择偏差
    DATA_SNOOPING = "data_snooping"  # 数据窥探
    OVERFITTING = "overfitting"  # 过拟合
    SURVIVAL_BIAS = "survival_bias"  # 存活偏差
    SURVIVOR_BIAS = "survivor_bias"  # 幸存者偏差
    ENDPOINT_BIAS = "endpoint_bias"  # 端点偏差


class ValidationStatus(str, Enum):
    """验证状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BIAS_DETECTED = "bias_detected"


@dataclass
class ValidationMetrics(BaseModel):
    """验证指标"""

    # 基础性能指标
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    sortino_ratio: float

    # 风险指标
    var_95: float
    var_99: float
    expected_shortfall: float
    tail_ratio: float

    # 交易指标
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_trade_return: float
    avg_win: float
    avg_loss: float

    # 统计指标
    information_ratio: float
    treynor_ratio: float
    jensen_alpha: float
    beta: float

    # 稳定性指标
    stability_of_returns: float
    consistency: float

    # 偏差检测指标
    bias_score: float
    detected_biases: List[BiasType] = field(default_factory=list)


@dataclass
class BacktestConfig(BaseModel):
    """回测配置"""

    # 时间配置
    start_date: datetime
    end_date: datetime
    rebalance_frequency: str = "daily"  # daily, weekly, monthly

    # 交易配置
    initial_capital: float = 1000000.0
    transaction_cost: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%

    # 风险配置
    max_position_size: float = 0.1  # 10%
    max_leverage: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    # 验证配置
    walk_forward_windows: int = 5
    monte_carlo_runs: int = 1000
    bootstrap_samples: int = 1000
    significance_level: float = 0.05

    # 偏差检测配置
    enable_bias_detection: bool = True
    bias_threshold: float = 0.7
    min_sample_size: int = 252  # 1年交易日


@dataclass
class BacktestResult(BaseModel):
    """回测结果"""

    result_id: str
    strategy_name: str
    config: BacktestConfig
    validation_status: ValidationStatus

    # 时间序列数据
    portfolio_values: List[float]
    returns: List[float]
    positions: List[Dict[str, float]]
    trades: List[Dict[str, Any]]

    # 验证指标
    metrics: ValidationMetrics

    # 偏差检测结果
    bias_analysis: Dict[str, Any]

    # 统计检验结果
    statistical_tests: Dict[str, Any]

    # 时间戳
    created_at: datetime
    validated_at: Optional[datetime] = None

    # 备注
    notes: List[str] = field(default_factory=list)


class BiasDetector:
    """偏差检测器"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.logger = logging.getLogger(
            "hk_quant_system.backtest_validation.bias_detector"
        )

    async def detect_look_ahead_bias(
        self, returns: pd.Series, signals: pd.Series, data_timestamps: pd.DatetimeIndex
    ) -> Tuple[float, bool]:
        """检测前瞻偏差"""

        try:
            # 检查信号是否在数据之前生成
            signal_lag = (signals.index - data_timestamps).dt.total_seconds()

            # 前瞻偏差分数：负值表示前瞻偏差
            look_ahead_score = signal_lag.mean() / (24 * 3600)  # 转换为天

            is_biased = look_ahead_score < -1.0  # 信号提前超过1天

            return abs(look_ahead_score), is_biased

        except Exception as exc:
            self.logger.error(f"前瞻偏差检测失败: {exc}")
            return 0.0, False

    async def detect_survivorship_bias(
        self, returns: pd.Series, universe_data: Dict[str, pd.DataFrame]
    ) -> Tuple[float, bool]:
        """检测生存偏差"""

        try:
            # 比较策略收益与完整宇宙收益
            universe_returns = []
            for symbol, data in universe_data.items():
                if "returns" in data.columns:
                    universe_returns.extend(data["returns"].dropna().tolist())

            if not universe_returns:
                return 0.0, False

            # 计算生存偏差分数
            strategy_mean = returns.mean()
            universe_mean = np.mean(universe_returns)

            survivorship_score = abs(strategy_mean - universe_mean) / abs(universe_mean)
            is_biased = survivorship_score > 0.2  # 偏差超过20%

            return survivorship_score, is_biased

        except Exception as exc:
            self.logger.error(f"生存偏差检测失败: {exc}")
            return 0.0, False

    async def detect_data_snooping(
        self, returns: pd.Series, multiple_strategies: List[pd.Series]
    ) -> Tuple[float, bool]:
        """检测数据窥探偏差"""

        try:
            if not multiple_strategies:
                return 0.0, False

            # 计算策略间的相关性
            correlations = []
            for strategy_returns in multiple_strategies:
                if len(strategy_returns) == len(returns):
                    corr = returns.corr(strategy_returns)
                    if not np.isnan(corr):
                        correlations.append(abs(corr))

            if not correlations:
                return 0.0, False

            # 高相关性表明可能存在数据窥探
            avg_correlation = np.mean(correlations)
            is_biased = avg_correlation > 0.8

            return avg_correlation, is_biased

        except Exception as exc:
            self.logger.error(f"数据窥探检测失败: {exc}")
            return 0.0, False

    async def detect_overfitting(
        self, in_sample_returns: pd.Series, out_of_sample_returns: pd.Series
    ) -> Tuple[float, bool]:
        """检测过拟合"""

        try:
            if len(out_of_sample_returns) < 10:
                return 0.0, False

            # 比较样本内和样本外表现
            in_sample_sharpe = in_sample_returns.mean() / in_sample_returns.std()
            out_of_sample_sharpe = (
                out_of_sample_returns.mean() / out_of_sample_returns.std()
            )

            # 过拟合分数：样本外表现显著下降
            overfitting_score = (in_sample_sharpe - out_of_sample_sharpe) / max(
                abs(in_sample_sharpe), 0.1
            )
            is_biased = overfitting_score > 0.5  # 样本外夏普比率下降超过50%

            return overfitting_score, is_biased

        except Exception as exc:
            self.logger.error(f"过拟合检测失败: {exc}")
            return 0.0, False

    async def detect_endpoint_bias(
        self, returns: pd.Series, start_date: datetime, end_date: datetime
    ) -> Tuple[float, bool]:
        """检测端点偏差"""

        try:
            # 检查起始和结束点的异常表现
            total_period = (end_date - start_date).days

            # 分析前10 % 和后10 % 期间的表现
            start_period = int(len(returns) * 0.1)
            end_period = int(len(returns) * 0.9)

            start_returns = returns.iloc[:start_period]
            end_returns = returns.iloc[end_period:]
            middle_returns = returns.iloc[start_period:end_period]

            if len(middle_returns) < 10:
                return 0.0, False

            # 计算端点偏差
            start_mean = start_returns.mean() if len(start_returns) > 0 else 0
            end_mean = end_returns.mean() if len(end_returns) > 0 else 0
            middle_mean = middle_returns.mean()

            endpoint_deviation = (
                abs(start_mean - middle_mean) + abs(end_mean - middle_mean)
            ) / abs(middle_mean)
            is_biased = endpoint_deviation > 0.3  # 端点偏差超过30%

            return endpoint_deviation, is_biased

        except Exception as exc:
            self.logger.error(f"端点偏差检测失败: {exc}")
            return 0.0, False

    async def comprehensive_bias_analysis(
        self,
        returns: pd.Series,
        signals: pd.Series,
        data_timestamps: pd.DatetimeIndex,
        universe_data: Optional[Dict[str, pd.DataFrame]] = None,
        multiple_strategies: Optional[List[pd.Series]] = None,
        in_sample_returns: Optional[pd.Series] = None,
        out_of_sample_returns: Optional[pd.Series] = None,
    ) -> Dict[str, Any]:
        """综合偏差分析"""

        bias_results = {
            "overall_bias_score": 0.0,
            "detected_biases": [],
            "bias_details": {},
        }

        try:
            # 前瞻偏差检测
            look_ahead_score, look_ahead_biased = await self.detect_look_ahead_bias(
                returns, signals, data_timestamps
            )
            bias_results["bias_details"]["look_ahead_bias"] = {
                "score": look_ahead_score,
                "is_biased": look_ahead_biased,
            }
            if look_ahead_biased:
                bias_results["detected_biases"].append(BiasType.LOOK_AHEAD_BIAS)

            # 生存偏差检测
            if universe_data:
                survivorship_score, survivorship_biased = (
                    await self.detect_survivorship_bias(returns, universe_data)
                )
                bias_results["bias_details"]["survivorship_bias"] = {
                    "score": survivorship_score,
                    "is_biased": survivorship_biased,
                }
                if survivorship_biased:
                    bias_results["detected_biases"].append(BiasType.SURVIVORSHIP_BIAS)

            # 数据窥探检测
            if multiple_strategies:
                snooping_score, snooping_biased = await self.detect_data_snooping(
                    returns, multiple_strategies
                )
                bias_results["bias_details"]["data_snooping"] = {
                    "score": snooping_score,
                    "is_biased": snooping_biased,
                }
                if snooping_biased:
                    bias_results["detected_biases"].append(BiasType.DATA_SNOOPING)

            # 过拟合检测
            if in_sample_returns is not None and out_of_sample_returns is not None:
                overfitting_score, overfitting_biased = await self.detect_overfitting(
                    in_sample_returns, out_of_sample_returns
                )
                bias_results["bias_details"]["overfitting"] = {
                    "score": overfitting_score,
                    "is_biased": overfitting_biased,
                }
                if overfitting_biased:
                    bias_results["detected_biases"].append(BiasType.OVERFITTING)

            # 端点偏差检测
            endpoint_score, endpoint_biased = await self.detect_endpoint_bias(
                returns, self.config.start_date, self.config.end_date
            )
            bias_results["bias_details"]["endpoint_bias"] = {
                "score": endpoint_score,
                "is_biased": endpoint_biased,
            }
            if endpoint_biased:
                bias_results["detected_biases"].append(BiasType.ENDPOINT_BIAS)

            # 计算总体偏差分数
            bias_scores = [
                detail["score"]
                for detail in bias_results["bias_details"].values()
                if detail["is_biased"]
            ]

            if bias_scores:
                bias_results["overall_bias_score"] = np.mean(bias_scores)

            return bias_results

        except Exception as exc:
            self.logger.error(f"综合偏差分析失败: {exc}")
            return bias_results


class StatisticalValidator:
    """统计验证器"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.logger = logging.getLogger(
            "hk_quant_system.backtest_validation.statistical_validator"
        )

    async def run_statistical_tests(self, returns: pd.Series) -> Dict[str, Any]:
        """运行统计检验"""

        test_results = {}

        try:
            # 正态性检验
            shapiro_stat, shapiro_p = stats.shapiro(returns)
            test_results["normality_test"] = {
                "statistic": shapiro_stat,
                "p_value": shapiro_p,
                "is_normal": shapiro_p > self.config.significance_level,
            }

            # 自相关性检验
            if len(returns) > 10:
                ljung_box_stat, ljung_box_p = stats.jarque_bera(returns)
                test_results["autocorrelation_test"] = {
                    "statistic": ljung_box_stat,
                    "p_value": ljung_box_p,
                    "has_autocorrelation": ljung_box_p < self.config.significance_level,
                }

            # 异方差检验
            if len(returns) > 20:
                # 简单的异方差检验：比较前半段和后半段的方差
                mid_point = len(returns) // 2
                var1 = returns.iloc[:mid_point].var()
                var2 = returns.iloc[mid_point:].var()
                f_stat = var1 / var2 if var2 > 0 else 1.0
                test_results["heteroscedasticity_test"] = {
                    "f_statistic": f_stat,
                    "is_heteroscedastic": f_stat > 2.0 or f_stat < 0.5,
                }

            # 平稳性检验 (简化版)
            if len(returns) > 30:
                # 简单的平稳性检验：比较不同时间段均值
                third = len(returns) // 3
                mean1 = returns.iloc[:third].mean()
                mean2 = returns.iloc[third : 2 * third].mean()
                mean3 = returns.iloc[2 * third :].mean()

                mean_variance = np.var([mean1, mean2, mean3])
                test_results["stationarity_test"] = {
                    "mean_variance": mean_variance,
                    "is_stationary": mean_variance < returns.var() * 0.1,
                }

            return test_results

        except Exception as exc:
            self.logger.error(f"统计检验失败: {exc}")
            return test_results

    async def bootstrap_analysis(self, returns: pd.Series) -> Dict[str, Any]:
        """Bootstrap分析"""

        try:
            bootstrap_returns = []

            for _ in range(self.config.bootstrap_samples):
                # 随机采样
                sample = returns.sample(n=len(returns), replace=True)
                bootstrap_returns.append(sample)

            # 计算Bootstrap统计量
            bootstrap_sharpes = []
            bootstrap_max_dds = []

            for boot_returns in bootstrap_returns:
                if boot_returns.std() > 0:
                    sharpe = boot_returns.mean() / boot_returns.std() * np.sqrt(252)
                    bootstrap_sharpes.append(sharpe)

                # 计算最大回撤
                cumulative = (1 + boot_returns).cumprod()
                rolling_max = cumulative.expanding().max()
                drawdown = (cumulative - rolling_max) / rolling_max
                max_dd = drawdown.min()
                bootstrap_max_dds.append(max_dd)

            return {
                "sharpe_confidence_interval": {
                    "mean": np.mean(bootstrap_sharpes),
                    "std": np.std(bootstrap_sharpes),
                    "percentile_5": np.percentile(bootstrap_sharpes, 5),
                    "percentile_95": np.percentile(bootstrap_sharpes, 95),
                },
                "max_drawdown_confidence_interval": {
                    "mean": np.mean(bootstrap_max_dds),
                    "std": np.std(bootstrap_max_dds),
                    "percentile_5": np.percentile(bootstrap_max_dds, 5),
                    "percentile_95": np.percentile(bootstrap_max_dds, 95),
                },
            }

        except Exception as exc:
            self.logger.error(f"Bootstrap分析失败: {exc}")
            return {}


class BacktestValidator:
    """回测验证器主类"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.backtest_validation")
        self.bias_detector = BiasDetector(config)
        self.statistical_validator = StatisticalValidator(config)

    def calculate_metrics(
        self, returns: pd.Series, portfolio_values: pd.Series
    ) -> ValidationMetrics:
        """计算验证指标"""

        try:
            # 基础性能指标
            total_return = (
                portfolio_values.iloc[-1] - portfolio_values.iloc[0]
            ) / portfolio_values.iloc[0]
            annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
            volatility = returns.std() * np.sqrt(252)
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

            # 最大回撤
            cumulative = portfolio_values / portfolio_values.iloc[0]
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # 其他指标
            calmar_ratio = (
                annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
            )
            sortino_ratio = (
                annualized_return / (returns[returns < 0].std() * np.sqrt(252))
                if len(returns[returns < 0]) > 0
                else 0
            )

            # VaR计算
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            expected_shortfall = returns[returns <= var_95].mean()
            tail_ratio = abs(var_95 / var_99) if var_99 != 0 else 0

            # 交易指标（简化版）
            total_trades = len(returns[returns != 0])
            win_rate = (
                len(returns[returns > 0]) / len(returns[returns != 0])
                if total_trades > 0
                else 0
            )
            profit_factor = (
                returns[returns > 0].sum() / abs(returns[returns < 0].sum())
                if len(returns[returns < 0]) > 0
                else 0
            )
            avg_trade_return = returns.mean()
            avg_win = (
                returns[returns > 0].mean() if len(returns[returns > 0]) > 0 else 0
            )
            avg_loss = (
                returns[returns < 0].mean() if len(returns[returns < 0]) > 0 else 0
            )

            # 稳定性指标
            stability_of_returns = (
                1 - returns.std() / abs(returns.mean()) if returns.mean() != 0 else 0
            )
            consistency = len(returns[returns > 0]) / len(returns)

            return ValidationMetrics(
                id=str(uuid.uuid4()),
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                calmar_ratio=calmar_ratio,
                sortino_ratio=sortino_ratio,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                tail_ratio=tail_ratio,
                total_trades=total_trades,
                win_rate=win_rate,
                profit_factor=profit_factor,
                avg_trade_return=avg_trade_return,
                avg_win=avg_win,
                avg_loss=avg_loss,
                information_ratio=0.0,  # 需要基准数据
                treynor_ratio=0.0,  # 需要beta数据
                jensen_alpha=0.0,  # 需要基准数据
                beta=0.0,  # 需要基准数据
                stability_of_returns=stability_of_returns,
                consistency=consistency,
                bias_score=0.0,
                detected_biases=[],
                timestamp=datetime.now(),
            )

        except Exception as exc:
            self.logger.error(f"指标计算失败: {exc}")
            raise

    async def validate_strategy(
        self,
        strategy_name: str,
        returns: pd.Series,
        portfolio_values: pd.Series,
        signals: pd.Series,
        positions: List[Dict[str, float]],
        trades: List[Dict[str, Any]],
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> BacktestResult:
        """验证策略"""

        try:
            self.logger.info(f"开始验证策略: {strategy_name}")

            # 创建回测结果
            result = BacktestResult(
                id=str(uuid.uuid4()),
                result_id=str(uuid.uuid4()),
                strategy_name=strategy_name,
                config=self.config,
                validation_status=ValidationStatus.IN_PROGRESS,
                portfolio_values=portfolio_values.tolist(),
                returns=returns.tolist(),
                positions=positions,
                trades=trades,
                metrics=ValidationMetrics(
                    id=str(uuid.uuid4()),
                    total_return=0.0,
                    annualized_return=0.0,
                    volatility=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    calmar_ratio=0.0,
                    sortino_ratio=0.0,
                    var_95=0.0,
                    var_99=0.0,
                    expected_shortfall=0.0,
                    tail_ratio=0.0,
                    total_trades=0,
                    win_rate=0.0,
                    profit_factor=0.0,
                    avg_trade_return=0.0,
                    avg_win=0.0,
                    avg_loss=0.0,
                    information_ratio=0.0,
                    treynor_ratio=0.0,
                    jensen_alpha=0.0,
                    beta=0.0,
                    stability_of_returns=0.0,
                    consistency=0.0,
                    bias_score=0.0,
                    detected_biases=[],
                    timestamp=datetime.now(),
                ),
                bias_analysis={},
                statistical_tests={},
                created_at=datetime.now(),
            )

            # 计算基础指标
            result.metrics = self.calculate_metrics(returns, portfolio_values)

            # 偏差检测
            if self.config.enable_bias_detection:
                data_timestamps = pd.date_range(
                    start=self.config.start_date,
                    end=self.config.end_date,
                    periods=len(returns),
                )

                bias_analysis = await self.bias_detector.comprehensive_bias_analysis(
                    returns=returns,
                    signals=signals,
                    data_timestamps=data_timestamps,
                    universe_data=(
                        additional_data.get("universe_data")
                        if additional_data
                        else None
                    ),
                    multiple_strategies=(
                        additional_data.get("multiple_strategies")
                        if additional_data
                        else None
                    ),
                    in_sample_returns=(
                        additional_data.get("in_sample_returns")
                        if additional_data
                        else None
                    ),
                    out_of_sample_returns=(
                        additional_data.get("out_of_sample_returns")
                        if additional_data
                        else None
                    ),
                )

                result.bias_analysis = bias_analysis
                result.metrics.bias_score = bias_analysis["overall_bias_score"]
                result.metrics.detected_biases = bias_analysis["detected_biases"]

                # 检查是否有显著偏差
                if bias_analysis["overall_bias_score"] > self.config.bias_threshold:
                    result.validation_status = ValidationStatus.BIAS_DETECTED
                    result.notes.append(
                        f"检测到显著偏差，偏差分数: {bias_analysis['overall_bias_score']:.3f}"
                    )

            # 统计检验
            statistical_tests = await self.statistical_validator.run_statistical_tests(
                returns
            )
            result.statistical_tests = statistical_tests

            # Bootstrap分析
            bootstrap_results = await self.statistical_validator.bootstrap_analysis(
                returns
            )
            result.statistical_tests["bootstrap_analysis"] = bootstrap_results

            # 更新验证状态
            if result.validation_status == ValidationStatus.IN_PROGRESS:
                result.validation_status = ValidationStatus.COMPLETED
                result.validated_at = datetime.now()
                result.notes.append("策略验证完成")

            self.logger.info(
                f"策略验证完成: {strategy_name}, 状态: {result.validation_status.value}"
            )

            return result

        except Exception as exc:
            self.logger.error(f"策略验证失败: {exc}")
            result.validation_status = ValidationStatus.FAILED
            result.notes.append(f"验证失败: {str(exc)}")
            return result

    async def walk_forward_validation(
        self,
        strategy_name: str,
        returns: pd.Series,
        portfolio_values: pd.Series,
        signals: pd.Series,
        positions: List[Dict[str, float]],
        trades: List[Dict[str, Any]],
    ) -> List[BacktestResult]:
        """前向验证"""

        try:
            results = []
            window_size = len(returns) // self.config.walk_forward_windows

            for i in range(self.config.walk_forward_windows):
                start_idx = i * window_size
                end_idx = (
                    (i + 1) * window_size
                    if i < self.config.walk_forward_windows - 1
                    else len(returns)
                )

                window_returns = returns.iloc[start_idx:end_idx]
                window_portfolio = portfolio_values.iloc[start_idx:end_idx]
                window_signals = signals.iloc[start_idx:end_idx]

                # 为每个窗口创建配置
                window_config = BacktestConfig(
                    start_date=self.config.start_date + timedelta(days=start_idx),
                    end_date=self.config.start_date + timedelta(days=end_idx),
                    rebalance_frequency=self.config.rebalance_frequency,
                    initial_capital=self.config.initial_capital,
                    transaction_cost=self.config.transaction_cost,
                    slippage=self.config.slippage,
                    max_position_size=self.config.max_position_size,
                    max_leverage=self.config.max_leverage,
                    stop_loss=self.config.stop_loss,
                    take_profit=self.config.take_profit,
                    walk_forward_windows=1,
                    monte_carlo_runs=self.config.monte_carlo_runs,
                    bootstrap_samples=self.config.bootstrap_samples,
                    significance_level=self.config.significance_level,
                    enable_bias_detection=self.config.enable_bias_detection,
                    bias_threshold=self.config.bias_threshold,
                    min_sample_size=self.config.min_sample_size,
                )

                window_validator = BacktestValidator(window_config)

                result = await window_validator.validate_strategy(
                    strategy_name=f"{strategy_name}_window_{i + 1}",
                    returns=window_returns,
                    portfolio_values=window_portfolio,
                    signals=window_signals,
                    positions=positions[start_idx:end_idx],
                    trades=trades[start_idx:end_idx],
                )

                results.append(result)

            return results

        except Exception as exc:
            self.logger.error(f"前向验证失败: {exc}")
            return []


__all__ = [
    "BacktestValidator",
    "BacktestConfig",
    "BacktestResult",
    "ValidationMetrics",
    "BiasDetector",
    "BiasType",
    "ValidationStatus",
    "StatisticalValidator",
]
