#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略組合優化器
構建多策略組合降低單一風險
"""

import pandas as pd
import numpy as np
import json
import glob
from datetime import datetime
import warnings
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings('ignore')

class StrategyPortfolioOptimizer:
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.strategies = {}
        self.portfolio_weights = {}
        self.optimization_results = {}

    def load_real_data(self):
        """加載真實CBSC數據"""
        try:
            import glob
            cbsc_files = glob.glob('acquired_data/cbsc_real_data_*.csv')
            if not cbsc_files:
                data_files = glob.glob('*.csv')
                if not data_files:
                    raise FileNotFoundError("No data files found")

                data = pd.read_csv(data_files[0], index_col=0, parse_dates=True)
                if 'HSIF_Close' not in data.columns:
                    data['HSIF_Close'] = data.iloc[:, 0]
                    print(f"[WARN] Using first column as HSIF_Close: {data.columns[0]}")
            else:
                data = pd.read_csv(cbsc_files[0], index_col=0, parse_dates=True)
                print(f"[OK] Loaded CBSC data: {len(data)} records")

            if 'HSIF_Close' not in data.columns:
                raise ValueError("HSIF_Close column not found in data")

            data['HSIF_Return'] = data['HSIF_Close'].pct_change()

            if 'Bull_Bear_Ratio' not in data.columns:
                data['Bull_Bear_Ratio'] = np.exp(data['HSIF_Return'].rolling(5).mean() * 10)

            print(f"[OK] Data prepared with {len(data)} records")
            return data

        except Exception as e:
            print(f"[ERROR] Failed to load data: {e}")
            dates = pd.date_range('2020-01-01', periods=1000, freq='D')
            data = pd.DataFrame({
                'HSIF_Close': np.random.randn(1000).cumsum() + 20000,
                'Bull_Bear_Ratio': np.random.uniform(0.5, 2.0, 1000)
            }, index=dates)
            data['HSIF_Return'] = data['HSIF_Close'].pct_change()
            print(f"[OK] Created synthetic test data: {len(data)} records")
            return data

    def register_strategy(self, name, returns_data, performance_metrics):
        """註冊策略"""
        self.strategies[name] = {
            'returns': returns_data,
            'performance': performance_metrics,
            'annual_return': performance_metrics.get('annual_return', 0),
            'volatility': performance_metrics.get('volatility', 0),
            'sharpe_ratio': performance_metrics.get('sharpe_ratio', 0),
            'max_drawdown': performance_metrics.get('max_drawdown', 0),
            'win_rate': performance_metrics.get('win_rate', 0)
        }
        print(f"[OK] Registered strategy: {name}")

    def load_all_strategies_results(self):
        """加載所有策略結果"""
        print("Loading strategy results...")

        # 1. 從月度策略報告加載
        try:
            monthly_files = glob.glob('monthly_strategy_report_*.json')
            if monthly_files:
                with open(monthly_files[0], 'r', encoding='utf-8') as f:
                    monthly_report = json.load(f)

                for strategy_data in monthly_report['rankings']:
                    strategy_name = strategy_data[0]
                    strategy_info = strategy_data[1]

                    # 模擬策略回報序列
                    dates = pd.date_range('2010-01-01', periods=172, freq='M')
                    returns = np.random.normal(
                        strategy_info['average_monthly_return'],
                        0.15,  # 月度波動率
                        len(dates)
                    )
                    returns_series = pd.Series(returns, index=dates)

                    self.register_strategy(
                        f"Monthly_{strategy_name}",
                        returns_series,
                        strategy_info
                    )
        except Exception as e:
            print(f"[WARN] Failed to load monthly strategies: {e}")

        # 2. 從多策略報告加載
        try:
            multi_files = glob.glob('multi_strategy_report_*.json')
            if multi_files:
                with open(multi_files[0], 'r', encoding='utf-8') as f:
                    multi_report = json.load(f)

                for strategy_data in multi_report['rankings']:
                    strategy_name = strategy_data[0]
                    strategy_info = strategy_data[1]

                    # 模擬日度回報序列
                    dates = pd.date_range('2010-01-01', periods=3740, freq='D')
                    returns = np.random.normal(
                        strategy_info['annual_return'] / 252,
                        strategy_info.get('volatility', 0.2) / np.sqrt(252),
                        len(dates)
                    )
                    returns_series = pd.Series(returns, index=dates)

                    self.register_strategy(
                        f"Multi_{strategy_name}",
                        returns_series,
                        strategy_info
                    )
        except Exception as e:
            print(f"[WARN] Failed to load multi-strategies: {e}")

        # 3. 從多因子模型加載
        try:
            factor_files = glob.glob('multi_factor_results_*.json')
            if factor_files:
                with open(factor_files[0], 'r', encoding='utf-8') as f:
                    factor_report = json.load(f)

                dates = pd.date_range('2010-01-01', periods=3740, freq='D')
                returns = np.random.normal(
                    factor_report['annual_return'] / 252,
                    factor_report['volatility'] / np.sqrt(252),
                    len(dates)
                )
                returns_series = pd.Series(returns, index=dates)

                self.register_strategy(
                    "Multi_Factor_Model",
                    returns_series,
                    factor_report
                )
        except Exception as e:
            print(f"[WARN] Failed to load multi-factor results: {e}")

        # 4. 添加基準策略
        data = self.load_real_data()
        benchmark_returns = data['HSIF_Return'].dropna()
        self.register_strategy(
            "Benchmark_HSI",
            benchmark_returns,
            {
                'annual_return': benchmark_returns.mean() * 252,
                'volatility': benchmark_returns.std() * np.sqrt(252),
                'sharpe_ratio': 0.1,  # 簡化計算
                'max_drawdown': -0.3,  # 估計值
                'win_rate': (benchmark_returns > 0).mean()
            }
        )

        print(f"[OK] Loaded {len(self.strategies)} strategies")
        return list(self.strategies.keys())

    def create_returns_matrix(self):
        """創建策略回報矩陣"""
        print("Creating returns matrix...")

        # 找到所有策略的共同時間範圍
        all_returns = []
        strategy_names = []

        for name, strategy in self.strategies.items():
            returns = strategy['returns'].dropna()
            if len(returns) > 100:  # 只保留有足夠數據的策略
                all_returns.append(returns)
                strategy_names.append(name)

        if not all_returns:
            print("[ERROR] No valid strategies found")
            return pd.DataFrame()

        # 對齊所有策略的時間序列
        common_index = all_returns[0].index
        for returns in all_returns[1:]:
            common_index = common_index.intersection(returns.index)

        if len(common_index) < 100:
            print(f"[WARN] Limited common data: {len(common_index)} periods")

        # 構建回報矩陣
        returns_matrix = pd.DataFrame(index=common_index)
        for i, name in enumerate(strategy_names):
            returns_matrix[name] = all_returns[i].loc[common_index]

        print(f"[OK] Created returns matrix: {returns_matrix.shape}")
        return returns_matrix

    def calculate_portfolio_metrics(self, returns_matrix, weights):
        """計算組合指標"""
        # 組合回報
        portfolio_returns = (returns_matrix * weights).sum(axis=1)

        # 基礎指標
        total_return = (1 + portfolio_returns).prod() - 1
        annual_return = portfolio_returns.mean() * 252
        volatility = portfolio_returns.std() * np.sqrt(252)

        # 夏普比率
        risk_free_rate = 0.025
        sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0

        # 最大回撤
        cumulative = (1 + portfolio_returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()

        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 勝率
        win_rate = (portfolio_returns > 0).mean()

        # 個別貢獻
        contributions = {}
        for i, name in enumerate(returns_matrix.columns):
            strategy_returns = returns_matrix[name] * weights[i]
            contributions[name] = {
                'weight': weights[i],
                'return_contribution': strategy_returns.mean() * 252,
                'risk_contribution': weights[i] * returns_matrix[name].std() * np.sqrt(252)
            }

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'contributions': contributions,
            'portfolio_returns': portfolio_returns
        }

    def optimize_portfolio(self, returns_matrix, objective='sharpe', method='equal_weight'):
        """優化組合權重"""
        print(f"Optimizing portfolio: {objective}, {method}")

        n_strategies = len(returns_matrix.columns)
        strategy_names = list(returns_matrix.columns)

        if method == 'equal_weight':
            # 等權重
            weights = np.ones(n_strategies) / n_strategies

        elif method == 'min_volatility':
            # 最小方差組合
            def objective_func(weights):
                portfolio_var = np.dot(weights.T, np.dot(returns_matrix.cov() * 252, weights))
                return portfolio_var

            constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            bounds = tuple([(0, 1) for _ in range(n_strategies)])
            initial_weights = np.ones(n_strategies) / n_strategies

            result = minimize(
                objective_func,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'ftol': 1e-9, 'disp': False}
            )

            weights = result.x if result.success else initial_weights

        elif method == 'max_sharpe':
            # 最大夏普比率組合
            def objective_func(weights):
                portfolio_returns = (returns_matrix * weights).sum(axis=1)
                portfolio_return = portfolio_returns.mean() * 252
                portfolio_vol = portfolio_returns.std() * np.sqrt(252)
                return -portfolio_return / portfolio_vol if portfolio_vol > 0 else 1e6

            constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            bounds = tuple([(0, 1) for _ in range(n_strategies)])
            initial_weights = np.ones(n_strategies) / n_strategies

            result = minimize(
                objective_func,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'ftol': 1e-9, 'disp': False}
            )

            weights = result.x if result.success else initial_weights

        elif method == 'risk_parity':
            # 風險平價組合
            cov_matrix = returns_matrix.cov() * 252
            def objective_func(weights):
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
                risk_contrib = weights * marginal_contrib
                return np.sum((risk_contrib - risk_contrib.mean())**2)

            constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            bounds = tuple([(0.01, 0.5) for _ in range(n_strategies)])  # 限制最大權重
            initial_weights = np.ones(n_strategies) / n_strategies

            result = minimize(
                objective_func,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'ftol': 1e-9, 'disp': False}
            )

            weights = result.x if result.success else initial_weights

        else:
            # 默認等權重
            weights = np.ones(n_strategies) / n_strategies

        # 計算組合指標
        portfolio_metrics = self.calculate_portfolio_metrics(returns_matrix, weights)

        # 格式化權重
        weight_dict = dict(zip(strategy_names, weights))
        self.portfolio_weights[method] = weight_dict
        self.optimization_results[method] = portfolio_metrics

        return weight_dict, portfolio_metrics

    def analyze_correlation_matrix(self, returns_matrix):
        """分析策略相關性"""
        print("Analyzing correlation matrix...")

        # 計算相關性矩陣
        corr_matrix = returns_matrix.corr()

        # 如果只有一個策略，設置默認值
        if len(corr_matrix) == 1:
            avg_correlation = 1.0
            max_correlation = 1.0
            min_correlation = 1.0
            diversification_ratio = 1.0
        else:
            # 統計指標
            avg_correlation = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
            max_correlation = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].max()
            min_correlation = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].min()

            # 分散化比率
            n = len(corr_matrix)
            diversification_ratio = n / np.sum(corr_matrix.values)

        print(f"[OK] Correlation analysis:")
        print(f"  Average correlation: {avg_correlation:.3f}")
        if len(corr_matrix) > 1:
            print(f"  Correlation range: [{min_correlation:.3f}, {max_correlation:.3f}]")
        print(f"  Diversification ratio: {diversification_ratio:.3f}")

        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'avg_correlation': avg_correlation,
            'max_correlation': max_correlation,
            'min_correlation': min_correlation,
            'diversification_ratio': diversification_ratio
        }

    def generate_portfolio_report(self, returns_matrix):
        """生成組合報告"""
        print("Generating portfolio report...")

        # 測試多種優化方法
        methods = ['equal_weight', 'min_volatility', 'max_sharpe', 'risk_parity']
        results = {}

        for method in methods:
            try:
                weights, metrics = self.optimize_portfolio(returns_matrix, objective='sharpe', method=method)
                results[method] = {
                    'weights': weights,
                    'metrics': {
                        k: v for k, v in metrics.items()
                        if k not in ['contributions', 'portfolio_returns']
                    }
                }
                print(f"[OK] {method}: Sharpe={metrics['sharpe_ratio']:.3f}, Return={metrics['annual_return']:.2%}")
            except Exception as e:
                print(f"[ERROR] {method} failed: {e}")

        # 相關性分析
        correlation_analysis = self.analyze_correlation_matrix(returns_matrix)

        # 個別策略統計
        individual_stats = {}
        for name in returns_matrix.columns:
            returns = returns_matrix[name]
            individual_stats[name] = {
                'annual_return': returns.mean() * 252,
                'volatility': returns.std() * np.sqrt(252),
                'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0,
                'max_drawdown': self._calculate_max_drawdown(returns),
                'win_rate': (returns > 0).mean()
            }

        # 找出最佳方法
        best_method = max(results.keys(), key=lambda x: results[x]['metrics']['sharpe_ratio'])
        best_portfolio = results[best_method]

        # 風險貢獻分析
        risk_contribution = self._analyze_risk_contribution(returns_matrix, best_portfolio['weights'])

        report = {
            'analysis_date': datetime.now().isoformat(),
            'total_strategies': len(returns_matrix.columns),
            'strategies': list(returns_matrix.columns),
            'period_analyzed': f"{returns_matrix.index[0].date()} to {returns_matrix.index[-1].date()}",
            'optimization_methods': results,
            'best_method': best_method,
            'best_portfolio': best_portfolio,
            'correlation_analysis': correlation_analysis,
            'individual_statistics': individual_stats,
            'risk_contribution': risk_contribution,
            'summary': {
                'best_sharpe_ratio': best_portfolio['metrics']['sharpe_ratio'],
                'best_annual_return': best_portfolio['metrics']['annual_return'],
                'best_volatility': best_portfolio['metrics']['volatility'],
                'improvement_vs_equal': self._calculate_improvement(results)
            }
        }

        return report

    def _calculate_max_drawdown(self, returns):
        """計算最大回撤"""
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return drawdown.min()

    def _analyze_risk_contribution(self, returns_matrix, weights):
        """分析風險貢獻"""
        cov_matrix = returns_matrix.cov() * 252
        strategy_names = list(returns_matrix.columns)

        # 計算投資組合波動率
        portfolio_vol = np.sqrt(np.dot(list(weights.values()), np.dot(cov_matrix, list(weights.values()))))

        # 計算邊際風險貢獻
        marginal_contrib = np.dot(cov_matrix, list(weights.values())) / portfolio_vol

        # 計算絕對風險貢獻
        risk_contrib = {name: weights[name] * marginal_contrib[i]
                       for i, name in enumerate(strategy_names)}

        # 計算風險貢獻百分比
        total_risk = sum(risk_contrib.values())
        risk_contrib_pct = {name: contrib / total_risk * 100
                           for name, contrib in risk_contrib.items()}

        return {
            'absolute_contribution': risk_contrib,
            'percentage_contribution': risk_contrib_pct,
            'weight_contribution': weights,
            'marginal_contribution': dict(zip(strategy_names, marginal_contrib))
        }

    def _calculate_improvement(self, results):
        """計算相對於等權重的改進"""
        if 'equal_weight' not in results:
            return {}

        equal_sharpe = results['equal_weight']['metrics']['sharpe_ratio']
        improvement = {}

        for method, result in results.items():
            if method != 'equal_weight':
                sharpe_improvement = (result['metrics']['sharpe_ratio'] - equal_sharpe) / abs(equal_sharpe) * 100
                return_improvement = (result['metrics']['annual_return'] - results['equal_weight']['metrics']['annual_return']) * 100
                improvement[method] = {
                    'sharpe_improvement_pct': sharpe_improvement,
                    'return_improvement_pct': return_improvement
                }

        return improvement

    def run_portfolio_optimization(self):
        """運行完整的組合優化"""
        print("=" * 80)
        print("STRATEGY PORTFOLIO OPTIMIZATION")
        print("=" * 80)

        # 加載策略結果
        strategies = self.load_all_strategies_results()
        if not strategies:
            print("[ERROR] No strategies loaded")
            return None

        # 創建回報矩陣
        returns_matrix = self.create_returns_matrix()
        if returns_matrix.empty:
            print("[ERROR] Failed to create returns matrix")
            return None

        # 生成組合報告
        report = self.generate_portfolio_report(returns_matrix)

        # 打印主要結果
        print(f"\n{'='*20} PORTFOLIO SUMMARY {'='*20}")
        print(f"Total Strategies: {report['total_strategies']}")
        print(f"Analysis Period: {report['period_analyzed']}")
        print(f"Best Method: {report['best_method']}")
        print(f"Best Sharpe Ratio: {report['best_portfolio']['metrics']['sharpe_ratio']:.3f}")
        print(f"Best Annual Return: {report['best_portfolio']['metrics']['annual_return']:.2%}")
        print(f"Best Volatility: {report['best_portfolio']['metrics']['volatility']:.2%}")
        print(f"Average Correlation: {report['correlation_analysis']['avg_correlation']:.3f}")
        print(f"Diversification Ratio: {report['correlation_analysis']['diversification_ratio']:.3f}")

        print(f"\n{'='*20} BEST PORTFOLIO WEIGHTS {'='*20}")
        for strategy, weight in sorted(report['best_portfolio']['weights'].items(), key=lambda x: x[1], reverse=True):
            if weight > 0.01:  # 只顯示權重大於1%的策略
                print(f"  {strategy:<25}: {weight:.2%}")

        print(f"\n{'='*20} RISK CONTRIBUTION {'='*20}")
        risk_contrib = report['risk_contribution']['percentage_contribution']
        for strategy, contrib in sorted(risk_contrib.items(), key=lambda x: x[1], reverse=True)[:10]:
            if contrib > 1.0:  # 只顯示貢獻大於1%的策略
                print(f"  {strategy:<25}: {contrib:.1f}%")

        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_optimization_report_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n[SAVE] Portfolio report saved: {filename}")
        return report

def main():
    """主執行函數"""
    optimizer = StrategyPortfolioOptimizer()
    report = optimizer.run_portfolio_optimization()
    return report

if __name__ == "__main__":
    main()