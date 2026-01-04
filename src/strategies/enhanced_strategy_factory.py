"""
Enhanced Strategy Factory
Factory with all migrated strategies from legacy system
Phase 4.1 - 重構現有策略類型
"""

from typing import Dict, Any, Type, List, Optional
from uuid import UUID
import logging
from datetime import datetime

from .strategy_factory_v2 import (
    BaseStrategy, StrategyFactory, TechnicalStrategy,
    MomentumStrategy, VolumeStrategy, PortfolioStrategy,
    FundamentalStrategy
)
from .adapters.legacy_strategy_adapter import LegacyStrategyAdapter

logger = logging.getLogger(__name__)


class EnhancedTechnicalStrategy(TechnicalStrategy):
    """Enhanced technical strategy with all indicators"""

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate technical indicators"""
        import pandas as pd
        import numpy as np

        df = pd.DataFrame(data)
        indicators = {}

        # Moving Averages
        if 'ma' in [ind.get('type') for ind in self.indicators_config]:
            for ind_config in self.indicators_config:
                if ind_config['type'] == 'ma':
                    period = ind_config['parameters']['period']
                    ma_type = ind_config['parameters'].get('ma_type', 'sma')

                    if ma_type == 'sma':
                        ma_values = df['close'].rolling(window=period).mean()
                    elif ma_type == 'ema':
                        ma_values = df['close'].ewm(span=period).mean()
                    elif ma_type == 'wma':
                        weights = np.arange(1, period + 1)
                        ma_values = df['close'].rolling(window=period).apply(
                            lambda x: np.dot(x, weights) / weights.sum(), raw=True
                        )

                    indicators[f'ma_{period}_{ma_type}'] = ma_values.tolist()

        # RSI
        if 'rsi' in [ind.get('type') for ind in self.indicators_config]:
            for ind_config in self.indicators_config:
                if ind_config['type'] == 'rsi':
                    period = ind_config['parameters']['period']
                    delta = df['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    indicators[f'rsi_{period}'] = rsi.tolist()

        # MACD
        if 'macd' in [ind.get('type') for ind in self.indicators_config]:
            for ind_config in self.indicators_config:
                if ind_config['type'] == 'macd':
                    fast = ind_config['parameters']['fast']
                    slow = ind_config['parameters']['slow']
                    signal = ind_config['parameters']['signal']

                    ema_fast = df['close'].ewm(span=fast).mean()
                    ema_slow = df['close'].ewm(span=slow).mean()
                    macd_line = ema_fast - ema_slow
                    signal_line = macd_line.ewm(span=signal).mean()
                    histogram = macd_line - signal_line

                    indicators['macd'] = macd_line.tolist()
                    indicators['macd_signal'] = signal_line.tolist()
                    indicators['macd_histogram'] = histogram.tolist()

        # Bollinger Bands
        if 'bb' in [ind.get('type') for ind in self.indicators_config]:
            for ind_config in self.indicators_config:
                if ind_config['type'] == 'bb':
                    period = ind_config['parameters']['period']
                    std_dev = ind_config['parameters']['std_dev']

                    sma = df['close'].rolling(window=period).mean()
                    std = df['close'].rolling(window=period).std()
                    upper_band = sma + (std * std_dev)
                    lower_band = sma - (std * std_dev)

                    indicators['bb_upper'] = upper_band.tolist()
                    indicators['bb_middle'] = sma.tolist()
                    indicators['bb_lower'] = lower_band.tolist()
                    indicators['bb_width'] = ((upper_band - lower_band) / sma).tolist()

        return indicators

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trading signals based on indicators"""
        import pandas as pd

        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        # Generate signals based on configured rules
        for rule in self.config.get('signal_rules', []):
            if rule['condition'] == 'ma_crossover':
                signals.extend(self._generate_ma_crossover_signals(indicators, rule, df))
            elif rule['condition'] == 'rsi_extremes':
                signals.extend(self._generate_rsi_signals(indicators, rule, df))
            elif rule['condition'] == 'macd_crossover':
                signals.extend(self._generate_macd_signals(indicators, rule, df))
            elif rule['condition'] == 'bb_breakout':
                signals.extend(self._generate_bb_signals(indicators, rule, df))

        return signals

    def _generate_ma_crossover_signals(self, indicators: Dict, rule: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate MA crossover signals"""
        signals = []
        fast_ma_key = f"ma_{rule['fast_ma']}_sma"  # Assuming SMA for simplicity
        slow_ma_key = f"ma_{rule['slow_ma']}_sma"

        if fast_ma_key not in indicators or slow_ma_key not in indicators:
            return signals

        fast_ma = indicators[fast_ma_key]
        slow_ma = indicators[slow_ma_key]
        threshold = rule.get('threshold', 0)

        for i in range(1, len(fast_ma)):
            # Check for crossover
            prev_diff = fast_ma[i-1] - slow_ma[i-1]
            curr_diff = fast_ma[i] - slow_ma[i]

            # Golden cross (fast crosses above slow)
            if prev_diff <= threshold and curr_diff > threshold:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': min(abs(curr_diff) / threshold if threshold else 1, 1),
                    'metadata': {
                        'strategy': 'ma_crossover',
                        'fast_ma': fast_ma[i],
                        'slow_ma': slow_ma[i],
                        'diff': curr_diff
                    }
                })

            # Death cross (fast crosses below slow)
            elif prev_diff >= -threshold and curr_diff < -threshold:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': min(abs(curr_diff) / threshold if threshold else 1, 1),
                    'metadata': {
                        'strategy': 'ma_crossover',
                        'fast_ma': fast_ma[i],
                        'slow_ma': slow_ma[i],
                        'diff': curr_diff
                    }
                })

        return signals

    def _generate_rsi_signals(self, indicators: Dict, rule: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate RSI signals"""
        signals = []
        overbought = rule.get('overbought', 70)
        oversold = rule.get('oversold', 30)

        rsi_key = f"rsi_{self.parameters.get('rsi_period', 14)}"
        if rsi_key not in indicators:
            return signals

        rsi_values = indicators[rsi_key]

        for i in range(1, len(rsi_values)):
            # Overbought to normal (sell signal)
            if rsi_values[i-1] >= overbought and rsi_values[i] < overbought:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': (rsi_values[i-1] - overbought) / (100 - overbought),
                    'metadata': {
                        'strategy': 'rsi',
                        'rsi': rsi_values[i],
                        'threshold': overbought
                    }
                })

            # Oversold to normal (buy signal)
            elif rsi_values[i-1] <= oversold and rsi_values[i] > oversold:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': (oversold - rsi_values[i-1]) / oversold,
                    'metadata': {
                        'strategy': 'rsi',
                        'rsi': rsi_values[i],
                        'threshold': oversold
                    }
                })

        return signals

    def _generate_macd_signals(self, indicators: Dict, rule: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate MACD signals"""
        signals = []

        if 'macd' not in indicators or 'macd_signal' not in indicators:
            return signals

        macd_line = indicators['macd']
        signal_line = indicators['macd_signal']

        for i in range(1, len(macd_line)):
            # MACD crosses above signal line (buy)
            if macd_line[i-1] <= signal_line[i-1] and macd_line[i] > signal_line[i]:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': min(abs(macd_line[i] - signal_line[i]) * 10, 1),
                    'metadata': {
                        'strategy': 'macd',
                        'macd': macd_line[i],
                        'signal': signal_line[i],
                        'histogram': indicators['macd_histogram'][i] if 'macd_histogram' in indicators else None
                    }
                })

            # MACD crosses below signal line (sell)
            elif macd_line[i-1] >= signal_line[i-1] and macd_line[i] < signal_line[i]:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': min(abs(macd_line[i] - signal_line[i]) * 10, 1),
                    'metadata': {
                        'strategy': 'macd',
                        'macd': macd_line[i],
                        'signal': signal_line[i],
                        'histogram': indicators['macd_histogram'][i] if 'macd_histogram' in indicators else None
                    }
                })

        return signals

    def _generate_bb_signals(self, indicators: Dict, rule: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate Bollinger Bands signals"""
        signals = []

        required_keys = ['bb_upper', 'bb_lower', 'close']
        if not all(k in indicators for k in required_keys):
            return signals

        upper_band = indicators['bb_upper']
        lower_band = indicators['bb_lower']
        prices = df['close'].tolist()

        for i in range(1, len(prices)):
            # Price breaks above upper band (sell - overbought)
            if prices[i-1] <= upper_band[i-1] and prices[i] > upper_band[i]:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': (prices[i] - upper_band[i]) / upper_band[i],
                    'metadata': {
                        'strategy': 'bollinger_bands',
                        'price': prices[i],
                        'upper_band': upper_band[i],
                        'lower_band': lower_band[i]
                    }
                })

            # Price breaks below lower band (buy - oversold)
            elif prices[i-1] >= lower_band[i-1] and prices[i] < lower_band[i]:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': (lower_band[i] - prices[i]) / lower_band[i],
                    'metadata': {
                        'strategy': 'bollinger_bands',
                        'price': prices[i],
                        'upper_band': upper_band[i],
                        'lower_band': lower_band[i]
                    }
                })

        return signals


