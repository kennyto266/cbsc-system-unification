"""
Fundamental Strategies V2 - Updated for New Framework
基本面策略 V2 - 適配新框架

將原有的基本面策略適配到新的量化策略框架中
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..quant_strategy_framework import (
    QuantStrategyBase, StrategyConfig, StrategyType, SignalType, Signal
)
from ..economic_data_adapter import get_economic_data_adapter

logger = logging.getLogger('FundamentalStrategiesV2')

class EconomicIndicatorStrategy(QuantStrategyBase):
    """經濟指標策略基類"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.data_adapter = get_economic_data_adapter()
        self.economic_data = None

    def initialize(self) -> bool:
        """初始化策略，預加載經濟數據"""
        try:
            # 獲取所需的經濟數據
            self.economic_data = self._load_economic_data()

            if self.economic_data is not None and not self.economic_data.empty:
                self.logger.info(f"已加載經濟數據，期間: {self.economic_data.index[0]} 至 {self.economic_data.index[-1]}")
                return True
            else:
                self.logger.warning("未能獲取經濟數據，將使用模擬數據")
                return True
        except Exception as e:
            self.logger.error(f"初始化失敗: {str(e)}")
            return False

    def _load_economic_data(self) -> pd.DataFrame:
        """加載經濟數據"""
        # 根據策略需求決定時間範圍
        start_date = datetime.now() - timedelta(days=365 * 2)  # 過去2年
        end_date = datetime.now()

        return self.data_adapter.get_all_economic_data(start_date, end_date)

