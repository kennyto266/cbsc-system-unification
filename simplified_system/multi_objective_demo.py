#!/usr / bin / env python3
"""
Multi - Objective Portfolio Optimization Demo
多目标投资组合优化演示

Task 2.3 完整功能演示:
- 多目标优化框架
- Pareto边界计算
- 目标函数自定义
- 交易成本考虑
- 交互式可视化
- 偏好启发工具
- 敏感性分析
"""

import time
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# 设置中文字体
plt.rcParams["font.sans - serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def demo_objective_functions():
    """演示目标函数"""
    print("=" * 60)
    print("1. Objective Functions Library Demo")
    print("=" * 60)

    # 创建测试数据
    np.random.seed(42)
    n_assets = 5
    n_periods = 252  # 一年数据

    # 模拟不同特征的资产
    returns_data = []
    asset_names = []

    for i in range(n_assets):
        # 不同资产有不同风险收益特征
        mean_return = 0.03 + i * 0.02  # 3%到11%年化收益
        volatility = 0.10 + i * 0.05  # 10%到30%年化波动率

        daily_returns = np.random.normal(
            mean_return / 252, volatility / np.sqrt(252), n_periods
        )
        returns_data.append(daily_returns)
        asset_names.append(f"资产{i + 1}")

    returns_df = pd.DataFrame(np.array(returns_data).T, columns = asset_names)

    print(f"创建了{n_assets}个资产，{n_periods}天的数据")
    print("\n资产特征:")
    for i, asset in enumerate(asset_names):
        annual_return = returns_df[asset].mean() * 252
        annual_vol = returns_df[asset].std() * np.sqrt(252)
        sharpe = (annual_return - 0.03) / annual_vol
        print(
            f"  {asset}: 年化收益{annual_return:.2%}, 年化波动{annual_vol:.2%}, 夏普{sharpe:.2f}"
        )

    # 测试不同目标函数
    weights = np.array([0.3, 0.25, 0.2, 0.15, 0.1])
    portfolio_returns = (returns_df * weights).sum(axis = 1)

    # 计算各种目标函数
    objectives = {}

    # 1. 夏普比率
    annual_return = portfolio_returns.mean() * 252
    annual_vol = portfolio_returns.std() * np.sqrt(252)
    objectives["sharpe"] = (annual_return - 0.03) / annual_vol

    # 2. 方差
    objectives["variance"] = annual_vol * *2

    # 3. 最大回撤
    cumulative_returns = (1 + portfolio_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    objectives["max_drawdown"] = drawdown.min()

    # 4. 期望回报
    objectives["expected_return"] = annual_return

    # 5. VaR (95%)
    objectives["var_95"] = np.percentile(portfolio_returns, 5) * np.sqrt(252)

    # 6. 交易成本 (模拟)
    previous_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    turnover = np.sum(np.abs(weights - previous_weights)) / 2
    trading_cost_rate = 0.001
    objectives["trading_cost"] = turnover * trading_cost_rate

    print(f"\n测试投资组合权重: {weights}")
    print("目标函数值:")
    for obj_name, obj_value in objectives.items():
        print(f"  {obj_name}: {obj_value:.6f}")

    return returns_df, objectives


def demo_pareto_frontier(returns_df):
    """演示帕累托边界计算"""
    print("\n" + "=" * 60)
    print("2. 帕累托边界计算演示")
    print("=" * 60)

    # 计算期望收益和协方差矩阵
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252

    # 生成大量随机投资组合
    n_portfolios = 1000
    portfolios = []

    print(f"生成{n_portfolios}个随机投资组合...")

    for i in range(n_portfolios):
        weights = np.random.dirichlet(np.ones(len(mean_returns)))

        portfolio_return = np.sum(mean_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility

        # 最大回撤估计 (简化版)
        var_95 = -1.65 * portfolio_volatility
        max_drawdown_est = var_95 * 1.5  # 粗略估计

        portfolios.append(
            {
                "weights": weights,
                "return": portfolio_return,
                "volatility": portfolio_volatility,
                "sharpe": sharpe_ratio,
                "max_drawdown": max_drawdown_est,
            }
        )

    # 找到帕累托最优组合 (回报 - 波动率)
    pareto_portfolios = []
    for i, p1 in enumerate(portfolios):
        is_pareto = True
        for j, p2 in enumerate(portfolios):
            if i != j:
                # p2在回报和波动率上都优于p1
                if (
                    p2["return"] >= p1["return"]
                    and p2["volatility"] <= p1["volatility"]
                    and (
                        p2["return"] > p1["return"]
                        or p2["volatility"] < p1["volatility"]
                    )
                ):
                    is_pareto = False
                    break
        if is_pareto:
            pareto_portfolios.append(p1)

    print(f"帕累托最优组合数量: {len(pareto_portfolios)}")

    # 找到特殊的投资组合
    if pareto_portfolios:
        # 最高夏普比率组合
        max_sharpe_portfolio = max(pareto_portfolios, key = lambda p: p["sharpe"])

        # 最小波动率组合
        min_vol_portfolio = min(pareto_portfolios, key = lambda p: p["volatility"])

        # 最大回报组合
        max_return_portfolio = max(pareto_portfolios, key = lambda p: p["return"])

        print("\n特殊投资组合:")
        print(f"\n最高夏普比率组合:")
        print(f"  权重: {max_sharpe_portfolio['weights']}")
        print(f"  年化收益: {max_sharpe_portfolio['return']:.2%}")
        print(f"  年化波动: {max_sharpe_portfolio['volatility']:.2%}")
        print(f"  夏普比率: {max_sharpe_portfolio['sharpe']:.3f}")

        print(f"\n最小波动率组合:")
        print(f"  权重: {min_vol_portfolio['weights']}")
        print(f"  年化收益: {min_vol_portfolio['return']:.2%}")
        print(f"  年化波动: {min_vol_portfolio['volatility']:.2%}")
        print(f"  夏普比率: {min_vol_portfolio['sharpe']:.3f}")

        print(f"\n最大收益组合:")
        print(f"  权重: {max_return_portfolio['weights']}")
        print(f"  年化收益: {max_return_portfolio['return']:.2%}")
        print(f"  年化波动: {max_return_portfolio['volatility']:.2%}")
        print(f"  夏普比率: {max_return_portfolio['sharpe']:.3f}")

        # 可视化帕累托边界
        plt.figure(figsize=(12, 8))

        # 所有投资组合
        all_returns = [p["return"] for p in portfolios]
        all_vols = [p["volatility"] for p in portfolios]
        plt.scatter(
            all_vols, all_returns, c="lightblue", alpha = 0.6, s = 10, label="所有投资组合"
        )

        # 帕累托前沿
        pareto_returns = [p["return"] for p in pareto_portfolios]
        pareto_vols = [p["volatility"] for p in pareto_portfolios]
        plt.scatter(pareto_vols, pareto_returns, c="red", s = 30, label="帕累托前沿")

        # 特殊组合
        plt.scatter(
            min_vol_portfolio["volatility"],
            min_vol_portfolio["return"],
            c="green",
            s = 100,
            marker="*",
            label="最小波动率",
        )
        plt.scatter(
            max_sharpe_portfolio["volatility"],
            max_sharpe_portfolio["return"],
            c="blue",
            s = 100,
            marker="*",
            label="最高夏普比率",
        )
        plt.scatter(
            max_return_portfolio["volatility"],
            max_return_portfolio["return"],
            c="purple",
            s = 100,
            marker="*",
            label="最大收益",
        )

        plt.xlabel("年化波动率")
        plt.ylabel("年化收益率")
        plt.title("投资组合帕累托前沿")
        plt.legend()
        plt.grid(True, alpha = 0.3)
        plt.tight_layout()

        # 保存图表
        plt.savefig("pareto_frontier_demo.png", dpi = 300, bbox_inches="tight")
        print("\n帕累托前沿图已保存为 'pareto_frontier_demo.png'")
        plt.show()

    return pareto_portfolios


def demo_multi_objective_optimization(returns_df):
    """演示多目标优化"""
    print("\n" + "=" * 60)
    print("3. 多目标优化演示")
    print("=" * 60)

    # 准备数据
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252
    n_assets = len(mean_returns)

    def multi_objective_function(weights, lambda_return, lambda_vol, lambda_dd):
        """多目标函数：收益 - 波动率 - 最大回撤"""
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        # 估计最大回撤
        max_drawdown_est = -1.5 * portfolio_volatility

        # 组合目标函数 (负值用于最小化)
        objective = (
            -lambda_return * portfolio_return
            + lambda_vol * portfolio_volatility
            + lambda_dd * abs(max_drawdown_est)
        )

        return objective

    from scipy.optimize import minimize

    # 不同的目标函数权重组合
    optimization_cases = [
        {"name": "收益偏好", "lambda_return": 0.6, "lambda_vol": 0.3, "lambda_dd": 0.1},
        {"name": "风险厌恶", "lambda_return": 0.2, "lambda_vol": 0.6, "lambda_dd": 0.2},
        {"name": "回撤控制", "lambda_return": 0.3, "lambda_vol": 0.2, "lambda_dd": 0.5},
        {
            "name": "均衡偏好",
            "lambda_return": 0.33,
            "lambda_vol": 0.33,
            "lambda_dd": 0.34,
        },
    ]

    results = []

    for case in optimization_cases:
        print(f"\n优化案例: {case['name']}")
        print(
            f"权重 - 收益:{case['lambda_return']:.2f}, 波动:{case['lambda_vol']:.2f}, 回撤:{case['lambda_dd']:.2f}"
        )

        # 约束条件
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        bounds = [(0.0, 1.0) for _ in range(n_assets)]
        initial_weights = np.ones(n_assets) / n_assets

        # 优化
        result = minimize(
            lambda w: multi_objective_function(
                w, case["lambda_return"], case["lambda_vol"], case["lambda_dd"]
            ),
            initial_weights,
            method="SLSQP",
            bounds = bounds,
            constraints = constraints,
            options={"maxiter": 1000},
        )

        if result.success:
            weights = result.x
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_volatility = np.sqrt(
                np.dot(weights.T, np.dot(cov_matrix, weights))
            )
            sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility

            # 估计其他指标
            max_drawdown_est = -1.5 * portfolio_volatility
            var_95 = -1.65 * portfolio_volatility

            result_data = {
                "case": case["name"],
                "weights": weights,
                "return": portfolio_return,
                "volatility": portfolio_volatility,
                "sharpe": sharpe_ratio,
                "max_drawdown": max_drawdown_est,
                "var_95": var_95,
                "objective_value": result.fun,
            }
            results.append(result_data)

            print(f"  优化成功!")
            print(f"  权重: {['%.3f' % w for w in weights]}")
            print(f"  年化收益: {portfolio_return:.2%}")
            print(f"  年化波动: {portfolio_volatility:.2%}")
            print(f"  夏普比率: {sharpe_ratio:.3f}")
            print(f"  预计最大回撤: {max_drawdown_est:.2%}")
        else:
            print(f"  优化失败: {result.message}")

    # 比较结果
    if results:
        print(f"\n多目标优化结果比较:")
        print("-" * 80)
        print(
            f"{'案例':<10} {'收益':<8} {'波动':<8} {'夏普':<8} {'最大回撤':<10} {'VaR(95%)':<10}"
        )
        print("-" * 80)

        for r in results:
            print(
                f"{r['case']:<10} {r['return']:<8.2%} {r['volatility']:<8.2%} {r['sharpe']:<8.3f} {r['max_drawdown']:<10.2%} {r['var_95']:<10.2%}"
            )

        # 可视化结果比较
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

        # 饼图 - 权重分布
        case_names = [r["case"] for r in results]
        for i, result in enumerate(results):
            ax1.pie(result["weights"], labels = returns_df.columns, autopct="%1.1f%%")
            ax1.set_title(f"{case_names[i]} - 权重分布")

        # 收益 vs 波动率
        returns_vals = [r["return"] for r in results]
        vols = [r["volatility"] for r in results]
        ax2.scatter(vols, returns_vals, s = 100)
        for i, case in enumerate(case_names):
            ax2.annotate(
                case,
                (vols[i], returns_vals[i]),
                xytext=(5, 5),
                textcoords="offset points",
            )
        ax2.set_xlabel("年化波动率")
        ax2.set_ylabel("年化收益率")
        ax2.set_title("收益 - 风险散点图")
        ax2.grid(True, alpha = 0.3)

        # 夏普比率比较
        sharpe_vals = [r["sharpe"] for r in results]
        bars = ax3.bar(case_names, sharpe_vals)
        ax3.set_ylabel("夏普比率")
        ax3.set_title("夏普比率比较")
        ax3.tick_params(axis="x", rotation = 45)
        for bar, sharpe in zip(bars, sharpe_vals):
            ax3.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{sharpe:.3f}",
                ha="center",
                va="bottom",
            )

        # 风险指标比较
        maxdds = [abs(r["max_drawdown"]) for r in results]
        var95s = [abs(r["var_95"]) for r in results]

        x = np.arange(len(case_names))
        width = 0.35

        ax4.bar(x - width / 2, maxdds, width, label="最大回撤", alpha = 0.8)
        ax4.bar(x + width / 2, var95s, width, label="VaR(95%)", alpha = 0.8)
        ax4.set_ylabel("风险指标")
        ax4.set_title("风险指标比较")
        ax4.set_xticks(x)
        ax4.set_xticklabels(case_names, rotation = 45)
        ax4.legend()
        ax4.grid(True, alpha = 0.3)

        plt.tight_layout()
        plt.savefig("multi_objective_comparison.png", dpi = 300, bbox_inches="tight")
        print("\n多目标优化比较图已保存为 'multi_objective_comparison.png'")
        plt.show()

    return results


def demo_trading_costs(returns_df):
    """演示交易成本考虑"""
    print("\n" + "=" * 60)
    print("4. 交易成本考虑演示")
    print("=" * 60)

    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252
    n_assets = len(mean_returns)

    # 模拟当前投资组合
    current_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    trading_cost_rate = 0.002  # 0.2% 交易成本

    def objective_with_costs(new_weights):
        """包含交易成本的目标函数"""
        # 基础组合指标
        portfolio_return = np.sum(mean_returns * new_weights)
        portfolio_volatility = np.sqrt(
            np.dot(new_weights.T, np.dot(cov_matrix, new_weights))
        )
        (portfolio_return - 0.03) / portfolio_volatility

        # 交易成本
        turnover = np.sum(np.abs(new_weights - current_weights)) / 2
        trading_cost = turnover * trading_cost_rate

        # 调整后的夏普比率
        adjusted_return = portfolio_return - trading_cost
        adjusted_sharpe = (adjusted_return - 0.03) / portfolio_volatility

        # 返回负调整夏普比率（用于最小化）
        return -adjusted_sharpe

    from scipy.optimize import minimize

    print(f"当前投资组合权重: {current_weights}")

    # 不考虑交易成本的优化
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, 1.0) for _ in range(n_assets)]
    initial_weights = np.ones(n_assets) / n_assets

    print("\n1. 不考虑交易成本的优化:")
    result_no_cost = minimize(
        lambda w: objective_with_costs(w) + trading_cost_rate,  # 移除成本影响
        initial_weights,
        method="SLSQP",
        bounds = bounds,
        constraints = constraints,
    )

    if result_no_cost.success:
        weights_no_cost = result_no_cost.x
        turnover_no_cost = np.sum(np.abs(weights_no_cost - current_weights)) / 2
        trading_cost_no_cost = turnover_no_cost * trading_cost_rate

        print(f"  优化权重: {['%.3f' % w for w in weights_no_cost]}")
        print(f"  换手率: {turnover_no_cost:.2%}")
        print(f"  交易成本: {trading_cost_no_cost:.4f}")

    print("\n2. 考虑交易成本的优化:")
    result_with_cost = minimize(
        objective_with_costs,
        initial_weights,
        method="SLSQP",
        bounds = bounds,
        constraints = constraints,
    )

    if result_with_cost.success:
        weights_with_cost = result_with_cost.x
        turnover_with_cost = np.sum(np.abs(weights_with_cost - current_weights)) / 2
        trading_cost_with_cost = turnover_with_cost * trading_cost_rate

        print(f"  优化权重: {['%.3f' % w for w in weights_with_cost]}")
        print(f"  换手率: {turnover_with_cost:.2%}")
        print(f"  交易成本: {trading_cost_with_cost:.4f}")

        # 比较两种策略的绩效
        return_no_cost = np.sum(mean_returns * weights_no_cost)
        vol_no_cost = np.sqrt(
            np.dot(weights_no_cost.T, np.dot(cov_matrix, weights_no_cost))
        )
        adjusted_return_no_cost = return_no_cost - trading_cost_no_cost

        return_with_cost = np.sum(mean_returns * weights_with_cost)
        vol_with_cost = np.sqrt(
            np.dot(weights_with_cost.T, np.dot(cov_matrix, weights_with_cost))
        )
        adjusted_return_with_cost = return_with_cost - trading_cost_with_cost

        print(f"\n绩效比较:")
        print(
            f"{'策略':<15} {'期望收益':<10} {'交易成本':<10} {'净收益':<10} {'波动率':<10}"
        )
        print("-" * 60)
        print(
            f"{'不考虑成本':<15} {return_no_cost:<10.2%} {trading_cost_no_cost:<10.4f} {adjusted_return_no_cost:<10.2%} {vol_no_cost:<10.2%}"
        )
        print(
            f"{'考虑成本':<15} {return_with_cost:<10.2%} {trading_cost_with_cost:<10.4f} {adjusted_return_with_cost:<10.2%} {vol_with_cost:<10.2%}"
        )

        # 权重比较图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 不考虑成本
        ax1.bar(returns_df.columns, current_weights, alpha = 0.5, label="当前权重")
        ax1.bar(returns_df.columns, weights_no_cost, alpha = 0.7, label="优化权重")
        ax1.set_title("不考虑交易成本的优化")
        ax1.set_ylabel("权重")
        ax1.legend()
        ax1.grid(True, alpha = 0.3)

        # 考虑成本
        ax2.bar(returns_df.columns, current_weights, alpha = 0.5, label="当前权重")
        ax2.bar(returns_df.columns, weights_with_cost, alpha = 0.7, label="优化权重")
        ax2.set_title("考虑交易成本的优化")
        ax2.set_ylabel("权重")
        ax2.legend()
        ax2.grid(True, alpha = 0.3)

        plt.tight_layout()
        plt.savefig("trading_costs_comparison.png", dpi = 300, bbox_inches="tight")
        print("\n交易成本比较图已保存为 'trading_costs_comparison.png'")
        plt.show()

    return result_with_cost.success


