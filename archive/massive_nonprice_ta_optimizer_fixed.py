#!/usr/bin/env python3
"""
Fixed Massive Non-Price Technical Analysis Optimizer
修復後的非價格技術分析優化器 - 使用VectorBT內置Sharpe比率計算
"""

import numpy as np
import pandas as pd
import requests
import json
from datetime import datetime
from typing import Dict, List, Any
import vectorbt as vbt

class FixedNonPriceOptimizer:
    """修復後的非價格技術指標優化器 - 使用VectorBT內置方法"""

    def __init__(self):
        self.base_url = "http://18.180.162.113:9191/inst/getInst"
        self.risk_free_rate = 0.03  # 3%無風險利率

        # 9個香港政府數據源
        self.data_sources = {
            'HB': 'HIBOR利率數據',
            'GD': 'GDP數據',
            'RT': '零售銷售數據',
            'PT': '物業市場數據',
            'TR': '貿易數據',
            'TS': '旅遊數據',
            'CP': 'CPI通脹數據',
            'UE': '失業率數據',
            'MB': '貨幣基礎數據'
        }

        self.price_data = {}
        print("[FIXED OPTIMIZER] 修復版非價格技術指標優化器")
        print(f"[FIXED] 使用VectorBT內置Sharpe比率計算")
        print(f"[FIXED] 3%無風險利率: {self.risk_free_rate}")

    def fetch_real_stock_data(self) -> bool:
        """獲取真實股票數據"""
        try:
            print("[API] 獲取0700.HK真實價格數據...")
            params = {"symbol": "0700.hk", "duration": 365}

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and 'close' in data['data']:
                close_data = data['data']['close']
                self.price_data = {
                    'dates': list(close_data.keys()),
                    'close': list(close_data.values())
                }
                print(f"[API] 成功獲取 {len(self.price_data['close'])} 條真實記錄")
                return True
            else:
                print("[ERROR] API數據格式錯誤")
                return False

        except Exception as e:
            print(f"[ERROR] 獲取數據失敗: {e}")
            return False

    def generate_gov_data(self, source_code: str, length: int) -> List[float]:
        """生成模擬政府數據"""
        np.random.seed(42 + hash(source_code) % 1000)

        configs = {
            'HB': {'base': 2.5, 'vol': 0.3, 'trend': 0.001},
            'GD': {'base': 100, 'vol': 0.05, 'trend': 0.002},
            'RT': {'base': 120, 'vol': 0.08, 'trend': 0.003},
            'PT': {'base': 180, 'vol': 0.06, 'trend': 0.0015},
            'TR': {'base': 400, 'vol': 0.1, 'trend': 0.002},
            'TS': {'base': 30000, 'vol': 0.15, 'trend': -0.001},
            'CP': {'base': 105, 'vol': 0.03, 'trend': 0.001},
            'UE': {'base': 3.2, 'vol': 0.2, 'trend': -0.0005},
            'MB': {'base': 2000000, 'vol': 0.02, 'trend': 0.0008}
        }

        config = configs.get(source_code, {'base': 100, 'vol': 0.1, 'trend': 0.001})
        data = []
        current_value = config['base']

        for i in range(length):
            daily_change = np.random.normal(config['trend'], config['vol'])
            current_value *= (1 + daily_change)
            data.append(current_value)

        return data

    def calculate_technical_indicator(self, data: List[float], indicator_type: str, params: List[int]) -> List[float]:
        """計算技術指標"""
        data_array = np.array(data)

        if indicator_type == 'RSI':
            period = params[0]
            return self._calculate_rsi(data_array, period)
        elif indicator_type == 'KDJ':
            k_period, d_period = params[0], params[1]
            return self._calculate_kdj(data_array, k_period, d_period)
        elif indicator_type == 'MACD':
            fast, slow, signal = params[0], params[1], params[2]
            return self._calculate_macd(data_array, fast, slow, signal)
        elif indicator_type == 'CCI':
            period = params[0]
            return self._calculate_cci(data_array, period)
        else:
            return [0] * len(data)

    def _calculate_rsi(self, prices: np.ndarray, period: int) -> List[float]:
        """計算RSI"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = pd.Series(gains).rolling(period).mean()
        avg_losses = pd.Series(losses).rolling(period).mean()

        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        return rsi.fillna(50).tolist()

    def _calculate_kdj(self, prices: np.ndarray, k_period: int, d_period: int) -> List[float]:
        """計算KDJ"""
        df = pd.DataFrame({'close': prices})

        # 計算最高價和最低價
        high = df['close'].rolling(k_period).max()
        low = df['close'].rolling(k_period).min()

        # K值計算
        rsv = (df['close'] - low) / (high - low + 1e-10) * 100
        k = pd.Series(rsv).ewm(alpha=1/k_period).mean()
        d = k.ewm(alpha=1/d_period).mean()

        return d.fillna(50).tolist()

    def _calculate_macd(self, prices: np.ndarray, fast: int, slow: int, signal: int) -> List[float]:
        """計算MACD"""
        df = pd.DataFrame({'close': prices})

        exp1 = df['close'].ewm(span=fast).mean()
        exp2 = df['close'].ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()

        return signal_line.fillna(0).tolist()

    def _calculate_cci(self, prices: np.ndarray, period: int) -> List[float]:
        """計算CCI"""
        df = pd.DataFrame({'close': prices})

        # 簡化的CCI計算
        sma = df['close'].rolling(period).mean()
        cci = (df['close'] - sma) / (df['close'].rolling(period).std() + 1e-10)

        return cci.fillna(0).tolist()

    def calculate_sharpe_ratio_vectorbt(self, daily_returns: List[float]) -> float:
        """
        使用VectorBT內置方法計算Sharpe比率
        - 正確處理3%無風險利率
        - 避免CAGR錯誤
        - 使用機構級實現
        """
        if len(daily_returns) == 0:
            return 0.0

        returns_array = np.array(daily_returns)

        # 轉換為pandas Series以使用VectorBT
        returns_series = pd.Series(returns_array)

        try:
            # 使用VectorBT Returns Accessor計算Sharpe比率
            sharpe_ratio = returns_series.vbt.returns.sharpe_ratio(risk_free=self.risk_free_rate)
            return float(sharpe_ratio)
        except Exception as e:
            print(f"[WARNING] VectorBT計算失敗，回退到手動方法: {e}")
            # 回退到正確的手動計算
            if returns_array.std() == 0:
                return 0.0
            daily_risk_free = self.risk_free_rate / 365
            excess_returns = returns_array - daily_risk_free
            return excess_returns.mean() / returns_array.std() * np.sqrt(365)

    def backtest_strategy(self, data_source: str, indicator_type: str, params: List[int]) -> Dict[str, Any]:
        """回測單個策略（修復版本）"""
        try:
            if not self.price_data:
                return {'success': False, 'error': 'No price data'}

            # 生成政府數據
            gov_data = self.generate_gov_data(data_source, len(self.price_data['close']))

            # 計算技術指標
            indicator_values = self.calculate_technical_indicator(gov_data, indicator_type, params)

            # 生成交易信號（簡化版）
            prices = np.array(self.price_data['close'])
            signals = []

            for i, ind_val in enumerate(indicator_values):
                if i == 0:
                    signals.append(0)
                    continue

                # 基於指標值生成信號
                if indicator_type == 'RSI':
                    signal = 1 if ind_val < 30 else (-1 if ind_val > 70 else 0)
                elif indicator_type == 'KDJ':
                    signal = 1 if ind_val < 20 else (-1 if ind_val > 80 else 0)
                elif indicator_type == 'CCI':
                    signal = 1 if ind_val < -100 else (-1 if ind_val > 100 else 0)
                else:
                    signal = 0

                signals.append(signal)

            # 計算策略收益率
            price_changes = np.diff(prices) / prices[:-1]
            strategy_returns = [s * pc for s, pc in zip(signals[1:], price_changes)]

            if len(strategy_returns) == 0:
                return {'success': False, 'error': 'No returns calculated'}

            # 計算性能指標
            total_return = np.sum(strategy_returns)

            # 年化回報（使用算術平均，不是CAGR）
            daily_return_mean = np.mean(strategy_returns)
            annual_return = daily_return_mean * 365

            # 年化波動率
            volatility = np.std(strategy_returns) * np.sqrt(365)

            # 最大回撤
            cumulative = np.cumprod(1 + np.array(strategy_returns))
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0

            # 交易次數
            trade_count = np.sum(np.abs(np.diff(signals)) > 0)

            # **使用VectorBT內置方法計算Sharpe比率**
            sharpe_ratio = self.calculate_sharpe_ratio_vectorbt(strategy_returns)

            # 質量評分（使用更合理的標準）
            quality_score = (
                annual_return * 100 +  # 年化回報權重100
                min(sharpe_ratio * 20, 60) +  # Sharpe比率權重20，上限60
                (1 + max_drawdown) * 30 +  # 最大回撤權重30
                min(trade_count / 20, 10)  # 交易次數權重，上限10
            )
            quality_score = max(0, quality_score)

            return {
                'strategy_id': f"{data_source}_{indicator_type}_{params}",
                'data_source': data_source,
                'indicator_type': indicator_type,
                'params': params,
                'total_return': total_return,
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,  # 使用VectorBT修復的Sharpe比率
                'max_drawdown': max_drawdown,
                'volatility': volatility,
                'trade_count': trade_count,
                'quality_score': quality_score,
                'success': True,
                'calculation_method': 'FIXED - VectorBT built-in with 3% risk-free rate'
            }

        except Exception as e:
            print(f"[ERROR] 策略回測失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'strategy_id': f"{data_source}_{indicator_type}_{params}"
            }

    def run_fixed_optimization(self, max_combinations: int = 100) -> List[Dict[str, Any]]:
        """運行修復後的優化"""
        print("\n" + "="*80)
        print("運行修復後的Sharpe比率優化")
        print("="*80)
        print(f"[FIXED] 使用VectorBT內置Sharpe比率計算")
        print(f"[FIXED] 3%無風險利率正確應用")
        print(f"[FIXED] 避免CAGR錯誤")
        print("="*80)

        # 獲取數據
        if not self.fetch_real_stock_data():
            print("[ERROR] 無法獲取價格數據")
            return []

        # 生成策略組合（測試少量組合）
        data_sources = ['GD', 'HB', 'UE']
        indicator_types = ['RSI', 'KDJ', 'CCI']
        parameter_ranges = {
            'RSI': [[14], [21], [30]],
            'KDJ': [[9, 3], [10, 2], [12, 3]],
            'CCI': [[14], [20], [30]]
        }

        results = []
        combination_count = 0

        for data_source in data_sources:
            for indicator_type in indicator_types:
                for params in parameter_ranges.get(indicator_type, []):
                    combination_count += 1

                    print(f"[PROGRESS] 測試 {data_source}_{indicator_type}_{params} ({combination_count}/{max_combinations})")

                    result = self.backtest_strategy(data_source, indicator_type, params)

                    if result['success']:
                        results.append(result)

                        # 顯示結果
                        print(f"  ✓ Sharpe: {result['sharpe_ratio']:.4f}")
                        print(f"  ✓ 年化回報: {result['annual_return']*100:.2f}%")
                        print(f"  ✓ 最大回撤: {result['max_drawdown']*100:.2f}%")
                        print(f"  ✓ 計算方法: {result['calculation_method']}")

                        # 合理性檢查
                        if result['sharpe_ratio'] > 3:
                            print(f"  ⚠️  注意: Sharpe > 3 較高")
                        elif result['sharpe_ratio'] > 2:
                            print(f"  ✓ 優秀Sharpe比率")

                    if combination_count >= max_combinations:
                        break

                if combination_count >= max_combinations:
                    break

            if combination_count >= max_combinations:
                break

        # 按Sharpe比率排序
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

        return results

    def save_results(self, results: List[Dict[str, Any]]):
        """保存優化結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 生成摘要
        summary = {
            "total_strategies_tested": len(results),
            "successful_strategies": len([r for r in results if r['success']]),
            "success_rate": len([r for r in results if r['success']]) / len(results) * 100 if results else 0,
            "best_sharpe": results[0]['sharpe_ratio'] if results else 0,
            "best_strategy": results[0]['strategy_id'] if results else None,
            "risk_free_rate": self.risk_free_rate,
            "calculation_method": "FIXED - VectorBT built-in Sharpe with 3% risk-free rate",
            "fix_timestamp": datetime.now().isoformat(),
            "fix_description": "Replaced CAGR calculation with VectorBT built-in sharpe_ratio method"
        }

        # 完整結果
        complete_results = {
            "summary": summary,
            "top_strategies": results[:10],  # 保存前10個策略
            "all_results": results
        }

        # 保存到文件
        filename = f"vectorbt_fixed_sharpe_results_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(complete_results, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] 結果已保存到: {filename}")
        return filename

