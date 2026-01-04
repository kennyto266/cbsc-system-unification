"""
Quantitative Strategy Development Example
量化策略開發完整示例

展示如何使用CBS-C系統開發和測試量化策略的完整流程：
1. 創建策略
2. 配置回測
3. 運行回測
4. 分析結果
"""

import asyncio
import sys
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# 添加項目路徑
sys.path.append('..')

from src.strategies.quant_strategy_framework import (
    create_strategy_config, StrategyType, StrategyManager
)
from src.strategies.examples.example_strategies import (
    MovingAverageCrossoverStrategy,
    RSIMeanReversionStrategy,
    BollingerBandsStrategy
)
from src.strategies.strategy_backtester import (
    BacktestEngine, BacktestConfig, BacktestAnalyzer
)

async def main():
    """主函數 - 完整的策略開發流程"""

    print("="*60)
    print("CBS-C 量化策略開發示例")
    print("="*60)

    # 1. 創建策略配置
    print("\n1. 創建策略配置...")

    # 移動平均線策略配置
    ma_config = create_strategy_config(
        name="MA交叉策略",
        strategy_type=StrategyType.MOMENTUM,
        symbols=["AAPL"],
        timeframe="1d",
        initial_capital=1000000,
        max_position_size=0.3,
        risk_limit=0.02,
        fast_period=10,
        slow_period=30,
        signal_threshold=0.02
    )

    # RSI策略配置
    rsi_config = create_strategy_config(
        name="RSI均值回歸",
        strategy_type=StrategyType.MEAN_REVERSION,
        symbols=["AAPL"],
        timeframe="1d",
        initial_capital=1000000,
        max_position_size=0.3,
        risk_limit=0.02,
        rsi_period=14,
        oversold_level=30,
        overbought_level=70
    )

    # 布林帶策略配置
    bb_config = create_strategy_config(
        name="布林帶突破",
        strategy_type=StrategyType.MOMENTUM,
        symbols=["AAPL"],
        timeframe="1d",
        initial_capital=1000000,
        max_position_size=0.3,
        risk_limit=0.02,
        bb_period=20,
        bb_std=2.0
    )

    print("✅ 策略配置創建完成")

    # 2. 創建策略實例
    print("\n2. 實例化策略...")

    ma_strategy = MovingAverageCrossoverStrategy(ma_config)
    rsi_strategy = RSIMeanReversionStrategy(rsi_config)
    bb_strategy = BollingerBandsStrategy(bb_config)

    strategies = [ma_strategy, rsi_strategy, bb_strategy]
    print(f"✅ 創建了 {len(strategies)} 個策略")

    # 3. 配置回測
    print("\n3. 配置回測參數...")

    backtest_config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=1000000,
        commission_rate=0.001,
        slippage_rate=0.0005,
        benchmark="AAPL"  # 使用AAPL作為基準
    )

    print(f"✅ 回測期間: {backtest_config.start_date.date()} 至 {backtest_config.end_date.date()}")

    # 4. 運行回測
    print("\n4. 運行回測...")

    backtester = BacktestEngine(backtest_config)
    results = []

    for strategy in strategies:
        try:
            print(f"  正在回測: {strategy.config.name}...")
            result = await backtester.run_backtest(strategy)
            results.append(result)
            print(f"  ✅ {strategy.config.name} 回測完成")
        except Exception as e:
            print(f"  ❌ {strategy.config.name} 回測失敗: {str(e)}")

    # 5. 分析回測結果
    print("\n5. 分析回測結果...")

    if results:
        # 生成比較表格
        comparison_df = BacktestAnalyzer.compare_strategies(results)
        print("\n策略比較:")
        print(comparison_df.to_string(index=False))

        # 生成詳細報告
        print("\n詳細報告:")
        for result in results:
            report = BacktestAnalyzer.generate_report(result)
            print(f"\n{report}")

        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"backtest_report_{timestamp}.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("CBS-C 量化策略回測報告\n")
            f.write("="*60 + "\n\n")

            for result in results:
                f.write(BacktestAnalyzer.generate_report(result))
                f.write("\n" + "-"*60 + "\n\n")

            f.write("\n策略比較:\n")
            comparison_df.to_csv(f, sep='\t', index=False)

        print(f"\n✅ 報告已保存至: {report_path}")

        # 繪製結果圖表
        print("\n6. 生成可視化圖表...")
        try:
            BacktestAnalyzer.plot_results(
                results,
                save_path=f"backtest_charts_{timestamp}.png"
            )
            print("✅ 圖表已生成")
        except Exception as e:
            print(f"⚠️ 圖表生成失敗: {str(e)}")

    # 6. 最佳實踐建議
    print("\n7. 最佳實踐建議:")
    print("""
    📌 策略開發建議：
    1. 多時間週期測試：在不同時間框架下測試策略
    2. 參數優化：使用網格搜索或貝葉斯優化
    3. 樣本外測試：保留部分數據做驗證
    4. 風險管理：始終設置止損和倉位限制
    5. 多樣化：考慮組合多個相關性低的策略

    📌 使用技巧：
    - 可以通過修改策略類快速自定義新策略
    - 使用 get_data_provider() 獲取實時數據
    - 通過 StrategyManager 管理多策略運行
    - 使用 PortfolioBacktester 測試策略組合
    """)

    # 7. 運行策略管理器示例
    print("\n8. 策略管理器示例...")

    strategy_manager = StrategyManager()
    for strategy in strategies:
        strategy_manager.register_strategy(strategy)

    # 初始化所有策略
    if strategy_manager.initialize_all():
        print("✅ 所有策略初始化成功")

        # 獲取策略信息
        for name, strategy in strategy_manager.strategies.items():
            info = strategy.get_strategy_info()
            print(f"\n策略 {name}:")
            print(f"  類型: {info['type']}")
            print(f"  參數: {info['parameters']}")

    print("\n" + "="*60)
    print("示例完成！CBS-C量化交易系統已準備就緒")
    print("="*60)

if __name__ == "__main__":
    # 設置日誌級別
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 運行主程序
    asyncio.run(main())