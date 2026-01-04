"""
经济数据策略使用示例

此示例展示了如何使用基于香港经济指标的基本面策略进行交易。
包括 HIBOR、GDP、访港旅客人数、PMI 和失业率等指标。
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 导入策略
from src.strategies import (
    HIBORStrategy,
    GDPGrowthStrategy,
    VisitorArrivalStrategy,
    PMIStrategy,
    UnemploymentStrategy,
    CompositeEconomicStrategy,
    get_economic_data_adapter,
    CSVDataLoader
)

# 导入基础回测模块
from src.backtest.backtest import Backtest
from src.risk.position_sizing import PositionSizer


def create_sample_data_with_economic_indicators():
    """创建包含经济指标的示例数据"""
    dates = pd.date_range(start="2020-01-01", end="2023-12-31", freq="D")

    # 创建股价数据（模拟香港恒生指数）
    np.random.seed(42)
    trend = np.linspace(25000, 17000, len(dates))  # 下跌趋势
    cycles = 1000 * np.sin(np.linspace(0, 4*np.pi, len(dates)))  # 周期性波动
    noise = np.random.randn(len(dates)) * 300
    prices = trend + cycles + noise
    prices = np.maximum(prices, 1000)  # 确保价格为正

    # 创建经济指标数据
    # HIBOR 利率 (1-8%)
    hibor_base = 4.0
    hibor_cycles = 2.0 * np.sin(np.linspace(0, 6*np.pi, len(dates)))
    hibor_noise = np.random.randn(len(dates)) * 0.3
    hibor_rates = hibor_base + hibor_cycles + hibor_noise
    hibor_rates = np.clip(hibor_rates, 1.0, 8.0)

    # GDP 增长率 (-2% 到 6%)
    gdp_base = 2.5
    gdp_cycles = 2.0 * np.sin(np.linspace(0, 2*np.pi, len(dates)/90))
    gdp_growth = np.repeat(gdp_base + gdp_cycles, 90)[:len(dates)]
    gdp_growth += np.random.randn(len(dates)) * 0.8
    gdp_growth = np.clip(gdp_growth, -2.0, 6.0)

    # 访港旅客人数（百万人次）
    # 模拟疫情的影响
    visitors_base = 5.0  # 500万/月
    pre_covid = np.zeros(len(dates))
    covid_impact = np.zeros(len(dates))
    post_covid = np.zeros(len(dates))

    # 疫情前正常增长
    pre_covid_mask = dates < datetime(2020, 2, 1)
    pre_covid[pre_covid_mask] = visitors_base * (1 + np.arange(np.sum(pre_covid_mask)) * 0.01)

    # 疫情期间大幅下降
    covid_mask = (dates >= datetime(2020, 2, 1)) & (dates < datetime(2023, 1, 1))
    covid_impact[covid_mask] = visitors_base * 0.1  # 只有10%

    # 疫情后恢复
    post_covid_mask = dates >= datetime(2023, 1, 1)
    post_covid[post_covid_mask] = visitors_base * (1 + np.arange(np.sum(post_covid_mask)) * 0.02)

    visitors = pre_covid + covid_impact + post_covid
    visitors += np.random.randn(len(dates)) * 0.5
    visitors = np.maximum(visitors, 0.1) * 1e6  # 转换为实际数字

    # PMI 数据 (30-70)
    pmi_base = 50
    pmi_cycles = 10 * np.sin(np.linspace(0, 4*np.pi, len(dates)/30))
    pmi_manufacturing = np.repeat(pmi_base + pmi_cycles, 30)[:len(dates)]
    pmi_manufacturing += np.random.randn(len(dates)) * 3
    pmi_manufacturing = np.clip(pmi_manufacturing, 30, 70)

    # 失业率 (2.0% - 7.5%)
    unemployment_base = 3.5
    unemployment_trend = np.linspace(0, 2.0, len(dates))
    unemployment_cycles = 1.5 * np.sin(np.linspace(0, 3*np.pi, len(dates)))
    unemployment = unemployment_base + unemployment_trend + unemployment_cycles
    unemployment += np.random.randn(len(dates)) * 0.4
    unemployment = np.clip(unemployment, 2.0, 7.5)

    # 创建 DataFrame
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(len(dates)) * 0.002),
        'high': prices * (1 + np.abs(np.random.randn(len(dates)) * 0.015)),
        'low': prices * (1 - np.abs(np.random.randn(len(dates)) * 0.015)),
        'close': prices,
        'volume': np.random.randint(100000, 500000, len(dates)),

        # 经济指标
        'hibor_rate': hibor_rates,
        'gdp_growth': gdp_growth,
        'visitor_arrivals': visitors,
        'pmi_manufacturing': pmi_manufacturing,
        'unemployment_rate': unemployment
    }, index=dates)

    return data


def example_hibor_strategy():
    """HIBOR 策略示例"""
    print("\n=== HIBOR 策略示例 ===")
    print("基于香港银行同业拆借利率的策略，当利率变化时产生交易信号")

    # 创建数据
    data = create_sample_data_with_economic_indicators()

    # 初始化策略
    strategy = HIBORStrategy(
        lookback_period=20,  # 20天回看期
        rate_threshold_high=5.0,  # 高利率阈值
        rate_threshold_low=2.5    # 低利率阈值
    )

    # 生成信号
    signals = strategy.generate_signals(data)

    # 分析信号
    signal_counts = signals.value_counts()
    print(f"\n信号分布:")
    print(f"买入信号 (1): {signal_counts.get(1, 0)} 次")
    print(f"卖出信号 (-1): {signal_counts.get(-1, 0)} 次")
    print(f"持有信号 (0): {signal_counts.get(0, 0)} 次")

    # 计算策略表现
    returns = data['close'].pct_change()
    strategy_returns = returns * signals.shift(1)  # 使用前一日的信号

    print(f"\n策略表现:")
    print(f"总收益率: {(1 + strategy_returns).prod() - 1:.2%}")
    print(f"年化收益率: {(1 + strategy_returns).prod()**(252/len(strategy_returns)) - 1:.2%}")
    print(f"最大回撤: {(strategy_returns.cumsum() - strategy_returns.cumsum().cummax()).min():.2%}")

    return signals


def example_gdp_strategy():
    """GDP 增长策略示例"""
    print("\n=== GDP 增长策略示例 ===")
    print("基于 GDP 增长率识别经济周期，在不同周期采取不同策略")

    data = create_sample_data_with_economic_indicators()

    # 初始化策略
    strategy = GDPGrowthStrategy(
        gdp_threshold_high=4.0,  # 高增长阈值
        gdp_threshold_low=1.0    # 低增长阈值
    )

    # 识别经济周期
    cycles = strategy.identify_economic_cycle(data)

    # 分析周期
    cycle_counts = cycles.value_counts()
    print(f"\n经济周期分布:")
    print(f"扩张期: {cycle_counts.get('expansion', 0)} 天")
    print(f"衰退期: {cycle_counts.get('recession', 0)} 天")
    print(f"中性期: {cycle_counts.get('neutral', 0)} 天")

    # 生成交易信号
    signals = strategy.generate_signals(data)

    return signals


def example_visitor_strategy():
    """访港旅客策略示例"""
    print("\n=== 访港旅客策略示例 ===")
    print("基于访港旅客人数变化，预测旅游相关股票走势")

    data = create_sample_data_with_economic_indicators()

    # 初始化策略
    strategy = VisitorArrivalStrategy(
        trend_period=90,          # 90天趋势期
        change_threshold=0.05     # 5%变化阈值
    )

    # 生成信号
    signals = strategy.generate_signals(data)

    # 分析游客数据与股价的关系
    visitors_change = data['visitor_arrivals'].pct_change(30)  # 30天变化率
    price_change = data['close'].pct_change(30)

    correlation = visitors_change.corr(price_change)
    print(f"\n游客数量变化与股价变化的相关性: {correlation:.3f}")

    return signals


def example_pmi_strategy():
    """PMI 策略示例"""
    print("\n=== PMI 策略示例 ===")
    print("基于采购经理人指数，预测制造业和服务业表现")

    data = create_sample_data_with_economic_indicators()

    # 初始化策略
    strategy = PMIStrategy(
        expansion_threshold=50.0,  # 扩张阈值
        contraction_threshold=45.0  # 收缩阈值
    )

    # 生成信号
    signals = strategy.generate_signals(data)

    # 分析 PMI 水平
    pmi_levels = strategy.interpret_pmi_level(data)
    level_counts = pmi_levels.value_counts()
    print(f"\nPMI 水平分布:")
    print(f"扩张: {level_counts.get('expansion', 0)} 天")
    print(f"收缩: {level_counts.get('contraction', 0)} 天")
    print(f"中性: {level_counts.get('neutral', 0)} 天")

    return signals


def example_composite_strategy():
    """综合经济策略示例"""
    print("\n=== 综合经济策略示例 ===")
    print("结合多个经济指标，生成更可靠的交易信号")

    data = create_sample_data_with_economic_indicators()

    # 初始化综合策略
    strategy = CompositeEconomicStrategy(
        hibor_weight=0.25,        # HIBOR 权重
        gdp_weight=0.25,          # GDP 权重
        pmi_weight=0.25,          # PMI 权重
        unemployment_weight=0.25  # 失业率权重
    )

    # 生成综合信号
    signals = strategy.generate_signals(data)

    # 分析信号强度分布
    composite_values = strategy.calculate_composite_signal(data)
    print(f"\n综合信号强度统计:")
    print(f"最强买入 (>0.5): {(composite_values > 0.5).sum()} 天")
    print(f"温和买入 (0-0.5): {((composite_values > 0) & (composite_values <= 0.5)).sum()} 天")
    print(f"温和卖出 (-0.5-0): {((composite_values >= -0.5) & (composite_values < 0)).sum()} 天")
    print(f"最强卖出 (<-0.5): {(composite_values < -0.5).sum()} 天")

    return signals


def run_backtest_with_economic_strategy(strategy_name, strategy_class, **kwargs):
    """运行基于经济指标的策略回测"""
    print(f"\n=== {strategy_name} 回测 ===")

    # 创建数据
    data = create_sample_data_with_economic_indicators()

    # 初始化策略
    strategy = strategy_class(**kwargs)

    # 创建回测实例
    backtest = Backtest(
        data=data,
        strategy=strategy,
        position_sizer=PositionSizer(method='fixed', size=0.1),  # 固定10%仓位
        commission=0.001,  # 0.1% 手续费
        slippage=0.0005    # 0.05% 滑点
    )

    # 运行回测
    result = backtest.run()

    # 显示结果
    print(f"\n回测结果:")
    print(f"总收益率: {result['total_return']:.2%}")
    print(f"年化收益率: {result['annualized_return']:.2%}")
    print(f"最大回撤: {result['max_drawdown']:.2%}")
    print(f"夏普比率: {result['sharpe_ratio']:.3f}")
    print(f"盈亏比: {result['profit_loss_ratio']:.3f}")
    print(f"交易次数: {result['total_trades']}")

    return result


def main():
    """主函数"""
    print("经济数据策略示例")
    print("=" * 50)
    print("本示例展示了如何使用基于香港经济指标的策略")
    print("包括 HIBOR、GDP、访港旅客、PMI 和失业率等指标")

    # 运行各个策略示例
    hibor_signals = example_hibor_strategy()
    gdp_signals = example_gdp_strategy()
    visitor_signals = example_visitor_strategy()
    pmi_signals = example_pmi_strategy()
    composite_signals = example_composite_strategy()

    # 运行回测
    print("\n" + "=" * 50)
    print("策略回测对比")

    strategies_to_test = [
        ("HIBOR 策略", HIBORStrategy, {}),
        ("GDP 增长策略", GDPGrowthStrategy, {}),
        ("访港旅客策略", VisitorArrivalStrategy, {}),
        ("PMI 策略", PMIStrategy, {}),
        ("综合经济策略", CompositeEconomicStrategy, {
            'hibor_weight': 0.25,
            'gdp_weight': 0.25,
            'pmi_weight': 0.25,
            'unemployment_weight': 0.25
        })
    ]

    results = []
    for name, strategy_class, kwargs in strategies_to_test:
        try:
            result = run_backtest_with_economic_strategy(name, strategy_class, **kwargs)
            results.append((name, result))
        except Exception as e:
            print(f"\n{name} 回测失败: {e}")

    # 策略对比总结
    if results:
        print("\n" + "=" * 50)
        print("策略对比总结")
        print("-" * 50)
        print(f"{'策略名称':<20} {'总收益率':<12} {'最大回撤':<12} {'夏普比率':<10}")
        print("-" * 50)

        for name, result in results:
            print(f"{name:<20} {result['total_return']:<12.2%} {result['max_drawdown']:<12.2%} {result['sharpe_ratio']:<10.3f}")

    print("\n" + "=" * 50)
    print("提示：")
    print("1. 这些策略适合长期投资，不适合短期交易")
    print("2. 经济数据通常有滞后性，需要注意时效性")
    print("3. 建议结合技术指标使用，提高信号准确性")
    print("4. 不同时期市场对经济数据的敏感度不同")


if __name__ == "__main__":
    main()