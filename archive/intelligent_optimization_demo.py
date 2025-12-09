#!/usr/bin/env python3
"""
智能參數優化演示系統
Intelligent Parameter Optimization Demo

展示專業級量化交易參數優化的完整流程：
1. 網格搜尋 vs 貝葉斯優化 vs 遺傳演算法
2. 交叉驗證防止過度擬合
3. 前進分析驗證穩健性
4. 多種優化方法的性能比較
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
import time
import matplotlib.pyplot as plt
import seaborn as sns

# 導入智能優化系統
from src.optimization.intelligent_parameter_optimizer import (
    IntelligentParameterOptimizer,
    create_optimization_config,
    OptimizationConfig
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyBacktester:
    """策略回測器"""

    def __init__(self):
        self.transaction_cost = 0.001  # 0.1% 手續費
        self.risk_free_rate = 0.03    # 3% 無風險利率

    def rsi_strategy_backtest(self, params: Dict[str, Any], data: pd.DataFrame) -> Any:
        """RSI策略回測"""
        try:
            # 參數驗證
            window = params.get('window', 14)
            buy_threshold = params.get('buy_threshold', 0.3)
            sell_threshold = params.get('sell_threshold', 0.7)

            # 計算RSI
            returns = data['close'].pct_change()
            gains = returns.where(returns > 0, 0)
            losses = -returns.where(returns < 0, 0)

            avg_gains = gains.rolling(window).mean()
            avg_losses = losses.rolling(window).mean()

            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))

            # 生成信號
            buy_signals = rsi < buy_threshold
            sell_signals = rsi > sell_threshold

            # 一買一賣邏輯
            positions = pd.Series(0, index=data.index)
            holding = False

            for i in range(1, len(data)):
                if buy_signals.iloc[i] and not holding:
                    positions.iloc[i] = 1
                    holding = True
                elif sell_signals.iloc[i] and holding:
                    positions.iloc[i] = -1
                    holding = False
                elif holding:
                    positions.iloc[i] = 1

            # 計算回報
            strategy_returns = positions.shift(1) * returns - self.transaction_cost * abs(positions.diff())

            # 計算性能指標
            total_return = (1 + strategy_returns).prod() - 1
            sharpe_ratio = self._calculate_sharpe_ratio(strategy_returns)
            max_drawdown = self._calculate_max_drawdown(strategy_returns)
            win_rate = (strategy_returns > 0).mean()

            # 返回結果
            from src.optimization.intelligent_parameter_optimizer import ParameterResult
            return ParameterResult(
                parameters=params,
                sharpe_ratio=sharpe_ratio,
                total_return=total_return,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                cv_score=0.0,  # 將在外部計算
                walk_forward_score=0.0,
                overfitting_risk=0.0,
                robustness_score=0.0,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"RSI strategy backtest failed: {e}")
            # 返回最差結果
            from src.optimization.intelligent_parameter_optimizer import ParameterResult
            return ParameterResult(
                parameters=params,
                sharpe_ratio=-10.0,
                total_return=-1.0,
                max_drawdown=1.0,
                win_rate=0.0,
                cv_score=0.0,
                walk_forward_score=0.0,
                overfitting_risk=1.0,
                robustness_score=0.0,
                timestamp=datetime.now()
            )

    def macd_strategy_backtest(self, params: Dict[str, Any], data: pd.DataFrame) -> Any:
        """MACD策略回測"""
        try:
            # 參數驗證
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            signal = params.get('signal', 9)

            # 計算MACD
            exp1 = data['close'].ewm(span=fast).mean()
            exp2 = data['close'].ewm(span=slow).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line

            # 生成信號
            buy_signals = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
            sell_signals = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

            # 一買一賣邏輯
            positions = pd.Series(0, index=data.index)
            holding = False

            for i in range(1, len(data)):
                if buy_signals.iloc[i] and not holding:
                    positions.iloc[i] = 1
                    holding = True
                elif sell_signals.iloc[i] and holding:
                    positions.iloc[i] = -1
                    holding = False
                elif holding:
                    positions.iloc[i] = 1

            # 計算回報
            returns = data['close'].pct_change()
            strategy_returns = positions.shift(1) * returns - self.transaction_cost * abs(positions.diff())

            # 計算性能指標
            total_return = (1 + strategy_returns).prod() - 1
            sharpe_ratio = self._calculate_sharpe_ratio(strategy_returns)
            max_drawdown = self._calculate_max_drawdown(strategy_returns)
            win_rate = (strategy_returns > 0).mean()

            # 返回結果
            from src.optimization.intelligent_parameter_optimizer import ParameterResult
            return ParameterResult(
                parameters=params,
                sharpe_ratio=sharpe_ratio,
                total_return=total_return,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                cv_score=0.0,
                walk_forward_score=0.0,
                overfitting_risk=0.0,
                robustness_score=0.0,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"MACD strategy backtest failed: {e}")
            from src.optimization.intelligent_parameter_optimizer import ParameterResult
            return ParameterResult(
                parameters=params,
                sharpe_ratio=-10.0,
                total_return=-1.0,
                max_drawdown=1.0,
                win_rate=0.0,
                cv_score=0.0,
                walk_forward_score=0.0,
                overfitting_risk=1.0,
                robustness_score=0.0,
                timestamp=datetime.now()
            )

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """計算Sharpe比率（3%無風險利率）"""
        excess_returns = returns - self.risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0
        return excess_returns.mean() / returns.std() * np.sqrt(252)

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """計算最大回撤"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

