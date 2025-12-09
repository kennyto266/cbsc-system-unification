#!/usr / bin / env python3
"""
Independent Alpha Source System
真正独立Alpha源系统 - 解决多策略组合相关性过高问题

基于不同数据源和逻辑原理，构建真正独立的Alpha因子
"""

import json
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")


class AlphaSourceType(Enum):
    """Alpha源类型"""

    TECHNICAL_ANALYSIS = "technical_analysis"  # 技术分析
    MACRO_ECONOMIC = "macro_economic"  # 宏观经济
    MARKET_SENTIMENT = "market_sentiment"  # 市场情绪
    ALTERNATIVE_DATA = "alternative_data"  # 另类数据
    CROSS_ASSET = "cross_asset"  # 跨资产分析
    QUANTITATIVE_FACTOR = "quantitative_factor"  # 量化因子


class AlphaStrategyType(Enum):
    """Alpha策略类型"""

    REVERSION = "reversion"  # 均值回归
    MOMENTUM = "momentum"  # 动量
    CARRY = "carry"  # 展期
    QUALITY = "quality"  # 质量
    GROWTH = "growth"  # 成长
    VALUE = "value"  # 价值


@dataclass
class AlphaSignal:
    """Alpha信号"""

    signal_value: float
    signal_strength: float  # 信号强度 0 - 1
    confidence: float  # 置信度 0 - 1
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class AlphaMetrics:
    """Alpha指标"""

    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    information_ratio: float
    correlation_to_market: float
    correlation_to_others: Dict[str, float]


class AlphaSource(ABC):
    """Alpha源抽象基类"""

    def __init__(self, name: str, source_type: AlphaSourceType):
        self.name = name
        self.source_type = source_type
        self.last_update = None
        self.signal_history = []

    @abstractmethod
    def generate_signals(
        self, market_data: pd.DataFrame, additional_data: Dict = None
    ) -> List[AlphaSignal]:
        """生成Alpha信号"""

    @abstractmethod
    def calculate_correlation(self, other_signals: List[AlphaSignal]) -> float:
        """计算与其他信号的相关性"""


