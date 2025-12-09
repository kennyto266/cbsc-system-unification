#!/usr/bin/env python3
"""
CBSC VectorBT 回測系統演示
CBSC VectorBT Backtesting System Demo
"""

import sys
import time
from pathlib import Path
import pandas as pd
import warnings

# 抑制警告信息
warnings.filterwarnings('ignore')

def main():
    """主演示函數"""
    print("=" * 60)
    print("CBSC VectorBT 回測系統演示")
    print("=" * 60)

    try:
        # 1. 檢查系統文件
        print("\n1. 系統文件檢查...")
        core_files = [
            'cbsc_backtester.py',
            'data_loader.py',
            'signal_generator.py',
            'optimizer.py'
        ]

        for file in core_files:
            if Path(file).exists():
                size = Path(file).stat().st_size
                print(f"   OK: {file} ({size:,} bytes)")
            else:
                print(f"   ERROR: {file} 不存在")
                return False

        # 2. 檢查數據文件
        print("\n2. 數據文件檢查...")
        data_file = "CODEX--/warrant_sentiment_daily.csv"
        if Path(data_file).exists():
            size = Path(data_file).stat().st_size
            print(f"   OK: {data_file} ({size:,} bytes)")

            # 檢查數據內容
            df = pd.read_csv(data_file)
            print(f"   數據記錄: {len(df)} 條")
            if not df.empty:
                print(f"   日期範圍: {df['Date'].min()} 到 {df['Date'].max()}")
        else:
            print(f"   ERROR: {data_file} 不存在")
            return False

        # 3. 導入核心模組
        print("\n3. 導入核心模組...")
        try:
            from cbsc_backtester import CBSCBacktester
            print("   OK: CBSCBacktester 導入成功")
        except ImportError as e:
            print(f"   ERROR: 導入失敗 - {e}")
            return False

        # 4. 初始化回測系統
        print("\n4. 初始化回測系統...")
        start_time = time.time()

        try:
            backtester = CBSCBacktester(data_file)
            init_time = time.time() - start_time
            print(f"   OK: 系統初始化完成 ({init_time:.2f}秒)")
        except Exception as e:
            print(f"   ERROR: 系統初始化失敗 - {e}")
            return False

        # 5. 載入測試數據
        print("\n5. 載入測試數據...")
        start_time = time.time()

        try:
            # 載入1年的0700.HK數據
            backtester.prepare_data("0700.HK")
            load_time = time.time() - start_time

            if backtester.price_data is not None and not backtester.price_data.empty:
                print(f"   OK: 載入 {len(backtester.price_data)} 天的價格數據 ({load_time:.2f}秒)")
                print(f"   價格範圍: {backtester.price_data['Close'].min():.2f} - {backtester.price_data['Close'].max():.2f}")
            else:
                print("   ERROR: 無法載入價格數據")
                return False
        except Exception as e:
            print(f"   ERROR: 數據載入失敗 - {e}")
            return False

        # 6. 運行多策略回測
        print("\n6. 運行多策略回測...")
        start_time = time.time()

        try:
            # 運行多策略回測
            portfolios = backtester.run_multiple_strategies("0700.HK")
            backtest_time = time.time() - start_time

            if portfolios is not None and len(portfolios) > 0:
                print(f"   OK: 多策略回測完成 ({backtest_time:.2f}秒)")
                print(f"   策略數量: {len(portfolios)}")

                # 顯示每個策略的結果
                print("\n7. 策略回測結果:")
                print("-" * 50)

                for strategy_name, portfolio in portfolios.items():
                    try:
                        stats = portfolio.stats()
                        print(f"\n{strategy_name}:")
                        print(f"  總回報率: {stats['Total Return [%]']:.2f}%")
                        print(f"  夏普比率: {stats['Sharpe Ratio']:.3f}")
                        print(f"  最大回撤: {stats['Max Drawdown [%]']:.2f}%")
                        print(f"  交易次數: {stats['# Trades']}")
                        print(f"  勝率: {stats['Win Rate [%]']:.1f}%")
                    except Exception as e:
                        print(f"  {strategy_name}: 統計計算失敗 - {e}")

                # 生成策略比較表
                print(f"\n8. 策略比較表:")
                print("-" * 50)

                comparison = backtester.compare_strategies()
                if comparison is not None and not comparison.empty:
                    print(comparison.round(3))
                else:
                    print("  無法生成比較表")

            else:
                print("   ERROR: 無法運行回測")
                return False

        except Exception as e:
            print(f"   ERROR: 回測執行失敗 - {e}")
            return False

        # 9. 性能總結
        total_time = init_time + load_time + backtest_time
        print(f"\n9. 性能總結:")
        print("-" * 40)
        print(f"總處理時間: {total_time:.3f}秒")
        print(f"目標時間: <30秒")

        if total_time < 30:
            print("狀態: OK 達到性能目標")
        else:
            print("狀態: WARNING 未達到性能目標")

        # 10. 生成報告
        print(f"\n10. 生成報告:")
        print("-" * 40)

        try:
            report_path = backtester.generate_report("0700.HK")
            if report_path and Path(report_path).exists():
                print(f"OK: 報告已生成 - {report_path}")
            else:
                print("WARNING: 報告生成失敗")
        except Exception as e:
            print(f"ERROR: 報告生成失敗 - {e}")

        print(f"\n{'='*60}")
        print("CBSC VectorBT 回測系統演示完成！")
        print("系統運行正常，可以使用完整功能。")
        print("="*60)

        return True

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)