def create_sample_data(symbol: str = "0700.HK", days: int = 1095) -> pd.DataFrame:
    """創建樣本數據（使用模擬數據進行演示）"""
    dates = pd.date_range(start='2022-01-01', periods=days, freq='D')

    # 生成真實感的價格數據
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.02, days)
    prices = [100]

    for ret in returns:
        prices.append(prices[-1] * (1 + ret))

    prices = np.array(prices[1:])

    # 添加波動性
    high_prices = prices * np.random.uniform(1.0, 1.03, days)
    low_prices = prices * np.random.uniform(0.97, 1.0, days)
    volumes = np.random.randint(1000000, 10000000, days)

    data = pd.DataFrame({
        'open': prices * np.random.uniform(0.995, 1.005, days),
        'high': high_prices,
        'low': low_prices,
        'close': prices,
        'volume': volumes
    }, index=dates)

    return data

async def run_optimization_comparison():
    """運行優化方法比較"""
    print("=" * 80)
    print("智能參數優化系統演示")
    print("Intelligent Parameter Optimization Demo")
    print("=" * 80)
    print()

    # 創建樣本數據
    print("1. 準備數據 Preparing Data")
    print("-" * 40)
    data = create_sample_data()
    print(f"數據範圍: {data.index[0]} 至 {data.index[-1]}")
    print(f"數據點數: {len(data)}")
    print(f"價格範圍: {data['close'].min():.2f} - {data['close'].max():.2f}")
    print()

    # 創建回測器
    backtester = StrategyBacktester()

    # 測試不同優化方法
    optimization_methods = ['grid_search', 'bayesian', 'genetic']
    results = {}

    for method in optimization_methods:
        print(f"2.{optimization_methods.index(method) + 1} 測試 {method.upper()} 優化")
        print("-" * 40)

        # 創建優化配置
        config = create_optimization_config('RSI', method)
        config.max_iterations = 100 if method == 'grid_search' else 50
        config.parallel_workers = 8

        # 創建優化器
        optimizer = IntelligentParameterOptimizer(config)

        # 運行優化
        start_time = time.time()

        def objective_func(params, data):
            return backtester.rsi_strategy_backtest(params, data)

        try:
            result = optimizer.optimize(data, objective_func)
            end_time = time.time()

            # 記錄結果
            results[method] = {
                'best_sharpe': result.sharpe_ratio,
                'best_params': result.parameters,
                'cv_score': result.cv_score,
                'walk_forward_score': result.walk_forward_score,
                'overfitting_risk': result.overfitting_risk,
                'robustness_score': result.robustness_score,
                'execution_time': end_time - start_time,
                'total_return': result.total_return,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate
            }

            print(f"最佳Sharpe: {result.sharpe_ratio:.4f}")
            print(f"最佳參數: {result.parameters}")
            print(f"交叉驗證分數: {result.cv_score:.4f}")
            print(f"前進分析分數: {result.walk_forward_score:.4f}")
            print(f"過度擬合風險: {result.overfitting_risk:.3f}")
            print(f"穩健性分數: {result.robustness_score:.3f}")
            print(f"執行時間: {end_time - start_time:.1f}秒")

        except Exception as e:
            print(f"優化失敗: {e}")
            results[method] = {
                'best_sharpe': -10.0,
                'best_params': {},
                'error': str(e)
            }

        print()

    # 比較結果
    print("3. 優化方法比較 Comparison")
    print("-" * 40)

    comparison_data = []
    for method, result in results.items():
        if 'error' not in result:
            comparison_data.append({
                'Method': method.upper(),
                'Best Sharpe': result['best_sharpe'],
                'CV Score': result['cv_score'],
                'Walk-Forward': result['walk_forward_score'],
                'Overfitting Risk': result['overfitting_risk'],
                'Robustness': result['robustness_score'],
                'Time (s)': result['execution_time']
            })

    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        print(df_comparison.to_string(index=False, float_format='%.4f'))

        # 找出最佳方法
        best_method = df_comparison.loc[df_comparison['Walk-Forward'].idxmax(), 'Method']
        print(f"\n最佳方法: {best_method}")
        print(f"最佳前進分析分數: {df_comparison['Walk-Forward'].max():.4f}")

    print()
    print("4. 結論與建議 Conclusions & Recommendations")
    print("-" * 40)

    if comparison_data:
        print("網格搜尋: 適合參數空間較小的情況，保證找到全局最優")
        print("貝葉斯優化: 適合中等參數空間，平衡探索與利用")
        print("遺傳演算法: 適合大型參數空間，可處理複雜約束")
        print("交叉驗證: 有效防止過度擬合")
        print("前進分析: 驗證策略在未來的穩健性")

    print()
    print("=" * 80)
    print("智能參數優化演示完成")
    print("Intelligent Parameter Optimization Demo Completed")
    print("=" * 80)

    return results

