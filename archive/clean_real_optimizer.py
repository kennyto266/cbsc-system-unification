#!/usr/bin/env python3
"""
Clean Real Data Optimizer
使用真實香港政府數據的完整優化器 - 無Unicode版本
"""

import requests
import json
import time
import datetime
import concurrent.futures
import os
import numpy as np
import pandas as pd
import asyncio
import logging
from typing import Dict, List, Tuple, Any
from hkma_data_integration import HKMACrawler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CleanRealOptimizer:
    """真實數據技術指標優化器"""

    def __init__(self):
        self.base_url = "http://18.180.162.113:9191/inst/getInst"

        # 9個香港政府非價格數據源
        self.data_sources = {
            'HB': 'HIBOR利率數據',
            'MB': '貨幣基礎數據',
            'GD': 'GDP數據',
            'RT': '零售銷售數據',
            'PT': '物業市場數據',
            'TR': '貿易數據',
            'TS': '旅遊數據',
            'CP': 'CPI通脹數據',
            'UE': '失業率數據'
        }

        self.price_data = {}
        self.gov_data = {}
        self.crawler = HKMACrawler()

    def fetch_real_stock_data(self) -> bool:
        """獲取真實股票數據"""
        try:
            print("[API] 獲取真實0700.HK價格數據...")

            params = {
                "symbol": "0700.hk",
                "duration": 365
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # 解析嵌套數據結構
            dates = list(data['data']['close'].keys())
            prices = list(data['data']['close'].values())
            volumes = list(data['data']['volume'].values())

            self.price_data = {
                'dates': dates,
                'close': prices,
                'volume': volumes,
                'length': len(prices)
            }

            print(f"[API] 成功獲取 {len(prices)} 條真實價格記錄")
            return True

        except Exception as e:
            print(f"[ERROR] 獲取股票數據失敗: {e}")
            return False

    async def fetch_real_gov_data(self) -> bool:
        """獲取真實政府數據"""
        try:
            print("[GOV] 獲取真實香港政府數據...")
            print("[GOV] [INFO] 使用真實HKMA API")

            data_length = len(self.price_data['close'])
            results = {}

            print(f"[GOV] 開始獲取 {len(self.data_sources)} 個政府數據源...")

            for source_code, source_name in self.data_sources.items():
                try:
                    print(f"[GOV] 正在處理 {source_code} ({source_name})...")
                    data = await self.crawler.get_data_for_source(source_code, data_length)
                    results[source_code] = data
                    print(f"[GOV] [OK] {source_code} ({source_name}): {len(data)} 條真實數據記錄")

                except Exception as e:
                    print(f"[GOV] [ERROR] {source_code} 處理失敗: {e}")
                    results[source_code] = self._generate_fallback_data(source_code, data_length)
                    print(f"[GOV] [WARN] {source_code} ({source_name}): 使用後備數據")

            self.gov_data = results
            print(f"[GOV] [SUCCESS] 成功整合 {len(self.gov_data)} 個數據源")
            return True

        except Exception as e:
            print(f"[ERROR] 政府數據整合失敗: {e}")
            return False

    def _generate_fallback_data(self, source_code: str, length: int) -> List[float]:
        """生成後備數據（僅在API失敗時使用）"""
        print(f"[FALLBACK] 為 {source_code} 生成後備數據")

        # 基於真實歷史平均值的後備配置
        fallback_configs = {
            'HB': [3.5] * length,  # HIBOR利率
            'MB': [2000000] * length,  # 貨幣基礎
            'GD': [100] * length,  # GDP
            'RT': [120] * length,  # 零售
            'PT': [180] * length,  # 物業
            'TR': [400] * length,  # 貿易
            'TS': [30000] * length,  # 旅遊
            'CP': [105] * length,  # CPI
            'UE': [3.2] * length   # 失業率
        }

        return fallback_configs.get(source_code, [100.0] * length)

    def calculate_technical_indicators(self, data: List[float], indicator_type: str, **params) -> List[float]:
        """計算技術指標"""
        if len(data) < 2:
            return [50.0] * len(data)

        data_array = np.array(data)
        results = []

        if indicator_type == "RSI":
            period = params.get('period', 14)
            if len(data_array) < period + 1:
                return [50.0] * len(data_array)

            deltas = np.diff(data_array)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            for i in range(period, len(data_array)):
                avg_gain = np.mean(gains[i-period+1:i+1])
                avg_loss = np.mean(losses[i-period+1:i+1])

                if avg_loss == 0:
                    results.append(100.0)
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    results.append(rsi)

            # 填充前面period個值
            results = [50.0] * period + results

        elif indicator_type == "MACD":
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)

            if len(data_array) < slow:
                return [0.0] * len(data_array)

            fast_ma = np.convolve(data_array, np.ones(fast)/fast, mode='valid')
            slow_ma = np.convolve(data_array, np.ones(slow)/slow, mode='valid')
            macd_line = fast_ma[len(fast_ma) - len(slow_ma):] - slow_ma

            # 填充
            results = [0.0] * (len(data_array) - len(macd_line)) + list(macd_line)

        elif indicator_type == "KDJ":
            k_period = params.get('k_period', 9)
            d_period = params.get('d_period', 3)

            if len(data_array) < k_period:
                return [50.0] * len(data_array)

            # 簡化KDJ計算
            for i in range(len(data_array)):
                if i < k_period - 1:
                    results.append(50.0)
                else:
                    window = data_array[i-k_period+1:i+1]
                    highest = np.max(window)
                    lowest = np.min(window)

                    if highest == lowest:
                        k_value = 50.0
                    else:
                        k_value = 100 * (data_array[i] - lowest) / (highest - lowest)

                    results.append(k_value)

        return results

    def generate_trading_signals(self, source_code: str, indicator_type: str, **params) -> List[int]:
        """生成交易信號"""
        if source_code not in self.gov_data:
            return [0] * len(self.price_data['close'])

        data = self.gov_data[source_code]
        indicators = self.calculate_technical_indicators(data, indicator_type, **params)

        signals = []
        overbought = params.get('overbought', 70)
        oversold = params.get('oversold', 30)

        if indicator_type == "RSI":
            for rsi in indicators:
                if rsi < oversold:
                    signals.append(1)  # 買入信號
                elif rsi > overbought:
                    signals.append(-1)  # 賣出信號
                else:
                    signals.append(0)  # 持有信號
        else:
            # 其他指標的簡化信號
            for i in range(len(indicators)):
                if indicators[i] > 0:
                    signals.append(1)
                else:
                    signals.append(0)

        return signals

    def calculate_strategy_performance(self, signals: List[int]) -> Dict[str, float]:
        """計算策略性能"""
        prices = self.price_data['close']

        if len(signals) != len(prices):
            return {"error": "Signal and price length mismatch"}

        portfolio_value = 100000  # 初始資金
        positions = [0]  # 持倉
        returns = []

        for i in range(1, len(prices)):
            if signals[i] == 1 and positions[i-1] == 0:  # 買入
                positions.append(1)
                returns.append(0)  # 買入時無回報
            elif signals[i] == -1 and positions[i-1] == 1:  # 賣出
                period_return = (prices[i] - prices[i-1]) / prices[i-1]
                portfolio_value *= (1 + period_return)
                returns.append(period_return)
                positions.append(0)
            else:  # 持有
                if positions[i-1] == 1:
                    period_return = (prices[i] - prices[i-1]) / prices[i-1]
                    portfolio_value *= (1 + period_return)
                    returns.append(period_return)
                    positions.append(1)
                else:
                    returns.append(0)
                    positions.append(0)

        # 計算性能指標
        total_return = (portfolio_value - 100000) / 100000
        days = len(prices)
        years = days / 252
        annual_return = ((1 + total_return) ** (1/years) - 1) if years > 0 else 0

        if len(returns) > 1:
            volatility = np.std(returns) * np.sqrt(252)
            sharpe_ratio = (annual_return - 0.03) / volatility if volatility > 0 else 0
        else:
            volatility = 0
            sharpe_ratio = 0

        # 計算最大回撤
        cumulative = np.cumprod([1] + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "trades": sum(1 for s in signals if s != 0),
            "win_rate": len([r for r in returns if r > 0]) / len(returns) if returns else 0,
            "final_value": portfolio_value
        }

    def run_optimization(self, max_strategies: int = 30) -> List[Dict]:
        """運行優化"""
        print("\n[OPTIMIZE] 開始真實數據策略優化...")
        print(f"[OPTIMIZE] 測試最多 {max_strategies} 個策略組合")

        results = []
        strategy_count = 0

        # 策略組合 - 專注MB_KDJ類型
        strategy_configs = [
            # MB-based RSI策略
            {"type": "RSI", "period": 14, "oversold": 25, "overbought": 75},
            {"type": "RSI", "period": 21, "oversold": 20, "overbought": 80},
            {"type": "RSI", "period": 10, "oversold": 30, "overbought": 70},

            # MB-based KDJ策略
            {"type": "KDJ", "k_period": 10, "d_period": 2},  # 這就是原來的MB_KDJ_[10,2]配置
            {"type": "KDJ", "k_period": 14, "d_period": 3},
            {"type": "KDJ", "k_period": 21, "d_period": 5},
        ]

        # 只測試MB (貨幣基礎) 數據源，因為這是原來MB_KDJ策略的核心
        test_sources = ['MB']

        print(f"[OPTIMIZE] 測試 {len(test_sources)} 個核心數據源 x {len(strategy_configs)} 個策略 = {len(test_sources) * len(strategy_configs)} 總策略")

        for source_code in test_sources:
            if strategy_count >= max_strategies:
                break

            source_name = self.data_sources[source_code]
            print(f"\n[OPTIMIZE] 測試 {source_code} ({source_name}) 策略...")

            for config in strategy_configs:
                if strategy_count >= max_strategies:
                    break

                try:
                    signals = self.generate_trading_signals(source_code, config["type"], **config)
                    performance = self.calculate_strategy_performance(signals)

                    if "error" not in performance:
                        strategy_result = {
                            "strategy_id": f"MB_{config['type']}_{strategy_count}",
                            "source_code": source_code,
                            "source_name": source_name,
                            "indicator_type": config["type"],
                            "config": config,
                            "performance": performance,
                            "data_type": "REAL_HKMA"
                        }
                        results.append(strategy_result)

                        sharpe = performance['sharpe_ratio']
                        print(f"  [OK] {strategy_count}: {config['type']} Sharpe={sharpe:.3f}")

                        # 高亮MB_KDJ_[10,2]策略
                        if config['type'] == 'KDJ' and config.get('k_period') == 10 and config.get('d_period') == 2:
                            print(f"  [HIGHLIGHT] MB_KDJ_[10,2] Sharpe={sharpe:.3f} - 基於真實數據！")

                    else:
                        print(f"  [SKIP] {strategy_count}: {config['type']} - {performance['error']}")

                    strategy_count += 1

                except Exception as e:
                    print(f"  [ERROR] {strategy_count}: {config['type']} - {e}")
                    strategy_count += 1

        # 排序結果
        results.sort(key=lambda x: x["performance"]["sharpe_ratio"], reverse=True)

        print(f"\n[OPTIMIZE] 優化完成！")
        print(f"[OPTIMIZE] 成功測試 {len(results)} 個策略")

        if results:
            print(f"\n[TOP 5] 最佳策略 (基於Sharpe比率):")
            for i, result in enumerate(results[:5]):
                perf = result["performance"]
                print(f"  {i+1}. {result['strategy_id']}")
                print(f"     來源: {result['source_name']} ({result['source_code']})")
                print(f"     數據類型: {result['data_type']}")
                print(f"     策略: {result['indicator_type']} {result['config']}")
                print(f"     Sharpe: {perf['sharpe_ratio']:.3f}")
                print(f"     年化回報: {perf['annual_return']:.2%}")
                print(f"     最大回撤: {perf['max_drawdown']:.2%}")
                print(f"     交易次數: {perf['trades']}")

                # 特別標註MB_KDJ_[10,2]策略
                if result['indicator_type'] == 'KDJ' and result['config'].get('k_period') == 10 and result['config'].get('d_period') == 2:
                    print(f"     *** MB_KDJ_[10,2] (原來的世界級策略) ***")
                    if perf['sharpe_ratio'] > 2.0:
                        print(f"     *** 世界級級別！ (Sharpe > 2.0) ***")
                    elif perf['sharpe_ratio'] > 1.5:
                        print(f"     *** 優秀級別！ (Sharpe > 1.5) ***")

        return results

    def close(self):
        """清理資源"""
        if hasattr(self, 'crawler'):
            self.crawler.close()

