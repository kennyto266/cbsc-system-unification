#!/usr/bin/env python3
"""
Balanced Risk Optimizer
平衡風險優化器 - 在風控和收益之間找到平衡
"""

import requests
import json
import time
import datetime
import asyncio
import logging
import numpy as np
from typing import Dict, List, Tuple, Any
from hkma_data_integration import HKMACrawler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BalancedRiskOptimizer:
    """平衡風險優化器"""

    def __init__(self):
        self.base_url = "http://18.180.162.113:9191/inst/getInst"
        self.price_data = {}
        self.gov_data = {}
        self.crawler = HKMACrawler()

        # 平衡風險管理參數
        self.max_position_size = 1.0  # 全倉，但加入止損
        self.stop_loss = -0.25  # 25%止損（較寬鬆）
        self.trailing_stop = -0.15  # 15%移動止損
        self.max_consecutive_losses = 5  # 連續5次虧損後暫停

        self.data_sources = {
            'MB': '貨幣基礎數據'
        }

    async def fetch_real_data(self) -> bool:
        """獲取真實數據"""
        try:
            # 股票數據
            print("[API] 獲取真實0700.HK數據...")
            response = requests.get(self.base_url, params={"symbol": "0700.hk", "duration": 365}, timeout=30)
            response.raise_for_status()
            data = response.json()

            self.price_data = {
                'dates': list(data['data']['close'].keys()),
                'close': list(data['data']['close'].values()),
                'length': len(data['data']['close'])
            }

            # 政府數據
            self.gov_data = {'MB': await self.crawler.get_data_for_source('MB', len(self.price_data['close']))}

            print(f"[OK] 成功獲取數據: 股價{len(self.price_data['close'])}條, 政府數據{len(self.gov_data['MB'])}條")
            return True

        except Exception as e:
            print(f"[ERROR] 數據獲取失敗: {e}")
            return False

    def calculate_enhanced_kdj(self, data: List[float], k_period: int = 10, d_period: int = 2) -> List[float]:
        """增強版KDJ計算"""
        if len(data) < k_period:
            return [50.0] * len(data)

        data_array = np.array(data)
        kdj_values = []

        for i in range(len(data_array)):
            if i < k_period - 1:
                kdj_values.append(50.0)
            else:
                window = data_array[i-k_period+1:i+1]
                rsv = 100 * (data_array[i] - np.min(window)) / (np.max(window) - np.min(window)) if np.max(window) != np.min(window) else 50.0

                # 使用更平滑的K值計算
                if i == k_period - 1:
                    k_value = rsv * (1/3) + 50 * (2/3)
                else:
                    k_value = rsv * (1/3) + kdj_values[-1] * (2/3)

                # D值計算
                if i == k_period - 1 + d_period - 1:
                    d_value = k_value * (1/3) + 50 * (2/3)
                elif i > k_period - 1 + d_period - 1:
                    d_values = kdj_values[-d_period+1:] + [k_value]
                    d_value = sum(d_values) / len(d_values)
                else:
                    d_value = 50.0

                kdj_values.append(d_value)

        return kdj_values

    def generate_smart_signals(self, kdj_config: Dict) -> List[int]:
        """生成智能交易信號"""
        mb_data = self.gov_data['MB']
        kdj_values = self.calculate_enhanced_kdj(mb_data, kdj_config['k_period'], kdj_config['d_period'])

        signals = []
        for i, kdj in enumerate(kdj_values):
            if i < 30:  # 前30天穩定期
                signals.append(0)
            elif kdj < 15:  # 深度超賣
                signals.append(1)
            elif kdj > 85:  # 深度超買
                signals.append(-1)
            elif kdj < 35 and kdj > kdj_values[i-1] if i > 0 else False:  # 上升突破
                signals.append(1)
            elif kdj > 65 and kdj < kdj_values[i-1] if i > 0 else False:  # 下降突破
                signals.append(-1)
            else:
                signals.append(0)

        return signals

    def apply_smart_risk_management(self, signals: List[int], prices: List[float]) -> Tuple[List[int], Dict]:
        """應用智能風險管理"""
        managed_signals = signals.copy()
        position = 0
        entry_price = 0
        consecutive_losses = 0
        stats = {
            'stop_losses': 0,
            'trailing_stops': 0,
            'loss_halts': 0,
            'total_adjustments': 0
        }

        for i in range(1, len(signals)):
            current_price = prices[i]

            # 移動止損檢查
            if position == 1 and entry_price > 0:
                current_return = (current_price - entry_price) / entry_price

                # 移動止損
                if current_return > 0.1:  # 盈利10%後啟動移動止損
                    trailing_stop_price = entry_price * (1 + max(0.05, current_return + self.trailing_stop))
                    if current_price < trailing_stop_price:
                        managed_signals[i] = -1
                        stats['trailing_stops'] += 1
                        position = 0
                        entry_price = 0
                        continue

                # 固定止損
                if current_return <= self.stop_loss:
                    managed_signals[i] = -1
                    stats['stop_losses'] += 1
                    consecutive_losses += 1
                    position = 0
                    entry_price = 0
                    continue

            # 連續虧損暫停
            if consecutive_losses >= self.max_consecutive_losses:
                for j in range(i, min(i+10, len(signals))):  # 暫停10天
                    if managed_signals[j] == 1:
                        managed_signals[j] = 0
                consecutive_losses = 0
                stats['loss_halts'] += 1

            # 正常信號處理
            if signals[i] == 1 and position == 0:
                position = 1
                entry_price = current_price
                managed_signals[i] = 1
            elif signals[i] == -1 and position == 1:
                position = 0
                entry_price = 0
                consecutive_losses = 0
                managed_signals[i] = -1
            elif signals[i] != 0 and position != 0:
                managed_signals[i] = 0  # 忽略衝突信號

            stats['total_adjustments'] += 1

        return managed_signals, stats

    def calculate_enhanced_performance(self, original_signals: List[int], managed_signals: List[int]) -> Dict[str, float]:
        """計算增強性能指標"""
        prices = self.price_data['close']

        # 原信號性能
        original_perf = self._calculate_performance(original_signals, prices, "Original")

        # 風控信號性能
        managed_perf = self._calculate_performance(managed_signals, prices, "Managed")

        return {
            'original': original_perf,
            'managed': managed_perf,
            'sharpe_improvement': managed_perf['sharpe_ratio'] - original_perf['sharpe_ratio'],
            'drawdown_improvement': managed_perf['max_drawdown'] - original_perf['max_drawdown'],
            'return_stability': managed_perf['annual_return'] / original_perf['annual_return'] if original_perf['annual_return'] > 0 else 1
        }

    def _calculate_performance(self, signals: List[int], prices: List[float], label: str) -> Dict[str, float]:
        """內部性能計算"""
        if len(signals) != len(prices):
            return {"error": "Length mismatch"}

        capital = 100000
        position = 0
        portfolio_value = capital
        returns = []
        peak = capital
        drawdowns = []

        for i in range(1, len(signals)):
            if signals[i] == 1 and position == 0:  # 買入
                position = 1
                returns.append(0)
            elif signals[i] == -1 and position == 1:  # 賣出
                period_return = (prices[i] - prices[i-1]) / prices[i-1]
                portfolio_value *= (1 + period_return)
                returns.append(period_return)
                position = 0
            elif position == 1:  # 持倉
                period_return = (prices[i] - prices[i-1]) / prices[i-1]
                portfolio_value *= (1 + period_return)
                returns.append(period_return)
            else:  # 空倉
                returns.append(0)

            peak = max(peak, portfolio_value)
            drawdowns.append((portfolio_value - peak) / peak)

        total_return = (portfolio_value - capital) / capital
        years = len(prices) / 252
        annual_return = ((1 + total_return) ** (1/years) - 1) if years > 0 else 0

        volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0
        sharpe_ratio = (annual_return - 0.03) / volatility if volatility > 0 else 0
        max_drawdown = min(drawdowns) if drawdowns else 0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'final_value': portfolio_value,
            'trades': sum(1 for s in signals if s != 0),
            'win_rate': len([r for r in returns if r > 0]) / len(returns) if returns else 0
        }

    def run_balanced_optimization(self) -> List[Dict]:
        """運行平衡優化"""
        print("\n[BALANCED] 開始平衡風險優化...")
        print(f"[BALANCED] 風控參數: 止損{self.stop_loss:.0%}, 移動止損{self.trailing_stop:.0%}")

        results = []

        # 測試多種KDJ配置
        configs = [
            {"k_period": 10, "d_period": 2},  # 原版
            {"k_period": 14, "d_period": 3},  # 穩健版
            {"k_period": 8, "d_period": 2},   # 靈活版
            {"k_period": 12, "d_period": 4},  # 平衡版
        ]

        for i, config in enumerate(configs):
            try:
                print(f"\n[BALANCED] 測試配置 {i+1}: K{config['k_period']}, D{config['d_period']}")

                # 生成智能信號
                smart_signals = self.generate_smart_signals(config)

                # 應用風險管理
                managed_signals, risk_stats = self.apply_smart_risk_management(smart_signals, self.price_data['close'])

                # 計算性能
                performance = self.calculate_enhanced_performance(smart_signals, managed_signals)

                strategy_result = {
                    "strategy_id": f"BAL_MB_KDJ_{i}",
                    "config": config,
                    "performance": performance,
                    "risk_stats": risk_stats,
                    "data_type": "BALANCED_RISK_REAL"
                }
                results.append(strategy_result)

                print(f"  [OK] 原信號 Sharpe: {performance['original']['sharpe_ratio']:.3f}")
                print(f"  [OK] 風控信號 Sharpe: {performance['managed']['sharpe_ratio']:.3f}")
                print(f"  [OK] 回撤改善: {performance['drawdown_improvement']:.2%}")
                print(f"  [OK] 止損觸發: {risk_stats['stop_losses']}次")

            except Exception as e:
                print(f"  [ERROR] 配置 {config} 失敗: {e}")

        # 排序結果
        results.sort(key=lambda x: x["performance"]["managed"]["sharpe_ratio"], reverse=True)

        print(f"\n[BALANCED] 平衡優化完成！")
        print(f"[BALANCED] 成功測試 {len(results)} 個策略")

        if results:
            print(f"\n[TOP 3] 最佳平衡策略:")
            for i, result in enumerate(results[:3]):
                orig = result["performance"]["original"]
                mang = result["performance"]["managed"]
                print(f"  {i+1}. {result['strategy_id']}")
                print(f"     參數: K{result['config']['k_period']}, D{result['config']['d_period']}")
                print(f"     原信號: Sharpe {orig['sharpe_ratio']:.3f}, 回撤 {orig['max_drawdown']:.2%}")
                print(f"     風控後: Sharpe {mang['sharpe_ratio']:.3f}, 回撤 {mang['max_drawdown']:.2%}")
                print(f"     改善效果: Sharpe {result['performance']['sharpe_improvement']:+.3f}, 回撤 {result['performance']['drawdown_improvement']:+.2%}")
                print(f"     最終價值: HK${mang['final_value']:,.0f}")

        return results

    def close(self):
        """清理資源"""
        if hasattr(self, 'crawler'):
            self.crawler.close()

