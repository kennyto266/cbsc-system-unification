"""
Multi-Asset Portfolio Optimization Example
多資產投資組合優化示例

演示如何使用多資產組合優化系統：
1. 多資產回測引擎使用
2. 動態權重調整策略
3. 相關性分析
4. 組合優化算法
5. 性能評估報告
"""

import sys
import os
import asyncio
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import logging

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入組件
from src.strategies.portfolio_v2.multi_asset_optimizer import (
    MultiAssetOptimizer,
    OptimizationMethod,
    OptimizationConstraints,
    BlackLittermanConfig
)
from src.strategies.portfolio_v2.dynamic_weight_strategy import (
    DynamicWeightAdjustmentStrategy,
    DynamicWeightConfig,
    MarketRegime,
    RebalanceTrigger
)
from src.strategies.portfolio_v2.correlation_analyzer import (
    CorrelationAnalyzer,
    CorrelationConfig,
    CorrelationMethod
)
from src.backtest.multi_asset_backtest_engine import (
    MultiAssetBacktestEngine,
    PortfolioConfig,
    RebalanceMethod
)
from src.backtest.portfolio_performance_analyzer import (
    PortfolioPerformanceAnalyzer,
    AnalysisConfig,
    AnalysisType
)

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_sample_data(assets: list, start_date: date, end_date: date) -> dict:
    """
    生成示例數據（實際應用中應使用真實市場數據）
    """
    price_data = {}

    # 生成日期範圍
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    trading_days = dates[dates.weekday < 5]  # 只保留工作日

    np.random.seed(42)  # 設置隨機種子以確保可重複性

    for asset in assets:
        # 生成價格序列
        initial_price = 100

        # 不同資產有不同的特徵
        if 'TECH' in asset:
            drift = 0.0003  # 科技股較高增長
            volatility = 0.02
        elif 'FINANCIAL' in asset:
            drift = 0.0001  # 金融股穩定增長
            volatility = 0.015
        elif 'ENERGY' in asset:
            drift = 0.0002  # 能源股中等等
            volatility = 0.025
        else:
            drift = 0.00015  # 默認
            volatility = 0.018

        # 生成收益率
        returns = np.random.normal(drift, volatility, len(trading_days))

        # 添加一些相關性（簡化處理）
        if assets.index(asset) > 0:
            # 與第一個資產相關
            correlation = 0.3 if asset != assets[0] else 1.0
            returns = correlation * returns + (1 - correlation) * np.random.normal(drift, volatility, len(trading_days))

        # 計算價格
        prices = initial_price * np.exp(np.cumsum(returns))

        # 創建DataFrame
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.001, len(prices))),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.005, len(prices)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.005, len(prices)))),
            'close': prices,
            'volume': np.random.normal(1000000, 200000, len(prices))
        }, index=trading_days)

        # 確保high >= close >= low
        df['high'] = df[['high', 'close']].max(axis=1)
        df['low'] = df[['low', 'close']].min(axis=1)

        price_data[asset] = df

    return price_data


async def example_1_basic_portfolio_optimization():
    """
    示例1：基礎投資組合優化
    """
    print("\n" + "="*50)
    print("示例1：基礎投資組合優化")
    print("="*50)

    # 1. 準備數據
    assets = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    start_date = date(2020, 1, 1)
    end_date = date(2024, 12, 31)

    print(f"加載數據: {len(assets)} 個資產，從 {start_date} 到 {end_date}")
    price_data = generate_sample_data(assets, start_date, end_date)

    # 2. 配置投資組合
    portfolio_config = PortfolioConfig(
        assets=assets,
        start_date=start_date,
        end_date=end_date,
        initial_capital=1000000,
        optimization_method=OptimizationMethod.MARKOWITZ,
        rebalance_frequency="M",
        commission=0.001,
        constraints=OptimizationConstraints(
            weight_bounds=(0.0, 0.4),  # 每個資產最大40%
            max_weight_per_asset=0.4
        )
    )

    # 3. 創建並運行回測引擎
    engine = MultiAssetBacktestEngine(portfolio_config)
    await engine.load_data()

    print("\n運行回測...")
    backtest_results = engine.run_backtest()

    # 4. 顯示結果
    metrics = backtest_results['performance_metrics']
    print(f"\n回測結果:")
    print(f"總收益率: {metrics['total_return']:.2%}")
    print(f"年化收益率: {metrics['annualized_return']:.2%}")
    print(f"年化波動率: {metrics['volatility']:.2%}")
    print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"最大回撤: {metrics['max_drawdown']:.2%}")

    # 5. 導出結果
    engine.export_results("results/basic_portfolio_optimization")
    print("\n結果已導出到: results/basic_portfolio_optimization")


