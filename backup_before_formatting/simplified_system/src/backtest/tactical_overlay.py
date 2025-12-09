#!/usr/bin/env python3
"""
動態資產配置系統 - 戰術覆蓋系統
Dynamic Asset Allocation System - Tactical Overlay System

戰術覆蓋系統，用於在戰略配置基礎上進行短期調整
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from enum import Enum

from .market_regime import MarketRegimeDetector, RegimeState, RegimePrediction
from .dynamic_allocator import DynamicAssetAllocator, AllocationResult, AssetConfig
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from indicators.core_indicators import CoreIndicators

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信號類型"""
    TECHNICAL = "technical"
    MACRO = "macro"
    SENTIMENT = "sentiment"
    SEASONAL = "seasonal"
    RISK_ON_RISK_OFF = "risk_on_risk_off"
    CARRY = "carry"

class SignalStrength(Enum):
    """信號強度"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4

@dataclass
class OverlaySignal:
    """覆蓋信號"""
    signal_id: str
    signal_type: SignalType
    asset_symbol: str
    direction: float  # -1 to 1, negative = sell, positive = buy
    strength: SignalStrength
    confidence: float  # 0 to 1
    timestamp: datetime
    expiry_date: Optional[datetime] = None

    # 信號描述
    description: str = ""
    trigger_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

    # 元數據
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OverlayConfig:
    """戰術覆蓋配置"""
    # 信號生成參數
    signal_generation_frequency: str = "daily"  # 'daily', 'weekly'
    max_signals_per_asset: int = 3
    min_signal_confidence: float = 0.6
    signal_expiry_days: int = 10

    # 覆蓋應用參數
    max_overlay_adjustment: float = 0.2  # 最大覆蓋調整幅度
    overlay_weight_decay: float = 0.1  # 權重衰減因子
    signal_aggregation_method: str = "weighted_average"  # 'weighted_average', 'max_strength', 'consensus'

    # 風險控制
    max_total_overlay_exposure: float = 0.3  # 最大總覆蓋暴露
    overlay_volatility_limit: float = 0.05  # 覆蓋波動率限制
    correlation_adjustment: bool = True  # 相關性調整

    # 執行參數
    overlay_execution_delay: int = 1  # 執行延遲（天）
    min_trade_size_overlay: float = 0.005  # 最小覆蓋交易規模
    overlay_cost_budget: float = 0.002  # 覆蓋成本預算

@dataclass
class OverlayResult:
    """覆蓋結果"""
    timestamp: datetime
    strategic_weights: Dict[str, float]
    tactical_adjustments: Dict[str, float]
    final_weights: Dict[str, float]

    # 信號信息
    active_signals: List[OverlaySignal]
    signal_summary: Dict[str, Dict[str, float]]  # 按資產統計信號

    # 成本分析
    overlay_costs: Dict[str, float]
    total_overlay_cost: float
    cost_efficiency: float

    # 風險分析
    overlay_risk_contribution: Dict[str, float]
    expected_overlay_return: float
    overlay_sharpe: float

class TacticalOverlaySystem:
    """
    戰術覆蓋系統

    在戰略資產配置基礎上，基於短期信號進行動態調整
    """

    def __init__(
        self,
        base_allocator: DynamicAssetAllocator,
        config: Optional[OverlayConfig] = None,
        regime_detector: Optional[MarketRegimeDetector] = None
    ):
        """初始化戰術覆蓋系統"""
        self.base_allocator = base_allocator
        self.config = config or OverlayConfig()
        self.regime_detector = regime_detector
        self.indicators = CoreIndicators()

        # 信號管理
        self.active_signals = []
        self.signal_history = []
        self.signal_generators = self._initialize_signal_generators()

        # 緩存
        self._cache = {}

        logger.info("Tactical Overlay System initialized")

    def _initialize_signal_generators(self) -> Dict[SignalType, Callable]:
        """初始化信號生成器"""
        return {
            SignalType.TECHNICAL: self._generate_technical_signals,
            SignalType.MACRO: self._generate_macro_signals,
            SignalType.SENTIMENT: self._generate_sentiment_signals,
            SignalType.SEASONAL: self._generate_seasonal_signals,
            SignalType.RISK_ON_RISK_OFF: self._generate_risk_on_risk_off_signals,
            SignalType.CARRY: self._generate_carry_signals
        }

    def generate_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[OverlaySignal]:
        """
        生成戰術覆蓋信號

        Args:
            market_data: 市場數據

        Returns:
            信號列表
        """
        logger.info("Generating tactical overlay signals...")

        all_signals = []

        # 為每種信號類型生成信號
        for signal_type, generator in self.signal_generators.items():
            try:
                signals = generator(market_data)
                all_signals.extend(signals)
                logger.debug(f"Generated {len(signals)} {signal_type.value} signals")
            except Exception as e:
                logger.error(f"Error generating {signal_type.value} signals: {e}")
                continue

        # 過濾和排序信號
        filtered_signals = self._filter_signals(all_signals)
        ranked_signals = self._rank_signals(filtered_signals)

        # 清理過期信號
        self._cleanup_expired_signals()

        # 更新活躍信號
        self.active_signals.extend(ranked_signals)

        # 記錄信號歷史
        self.signal_history.extend(ranked_signals)

        logger.info(f"Generated {len(ranked_signals)} new signals. Total active: {len(self.active_signals)}")

        return ranked_signals

    def _generate_technical_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[OverlaySignal]:
        """生成技術分析信號"""
        signals = []

        for symbol, data in market_data.items():
            if len(data) < 50:
                continue

            try:
                close = data['close']
                high = data['high']
                low = data['low']
                volume = data['volume']

                # RSI信號
                rsi = self.indicators.calculate_rsi(close, 14)
                latest_rsi = rsi.iloc[-1]

                if latest_rsi < 30:  # 超賣
                    signals.append(OverlaySignal(
                        signal_id=f"RSI_OVERSOLD_{symbol}",
                        signal_type=SignalType.TECHNICAL,
                        asset_symbol=symbol,
                        direction=1.0,
                        strength=SignalStrength.STRONG if latest_rsi < 20 else SignalStrength.MODERATE,
                        confidence=min(0.9, (35 - latest_rsi) / 10),
                        timestamp=datetime.now(),
                        expiry_date=datetime.now() + timedelta(days=5),
                        description=f"RSI超賣信號: {latest_rsi:.1f}",
                        source="RSI_Indicator"
                    ))
                elif latest_rsi > 70:  # 超買
                    signals.append(OverlaySignal(
                        signal_id=f"RSI_OVERBOUGHT_{symbol}",
                        signal_type=SignalType.TECHNICAL,
                        asset_symbol=symbol,
                        direction=-1.0,
                        strength=SignalStrength.STRONG if latest_rsi > 80 else SignalStrength.MODERATE,
                        confidence=min(0.9, (latest_rsi - 65) / 10),
                        timestamp=datetime.now(),
                        expiry_date=datetime.now() + timedelta(days=5),
                        description=f"RSI超買信號: {latest_rsi:.1f}",
                        source="RSI_Indicator"
                    ))

                # MACD信號
                macd_results = self.indicators.calculate_macd(close)
                macd_line = macd_results['macd']
                signal_line = macd_results['signal']

                if len(macd_line) > 1:
                    # 金叉
                    if (macd_line.iloc[-2] <= signal_line.iloc[-2] and
                        macd_line.iloc[-1] > signal_line.iloc[-1]):
                        signals.append(OverlaySignal(
                            signal_id=f"MACD_GOLDEN_CROSS_{symbol}",
                            signal_type=SignalType.TECHNICAL,
                            asset_symbol=symbol,
                            direction=1.0,
                            strength=SignalStrength.MODERATE,
                            confidence=0.7,
                            timestamp=datetime.now(),
                            expiry_date=datetime.now() + timedelta(days=7),
                            description="MACD金叉信號",
                            source="MACD_Indicator"
                        ))

                    # 死叉
                    elif (macd_line.iloc[-2] >= signal_line.iloc[-2] and
                          macd_line.iloc[-1] < signal_line.iloc[-1]):
                        signals.append(OverlaySignal(
                            signal_id=f"MACD_DEATH_CROSS_{symbol}",
                            signal_type=SignalType.TECHNICAL,
                            asset_symbol=symbol,
                            direction=-1.0,
                            strength=SignalStrength.MODERATE,
                            confidence=0.7,
                            timestamp=datetime.now(),
                            expiry_date=datetime.now() + timedelta(days=7),
                            description="MACD死叉信號",
                            source="MACD_Indicator"
                        ))

                # 突破信號
                sma_20 = self.indicators.calculate_sma(close, 20)
                sma_50 = self.indicators.calculate_sma(close, 50)
                latest_price = close.iloc[-1]
                latest_sma20 = sma_20.iloc[-1]
                latest_sma50 = sma_50.iloc[-1]

                # 均線突破
                if latest_price > latest_sma20 > latest_sma50:
                    signals.append(OverlaySignal(
                        signal_id=f"MA_BREAKOUT_UP_{symbol}",
                        signal_type=SignalType.TECHNICAL,
                        asset_symbol=symbol,
                        direction=0.5,
                        strength=SignalStrength.MODERATE,
                        confidence=0.6,
                        timestamp=datetime.now(),
                        expiry_date=datetime.now() + timedelta(days=3),
                        description="均線向上突破",
                        source="Moving_Average"
                    ))
                elif latest_price < latest_sma20 < latest_sma50:
                    signals.append(OverlaySignal(
                        signal_id=f"MA_BREAKOUT_DOWN_{symbol}",
                        signal_type=SignalType.TECHNICAL,
                        asset_symbol=symbol,
                        direction=-0.5,
                        strength=SignalStrength.MODERATE,
                        confidence=0.6,
                        timestamp=datetime.now(),
                        expiry_date=datetime.now() + timedelta(days=3),
                        description="均線向下突破",
                        source="Moving_Average"
                    ))

            except Exception as e:
                logger.error(f"Error generating technical signals for {symbol}: {e}")
                continue

        return signals

    def _generate_macro_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[OverlaySignal]:
        """生成宏觀經濟信號"""
        signals = []

        try:
            # 市場波動率信號
            all_returns = []
            for symbol, data in market_data.items():
                returns = data['close'].pct_change().dropna()
                all_returns.append(returns)

            if all_returns:
                market_returns = pd.concat(all_returns, axis=1).mean(axis=1)
                volatility = market_returns.rolling(20).std().iloc[-1]
                historical_vol = market_returns.rolling(252).std().mean()

                # 高波動率信號（減少風險暴露）
                if volatility > historical_vol * 1.5:
                    for symbol in market_data.keys():
                        signals.append(OverlaySignal(
                            signal_id=f"HIGH_VOLATILITY_{symbol}",
                            signal_type=SignalType.MACRO,
                            asset_symbol=symbol,
                            direction=-0.3,
                            strength=SignalStrength.MODERATE,
                            confidence=0.7,
                            timestamp=datetime.now(),
                            expiry_date=datetime.now() + timedelta(days=5),
                            description="市場高波動率",
                            source="Macro_Analysis"
                        ))

                # 低波動率信號（增加風險暴露）
                elif volatility < historical_vol * 0.7:
                    for symbol in market_data.keys():
                        if self.base_allocator.assets[symbol].asset_class == "equity":
                            signals.append(OverlaySignal(
                                signal_id=f"LOW_VOLATILITY_{symbol}",
                                signal_type=SignalType.MACRO,
                                asset_symbol=symbol,
                                direction=0.2,
                                strength=SignalStrength.WEAK,
                                confidence=0.5,
                                timestamp=datetime.now(),
                                expiry_date=datetime.now() + timedelta(days=5),
                                description="市場低波動率",
                                source="Macro_Analysis"
                            ))

        except Exception as e:
            logger.error(f"Error generating macro signals: {e}")

        return signals

    def _generate_sentiment_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[OverlaySignal]:
        """生成市場情緒信號"""
        signals = []

        try:
            # 基於成交量的情緒分析
            for symbol, data in market_data.items():
                if len(data) < 50:
                    continue

                volume = data['volume']
                close = data['close']

                # 成交量突增
                volume_ma = volume.rolling(20).mean()
                volume_ratio = volume.iloc[-1] / volume_ma.iloc[-1]

                # 價格變化
                price_change = close.pct_change(5).iloc[-1]

                # 高成交量上漲
                if volume_ratio > 2.0 and price_change > 0.03:
                    signals.append(OverlaySignal(
                        signal_id=f"VOLUME_SURGE_UP_{symbol}",
                        signal_type=SignalType.SENTIMENT,
                        asset_symbol=symbol,
                        direction=0.4,
                        strength=SignalStrength.MODERATE,
                        confidence=min(0.8, volume_ratio / 3),
                        timestamp=datetime.now(),
                        expiry_date=datetime.now() + timedelta(days=2),
                        description=f"高成交量上漲，成交量比率: {volume_ratio:.1f}",
                        source="Volume_Analysis"
                    ))

                # 高成交量下跌
                elif volume_ratio > 2.0 and price_change < -0.03:
                    signals.append(OverlaySignal(
                        signal_id=f"VOLUME_SURGE_DOWN_{symbol}",
                        signal_type=SignalType.SENTIMENT,
                        asset_symbol=symbol,
                        direction=-0.4,
                        strength=SignalStrength.MODERATE,
                        confidence=min(0.8, volume_ratio / 3),
                        timestamp=datetime.now(),
                        expiry_date=datetime.now() + timedelta(days=2),
                        description=f"高成交量下跌，成交量比率: {volume_ratio:.1f}",
                        source="Volume_Analysis"
                    ))

        except Exception as e:
            logger.error(f"Error generating sentiment signals: {e}")

        return signals

    def _generate_seasonal_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[OverlaySignal]:
        """生成季節性信號"""
        signals = []

        try:
            current_date = datetime.now()
            current_month = current_date.month

            # 季節性效應（簡化版本）
            seasonal_effects = {
                1: {"equity": 0.1, "description": "一月效應"},
                12: {"equity": 0.05, "description": "聖課老人升浪"},
                10: {"equity": -0.05, "description": "十月效應"},
            }

            if current_month in seasonal_effects:
                effect = seasonal_effects[current_month]

                for symbol, asset in self.base_allocator.assets.items():
                    if asset.asset_class == "equity":
                        signals.append(OverlaySignal(
                            signal_id=f"SEASONAL_{symbol}_{current_month}",
                            signal_type=SignalType.SEASONAL,
                            asset_symbol=symbol,
                            direction=effect["equity"],
                            strength=SignalStrength.WEAK,
                            confidence=0.4,
                            timestamp=datetime.now(),
                            expiry_date=datetime.now() + timedelta(days=30),
                            description=effect["description"],
                            source="Seasonal_Analysis"
                        ))

        except Exception as e:
            logger.error(f"Error generating seasonal signals: {e}")

        return signals

    def _generate_risk_on_risk_off_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[OverlaySignal]:
        """生成Risk-On/Risk-Off信號"""
        signals = []

        try:
            # 計算市場廣度和風險偏好指標
            equity_returns = []
            bond_returns = []

            for symbol, data in market_data.items():
                if len(data) < 20:
                    continue

                returns = data['close'].pct_change(10).iloc[-1]
                asset = self.base_allocator.assets.get(symbol)

                if asset:
                    if asset.asset_class == "equity":
                        equity_returns.append(returns)
                    elif asset.asset_class == "bond":
                        bond_returns.append(returns)

            if equity_returns and bond_returns:
                avg_equity_return = np.mean(equity_returns)
                avg_bond_return = np.mean(bond_returns)

                # Risk-On信號（權益表現優於債券）
                if avg_equity_return > avg_bond_return + 0.02:
                    for symbol, asset in self.base_allocator.assets.items():
                        if asset.asset_class == "equity":
                            signals.append(OverlaySignal(
                                signal_id=f"RISK_ON_{symbol}",
                                signal_type=SignalType.RISK_ON_RISK_OFF,
                                asset_symbol=symbol,
                                direction=0.3,
                                strength=SignalStrength.MODERATE,
                                confidence=0.6,
                                timestamp=datetime.now(),
                                expiry_date=datetime.now() + timedelta(days=7),
                                description="Risk-On市場環境",
                                source="Risk_Appetite"
                            ))
                        elif asset.asset_class == "bond":
                            signals.append(OverlaySignal(
                                signal_id=f"RISK_ON_BOND_{symbol}",
                                signal_type=SignalType.RISK_ON_RISK_OFF,
                                asset_symbol=symbol,
                                direction=-0.2,
                                strength=SignalStrength.MODERATE,
                                confidence=0.6,
                                timestamp=datetime.now(),
                                expiry_date=datetime.now() + timedelta(days=7),
                                description="Risk-On市場環境",
                                source="Risk_Appetite"
                            ))

                # Risk-Off信號（債券表現優於權益）
                elif avg_bond_return > avg_equity_return + 0.02:
                    for symbol, asset in self.base_allocator.assets.items():
                        if asset.asset_class == "equity":
                            signals.append(OverlaySignal(
                                signal_id=f"RISK_OFF_{symbol}",
                                signal_type=SignalType.RISK_ON_RISK_OFF,
                                asset_symbol=symbol,
                                direction=-0.3,
                                strength=SignalStrength.MODERATE,
                                confidence=0.6,
                                timestamp=datetime.now(),
                                expiry_date=datetime.now() + timedelta(days=7),
                                description="Risk-Off市場環境",
                                source="Risk_Appetite"
                            ))
                        elif asset.asset_class == "bond":
                            signals.append(OverlaySignal(
                                signal_id=f"RISK_OFF_BOND_{symbol}",
                                signal_type=SignalType.RISK_ON_RISK_OFF,
                                asset_symbol=symbol,
                                direction=0.2,
                                strength=SignalStrength.MODERATE,
                                confidence=0.6,
                                timestamp=datetime.now(),
                                expiry_date=datetime.now() + timedelta(days=7),
                                description="Risk-Off市場環境",
                                source="Risk_Appetite"
                            ))

        except Exception as e:
            logger.error(f"Error generating risk-on/risk-off signals: {e}")

        return signals

    def _generate_carry_signals(self, market_data: Dict[str, pd.DataFrame]) -> List[OverlaySignal]:
        """生成Carry交易信號"""
        signals = []

        try:
            # 簡化的Carry信號（基於歷史回報率）
            for symbol, data in market_data.items():
                if len(data) < 252:
                    continue

                # 計算Carry回報（趨勢回報）
                returns_1m = data['close'].pct_change(21).iloc[-1]  # 1個月回報
                returns_3m = data['close'].pct_change(63).iloc[-1]  # 3個月回報

                # 正Carry信號
                if returns_1m > 0.02 and returns_3m > 0.05:
                    signals.append(OverlaySignal(
                        signal_id=f"POSITIVE_CARRY_{symbol}",
                        signal_type=SignalType.CARRY,
                        asset_symbol=symbol,
                        direction=0.2,
                        strength=SignalStrength.MODERATE,
                        confidence=min(0.7, returns_3m / 0.1),
                        timestamp=datetime.now(),
                        expiry_date=datetime.now() + timedelta(days=14),
                        description=f"正Carry，1個月: {returns_1m:.2%}, 3個月: {returns_3m:.2%}",
                        source="Carry_Analysis"
                    ))

                # 負Carry信號
                elif returns_1m < -0.02 and returns_3m < -0.05:
                    signals.append(OverlaySignal(
                        signal_id=f"NEGATIVE_CARRY_{symbol}",
                        signal_type=SignalType.CARRY,
                        asset_symbol=symbol,
                        direction=-0.2,
                        strength=SignalStrength.MODERATE,
                        confidence=min(0.7, abs(returns_3m) / 0.1),
                        timestamp=datetime.now(),
                        expiry_date=datetime.now() + timedelta(days=14),
                        description=f"負Carry，1個月: {returns_1m:.2%}, 3個月: {returns_3m:.2%}",
                        source="Carry_Analysis"
                    ))

        except Exception as e:
            logger.error(f"Error generating carry signals: {e}")

        return signals

    def _filter_signals(self, signals: List[OverlaySignal]) -> List[OverlaySignal]:
        """過濾信號"""
        filtered = []

        for signal in signals:
            # 置信度過濾
            if signal.confidence < self.config.min_signal_confidence:
                continue

            # 過期檢查
            if signal.expiry_date and signal.expiry_date <= datetime.now():
                continue

            filtered.append(signal)

        return filtered

    def _rank_signals(self, signals: List[OverlaySignal]) -> List[OverlaySignal]:
        """排序信號"""
        # 計算信號分數
        for signal in signals:
            signal.metadata['score'] = (
                signal.confidence * signal.strength.value *
                self._get_signal_type_weight(signal.signal_type)
            )

        # 按分數排序
        ranked = sorted(signals, key=lambda x: x.metadata['score'], reverse=True)

        # 限制每個資產的信號數量
        final_signals = []
        asset_signal_count = {}

        for signal in ranked:
            asset = signal.asset_symbol
            if asset not in asset_signal_count:
                asset_signal_count[asset] = 0

            if asset_signal_count[asset] < self.config.max_signals_per_asset:
                final_signals.append(signal)
                asset_signal_count[asset] += 1

        return final_signals

    def _get_signal_type_weight(self, signal_type: SignalType) -> float:
        """獲取信號類型權重"""
        weights = {
            SignalType.TECHNICAL: 1.0,
            SignalType.MACRO: 1.2,
            SignalType.SENTIMENT: 0.8,
            SignalType.SEASONAL: 0.5,
            SignalType.RISK_ON_RISK_OFF: 1.1,
            SignalType.CARRY: 0.9
        }
        return weights.get(signal_type, 1.0)

    def _cleanup_expired_signals(self) -> None:
        """清理過期信號"""
        current_time = datetime.now()
        self.active_signals = [
            signal for signal in self.active_signals
            if not signal.expiry_date or signal.expiry_date > current_time
        ]

    def apply_tactical_overlay(
        self,
        strategic_weights: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
        regime_prediction: Optional[RegimePrediction] = None
    ) -> OverlayResult:
        """
        應用戰術覆蓋

        Args:
            strategic_weights: 戰略權重
            market_data: 市場數據
            regime_prediction: 制度預測

        Returns:
            覆蓋結果
        """
        logger.info("Applying tactical overlay...")

        # 生成新信號
        new_signals = self.generate_signals(market_data)

        # 聚合信號
        signal_adjustments = self._aggregate_signals()

        # 計算戰術調整
        tactical_adjustments = self._calculate_tactical_adjustments(
            signal_adjustments, strategic_weights
        )

        # 應用調整
        final_weights = self._apply_tactical_adjustments(
            strategic_weights, tactical_adjustments
        )

        # 計算覆蓋成本
        overlay_costs = self._calculate_overlay_costs(
            strategic_weights, final_weights, market_data
        )

        # 風險分析
        risk_analysis = self._analyze_overlay_risk(
            tactical_adjustments, market_data
        )

        # 信號摘要
        signal_summary = self._create_signal_summary()

        result = OverlayResult(
            timestamp=datetime.now(),
            strategic_weights=strategic_weights,
            tactical_adjustments=tactical_adjustments,
            final_weights=final_weights,
            active_signals=self.active_signals,
            signal_summary=signal_summary,
            overlay_costs=overlay_costs,
            total_overlay_cost=sum(overlay_costs.values()),
            cost_efficiency=self._calculate_cost_efficiency(overlay_costs, tactical_adjustments),
            overlay_risk_contribution=risk_analysis['risk_contribution'],
            expected_overlay_return=risk_analysis['expected_return'],
            overlay_sharpe=risk_analysis['sharpe_ratio']
        )

        logger.info(f"Tactical overlay applied. Total cost: {result.total_overlay_cost:.4f}")

        return result

    def _aggregate_signals(self) -> Dict[str, Dict[str, float]]:
        """聚合信號"""
        signal_adjustments = {}

        for symbol in self.base_allocator.assets.keys():
            symbol_signals = [
                signal for signal in self.active_signals
                if signal.asset_symbol == symbol
            ]

            if not symbol_signals:
                continue

            # 按信號類型分組
            type_groups = {}
            for signal in symbol_signals:
                if signal.signal_type not in type_groups:
                    type_groups[signal.signal_type] = []
                type_groups[signal.signal_type].append(signal)

            # 聚合每種類型的信號
            type_adjustments = {}
            for signal_type, signals in type_groups.items():
                if self.config.signal_aggregation_method == "weighted_average":
                    adjustment = self._weighted_average_aggregation(signals)
                elif self.config.signal_aggregation_method == "max_strength":
                    adjustment = self._max_strength_aggregation(signals)
                else:  # consensus
                    adjustment = self._consensus_aggregation(signals)

                type_adjustments[signal_type] = adjustment

            signal_adjustments[symbol] = type_adjustments

        return signal_adjustments

    def _weighted_average_aggregation(self, signals: List[OverlaySignal]) -> float:
        """加權平均聚合"""
        total_weight = 0
        weighted_sum = 0

        for signal in signals:
            weight = signal.confidence * signal.strength.value
            total_weight += weight
            weighted_sum += signal.direction * weight

        return weighted_sum / total_weight if total_weight > 0 else 0

    def _max_strength_aggregation(self, signals: List[OverlaySignal]) -> float:
        """最大強度聚合"""
        if not signals:
            return 0

        # 找到最強信號
        strongest_signal = max(signals, key=lambda s: s.strength.value * s.confidence)
        return strongest_signal.direction * strongest_signal.confidence

    def _consensus_aggregation(self, signals: List[OverlaySignal]) -> float:
        """共識聚合"""
        if not signals:
            return 0

        # 計算多空信號數量
        long_signals = [s for s in signals if s.direction > 0]
        short_signals = [s for s in signals if s.direction < 0]

        # 共識信號
        if len(long_signals) > len(short_signals) * 1.5:
            return min(0.5, len(long_signals) / len(signals))
        elif len(short_signals) > len(long_signals) * 1.5:
            return -min(0.5, len(short_signals) / len(signals))
        else:
            return 0  # 無明確共識

    def _calculate_tactical_adjustments(
        self,
        signal_adjustments: Dict[str, Dict[str, float]],
        strategic_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """計算戰術調整"""
        adjustments = {}

        for symbol, base_weight in strategic_weights.items():
            if symbol in signal_adjustments:
                type_adjustments = signal_adjustments[symbol]

                # 綜合所有信號類型的調整
                total_adjustment = 0
                total_weight = 0

                for signal_type, adjustment in type_adjustments.items():
                    type_weight = self._get_signal_type_weight(signal_type)
                    total_adjustment += adjustment * type_weight
                    total_weight += type_weight

                if total_weight > 0:
                    average_adjustment = total_adjustment / total_weight

                    # 應用調整限制
                    max_adjustment = self.config.max_overlay_adjustment * base_weight
                    limited_adjustment = np.clip(
                        average_adjustment,
                        -max_adjustment,
                        max_adjustment
                    )

                    adjustments[symbol] = limited_adjustment
                else:
                    adjustments[symbol] = 0
            else:
                adjustments[symbol] = 0

        return adjustments

    def _apply_tactical_adjustments(
        self,
        strategic_weights: Dict[str, float],
        tactical_adjustments: Dict[str, float]
    ) -> Dict[str, float]:
        """應用戰術調整"""
        final_weights = {}

        for symbol in strategic_weights.keys():
            base_weight = strategic_weights[symbol]
            adjustment = tactical_adjustments.get(symbol, 0)

            final_weight = base_weight + adjustment
            final_weights[symbol] = final_weight

        # 正規化權重
        total_weight = sum(final_weights.values())
        if total_weight > 0:
            final_weights = {k: v / total_weight for k, v in final_weights.items()}

        return final_weights

    def _calculate_overlay_costs(
        self,
        strategic_weights: Dict[str, float],
        final_weights: Dict[str, float],
        market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """計算覆蓋成本"""
        costs = {}

        for symbol in strategic_weights.keys():
            if symbol in final_weights:
                trade_size = final_weights[symbol] - strategic_weights[symbol]

                if abs(trade_size) > self.config.min_trade_size_overlay:
                    asset = self.base_allocator.assets[symbol]

                    # 計算成本
                    cost = abs(trade_size) * (
                        asset.commission_rate +
                        asset.bid_ask_spread / 2 +
                        asset.market_impact * abs(trade_size)
                    )

                    costs[symbol] = cost

        return costs

    def _analyze_overlay_risk(
        self,
        tactical_adjustments: Dict[str, float],
        market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """分析覆蓋風險"""
        # 簡化的風險分析
        total_adjustment = sum(abs(v) for v in tactical_adjustments.values())
        expected_return = total_adjustment * 0.1  # 假設10%的預期回報率
        risk_contribution = {k: abs(v) for k, v in tactical_adjustments.items()}

        # 簡化的Sharpe計算
        risk = total_adjustment * 0.2  # 假設20%的風險
        sharpe_ratio = expected_return / risk if risk > 0 else 0

        return {
            'risk_contribution': risk_contribution,
            'expected_return': expected_return,
            'sharpe_ratio': sharpe_ratio
        }

    def _create_signal_summary(self) -> Dict[str, Dict[str, float]]:
        """創建信號摘要"""
        summary = {}

        for symbol in self.base_allocator.assets.keys():
            symbol_signals = [
                signal for signal in self.active_signals
                if signal.asset_symbol == symbol
            ]

            if symbol_signals:
                # 按類型統計
                type_counts = {}
                total_strength = 0
                avg_confidence = 0

                for signal in symbol_signals:
                    signal_type = signal.signal_type.value
                    type_counts[signal_type] = type_counts.get(signal_type, 0) + 1
                    total_strength += signal.strength.value
                    avg_confidence += signal.confidence

                summary[symbol] = {
                    'signal_count': len(symbol_signals),
                    'type_distribution': type_counts,
                    'avg_strength': total_strength / len(symbol_signals),
                    'avg_confidence': avg_confidence / len(symbol_signals)
                }

        return summary

    def _calculate_cost_efficiency(
        self,
        costs: Dict[str, float],
        adjustments: Dict[str, float]
    ) -> float:
        """計算成本效率"""
        total_cost = sum(costs.values())
        total_adjustment = sum(abs(v) for v in adjustments.values())

        if total_adjustment > 0:
            return 1.0 - (total_cost / total_adjustment)
        else:
            return 1.0

# 便利函數
def apply_tactical_overlay_to_allocation(
    strategic_weights: Dict[str, float],
    assets: List[AssetConfig],
    market_data: Dict[str, pd.DataFrame],
    overlay_config: Optional[OverlayConfig] = None
) -> OverlayResult:
    """便利函數：應用戰術覆蓋到配置"""
    # 創建基礎配置器
    from .dynamic_allocator import DynamicAssetAllocator, AllocationConfig
    allocator = DynamicAssetAllocator(assets, AllocationConfig())

    # 創建覆蓋系統
    overlay_system = TacticalOverlaySystem(allocator, overlay_config)

    # 應用覆蓋
    return overlay_system.apply_tactical_overlay(strategic_weights, market_data)