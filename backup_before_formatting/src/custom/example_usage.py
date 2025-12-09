"""
策略模板系统使用示例
演示如何使用策略模板引擎、模板管理器和策略测试器
"""

import json
from datetime import datetime, timedelta

from strategy_template import (
    StrategyNode,
    StrategyTemplateEngine,
    TemplateStatus,
    TemplateType,
    TemplateVariable,
    create_predefined_templates,
)
from strategy_tester import StrategyTester, TestConfig, TestType
from template_manager import ExportFormat, SortField, SortOrder, TemplateManager


def example_1_create_template():
    """示例1: 创建自定义策略模板"""
    print("\n=== 示例1: 创建自定义策略模板 ===")

    # 初始化模板引擎
    engine = StrategyTemplateEngine()

    # 定义模板变量
    variables = [
        TemplateVariable(
            name="fast_period",
            type="int",
            default=12,
            description="快线周期",
            required=True,
        ),
        TemplateVariable(
            name="slow_period",
            type="int",
            default=26,
            description="慢线周期",
            required=True,
        ),
        TemplateVariable(
            name="signal_period",
            type="int",
            default=9,
            description="信号线周期",
            required=True,
        ),
    ]

    # 定义策略节点
    nodes = [
        StrategyNode(
            id="node_1",
            type="indicator",
            name="MACD指标",
            parameters={"fast": 12, "slow": 26, "signal": 9},
        ),
        StrategyNode(
            id="node_2", type="signal", name="金叉信号", parameters={"direction": "up"}
        ),
    ]

    # 创建模板
    template_id = engine.create_template(
        name="MACD金叉策略",
        template_type=TemplateType.SIGNAL,
        description="基于MACD金叉的买入信号策略",
        author="系统",
        variables=variables,
        nodes=nodes,
        code_template="""
def macd_cross_strategy(data, fast_period={{ fast_period }}, slow_period={{ slow_period }}, signal_period={{ signal_period }}):
    '''MACD金叉策略'''
    import pandas as pd

    # 计算MACD
    exp1 = data['close'].ewm(span=fast_period).mean()
    exp2 = data['close'].ewm(span=slow_period).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=signal_period).mean()

    # 生成信号
    signals = []
    for i in range(1, len(data)):
        if macd.iloc[i] > signal.iloc[i] and macd.iloc[i - 1] <= signal.iloc[i - 1]:
            signals.append(('BUY', data.index[i], data['close'].iloc[i]))
        elif macd.iloc[i] < signal.iloc[i] and macd.iloc[i - 1] >= signal.iloc[i - 1]:
            signals.append(('SELL', data.index[i], data['close'].iloc[i]))

    return signals
        """,
        metadata={
            "category": "趋势策略",
            "tags": ["MACD", "金叉", "趋势"],
            "risk_level": "medium",
        },
    )

    print(f"模板创建成功，ID: {template_id}")

    # 实例化模板
    instantiated = engine.instantiate_template(
        template_id, {"fast_period": 10, "slow_period": 30, "signal_period": 8}
    )

    print("模板实例化成功")
    print(f"生成代码:\n{instantiated.get('generated_code', '')[:200]}...")

    return template_id


def example_2_template_management():
    """示例2: 模板管理功能"""
    print("\n=== 示例2: 模板管理功能 ===")

    engine = StrategyTemplateEngine()
    manager = TemplateManager(engine)

    # 创建几个示例模板
    ma_template_id = engine.create_template(
        name="简单移动平均",
        template_type=TemplateType.FULL_STRATEGY,
        description="SMA策略",
        author="用户A",
    )

    rsi_template_id = engine.create_template(
        name="RSI反转",
        template_type=TemplateType.SIGNAL,
        description="RSI超买超卖",
        author="用户B",
    )

    print(f"创建了 {len(engine.templates)} 个模板")

    # 搜索模板
    print("\n--- 搜索模板 ---")
    results = manager.search_templates(
        query="移动平均", sort_by=SortField.NAME, sort_order=SortOrder.ASC
    )
    print(f"搜索结果: {len(results)} 个模板")

    # 导出模板
    print("\n--- 导出模板 ---")
    export_path = manager.export_template(ma_template_id, ExportFormat.JSON)
    print(f"模板已导出到: {export_path}")

    # 获取统计信息
    print("\n--- 统计信息 ---")
    stats = manager.get_template_analytics()
    print(f"总模板数: {stats['summary']['total_templates']}")
    print(f"按类型分布: {stats['summary']['by_type']}")
    print(f"按分类分布: {stats['by_category']}")

    return ma_template_id, rsi_template_id


