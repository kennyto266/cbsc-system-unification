"""
CBSC Parameter Optimizer
CBSC參數優化器

Parameter optimization interface for CBSC strategies using VectorBT optimization.
使用VectorBT優化的CBSC策略參數優化接口。

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
from typing import Dict, List, Tuple, Optional, Any, Callable
import itertools
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

from data_loader import CBSCDataLoader
from signal_generator import CBSCSignalGenerator
from cbsc_backtester import CBSCBacktester

class CBSCOptimizer:
    """CBSC參數優化器 - 基於VectorBT的高性能優化引擎"""

    def __init__(self, sentiment_path: str, config: Optional[Dict] = None):
        """
        初始化優化器

        Args:
            sentiment_path: CBSC情緒數據路徑
            config: 優化配置參數
        """
        self.config = config or self._default_config()

        # 初始化回測器（用於數據準備）
        self.backtester = CBSCBacktester(sentiment_path, self.config.get('backtest_config', {}))

        # 優化結果存儲
        self.optimization_results = {}
        self.best_parameters = {}

        print("CBSC優化器初始化完成")

    def _default_config(self) -> Dict:
        """默認配置參數"""
        return {
            'backtest_config': {
                'initial_cash': 1000000,
                'fees': 0.003,
                'slippage': 0.001
            },
            'optimization_ranges': {
                'sentiment_threshold': [0.1, 0.2, 0.3, 0.4, 0.5],
                'rsi_overbought': [65, 70, 75, 80],
                'rsi_oversold': [20, 25, 30, 35],
                'signal_smoothing': [1, 3, 5, 7],
                'extreme_sentiment_boost': [1.2, 1.5, 1.8, 2.0]
            },
            'optimization_metric': 'sharpe_ratio',  # 優化目標
            'max_combinations': 1000,  # 最大參數組合數
            'cv_folds': 3  # 交叉驗證折數
        }

    def prepare_optimization_data(self, symbol: str = "0700.HK") -> bool:
        """
        準備優化數據

        Args:
            symbol: 股票代碼

        Returns:
            是否成功準備數據
        """
        success = self.backtester.prepare_data(symbol)
        if success:
            print(f"優化數據準備完成: {len(self.backtester.features_df)} 條記錄")
        return success

    def generate_parameter_grid(self) -> List[Dict]:
        """
        生成參數網格

        Returns:
            參數組合列表
        """
        ranges = self.config['optimization_ranges']
        keys = list(ranges.keys())
        values = list(ranges.values())

        # 生成所有組合
        combinations = list(itertools.product(*values))

        # 限制組合數量
        if len(combinations) > self.config['max_combinations']:
            # 隨機採樣
            np.random.shuffle(combinations)
            combinations = combinations[:self.config['max_combinations']]

        # 轉換為字典列表
        param_grid = []
        for combination in combinations:
            param_dict = dict(zip(keys, combination))
            param_grid.append(param_dict)

        print(f"生成參數網格: {len(param_grid)} 組合")
        return param_grid

    def evaluate_single_parameter_set(self, params: Dict, features_df: pd.DataFrame,
                                    price_data: pd.DataFrame) -> Dict[str, float]:
        """
        評估單個參數集

        Args:
            params: 參數字典
            features_df: 特徵數據
            price_data: 價格數據

        Returns:
            性能指標字典
        """
        try:
            # 創建自定義信號生成器
            signal_generator = CBSCSignalGenerator({
                'sentiment_threshold': params.get('sentiment_threshold', 0.3),
                'extreme_sentiment_boost': params.get('extreme_sentiment_boost', 1.5),
                'rsi_overbought': params.get('rsi_overbought', 70),
                'rsi_oversold': params.get('rsi_oversold', 30),
                'signal_smoothing': params.get('signal_smoothing', 3)
            })

            # 生成信號
            entries, exits = signal_generator.generate_vectorbt_signals(
                features_df, 'cbsc_aware'
            )

            # 創建投資組合
            portfolio = vbt.Portfolio.from_signals(
                close=price_data['close'],
                entries=entries,
                exits=exits,
                init_cash=self.config['backtest_config']['initial_cash'],
                fees=self.config['backtest_config']['fees'],
                slippage=self.config['backtest_config']['slippage'],
                freq='1D'
            )

            # 計算性能指標
            stats = portfolio.stats()
            returns = portfolio.returns()

            metrics = {
                'sharpe_ratio': float(stats['Sharpe Ratio']),
                'total_return': float(stats['Total Return [%]']),
                'max_drawdown': float(stats['Max Drawdown [%]']),
                'annual_return': float(stats['Annual Return [%]']),
                'win_rate': float(stats['Win Rate [%]']),
                'profit_factor': float(stats['Profit Factor']),
                'total_trades': int(stats['# Trades']),
                'sortino_ratio': float(returns.mean() / returns[returns < 0].std() if len(returns[returns < 0]) > 0 else 0),
                'volatility': float(returns.std() * np.sqrt(252))
            }

            return metrics

        except Exception as e:
            print(f"參數評估失敗: {params}, 錯誤: {e}")
            return {}

    def run_grid_search(self, symbol: str = "0700.HK") -> pd.DataFrame:
        """
        運行網格搜索優化

        Args:
            symbol: 股票代碼

        Returns:
            優化結果DataFrame
        """
        if not self.prepare_optimization_data(symbol):
            return pd.DataFrame()

        print("開始網格搜索優化...")

        # 生成參數網格
        param_grid = self.generate_parameter_grid()
        features_df = self.backtester.features_df
        price_data = self.backtester.price_data

        # 評估所有參數組合
        results = []
        total_combinations = len(param_grid)

        for i, params in enumerate(param_grid):
            if i % 50 == 0:
                print(f"進度: {i}/{total_combinations} ({i/total_combinations*100:.1f}%)")

            # 評估參數集
            metrics = self.evaluate_single_parameter_set(params, features_df, price_data)

            if metrics:
                result_row = params.copy()
                result_row.update(metrics)
                results.append(result_row)

        # 創建結果DataFrame
        if results:
            results_df = pd.DataFrame(results)

            # 排序（按優化目標）
            optimization_metric = self.config['optimization_metric']
            if optimization_metric in ['max_drawdown']:
                # 對於回撤等指標，越小越好
                results_df = results_df.sort_values(optimization_metric, ascending=True)
            else:
                # 對於收益等指標，越大越好
                results_df = results_df.sort_values(optimization_metric, ascending=False)

            self.optimization_results[symbol] = results_df

            # 保存最佳參數
            if not results_df.empty:
                self.best_parameters[symbol] = results_df.iloc[0].to_dict()

            print(f"網格搜索完成: {len(results_df)} 個有效結果")
            return results_df

        return pd.DataFrame()

    def run_random_search(self, symbol: str = "0700.HK", n_iterations: int = 200) -> pd.DataFrame:
        """
        運行隨機搜索優化

        Args:
            symbol: 股票代碼
            n_iterations: 迭代次數

        Returns:
            優化結果DataFrame
        """
        if not self.prepare_optimization_data(symbol):
            return pd.DataFrame()

        print(f"開始隨機搜索優化: {n_iterations} 次迭代")

        ranges = self.config['optimization_ranges']
        features_df = self.backtester.features_df
        price_data = self.backtester.price_data

        results = []

        for i in range(n_iterations):
            if i % 20 == 0:
                print(f"進度: {i}/{n_iterations} ({i/n_iterations*100:.1f}%)")

            # 隨機生成參數
            params = {}
            for param_name, param_values in ranges.items():
                params[param_name] = np.random.choice(param_values)

            # 評估參數集
            metrics = self.evaluate_single_parameter_set(params, features_df, price_data)

            if metrics:
                result_row = params.copy()
                result_row.update(metrics)
                results.append(result_row)

        # 創建結果DataFrame
        if results:
            results_df = pd.DataFrame(results)

            # 排序
            optimization_metric = self.config['optimization_metric']
            if optimization_metric in ['max_drawdown']:
                results_df = results_df.sort_values(optimization_metric, ascending=True)
            else:
                results_df = results_df.sort_values(optimization_metric, ascending=False)

            print(f"隨機搜索完成: {len(results_df)} 個有效結果")
            return results_df

        return pd.DataFrame()

    def run_bayesian_optimization(self, symbol: str = "0700.HK", n_calls: int = 50) -> pd.DataFrame:
        """
        運行貝葉斯優化（簡化版）

        Args:
            symbol: 股票代碼
            n_calls: 優化調用次數

        Returns:
            優化結果DataFrame
        """
        # 簡化實現：使用更智能的隨機搜索模擬貝葉斯優化
        print("運行貝葉斯優化（智能搜索模式）...")

        # 第一階段：寬範圍搜索
        broad_results = self.run_random_search(symbol, n_calls // 2)

        if broad_results.empty:
            return pd.DataFrame()

        # 第二階段：基於最佳結果的局部搜索
        best_params = broad_results.iloc[0]
        ranges = self.config['optimization_ranges']

        # 縮小搜索範圍
        focused_ranges = {}
        for param_name, param_values in ranges.items():
            if param_name in best_params:
                best_value = best_params[param_name]
                if isinstance(param_values[0], (int, float)):
                    # 數值參數：在最佳值附近搜索
                    if len(param_values) > 1:
                        param_values = sorted(param_values)
                        best_idx = param_values.index(best_value)
                        window = max(1, len(param_values) // 4)
                        start_idx = max(0, best_idx - window)
                        end_idx = min(len(param_values), best_idx + window + 1)
                        focused_ranges[param_name] = param_values[start_idx:end_idx]
                    else:
                        focused_ranges[param_name] = param_values
                else:
                    focused_ranges[param_name] = [best_value]

        # 臨時更新範圍
        original_ranges = self.config['optimization_ranges']
        self.config['optimization_ranges'] = focused_ranges

        # 局部精細搜索
        focused_results = self.run_random_search(symbol, n_calls // 2)

        # 恢復原始範圍
        self.config['optimization_ranges'] = original_ranges

        # 合併結果
        if not focused_results.empty:
            combined_results = pd.concat([broad_results, focused_results], ignore_index=True)

            # 排序
            optimization_metric = self.config['optimization_metric']
            if optimization_metric in ['max_drawdown']:
                combined_results = combined_results.sort_values(optimization_metric, ascending=True)
            else:
                combined_results = combined_results.sort_values(optimization_metric, ascending=False)

            print(f"貝葉斯優化完成: {len(combined_results)} 個結果")
            return combined_results

        return broad_results

    def get_optimization_summary(self, symbol: str = "0700.HK") -> Dict:
        """
        獲取優化結果摘要

        Args:
            symbol: 股票代碼

        Returns:
            優化摘要字典
        """
        if symbol not in self.optimization_results:
            return {"error": "沒有找到優化結果"}

        results_df = self.optimization_results[symbol]
        best_params = self.best_parameters[symbol]

        summary = {
            'symbol': symbol,
            'total_combinations_tested': len(results_df),
            'best_parameters': {k: v for k, v in best_params.items()
                             if k in self.config['optimization_ranges']},
            'best_performance': {
                'sharpe_ratio': best_params.get('sharpe_ratio', 0),
                'total_return': best_params.get('total_return', 0),
                'max_drawdown': best_params.get('max_drawdown', 0),
                'annual_return': best_params.get('annual_return', 0),
                'win_rate': best_params.get('win_rate', 0)
            },
            'optimization_metric': self.config['optimization_metric'],
            'parameter_sensitivity': self._analyze_parameter_sensitivity(results_df)
        }

        return summary

    def _analyze_parameter_sensitivity(self, results_df: pd.DataFrame) -> Dict:
        """分析參數敏感性"""
        sensitivity = {}
        ranges = self.config['optimization_ranges']

        for param_name in ranges:
            if param_name in results_df.columns:
                # 計算每個參數值對應的平均性能
                param_performance = results_df.groupby(param_name)[self.config['optimization_metric']].mean()

                # 計算性能範圍
                performance_range = param_performance.max() - param_performance.min()
                performance_std = param_performance.std()

                sensitivity[param_name] = {
                    'performance_range': float(performance_range),
                    'performance_std': float(performance_std),
                    'best_value': float(param_performance.idxmax()),
                    'worst_value': float(param_performance.idxmin())
                }

        return sensitivity

    def plot_optimization_results(self, symbol: str = "0700.HK",
                                 save_path: Optional[str] = None) -> None:
        """
        繪製優化結果

        Args:
            symbol: 股票代碼
            save_path: 保存路徑
        """
        if symbol not in self.optimization_results:
            print("沒有找到優化結果進行繪製")
            return

        results_df = self.optimization_results[symbol]

        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{symbol} CBSC策略參數優化結果', fontsize=16)

        # 1. 參數重要性
        ax1 = axes[0, 0]
        sensitivity = self._analyze_parameter_sensitivity(results_df)
        if sensitivity:
            params = list(sensitivity.keys())
            importance = [sensitivity[param]['performance_range'] for param in params]
            ax1.barh(params, importance)
            ax1.set_title('參數重要性 (性能範圍)')
            ax1.set_xlabel('性能範圍')

        # 2. 最佳參數分布
        ax2 = axes[0, 1]
        top_10 = results_df.head(10)
        if 'sentiment_threshold' in top_10.columns:
            ax2.hist(top_10['sentiment_threshold'], alpha=0.7, bins=5)
            ax2.set_title('前10名參數分布')
            ax2.set_xlabel('情緒閾值')

        # 3. 散點圖：Sharpe vs Return
        ax3 = axes[1, 0]
        if 'sharpe_ratio' in results_df.columns and 'total_return' in results_df.columns:
            scatter = ax3.scatter(results_df['total_return'], results_df['sharpe_ratio'],
                                alpha=0.6, c=results_df['max_drawdown'], cmap='RdYlGn_r')
            ax3.set_xlabel('總收益率 (%)')
            ax3.set_ylabel('Sharpe比率')
            ax3.set_title('風險收益散點圖')
            plt.colorbar(scatter, ax=ax3, label='最大回撤 (%)')

        # 4. 收敛圖
        ax4 = axes[1, 1]
        optimization_metric = self.config['optimization_metric']
        if optimization_metric in results_df.columns:
            cumulative_best = results_df[optimization_metric].expanding().max()
            ax4.plot(cumulative_best.values)
            ax4.set_title(f'優化收敛過程 ({optimization_metric})')
            ax4.set_xlabel('測試次數')
            ax4.set_ylabel('最佳值')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"優化結果圖表已保存到: {save_path}")

        plt.show()

def main():
    """測試CBSC優化器"""
    print("=== CBSC 參數優化器測試 ===")

    # 初始化優化器
    sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
    optimizer = CBSCOptimizer(sentiment_path)

    # 運行優化
    print("\n1. 運行隨機搜索優化...")
    results = optimizer.run_random_search("0700.HK", n_iterations=50)

    if not results.empty:
        # 顯示結果
        print("\n2. 優化結果 (前10名):")
        display_cols = ['sentiment_threshold', 'rsi_overbought', 'rsi_oversold',
                       'sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate']
        available_cols = [col for col in display_cols if col in results.columns]
        print(results[available_cols].head(10).round(3))

        # 摘要信息
        print("\n3. 優化摘要:")
        summary = optimizer.get_optimization_summary("0700.HK")
        print(f"測試組合數: {summary['total_combinations_tested']}")
        print(f"最佳Sharpe比率: {summary['best_performance']['sharpe_ratio']:.3f}")
        print(f"最佳總收益率: {summary['best_performance']['total_return']:.2f}%")

        print("\n✅ CBSC優化器測試完成！")
    else:
        print("❌ 優化失敗")

if __name__ == "__main__":
    main()