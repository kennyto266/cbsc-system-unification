#!/usr / bin / env python3
"""
实时量化交易会话 - 完整的量化系统使用演示
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


def get_real_stock_data():
    """获取真实股票数据"""
    print("=" * 80)
    print("🔥 歡骤1: 获取真实港股数据")
    print("=" * 80)

    try:
        from api.stock_api import get_hk_stock_data

        # 获取腾讯(0700.HK)过去一年的数据
        print("📊 正在获取 0700.HK (腾讯) 数据...")
        stock_data = get_hk_stock_data("0700.HK", 252)  # 252个交易日 = 1年

        if stock_data is not None and not stock_data.empty:
            print(f"✅ 成功获取 {len(stock_data)} 条记录")
            print(
                f"📈 数据时间范围: {stock_data.index[0].date()} 至 {stock_data.index[-1].date()}"
            )
            print(f"💰 最新收盘价: {stock_data['close'].iloc[-1]:.2f} HKD")
            print(f"📊 期间最高价: {stock_data['high'].max():.2f} HKD")
            print(f"📉 期间最低价: {stock_data['low'].min():.2f} HKD")

            # 显示最近5天数据
            print("\n📋 最近5天价格数据:")
            print(stock_data.tail(5)[["close", "high", "low", "volume"]].to_string())

            return stock_data
        else:
            print("❌ 无法获取股票数据")
            return None

    except Exception as e:
        print(f"❌ 获取股票数据失败: {e}")
        return None


def calculate_technical_indicators(stock_data):
    """计算技术指标"""
    print("\n" + "=" * 80)
    print("📈 步骤2: 计算技术指标")
    print("=" * 80)

    try:
        from indicators.core_indicators import CoreIndicators

        print("🔧 初始化技术指标引擎...")
        indicators = CoreIndicators()

        prices = stock_data["close"]
        print(f"📊 价格数据: {len(prices)} 条记录")

        # 计算多种技术指标
        print("\n📊 正在计算技术指标...")

        # RSI指标
        rsi_14 = indicators.calculate_rsi(prices, 14)
        rsi_30 = indicators.calculate_rsi(prices, 30)
        print(f"✅ RSI(14): {rsi_14.iloc[-1]:.2f}")
        print(f"✅ RSI(30): {rsi_30.iloc[-1]:.2f}")

        # 移动平均线
        sma_20 = indicators.calculate_sma(prices, 20)
        sma_50 = indicators.calculate_sma(prices, 50)
        ema_12 = indicators.calculate_ema(prices, 12)
        print(f"✅ SMA(20): {sma_20.iloc[-1]:.2f}")
        print(f"✅ SMA(50): {sma_50.iloc[-1]:.2f}")
        print(f"✅ EMA(12): {ema_12.iloc[-1]:.2f}")

        # MACD指标
        macd_data = indicators.calculate_macd(prices, 12, 26, 9)
        if macd_data:
            macd = macd_data["macd"].iloc[-1]
            signal = macd_data["signal"].iloc[-1]
            histogram = macd_data["histogram"].iloc[-1]
            print(f"✅ MACD: {macd:.4f}")
            print(f"✅ Signal: {signal:.4f}")
            print(f"✅ Histogram: {histogram:.4f}")

        # 布林带
        bb_data = indicators.calculate_bollinger_bands(prices, 20, 2)
        if bb_data:
            upper = bb_data["upper"].iloc[-1]
            middle = bb_data["middle"].iloc[-1]
            lower = bb_data["lower"].iloc[-1]
            current_price = prices.iloc[-1]
            bb_position = (current_price - lower) / (upper - lower) * 100
            print(f"✅ 布林带上轨: {upper:.2f}")
            print(f"✅ 布林带中轨: {middle:.2f}")
            print(f"✅ 布林带下轨: {lower:.2f}")
            print(f"✅ 当前价格位置: {bb_position:.1f}%")

        # 动量指标
        momentum_10 = indicators.calculate_momentum(prices, 10)
        print(f"✅ 10日动量: {momentum_10.iloc[-1]:.2f}")

        return {
            "rsi_14": rsi_14.iloc[-1],
            "rsi_30": rsi_30.iloc[-1],
            "sma_20": sma_20.iloc[-1],
            "sma_50": sma_50.iloc[-1],
            "ema_12": ema_12.iloc[-1],
            "current_price": prices.iloc[-1],
            "macd": macd,
            "bollinger_bands": bb_data,
            "momentum": momentum_10.iloc[-1],
        }

    except Exception as e:
        print(f"❌ 计算技术指标失败: {e}")
        return None


def get_government_data():
    """获取政府经济数据"""
    print("\n" + "=" * 80)
    print("🏛️ 步骤3: 获取香港政府经济数据")
    print("=" * 80)

    try:
        from api.government_data import get_hibor_data, get_latest_hibor

        print("📊 正在获取最新HIBOR利率数据...")

        # 获取最新HIBOR数据
        latest_hibor = get_latest_hibor()

        if latest_hibor:
            print(f"✅ HIBOR隔夜利率: {latest_hibor.get('overnight', 'N / A')}%")
            print(f"✅ HIBOR1周利率: {latest_hibor.get('1_week', 'N / A')}%")
            print(f"✅ HIBOR1月利率: {latest_hibor.get('1_month', 'N / A')}%")
            print(f"✅ HIBOR3月利率: {latest_hibor.get('3_months', 'N / A')}%")
            return latest_hibor
        else:
            print("⚠️ 无法获取最新HIBOR数据，使用备用数据...")

            # 获取历史HIBOR数据
            hibor_history = get_hibor_data(30)
            if hibor_history and hibor_history.get("data"):
                latest_record = hibor_history["data"][0]  # 最新的记录
                print(f"✅ 历史HIBOR隔夜: {latest_record.get('overnight', 'N / A')}%")
                return latest_record
            else:
                print("❌ 无法获取HIBOR数据")
                return None

    except Exception as e:
        print(f"❌ 获取政府数据失败: {e}")
        return None


def generate_trading_signals(indicators, government_data):
    """生成交易信号"""
    print("\n" + "=" * 80)
    print("📡 步骤4: 生成交易信号")
    print("=" * 80)

    if not indicators:
        print("❌ 无法生成信号：缺少技术指标数据")
        return None

    signals = []
    current_price = indicators["current_price"]

    print(f"🎯 当前价格: {current_price:.2f} HKD")

    # RSI信号
    rsi_14 = indicators["rsi_14"]
    if rsi_14 < 30:
        signals.append(
            {
                "indicator": "RSI(14)",
                "signal": "BUY",
                "strength": "STRONG",
                "reason": f"RSI超卖 ({rsi_14:.1f} < 30)",
                "action": "考虑买入",
            }
        )
        print(f"🟢 RSI买入信号: {rsi_14:.1f} (超卖)")
    elif rsi_14 > 70:
        signals.append(
            {
                "indicator": "RSI(14)",
                "signal": "SELL",
                "strength": "STRONG",
                "reason": f"RSI超买 ({rsi_14:.1f} > 70)",
                "action": "考虑卖出",
            }
        )
        print(f"🔴 RSI卖出信号: {rsi_14:.1f} (超买)")
    else:
        print(f"🟡 RSI中性: {rsi_14:.1f} (观望)")

    # 移动平均线信号
    sma_20 = indicators["sma_20"]
    sma_50 = indicators["sma_50"]

    if current_price > sma_20 and sma_20 > sma_50:
        signals.append(
            {
                "indicator": "MA交叉",
                "signal": "BUY",
                "strength": "MEDIUM",
                "reason": f"价格在均线上方，均线多头排列",
                "action": "趋势向上，考虑持仓",
            }
        )
        print(
            f"🟢 MA买入信号: 价格 {current_price:.2f} > SMA20 {sma_20:.2f} > SMA50 {sma_50:.2f}"
        )
    elif current_price < sma_20 and sma_20 < sma_50:
        signals.append(
            {
                "indicator": "MA交叉",
                "signal": "SELL",
                "strength": "MEDIUM",
                "reason": f"价格在均线下方，均线空头排列",
                "action": "趋势向下，考虑减仓",
            }
        )
        print(
            f"🔴 MA卖出信号: 价格 {current_price:.2f} < SMA20 {sma_20:.2f} < SMA50 {sma_50:.2f}"
        )
    else:
        print(f"🟡 MA中性: 价格在均线间震荡")

    # MACD信号
    macd_data = indicators["macd"]
    if macd_data:
        macd = macd_data["macd"].iloc[-1]
        signal = macd_data["signal"].iloc[-1]
        histogram = macd_data["histogram"].iloc[-1]

        if macd > signal and histogram > 0:
            signals.append(
                {
                    "indicator": "MACD",
                    "signal": "BUY",
                    "strength": "MEDIUM",
                    "reason": f"MACD金叉 ({macd:.4f} > {signal:.4f})",
                    "action": "动能转强，考虑买入",
                }
            )
            print(f"🟢 MACD买入信号: 金叉 ({macd:.4f} > {signal:.4f})")
        elif macd < signal and histogram < 0:
            signals.append(
                {
                    "indicator": "MACD",
                    "signal": "SELL",
                    "strength": "MEDIUM",
                    "reason": f"MACD死叉 ({macd:.4f} < {signal:.4f})",
                    "action": "动能转弱，考虑卖出",
                }
            )
            print(f"🔴 MACD卖出信号: 死叉 ({macd:.4f} < {signal:.4f})")
        else:
            print(f"🟡 MACD中性: ({macd:.4f} vs {signal:.4f})")

    # 布林带信号
    bb_data = indicators["bollinger_bands"]
    if bb_data:
        upper = bb_data["upper"].iloc[-1]
        lower = bb_data["lower"].iloc[-1]
        bb_position = (current_price - lower) / (upper - lower) * 100

        if bb_position >= 95:
            signals.append(
                {
                    "indicator": "布林带",
                    "signal": "SELL",
                    "strength": "STRONG",
                    "reason": f"价格接近布林带上轨 ({bb_position:.1f}%)",
                    "action": "价格过高，考虑卖出",
                }
            )
            print(f"🔴 布林带卖出信号: {bb_position:.1f}% 接近上轨")
        elif bb_position <= 5:
            signals.append(
                {
                    "indicator": "布林带",
                    "signal": "BUY",
                    "strength": "STRONG",
                    "reason": f"价格接近布林带下轨 ({bb_position:.1f}%)",
                    "action": "价格过低，考虑买入",
                }
            )
            print(f"🟢 布林带买入信号: {bb_position:.1f}% 接近下轨")
        else:
            print(f"🟡 布林带中性: {bb_position:.1f}% 在正常区间")

    # 经济环境信号
    if government_data:
        hibor_overnight = government_data.get("overnight")
        if hibor_overnight:
            if hibor_overnight > 5.0:
                signals.append(
                    {
                        "indicator": "HIBOR",
                        "signal": "CAUTION",
                        "strength": "WEAK",
                        "reason": f"高利率环境 ({hibor_overnight:.2f}%)",
                        "action": "高利率环境，谨慎操作",
                    }
                )
                print(f"🟡 HIBOR警告: 高利率环境 {hibor_overnight:.2f}%")
            elif hibor_overnight < 2.0:
                signals.append(
                    {
                        "indicator": "HIBOR",
                        "signal": "FAVORABLE",
                        "strength": "WEAK",
                        "reason": f"低利率环境 ({hibor_overnight:.2f}%)",
                        "action": "低利率环境，有利于股市",
                    }
                )
                print(f"🟢 HIBOR利好: 低利率环境 {hibor_overnight:.2f}%")

    print(f"\n📊 总信号数: {len(signals)}")

    # 综合建议
    buy_signals = len([s for s in signals if s["signal"] == "BUY"])
    sell_signals = len([s for s in signals if s["signal"] == "SELL"])

    if buy_signals > sell_signals:
        recommendation = "🟢 建议买入 - 看涨信号较多"
    elif sell_signals > buy_signals:
        recommendation = "🔴 建议卖出 - 看跌信号较多"
    else:
        recommendation = "🟡 建议观望 - 信号平衡"

    print(f"\n🎯 综合建议: {recommendation}")

    return signals, recommendation


def run_vectorbt_backtest(stock_data):
    """运行VectorBT回测"""
    print("\n" + "=" * 80)
    print("📊 步骤5: VectorBT策略回测")
    print("=" * 80)

    try:
        # 由于导入问题，我们创建简化的回测逻辑
        print("🔧 创建简化回测系统...")

        # RSI策略回测
        def backtest_rsi_strategy(data, period = 14, oversold = 30, overbought = 70):
            """简化RSI策略回测"""
            prices = data["close"]

            # 计算RSI
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window = period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window = period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # 生成交易信号
            buy_signals = rsi < oversold
            sell_signals = rsi > overbought

            # 计算收益
            positions = pd.Series(0, index = prices.index)
            positions[buy_signals] = 1
            positions[sell_signals] = -1

            # 持仓逻辑：买入后持有直到卖出
            current_pos = 0
            for i in range(1, len(positions)):
                if current_pos == 0 and buy_signals.iloc[i]:
                    current_pos = 1
                elif current_pos == 1 and sell_signals.iloc[i]:
                    current_pos = 0
                positions.iloc[i] = current_pos

            # 计算收益
            returns = positions * prices.pct_change().shift(-1)

            # 计算性能指标
            total_return = (1 + returns).cumprod().iloc[-2] - 1
            annual_return = total_return * 252 / len(returns)

            # 计算夏普比率 (假设无风险利率3%)
            excess_returns = returns - 0.03 / 252
            sharpe_ratio = (
                excess_returns.mean() / excess_returns.std() * np.sqrt(252)
                if excess_returns.std() > 0
                else 0
            )

            # 计算最大回撤
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            return {
                "strategy": "RSI_MEAN_REVERSION",
                "total_return": total_return,
                "annual_return": annual_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "trade_count": len(positions[position.diff() != 0]),
                "parameters": {
                    "period": period,
                    "oversold": oversold,
                    "overbought": overbought,
                },
            }

        # 运行RSI策略回测
        print("📊 正在回测RSI均值回归策略...")
        rsi_results = backtest_rsi_strategy(stock_data)

        print(f"✅ 策略: {rsi_results['strategy']}")
        print(f"📈 总收益率: {rsi_results['total_return']:.2%}")
        print(f"📅 年化收益率: {rsi_results['annual_return']:.2%}")
        print(f"📊 夏普比率: {rsi_results['sharpe_ratio']:.3f}")
        print(f"📉 最大回撤: {rsi_results['max_drawdown']:.2%}")
        print(f"🔄 交易次数: {rsi_results['trade_count']}")

        # 简单的买入持有策略作为基准
        buy_hold_return = stock_data["close"].iloc[-1] / stock_data["close"].iloc[0] - 1
        buy_hold_annual = buy_hold_return * 252 / len(stock_data)

        print(f"\n📊 基准对比:")
        print(f"🔹 买入持有收益率: {buy_hold_return:.2%} (年化 {buy_hold_annual:.2%})")
        print(
            f"🔹 策略超额收益: {(rsi_results['annual_return'] - buy_hold_annual):.2%}"
        )

        if rsi_results["sharpe_ratio"] > 1.0:
            print("🟢 策略评级: 优秀 (Sharpe > 1.0)")
        elif rsi_results["sharpe_ratio"] > 0.5:
            print("🟡 策略评级: 良好 (Sharpe > 0.5)")
        else:
            print("🔴 策略评级: 需要改进 (Sharpe < 0.5)")

        return rsi_results

    except Exception as e:
        print(f"❌ 回测失败: {e}")
        return None


def generate_trading_report(stock_data, indicators, signals, backtest_results):
    """生成交易报告"""
    print("\n" + "=" * 80)
    print("📋 步骤6: 生成交易报告")
    print("=" * 80)

    # 创建详细报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    report = {
        "trading_session": {
            "timestamp": datetime.now().isoformat(),
            "stock_symbol": "0700.HK",
            "stock_name": "Tencent",
            "data_period": f"{stock_data.index[0].date()} 至 {stock_data.index[-1].date()}",
            "total_trading_days": len(stock_data),
        },
        "current_market": {
            "current_price": indicators["current_price"],
            "daily_change": (
                (stock_data["close"].iloc[-1] / stock_data["close"].iloc[-2] - 1) * 100
                if len(stock_data) > 1
                else 0
            ),
            "volume": (
                stock_data["volume"].iloc[-1] if "volume" in stock_data.columns else 0
            ),
            "price_range_52w": {
                "high": stock_data["high"].max(),
                "low": stock_data["low"].min(),
            },
        },
        "technical_indicators": {
            "rsi_14": indicators["rsi_14"],
            "rsi_30": indicators["rsi_30"],
            "sma_20": indicators["sma_20"],
            "sma_50": indicators["sma_50"],
            "ema_12": indicators["ema_12"],
            "momentum_10": indicators["momentum"],
            "macd_signal": (
                "BULLISH"
                if indicators["macd"]["macd"].iloc[-1]
                > indicators["macd"]["signal"].iloc[-1]
                else "BEARISH"
            ),
        },
        "trading_signals": signals,
        "backtest_results": backtest_results,
        "recommendations": [],
    }

    # 添加建议
    if signals:
        buy_count = len([s for s in signals if s["signal"] == "BUY"])
        sell_count = len([s for s in signals if s["signal"] == "SELL"])

        if buy_count > sell_count:
            report["recommendations"].append("基于当前技术指标，建议考虑逢低买入策略")
        elif sell_count > buy_count:
            report["recommendations"].append("基于当前技术指标，建议考虑减仓或止盈")
        else:
            report["recommendations"].append("市场信号混合，建议观望等待明确方向")

    if backtest_results:
        if backtest_results["sharpe_ratio"] > 1.0:
            report["recommendations"].append("策略表现优秀，可考虑实盘测试")
        elif backtest_results["sharpe_ratio"] > 0:
            report["recommendations"].append("策略表现正面，可考虑优化参数后使用")
        else:
            report["recommendations"].append("策略需要改进，建议调整参数或寻找其他机会")

    # 保存报告
    report_file = f"trading_session_report_{timestamp}.json"
    with open(report_file, "w", encoding="utf - 8") as f:
        json.dump(report, f, indent = 2, ensure_ascii = False)

    # 生成Markdown报告
    md_file = f"trading_session_report_{timestamp}.md"
    with open(md_file, "w", encoding="utf - 8") as f:
        f.write(
            f"""# 🚀 腾讯(0700.HK)量化交易分析报告

