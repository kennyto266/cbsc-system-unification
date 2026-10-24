"""
Enhanced Non-Price TA System - Intelligent Indicator Selector
智能指标适配系统 - 根据数据特性自动选择最适合的技术指标

核心功能:
1. IndicatorSuitabilityAssessor - 指标适用性评估器
2. ParameterAdaptationEngine - 参数自适应引擎
3. DataTypeClassifier - 数据类型分类器
4. 指标适用性矩阵和智能推荐
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import warnings

class DataType(Enum):
    """数据类型枚举"""
    INTEREST_RATE = "interest_rate"      # 利率数据 (HIBOR等)
    EXCHANGE_RATE = "exchange_rate"      # 汇率数据
    MONETARY_AGGREGATE = "monetary_aggregate"  # 货币总量
    LIQUIDITY_INDICATOR = "liquidity_indicator"  # 流动性指标
    BOND_YIELD = "bond_yield"           # 债券收益率
    ECONOMIC_INDEX = "economic_index"    # 经济指数
    PRICE_INDEX = "price_index"          # 价格指数
    VOLUME_DATA = "volume_data"          # 成交量数据

@dataclass
class IndicatorProfile:
    """技术指标档案"""
    name: str
    category: str  # trend, momentum, volatility, volume
    data_type_suitability: Dict[DataType, float]  # 适用性评分
    min_data_points: int  # 最小数据点数
    parameter_ranges: Dict[str, Tuple[float, float]]  # 参数范围
    characteristics: List[str]  # 指标特征
    computational_complexity: str  # low, medium, high

@dataclass
class IndicatorRecommendation:
    """指标推荐结果"""
    indicator_name: str
    suitability_score: float
    recommended_parameters: Dict[str, float]
    reasoning: List[str]
    expected_performance: str
    risk_level: str

class DataTypeClassifier:
    """数据类型分类器 - 自动识别经济数据的类型"""

    def __init__(self):
        self.classification_rules = {
            DataType.INTEREST_RATE: {
                'keywords': ['rate', 'hibor', 'interest', 'ir'],
                'value_range': (0, 20),  # 0-20%
                'characteristics': ['low_volatility', 'mean_reverting']
            },
            DataType.EXCHANGE_RATE: {
                'keywords': ['exchange', 'fx', 'currency', 'hkd', 'usd'],
                'value_range': (0.1, 1000),
                'characteristics': ['relative_pricing', 'policy_influenced']
            },
            DataType.MONETARY_AGGREGATE: {
                'keywords': ['monetary', 'base', 'money', 'm2', 'm1'],
                'value_range': (0, 100000),  # 亿级
                'characteristics': ['trending', 'expanding']
            },
            DataType.LIQUIDITY_INDICATOR: {
                'keywords': ['liquidity', 'interbank', 'funding'],
                'value_range': (0, 100000),
                'characteristics': ['cyclical', 'policy_sensitive']
            },
            DataType.BOND_YIELD: {
                'keywords': ['bond', 'yield', 'efbn', 'bill'],
                'value_range': (0, 20),
                'characteristics': ['market_priced', 'forward_looking']
            },
            DataType.ECONOMIC_INDEX: {
                'keywords': ['index', 'cpi', 'gdp', 'pmi'],
                'value_range': (0, 1000),
                'characteristics': ['baseline_anchored', 'trending']
            }
        }

    def classify_data(self, data: pd.DataFrame, column_name: str = None) -> DataType:
        """分类数据类型"""
        if column_name is None:
            # 使用第一列数值数据
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                raise ValueError("没有找到数值型数据")
            column_name = numeric_cols[0]

        series = data[column_name].dropna()
        if len(series) == 0:
            raise ValueError(f"列 {column_name} 没有有效数据")

        # 基于关键词分类
        name_score = {}
        for data_type, rules in self.classification_rules.items():
            score = 0
            for keyword in rules['keywords']:
                if column_name.lower().find(keyword) != -1:
                    score += 1
            name_score[data_type] = score

        # 基于数值特征分类
        value_score = {}
        mean_val = series.mean()
        std_val = series.std()
        cv = std_val / mean_val if mean_val != 0 else 0  # 变异系数

        for data_type, rules in self.classification_rules.items():
            min_val, max_val = rules['value_range']
            if min_val <= mean_val <= max_val:
                value_score[data_type] = 1.0
            else:
                # 基于距离计算分数
                distance = min(abs(mean_val - min_val), abs(mean_val - max_val))
                value_score[data_type] = max(0, 1 - distance / max_val)

        # 基于统计特征分类
        feature_score = {}
        for data_type, rules in self.classification_rules.items():
            score = 0
            for characteristic in rules['characteristics']:
                if characteristic == 'low_volatility' and cv < 0.1:
                    score += 1
                elif characteristic == 'mean_reverting':
                    # 简单的均值回归检测
                    half_life = self._calculate_half_life(series)
                    if half_life < 50:  # 短期均值回归
                        score += 1
                elif characteristic == 'trending' and cv > 0.2:
                    score += 1
                elif characteristic == 'expanding':
                    if series.iloc[-1] > series.iloc[0] * 1.5:  # 长期扩张
                        score += 1
                elif characteristic == 'cyclical':
                    # 简单的周期性检测
                    autocorr = series.autocorr(lag=30)
                    if autocorr > 0.5:
                        score += 1

            feature_score[data_type] = score / len(rules['characteristics'])

        # 综合评分
        final_score = {}
        for data_type in self.classification_rules.keys():
            # 权重: 名称特征 40%, 数值范围 30%, 统计特征 30%
            final_score[data_type] = (
                0.4 * name_score.get(data_type, 0) / max(name_score.values() or 1) +
                0.3 * value_score.get(data_type, 0) +
                0.3 * feature_score.get(data_type, 0)
            )

        # 返回得分最高的数据类型
        best_type = max(final_score, key=final_score.get)

        print(f"🔍 数据分类结果:")
        print(f"  列名: {column_name}")
        print(f"  推荐类型: {best_type.value}")
        print(f"  评分: {final_score[best_type]:.3f}")
        print(f"  统计特征: 均值={mean_val:.2f}, 标准差={std_val:.2f}, 变异系数={cv:.3f}")

        return best_type

    def _calculate_half_life(self, series: pd.Series) -> float:
        """计算均值回归的半衰期"""
        if len(series) < 30:
            return float('inf')

        # 计算一阶差分的自回归
        diff_series = series.diff().dropna()
        if len(diff_series) < 10:
            return float('inf')

        try:
            # 简单的OLS回归来计算速度
            y = diff_series[1:]
            x = -series.shift(1).dropna()[:len(y)]

            if len(x) > 0 and len(y) > 0:
                beta = np.cov(x, y)[0, 1] / np.var(x)
                if beta > 0:
                    return np.log(2) / beta
        except:
            pass

        return float('inf')

class IndicatorSuitabilityAssessor:
    """指标适用性评估器 - 评估技术指标对特定数据的适用性"""

    def __init__(self):
        self.indicator_profiles = self._initialize_indicator_profiles()
        self.suitability_matrix = self._build_suitability_matrix()

    def _initialize_indicator_profiles(self) -> Dict[str, IndicatorProfile]:
        """初始化技术指标档案"""
        profiles = {}

        # 趋势类指标
        profiles['SMA'] = IndicatorProfile(
            name='Simple Moving Average',
            category='trend',
            data_type_suitability={
                DataType.INTEREST_RATE: 0.8,
                DataType.EXCHANGE_RATE: 0.9,
                DataType.MONETARY_AGGREGATE: 0.9,
                DataType.LIQUIDITY_INDICATOR: 0.8,
                DataType.BOND_YIELD: 0.8,
                DataType.ECONOMIC_INDEX: 0.8
            },
            min_data_points=20,
            parameter_ranges={'period': (5, 200)},
            characteristics=['trend_following', 'smoothing', 'lagging'],
            computational_complexity='low'
        )

        profiles['EMA'] = IndicatorProfile(
            name='Exponential Moving Average',
            category='trend',
            data_type_suitability={
                DataType.INTEREST_RATE: 0.9,
                DataType.EXCHANGE_RATE: 0.9,
                DataType.MONETARY_AGGREGATE: 0.9,
                DataType.LIQUIDITY_INDICATOR: 0.8,
                DataType.BOND_YIELD: 0.9,
                DataType.ECONOMIC_INDEX: 0.8
            },
            min_data_points=10,
            parameter_ranges={'period': (5, 100)},
            characteristics=['trend_following', 'responsive', 'lagging'],
            computational_complexity='low'
        )

        profiles['MACD'] = IndicatorProfile(
            name='MACD',
            category='momentum',
            data_type_suitability={
                DataType.INTEREST_RATE: 0.9,
                DataType.EXCHANGE_RATE: 0.8,
                DataType.MONETARY_AGGREGATE: 0.7,
                DataType.LIQUIDITY_INDICATOR: 0.8,
                DataType.BOND_YIELD: 0.9,
                DataType.ECONOMIC_INDEX: 0.7
            },
            min_data_points=26,
            parameter_ranges={'fast': (8, 20), 'slow': (21, 50), 'signal': (5, 15)},
            characteristics=['momentum', 'trend_confirmation', 'crossover'],
            computational_complexity='medium'
        )

        # 动量类指标
        profiles['RSI'] = IndicatorProfile(
            name='Relative Strength Index',
            category='momentum',
            data_type_suitability={
                DataType.INTEREST_RATE: 0.9,  # 利率的均值回归特性
                DataType.EXCHANGE_RATE: 0.7,
                DataType.MONETARY_AGGREGATE: 0.6,
                DataType.LIQUIDITY_INDICATOR: 0.8,
                DataType.BOND_YIELD: 0.9,
                DataType.ECONOMIC_INDEX: 0.6
            },
            min_data_points=14,
            parameter_ranges={'period': (5, 30)},
            characteristics=['mean_reversion', 'overbought_oversold', 'leading'],
            computational_complexity='medium'
        )

        profiles['Stochastic'] = IndicatorProfile(
            name='Stochastic Oscillator',
            category='momentum',
            data_type_suitability={
                DataType.INTEREST_RATE: 0.7,
                DataType.EXCHANGE_RATE: 0.8,
                DataType.MONETARY_AGGREGATE: 0.5,
                DataType.LIQUIDITY_INDICATOR: 0.7,
                DataType.BOND_YIELD: 0.8,
                DataType.ECONOMIC_INDEX: 0.6
            },
            min_data_points=14,
            parameter_ranges={'k_period': (5, 20), 'd_period': (3, 10)},
            characteristics=['momentum', 'overbought_oversold', 'leading'],
            computational_complexity='medium'
        )

        # 波动率类指标
        profiles['Bollinger_Bands'] = IndicatorProfile(
            name='Bollinger Bands',
            category='volatility',
            data_type_suitability={
                DataType.INTEREST_RATE: 0.8,
                DataType.EXCHANGE_RATE: 0.9,
                DataType.MONETARY_AGGREGATE: 0.6,
                DataType.LIQUIDITY_INDICATOR: 0.7,
                DataType.BOND_YIELD: 0.8,
                DataType.ECONOMIC_INDEX: 0.7
            },
            min_data_points=20,
            parameter_ranges={'period': (10, 50), 'std_dev': (1.5, 2.5)},
            characteristics=['volatility', 'mean_reversion', 'adaptive'],
            computational_complexity='medium'
        )

        profiles['ATR'] = IndicatorProfile(
            name='Average True Range',
            category='volatility',
            data_type_suitability={
                DataType.INTEREST_RATE: 0.7,
                DataType.EXCHANGE_RATE: 0.9,
                DataType.MONETARY_AGGREGATE: 0.4,
                DataType.LIQUIDITY_INDICATOR: 0.6,
                DataType.BOND_YIELD: 0.7,
                DataType.ECONOMIC_INDEX: 0.5
            },
            min_data_points=14,
            parameter_ranges={'period': (7, 30)},
            characteristics=['volatility', 'trend_strength'],
            computational_complexity='medium'
        )

        return profiles

    def _build_suitability_matrix(self) -> Dict:
        """构建指标适用性矩阵"""
        matrix = {}

        for indicator_name, profile in self.indicator_profiles.items():
            matrix[indicator_name] = {
                'category': profile.category,
                'min_data_points': profile.min_data_points,
                'complexity': profile.computational_complexity,
                'data_suitability': profile.data_type_suitability
            }

        return matrix

    def assess_suitability(self, data: pd.DataFrame, data_type: DataType,
                          data_length: int) -> List[IndicatorRecommendation]:
        """评估所有指标的适用性并生成推荐"""
        print(f"🎯 评估数据类型 {data_type.value} 的指标适用性...")

        recommendations = []

        for indicator_name, profile in self.indicator_profiles.items():
            # 基础适用性评分
            base_score = profile.data_type_suitability.get(data_type, 0.5)

            # 数据长度检查
            length_score = 1.0 if data_length >= profile.min_data_points else 0.3

            # 数据质量调整（基于简单特征）
            series = data.select_dtypes(include=[np.number]).iloc[:, 0].dropna()
            quality_adjustment = self._assess_data_quality(series, profile)

            # 最终评分
            final_score = base_score * length_score * quality_adjustment

            if final_score > 0.3:  # 只推荐评分大于0.3的指标
                # 推荐参数
                recommended_params = self._recommend_parameters(
                    profile, series, data_type
                )

                # 生成推荐理由
                reasoning = self._generate_reasoning(
                    profile, data_type, final_score, series
                )

                # 预期表现
                expected_performance = self._predict_performance(profile, final_score)

                # 风险等级
                risk_level = self._assess_risk_level(profile, data_type)

                recommendation = IndicatorRecommendation(
                    indicator_name=indicator_name,
                    suitability_score=final_score,
                    recommended_parameters=recommended_params,
                    reasoning=reasoning,
                    expected_performance=expected_performance,
                    risk_level=risk_level
                )

                recommendations.append(recommendation)

        # 按评分排序
        recommendations.sort(key=lambda x: x.suitability_score, reverse=True)

        # 输出推荐结果
        print(f"\n📊 推荐技术指标 (Top {min(5, len(recommendations))}):")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"\n{i}. {rec.indicator_name}")
            print(f"   适用性评分: {rec.suitability_score:.3f}")
            print(f"   推荐参数: {rec.recommended_parameters}")
            print(f"   预期表现: {rec.expected_performance}")
            print(f"   风险等级: {rec.risk_level}")
            print(f"   推荐理由: {', '.join(rec.reasoning[:2])}")

        return recommendations

    def _assess_data_quality(self, series: pd.Series,
                           profile: IndicatorProfile) -> float:
        """评估数据质量对指标的影响"""
        quality_factors = []

        # 完整性
        completeness = len(series) / len(series)  # 已经dropna，所以为1
        quality_factors.append(completeness)

        # 数据点数量充足性
        data_points_score = min(1.0, len(series) / (profile.min_data_points * 5))
        quality_factors.append(data_points_score)

        # 波动性适合性
        cv = series.std() / series.mean() if series.mean() != 0 else 0
        if profile.category == 'volatility':
            volatility_score = min(1.0, cv / 0.1)  # 波动率指标需要一定波动
        elif profile.category == 'momentum':
            volatility_score = min(1.0, cv / 0.05)  # 动量指标需要适度波动
        else:  # trend
            volatility_score = 1.0 - min(1.0, cv / 0.2)  # 趋势指标偏好稳定
        quality_factors.append(volatility_score)

        # 趋势性
        if 'trend' in profile.characteristics:
            trend_score = abs(series.iloc[-1] - series.iloc[0]) / series.mean()
            quality_factors.append(min(1.0, trend_score * 10))

        # 均值回归性
        if 'mean_reversion' in profile.characteristics:
            # 简单的均值回归检测
            half_life = self._calculate_simple_half_life(series)
            reversion_score = 1.0 if half_life < 50 else 0.5
            quality_factors.append(reversion_score)

        return np.mean(quality_factors)

    def _calculate_simple_half_life(self, series: pd.Series) -> float:
        """简单计算均值回归半衰期"""
        if len(series) < 30:
            return float('inf')

        try:
            # 使用一阶自回归
            y = series.diff().dropna()
            x = -series.shift(1).dropna()[:len(y)]

            if len(x) > 5:
                beta = np.cov(x, y)[0, 1] / np.var(x)
                if beta > 0:
                    return np.log(2) / beta
        except:
            pass

        return float('inf')

    def _recommend_parameters(self, profile: IndicatorProfile,
                            series: pd.Series, data_type: DataType) -> Dict[str, float]:
        """推荐指标参数"""
        params = {}

        data_length = len(series)
        volatility = series.std() / series.mean() if series.mean() != 0 else 0

        for param_name, (min_val, max_val) in profile.parameter_ranges.items():
            if param_name == 'period':
                # 根据数据长度调整周期
                if data_type == DataType.INTEREST_RATE:
                    # 利率数据通常较稳定，可使用较短周期
                    params[param_name] = min(max_val, max(min_val, data_length // 20))
                elif data_type in [DataType.EXCHANGE_RATE, DataType.BOND_YIELD]:
                    # 汇率和债券收益率较活跃
                    params[param_name] = min(max_val, max(min_val, data_length // 15))
                else:
                    # 默认基于数据长度
                    params[param_name] = min(max_val, max(min_val, data_length // 25))

            elif param_name == 'std_dev':
                # 根据波动性调整标准差倍数
                if volatility > 0.1:
                    params[param_name] = 2.5  # 高波动需要更宽的带
                else:
                    params[param_name] = 2.0  # 标准设置

            elif param_name in ['fast', 'slow']:
                # MACD参数
                if param_name == 'fast':
                    params[param_name] = min(max_val, max(min_val, data_length // 30))
                else:  # slow
                    params[param_name] = min(max_val, max(min_val, data_length // 15))

            elif param_name in ['k_period', 'd_period']:
                # Stochastic参数
                if param_name == 'k_period':
                    params[param_name] = min(max_val, max(min_val, data_length // 25))
                else:  # d_period
                    params[param_name] = min(max_val, max(min_val, 3))

            else:
                # 默认使用参数范围的中值
                params[param_name] = (min_val + max_val) / 2

        return params

    def _generate_reasoning(self, profile: IndicatorProfile,
                          data_type: DataType, score: float,
                          series: pd.Series) -> List[str]:
        """生成推荐理由"""
        reasoning = []

        # 数据类型适配性
        suitability = profile.data_type_suitability.get(data_type, 0.5)
        if suitability > 0.8:
            reasoning.append(f"非常适合{data_type.value}类型数据")
        elif suitability > 0.6:
            reasoning.append(f"适合{data_type.value}类型数据")

        # 指标特性匹配
        if profile.category == 'trend':
            if series.iloc[-1] > series.iloc[0] * 1.1:
                reasoning.append("数据显示明显趋势，适合趋势跟踪")
        elif profile.category == 'momentum':
            reasoning.append("可捕捉数据的动量变化")
        elif profile.category == 'volatility':
            cv = series.std() / series.mean()
            if cv > 0.05:
                reasoning.append("数据具有一定波动性，适合波动率分析")

        # 数据特征匹配
        if 'mean_reversion' in profile.characteristics:
            half_life = self._calculate_simple_half_life(series)
            if half_life < 50:
                reasoning.append("数据显示均值回归特征")

        # 评分相关
        if score > 0.8:
            reasoning.append("综合评分很高，预期效果良好")
        elif score > 0.6:
            reasoning.append("综合评分良好，值得尝试")

        return reasoning

    def _predict_performance(self, profile: IndicatorProfile,
                           score: float) -> str:
        """预测指标表现"""
        if score > 0.8:
            return "优秀 - 预期能有效捕捉数据特征"
        elif score > 0.6:
            return "良好 - 能够提供有价值的信号"
        elif score > 0.4:
            return "一般 - 可能需要结合其他指标使用"
        else:
            return "较差 - 不建议单独使用"

    def _assess_risk_level(self, profile: IndicatorProfile,
                         data_type: DataType) -> str:
        """评估风险等级"""
        # 基于指标复杂度和数据类型评估风险
        complexity_risk = {
            'low': 0.1,
            'medium': 0.3,
            'high': 0.5
        }[profile.computational_complexity]

        data_type_risk = {
            DataType.INTEREST_RATE: 0.2,
            DataType.EXCHANGE_RATE: 0.4,
            DataType.MONETARY_AGGREGATE: 0.3,
            DataType.LIQUIDITY_INDICATOR: 0.3,
            DataType.BOND_YIELD: 0.3,
            DataType.ECONOMIC_INDEX: 0.2
        }[data_type]

        total_risk = complexity_risk + data_type_risk

        if total_risk < 0.3:
            return "低风险"
        elif total_risk < 0.6:
            return "中等风险"
        else:
            return "高风险"

class ParameterAdaptationEngine:
    """参数自适应引擎 - 根据数据特性动态调整指标参数"""

    def __init__(self):
        self.adaptation_rules = self._initialize_adaptation_rules()

    def _initialize_adaptation_rules(self) -> Dict:
        """初始化参数适配规则"""
        return {
            'period_adjustment': {
                'high_volatility': 0.7,    # 降低周期
                'low_volatility': 1.3,     # 增加周期
                'trending': 1.2,           # 增加周期
                'mean_reverting': 0.8      # 降低周期
            },
            'sensitivity_adjustment': {
                'interest_rate': 0.9,      # 利率数据相对稳定
                'exchange_rate': 1.2,      # 汇率数据更敏感
                'bond_yield': 1.1          # 债券收益率中等敏感
            }
        }

    def adapt_parameters(self, base_parameters: Dict[str, float],
                        data_characteristics: Dict,
                        data_type: DataType) -> Dict[str, float]:
        """根据数据特性适配参数"""
        adapted_params = base_parameters.copy()

        # 获取数据特征
        volatility = data_characteristics.get('volatility', 0.1)
        trend_strength = data_characteristics.get('trend_strength', 0.5)
        reversion_tendency = data_characteristics.get('reversion_tendency', 0.5)

        # 根据波动性调整
        if volatility > 0.15:
            adjustment = self.adaptation_rules['period_adjustment']['high_volatility']
        elif volatility < 0.05:
            adjustment = self.adaptation_rules['period_adjustment']['low_volatility']
        else:
            adjustment = 1.0

        # 根据趋势性调整
        if trend_strength > 0.7:
            adjustment *= self.adaptation_rules['period_adjustment']['trending']

        # 根据均值回归倾向调整
        if reversion_tendency > 0.7:
            adjustment *= self.adaptation_rules['period_adjustment']['mean_reverting']

        # 应用数据类型敏感度调整
        sensitivity_adj = self.adaptation_rules['sensitivity_adjustment'].get(
            data_type.value, 1.0
        )

        # 调整参数
        for param_name in adapted_params:
            if param_name in ['period', 'fast', 'slow', 'k_period']:
                adapted_params[param_name] = max(
                    1, int(adapted_params[param_name] * adjustment * sensitivity_adj)
                )
            elif param_name == 'std_dev':
                # 标准差倍数不直接按比例调整
                if volatility > 0.15:
                    adapted_params[param_name] *= 1.2
                elif volatility < 0.05:
                    adapted_params[param_name] *= 0.9

        return adapted_params

    def analyze_data_characteristics(self, data: pd.DataFrame) -> Dict:
        """分析数据特征"""
        series = data.select_dtypes(include=[np.number]).iloc[:, 0].dropna()

        # 计算统计特征
        returns = series.pct_change().dropna()
        volatility = returns.std() if len(returns) > 0 else 0

        # 趋势强度
        trend_strength = abs((series.iloc[-1] - series.iloc[0]) / series.mean())

        # 均值回归倾向（简化版）
        half_life = self._calculate_half_life(returns)
        reversion_tendency = 1.0 / (1.0 + half_life) if half_life != float('inf') else 0

        return {
            'volatility': volatility,
            'trend_strength': trend_strength,
            'reversion_tendency': reversion_tendency,
            'data_length': len(series)
        }

    def _calculate_half_life(self, returns: pd.Series) -> float:
        """计算半衰期"""
        if len(returns) < 10:
            return float('inf')

        try:
            y = returns[1:]
            x = -returns.shift(1).dropna()[:len(y)]

            if len(x) > 5:
                beta = np.cov(x, y)[0, 1] / np.var(x)
                if beta > 0:
                    return np.log(2) / beta
        except:
            pass

        return float('inf')

class IntelligentIndicatorSelector:
    """智能指标选择器 - 统一的智能指标选择接口"""

    def __init__(self):
        self.data_type_classifier = DataTypeClassifier()
        self.suitability_assessor = IndicatorSuitabilityAssessor()
        self.parameter_adapter = ParameterAdaptationEngine()

    def select_indicators(self, data: pd.DataFrame,
                         column_name: str = None,
                         top_n: int = 5) -> List[IndicatorRecommendation]:
        """智能选择最适合的技术指标"""
        print("🧠 智能指标选择器启动...")
        print("=" * 60)

        # 步骤1: 分类数据类型
        data_type = self.data_type_classifier.classify_data(data, column_name)

        # 步骤2: 分析数据特征
        data_characteristics = self.parameter_adapter.analyze_data_characteristics(data)

        print(f"\n📊 数据特征分析:")
        print(f"  数据长度: {data_characteristics['data_length']} 点")
        print(f"  波动性: {data_characteristics['volatility']:.3f}")
        print(f"  趋势强度: {data_characteristics['trend_strength']:.3f}")
        print(f"  均值回归倾向: {data_characteristics['reversion_tendency']:.3f}")

        # 步骤3: 评估指标适用性
        recommendations = self.suitability_assessor.assess_suitability(
            data, data_type, len(data)
        )

        # 步骤4: 参数自适应调整
        for rec in recommendations:
            adapted_params = self.parameter_adapter.adapt_parameters(
                rec.recommended_parameters,
                data_characteristics,
                data_type
            )
            rec.recommended_parameters = adapted_params

        print("=" * 60)
        print(f"✅ 指标选择完成! 共评估了 {len(self.suitability_assessor.indicator_profiles)} 个指标")

        return recommendations[:top_n]

    def get_indicator_profile(self, indicator_name: str) -> Optional[IndicatorProfile]:
        """获取指标档案"""
        return self.suitability_assessor.indicator_profiles.get(indicator_name)

    def export_recommendations(self, recommendations: List[IndicatorRecommendation],
                              output_path: str):
        """导出推荐结果"""
        import json

        export_data = []
        for rec in recommendations:
            export_data.append({
                'indicator_name': rec.indicator_name,
                'suitability_score': rec.suitability_score,
                'recommended_parameters': rec.recommended_parameters,
                'reasoning': rec.reasoning,
                'expected_performance': rec.expected_performance,
                'risk_level': rec.risk_level
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"📄 推荐结果已导出至: {output_path}")

# 演示功能
def demo_intelligent_selection():
    """演示智能指标选择功能"""
    print("🎯 智能指标选择器演示")
    print("=" * 60)

    # 创建不同类型的示例数据
    np.random.seed(42)

    # HIBOR利率数据（均值回归特征）
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    hibor_rates = 3.0 + np.random.normal(0, 0.5, len(dates))
    hibor_rates = pd.Series(hibor_rates, index=dates).fillna(method='ffill')
    hibor_data = pd.DataFrame({'hibor_overnight': hibor_rates})

    # 汇率数据（趋势特征）
    usdhkd_trend = np.linspace(7.75, 7.85, len(dates)) + np.random.normal(0, 0.02, len(dates))
    usdhkd_data = pd.DataFrame({'usd_hkd_rate': usdhkd_trend}, index=dates)

    # 货币基础数据（长期增长趋势）
    mb_trend = np.linspace(2000, 2500, len(dates)) + np.random.normal(0, 20, len(dates))
    mb_data = pd.DataFrame({'monetary_base': mb_trend}, index=dates)

    # 创建智能选择器
    selector = IntelligentIndicatorSelector()

    # 测试不同数据类型
    test_cases = [
        ("HIBOR利率数据", hibor_data),
        ("USD/HKD汇率数据", usdhkd_data),
        ("货币基础数据", mb_data)
    ]

    for case_name, data in test_cases:
        print(f"\n{'='*60}")
        print(f"🧪 测试案例: {case_name}")
        print(f"{'='*60}")

        recommendations = selector.select_indicators(data, top_n=3)

        # 导出结果
        output_file = f"indicator_recommendations_{case_name.replace(' ', '_').replace('/', '')}.json"
        selector.export_recommendations(recommendations, output_file)

    return recommendations

if __name__ == "__main__":
    # 运行演示
    recommendations = demo_intelligent_selection()

    print("\n🎉 演示完成!")
    print("📄 已生成指标推荐报告文件")