class HIBORStrategyV2(EconomicIndicatorStrategy):
    """香港銀行同業拆息策略 V2"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.lookback_period = self.parameters.get('lookback_period', 30)
        self.rate_threshold_high = self.parameters.get('rate_threshold_high', 5.0)
        self.rate_threshold_low = self.parameters.get('rate_threshold_low', 2.0)
        self.use_momentum = self.parameters.get('use_momentum', True)

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """基於HIBOR數據生成信號"""
        signals = []

        # 獲取HIBOR數據
        if self.economic_data is None or 'hibor_rate' not in self.economic_data.columns:
            self.logger.warning("無HIBOR數據，跳過信號生成")
            return signals

        # 對齊數據日期
        common_dates = data.index.intersection(self.economic_data.index)
        if len(common_dates) == 0:
            return signals

        aligned_economic = self.economic_data.loc[common_dates]
        aligned_data = data.loc[common_dates]

        # 計算HIBOR指標
        hibor = aligned_economic['hibor_rate']
        hibor_ma = hibor.rolling(window=self.lookback_period).mean()
        hibor_momentum = hibor.diff(self.lookback_period)

        # 生成信號
        for i in range(self.lookback_period, len(aligned_data)):
            current_date = aligned_data.index[i]
            current_rate = hibor.iloc[i]
            avg_rate = hibor_ma.iloc[i]
            current_momentum = hibor_momentum.iloc[i]

            # 獲取當前價格
            symbol = self.config.symbols[0]
            price_col = f'close_{symbol}'
            if price_col not in aligned_data.columns:
                continue
            current_price = aligned_data[price_col].iloc[i]

            # 信號強度計算
            strength = min(abs(current_rate - avg_rate) / 2.0, 1.0)
            confidence = 0.7 if strength > 0.5 else 0.5

            # 看漲信號
            if current_rate < self.rate_threshold_low:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strength=strength,
                    price=current_price,
                    timestamp=current_date,
                    confidence=confidence,
                    metadata={
                        'hibor_rate': current_rate,
                        'avg_rate': avg_rate,
                        'indicator': 'HIBOR',
                        'action': 'low_rate'
                    }
                )
                signals.append(signal)

            # 看漲信號（動量）
            elif current_rate < avg_rate and self.use_momentum and current_momentum < 0:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strength=strength * 0.8,
                    price=current_price,
                    timestamp=current_date,
                    confidence=0.6,
                    metadata={
                        'hibor_rate': current_rate,
                        'momentum': current_momentum,
                        'indicator': 'HIBOR',
                        'action': 'falling_rate'
                    }
                )
                signals.append(signal)

            # 看跌信號
            elif current_rate > self.rate_threshold_high:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    strength=strength,
                    price=current_price,
                    timestamp=current_date,
                    confidence=confidence,
                    metadata={
                        'hibor_rate': current_rate,
                        'avg_rate': avg_rate,
                        'indicator': 'HIBOR',
                        'action': 'high_rate'
                    }
                )
                signals.append(signal)

            # 看跌信號（動量）
            elif current_rate > avg_rate and self.use_momentum and current_momentum > 0:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    strength=strength * 0.8,
                    price=current_price,
                    timestamp=current_date,
                    confidence=0.6,
                    metadata={
                        'hibor_rate': current_rate,
                        'momentum': current_momentum,
                        'indicator': 'HIBOR',
                        'action': 'rising_rate'
                    }
                )
                signals.append(signal)

        return signals

    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """基於信號強度計算倉位"""
        base_size = portfolio_value * self.config.max_position_size
        # HIBOR策略使用較保守的倉位
        return base_size * signal.strength * 0.5 / signal.price

class GDPGrowthStrategyV2(EconomicIndicatorStrategy):
    """GDP增長策略 V2"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.growth_threshold_high = self.parameters.get('growth_threshold_high', 0.05)
        self.growth_threshold_low = self.parameters.get('growth_threshold_low', 0.01)
        self.lookback_quarters = self.parameters.get('lookback_quarters', 4)
        self.use_acceleration = self.parameters.get('use_acceleration', True)

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """基於GDP增長數據生成信號"""
        signals = []

        # 獲取GDP數據
        if self.economic_data is None or 'gdp_growth' not in self.economic_data.columns:
            self.logger.warning("無GDP數據，跳過信號生成")
            return signals

        # 對齊數據
        common_dates = data.index.intersection(self.economic_data.index)
        if len(common_dates) == 0:
            return signals

        aligned_economic = self.economic_data.loc[common_dates]
        aligned_data = data.loc[common_dates]

        # 前向填充GDP數據（季度數據）
        gdp_growth = aligned_economic['gdp_growth'].ffill()
        gdp_ma = gdp_growth.rolling(window=self.lookback_quarters).mean()

        if self.use_acceleration:
            gdp_accel = gdp_growth.diff()
        else:
            gdp_accel = pd.Series(0, index=gdp_growth.index)

        # 生成信號
        for i in range(self.lookback_quarters, len(aligned_data)):
            current_date = aligned_data.index[i]
            current_growth = gdp_growth.iloc[i]
            avg_growth = gdp_ma.iloc[i]
            current_accel = gdp_accel.iloc[i]

            symbol = self.config.symbols[0]
            price_col = f'close_{symbol}'
            if price_col not in aligned_data.columns:
                continue
            current_price = aligned_data[price_col].iloc[i]

            # 計算信號強度
            strength = 0
            if current_growth > self.growth_threshold_high:
                strength = min((current_growth - self.growth_threshold_high) * 10, 1.0)
            elif current_growth < -0.01:
                strength = min((-current_growth - 0.01) * 10, 1.0)

            confidence = 0.8 if strength > 0.7 else 0.5

            # 強烈看漲信號
            if current_growth > self.growth_threshold_high:
                if self.use_acceleration and current_accel > 0:
                    strength = min(strength * 1.5, 1.0)
                    confidence = 0.9

                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strength=strength,
                    price=current_price,
                    timestamp=current_date,
                    confidence=confidence,
                    metadata={
                        'gdp_growth': current_growth,
                        'avg_growth': avg_growth,
                        'acceleration': current_accel,
                        'indicator': 'GDP',
                        'action': 'strong_growth'
                    }
                )
                signals.append(signal)

            # 強烈看跌信號
            elif current_growth < -0.01:
                if self.use_acceleration and current_accel < 0:
                    strength = min(strength * 1.5, 1.0)
                    confidence = 0.9

                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    strength=strength,
                    price=current_price,
                    timestamp=current_date,
                    confidence=confidence,
                    metadata={
                        'gdp_growth': current_growth,
                        'avg_growth': avg_growth,
                        'acceleration': current_accel,
                        'indicator': 'GDP',
                        'action': 'negative_growth'
                    }
                )
                signals.append(signal)

        return signals

    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """GDP策略使用較大的倉位（經濟數據變化較慢）"""
        base_size = portfolio_value * self.config.max_position_size
        return base_size * 0.7 / signal.price

