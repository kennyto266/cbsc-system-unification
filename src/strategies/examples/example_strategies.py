"""
Example Quantitative Trading Strategies
示例量化交易策略

包含多種常用的量化策略實現：
1. Moving Average Crossover Strategy
2. RSI Mean Reversion Strategy
3. Pairs Trading Strategy
4. Bollinger Bands Breakout Strategy
5. Momentum Strategy
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..quant_strategy_framework import (
    QuantStrategyBase, StrategyConfig, StrategyType, SignalType, Signal
)

logger = logging.getLogger('ExampleStrategies')

class MovingAverageCrossoverStrategy(QuantStrategyBase):
    """移動平均線交叉策略"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.fast_period = self.parameters.get('fast_period', 10)
        self.slow_period = self.parameters.get('slow_period', 30)
        self.signal_threshold = self.parameters.get('signal_threshold', 0.02)

        # 驗證參數
        if self.fast_period >= self.slow_period:
            raise ValueError("快速MA週期必須小於慢速MA週期")

    def initialize(self) -> bool:
        """初始化策略"""
        try:
            self.logger.info(
                f"初始化MA交叉策略: 快速={self.fast_period}, 慢速={self.slow_period}, "
                f"閾值={self.signal_threshold}"
            )
            return True
        except Exception as e:
            self.logger.error(f"初始化失敗: {str(e)}")
            return False

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信號"""
        signals = []

        # 計算移動平均線
        data['ma_fast'] = data['close'].rolling(window=self.fast_period).mean()
        data['ma_slow'] = data['close'].rolling(window=self.slow_period).mean()

        # 計算交叉點
        data['ma_diff'] = data['ma_fast'] - data['ma_slow']
        data['ma_diff_pct'] = data['ma_diff'] / data['ma_slow']

        # 當前數據
        current = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else current

        # 金叉：快速MA上穿慢速MA
        if (prev['ma_fast'] <= prev['ma_slow'] and
            current['ma_fast'] > current['ma_slow'] and
            abs(current['ma_diff_pct']) > self.signal_threshold):

            signal = Signal(
                symbol=self.config.symbols[0],
                signal_type=SignalType.BUY,
                strength=min(abs(current['ma_diff_pct']) * 10, 1.0),
                price=current['close'],
                timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                confidence=0.7,
                metadata={
                    'fast_ma': current['ma_fast'],
                    'slow_ma': current['ma_slow'],
                    'ma_diff': current['ma_diff']
                }
            )
            signals.append(signal)

        # 死叉：快速MA下穿慢速MA
        elif (prev['ma_fast'] >= prev['ma_slow'] and
              current['ma_fast'] < current['ma_slow'] and
              abs(current['ma_diff_pct']) > self.signal_threshold):

            signal = Signal(
                symbol=self.config.symbols[0],
                signal_type=SignalType.SELL,
                strength=min(abs(current['ma_diff_pct']) * 10, 1.0),
                price=current['close'],
                timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                confidence=0.7,
                metadata={
                    'fast_ma': current['ma_fast'],
                    'slow_ma': current['ma_slow'],
                    'ma_diff': current['ma_diff']
                }
            )
            signals.append(signal)

        return signals

    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """計算倉位大小"""
        # 基於信號強度和最大倉位限制
        base_size = portfolio_value * self.config.max_position_size
        return base_size * signal.strength / signal.price

class RSIMeanReversionStrategy(QuantStrategyBase):
    """RSI均值回歸策略"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.rsi_period = self.parameters.get('rsi_period', 14)
        self.oversold_level = self.parameters.get('oversold_level', 30)
        self.overbought_level = self.parameters.get('overbought_level', 70)
        self.exit_oversold = self.parameters.get('exit_oversold', 50)
        self.exit_overbought = self.parameters.get('exit_overbought', 50)

    def initialize(self) -> bool:
        """初始化策略"""
        try:
            self.logger.info(
                f"初始化RSI策略: RSI週期={self.rsi_period}, "
                f"超賣={self.oversold_level}, 超買={self.overbought_level}"
            )
            return True
        except Exception as e:
            self.logger.error(f"初始化失敗: {str(e)}")
            return False

    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信號"""
        signals = []

        # 計算RSI
        data['rsi'] = self.calculate_rsi(data['close'], self.rsi_period)

        current = data.iloc[-1]

        # 超賣信號：RSI低於超賣水平
        if current['rsi'] < self.oversold_level:
            position = self.positions.get(self.config.symbols[0])

            # 如果沒有空頭持倉，則買入
            if not position or position.quantity <= 0:
                signal = Signal(
                    symbol=self.config.symbols[0],
                    signal_type=SignalType.BUY,
                    strength=(self.oversold_level - current['rsi']) / self.oversold_level,
                    price=current['close'],
                    timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                    confidence=0.6,
                    metadata={
                        'rsi': current['rsi'],
                        'action': 'oversold_entry'
                    }
                )
                signals.append(signal)

        # 超買信號：RSI高於超買水平
        elif current['rsi'] > self.overbought_level:
            position = self.positions.get(self.config.symbols[0])

            # 如果沒有多頭持倉，則賣出
            if not position or position.quantity >= 0:
                signal = Signal(
                    symbol=self.config.symbols[0],
                    signal_type=SignalType.SELL,
                    strength=(current['rsi'] - self.overbought_level) / (100 - self.overbought_level),
                    price=current['close'],
                    timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                    confidence=0.6,
                    metadata={
                        'rsi': current['rsi'],
                        'action': 'overbought_entry'
                    }
                )
                signals.append(signal)

        # 退出信號：RSI回到中間區域
        elif self.exit_oversold <= current['rsi'] <= self.exit_overbought:
            position = self.positions.get(self.config.symbols[0])

            if position and position.quantity != 0:
                signal = Signal(
                    symbol=self.config.symbols[0],
                    signal_type=SignalType.CLOSE,
                    strength=0.8,
                    price=current['close'],
                    timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                    confidence=0.5,
                    metadata={
                        'rsi': current['rsi'],
                        'action': 'exit_mean_reversion'
                    }
                )
                signals.append(signal)

        return signals

    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """計算倉位大小"""
        base_size = portfolio_value * self.config.max_position_size

        # RSI策略使用固定倉位大小
        return base_size / signal.price

class PairsTradingStrategy(QuantStrategyBase):
    """配對交易策略"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        if len(self.config.symbols) != 2:
            raise ValueError("配對交易策略需要恰好兩個標的")

        self.lookback_period = self.parameters.get('lookback_period', 60)
        self.z_entry = self.parameters.get('z_entry', 2.0)
        self.z_exit = self.parameters.get('z_exit', 0.5)
        self.hedge_ratio = None

    def initialize(self) -> bool:
        """初始化策略"""
        try:
            self.logger.info(
                f"初始化配對交易策略: 標的={self.config.symbols}, "
                f"回看期={self.lookback_period}, 入場Z值={self.z_entry}"
            )
            return True
        except Exception as e:
            self.logger.error(f"初始化失敗: {str(e)}")
            return False

    def calculate_hedge_ratio(self, y: pd.Series, x: pd.Series) -> float:
        """計算對沖比率"""
        # 使用回歸方法計算對沖比率
        valid_idx = y.notna() & x.notna()
        if sum(valid_idx) < 10:
            return 1.0

        # 去除趨勢
        y_ret = y.pct_change().dropna()
        x_ret = x.pct_change().dropna()

        # 對齊數據
        common_idx = y_ret.index.intersection(x_ret.index)
        if len(common_idx) < 10:
            return 1.0

        # 計算beta作為對沖比率
        beta = np.cov(y_ret[common_idx], x_ret[common_idx])[0, 1] / np.var(x_ret[common_idx])

        return beta if not np.isnan(beta) else 1.0

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信號"""
        signals = []

        if len(self.config.symbols) != 2:
            return signals

        symbol1, symbol2 = self.config.symbols

        # 計算對沖比率
        self.hedge_ratio = self.calculate_hedge_ratio(
            data[f'close_{symbol1}'],
            data[f'close_{symbol2}']
        )

        # 計算價差
        data['spread'] = data[f'close_{symbol1}'] - self.hedge_ratio * data[f'close_{symbol2}']

        # 計算價差的Z分數
        data['spread_mean'] = data['spread'].rolling(window=self.lookback_period).mean()
        data['spread_std'] = data['spread'].rolling(window=self.lookback_period).std()
        data['z_score'] = (data['spread'] - data['spread_mean']) / data['spread_std']

        current = data.iloc[-1]
        current_z = current['z_score']

        # 價差過大（做空價差）：賣出symbol1，買入symbol2
        if current_z > self.z_entry:
            signals.append(Signal(
                symbol=symbol1,
                signal_type=SignalType.SELL,
                strength=min(abs(current_z) / self.z_entry, 1.0),
                price=current[f'close_{symbol1}'],
                timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                confidence=0.7,
                metadata={
                    'z_score': current_z,
                    'spread': current['spread'],
                    'hedge_ratio': self.hedge_ratio,
                    'action': 'short_spread'
                }
            ))

            signals.append(Signal(
                symbol=symbol2,
                signal_type=SignalType.BUY,
                strength=min(abs(current_z) / self.z_entry, 1.0),
                price=current[f'close_{symbol2}'],
                timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                confidence=0.7,
                metadata={
                    'z_score': current_z,
                    'spread': current['spread'],
                    'hedge_ratio': self.hedge_ratio,
                    'action': 'long_spread_hedge'
                }
            ))

        # 價差過小（做多價差）：買入symbol1，賣出symbol2
        elif current_z < -self.z_entry:
            signals.append(Signal(
                symbol=symbol1,
                signal_type=SignalType.BUY,
                strength=min(abs(current_z) / self.z_entry, 1.0),
                price=current[f'close_{symbol1}'],
                timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                confidence=0.7,
                metadata={
                    'z_score': current_z,
                    'spread': current['spread'],
                    'hedge_ratio': self.hedge_ratio,
                    'action': 'long_spread'
                }
            ))

            signals.append(Signal(
                symbol=symbol2,
                signal_type=SignalType.SELL,
                strength=min(abs(current_z) / self.z_entry, 1.0),
                price=current[f'close_{symbol2}'],
                timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                confidence=0.7,
                metadata={
                    'z_score': current_z,
                    'spread': current['spread'],
                    'hedge_ratio': self.hedge_ratio,
                    'action': 'short_spread_hedge'
                }
            ))

        # 價差回到正常範圍：平倉
        elif abs(current_z) < self.z_exit:
            # 檢查是否有持倉需要平倉
            for symbol in self.config.symbols:
                position = self.positions.get(symbol)
                if position and position.quantity != 0:
                    signals.append(Signal(
                        symbol=symbol,
                        signal_type=SignalType.CLOSE,
                        strength=1.0,
                        price=current[f'close_{symbol}'],
                        timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                        confidence=0.9,
                        metadata={
                            'z_score': current_z,
                            'action': 'close_pairs'
                        }
                    ))

        return signals

    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """計算倉位大小"""
        base_size = portfolio_value * self.config.max_position_size * 0.5  # 每個標的佔用一半資金
        return base_size / signal.price

class BollingerBandsStrategy(QuantStrategyBase):
    """布林帶突破策略"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.bb_period = self.parameters.get('bb_period', 20)
        self.bb_std = self.parameters.get('bb_std', 2)
        self.volume_filter = self.parameters.get('volume_filter', True)

    def initialize(self) -> bool:
        """初始化策略"""
        try:
            self.logger.info(
                f"初始化布林帶策略: 週期={self.bb_period}, 標準差={self.bb_std}"
            )
            return True
        except Exception as e:
            self.logger.error(f"初始化失敗: {str(e)}")
            return False

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信號"""
        signals = []

        # 計算布林帶
        data['bb_middle'] = data['close'].rolling(window=self.bb_period).mean()
        bb_std = data['close'].rolling(window=self.bb_period).std()
        data['bb_upper'] = data['bb_middle'] + self.bb_std * bb_std
        data['bb_lower'] = data['bb_middle'] - self.bb_std * bb_std

        # 計算布林帶位置
        data['bb_position'] = (data['close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])

        # 成交量濾鏡
        if self.volume_filter and 'volume' in data.columns:
            data['volume_ma'] = data['volume'].rolling(window=self.bb_period).mean()
            data['high_volume'] = data['volume'] > data['volume_ma'] * 1.5

        current = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else current

        # 上軌突破：買入信號
        if (current['close'] > current['bb_upper'] and
            prev['close'] <= prev['bb_upper']):

            # 檢查成交量
            if not self.volume_filter or current.get('high_volume', True):
                signal = Signal(
                    symbol=self.config.symbols[0],
                    signal_type=SignalType.BUY,
                    strength=min(current['bb_position'], 1.0),
                    price=current['close'],
                    timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                    confidence=0.6,
                    metadata={
                        'bb_position': current['bb_position'],
                        'bb_upper': current['bb_upper'],
                        'bb_middle': current['bb_middle'],
                        'bb_lower': current['bb_lower'],
                        'action': 'breakout_upper'
                    }
                )
                signals.append(signal)

        # 下軌突破：賣出信號
        elif (current['close'] < current['bb_lower'] and
              prev['close'] >= prev['bb_lower']):

            # 檢查成交量
            if not self.volume_filter or current.get('high_volume', True):
                signal = Signal(
                    symbol=self.config.symbols[0],
                    signal_type=SignalType.SELL,
                    strength=min(1 - current['bb_position'], 1.0),
                    price=current['close'],
                    timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                    confidence=0.6,
                    metadata={
                        'bb_position': current['bb_position'],
                        'bb_upper': current['bb_upper'],
                        'bb_middle': current['bb_middle'],
                        'bb_lower': current['bb_lower'],
                        'action': 'breakout_lower'
                    }
                )
                signals.append(signal)

        # 回歸中軌：平倉信號
        elif (abs(current['bb_position'] - 0.5) < 0.1 and
              self.positions.get(self.config.symbols[0]) and
              self.positions[self.config.symbols[0]].quantity != 0):

            signal = Signal(
                symbol=self.config.symbols[0],
                signal_type=SignalType.CLOSE,
                strength=0.8,
                price=current['close'],
                timestamp=current.name if isinstance(current.name, datetime) else datetime.now(),
                confidence=0.5,
                metadata={
                    'bb_position': current['bb_position'],
                    'action': 'return_to_mean'
                }
            )
            signals.append(signal)

        return signals

    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """計算倉位大小"""
        base_size = portfolio_value * self.config.max_position_size
        return base_size * signal.strength / signal.price

class MomentumStrategy(QuantStrategyBase):
    """動量策略"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.lookback_period = self.parameters.get('lookback_period', 252)  # 1年
        self.holding_period = self.parameters.get('holding_period', 20)
        self.top_n = self.parameters.get('top_n', 5)
        self.universe_size = len(self.config.symbols)

    def initialize(self) -> bool:
        """初始化策略"""
        try:
            self.logger.info(
                f"初始化動量策略: 回看期={self.lookback_period}天, "
                f"持有期={self.holding_period}天, 選擇Top {self.top_n}"
            )
            return True
        except Exception as e:
            self.logger.error(f"初始化失敗: {str(e)}")
            return False

    def calculate_momentum_score(self, returns: pd.Series) -> float:
        """計算動量得分（年化收益率）"""
        if len(returns) < self.lookback_period:
            return 0.0

        # 使用最近回看期數據
        recent_returns = returns.tail(self.lookback_period)
        total_return = (1 + recent_returns).prod() - 1

        # 年化收益率
        annual_return = (1 + total_return) ** (252 / len(recent_returns)) - 1

        return annual_return

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信號"""
        signals = []

        # 計算每個標的的動量得分
        momentum_scores = {}
        for symbol in self.config.symbols:
            close_col = f'close_{symbol}'
            if close_col in data.columns:
                returns = data[close_col].pct_change().dropna()
                momentum_scores[symbol] = self.calculate_momentum_score(returns)

        # 排序並選擇前N個
        sorted_symbols = sorted(
            momentum_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 獲取當前時間
        current_time = data.index[-1] if isinstance(data.index[-1], datetime) else datetime.now()
        current_prices = {}
        for symbol in self.config.symbols:
            close_col = f'close_{symbol}'
            if close_col in data.columns:
                current_prices[symbol] = data[close_col].iloc[-1]

        # 買入前N個動量最好的標的
        for symbol, score in sorted_symbols[:self.top_n]:
            if score > 0:  # 只買入正動量的標的
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strength=min(score / 0.5, 1.0),  # 假設50%年化收益率為強信號
                    price=current_prices.get(symbol, 0),
                    timestamp=current_time,
                    confidence=0.6,
                    metadata={
                        'momentum_score': score,
                        'rank': sorted_symbols.index((symbol, score)) + 1,
                        'action': 'momentum_buy'
                    }
                )
                signals.append(signal)

        # 賣出動量差的標的（當前持有但不在前N）
        for symbol in self.config.symbols:
            position = self.positions.get(symbol)
            if position and position.quantity > 0:
                if symbol not in [s[0] for s in sorted_symbols[:self.top_n]]:
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        strength=0.8,
                        price=current_prices.get(symbol, 0),
                        timestamp=current_time,
                        confidence=0.5,
                        metadata={
                            'momentum_score': momentum_scores.get(symbol, 0),
                            'action': 'momentum_exit'
                        }
                    )
                    signals.append(signal)

        return signals

    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """計算倉位大小（等權重分配）"""
        base_size = portfolio_value * self.config.max_position_size / self.top_n
        return base_size / signal.price