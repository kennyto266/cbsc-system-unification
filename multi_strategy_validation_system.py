#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多策略組合驗證系統
使用真實認證框架測試多種策略組合
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MultiStrategyValidator:
    def __init__(self):
        self.strategies = {}
        self.results = {}

    def load_real_data(self):
        """加載真實CBSC數據"""
        try:
            import glob
            cbsc_files = glob.glob('acquired_data/cbsc_real_data_*.csv')
            if not cbsc_files:
                raise FileNotFoundError("No CBSC data files found")

            data = pd.read_csv(cbsc_files[0], index_col=0, parse_dates=True)
            print(f"[OK] Loaded {len(data)} records from {cbsc_files[0]}")
            return data

        except Exception as e:
            print(f"[ERROR] Failed to load CBSC data: {e}")
            return None

    def register_strategy(self, name, implementation_func, params=None):
        """註冊策略"""
        self.strategies[name] = {
            'implementation': implementation_func,
            'params': params or {},
            'name': name
        }
        print(f"[OK] Registered strategy: {name}")

    def implement_rsi_strategy(self, data, params=None):
        """RSI策略實現"""
        params = params or {'period': 14, 'overbought': 70, 'oversold': 30}

        # 計算RSI
        delta = data['HSIF_Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=params['period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=params['period']).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # 生成信號（低頻率版本 - 月度檢查）
        data['rsi_signal'] = 0
        data.loc[data['RSI'] < params['oversold'], 'rsi_signal'] = 1
        data.loc[data['RSI'] > params['overbought'], 'rsi_signal'] = -1

        # 每月只檢查一次信號
        monthly_check = data.resample('M').first()
        data['final_signal'] = np.nan

        for date, row in monthly_check.iterrows():
            if row['rsi_signal'] != 0:
                data.loc[date:, 'final_signal'] = row['rsi_signal']

        data['final_signal'] = data['final_signal'].fillna(0)

        return data

    def implement_bollinger_strategy(self, data, params=None):
        """布林帶策略實現"""
        params = params or {'period': 20, 'std_dev': 2.0}

        # 計算布林帶
        sma = data['HSIF_Close'].rolling(window=params['period']).mean()
        std = data['HSIF_Close'].rolling(window=params['period']).std()

        data['BB_Upper'] = sma + (std * params['std_dev'])
        data['BB_Lower'] = sma - (std * params['std_dev'])
        data['BB_Middle'] = sma

        # 生成信號（月度檢查）
        data['bb_signal'] = 0
        data.loc[data['HSIF_Close'] < data['BB_Lower'], 'bb_signal'] = 1
        data.loc[data['HSIF_Close'] > data['BB_Upper'], 'bb_signal'] = -1

        # 每月只檢查一次信號
        monthly_check = data.resample('M').first()
        data['final_signal'] = np.nan

        for date, row in monthly_check.iterrows():
            if row['bb_signal'] != 0:
                data.loc[date:, 'final_signal'] = row['bb_signal']

        data['final_signal'] = data['final_signal'].fillna(0)

        return data

    def implement_trend_following(self, data, params=None):
        """趨勢跟蹤策略實現"""
        params = params or {'short_ma': 20, 'long_ma': 60}

        # 計算移動平均線
        data['MA_Short'] = data['HSIF_Close'].rolling(window=params['short_ma']).mean()
        data['MA_Long'] = data['HSIF_Close'].rolling(window=params['long_ma']).mean()

        # 生成信號（月度檢查）
        data['trend_signal'] = 0
        data.loc[data['MA_Short'] > data['MA_Long'], 'trend_signal'] = 1
        data.loc[data['MA_Short'] < data['MA_Long'], 'trend_signal'] = -1

        # 每月只檢查一次信號
        monthly_check = data.resample('M').first()
        data['final_signal'] = np.nan

        for date, row in monthly_check.iterrows():
            if row['trend_signal'] != 0:
                data.loc[date:, 'final_signal'] = row['trend_signal']

        data['final_signal'] = data['final_signal'].fillna(0)

        return data

    def implement_mean_reversion(self, data, params=None):
        """均值回歸策略實現"""
        params = params or {'period': 60, 'threshold': 2.0}

        # 計算均值回歸指標
        data['Price_Mean'] = data['HSIF_Close'].rolling(window=params['period']).mean()
        data['Price_Std'] = data['HSIF_Close'].rolling(window=params['period']).std()

        # 計算Z分數
        data['Z_Score'] = (data['HSIF_Close'] - data['Price_Mean']) / data['Price_Std']

        # 生成信號（月度檢查）
        data['mr_signal'] = 0
        data.loc[data['Z_Score'] < -params['threshold'], 'mr_signal'] = 1   # 低於均值2個標準差買入
        data.loc[data['Z_Score'] > params['threshold'], 'mr_signal'] = -1   # 高於均值2個標準差賣出

        # 每月只檢查一次信號
        monthly_check = data.resample('M').first()
        data['final_signal'] = np.nan

        for date, row in monthly_check.iterrows():
            if row['mr_signal'] != 0:
                data.loc[date:, 'final_signal'] = row['mr_signal']

        data['final_signal'] = data['final_signal'].fillna(0)

        return data

    def implement_sentiment_strategy(self, data, params=None):
        """市場情緒策略實現"""
        params = params or {'bull_bear_threshold': 2.0, 'fear_greed_threshold': 30}

        # 基於牛熊比例的情緒策略
        if 'Bull_Bear_Ratio' not in data.columns:
            # 如果沒有情緒數據，基於價格變化模擬
            data['Bull_Bear_Ratio'] = np.exp(data['HSIF_Return'].rolling(5).mean() * 10)

        if 'Fear_Greed_Index' not in data.columns:
            # 模擬恐懼貪婪指標
            data['Fear_Greed_Index'] = 50 + 25 * np.tanh(data['HSIF_Return'].rolling(20).sum() * 10)

        # 生成信號（月度檢查）
        data['sentiment_signal'] = 0
        data.loc[data['Bull_Bear_Ratio'] > params['bull_bear_threshold'], 'sentiment_signal'] = 1  # 極度看漲
        data.loc[data['Bull_Bear_Ratio'] < (1/params['bull_bear_threshold']), 'sentiment_signal'] = -1  # 極度看跌

        # 每月只檢查一次信號
        monthly_check = data.resample('M').first()
        data['final_signal'] = np.nan

        for date, row in monthly_check.iterrows():
            if row['sentiment_signal'] != 0:
                data.loc[date:, 'final_signal'] = row['sentiment_signal']

        data['final_signal'] = data['final_signal'].fillna(0)

        return data

    def implement_volatility_strategy(self, data, params=None):
        """波動率策略實現"""
        params = params or {'lookback': 20, 'threshold': 0.25}

        # 計算波動率
        data['Volatility'] = data['HSIF_Return'].rolling(window=params['lookback']).std() * np.sqrt(252)

        # 生成信號（月度檢查）
        data['vol_signal'] = 0
        data.loc[data['Volatility'] < params['threshold'], 'vol_signal'] = 1  # 低波動率買入
        data.loc[data['Volatility'] > params['threshold'] * 2, 'vol_signal'] = -1  # 高波動率賣出

        # 每月只檢查一次信號
        monthly_check = data.resample('M').first()
        data['final_signal'] = np.nan

        for date, row in monthly_check.iterrows():
            if row['vol_signal'] != 0:
                data.loc[date:, 'final_signal'] = row['vol_signal']

        data['final_signal'] = data['final_signal'].fillna(0)

        return data

    def calculate_strategy_performance(self, data, strategy_name):
        """計算策略性能"""
        returns = data['HSIF_Return'] * data['final_signal'].shift(1)

        # 基礎指標
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1

        # 風險指標
        volatility = returns.std() * np.sqrt(252)

        # 夏普比率
        risk_free_rate = 0.025
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

        # 最大回撤
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()

        # 交易統計
        total_trades = data['final_signal'].abs().sum()
        trading_costs = total_trades * 1000  # 固定成本模型

        # 勝率
        trading_days = (returns != 0).sum()
        winning_days = (returns > 0).sum()
        win_rate = winning_days / trading_days if trading_days > 0 else 0

        # 計算年化交易頻率
        years_traded = len(data) / 252
        trades_per_year = total_trades / years_traded if years_traded > 0 else 0

        return {
            'strategy_name': strategy_name,
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': int(total_trades),
            'trading_costs': trading_costs,
            'trades_per_year': trades_per_year,
            'total_days': len(data),
            'years_tested': len(data) / 252
        }

    def evaluate_statistical_significance(self, returns):
        """評估統計顯著性"""
        n = len(returns)
        if n == 0:
            return {'significant': False, 'p_value': 1.0}

        mean_return = returns.mean()
        std_return = returns.std()

        if std_return == 0:
            return {'significant': False, 'p_value': 1.0}

        # t檢驗
        t_statistic = mean_return / (std_return / np.sqrt(n))

        # p值
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(abs(t_statistic), df=n-1))

        return {
            'significant': p_value < 0.05,
            'p_value': p_value,
            't_statistic': t_statistic,
            'sample_size': n
        }

    def run_all_strategies(self):
        """運行所有策略"""
        print("Starting Multi-Strategy Validation System")
        print("=" * 60)

        # 加載數據
        data = self.load_real_data()
        if data is None:
            return None

        # 註冊內置策略
        self.register_strategy("RSI_Low_Frequency", self.implement_rsi_strategy,
                               {'period': 21, 'overbought': 75, 'oversold': 25})
        self.register_strategy("Bollinger_Low_Freq", self.implement_bollinger_strategy,
                               {'period': 30, 'std_dev': 2.0})
        self.register_strategy("Trend_Following_Monthly", self.implement_trend_following,
                               {'short_ma': 30, 'long_ma': 90})
        self.register_strategy("Mean_Reversion", self.implement_mean_reversion,
                               {'period': 90, 'threshold': 2.5})
        self.register_strategy("Sentiment_Based", self.implement_sentiment_strategy,
                               {'bull_bear_threshold': 2.5})
        self.register_strategy("Volatility_Based", self.implement_volatility_strategy,
                               {'lookback': 30, 'threshold': 0.2})

        results = {}

        for strategy_name, strategy_info in self.strategies.items():
            print(f"\n{'='*20} {strategy_name} {'='*20}")

            try:
                # 實施策略
                strategy_data = strategy_info['implementation'](data.copy(), strategy_info['params'])

                # 計算性能
                performance = self.calculate_strategy_performance(strategy_data, strategy_name)

                # 統計顯著性
                strategy_returns = strategy_data['HSIF_Return'] * strategy_data['final_signal'].shift(1)
                significance = self.evaluate_statistical_significance(strategy_returns)

                # 綜合評分
                score = self._calculate_strategy_score(performance, significance)

                results[strategy_name] = {
                    **performance,
                    **significance,
                    'score': score,
                    'grade': self._get_grade(score)
                }

                # 打印結果
                print(f"  Total Return: {performance['total_return']:.2%}")
                print(f"  Annual Return: {performance['annual_return']:.2%}")
                print(f"  Sharpe Ratio: {performance['sharpe_ratio']:.3f}")
                print(f"  Max Drawdown: {performance['max_drawdown']:.2%}")
                print(f"  Win Rate: {performance['win_rate']:.2%}")
                print(f"  Trades/Year: {performance['trades_per_year']:.1f}")
                print(f"  Statistically Significant: {'Yes' if significance['significant'] else 'No'}")
                print(f"  Score: {score:.1f}/100 ({self._get_grade(score)})")

            except Exception as e:
                print(f"  ERROR: Strategy failed - {e}")
                results[strategy_name] = {
                    'error': str(e),
                    'score': 0,
                    'grade': 'F'
                }

        # 生成排名報告
        self._generate_ranking_report(results)

        return results

    def _calculate_strategy_score(self, performance, significance):
        """計算策略綜合評分"""
        score = 0

        # 收益評分 (0-30分)
        if performance['annual_return'] > 0.15:
            score += 30
        elif performance['annual_return'] > 0.10:
            score += 25
        elif performance['annual_return'] > 0.05:
            score += 20
        elif performance['annual_return'] > 0:
            score += 15
        elif performance['annual_return'] > -0.05:
            score += 10

        # 夏普比率評分 (0-25分)
        if performance['sharpe_ratio'] > 1.0:
            score += 25
        elif performance['sharpe_ratio'] > 0.8:
            score += 20
        elif performance['sharpe_ratio'] > 0.6:
            score += 15
        elif performance['sharpe_ratio'] > 0.4:
            score += 10
        elif performance['sharpe_ratio'] > 0.2:
            score += 5

        # 最大回撤評分 (0-20分)
        if performance['max_drawdown'] > -0.1:
            score += 20
        elif performance['max_drawdown'] > -0.2:
            score += 15
        elif performance['max_drawdown'] > -0.3:
            score += 10
        elif performance['max_drawdown'] > -0.4:
            score += 5

        # 交易頻率評分 (0-15分)
        if performance['trades_per_year'] < 12:
            score += 15
        elif performance['trades_per_year'] < 24:
            score += 10
        elif performance['trades_per_year'] < 36:
            score += 5

        # 統計顯著性評分 (0-10分)
        if significance['significant']:
            score += 10
        elif significance['p_value'] < 0.1:
            score += 5

        return min(100, score)

    def _get_grade(self, score):
        """獲取評級"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C+'
        elif score >= 40:
            return 'C'
        elif score >= 30:
            return 'D+'
        elif score >= 20:
            return 'D'
        else:
            return 'F'

    def _generate_ranking_report(self, results):
        """生成排名報告"""
        print(f"\n{'='*80}")
        print("STRATEGY RANKING REPORT")
        print(f"{'='*80}")

        # 排除錯誤的策略
        valid_results = {k: v for k, v in results.items() if 'error' not in v}

        if not valid_results:
            print("No valid strategies found!")
            return

        # 按評分排序
        sorted_results = sorted(valid_results.items(), key=lambda x: x[1]['score'], reverse=True)

        print(f"\n{'Rank':<8} {'Strategy':<25} {'Score':<8} {'Grade':<8} {'Annual Return':<15} {'Sharpe':<10} {'Trades/Year':<12} {'Significant':<12}")
        print("-" * 100)

        for i, (name, result) in enumerate(sorted_results, 1):
            print(f"{i:<8} {name:<25} {result['score']:<8.1f} {result['grade']:<8} "
                  f"{result['annual_return']:<15.2%} {result['sharpe_ratio']:<10.3f} "
                  f"{result['trades_per_year']:<12.1f} {'Yes' if result['significant'] else 'No':<12}")

        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            'validation_date': datetime.now().isoformat(),
            'total_strategies': len(self.strategies),
            'valid_strategies': len(valid_results),
            'rankings': sorted_results,
            'best_strategy': sorted_results[0] if sorted_results else None,
            'average_score': sum(r['score'] for r in valid_results.values()) / len(valid_results)
        }

        filename = f"multi_strategy_report_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n[SAVE] Full report saved: {filename}")

def main():
    """主執行函數"""
    validator = MultiStrategyValidator()
    results = validator.run_all_strategies()
    return results

if __name__ == "__main__":
    main()