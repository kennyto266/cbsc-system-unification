"""
適應性市場系統 - Phase 3核心實現
Market Regime Detection and Adaptive Parameter Adjustment
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
import json

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """市場狀況枚舉"""
    BULL_MARKET = "bull_market"      # 牛市
    BEAR_MARKET = "bear_market"      # 熊市
    SIDEWAYS = "sideways"            # 震盪市
    HIGH_VOLATILITY = "high_volatility"  # 高波動
    LOW_VOLATILITY = "low_volatility"    # 低波動

@dataclass
class MarketState:
    """市場狀態數據結構"""
    regime: MarketRegime
    volatility_level: float
    trend_strength: float
    momentum_score: float
    confidence: float
    last_updated: datetime

@dataclass
class AdaptiveParameters:
    """適應性參數配置"""
    rsi_periods: List[int]
    macd_params: Tuple[int, int, int]
    bollinger_periods: List[int]
    bollinger_std: List[float]
    regime_weights: Dict[str, float]
    sensitivity_level: float

class MarketRegimeDetector:
    """市場狀況檢測器"""

    def __init__(self, lookback_period: int = 60):
        self.lookback_period = lookback_period
        self.min_data_points = 20

    def detect_market_regime(self, price_data: pd.Series,
                           volume_data: Optional[pd.Series] = None) -> MarketState:
        """
        檢測當前市場狀況

        Args:
            price_data: 價格數據序列
            volume_data: 可選的成交量數據

        Returns:
            MarketState: 市場狀態對象
        """
        if len(price_data) < self.min_data_points:
            logger.warning(f"數據不足 ({len(price_data)} < {self.min_data_points}), 使用默認狀態")
            return MarketState(
                regime=MarketRegime.SIDEWAYS,
                volatility_level=0.3,
                trend_strength=0.0,
                momentum_score=0.0,
                confidence=0.1,
                last_updated=datetime.now()
            )

        # 計算關鍵指標
        returns = price_data.pct_change().dropna()
        volatility = returns.rolling(20).std().iloc[-1]
        trend = self._calculate_trend_strength(price_data)
        momentum = self._calculate_momentum(price_data)

        # 檢測市場狀況
        regime = self._classify_regime(volatility, trend, momentum)
        confidence = self._calculate_confidence(volatility, trend, momentum)

        return MarketState(
            regime=regime,
            volatility_level=float(volatility),
            trend_strength=float(trend),
            momentum_score=float(momentum),
            confidence=float(confidence),
            last_updated=datetime.now()
        )

    def _calculate_trend_strength(self, price_data: pd.Series) -> float:
        """計算趨勢強度"""
        # 使用線性回歸計算趨勢
        x = np.arange(len(price_data))
        y = price_data.values

        # 標準化
        x = (x - x.mean()) / x.std()
        y = (y - y.mean()) / y.std()

        # 計算相關係數作為趨勢強度
        correlation = np.corrcoef(x, y)[0, 1]
        return correlation

    def _calculate_momentum(self, price_data: pd.Series) -> float:
        """計算動量指標"""
        # 短期vs長期回報比較
        short_return = (price_data.iloc[-1] / price_data.iloc[-10] - 1) if len(price_data) > 10 else 0
        long_return = (price_data.iloc[-1] / price_data.iloc[-30] - 1) if len(price_data) > 30 else 0

        # 動量 = 短期動量 + 長期趨勢
        momentum = (short_return * 0.7 + long_return * 0.3)
        return momentum

    def _classify_regime(self, volatility: float, trend: float, momentum: float) -> MarketRegime:
        """根據指標分類市場狀況"""

        # 高波動檢測
        if volatility > 0.04:
            return MarketRegime.HIGH_VOLATILITY

        # 低波動檢測
        if volatility < 0.015:
            return MarketRegime.LOW_VOLATILITY

        # 趨勢檢測
        if abs(trend) > 0.3:
            if trend > 0 and momentum > 0.02:
                return MarketRegime.BULL_MARKET
            elif trend < 0 and momentum < -0.02:
                return MarketRegime.BEAR_MARKET

        # 默認震盪市
        return MarketRegime.SIDEWAYS

    def _calculate_confidence(self, volatility: float, trend: float, momentum: float) -> float:
        """計算檢測置信度"""
        # 基於指標一致性計算置信度
        trend_confidence = min(abs(trend) * 2, 1.0)
        volatility_confidence = min(volatility * 30, 1.0)
        momentum_confidence = min(abs(momentum) * 20, 1.0)

        # 加權平均
        confidence = (trend_confidence * 0.4 +
                     volatility_confidence * 0.3 +
                     momentum_confidence * 0.3)

        return confidence

class AdaptiveParameterOptimizer:
    """適應性參數優化器"""

    def __init__(self):
        self.regime_parameters = self._initialize_regime_parameters()

    def _initialize_regime_parameters(self) -> Dict[MarketRegime, AdaptiveParameters]:
        """初始化不同市場狀況的參數配置"""
        return {
            MarketRegime.BULL_MARKET: AdaptiveParameters(
                rsi_periods=[14, 21],
                macd_params=(12, 26, 9),
                bollinger_periods=[20],
                bollinger_std=[2.0, 2.5],
                regime_weights={"trend": 0.6, "momentum": 0.3, "volatility": 0.1},
                sensitivity_level=0.7
            ),
            MarketRegime.BEAR_MARKET: AdaptiveParameters(
                rsi_periods=[7, 14, 21],
                macd_params=(5, 13, 5),
                bollinger_periods=[10, 20],
                bollinger_std=[1.5, 2.0, 2.5],
                regime_weights={"trend": 0.4, "momentum": 0.2, "volatility": 0.4},
                sensitivity_level=0.9
            ),
            MarketRegime.SIDEWAYS: AdaptiveParameters(
                rsi_periods=[14, 28],
                macd_params=(8, 17, 9),
                bollinger_periods=[20, 30],
                bollinger_std=[2.0],
                regime_weights={"trend": 0.2, "momentum": 0.5, "volatility": 0.3},
                sensitivity_level=0.5
            ),
            MarketRegime.HIGH_VOLATILITY: AdaptiveParameters(
                rsi_periods=[5, 10, 14],
                macd_params=(3, 8, 3),
                bollinger_periods=[10, 15],
                bollinger_std=[2.5, 3.0],
                regime_weights={"trend": 0.3, "momentum": 0.3, "volatility": 0.4},
                sensitivity_level=1.0
            ),
            MarketRegime.LOW_VOLATILITY: AdaptiveParameters(
                rsi_periods=[21, 28],
                macd_params=(21, 50, 21),
                bollinger_periods=[20, 30, 50],
                bollinger_std=[1.8, 2.0],
                regime_weights={"trend": 0.5, "momentum": 0.4, "volatility": 0.1},
                sensitivity_level=0.3
            )
        }

    def get_optimal_parameters(self, market_state: MarketState) -> AdaptiveParameters:
        """根據市場狀態獲取最優參數"""
        base_params = self.regime_parameters[market_state.regime]

        # 根據置信度調整參數
        confidence_adjustment = market_state.confidence

        # 動態調整敏感度
        adjusted_sensitivity = base_params.sensitivity_level * (0.7 + confidence_adjustment * 0.6)

        # 創建調整後的參數
        adjusted_params = AdaptiveParameters(
            rsi_periods=base_params.rsi_periods.copy(),
            macd_params=base_params.macd_params,
            bollinger_periods=base_params.bollinger_periods.copy(),
            bollinger_std=base_params.bollinger_std.copy(),
            regime_weights=base_params.regime_weights.copy(),
            sensitivity_level=min(adjusted_sensitivity, 1.0)
        )

        return adjusted_params

    def calculate_adaptive_weights(self, market_state,
                                 source_performance: Dict[str, float]) -> Dict[str, float]:
        """
        計算適應性權重分配

        Args:
            market_state: 當前市場狀態 (MarketState object or dict)
            source_performance: 各數據源性能評分

        Returns:
            Dict[str, float]: 調整後的權重分配
        """
        # Handle both MarketState object and dict
        if hasattr(market_state, 'regime'):
            regime = market_state.regime
        else:
            # It's a dict, get regime from 'regime' key
            regime_str = market_state.get('regime', 'sideways')
            # Convert string to MarketRegime enum
            from enum import Enum
            regime = None
            for r in MarketRegime:
                if r.value == regime_str:
                    regime = r
                    break
            if regime is None:
                regime = MarketRegime.SIDEWAYS

        regime_weights = self.regime_parameters[regime].regime_weights

        # 基於性能調整權重
        adaptive_weights = {}
        total_weight = 0

        for source, performance in source_performance.items():
            # 基礎權重基於性能
            base_weight = performance

            # 根據市場狀況調整
            if "trend" in source.lower():
                base_weight *= regime_weights["trend"]
            elif "momentum" in source.lower():
                base_weight *= regime_weights["momentum"]
            elif "volatility" in source.lower():
                base_weight *= regime_weights["volatility"]

            # 應用敏感度調整
            sensitivity = self.regime_parameters[regime].sensitivity_level
            confidence = market_state.confidence if hasattr(market_state, 'confidence') else market_state.get('confidence', 0.5)
            adjusted_weight = base_weight * (1 + sensitivity * confidence)

            adaptive_weights[source] = adjusted_weight
            total_weight += adjusted_weight

        # 標準化權重
        if total_weight > 0:
            for source in adaptive_weights:
                adaptive_weights[source] /= total_weight

        return adaptive_weights

class AdaptiveTechnicalAnalyzer:
    """適應性技術分析器"""

    def __init__(self):
        self.regime_detector = MarketRegimeDetector()
        self.parameter_optimizer = AdaptiveParameterOptimizer()

    def analyze_with_adaptation(self, data: pd.Series,
                              source_name: str = "default") -> Dict[str, Any]:
        """
        使用適應性參數進行技術分析

        Args:
            data: 數據序列
            source_name: 數據源名稱

        Returns:
            Dict[str, Any]: 適應性分析結果
        """
        # 檢測市場狀況
        market_state = self.regime_detector.detect_market_regime(data)

        # 獲取最優參數
        optimal_params = self.parameter_optimizer.get_optimal_parameters(market_state)

        # 計算適應性技術指標
        indicators = self._calculate_adaptive_indicators(data, optimal_params, source_name)

        return {
            "market_state": {
                "regime": market_state.regime.value,
                "volatility_level": market_state.volatility_level,
                "trend_strength": market_state.trend_strength,
                "momentum_score": market_state.momentum_score,
                "confidence": market_state.confidence,
                "last_updated": market_state.last_updated.isoformat()
            },
            "optimal_parameters": {
                "rsi_periods": optimal_params.rsi_periods,
                "macd_params": optimal_params.macd_params,
                "bollinger_periods": optimal_params.bollinger_periods,
                "sensitivity_level": optimal_params.sensitivity_level
            },
            "adaptive_indicators": indicators,
            "source_name": source_name
        }

    def _calculate_adaptive_indicators(self, data: pd.Series,
                                     params: AdaptiveParameters,
                                     source_name: str) -> Dict[str, Any]:
        """計算適應性技術指標"""
        indicators = {}

        # RSI - 使用多週期
        for period in params.rsi_periods:
            if len(data) >= period:
                rsi = self._calculate_rsi(data, period)
                indicators[f"rsi_{period}"] = {
                    "current": float(rsi.iloc[-1]) if not rsi.empty else 50.0,
                    "signal": self._rsi_signal(rsi.iloc[-1] if not rsi.empty else 50.0),
                    "period": period
                }

        # MACD
        fast, slow, signal = params.macd_params
        if len(data) >= slow:
            macd_result = self._calculate_macd(data, fast, slow, signal)
            indicators["macd"] = {
                "signal": macd_result["signal"],
                "strength": macd_result["strength"],
                "params": params.macd_params
            }

        # 趨勢分析
        trend_result = self._analyze_trend_adaptive(data, params)
        indicators["trend"] = trend_result

        # 計算總體評分
        indicators["total_score"] = self._calculate_adaptive_score(
            indicators, params.sensitivity_level
        )

        return indicators

    def _calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """計算RSI"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _rsi_signal(self, rsi_value: float) -> str:
        """RSI信號生成"""
        if rsi_value < 30:
            return "oversold"
        elif rsi_value > 70:
            return "overbought"
        else:
            return "neutral"

    def _calculate_macd(self, data: pd.Series, fast: int, slow: int, signal: int) -> Dict[str, Any]:
        """計算MACD"""
        exp1 = data.ewm(span=fast).mean()
        exp2 = data.ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_hist = histogram.iloc[-1]

        if current_macd > current_signal and current_hist > 0:
            signal_type = "bullish"
            strength = min(abs(current_hist) / current_signal, 1.0)
        elif current_macd < current_signal and current_hist < 0:
            signal_type = "bearish"
            strength = min(abs(current_hist) / abs(current_signal), 1.0)
        else:
            signal_type = "neutral"
            strength = 0.0

        return {
            "signal": signal_type,
            "strength": strength,
            "macd": float(current_macd),
            "signal_line": float(current_signal),
            "histogram": float(current_hist)
        }

    def _analyze_trend_adaptive(self, data: pd.Series, params: AdaptiveParameters) -> Dict[str, Any]:
        """適應性趨勢分析"""
        # 使用不同週期的移動平均
        short_ma = data.rolling(window=10).mean()
        long_ma = data.rolling(window=30).mean()

        if short_ma.iloc[-1] > long_ma.iloc[-1]:
            direction = "bullish"
        else:
            direction = "bearish"

        # 計算趨勢強度
        trend_strength = abs(short_ma.iloc[-1] - long_ma.iloc[-1]) / long_ma.iloc[-1]

        return {
            "direction": direction,
            "strength": float(trend_strength),
            "short_ma": float(short_ma.iloc[-1]),
            "long_ma": float(long_ma.iloc[-1])
        }

    def _calculate_adaptive_score(self, indicators: Dict[str, Any],
                                sensitivity: float) -> float:
        """計算適應性評分"""
        score = 0.0
        count = 0

        # RSI評分
        for key, value in indicators.items():
            if key.startswith("rsi_"):
                rsi_val = value.get("current", 50)
                if 40 <= rsi_val <= 60:  # 中性區域
                    score += 0.3
                elif value.get("signal") in ["oversold", "overbought"]:
                    score += 0.7
                count += 1

        # MACD評分
        if "macd" in indicators:
            macd_strength = indicators["macd"].get("strength", 0)
            score += macd_strength * 0.5
            count += 1

        # 趨勢評分
        if "trend" in indicators:
            trend_strength = indicators["trend"].get("strength", 0)
            score += trend_strength * 0.3
            count += 1

        # 平均並應用敏感度
        if count > 0:
            final_score = (score / count) * (1 + sensitivity)
            return min(final_score, 1.0)

        return 0.0