async def demonstrate_parameter_combination_realities():
    """演示參數組合現實"""
    print("=" * 80)
    print("參數組合現實分析")
    print("Parameter Combination Reality Analysis")
    print("=" * 80)
    print()

    # 不同策略的參數組合數量
    strategies = {
        'RSI': {
            'params': {
                'window': list(range(5, 51, 5)),  # 10 choices
                'buy_threshold': [x/10 for x in range(10, 36, 5)],  # 6 choices
                'sell_threshold': [x/10 for x in range(65, 86, 5)]  # 5 choices
            }
        },
        'MACD': {
            'params': {
                'fast': list(range(5, 16, 2)),  # 6 choices
                'slow': list(range(20, 41, 5)),  # 5 choices
                'signal': list(range(5, 16, 2))  # 6 choices
            }
        },
        'Bollinger_Bands': {
            'params': {
                'window': list(range(10, 31, 5)),  # 5 choices
                'std': [x/10 for x in range(15, 26, 2)]  # 6 choices
            }
        }
    }

    print("1. 單一策略參數組合")
    print("-" * 30)
    total_single = 0
    for strategy, config in strategies.items():
        combinations = 1
        param_details = []
        for param_name, param_values in config['params'].items():
            combinations *= len(param_values)
            param_details.append(f"{param_name}: {len(param_values)}")

        total_single += combinations
        print(f"{strategy}: {combinations:,} 組合 ({', '.join(param_details)})")

    print(f"單一策略總計: {total_single:,} 組合")
    print()

    print("2. 多策略組合爆炸")
    print("-" * 30)

    # 常見組合
    common_combinations = [
        ('RSI + MACD', ['RSI', 'MACD']),
        ('RSI + MACD + Bollinger', ['RSI', 'MACD', 'Bollinger_Bands']),
        ('Complete System', ['RSI', 'MACD', 'Bollinger_Bands'])
    ]

    for combo_name, strategy_list in common_combinations:
        combinations = 1
        for strategy in strategy_list:
            for param_values in strategies[strategy]['params'].values():
                combinations *= len(param_values)

        print(f"{combo_name}: {combinations:,} 組合")

    print()

    print("3. 計算時間估算（假設每個組合0.1秒）")
    print("-" * 45)

    for combo_name, strategy_list in common_combinations:
        combinations = 1
        for strategy in strategy_list:
            for param_values in strategies[strategy]['params'].values():
                combinations *= len(param_values)

        time_seconds = combinations * 0.1
        if time_seconds < 60:
            time_str = f"{time_seconds:.1f} 秒"
        elif time_seconds < 3600:
            time_str = f"{time_seconds/60:.1f} 分鐘"
        elif time_seconds < 86400:
            time_str = f"{time_seconds/3600:.1f} 小時"
        else:
            time_str = f"{time_seconds/86400:.1f} 天"

        print(f"{combo_name}: {time_str}")

    print()

    print("4. 智能優化的必要性")
    print("-" * 30)
    print("網格搜尋: 適合小型參數空間")
    print("貝葉斯優化: 適合中型參數空間")
    print("遺傳演算法: 適合大型參數空間")
    print("分層優化: 先優化重要參數")
    print("預選機制: 基於歷史表現篩選")
    print("並行計算: 充分利用多核心")
    print()

async def main():
    """主函數"""
    try:
        # 演示參數組合現實
        await demonstrate_parameter_combination_realities()

        print("\n" + "=" * 80)
        print()

        # 運行優化比較
        results = await run_optimization_comparison()

        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intelligent_optimization_results_{timestamp}.json"

        import json
        with open(filename, 'w', encoding='utf-8') as f:
            # 轉換numpy類型為原生Python類型
            serializable_results = {}
            for key, value in results.items():
                if isinstance(value, dict):
                    serializable_results[key] = {
                        k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                        for k, v in value.items()
                    }
                else:
                    serializable_results[key] = value

            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        print(f"詳細結果已保存至: {filename}")

    except Exception as e:
        logger.error(f"演示失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())