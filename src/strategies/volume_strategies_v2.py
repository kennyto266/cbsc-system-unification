"""
Volume Strategies v2.0
Complete implementation of volume-based trading strategies
Phase 4.2 - 實現動量和成交量策略
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

from .strategy_factory_v2 import BaseStrategy

logger = logging.getLogger(__name__)


class VPTStrategy(BaseStrategy):
    """Volume Price Trend (VPT) Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ma_period = config.get('ma_period', 20)
        self.signal_threshold = config.get('signal_threshold', 0.02)
        self.volume_multiplier = config.get('volume_multiplier', 1.5)

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate VPT and related indicators"""
        df = pd.DataFrame(data)

        # Calculate VPT
        price_change_pct = df['close'].pct_change()
        vpt = (price_change_pct * df['volume']).cumsum()

        # Calculate VPT moving average
        vpt_ma = vpt.rolling(window=self.ma_period).mean()

        # Calculate VPT deviation from MA
        vpt_deviation = (vpt - vpt_ma) / vpt_ma

        # Volume confirmation
        volume_ma = df['volume'].rolling(window=self.ma_period).mean()
        volume_ratio = df['volume'] / volume_ma

        # VPT rate of change
        vpt_roc = vpt.pct_change(periods=self.ma_period)

        return {
            'vpt': vpt.tolist(),
            'vpt_ma': vpt_ma.tolist(),
            'vpt_deviation': vpt_deviation.tolist(),
            'volume_ratio': volume_ratio.tolist(),
            'vpt_roc': vpt_roc.tolist()
        }

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate VPT-based signals"""
        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        vpt = indicators['vpt']
        vpt_deviation = indicators['vpt_deviation']
        volume_ratio = indicators['volume_ratio']
        vpt_roc = indicators['vpt_roc']

        for i in range(self.ma_period, len(vpt)):
            current_vpt = vpt[i]
            current_deviation = vpt_deviation[i]
            current_volume_ratio = volume_ratio[i]
            current_roc = vpt_roc[i]

            # Strong buy signal: VPT positive deviation with high volume
            if (current_deviation > self.signal_threshold and
                current_volume_ratio > self.volume_multiplier and
                current_roc > 0):
                strength = min(
                    (current_deviation * current_volume_ratio * (1 + current_roc)) / 2,
                    1
                )
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'buy',
                    'strength': strength,
                    'price': df['close'].iloc[i],
                    'metadata': {
                        'strategy': 'vpt',
                        'vpt': current_vpt,
                        'deviation': current_deviation,
                        'volume_ratio': current_volume_ratio,
                        'roc': current_roc,
                        'signal_type': 'strong_trend_buy'
                    }
                })

            # Strong sell signal: VPT negative deviation with high volume
            elif (current_deviation < -self.signal_threshold and
                  current_volume_ratio > self.volume_multiplier and
                  current_roc < 0):
                strength = min(
                    (abs(current_deviation) * current_volume_ratio * (1 + abs(current_roc))) / 2,
                    1
                )
                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': 'sell',
                    'strength': strength,
                    'price': df['close'].iloc[i],
                    'metadata': {
                        'strategy': 'vpt',
                        'vpt': current_vpt,
                        'deviation': current_deviation,
                        'volume_ratio': current_volume_ratio,
                        'roc': current_roc,
                        'signal_type': 'strong_trend_sell'
                    }
                })

            # Weak signals for VPT crossovers
            elif i > self.ma_period:
                prev_deviation = vpt_deviation[i-1]

                # VPT crosses above MA (buy)
                if prev_deviation <= 0 and current_deviation > 0:
                    strength = min(abs(current_deviation) * 10, 0.5)  # Weaker signal
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'buy',
                        'strength': strength,
                        'price': df['close'].iloc[i],
                        'metadata': {
                            'strategy': 'vpt',
                            'vpt': current_vpt,
                            'deviation': current_deviation,
                            'signal_type': 'crossover_buy'
                        }
                    })

                # VPT crosses below MA (sell)
                elif prev_deviation >= 0 and current_deviation < 0:
                    strength = min(abs(current_deviation) * 10, 0.5)  # Weaker signal
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'sell',
                        'strength': strength,
                        'price': df['close'].iloc[i],
                        'metadata': {
                            'strategy': 'vpt',
                            'vpt': current_vpt,
                            'deviation': current_deviation,
                            'signal_type': 'crossover_sell'
                        }
                    })

        return signals


