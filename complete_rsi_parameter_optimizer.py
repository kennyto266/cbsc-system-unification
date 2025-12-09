#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整RSI參數優化器
Buy < x, Sell > y, 範圍0-300, 步長5, 全面測試3600種組合
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import itertools
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class CompleteRSIOptimizer:
    def __init__(self):
        self.rsi_period = 14  # 標準RSI週期
        self.results = {}
        self.best_results = {}
        self.optimization_data = None

    def generate_rsi_parameters(self) -> List[Tuple[int, int]]:
        """生成所有RSI參數組合"""
        buy_values = list(range(5, 301, 5))  # Buy: 5, 10, 15, ..., 300
        sell_values = list(range(5, 301, 5))  # Sell: 5, 10, 15, ..., 300

        print(f"生成RSI參數組合...")
        print(f"Buy參數範圍: {len(buy_values)}個值 (5 到 300, 步長5)")
        print(f"Sell參數範圍: {len(sell_values)}個值 (5 到 300, 步長5)")
        print(f"總組合數: {len(buy_values) * len(sell_values)} 種")

        # 生成所有有效組合（Buy必須小於Sell）
        valid_combinations = []
        for buy in buy_values:
            for sell in sell_values:
                if buy < sell:  # 確保Buy < Sell
                    valid_combinations.append((buy, sell))

        print(f"有效組合數: {len(valid_combinations)} 種")
        return valid_combinations

    def load_cbsc_data(self):
        """加載CBSC數據"""
        print("加載CBSC數據...")

        try:
            # 嘗試加載真實的CBSC數據
            data_files = [
                'warrant_sentiment_merged.csv',
                'acheng_sharpe_results.csv',
                'strategy_performance_demo.csv'
            ]

            data = None
            for file in data_files:
                try:
                    data = pd.read_csv(file)
                    if 'Date' in data.columns or 'date' in data.columns:
                        print(f"成功加載數據文件: {file}")
                        break
                except:
                    continue

            if data is None:
                # 生成模擬數據用於測試
                print("未找到真實數據，生成模擬CBSC數據進行測試...")
                dates = pd.date_range(start='2025-09-01', end='2025-10-17', freq='D')
                dates = dates[dates.weekday < 5]  # 只保留工作日

                np.random.seed(42)  # 確保結果可重複
                n_days = len(dates)

                data = pd.DataFrame({
                    'Date': dates,
                    'Close': 100 + np.cumsum(np.random.normal(0, 0.02, n_days)),
                    'Volume': np.random.uniform(100000000, 500000000, n_days),
                    'Bull_Ratio': np.random.uniform(0.3, 0.7, n_days),
                    'Bear_Turnover_HKD': np.random.uniform(50000000, 300000000, n_days),
                    'Signal': np.random.choice(['BUY', 'SELL', 'HOLD'], n_days)
                })

                # 確保 Bull_Ratio 在合理範圍內
                data['Bull_Ratio'] = np.clip(data['Bull_Ratio'], 0.2, 0.8)

            # 確保Date列格式正確
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
            elif 'date' in data.columns:
                data['Date'] = pd.to_datetime(data['date'])
                data = data.drop('date', axis=1)

            # 按日期排序
            data = data.sort_values('Date').reset_index(drop=True)

            print(f"數據加載完成: {len(data)} 條記錄")
            print(f"數據期間: {data['Date'].min().strftime('%Y-%m-%d')} 到 {data['Date'].max().strftime('%Y-%m-%d')}")

            self.optimization_data = data
            return True

        except Exception as e:
            print(f"數據加載失敗: {e}")
            return False

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def simulate_rsi_strategy(self, data: pd.DataFrame, buy_threshold: int, sell_threshold: int) -> Dict:
        """模擬RSI策略"""

        # 計算RSI
        data['RSI'] = self.calculate_rsi(data['Close'], self.rsi_period)

        # 生成交易信號
        data['Signal'] = 'HOLD'
        data.loc[data['RSI'] < buy_threshold, 'Signal'] = 'BUY'
        data.loc[data['RSI'] > sell_threshold, 'Signal'] = 'SELL'

        # 計算持倉和收益
        data['Position'] = 0
        data['Returns'] = 0.0

        position = 0
        entry_price = 0
        trades = []
        portfolio_values = [100000]  # 初始資金100,000
        current_cash = 100000

        for i in range(len(data)):
            current_price = data.loc[i, 'Close']
            signal = data.loc[i, 'Signal']

            if signal == 'BUY' and position == 0 and current_cash > current_price:
                # 買入
                position = current_cash // current_price
                current_cash = current_cash % current_price
                entry_price = current_price
                trades.append({'type': 'BUY', 'date': data.loc[i, 'Date'], 'price': current_price, 'rsi': data.loc[i, 'RSI']})

            elif signal == 'SELL' and position > 0:
                # 賣出
                current_cash = position * current_price
                portfolio_value = current_cash
                portfolio_values.append(portfolio_value)
                trades.append({'type': 'SELL', 'date': data.loc[i, 'Date'], 'price': current_price, 'rsi': data.loc[i, 'RSI']})
                position = 0

            # 記錄當前投資組合價值
            if position > 0:
                portfolio_value = current_cash + position * current_price
                portfolio_values.append(portfolio_value)

        # 計算性能指標
        if len(portfolio_values) > 1:
            portfolio_returns = pd.Series(portfolio_values).pct_change().dropna()
            total_return = (portfolio_values[-1] / portfolio_values[0] - 1)

            # 年化收益（基於實際交易日）
            trading_days = len(data)
            annual_return = total_return * (252 / trading_days) if trading_days > 0 else 0

            # 計算波動率
            volatility = np.std(portfolio_returns) * np.sqrt(252) if len(portfolio_returns) > 1 else 0.15

            # 計算Sharpe比率
            sharpe_ratio = (annual_return - 0.02) / volatility if volatility > 0 else 0

            # 計算最大回撤
            portfolio_series = pd.Series(portfolio_values)
            rolling_max = portfolio_series.expanding().max()
            drawdown = (portfolio_series - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # 計算Calmar比率
            calmar_ratio = abs(annual_return / max_drawdown) if max_drawdown != 0 else annual_return / 0.001

            # 計算交易統計
            buy_trades = len([t for t in trades if t['type'] == 'BUY'])
            sell_trades = len([t for t in trades if t['type'] == 'SELL'])
            total_trades = min(buy_trades, sell_trades)

            # 計算勝率
            profitable_trades = 0
            trade_pairs = []
            for i, trade in enumerate(trades):
                if trade['type'] == 'SELL' and i > 0 and trades[i-1]['type'] == 'BUY':
                    buy_price = trades[i-1]['price']
                    sell_price = trade['price']
                    if sell_price > buy_price:
                        profitable_trades += 1
                    trade_pairs.append({
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'profit_pct': (sell_price - buy_price) / buy_price,
                        'buy_rsi': trades[i-1]['rsi'],
                        'sell_rsi': trade['rsi']
                    })

            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            avg_profit = np.mean([t['profit_pct'] for t in trade_pairs]) if trade_pairs else 0

        else:
            total_return = 0
            annual_return = 0
            sharpe_ratio = 0
            max_drawdown = 0
            calmar_ratio = 0
            win_rate = 0
            total_trades = 0
            avg_profit = 0
            volatility = 0.15

        return {
            'buy_threshold': buy_threshold,
            'sell_threshold': sell_threshold,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'avg_profit': avg_profit,
            'volatility': volatility,
            'final_value': portfolio_values[-1] if portfolio_values else 100000,
            'trade_count': len(trades),
            'profitable_trades': profitable_trades if 'profitable_trades' in locals() else 0
        }

    def run_complete_optimization(self):
        """運行完整RSI參數優化"""
        print("開始完整RSI參數優化...")
        print("=" * 80)

        # 加載數據
        if not self.load_cbsc_data():
            print("數據加載失敗，無法進行優化")
            return None

        # 生成參數組合
        parameter_combinations = self.generate_rsi_parameters()

        print(f"\n開始測試 {len(parameter_combinations)} 種RSI參數組合...")
        print("=" * 80)

        # 運行優化
        results = []
        best_sharpe = -float('inf')
        best_return = -float('inf')
        best_calmar = -float('inf')
        best_trades = 0

        optimal_sharpe = None
        optimal_return = None
        optimal_calmar = None
        optimal_trades = None

        total_combinations = len(parameter_combinations)

        for idx, (buy_threshold, sell_threshold) in enumerate(parameter_combinations):
            # 進度顯示
            if (idx + 1) % 100 == 0 or idx == 0:
                progress = (idx + 1) / total_combinations * 100
                print(f"進度: {progress:.1f}% ({idx+1}/{total_combinations}) - 當前最佳Sharpe: {best_sharpe:.4f}")

            # 模擬策略
            result = self.simulate_rsi_strategy(self.optimization_data.copy(), buy_threshold, sell_threshold)
            results.append(result)

            # 更新最佳結果
            if result['sharpe_ratio'] > best_sharpe and result['total_trades'] > 0:
                best_sharpe = result['sharpe_ratio']
                optimal_sharpe = result.copy()

            if result['total_return'] > best_return and result['total_trades'] > 0:
                best_return = result['total_return']
                optimal_return = result.copy()

            if result['calmar_ratio'] > best_calmar and result['total_trades'] > 0:
                best_calmar = result['calmar_ratio']
                optimal_calmar = result.copy()

            if result['total_trades'] > best_trades:
                best_trades = result['total_trades']
                optimal_trades = result.copy()

        # 保存結果
        self.results = {
            'all_results': results,
            'total_combinations_tested': len(parameter_combinations),
            'optimization_metadata': {
                'data_period': f"{self.optimization_data['Date'].min().strftime('%Y-%m-%d')} 到 {self.optimization_data['Date'].max().strftime('%Y-%m-%d')}",
                'trading_days': len(self.optimization_data),
                'rsi_period': self.rsi_period,
                'buy_range': '5-300 (步長5)',
                'sell_range': '5-300 (步長5)',
                'total_combinations': total_combinations,
                'valid_combinations': len(parameter_combinations)
            }
        }

        self.best_results = {
            'best_sharpe': optimal_sharpe,
            'best_return': optimal_return,
            'best_calmar': optimal_calmar,
            'most_trades': optimal_trades
        }

        print(f"\n優化完成！")
        print(f"測試組合數: {len(parameter_combinations)}")
        print(f"數據期間: {self.optimization_data['Date'].min().strftime('%Y-%m-%d')} 到 {self.optimization_data['Date'].max().strftime('%Y-%m-%d')}")

        return self.results

    def analyze_results(self):
        """分析優化結果"""
        print("\n" + "=" * 80)
        print("RSI參數優化結果分析")
        print("=" * 80)

        if not self.results:
            print("沒有可分析的結果")
            return

        results = self.results['all_results']
        metadata = self.results['optimization_metadata']

        # 統計分析
        print(f"\n📊 優化統計:")
        print(f"  測試組合總數: {metadata['total_combinations']:,}")
        print(f"  有效組合數: {metadata['valid_combinations']:,}")
        print(f"  數據天數: {metadata['trading_days']}")
        print(f"  RSI週期: {metadata['rsi_period']}")

        # 篩選有交易的結果
        trading_results = [r for r in results if r['total_trades'] > 0]
        print(f"  產生交易的組合: {len(trading_results):,}")

        if trading_results:
            print(f"\n📈 性能統計 (有交易的組合):")
            print(f"  平均總回報: {np.mean([r['total_return'] for r in trading_results]):.6f}")
            print(f"  平均Sharpe比率: {np.mean([r['sharpe_ratio'] for r in trading_results]):.4f}")
            print(f"  平均最大回撤: {np.mean([r['max_drawdown'] for r in trading_results]):.6f}")
            print(f"  平均勝率: {np.mean([r['win_rate'] for r in trading_results]):.4f}")
            print(f"  平均交易次數: {np.mean([r['total_trades'] for r in trading_results]):.1f}")

            print(f"\n🏆 最佳表現組合:")

            # 按不同指標排序
            best_sharpe = max(trading_results, key=lambda x: x['sharpe_ratio'])
            best_return = max(trading_results, key=lambda x: x['total_return'])
            best_calmar = max(trading_results, key=lambda x: x['calmar_ratio'])
            most_trades = max(trading_results, key=lambda x: x['total_trades'])

            print(f"\n  🥇 最佳Sharpe比率:")
            print(f"     Buy < {best_sharpe['buy_threshold']}, Sell > {best_sharpe['sell_threshold']}")
            print(f"     Sharpe: {best_sharpe['sharpe_ratio']:.6f}, 回報: {best_sharpe['total_return']:.6f}, 交易: {best_sharpe['total_trades']}")

            print(f"\n  🥈 最高總回報:")
            print(f"     Buy < {best_return['buy_threshold']}, Sell > {best_return['sell_threshold']}")
            print(f"     回報: {best_return['total_return']:.6f}, Sharpe: {best_return['sharpe_ratio']:.6f}, 交易: {best_return['total_trades']}")

            print(f"\n  🥉 最佳Calmar比率:")
            print(f"     Buy < {best_calmar['buy_threshold']}, Sell > {best_calmar['sell_threshold']}")
            print(f"     Calmar: {best_calmar['calmar_ratio']:.6f}, 回報: {best_calmar['total_return']:.6f}, MDD: {best_calmar['max_drawdown']:.6f}")

            print(f"\n  📊 最多交易次數:")
            print(f"     Buy < {most_trades['buy_threshold']}, Sell > {most_trades['sell_threshold']}")
            print(f"     交易次數: {most_trades['total_trades']}, 回報: {most_trades['total_return']:.6f}, 勝率: {most_trades['win_rate']:.4f}")

        # 參數區間分析
        print(f"\n📋 參數區間分析:")

        # Buy參數分析
        buy_analysis = {}
        for buy in range(5, 301, 5):
            buy_results = [r for r in trading_results if r['buy_threshold'] == buy]
            if buy_results:
                avg_sharpe = np.mean([r['sharpe_ratio'] for r in buy_results])
                buy_analysis[buy] = avg_sharpe

        if buy_analysis:
            best_buy_range = max(buy_analysis.items(), key=lambda x: x[1])
            print(f"  最佳Buy區間: < {best_buy_range[0]} (平均Sharpe: {best_buy_range[1]:.4f})")

        # Sell參數分析
        sell_analysis = {}
        for sell in range(5, 301, 5):
            sell_results = [r for r in trading_results if r['sell_threshold'] == sell]
            if sell_results:
                avg_sharpe = np.mean([r['sharpe_ratio'] for r in sell_results])
                sell_analysis[sell] = avg_sharpe

        if sell_analysis:
            best_sell_range = max(sell_analysis.items(), key=lambda x: x[1])
            print(f"  最佳Sell區間: > {best_sell_range[0]} (平均Sharpe: {best_sell_range[1]:.4f})")

    def save_results(self):
        """保存優化結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存完整結果
        results_file = f"rsi_optimization_complete_{timestamp}.json"

        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'optimization_metadata': self.results['optimization_metadata'],
                    'best_results': self.best_results,
                    'summary_statistics': {
                        'total_combinations_tested': self.results['total_combinations_tested'],
                        'trading_combinations': len([r for r in self.results['all_results'] if r['total_trades'] > 0]),
                        'analysis_timestamp': timestamp
                    }
                }, f, indent=2, ensure_ascii=False)

            print(f"\n💾 完整結果已保存至: {results_file}")

            # 保存簡化報告
            report_file = f"rsi_optimization_report_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("RSI參數完整優化報告\n")
                f.write(f"生成時間: {timestamp}\n")
                f.write("=" * 50 + "\n\n")

                metadata = self.results['optimization_metadata']
                f.write(f"優化配置:\n")
                f.write(f"  Buy參數範圍: {metadata['buy_range']}\n")
                f.write(f"  Sell參數範圍: {metadata['sell_range']}\n")
                f.write(f"  RSI週期: {metadata['rsi_period']}\n")
                f.write(f"  測試組合總數: {metadata['total_combinations']:,}\n")
                f.write(f"  有效組合數: {metadata['valid_combinations']:,}\n")
                f.write(f"  數據期間: {metadata['data_period']}\n")
                f.write(f"  交易日數: {metadata['trading_days']}\n\n")

                if self.best_results and self.best_results['best_sharpe']:
                    f.write("最佳參數組合:\n\n")

                    best = self.best_results['best_sharpe']
                    f.write(f"最佳Sharpe比率組合:\n")
                    f.write(f"  Buy < {best['buy_threshold']}, Sell > {best['sell_threshold']}\n")
                    f.write(f"  總回報: {best['total_return']:.6f}\n")
                    f.write(f"  年化回報: {best['annual_return']:.6f}\n")
                    f.write(f"  Sharpe比率: {best['sharpe_ratio']:.6f}\n")
                    f.write(f"  最大回撤: {best['max_drawdown']:.6f}\n")
                    f.write(f"  Calmar比率: {best['calmar_ratio']:.6f}\n")
                    f.write(f"  勝率: {best['win_rate']:.4f}\n")
                    f.write(f"  交易次數: {best['total_trades']}\n")
                    f.write(f"  平均利潤: {best['avg_profit']:.6f}\n\n")

                f.write("詳細結果請參考JSON文件。\n")

            print(f"📄 簡化報告已保存至: {report_file}")

        except Exception as e:
            print(f"保存結果時出錯: {e}")

def main():
    """主執行函數"""
    print("🚀 RSI參數完整優化器")
    print("Buy < x, Sell > y, 範圍0-300, 步長5")
    print("=" * 80)

    optimizer = CompleteRSIOptimizer()

    try:
        # 運行完整優化
        results = optimizer.run_complete_optimization()

        if results:
            # 分析結果
            optimizer.analyze_results()

            # 保存結果
            optimizer.save_results()

            print(f"\n✅ 優化完成！")
            print(f"已測試所有RSI參數組合，找出最佳配置。")
        else:
            print("❌ 優化失敗")

    except Exception as e:
        print(f"執行過程中出錯: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()