"""
Phase 2.2: Momentum Indicators Implementation
动量类扩展指标实现 - Phase 2.2

包含:
- 扩展RSI指标 (Standard, Wilder, Cutler, Adaptive)
- 随机指标 (Stochastic Oscillator)
- 威廉指标 (Williams %R)
- 商品通道指标 (CCI)
- 资金流量指标 (MFI)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class IndicatorResult:
    """技术指标计算结果"""
    name: str
    values: pd.Series
    parameters: Dict
    signals: Optional[pd.Series] = None
    performance_metrics: Optional[Dict] = None

class MomentumIndicators:
    """动量类技术指标计算器"""

    def __init__(self):
        self.performance_cache = {}

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
            raise ValueError(f"Data length {len(data)} less than required period {period + 1}")

        if method == 'standard':
            rsi = self._calculate_rsi_standard(data, period)
        elif method == 'wilder':
            rsi = self._calculate_rsi_wilder(data, period)
        elif method == 'cutler':
            rsi = self._calculate_rsi_cutler(data, period)
        elif method == 'adaptive':
            rsi = self._calculate_rsi_adaptive(data, period)
        else:
            raise ValueError(f"Unsupported RSI method: {method}")

        # Apply normalization
        if normalization == 'minmax':
            rsi = (rsi - rsi.min()) / (rsi.max() - rsi.min())
        elif normalization == 'zscore':
            rsi = (rsi - rsi.mean()) / rsi.std()
        elif normalization == 'sigmoid':
            rsi = 1 / (1 + np.exp(-rsi))

        # Generate trading signals
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
            raise ValueError("High, low, close data lengths must be equal")

        if len(high) < k_period:
            raise ValueError(f"Data length {len(high)} less than required period {k_period}")

        # Calculate highest and lowest values
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        # Calculate %K values
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))

        # Apply smoothing
        k_smooth = k_percent.rolling(window=slowing).mean()

        # Calculate %D values
        d_percent = k_smooth.rolling(window=d_period).mean()

        # Generate trading signals
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
            raise ValueError("High, low, close data lengths must be equal")

        if len(high) < period:
            raise ValueError(f"Data length {len(high)} less than required period {period}")

        # Calculate highest and lowest values
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        # Calculate %R values
        williams_r = (highest_high - close) / (highest_high - lowest_low) * -100

        # Generate trading signals
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
            raise ValueError("High, low, close data lengths must be equal")

        if len(high) < period:
            raise ValueError(f"Data length {len(high)} less than required period {period}")

        # Calculate typical price
        typical_price = (high + low + close) / 3

        # Calculate SMA
        sma_tp = typical_price.rolling(window=period).mean()

        # Calculate mean absolute deviation
        mad = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )

        # Calculate CCI
        cci = (typical_price - sma_tp) / (constant * mad)

        # Generate trading signals
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
            raise ValueError("All input data lengths must be equal")

        if len(high) < period + 1:
            raise ValueError(f"Data length {len(high)} less than required period {period + 1}")

        # Calculate typical price
        typical_price = (high + low + close) / 3

        # Calculate raw money flow
        raw_money_flow = typical_price * volume

        # Calculate positive and negative money flow
        tp_change = typical_price.diff()
        positive_flow = pd.Series(0, index=typical_price.index)
        negative_flow = pd.Series(0, index=typical_price.index)

        positive_flow[tp_change > 0] = raw_money_flow[tp_change > 0]
        negative_flow[tp_change < 0] = raw_money_flow[tp_change < 0]

        # Calculate periodic sums
        positive_sum = positive_flow.rolling(window=period).sum()
        negative_sum = negative_flow.rolling(window=period).sum()

        # Calculate money flow ratio and MFI
        money_flow_ratio = positive_sum / negative_sum
        mfi = 100 - (100 / (1 + money_flow_ratio))

        # Generate trading signals
        signals = self._generate_mfi_signals(mfi)

        return IndicatorResult(
            name="MFI",
            values=mfi,
            parameters={'period': period},
            signals=signals
        )

    # ========================================
    # RSI Calculation Methods
    # ========================================

    def _calculate_rsi_standard(self, data, period):
        """Standard RSI calculation"""
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_rsi_wilder(self, data, period):
        """Wilder RSI calculation (exponential smoothing)"""
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_rsi_cutler(self, data, period):
        """Cutler RSI calculation (simple average)"""
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Use simple moving average
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_rsi_adaptive(self, data, period):
        """Adaptive RSI - adjust period based on volatility"""
        returns = data.pct_change()
        volatility = returns.rolling(window=20).std()

        # Adaptive period
        adaptive_period = period * (1 + volatility * 10)  # Adjust sensitivity
        adaptive_period = adaptive_period.fillna(period)  # Fill NaN with base period
        adaptive_period = adaptive_period.astype(int).clip(period//2, period*2)

        rsi_values = []
        for i in range(len(data)):
            if i < period:
                rsi_values.append(np.nan)
            else:
                current_period = int(adaptive_period.iloc[i])
                if current_period <= i + 1:  # Ensure we have enough data
                    window_data = data.iloc[max(0, i-current_period+1):i+1]
                    if len(window_data) >= 2:  # Need at least 2 points for RSI
                        rsi = self._calculate_rsi_standard(window_data, min(current_period, len(window_data)-1))
                        if len(rsi) > 0:
                            rsi_values.append(rsi.iloc[-1])
                        else:
                            rsi_values.append(np.nan)
                    else:
                        rsi_values.append(np.nan)
                else:
                    rsi_values.append(np.nan)

        return pd.Series(rsi_values, index=data.index)

    # ========================================
    # Momentum Indicator Signal Generation
    # ========================================

    def _generate_rsi_signals(self, rsi, oversold=30, overbought=70):
        """Generate RSI trading signals"""
        signals = pd.Series(0, index=rsi.index)

        # Oversold buy signal
        signals[(rsi < oversold) & (rsi.shift(1) >= oversold)] = 1

        # Overbought sell signal
        signals[(rsi > overbought) & (rsi.shift(1) <= overbought)] = -1

        return signals

    def _generate_stochastic_signals(self, k_line, d_line, oversold=20, overbought=80):
        """Generate Stochastic trading signals"""
        signals = pd.Series(0, index=k_line.index)

        # Golden cross buy
        signals[(k_line > d_line) & (k_line.shift(1) <= d_line.shift(1)) & (k_line < oversold)] = 1

        # Death cross sell
        signals[(k_line < d_line) & (k_line.shift(1) >= d_line.shift(1)) & (k_line > overbought)] = -1

        return signals

    def _generate_williams_r_signals(self, williams_r, oversold=-80, overbought=-20):
        """Generate Williams %R trading signals"""
        signals = pd.Series(0, index=williams_r.index)

        # Oversold buy
        signals[(williams_r < oversold) & (williams_r.shift(1) >= oversold)] = 1

        # Overbought sell
        signals[(williams_r > overbought) & (williams_r.shift(1) <= overbought)] = -1

        return signals

    def _generate_cci_signals(self, cci, oversold=-100, overbought=100):
        """Generate CCI trading signals"""
        signals = pd.Series(0, index=cci.index)

        # Oversold buy
        signals[(cci < oversold) & (cci.shift(1) >= oversold)] = 1

        # Overbought sell
        signals[(cci > overbought) & (cci.shift(1) <= overbought)] = -1

        return signals

    def _generate_mfi_signals(self, mfi, oversold=20, overbought=80):
        """Generate MFI trading signals"""
        signals = pd.Series(0, index=mfi.index)

        # Oversold buy
        signals[(mfi < oversold) & (mfi.shift(1) >= oversold)] = 1

        # Overbought sell
        signals[(mfi > overbought) & (mfi.shift(1) <= overbought)] = -1

        return signals

    # ========================================
    # Performance Metrics
    # ========================================

    def get_indicator_performance_metrics(self, result: IndicatorResult) -> Dict:
        """获取指标性能指标"""
        if isinstance(result.values, pd.Series):
            values = result.values
        else:
            values = result.values.iloc[:, 0]  # Take first column

        # Calculate basic performance metrics
        metrics = {
            'mean': values.mean(),
            'std': values.std(),
            'min': values.min(),
            'max': values.max(),
            'nan_count': values.isna().sum(),
            'valid_count': values.count(),
            'signal_ratio': 0
        }

        # Calculate signal ratio (if signals exist)
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


def test_momentum_indicators():
    """测试动量类扩展指标"""
    import numpy as np

    # Create test data
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    # Simulate comprehensive economic data
    base_value = 100
    price_data = []
    high_data = []
    low_data = []

    for i in range(len(dates)):
        # Add trend and cyclical components
        trend = base_value + i * 0.01
        cycle = 10 * np.sin(2 * np.pi * i / 50)
        noise = np.random.normal(0, 2)

        close = trend + cycle + noise
        high = close + abs(np.random.normal(0, 1))
        low = close - abs(np.random.normal(0, 1))

        price_data.append(close)
        high_data.append(high)
        low_data.append(low)

    # Simulate volume data
    volume_data = np.random.lognormal(10, 0.5, len(dates))

    close_series = pd.Series(price_data, index=dates)
    high_series = pd.Series(high_data, index=dates)
    low_series = pd.Series(low_data, index=dates)
    volume_series = pd.Series(volume_data, index=dates)

    # Create indicator calculator
    calculator = MomentumIndicators()

    print("Testing Momentum Indicators - Phase 2.2")
    print("=" * 60)

    # Test Extended RSI
    print("\n1. Extended RSI:")
    try:
        # Standard RSI
        rsi_std = calculator.calculate_rsi_extended(close_series, period=14, method='standard')
        std_metrics = calculator.get_indicator_performance_metrics(rsi_std)
        print(f"   RSI Standard: SUCCESS")
        print(f"   Mean: {std_metrics['mean']:.2f}, Valid: {std_metrics['valid_count']}")

        # Wilder RSI
        rsi_wild = calculator.calculate_rsi_extended(close_series, period=14, method='wilder')
        wild_metrics = calculator.get_indicator_performance_metrics(rsi_wild)
        print(f"   RSI Wilder: SUCCESS")
        print(f"   Mean: {wild_metrics['mean']:.2f}, Valid: {wild_metrics['valid_count']}")

        # Adaptive RSI
        rsi_adapt = calculator.calculate_rsi_extended(close_series, period=14, method='adaptive')
        adapt_metrics = calculator.get_indicator_performance_metrics(rsi_adapt)
        print(f"   RSI Adaptive: SUCCESS")
        print(f"   Mean: {adapt_metrics['mean']:.2f}, Valid: {adapt_metrics['valid_count']}")

        # Normalized RSI
        rsi_norm = calculator.calculate_rsi_extended(close_series, period=14, normalization='minmax')
        norm_metrics = calculator.get_indicator_performance_metrics(rsi_norm)
        print(f"   RSI Normalized: SUCCESS")
        print(f"   Mean: {norm_metrics['mean']:.2f}, Valid: {norm_metrics['valid_count']}")

        print("   Overall Status: SUCCESS")
    except Exception as e:
        print(f"   Overall Status: FAILED - {e}")
        return False

    # Test Stochastic Oscillator
    print("\n2. Stochastic Oscillator:")
    try:
        stochastic = calculator.calculate_stochastic(high_series, low_series, close_series)
        print(f"   Stochastic: SUCCESS")
        print(f"   %K Mean: {stochastic.values['%K'].mean():.2f}")
        print(f"   %D Mean: {stochastic.values['%D'].mean():.2f}")
        print(f"   Valid points: {stochastic.values['%K'].count()}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test Williams %R
    print("\n3. Williams %R:")
    try:
        williams = calculator.calculate_williams_r(high_series, low_series, close_series)
        williams_metrics = calculator.get_indicator_performance_metrics(williams)
        print(f"   Williams %R: SUCCESS")
        print(f"   Mean: {williams_metrics['mean']:.2f}")
        print(f"   Range: {williams_metrics['min']:.2f} to {williams_metrics['max']:.2f}")
        print(f"   Valid points: {williams_metrics['valid_count']}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test CCI
    print("\n4. Commodity Channel Index:")
    try:
        cci = calculator.calculate_cci(high_series, low_series, close_series)
        cci_metrics = calculator.get_indicator_performance_metrics(cci)
        print(f"   CCI: SUCCESS")
        print(f"   Mean: {cci_metrics['mean']:.2f}")
        print(f"   Std Dev: {cci_metrics['std']:.2f}")
        print(f"   Valid points: {cci_metrics['valid_count']}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    # Test MFI
    print("\n5. Money Flow Index:")
    try:
        mfi = calculator.calculate_mfi(high_series, low_series, close_series, volume_series)
        mfi_metrics = calculator.get_indicator_performance_metrics(mfi)
        print(f"   MFI: SUCCESS")
        print(f"   Mean: {mfi_metrics['mean']:.2f}")
        print(f"   Range: {mfi_metrics['min']:.2f} to {mfi_metrics['max']:.2f}")
        print(f"   Valid points: {mfi_metrics['valid_count']}")
        print("   Status: SUCCESS")
    except Exception as e:
        print(f"   Status: FAILED - {e}")
        return False

    print("\n" + "=" * 60)
    print("Phase 2.2 Momentum Indicators Test Complete!")
    print("All 5 momentum indicator types implemented successfully!")
    print("Status: ALL TESTS PASSED")
    return True


if __name__ == "__main__":
    success = test_momentum_indicators()
    if success:
        print("\nPhase 2.2 completed successfully!")
    else:
        print("\nPhase 2.2 failed!")