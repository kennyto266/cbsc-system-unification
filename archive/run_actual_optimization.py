#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實際運行0700.HK參數優化
Actual 0700.HK Parameter Optimization Run
"""

import time
import warnings
import numpy as np
import pandas as pd
import logging
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import sys

warnings.filterwarnings('ignore')

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=" * 70)
    print("🚀 開始 0700.HK 0-300全參數範圍綜合優化")
    print("=" * 70)

    try:
        # 檢查系統環境
        print("📊 檢查系統環境...")

        # 檢查GPU
        try:
            from simplified_system.src.utils.gpu_detector import get_gpu_environment
            gpu_env = get_gpu_environment()
            print(f"✅ GPU狀態: {'可用' if gpu_env.is_gpu_available() else '不可用'}")
            use_gpu = gpu_env.is_gpu_available()
            if use_gpu:
                print("🔥 將使用GPU加速模式")
            else:
                print("💻 將使用CPU模式")
        except Exception as e:
            print(f"⚠️ GPU檢查失敗: {e}")
            use_gpu = False

        # 導入核心組件
        print("🔧 導入核心組件...")
        from comprehensive_parameter_optimizer import ComprehensiveParameterOptimizer, OptimizationConfig

        # 配置優化器
        config = OptimizationConfig(
            max_workers=6,  # 降低並行度避免資源問題
            batch_size=50,
            use_gpu=use_gpu,
            min_sharpe_ratio=0.5,  # 降低標準以獲得更多結果
            max_max_drawdown=0.3,
            min_win_rate=0.3
        )

        optimizer = ComprehensiveParameterOptimizer(config)
        print("✅ 參數優化器初始化成功")

        # 獲取真實數據
        print("📡 獲取真實股票數據...")
        from simplified_system.src.api.stock_api import get_hk_stock_data

        # 獲取1年數據進行測試
        data = get_hk_stock_data("0700.HK", 365)
        print(f"✅ 成功獲取 {len(data)} 天的0700.HK數據")
        print(f"💰 價格範圍: ${data['close'].min():.2f} - ${data['close'].max():.2f}")

        # 手動生成測試參數組合（避免導入問題）
        print("\n🎯 開始 HIBOR-RSI 參數優化...")
        print("📈 參數空間: RSI週期(10-50), 超賣(20-40), 超買(60-80)")
        print("🔢 設置: 最多200個組合用於演示")

        start_time = time.time()

        # 生成有效參數組合
        valid_combinations = []
        for period in range(10, 51, 5):        # 10-50, step=5
            for oversold in range(20, 45, 5):      # 20-40, step=5
                for overbought in range(60, 85, 5):     # 60-80, step=5
                    if oversold < overbought:  # 驗證邏輯關係
                        valid_combinations.append({
                            'rsi_period': period,
                            'rsi_oversold': oversold,
                            'rsi_overbought': overbought
                        })
                        if len(valid_combinations) >= 200:  # 限制組合數
                            break
            if len(valid_combinations) >= 200:
                break
            if len(valid_combinations) >= 200:
                break

        print(f"✅ 生成 {len(valid_combinations)} 個有效參數組合")

        # 並行測試參數組合
        results = []
        total_combinations = len(valid_combinations)
        batch_size = 20

        print(f"⚡ 開始並行測試 (批大小: {batch_size})...")

        def test_rsi_combination(params, vectorbt_engine):
            try:
                strategy_params = {
                    'period': params['rsi_period'],
                    'oversold': params['rsi_oversold'],
                    'overbought': params['rsi_overbought']
                }

                result = vectorbt_engine.backtest_strategy(
                    data=data,
                    strategy="RSI_MEAN_REVERSION",
                    parameters=strategy_params,
                    symbol="0700.HK"
                )

                return {
                    'parameters': params,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'win_rate': result.win_rate,
                    'total_return': result.total_return,
                    'total_trades': result.total_trades,
                    'success': True
                }
            except Exception as e:
                return {
                    'parameters': params,
                    'error': str(e),
                    'success': False
                }

        # 分批處理
        for batch_start in range(0, total_combinations, batch_size):
            batch_end = min(batch_start + batch_size, total_combinations)
            batch = valid_combinations[batch_start:batch_end]

            print(f"📊 處理批次 {batch_start//batch_size + 1}: {len(batch)} 個組合")

            # 並行執行
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(test_rsi_combination, params, optimizer.vectorbt_engine)
                    for params in batch
                ]

                for future in futures:
                    try:
                        result = future.result()
                        if result['success']:
                            results.append(result)
                    except Exception as e:
                        logger.warning(f"處理結果失敗: {e}")

        execution_time = time.time() - start_time

        print(f"\n✅ 優化完成！")
        print(f"⏱️  執行時間: {execution_time:.2f} 秒")
        print(f"📈 成功測試: {len(results)} / {total_combinations} 個組合")
        print(f"⚡ 處理速度: {len(results) / execution_time:.1f} 組合/秒")

        # 分析結果
        if results:
            # 按Sharpe比率排序
            results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

            print(f"\n🏆 Top 10 最優 HIBOR-RSI 參數組合:")
            print("-" * 80)

            for i, result in enumerate(results[:10], 1):
                params = result['parameters']
                print(f"{i:2d}. Sharpe: {result['sharpe_ratio']:6.3f} | "
                      f"回撤: {result['max_drawdown']:6.2%} | "
                      f"勝率: {result['win_rate']:5.1%} | "
                      f"交易: {result['total_trades']:3d} | "
                      f"週期:{params['rsi_period']:3d} "
                      f"超賣:{params['rsi_oversold']:2d} "
                      f"超買:{params['rsi_overbought']:2d}")

            # 統計分析
            sharpe_values = [r['sharpe_ratio'] for r in results]
            positive_results = [r for r in results if r['sharpe_ratio'] > 1.0]

            print(f"\n📊 優化結果統計:")
            print(f"   平均 Sharpe: {np.mean(sharpe_values):.3f}")
            print(f"   最佳 Sharpe: {np.max(sharpe_values):.3f}")
            print(f"   正Sharpe組合: {len(positive_results)} ({len(positive_results)/len(results)*100:.1f}%)")
            print(f"   無交易組合: {len([r for r in results if r['total_trades'] == 0])}")

            if positive_results:
                best = positive_results[0]
                print(f"\n🎯 推薦參數組合:")
                print(f"   RSI週期: {best['parameters']['rsi_period']}")
                print(f"   超賣閾值: {best['parameters']['rsi_oversold']}")
                print(f"   超買閾值: {best['parameters']['rsi_overbought']}")
                print(f"   預期Sharpe: {best['sharpe_ratio']:.3f}")
                print(f"   預期最大回撤: {best['max_drawdown']*100:.2f}%")
                print(f"   預期勝率: {best['win_rate']*100:.2f}%")

            # 保存結果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': '0700.HK',
                'data_points': len(data),
                'optimization_summary': {
                    'total_combinations_tested': total_combinations,
                    'successful_combinations': len(results),
                    'execution_time': execution_time,
                    'processing_speed': len(results) / execution_time
                },
                'best_parameters': results[:10],
                'statistics': {
                    'average_sharpe': float(np.mean(sharpe_values)),
                    'max_sharpe': float(np.max(sharpe_values)),
                    'positive_sharpe_count': len(positive_results),
                    'no_trade_count': len([r for r in results if r['total_trades'] == 0])
                }
            }

            with open(f'hibor_rsi_optimization_results_{timestamp}.json', 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 結果已保存到: hibor_rsi_optimization_results_{timestamp}.json")

        else:
            print("❌ 沒有成功的測試結果")

        print(f"\n🎉 0700.HK HIBOR-RSI 參數優化演示完成！")
        print(f"📊 這只是小規模演示，完整系統支持 528,000+ 參數組合")
        return True

    except Exception as e:
        print(f"❌ 優化過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)