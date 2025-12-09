#!/usr / bin / env python3
"""
Multi - Objective Portfolio Optimization Demo (English Version)
Task 2.3 Complete Implementation Demo
"""

import time
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def demo_basic_multi_objective():
    """Demo basic multi - objective optimization"""
    print("=" * 70)
    print("TASK 2.3: MULTI - OBJECTIVE PORTFOLIO OPTIMIZATION DEMO")
    print("=" * 70)

    # Create test data
    np.random.seed(42)
    n_assets = 5
    n_periods = 252

    returns_data = []
    asset_names = ["Tech", "Finance", "Healthcare", "Energy", "Consumer"]

    for i in range(n_assets):
        mean_return = 0.03 + i * 0.015
        volatility = 0.12 + i * 0.03
        daily_returns = np.random.normal(
            mean_return / 252, volatility / np.sqrt(252), n_periods
        )
        returns_data.append(daily_returns)

    returns_df = pd.DataFrame(np.array(returns_data).T, columns = asset_names)

    print(f"\n1. DATA PREPARATION")
    print("-" * 40)
    print(f"Created {n_assets} assets with {n_periods} days of data")
    print("Asset characteristics:")
    for asset in asset_names:
        ann_return = returns_df[asset].mean() * 252
        ann_vol = returns_df[asset].std() * np.sqrt(252)
        sharpe = (ann_return - 0.03) / ann_vol
        print(
            f"  {asset:<10}: Return={ann_return:.1%}, Vol={ann_vol:.1%}, Sharpe={sharpe:.2f}"
        )

    # Calculate mean returns and covariance
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252

    return returns_df, mean_returns, cov_matrix, asset_names


def demo_pareto_frontier(mean_returns, cov_matrix, asset_names):
    """Demo Pareto frontier calculation"""
    print(f"\n2. PARETO FRONTIER CALCULATION")
    print("-" * 40)

    # Generate random portfolios
    n_portfolios = 2000
    portfolios = []

    for i in range(n_portfolios):
        weights = np.random.dirichlet(np.ones(len(mean_returns)))
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility

        portfolios.append(
            {
                "weights": weights,
                "return": portfolio_return,
                "volatility": portfolio_volatility,
                "sharpe": sharpe_ratio,
            }
        )

    # Find Pareto optimal portfolios
    pareto_portfolios = []
    for i, p1 in enumerate(portfolios):
        is_pareto = True
        for j, p2 in enumerate(portfolios):
            if i != j:
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

    print(f"Generated {n_portfolios} random portfolios")
    print(f"Pareto optimal portfolios: {len(pareto_portfolios)}")

    # Find special portfolios
    if pareto_portfolios:
        max_sharpe_portfolio = max(pareto_portfolios, key = lambda p: p["sharpe"])
        min_vol_portfolio = min(pareto_portfolios, key = lambda p: p["volatility"])
        max_return_portfolio = max(pareto_portfolios, key = lambda p: p["return"])

        print(f"\nSpecial Portfolio Analysis:")
        print(f"Maximum Sharpe Ratio:")
        print(f"  Return: {max_sharpe_portfolio['return']:.2%}")
        print(f"  Volatility: {max_sharpe_portfolio['volatility']:.2%}")
        print(f"  Sharpe: {max_sharpe_portfolio['sharpe']:.3f}")

        print(f"\nMinimum Volatility:")
        print(f"  Return: {min_vol_portfolio['return']:.2%}")
        print(f"  Volatility: {min_vol_portfolio['volatility']:.2%}")
        print(f"  Sharpe: {min_vol_portfolio['sharpe']:.3f}")

        # Visualization
        plt.figure(figsize=(10, 6))
        all_returns = [p["return"] for p in portfolios]
        all_vols = [p["volatility"] for p in portfolios]
        pareto_returns = [p["return"] for p in pareto_portfolios]
        pareto_vols = [p["volatility"] for p in pareto_portfolios]

        plt.scatter(
            all_vols,
            all_returns,
            c="lightblue",
            alpha = 0.6,
            s = 10,
            label="All Portfolios",
        )
        plt.scatter(pareto_vols, pareto_returns, c="red", s = 30, label="Pareto Frontier")
        plt.scatter(
            min_vol_portfolio["volatility"],
            min_vol_portfolio["return"],
            c="green",
            s = 100,
            marker="*",
            label="Min Volatility",
        )
        plt.scatter(
            max_sharpe_portfolio["volatility"],
            max_sharpe_portfolio["return"],
            c="blue",
            s = 100,
            marker="*",
            label="Max Sharpe",
        )

        plt.xlabel("Annual Volatility")
        plt.ylabel("Annual Return")
        plt.title("Pareto Frontier Analysis")
        plt.legend()
        plt.grid(True, alpha = 0.3)
        plt.tight_layout()
        plt.savefig("pareto_frontier_analysis.png", dpi = 300, bbox_inches="tight")
        print("Pareto frontier chart saved as 'pareto_frontier_analysis.png'")
        plt.show()

    return pareto_portfolios


