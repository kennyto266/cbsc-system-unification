#!/usr/bin/env python3
"""
Risk-Controlled Real Data Optimizer
基於真實HKMA數據的風控優化器
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

class RiskControlledOptimizer:
    """風控版真實數據優化器"""

    def __init__(self):
        self.base_url = "http://18.180.162.113:9191/inst/getInst"
        self.price_data = {}
        self.gov_data = {}
        self.crawler = HKMACrawler()

        # 風險管理參數
        self.max_position_size = 0.8  # 最大倉位80%，保留20%現金
        self.stop_loss = -0.15  # 15%止損
        self.max_drawdown_limit = -0.25  # 25%最大回撤限制
        self.volatility_threshold = 0.4  # 40%波動率閾值

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

            dates = list(data['data']['close'].keys())
            prices = list(data['data']['close'].values())

            self.price_data = {
                'dates': dates,
                'close': prices,
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

            data_length = len(self.price_data['close'])
            results = {}

            # 只獲取核心數據源MB (貨幣基礎)
            core_sources = ['MB']

            for source_code in core_sources:
                source_name = self.data_sources[source_code]
                try:
                    print(f"[GOV] 正在處理 {source_code} ({source_name})...")
                    data = await self.crawler.get_data_for_source(source_code, data_length)
                    results[source_code] = data
                    print(f"[GOV] [OK] {source_code}: {len(data)} 條真實數據記錄")

                except Exception as e:
                    print(f"[GOV] [ERROR] {source_code} 處理失敗: {e}")
                    return False

            self.gov_data = results
            print(f"[GOV] [SUCCESS] 成功整合 {len(self.gov_data)} 個數據源")
            return True

        except Exception as e:
            print(f"[ERROR] 政府數據整合失敗: {e}")
            return False

    def calculate_kdj(self, data: List[float], k_period: int = 9, d_period: int = 3) -> List[float]:
        """改進版KDJ計算"""
        if len(data) < k_period:
            return [50.0] * len(data)

        data_array = np.array(data)
        k_values = []
        d_values = []

        # 計算K值
        for i in range(len(data_array)):
            if i < k_period - 1:
                k_values.append(50.0)
            else:
                window = data_array[i-k_period+1:i+1]
                highest = np.max(window)
                lowest = np.min(window)

                if highest == lowest:
                    k_value = 50.0
                else:
                    k_value = 100 * (data_array[i] - lowest) / (highest - lowest)

                k_values.append(k_value)

        # 計算D值 (K的移動平均)
        for i in range(len(k_values)):
            if i < d_period - 1:
                d_values.append(50.0)
            else:
                d_value = np.mean(k_values[i-d_period+1:i+1])
                d_values.append(d_value)

        return d_values

    def generate_risk_controlled_signals(self, source_code: str, kdj_config: Dict) -> List[int]:
        """生成風控交易信號"""
        if source_code not in self.gov_data:
            return [0] * len(self.price_data['close'])

        data = self.gov_data[source_code]
        kdj_values = self.calculate_kdj(data, kdj_config['k_period'], kdj_config['d_period'])

        signals = []
        for i, kdj in enumerate(kdj_values):
            if i < 20:  # 前20天無信號
                signals.append(0)
            elif kdj < 20:  # 超賣
                signals.append(1)
            elif kdj > 80:  # 超買
                signals.append(-1)
            else:
                signals.append(0)

        return signals

    def apply_risk_management(self, signals: List[int], prices: List[float]) -> List[int]:
        """應用風險管理"""
        controlled_signals = signals.copy()
        current_position = 0
        entry_price = 0

        for i in range(1, len(signals)):
            current_price = prices[i]

            # 止損檢查
            if current_position == 1 and entry_price > 0:
                drawdown = (current_price - entry_price) / entry_price
                if drawdown <= self.stop_loss:
                    controlled_signals[i] = -1  # 強制平倉
                    print(f"[RISK] 止損觸發: {drawdown:.2%} 在位置 {i}")
                    current_position = 0
                    continue

            # 信號處理
            if signals[i] == 1 and current_position == 0:
                # 買入信號，但檢查倉位大小
                current_position = self.max_position_size
                entry_price = current_price
                controlled_signals[i] = 1

            elif signals[i] == -1 and current_position > 0:
                # 賣出信號
                current_position = 0
                entry_price = 0
                controlled_signals[i] = -1

            else:
                controlled_signals[i] = 0

        return controlled_signals

    def calculate_strategy_performance(self, signals: List[int]) -> Dict[str, float]:
        """計算策略性能（含風控）"""
        prices = self.price_data['close']

        if len(signals) != len(prices):
            return {"error": "Signal and price length mismatch"}

        initial_capital = 100000
        portfolio_value = initial_capital
        positions = [0]  # 持倉狀態
        returns = []
        peak_value = initial_capital
        drawdowns = []

        for i in range(1, len(prices)):
            current_signal = signals[i]
            current_price = prices[i]
            prev_position = positions[i-1]
            prev_value = portfolio_value

            if current_signal == 1 and prev_position == 0:  # 買入
                # 買入時使用部分倉位
                position_value = portfolio_value * self.max_position_size
                cash_remaining = portfolio_value * (1 - self.max_position_size)
                portfolio_value = cash_remaining + position_value  # 買入後總價值不變
                positions.append(self.max_position_size)
                returns.append(0)

            elif current_signal == -1 and prev_position > 0:  # 賣出
                # 計算持倉期間回報
                period_return = (current_price - prices[i-1]) / prices[i-1]
                position_return = period_return * prev_position
                portfolio_value = portfolio_value * (1 + position_return)
                returns.append(position_return)
                positions.append(0)

            else:  # 持有或空倉
                if prev_position > 0:
                    # 持倉期間的價值變化
                    period_return = (current_price - prices[i-1]) / prices[i-1]
                    position_return = period_return * prev_position
                    portfolio_value = portfolio_value * (1 + position_return)
                    returns.append(position_return)
                else:
                    # 空倉，價值不變
                    returns.append(0)
                positions.append(prev_position)

            # 計算最大回撤
            peak_value = max(peak_value, portfolio_value)
            drawdown = (portfolio_value - peak_value) / peak_value
            drawdowns.append(drawdown)

        # 計算性能指標
        total_return = (portfolio_value - initial_capital) / initial_capital
        days = len(prices)
        years = days / 252
        annual_return = ((1 + total_return) ** (1/years) - 1) if years > 0 else 0

        if len(returns) > 1 and np.std(returns) > 0:
            volatility = np.std(returns) * np.sqrt(252)
            sharpe_ratio = (annual_return - 0.03) / volatility
        else:
            volatility = 0
            sharpe_ratio = 0

        max_drawdown = min(drawdowns) if drawdowns else 0

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "trades": sum(1 for s in signals if s != 0),
            "win_rate": len([r for r in returns if r > 0]) / len(returns) if returns else 0,
            "final_value": portfolio_value,
            "peak_value": peak_value,
            "risk_controlled": True
        }

    def run_risk_controlled_optimization(self) -> List[Dict]:
        """運行風控優化"""
        print("\n[RISK-OPT] 開始風控優化...")
        print(f"[RISK-OPT] 風控參數: 最大倉位{self.max_position_size:.0%}, 止損{self.stop_loss:.0%}")

        results = []

        # 測試改進的MB_KDJ策略
        kdj_configs = [
            {"k_period": 10, "d_period": 2},  # 原版
            {"k_period": 14, "d_period": 3},  # 保守版
            {"k_period": 8, "d_period": 2},   # 敏捷版
            {"k_period": 20, "d_period": 5},  # 長期版
        ]

        strategy_count = 0
        for config in kdj_configs:
            try:
                print(f"\n[RISK-OPT] 測試 KDJ {config}...")

                # 生成交易信號
                signals = self.generate_risk_controlled_signals('MB', config)

                # 應用風險管理
                risk_signals = self.apply_risk_management(signals, self.price_data['close'])

                # 計算性能
                performance = self.calculate_strategy_performance(risk_signals)

                if "error" not in performance:
                    strategy_result = {
                        "strategy_id": f"RC_MB_KDJ_{strategy_count}",
                        "source_code": "MB",
                        "source_name": "貨幣基礎數據",
                        "indicator_type": "KDJ",
                        "config": config,
                        "performance": performance,
                        "data_type": "REAL_HKMA_RISK_CONTROLLED"
                    }
                    results.append(strategy_result)

                    print(f"  [OK] Sharpe={performance['sharpe_ratio']:.3f}, 回撤={performance['max_drawdown']:.2%}")

                strategy_count += 1

            except Exception as e:
                print(f"  [ERROR] 配置 {config} 失敗: {e}")
                strategy_count += 1

        # 排序結果
        results.sort(key=lambda x: x["performance"]["sharpe_ratio"], reverse=True)

        print(f"\n[RISK-OPT] 風控優化完成！")
        print(f"[RISK-OPT] 成功測試 {len(results)} 個策略")

        if results:
            print(f"\n[TOP 3] 最佳風控策略:")
            for i, result in enumerate(results[:3]):
                perf = result["performance"]
                print(f"  {i+1}. {result['strategy_id']}")
                print(f"     參數: K{result['config']['k_period']}, D{result['config']['d_period']}")
                print(f"     Sharpe: {perf['sharpe_ratio']:.3f}")
                print(f"     年化回報: {perf['annual_return']:.2%}")
                print(f"     最大回撤: {perf['max_drawdown']:.2%}")
                print(f"     最終價值: HK${perf['final_value']:,.0f}")

                # 評級
                if perf['max_drawdown'] > -0.20:
                    print(f"     *** 風控優秀 (回撤 < 20%) ***")

        return results

    def close(self):
        """清理資源"""
        if hasattr(self, 'crawler'):
            self.crawler.close()

def main():
    """主程序"""
    print("=" * 80)
    print("風控版真實數據優化器")
    print("基於真實HKMA數據 + 專業風險管理")
    print("=" * 80)

    optimizer = RiskControlledOptimizer()

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

        # 3. 運行風控優化
        print(f"\n步驟3/3: 運行風控優化")
        results = optimizer.run_risk_controlled_optimization()

        # 保存結果
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"risk_controlled_optimization_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n🎉 風控優化完成！結果已保存到: {filename}")

        # 對比原版結果
        print(f"\n📊 風控效果對比:")
        if results:
            best_rc = results[0]["performance"]
            print(f"風控版 Sharpe: {best_rc['sharpe_ratio']:.3f}")
            print(f"風控版 回撤: {best_rc['max_drawdown']:.2%}")
            print(f"風控版 回報: {best_rc['annual_return']:.2%}")

            print(f"\n原版對比:")
            print(f"原版 Sharpe: 1.680")
            print(f"原版 回撤: -100.00%")
            print(f"原版 回報: 56.85%")

            print(f"\n風控改進:")
            sharpe_change = ((best_rc['sharpe_ratio'] - 1.680) / 1.680) * 100
            drawdown_improvement = best_rc['max_drawdown'] - (-1.0)
            print(f"Sharpe變化: {sharpe_change:+.1f}%")
            print(f"回撤改進: {drawdown_improvement:+.2f}")

    except Exception as e:
        print(f"ERROR: 優化過程出錯: {e}")
        import traceback
        traceback.print_exc()
    finally:
        optimizer.close()

if __name__ == "__main__":
    main()