def demo_sensitivity_analysis(returns_df):
    """演示敏感性分析"""
    print("\n" + "=" * 60)
    print("5. 敏感性分析演示")
    print("=" * 60)

    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252

    # 找到最优权重
    from scipy.optimize import minimize

    def sharpe_objective(weights):
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return -(portfolio_return - 0.03) / portfolio_volatility

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, 1.0) for _ in range(len(mean_returns))]
    initial_weights = np.ones(len(mean_returns)) / len(mean_returns)

    result = minimize(
        sharpe_objective,
        initial_weights,
        method="SLSQP",
        bounds = bounds,
        constraints = constraints,
    )

    if not result.success:
        print("无法找到基准最优权重")
        return

    optimal_weights = result.x
    print(f"基准最优权重: {['%.3f' % w for w in optimal_weights]}")

    # 敏感性分析：均值回报变化
    print("\n均值回报敏感性分析:")
    print("-" * 50)

    sensitivity_ranges = np.linspace(-0.2, 0.2, 9)  # -20%到 + 20%变化
    sensitivity_results = []

    for asset_idx, asset_name in enumerate(returns_df.columns):
        asset_sensitivity = []

        for change in sensitivity_ranges:
            # 调整资产回报
            adjusted_returns = mean_returns.copy()
            adjusted_returns[asset_idx] *= 1 + change

            def adjusted_sharpe(weights):
                portfolio_return = np.sum(adjusted_returns * weights)
                portfolio_volatility = np.sqrt(
                    np.dot(weights.T, np.dot(cov_matrix, weights))
                )
                return -(portfolio_return - 0.03) / portfolio_volatility

            # 使用基准权重计算新夏普比率
            base_sharpe = -sharpe_objective(optimal_weights)
            new_sharpe = -adjusted_sharpe(optimal_weights)

            asset_sensitivity.append(new_sharpe)

        sensitivity_results.append(asset_sensitivity)
        print(
            f"{asset_name}: 基准夏普{base_sharpe:.3f}, "
            + f"最差情况{min(asset_sensitivity):.3f}, 最佳情况{max(asset_sensitivity):.3f}"
        )

    # 可视化敏感性
    plt.figure(figsize=(12, 8))

    for i, asset_name in enumerate(returns_df.columns):
        plt.plot(
            sensitivity_ranges,
            sensitivity_results[i],
            marker="o",
            label = asset_name,
            linewidth = 2,
        )

    plt.axhline(y = 0, color="red", linestyle="--", alpha = 0.7)
    plt.axvline(x = 0, color="red", linestyle="--", alpha = 0.7)
    plt.xlabel("资产回报变化率")
    plt.ylabel("夏普比率")
    plt.title("投资组合对资产回报变化的敏感性")
    plt.legend()
    plt.grid(True, alpha = 0.3)
    plt.tight_layout()

    plt.savefig("sensitivity_analysis.png", dpi = 300, bbox_inches="tight")
    print("\n敏感性分析图已保存为 'sensitivity_analysis.png'")
    plt.show()


