"""
信號組合器
將多個信號源組合成最終的交易決策
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .signal_models import (
    MultiFactorSignal,
    SignalSource,
    SignalStrength,
    SignalType,
    TradingSignal,
)


class SignalCombiner:
    """
    智能信號組合器

    功能:
    - 整合多個信號源
    - 動態權重調整
    - 信號過濾和優化
    - 最終決策生成
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.logger = logging.getLogger("hk_quant_system.signal_combiner")

        # 信號歷史記錄
        self.signal_history: Dict[str, List[TradingSignal]] = {}

        # 權重配置
        self.weights = self.config.get(
            "weights",
            {
                SignalSource.TECHNICAL: 0.25,
                SignalSource.FUNDAMENTAL: 0.20,
                SignalSource.SENTIMENT: 0.15,
                SignalSource.QUANTITATIVE: 0.25,
                SignalSource.ML: 0.15,
            },
        )

        # 信號質量評估器
        self.quality_evaluator = SignalQualityEvaluator()

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "min_signal_strength": SignalStrength.MODERATE,
            "min_confidence": 60.0,
            "consensus_threshold": 0.6,  # 需要60 % 信號一致
            "max_age_hours": 24,
            "volatility_adjustment": True,
            "trend_filter": True,
            "weights": {
                SignalSource.TECHNICAL: 0.25,
                SignalSource.FUNDAMENTAL: 0.20,
                SignalSource.SENTIMENT: 0.15,
                SignalSource.QUANTITATIVE: 0.25,
                SignalSource.ML: 0.15,
            },
        }

    def combine_signals(
        self,
        symbol: str,
        signals: List[TradingSignal],
        current_price: float,
        market_trend: Optional[str] = None,
    ) -> TradingSignal:
        """
        組合多個信號生成最終決策

        Args:
            symbol: 股票代碼
            signals: 信號列表
            current_price: 當前價格
            market_trend: 市場趨勢 ("up", "down", "sideways")

        Returns:
            組合後的最終信號
        """
        if not signals:
            self.logger.warning(f"沒有信號用於組合: {symbol}")
            return self._create_hold_signal(symbol, current_price)

        self.logger.info(f"組合 {len(signals)} 個信號: {symbol}")

        # 過濾無效信號
        valid_signals = self._filter_signals(signals)

        if not valid_signals:
            self.logger.warning(f"沒有有效信號: {symbol}")
            return self._create_hold_signal(symbol, current_price)

        # 評估信號質量
        quality_scores = self.quality_evaluator.evaluate_signals(valid_signals)

        # 動態調整權重
        adjusted_weights = self._adjust_weights(valid_signals, quality_scores)

        # 計算加權分數
        weighted_score = self._calculate_weighted_score(valid_signals, adjusted_weights)

        # 計算一致性
        consensus = self._calculate_consensus(valid_signals)

        # 波動率調整
        if self.config.get("volatility_adjustment", True):
            weighted_score = self._apply_volatility_adjustment(
                weighted_score, valid_signals
            )

        # 趨勢過濾
        if self.config.get("trend_filter", True) and market_trend:
            weighted_score = self._apply_trend_filter(weighted_score, market_trend)

        # 創建最終信號
        final_signal = self._create_final_signal(
            symbol, weighted_score, current_price, valid_signals
        )

        # 記錄信號歷史
        self._record_signal(symbol, final_signal)

        self.logger.info(
            f"信號組合完成: {symbol}, "
            f"score={weighted_score:.2f}, "
            f"consensus={consensus:.2f}, "
            f"type={final_signal.signal_type.value}"
        )

        return final_signal

    def _filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """過濾無效或過期的信號"""
        filtered = []
        max_age = self.config.get("max_age_hours", 24)

        for signal in signals:
            # 檢查信號年齡
            age_hours = (datetime.now() - signal.timestamp).total_seconds() / 3600
            if age_hours > max_age:
                self.logger.debug(
                    f"過濾過期信號: {signal.symbol}, age={age_hours:.1f}h"
                )
                continue

            # 檢查信心度
            if signal.confidence < self.config.get("min_confidence", 60):
                self.logger.debug(
                    f"過濾低信心信號: {signal.symbol}, conf={signal.confidence}"
                )
                continue

            # 檢查信號強度
            min_strength = self.config.get(
                "min_signal_strength", SignalStrength.MODERATE
            )
            if signal.strength.value < min_strength.value:
                self.logger.debug(
                    f"過濾弱信號: {signal.symbol}, strength={signal.strength.name}"
                )
                continue

            filtered.append(signal)

        return filtered

    def _adjust_weights(
        self, signals: List[TradingSignal], quality_scores: Dict[str, float]
    ) -> Dict[SignalSource, float]:
        """根據信號質量動態調整權重"""
        adjusted_weights = self.weights.copy()

        # 根據質量分數調整權重
        for signal in signals:
            source = signal.source
            if source and source in quality_scores:
                quality_score = quality_scores.get(source.value, 1.0)
                # 質量高的信號獲得更高權重
                adjusted_weights[source] *= 0.5 + quality_score * 0.5

        # 標準化權重
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {
                k: v / total_weight for k, v in adjusted_weights.items()
            }

        return adjusted_weights

    def _calculate_weighted_score(
        self, signals: List[TradingSignal], weights: Dict[SignalSource, float]
    ) -> float:
        """計算加權分數"""
        signal_scores = {}
        source_scores = {}

        # 將信號轉換為分數 (-100 到 100)
        for signal in signals:
            score = self._signal_to_score(signal)
            source = signal.source

            if source not in source_scores:
                source_scores[source] = []
            source_scores[source].append(score)

        # 計算每個來源的平均分數
        for source, scores in source_scores.items():
            if scores:
                source_scores[source] = np.mean(scores)

        # 加權平均
        total_score = 0
        total_weight = 0

        for source, avg_score in source_scores.items():
            weight = weights.get(source, 0)
            total_score += weight * avg_score
            total_weight += weight

        if total_weight > 0:
            return total_score / total_weight
        else:
            return 50  # 中性分數

    def _signal_to_score(self, signal: TradingSignal) -> float:
        """將信號轉換為分數 (-100 到 100)"""
        # 基礎分數
        if signal.signal_type == SignalType.STRONG_BUY:
            base_score = 100
        elif signal.signal_type == SignalType.BUY:
            base_score = 75
        elif signal.signal_type == SignalType.HOLD:
            base_score = 50
        elif signal.signal_type == SignalType.SELL:
            base_score = 25
        elif signal.signal_type == SignalType.STRONG_SELL:
            base_score = 0
        else:
            base_score = 50

        # 調整強度
        strength_adjustment = (signal.strength.value - 3) * 10  # -20 到 +20
        base_score += strength_adjustment

        # 信心度調整
        confidence_adjustment = (signal.confidence - 50) * 0.4  # -20 到 +20
        base_score += confidence_adjustment

        # 風險調整
        risk_adjustment = (5 - signal.risk_score) * 5  # -25 到 +25
        base_score += risk_adjustment

        return max(0, min(100, base_score))

    def _calculate_consensus(self, signals: List[TradingSignal]) -> float:
        """計算信號一致性"""
        if not signals:
            return 0

        # 統計信號類型
        buy_count = sum(1 for s in signals if s.is_buy_signal)
        sell_count = sum(1 for s in signals if s.is_sell_signal)
        hold_count = sum(1 for s in signals if s.signal_type == SignalType.HOLD)

        total_count = len(signals)

        # 計算一致性比例
        if buy_count > sell_count:
            consensus = buy_count / total_count
        elif sell_count > buy_count:
            consensus = -sell_count / total_count
        else:
            consensus = 0

        return abs(consensus)

    def _apply_volatility_adjustment(
        self, score: float, signals: List[TradingSignal]
    ) -> float:
        """應用波動率調整"""
        if not signals:
            return score

        # 計算平均波動率
        avg_volatility = np.mean([s.volatility for s in signals if s.volatility > 0])

        if avg_volatility > 0:
            # 高波動率降低信心
            volatility_penalty = min(20, avg_volatility * 100)
            score = score - volatility_penalty

        return score

    def _apply_trend_filter(self, score: float, market_trend: str) -> float:
        """應用趨勢過濾"""
        # 如果市場趨勢明確，強化相應方向的信號
        if market_trend == "up":
            if score < 50:
                score -= 10  # 逆趨勢信號打折
            else:
                score += 5  # 順趨勢信號加強
        elif market_trend == "down":
            if score > 50:
                score += 10  # 逆趨勢信號打折
            else:
                score -= 5  # 順趨勢信號加強

        return max(0, min(100, score))

    def _create_hold_signal(self, symbol: str, current_price: float) -> TradingSignal:
        """創建持有信號"""
        return TradingSignal(
            symbol=symbol,
            timestamp=datetime.now(),
            signal_type=SignalType.HOLD,
            strength=SignalStrength.WEAK,
            current_price=current_price,
            confidence=0,
            source=None,
            reasons=["沒有明確信號"],
            factors={},
        )

    def _create_final_signal(
        self,
        symbol: str,
        score: float,
        current_price: float,
        component_signals: List[TradingSignal],
    ) -> TradingSignal:
        """創建最終信號"""
        # 確定信號類型
        if score >= 75:
            signal_type = SignalType.STRONG_BUY
            strength = SignalStrength.VERY_STRONG
        elif score >= 60:
            signal_type = SignalType.BUY
            strength = SignalStrength.STRONG
        elif score >= 40:
            signal_type = SignalType.HOLD
            strength = SignalStrength.MODERATE
        elif score >= 25:
            signal_type = SignalType.SELL
            strength = SignalStrength.STRONG
        else:
            signal_type = SignalType.STRONG_SELL
            strength = SignalStrength.VERY_STRONG

        # 收集所有理由
        all_reasons = []
        all_factors = {}

        for signal in component_signals:
            all_reasons.extend(signal.reasons)
            all_factors.update(signal.factors)

        # 計算平均風險分數
        avg_risk = np.mean([s.risk_score for s in component_signals])

        # 計算平均波動率
        avg_volatility = np.mean(
            [s.volatility for s in component_signals if s.volatility > 0]
        )

        # 計算預期收益 (簡化)
        expected_return = (score - 50) / 100 * 0.1  # 簡化計算

        return TradingSignal(
            symbol=symbol,
            timestamp=datetime.now(),
            signal_type=signal_type,
            strength=strength,
            current_price=current_price,
            confidence=min(100, abs(score)),
            source=SignalSource.HYBRID,
            reasons=list(set(all_reasons)),  # 去重
            factors=all_factors,
            risk_score=avg_risk,
            volatility=avg_volatility,
            expected_return=expected_return,
        )

    def _record_signal(self, symbol: str, signal: TradingSignal):
        """記錄信號歷史"""
        if symbol not in self.signal_history:
            self.signal_history[symbol] = []

        self.signal_history[symbol].append(signal)

        # 保持歷史記錄數量 (最近100個)
        if len(self.signal_history[symbol]) > 100:
            self.signal_history[symbol] = self.signal_history[symbol][-100:]

    def get_signal_history(self, symbol: str, hours: int = 24) -> List[TradingSignal]:
        """獲取信號歷史"""
        if symbol not in self.signal_history:
            return []

        cutoff_time = datetime.now().timestamp() - (hours * 3600)

        return [
            s
            for s in self.signal_history[symbol]
            if s.timestamp.timestamp() > cutoff_time
        ]

    def clear_history(self, symbol: Optional[str] = None):
        """清除信號歷史"""
        if symbol:
            self.signal_history.pop(symbol, None)
        else:
            self.signal_history.clear()


