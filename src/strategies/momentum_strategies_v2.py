"""
Momentum Strategies v2.0
Complete implementation of momentum-based trading strategies
Phase 4.2 - 實現動量和成交量策略
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

from .strategy_factory_v2 import BaseStrategy

logger = logging.getLogger(__name__)


class ADXMomentumStrategy(BaseStrategy):
    """ADX (Average Directional Index) Momentum Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.period = config.get('adx_period', 14)
        self.trend_threshold = config.get('trend_threshold', 25)
        self.strength_threshold = config.get('strength_threshold', 40)

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate ADX and related indicators"""
        df = pd.DataFrame(data)
        indicators = {}

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
        tr_smooth = tr.rolling(window=self.period).mean()
        plus_di = (pd.Series(plus_dm).rolling(window=self.period).sum() /
                  tr_smooth.rolling(window=self.period).sum()) * 100
        minus_di = (pd.Series(minus_dm).rolling(window=self.period).sum() /
                   tr_smooth.rolling(window=self.period).sum()) * 100

        # ADX
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        adx = dx.rolling(window=self.period).mean()

        # Trend strength classification
        trend_strength = pd.cut(
            adx,
            bins=[0, 20, 25, 40, 60, 100],
            labels=['very_weak', 'weak', 'moderate', 'strong', 'very_strong']
        )

        indicators['adx'] = adx.tolist()
        indicators['plus_di'] = plus_di.tolist()
        indicators['minus_di'] = minus_di.tolist()
        indicators['trend_strength'] = trend_strength.tolist()

        # ADX momentum
        adx_momentum = adx.diff()
        indicators['adx_momentum'] = adx_momentum.tolist()

        # DI spread
        di_spread = plus_di - minus_di
        indicators['di_spread'] = di_spread.tolist()

        return indicators

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate ADX-based trading signals"""
        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        adx_values = indicators['adx']
        plus_di = indicators['plus_di']
        minus_di = indicators['minus_di']
        adx_momentum = indicators['adx_momentum']

        for i in range(2, len(adx_values)):
            current_adx = adx_values[i]
            current_plus_di = plus_di[i]
            current_minus_di = minus_di[i]

            # Strong trend conditions
            if current_adx > self.trend_threshold:
                # Bullish signal: +DI crosses above -DI in strong trend
                if (current_plus_di > current_minus_di and
                    plus_di[i-1] <= minus_di[i-1] and
                    adx_momentum[i] > 0):  # ADX increasing
                    strength = self._calculate_signal_strength(
                        current_adx, current_plus_di, current_minus_di
                    )
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'buy',
                        'strength': strength,
                        'price': df['close'].iloc[i],
                        'metadata': {
                            'strategy': 'adx_momentum',
                            'adx': current_adx,
                            'plus_di': current_plus_di,
                            'minus_di': current_minus_di,
                            'trend_strength': self._get_trend_strength_label(current_adx),
                            'signal_type': 'di_crossover_bullish'
                        }
                    })

                # Bearish signal: -DI crosses above +DI in strong trend
                elif (current_minus_di > current_plus_di and
                      minus_di[i-1] <= plus_di[i-1] and
                      adx_momentum[i] < 0):  # ADX decreasing
                    strength = self._calculate_signal_strength(
                        current_adx, current_minus_di, current_plus_di
                    )
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'sell',
                        'strength': strength,
                        'price': df['close'].iloc[i],
                        'metadata': {
                            'strategy': 'adx_momentum',
                            'adx': current_adx,
                            'plus_di': current_plus_di,
                            'minus_di': current_minus_di,
                            'trend_strength': self._get_trend_strength_label(current_adx),
                            'signal_type': 'di_crossover_bearish'
                        }
                    })

        return signals

    def _calculate_signal_strength(self, adx: float, di1: float, di2: float) -> float:
        """Calculate signal strength based on ADX and DI values"""
        # Base strength from ADX
        adx_strength = min(adx / 60, 1)  # Normalize assuming 60 as very strong

        # Additional strength from DI separation
        di_separation = abs(di1 - di2) / 100
        separation_strength = min(di_separation, 1)

        # Combined strength
        combined_strength = (adx_strength * 0.6) + (separation_strength * 0.4)
        return min(combined_strength, 1)

    def _get_trend_strength_label(self, adx: float) -> str:
        """Get trend strength label"""
        if adx < 20:
            return 'very_weak'
        elif adx < 25:
            return 'weak'
        elif adx < 40:
            return 'moderate'
        elif adx < 60:
            return 'strong'
        else:
            return 'very_strong'


