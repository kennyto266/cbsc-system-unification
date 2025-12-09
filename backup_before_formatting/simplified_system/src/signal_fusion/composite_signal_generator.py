#!/usr/bin/env python3
"""
簡化系統 - 綜合信號生成器
Simplified System - Composite Signal Generator

Phase 4.4: 綜合信號生成系統
- 實現CompositeSignalGenerator類
- 整合所有指標信號進行智能融合
- 計算綜合信號強度和方向
- 生成信號解釋和決策理由
- 實現信號質量評估和風險評級
- 創建信號可視化和報告系統
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
from enum import Enum

from .signal_generator import SignalGenerator, TradingSignal, SignalType
from .weight_manager import DynamicWeightManager
from .conflict_resolver import ConflictResolver, ConflictResolution

logger = logging.getLogger(__name__)

class SignalQuality(Enum):
    """信號質量等級"""
    EXCELLENT = "EXCELLENT"    # 90-100分
    GOOD = "GOOD"             # 80-89分
    FAIR = "FAIR"             # 70-79分
    POOR = "POOR"             # 60-69分
    VERY_POOR = "VERY_POOR"   # <60分

class RiskLevel(Enum):
    """風險等級"""
    VERY_LOW = "VERY_LOW"     # 1-2
    LOW = "LOW"               # 3-4
    MODERATE = "MODERATE"     # 5-6
    HIGH = "HIGH"             # 7-8
    VERY_HIGH = "VERY_HIGH"   # 9-10

@dataclass
class CompositeSignal:
    """綜合信號數據類"""
    # 基本信息
    symbol: str
    signal_type: SignalType
    strength: float  # 1-10
    confidence: float  # 0-1
    quality_score: float  # 0-100

    # 時間信息
    timestamp: datetime
    data_time: pd.Timestamp

    # 價格信息
    current_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

    # 風險評估
    risk_level: RiskLevel = RiskLevel.MODERATE
    risk_score: float = 5.0  # 1-10

    # 組成信號
    component_signals: List[TradingSignal] = field(default_factory=list)
    indicator_weights: Dict[str, float] = field(default_factory=dict)

    # 決策信息
    decision_reason: str = ""
    detailed_explanation: str = ""
    key_factors: List[str] = field(default_factory=list)

    # 性能預期
    expected_return: float = 0.0  # 預期回報
    holding_period: int = 5  # 預期持有天數
    success_probability: float = 0.5

    # 歷史對比
    similar_signal_performance: Dict[str, float] = field(default_factory=dict)

@dataclass
class SignalReport:
    """信號報告"""
    symbol: str
    report_time: datetime
    composite_signal: CompositeSignal
    market_context: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    recommendations: List[str]

class CompositeSignalGenerator:
    """
    綜合信號生成器

    核心功能：
    1. 整合多個技術指標信號
    2. 智能權重分配和衝突解決
    3. 生成綜合信號和決策建議
    4. 提供詳細的解釋和理由
    5. 評估信號質量和風險
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化綜合信號生成器"""
        self.config = config or self._get_default_config()

        # 初始化子系統
        self.signal_generator = SignalGenerator(config)
        self.weight_manager = DynamicWeightManager(config)
        self.conflict_resolver = ConflictResolver(config)

        # 信號歷史
        self.composite_signal_history: List[CompositeSignal] = []
        self.signal_reports: List[SignalReport] = []

        # 質量評估器
        self.quality_assessor = SignalQualityAssessor()

        # 風險評估器
        self.risk_assessor = SignalRiskAssessor()

        logger.info("Composite Signal Generator initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            'fusion_parameters': {
                'min_component_signals': 2,
                'max_component_signals': 10,
                'consensus_threshold': 0.6,
                'diversity_bonus': 0.1,
                'confidence_threshold': 0.5
            },
            'quality_thresholds': {
                'excellent': 90,
                'good': 80,
                'fair': 70,
                'poor': 60
            },
            'risk_parameters': {
                'risk_free_rate': 0.03,
                'volatility_lookback': 20,
                'max_position_size': 0.1,
                'stop_loss_multiplier': 2.0
            },
            'interpretation': {
                'enable_explanations': True,
                'enable_visualization': True,
                'include_market_context': True,
                'detail_level': 'comprehensive'
            }
        }

    def generate_composite_signal(
        self,
        symbol: str = None,
        data: pd.DataFrame = None,
        indicators: Dict[str, Any] = None,
        weights: Optional[Dict[str, float]] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Union[CompositeSignal, Dict]:
        """
        生成綜合信號

        Args:
            symbol: 股票代碼 (可選，用於兼容性)
            data: OHLCV數據 (可選，用於兼容性)
            indicators: 技術指標數據 (可選，用於兼容性)
            weights: 自定義權重
            custom_params: 自定義參數

        Returns:
            綜合信號
        """

        # 兼容性處理：如果只提供data參數，自動生成symbol和indicators
        if data is not None and symbol is None and indicators is None:
            symbol = "AUTO_SYMBOL"
            indicators = {}

            # 自動生成基本指標
            from src.indicators.core_indicators import CoreIndicators
            core_indicators = CoreIndicators()

            # 計算RSI
            try:
                rsi = core_indicators.calculate_rsi(data['close'], 14)
                indicators['RSI'] = {
                    'signal': 'HOLD' if 40 <= rsi.iloc[-1] <= 60 else ('BUY' if rsi.iloc[-1] < 40 else 'SELL'),
                    'strength': 5.0,
                    'confidence': 0.7
                }
            except:
                indicators['RSI'] = {'signal': 'HOLD', 'strength': 5.0, 'confidence': 0.5}

            # 計算MACD
            try:
                macd = core_indicators.calculate_macd(data['close'], 12, 26, 9)
                indicators['MACD'] = {
                    'signal': 'HOLD',
                    'strength': 5.0,
                    'confidence': 0.6
                }
            except:
                indicators['MACD'] = {'signal': 'HOLD', 'strength': 5.0, 'confidence': 0.5}

        try:
            # 1. 生成基礎信號
            base_signals = self.signal_generator.generate_signals(symbol, data, indicators)

            if len(base_signals) < self.config['fusion_parameters']['min_component_signals']:
                logger.warning(f"Insufficient signals for {symbol}: {len(base_signals)} < {self.config['fusion_parameters']['min_component_signals']}")
                return self._create_default_signal(symbol, data)

            # 2. 獲取權重配置
            if weights is None:
                weights = self.weight_manager.get_weights(symbol)

            # 3. 檢測和解決衝突
            conflicts = self.conflict_resolver.detect_conflicts(base_signals)
            if conflicts:
                resolutions = self.conflict_resolver.resolve_conflicts(conflicts, weights=weights)
                base_signals = self._apply_conflict_resolutions(base_signals, resolutions)

            # 4. 計算加權信號
            weighted_signal = self._calculate_weighted_signal(base_signals, weights)

            # 5. 評估信號質量
            quality_score = self.quality_assessor.assess_quality(weighted_signal, base_signals, data)

            # 6. 評估風險
            risk_score, risk_level = self.risk_assessor.assess_risk(weighted_signal, data)

            # 7. 生成決策解釋
            explanation = self._generate_explanation(weighted_signal, base_signals, weights, data)

            # 8. 計算性能預期
            expected_metrics = self._calculate_expected_metrics(weighted_signal, data)

            # 9. 創建綜合信號
            composite_signal = CompositeSignal(
                symbol=symbol,
                signal_type=weighted_signal['signal_type'],
                strength=weighted_signal['strength'],
                confidence=weighted_signal['confidence'],
                quality_score=quality_score,
                timestamp=datetime.now(),
                data_time=data.index[-1],
                current_price=float(data['close'].iloc[-1]),
                target_price=self._calculate_target_price(weighted_signal, data),
                stop_loss=self._calculate_stop_loss(weighted_signal, data),
                risk_level=risk_level,
                risk_score=risk_score,
                component_signals=base_signals,
                indicator_weights=weights,
                decision_reason=explanation['reason'],
                detailed_explanation=explanation['detailed'],
                key_factors=explanation['key_factors'],
                expected_return=expected_metrics['return'],
                holding_period=expected_metrics['period'],
                success_probability=expected_metrics['probability'],
                similar_signal_performance=self._find_similar_signals(weighted_signal)
            )

            # 10. 更新歷史記錄
            self.composite_signal_history.append(composite_signal)

            logger.info(f"Generated composite signal for {symbol}: {weighted_signal['signal_type'].value}")
            return composite_signal

        except Exception as e:
            logger.error(f"Error generating composite signal for {symbol}: {e}")
            return self._create_default_signal(symbol, data)

    def _create_default_signal(self, symbol: str, data: pd.DataFrame) -> CompositeSignal:
        """創建默認信號"""
        # 安全檢查數據
        if data is None or not isinstance(data, pd.DataFrame) or len(data) == 0:
            symbol_str = "UNKNOWN" if symbol is None else str(symbol)
            return CompositeSignal(
                symbol=symbol_str,
                signal_type=SignalType.HOLD,
                strength=5.0,
                confidence=0.5,
                quality_score=50.0,
                timestamp=datetime.now(),
                data_time=datetime.now(),
                current_price=0.0,
                risk_level=RiskLevel.MODERATE,
                risk_score=5.0,
                decision_reason="無有效數據生成決策",
                detailed_explanation="由於缺乏有效的市場數據，系統採取保守的持倉策略。",
                key_factors=["數據無效"],
                success_probability=0.5
            )

        # 安全檢查並創建正常信號
        try:
            return CompositeSignal(
                symbol=symbol,
                signal_type=SignalType.HOLD,
                strength=5.0,
                confidence=0.5,
                quality_score=50.0,
                timestamp=datetime.now(),
                data_time=data.index[-1],
                current_price=float(data['close'].iloc[-1]) if 'close' in data.columns else 0.0,
                risk_level=RiskLevel.MODERATE,
                risk_score=5.0,
                decision_reason="無足夠信號生成決策",
                detailed_explanation="由於缺乏足夠的技術指標信號，系統採取保守的持倉策略。",
                key_factors=["信號不足"],
                success_probability=0.5
            )
        except Exception as e:
            logger.error(f"Error creating default signal: {e}")
            # 返回最簡單的HOLD信號
            symbol_str = "UNKNOWN" if symbol is None else str(symbol)
            return CompositeSignal(
                symbol=symbol_str,
                signal_type=SignalType.HOLD,
                strength=5.0,
                confidence=0.5,
                quality_score=50.0,
                timestamp=datetime.now(),
                data_time=datetime.now(),
                current_price=0.0,
                risk_level=RiskLevel.MODERATE,
                risk_score=5.0,
                decision_reason="系統錯誤 - 保守持倉",
                detailed_explanation="系統遇到錯誤，採取最保守的持倉策略。",
                key_factors=["系統錯誤"],
                success_probability=0.5
            )

    def _calculate_weighted_signal(
        self,
        signals: List[TradingSignal],
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """計算加權信號"""
        if not signals:
            return {
                'signal_type': SignalType.HOLD,
                'strength': 5.0,
                'confidence': 0.5
            }

        # 按信號類型分組
        signal_groups = {}
        for signal in signals:
            if signal.signal_type not in signal_groups:
                signal_groups[signal.signal_type] = []
            signal_groups[signal.signal_type].append(signal)

        # 計算每種信號類型的加權分數
        type_scores = {}
        for signal_type, group_signals in signal_groups.items():
            total_weighted_score = 0
            total_weight = 0

            for signal in group_signals:
                indicator_weight = weights.get(signal.indicator_name, 0.1)
                weighted_score = signal.strength * signal.confidence * indicator_weight

                total_weighted_score += weighted_score
                total_weight += indicator_weight

            if total_weight > 0:
                type_scores[signal_type] = total_weighted_score / total_weight

        # 選擇得分最高的信號類型
        if not type_scores:
            return {
                'signal_type': SignalType.HOLD,
                'strength': 5.0,
                'confidence': 0.5
            }

        best_type = max(type_scores, key=type_scores.get)
        best_score = type_scores[best_type]

        # 計算最終強度和置信度
        best_signals = signal_groups[best_type]
        final_strength = np.mean([s.strength for s in best_signals])
        final_confidence = np.mean([s.confidence for s in best_signals])

        # 應用共識加成
        consensus_ratio = len(best_signals) / len(signals)
        if consensus_ratio > self.config['fusion_parameters']['consensus_threshold']:
            final_confidence *= (1 + self.config['fusion_parameters']['diversity_bonus'])

        final_confidence = min(1.0, final_confidence)

        return {
            'signal_type': best_type,
            'strength': final_strength,
            'confidence': final_confidence
        }

    def _apply_conflict_resolutions(
        self,
        signals: List[TradingSignal],
        resolutions: List[ConflictResolution]
    ) -> List[TradingSignal]:
        """應用衝突解決結果"""
        if not resolutions:
            return signals

        # 創建解決結果映射
        resolution_map = {r.conflict_id: r for r in resolutions}

        # 處理每個衝突
        modified_signals = []
        processed_conflicts = set()

        for signal in signals:
            # 檢查信號是否涉及衝突
            signal_conflict = None
            for conflict_id, resolution in resolution_map.items():
                if conflict_id not in processed_conflicts:
                    # 檢查信號是否在衝突中
                    if signal in resolution.conflict_resolver.conflicting_signals:
                        signal_conflict = resolution
                        processed_conflicts.add(conflict_id)
                        break

            if signal_conflict:
                # 替換為解決後的信號
                modified_signal = TradingSignal(
                    symbol=signal.symbol,
                    indicator_name=f"RESOLVED_{signal_conflict.resolution_strategy.value}",
                    signal_type=signal_conflict.final_signal_type,
                    strength=signal_conflict.final_strength,
                    confidence=signal_conflict.final_confidence,
                    timestamp=signal.timestamp,
                    data_time=signal.data_time,
                    indicator_value=signal.indicator_value,
                    trigger_price=signal.trigger_price,
                    trigger_conditions={
                        'original_signal': signal.indicator_name,
                        'resolution_strategy': signal_conflict.resolution_strategy.value,
                        'resolution_reason': signal_conflict.resolution_reason
                    },
                    reason=signal_conflict.resolution_reason,
                    explanation=f"原信號{signal.indicator_name}通過{signal_conflict.resolution_strategy.value}解決衝突"
                )
                modified_signals.append(modified_signal)
            else:
                modified_signals.append(signal)

        return modified_signals

    def _calculate_target_price(
        self,
        weighted_signal: Dict[str, Any],
        data: pd.DataFrame
    ) -> Optional[float]:
        """計算目標價格"""
        current_price = float(data['close'].iloc[-1])

        # 基於信號強度和類型計算目標價格
        if weighted_signal['signal_type'] == SignalType.BUY:
            # 買入信號：計算上漲目標
            strength_factor = weighted_signal['strength'] / 10.0
            confidence_factor = weighted_signal['confidence']

            # 使用ATR計算目標價格（如果有ATR數據）
            atr = data.get('ATR', pd.Series([current_price * 0.02])).iloc[-1] if 'ATR' in data else current_price * 0.02

            target_multiplier = 1 + (strength_factor * confidence_factor * 2 + 1)  # 1-3倍ATR
            target_price = current_price + atr * target_multiplier

        elif weighted_signal['signal_type'] == SignalType.SELL:
            # 賣出信號：計算下跌目標
            strength_factor = weighted_signal['strength'] / 10.0
            confidence_factor = weighted_signal['confidence']

            atr = data.get('ATR', pd.Series([current_price * 0.02])).iloc[-1] if 'ATR' in data else current_price * 0.02

            target_multiplier = strength_factor * confidence_factor * 2 + 1  # 1-3倍ATR
            target_price = current_price - atr * target_multiplier

        else:
            # HOLD信號：不設目標價格
            target_price = None

        return target_price

    def _calculate_stop_loss(
        self,
        weighted_signal: Dict[str, Any],
        data: pd.DataFrame
    ) -> Optional[float]:
        """計算止損價格"""
        current_price = float(data['close'].iloc[-1])
        risk_multiplier = self.config['risk_parameters']['stop_loss_multiplier']

        # 使用ATR計算止損
        atr = data.get('ATR', pd.Series([current_price * 0.02])).iloc[-1] if 'ATR' in data else current_price * 0.02

        if weighted_signal['signal_type'] == SignalType.BUY:
            # 買入信號：設置下方止損
            stop_loss = current_price - atr * risk_multiplier
        elif weighted_signal['signal_type'] == SignalType.SELL:
            # 賣出信號：設置上方止損
            stop_loss = current_price + atr * risk_multiplier
        else:
            # HOLD信號：不設止損
            stop_loss = None

        return stop_loss

    def _generate_explanation(
        self,
        weighted_signal: Dict[str, Any],
        base_signals: List[TradingSignal],
        weights: Dict[str, float],
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """生成決策解釋"""
        signal_type = weighted_signal['signal_type']
        strength = weighted_signal['strength']
        confidence = weighted_signal['confidence']

        # 基本原因
        if signal_type == SignalType.BUY:
            reason = f"買入信號：強度{strength:.1f}/10，置信度{confidence:.1%}"
        elif signal_type == SignalType.SELL:
            reason = f"賣出信號：強度{strength:.1f}/10，置信度{confidence:.1%}"
        else:
            reason = f"持有信號：強度{strength:.1f}/10，置信度{confidence:.1%}"

        # 關鍵因素
        key_factors = []

        # 分析主要支持信號
        supporting_signals = [s for s in base_signals if s.signal_type == signal_type]
        if supporting_signals:
            # 找出權重最大的指標
            top_signals = sorted(
                supporting_signals,
                key=lambda s: weights.get(s.indicator_name, 0) * s.strength * s.confidence,
                reverse=True
            )[:3]

            for signal in top_signals:
                factor = f"{signal.indicator_name}: {signal.reason}"
                key_factors.append(factor)

        # 市場背景因素
        current_price = float(data['close'].iloc[-1])
        if len(data) > 1:
            price_change = (current_price / float(data['close'].iloc[-2]) - 1) * 100
            if abs(price_change) > 2:
                key_factors.append(f"價格變動: {price_change:+.1f}%")

        # 詳細解釋
        detailed_parts = [
            f"綜合分析{len(base_signals)}個技術指標信號",
            f"主要決策基於{len(supporting_signals)}個{signal_type.value}信號",
            f"平均信號強度: {strength:.1f}/10",
            f"綜合置信度: {confidence:.1%}",
            f"信號共識度: {len(supporting_signals)/len(base_signals):.1%}"
        ]

        # 添加主要指標的詳細信息
        if supporting_signals:
            detailed_parts.append("\n主要支持指標:")
            for signal in supporting_signals[:3]:
                weight = weights.get(signal.indicator_name, 0)
                detailed_parts.append(
                    f"  - {signal.indicator_name} (權重{weight:.2f}): {signal.explanation}"
                )

        detailed_explanation = "\n".join(detailed_parts)

        return {
            'reason': reason,
            'detailed': detailed_explanation,
            'key_factors': key_factors
        }

    def _calculate_expected_metrics(
        self,
        weighted_signal: Dict[str, Any],
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """計算預期指標"""
        signal_type = weighted_signal['signal_type']
        strength = weighted_signal['strength'] / 10.0
        confidence = weighted_signal['confidence']

        # 基於信號強度和歷史數據計算預期回報
        if signal_type == SignalType.BUY:
            base_return = 0.05  # 5%基礎回報
            expected_return = base_return * strength * confidence
            holding_period = int(5 + strength * 10)  # 5-15天
        elif signal_type == SignalType.SELL:
            base_return = 0.03  # 3%基礎回報（做空通常回報較低）
            expected_return = base_return * strength * confidence
            holding_period = int(3 + strength * 7)   # 3-10天
        else:
            expected_return = 0.0
            holding_period = 1

        # 成功概率基於置信度
        success_probability = confidence

        # 考慮市場波動率
        if len(data) > 20:
            returns = data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # 年化波動率
            if volatility > 0.3:  # 高波動率市場
                success_probability *= 0.9
                expected_return *= 0.8
            elif volatility < 0.15:  # 低波動率市場
                success_probability *= 1.1
                expected_return *= 1.1

        success_probability = max(0.1, min(0.9, success_probability))

        return {
            'return': expected_return,
            'period': holding_period,
            'probability': success_probability
        }

    def _find_similar_signals(self, weighted_signal: Dict[str, Any]) -> Dict[str, float]:
        """尋找類似信號的歷史表現"""
        # 簡化實現：基於信號類型和強度查找歷史類似信號
        signal_type = weighted_signal['signal_type']
        strength = weighted_signal['strength']

        similar_signals = [
            signal for signal in self.composite_signal_history
            if signal.signal_type == signal_type and
            abs(signal.strength - strength) < 2.0  # 強度差異小於2
        ]

        if not similar_signals:
            return {'count': 0, 'avg_return': 0.0, 'success_rate': 0.5}

        # 計算歷史表現
        returns = [s.expected_return for s in similar_signals]
        avg_return = np.mean(returns)
        success_rate = np.mean([s.success_probability for s in similar_signals])

        return {
            'count': len(similar_signals),
            'avg_return': avg_return,
            'success_rate': success_rate
        }

    def generate_signal_report(
        self,
        composite_signal: CompositeSignal,
        data: pd.DataFrame,
        market_context: Optional[Dict[str, Any]] = None
    ) -> SignalReport:
        """生成信號報告"""
        # 技術分析摘要
        technical_analysis = {
            'signal_type': composite_signal.signal_type.value,
            'strength_score': composite_signal.strength,
            'confidence_level': composite_signal.confidence,
            'quality_rating': self._get_quality_rating(composite_signal.quality_score),
            'key_indicators': [
                {
                    'name': signal.indicator_name,
                    'signal': signal.signal_type.value,
                    'strength': signal.strength,
                    'confidence': signal.confidence
                }
                for signal in composite_signal.component_signals[:5]
            ]
        }

        # 風險分析
        risk_analysis = {
            'risk_level': composite_signal.risk_level.value,
            'risk_score': composite_signal.risk_score,
            'stop_loss': composite_signal.stop_loss,
            'potential_loss': abs(composite_signal.stop_loss - composite_signal.current_price) if composite_signal.stop_loss else 0,
            'position_size_recommendation': self._calculate_position_size(composite_signal)
        }

        # 市場背景
        if market_context is None:
            market_context = self._generate_market_context(data)

        # 生成建議
        recommendations = self._generate_recommendations(composite_signal, market_context)

        report = SignalReport(
            symbol=composite_signal.symbol,
            report_time=datetime.now(),
            composite_signal=composite_signal,
            market_context=market_context,
            technical_analysis=technical_analysis,
            risk_analysis=risk_analysis,
            recommendations=recommendations
        )

        self.signal_reports.append(report)
        return report

    def _get_quality_rating(self, score: float) -> str:
        """獲取質量等級"""
        thresholds = self.config['quality_thresholds']
        if score >= thresholds['excellent']:
            return SignalQuality.EXCELLENT.value
        elif score >= thresholds['good']:
            return SignalQuality.GOOD.value
        elif score >= thresholds['fair']:
            return SignalQuality.FAIR.value
        elif score >= thresholds['poor']:
            return SignalQuality.POOR.value
        else:
            return SignalQuality.VERY_POOR.value

    def _calculate_position_size(self, signal: CompositeSignal) -> float:
        """計算建議倉位大小"""
        # 基於凱利公式的簡化版本
        win_prob = signal.success_probability
        avg_return = abs(signal.expected_return)
        risk_loss = abs(signal.stop_loss - signal.current_price) / signal.current_price if signal.stop_loss else 0.05

        if risk_loss == 0:
            return 0.1  # 默認10%

        # 簡化凱利公式
        kelly_fraction = (win_prob * avg_return - (1 - win_prob) * risk_loss) / risk_loss

        # 限制倉位大小
        max_position = self.config['risk_parameters']['max_position_size']
        position_size = max(0.01, min(max_position, kelly_fraction * 0.5))  # 保守因子0.5

        return position_size

    def _generate_market_context(self, data: pd.DataFrame) -> Dict[str, Any]:
        """生成市場背景"""
        if len(data) < 2:
            return {'status': 'insufficient_data'}

        current_price = float(data['close'].iloc[-1])
        prev_price = float(data['close'].iloc[-2])
        price_change = (current_price / prev_price - 1) * 100

        # 計算波動率
        if len(data) >= 20:
            returns = data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
        else:
            volatility = 0.2

        # 趨勢分析
        if len(data) >= 50:
            ma_20 = data['close'].rolling(20).mean().iloc[-1]
            ma_50 = data['close'].rolling(50).mean().iloc[-1]
            trend = "UP" if current_price > ma_20 > ma_50 else "DOWN" if current_price < ma_20 < ma_50 else "SIDEWAYS"
        else:
            trend = "UNKNOWN"

        return {
            'current_price': current_price,
            'price_change_pct': price_change,
            'volatility': volatility,
            'trend': trend,
            'data_points': len(data),
            'time_range': f"{data.index[0].date()} to {data.index[-1].date()}"
        }

    def _generate_recommendations(self, signal: CompositeSignal, market_context: Dict[str, Any]) -> List[str]:
        """生成操作建議"""
        recommendations = []

        if signal.signal_type == SignalType.BUY:
            recommendations.append(f"建議買入 {signal.symbol}，目標價格 {signal.target_price:.2f}")
            if signal.stop_loss:
                recommendations.append(f"設置止損價格 {signal.stop_loss:.2f}")
            recommendations.append(f"建議倉位大小：{signal.expected_return:.1%}")
        elif signal.signal_type == SignalType.SELL:
            recommendations.append(f"建議賣出 {signal.symbol}，目標價格 {signal.target_price:.2f}")
            if signal.stop_loss:
                recommendations.append(f"設置止損價格 {signal.stop_loss:.2f}")
        else:
            recommendations.append(f"建議持倉觀望 {signal.symbol}")

        # 基於質量的建議
        if signal.quality_score >= 80:
            recommendations.append("信號質量優秀，可考慮執行")
        elif signal.quality_score >= 60:
            recommendations.append("信號質量良好，但需謹慎")
        else:
            recommendations.append("信號質量較差，建議等待更佳時機")

        # 基於風險的建議
        if signal.risk_score >= 8:
            recommendations.append("風險較高，請控制倉位大小")
        elif signal.risk_score <= 3:
            recommendations.append("風險較低，可適度增加倉位")

        return recommendations

class SignalQualityAssessor:
    """信號質量評估器"""

    def assess_quality(
        self,
        weighted_signal: Dict[str, Any],
        base_signals: List[TradingSignal],
        data: pd.DataFrame
    ) -> float:
        """評估信號質量 (0-100)"""
        quality_score = 50  # 基礎分數

        # 信號一致性 (+20)
        if len(base_signals) > 0:
            signal_types = [s.signal_type for s in base_signals]
            most_common_count = max(signal_types.count(st) for st in set(signal_types))
            consistency_score = (most_common_count / len(base_signals)) * 20
            quality_score += consistency_score

        # 信號強度 (+15)
        avg_strength = np.mean([s.strength for s in base_signals]) if base_signals else 5
        strength_score = (avg_strength / 10) * 15
        quality_score += strength_score

        # 置信度 (+15)
        avg_confidence = np.mean([s.confidence for s in base_signals]) if base_signals else 0.5
        confidence_score = avg_confidence * 15
        quality_score += confidence_score

        # 指標多樣性 (+10)
        indicator_types = len(set(s.indicator_name for s in base_signals)) if base_signals else 1
        diversity_score = min(10, indicator_types * 2)
        quality_score += diversity_score

        # 數據質量 (+10)
        data_quality = min(10, len(data) / 50)  # 基於數據點數量
        quality_score += data_quality

        return max(0, min(100, quality_score))

class SignalRiskAssessor:
    """信號風險評估器"""

    def assess_risk(
        self,
        weighted_signal: Dict[str, Any],
        data: pd.DataFrame
    ) -> Tuple[float, RiskLevel]:
        """評估風險等級"""
        risk_score = 5  # 基礎風險分數

        # 基於信號類型的風險
        if weighted_signal['signal_type'] == SignalType.BUY:
            signal_risk = 2
        elif weighted_signal['signal_type'] == SignalType.SELL:
            signal_risk = 4  # 做空通常風險更高
        else:
            signal_risk = 1

        risk_score += signal_risk

        # 基於信號強度的風險
        strength_risk = (10 - weighted_signal['strength']) / 2  # 強信號風險較低
        risk_score += strength_risk

        # 基於市場波動率的風險
        if len(data) >= 20:
            returns = data['close'].pct_change().dropna()
            volatility = returns.std()
            volatility_risk = min(5, volatility * 50)  # 標準化波動率風險
            risk_score += volatility_risk

        # 確定風險等級
        risk_score = max(1, min(10, risk_score))

        if risk_score <= 2:
            risk_level = RiskLevel.VERY_LOW
        elif risk_score <= 4:
            risk_level = RiskLevel.LOW
        elif risk_score <= 6:
            risk_level = RiskLevel.MODERATE
        elif risk_score <= 8:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH

        return risk_score, risk_level

# 全局實例
composite_signal_generator = CompositeSignalGenerator()

# 便利函數
def generate_composite_signal(symbol: str, data: pd.DataFrame, indicators: Dict[str, Any]) -> CompositeSignal:
    """便利函數：生成綜合信號"""
    return composite_signal_generator.generate_composite_signal(symbol, data, indicators)