class AdaptiveMarketSystem:
    """適應性市場系統主類"""

    def __init__(self):
        self.analyzer = AdaptiveTechnicalAnalyzer()
        self.parameter_optimizer = AdaptiveParameterOptimizer()

    def run_adaptive_analysis(self, market_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """
        運行完整的適應性分析

        Args:
            market_data: 市場數據字典 {source_name: data_series}

        Returns:
            Dict[str, Any]: 完整的適應性分析結果
        """
        logger.info("開始適應性市場分析...")

        results = {}
        market_states = []
        source_performances = {}

        # 對每個數據源進行適應性分析
        for source_name, data in market_data.items():
            try:
                analysis = self.analyzer.analyze_with_adaptation(data, source_name)
                results[source_name] = analysis

                # 收集市場狀態和性能
                market_states.append(analysis["market_state"])
                source_performances[source_name] = analysis["adaptive_indicators"].get("total_score", 0)

                logger.info(f"✅ {source_name}: {analysis['market_state']['regime']} "
                          f"(信心: {analysis['market_state']['confidence']:.2f})")

            except Exception as e:
                logger.error(f"❌ {source_name} 分析失敗: {e}")
                continue

        # 綜合市場狀態
        consensus_market_state = self._get_consensus_market_state(market_states)

        # 計算適應性權重
        adaptive_weights = self.parameter_optimizer.calculate_adaptive_weights(
            consensus_market_state, source_performances
        )

        # 生成最終信號
        final_signal = self._generate_adaptive_signal(results, adaptive_weights, consensus_market_state)

        system_result = {
            "timestamp": datetime.now().isoformat(),
            "consensus_market_state": consensus_market_state,
            "adaptive_weights": adaptive_weights,
            "source_analyses": results,
            "final_signal": final_signal,
            "system_performance": {
                "sources_analyzed": len(results),
                "average_confidence": np.mean([state.get("confidence", 0) for state in market_states]),
                "regime_consensus": self._calculate_regime_consensus(market_states)
            }
        }

        logger.info(f"🎯 適應性分析完成: {final_signal['signal']} "
                   f"(信心: {final_signal['confidence']:.2%})")

        return system_result

    def _get_consensus_market_state(self, market_states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """獲取共識市場狀態"""
        if not market_states:
            return {}

        # 平均各項指標
        avg_volatility = np.mean([state.get("volatility_level", 0) for state in market_states])
        avg_trend = np.mean([state.get("trend_strength", 0) for state in market_states])
        avg_momentum = np.mean([state.get("momentum_score", 0) for state in market_states])
        avg_confidence = np.mean([state.get("confidence", 0) for state in market_states])

        # 眾數regime
        regimes = [state.get("regime", "sideways") for state in market_states]
        consensus_regime = max(set(regimes), key=regimes.count)

        return {
            "regime": consensus_regime,
            "volatility_level": float(avg_volatility),
            "trend_strength": float(avg_trend),
            "momentum_score": float(avg_momentum),
            "confidence": float(avg_confidence),
            "last_updated": datetime.now().isoformat()
        }

    def _calculate_regime_consensus(self, market_states: List[Dict[str, Any]]) -> float:
        """計算regime共識度"""
        if len(market_states) <= 1:
            return 1.0

        regimes = [state.get("regime", "sideways") for state in market_states]
        most_common = max(set(regimes), key=regimes.count)
        consensus_ratio = regimes.count(most_common) / len(regimes)

        return consensus_ratio

    def _generate_adaptive_signal(self, analyses: Dict[str, Any],
                                weights: Dict[str, float],
                                market_state: Dict[str, Any]) -> Dict[str, Any]:
        """生成適應性交易信號"""
        buy_votes = 0.0
        sell_votes = 0.0
        hold_votes = 0.0
        total_weight = 0.0

        for source_name, analysis in analyses.items():
            weight = weights.get(source_name, 0)
            if weight == 0:
                continue

            indicators = analysis["adaptive_indicators"]
            source_signal = self._get_source_signal(indicators)

            # 根據市場狀況調整信號權重
            regime_adjustment = self._get_regime_adjustment(
                analysis["market_state"]["regime"], market_state["regime"]
            )

            adjusted_weight = weight * (0.5 + regime_adjustment * 0.5)

            if source_signal == "buy":
                buy_votes += adjusted_weight
            elif source_signal == "sell":
                sell_votes += adjusted_weight
            else:
                hold_votes += adjusted_weight

            total_weight += adjusted_weight

        # 確定最終信號
        if buy_votes > sell_votes and buy_votes > hold_votes:
            final_signal = "BUY"
            confidence = buy_votes / total_weight if total_weight > 0 else 0
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            final_signal = "SELL"
            confidence = sell_votes / total_weight if total_weight > 0 else 0
        else:
            final_signal = "HOLD"
            confidence = hold_votes / total_weight if total_weight > 0 else 0

        return {
            "signal": final_signal,
            "confidence": float(confidence),
            "vote_distribution": {
                "buy": float(buy_votes),
                "sell": float(sell_votes),
                "hold": float(hold_votes),
                "total": float(total_weight)
            },
            "market_regime": market_state["regime"],
            "weight_adjustment": True
        }

    def _get_source_signal(self, indicators: Dict[str, Any]) -> str:
        """從指標中獲取源信號"""
        buy_signals = 0
        sell_signals = 0

        # RSI信號
        for key, value in indicators.items():
            if key.startswith("rsi_"):
                rsi_signal = value.get("signal", "neutral")
                if rsi_signal == "oversold":
                    buy_signals += 1
                elif rsi_signal == "overbought":
                    sell_signals += 1

        # MACD信號
        if "macd" in indicators:
            macd_signal = indicators["macd"].get("signal", "neutral")
            if macd_signal == "bullish":
                buy_signals += 2
            elif macd_signal == "bearish":
                sell_signals += 2

        # 趨勢信號
        if "trend" in indicators:
            trend_signal = indicators["trend"].get("direction", "neutral")
            if trend_signal == "bullish":
                buy_signals += 1
            elif trend_signal == "bearish":
                sell_signals += 1

        # 綜合判斷
        if buy_signals > sell_signals:
            return "buy"
        elif sell_signals > buy_signals:
            return "sell"
        else:
            return "hold"

    def _get_regime_adjustment(self, source_regime: str, consensus_regime: str) -> float:
        """獲取regime調整係數"""
        if source_regime == consensus_regime:
            return 1.0  # 完全一致，權重不變
        elif self._is_compatible_regime(source_regime, consensus_regime):
            return 0.7  # 部分兼容，權重略微降低
        else:
            return 0.3  # 不兼容，權重大幅降低

    def _is_compatible_regime(self, regime1: str, regime2: str) -> bool:
        """檢查regime兼容性"""
        compatible_pairs = [
            ("bull_market", "low_volatility"),
            ("bear_market", "high_volatility"),
            ("sideways", "low_volatility"),
            ("high_volatility", "bear_market"),
            ("low_volatility", "bull_market")
        ]

        return (regime1, regime2) in compatible_pairs or (regime2, regime1) in compatible_pairs

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """保存分析結果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"adaptive_market_analysis_{timestamp}.json"

        filepath = f"C:\\Users\\Penguin8n\\CODEX--\\simplified_system\\results\\{filename}"

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"📁 結果已保存至: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ 保存失敗: {e}")
            return ""

if __name__ == "__main__":
    # 測試適應性系統
    print("🚀 啟動適應性市場系統測試")

    system = AdaptiveMarketSystem()

    # 模擬市場數據
    dates = pd.date_range('2023-01-01', periods=100, freq='D')

    # 模擬不同類型的數據源
    np.random.seed(42)

    market_data = {
        "hibor_rates": pd.Series(
            np.cumsum(np.random.normal(0.001, 0.02, 100)) + 3.5,
            index=dates
        ),
        "monetary_base": pd.Series(
            np.cumsum(np.random.normal(0.0005, 0.01, 100)) + 1000,
            index=dates
        ),
        "exchange_rates": pd.Series(
            np.cumsum(np.random.normal(-0.0002, 0.015, 100)) + 7.8,
            index=dates
        )
    }

    # 運行適應性分析
    results = system.run_adaptive_analysis(market_data)

    # 保存結果
    system.save_results(results)

    print("\n🎯 適應性分析結果:")
    print(f"最終信號: {results['final_signal']['signal']}")
    print(f"信心度: {results['final_signal']['confidence']:.2%}")
    print(f"市場狀況: {results['consensus_market_state']['regime']}")
    print(f"分析源數量: {results['system_performance']['sources_analyzed']}")