class TechnicalAnalysisAlpha(AlphaSource):
    """技术分析Alpha源"""

    def __init__(self, name: str, strategy_type: AlphaStrategyType):
        super().__init__(name, AlphaSourceType.TECHNICAL_ANALYSIS)
        self.strategy_type = strategy_type
        self.parameters = self._initialize_parameters()

    def _initialize_parameters(self) -> Dict:
        """初始化参数"""
        if self.strategy_type == AlphaStrategyType.REVERSION:
            return {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "bollinger_period": 20,
                "bollinger_std": 2.0,
            }
        elif self.strategy_type == AlphaStrategyType.MOMENTUM:
            return {"ma_short": 20, "ma_long": 60, "momentum_period": 252}
        else:
            return {}

    def generate_signals(
        self, market_data: pd.DataFrame, additional_data: Dict = None
    ) -> List[AlphaSignal]:
        """生成技术分析信号"""
        signals = []

        if len(market_data) < 60:
            return signals

        # 基于策略类型生成不同信号
        if self.strategy_type == AlphaStrategyType.REVERSION:
            signals = self._generate_reversion_signals(market_data)
        elif self.strategy_type == AlphaStrategyType.MOMENTUM:
            signals = self._generate_momentum_signals(market_data)

        self.signal_history.extend(signals)
        self.last_update = datetime.now()

        return signals

    def _generate_reversion_signals(self, data: pd.DataFrame) -> List[AlphaSignal]:
        """生成均值回归信号"""
        signals = []

        # RSI指标
        delta = data["close"].diff()
        gain = (
            (delta.where(delta > 0, 0))
            .rolling(window = self.parameters["rsi_period"])
            .mean()
        )
        loss = (
            (-delta.where(delta < 0, 0))
            .rolling(window = self.parameters["rsi_period"])
            .mean()
        )
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # 布林带
        sma = data["close"].rolling(window = self.parameters["bollinger_period"]).mean()
        std = data["close"].rolling(window = self.parameters["bollinger_period"]).std()
        upper_band = sma + (std * self.parameters["bollinger_std"])
        lower_band = sma - (std * self.parameters["bollinger_std"])

        # 生成信号
        for i in range(len(data)):
            if i < self.parameters["rsi_period"]:
                continue

            current_rsi = rsi.iloc[i]
            current_price = data["close"].iloc[i]
            current_lower = lower_band.iloc[i]
            current_upper = upper_band.iloc[i]

            # RSI超卖 + 价格接近布林带下轨 = 买入信号
            if (
                current_rsi < self.parameters["rsi_oversold"]
                and current_price <= current_lower * 1.02
            ):

                signal_strength = min(
                    1.0, (self.parameters["rsi_oversold"] - current_rsi) / 20
                )
                confidence = 0.7

                signals.append(
                    AlphaSignal(
                        signal_value = 1.0,  # 买入
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = data.index[i],
                        metadata={
                            "rsi": current_rsi,
                            "price_to_lower": current_price / current_lower,
                            "strategy": "rsi_bollinger_reversion",
                        },
                    )
                )

            # RSI超买 + 价格接近布林带上轨 = 卖出信号
            elif (
                current_rsi > self.parameters["rsi_overbought"]
                and current_price >= current_upper * 0.98
            ):

                signal_strength = min(
                    1.0, (current_rsi - self.parameters["rsi_overbought"]) / 20
                )
                confidence = 0.7

                signals.append(
                    AlphaSignal(
                        signal_value = -1.0,  # 卖出
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = data.index[i],
                        metadata={
                            "rsi": current_rsi,
                            "price_to_upper": current_price / current_upper,
                            "strategy": "rsi_bollinger_reversion",
                        },
                    )
                )

        return signals

    def _generate_momentum_signals(self, data: pd.DataFrame) -> List[AlphaSignal]:
        """生成动量信号"""
        signals = []

        # 移动平均线
        ma_short = data["close"].rolling(window = self.parameters["ma_short"]).mean()
        ma_long = data["close"].rolling(window = self.parameters["ma_long"]).mean()

        # 动量指标
        momentum = data["close"].pct_change(self.parameters["momentum_period"])

        for i in range(len(data)):
            if i < self.parameters["ma_long"]:
                continue

            current_price = data["close"].iloc[i]
            current_ma_short = ma_short.iloc[i]
            current_ma_long = ma_long.iloc[i]
            current_momentum = momentum.iloc[i]

            # 短期均线上穿长期均线 + 正动量 = 买入
            if (
                current_ma_short > current_ma_long
                and current_momentum > 0
                and current_price > current_ma_short
            ):

                ma_ratio = (current_ma_short - current_ma_long) / current_ma_long
                signal_strength = min(1.0, abs(ma_ratio) * 10)
                confidence = 0.8

                signals.append(
                    AlphaSignal(
                        signal_value = 1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = data.index[i],
                        metadata={
                            "ma_ratio": ma_ratio,
                            "momentum": current_momentum,
                            "strategy": "dual_ma_momentum",
                        },
                    )
                )

            # 短期均线下穿长期均线 + 负动量 = 卖出
            elif (
                current_ma_short < current_ma_long
                and current_momentum < 0
                and current_price < current_ma_short
            ):

                ma_ratio = (current_ma_long - current_ma_short) / current_ma_long
                signal_strength = min(1.0, abs(ma_ratio) * 10)
                confidence = 0.8

                signals.append(
                    AlphaSignal(
                        signal_value = -1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = data.index[i],
                        metadata={
                            "ma_ratio": ma_ratio,
                            "momentum": current_momentum,
                            "strategy": "dual_ma_momentum",
                        },
                    )
                )

        return signals

    def calculate_correlation(self, other_signals: List[AlphaSignal]) -> float:
        """计算相关性"""
        if not self.signal_history or not other_signals:
            return 0.0

        # 提取信号值序列
        self_values = [s.signal_value for s in self.signal_history]
        other_values = [s.signal_value for s in other_signals]

        if len(self_values) != len(other_values):
            # 对齐长度
            min_len = min(len(self_values), len(other_values))
            self_values = self_values[-min_len:]
            other_values = other_values[-min_len:]

        if len(self_values) < 10:
            return 0.0

        correlation = np.corrcoef(self_values, other_values)[0, 1]
        return correlation if not np.isnan(correlation) else 0.0