async def example_2_dynamic_weight_adjustment():
    """
    示例2：動態權重調整策略
    """
    print("\n" + "="*50)
    print("示例2：動態權重調整策略")
    print("="*50)

    # 1. 準備數據
    assets = ['TECH_1', 'TECH_2', 'FINANCIAL_1', 'FINANCIAL_2', 'ENERGY_1', 'ENERGY_2', 'CONSUMER_1', 'CONSUMER_2']
    start_date = date(2019, 1, 1)
    end_date = date(2024, 12, 31)

    print(f"加載數據: {len(assets)} 個資產，從 {start_date} 到 {end_date}")
    price_data = generate_sample_data(assets, start_date, end_date)

    # 添加基準數據（市場指數）
    benchmark_assets = ['MARKET_INDEX']
    price_data.update(generate_sample_data(benchmark_assets, start_date, end_date))

    # 2. 配置動態權重策略
    dynamic_config = DynamicWeightConfig(
        rebalance_triggers=[RebalanceTrigger.TIME_BASED, RebalanceTrigger.VOLATILITY],
        rebalance_frequency="M",
        weight_deviation_threshold=0.05,
        volatility_threshold=0.25,
        base_risk_target=0.15,
        use_ml_prediction=False
    )

    # 3. 配置投資組合
    portfolio_config = PortfolioConfig(
        assets=assets,
        start_date=start_date,
        end_date=end_date,
        initial_capital=1000000,
        benchmark='MARKET_INDEX',
        optimization_method=OptimizationMethod.RISK_PARITY,
        use_dynamic_weights=True,
        dynamic_config=dynamic_config,
        constraints=OptimizationConstraints(
            weight_bounds=(0.0, 0.3),
            max_turnover=0.5
        )
    )

    # 4. 創建並運行回測引擎
    engine = MultiAssetBacktestEngine(portfolio_config)
    await engine.load_data()

    print("\n運行動態權重回測...")
    backtest_results = engine.run_backtest()

    # 5. 顯示結果
    metrics = backtest_results['performance_metrics']
    print(f"\n動態權重回測結果:")
    print(f"總收益率: {metrics['total_return']:.2%}")
    print(f"年化收益率: {metrics['annualized_return']:.2%}")
    print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"信息比率: {metrics['information_ratio']:.2f}")
    print(f"周轉率: {metrics['turnover']:.2%}")

    # 6. 顯示動態策略摘要
    if backtest_results.get('dynamic_strategy_summary'):
        print(f"\n動態策略表現:")
        print(f"市場狀態變化次數: {len(engine.dynamic_strategy.regime_history)}")
        print(f"總再平衡次數: {len(engine.weights_history)}")

    # 7. 導出結果
    engine.export_results("results/dynamic_weight_strategy")
    print("\n結果已導出到: results/dynamic_weight_strategy")