class SARMomentumStrategy(BaseStrategy):
    """Parabolic SAR Momentum Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.acceleration = config.get('acceleration', 0.02)
        self.maximum = config.get('maximum', 0.2)
        self.af_increment = config.get('af_increment', 0.02)

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Parabolic SAR indicators"""
        df = pd.DataFrame(data)
        high, low, close = df['high'], df['low'], df['close']

        # Initialize SAR values
        length = len(df)
        psar = np.zeros(length)
        ep = np.zeros(length)
        af = np.zeros(length)
        trend = np.zeros(length)

        # Initialize
        psar[0] = low.iloc[0]
        ep[0] = high.iloc[0]
        af[0] = self.acceleration
        trend[0] = 1  # 1 for uptrend, -1 for downtrend

        for i in range(1, length):
            if trend[i-1] == 1:  # Uptrend
                psar[i] = psar[i-1] + af[i-1] * (ep[i-1] - psar[i-1])

                # Check for stop and reverse
                if low.iloc[i] < psar[i]:
                    trend[i] = -1
                    psar[i] = ep[i-1]
                    ep[i] = low.iloc[i]
                    af[i] = self.acceleration
                else:
                    trend[i] = 1
                    # Update extreme point
                    if high.iloc[i] > ep[i-1]:
                        ep[i] = high.iloc[i]
                        af[i] = min(af[i-1] + self.af_increment, self.maximum)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]

                    # Update SAR with previous lows
                    if i >= 2:
                        psar[i] = max(psar[i], low.iloc[i-1], low.iloc[i-2])

            else:  # Downtrend
                psar[i] = psar[i-1] + af[i-1] * (ep[i-1] - psar[i-1])

                # Check for stop and reverse
                if high.iloc[i] > psar[i]:
                    trend[i] = 1
                    psar[i] = ep[i-1]
                    ep[i] = high.iloc[i]
                    af[i] = self.acceleration
                else:
                    trend[i] = -1
                    # Update extreme point
                    if low.iloc[i] < ep[i-1]:
                        ep[i] = low.iloc[i]
                        af[i] = min(af[i-1] + self.af_increment, self.maximum)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]

                    # Update SAR with previous highs
                    if i >= 2:
                        psar[i] = min(psar[i], high.iloc[i-1], high.iloc[i-2])

        # Calculate SAR distance from price
        price_distance = (close - psar) / close

        return {
            'sar': psar.tolist(),
            'trend': trend.tolist(),
            'acceleration_factor': af.tolist(),
            'price_distance': price_distance.tolist()
        }

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Parabolic SAR signals"""
        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        sar_values = indicators['sar']
        trend = indicators['trend']
        acceleration_factor = indicators['acceleration_factor']

        for i in range(1, len(sar_values)):
            # Trend reversal signal
            if trend[i] != trend[i-1]:
                signal_type = 'buy' if trend[i] == 1 else 'sell'
                strength = min(acceleration_factor[i] / self.maximum, 1)

                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': signal_type,
                    'strength': strength,
                    'price': df['close'].iloc[i],
                    'sar': sar_values[i],
                    'metadata': {
                        'strategy': 'sar_momentum',
                        'trend': 'uptrend' if trend[i] == 1 else 'downtrend',
                        'acceleration_factor': acceleration_factor[i],
                        'signal_type': 'trend_reversal'
                    }
                })

        return signals


class AroonMomentumStrategy(BaseStrategy):
    """Aroon Momentum Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.period = config.get('period', 25)
        self.bullish_threshold = config.get('bullish_threshold', 70)
        self.bearish_threshold = config.get('bearish_threshold', 30)

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Aroon indicators"""
        df = pd.DataFrame(data)
        high, low = df['high'], df['low']

        # Aroon Up - measures uptrend strength
        def calculate_aroon_up(series):
            return series.rolling(window=self.period + 1).apply(
                lambda x: (self.period - x.argmax()) / self.period * 100,
                raw=True
            )

        # Aroon Down - measures downtrend strength
        def calculate_aroon_down(series):
            return series.rolling(window=self.period + 1).apply(
                lambda x: (self.period - x.argmin()) / self.period * 100,
                raw=True
            )

        aroon_up = calculate_aroon_up(high)
        aroon_down = calculate_aroon_down(low)

        # Aroon Oscillator
        aroon_oscillator = aroon_up - aroon_down

        # Aroon Signal (crossover indicator)
        aroon_signal = np.where(
            (aroon_up > self.bullish_threshold) & (aroon_down < self.bearish_threshold), 1,
            np.where(
                (aroon_down > self.bullish_threshold) & (aroon_up < self.bearish_threshold), -1, 0
            )
        )

        return {
            'aroon_up': aroon_up.tolist(),
            'aroon_down': aroon_down.tolist(),
            'aroon_oscillator': aroon_oscillator.tolist(),
            'aroon_signal': aroon_signal.tolist()
        }

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Aroon-based signals"""
        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        aroon_up = indicators['aroon_up']
        aroon_down = indicators['aroon_down']
        aroon_oscillator = indicators['aroon_oscillator']
        aroon_signal = indicators['aroon_signal']

        for i in range(1, len(aroon_signal)):
            # Strong trend signal
            if aroon_signal[i] != aroon_signal[i-1] and aroon_signal[i] != 0:
                signal_type = 'buy' if aroon_signal[i] == 1 else 'sell'
                strength = abs(aroon_oscillator[i]) / 100

                # Additional confirmation based on Aroon values
                if signal_type == 'buy':
                    confirmation = (aroon_up[i] > self.bullish_threshold and
                                  aroon_down[i] < self.bearish_threshold)
                else:
                    confirmation = (aroon_down[i] > self.bullish_threshold and
                                  aroon_up[i] < self.bearish_threshold)

                if confirmation:
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': signal_type,
                        'strength': min(strength, 1),
                        'price': df['close'].iloc[i],
                        'metadata': {
                            'strategy': 'aroon_momentum',
                            'aroon_up': aroon_up[i],
                            'aroon_down': aroon_down[i],
                            'aroon_oscillator': aroon_oscillator[i],
                            'signal_type': 'strong_trend'
                        }
                    })

            # Crossover signal (Aroon Oscillator crosses zero)
            elif aroon_oscillator[i-1] <= 0 and aroon_oscillator[i] > 0:
                # Bullish crossover
                strength = min(aroon_up[i] / 100, 1)
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': strength,
                    'price': df['close'].iloc[i],
                    'metadata': {
                        'strategy': 'aroon_momentum',
                        'aroon_up': aroon_up[i],
                        'aroon_down': aroon_down[i],
                        'aroon_oscillator': aroon_oscillator[i],
                        'signal_type': 'oscillator_crossover_bullish'
                    }
                })

            elif aroon_oscillator[i-1] >= 0 and aroon_oscillator[i] < 0:
                # Bearish crossover
                strength = min(aroon_down[i] / 100, 1)
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': strength,
                    'price': df['close'].iloc[i],
                    'metadata': {
                        'strategy': 'aroon_momentum',
                        'aroon_up': aroon_up[i],
                        'aroon_down': aroon_down[i],
                        'aroon_oscillator': aroon_oscillator[i],
                        'signal_type': 'oscillator_crossover_bearish'
                    }
                })

        return signals