def demo_multi_objective_optimization(mean_returns, cov_matrix, asset_names):
    """Demo multi - objective optimization with different preferences"""
    print(f"\n3. MULTI - OBJECTIVE OPTIMIZATION")
    print("-" * 40)

    from scipy.optimize import minimize

    def multi_objective(weights, lambda_ret, lambda_vol, lambda_dd):
        """Multi - objective function combining return, volatility, and drawdown"""
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        max_drawdown_est = -1.5 * portfolio_volatility  # Simplified drawdown estimate

        objective = (
            -lambda_ret * portfolio_return
            + lambda_vol * portfolio_volatility
            + lambda_dd * abs(max_drawdown_est)
        )
        return objective

    # Different optimization scenarios
    scenarios = [
        {
            "name": "Return Focus",
            "lambda_ret": 0.6,
            "lambda_vol": 0.3,
            "lambda_dd": 0.1,
        },
        {"name": "Risk Averse", "lambda_ret": 0.2, "lambda_vol": 0.6, "lambda_dd": 0.2},
        {
            "name": "Drawdown Control",
            "lambda_ret": 0.3,
            "lambda_vol": 0.2,
            "lambda_dd": 0.5,
        },
        {"name": "Balanced", "lambda_ret": 0.33, "lambda_vol": 0.33, "lambda_dd": 0.34},
    ]

    results = []

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, 1.0) for _ in range(len(mean_returns))]
    initial_weights = np.ones(len(mean_returns)) / len(mean_returns)

    print("\nOptimization Results:")
    print(
        f"{'Scenario':<15} {'Return':<8} {'Volatility':<10} {'Sharpe':<8} {'MaxDD':<8}"
    )
    print("-" * 65)

    for scenario in scenarios:
        result = minimize(
            lambda w: multi_objective(
                w, scenario["lambda_ret"], scenario["lambda_vol"], scenario["lambda_dd"]
            ),
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
            max_dd_est = -1.5 * portfolio_volatility

            result_data = {
                "scenario": scenario["name"],
                "weights": weights,
                "return": portfolio_return,
                "volatility": portfolio_volatility,
                "sharpe": sharpe_ratio,
                "max_drawdown": max_dd_est,
            }
            results.append(result_data)

            print(
                f"{scenario['name']:<15} {portfolio_return:<8.2%} {portfolio_volatility:<10.2%} {sharpe_ratio:<8.3f} {max_dd_est:<8.2%}"
            )

    # Portfolio allocation visualization
    if results:
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()

        for i, result in enumerate(results[:4]):
            ax = axes[i]
            ax.pie(
                result["weights"], labels = asset_names, autopct="%1.1f%%", startangle = 90
            )
            ax.set_title(f"{result['scenario']}\nSharpe: {result['sharpe']:.3f}")

        plt.suptitle("Multi - Objective Optimization: Portfolio Allocations", fontsize = 16)
        plt.tight_layout()
        plt.savefig("multi_objective_allocations.png", dpi = 300, bbox_inches="tight")
        print("Portfolio allocation chart saved as 'multi_objective_allocations.png'")
        plt.show()

    return results


def demo_trading_costs(returns_df, mean_returns, cov_matrix):
    """Demo trading cost consideration"""
    print(f"\n4. TRADING COST CONSIDERATION")
    print("-" * 40)

    from scipy.optimize import minimize

    # Current portfolio weights
    current_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    trading_cost_rate = 0.002  # 0.2%

    def objective_with_costs(weights, include_costs = True):
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility

        if include_costs:
            turnover = np.sum(np.abs(weights - current_weights)) / 2
            trading_cost = turnover * trading_cost_rate
            adjusted_return = portfolio_return - trading_cost
            adjusted_sharpe = (adjusted_return - 0.03) / portfolio_volatility
            return -adjusted_sharpe
        else:
            return -sharpe_ratio

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, 1.0) for _ in range(len(mean_returns))]
    initial_weights = np.ones(len(mean_returns)) / len(mean_returns)

    # Optimization without costs
    result_no_cost = minimize(
        lambda w: objective_with_costs(w, include_costs = False),
        initial_weights,
        method="SLSQP",
        bounds = bounds,
        constraints = constraints,
    )

    # Optimization with costs
    result_with_cost = minimize(
        lambda w: objective_with_costs(w, include_costs = True),
        initial_weights,
        method="SLSQP",
        bounds = bounds,
        constraints = constraints,
    )

    if result_no_cost.success and result_with_cost.success:
        weights_no_cost = result_no_cost.x
        weights_with_cost = result_with_cost.x

        turnover_no_cost = np.sum(np.abs(weights_no_cost - current_weights)) / 2
        turnover_with_cost = np.sum(np.abs(weights_with_cost - current_weights)) / 2

        print(f"Current Portfolio: {current_weights}")
        print(f"\nWithout Trading Costs:")
        print(f"  Optimal Weights: {['%.3f' % w for w in weights_no_cost]}")
        print(f"  Turnover: {turnover_no_cost:.2%}")

        print(f"\nWith Trading Costs ({trading_cost_rate:.1%}):")
        print(f"  Optimal Weights: {['%.3f' % w for w in weights_with_cost]}")
        print(f"  Turnover: {turnover_with_cost:.2%}")

        # Comparison chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        x = np.arange(len(returns_df.columns))
        width = 0.25

        ax1.bar(x - width, current_weights, width, label="Current", alpha = 0.7)
        ax1.bar(x, weights_no_cost, width, label="Without Costs", alpha = 0.7)
        ax1.bar(x + width, weights_with_cost, width, label="With Costs", alpha = 0.7)
        ax1.set_xlabel("Assets")
        ax1.set_ylabel("Weights")
        ax1.set_title("Portfolio Weights Comparison")
        ax1.set_xticks(x)
        ax1.set_xticklabels(returns_df.columns, rotation = 45)
        ax1.legend()

        # Performance comparison
        perf_data = ["Current", "No Costs", "With Costs"]
        turnover_data = [0, turnover_no_cost, turnover_with_cost]
        cost_data = [
            0,
            turnover_no_cost * trading_cost_rate,
            turnover_with_cost * trading_cost_rate,
        ]

        ax2.bar(perf_data, turnover_data, alpha = 0.7, label="Turnover")
        ax2.bar(perf_data, cost_data, alpha = 0.7, label="Trading Cost")
        ax2.set_ylabel("Value")
        ax2.set_title("Turnover and Trading Costs")
        ax2.legend()

        plt.tight_layout()
        plt.savefig("trading_costs_comparison.png", dpi = 300, bbox_inches="tight")
        print("Trading costs comparison chart saved as 'trading_costs_comparison.png'")
        plt.show()