class MacroEconomicAlpha(AlphaSource):
    """宏观经济Alpha源"""

    def __init__(self, name: str):
        super().__init__(name, AlphaSourceType.MACRO_ECONOMIC)
        self.economic_indicators = [
            "interest_rate",
            "inflation_rate",
            "gdp_growth",
            "unemployment_rate",
        ]

    def generate_signals(
        self, market_data: pd.DataFrame, additional_data: Dict = None
    ) -> List[AlphaSignal]:
        """生成宏观经济信号"""
        signals = []

        if not additional_data or "economic_data" not in additional_data:
            return signals

        econ_data = additional_data["economic_data"]

        # 利率周期分析
        rate_signals = self._analyze_interest_rate_cycle(econ_data, market_data)

        # 经济增长分析
        growth_signals = self._analyze_growth_cycle(econ_data, market_data)

        signals.extend(rate_signals)
        signals.extend(growth_signals)

        self.signal_history.extend(signals)
        self.last_update = datetime.now()

        return signals

    def _analyze_interest_rate_cycle(
        self, econ_data: pd.DataFrame, market_data: pd.DataFrame
    ) -> List[AlphaSignal]:
        """分析利率周期"""
        signals = []

        if "interest_rate" not in econ_data.columns:
            return signals

        # 利率变化趋势
        rate_change = econ_data["interest_rate"].diff()
        rate_trend = rate_change.rolling(window = 12).mean()  # 12个月趋势

        # 市场估值水平 (简化PE)
        market_pe = (
            market_data["close"] / market_data["close"].rolling(window = 252).mean()
        )

        for i in range(len(market_data)):
            if i >= len(rate_trend) or pd.isna(rate_trend.iloc[i]):
                continue

            current_rate_trend = rate_trend.iloc[i]
            current_pe = market_pe.iloc[i]

            # 利率上升周期 + 高估值 = 卖出信号
            if current_rate_trend > 0.1 and current_pe > 1.2:
                signal_strength = min(1.0, current_rate_trend * 5)
                confidence = 0.6

                signals.append(
                    AlphaSignal(
                        signal_value = -1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = market_data.index[i],
                        metadata={
                            "rate_trend": current_rate_trend,
                            "pe_ratio": current_pe,
                            "strategy": "rate_cycle",
                        },
                    )
                )

            # 利率下降周期 + 低估值 = 买入信号
            elif current_rate_trend < -0.1 and current_pe < 0.9:
                signal_strength = min(1.0, abs(current_rate_trend) * 5)
                confidence = 0.6

                signals.append(
                    AlphaSignal(
                        signal_value = 1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = market_data.index[i],
                        metadata={
                            "rate_trend": current_rate_trend,
                            "pe_ratio": current_pe,
                            "strategy": "rate_cycle",
                        },
                    )
                )

        return signals

    def _analyze_growth_cycle(
        self, econ_data: pd.DataFrame, market_data: pd.DataFrame
    ) -> List[AlphaSignal]:
        """分析增长周期"""
        signals = []

        if "gdp_growth" not in econ_data.columns:
            return signals

        # GDP增长趋势
        gdp_trend = econ_data["gdp_growth"].rolling(window = 4).mean()  # 4季度趋势

        for i in range(len(market_data)):
            if i >= len(gdp_trend) or pd.isna(gdp_trend.iloc[i]):
                continue

            current_gdp_trend = gdp_trend.iloc[i]

            # GDP加速增长 = 买入信号
            if current_gdp_trend > 0.5:  # 季度环比增长 >0.5%
                signal_strength = min(1.0, current_gdp_trend)
                confidence = 0.5

                signals.append(
                    AlphaSignal(
                        signal_value = 1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = market_data.index[i],
                        metadata={
                            "gdp_trend": current_gdp_trend,
                            "strategy": "growth_cycle",
                        },
                    )
                )

            # GDP减速增长 = 卖出信号
            elif current_gdp_trend < -0.5:  # 季度环比增长 <-0.5%
                signal_strength = min(1.0, abs(current_gdp_trend))
                confidence = 0.5

                signals.append(
                    AlphaSignal(
                        signal_value = -1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = market_data.index[i],
                        metadata={
                            "gdp_trend": current_gdp_trend,
                            "strategy": "growth_cycle",
                        },
                    )
                )

        return signals

    def calculate_correlation(self, other_signals: List[AlphaSignal]) -> float:
        """计算相关性"""
        return TechnicalAnalysisAlpha.calculate_correlation(self, other_signals)