class SignalQualityEvaluator:
    """信號質量評估器"""

    def evaluate_signals(self, signals: List[TradingSignal]) -> Dict[str, float]:
        """
        評估信號質量

        返回每個信號來源的質量分數 (0 - 1)
        """
        quality_scores = {}

        # 按來源分組
        source_signals = {}
        for signal in signals:
            source = signal.source.value if signal.source else "unknown"
            if source not in source_signals:
                source_signals[source] = []
            source_signals[source].append(signal)

        # 評估每個來源
        for source, source_signal_list in source_signals.items():
            # 計算一致性
            consistency = self._calculate_consistency(source_signal_list)

            # 計算準確性 (基於歷史表現)
            accuracy = self._estimate_accuracy(source_signal_list)

            # 計算穩定性
            stability = self._calculate_stability(source_signal_list)

            # 綜合質量分數
            quality_scores[source] = (consistency + accuracy + stability) / 3

        return quality_scores

    def _calculate_consistency(self, signals: List[TradingSignal]) -> float:
        """計算信號一致性"""
        if len(signals) < 2:
            return 1.0

        # 轉換為分數
        scores = [self._signal_to_score(s) for s in signals]

        # 計算標準差
        std_dev = np.std(scores)

        # 轉換為一致性分數 (0 - 1)
        consistency = max(0, 1 - std_dev / 50)

        return consistency

    def _estimate_accuracy(self, signals: List[TradingSignal]) -> float:
        """估算準確性 (基於信心度和強度)"""
        if not signals:
            return 0.5

        # 考慮信心度和強度
        scores = []
        for signal in signals:
            confidence_score = signal.confidence / 100
            strength_score = signal.strength.value / 5
            scores.append((confidence_score + strength_score) / 2)

        return np.mean(scores)

    def _calculate_stability(self, signals: List[TradingSignal]) -> float:
        """計算穩定性"""
        if len(signals) < 2:
            return 1.0

        # 檢查信號類型變化
        signal_types = [s.signal_type for s in signals]

        # 計算類型變化頻率
        changes = 0
        for i in range(1, len(signal_types)):
            if signal_types[i] != signal_types[i - 1]:
                changes += 1

        change_rate = changes / (len(signal_types) - 1)

        # 穩定性 = 1 - 變化率
        stability = max(0, 1 - change_rate)

        return stability

    def _signal_to_score(self, signal: TradingSignal) -> float:
        """將信號轉換為分數"""
        if signal.signal_type == SignalType.STRONG_BUY:
            return 100
        elif signal.signal_type == SignalType.BUY:
            return 75
        elif signal.signal_type == SignalType.HOLD:
            return 50
        elif signal.signal_type == SignalType.SELL:
            return 25
        elif signal.signal_type == SignalType.STRONG_SELL:
            return 0
        else:
            return 50