class PMIStrategyV2(EconomicIndicatorStrategy):
    """採購經理人指數策略 V2"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.expansion_threshold = self.parameters.get('expansion_threshold', 55)
        self.contraction_threshold = self.parameters.get('contraction_threshold', 45)
        self.trend_periods = self.parameters.get('trend_periods', 3)
        self.combine_manufacturing_services = self.parameters.get('combine_manufacturing_services', True)

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """基於PMI數據生成信號"""
        signals = []

        # 獲取PMI數據
        if self.economic_data is None:
            self.logger.warning("無PMI數據，跳過信號生成")
            return signals

        # 對齊數據
        common_dates = data.index.intersection(self.economic_data.index)
        if len(common_dates) == 0:
            return signals

        aligned_economic = self.economic_data.loc[common_dates]
        aligned_data = data.loc[common_dates]

        # 獲取PMI數據
        if (self.combine_manufacturing_services and
            all(col in aligned_economic.columns for col in ['pmi_manufacturing', 'pmi_services'])):
            pmi = (aligned_economic['pmi_manufacturing'] + aligned_economic['pmi_services']) / 2
        elif 'pmi_manufacturing' in aligned_economic.columns:
            pmi = aligned_economic['pmi_manufacturing']
        elif 'pmi_services' in aligned_economic.columns:
            pmi = aligned_economic['pmi_services']
        else:
            self.logger.warning("無PMI數據列")
            return signals

        # 前向填充
        pmi = pmi.ffill()
        pmi_trend = pmi.diff(self.trend_periods)

        # 生成信號
        for i in range(self.trend_periods, len(aligned_data)):
            current_date = aligned_data.index[i]
            current_pmi = pmi.iloc[i]
            current_trend = pmi_trend.iloc[i]

            symbol = self.config.symbols[0]
            price_col = f'close_{symbol}'
            if price_col not in aligned_data.columns:
                continue
            current_price = aligned_data[price_col].iloc[i]

            # 計算信號強度
            strength = 0
            if current_pmi > self.expansion_threshold:
                strength = min((current_pmi - 50) / 20, 1.0)
            elif current_pmi < self.contraction_threshold:
                strength = min((50 - current_pmi) / 20, 1.0)

            confidence = 0.7

            # 擴張信號
            if current_pmi > self.expansion_threshold:
                if current_trend > 0:  # 加速擴張
                    strength = min(strength * 1.3, 1.0)
                    confidence = 0.85

                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strength=strength,
                    price=current_price,
                    timestamp=current_date,
                    confidence=confidence,
                    metadata={
                        'pmi': current_pmi,
                        'trend': current_trend,
                        'indicator': 'PMI',
                        'action': 'expansion'
                    }
                )
                signals.append(signal)

            # 收縮信號
            elif current_pmi < self.contraction_threshold:
                if current_trend < 0:  # 加速收縮
                    strength = min(strength * 1.3, 1.0)
                    confidence = 0.85

                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    strength=strength,
                    price=current_price,
                    timestamp=current_date,
                    confidence=confidence,
                    metadata={
                        'pmi': current_pmi,
                        'trend': current_trend,
                        'indicator': 'PMI',
                        'action': 'contraction'
                    }
                )
                signals.append(signal)

            # 趨勢信號
            elif current_trend > 5:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strength=0.6,
                    price=current_price,
                    timestamp=current_date,
                    confidence=0.6,
                    metadata={
                        'pmi': current_pmi,
                        'trend': current_trend,
                        'indicator': 'PMI',
                        'action': 'strong_uptrend'
                    }
                )
                signals.append(signal)

            elif current_trend < -5:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    strength=0.6,
                    price=current_price,
                    timestamp=current_date,
                    confidence=0.6,
                    metadata={
                        'pmi': current_pmi,
                        'trend': current_trend,
                        'indicator': 'PMI',
                        'action': 'strong_downtrend'
                    }
                )
                signals.append(signal)

        return signals

    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """PMI策略使用中等倉位"""
        base_size = portfolio_value * self.config.max_position_size
        return base_size * 0.6 / signal.price

class CompositeFundamentalStrategy(QuantStrategyBase):
    """綜合基本面策略"""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.data_adapter = get_economic_data_adapter()
        self.sub_strategies = []
        self.indicator_weights = self.parameters.get('indicator_weights', {
            'hibor': 0.3,
            'gdp': 0.3,
            'pmi': 0.3,
            'visitor': 0.1
        })

    def initialize(self) -> bool:
        """初始化所有子策略"""
        try:
            # 創建子策略配置
            sub_configs = {}
            for indicator in self.indicator_weights.keys():
                sub_configs[indicator] = StrategyConfig(
                    name=f"{self.config.name}_{indicator}",
                    strategy_type=StrategyType.STATISTICAL,
                    symbols=self.config.symbols,
                    timeframe=self.config.timeframe,
                    initial_capital=self.config.initial_capital,
                    max_position_size=self.config.max_position_size * self.indicator_weights[indicator],
                    risk_limit=self.config.risk_limit
                )

            # 創建並初始化子策略
            if 'hibor' in self.indicator_weights:
                strategy = HIBORStrategyV2(sub_configs['hibor'])
                strategy.parameters = {
                    'lookback_period': self.parameters.get('hibor_lookback', 30),
                    'rate_threshold_high': self.parameters.get('hibor_high', 5.0),
                    'rate_threshold_low': self.parameters.get('hibor_low', 2.0)
                }
                self.sub_strategies.append(strategy)

            if 'gdp' in self.indicator_weights:
                strategy = GDPGrowthStrategyV2(sub_configs['gdp'])
                strategy.parameters = {
                    'growth_threshold_high': self.parameters.get('gdp_high', 0.05),
                    'growth_threshold_low': self.parameters.get('gdp_low', 0.01),
                    'lookback_quarters': self.parameters.get('gdp_lookback', 4)
                }
                self.sub_strategies.append(strategy)

            if 'pmi' in self.indicator_weights:
                strategy = PMIStrategyV2(sub_configs['pmi'])
                strategy.parameters = {
                    'expansion_threshold': self.parameters.get('pmi_expansion', 55),
                    'contraction_threshold': self.parameters.get('pmi_contraction', 45)
                }
                self.sub_strategies.append(strategy)

            # 初始化所有子策略
            for strategy in self.sub_strategies:
                if not strategy.initialize():
                    self.logger.error(f"子策略 {strategy.config.name} 初始化失敗")
                    return False

            self.logger.info(f"綜合基本面策略初始化成功，包含 {len(self.sub_strategies)} 個子策略")
            return True

        except Exception as e:
            self.logger.error(f"初始化失敗: {str(e)}")
            return False

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """綜合所有子策略的信號"""
        all_signals = []

        # 收集所有子策略的信號
        for strategy in self.sub_strategies:
            signals = strategy.generate_signals(data)
            all_signals.extend(signals)

        # 按時間和標的匯總信號
        signal_groups = {}
        for signal in all_signals:
            key = (signal.timestamp, signal.symbol)
            if key not in signal_groups:
                signal_groups[key] = []
            signal_groups[key].append(signal)

        # 合併信號
        merged_signals = []
        for (timestamp, symbol), group_signals in signal_groups.items():
            # 加權平均
            total_strength = 0
            total_weight = 0
            buy_count = 0
            sell_count = 0

            for signal in group_signals:
                indicator = signal.metadata.get('indicator', 'unknown')
                weight = self.indicator_weights.get(indicator.lower(), 0.1)

                if signal.signal_type == SignalType.BUY:
                    buy_count += weight
                    total_strength += signal.strength * weight
                elif signal.signal_type == SignalType.SELL:
                    sell_count += weight
                    total_strength -= signal.strength * weight

                total_weight += weight

            # 決定最終信號
            if total_weight > 0:
                avg_strength = abs(total_strength) / total_weight
                net_weight = buy_count - sell_count

                if net_weight > 0.2:  # 淨看漲
                    signal_type = SignalType.BUY
                elif net_weight < -0.2:  # 淨看跌
                    signal_type = SignalType.SELL
                else:
                    signal_type = SignalType.HOLD

                if signal_type != SignalType.HOLD:
                    merged_signal = Signal(
                        symbol=symbol,
                        signal_type=signal_type,
                        strength=avg_strength,
                        price=group_signals[0].price,  # 使用第一個信號的價格
                        timestamp=timestamp,
                        confidence=0.7,
                        metadata={
                            'composite_signal': True,
                            'buy_weight': buy_count,
                            'sell_weight': sell_count,
                            'num_signals': len(group_signals),
                            'indicators': [s.metadata.get('indicator') for s in group_signals]
                        }
                    )
                    merged_signals.append(merged_signal)

        return merged_signals

    def calculate_position_size(self, signal: Signal, portfolio_value: float) -> float:
        """綜合策略使用較保守的倉位"""
        base_size = portfolio_value * self.config.max_position_size

        # 基於信號數量調整
        num_signals = signal.metadata.get('num_signals', 1)
        adjustment = min(num_signals / len(self.sub_strategies), 1.0)

        return base_size * signal.strength * adjustment / signal.price