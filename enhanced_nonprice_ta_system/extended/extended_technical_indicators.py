"""
Enhanced Technical Indicators - Phase 2 Extensions
扩展技术指标库 - Phase 2实施

包含:
1. 趋势类扩展指标 (DEMA, TEMA, TRIMA, MACD变体)
2. 动量类扩展指标 (RSI扩展, Stochastic, Williams %R, CCI, MFI)
3. 波动率指标 (布林带, ATR, 肯特纳通道)
4. 数据源特定专用指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import warnings
from dataclasses import dataclass

@dataclass
class IndicatorResult:
    """技术指标计算结果"""
    name: str
    values: pd.Series
    parameters: Dict
    signals: Optional[pd.Series] = None
    performance_metrics: Optional[Dict] = None

class ExtendedTechnicalIndicators:
    """扩展技术指标计算器 - Phase 2实现"""

    def __init__(self):
        self.performance_cache = {}

    # ========================================
    # Phase 2.1: 趋势类扩展指标
    # ========================================

    def calculate_dema(self, data: pd.Series, period: int = 21) -> IndicatorResult:
        """
        双指数移动平均线 (Double Exponential Moving Average)
        DEMA = 2*EMA - EMA(EMA)

        特点:
        - 减少滞后，比EMA更快速响应价格变化
        - 适用于趋势跟踪和短期交易
        - 对非价格数据（利率、汇率）有良好适应性
        """
        if len(data) < period:
            raise ValueError(f"数据长度 {len(data)} 小于所需周期 {period}")

        # 计算第一次EMA
        ema1 = data.ewm(span=period, adjust=False).mean()

        # 计算第二次EMA (对EMA1再计算EMA)
        ema2 = ema1.ewm(span=period, adjust=False).mean()

        # DEMA = 2*EMA1 - EMA2
        dema = 2 * ema1 - ema2

        # 生成交易信号
        signals = self._generate_trend_signals(data, dema)

        return IndicatorResult(
            name="DEMA",
            values=dema,
            parameters={'period': period},
            signals=signals
        )

    def calculate_tema(self, data: pd.Series, period: int = 21) -> IndicatorResult:
        """
        三指数移动平均线 (Triple Exponential Moving Average)
        TEMA = 3*EMA1 - 3*EMA2 + EMA3

        特点:
        - 进一步减少滞后，最快速的趋势指标
        - 适合高频交易和快速响应
        - 在非价格数据中能有效捕捉转折点
        """
        if len(data) < period:
            raise ValueError(f"数据长度 {len(data)} 小于所需周期 {period}")

        # 计算三层EMA
        ema1 = data.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()

        # TEMA = 3*EMA1 - 3*EMA2 + EMA3
        tema = 3 * ema1 - 3 * ema2 + ema3

        # 生成交易信号
        signals = self._generate_trend_signals(data, tema)

        return IndicatorResult(
            name="TEMA",
            values=tema,
            parameters={'period': period},
            signals=signals
        )

    def calculate_trima(self, data: pd.Series, period: int = 21) -> IndicatorResult:
        """
        三角移动平均线 (Triangular Moving Average)
        TRIMA = SMA(SMA(data, period), period/2)

        特点:
        - 双重平滑，减少噪音
        - 适合中长期趋势分析
        - 对经济数据的周期性变化有良好表现
        """
        if len(data) < period:
            raise ValueError(f"数据长度 {len(data)} 小于所需周期 {period}")

        # 第一次SMA
        sma1 = data.rolling(window=period).mean()

        # 第二次SMA (对SMA1再计算SMA)
        trima_period = max(1, period // 2)
        trima = sma1.rolling(window=trima_period).mean()

        # 生成交易信号
        signals = self._generate_trend_signals(data, trima)

        return IndicatorResult(
            name="TRIMA",
            values=trima,
            parameters={'period': period},
            signals=signals
        )

    def calculate_macd_extended(self,
                              data: pd.Series,
                              fast_period: int = 12,
                              slow_period: int = 26,
                              signal_period: int = 9,
                              variant: str = 'standard') -> IndicatorResult:
        """
        扩展MACD指标 - 支持多种变体

        Variants:
        - 'standard': 标准MACD
        - 'histogram': MACD直方图
        - 'zero_lag': 零滞后MACD
        - 'adaptive': 自适应MACD
        """
        if len(data) < slow_period:
            raise ValueError(f"数据长度 {len(data)} 小于所需慢线周期 {slow_period}")

        if variant == 'standard':
            return self._calculate_macd_standard(data, fast_period, slow_period, signal_period)
        elif variant == 'histogram':
            return self._calculate_macd_histogram(data, fast_period, slow_period, signal_period)
        elif variant == 'zero_lag':
            return self._calculate_macd_zero_lag(data, fast_period, slow_period, signal_period)
        elif variant == 'adaptive':
            return self._calculate_macd_adaptive(data, fast_period, slow_period, signal_period)
        else:
            raise ValueError(f"不支持的MACD变体: {variant}")

    def _calculate_macd_standard(self, data, fast, slow, signal):
        """标准MACD"""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        return IndicatorResult(
            name="MACD_Standard",
            values=pd.DataFrame({
                'MACD': macd_line,
                'Signal': signal_line,
                'Histogram': histogram
            }),
            parameters={
                'fast_period': fast,
                'slow_period': slow,
                'signal_period': signal
            }
        )

    def _calculate_macd_histogram(self, data, fast, slow, signal):
        """MACD直方图变体 - 更注重背离分析"""
        standard_result = self._calculate_macd_standard(data, fast, slow, signal)

        # 计算直方图的移动平均
        hist = standard_result.values['Histogram']
        hist_ma = hist.rolling(window=9).mean()

        # 识别背离信号
        divergence = self._identify_divergence(data, hist)

        return IndicatorResult(
            name="MACD_Histogram",
            values=pd.DataFrame({
                'MACD': standard_result.values['MACD'],
                'Signal': standard_result.values['Signal'],
                'Histogram': hist,
                'Histogram_MA': hist_ma,
                'Divergence': divergence
            }),
            parameters={
                'fast_period': fast,
                'slow_period': slow,
                'signal_period': signal
            }
        )

    def _calculate_macd_zero_lag(self, data, fast, slow, signal):
        """零滞后MACD"""
        # 使用零滞后指数移动平均
        def zero_lag_ema(series, period):
            lag = (period - 1) / 2
            ema = series.ewm(span=period).mean()
            return ema + (series - ema.shift(int(lag)))

        ema_fast = zero_lag_ema(data, fast)
        ema_slow = zero_lag_ema(data, slow)

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        return IndicatorResult(
            name="MACD_ZeroLag",
            values=pd.DataFrame({
                'MACD': macd_line,
                'Signal': signal_line,
                'Histogram': histogram
            }),
            parameters={
                'fast_period': fast,
                'slow_period': slow,
                'signal_period': signal
            }
        )

    def _calculate_macd_adaptive(self, data, fast, slow, signal):
        """自适应MACD - 根据波动率调整参数"""
        # 计算波动率
        returns = data.pct_change()
        volatility = returns.rolling(window=20).std()

        # 自适应调整周期
        adaptive_fast = fast * (1 + volatility)
        adaptive_slow = slow * (1 + volatility)

        # 计算自适应EMA
        macd_values = []
        signal_values = []

        for i in range(len(data)):
            if i < slow:
                macd_values.append(np.nan)
                signal_values.append(np.nan)
            else:
                # 使用动态周期
                current_fast = int(adaptive_fast.iloc[i])
                current_slow = int(adaptive_slow.iloc[i])

                current_data = data.iloc[:i+1]
                ema_fast = current_data.ewm(span=current_fast).mean().iloc[-1]
                ema_slow = current_data.ewm(span=current_slow).mean().iloc[-1]

                macd_line = ema_fast - ema_slow
                macd_values.append(macd_line)

        macd_series = pd.Series(macd_values, index=data.index)
        signal_series = macd_series.ewm(span=signal).mean()

        return IndicatorResult(
            name="MACD_Adaptive",
            values=pd.DataFrame({
                'MACD': macd_series,
                'Signal': signal_series,
                'Histogram': macd_series - signal_series
            }),
            parameters={
                'fast_period': fast,
                'slow_period': slow,
                'signal_period': signal,
                'adaptive': True
            }
        )

    # ========================================
    # 辅助方法
    # ========================================

    def _generate_trend_signals(self, data: pd.Series, indicator: pd.Series) -> pd.Series:
        """生成趋势交易信号"""
        signals = pd.Series(0, index=data.index)

        # 金叉买入信号
        signals[(indicator > data) & (indicator.shift(1) <= data.shift(1))] = 1

        # 死叉卖出信号
        signals[(indicator < data) & (indicator.shift(1) >= data.shift(1))] = -1

        return signals

    def _identify_divergence(self, price: pd.Series, indicator: pd.Series, window: int = 20) -> pd.Series:
        """识别价格与指标的背离"""
        divergence = pd.Series(0, index=price.index)

        for i in range(window, len(price)):
            price_window = price.iloc[i-window:i]
            indicator_window = indicator.iloc[i-window:i]

            # 检查看涨背离：价格新低但指标未创新低
            if price_window.iloc[-1] == price_window.min():
                if indicator_window.iloc[-1] > indicator_window.min():
                    divergence.iloc[i] = 1

            # 检查看跌背离：价格新高但指标未创新高
            elif price_window.iloc[-1] == price_window.max():
                if indicator_window.iloc[-1] < indicator_window.max():
                    divergence.iloc[i] = -1

        return divergence

    # ========================================
    # 性能优化方法
    # ========================================

    def calculate_all_trend_indicators(self,
                                      data: pd.Series,
                                      dema_periods: List[int] = [9, 21, 50],
                                      tema_periods: List[int] = [9, 21, 50],
                                      trima_periods: List[int] = [9, 21, 50],
                                      macd_configs: List[Dict] = None) -> Dict[str, IndicatorResult]:
        """批量计算所有趋势指标"""
        results = {}

        # 计算DEMA
        for period in dema_periods:
            if len(data) >= period:
                results[f'DEMA_{period}'] = self.calculate_dema(data, period)

        # 计算TEMA
        for period in tema_periods:
            if len(data) >= period:
                results[f'TEMA_{period}'] = self.calculate_tema(data, period)

        # 计算TRIMA
        for period in trima_periods:
            if len(data) >= period:
                results[f'TRIMA_{period}'] = self.calculate_trima(data, period)

        # 计算MACD变体
        if macd_configs is None:
            macd_configs = [
                {'fast': 12, 'slow': 26, 'signal': 9, 'variant': 'standard'},
                {'fast': 8, 'slow': 21, 'signal': 7, 'variant': 'zero_lag'},
                {'fast': 5, 'slow': 35, 'signal': 5, 'variant': 'histogram'}
            ]

        for i, config in enumerate(macd_configs):
            if len(data) >= config['slow']:
                variant_name = f"MACD_{config['variant']}_{i}"
                # Extract parameters properly
                fast_period = config.get('fast', config.get('fast_period', 12))
                slow_period = config.get('slow', config.get('slow_period', 26))
                signal_period = config.get('signal', config.get('signal_period', 9))
                variant = config.get('variant', 'standard')

                results[variant_name] = self.calculate_macd_extended(
                    data=data,
                    fast_period=fast_period,
                    slow_period=slow_period,
                    signal_period=signal_period,
                    variant=variant
                )

        return results

    def get_indicator_performance_metrics(self, result: IndicatorResult) -> Dict:
        """获取指标性能指标"""
        if isinstance(result.values, pd.Series):
            values = result.values
        else:
            values = result.values.iloc[:, 0]  # 取第一列

        # 计算基本性能指标
        metrics = {
            'mean': values.mean(),
            'std': values.std(),
            'min': values.min(),
            'max': values.max(),
            'nan_count': values.isna().sum(),
            'valid_count': values.count(),
            'signal_ratio': 0
        }

        # 计算信号比率（如果有信号）
        if result.signals is not None:
            signals = result.signals.dropna()
            if len(signals) > 0:
                buy_signals = (signals == 1).sum()
                sell_signals = (signals == -1).sum()
                total_signals = len(signals)
                metrics['signal_ratio'] = total_signals / len(values)
                metrics['buy_ratio'] = buy_signals / total_signals if total_signals > 0 else 0
                metrics['sell_ratio'] = sell_signals / total_signals if total_signals > 0 else 0

        return metrics


def test_trend_indicators():
    """测试趋势类指标"""
    import numpy as np

    # 创建测试数据
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    # 模拟HIBOR利率数据
    trend = np.linspace(3.0, 4.5, len(dates))
    noise = np.random.normal(0, 0.1, len(dates))
    hibor_data = trend + noise

    # 添加一些周期性变化
    for i in range(len(hibor_data)):
        hibor_data[i] += 0.2 * np.sin(2 * np.pi * i / 365.25)

    test_series = pd.Series(hibor_data, index=dates)

    # 创建指标计算器
    calculator = ExtendedTechnicalIndicators()

    print("测试趋势类扩展指标...")
    print("=" * 60)

    # 测试DEMA
    print("\n1. DEMA (双指数移动平均):")
    dema_result = calculator.calculate_dema(test_series, period=21)
    metrics = calculator.get_indicator_performance_metrics(dema_result)
    print(f"   周期: 21")
    print(f"   平均值: {metrics['mean']:.4f}")
    print(f"   标准差: {metrics['std']:.4f}")
    print(f"   信号比率: {metrics['signal_ratio']:.4f}")

    # 测试TEMA
    print("\n2. TEMA (三指数移动平均):")
    tema_result = calculator.calculate_tema(test_series, period=21)
    metrics = calculator.get_indicator_performance_metrics(tema_result)
    print(f"   周期: 21")
    print(f"   平均值: {metrics['mean']:.4f}")
    print(f"   标准差: {metrics['std']:.4f}")
    print(f"   信号比率: {metrics['signal_ratio']:.4f}")

    # 测试TRIMA
    print("\n3. TRIMA (三角移动平均):")
    trima_result = calculator.calculate_trima(test_series, period=21)
    metrics = calculator.get_indicator_performance_metrics(trima_result)
    print(f"   周期: 21")
    print(f"   平均值: {metrics['mean']:.4f}")
    print(f"   标准差: {metrics['std']:.4f}")
    print(f"   信号比率: {metrics['signal_ratio']:.4f}")

    # 测试MACD变体
    print("\n4. MACD扩展变体:")

    # 标准MACD
    macd_std = calculator.calculate_macd_extended(test_series, variant='standard')
    print(f"   标准MACD: 计算完成")

    # 直方图MACD
    macd_hist = calculator.calculate_macd_extended(test_series, variant='histogram')
    print(f"   直方图MACD: 计算完成")

    # 零滞后MACD
    macd_zero = calculator.calculate_macd_extended(test_series, variant='zero_lag')
    print(f"   零滞后MACD: 计算完成")

    # 批量计算测试
    print("\n5. 批量计算测试:")
    all_results = calculator.calculate_all_trend_indicators(test_series)
    print(f"   计算指标数量: {len(all_results)}")

    for name, result in all_results.items():
        metrics = calculator.get_indicator_performance_metrics(result)
        print(f"   {name}: 有效数据点 {metrics['valid_count']}, 信号比率 {metrics['signal_ratio']:.3f}")

    print("\n✅ 趋势类指标测试完成!")
    return calculator, test_series, all_results


  # ========================================
    # Phase 2.2: 动量类扩展指标
    # ========================================

    def calculate_rsi_extended(self,
                              data: pd.Series,
                              period: int = 14,
                              method: str = 'standard',
                              normalization: str = 'none') -> IndicatorResult:
        """
        扩展RSI指标 - 支持多种计算方法和标准化选项

        Parameters:
        - method: 'standard', 'wilder', 'cutler', 'adaptive'
        - normalization: 'none', 'minmax', 'zscore', 'sigmoid'

        特点:
        - 支持5-100周期范围（超出标准14周期）
        - 多种RSI计算方法
        - 数据标准化选项
        - 非价格数据适配
        """
        if len(data) < period + 1:
            raise ValueError(f"数据长度 {len(data)} 小于所需周期 {period + 1}")

        if method == 'standard':
            rsi = self._calculate_rsi_standard(data, period)
        elif method == 'wilder':
            rsi = self._calculate_rsi_wilder(data, period)
        elif method == 'cutler':
            rsi = self._calculate_rsi_cutler(data, period)
        elif method == 'adaptive':
            rsi = self._calculate_rsi_adaptive(data, period)
        else:
            raise ValueError(f"不支持的RSI方法: {method}")

        # 应用标准化
        if normalization == 'minmax':
            rsi = (rsi - rsi.min()) / (rsi.max() - rsi.min())
        elif normalization == 'zscore':
            rsi = (rsi - rsi.mean()) / rsi.std()
        elif normalization == 'sigmoid':
            rsi = 1 / (1 + np.exp(-rsi))

        # 生成交易信号
        signals = self._generate_rsi_signals(rsi)

        return IndicatorResult(
            name=f"RSI_{method}_{normalization}",
            values=rsi,
            parameters={
                'period': period,
                'method': method,
                'normalization': normalization
            },
            signals=signals
        )

    def calculate_stochastic(self,
                           high: pd.Series,
                           low: pd.Series,
                           close: pd.Series,
                           k_period: int = 14,
                           d_period: int = 3,
                           slowing: int = 3) -> IndicatorResult:
        """
        随机指标 (Stochastic Oscillator) - 适用于非价格数据

        对于非价格数据，将数据视为价格序列:
        - high: 数据周期内的最大值
        - low: 数据周期内的最小值
        - close: 当前值

        特点:
        - 适用于利率、汇率等经济数据的超买超卖分析
        - 支持自定义周期参数
        - 生成K线和D线双重信号
        """
        if len(high) != len(low) or len(high) != len(close):
            raise ValueError("high, low, close 数据长度必须相同")

        if len(high) < k_period:
            raise ValueError(f"数据长度 {len(high)} 小于所需周期 {k_period}")

        # 计算最高最低值
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        # 计算%K值
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))

        # 应用平滑
        k_smooth = k_percent.rolling(window=slowing).mean()

        # 计算%D值
        d_percent = k_smooth.rolling(window=d_period).mean()

        # 生成交易信号
        signals = self._generate_stochastic_signals(k_smooth, d_percent)

        return IndicatorResult(
            name="Stochastic",
            values=pd.DataFrame({
                '%K': k_smooth,
                '%D': d_percent
            }),
            parameters={
                'k_period': k_period,
                'd_period': d_period,
                'slowing': slowing
            },
            signals=signals
        )

    def calculate_williams_r(self,
                            high: pd.Series,
                            low: pd.Series,
                            close: pd.Series,
                            period: int = 14) -> IndicatorResult:
        """
        威廉指标 (Williams %R)

        公式: %R = (Highest High - Current Close) / (Highest High - Lowest Low) * -100

        特点:
        - 超买超卖指标，范围-100到0
        - 领先指标，能提前发出信号
        - 适用于经济数据的极值识别
        """
        if len(high) != len(low) or len(high) != len(close):
            raise ValueError("high, low, close 数据长度必须相同")

        if len(high) < period:
            raise ValueError(f"数据长度 {len(high)} 小于所需周期 {period}")

        # 计算最高最低值
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        # 计算%R值
        williams_r = (highest_high - close) / (highest_high - lowest_low) * -100

        # 生成交易信号
        signals = self._generate_williams_r_signals(williams_r)

        return IndicatorResult(
            name="Williams_R",
            values=williams_r,
            parameters={'period': period},
            signals=signals
        )

    def calculate_cci(self,
                    high: pd.Series,
                    low: pd.Series,
                    close: pd.Series,
                    period: int = 20,
                    constant: float = 0.015) -> IndicatorResult:
        """
        商品通道指标 (Commodity Channel Index)

        公式: CCI = (TP - SMA(TP, period)) / (constant * MD)

        其中 TP = (High + Low + Close) / 3
        MD = Mean Deviation of TP over period

        特点:
        - 识别周期性超买超卖
        - 适用于经济数据的周期性分析
        - 支持自定义常数调整敏感度
        """
        if len(high) != len(low) or len(high) != len(close):
            raise ValueError("high, low, close 数据长度必须相同")

        if len(high) < period:
            raise ValueError(f"数据长度 {len(high)} 小于所需周期 {period}")

        # 计算典型价格
        typical_price = (high + low + close) / 3

        # 计算SMA
        sma_tp = typical_price.rolling(window=period).mean()

        # 计算平均绝对偏差
        mad = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )

        # 计算CCI
        cci = (typical_price - sma_tp) / (constant * mad)

        # 生成交易信号
        signals = self._generate_cci_signals(cci)

        return IndicatorResult(
            name="CCI",
            values=cci,
            parameters={
                'period': period,
                'constant': constant
            },
            signals=signals
        )

    def calculate_mfi(self,
                     high: pd.Series,
                     low: pd.Series,
                     close: pd.Series,
                     volume: pd.Series,
                     period: int = 14) -> IndicatorResult:
        """
        资金流量指标 (Money Flow Index)

        公式: MFI = 100 - (100 / (1 + Money Flow Ratio))

        特点:
        - 结合价格和成交量的动量指标
        - 对于非价格数据，使用数据变化作为"成交量"代理
        - 识别资金流入流出趋势
        """
        if len(high) != len(low) or len(high) != len(close) or len(high) != len(volume):
            raise ValueError("所有输入数据长度必须相同")

        if len(high) < period + 1:
            raise ValueError(f"数据长度 {len(high)} 小于所需周期 {period + 1}")

        # 计算典型价格
        typical_price = (high + low + close) / 3

        # 计算原始资金流量
        raw_money_flow = typical_price * volume

        # 计算正负资金流量
        tp_change = typical_price.diff()
        positive_flow = pd.Series(0, index=typical_price.index)
        negative_flow = pd.Series(0, index=typical_price.index)

        positive_flow[tp_change > 0] = raw_money_flow[tp_change > 0]
        negative_flow[tp_change < 0] = raw_money_flow[tp_change < 0]

        # 计算周期性总和
        positive_sum = positive_flow.rolling(window=period).sum()
        negative_sum = negative_flow.rolling(window=period).sum()

        # 计算资金流量比率和MFI
        money_flow_ratio = positive_sum / negative_sum
        mfi = 100 - (100 / (1 + money_flow_ratio))

        # 生成交易信号
        signals = self._generate_mfi_signals(mfi)

        return IndicatorResult(
            name="MFI",
            values=mfi,
            parameters={'period': period},
            signals=signals
        )

    # ========================================
    # RSI计算方法
    # ========================================

    def _calculate_rsi_standard(self, data, period):
        """标准RSI计算"""
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_rsi_wilder(self, data, period):
        """Wilder RSI计算 (指数平滑)"""
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_rsi_cutler(self, data, period):
        """Cutler RSI计算 (简单平均)"""
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 使用简单移动平均
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_rsi_adaptive(self, data, period):
        """自适应RSI - 根据波动率调整周期"""
        returns = data.pct_change()
        volatility = returns.rolling(window=20).std()

        # 自适应周期
        adaptive_period = period * (1 + volatility * 10)  # 调整敏感度
        adaptive_period = adaptive_period.astype(int).clip(period//2, period*2)

        rsi_values = []
        for i in range(len(data)):
            if i < period:
                rsi_values.append(np.nan)
            else:
                current_period = adaptive_period.iloc[i]
                window_data = data.iloc[i-current_period+1:i+1]
                rsi = self._calculate_rsi_standard(window_data, current_period)
                rsi_values.append(rsi.iloc[-1])

        return pd.Series(rsi_values, index=data.index)

    # ========================================
    # 动量指标信号生成
    # ========================================

    def _generate_rsi_signals(self, rsi, oversold=30, overbought=70):
        """生成RSI交易信号"""
        signals = pd.Series(0, index=rsi.index)

        # 超卖买入
        signals[(rsi < oversold) & (rsi.shift(1) >= oversold)] = 1

        # 超买卖出
        signals[(rsi > overbought) & (rsi.shift(1) <= overbought)] = -1

        return signals

    def _generate_stochastic_signals(self, k_line, d_line, oversold=20, overbought=80):
        """生成随机指标交易信号"""
        signals = pd.Series(0, index=k_line.index)

        # 金叉买入
        signals[(k_line > d_line) & (k_line.shift(1) <= d_line.shift(1)) & (k_line < oversold)] = 1

        # 死叉卖出
        signals[(k_line < d_line) & (k_line.shift(1) >= d_line.shift(1)) & (k_line > overbought)] = -1

        return signals

    def _generate_williams_r_signals(self, williams_r, oversold=-80, overbought=-20):
        """生成威廉指标交易信号"""
        signals = pd.Series(0, index=williams_r.index)

        # 超卖买入
        signals[(williams_r < oversold) & (williams_r.shift(1) >= oversold)] = 1

        # 超买卖出
        signals[(williams_r > overbought) & (williams_r.shift(1) <= overbought)] = -1

        return signals

    def _generate_cci_signals(self, cci, oversold=-100, overbought=100):
        """生成CCI交易信号"""
        signals = pd.Series(0, index=cci.index)

        # 超卖买入
        signals[(cci < oversold) & (cci.shift(1) >= oversold)] = 1

        # 超买卖出
        signals[(cci > overbought) & (cci.shift(1) <= overbought)] = -1

        return signals

    def _generate_mfi_signals(self, mfi, oversold=20, overbought=80):
        """生成MFI交易信号"""
        signals = pd.Series(0, index=mfi.index)

        # 超卖买入
        signals[(mfi < oversold) & (mfi.shift(1) >= oversold)] = 1

        # 超买卖出
        signals[(mfi > overbought) & (mfi.shift(1) <= overbought)] = -1

        return signals

    # ========================================
    # Phase 2.3: 波动率指标实现
    # ========================================

    def calculate_bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: float = 2.0) -> IndicatorResult:
        """
        计算布林带 (Bollinger Bands)

        Parameters:
        -----------
        data : pd.Series
            价格数据
        period : int, default 20
            移动平均周期
        std_dev : float, default 2.0
            标准差倍数

        Returns:
        --------
        IndicatorResult
            包含上轨、中轨、下轨的布林带指标
        """
        try:
            # 中轨：简单移动平均
            sma = data.rolling(window=period).mean()

            # 标准差
            rolling_std = data.rolling(window=period).std()

            # 上轨和下轨
            upper_band = sma + (rolling_std * std_dev)
            lower_band = sma - (rolling_std * std_dev)

            # %B指标（价格在布林带中的位置）
            percent_b = (data - lower_band) / (upper_band - lower_band)

            # 带宽（布林带宽度）
            bandwidth = (upper_band - lower_band) / sma

            values = {
                'upper': upper_band,
                'middle': sma,
                'lower': lower_band,
                'percent_b': percent_b,
                'bandwidth': bandwidth
            }

            parameters = {
                'period': period,
                'std_dev': std_dev
            }

            return IndicatorResult(
                name="Bollinger_Bands",
                values=values,
                parameters=parameters,
                signals=self._generate_bollinger_signals(data, upper_band, lower_band, percent_b)
            )

        except Exception as e:
            raise ValueError(f"布林带计算失败: {e}")

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> IndicatorResult:
        """
        计算平均真实波动范围 (Average True Range)

        Parameters:
        -----------
        high : pd.Series
            最高价数据
        low : pd.Series
            最低价数据
        close : pd.Series
            收盘价数据
        period : int, default 14
            ATR周期

        Returns:
        --------
        IndicatorResult
            ATR指标值
        """
        try:
            # 计算真实波动范围
            tr1 = high - low  # 当前最高价减去最低价
            tr2 = abs(high - close.shift(1))  # 当前最高价减去前收盘价
            tr3 = abs(low - close.shift(1))   # 当前最低价减去前收盘价

            # 真实波动范围为三者中的最大值
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # ATR为真实波动范围的移动平均
            atr = true_range.rolling(window=period).mean()

            # ATR百分比（相对于收盘价的百分比）
            atr_percent = (atr / close) * 100

            values = pd.Series(atr, index=close.index)
            metadata = {
                'true_range': true_range,
                'atr_percent': atr_percent
            }

            parameters = {'period': period}

            return IndicatorResult(
                name="ATR",
                values=values,
                parameters=parameters,
                metadata=metadata,
                signals=self._generate_atr_signals(atr, atr_percent)
            )

        except Exception as e:
            raise ValueError(f"ATR计算失败: {e}")

    def calculate_keltner_channels(self, high: pd.Series, low: pd.Series, close: pd.Series,
                                 ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0) -> IndicatorResult:
        """
        计算肯特纳通道 (Keltner Channels)

        Parameters:
        -----------
        high : pd.Series
            最高价数据
        low : pd.Series
            最低价数据
        close : pd.Series
            收盘价数据
        ema_period : int, default 20
            EMA周期
        atr_period : int, default 10
            ATR周期
        multiplier : float, default 2.0
            ATR倍数

        Returns:
        --------
        IndicatorResult
            肯特纳通道指标
        """
        try:
            # 中线：EMA
            middle_line = close.ewm(span=ema_period, adjust=False).mean()

            # 计算ATR
            atr_result = self.calculate_atr(high, low, close, atr_period)
            atr = atr_result.values

            # 上轨和下轨
            upper_channel = middle_line + (atr * multiplier)
            lower_channel = middle_line - (atr * multiplier)

            # 通道位置（价格在通道中的相对位置）
            channel_position = (close - lower_channel) / (upper_channel - lower_channel)

            # 通道宽度
            channel_width = (upper_channel - lower_channel) / middle_line

            values = {
                'upper': upper_channel,
                'middle': middle_line,
                'lower': lower_channel,
                'channel_position': channel_position,
                'channel_width': channel_width
            }

            parameters = {
                'ema_period': ema_period,
                'atr_period': atr_period,
                'multiplier': multiplier
            }

            return IndicatorResult(
                name="Keltner_Channels",
                values=values,
                parameters=parameters,
                signals=self._generate_keltner_signals(close, upper_channel, lower_channel, channel_position)
            )

        except Exception as e:
            raise ValueError(f"肯特纳通道计算失败: {e}")

    def calculate_donchian_channels(self, high: pd.Series, low: pd.Series, period: int = 20) -> IndicatorResult:
        """
        计算唐奇安通道 (Donchian Channels)

        Parameters:
        -----------
        high : pd.Series
            最高价数据
        low : pd.Series
            最低价数据
        period : int, default 20
            通道周期

        Returns:
        --------
        IndicatorResult
            唐奇安通道指标
        """
        try:
            # 上轨：周期内最高价的最高值
            upper_channel = high.rolling(window=period).max()

            # 下轨：周期内最低价的最低值
            lower_channel = low.rolling(window=period).min()

            # 中轨：上下轨的平均值
            middle_channel = (upper_channel + lower_channel) / 2

            # 通道宽度
            channel_width = (upper_channel - lower_channel) / middle_channel

            # 价格在通道中的位置
            price_position = (high + low) / 2  # 使用中间价格
            channel_position = (price_position - lower_channel) / (upper_channel - lower_channel)

            values = {
                'upper': upper_channel,
                'middle': middle_channel,
                'lower': lower_channel,
                'channel_width': channel_width,
                'channel_position': channel_position
            }

            parameters = {'period': period}

            return IndicatorResult(
                name="Donchian_Channels",
                values=values,
                parameters=parameters,
                signals=self._generate_donchian_signals(high, low, upper_channel, lower_channel)
            )

        except Exception as e:
            raise ValueError(f"唐奇安通道计算失败: {e}")

    def calculate_all_volatility_indicators(self, data: pd.DataFrame) -> dict:
        """
        批量计算所有波动率指标

        Parameters:
        -----------
        data : pd.DataFrame
            包含OHLC数据的DataFrame

        Returns:
        --------
        dict
            所有波动率指标的结果
        """
        results = {}

        try:
            # 布林带（多种参数）
            for period, std_dev in [(10, 1.5), (20, 2.0), (20, 2.5), (50, 2.0)]:
                bb_result = self.calculate_bollinger_bands(data['close'], period, std_dev)
                results[f'BB_{period}_{std_dev}'] = bb_result

            # ATR（多种周期）
            for period in [7, 14, 21]:
                atr_result = self.calculate_atr(data['high'], data['low'], data['close'], period)
                results[f'ATR_{period}'] = atr_result

            # 肯特纳通道（多种参数）
            for ema_period, multiplier in [(20, 2.0), (20, 2.5), (10, 1.5)]:
                kc_result = self.calculate_keltner_channels(
                    data['high'], data['low'], data['close'],
                    ema_period=ema_period, atr_period=10, multiplier=multiplier
                )
                results[f'KC_{ema_period}_{multiplier}'] = kc_result

            # 唐奇安通道（多种周期）
            for period in [10, 20, 50]:
                dc_result = self.calculate_donchian_channels(data['high'], data['low'], period)
                results[f'DC_{period}'] = dc_result

        except Exception as e:
            raise ValueError(f"批量计算波动率指标失败: {e}")

        return results

    # ========================================
    # 波动率指标信号生成
    # ========================================

    def _generate_bollinger_signals(self, price, upper_band, lower_band, percent_b):
        """生成布林带交易信号"""
        signals = pd.Series(0, index=price.index)

        # 价格突破下轨买入
        signals[(price < lower_band) & (price.shift(1) >= lower_band.shift(1))] = 1

        # 价格突破上轨卖出
        signals[(price > upper_band) & (price.shift(1) <= upper_band.shift(1))] = -1

        # %B指标信号
        signals[(percent_b < 0.05) & (percent_b.shift(1) >= 0.05)] = 1  # 超卖
        signals[(percent_b > 0.95) & (percent_b.shift(1) <= 0.95)] = -1  # 超买

        return signals

    def _generate_atr_signals(self, atr, atr_percent, threshold_multiplier=2.0):
        """生成ATR相关信号"""
        signals = pd.Series(0, index=atr.index)

        # ATR异常高值（可能的市场转折点）
        atr_threshold = atr_percent.rolling(window=20).mean() * threshold_multiplier
        signals[atr_percent > atr_threshold] = 1  # 高波动率机会

        # ATR异常低值（可能的突破前盘整）
        atr_low_threshold = atr_percent.rolling(window=20).mean() * 0.5
        signals[atr_percent < atr_low_threshold] = -1  # 低波动率盘整

        return signals

    def _generate_keltner_signals(self, price, upper_channel, lower_channel, channel_position):
        """生成肯特纳通道信号"""
        signals = pd.Series(0, index=price.index)

        # 突破上轨
        signals[(price > upper_channel) & (price.shift(1) <= upper_channel.shift(1))] = 1

        # 突破下轨
        signals[(price < lower_channel) & (price.shift(1) >= lower_channel.shift(1))] = -1

        # 通道位置信号
        signals[(channel_position < 0.1) & (channel_position.shift(1) >= 0.1)] = 1  # 接近下轨
        signals[(channel_position > 0.9) & (channel_position.shift(1) <= 0.9)] = -1  # 接近上轨

        return signals

    def _generate_donchian_signals(self, high, low, upper_channel, lower_channel):
        """生成唐奇安通道信号"""
        signals = pd.Series(0, index=high.index)

        # 突破20日新高买入
        buy_breakout = (high > upper_channel) & (high.shift(1) <= upper_channel.shift(1))
        signals[buy_breakout] = 1

        # 突破20日新低卖出
        sell_breakout = (low < lower_channel) & (low.shift(1) >= lower_channel.shift(1))
        signals[sell_breakout] = -1

        return signals


def test_momentum_indicators():
    """测试动量类扩展指标"""
    import numpy as np

    # 创建测试数据
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    # 模拟综合经济数据
    base_value = 100
    price_data = []
    high_data = []
    low_data = []

    for i in range(len(dates)):
        # 添加趋势和周期性
        trend = base_value + i * 0.01
        cycle = 10 * np.sin(2 * np.pi * i / 50)
        noise = np.random.normal(0, 2)

        close = trend + cycle + noise
        high = close + abs(np.random.normal(0, 1))
        low = close - abs(np.random.normal(0, 1))

        price_data.append(close)
        high_data.append(high)
        low_data.append(low)

    # 模拟成交量数据
    volume_data = np.random.lognormal(10, 0.5, len(dates))

    close_series = pd.Series(price_data, index=dates)
    high_series = pd.Series(high_data, index=dates)
    low_series = pd.Series(low_data, index=dates)
    volume_series = pd.Series(volume_data, index=dates)

    # 创建指标计算器
    calculator = ExtendedTechnicalIndicators()

    print("Testing Momentum Indicators - Phase 2.2")
    print("=" * 60)

    # 测试RSI扩展
    print("\n1. Extended RSI:")
    try:
        # 标准RSI
        rsi_std = calculator.calculate_rsi_extended(close_series, period=14, method='standard')
        print(f"   RSI Standard: 计算完成")

        # Wilder RSI
        rsi_wild = calculator.calculate_rsi_extended(close_series, period=14, method='wilder')
        print(f"   RSI Wilder: 计算完成")

        # 自适应RSI
        rsi_adapt = calculator.calculate_rsi_extended(close_series, period=14, method='adaptive')
        print(f"   RSI Adaptive: 计算完成")

        # 标准化RSI
        rsi_norm = calculator.calculate_rsi_extended(close_series, period=14, normalization='minmax')
        print(f"   RSI Normalized: 计算完成")

        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")

    # 测试随机指标
    print("\n2. Stochastic Oscillator:")
    try:
        stochastic = calculator.calculate_stochastic(high_series, low_series, close_series)
        print(f"   Stochastic: 计算完成")
        print(f"   %K Mean: {stochastic.values['%K'].mean():.2f}")
        print(f"   %D Mean: {stochastic.values['%D'].mean():.2f}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")

    # 测试威廉指标
    print("\n3. Williams %R:")
    try:
        williams = calculator.calculate_williams_r(high_series, low_series, close_series)
        print(f"   Williams %R: 计算完成")
        print(f"   Mean: {williams.values.mean():.2f}")
        print(f"   Range: {williams.values.min():.2f} to {williams.values.max():.2f}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")

    # 测试CCI
    print("\n4. Commodity Channel Index:")
    try:
        cci = calculator.calculate_cci(high_series, low_series, close_series)
        print(f"   CCI: 计算完成")
        print(f"   Mean: {cci.values.mean():.2f}")
        print(f"   Std Dev: {cci.values.std():.2f}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")

    # 测试MFI
    print("\n5. Money Flow Index:")
    try:
        mfi = calculator.calculate_mfi(high_series, low_series, close_series, volume_series)
        print(f"   MFI: 计算完成")
        print(f"   Mean: {mfi.values.mean():.2f}")
        print(f"   Range: {mfi.values.min():.2f} to {mfi.values.max():.2f}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")

    print("\nPhase 2.2 Momentum Indicators Test Complete!")
    return calculator


if __name__ == "__main__":
    test_momentum_indicators()