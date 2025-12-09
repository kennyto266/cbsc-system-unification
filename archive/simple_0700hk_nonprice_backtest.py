#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡化版0700.HK非價格數據技術分析回測
使用真實股票數據進行四大策略回測分析
"""

import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
import sys
import os

def load_0700_data():
    """加載0700.HK真實數據"""
    print("[DATA] 正在加載0700.HK真實數據...")

    try:
        from relaxed_data_integration import DataIntegrationManager
        data_manager = DataIntegrationManager()

        # 獲取1年數據
        stock_data, gov_data = data_manager.prepare_backtest_data("0700.HK", 365)

        print(f"  [OK] 股票數據: {len(stock_data)} 條記錄")
        print(f"  [OK] 價格範圍: {stock_data['close'].min():.2f} - {stock_data['close'].max():.2f} HKD")
        print(f"  [OK] 時間範圍: {stock_data.index[0].date()} 至 {stock_data.index[-1].date()}")

        return stock_data

    except Exception as e:
        print(f"  [FAIL] 數據加載失敗: {str(e)}")
        return None

def run_strategy_backtests(stock_data):
    """執行四大策略回測"""
    print("\n" + "="*80)
    print("執行0700.HK四大策略技術分析回測")
    print("="*80)

    try:
        from strategy_backtest_implementations import StrategyBacktestImplementations

        strategy_impl = StrategyBacktestImplementations()
        results = []

        # 定義策略參數組合
        strategies = [
            {
                'name': 'RSI_14',
                'type': 'RSI',
                'params': {
                    'strategy': 'RSI',
                    'period': 14,
                    'oversold': 30,
                    'overbought': 70,
                    'condition_type': 'moderate'
                }
            },
            {
                'name': 'RSI_21',
                'type': 'RSI',
                'params': {
                    'strategy': 'RSI',
                    'period': 21,
                    'oversold': 25,
                    'overbought': 75,
                    'condition_type': 'moderate'
                }
            },
            {
                'name': 'MACD_12_26_9',
                'type': 'MACD',
                'params': {
                    'strategy': 'MACD',
                    'fast': 12,
                    'slow': 26,
                    'signal': 9,
                    'condition_type': 'standard'
                }
            },
            {
                'name': 'MACD_8_21_8',
                'type': 'MACD',
                'params': {
                    'strategy': 'MACD',
                    'fast': 8,
                    'slow': 21,
                    'signal': 8,
                    'condition_type': 'standard'
                }
            },
            {
                'name': 'KDJ_9_3',
                'type': 'KDJ',
                'params': {
                    'strategy': 'KDJ',
                    'k_period': 9,
                    'd_period': 3,
                    'condition_type': 'standard'
                }
            },
            {
                'name': 'KDJ_14_5',
                'type': 'KDJ',
                'params': {
                    'strategy': 'KDJ',
                    'k_period': 14,
                    'd_period': 5,
                    'condition_type': 'standard'
                }
            },
            {
                'name': 'BOLLINGER_20_2',
                'type': 'BOLLINGER_BANDS',
                'params': {
                    'strategy': 'BOLLINGER_BANDS',
                    'period': 20,
                    'std_dev': 2.0,
                    'condition_type': 'moderate'
                }
            },
            {
                'name': 'BOLLINGER_15_1.8',
                'type': 'BOLLINGER_BANDS',
                'params': {
                    'strategy': 'BOLLINGER_BANDS',
                    'period': 15,
                    'std_dev': 1.8,
                    'condition_type': 'moderate'
                }
            }
        ]

        print(f"\n[BACKTEST] 測試 {len(strategies)} 個策略組合...")

        successful_strategies = 0
        best_strategy = None
        max_sharpe = -999

        for i, strategy in enumerate(strategies, 1):
            try:
                print(f"\n[{i}/{len(strategies)}] 測試 {strategy['name']} ({strategy['type']})...")

                # 動態調用對應的回測方法
                if strategy['type'] == 'RSI':
                    result = strategy_impl.backtest_rsi_strategy(strategy['params'], stock_data)
                elif strategy['type'] == 'MACD':
                    result = strategy_impl.backtest_macd_strategy(strategy['params'], stock_data)
                elif strategy['type'] == 'KDJ':
                    result = strategy_impl.backtest_kdj_strategy(strategy['params'], stock_data)
                elif strategy['type'] == 'BOLLINGER_BANDS':
                    result = strategy_impl.backtest_bollinger_bands_strategy(strategy['params'], stock_data)

                if result.success:
                    successful_strategies += 1

                    # 記錄最佳策略
                    if result.sharpe_ratio > max_sharpe:
                        max_sharpe = result.sharpe_ratio
                        best_strategy = {
                            'name': strategy['name'],
                            'type': strategy['type'],
                            'parameters': strategy['params'],
                            'sharpe_ratio': result.sharpe_ratio,
                            'total_return': result.total_return,
                            'max_drawdown': result.max_drawdown,
                            'volatility': result.volatility,
                            'trade_frequency': result.trade_frequency,
                            'trade_count': result.trade_count
                        }

                    # 存儲結果
                    results.append({
                        'strategy_name': strategy['name'],
                        'strategy_type': strategy['type'],
                        'parameters': strategy['params'],
                        'success': True,
                        'sharpe_ratio': result.sharpe_ratio,
                        'total_return': result.total_return,
                        'max_drawdown': result.max_drawdown,
                        'volatility': result.volatility,
                        'trade_frequency': result.trade_frequency,
                        'trade_count': result.trade_count,
                        'annual_return': result.annual_return
                    })

                    print(f"  [OK] Sharpe: {result.sharpe_ratio:.3f}")
                    print(f"  [OK] Return: {result.total_return:.2%}")
                    print(f"  [OK] Max DD: {result.max_drawdown:.2%}")
                    print(f"  [OK] Trades: {result.trade_count}")

                else:
                    print(f"  [FAIL] 策略失敗: {result.error_message}")
                    results.append({
                        'strategy_name': strategy['name'],
                        'strategy_type': strategy['type'],
                        'parameters': strategy['params'],
                        'success': False,
                        'error': result.error_message
                    })

            except Exception as e:
                print(f"  [ERROR] 回測錯誤: {str(e)}")
                results.append({
                    'strategy_name': strategy['name'],
                    'strategy_type': strategy['type'],
                    'parameters': strategy['params'],
                    'success': False,
                    'error': str(e)
                })

        # 計算統計
        success_rate = successful_strategies / len(strategies)
        successful_results = [r for r in results if r['success']]

        if successful_results:
            sharpe_values = [r['sharpe_ratio'] for r in successful_results]
            return_values = [r['total_return'] for r in successful_results]
            drawdown_values = [r['max_drawdown'] for r in successful_results]

            avg_sharpe = np.mean(sharpe_values)
            avg_return = np.mean(return_values)
            avg_drawdown = np.mean(drawdown_values)

            print(f"\n[BACKTEST] 回測結果統計:")
            print(f"  [OK] 成功策略: {successful_strategies}/{len(strategies)} ({success_rate:.1%})")
            print(f"  [OK] 平均Sharpe: {avg_sharpe:.3f}")
            print(f"  [OK] 最高Sharpe: {max_sharpe:.3f}")
            print(f"  [OK] 平均回報: {avg_return:.2%}")
            print(f"  [OK] 平均回撤: {avg_drawdown:.2%}")

        return results, {
            'total_strategies': len(strategies),
            'successful_strategies': successful_strategies,
            'success_rate': success_rate,
            'best_strategy': best_strategy,
            'max_sharpe': max_sharpe
        }

    except Exception as e:
        print(f"  [FAIL] 回測執行錯誤: {str(e)}")
        return [], {}

def analyze_results(results, summary):
    """分析回測結果"""
    print("\n" + "="*80)
    print("0700.HK技術分析結果深度分析")
    print("="*80)

    try:
        successful_results = [r for r in results if r['success']]

        if not successful_results:
            print("[WARN] 沒有成功的策略結果可供分析")
            return {}

        # 1. 策略類型性能比較
        print("\n[ANALYSIS] 1. 策略類型性能比較:")

        strategy_performance = {}
        for result in successful_results:
            strategy_type = result['strategy_type']
            if strategy_type not in strategy_performance:
                strategy_performance[strategy_type] = []
            strategy_performance[strategy_type].append(result['sharpe_ratio'])

        for strategy_type, sharpes in strategy_performance.items():
            avg_sharpe = np.mean(sharpes)
            max_sharpe = np.max(sharpes)
            count = len(sharpes)
            print(f"  {strategy_type:15}: 平均={avg_sharpe:7.3f}, 最高={max_sharpe:7.3f}, 數量={count}")

        # 2. 風險回報分析
        print(f"\n[ANALYSIS] 2. 風險回報分析:")

        return_values = [r['total_return'] for r in successful_results]
        drawdown_values = [r['max_drawdown'] for r in successful_results]
        sharpe_values = [r['sharpe_ratio'] for r in successful_results]

        # 風險調整回報分析
        risk_adjusted_returns = []
        for result in successful_results:
            if result['max_drawdown'] < 0:
                risk_adj_return = result['total_return'] / abs(result['max_drawdown'])
                risk_adjusted_returns.append(risk_adj_return)

        if risk_adjusted_returns:
            print(f"  平均風險調整回報: {np.mean(risk_adjusted_returns):.3f}")
            print(f"  最高風險調整回報: {np.max(risk_adjusted_returns):.3f}")

        # 3. 性能分布分析
        print(f"\n[ANALYSIS] 3. 性能分布分析:")
        print(f"  Sharpe Ratio - 均值: {np.mean(sharpe_values):.3f}, 標準差: {np.std(sharpe_values):.3f}")
        print(f"  Total Return - 均值: {np.mean(return_values):.2%}, 標準差: {np.std(return_values):.2%}")
        print(f"  Max Drawdown - 均值: {np.mean(drawdown_values):.2%}, 最差: {np.min(drawdown_values):.2%}")

        # 4. 最佳策略詳細分析
        if summary.get('best_strategy'):
            best = summary['best_strategy']
            print(f"\n[ANALYSIS] 4. 最佳策略詳細分析:")
            print(f"  策略名稱: {best['name']}")
            print(f"  策略類型: {best['type']}")
            print(f"  Sharpe比率: {best['sharpe_ratio']:.3f}")
            print(f"  總回報率: {best['total_return']:.2%}")
            print(f"  最大回撤: {best['max_drawdown']:.2%}")
            print(f"  波動率: {best['volatility']:.2%}")
            print(f"  交易次數: {best['trade_count']}")
            print(f"  交易頻率: {best['trade_frequency']:.2%}")

        # 5. 投資建議
        print(f"\n[ANALYSIS] 5. 投資建議:")

        if summary['success_rate'] > 0.7:
            print("  [INFO] 策略成功率較高，可考慮實際部署")
        elif summary['success_rate'] > 0.5:
            print("  [INFO] 策略成功率中等，建議進一步優化")
        else:
            print("  [WARN] 策略成功率較低，建議重新調整參數")

        if summary.get('max_sharpe', 0) > 1.5:
            print("  [INFO] 發現高Sharpe策略，具有實際應用價值")
        elif summary.get('max_sharpe', 0) > 1.0:
            print("  [INFO] 策略表現良好，可繼續優化")
        else:
            print("  [WARN] 策略表現一般，建議調整或尋找其他機會")

        return {
            'strategy_performance': strategy_performance,
            'risk_adjusted_performance': {
                'avg': np.mean(risk_adjusted_returns) if risk_adjusted_returns else 0,
                'max': np.max(risk_adjusted_returns) if risk_adjusted_returns else 0
            },
            'performance_stats': {
                'sharpe_mean': np.mean(sharpe_values),
                'sharpe_std': np.std(sharpe_values),
                'return_mean': np.mean(return_values),
                'return_std': np.std(return_values),
                'drawdown_mean': np.mean(drawdown_values),
                'drawdown_worst': np.min(drawdown_values)
            }
        }

    except Exception as e:
        print(f"  [FAIL] 分析錯誤: {str(e)}")
        return {}

def generate_report(stock_data, results, summary, analysis):
    """生成分析報告"""
    print("\n" + "="*80)
    print("生成0700.HK技術分析報告")
    print("="*80)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 報告數據
    report = {
        'stock_info': {
            'symbol': '0700.HK',
            'company': 'Tencent Holdings Limited',
            'data_period': f"{stock_data.index[0].date()} 至 {stock_data.index[-1].date()}",
            'total_days': len(stock_data),
            'price_range': {
                'min': float(stock_data['close'].min()),
                'max': float(stock_data['close'].max()),
                'current': float(stock_data['close'].iloc[-1])
            }
        },
        'backtest_summary': summary,
        'detailed_results': results,
        'analysis': analysis,
        'generated_at': datetime.now().isoformat()
    }

    # 保存報告
    report_file = f"0700_hk_technical_analysis_report_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[OK] 分析報告已保存: {report_file}")

    # 生成摘要
    print(f"\n[REPORT] 0700.HK技術分析摘要:")
    print(f"  股票代碼: 0700.HK (騰訊控股)")
    print(f"  數據期間: {stock_data.index[0].date()} 至 {stock_data.index[-1].date()}")
    print(f"  價格範圍: {stock_data['close'].min():.2f} - {stock_data['close'].max():.2f} HKD")
    print(f"  測試策略: {summary.get('total_strategies', 0)} 個")
    print(f"  成功策略: {summary.get('successful_strategies', 0)} 個")
    print(f"  成功率: {summary.get('success_rate', 0):.1%}")

    if summary.get('best_strategy'):
        best = summary['best_strategy']
        print(f"  最佳策略: {best['name']}")
        print(f"  最高Sharpe: {best['sharpe_ratio']:.3f}")
        print(f"  最高回報: {best['total_return']:.2%}")

    return report_file, report

def main():
    """主函數"""
    print("=" * 80)
    print("0700.HK 騰訊控股 - 非價格數據技術分析系統")
    print("=" * 80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    start_time = time.time()

    try:
        # 1. 加載數據
        stock_data = load_0700_data()

        if stock_data is None or stock_data.empty:
            print("[ERROR] 無法加載股票數據")
            return False

        # 2. 執行策略回測
        results, summary = run_strategy_backtests(stock_data)

        if not results:
            print("[ERROR] 回測執行失敗")
            return False

        # 3. 分析結果
        analysis = analyze_results(results, summary)

        # 4. 生成報告
        report_file, report = generate_report(stock_data, results, summary, analysis)

        # 5. 總結
        total_time = time.time() - start_time

        print("\n" + "="*80)
        print("0700.HK 技術分析系統執行完成")
        print("="*80)

        print(f"\n[SUMMARY] 執行總結:")
        print(f"  執行時間: {total_time:.2f}秒")
        print(f"  股票數據: {len(stock_data)} 天")
        print(f"  測試策略: {summary.get('total_strategies', 0)} 個")
        print(f"  成功策略: {summary.get('successful_strategies', 0)} 個")
        print(f"  成功率: {summary.get('success_rate', 0):.1%}")
        print(f"  最高Sharpe: {summary.get('max_sharpe', 0):.3f}")

        print(f"\n[SUMMARY] 分析報告: {report_file}")

        # 判斷成功
        success = (
            summary.get('success_rate', 0) > 0 and
            summary.get('successful_strategies', 0) > 0 and
            len(results) > 0
        )

        if success:
            print(f"\n[SUCCESS] 0700.HK技術分析成功完成！")
            if summary.get('max_sharpe', 0) > 1.0:
                print(f"[INFO] 發現具有投資價值的策略組合")
            else:
                print(f"[INFO] 策略分析完成，建議進一步優化參數")
        else:
            print(f"\n[WARNING] 技術分析結果不理想")

        return success

    except Exception as e:
        print(f"\n[FATAL] 系統錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)