class OBVStrategy(BaseStrategy):
    """On-Balance Volume (OBV) Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ma_period = config.get('ma_period', 20)
        self.divergence_periods = config.get('divergence_periods', 20)
        self.confirmation_periods = config.get('confirmation_periods', 5)

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate OBV and related indicators"""
        df = pd.DataFrame(data)

        # Calculate OBV
        price_change = df['close'].diff()
        obv = np.where(price_change > 0, df['volume'],
                     np.where(price_change < 0, -df['volume'], 0)).cumsum()

        # Calculate OBV moving averages
        obv_ma = obv.rolling(window=self.ma_period).mean()
        obv_ema = obv.ewm(span=self.ma_period).mean()

        # Calculate OBV divergences
        obv_slope = obv.rolling(window=self.divergence_periods).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0], raw=True
        )
        price_slope = df['close'].rolling(window=self.divergence_periods).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0], raw=True
        )

        # Divergence indicator
        divergence = np.where(
            (price_slope > 0) & (obv_slope < 0), 1,  # Bearish divergence
            np.where(
                (price_slope < 0) & (obv_slope > 0), -1,  # Bullish divergence
                0  # No divergence
            )
        )

        return {
            'obv': obv.tolist(),
            'obv_ma': obv_ma.tolist(),
            'obv_ema': obv_ema.tolist(),
            'obv_slope': obv_slope.tolist(),
            'price_slope': price_slope.tolist(),
            'divergence': divergence.tolist()
        }

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate OBV-based signals"""
        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        obv = indicators['obv']
        obv_ma = indicators['obv_ma']
        obv_ema = indicators['obv_ema']
        divergence = indicators['divergence']

        for i in range(self.ma_period + self.divergence_periods, len(obv)):
            current_obv = obv[i]
            current_divergence = divergence[i]

            # Divergence signals (strongest signals)
            if current_divergence != 0:
                signal_type = 'sell' if current_divergence > 0 else 'buy'

                # Calculate divergence strength
                obv_diff = abs(obv[i] - obv_ma[i]) / abs(obv_ma[i]) if obv_ma[i] != 0 else 0
                strength = min(obv_diff * 5, 1)  # Scale to 0-1

                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': signal_type,
                    'strength': strength,
                    'price': df['close'].iloc[i],
                    'metadata': {
                        'strategy': 'obv',
                        'obv': current_obv,
                        'obv_ma': obv_ma[i],
                        'divergence_type': 'bearish' if current_divergence > 0 else 'bullish',
                        'signal_type': 'divergence'
                    }
                })

            # Trend confirmation signals
            elif i > self.ma_period + self.confirmation_periods:
                # OBV trend confirmation
                obv_trend_up = all(obv[j] > obv_ma[j] for j in range(i - self.confirmation_periods, i))
                obv_trend_down = all(obv[j] < obv_ma[j] for j in range(i - self.confirmation_periods, i))

                if obv_trend_up:
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'buy',
                        'strength': 0.6,  # Moderate strength
                        'price': df['close'].iloc[i],
                        'metadata': {
                            'strategy': 'obv',
                            'obv': current_obv,
                            'signal_type': 'trend_confirmation_buy'
                        }
                    })
                elif obv_trend_down:
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'sell',
                        'strength': 0.6,  # Moderate strength
                        'price': df['close'].iloc[i],
                        'metadata': {
                            'strategy': 'obv',
                            'obv': current_obv,
                            'signal_type': 'trend_confirmation_sell'
                        }
                    })

        return signals


class VWAPStrategy(BaseStrategy):
    """Volume Weighted Average Price (VWAP) Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.std_dev_multiplier = config.get('std_dev_multiplier', 2.0)
        self.mean_reversion_threshold = config.get('mean_reversion_threshold', 0.015)
        self.reset_frequency = config.get('reset_frequency', 'daily')

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate VWAP and related indicators"""
        df = pd.DataFrame(data)

        # Group by reset frequency
        if self.reset_frequency == 'daily':
            df['date'] = df.index.date
            groups = df.groupby('date')
        elif self.reset_frequency == 'weekly':
            df['week'] = df.index.isocalendar().week
            df['year'] = df.index.year
            groups = df.groupby(['year', 'week'])
        else:  # monthly
            df['month'] = df.index.month
            df['year'] = df.index.year
            groups = df.groupby(['year', 'month'])

        # Calculate VWAP, variance, and standard deviation for each group
        vwap_list = []
        upper_band_list = []
        lower_band_list = []

        for name, group in groups:
            typical_price = (group['high'] + group['low'] + group['close']) / 3
            vwap = (typical_price * group['volume']).cumsum() / group['volume'].cumsum()

            # Calculate standard deviation bands
            vwap_variance = ((typical_price - vwap) ** 2 * group['volume']).cumsum() / group['volume'].cumsum()
            vwap_std = np.sqrt(vwap_variance)

            upper_band = vwap + (vwap_std * self.std_dev_multiplier)
            lower_band = vwap - (vwap_std * self.std_dev_multiplier)

            vwap_list.extend(vwap.tolist())
            upper_band_list.extend(upper_band.tolist())
            lower_band_list.extend(lower_band.tolist())

        # Pad with NaN if needed to match original length
        padding = len(df) - len(vwap_list)
        if padding > 0:
            vwap_list = [np.nan] * padding + vwap_list
            upper_band_list = [np.nan] * padding + upper_band_list
            lower_band_list = [np.nan] * padding + lower_band_list

        # Calculate VWAP deviation percentage
        vwap_array = np.array(vwap_list)
        price_array = df['close'].values
        vwap_deviation = np.where(
            ~np.isnan(vwap_array),
            (price_array - vwap_array) / vwap_array,
            0
        )

        # Band width (volatility indicator)
        band_width = np.where(
            ~np.isnan(vwap_array),
            (np.array(upper_band_list) - np.array(lower_band_list)) / vwap_array,
            0
        )

        return {
            'vwap': vwap_list,
            'vwap_upper': upper_band_list,
            'vwap_lower': lower_band_list,
            'vwap_deviation': vwap_deviation.tolist(),
            'band_width': band_width.tolist()
        }

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate VWAP-based signals"""
        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        vwap = indicators['vwap']
        vwap_upper = indicators['vwap_upper']
        vwap_lower = indicators['vwap_lower']
        vwap_deviation = indicators['vwap_deviation']
        band_width = indicators['band_width']

        for i in range(len(vwap)):
            if np.isnan(vwap[i]):
                continue

            current_deviation = vwap_deviation[i]
            current_band_width = band_width[i]

            # Mean reversion signals
            if abs(current_deviation) > self.mean_reversion_threshold:
                signal_type = 'sell' if current_deviation > 0 else 'buy'

                # Strength based on deviation and band width
                strength = min(abs(current_deviation) / (current_band_width if current_band_width > 0 else 0.1), 1)

                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': signal_type,
                    'strength': strength,
                    'price': df['close'].iloc[i],
                    'vwap': vwap[i],
                    'metadata': {
                        'strategy': 'vwap',
                        'vwap_deviation': current_deviation,
                        'band_width': current_band_width,
                        'signal_type': 'mean_reversion'
                    }
                })

            # Breakout signals
            elif not np.isnan(vwap_upper[i]) and not np.isnan(vwap_lower[i]):
                price = df['close'].iloc[i]

                # Breakout above upper band
                if price > vwap_upper[i]:
                    strength = min((price - vwap_upper[i]) / (vwap_upper[i] - vwap[i]) if vwap_upper[i] != vwap[i] else 0, 1)
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'buy',
                        'strength': strength,
                        'price': price,
                        'vwap': vwap[i],
                        'metadata': {
                            'strategy': 'vwap',
                            'breakout_type': 'upper_band',
                            'signal_type': 'breakout_buy'
                        }
                    })

                # Breakout below lower band
                elif price < vwap_lower[i]:
                    strength = min((vwap[i] - price) / (vwap[i] - vwap_lower[i]) if vwap[i] != vwap_lower[i] else 0, 1)
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'sell',
                        'strength': strength,
                        'price': price,
                        'vwap': vwap[i],
                        'metadata': {
                            'strategy': 'vwap',
                            'breakout_type': 'lower_band',
                            'signal_type': 'breakout_sell'
                        }
                    })

        return signals


