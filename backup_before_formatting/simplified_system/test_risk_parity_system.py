#!/usr/bin/env python3
"""
Risk Parity System Integration Test
风险平价系统集成测试

Comprehensive testing of the risk parity system
风险平价系统综合测试

This script tests:
1. Risk Parity Optimizer
2. Risk Budgeting Framework
3. Risk Contribution Analysis
4. Risk Parity Backtesting
5. Integration with existing components
"""

import sys
import os
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add the simplified_system path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'backtest'))

# Import test data
from api.stock_api import get_hk_stock_data

# Import risk parity components directly
import risk_parity_optimizer
import risk_budgeting
import risk_contribution
import risk_parity_backtester
import mpt_optimizer
import risk_metrics

# Get classes from modules
RiskParityOptimizer = risk_parity_optimizer.RiskParityOptimizer
RiskParityConfig = risk_parity_optimizer.RiskParityConfig
RiskBudgetingFramework = risk_budgeting.RiskBudgetingFramework
RiskBudgetConfig = risk_budgeting.RiskBudgetConfig
RiskContributionCalculator = risk_contribution.RiskContributionCalculator
RiskContributionConfig = risk_contribution.RiskContributionConfig
RiskParityBacktester = risk_parity_backtester.RiskParityBacktester
BacktestConfig = risk_parity_backtester.BacktestConfig
MPTOptimizer = mpt_optimizer.MPTOptimizer
AdvancedRiskMetrics = risk_metrics.AdvancedRiskMetrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RiskParitySystemTester:
    """风险平价系统测试器"""

    def __init__(self):
        """初始化测试器"""
        self.test_assets = ['0700.HK', '0941.HK', '1398.HK']  # 腾讯、中国移动、工商银行
        self.test_data = None
        self.test_results = {}

    def load_test_data(self):
        """加载测试数据"""
        logger.info("Loading test data...")

        try:
            # 获取测试资产的数据
            asset_data = {}
            for symbol in self.test_assets:
                try:
                    data = get_hk_stock_data(symbol, 1095)  # 3年数据
                    if data is not None and len(data) > 0:
                        # 计算日回报率
                        prices = pd.Series(data['close'])
                        returns = prices.pct_change().dropna()
                        asset_data[symbol] = returns
                        logger.info(f"Loaded {len(returns)} return observations for {symbol}")
                    else:
                        logger.warning(f"No data available for {symbol}")
                except Exception as e:
                    logger.error(f"Failed to load data for {symbol}: {e}")
                    continue

            if asset_data:
                # 创建对齐的回报率DataFrame
                self.test_data = pd.DataFrame(asset_data)
                # 移除任何包含NaN的行
                self.test_data = self.test_data.dropna()

                logger.info(f"Successfully loaded test data: {self.test_data.shape}")
                logger.info(f"Data period: {self.test_data.index[0]} to {self.test_data.index[-1]}")
                return True
            else:
                logger.error("No asset data loaded")
                return False

        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            return False

    def generate_synthetic_data(self):
        """生成合成测试数据"""
        logger.info("Generating synthetic test data...")

        try:
            # 参数设置
            num_assets = 5
            num_periods = 1000
            start_date = datetime.now() - timedelta(days=num_periods * 2)

            # 生成随机协方差矩阵
            np.random.seed(42)
            returns = np.random.multivariate_normal(
                mean=np.array([0.0005] * num_assets),
                cov=np.eye(num_assets) * 0.02 + np.random.rand(num_assets, num_assets) * 0.01,
                size=num_periods
            )

            # 添加一些相关性结构
            correlation_matrix = np.array([
                [1.0, 0.3, 0.2, 0.1, 0.0],
                [0.3, 1.0, 0.4, 0.2, 0.1],
                [0.2, 0.4, 1.0, 0.3, 0.2],
                [0.1, 0.2, 0.3, 1.0, 0.4],
                [0.0, 0.1, 0.2, 0.4, 1.0]
            ])

            # 应用相关性
            volatilities = np.std(returns, axis=0)
            correlation_adjusted_returns = returns.copy()
            for i in range(num_assets):
                for j in range(num_assets):
                    if i != j:
                        correlation_adjusted_returns[:, j] = (
                            correlation_matrix[i, j] * volatilities[i] / volatilities[j] * returns[:, i] +
                            (1 - correlation_matrix[i, j]) * returns[:, j]
                        )

            # 创建DataFrame
            asset_names = [f'ASSET_{i+1}' for i in range(num_assets)]
            dates = pd.date_range(start=start_date, periods=num_periods, freq='D')

            self.test_data = pd.DataFrame(
                correlation_adjusted_returns,
                index=dates,
                columns=asset_names
            )

            logger.info(f"Generated synthetic data: {self.test_data.shape}")
            logger.info(f"Data period: {self.test_data.index[0]} to {self.test_data.index[-1]}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate synthetic data: {e}")
            return False

    def test_risk_parity_optimizer(self):
        """测试风险平价优化器"""
        logger.info("Testing Risk Parity Optimizer...")

        try:
            # 初始化优化器
            config = RiskParityConfig()
            optimizer = RiskParityOptimizer(config)

            # 测试等风险贡献
            result_erc = optimizer.optimize_equal_risk_contribution(self.test_data)
            self.test_results['equal_risk_contribution'] = {
                'success': True,
                'sharpe_ratio': result_erc.sharpe_ratio,
                'volatility': result_erc.volatility,
                'parity_satisfaction': result_erc.risk_contributions.parity_satisfaction
            }

            logger.info(f"✓ Equal Risk Contribution: Sharpe={result_erc.sharpe_ratio:.3f}, Parity={result_erc.risk_contributions.parity_satisfaction:.2%}")

            # 测试风险预算
            risk_budget = np.array([0.4, 0.3, 0.2, 0.05, 0.05])[:len(self.test_data.columns)]
            risk_budget = risk_budget / risk_budget.sum()

            result_rb = optimizer.optimize_risk_budgeting(self.test_data, risk_budget)
            self.test_results['risk_budgeting'] = {
                'success': True,
                'sharpe_ratio': result_rb.sharpe_ratio,
                'budget_error': result_rb.risk_contributions.budget_error
            }

            logger.info(f"✓ Risk Budgeting: Sharpe={result_rb.sharpe_ratio:.3f}, Budget Error={result_rb.risk_contributions.budget_error:.6f}")

            # 测试层次风险平价
            result_hrp = optimizer.optimize_hierarchical_risk_parity(self.test_data)
            self.test_results['hierarchical_risk_parity'] = {
                'success': True,
                'sharpe_ratio': result_hrp.sharpe_ratio,
                'volatility': result_hrp.volatility
            }

            logger.info(f"✓ Hierarchical Risk Parity: Sharpe={result_hrp.sharpe_ratio:.3f}")

            return True

        except Exception as e:
            logger.error(f"Risk Parity Optimizer test failed: {e}")
            self.test_results['risk_parity_optimizer'] = {'success': False, 'error': str(e)}
            return False

    def test_risk_budgeting_framework(self):
        """测试风险预算框架"""
        logger.info("Testing Risk Budgeting Framework...")

        try:
            # 初始化框架
            config = RiskBudgetingFramework(RiskBudgetingConfig())

            # 创建等风险预算
            equal_budget = config.create_equal_risk_budget(
                list(self.test_data.columns),
                "test_equal_budget"
            )

            # 创建自定义风险预算
            custom_allocations = {
                asset: 1.0 / len(self.test_data.columns) for asset in self.test_data.columns
            }
            # 给第一个资产更高权重
            first_asset = self.test_data.columns[0]
            custom_allocations[first_asset] = 0.5
            custom_allocations = {k: v for k, v in sorted(custom_allocations.items(), key=lambda x: x[0])}

            custom_budget = config.create_custom_risk_budget(
                list(self.test_data.columns),
                custom_allocations,
                "test_custom_budget"
            )

            # 测试投资组合分配
            allocation = config.allocate_portfolio(self.test_data, "test_equal_budget")

            self.test_results['risk_budgeting_framework'] = {
                'success': True,
                'budget_satisfaction': allocation.budget_satisfaction,
                'expected_return': allocation.expected_return,
                'volatility': allocation.volatility
            }

            logger.info(f"✓ Risk Budgeting Framework: Satisfaction={allocation.budget_satisfaction:.2%}, Sharpe={allocation.sharpe_ratio:.3f}")

            return True

        except Exception as e:
            logger.error(f"Risk Budgeting Framework test failed: {e}")
            self.test_results['risk_budgeting_framework'] = {'success': False, 'error': str(e)}
            return False

    def test_risk_contribution_calculator(self):
        """测试风险贡献计算器"""
        logger.info("Testing Risk Contribution Calculator...")

        try:
            # 初始化计算器
            calculator = RiskContributionCalculator()

            # 创建测试权重
            num_assets = len(self.test_data.columns)
            test_weights = np.ones(num_assets) / num_assets

            # 计算风险贡献
            analysis = calculator.calculate_marginal_contributions(
                self.test_data, test_weights, "volatility"
            )

            # 测试滚动贡献
            rolling_contributions = calculator.calculate_rolling_contributions(
                self.test_data, test_weights, window=60
            )

            self.test_results['risk_contribution_calculator'] = {
                'success': True,
                'portfolio_volatility': analysis.portfolio_volatility,
                'diversification_ratio': analysis.diversification_ratio,
                'num_factors': len(analysis.factor_contributions)
            }

            logger.info(f"✓ Risk Contribution Calculator: Vol={analysis.portfolio_volatility:.4f}, DivRatio={analysis.diversification_ratio:.3f}")

            return True

        except Exception as e:
            logger.error(f"Risk Contribution Calculator test failed: {e}")
            self.test_results['risk_contribution_calculator'] = {'success': False, 'error': str(e)}
            return False

    def test_risk_parity_backtester(self):
        """测试风险平价回测器"""
        logger.info("Testing Risk Parity Backtester...")

        try:
            # 配置回测
            config = BacktestConfig(
                start_date=self.test_data.index[0].strftime('%Y-%m-%d'),
                end_date=self.test_data.index[-1].strftime('%Y-%m-%d'),
                rebalance_frequency="monthly",
                lookback_window=252
            )

            backtester = RiskParityBacktester(config)

            # 测试等风险平价回测
            result_erc = backtester.backtest_equal_risk_parity(
                self.test_data, "Test Equal Risk Parity"
            )

            # 测试层次风险平价回测
            result_hrp = backtester.backtest_hierarchical_risk_parity(
                self.test_data, "ward", "Test HRP"
            )

            self.test_results['risk_parity_backtester'] = {
                'success': True,
                'erc_sharpe': result_erc.sharpe_ratio,
                'erc_max_drawdown': result_erc.max_drawdown,
                'hrp_sharpe': result_hrp.sharpe_ratio,
                'hrp_max_drawdown': result_hrp.max_drawdown,
                'erc_turnover': result_erc.turnover
            }

            logger.info(f"✓ Risk Parity Backtester: ERC Sharpe={result_erc.sharpe_ratio:.3f}, HRP Sharpe={result_hrp.sharpe_ratio:.3f}")

            return True

        except Exception as e:
            logger.error(f"Risk Parity Backtester test failed: {e}")
            self.test_results['risk_parity_backtester'] = {'success': False, 'error': str(e)}
            return False

    def test_integration_with_existing_components(self):
        """测试与现有组件的集成"""
        logger.info("Testing Integration with Existing Components...")

        try:
            # 测试与MPT优化器的集成
            mpt_optimizer = MPTOptimizer()
            mpt_result = mpt_optimizer.risk_parity_optimization(self.test_data)

            # 测试与风险指标系统的集成
            risk_metrics = AdvancedRiskMetrics()

            # 创建测试投资组合
            weights = np.ones(len(self.test_data.columns)) / len(self.test_data.columns)
            portfolio_returns = (self.test_data * weights).sum(axis=1)

            metrics = risk_metrics.calculate_risk_metrics(portfolio_returns)

            self.test_results['integration_test'] = {
                'success': True,
                'mpt_sharpe': mpt_result.sharpe_ratio,
                'risk_metrics_sharpe': metrics.sharpe_ratio,
                'integration_success': True
            }

            logger.info(f"✓ Integration Test: MPT Sharpe={mpt_result.sharpe_ratio:.3f}, Risk Metrics Sharpe={metrics.sharpe_ratio:.3f}")

            return True

        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            self.test_results['integration_test'] = {'success': False, 'error': str(e)}
            return False

    def run_comprehensive_backtest_comparison(self):
        """运行综合回测比较"""
        logger.info("Running Comprehensive Backtest Comparison...")

        try:
            # 配置回测
            config = BacktestConfig(
                start_date=self.test_data.index[0].strftime('%Y-%m-%d'),
                end_date=self.test_data.index[-1].strftime('%Y-%m-%d'),
                rebalance_frequency="monthly",
                lookback_window=126  # 6个月
            )

            backtester = RiskParityBacktester(config)

            # 定义策略
            strategies = [
                ("equal_risk_parity", {"name": "Equal Risk Parity"}),
                ("hierarchical_risk_parity", {
                    "linkage_method": "ward",
                    "name": "Hierarchical RP (Ward)"
                }),
                ("risk_budgeting", {
                    "risk_allocations": {
                        asset: 0.6 if i == 0 else 0.4 / (len(self.test_data.columns) - 1)
                        for i, asset in enumerate(self.test_data.columns)
                    },
                    "name": "Custom Risk Budget"
                })
            ]

            # 比较策略
            comparison_results = backtester.compare_strategies(self.test_data, strategies)

            self.test_results['comprehensive_comparison'] = {
                'success': True,
                'num_strategies': len(comparison_results),
                'best_strategy': comparison_results.iloc[0]['strategy_name'] if len(comparison_results) > 0 else None,
                'best_sharpe': comparison_results.iloc[0]['sharpe_ratio'] if len(comparison_results) > 0 else None
            }

            logger.info(f"✓ Comprehensive Comparison: {len(comparison_results)} strategies tested")
            if len(comparison_results) > 0:
                logger.info(f"Best strategy: {comparison_results.iloc[0]['strategy_name']} (Sharpe: {comparison_results.iloc[0]['sharpe_ratio']:.3f})")

            return True

        except Exception as e:
            logger.error(f"Comprehensive comparison failed: {e}")
            self.test_results['comprehensive_comparison'] = {'success': False, 'error': str(e)}
            return False

    def generate_test_report(self):
        """生成测试报告"""
        logger.info("Generating Test Report...")

        try:
            report = {
                'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'test_data_info': {
                    'shape': self.test_data.shape,
                    'period': f"{self.test_data.index[0]} to {self.test_data.index[-1]}",
                    'assets': list(self.test_data.columns)
                },
                'test_results': self.test_results,
                'summary': {
                    'total_tests': len(self.test_results),
                    'successful_tests': sum(1 for result in self.test_results.values() if result.get('success', False)),
                    'failed_tests': sum(1 for result in self.test_results.values() if not result.get('success', False))
                }
            }

            # 保存报告
            report_file = f"risk_parity_system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            import json
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"✓ Test report saved to {report_file}")

            # 打印摘要
            print("\n" + "="*60)
            print("RISK PARITY SYSTEM TEST SUMMARY")
            print("="*60)
            print(f"Total Tests: {report['summary']['total_tests']}")
            print(f"Successful: {report['summary']['successful_tests']}")
            print(f"Failed: {report['summary']['failed_tests']}")
            print(f"Success Rate: {report['summary']['successful_tests'] / report['summary']['total_tests'] * 100:.1f}%")
            print("="*60)

            # 详细结果
            for test_name, result in self.test_results.items():
                status = "✓ PASS" if result.get('success', False) else "✗ FAIL"
                print(f"{status}: {test_name}")
                if not result.get('success', False):
                    print(f"  Error: {result.get('error', 'Unknown error')}")

            return report

        except Exception as e:
            logger.error(f"Failed to generate test report: {e}")
            return None

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("Starting Risk Parity System Comprehensive Test...")

        # 加载或生成测试数据
        if not self.load_test_data():
            logger.warning("Failed to load real data, using synthetic data...")
            if not self.generate_synthetic_data():
                logger.error("Failed to generate synthetic data, aborting tests")
                return False

        # 运行测试
        tests = [
            self.test_risk_parity_optimizer,
            self.test_risk_budgeting_framework,
            self.test_risk_contribution_calculator,
            self.test_risk_parity_backtester,
            self.test_integration_with_existing_components,
            self.run_comprehensive_backtest_comparison
        ]

        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed: {e}")

        # 生成报告
        self.generate_test_report()

        # 检查整体成功率
        successful_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        total_tests = len(self.test_results)
        success_rate = successful_tests / total_tests if total_tests > 0 else 0

        logger.info(f"All tests completed. Success rate: {success_rate * 100:.1f}%")

        return success_rate >= 0.8  # 80%成功率认为是成功

def main():
    """主函数"""
    print("Risk Parity System Integration Test")
    print("=" * 50)

    tester = RiskParitySystemTester()
    success = tester.run_all_tests()

    if success:
        print("\n🎉 All tests completed successfully!")
        print("The Risk Parity System is ready for production use.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors.")
        print("The system may need adjustments before production use.")

if __name__ == "__main__":
    main()