class CrossAssetAlpha(AlphaSource):
    """跨资产Alpha源"""

    def __init__(self, name: str):
        super().__init__(name, AlphaSourceType.CROSS_ASSET)
        self.asset_classes = ["equity", "bond", "commodity", "currency"]

    def generate_signals(
        self, market_data: pd.DataFrame, additional_data: Dict = None
    ) -> List[AlphaSignal]:
        """生成跨资产信号"""
        signals = []

        if not additional_data or "cross_asset_data" not in additional_data:
            return signals

        cross_data = additional_data["cross_asset_data"]

        # 股债相对价值
        equity_bond_signals = self._analyze_equity_bond_ratio(market_data, cross_data)

        # 商品股票相对强度
        commodity_equity_signals = self._analyze_commodity_equity_ratio(
            market_data, cross_data
        )

        signals.extend(equity_bond_signals)
        signals.extend(commodity_equity_signals)

        self.signal_history.extend(signals)
        self.last_update = datetime.now()

        return signals

    def _analyze_equity_bond_ratio(
        self, equity_data: pd.DataFrame, cross_data: pd.DataFrame
    ) -> List[AlphaSignal]:
        """分析股债比率"""
        signals = []

        if "bond_yield" not in cross_data.columns:
            return signals

        # 股票收益率
        equity_returns = equity_data["close"].pct_change().rolling(window = 21).mean()

        # 债券收益率变化
        bond_yield_change = cross_data["bond_yield"].diff()

        for i in range(len(equity_data)):
            if i >= len(bond_yield_change) or pd.isna(bond_yield_change.iloc[i]):
                continue

            current_equity_return = equity_returns.iloc[i]
            current_bond_yield_change = bond_yield_change.iloc[i]

            # 债券收益率下降 + 股票正收益 = 买入股票
            if current_bond_yield_change < -0.01 and current_equity_return > 0.01:
                signal_strength = min(1.0, abs(current_bond_yield_change) * 50)
                confidence = 0.7

                signals.append(
                    AlphaSignal(
                        signal_value = 1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = equity_data.index[i],
                        metadata={
                            "bond_yield_change": current_bond_yield_change,
                            "equity_return": current_equity_return,
                            "strategy": "equity_bond_rotation",
                        },
                    )
                )

            # 债券收益率上升 + 股票负收益 = 卖出股票
            elif current_bond_yield_change > 0.01 and current_equity_return < -0.01:
                signal_strength = min(1.0, current_bond_yield_change * 50)
                confidence = 0.7

                signals.append(
                    AlphaSignal(
                        signal_value = -1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = equity_data.index[i],
                        metadata={
                            "bond_yield_change": current_bond_yield_change,
                            "equity_return": current_equity_return,
                            "strategy": "equity_bond_rotation",
                        },
                    )
                )

        return signals

    def _analyze_commodity_equity_ratio(
        self, equity_data: pd.DataFrame, cross_data: pd.DataFrame
    ) -> List[AlphaSignal]:
        """分析商品股票比率"""
        signals = []

        if "commodity_index" not in cross_data.columns:
            return signals

        # 商品指数动量
        commodity_momentum = cross_data["commodity_index"].pct_change(63)  # 3个月动量

        for i in range(len(equity_data)):
            if i >= len(commodity_momentum) or pd.isna(commodity_momentum.iloc[i]):
                continue

            current_commodity_momentum = commodity_momentum.iloc[i]

            # 商品强势动量 = 卖出股票 (资金流向商品)
            if current_commodity_momentum > 0.1:  # 10% 3个月收益
                signal_strength = min(1.0, current_commodity_momentum * 5)
                confidence = 0.6

                signals.append(
                    AlphaSignal(
                        signal_value = -1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = equity_data.index[i],
                        metadata={
                            "commodity_momentum": current_commodity_momentum,
                            "strategy": "commodity_equity_rotation",
                        },
                    )
                )

            # 商品弱势动量 = 买入股票 (资金流向股票)
            elif current_commodity_momentum < -0.1:  # -10% 3个月收益
                signal_strength = min(1.0, abs(current_commodity_momentum) * 5)
                confidence = 0.6

                signals.append(
                    AlphaSignal(
                        signal_value = 1.0,
                        signal_strength = signal_strength,
                        confidence = confidence,
                        timestamp = equity_data.index[i],
                        metadata={
                            "commodity_momentum": current_commodity_momentum,
                            "strategy": "commodity_equity_rotation",
                        },
                    )
                )

        return signals

    def calculate_correlation(self, other_signals: List[AlphaSignal]) -> float:
        """计算相关性"""
        return TechnicalAnalysisAlpha.calculate_correlation(self, other_signals)