async def example_3_correlation_analysis():
    """
    示例3：相關性分析
    """
    print("\n" + "="*50)
    print("示例3：相關性分析")
    print("="*50)

    # 1. 準備數據
    assets = ['SECTOR_TECH', 'SECTOR_FIN', 'SECTOR_ENERGY', 'SECTOR_HEALTH', 'SECTOR_CONSUMER', 'SECTOR_INDUSTRIAL']
    start_date = date(2020, 1, 1)
    end_date = date(2024, 12, 31)

    print(f"加載數據: {len(assets)} 個行業資產")
    price_data = generate_sample_data(assets, start_date, end_date)

    # 2. 配置相關性分析器
    corr_config = CorrelationConfig(
        method=CorrelationMethod.PEARSON,
        lookback_window=252,
        high_correlation_threshold=0.7,
        clustering_method='hierarchical',
        n_clusters=3,
        save_plots=True
    )

    # 3. 創建並運行相關性分析器
    analyzer = CorrelationAnalyzer(corr_config)

    # 計算收益率數據
    returns_data = pd.DataFrame({
        asset: df['close'].pct_change().dropna()
        for asset, df in price_data.items()
    })

    print("\n計算相關性矩陣...")
    correlation_matrix = analyzer.calculate_correlation_matrix(returns_data)

    # 4. 顯示相關性摘要
    print("\n相關性分析摘要:")
    summary = analyzer.correlation_summary
    print(f"平均相關性: {summary['mean_correlation']:.3f}")
    print(f"最高相關性: {summary['max_correlation']:.3f}")
    print(f"最低相關性: {summary['min_correlation']:.3f}")
    print(f"高相關性資產對數量: {summary['high_corr_count']}")

    # 5. 資產聚類
    print("\n執行資產聚類...")
    clusters = analyzer.cluster_assets()
    for cluster_id, cluster_assets in clusters.items():
        print(f"聚類 {cluster_id}: {cluster_assets}")

    # 6. 動態相關性分析
    print("\n計算動態相關性...")
    dynamic_correlations = analyzer.calculate_dynamic_correlations(returns_data)

    # 7. 相關性變化分析
    print("\n分析相關性變化...")
    correlation_changes = analyzer.analyze_correlation_changes()
    print(f"平均變化: {correlation_changes['mean_change']:.3f}")
    print(f"顯著變化資產對數量: {correlation_changes['significant_changes']}")

    # 8. 生成報告
    correlation_report = analyzer.generate_correlation_report()

    # 9. 導出結果
    analyzer.export_correlation_data("results/correlation_analysis")
    print("\n相關性分析結果已導出到: results/correlation_analysis")


async def example_4_portfolio_optimization_comparison():
    """
    示例4：投資組合優化方法比較
    """
    print("\n" + "="*50)
    print("示例4：投資組合優化方法比較")
    print("="*50)

    # 1. 準備數據
    assets = ['ASSET_A', 'ASSET_B', 'ASSET_C', 'ASSET_D', 'ASSET_E', 'ASSET_F']
    start_date = date(2020, 1, 1)
    end_date = date(2024, 12, 31)

    print(f"加載數據: {len(assets)} 個資產")
    price_data = generate_sample_data(assets, start_date, end_date)

    # 2. 比較不同優化方法
    optimization_methods = [
        OptimizationMethod.MARKOWITZ,
        OptimizationMethod.MIN_VARIANCE,
        OptimizationMethod.RISK_PARITY,
        OptimizationMethod.EQUAL_WEIGHT
    ]

    results = {}

    for method in optimization_methods:
        print(f"\n測試優化方法: {method.value}")

        # 配置投資組合
        portfolio_config = PortfolioConfig(
            assets=assets,
            start_date=start_date,
            end_date=end_date,
            initial_capital=1000000,
            optimization_method=method,
            rebalance_frequency="Q"
        )

        # 運行回測
        engine = MultiAssetBacktestEngine(portfolio_config)
        await engine.load_data()
        backtest_results = engine.run_backtest()

        # 保存結果
        results[method.value] = backtest_results['performance_metrics']

        print(f"  總收益率: {results[method.value]['total_return']:.2%}")
        print(f"  夏普比率: {results[method.value]['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {results[method.value]['max_drawdown']:.2%}")

    # 3. 生成比較報告
    print("\n" + "="*30)
    print("優化方法比較摘要")
    print("="*30)

    comparison_df = pd.DataFrame(results).T
    print("\n性能指標比較:")
    print(comparison_df[['total_return', 'sharpe_ratio', 'max_drawdown', 'volatility']].round(4))

    # 4. 找出最佳方法
    best_sharpe = comparison_df['sharpe_ratio'].idxmax()
    best_return = comparison_df['total_return'].idxmax()
    lowest_risk = comparison_df['max_drawdown'].idxmax()  # 負值越大，回撤越小

    print(f"\n最佳夏普比率: {best_sharpe}")
    print(f"最高收益率: {best_return}")
    print(f"最低風險（最小回撤）: {lowest_risk}")

    # 5. 導出比較結果
    comparison_df.to_csv("results/optimization_methods_comparison.csv")
    print("\n比較結果已導出到: results/optimization_methods_comparison.csv")