class EnhancedMomentumStrategy(MomentumStrategy):
    """Enhanced momentum strategy with ADX, SAR, Aroon"""

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate momentum indicators"""
        import pandas as pd
        import numpy as np

        df = pd.DataFrame(data)
        indicators = {}

        # ADX
        if 'adx' in self.config:
            period = self.config.get('adx_period', 14)
            high, low, close = df['high'], df['low'], df['close']

            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # Directional Movement
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low

            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

            # Smoothed values
            tr_smooth = tr.rolling(window=period).mean()
            plus_di = (pd.Series(plus_dm).rolling(window=period).sum() /
                      tr_smooth.rolling(window=period).sum()) * 100
            minus_di = (pd.Series(minus_dm).rolling(window=period).sum() /
                       tr_smooth.rolling(window=period).sum()) * 100

            # ADX
            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
            adx = dx.rolling(window=period).mean()

            indicators['adx'] = adx.tolist()
            indicators['plus_di'] = plus_di.tolist()
            indicators['minus_di'] = minus_di.tolist()

        # Aroon
        if 'aroon' in self.config:
            period = self.config.get('aroon_period', 25)
            high, low = df['high'], df['low']

            # Aroon Up
            high_periods = high.rolling(window=period + 1).apply(
                lambda x: x.argmax(), raw=True
            )
            aroon_up = ((period - high_periods) / period) * 100

            # Aroon Down
            low_periods = low.rolling(window=period + 1).apply(
                lambda x: x.argmin(), raw=True
            )
            aroon_down = ((period - low_periods) / period) * 100

            # Aroon Oscillator
            aroon_oscillator = aroon_up - aroon_down

            indicators['aroon_up'] = aroon_up.tolist()
            indicators['aroon_down'] = aroon_down.tolist()
            indicators['aroon_oscillator'] = aroon_oscillator.tolist()

        return indicators

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate momentum signals"""
        import pandas as pd

        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        # ADX signals
        if 'adx' in indicators:
            signals.extend(self._generate_adx_signals(indicators, df))

        # Aroon signals
        if 'aroon_up' in indicators:
            signals.extend(self._generate_aroon_signals(indicators, df))

        return signals

    def _generate_adx_signals(self, indicators: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate ADX-based signals"""
        signals = []
        threshold = self.config.get('adx_trend_threshold', 25)

        adx_values = indicators['adx']
        plus_di = indicators['plus_di']
        minus_di = indicators['minus_di']

        for i in range(1, len(adx_values)):
            if adx_values[i] > threshold:
                # Bullish trend
                if plus_di[i-1] <= minus_di[i-1] and plus_di[i] > minus_di[i]:
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'buy',
                        'strength': min(adx_values[i] / 50, 1),
                        'metadata': {
                            'strategy': 'adx',
                            'adx': adx_values[i],
                            'plus_di': plus_di[i],
                            'minus_di': minus_di[i]
                        }
                    })

                # Bearish trend
                elif plus_di[i-1] >= minus_di[i-1] and plus_di[i] < minus_di[i]:
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'sell',
                        'strength': min(adx_values[i] / 50, 1),
                        'metadata': {
                            'strategy': 'adx',
                            'adx': adx_values[i],
                            'plus_di': plus_di[i],
                            'minus_di': minus_di[i]
                        }
                    })

        return signals

    def _generate_aroon_signals(self, indicators: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate Aroon-based signals"""
        signals = []

        aroon_up = indicators['aroon_up']
        aroon_down = indicators['aroon_down']
        oscillator = indicators['aroon_oscillator']

        for i in range(1, len(oscillator)):
            # Bullish crossover
            if oscillator[i-1] <= 0 and oscillator[i] > 0:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': min(abs(oscillator[i]) / 100, 1),
                    'metadata': {
                        'strategy': 'aroon',
                        'aroon_up': aroon_up[i],
                        'aroon_down': aroon_down[i],
                        'oscillator': oscillator[i]
                    }
                })

            # Bearish crossover
            elif oscillator[i-1] >= 0 and oscillator[i] < 0:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': min(abs(oscillator[i]) / 100, 1),
                    'metadata': {
                        'strategy': 'aroon',
                        'aroon_up': aroon_up[i],
                        'aroon_down': aroon_down[i],
                        'oscillator': oscillator[i]
                    }
                })

        return signals