class IndependentAlphaSystem:
    """独立Alpha系统"""

    def __init__(self):
        self.alpha_sources = []
        self.signal_aggregator = SignalAggregator()
        self.performance_analyzer = PerformanceAnalyzer()

    def add_alpha_source(self, alpha_source: AlphaSource):
        """添加Alpha源"""
        self.alpha_sources.append(alpha_source)

    def generate_all_signals(
        self, market_data: pd.DataFrame, additional_data: Dict = None
    ) -> Dict[str, List[AlphaSignal]]:
        """生成所有Alpha信号"""
        all_signals = {}

        for source in self.alpha_sources:
            print(f"Generating signals from {source.name}...")
            signals = source.generate_signals(market_data, additional_data)
            all_signals[source.name] = signals
            print(f"Generated {len(signals)} signals")

        return all_signals

    def analyze_independence(self) -> Dict[str, float]:
        """分析Alpha源的独立性"""
        correlation_matrix = {}

        [s.name for s in self.alpha_sources]

        for i, source1 in enumerate(self.alpha_sources):
            correlation_matrix[source1.name] = {}

            for j, source2 in enumerate(self.alpha_sources):
                if i == j:
                    correlation_matrix[source1.name][source2.name] = 1.0
                else:
                    correlation = source1.calculate_correlation(source2.signal_history)
                    correlation_matrix[source1.name][source2.name] = correlation

        return correlation_matrix

    def calculate_portfolio_weights(
        self, signals: Dict[str, List[AlphaSignal]], correlation_matrix: Dict = None
    ) -> Dict[str, float]:
        """计算最优组合权重"""
        if not correlation_matrix:
            correlation_matrix = self.analyze_independence()

        # 基于相关性的权重分配
        weights = {}

        # 简化版本：使用最小相关性的权重分配
        avg_correlations = {}
        for source_name in signals.keys():
            correlations = []
            for other_name in signals.keys():
                if source_name != other_name:
                    correlations.append(
                        abs(correlation_matrix[source_name][other_name])
                    )

            avg_correlations[source_name] = np.mean(correlations) if correlations else 0

        # 相关性越低，权重越高
        inv_correlations = {
            name: 1.0 / (1.0 + corr) for name, corr in avg_correlations.items()
        }
        total_inv_corr = sum(inv_correlations.values())

        weights = {
            name: inv_corr / total_inv_corr
            for name, inv_corr in inv_correlations.items()
        }

        return weights

    def generate_portfolio_signals(
        self, market_data: pd.DataFrame, additional_data: Dict = None
    ) -> Dict:
        """生成组合信号"""
        print("Generating Independent Alpha Portfolio Signals...")

        # 生成所有信号
        all_signals = self.generate_all_signals(market_data, additional_data)

        # 分析独立性
        correlation_matrix = self.analyze_independence()
        print("Alpha Source Independence Analysis:")
        for source, correlations in correlation_matrix.items():
            avg_corr = np.mean([v for k, v in correlations.items() if k != source])
            print(f"  {source}: Avg Correlation = {avg_corr:.3f}")

        # 计算权重
        weights = self.calculate_portfolio_weights(all_signals, correlation_matrix)
        print("Portfolio Weights:")
        for source, weight in weights.items():
            print(f"  {source}: {weight:.2%}")

        # 聚合信号
        portfolio_signals = self.signal_aggregator.aggregate_signals(
            all_signals, weights
        )

        # 性能分析
        performance_metrics = self.performance_analyzer.analyze_portfolio_signals(
            portfolio_signals, market_data
        )

        return {
            "signals": all_signals,
            "weights": weights,
            "correlation_matrix": correlation_matrix,
            "portfolio_signals": portfolio_signals,
            "performance_metrics": performance_metrics,
            "independence_score": self._calculate_independence_score(
                correlation_matrix
            ),
        }

    def _calculate_independence_score(self, correlation_matrix: Dict) -> float:
        """计算独立性评分"""
        correlations = []
        for source1, corr_dict in correlation_matrix.items():
            for source2, corr in corr_dict.items():
                if source1 != source2:
                    correlations.append(abs(corr))

        if not correlations:
            return 1.0

        avg_correlation = np.mean(correlations)
        independence_score = 1.0 - avg_correlation

        return independence_score