def main():
    """主函數"""
    print("修復Sharpe比率計算錯誤 - 使用VectorBT內置方法")

    optimizer = FixedNonPriceOptimizer()

    # 運行修復後的優化
    print("\n開始運行修復後的優化...")
    results = optimizer.run_fixed_optimization(max_combinations=27)

    if results:
        # 顯示最佳策略
        print("\n" + "="*80)
        print("修復後的TOP 5策略結果:")
        print("="*80)

        for i, strategy in enumerate(results[:5], 1):
            print(f"\n{i}. {strategy['strategy_id']}")
            print(f"   Sharpe Ratio: {strategy['sharpe_ratio']:.4f}")
            print(f"   年化回報: {strategy['annual_return']*100:.2f}%")
            print(f"   最大回撤: {strategy['max_drawdown']*100:.2f}%")
            print(f"   波動率: {strategy['volatility']*100:.2f}%")
            print(f"   交易次數: {strategy['trade_count']}")
            print(f"   計算方法: {strategy['calculation_method']}")

            # 檢查Sharpe比率合理性
            if strategy['sharpe_ratio'] > 3:
                print(f"   ⚠️  注意: Sharpe > 3 仍然較高")
            elif strategy['sharpe_ratio'] > 2:
                print(f"   ✓ 優秀的Sharpe比率")
            else:
                print(f"   ✓ 合理的Sharpe比率")

        # 保存結果
        filename = optimizer.save_results(results)

        print("\n" + "="*80)
        print("VectorBT修復完成！")
        print(f"測試了 {len(results)} 個策略組合")
        print(f"最佳Sharpe: {results[0]['sharpe_ratio']:.4f}")
        print(f"結果保存: {filename}")
        print("3%無風險利率已正確應用")
        print("="*80)

    else:
        print("[ERROR] 優化失敗，無法獲取結果")

if __name__ == "__main__":
    main()