class MFIStrategy(BaseStrategy):
    """Money Flow Index (MFI) Strategy"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.period = config.get('period', 14)
        self.overbought = config.get('overbought', 80)
        self.oversold = config.get('oversold', 20)
        self.divergence_threshold = config.get('divergence_threshold', 0.1)

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate MFI and related indicators"""
        df = pd.DataFrame(data)

        # Calculate typical price
        typical_price = (df['high'] + df['low'] + df['close']) / 3

        # Calculate raw money flow
        raw_money_flow = typical_price * df['volume']

        # Determine positive and negative money flow
        price_change = typical_price.diff()
        positive_flow = raw_money_flow.where(price_change > 0, 0)
        negative_flow = raw_money_flow.where(price_change < 0, 0)

        # Calculate money flow sums
        positive_sum = positive_flow.rolling(window=self.period).sum()
        negative_sum = negative_flow.rolling(window=self.period).sum()

        # Calculate Money Flow Index
        money_ratio = positive_sum / negative_sum
        mfi = 100 - (100 / (1 + money_ratio))

        # Calculate MFI divergences (similar to RSI divergences)
        mfi_slope = mfi.rolling(window=20).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 and not np.isnan(x).any() else 0,
            raw=True
        )
        price_slope = df['close'].rolling(window=20).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 and not np.isnan(x).any() else 0,
            raw=True
        )

        # Divergence detection
        divergence = np.where(
            (price_slope > 0) & (mfi_slope < 0), 1,  # Bearish divergence
            np.where(
                (price_slope < 0) & (mfi_slope > 0), -1,  # Bullish divergence
                0  # No divergence
            )
        )

        return {
            'mfi': mfi.tolist(),
            'mfi_slope': mfi_slope.tolist(),
            'price_slope': price_slope.tolist(),
            'divergence': divergence.tolist()
        }

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate MFI-based signals"""
        indicators = self.calculate_indicators(data)
        df = pd.DataFrame(data)
        signals = []

        mfi = indicators['mfi']
        divergence = indicators['divergence']

        for i in range(self.period + 20, len(mfi)):  # Wait for divergence calculations
            current_mfi = mfi[i]
            current_divergence = divergence[i]

            # Overbought/Oversold signals
            if i > 0:
                prev_mfi = mfi[i-1]

                # Overbought to normal (sell signal)
                if prev_mfi >= self.overbought and current_mfi < self.overbought:
                    strength = (prev_mfi - self.overbought) / (100 - self.overbought)
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'sell',
                        'strength': min(strength, 1),
                        'price': df['close'].iloc[i],
                        'metadata': {
                            'strategy': 'mfi',
                            'mfi': current_mfi,
                            'signal_type': 'overbought_exit'
                        }
                    })

                # Oversold to normal (buy signal)
                elif prev_mfi <= self.oversold and current_mfi > self.oversold:
                    strength = (self.oversold - prev_mfi) / self.oversold
                    signals.append({
                        'timestamp': df.index[i].isoformat(),
                        'type': 'buy',
                        'strength': min(strength, 1),
                        'price': df['close'].iloc[i],
                        'metadata': {
                            'strategy': 'mfi',
                            'mfi': current_mfi,
                            'signal_type': 'oversold_exit'
                        }
                    })

            # Divergence signals
            if current_divergence != 0:
                signal_type = 'sell' if current_divergence > 0 else 'buy'
                divergence_strength = 0.8  # High strength for divergences

                signals.append({
                    'timestamp': df.index[i].isoformat(),
                    'type': signal_type,
                    'strength': divergence_strength,
                    'price': df['close'].iloc[i],
                    'metadata': {
                        'strategy': 'mfi',
                        'mfi': current_mfi,
                        'divergence_type': 'bearish' if current_divergence > 0 else 'bullish',
                        'signal_type': 'divergence'
                    }
                })

        return signals


class CompositeVolumeStrategy(BaseStrategy):
    """Composite strategy combining multiple volume indicators"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.indicators = config.get('indicators', ['vpt', 'obv', 'vwap', 'mfi'])
        self.weights = config.get('weights', {
            'vpt': 0.25, 'obv': 0.25, 'vwap': 0.25, 'mfi': 0.25
        })
        self.consensus_threshold = config.get('consensus_threshold', 0.6)

        # Initialize sub-strategies
        self.sub_strategies = {}
        if 'vpt' in self.indicators:
            self.sub_strategies['vpt'] = VPTStrategy(config.get('vpt_config', {}))
        if 'obv' in self.indicators:
            self.sub_strategies['obv'] = OBVStrategy(config.get('obv_config', {}))
        if 'vwap' in self.indicators:
            self.sub_strategies['vwap'] = VWAPStrategy(config.get('vwap_config', {}))
        if 'mfi' in self.indicators:
            self.sub_strategies['mfi'] = MFIStrategy(config.get('mfi_config', {}))

    def calculate_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all volume indicators"""
        all_indicators = {}

        for indicator_name, strategy in self.sub_strategies.items():
            try:
                indicators = strategy.calculate_indicators(data)
                for key, value in indicators.items():
                    all_indicators[f"{indicator_name}_{key}"] = value
            except Exception as e:
                logger.error(f"Error calculating {indicator_name}: {e}")

        # Calculate composite volume score
        composite_score = self._calculate_composite_score(all_indicators)
        all_indicators['composite_volume_score'] = composite_score

        return all_indicators

    def generate_signals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate composite volume signals"""
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

        # Remove duplicate signals
        unique_signals = self._deduplicate_signals(all_signals)

        return unique_signals

    def _calculate_composite_score(self, indicators: Dict[str, Any]) -> List[float]:
        """Calculate composite volume score"""
        scores = []

        if not indicators:
            return scores

        # Find the minimum length among all indicator arrays
        indicator_lengths = []
        for key, value in indicators.items():
            if isinstance(value, list):
                indicator_lengths.append(len(value))

        if not indicator_lengths:
            return scores

        min_length = min(indicator_lengths)
        composite_scores = [0.0] * min_length

        for indicator_name, strategy in self.sub_strategies.items():
            weight = self.weights.get(indicator_name, 0)

            if indicator_name == 'vpt' and 'vpt_deviation' in indicators:
                vpt_dev = indicators['vpt_deviation'][:min_length]
                for i, val in enumerate(vpt_dev):
                    # Normalize deviation to 0-1
                    composite_scores[i] += (abs(val) * 5 * weight) if abs(val) < 0.2 else weight

            elif indicator_name == 'obv' and 'obv_slope' in indicators:
                obv_slope = indicators['obv_slope'][:min_length]
                for i, val in enumerate(obv_slope):
                    # Normalize slope to 0-1
                    composite_scores[i] += (min(abs(val) / 1000000, 1) * weight)

            elif indicator_name == 'vwap' and 'vwap_deviation' in indicators:
                vwap_dev = indicators['vwap_deviation'][:min_length]
                for i, val in enumerate(vwap_dev):
                    # Use absolute deviation
                    composite_scores[i] += (abs(val) * 10 * weight) if abs(val) < 0.1 else weight

            elif indicator_name == 'mfi' and 'mfi' in indicators:
                mfi_vals = indicators['mfi'][:min_length]
                for i, val in enumerate(mfi_vals):
                    # Normalize MFI to 0-1 (closer to 50 is neutral)
                    distance_from_center = abs(val - 50) / 50
                    composite_scores[i] += (distance_from_center * weight)

        # Normalize final scores
        total_weight = sum(self.weights.get(name, 0) for name in self.sub_strategies.keys())
        if total_weight > 0:
            composite_scores = [min(score / total_weight, 1) for score in composite_scores]

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
                        'strategy': 'composite_volume',
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
                        'strategy': 'composite_volume',
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
            closest_idx = df.index.get_indexer([dt], method='nearest')[0]
            return df['close'].iloc[closest_idx]
        except:
            return 0.0