class SignalAggregator:
    """信号聚合器"""

    def aggregate_signals(
        self, all_signals: Dict[str, List[AlphaSignal]], weights: Dict[str, float]
    ) -> List[AlphaSignal]:
        """聚合信号"""
        # 按时间对齐信号
        time_aligned_signals = self._align_signals_by_time(all_signals)

        # 加权聚合
        aggregated_signals = []

        for timestamp in time_aligned_signals:
            weighted_value = 0
            total_weight = 0
            total_confidence = 0

            for source_name, signal in time_aligned_signals[timestamp].items():
                if signal and source_name in weights:
                    weight = weights[source_name]
                    weighted_value += (
                        signal.signal_value
                        * signal.signal_strength
                        * weight
                        * signal.confidence
                    )
                    total_weight += weight
                    total_confidence += signal.confidence * weight

            if total_weight > 0:
                final_signal_value = weighted_value / total_weight
                avg_confidence = total_confidence / total_weight

                aggregated_signals.append(
                    AlphaSignal(
                        signal_value = final_signal_value,
                        signal_strength = min(1.0, abs(final_signal_value)),
                        confidence = avg_confidence,
                        timestamp = timestamp,
                        metadata={
                            "source_count": len(time_aligned_signals[timestamp]),
                            "method": "weighted_aggregation",
                        },
                    )
                )

        return aggregated_signals

    def _align_signals_by_time(self, all_signals: Dict[str, List[AlphaSignal]]) -> Dict:
        """按时间对齐信号"""
        # 收集所有时间点
        all_timestamps = set()
        for signals in all_signals.values():
            for signal in signals:
                all_timestamps.add(signal.timestamp)

        # 创建时间到信号的映射
        time_aligned = {}

        for timestamp in sorted(all_timestamps):
            time_aligned[timestamp] = {}

            for source_name, signals in all_signals.items():
                # 找到最接近该时间点的信号
                closest_signal = None
                min_time_diff = timedelta(days = 365)  # 初始大值

                for signal in signals:
                    time_diff = abs(signal.timestamp - timestamp)
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_signal = signal

                # 只考虑时间差在合理范围内的信号
                if min_time_diff <= timedelta(days = 1):
                    time_aligned[timestamp][source_name] = closest_signal

        return time_aligned