def main():
    """主程序"""
    print("=" * 80)
    print("平衡風險優化器")
    print("在風控和收益之間找到最佳平衡點")
    print("=" * 80)

    optimizer = BalancedRiskOptimizer()

    try:
        # 獲取數據
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if not loop.run_until_complete(optimizer.fetch_real_data()):
                print("ERROR: 數據獲取失敗")
                return
        finally:
            loop.close()

        # 運行優化
        results = optimizer.run_balanced_optimization()

        # 保存結果
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"balanced_risk_optimization_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n[BALANCED] 優化完成！結果保存至: {filename}")

        # 綜合評估
        if results:
            best = results[0]
            managed_perf = best["performance"]["managed"]
            original_perf = best["performance"]["original"]

            print(f"\n[FINAL] 最佳策略綜合評估:")
            print(f"策略ID: {best['strategy_id']}")
            print(f"原信號 Sharpe: {original_perf['sharpe_ratio']:.3f}")
            print(f"風控後 Sharpe: {managed_perf['sharpe_ratio']:.3f}")
            print(f"Sharpe提升: {best['performance']['sharpe_improvement']:+.3f}")
            print(f"回撤改善: {best['performance']['drawdown_improvement']:+.2%}")
            print(f"風險統計: 止損{best['risk_stats']['stop_losses']}次, 移動止損{best['risk_stats']['trailing_stops']}次")

    except Exception as e:
        print(f"ERROR: 優化失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        optimizer.close()

if __name__ == "__main__":
    main()