class CompositeMomentumStrategy(BaseStrategy):
    """Composite strategy combining multiple momentum indicators"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.indicators = config.get('indicators', ['adx', 'sar', 'aroon'])
        self.weights = config.get('weights', {'adx': 0.4, 'sar': 0.3, 'aroon': 0.3})
        self.consensus_threshold = config.get('consensus_threshold', 0.6)

        # Initialize sub-strategies
        self.sub_strategies = {}
        if 'adx' in self.indicators:
            self.sub_strategies['adx'] = ADXMomentumStrategy(config.get('adx_config', {}))
        if 'sar' in self.indicators:
            self.sub_strategies['sar'] = SARMomentumStrategy(config.get('sar_config', {}))
        if 'aroon' in self.indicators:
            self.sub_strategies['aroon'] = AroonMomentumStrategy(config.get('aroon_config', {}))

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all momentum indicators"""
        all_indicators = {}

        for indicator_name, strategy in self.sub_strategies.items():
            try:
                indicators = strategy.calculate_indicators(data)
                for key, value in indicators.items():
                    all_indicators[f"{indicator_name}_{key}"] = value
            except Exception as e:
                logger.error(f"Error calculating {indicator_name}: {e}")

        # Calculate composite momentum score
        composite_score = self._calculate_composite_score(all_indicators)
        all_indicators['composite_momentum_score'] = composite_score

        return all_indicators

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate composite momentum signals"""
        all_signals = []
        signal_votes = []

        # Collect signals from all sub-strategies
        for indicator_name, strategy in self.sub_strategies.items():
            try:
                signals = strategy.generate_signals(data)
                all_signals.extend(signals)

                # Count votes for consensus
                for signal in signals:
                    vote = {
                        'type': signal['type'],
                        'weight': self.weights.get(indicator_name, 1),
                        'strength': signal['strength'],
                        'timestamp': signal['timestamp']
                    }
                    signal_votes.append(vote)
            except Exception as e:
                logger.error(f"Error generating signals for {indicator_name}: {e}")

        # Generate consensus signals
        consensus_signals = self._generate_consensus_signals(signal_votes, data)
        all_signals.extend(consensus_signals)

        # Remove duplicate signals (same timestamp and type)
        unique_signals = self._deduplicate_signals(all_signals)

        return unique_signals

    def _calculate_composite_score(self, indicators: Dict[str, Any]) -> List[float]:
        """Calculate composite momentum score"""
        scores = []

        # Initialize with zeros
        if not indicators:
            return scores

        length = max(len(v) for v in indicators.values() if isinstance(v, list))
        composite_scores = [0.0] * length

        for indicator_name, strategy in self.sub_strategies.items():
            weight = self.weights.get(indicator_name, 0)

            if indicator_name == 'adx' and 'adx' in indicators:
                adx_values = indicators['adx']
                # Normalize ADX to 0-1 range (assuming max 100)
                for i, val in enumerate(adx_values[:length]):
                    composite_scores[i] += (val / 100) * weight

            elif indicator_name == 'sar' and 'trend' in indicators:
                trend_values = indicators['trend']
                for i, val in enumerate(trend_values[:length]):
                    composite_scores[i] += val * weight

            elif indicator_name == 'aroon' and 'aroon_oscillator' in indicators:
                oscillator_values = indicators['aroon_oscillator']
                for i, val in enumerate(oscillator_values[:length]):
                    # Normalize oscillator to 0-1 range (-100 to 100)
                    composite_scores[i] += ((val + 100) / 200) * weight

        return composite_scores

    def _generate_consensus_signals(self, votes: List[Dict], data: Dict[str, Any]) -> List[Dict]:
        """Generate consensus signals from voting"""
        if not votes:
            return []

        df = pd.DataFrame(data)
        consensus_signals = []

        # Group votes by timestamp
        vote_groups = {}
        for vote in votes:
            timestamp = vote['timestamp']
            if timestamp not in vote_groups:
                vote_groups[timestamp] = {'buy': 0, 'sell': 0, 'buy_strength': [], 'sell_strength': []}

            vote_groups[timestamp][vote['type']] += vote['weight']
            if vote['type'] == 'buy':
                vote_groups[timestamp]['buy_strength'].append(vote['strength'] * vote['weight'])
            else:
                vote_groups[timestamp]['sell_strength'].append(vote['strength'] * vote['weight'])

        # Generate consensus signals
        for timestamp, group in vote_groups.items():
            total_weight = group['buy'] + group['sell']
            if total_weight == 0:
                continue

            buy_ratio = group['buy'] / total_weight
            sell_ratio = group['sell'] / total_weight

            # Generate signal if consensus threshold is met
            if buy_ratio >= self.consensus_threshold:
                avg_strength = np.mean(group['buy_strength']) if group['buy_strength'] else 0
                consensus_signals.append({
                    'timestamp': timestamp,
                    'type': 'buy',
                    'strength': min(avg_strength, 1),
                    'price': self._get_price_at_timestamp(df, timestamp),
                    'metadata': {
                        'strategy': 'composite_momentum',
                        'consensus': buy_ratio,
                        'votes': group['buy'],
                        'signal_type': 'consensus_buy'
                    }
                })
            elif sell_ratio >= self.consensus_threshold:
                avg_strength = np.mean(group['sell_strength']) if group['sell_strength'] else 0
                consensus_signals.append({
                    'timestamp': timestamp,
                    'type': 'sell',
                    'strength': min(avg_strength, 1),
                    'price': self._get_price_at_timestamp(df, timestamp),
                    'metadata': {
                        'strategy': 'composite_momentum',
                        'consensus': sell_ratio,
                        'votes': group['sell'],
                        'signal_type': 'consensus_sell'
                    }
                })

        return consensus_signals

    def _deduplicate_signals(self, signals: List[Dict]) -> List[Dict]:
        """Remove duplicate signals with same timestamp and type"""
        unique_signals = []
        seen = set()

        for signal in sorted(signals, key=lambda x: (x['timestamp'], x['type'])):
            key = (signal['timestamp'], signal['type'])
            if key not in seen:
                unique_signals.append(signal)
                seen.add(key)

        return unique_signals

    def _get_price_at_timestamp(self, df: pd.DataFrame, timestamp: str) -> float:
        """Get price at specific timestamp"""
        try:
            dt = pd.to_datetime(timestamp)
            # Find closest price
            closest_idx = df.index.get_indexer([dt], method='nearest')[0]
            return df['close'].iloc[closest_idx]
        except:
            return 0.0