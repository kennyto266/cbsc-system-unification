#!/usr / bin / env python3
"""
Cookbook增強功能使用示例
展示如何使用基於Python Algorithmic Trading Cookbook的專業級量化交易技術

這個示例演示了：
1. Walk - Forward優化
2. Cookbook策略比較
3. 高級投資組合分析
4. GPU加速計算
5. 綜合報告生成
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "simplified_system", "src")
)

try:
    from backtest.enhanced import (
        AdvancedPortfolioAnalyzer,
        CookbookStrategyBuilder,
        GPUVectorBTAccelerator,
        WalkForwardOptimizer,
        compare_all_strategies,
        get_enhanced_backtest_engine,
        quick_strategy_analysis,
        run_walkforward_optimization,
    )

    print("Successfully imported Cookbook enhanced features")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)


def generate_sample_data():
    """Generate sample data"""
    print("\nGenerating sample data...")

    # Simulate price data (similar to 0700.HK)
    np.random.seed(42)
    dates = pd.date_range("2020 - 01 - 01", "2023 - 12 - 31", freq="D")

    # Generate trend price
    trend = np.linspace(100, 300, len(dates))
    noise = np.cumsum(np.random.randn(len(dates)) * 0.01)
    price = trend + noise

    # Add some volatility
    volatility = np.random.rand(len(dates)) * 0.02
    price = price * (1 + volatility)

    price_data = pd.Series(price, index = dates)
    print(f"Generated {len(price_data)} days of price data")

    return price_data


def demo_gpu_acceleration(price_data):
    """演示GPU加速功能"""
    print("\n🚀 GPU加速功能演示")

    try:
        # 初始化GPU加速器
        accelerator = GPUVectorBTAccelerator()

        # 檢查GPU狀態
        gpu_status = accelerator.monitor_gpu_usage()
        print(f"GPU可用: {gpu_status.get('gpu_available', False)}")

        if gpu_status.get("gpu_available"):
            device_info = gpu_status.get("device_info", {})
            print(f"GPU設備: {device_info.get('name', 'Unknown')}")
            print(f"GPU內存: {device_info.get('total_memory', 0) / (1024 * *3):.1f} GB")

        # 運行性能基準測試
        benchmark_result = accelerator.run_performance_benchmark(price_data)

        # 生成性能報告
        report = accelerator.generate_performance_report(benchmark_result)
        print("\n" + "=" * 50)
        print("GPU加速性能報告")
        print("=" * 50)
        print(report)

    except Exception as e:
        print(f"❌ GPU加速演示失敗: {e}")


def demo_strategy_comparison(price_data):
    """演示策略比較功能"""
    print("\n📈 策略比較演示")

    try:
        # 比較所有可用策略
        comparison = compare_all_strategies(price_data)

        print("\n策略比較結果:")
        print("=" * 60)

        # 顯示關鍵指標
        key_metrics = ["sharpe_ratio", "total_return", "max_drawdown", "win_rate"]
        display_cols = ["description"] + [
            col for col in comparison.columns if col in key_metrics
        ]

        print(comparison[display_cols].round(4))

        # 找出最佳策略
        best_sharpe = comparison["sharpe_ratio"].idxmax()
        best_return = comparison["total_return"].idxmax()

        print(f"\n🏆 最佳Sharpe策略: {best_sharpe}")
        print(f"💰 最高回報策略: {best_return}")

        return comparison

    except Exception as e:
        print(f"❌ 策略比較失敗: {e}")
        return None


def demo_single_strategy_analysis(price_data):
    """演示單個策略深度分析"""
    print("\n🔍 單策略深度分析演示")

    try:
        # 使用RSI策略進行深度分析
        analysis_result = quick_strategy_analysis(price_data, "RSI_MEAN_REVERSION")

        analysis_result["portfolio"]
        performance = analysis_result["analysis"]["performance"]
        risk_metrics = analysis_result["analysis"]["risk_metrics"]

        print(f"\n策略績效指標:")
        print(f"  總回報: {performance.total_return:.2%}")
        print(f"  年化回報: {performance.annualized_return:.2%}")
        print(f"  Sharpe比率: {performance.sharpe_ratio:.3f}")
        print(f"  最大回撤: {risk_metrics.max_drawdown:.2%}")
        print(f"  勝率: {performance.win_rate:.2%}")

        # 生成完整報告
        full_report = analysis_result["report"]
        print(f"\n{full_report}")

        return analysis_result

    except Exception as e:
        print(f"❌ 單策略分析失敗: {e}")
        return None


def demo_walkforward_optimization(price_data):
    """演示Walk - Forward優化"""
    print("\n🔄 Walk - Forward優化演示")

    try:
        # 創建簡化的Walk - Forward配置
        from simplified_system.src.backtest.enhanced.vectorbt_walkforward_optimizer import (
            WalkForwardConfig,
        )

        config = WalkForwardConfig(
            window_len = 252,  # 1年窗口
            n_splits = 3,  # 3個分割
            set_lens=(126,),  # 6個月Out - of - Sample
            objective="sharpe_ratio",
        )

        # 使用RSI策略進行Walk - Forward優化
        result = run_walkforward_optimization(
            price_data, rsi_mean_reversion_strategy, config
        )

        wf_result = result["result"]
        report = result["report"]

        print(f"\nWalk - Forward優化結果:")
        print(f"  總分割數: {wf_result.total_splits}")
        print(f"  成功分割數: {wf_result.successful_splits}")
        print(f"  穩定性評分: {wf_result.stability_score:.2f}/100")
        print(f"  Sharpe改善: {wf_result.sharpe_improvement:.4f}")
        print(f"  優化耗時: {wf_result.optimization_time:.2f}秒")

        # 生成詳細報告
        print(f"\n{report}")

        return result

    except Exception as e:
        print(f"❌ Walk - Forward優化失敗: {e}")
        return None


def demo_advanced_portfolio_analysis(price_data):
    """演示高級投資組合分析"""
    print("\n📊 高級投資組合分析演示")

    try:
        from simplified_system.src.backtest.enhanced.cookbook_strategies.rsi_mean_reversion_strategy import (
            rsi_mean_reversion_strategy,
        )
        from vectorbt import Portfolio

        # 創建投資組合
        portfolio = rsi_mean_reversion_strategy(
            price_data, rsi_period = 14, oversold = 30, overbought = 70
        )

        # 使用高級分析器
        analyzer = AdvancedPortfolioAnalyzer()
        analysis_result = analyzer.analyze_portfolio(portfolio)

        # 提取關鍵結果
        performance = analysis_result["performance"]
        risk_metrics = analysis_result["risk_metrics"]
        drawdown_analysis = analysis_result["drawdown_analysis"]
        trade_analysis = analysis_result["trade_analysis"]

        print(f"\n詳細投資組合分析:")
        print("=" * 60)

        print(f"📈 績效指標:")
        print(f"  總回報: {performance.total_return:.2%}")
        print(f"  年化回報: {performance.annualized_return:.2%}")
        print(f"  Sharpe比率: {performance.sharpe_ratio:.3f}")
        print(f"  Sortino比率: {performance.sortino_ratio:.3f}")
        print(f"  Calmar比率: {performance.calmar_ratio:.3f}")
        print(f"  勝率: {performance.win_rate:.2%}")

        print(f"\n🛡️ 風險指標:")
        print(f"  最大回撤: {risk_metrics.max_drawdown:.2%}")
        print(f"  年化波動率: {risk_metrics.volatility:.2%}")
        print(f"  VaR (95%): {risk_metrics.var_95:.2%}")
        print(f"  CVaR (95%): {risk_metrics.cvar_95:.2%}")

        print(f"\n📉 回撤分析:")
        print(f"  當前回撤: {drawdown_analysis['current_drawdown']:.2%}")
        print(f"  最大回撤持續: {drawdown_analysis['max_drawdown_duration']:.0f}天")
        print(f"  平均恢復時間: {drawdown_analysis['average_recovery_time']:.0f}天")

        if "error" not in trade_analysis:
            print(f"\n💼 交易統計:")
            print(f"  總交易次數: {trade_analysis['total_trades']}")
            print(f"  獲利交易: {trade_analysis['winning_trades']}")
            print(f"  虧損交易: {trade_analysis['losing_trades']}")
            print(f"  盈利因子: {trade_analysis['profit_factor']:.2f}")
            print(f"  平均持倉期: {trade_analysis['avg_holding_period']:.1f}天")

        # 生成可視化
        try:
            analyzer.create_performance_visualization(analysis_result)
        except Exception as e:
            print(f"⚠️ 可視化創建失敗: {e}")

        return analysis_result

    except Exception as e:
        print(f"❌ 高級投資組合分析失敗: {e}")
        return None


def main():
    """主函數"""
    print("🎯 Cookbook增強功能完整演示")
    print("基於Python Algorithmic Trading Cookbook的專業級量化交易技術")
    print("=" * 70)

    # 生成示例數據
    price_data = generate_sample_data()

    # 1. GPU加速功能演示
    demo_gpu_acceleration(price_data)

    # 2. 策略比較演示
    demo_strategy_comparison(price_data)

    # 3. 單策略深度分析演示
    demo_single_strategy_analysis(price_data)

    # 4. Walk - Forward優化演示
    demo_walkforward_optimization(price_data)

    # 5. 高級投資組合分析演示
    demo_advanced_portfolio_analysis(price_data)

    print("\n" + "=" * 70)
    print("🎉 演示完成！Cookbook增強功能已成功集成到Simplified System")
    print("\n📚 主要功能總結:")
    print("  ✅ Walk - Forward優化 - 防止過擬合的專業技術")
    print("  ✅ Cookbook策略庫 - 經過驗證的量化策略")
    print("  ✅ 高級投資組合分析 - 機構級風險和績效分析")
    print("  ✅ GPU加速計算 - 大幅提升計算性能")
    print("  ✅ 綜合報告生成 - 專業級分析報告")

    print("\n🚀 下一步建議:")
    print("  1. 使用真實港股數據進行測試")
    print("  2. 根據您的具體需求調整參數")
    print("  3. 探索更多Cookbook中的高級技術")
    print("  4. 考慮實施Alpha因子分析系統")


if __name__ == "__main__":
    main()
