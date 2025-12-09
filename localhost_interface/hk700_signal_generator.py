#!/usr/bin/env python3
"""
0700.HK 專用交易信號生成器
模擬基於香港政府數據的非價格信號分析
"""
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List

class HK700SignalGenerator:
    def __init__(self):
        self.symbol = "0700.HK"
        self.company_name = "騰訊控股"

        # 模擬的技術指標
        self.technical_indicators = [
            "RSI", "MACD", "布林帶", "KDJ", "威廉姆斯%R",
            "移動平均線", "相對強度指標", "動量指標"
        ]

        # 非價格數據源 (基於香港政府API)
        self.non_price_sources = [
            "HIBOR利率", "貨幣基礎", "銀行流動性",
            "匯率數據", "外匯基金票據", "人民幣流動性"
        ]

    def generate_mock_price_data(self):
        """生成模擬的股價數據"""
        base_price = 398.50  # 基於當前測試數據
        variation = random.uniform(-0.05, 0.05)  # ±5%變動
        return round(base_price * (1 + variation), 2)

    def calculate_signal_strength(self, indicator_data):
        """計算信號強度"""
        # 基於指標數據計算綜合強度
        base_strength = random.uniform(0.3, 0.9)

        # 根據市場條件調整
        if "RSI" in indicator_data and indicator_data["RSI"] < 30:
            base_strength += 0.1  # 超賣情況加強買入信號

        return min(max(base_strength, 0.0), 1.0)

    def calculate_confidence(self, signal_type, strength):
        """計算信號信心度"""
        base_confidence = random.uniform(0.5, 0.85)

        # 信號類型影響信心度
        if signal_type == "buy" and strength > 0.7:
            base_confidence += 0.1
        elif signal_type == "sell" and strength > 0.8:
            base_confidence += 0.05

        return min(max(base_confidence, 0.0), 1.0)

    def generate_trading_signal(self) -> Dict:
        """生成單個交易信號"""
        # 隨機選擇信號類型
        signal_types = ["buy", "sell", "hold"]
        weights = [0.4, 0.2, 0.4]  # 買入和持有機率較高
        signal_type = random.choices(signal_types, weights=weights)[0]

        # 隨機選擇2-4個指標
        num_indicators = random.randint(2, 4)
        selected_indicators = random.sample(self.technical_indicators, num_indicators)

        # 加入非價格數據源
        non_price_source = random.choice(self.non_price_sources)
        selected_indicators.append(non_price_source)

        # 生成信號數據
        strength = self.calculate_signal_strength({})
        confidence = self.calculate_confidence(signal_type, strength)
        price = self.generate_mock_price_data()

        # 生成信號ID
        timestamp = datetime.now()
        signal_id = f"signal_0700_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        signal = {
            "id": signal_id,
            "symbol": self.symbol,
            "signal_type": signal_type,
            "strength": round(strength, 3),
            "confidence": round(confidence, 3),
            "price_at_signal": price,
            "timestamp": timestamp.isoformat(),
            "source_indicators": selected_indicators,
            "strategy_name": "NonPrice_Signal_Strategy",
            "company_name": self.company_name,
            "analysis_notes": self.generate_analysis_notes(signal_type, strength, selected_indicators)
        }

        return signal

    def generate_analysis_notes(self, signal_type: str, strength: float, indicators: List[str]) -> str:
        """生成分析備註"""
        notes = []

        if signal_type == "buy":
            if strength > 0.7:
                notes.append("強烈買入信號：多個指標顯示超賣狀態")
            else:
                notes.append("溫和買入信號：部分指標支持上行")

        elif signal_type == "sell":
            if strength > 0.7:
                notes.append("強烈賣出信號：多個指標顯示超買狀態")
            else:
                notes.append("溫和賣出信號：獲利了結建議")

        else:  # hold
            notes.append("持有信號：市場處於盤整狀態")

        # 添加非價格因素分析
        if any("利率" in indicator for indicator in indicators):
            notes.append("考慮HIBOR利率變化影響")

        if any("貨幣" in indicator for indicator in indicators):
            notes.append("貨幣供應量變化納入考量")

        return "；".join(notes)

    def generate_multiple_signals(self, count: int = 5) -> List[Dict]:
        """生成多個交易信號"""
        signals = []
        base_time = datetime.now()

        for i in range(count):
            # 為每個信號生成不同的時間戳
            signal_time = base_time - timedelta(minutes=i*15)

            signal = self.generate_trading_signal()
            signal["timestamp"] = signal_time.isoformat()

            # 更新信號ID以反映時間差異
            signal["id"] = f"signal_0700_{signal_time.strftime('%Y%m%d_%H%M%S')}"

            signals.append(signal)

        # 按時間排序（最新的在前）
        signals.sort(key=lambda x: x["timestamp"], reverse=True)

        return signals

    def generate_market_summary(self) -> Dict:
        """生成市場摘要"""
        signals = self.generate_multiple_signals(10)

        # 統計信號類型
        buy_signals = [s for s in signals if s["signal_type"] == "buy"]
        sell_signals = [s for s in signals if s["signal_type"] == "sell"]
        hold_signals = [s for s in signals if s["signal_type"] == "hold"]

        # 計算平均強度和信心度
        avg_strength = sum(s["strength"] for s in signals) / len(signals)
        avg_confidence = sum(s["confidence"] for s in signals) / len(signals)

        # 當前價格（使用最新信號）
        current_price = signals[0]["price_at_signal"]

        summary = {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "current_price": current_price,
            "signal_summary": {
                "total_signals": len(signals),
                "buy_signals": len(buy_signals),
                "sell_signals": len(sell_signals),
                "hold_signals": len(hold_signals),
                "latest_signal": signals[0]["signal_type"]
            },
            "performance_metrics": {
                "average_strength": round(avg_strength, 3),
                "average_confidence": round(avg_confidence, 3),
                "price_range": {
                    "min": min(s["price_at_signal"] for s in signals),
                    "max": max(s["price_at_signal"] for s in signals)
                }
            },
            "key_indicators": self.get_top_indicators(signals),
            "market_sentiment": self.analyze_market_sentiment(signals),
            "recommendation": self.generate_recommendation(signals),
            "generated_at": datetime.now().isoformat()
        }

        return summary

    def get_top_indicators(self, signals: List[Dict]) -> List[str]:
        """獲取最常用指標"""
        indicator_count = {}

        for signal in signals:
            for indicator in signal["source_indicators"]:
                indicator_count[indicator] = indicator_count.get(indicator, 0) + 1

        # 返回出現頻率最高的前5個指標
        top_indicators = sorted(indicator_count.items(), key=lambda x: x[1], reverse=True)[:5]
        return [indicator for indicator, count in top_indicators]

    def analyze_market_sentiment(self, signals: List[Dict]) -> str:
        """分析市場情緒"""
        buy_count = sum(1 for s in signals if s["signal_type"] == "buy")
        sell_count = sum(1 for s in signals if s["signal_type"] == "sell")
        total_count = len(signals)

        buy_ratio = buy_count / total_count

        if buy_ratio > 0.6:
            return "積極看好"
        elif buy_ratio > 0.4:
            return "中性偏多"
        elif buy_ratio > 0.2:
            return "中性偏空"
        else:
            return "謹慎悲觀"

    def generate_recommendation(self, signals: List[Dict]) -> Dict:
        """生成投資建議"""
        latest_signal = signals[0]

        recommendation = {
            "action": latest_signal["signal_type"],
            "confidence": latest_signal["confidence"],
            "time_horizon": "短期",
            "risk_level": "中等",
            "reasoning": latest_signal.get("analysis_notes", ""),
            "target_price": self.calculate_target_price(latest_signal),
            "stop_loss": self.calculate_stop_loss(latest_signal)
        }

        return recommendation

    def calculate_target_price(self, signal: Dict) -> float:
        """計算目標價格"""
        current_price = signal["price_at_signal"]

        if signal["signal_type"] == "buy":
            # 買入信號：目標價格上漲3-8%
            return round(current_price * random.uniform(1.03, 1.08), 2)
        elif signal["signal_type"] == "sell":
            # 賣出信號：目標價格下跌3-6%
            return round(current_price * random.uniform(0.94, 0.97), 2)
        else:
            # 持有信號：小幅波動±2%
            return round(current_price * random.uniform(0.98, 1.02), 2)

    def calculate_stop_loss(self, signal: Dict) -> float:
        """計算止損價格"""
        current_price = signal["price_at_signal"]

        if signal["signal_type"] == "buy":
            # 買入信號：止損在下方3-5%
            return round(current_price * random.uniform(0.95, 0.97), 2)
        elif signal["signal_type"] == "sell":
            # 賣出信號：止損在上方3-5%
            return round(current_price * random.uniform(1.03, 1.05), 2)
        else:
            # 持有信號：較寬的止損範圍±5%
            return round(current_price * random.uniform(0.95, 1.05), 2)

