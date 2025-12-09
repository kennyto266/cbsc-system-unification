#!/usr / bin / env python3
"""
Cookbook增強功能測試
測試Walk - Forward優化、Cookbook策略集成和高級投資組合分析功能
"""

import os
import sys
import unittest

import numpy as np
import pandas as pd

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "..", "simplified_system", "src")
)

try:
    import vectorbt as vbt

    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False


class TestCookbookIntegration(unittest.TestCase):
    """Cookbook集成測試類"""

    @classmethod
    def setUpClass(cls):
        """設置測試類"""
        if not VECTORBT_AVAILABLE:
            cls.skipTest("VectorBT not available")
            return

        # 生成測試數據
        np.random.seed(42)
        dates = pd.date_range("2020 - 01 - 01", "2023 - 12 - 31", freq="D")
        price = 100 + np.cumsum(np.random.randn(len(dates)) * 0.01)
        cls.price_data = pd.Series(price, index = dates)

    def test_walkforward_optimizer_initialization(self):
        """測試Walk - Forward優化器初始化"""
        from simplified_system.src.backtest.enhanced.vectorbt_walkforward_optimizer import (
            WalkForwardConfig,
            WalkForwardOptimizer,
        )

        config = WalkForwardConfig(window_len = 252, n_splits = 5, set_lens=(126,))

        def mock_strategy(price, **params):
            # 模擬策略函數
            return vbt.Portfolio.from_holding(price, init_cash = 100000)

        optimizer = WalkForwardOptimizer(self.price_data, mock_strategy, config)

        self.assertIsNotNone(optimizer)
        self.assertEqual(optimizer.config.window_len, 252)
        self.assertEqual(optimizer.config.n_splits, 5)

    def test_strategy_builder_initialization(self):
        """測試策略構建器初始化"""
        from simplified_system.src.backtest.enhanced.vectorbt_strategy_builder import (
            CookbookStrategyBuilder,
        )

        builder = CookbookStrategyBuilder()

        self.assertIsNotNone(builder)
        available_strategies = builder.get_available_strategies()
        self.assertIn("MA_CROSSOVER", available_strategies)
        self.assertIn("RSI_MEAN_REVERSION", available_strategies)
        self.assertIn("RSI_WITH_STOP_LOSS", available_strategies)

    def test_ma_crossover_strategy(self):
        """測試MA交叉策略"""
        from simplified_system.src.backtest.enhanced.cookbook_strategies.ma_crossover_strategy import (
            ma_crossover_strategy,
        )

        portfolio = ma_crossover_strategy(
            self.price_data, fast_window = 10, slow_window = 30
        )

        self.assertIsNotNone(portfolio)
        self.assertGreater(portfolio.total_return(), 0)
        self.assertIsInstance(portfolio.sharpe_ratio(), (int, float))

    def test_rsi_mean_reversion_strategy(self):
        """測試RSI均值回歸策略"""
        from simplified_system.src.backtest.enhanced.cookbook_strategies.rsi_mean_reversion_strategy import (
            rsi_mean_reversion_strategy,
        )

        portfolio = rsi_mean_reversion_strategy(
            self.price_data, rsi_period = 14, oversold = 30, overbought = 70
        )

        self.assertIsNotNone(portfolio)
        self.assertIsInstance(portfolio.total_return(), (int, float))

    def test_portfolio_analyzer_initialization(self):
        """測試投資組合分析器初始化"""
        from simplified_system.src.backtest.enhanced.vectorbt_portfolio_analyzer import (
            AdvancedPortfolioAnalyzer,
            PortfolioAnalysisConfig,
        )

        config = PortfolioAnalysisConfig()
        analyzer = AdvancedPortfolioAnalyzer(config)

        self.assertIsNotNone(analyzer)
        self.assertEqual(analyzer.config.risk_free_rate, 0.03)

    def test_ma_crossover_optimization(self):
        """測試MA交叉策略優化"""
        from simplified_system.src.backtest.enhanced.cookbook_strategies.ma_crossover_strategy import (
            optimize_ma_crossover,
        )

        # 使用較小的參數範圍以加快測試
        result = optimize_ma_crossover(
            self.price_data, fast_range=[10, 15], slow_range=[20, 30]
        )

        self.assertIsNotNone(result)
        self.assertIn("best_params", result)
        self.assertIn("portfolio", result)
        self.assertIn("all_results", result)

        best_params = result["best_params"]
        self.assertIn("fast_window", best_params)
        self.assertIn("slow_window", best_params)

    def test_strategy_comparison(self):
        """測試策略比較功能"""
        from simplified_system.src.backtest.enhanced.vectorbt_strategy_builder import (
            CookbookStrategyBuilder,
        )

        builder = CookbookStrategyBuilder()

        # 比較有限數量的策略以加快測試
        comparison_result = builder.compare_strategies(
            self.price_data, strategy_names=["MA_CROSSOVER", "RSI_MEAN_REVERSION"]
        )

        self.assertIsInstance(comparison_result, pd.DataFrame)
        self.assertEqual(len(comparison_result), 2)
        self.assertIn("sharpe_ratio", comparison_result.columns)
        self.assertIn("total_return", comparison_result.columns)

    def test_rsi_strategy_optimization(self):
        """測試RSI策略優化"""
        from simplified_system.src.backtest.enhanced.cookbook_strategies.rsi_mean_reversion_strategy import (
            optimize_rsi_strategy,
        )

        # 使用較小的參數範圍以加快測試
        result = optimize_rsi_strategy(
            self.price_data,
            rsi_range=[14],
            oversold_range=[25, 30],
            overbought_range=[70, 75],
        )

        self.assertIsNotNone(result)
        self.assertIn("best_params", result)
        best_params = result["best_params"]
        self.assertEqual(best_params["rsi_period"], 14)

    def test_portfolio_performance_calculation(self):
        """測試投資組合績效計算"""
        # 創建簡單的投資組合
        entries = pd.Series(False, index = self.price_data.index)
        exits = pd.Series(False, index = self.price_data.index)

        # 在中間位置設置買入和賣出信號
        mid_point = len(self.price_data) // 3
        entries.iloc[mid_point : mid_point + 50] = True
        exits.iloc[mid_point + 50 : mid_point + 100] = True

        portfolio = vbt.Portfolio.from_signals(
            self.price_data, entries, exits, init_cash = 100000, fees = 0.001
        )

        # 測試基本性能指標
        self.assertIsInstance(portfolio.total_return(), (int, float))
        self.assertIsInstance(portfolio.sharpe_ratio(), (int, float))
        self.assertIsInstance(portfolio.max_drawdown(), (int, float))

    def test_walkforward_optimization_basic(self):
        """測試基本Walk - Forward優化功能"""
        from simplified_system.src.backtest.enhanced.vectorbt_walkforward_optimizer import (
            WalkForwardConfig,
            WalkForwardOptimizer,
        )

        def simple_strategy(price, **params):
            # 簡單的持有策略作為測試
            return vbt.Portfolio.from_holding(price, init_cash = 100000)

        config = WalkForwardConfig(
            window_len = 252, n_splits = 3, set_lens=(126,)  # 減少分割數量以加快測試
        )

        optimizer = WalkForwardOptimizer(self.price_data, simple_strategy, config)
        result = optimizer.optimize()

        self.assertIsNotNone(result)
        self.assertIsInstance(result.sharpe_improvement, (int, float))
        self.assertIsInstance(result.stability_score, (int, float))
        self.assertGreaterEqual(result.stability_score, 0)
        self.assertLessEqual(result.stability_score, 100)


if __name__ == "__main__":
    # 運行測試
    unittest.main(verbosity = 2)