async def example_5_black_litterman_model():
    """
    示例5：Black-Litterman模型優化
    """
    print("\n" + "="*50)
    print("示例5：Black-Litterman模型優化")
    print("="*50)

    # 1. 準備數據
    assets = ['STOCK_1', 'STOCK_2', 'STOCK_3', 'STOCK_4', 'STOCK_5']
    start_date = date(2020, 1, 1)
    end_date = date(2024, 12, 31)

    print(f"加載數據: {len(assets)} 個股票")
    price_data = generate_sample_data(assets, start_date, end_date)

    # 2. 配置Black-Litterman模型
    bl_config = BlackLittermanConfig(
        tau=0.025,
        views=[
            {
                "assets": ["STOCK_1", "STOCK_2"],
                "weights": [0.6, 0.4],
                "confidence": 0.5,
                "expected_return": 0.12
            },
            {
                "assets": ["STOCK_3"],
                "weights": [1.0],
                "confidence": 0.7,
                "expected_return": 0.15
            }
        ],
        use_prior_returns=True
    )

    # 3. 創建優化器
    optimizer = MultiAssetOptimizer(method=OptimizationMethod.BLACK_LITTERMAN)

    # 準備數據
    returns_data = pd.DataFrame({
        asset: df['close'].pct_change().dropna()
        for asset, df in price_data.items()
    })

    # 執行優化
    weights = optimizer.optimize_weights(bl_config=bl_config)

    print("\nBlack-Litterman優化權重:")
    for asset, weight in weights.items():
        print(f"  {asset}: {weight:.2%}")

    # 4. 與傳統Markowitz比較
    print("\n與傳統Markowitz比較...")
    markowitz_optimizer = MultiAssetOptimizer(method=OptimizationMethod.MARKOWITZ)
    markowitz_optimizer.prepare_data(price_data)
    markowitz_weights = markowitz_optimizer.optimize_weights()

    print("\nMarkowitz優化權重:")
    for asset, weight in markowitz_weights.items():
        print(f"  {asset}: {weight:.2%}")

    # 5. 計算性能差異
    bl_return = optimizer._calculate_portfolio_return(weights)
    bl_volatility = optimizer._calculate_portfolio_volatility(weights)
    bl_sharpe = optimizer._calculate_sharpe_ratio(weights)

    mkw_return = markowitz_optimizer._calculate_portfolio_return(markowitz_weights)
    mkw_volatility = markowitz_optimizer._calculate_portfolio_volatility(markowitz_weights)
    mkw_sharpe = markowitz_optimizer._calculate_sharpe_ratio(markowitz_weights)

    print("\n性能比較:")
    print(f"Black-Litterman - 收益率: {bl_return:.2%}, 波動率: {bl_volatility:.2%}, 夏普比率: {bl_sharpe:.2f}")
    print(f"Markowitz - 收益率: {mkw_return:.2%}, 波動率: {mkw_volatility:.2%}, 夏普比率: {mkw_sharpe:.2f}")


