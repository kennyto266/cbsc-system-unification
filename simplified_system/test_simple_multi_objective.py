#!/usr / bin / env python3
"""
Simple Multi - Objective Optimization Test
简化的多目标优化测试

Test basic multi - objective optimization functionality
"""

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def test_basic_objectives():
    """测试基本目标函数"""
    print("Testing Basic Objectives")
    print("-" * 30)

    # 创建测试数据
    np.random.seed(42)
    n_assets = 4
    n_periods = 100

    returns_data = np.random.normal(0.001, 0.02, (n_periods, n_assets))
    asset_names = [f"Asset_{i}" for i in range(n_assets)]
    returns_df = pd.DataFrame(returns_data, columns = asset_names)

    print(f"Created test data: {returns_df.shape}")

    # 测试权重
    weights = np.array([0.3, 0.25, 0.25, 0.2])
    print(f"Test weights: {weights}")

    # 计算基本指标
    portfolio_returns = (returns_df * weights).sum(axis = 1)

    # 年化回报
    annual_return = portfolio_returns.mean() * 252
    print(f"Annual Return: {annual_return:.4f}")

    # 年化波动率
    annual_volatility = portfolio_returns.std() * np.sqrt(252)
    print(f"Annual Volatility: {annual_volatility:.4f}")

    # 夏普比率
    risk_free_rate = 0.03
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
    print(f"Sharpe Ratio: {sharpe_ratio:.4f}")

    # 最大回撤
    cumulative_returns = (1 + portfolio_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min()
    print(f"Max Drawdown: {max_drawdown:.4f}")

    return True


def test_pareto_simple():
    """测试简化的帕累托优化"""
    print("\nTesting Simple Pareto Optimization")
    print("-" * 30)

    # 创建测试数据
    np.random.seed(42)
    n_assets = 3
    n_periods = 50

    returns_data = np.random.normal(0.001, 0.02, (n_periods, n_assets))
    asset_names = [f"Stock_{i}" for i in range(n_assets)]
    returns_df = pd.DataFrame(returns_data, columns = asset_names)

    # 计算协方差矩阵和期望回报
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252

    print(f"Mean returns: {mean_returns.values}")
    print(f"Covariance matrix diagonal: {np.diag(cov_matrix)}")

    # 生成随机权重组合
    n_portfolios = 100
    portfolios = []

    for i in range(n_portfolios):
        weights = np.random.dirichlet(np.ones(n_assets))
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)

        sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility

        portfolios.append(
            {
                "weights": weights,
                "return": portfolio_return,
                "volatility": portfolio_volatility,
                "sharpe": sharpe_ratio,
            }
        )

    # 找到帕累托最优解
    pareto_portfolios = []
    for i, p1 in enumerate(portfolios):
        is_pareto = True
        for j, p2 in enumerate(portfolios):
            if i != j:
                # 如果p2在回报和波动率上都优于p1，则p1不是帕累托最优
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

    print(f"Total portfolios: {n_portfolios}")
    print(f"Pareto optimal portfolios: {len(pareto_portfolios)}")

    if pareto_portfolios:
        # 找到最高夏普比率组合
        best_sharpe_portfolio = max(pareto_portfolios, key = lambda p: p["sharpe"])
        print(f"\nBest Sharpe Ratio Portfolio:")
        print(f"  Weights: {best_sharpe_portfolio['weights']}")
        print(f"  Return: {best_sharpe_portfolio['return']:.4f}")
        print(f"  Volatility: {best_sharpe_portfolio['volatility']:.4f}")
        print(f"  Sharpe: {best_sharpe_portfolio['sharpe']:.4f}")

        # 找到最低波动率组合
        min_vol_portfolio = min(pareto_portfolios, key = lambda p: p["volatility"])
        print(f"\nMinimum Volatility Portfolio:")
        print(f"  Weights: {min_vol_portfolio['weights']}")
        print(f"  Return: {min_vol_portfolio['return']:.4f}")
        print(f"  Volatility: {min_vol_portfolio['volatility']:.4f}")
        print(f"  Sharpe: {min_vol_portfolio['sharpe']:.4f}")

    return len(pareto_portfolios) > 0


def test_weighted_sum_optimization():
    """测试加权和优化"""
    print("\nTesting Weighted Sum Optimization")
    print("-" * 30)

    # 创建测试数据
    np.random.seed(42)
    n_assets = 4
    n_periods = 100

    returns_data = np.random.normal(0.001, 0.02, (n_periods, n_assets))
    asset_names = [f"Asset_{i}" for i in range(n_assets)]
    returns_df = pd.DataFrame(returns_data, columns = asset_names)

    # 计算协方差矩阵和期望回报
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252

    def objective_function(weights, lambda_return, lambda_vol):
        """组合目标函数：最大化回报，最小化波动率"""
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        # 负的加权组合（用于最小化）
        return -lambda_return * portfolio_return + lambda_vol * portfolio_volatility

    # 不同的风险偏好权重
    weight_combinations = [
        (0.8, 0.2),  # 偏好回报
        (0.5, 0.5),  # 平衡
        (0.2, 0.8),  # 偏好低风险
    ]

    from scipy.optimize import minimize

    results = []
    for lambda_return, lambda_vol in weight_combinations:
        # 约束条件
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        bounds = [(0.0, 1.0) for _ in range(n_assets)]
        initial_weights = np.ones(n_assets) / n_assets

        # 优化
        result = minimize(
            lambda w: objective_function(w, lambda_return, lambda_vol),
            initial_weights,
            method="SLSQP",
            bounds = bounds,
            constraints = constraints,
        )

        if result.success:
            weights = result.x
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_volatility = np.sqrt(
                np.dot(weights.T, np.dot(cov_matrix, weights))
            )
            sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility

            results.append(
                {
                    "lambda_return": lambda_return,
                    "lambda_vol": lambda_vol,
                    "weights": weights,
                    "return": portfolio_return,
                    "volatility": portfolio_volatility,
                    "sharpe": sharpe_ratio,
                }
            )

    print("Weighted Sum Optimization Results:")
    for res in results:
        print(
            f"\nPreference (Return: {res['lambda_return']:.1f}, Vol: {res['lambda_vol']:.1f}):"
        )
        print(f"  Weights: {res['weights']}")
        print(f"  Return: {res['return']:.4f}")
        print(f"  Volatility: {res['volatility']:.4f}")
        print(f"  Sharpe: {res['sharpe']:.4f}")

    return len(results) > 0


def main():
    """主测试函数"""
    print("=" * 50)
    print("SIMPLE MULTI - OBJECTIVE OPTIMIZATION TEST")
    print("=" * 50)

    tests = [
        ("Basic Objectives", test_basic_objectives),
        ("Simple Pareto Optimization", test_pareto_simple),
        ("Weighted Sum Optimization", test_weighted_sum_optimization),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                print(f"[PASS] {test_name}: PASSED")
                passed += 1
            else:
                print(f"[FAIL] {test_name}: FAILED")
        except Exception as e:
            print(f"[ERROR] {test_name}: ERROR - {str(e)}")

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} passed")
    if passed == total:
        print("All tests passed!")
    else:
        print("Some tests failed.")


if __name__ == "__main__":
    main()
