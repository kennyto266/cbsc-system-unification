#!/usr / bin / env python3
"""
非價格數據技術分析演示
Non - Price Data Technical Analysis Demo

演示完整邏輯鏈: 非價格數據 → 技術指標 → 買賣信號 → 回測
"""

import json
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from api.stock_api import get_hk_stock_data

    class NonPriceTADemo:
        """非價格技術分析演示"""

        def __init__(self):
            print("=" * 80)
            print("🔄 非價格數據技術分析完整邏輯鏈演示")
            print("邏輯: 非價格數據 → 技術指標 → 買賣信號 → 回測")
            print("=" * 80)

        def collect_non_price_data(self):
            """步驟1: 收集非價格數據"""
            print("\n📊 [步驟 1 / 4] 收集非價格數據...")

            # 模擬真實香港政府經濟數據
            dates = pd.date_range(end = datetime.now(), periods = 365, freq="D")

            np.random.seed(42)  # 確保可重複性

            # 1. HIBOR利率數據 (香港銀行同業拆息)
            hibor_base = 3.5
            hibor_trend = np.linspace(0, 0.5, 365) * 0.001  # 輕微上升趨勢
            hibor_noise = np.random.normal(0, 0.02, 365) * 0.01
            hibor_rates = hibor_base + hibor_trend + hibor_noise
            hibor_rates = np.clip(hibor_rates, 1.0, 8.0)  # 合理範圍

            # 2. 貨幣基礎數據 (香港貨幣供給)
            monetary_base = 2000000  # 20億港幣基礎
            monetary_growth = np.linspace(0, 0.03, 365)  # 3%年增長
            monetary_volatility = np.random.normal(0, 0.01, 365)
            monetary_values = monetary_base * (
                1 + monetary_growth + monetary_volatility
            )

            # 3. 匯率數據 (美元兌港幣)
            exchange_base = 7.8
            exchange_volatility = np.random.normal(0, 0.015, 365) * 0.01
            exchange_rates = exchange_base + exchange_volatility
            exchange_rates = np.clip(exchange_rates, 7.5, 8.1)

            # 4. 創建數據字典
            non_price_data = {
                "hibor_rates": pd.Series(hibor_rates, index = dates, name="HIBOR_Rates"),
                "monetary_base": pd.Series(
                    monetary_values, index = dates, name="Monetary_Base"
                ),
                "exchange_rates": pd.Series(
                    exchange_rates, index = dates, name="Exchange_Rates"
                ),
            }

            # 5. 生成擴展指標
            print("   📈 生成擴展經濟指標...")

            # 利率變化率
            non_price_data["hibor_rate_change"] = (
                non_price_data["hibor_rates"].pct_change().fillna(0)
            )

            # 貨幣供給增長率
            non_price_data["monetary_growth"] = (
                non_price_data["monetary_base"].pct_change().fillna(0)
            )

            # 匯率波動率
            non_price_data["exchange_volatility"] = (
                non_price_data["exchange_rates"]
                .pct_change()
                .rolling(20)
                .std()
                .fillna(0)
            )

            print(f"   ✅ 收集完成 {len(non_price_data)} 個非價格數據源:")
            for name, series in non_price_data.items():
                print(f"      - {name}: {len(series)} 條記錄")

            return non_price_data

        def calculate_technical_indicators(self, data):
            """步驟2: 計算技術指標"""
            print("\n🔧 [步驟 2 / 4] 計算技術指標...")

            indicator_results = {}

            for source_name, series in data.items():
                print(f"   📈 計算 {source_name} 技術指標...")

                indicators = {}

                try:
                    # RSI (相對強弱指標)
                    deltas = series.diff()
                    gains = deltas.where(deltas > 0, 0).rolling(window = 14).mean()
                    losses = (-deltas.where(deltas < 0, 0)).rolling(window = 14).mean()
                    rs = gains / losses
                    rsi = 100 - (100 / (1 + rs))

                    if not rsi.empty:
                        current_rsi = rsi.iloc[-1]
                        rsi_signal = (
                            "oversold"
                            if current_rsi < 30
                            else ("overbought" if current_rsi > 70 else "neutral")
                        )

                        indicators["rsi"] = {
                            "current": current_rsi,
                            "signal": rsi_signal,
                            "series": rsi,
                        }

                    # MACD (移動平均收斷發散)
                    ema_12 = series.ewm(span = 12).mean()
                    ema_26 = series.ewm(span = 26).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span = 9).mean()

                    if not macd_line.empty and not signal_line.empty:
                        macd_signal = (
                            "bullish"
                            if macd_line.iloc[-1] > signal_line.iloc[-1]
                            else "bearish"
                        )

                        indicators["macd"] = {
                            "macd": macd_line.iloc[-1],
                            "signal": signal_line.iloc[-1],
                            "signal_type": macd_signal,
                        }

                    # 簡單移動平均
                    sma_20 = series.rolling(window = 20).mean()
                    sma_50 = series.rolling(window = 50).mean()

                    if not sma_20.empty and not sma_50.empty:
                        trend_signal = (
                            "bullish"
                            if sma_20.iloc[-1] > sma_50.iloc[-1]
                            else "bearish"
                        )

                        indicators["sma"] = {
                            "sma_20": sma_20.iloc[-1],
                            "sma_50": sma_50.iloc[-1],
                            "trend": trend_signal,
                        }

                    # 波動率
                    volatility = series.rolling(window = 20).std()

                    if not volatility.empty:
                        current_vol = volatility.iloc[-1]
                        vol_signal = (
                            "high"
                            if current_vol > np.percentile(volatility.dropna(), 75)
                            else "low"
                        )

                        indicators["volatility"] = {
                            "current": current_vol,
                            "signal": vol_signal,
                        }

                    # 綜合評分 (0 - 1)
                    score = 0.5  # 基礎分

                    # RSI貢獻
                    if "rsi" in indicators:
                        rsi_val = indicators["rsi"]["current"]
                        if rsi_val < 30:
                            score += 0.2  # 超賣加分
                        elif rsi_val > 70:
                            score -= 0.2  # 超買減分

                    # MACD貢獻
                    if "macd" in indicators:
                        if indicators["macd"]["signal_type"] == "bullish":
                            score += 0.15
                        else:
                            score -= 0.15

                    # 趨勢貢獻
                    if "sma" in indicators:
                        if indicators["sma"]["trend"] == "bullish":
                            score += 0.1

                    indicators["composite_score"] = max(0, min(1, score))

                    indicator_results[source_name] = indicators

                except Exception as e:
                    print(f"      ⚠️ 計算 {source_name} 指標時出錯: {e}")
                    continue

            print(f"   ✅ 成功計算 {len(indicator_results)} 個數據源的技術指標")
            return indicator_results

        def generate_trading_signals(self, indicators):
            """步驟3: 生成買賣信號"""
            print("\n📡 [步驟 3 / 4] 生成買賣信號...")

            trading_signals = {}

            for source_name, data in indicators.items():
                print(f"   🎯 生成 {source_name} 交易信號...")

                try:
                    # 收集信號投票
                    buy_votes = 0
                    sell_votes = 0
                    hold_votes = 0
                    rationale = []

                    # RSI信號 (權重: 0.3)
                    if "rsi" in data:
                        rsi_signal = data["rsi"]["signal"]
                        rsi_val = data["rsi"]["current"]
                        if rsi_signal == "oversold":
                            buy_votes += 3
                            rationale.append(f"RSI超賣 ({rsi_val:.1f})")
                        elif rsi_signal == "overbought":
                            sell_votes += 3
                            rationale.append(f"RSI超買 ({rsi_val:.1f})")
                        else:
                            hold_votes += 1

                    # MACD信號 (權重: 0.25)
                    if "macd" in data:
                        macd_signal = data["macd"]["signal_type"]
                        if macd_signal == "bullish":
                            buy_votes += 2.5
                            rationale.append("MACD看漲")
                        elif macd_signal == "bearish":
                            sell_votes += 2.5
                            rationale.append("MACD看跌")
                        else:
                            hold_votes += 1

                    # 趨勢信號 (權重: 0.2)
                    if "sma" in data:
                        trend_signal = data["sma"]["trend"]
                        if trend_signal == "bullish":
                            buy_votes += 2
                            rationale.append("上升趨勢")
                        elif trend_signal == "bearish":
                            sell_votes += 2
                            rationale.append("下降趨勢")
                        else:
                            hold_votes += 1

                    # 綜合評分
                    total_votes = buy_votes + sell_votes + hold_votes
                    if total_votes > 0:
                        buy_strength = buy_votes / total_votes
                        sell_strength = sell_votes / total_votes
                        hold_strength = hold_votes / total_votes

                        # 確定主要信號
                        if buy_strength > 0.6:
                            primary_signal = "BUY"
                            signal_strength = buy_strength
                        elif sell_strength > 0.6:
                            primary_signal = "SELL"
                            signal_strength = sell_strength
                        else:
                            primary_signal = "HOLD"
                            signal_strength = hold_strength

                        # 信心度基於信號一致性
                        confidence = max(buy_strength, sell_strength, hold_strength)
                        confidence = min(confidence * 1.2, 1.0)  # 放大但限制在1.0

                    trading_signals[source_name] = {
                        "primary_signal": primary_signal,
                        "signal_strength": signal_strength,
                        "confidence": confidence,
                        "rationale": rationale,
                        "buy_votes": buy_votes,
                        "sell_votes": sell_votes,
                        "hold_votes": hold_votes,
                    }

                except Exception as e:
                    print(f"      ⚠️ 生成 {source_name} 信號時出錯: {e}")
                    continue

            print(f"   ✅ 成功生成 {len(trading_signals)} 個交易信號")

            # 顯示信號分佈
            signal_dist = {"BUY": 0, "SELL": 0, "HOLD": 0}
            for signal_data in trading_signals.values():
                signal_dist[signal_data["primary_signal"]] += 1

            print(
                f"   📊 信號分佈: BUY({signal_dist['BUY']}) SELL({signal_dist['SELL']}) HOLD({signal_dist['HOLD']})"
            )

            return trading_signals

        def run_backtest(self, trading_signals):
            """步驟4: 運行回測"""
            print("\n📊 [步驟 4 / 4] 運行回測...")

            try:
                # 獲取0700.HK真實股價數據
                print("   📈 獲取0700.HK真實股價數據...")
                stock_data = get_hk_stock_data("0700.HK", 365)

                if not stock_data or "data" not in stock_data:
                    print("   ⚠️ 無法獲取股價數據，使用模擬數據進行回測")
                    return self._simulate_backtest(trading_signals)

                price_data = stock_data["data"]["close"]
                list(price_data.keys())
                prices = list(price_data.values())

                if len(prices) < 50:
                    print("   ⚠️ 股價數據不足，使用模擬數據進行回測")
                    return self._simulate_backtest(trading_signals)

                print(f"   ✅ 成功獲取 {len(prices)} 天的股價數據")

                # 生成信號時間序列
                signal_series = self._generate_signal_series(
                    trading_signals, len(prices)
                )

                # 執行回測
                return self._execute_backtest(prices, signal_series)

            except Exception as e:
                print(f"   ⚠️ 回測過程出錯，使用模擬數據: {e}")
                return self._simulate_backtest(trading_signals)

        def _generate_signal_series(self, trading_signals, price_length):
            """生成信號時間序列"""
            try:
                # 基於信號分析生成時間序列
                total_signals = len(trading_signals)
                if total_signals == 0:
                    return pd.Series([0] * price_length)

                # 計算平均信號強度
                avg_buy_strength = np.mean(
                    [
                        s["signal_strength"]
                        for s in trading_signals.values()
                        if s["primary_signal"] == "BUY"
                    ]
                )
                avg_sell_strength = np.mean(
                    [
                        s["signal_strength"]
                        for s in trading_signals.values()
                        if s["primary_signal"] == "SELL"
                    ]
                )
                avg_hold_strength = np.mean(
                    [
                        s["signal_strength"]
                        for s in trading_signals.values()
                        if s["primary_signal"] == "HOLD"
                    ]
                )

                # 生成隨機但符合分佈的信號序列
                np.random.seed(123)
                signals = []

                buy_prob = avg_buy_strength / 3 if avg_buy_strength > 0 else 0.2
                sell_prob = avg_sell_strength / 3 if avg_sell_strength > 0 else 0.2
                1 - buy_prob - sell_prob

                for i in range(price_length):
                    rand = np.random.random()
                    if rand < buy_prob:
                        signals.append(0.8)  # BUY信號
                    elif rand < buy_prob + sell_prob:
                        signals.append(-0.8)  # SELL信號
                    else:
                        signals.append(0.0)  # HOLD信號

                return pd.Series(signals)

            except Exception as e:
                print(f"   ⚠️ 生成信號序列出錯: {e}")
                return pd.Series([0] * price_length)

        def _execute_backtest(self, prices, signals):
            """執行回測"""
            try:
                initial_capital = 100000
                capital = initial_capital
                position = 0  # 0 = 空倉, 1 = 滿倉
                trades = []
                portfolio_values = []

                min_length = min(len(prices), len(signals))

                for i in range(min_length):
                    current_price = prices[i]
                    signal = signals.iloc[i] if i < len(signals) else 0

                    # 交易邏輯
                    if signal > 0.5 and position == 0:  # 買入信號
                        position = 1
                        shares = capital / current_price
                        trades.append(
                            {
                                "day": i,
                                "action": "BUY",
                                "price": current_price,
                                "shares": shares,
                                "signal": signal,
                            }
                        )

                    elif signal < -0.5 and position == 1:  # 賣出信號
                        position = 0
                        portfolio_value = shares * current_price
                        capital = portfolio_value
                        trades.append(
                            {
                                "day": i,
                                "action": "SELL",
                                "price": current_price,
                                "portfolio_value": capital,
                                "signal": signal,
                            }
                        )

                    # 計算投資組合價值
                    if position == 1 and "shares" in locals():
                        portfolio_value = shares * current_price
                    else:
                        portfolio_value = capital

                    portfolio_values.append(portfolio_value)

                # 計算最終結果
                final_value = (
                    portfolio_values[-1] if portfolio_values else initial_capital
                )
                total_return = (final_value - initial_capital) / initial_capital

                # 計算Sharpe比率
                daily_returns = []
                for i in range(1, len(portfolio_values)):
                    daily_return = (
                        portfolio_values[i] - portfolio_values[i - 1]
                    ) / portfolio_values[i - 1]
                    daily_returns.append(daily_return)

                if daily_returns and np.std(daily_returns) > 0:
                    excess_returns = (
                        np.array(daily_returns) - 0.03 / 252
                    )  # 3%無風險利率
                    sharpe_ratio = (
                        np.mean(excess_returns) / np.std(daily_returns) * np.sqrt(252)
                    )
                else:
                    sharpe_ratio = 0

                # 最大回撤
                peak = portfolio_values[0] if portfolio_values else initial_capital
                max_drawdown = 0
                for value in portfolio_values:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / peak
                    max_drawdown = max(max_drawdown, drawdown)

                # 勝率
                winning_trades = 0
                total_completed_trades = 0

                for i in range(0, len(trades) - 1, 2):
                    if i + 1 < len(trades):
                        buy_trade = trades[i]
                        sell_trade = trades[i + 1]
                        if (
                            buy_trade["action"] == "BUY"
                            and sell_trade["action"] == "SELL"
                        ):
                            total_completed_trades += 1
                            buy_value = buy_trade["price"] * buy_trade["shares"]
                            sell_value = sell_trade.get("portfolio_value", 0)
                            if sell_value > buy_value:
                                winning_trades += 1

                win_rate = (
                    winning_trades / total_completed_trades
                    if total_completed_trades > 0
                    else 0
                )

                results = {
                    "backtest_type": "real_data",
                    "initial_capital": initial_capital,
                    "final_value": final_value,
                    "total_return": total_return,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": max_drawdown,
                    "total_trades": len(trades),
                    "completed_trades": total_completed_trades,
                    "winning_trades": winning_trades,
                    "win_rate": win_rate,
                    "portfolio_values": portfolio_values,
                    "trades": trades,
                }

                self._display_backtest_results(results)
                return results

            except Exception as e:
                print(f"   ⚠️ 執行回測出錯: {e}")
                return {"error": str(e)}

        def _simulate_backtest(self, trading_signals):
            """使用模擬數據進行回測"""
            print("   📈 使用模擬數據進行回測...")

            try:
                # 生成模擬股價
                np.random.seed(456)
                days = 365
                base_price = 400  # 騰訊價格約400港幣
                returns = np.random.normal(0.001, 0.02, days)  # 日回報
                prices = [base_price]

                for r in returns:
                    new_price = prices[-1] * (1 + r)
                    prices.append(new_price)

                prices = prices[:days]  # 確保正確長度

                # 生成信號序列
                signals = self._generate_signal_series(trading_signals, days)

                # 執行回測
                return self._execute_backtest(prices, signals)

            except Exception as e:
                print(f"   ❌ 模擬回測失敗: {e}")
                return {"error": str(e)}

        def _display_backtest_results(self, results):
            """顯示回測結果"""
            print("\n" + "=" * 60)
            print("📊 回測結果摘要")
            print("=" * 60)

            if "error" in results:
                print(f"❌ 回測失敗: {results['error']}")
                return

            print(f"💰 初始資本: ${results['initial_capital']:,.2f}")
            print(f"💰 最終價值: ${results['final_value']:,.2f}")
            print(f"📈 總回報: {results['total_return']:.2%}")
            print(f"📊 Sharpe比率: {results['sharpe_ratio']:.3f}")
            print(f"📉 最大回撤: {results['max_drawdown']:.2%}")
            print(f"🔄 總交易次數: {results['total_trades']}")
            print(f"✅ 完成交易: {results['completed_trades']}")
            print(f"🎯 獲利交易: {results['winning_trades']}")
            print(f"📊 勝率: {results['win_rate']:.2%}")

            # 評級評價
            total_score = 0
            grade = "N / A"

            if results["total_return"] > 0.2:  # 20%以上
                total_score += 25
            elif results["total_return"] > 0.1:
                total_score += 15
            elif results["total_return"] > 0:
                total_score += 10

            if results["sharpe_ratio"] > 2.0:
                total_score += 30
            elif results["sharpe_ratio"] > 1.5:
                total_score += 25
            elif results["sharpe_ratio"] > 1.0:
                total_score += 20
            elif results["sharpe_ratio"] > 0.5:
                total_score += 15
            elif results["sharpe_ratio"] > 0:
                total_score += 10

            if results["max_drawdown"] < 0.1:
                total_score += 25
            elif results["max_drawdown"] < 0.15:
                total_score += 20
            elif results["max_drawdown"] < 0.2:
                total_score += 15
            elif results["max_drawdown"] < 0.25:
                total_score += 10

            if results["win_rate"] > 0.6:
                total_score += 20
            elif results["win_rate"] > 0.5:
                total_score += 15
            elif results["win_rate"] > 0.4:
                total_score += 10
            elif results["win_rate"] > 0.3:
                total_score += 5

            # 評級
            if total_score >= 85:
                grade = "A+"
            elif total_score >= 75:
                grade = "A"
            elif total_score >= 65:
                grade = "B+"
            elif total_score >= 55:
                grade = "B"
            elif total_score >= 45:
                grade = "C+"
            elif total_score >= 35:
                grade = "C"
            elif total_score >= 25:
                grade = "D"
            else:
                grade = "F"

            print(f"🏆 綜合評分: {total_score}/100")
            print(f"📝 策略等級: {grade}")

            print("=" * 60)

        def run_complete_workflow(self):
            """運行完整工作流程"""
            start_time = time.time()

            try:
                # 步驟1: 收集非價格數據
                non_price_data = self.collect_non_price_data()

                # 步驟2: 計算技術指標
                indicators = self.calculate_technical_indicators(non_price_data)

                # 步驟3: 生成買賣信號
                signals = self.generate_trading_signals(indicators)

                # 步驟4: 運行回測
                backtest_results = self.run_backtest(signals)

                # 生成最終報告
                execution_time = time.time() - start_time

                final_report = {
                    "workflow_info": {
                        "execution_time": execution_time,
                        "timestamp": datetime.now().isoformat(),
                        "status": "completed",
                    },
                    "data_sources": {
                        "count": len(non_price_data),
                        "sources": list(non_price_data.keys()),
                    },
                    "technical_indicators": {
                        "processed_sources": len(indicators),
                        "indicator_types": ["RSI", "MACD", "SMA", "Volatility"],
                    },
                    "trading_signals": {
                        "generated": len(signals),
                        "signals": {
                            name: data["primary_signal"]
                            for name, data in signals.items()
                        },
                    },
                    "backtest_results": backtest_results,
                }

                # 保存結果
                self._save_results(final_report)

                print(f"\n⏱️ 總執行時間: {execution_time:.2f} 秒")
                print("🎉 非價格數據技術分析完整邏輯鏈演示完成！")

                return final_report

            except Exception as e:
                print(f"❌ 工作流程執行失敗: {e}")
                return {"error": str(e)}

        def _save_results(self, results):
            """保存結果"""
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"non_price_ta_demo_results_{timestamp}.json"
                filepath = os.path.join(os.getcwd(), filename)

                with open(filepath, "w", encoding="utf - 8") as f:
                    json.dump(results, f, ensure_ascii = False, indent = 2, default = str)

                print(f"📁 結果已保存至: {filename}")

            except Exception as e:
                print(f"⚠️ 保存結果失敗: {e}")

    def main():
        """主函數"""
        demo = NonPriceTADemo()
        results = demo.run_complete_workflow()

        if "error" in results:
            print(f"\n❌ 演示失敗: {results['error']}")
            return False
        else:
            print(f"\n✅ 演示成功完成!")
            return True

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
    print("請確保已安裝必要的依賴庫")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback

    traceback.print_exc()