def example_3_backtest():
    """示例3: 策略回测"""
    print("\n=== 示例3: 策略回测 ===")

    tester = StrategyTester()

    # 定义回测配置
    config = TestConfig(
        strategy_code="""
# 简单的双均线策略
def strategy(data):
    signals = []
    data['MA5'] = data['close'].rolling(window=5).mean()
    data['MA20'] = data['close'].rolling(window=20).mean()

    position = 0
    for i in range(len(data)):
        if data['MA5'].iloc[i] > data['MA20'].iloc[i] and position == 0:
            signals.append(('BUY', data.index[i], data['close'].iloc[i]))
            position = 1
        elif data['MA5'].iloc[i] < data['MA20'].iloc[i] and position == 1:
            signals.append(('SELL', data.index[i], data['close'].iloc[i]))
            position = 0

    return signals
        """,
        symbol="0700.HK",
        start_date="2023 - 01 - 01",
        end_date="2023 - 12 - 31",
        initial_capital=100000.0,
    )

    # 运行回测
    print("开始回测...")
    result = tester.run_backtest(config)

    # 输出结果
    print("\n回测完成!")
    print(f"测试ID: {result.test_id}")
    print(f"总收益率: {result.total_return:.2%}")
    print(f"年化收益率: {result.annualized_return:.2%}")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"胜率: {result.win_rate:.2%}")
    print(f"交易次数: {result.total_trades}")

    # 生成报告
    report_path = tester.generate_report(result.test_id)
    print(f"\n报告已生成: {report_path}")

    return result.test_id


def example_4_walk_forward():
    """示例4: 前进分析"""
    print("\n=== 示例4: 前进分析 ===")

    tester = StrategyTester()

    config = TestConfig(
        strategy_code="""
def strategy(data):
    signals = []
    data['MA10'] = data['close'].rolling(window=10).mean()

    for i in range(len(data)):
        if i > 0 and data['MA10'].iloc[i] > data['MA10'].iloc[i - 1]:
            signals.append(('BUY', data.index[i], data['close'].iloc[i]))
        elif i > 0 and data['MA10'].iloc[i] < data['MA10'].iloc[i - 1]:
            signals.append(('SELL', data.index[i], data['close'].iloc[i]))

    return signals
        """,
        symbol="0388.HK",
        start_date="2022 - 01 - 01",
        end_date="2023 - 12 - 31",
        initial_capital=100000.0,
    )

    print("开始前进分析...")
    results = tester.run_walk_forward(
        config,
        train_period=180,  # 6个月训练
        test_period=30,  # 1个月测试
        step=15,  # 步长15天
    )

    print(f"\n前进分析完成! 共进行了 {len(results)} 轮测试")
    print("\n各轮结果:")
    for i, result in enumerate(results, 1):
        print(
            f"第 {i} 轮: 收益率={result.total_return:.2%}, 夏普={result.sharpe_ratio:.2f}"
        )

    return [r.test_id for r in results]


def example_5_monte_carlo():
    """示例5: 蒙特卡洛模拟"""
    print("\n=== 示例5: 蒙特卡洛模拟 ===")

    tester = StrategyTester()

    config = TestConfig(
        strategy_code="",
        symbol="0700.HK",
        start_date="2023 - 01 - 01",
        end_date="2023 - 12 - 31",
        initial_capital=100000.0,
    )

    print("开始蒙特卡洛模拟...")
    result = tester.run_monte_carlo(config, num_simulations=500)

    print("\n模拟完成!")
    print(f"模拟次数: {result['num_simulations']}")
    print(f"平均收益率: {result['mean_return']:.2%}")
    print(f"收益率标准差: {result['std_return']:.2%}")
    print(f"95% VaR: {result['var_95']:.2%}")
    print(f"99% VaR: {result['var_99']:.2%}")
    print(f"正收益概率: {result['prob_positive']:.2%}")
    print(
        f"95 % 置信区间: [{result['confidence_interval'][0]:.2%}, {result['confidence_interval'][1]:.2%}]"
    )

    return result


def example_6_predefined_templates():
    """示例6: 使用预定义模板"""
    print("\n=== 示例6: 使用预定义模板 ===")

    engine = StrategyTemplateEngine()

    # 创建预定义模板
    template_ids = create_predefined_templates(engine)

    print(f"已创建 {len(template_ids)} 个预定义模板")

    # 列出所有模板
    templates = engine.list_templates()

    print("\n所有模板:")
    for template in templates:
        print(
            f"- {template.name} (类型: {template.type.value}, 作者: {template.author})"
        )
        print(f"  描述: {template.description}")

        # 实例化示例
        if template.type == TemplateType.FULL_STRATEGY and template.variables:
            var_dict = {v.name: v.default for v in template.variables}
            instantiated = engine.instantiate_template(template.id, var_dict)
            print(f"  示例代码:\n{instantiated.get('generated_code', '')[:150]}...")
            print()


def main():
    """主函数 - 运行所有示例"""
    print("=" * 60)
    print("策略模板系统使用示例")
    print("=" * 60)

    try:
        # 示例1: 创建模板
        template_id = example_1_create_template()

        # 示例2: 模板管理
        ma_id, rsi_id = example_2_template_management()

        # 示例3: 回测
        test_id = example_3_backtest()

        # 示例4: 前进分析
        walk_forward_ids = example_4_walk_forward()

        # 示例5: 蒙特卡洛
        mc_result = example_5_monte_carlo()

        # 示例6: 预定义模板
        example_6_predefined_templates()

        print("\n" + "=" * 60)
        print("所有示例运行完成!")
        print("=" * 60)

        print("\n创建的资源:")
        print(f"- 模板ID: {template_id}, {ma_id}, {rsi_id}")
        print(f"- 回测ID: {test_id}")
        print(f"- 前进分析ID: {', '.join(walk_forward_ids)}")
        print(f"- 蒙特卡洛: {mc_result['num_simulations']} 次模拟")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
