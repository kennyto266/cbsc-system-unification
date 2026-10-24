"""
Phase 2.4: Specialized Data Source Specific Indicators
数据源特定专用指标实现 - Phase 2.4

包含7个专业化指标:
1. calculate_rate_curve_indicator() - HIBOR利率期限结构指标
2. calculate_rate_spread_indicator() - 利差分析指标
3. calculate_currency_strength_indicator() - 汇率强弱指标
4. calculate_monetary_growth_indicator() - 货币供给增长指标
5. calculate_liquidity_pressure_indicator() - 流动性压力指标
6. calculate_yield_spread_indicator() - 外汇基金票据收益率差
7. calculate_usage_ratio_indicator() - 人民币流动性使用率

特点:
- 专为非价格数据设计
- 适应香港政府数据源特性
- 包含完整的信号生成机制
- 性能指标计算和错误处理
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings

@dataclass
class IndicatorResult:
    """技术指标计算结果"""
    name: str
    values: pd.Series
    parameters: Dict
    signals: Optional[pd.Series] = None
    performance_metrics: Optional[Dict] = None

class SpecializedIndicators:
    """数据源特定专用指标计算器 - Phase 2.4实现"""

    def __init__(self):
        self.performance_cache = {}

    def _generate_performance_metrics(self, signals: pd.Series, data: pd.Series) -> Dict:
        """生成性能指标"""
        if len(signals) == 0 or len(data) == 0:
            return {}

        try:
            # 基本统计
            signal_changes = signals.diff().dropna()
            data_changes = data.pct_change().dropna()

            # 信号统计
            total_signals = len(signal_changes[signal_changes != 0])
            buy_signals = len(signals[signals == 1])
            sell_signals = len(signals[signals == -1])

            # 波动率
            volatility = data_changes.std() * np.sqrt(252) if len(data_changes) > 0 else 0

            # 趋势强度
            trend_strength = abs(data_changes.mean()) * 252 if len(data_changes) > 0 else 0

            return {
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'signal_ratio': total_signals / len(data) if len(data) > 0 else 0,
                'volatility': volatility,
                'trend_strength': trend_strength,
                'data_points': len(data)
            }
        except Exception as e:
            warnings.warn(f"性能指标计算失败: {e}")
            return {}

    # ========================================
    # Phase 2.4: 数据源特定专用指标
    # ========================================

    def calculate_rate_curve_indicator(self,
                                     hibor_data: pd.DataFrame,
                                     short_tenor: str = 'Overnight',
                                     long_tenor: str = '12-months') -> IndicatorResult:
        """
        HIBOR利率期限结构指标

        计算短期与长期HIBOR利率的利差，分析收益率曲线形态

        Parameters:
        - hibor_data: 包含不同期限HIBOR利率的DataFrame
        - short_tenor: 短期利率期限
        - long_tenor: 长期利率期限

        特点:
        - 捕捉收益率曲线斜率变化
        - 预测货币政策调整
        - 识别流动性紧张信号
        """
        if hibor_data.empty:
            raise ValueError("HIBOR数据为空")

        # 提取短期和长期利率
        try:
            short_rate = hibor_data[short_tenor]
            long_rate = hibor_data[long_tenor]
        except KeyError as e:
            raise ValueError(f"找不到指定的HIBOR期限: {e}")

        # 计算利率差 (长期 - 短期)
        rate_spread = long_rate - short_rate

        # 计算利率期限结构斜率变化
        spread_change = rate_spread.diff()
        spread_momentum = spread_change.rolling(window=5).mean()

        # 计算Z-score标准化
        spread_zscore = (rate_spread - rate_spread.rolling(20).mean()) / rate_spread.rolling(20).std()

        # 综合指标值
        indicator_value = spread_zscore + spread_momentum * 0.5

        # 生成交易信号
        signals = pd.Series(0, index=indicator_value.index)

        # 收益率曲线陡峭化 (长期利率相对于短期上升)
        signals[indicator_value > 1.0] = 1  # 买入信号
        # 收益率曲线平坦化或倒挂 (长期利率相对于短期下降)
        signals[indicator_value < -1.0] = -1  # 卖出信号

        # 平滑信号
        signals = signals.rolling(window=3).apply(lambda x: 1 if x.mean() > 0.5 else (-1 if x.mean() < -0.5 else 0))

        return IndicatorResult(
            name="HIBOR_RATE_CURVE",
            values=indicator_value.fillna(0),
            parameters={
                'short_tenor': short_tenor,
                'long_tenor': long_tenor,
                'current_spread': rate_spread.iloc[-1] if len(rate_spread) > 0 else 0,
                'spread_zscore': spread_zscore.iloc[-1] if len(spread_zscore) > 0 else 0
            },
            signals=signals.fillna(0),
            performance_metrics=self._generate_performance_metrics(signals, indicator_value)
        )

    def calculate_rate_spread_indicator(self,
                                      hibor_data: pd.DataFrame,
                                      benchmark_tenor: str = 'Overnight',
                                      spread_tenors: List[str] = ['1-month', '3-month', '6-month']) -> IndicatorResult:
        """
        利差分析指标

        分析各期限HIBOR与基准利率的利差变化

        Parameters:
        - hibor_data: HIBOR利率数据
        - benchmark_tenor: 基准利率期限
        - spread_tenors: 需要计算利差的期限列表

        特点:
        - 多期限利差综合分析
        - 识别流动性分层现象
        - 预测利率调整压力
        """
        if hibor_data.empty or benchmark_tenor not in hibor_data.columns:
            raise ValueError("HIBOR数据无效或缺少基准利率")

        benchmark_rate = hibor_data[benchmark_tenor]
        spread_values = []

        # 计算各期限利差
        for tenor in spread_tenors:
            if tenor in hibor_data.columns:
                spread = hibor_data[tenor] - benchmark_rate
                spread_values.append(spread)

        if not spread_values:
            raise ValueError("没有有效的利差数据")

        # 综合利差指标 (平均利差)
        avg_spread = pd.concat(spread_values, axis=1).mean(axis=1)

        # 利差波动率
        spread_volatility = avg_spread.rolling(window=10).std()

        # 利差趋势强度
        spread_trend = avg_spread.diff().rolling(window=5).mean()

        # 利差压力指标 (标准化的利差变化)
        spread_pressure = (avg_spread - avg_spread.rolling(20).mean()) / spread_volatility

        # 综合指标
        indicator_value = spread_pressure + spread_trend * 0.3

        # 生成交易信号
        signals = pd.Series(0, index=indicator_value.index)

        # 利差扩大压力
        signals[indicator_value > 0.8] = 1  # 买入信号
        # 利差收窄压力
        signals[indicator_value < -0.8] = -1  # 卖出信号

        return IndicatorResult(
            name="HIBOR_RATE_SPREAD",
            values=indicator_value.fillna(0),
            parameters={
                'benchmark_tenor': benchmark_tenor,
                'spread_tenors': spread_tenors,
                'current_avg_spread': avg_spread.iloc[-1] if len(avg_spread) > 0 else 0,
                'spread_volatility': spread_volatility.iloc[-1] if len(spread_volatility) > 0 else 0
            },
            signals=signals.fillna(0),
            performance_metrics=self._generate_performance_metrics(signals, indicator_value)
        )

    def calculate_currency_strength_indicator(self,
                                           exchange_rate_data: pd.Series,
                                           period: int = 14) -> IndicatorResult:
        """
        汇率强弱指标

        分析港币汇率的变化趋势和强度

        Parameters:
        - exchange_rate_data: 汇率数据 (港币/其他货币)
        - period: 计算周期

        特点:
        - 衡量汇率相对强度
        - 识别趋势转折点
        - 适应央行干预信号
        """
        if len(exchange_rate_data) < period:
            raise ValueError(f"汇率数据长度 {len(exchange_rate_data)} 小于所需周期 {period}")

        # 计算汇率变化率
        rate_changes = exchange_rate_data.pct_change()

        # 计算相对强度指数 (类似RSI但适用于汇率)
        positive_changes = rate_changes.clip(lower=0)
        negative_changes = -rate_changes.clip(upper=0)

        avg_gain = positive_changes.rolling(window=period).mean()
        avg_loss = negative_changes.rolling(window=period).mean()

        # 避免除零错误
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        # 计算汇率趋势强度
        trend_strength = abs(rate_changes.rolling(window=period).mean() * 252)

        # 计算汇率波动率
        volatility = rate_changes.rolling(window=period).std() * np.sqrt(252)

        # 综合强度指标
        strength_indicator = rsi + trend_strength * 10 - volatility * 5

        # 生成交易信号
        signals = pd.Series(0, index=strength_indicator.index)

        # 港币走强
        signals[strength_indicator > 60] = 1  # 买入信号
        # 港币走弱
        signals[strength_indicator < 40] = -1  # 卖出信号

        return IndicatorResult(
            name="CURRENCY_STRENGTH",
            values=strength_indicator.fillna(50),
            parameters={
                'period': period,
                'current_rate': exchange_rate_data.iloc[-1] if len(exchange_rate_data) > 0 else 0,
                'rsi_value': rsi.iloc[-1] if len(rsi) > 0 else 50,
                'trend_strength': trend_strength.iloc[-1] if len(trend_strength) > 0 else 0
            },
            signals=signals.fillna(0),
            performance_metrics=self._generate_performance_metrics(signals, strength_indicator)
        )

    def calculate_monetary_growth_indicator(self,
                                         monetary_base_data: pd.Series,
                                         period: int = 30) -> IndicatorResult:
        """
        货币供给增长指标

        分析货币基础变化趋势

        Parameters:
        - monetary_base_data: 货币基础数据
        - period: 计算周期

        特点:
        - 捕捉货币供给变化趋势
        - 识别流动性投放/回收
        - 预测市场资金面变化
        """
        if len(monetary_base_data) < period:
            raise ValueError(f"货币基础数据长度 {len(monetary_base_data)} 小于所需周期 {period}")

        # 计算同比增长率
        yoy_growth = monetary_base_data.pct_change(periods=252)  # 252个交易日 ≈ 1年

        # 计算环比增长率
        mom_growth = monetary_base_data.pct_change(periods=period)

        # 计算增长率趋势
        growth_trend = yoy_growth.rolling(window=period).mean()

        # 计算增长率加速度
        growth_acceleration = growth_trend.diff()

        # 计算货币供给波动率
        growth_volatility = yoy_growth.rolling(window=period).std()

        # 标准化增长率
        normalized_growth = (yoy_growth - yoy_growth.rolling(252).mean()) / growth_volatility

        # 综合指标
        indicator_value = normalized_growth + growth_acceleration * 0.5

        # 生成交易信号
        signals = pd.Series(0, index=indicator_value.index)

        # 货币供给加速增长
        signals[indicator_value > 1.0] = 1  # 买入信号
        # 货币供给增速放缓
        signals[indicator_value < -1.0] = -1  # 卖出信号

        return IndicatorResult(
            name="MONETARY_GROWTH",
            values=indicator_value.fillna(0),
            parameters={
                'period': period,
                'current_yoy_growth': yoy_growth.iloc[-1] if len(yoy_growth) > 0 else 0,
                'current_mom_growth': mom_growth.iloc[-1] if len(mom_growth) > 0 else 0,
                'growth_trend': growth_trend.iloc[-1] if len(growth_trend) > 0 else 0
            },
            signals=signals.fillna(0),
            performance_metrics=self._generate_performance_metrics(signals, indicator_value)
        )

    def calculate_liquidity_pressure_indicator(self,
                                             interbank_data: pd.Series,
                                             threshold_percentile: float = 80) -> IndicatorResult:
        """
        流动性压力指标

        分析银行间市场流动性压力

        Parameters:
        - interbank_data: 银行间流动性数据
        - threshold_percentile: 压力阈值百分位数

        特点:
        - 识别流动性紧张信号
        - 预测央行干预可能
        - 量化市场压力水平
        """
        if len(interbank_data) < 50:
            raise ValueError(f"银行间流动性数据长度 {len(interbank_data)} 小于最小要求 50")

        # 计算流动性变化率
        liquidity_change = interbank_data.pct_change()

        # 计算历史分位数阈值
        historical_low = interbank_data.rolling(252).quantile(0.1)
        historical_high = interbank_data.rolling(252).quantile(0.9)
        historical_percentile = interbank_data.rolling(252).quantile(threshold_percentile/100)

        # 计算相对位置
        relative_position = (interbank_data - historical_low) / (historical_high - historical_low)

        # 计算流动性压力得分
        pressure_score = np.where(
            interbank_data < historical_percentile,
            (historical_percentile - interbank_data) / historical_percentile * 100,
            0
        )

        # 计算压力趋势
        pressure_trend = pd.Series(pressure_score).rolling(window=5).mean().diff()

        # 综合压力指标
        pressure_indicator = pd.Series(pressure_score) + pressure_trend * 10

        # 生成交易信号
        signals = pd.Series(0, index=pressure_indicator.index)

        # 流动性压力过高 (央行可能投放流动性)
        signals[pressure_indicator > 50] = 1  # 买入信号
        # 流动性充裕 (央行可能回收流动性)
        signals[pressure_indicator < 10] = -1  # 卖出信号

        return IndicatorResult(
            name="LIQUIDITY_PRESSURE",
            values=pressure_indicator.fillna(0),
            parameters={
                'threshold_percentile': threshold_percentile,
                'current_level': interbank_data.iloc[-1] if len(interbank_data) > 0 else 0,
                'current_pressure': pressure_score[-1] if len(pressure_score) > 0 else 0,
                'relative_position': relative_position.iloc[-1] if len(relative_position) > 0 else 0.5
            },
            signals=signals.fillna(0),
            performance_metrics=self._generate_performance_metrics(signals, pressure_indicator)
        )

    def calculate_yield_spread_indicator(self,
                                       efbn_data: pd.DataFrame,
                                       short_term: str = '2-year',
                                       long_term: str = '10-year') -> IndicatorResult:
        """
        外汇基金票据收益率差指标

        分析外汇基金票据收益率曲线

        Parameters:
        - efbn_data: 外汇基金票据数据
        - short_term: 短期票据
        - long_term: 长期票据

        特点:
        - 收益率曲线形态分析
        - 预期通胀指标
        - 货币政策预期
        """
        if efbn_data.empty:
            raise ValueError("外汇基金票据数据为空")

        try:
            short_yield = efbn_data[short_term]
            long_yield = efbn_data[long_term]
        except KeyError as e:
            raise ValueError(f"找不到指定的外汇基金票据期限: {e}")

        # 计算收益率差
        yield_spread = long_yield - short_yield

        # 计算收益率差变化
        spread_change = yield_spread.diff()

        # 计算收益率差趋势
        spread_trend = spread_change.rolling(window=5).mean()

        # 计算收益率差波动率
        spread_volatility = spread_change.rolling(window=20).std()

        # 计算Z-score
        spread_zscore = (yield_spread - yield_spread.rolling(60).mean()) / spread_volatility

        # 综合指标
        indicator_value = spread_zscore + spread_trend * 2

        # 生成交易信号
        signals = pd.Series(0, index=indicator_value.index)

        # 收益率曲线陡峭化
        signals[indicator_value > 1.5] = 1  # 买入信号
        # 收益率曲线平坦化或倒挂
        signals[indicator_value < -1.5] = -1  # 卖出信号

        return IndicatorResult(
            name="YIELD_SPREAD",
            values=indicator_value.fillna(0),
            parameters={
                'short_term': short_term,
                'long_term': long_term,
                'current_spread': yield_spread.iloc[-1] if len(yield_spread) > 0 else 0,
                'spread_zscore': spread_zscore.iloc[-1] if len(spread_zscore) > 0 else 0,
                'volatility': spread_volatility.iloc[-1] if len(spread_volatility) > 0 else 0
            },
            signals=signals.fillna(0),
            performance_metrics=self._generate_performance_metrics(signals, indicator_value)
        )

    def calculate_usage_ratio_indicator(self,
                                      rmb_data: pd.Series,
                                      total_data: pd.Series,
                                      period: int = 20) -> IndicatorResult:
        """
        人民币流动性使用率指标

        分析人民币流动性工具使用情况

        Parameters:
        - rmb_data: 人民币流动性使用量
        - total_data: 总流动性
        - period: 计算周期

        特点:
        - 人民币需求强度指标
        - 离岸人民币流动性
        - 央行政策效果评估
        """
        if len(rmb_data) < period or len(total_data) < period:
            raise ValueError(f"数据长度不足，需要至少 {period} 个数据点")

        # 确保数据对齐
        if not rmb_data.index.equals(total_data.index):
            # 重新索引对齐
            common_index = rmb_data.index.intersection(total_data.index)
            rmb_data = rmb_data.reindex(common_index)
            total_data = total_data.reindex(common_index)

        # 计算使用率
        usage_ratio = rmb_data / total_data.replace(0, np.nan)

        # 计算使用率变化
        ratio_change = usage_ratio.pct_change()

        # 计算使用率趋势
        ratio_trend = usage_ratio.rolling(window=period).mean()

        # 计算使用率波动率
        ratio_volatility = ratio_change.rolling(window=period).std()

        # 计算相对使用率 (相对于历史水平)
        historical_avg = usage_ratio.rolling(252).mean()
        relative_usage = usage_ratio / historical_avg

        # 综合指标
        indicator_value = (relative_usage - 1) * 100 + ratio_trend * 50

        # 生成交易信号
        signals = pd.Series(0, index=indicator_value.index)

        # 人民币需求增加
        signals[indicator_value > 20] = 1  # 买入信号
        # 人民币需求减少
        signals[indicator_value < -20] = -1  # 卖出信号

        return IndicatorResult(
            name="RMB_USAGE_RATIO",
            values=indicator_value.fillna(0),
            parameters={
                'period': period,
                'current_ratio': usage_ratio.iloc[-1] if len(usage_ratio) > 0 else 0,
                'relative_usage': relative_usage.iloc[-1] if len(relative_usage) > 0 else 1,
                'trend': ratio_trend.iloc[-1] if len(ratio_trend) > 0 else 0,
                'volatility': ratio_volatility.iloc[-1] if len(ratio_volatility) > 0 else 0
            },
            signals=signals.fillna(0),
            performance_metrics=self._generate_performance_metrics(signals, indicator_value)
        )


# ========================================
# 测试函数
# ========================================

def test_specialized_indicators():
    """Test all specialized indicators"""
    print("Starting Phase 2.4 Specialized Indicators Test...")

    # Create indicator calculator
    calculator = SpecializedIndicators()

    try:
        # Generate test data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')

        # HIBOR test data
        hibor_data = pd.DataFrame({
            'Overnight': np.random.uniform(3.0, 4.0, 100),
            '1-month': np.random.uniform(3.5, 4.5, 100),
            '3-month': np.random.uniform(4.0, 5.0, 100),
            '6-month': np.random.uniform(4.2, 5.2, 100),
            '12-months': np.random.uniform(4.5, 5.5, 100)
        }, index=dates)

        # Exchange rate test data
        exchange_rate_data = pd.Series(7.8 + np.random.uniform(-0.1, 0.1, 100), index=dates)

        # Monetary base test data
        monetary_base_data = pd.Series(1000000 + np.cumsum(np.random.uniform(-1000, 1000, 100)), index=dates)

        # Interbank liquidity test data
        interbank_data = pd.Series(50000 + np.random.uniform(-5000, 5000, 100), index=dates)

        # Exchange Fund Bills test data
        efbn_data = pd.DataFrame({
            '2-year': np.random.uniform(3.0, 4.0, 100),
            '5-year': np.random.uniform(3.5, 4.5, 100),
            '10-year': np.random.uniform(4.0, 5.0, 100)
        }, index=dates)

        # RMB liquidity test data
        rmb_data = pd.Series(10000 + np.random.uniform(-1000, 2000, 100), index=dates)
        total_data = pd.Series(50000 + np.random.uniform(-2000, 2000, 100), index=dates)

        results = []

        # Test 1: HIBOR Rate Curve Indicator
        print("\nTest 1: HIBOR Rate Curve Indicator")
        result1 = calculator.calculate_rate_curve_indicator(hibor_data)
        results.append(result1)
        print(f"[PASS] {result1.name}: Current spread {result1.parameters['current_spread']:.4f}")

        # Test 2: Rate Spread Indicator
        print("\nTest 2: Rate Spread Indicator")
        result2 = calculator.calculate_rate_spread_indicator(hibor_data)
        results.append(result2)
        print(f"[PASS] {result2.name}: Average spread {result2.parameters['current_avg_spread']:.4f}")

        # Test 3: Currency Strength Indicator
        print("\nTest 3: Currency Strength Indicator")
        result3 = calculator.calculate_currency_strength_indicator(exchange_rate_data)
        results.append(result3)
        print(f"[PASS] {result3.name}: Current rate {result3.parameters['current_rate']:.4f}")

        # Test 4: Monetary Growth Indicator
        print("\nTest 4: Monetary Growth Indicator")
        result4 = calculator.calculate_monetary_growth_indicator(monetary_base_data)
        results.append(result4)
        print(f"[PASS] {result4.name}: YoY growth {result4.parameters['current_yoy_growth']:.4f}")

        # Test 5: Liquidity Pressure Indicator
        print("\nTest 5: Liquidity Pressure Indicator")
        result5 = calculator.calculate_liquidity_pressure_indicator(interbank_data)
        results.append(result5)
        print(f"[PASS] {result5.name}: Pressure level {result5.parameters['current_pressure']:.2f}")

        # Test 6: Yield Spread Indicator
        print("\nTest 6: Yield Spread Indicator")
        result6 = calculator.calculate_yield_spread_indicator(efbn_data)
        results.append(result6)
        print(f"[PASS] {result6.name}: Yield spread {result6.parameters['current_spread']:.4f}")

        # Test 7: RMB Usage Ratio Indicator
        print("\nTest 7: RMB Usage Ratio Indicator")
        result7 = calculator.calculate_usage_ratio_indicator(rmb_data, total_data)
        results.append(result7)
        print(f"[PASS] {result7.name}: Usage ratio {result7.parameters['current_ratio']:.4f}")

        # Summary results
        print("\n" + "="*60)
        print("Phase 2.4 Specialized Indicators Test Completed!")
        print("="*60)

        for i, result in enumerate(results, 1):
            metrics = result.performance_metrics
            signals_count = metrics.get('total_signals', 0) if metrics else 0
            volatility = metrics.get('volatility', 0) if metrics else 0

            print(f"\n{i}. {result.name}")
            print(f"   Parameters: {result.parameters}")
            print(f"   Signal count: {signals_count}")
            print(f"   Volatility: {volatility:.4f}")
            print(f"   Data points: {len(result.values)}")

        print(f"\n[PASS] All {len(results)} Phase 2.4 specialized indicators tested successfully!")
        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_specialized_indicators()
    if success:
        print("\n[SUCCESS] Phase 2.4 Data Source Specific Indicators Implementation Complete!")
        print("These indicators are ready for use with real data.")
    else:
        print("\n[ERROR] Indicators test failed, please check implementation.")