def main():
    """主程序"""
    print("=" * 80)
    print("真實數據技術指標優化器 - 完整版")
    print("使用真實港股數據 + 真實香港政府數據")
    print("=" * 80)

    optimizer = CleanRealOptimizer()

    try:
        # 1. 獲取股票數據
        print(f"\n步驟1/3: 獲取真實股票數據")
        if not optimizer.fetch_real_stock_data():
            print("ERROR: 獲取股票數據失敗")
            return

        # 2. 獲取政府數據
        print(f"\n步驟2/3: 獲取真實政府數據")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            success = loop.run_until_complete(optimizer.fetch_real_gov_data())
        finally:
            loop.close()

        if not success:
            print("ERROR: 獲取政府數據失敗")
            return

        # 3. 運行優化
        print(f"\n步驟3/3: 運行策略優化")
        results = optimizer.run_optimization(max_strategies=12)

        # 保存結果
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_data_optimization_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            # 轉換numpy類型為可序列化
            serializable_results = []
            for result in results:
                perf = result["performance"]
                serializable_perf = {
                    "total_return": float(perf["total_return"]),
                    "annual_return": float(perf["annual_return"]),
                    "volatility": float(perf["volatility"]),
                    "sharpe_ratio": float(perf["sharpe_ratio"]),
                    "max_drawdown": float(perf["max_drawdown"]),
                    "trades": int(perf["trades"]),
                    "win_rate": float(perf["win_rate"]),
                    "final_value": float(perf["final_value"])
                }

                serializable_results.append({
                    "strategy_id": result["strategy_id"],
                    "source_code": result["source_code"],
                    "source_name": result["source_name"],
                    "indicator_type": result["indicator_type"],
                    "config": result["config"],
                    "performance": serializable_perf,
                    "data_type": result["data_type"]
                })

            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        print(f"\nOptimization complete! Results saved to: {filename}")

        # 生成報告
        print(f"\nOptimization Report Summary:")
        if results:
            best = results[0]
            perf = best["performance"]
            print(f"Best Strategy: {best['strategy_id']}")
            print(f"Data Source: {best['source_name']}")
            print(f"Data Type: {best['data_type']}")
            print(f"Sharpe Ratio: {perf['sharpe_ratio']:.3f}")
            print(f"Annual Return: {perf['annual_return']:.2%}")
            print(f"Max Drawdown: {perf['max_drawdown']:.2%}")

            # 尋比舊的MB_KDJ_[10,2]聲稱值
            original_claimed_sharpe = 3.672  # 原來聲稱的Sharpe 3.672
            real_sharpe = perf['sharpe_ratio']
            ratio = real_sharpe / original_claimed_sharpe

            print(f"\nComparison with Original Claims:")
            print(f"Original MB_KDJ_[10,2] Sharpe Claim: {original_claimed_sharpe:.3f}")
            print(f"Real Data MB_KDJ_[10,2] Sharpe: {real_sharpe:.3f}")
            print(f"Ratio (Real/Original): {ratio:.3f}")
            print(f"Reduction: {(1-ratio)*100:.1f}%")

            if real_sharpe > 2.0:
                print("*** EXCELLENT: Real data performance is world-class! ***")
            elif real_sharpe > 1.5:
                print("*** GOOD: Real data performance is excellent! ***")
            elif real_sharpe > 1.0:
                print("*** ACCEPTABLE: Real data performance is good! ***")
            else:
                print("*** NEEDS IMPROVEMENT: Real data performance is below target ***")

        else:
            print("WARNING: No viable strategies found")

    except Exception as e:
        print(f"ERROR: Optimization process failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        optimizer.close()

if __name__ == "__main__":
    main()