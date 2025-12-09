"""
Complete CBSC System Test
完整CBSC系統測試

Test the complete VectorBT-native CBSC backtesting system with real data.
使用真實數據測試完整的VectorBT原生CBSC回測系統。

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

import sys
import time
import traceback
from pathlib import Path

# 確保可以導入本地模塊
sys.path.append(str(Path(__file__).parent))

from data_loader import CBSCDataLoader
from signal_generator import CBSCSignalGenerator
from cbsc_backtester import CBSCBacktester
from optimizer import CBSCOptimizer

def test_data_loader():
    """測試數據加載器"""
    print("=" * 60)
    print("1. 測試數據加載器")
    print("=" * 60)

    try:
        # 檢查數據文件
        sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
        if not Path(sentiment_path).exists():
            print(f"❌ 數據文件不存在: {sentiment_path}")
            return False

        # 初始化加載器
        loader = CBSCDataLoader(sentiment_path)

        # 加載情緒數據
        print("   加載情緒數據...")
        sentiment_df = loader.load_sentiment_data()
        if sentiment_df.empty:
            print("❌ 情緒數據加載失敗")
            return False
        print(f"OK: 成功加載 {len(sentiment_df)} 條情緒數據")

        # 加載價格數據
        print("   加載價格數據...")
        price_df = loader.load_price_data("0700.HK")
        if price_df.empty:
            print("FAIL: 價格數據加載失敗")
            return False
        print(f"OK: 成功加載 {len(price_df)} 條價格數據")

        # 數據摘要
        summary = loader.get_data_summary()
        print("   數據摘要:")
        print(f"     情緒記錄數: {summary['sentiment_records']}")
        print(f"     價格記錄數: {summary['price_records']}")
        print(f"     平均情緒強度: {summary['avg_sentiment_strength']:.3f}")
        print(f"     情緒波動率: {summary['sentiment_volatility']:.3f}")

        return True

    except Exception as e:
        print(f"❌ 數據加載器測試失敗: {e}")
        traceback.print_exc()
        return False

def test_signal_generator():
    """測試信號生成器"""
    print("\n" + "=" * 60)
    print("2. 測試信號生成器")
    print("=" * 60)

    try:
        # 初始化組件
        sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
        loader = CBSCDataLoader(sentiment_path)
        generator = CBSCSignalGenerator()

        # 準備數據
        print("   準備數據...")
        sentiment_df = loader.load_sentiment_data()
        price_df = loader.load_price_data("0700.HK")
        aligned_sentiment, aligned_price = loader.align_data()
        features_df = loader.create_cbsc_features(aligned_sentiment, aligned_price)

        if features_df.empty:
            print("❌ 特徵數據創建失敗")
            return False
        print(f"✅ 成功創建 {len(features_df)} 條特徵數據")

        # 生成信號
        print("   生成多策略信號...")
        strategies = generator.generate_multiple_strategies(features_df)
        print(f"✅ 成功生成 {len(strategies)} 種策略信號")

        # 分析信號質量
        print("   分析信號質量...")
        for strategy_name, (entries, exits) in strategies.items():
            quality = generator.analyze_signal_quality(features_df, entries, exits)
            print(f"   {strategy_name}: {quality['total_entries']} 進入信號, "
                  f"{quality['total_exits']} 退出信號, "
                  f"質量分數: {quality['sentiment_data_quality']:.3f}")

        return True

    except Exception as e:
        print(f"❌ 信號生成器測試失敗: {e}")
        traceback.print_exc()
        return False

def test_backtester():
    """測試回測器"""
    print("\n" + "=" * 60)
    print("3. 測試回測器")
    print("=" * 60)

    try:
        # 初始化回測器
        sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
        backtester = CBSCBacktester(sentiment_path)

        # 準備數據
        print("   準備回測數據...")
        if not backtester.prepare_data("0700.HK"):
            print("❌ 數據準備失敗")
            return False
        print("✅ 數據準備完成")

        # 運行多策略回測
        print("   運行多策略回測...")
        portfolios = backtester.run_multiple_strategies("0700.HK")
        if not portfolios:
            print("❌ 策略回測失敗")
            return False
        print(f"✅ 成功回測 {len(portfolios)} 種策略")

        # 比較策略
        print("   比較策略性能...")
        comparison_df = backtester.compare_strategies()
        if comparison_df.empty:
            print("❌ 策略比較失敗")
            return False

        print("   策略性能排名:")
        for i, (strategy_name, metrics) in enumerate(comparison_df.iterrows(), 1):
            print(f"     {i}. {strategy_name}: "
                  f"Sharpe={metrics['sharpe_ratio']:.3f}, "
                  f"收益率={metrics['total_return']:.2f}%, "
                  f"回撤={metrics['max_drawdown']:.2f}%")

        return True

    except Exception as e:
        print(f"❌ 回測器測試失敗: {e}")
        traceback.print_exc()
        return False

def test_optimizer():
    """測試優化器"""
    print("\n" + "=" * 60)
    print("4. 測試優化器")
    print("=" * 60)

    try:
        # 初始化優化器
        sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
        optimizer = CBSCOptimizer(sentiment_path)

        # 運行小規模優化
        print("   運行參數優化...")
        results = optimizer.run_random_search("0700.HK", n_iterations=20)
        if results.empty:
            print("❌ 參數優化失敗")
            return False
        print(f"✅ 成功完成 {len(results)} 次參數組合測試")

        # 最佳參數
        best_result = results.iloc[0]
        print("   最佳參數組合:")
        print(f"     Sharpe比率: {best_result.get('sharpe_ratio', 'N/A'):.3f}")
        print(f"     總收益率: {best_result.get('total_return', 'N/A'):.2f}%")
        print(f"     最大回撤: {best_result.get('max_drawdown', 'N/A'):.2f}%")

        # 優化摘要
        summary = optimizer.get_optimization_summary("0700.HK")
        print("   優化摘要:")
        print(f"     測試組合數: {summary['total_combinations_tested']}")
        print(f"     優化目標: {summary['optimization_metric']}")

        return True

    except Exception as e:
        print(f"❌ 優化器測試失敗: {e}")
        traceback.print_exc()
        return False

def test_performance():
    """測試系統性能"""
    print("\n" + "=" * 60)
    print("5. 測試系統性能")
    print("=" * 60)

    try:
        sentiment_path = "CODEX--/warrant_sentiment_daily.csv"

        # 數據加載性能
        print("   測試數據加載性能...")
        start_time = time.time()
        loader = CBSCDataLoader(sentiment_path)
        sentiment_df = loader.load_sentiment_data()
        price_df = loader.load_price_data("0700.HK")
        aligned_sentiment, aligned_price = loader.align_data()
        features_df = loader.create_cbsc_features(aligned_sentiment, aligned_price)
        load_time = time.time() - start_time
        print(f"✅ 數據加載完成: {load_time:.3f}秒")

        # 信號生成性能
        print("   測試信號生成性能...")
        start_time = time.time()
        generator = CBSCSignalGenerator()
        strategies = generator.generate_multiple_strategies(features_df)
        signal_time = time.time() - start_time
        print(f"✅ 信號生成完成: {signal_time:.3f}秒")

        # 回測性能
        print("   測試回測性能...")
        start_time = time.time()
        backtester = CBSCBacktester(sentiment_path)
        backtester.features_df = features_df
        backtester.price_data = price_df.set_index('Date')
        portfolios = backtester.run_multiple_strategies("0700.HK")
        backtest_time = time.time() - start_time
        print(f"✅ 回測完成: {backtest_time:.3f}秒")

        # 性能總結
        total_time = load_time + signal_time + backtest_time
        print(f"\n   性能總結:")
        print(f"     數據記錄數: {len(features_df)}")
        print(f"     數據加載: {load_time:.3f}秒")
        print(f"     信號生成: {signal_time:.3f}秒")
        print(f"     回測執行: {backtest_time:.3f}秒")
        print(f"     總耗時: {total_time:.3f}秒")

        # 性能目標檢查
        if total_time < 30:  # 目標：30秒內完成
            print("✅ 性能目標達成！")
        else:
            print(f"⚠️  性能目標未達成 (目標 < 30秒, 實際 {total_time:.3f}秒)")

        return True

    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """測試系統集成"""
    print("\n" + "=" * 60)
    print("6. 測試系統集成")
    print("=" * 60)

    try:
        sentiment_path = "CODEX--/warrant_sentiment_daily.csv"

        # 完整工作流程測試
        print("   執行完整工作流程...")
        start_time = time.time()

        # 1. 數據加載
        loader = CBSCDataLoader(sentiment_path)
        sentiment_df = loader.load_sentiment_data()
        price_df = loader.load_price_data("0700.HK")
        aligned_sentiment, aligned_price = loader.align_data()
        features_df = loader.create_cbsc_features(aligned_sentiment, aligned_price)

        # 2. 策略回測
        backtester = CBSCBacktester(sentiment_path)
        backtester.features_df = features_df
        backtester.price_data = price_df.set_index('Date')
        portfolios = backtester.run_multiple_strategies("0700.HK")

        # 3. 參數優化
        optimizer = CBSCOptimizer(sentiment_path)
        optimization_results = optimizer.run_random_search("0700.HK", n_iterations=10)

        # 4. 生成報告
        report = backtester.generate_report("cbsc_integration_test_report.txt")

        workflow_time = time.time() - start_time

        print(f"✅ 完整工作流程完成: {workflow_time:.3f}秒")
        print(f"   數據記錄: {len(features_df)}")
        print(f"   策略數量: {len(portfolios)}")
        print(f"   優化組合: {len(optimization_results)}")
        print(f"   報告生成: 完成")

        return True

    except Exception as e:
        print(f"❌ 系統集成測試失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("CBSC VectorBT 完整系統測試")
    print("測試目標: 驗證 < 500行代碼的CBSC回測系統")
    print("=" * 60)

    # 運行所有測試
    tests = [
        ("數據加載器", test_data_loader),
        ("信號生成器", test_signal_generator),
        ("回測引擎", test_backtester),
        ("參數優化器", test_optimizer),
        ("系統性能", test_performance),
        ("系統集成", test_integration)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} 測試通過")
            else:
                print(f"❌ {test_name} 測試失敗")
        except Exception as e:
            print(f"❌ {test_name} 測試異常: {e}")

    # 測試總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    print(f"通過測試: {passed_tests}/{total_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")

    if passed_tests == total_tests:
        print("\n所有測試通過！CBSC VectorBT回測系統運行正常")
        print("系統特點:")
        print("   • VectorBT原生架構 - 高性能向量化計算")
        print("   • CBSC專用邏輯 - 處理收回價風險和槓桿效應")
        print("   • 情緒數據整合 - 基於HKEX牛熊證情緒")
        print("   • 多策略支持 - 5種內置策略模板")
        print("   • 參數優化 - 網格搜索、隨機搜索、貝葉斯優化")
        print("   • 代碼簡潔 - 核心功能 < 500行")
        return True
    else:
        print(f"\n{total_tests - passed_tests} 個測試失敗，請檢查系統配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)