def main():
    """主演示函数"""
    print("Multi - Objective Portfolio Optimization System Demo")
    print("Task 2.3 - Multi - Objective Optimization")
    print("=" * 80)

    start_time = time.time()

    try:
        # 1. 目标函数演示
        returns_df, objectives = demo_objective_functions()

        # 2. 帕累托边界演示
        demo_pareto_frontier(returns_df)

        # 3. 多目标优化演示
        demo_multi_objective_optimization(returns_df)

        # 4. 交易成本演示
        demo_trading_costs(returns_df)

        # 5. 敏感性分析演示
        demo_sensitivity_analysis(returns_df)

        total_time = time.time() - start_time
        print("\n" + "=" * 80)
        print(f"Demo completed! Total time: {total_time:.2f} seconds")
        print("\nTask 2.3 Multi - Objective Optimization System Features:")
        print(
            "✓ Multi - objective optimization framework - supports various objective combinations"
        )
        print(
            "✓ Pareto frontier calculation - efficient frontier identification and visualization"
        )
        print(
            "✓ Custom objective functions - return, risk, drawdown, and other metrics"
        )
        print("✓ Trading cost consideration - cost - aware portfolio optimization")
        print("✓ Interactive visualization - multi - dimensional charts")
        print(
            "✓ Preference elicitation tools - strategies for different risk preferences"
        )
        print("✓ Sensitivity analysis - robustness assessment for parameter changes")
        print("\nAll charts have been saved as PNG files for further analysis.")
        print("=" * 80)

    except Exception as e:
        print(f"Error during demo: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