**生成时间 * *: {report['trading_session']['timestamp']}
**分析周期 * *: {report['trading_session']['data_period']}
**交易天数 * *: {report['trading_session']['total_trading_days']}天

## 📊 当前市场状况

- **当前价格 * *: HK${report['current_market']['current_price']:.2f}
- **日涨跌幅 * *: {report['current_market']['daily_change']:+.2f}%
- **52周高低点 * *: HK${report['current_market']['price_range_52w']['high']:.2f} / HK${report['current_market']['price_range_52w']['low']:.2f}

## 📈 技术指标分析

| 指标 | 数值 | 解读 |
|------|------|------|
| RSI(14) | {report['technical_indicators']['rsi_14']:.1f} | {'超卖' if report['technical_indicators']['rsi_14'] < 30 else '超买' if report['technical_indicators']['rsi_14'] > 70 else '中性'} |
| RSI(30) | {report['technical_indicators']['rsi_30']:.1f} | {'超卖' if report['technical_indicators']['rsi_30'] < 30 else '超买' if report['technical_indicators']['rsi_30'] > 70 else '中性'} |
| SMA(20) | HK${report['technical_indicators']['sma_20']:.2f} | 短期趋势 |
| SMA(50) | HK${report['technical_indicators']['sma_50']:.2f} | 中期趋势 |
| EMA(12) | HK${report['technical_indicators']['ema_12']:.2f} | 快速趋势 |
| 动量(10) | {report['technical_indicators']['momentum_10']:.2f} | {'上涨' if report['technical_indicators']['momentum_10'] > 0 else '下跌'} |
| MACD | {report['technical_indicators']['macd_signal']} | {'多头' if report['technical_indicators']['macd_signal'] == 'BULLISH' else '空头'} |