class PerformanceAnalyzer:
    """性能分析器"""

    def analyze_portfolio_signals(
        self, portfolio_signals: List[AlphaSignal], market_data: pd.DataFrame
    ) -> Dict:
        """分析组合信号性能"""
        if not portfolio_signals or len(market_data) == 0:
            return self._empty_metrics()

        # 将信号转换为时间序列
        signal_series = self._signals_to_series(portfolio_signals)

        # 对齐市场数据
        aligned_data = self._align_with_market_data(signal_series, market_data)

        # 计算投资组合表现
        portfolio_returns = self._calculate_portfolio_returns(
            aligned_data["signals"], aligned_data["market_returns"]
        )

        # 计算性能指标
        metrics = self._calculate_performance_metrics(portfolio_returns)

        return metrics

    def _empty_metrics(self) -> Dict:
        """返回空指标"""
        return {
            "annual_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "information_ratio": 0.0,
            "correlation_to_market": 0.0,
            "signal_count": 0,
        }

    def _signals_to_series(self, signals: List[AlphaSignal]) -> pd.Series:
        """将信号转换为时间序列"""
        timestamps = [s.timestamp for s in signals]
        values = [s.signal_value for s in signals]
        return pd.Series(values, index = timestamps)

    def _align_with_market_data(
        self, signal_series: pd.Series, market_data: pd.DataFrame
    ) -> Dict:
        """与市场数据对齐"""
        # 计算市场收益率
        market_returns = market_data["close"].pct_change()

        # 对齐信号和收益率
        common_index = signal_series.index.intersection(market_returns.index)
        aligned_signals = signal_series.loc[common_index]
        aligned_returns = market_returns.loc[common_index]

        return {"signals": aligned_signals, "market_returns": aligned_returns}

    def _calculate_portfolio_returns(
        self, signals: pd.Series, market_returns: pd.Series
    ) -> pd.Series:
        """计算投资组合收益率"""
        # 简单策略：信号为正时做多，信号为负时做空
        positions = signals.shift(1)  # 用前一日的信号决定当日仓位

        # 计算投资组合收益率
        portfolio_returns = positions * market_returns

        return portfolio_returns

    def _calculate_performance_metrics(self, returns: pd.Series) -> Dict:
        """计算性能指标"""
        if len(returns) == 0:
            return self._empty_metrics()

        # 年化收益率
        annual_return = returns.mean() * 252

        # 年化波动率
        returns.std() * np.sqrt(252)

        # Sharpe比率 (无风险利率3%)
        excess_returns = returns - 0.03 / 252
        sharpe_ratio = (
            excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            if excess_returns.std() > 0
            else 0
        )

        # 最大回撤
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # 胜率
        win_rate = (returns > 0).mean()

        # 信息比率 (相对于市场)
        market_return = 0.08 / 252  # 假设市场年化收益率8%
        active_returns = returns - market_return
        information_ratio = (
            active_returns.mean() / active_returns.std() * np.sqrt(252)
            if active_returns.std() > 0
            else 0
        )

        # 与市场相关性
        market_returns_sample = np.random.normal(
            0, 0.01, len(returns)
        )  # 模拟市场收益率
        correlation_to_market = np.corrcoef(returns, market_returns_sample)[0, 1]
        correlation_to_market = (
            correlation_to_market if not np.isnan(correlation_to_market) else 0
        )

        return {
            "annual_return": annual_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "information_ratio": information_ratio,
            "correlation_to_market": correlation_to_market,
            "signal_count": len(returns),
        }


