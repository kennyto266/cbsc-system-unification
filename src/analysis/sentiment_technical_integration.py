"""
Sentiment-Technical Analysis Integration
情緒-技術分析整合模組

This module integrates CBSC sentiment data with traditional technical analysis
to create enhanced trading signals and indicators for CBSC products.

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

from models.cbsc_models import (
    CBSCContract, WarrantSentiment, CBSCType, SentimentLevel, SignalType
)

logger = logging.getLogger(__name__)

class SentimentSignalStrength(Enum):
    """情緒信號強度"""
    VERY_WEAK = 0.1
    WEAK = 0.3
    MODERATE = 0.5
    STRONG = 0.7
    VERY_STRONG = 0.9

@dataclass
class SentimentEnhancedSignal:
    """情緒增強信號"""
    timestamp: datetime
    symbol: str
    signal_type: SignalType
    technical_score: float
    sentiment_score: float
    combined_score: float
    confidence: float
    recommendation: str
    risk_level: str
    metadata: Dict[str, Any]

class SentimentTechnicalIntegrator:
    """情緒技術分析整合器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 配置參數
        self.sentiment_weight = config.get('sentiment_weight', 0.4)  # 情緒權重
        self.technical_weight = config.get('technical_weight', 0.6)  # 技術權重
        self.min_confidence = config.get('min_confidence', 0.6)  # 最小信心度
        self.sentiment_lookback = config.get('sentiment_lookback', 5)  # 情緒回看天數

        # 閾值參數
        self.extreme_sentiment_threshold = config.get('extreme_sentiment_threshold', 0.8)
        self.volatility_threshold = config.get('volatility_threshold', 0.02)
        self.momentum_threshold = config.get('momentum_threshold', 0.1)

    def calculate_sentiment_indicators(self, sentiment_data: List[WarrantSentiment]) -> Dict[str, Any]:
        """計算情緒指標"""
        if not sentiment_data:
            return {
                'sentiment_momentum': 0.0,
                'sentiment_trend': 'NEUTRAL',
                'sentiment_volatility': 0.0,
                'extreme_sentiment_ratio': 0.0,
                'sentiment_strength': SentimentSignalStrength.VERY_WEAK
            }

        # 按日期排序
        sorted_data = sorted(sentiment_data, key=lambda x: x.date)
        recent_data = sorted_data[-self.sentiment_lookback:]  # 最近N天

        # 計算情緒動量
        sentiment_strengths = [record.sentiment_strength for record in recent_data]
        if len(sentiment_strengths) >= 3:
            # 簡單的動量計算：最近值與N天前平均值的差異
            recent_avg = np.mean(sentiment_strengths[-3:])
            earlier_avg = np.mean(sentiment_strengths[:-3]) if len(sentiment_strengths) > 3 else recent_avg
            sentiment_momentum = recent_avg - earlier_avg
        else:
            sentiment_momentum = 0.0

        # 計算情緒趨勢
        if len(sentiment_strengths) >= 2:
            recent_change = sentiment_strengths[-1] - sentiment_strengths[0]
            if recent_change > 0.2:
                sentiment_trend = 'BULLISH'
            elif recent_change < -0.2:
                sentiment_trend = 'BEARISH'
            else:
                sentiment_trend = 'NEUTRAL'
        else:
            sentiment_trend = 'NEUTRAL'

        # 計算情緒波動率
        sentiment_volatility = np.std(sentiment_strengths) if len(sentiment_strengths) > 1 else 0.0

        # 計算極端情緒比例
        extreme_count = sum(1 for record in recent_data if record.get_extreme_signal())
        extreme_sentiment_ratio = extreme_count / len(recent_data)

        # 評估情緒強度
        avg_strength = np.mean([abs(s) for s in sentiment_strengths])
        if avg_strength >= 0.8:
            sentiment_strength = SentimentSignalStrength.VERY_STRONG
        elif avg_strength >= 0.6:
            sentiment_strength = SentimentSignalStrength.STRONG
        elif avg_strength >= 0.4:
            sentiment_strength = SentimentSignalStrength.MODERATE
        elif avg_strength >= 0.2:
            sentiment_strength = SentimentSignalStrength.WEAK
        else:
            sentiment_strength = SentimentSignalStrength.VERY_WEAK

        return {
            'sentiment_momentum': sentiment_momentum,
            'sentiment_trend': sentiment_trend,
            'sentiment_volatility': sentiment_volatility,
            'extreme_sentiment_ratio': extreme_sentiment_ratio,
            'sentiment_strength': sentiment_strength,
            'recent_sentiment': sentiment_strengths[-1] if sentiment_strengths else 0.0
        }

    def calculate_technical_score(self, price_data: pd.DataFrame) -> float:
        """計算技術分析評分"""
        if price_data.empty or 'close' not in price_data.columns:
            return 0.0

        try:
            closes = price_data['close'].values

            # 計算RSI
            if len(closes) >= 14:
                rsi = self._calculate_rsi(closes)
                rsi_signal = self._rsi_to_signal(rsi)
            else:
                rsi_signal = 0.0

            # 計算移動平均趨勢
            if len(closes) >= 20:
                ma_short = np.mean(closes[-5:])
                ma_long = np.mean(closes[-20:])
                ma_signal = (ma_short - ma_long) / ma_long if ma_long != 0 else 0.0
            else:
                ma_signal = 0.0

            # 計算動量
            if len(closes) >= 2:
                momentum = (closes[-1] - closes[0]) / closes[0]
                momentum_signal = np.tanh(momentum * 10)  # 使用tanh限制在[-1,1]
            else:
                momentum_signal = 0.0

            # 計算波動率調整的信號
            volatility = np.std(np.diff(closes)) / np.mean(closes) if len(closes) > 1 else 0.0
            volatility_adjustment = 1.0 / (1.0 + volatility * 10)

            # 綜合技術評分
            technical_score = (rsi_signal * 0.4 + ma_signal * 0.3 + momentum_signal * 0.3) * volatility_adjustment

            return np.clip(technical_score, -1.0, 1.0)

        except Exception as e:
            self.logger.error(f"技術分析評分計算錯誤: {e}")
            return 0.0

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """計算RSI"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _rsi_to_signal(self, rsi: float) -> float:
        """將RSI轉換為信號評分"""
        if rsi >= 70:
            return -0.8  # 超買，看跌信號
        elif rsi <= 30:
            return 0.8   # 超賣，看漲信號
        elif rsi >= 60:
            return -0.3  # 偏超買
        elif rsi <= 40:
            return 0.3   # 偏超賣
        else:
            return 0.0   # 中性

    def calculate_sentiment_score(self, sentiment_data: List[WarrantSentiment]) -> float:
        """計算情緒評分"""
        if not sentiment_data:
            return 0.0

        # 獲取最新情緒數據
        latest_data = sorted(sentiment_data, key=lambda x: x.date)[-1]
        base_score = latest_data.sentiment_strength

        # 調整分數
        sentiment_indicators = self.calculate_sentiment_indicators(sentiment_data)

        # 動量加權
        momentum_boost = sentiment_indicators['sentiment_momentum'] * 0.3
        trend_boost = 1.0

        if sentiment_indicators['sentiment_trend'] == 'BULLISH':
            trend_boost = 1.2
        elif sentiment_indicators['sentiment_trend'] == 'BEARISH':
            trend_boost = 0.8

        # 極端情緒加權
        extreme_adjustment = 1.0
        if sentiment_indicators['extreme_sentiment_ratio'] > 0.5:
            extreme_adjustment = 1.5  # 增強極端情緒的信號

        # 波動率減權
        volatility_adjustment = 1.0 / (1.0 + sentiment_indicators['sentiment_volatility'] * 5)

        # 綜合情緒評分
        sentiment_score = base_score * trend_boost * extreme_adjustment * volatility_adjustment + momentum_boost

        return np.clip(sentiment_score, -1.0, 1.0)

    def combine_signals(self, technical_score: float, sentiment_score: float) -> float:
        """結合技術和情緒信號"""
        # 加權平均
        combined_score = (
            technical_score * self.technical_weight +
            sentiment_score * self.sentiment_weight
        )

        # 一致性加權
        signal_consensus = 1.0
        if technical_score * sentiment_score > 0:
            # 信號方向一致，增強信號
            signal_consensus = 1.2
        elif technical_score * sentiment_score < 0:
            # 信號方向相反，減弱信號
            signal_consensus = 0.6

        combined_score *= signal_consensus

        return np.clip(combined_score, -1.0, 1.0)

    def calculate_confidence(self, technical_score: float, sentiment_score: float,
                            sentiment_data: List[WarrantSentiment]) -> float:
        """計算信號信心度"""
        base_confidence = 0.5

        # 技術分析信心度（基於信號強度）
        technical_confidence = min(abs(technical_score), 0.8)

        # 情緒分析信心度
        if sentiment_data:
            sentiment_indicators = self.calculate_sentiment_indicators(sentiment_data)

            # 極端情緒增加信心度
            extreme_confidence_boost = sentiment_indicators['extreme_sentiment_ratio'] * 0.3

            # 低波動率增加信心度
            stability_boost = (1.0 - sentiment_indicators['sentiment_volatility']) * 0.2

            sentiment_confidence = min(abs(sentiment_score), 0.8) + extreme_confidence_boost + stability_boost
        else:
            sentiment_confidence = 0.3

        # 信號一致性信心度
        if technical_score * sentiment_score > 0:
            consensus_confidence = 0.2
        else:
            consensus_confidence = -0.1

        # 綜合信心度
        confidence = base_confidence + technical_confidence + sentiment_confidence + consensus_confidence

        return np.clip(confidence, 0.0, 1.0)

    def generate_trading_signal(self, symbol: str, price_data: pd.DataFrame,
                             sentiment_data: List[WarrantSentiment],
                             current_price: Optional[float] = None) -> SentimentEnhancedSignal:
        """生成交易信號"""

        # 計算技術評分
        technical_score = self.calculate_technical_score(price_data)

        # 計算情緒評分
        sentiment_score = self.calculate_sentiment_score(sentiment_data)

        # 結合信號
        combined_score = self.combine_signals(technical_score, sentiment_score)

        # 計算信心度
        confidence = self.calculate_confidence(technical_score, sentiment_score, sentiment_data)

        # 確定信號類型
        if combined_score > 0.3:
            signal_type = SignalType.BUY_BULL
        elif combined_score < -0.3:
            signal_type = SignalType.SELL_BEAR
        else:
            signal_type = SignalType.HOLD

        # 確定建議
        if confidence >= self.min_confidence and signal_type != SignalType.HOLD:
            recommendation = "EXECUTE"
        elif confidence >= 0.4:
            recommendation = "CONSIDER"
        else:
            recommendation = "WAIT"

        # 風險評估
        risk_level = self._assess_risk_level(combined_score, confidence)

        # 創建信號對象
        signal = SentimentEnhancedSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            signal_type=signal_type,
            technical_score=technical_score,
            sentiment_score=sentiment_score,
            combined_score=combined_score,
            confidence=confidence,
            recommendation=recommendation,
            risk_level=risk_level,
            metadata={
                'sentiment_trend': self.calculate_sentiment_indicators(sentiment_data)['sentiment_trend'],
                'sentiment_strength': self.calculate_sentiment_indicators(sentiment_data)['sentiment_strength'].name,
                'current_price': current_price,
                'sentiment_weight': self.sentiment_weight,
                'technical_weight': self.technical_weight
            }
        )

        return signal

    def _assess_risk_level(self, score: float, confidence: float) -> str:
        """評估風險等級"""
        if confidence < 0.3:
            return "HIGH"  # 低信心度 = 高風險
        elif abs(score) > 0.8:
            return "HIGH"  # 極端信號 = 高風險
        elif abs(score) < 0.2:
            return "LOW"   # 弱信號 = 低風險
        else:
            return "MEDIUM"

    def generate_signal_series(self, symbol: str, price_data: pd.DataFrame,
                               sentiment_data: List[WarrantSentiment]) -> List[SentimentEnhancedSignal]:
        """生成信號序列"""
        if price_data.empty or not sentiment_data:
            return []

        signals = []

        # 按日期分組情緒數據
        sentiment_by_date = {}
        for record in sentiment_data:
            date_key = record.date.date()
            if date_key not in sentiment_by_date:
                sentiment_by_date[date_key] = []
            sentiment_by_date[date_key].append(record)

        # 為每個交易日生成信號
        for date, price_info in price_data.iterrows():
            date_key = date.date() if hasattr(date, 'date') else date

            if date_key in sentiment_by_date:
                day_sentiment = sentiment_by_date[date_key]

                # 使用當天之前的價格數據
                historical_prices = price_data[price_data.index <= date]

                if not historical_prices.empty:
                    signal = self.generate_trading_signal(
                        symbol=symbol,
                        price_data=historical_prices,
                        sentiment_data=day_sentiment,
                        current_price=price_info.get('close')
                    )
                    signals.append(signal)

        return signals

    def backtest_strategy(self, symbol: str, price_data: pd.DataFrame,
                         sentiment_data: List[WarrantSentiment],
                         initial_capital: float = 100000) -> Dict[str, Any]:
        """回測策略"""
        signals = self.generate_signal_series(symbol, price_data, sentiment_data)

        if not signals:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'signals_count': 0
            }

        # 模擬交易
        capital = initial_capital
        positions = []
        trades = []

        for signal in signals:
            if signal.confidence < self.min_confidence:
                continue

            if signal.signal_type == SignalType.BUY_BULL and not positions:
                # 買入信號
                if signal.current_price:
                    position_size = capital * 0.1  # 10%資金
                    shares = int(position_size / signal.current_price)
                    positions.append({
                        'entry_price': signal.current_price,
                        'shares': shares,
                        'entry_date': signal.timestamp,
                        'signal': signal
                    })

            elif signal.signal_type == SignalType.SELL_BEAR and positions:
                # 賣出信號
                position = positions[0]
                if signal.current_price:
                    pnl = (signal.current_price - position['entry_price']) * position['shares']
                    trades.append({
                        'entry_price': position['entry_price'],
                        'exit_price': signal.current_price,
                        'shares': position['shares'],
                        'pnl': pnl,
                        'entry_date': position['entry_date'],
                        'exit_date': signal.timestamp,
                        'return': pnl / (position['entry_price'] * position['shares'])
                    })
                    capital += pnl
                    positions = []

        # 計算性能指標
        if trades:
            returns = [trade['return'] for trade in trades]
            total_return = sum(trades[i]['pnl'] for i in range(len(trades))) / initial_capital

            # Sharpe ratio (簡化計算)
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = mean_return / std_return if std_return > 0 else 0

            # 最大回撤 (簡化計算)
            cumulative_returns = np.cumprod([1 + r for r in returns])
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0

            win_rate = sum(1 for r in returns if r > 0) / len(returns)
        else:
            total_return = 0.0
            sharpe_ratio = 0.0
            max_drawdown = 0.0
            win_rate = 0.0

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'signals_count': len(signals),
            'signals': signals,
            'trades': trades
        }

# 工廠函數
def create_sentiment_integrator(**config) -> SentimentTechnicalIntegrator:
    """創建情緒技術分析整合器"""
    default_config = {
        'sentiment_weight': 0.4,
        'technical_weight': 0.6,
        'min_confidence': 0.6,
        'sentiment_lookback': 5,
        'extreme_sentiment_threshold': 0.8,
        'volatility_threshold': 0.02,
        'momentum_threshold': 0.1
    }

    default_config.update(config)
    return SentimentTechnicalIntegrator(default_config)

if __name__ == "__main__":
    # 測試代碼
    print("=== Sentiment-Technical Integration 測試 ===")

    from models.cbsc_models import parse_warrant_sentiment_csv
    from pathlib import Path

    # 創建整合器
    integrator = create_sentiment_integrator()
    print("OK: 情緒技術整合器創建成功")

    # 加載測試數據
    sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
    if sentiment_path.exists():
        sentiment_data = parse_warrant_sentiment_csv(str(sentiment_path))
        print(f"OK: 加載 {len(sentiment_data)} 條情緒記錄")

        # 測試情緒指標計算
        sentiment_indicators = integrator.calculate_sentiment_indicators(sentiment_data)
        print(f"OK: 情緒指標計算完成")
        print(f"  情緒趨勢: {sentiment_indicators['sentiment_trend']}")
        print(f"  情緒強度: {sentiment_indicators['sentiment_strength'].name}")
        print(f"  極端情緒比例: {sentiment_indicators['extreme_sentiment_ratio']:.2%}")

        # 測試信號生成
        # 模擬價格數據
        price_data = pd.DataFrame({
            'close': np.linspace(250, 300, 100),
            'date': pd.date_range('2025-01-01', periods=100)
        })

        signal = integrator.generate_trading_signal("0700.HK", price_data, sentiment_data)
        print(f"OK: 交易信號生成完成")
        print(f"  信號類型: {signal.signal_type}")
        print(f"  綜合評分: {signal.combined_score:.3f}")
        print(f"  信心度: {signal.confidence:.3f}")
        print(f"  建議: {signal.recommendation}")

        # 測試回測
        backtest_result = integrator.backtest_strategy("0700.HK", price_data, sentiment_data)
        print(f"OK: 回測完成")
        print(f"  總收益率: {backtest_result['total_return']:.2%}")
        print(f"  夏普比率: {backtest_result['sharpe_ratio']:.3f}")
        print(f"  最大回撤: {backtest_result['max_drawdown']:.2%}")
        print(f"  勝率: {backtest_result['win_rate']:.2%}")

    print("Sentiment-Technical Integration 測試完成！")