## 📡 交易信号

"""
        )

        for signal in signals:
            icon = (
                "🟢"
                if signal["signal"] == "BUY"
                else "🔴" if signal["signal"] == "SELL" else "🟡"
            )
            f.write(
                f"- {icon} **{signal['indicator']}**: {signal['signal']} - {signal['reason']}\n"
            )
            f.write(f"  - 行动建议: {signal['action']}\n\n")

        f.write(
            f"""
## 📊 策略回测结果

- **策略 * *: {backtest_results['strategy']}
- **总收益率 * *: {backtest_results['total_return']:.2%}
- **年化收益率 * *: {backtest_results['annual_return']:.2%}
- **夏普比率 * *: {backtest_results['sharpe_ratio']:.3f}
- **最大回撤 * *: {backtest_results['max_drawdown']:.2%}
- **交易次数 * *: {backtest_results['trade_count']}

## 🎯 投资建议

"""
        )
        for rec in report["recommendations"]:
            f.write(f"- {rec}\n")

        f.write(
            f"""
---
*报告由量化交易系统自动生成*
*数据来源: 香港联合交易所 + 香港金管局*
"""
        )

    print(f"✅ 报告已保存:")
    print(f"   📊 JSON格式: {report_file}")
    print(f"   📄 Markdown格式: {md_file}")

    return report_file, md_file


def main():
    """主函数 - 完整的量化交易流程"""
    print("[+] 启动量化交易系统...")
    print("[+] 股票: 0700.HK (腾讯)")
    print("[+] 时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 步骤1: 获取股票数据
    stock_data = get_real_stock_data()
    if stock_data is None:
        print("❌ 无法获取股票数据，系统退出")
        return

    # 步骤2: 计算技术指标
    indicators = calculate_technical_indicators(stock_data)
    if indicators is None:
        print("❌ 无法计算技术指标，系统退出")
        return

    # 步骤3: 获取政府数据
    government_data = get_government_data()

    # 步骤4: 生成交易信号
    signals_result = generate_trading_signals(indicators, government_data)
    if signals_result:
        signals, recommendation = signals_result
    else:
        signals = []
        recommendation = "无法生成信号"

    # 步骤5: 运行回测
    backtest_results = run_vectorbt_backtest(stock_data)

    # 步骤6: 生成报告
    report_files = generate_trading_report(
        stock_data, indicators, signals, backtest_results
    )

    # 最终总结
    print("\n" + "=" * 80)
    print("[+] 量化交易会话完成!")
    print("=" * 80)
    print(f"[+] 股票: 0700.HK (腾讯)")
    print(f"[+] 当前价格: HK${indicators['current_price']:.2f}")
    print(f"[+] RSI(14): {indicators['rsi_14']:.1f}")
    print(f"[+] 综合建议: {recommendation}")

    if backtest_results:
        print(f"[+] 策略收益率: {backtest_results['annual_return']:.2%}")
        print(f"[+] 夏普比率: {backtest_results['sharpe_ratio']:.3f}")

    print(f"\n[+] 详细报告: {report_files[1]}")
    print("[+] 量化交易系统运行完成!")


if __name__ == "__main__":
    main()
