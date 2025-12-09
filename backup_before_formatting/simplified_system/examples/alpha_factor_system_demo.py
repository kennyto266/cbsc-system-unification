#!/usr/bin/env python3
"""
Alpha Factor System Demonstration
展示Alpha因子系統的完整功能

這個示例演示了：
1. Alpha因子計算引擎
2. 技術指標到Alpha因子轉換
3. 因子有效性檢驗
4. AlphaLens分析（如果可用）
5. 多因子模型構建
6. 因子投資組合管理
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def generate_sample_market_data():
    """生成示例市場數據"""
    print("📊 生成示例市場數據...")

    # 模擬港股數據
    np.random.seed(42)
    symbols = ['0700.HK', '0941.HK', '1398.HK', '0388.HK', '1299.HK', '2318.HK', '0005.HK', '0399.HK']
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')

    market_data = {}

    for symbol in symbols:
        # 生成趨勢價格
        trend = np.random.choice([-1, 1]) * np.linspace(100, 300, len(dates))
        noise = np.cumsum(np.random.randn(len(dates)) * 0.02)
        base_price = 50 + np.random.choice([50, 100, 150, 200])

        price = base_price + trend + noise

        # 生成成交量數據
        base_volume = np.random.randint(1000000, 10000000)
        volume = base_volume * (1 + 0.5 * np.random.randn(len(dates)))

        # 生成OHLCV數據
        high_low_range = price * 0.02
        high = price + np.random.rand(len(dates)) * high_low_range
        low = price - np.random.rand(len(dates)) * high_low_range
        open_price = price + np.random.randn(len(dates)) * 0.01

        df = pd.DataFrame({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': price,
            'Volume': volume
        }, index=dates)

        # 確保OHLC關係正確
        df['High'] = np.maximum(df['High'], np.maximum(df['Open'], df['Close']))
        df['Low'] = np.minimum(df['Low'], np.minimum(df['Open'], df['Close']))

        market_data[symbol] = df

    print(f"✓ 生成 {len(symbols)} 個股票 {len(dates)} 天的數據")
    return market_data

def demo_alpha_factor_engine(market_data):
    """演示Alpha因子計算引擎"""
    print("\n🔬 Alpha因子計算引擎演示")

    try:
        from alpha.factor_engine.alpha_factor_engine import AlphaFactorEngine, FactorTypes, FactorConfig

        # 創建因子引擎配置
        config = FactorConfig(
            standardize=True,
            winsorize=True,
            winsorize_method="quantile",
            winsorize_limits=(0.05, 0.95)
        )

        # 初始化因子引擎
        engine = AlphaFactorEngine(config)

        # 選擇一個股票進行演示
        symbol = '0700.HK'
        data = market_data[symbol]

        # 計算多種Alpha因子
        factor_types = [FactorTypes.MOMENTUM, FactorTypes.REVERSAL, FactorTypes.VOLATILITY, FactorTypes.VOLUME]
        lookback_periods = [5, 10, 20, 60]

        factors = engine.calculate_factors(
            data,
            factor_types=factor_types,
            lookback_periods=lookback_periods
        )

        print(f"✓ 成功計算 {len(factors)} 個Alpha因子")
        print(f"  因子類型: {[f.factor_type.value for f in factors.values()]}")

        # 顯示因子摘要
        summary = engine.get_factor_summary(factors)
        print("\n因子摘要:")
        print(summary[['factor_name', 'factor_type', 'lookback_period', 'data_points']].head(10))

        return factors

    except Exception as e:
        print(f"❌ Alpha因子計算失敗: {e}")
        return {}

def demo_technical_to_alpha_conversion(market_data):
    """演示技術指標到Alpha因子轉換"""
    print("\n🔄 技術指標到Alpha因子轉換演示")

    try:
        from alpha.alpha_factors.technical_to_alpha_converter import TechnicalIndicatorConverter, BulkTechnicalConverter

        # 創建轉換器
        converter = TechnicalIndicatorConverter()
        bulk_converter = BulkTechnicalConverter()

        # 選擇一個股票進行轉換
        symbol = '0700.HK'
        data = market_data[symbol]

        # 轉換特定的技術指標
        selected_indicators = ['RSI', 'MACD', 'Bollinger', 'ATR', 'ADX']
        alpha_factors = converter.convert_technical_to_alpha(
            data,
            indicator_names=selected_indicators,
            lookback_periods=[14, 20, 30]
        )

        print(f"✓ 成功轉換 {len(alpha_factors.columns)} 個技術指標為Alpha因子")
        print("  轉換的因子:", list(alpha_factors.columns)[:5])

        # 批量轉換所有可用指標
        all_factors = bulk_converter.convert_all_available_indicators(data)
        print(f"✓ 批量轉換完成，總計 {len(all_factors.columns)} 個因子")

        # 生成因子元數據
        metadata = bulk_converter.create_factor_metadata(all_factors)
        print(f"✓ 生成 {len(metadata)} 個因子的元數據")

        return all_factors

    except Exception as e:
        print(f"❌ 技術指標轉換失敗: {e}")
        return pd.DataFrame()

def demo_factor_validation(market_data, factors):
    """演示因子有效性檢驗"""
    print("\n✅ 因子有效性檢驗演示")

    try:
        from alpha.factor_analyzer.factor_validator import FactorValidator
        from alpha.factor_engine.alpha_factor_engine import FactorMetrics, FactorTypes

        if not factors:
            print("沒有可用的因子數據，跳過檢驗")
            return {}

        # 創建因子檢驗器
        validator = FactorValidator(risk_free_rate=0.03, confidence_level=0.95)

        # 準備價格數據
        symbol = '0700.HK'
        price_data = market_data[symbol]
        returns_data = price_data['Close'].pct_change()

        # 轉換因子數據為FactorMetrics對象
        factor_metrics_dict = {}
        for factor_name, factor_data in factors.items():
            if len(factor_data) > 30:  # 最少需要30個觀察值
                metrics = FactorMetrics(
                    factor_name=factor_name,
                    factor_type=FactorTypes.TECHNICAL,
                    factor_data=factor_data,
                    description=f"Technical factor {factor_name}",
                    calculation_method="Technical analysis",
                    lookback_period=20
                )
                factor_metrics_dict[factor_name] = metrics

        if not factor_metrics_dict:
            print("沒有足夠的因子數據進行檢驗")
            return {}

        # 檢驗因子
        validation_results = validator.validate_multiple_factors(
            factor_metrics_dict,
            price_data,
            returns_data
        )

        # 生成檢驗報告
        report = validator.generate_validation_report(validation_results)

        if not report.empty:
            print(f"✓ 成功檢驗 {len(report)} 個因子")
            print("\n因子檢驗結果 (Top 5):")
            display_cols = ['factor_name', 'ic_mean', 'sharpe_ratio', 'hit_rate', 'composite_score']
            print(report[display_cols].head().round(4))

            return report
        else:
            print("沒有有效的檢驗結果")
            return {}

    except Exception as e:
        print(f"❌ 因子檢驗失敗: {e}")
        return {}

def demo_alpha_lens_analysis(market_data, factors):
    """演示AlphaLens分析"""
    print("\n📈 AlphaLens分析演示")

    try:
        from alpha.factor_analyzer.alpha_lens_analyzer import AlphaLensAnalyzer, AlphaLensConfig

        if factors.empty:
            print("沒有可用的因子數據，跳過AlphaLens分析")
            return {}

        # 創建AlphaLens配置
        config = AlphaLensConfig(
            quantiles=5,
            periods=[1, 5, 10, 20],
            factor_name="Technical Alpha Factor"
        )

        # 創建分析器
        analyzer = AlphaLensAnalyzer(config)

        # 準備數據
        symbol = '0700.HK'
        price_data = market_data[symbol]

        # 選擇一個因子進行分析
        factor_name = factors.columns[0] if len(factors.columns) > 0 else None
        if not factor_name:
            print("沒有可用的因子進行分析")
            return {}

        factor_series = factors[factor_name].dropna()

        # 格式化因子數據為(date, asset)格式
        factor_data_formatted = factor_series.to_frame('factor')
        factor_data_formatted.index = pd.MultiIndex.from_arrays(
            [factor_data_formatted.index, [symbol] * len(factor_data_formatted)]
        )

        # 格式化價格數據
        price_data_formatted = price_data['Close'].to_frame('price')
        price_data_formatted.index = pd.MultiIndex.from_arrays(
            [price_data_formatted.index, [symbol] * len(price_data_formatted)]
        )

        # 執行Tear Sheet分析
        tear_sheet_results = analyzer.create_tear_sheet(
            factor_data_formatted,
            price_data_formatted
        )

        print(f"✓ AlphaLens分析完成")
        print("分析結果包含:")
        for key, value in tear_sheet_results.items():
            if isinstance(value, dict) and 'error' not in value:
                print(f"  - {key}: 成功")
            elif isinstance(value, dict) and 'error' in value:
                print(f"  - {key}: 失敗 ({value['error']})")
            else:
                print(f"  - {key}: {type(value)}")

        return tear_sheet_results

    except Exception as e:
        print(f"❌ AlphaLens分析失敗: {e}")
        return {}

def demo_multi_factor_model(market_data, factors):
    """演示多因子模型構建"""
    print("\n🏗️ 多因子模型構建演示")

    try:
        from alpha.factor_portfolio.factor_portfolio import FactorPortfolio, FactorModelConfig, ModelType

        if factors.empty:
            print("沒有可用的因子數據，跳過多因子模型構建")
            return {}

        # 創建配置
        config = FactorModelConfig(
            model_type=ModelType.LINEAR_REGRESSION,
            max_factors=5,
            lookback_window=60
        )

        # 創建因子投資組合構建器
        portfolio = FactorPortfolio(config)

        # 準備數據
        symbol = '0700.HK'
        price_data = market_data[symbol]
        returns = price_data['Close'].pct_change()

        # 選擇因子
        available_factors = {col: factors[[col]] for col in factors.columns[:8]}  # 使用前8個因子
        selected_factors = portfolio.select_factors(available_factors, criteria="composite")

        print(f"✓ 選中 {len(selected_factors)} 個因子: {selected_factors}")

        # 構建多因子模型
        model = portfolio.build_model(available_factors, returns)

        # 獲取模型性能
        model_performance = portfolio.get_model_performance()
        print(f"✓ 模型構建完成")
        print("模型性能:")
        for metric, value in model_performance.items():
            print(f"  {metric}: {value:.4f}")

        # 獲取因子重要性
        factor_importance = model.get_feature_importance()
        print("\n因子重要性:")
        print(factor_importance.head())

        return model

    except Exception as e:
        print(f"❌ 多因子模型構建失敗: {e}")
        return None

def demo_factor_investment_portfolio(market_data, factors):
    """演示因子投資組合管理"""
    print("\n💼 因子投資組合管理演示")

    try:
        from alpha.factor_portfolio.factor_investment_portfolio import (
            FactorInvestmentPortfolio, PortfolioConfig, PortfolioStrategy
        )

        if factors.empty:
            print("沒有可用的因子數據，跳過投資組合管理")
            return {}

        # 創建配置
        config = PortfolioConfig(
            strategy=PortfolioStrategy.TOP_QUANTILES,
            max_positions=5,
            top_quantile_threshold=0.8
        )

        # 創建投資組合管理器
        portfolio_manager = FactorInvestmentPortfolio(config)

        # 準備數據
        symbol = '0700.HK'
        price_data = market_data[symbol]
        returns_data = pd.DataFrame({symbol: price_data['Close'].pct_change()})

        # 使用因子分數選擇股票（這裡使用單股票作為演示）
        # 實際應用中應該有多個股票的因子分數
        available_stocks = [symbol]  # 簡化演示
        factor_scores = factors.iloc[:len(available_stocks)]  # 簡化處理

        if factor_scores.empty:
            print("沒有可用的因子分數")
            return {}

        # 選擇股票
        selected_stocks = portfolio_manager.select_stocks(factor_scores, available_stocks)
        print(f"✓ 選中 {len(selected_stocks)} 隻股票")

        # 分配權重
        weights = portfolio_manager.allocate_weights(selected_stocks, factor_scores, price_data)
        print(f"✓ 分配權重: {weights}")

        # 計算投資組合指標
        portfolio_metrics = portfolio_manager.calculate_portfolio_metrics(weights, returns_data)
        print(f"✓ 投資組合指標:")
        print(f"  年化回報: {portfolio_metrics.annualized_return:.2%}")
        print(f"  波動率: {portfolio_metrics.volatility:.2%}")
        print(f"  Sharpe比率: {portfolio_metrics.sharpe_ratio:.3f}")
        print(f"  最大回撤: {portfolio_metrics.max_drawdown:.2%}")

        # 生成績效報告
        performance_report = portfolio_manager.generate_performance_report()
        print(f"\n📊 投資組合績效報告:")
        print(f"  持倉數量: {performance_report['current_positions']['count']}")
        print(f"  總暴露度: {performance_report['current_positions']['total_exposure']:.2%}")

        return performance_report

    except Exception as e:
        print(f"❌ 因子投資組合管理失敗: {e}")
        return {}

def main():
    """主函數"""
    print("🎯 Alpha因子系統完整演示")
    print("=" * 60)
    print("基於機構級量化投資的專業因子分析系統")
    print("=" * 60)

    # 生成示例數據
    market_data = generate_sample_market_data()

    # 1. Alpha因子計算引擎演示
    factors = demo_alpha_factor_engine(market_data)

    # 2. 技術指標到Alpha因子轉換演示
    all_factors = demo_technical_to_alpha_conversion(market_data)

    # 合併因子數據
    if not factors.empty and not all_factors.empty:
        combined_factors = pd.concat([factors, all_factors], axis=1)
    elif not all_factors.empty:
        combined_factors = all_factors
    else:
        combined_factors = factors

    # 3. 因子有效性檢驗演示
    validation_report = demo_factor_validation(market_data, combined_factors)

    # 4. AlphaLens分析演示
    alpha_lens_results = demo_alpha_lens_analysis(market_data, combined_factors)

    # 5. 多因子模型構建演示
    factor_model = demo_multi_factor_model(market_data, combined_factors)

    # 6. 因子投資組合管理演示
    portfolio_report = demo_factor_investment_portfolio(market_data, combined_factors)

    print("\n" + "=" * 60)
    print("🎉 Alpha因子系統演示完成！")
    print("\n📚 主要功能總結:")
    print("  ✅ Alpha因子計算引擎 - 支持多種因子類型")
    print("  ✅ 技術指標轉換 - 477種技術指標轉Alpha因子")
    print("  ✅ 因子有效性檢驗 - IC分析和統計檢驗")
    print("  ✅ AlphaLens分析 - 機構級因子分析")
    print("  ✅ 多因子模型構建 - 機器學習和統計模型")
    print("  ✅ 因子投資組合管理 - 專業級組合管理")

    print("\n🚀 系統特點:")
    print("  🔬 機構級Alpha因子分析能力")
    print("  📊 與現有477種技術指標無縫集成")
    print("  🎯 專業級風險管理和績效分析")
    print("  ⚡ 高性能計算和優化算法")
    print("  🛡️ 完整的驗證和回測框架")

if __name__ == '__main__':
    main()