async def example_6_performance_analysis():
    """
    示例6：投資組合性能分析
    """
    print("\n" + "="*50)
    print("示例6：投資組合性能分析")
    print("="*50)

    # 1. 模擬投資組合價值數據
    dates = pd.date_range(start=date(2020, 1, 1), end=date(2024, 12, 31), freq='D')
    trading_days = dates[dates.weekday < 5]

    # 生成投資組合價值序列
    initial_value = 1000000
    daily_returns = np.random.normal(0.0003, 0.015, len(trading_days))  # 年化7.5%，15%波動率
    portfolio_values = initial_value * np.exp(np.cumsum(daily_returns))

    portfolio_series = pd.Series(portfolio_values, index=trading_days)

    # 生成權重歷史
    assets = ['ASSET_1', 'ASSET_2', 'ASSET_3', 'ASSET_4', 'ASSET_5']
    weights_history = []

    for i, date in enumerate(trading_days[::30]):  # 每月記錄一次
        weights = {
            'ASSET_1': 0.2 + np.random.normal(0, 0.05),
            'ASSET_2': 0.2 + np.random.normal(0, 0.05),
            'ASSET_3': 0.2 + np.random.normal(0, 0.05),
            'ASSET_4': 0.2 + np.random.normal(0, 0.05),
            'ASSET_5': 0.2 + np.random.normal(0, 0.05)
        }

        # 正規化權重
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}

        weights_history.append({
            'date': date,
            'weights': weights
        })

    # 2. 配置性能分析器
    analysis_config = AnalysisConfig(
        analysis_types=[
            AnalysisType.PERFORMANCE,
            AnalysisType.RISK,
            AnalysisType.ATTRIBUTION,
            AnalysisType.STRESS_TEST
        ],
        risk_free_rate=0.02,
        include_charts=True
    )

    # 3. 創建並運行分析器
    analyzer = PortfolioPerformanceAnalyzer(analysis_config)

    # 加載數據
    analyzer.load_data(
        portfolio_values=portfolio_series,
        weights_history=weights_history
    )

    print("\n運行性能分析...")

    # 運行分析
    results = analyzer.run_analysis()

    # 4. 顯示性能指標
    if 'performance' in results:
        metrics = results['performance']['metrics']
        print("\n性能指標:")
        print(f"總收益率: {metrics['total_return']:.2%}")
        print(f"年化收益率: {metrics['annualized_return']:.2%}")
        print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
        print(f"最大回撤: {metrics['max_drawdown']:.2%}")
        print(f"Alpha: {metrics['alpha']:.2%}")
        print(f"Beta: {metrics['beta']:.2f}")

    # 5. 顯示風險分析
    if 'risk' in results:
        risk_analysis = results['risk']
        print("\n風險分析:")
        if 'volatility_analysis' in risk_analysis:
            print(f"當前波動率: {risk_analysis['volatility_analysis']['current_volatility']:.2%}")
        if 'drawdown_analysis' in risk_analysis:
            print(f"最大回撤持續時間: {risk_analysis['drawdown_analysis']['max_drawdown_duration']} 天")

    # 6. 顯示壓力測試結果
    if 'stress_test' in results:
        stress_results = results['stress_test']
        print("\n壓力測試結果:")
        for scenario, result in stress_results.items():
            print(f"{scenario}: 潛在損失 {result['loss_percentage']:.1%}")

    # 7. 導出報告
    os.makedirs("results", exist_ok=True)
    analyzer.export_report("results/portfolio_performance_analysis", format="html")
    print("\n性能分析報告已導出到: results/portfolio_performance_analysis.html")


async def main():
    """
    主函數：運行所有示例
    """
    print("="*60)
    print("多資產投資組合優化系統示例")
    print("="*60)

    # 創建結果目錄
    os.makedirs("results", exist_ok=True)

    try:
        # 運行所有示例
        await example_1_basic_portfolio_optimization()
        await example_2_dynamic_weight_adjustment()
        await example_3_correlation_analysis()
        await example_4_portfolio_optimization_comparison()
        await example_5_black_litterman_model()
        await example_6_performance_analysis()

        print("\n" + "="*60)
        print("所有示例運行完成！")
        print("請查看 results/ 目錄中的輸出文件")
        print("="*60)

    except Exception as e:
        logger.error(f"運行示例時出錯: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 運行示例
    asyncio.run(main())