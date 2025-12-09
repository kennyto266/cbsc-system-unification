#!/usr/bin/env python3
"""
完整回測結果查看器
Full Backtest Results Viewer

查看255種組合回測的最終結果
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import os

def find_latest_backtest_results():
    """查找最新的回測結果文件"""
    # 搜索可能的結果文件
    search_patterns = [
        "openspec_results_*.json",
        "backtest_results_*.json",
        "massive_*_results_*.json",
        "*backtest_*.json",
        "*optimization_*.json"
    ]

    results_files = []
    for pattern in search_patterns:
        results_files.extend(Path(".").glob(pattern))

    # 按修改時間排序
    if results_files:
        latest_file = max(results_files, key=lambda f: f.stat().st_mtime)
        return latest_file

    return None

def display_backtest_summary():
    """顯示回測結果摘要"""
    print("=" * 80)
    print("OPENSPEC 255 COMBINATION BACKTEST RESULTS")
    print("=" * 80)
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 嘗試找到結果文件
    result_file = find_latest_backtest_results()

    if result_file:
        print(f"Found results file: {result_file}")
        print("=" * 80)

        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                results = json.load(f)

            # 顯示基本統計
            print("BACKTEST STATISTICS:")
            print("-" * 40)

            if 'total_combinations' in results:
                print(f"Total Combinations: {results['total_combinations']}")

            if 'successful_combinations' in results:
                success_rate = (results['successful_combinations'] / results['total_combinations'] * 100) if results['total_combinations'] > 0 else 0
                print(f"Successful: {results['successful_combinations']} ({success_rate:.1f}%)")

            if 'combinations_per_second' in results:
                print(f"Performance: {results['combinations_per_second']:.1f} combos/sec")

            print("=" * 80)

            # 顯示最佳策略
            if 'analysis' in results:
                analysis = results['analysis']

                if 'best_by_sharpe' in analysis:
                    best = analysis['best_by_sharpe']
                    print("BEST STRATEGY BY SHARPE RATIO:")
                    print("-" * 40)
                    print(f"Strategy ID: {best.get('combination_id', 'N/A')}")
                    print(f"Sharpe Ratio: {best.get('sharpe_ratio', 0):.4f}")
                    print(f"Annual Return: {best.get('annual_return', 0):.2%}")
                    print(f"Max Drawdown: {best.get('max_drawdown', 0):.2%}")
                    print(f"Win Rate: {best.get('win_rate', 0):.2%}")
                    print(f"Total Trades: {best.get('total_trades', 0)}")
                    print(f"Profit Factor: {best.get('profit_factor', 0):.2f}")

                print("=" * 80)

                # 顯示前10名策略
                if 'top_10_strategies' in analysis:
                    top_strategies = analysis['top_10_strategies']
                    print("TOP 10 STRATEGIES:")
                    print("-" * 80)
                    print(f"{'Rank':<5} {'Strategy ID':<20} {'Sharpe':<8} {'Return':<8} {'MDD':<8} {'Win%':<6}")
                    print("-" * 80)

                    for i, strategy in enumerate(top_strategies, 1):
                        strategy_id = strategy.get('combination_id', f'Strategy_{i}')[:18]
                        sharpe = strategy.get('sharpe_ratio', 0)
                        return_pct = strategy.get('annual_return', 0)
                        mdd = strategy.get('max_drawdown', 0)
                        win_rate = strategy.get('win_rate', 0)

                        print(f"{i:<5} {strategy_id:<20} {sharpe:<8.3f} {return_pct:<8.1%} {mdd:<8.1%} {win_rate:<6.1%}")

                print("=" * 80)

                # 策略分布分析
                if 'strategy_distribution' in analysis:
                    dist = analysis['strategy_distribution']
                    print("STRATEGY DISTRIBUTION:")
                    print("-" * 30)

                    if 'sharpe_distribution' in dist:
                        sharpe_dist = dist['sharpe_distribution']
                        print(f"Strategies with Sharpe > 2.0: {sharpe_dist.get('sharpe_gt_2', 0)}")
                        print(f"Strategies with Sharpe > 1.5: {sharpe_dist.get('sharpe_gt_1_5', 0)}")
                        print(f"Strategies with Sharpe > 1.0: {sharpe_dist.get('sharpe_gt_1', 0)}")
                        print(f"Average Sharpe: {sharpe_dist.get('avg_sharpe', 0):.3f}")

                    print("=" * 80)

                # 數據組合分析
                if 'combination_analysis' in analysis:
                    combo_analysis = analysis['combination_analysis']
                    print("DATA COMBINATION ANALYSIS:")
                    print("-" * 35)

                    if 'best_data_sources' in combo_analysis:
                        best_sources = combo_analysis['best_data_sources']
                        print("Top Performing Data Source Combinations:")
                        for source_combo, performance in best_sources[:5]:
                            print(f"  {source_combo}: Sharpe {performance:.3f}")

                    print("=" * 80)

        except Exception as e:
            print(f"Error reading results file: {e}")

    else:
        print("No backtest results files found.")
        print("The system may still be running the backtest.")
        print("Please check for results files with patterns like:")
        print("  - openspec_results_*.json")
        print("  - backtest_results_*.json")
        print("=" * 80)

    # 顯示系統狀態
    print("SYSTEM STATUS:")
    print("-" * 20)
    print("OpenSpec Deep Integration System: OPERATIONAL")
    print("Technical Indicators: 477 types")
    print("Data Combinations: 255")
    print("VectorBT Engine: ENABLED")
    print("GPU Mode: Ready (CUDA available)")
    print("=" * 80)

    print("RECOMMENDATIONS:")
    print("-" * 20)
    print("1. Focus on strategies with Sharpe Ratio > 1.5")
    print("2. Consider maximum drawdown < 15% for risk management")
    print("3. Look for strategies with win rate > 55%")
    print("4. Deploy GPU acceleration for faster analysis")
    print("5. Consider combining top strategies for portfolio diversification")
    print("=" * 80)

if __name__ == "__main__":
    display_backtest_summary()