class EnhancedVolumeStrategy(VolumeStrategy):
    """Enhanced volume strategy with VPT, OBV, VWAP, MFI"""

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate volume indicators"""
        import pandas as pd
        import numpy as np

        df = pd.DataFrame(data)
        indicators = {}

        # On-Balance Volume (OBV)
        if 'obv' in self.config:
            price_change = df['close'].diff()
            obv = np.where(price_change > 0, df['volume'],
                         np.where(price_change < 0, -df['volume'], 0)).cumsum()
            indicators['obv'] = obv.tolist()

        # Volume Price Trend (VPT)
        if 'vpt' in self.config:
            price_change_pct = df['close'].pct_change()
            vpt = (price_change_pct * df['volume']).cumsum()
            indicators['vpt'] = vpt.tolist()

        # VWAP
        if 'vwap' in self.config:
            period = self.config.get('vwap_period', 'daily')
            if period == 'daily':
                # Reset VWAP daily
                df['date'] = df.index.date
                vwap = df.groupby('date').apply(
                    lambda x: (x['close'] * x['volume']).cumsum() / x['volume'].cumsum()
                ).reset_index(level=0, drop=True)
            else:
                # Simple rolling VWAP
                window = int(period.replace('d', '')) if 'd' in period else 20
                vwap = (df['close'] * df['volume']).rolling(window=window).sum() / \
                       df['volume'].rolling(window=window).sum()

            indicators['vwap'] = vwap.tolist()

        # Money Flow Index (MFI)
        if 'mfi' in self.config:
            period = self.config.get('mfi_period', 14)
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            raw_money_flow = typical_price * df['volume']

            # Positive and Negative Money Flow
            positive_flow = raw_money_flow.where(typical_price.diff() > 0, 0)
            negative_flow = raw_money_flow.where(typical_price.diff() < 0, 0)

            # Money Flow Index
            positive_sum = positive_flow.rolling(window=period).sum()
            negative_sum = negative_flow.rolling(window=period).sum()
            mfi = 100 - (100 / (1 + positive_sum / negative_sum))

            indicators['mfi'] = mfi.tolist()

        return indicators

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate volume-based signals"""
        import pandas as pd

        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        # OBV signals (divergence detection)
        if 'obv' in indicators:
            signals.extend(self._generate_obv_signals(indicators, df))

        # VPT signals
        if 'vpt' in indicators:
            signals.extend(self._generate_vpt_signals(indicators, df))

        # MFI signals
        if 'mfi' in indicators:
            signals.extend(self._generate_mfi_signals(indicators, df))

        # VWAP signals
        if 'vwap' in indicators:
            signals.extend(self._generate_vwap_signals(indicators, df))

        return signals

    def _generate_obv_signals(self, indicators: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate OBV divergence signals"""
        signals = []
        obv = indicators['obv']
        prices = df['close'].tolist()

        # Simple divergence detection
        for i in range(20, len(obv)):  # Need at least 20 periods for trend
            price_trend = prices[i] > prices[i-20]
            obv_trend = obv[i] > obv[i-20]

            # Bearish divergence (price up, OBV down)
            if price_trend and not obv_trend:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': 0.7,
                    'metadata': {
                        'strategy': 'obv_divergence',
                        'divergence_type': 'bearish',
                        'obv': obv[i],
                        'price': prices[i]
                    }
                })

            # Bullish divergence (price down, OBV up)
            elif not price_trend and obv_trend:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': 0.7,
                    'metadata': {
                        'strategy': 'obv_divergence',
                        'divergence_type': 'bullish',
                        'obv': obv[i],
                        'price': prices[i]
                    }
                })

        return signals

    def _generate_mfi_signals(self, indicators: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate MFI signals"""
        signals = []
        overbought = self.config.get('mfi_overbought', 80)
        oversold = self.config.get('mfi_oversold', 20)

        mfi_values = indicators['mfi']

        for i in range(1, len(mfi_values)):
            # Overbought to normal (sell)
            if mfi_values[i-1] >= overbought and mfi_values[i] < overbought:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': (mfi_values[i-1] - overbought) / (100 - overbought),
                    'metadata': {
                        'strategy': 'mfi',
                        'mfi': mfi_values[i],
                        'threshold': overbought
                    }
                })

            # Oversold to normal (buy)
            elif mfi_values[i-1] <= oversold and mfi_values[i] > oversold:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': (oversold - mfi_values[i-1]) / oversold,
                    'metadata': {
                        'strategy': 'mfi',
                        'mfi': mfi_values[i],
                        'threshold': oversold
                    }
                })

        return signals

    def _generate_vwap_signals(self, indicators: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate VWAP mean reversion signals"""
        signals = []
        vwap = indicators['vwap']
        prices = df['close'].tolist()

        for i in range(1, len(vwap)):
            deviation = (prices[i] - vwap[i]) / vwap[i]

            # Price significantly above VWAP (sell - overvalued)
            if deviation > 0.02:  # 2% above VWAP
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': min(abs(deviation) * 10, 1),
                    'metadata': {
                        'strategy': 'vwap_mean_reversion',
                        'price': prices[i],
                        'vwap': vwap[i],
                        'deviation': deviation
                    }
                })

            # Price significantly below VWAP (buy - undervalued)
            elif deviation < -0.02:  # 2% below VWAP
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': min(abs(deviation) * 10, 1),
                    'metadata': {
                        'strategy': 'vwap_mean_reversion',
                        'price': prices[i],
                        'vwap': vwap[i],
                        'deviation': deviation
                    }
                })

        return signals

    def _generate_vpt_signals(self, indicators: Dict, df: pd.DataFrame) -> List[Dict]:
        """Generate VPT trend signals"""
        signals = []
        vpt = indicators['vpt']

        # Trend detection
        for i in range(10, len(vpt)):
            # Calculate trend
            vpt_slope = (vpt[i] - vpt[i-10]) / 10

            # Strong uptrend
            if vpt_slope > 1000:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': min(vpt_slope / 10000, 1),
                    'metadata': {
                        'strategy': 'vpt_trend',
                        'vpt': vpt[i],
                        'slope': vpt_slope
                    }
                })

            # Strong downtrend
            elif vpt_slope < -1000:
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': min(abs(vpt_slope) / 10000, 1),
                    'metadata': {
                        'strategy': 'vpt_trend',
                        'vpt': vpt[i],
                        'slope': vpt_slope
                    }
                })

        return signals


# Register enhanced strategies with factory
class EnhancedStrategyFactory(StrategyFactory):
    """Enhanced factory with all migrated strategies"""

    @classmethod
    def _register_enhanced_strategies(cls):
        """Register all enhanced strategy implementations"""
        # Override technical strategy
        cls._strategy_registry['technical'] = EnhancedTechnicalStrategy

        # Override momentum strategy
        cls._strategy_registry['momentum'] = EnhancedMomentumStrategy

        # Override volume strategy
        cls._strategy_registry['volume'] = EnhancedVolumeStrategy

    @classmethod
    def create_legacy_strategy(cls, legacy_type: str, legacy_config: Dict[str, Any]) -> BaseStrategy:
        """Create strategy from legacy configuration"""
        return LegacyStrategyAdapter.migrate_strategy_config(legacy_type, legacy_config)

    @classmethod
    def get_available_legacy_strategies(cls) -> List[str]:
        """Get list of migratable legacy strategies"""
        return [
            'ma_crossover',
            'rsi',
            'macd',
            'bollinger_bands',
            'adx',
            'sar',
            'aroon',
            'vpt',
            'obv',
            'vwap',
            'mfi'
        ]

    @classmethod
    def migrate_all_legacy_strategies(cls, db_session) -> Dict[str, Any]:
        """Migrate all legacy strategies in database"""
        from .adapters.legacy_strategy_adapter import StrategyMigrationService

        migration_service = StrategyMigrationService(db_session)
        return migration_service.migrate_all_strategies()


# Initialize enhanced factory
EnhancedStrategyFactory._register_enhanced_strategies()