def main():
    """主函数 - 演示独立Alpha系统"""
    print("Starting Independent Alpha System Demo...")

    # 创建独立Alpha系统
    alpha_system = IndependentAlphaSystem()

    # 添加不同类型的Alpha源
    alpha_system.add_alpha_source(
        TechnicalAnalysisAlpha("RSI_Reversion", AlphaStrategyType.REVERSION)
    )
    alpha_system.add_alpha_source(
        TechnicalAnalysisAlpha("MA_Momentum", AlphaStrategyType.MOMENTUM)
    )
    alpha_system.add_alpha_source(MacroEconomicAlpha("Interest_Rate_Cycle"))
    alpha_system.add_alpha_source(CrossAssetAlpha("Equity_Bond_Rotation"))

    # 生成模拟市场数据
    print("\nGenerating market data...")
    np.random.seed(42)
    dates = pd.date_range("2022 - 01 - 01", "2024 - 12 - 31", freq="D")
    base_price = 100

    # 生成股票价格数据
    trend = np.linspace(0, 0.3, len(dates))
    volatility = np.random.randn(len(dates)) * 0.015
    price_changes = trend + volatility
    prices = base_price * np.exp(np.cumsum(price_changes))

    market_data = pd.DataFrame(
        {"close": prices, "volume": np.random.randint(1000000, 5000000, len(dates))},
        index = dates,
    )

    # 生成宏观经济数据
    econ_dates = pd.date_range("2022 - 01 - 01", "2024 - 12 - 31", freq="M")
    economic_data = pd.DataFrame(
        {
            "interest_rate": 3.0
            + np.sin(np.linspace(0, 4 * np.pi, len(econ_dates))) * 1.5,
            "gdp_growth": 2.0 + np.random.normal(0, 0.5, len(econ_dates)),
            "inflation_rate": 2.5 + np.random.normal(0, 0.3, len(econ_dates)),
            "unemployment_rate": 5.0 + np.random.normal(0, 0.5, len(econ_dates)),
        },
        index = econ_dates,
    )

    # 生成跨资产数据
    cross_asset_data = pd.DataFrame(
        {
            "bond_yield": 2.5 + np.sin(np.linspace(0, 4 * np.pi, len(dates))) * 1.0,
            "commodity_index": 100
            * np.exp(np.cumsum(np.random.normal(0, 0.01, len(dates)))),
        },
        index = dates,
    )

    additional_data = {
        "economic_data": economic_data,
        "cross_asset_data": cross_asset_data,
    }

    # 生成组合信号
    print(f"\nGenerating portfolio signals for {len(market_data)} trading days...")
    result = alpha_system.generate_portfolio_signals(market_data, additional_data)

    # 输出结果
    print(f"\nPortfolio Performance Metrics:")
    print(f"Annual Return: {result['performance_metrics']['annual_return']:.2%}")
    print(f"Sharpe Ratio: {result['performance_metrics']['sharpe_ratio']:.3f}")
    print(f"Max Drawdown: {result['performance_metrics']['max_drawdown']:.2%}")
    print(f"Win Rate: {result['performance_metrics']['win_rate']:.2%}")
    print(
        f"Information Ratio: {result['performance_metrics']['information_ratio']:.3f}"
    )
    print(
        f"Market Correlation: {result['performance_metrics']['correlation_to_market']:.3f}"
    )
    print(f"Total Signals: {result['performance_metrics']['signal_count']}")

    print(f"\nIndependence Score: {result['independence_score']:.3f}")
    print("Score Interpretation:")
    print("  > 0.8: Excellent independence")
    print("  > 0.6: Good independence")
    print("  > 0.4: Moderate independence")
    print("  < 0.4: Low independence (high correlation)")

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"independent_alpha_results_{timestamp}.json"

    # 准备可序列化的数据
    serializable_result = {
        "timestamp": datetime.now().isoformat(),
        "portfolio_weights": result["weights"],
        "performance_metrics": result["performance_metrics"],
        "independence_score": result["independence_score"],
        "alpha_sources": [
            {
                "name": source.name,
                "type": source.source_type.value,
                "signal_count": len(source.signal_history),
            }
            for source in alpha_system.alpha_sources
        ],
    }

    with open(result_file, "w", encoding="utf - 8") as f:
        json.dump(serializable_result, f, indent = 2, ensure_ascii = False)

    print(f"\nResults saved to: {result_file}")

    return alpha_system, result


if __name__ == "__main__":
    alpha_system, result = main()