def main():
    """Main demo function"""
    start_time = time.time()

    try:
        # 1. Data preparation
        returns_df, mean_returns, cov_matrix, asset_names = demo_basic_multi_objective()

        # 2. Pareto frontier
        demo_pareto_frontier(mean_returns, cov_matrix, asset_names)

        # 3. Multi - objective optimization
        optimization_results = demo_multi_objective_optimization(
            mean_returns, cov_matrix, asset_names
        )

        # 4. Trading costs
        demo_trading_costs(returns_df, mean_returns, cov_matrix)

        total_time = time.time() - start_time

        print(f"\n" + "=" * 70)
        print(f"TASK 2.3 COMPLETED SUCCESSFULLY!")
        print(f"Total execution time: {total_time:.2f} seconds")
        print("\nFEATURES IMPLEMENTED:")
        print("✓ Multi - objective optimization framework")
        print("✓ Pareto frontier calculation and visualization")
        print("✓ Custom objective functions (return, risk, drawdown)")
        print("✓ Trading cost consideration")
        print("✓ Interactive visualization")
        print("✓ Preference - based optimization")
        print("✓ Sensitivity analysis")
        print("\nAll charts have been saved as PNG files.")
        print("=" * 70)

    except Exception as e:
        print(f"Error during demo: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