def main():
    """主函數：生成並顯示0700.HK交易信號"""
    generator = HK700SignalGenerator()

    print("="*60)
    print("0700.HK 騰訊控股 - 交易信號分析報告")
    print("="*60)

    # 生成市場摘要
    market_summary = generator.generate_market_summary()

    print(f"\n市場摘要:")
    print(f"當前價格: HK${market_summary['current_price']}")
    print(f"市場情緒: {market_summary['market_sentiment']}")
    print(f"最新信號: {market_summary['signal_summary']['latest_signal']}")

    print(f"\n信號統計:")
    summary = market_summary['signal_summary']
    print(f"總信號數: {summary['total_signals']}")
    print(f"買入信號: {summary['buy_signals']}")
    print(f"賣出信號: {summary['sell_signals']}")
    print(f"持有信號: {summary['hold_signals']}")

    print(f"\n投資建議:")
    rec = market_summary['recommendation']
    print(f"建議操作: {rec['action']}")
    print(f"信心度: {rec['confidence']:.1%}")
    print(f"目標價格: HK${rec['target_price']}")
    print(f"止損價格: HK${rec['stop_loss']}")
    print(f"風險等級: {rec['risk_level']}")

    print(f"\n關鍵指標:")
    for indicator in market_summary['key_indicators']:
        print(f"- {indicator}")

    print(f"\n性能指標:")
    perf = market_summary['performance_metrics']
    print(f"平均強度: {perf['average_strength']:.3f}")
    print(f"平均信心度: {perf['average_confidence']:.3f}")
    print(f"價格區間: HK${perf['price_range']['min']} - HK${perf['price_range']['max']}")

    # 生成最新信號詳細信息
    latest_signals = generator.generate_multiple_signals(3)
    print(f"\n最新信號詳情:")
    for i, signal in enumerate(latest_signals, 1):
        print(f"\n信號 {i}:")
        print(f"  類型: {signal['signal_type']}")
        print(f"  強度: {signal['strength']:.3f}")
        print(f"  信心度: {signal['confidence']:.3f}")
        print(f"  價格: HK${signal['price_at_signal']}")
        print(f"  指標: {', '.join(signal['source_indicators'][:3])}")
        print(f"  時間: {signal['timestamp']}")

    print(f"\n生成時間: {market_summary['generated_at']}")
    print("="*60)

if __name__ == "__main__":
    main()