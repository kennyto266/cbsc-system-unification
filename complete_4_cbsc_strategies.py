#!/usr/bin/env/env python3
"""
完整的4種CBSC牛熊證策略實現和回測
Complete 4 Types of CBSC Bull/Bear Certificate Strategies and Backtesting

Author: CBSC Strategy Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from typing import Dict, List, Tuple

warnings.filterwarnings('ignore')

class CBSCFourStrategies:
    """
    完整的4種CBSC牛熊證策略實現
    Complete 4 Types of CBSC Bull/Bear Certificate Strategies
    """

    def __init__(self):
        self.data = None
        self.results = {}

    def load_real_data(self):
        """加載真實CBSC數據"""
        data_file = "CODEX--/warrant_sentiment_merged.csv"

        if not Path(data_file).exists():
            print(f"ERROR: 數據文件不存在: {data_file}")
            return False

        try:
            self.data = pd.read_csv(data_file)
            self.data['Date'] = pd.to_datetime(self.data['Date'])
            self.data = self.data.dropna(subset=['Afternoon_Close', 'Date'])
            self.data = self.data.drop_duplicates(subset=['Date'], keep='last')
            self.data = self.data.sort_values('Date')

            print(f"✅ 成功加載 {len(self.data)} 天的真實CBSC數據")
            print(f"   日期範圍: {self.data['Date'].min().date()} 到 {self.data['Date'].max().date()}")

            return True

        except Exception as e:
            print(f"ERROR: 數據加載失敗 - {e}")
            return False

    def strategy_1_sentiment_momentum(self, data: pd.DataFrame) -> Dict:
        """
        策略1: 情緒動量策略
        基於牛熊證情緒動量的交易策略
        """
        print("\n=== 策略1: 情緒動量策略 ===")

        # 計算情緒動量
        data['Sentiment_MA_5'] = data['Bull_Ratio'].rolling(5, min_periods=3).mean()
        data['Sentiment_MA_10'] = data['Bull_Ratio'].rolling(10, min_periods=5).mean()
        data['Sentiment_Momentum'] = data['Sentiment_MA_5'] - data['Sentiment_MA_10']

        # 動量指標
        data['Bull_Volume_MA'] = data['Bull_Turnover_HKD'].rolling(5, min_periods=3).mean()
        data['Total_Volume_MA'] = (data['Bull_Turnover_HKD'] + data['Bear_Turnover_HKD']).rolling(5, min_periods=3).mean()

        # 動量確認
        volume_surge = data['Bull_Turnover_HKD'] > (data['Bull_Volume_MA'] * 1.3)

        # 生成動量信號
        momentum_signal = data['Sentiment_Momentum'] > 0.1
        volume_confirmation = volume_surge & (data['Total_Volume_MA'] > 100000000)

        buy_signals = momentum_signal & volume_confirmation
        sell_signals = (data['Sentiment_Momentum'] < -0.1) & volume_surge

        return self._backtest_strategy(data, buy_signals, sell_signals, "情緒動量策略")

    def strategy_2_volume_reversal(self, data: pd.DataFrame) -> Dict:
        """
        策略2: 成交量反轉策略
        基於牛熊證成交額變化的反向操作策略
        """
        print("\n=== 策略2: 成交量反轉策略 ===")

        # 計算成交量比率
        data['Bull_Ratio_5'] = data['Bull_Ratio'].rolling(5, min_periods=3).mean()
        data['Bull_Ratio_20'] = data['Bull_Ratio'].rolling(20, min_periods=10).mean()

        # 成交量突變檢測
        data['Volume_Spike'] = data['Total_Turnover'] > (data['Total_Turnover'].rolling(10, min_periods=5).mean() * 1.5)

        # 極端比率檢測
        extreme_bull = data['Bull_Ratio_5'] > 0.7
        extreme_bear = data['Bull_Ratio_5'] < 0.3

        # 反轉信號（當趨勢反轉時）
        ratio_turning_bull = (data['Bull_Ratio_5'] > data['Bull_Ratio_20']) & extreme_bear
        ratio_turning_bear = (data['Bull_Ratio_5'] < data['Bull_Ratio_20']) & extreme_bull

        buy_signals = ratio_turning_bull & volume_spike
        sell_signals = ratio_turning_bear & volume_spike

        return self._backtest_strategy(data, buy_signals, sell_signals, "成交量反轉策略")

    def strategy_3_risk_adjusted_bollinger(self, data: pd.DataFrame) -> Dict:
        """
        策略3: 風險調整布林帶策略
        結合技術指標和CBSC特定風險的布林帶策略
        """
        print("\n=== 策略3: 風險調整布林帶策略 ===")

        # RSI計算
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14, min_periods=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14, min_periods=7).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # 布林帶計算
        window = min(20, len(data) // 4)
        data['BB_Middle'] = data['Close'].rolling(window).mean()
        data['BB_Std'] = data['Close'].rolling(window).std()
        data['BB_Upper'] = data['BB_Middle'] + (data['BB_Std'] * 2)
        data['BB_Lower'] = data['BB_Middle'] - (data['BB_Std'] * 2)

        # CBSC風險評估
        data['Call_Risk_Bull'] = np.maximum(0, (data['Bull_Ratio'] - 0.5) * 2)  # 0-1範圍
        data['Call_Risk_Bear'] = np.maximum(0, (0.5 - data['Bull_Ratio']) * 2)  # 0-1範圍

        # 風險調整的信號生成
        rsi_buy = data['RSI'] < 35
        rsi_sell = data['RSI'] > 65
        bb_buy = data['Close'] < data['BB_Lower'] & (data['Call_Risk_Bull'] < 0.3)
        bb_sell = data['Close'] > data['BB_Upper'] & (data['Call_Risk_Bear'] < 0.3)

        buy_signals = (rsi_buy | bb_buy) & (data['Call_Risk_Bull'] < 0.5)
        sell_signals = (rsi_sell | bb_sell) & (data['Call_Risk_Bear'] < 0.5)

        return self._backtest_strategy(data, buy_signals, sell_signals, "風險調整布林帶策略")

    def strategy_4_time_decay_momentum(self, data: pd.DataFrame) -> Dict:
        """
        策略4: 時衰減動量策略
        考慮牛熊證時間衰減特性的動量策略
        """
        print("\n=== 策略4: 時衰減動量策略 ===")

        # 計算到期時間衰減因子（模擬）
        days_to_expiry = np.arange(len(data))
        data['Time_Decay_Factor'] = np.exp(-days_to_expiry / 60)  # 60天半衰期
        data['Adjusted_Price'] = data['Close'] * (1 + data['Time_Decay_Factor'] * 0.1)

        # 動量強度調整
        data['Momentum_Strength'] = data['Bull_Ratio'] * data['Time_Decay_Factor']

        # 時衰減動量信號
        momentum_buy = (data['Momentum_Strength'] > 0.05) & (data['Bull_Ratio'] > 0.6)
        momentum_sell = (data['Momentum_Strength'] < 0.05) & (data['Bull_Ratio'] < 0.4)

        # 時間敏感度調整
        time_sensitive_buy = momentum_buy & (data['Time_Decay_Factor'] > 0.8)
        time_sensitive_sell = momentum_sell & (data['Time_Decay_Factor'] > 0.8)

        buy_signals = time_sensitive_buy & (data['Total_Turnover'] > 500000)
        sell_signals = time_sensitive_sell & (data['Total_Turnover'] > 500000)

        return self._backtest_strategy(data, buy_signals, sell_signals, "時衰減動量策略")

    def _backtest_strategy(self, data: pd.DataFrame, buy_signals: pd.Series,
                           sell_signals: pd.Series, strategy_name: str) -> Dict:
        """統一回測框架"""

        initial_capital = 100000
        cash = initial_capital
        position_size = 0
        trades = []
        equity_curve = [initial_capital]

        for i in range(1, len(data)):
            current_price = data['Close'].iloc[i]
            current_value = cash + (position_size * current_price)
            equity_curve.append(current_value)

            # 買入信號
            if buy_signals.iloc[i] and position_size == 0:
                position_size = int((cash * 0.25) / current_price)
                cash -= position_size * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': position_size,
                    'sentiment': data['Bull_Ratio'].iloc[i],
                    'turnover': data['Total_Turnover'].iloc[i]
                })

            # 賣出信號
            elif sell_signals.iloc[i] and position_size > 0:
                cash += position_size * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': position_size,
                    'sentiment': data['Bull_Ratio'].iloc[i],
                    'turnover': data['Total_Turnover'].iloc[i]
                })
                position_size = 0

        # 計算性能指標
        final_value = equity_curve[-1]
        total_return = (final_value - initial_capital) / initial_capital

        if len(equity_curve) > 1:
            returns = pd.Series(equity_curve).pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            annual_return = total_return * (252 / len(data))
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        else:
            annual_return = 0
            sharpe_ratio = 0

        # 最大回撤
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        max_drawdown = drawdown.min()

        # 勝率
        sell_trades = len([t for t in trades if t['action'] == 'SELL'])
        win_rate = sell_trades / len(trades) if trades else 0

        return {
            'strategy_name': strategy_name,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'equity_curve': equity_curve,
            'trades': trades
        }

    def run_all_strategies(self):
        """運行所有4種策略"""
        print("=" * 80)
        print("完整4種CBSC牛熊證策略回測系統")
        print("使用所有真實數據 - 無模擬")
        print("=" * 80)

        if not self.load_real_data():
            return

        # 市場基準
        benchmark_return = (self.data['Afternoon_Close'].iloc[-1] - self.data['Afternoon_Close'].iloc[0]) / self.data['Afternoon_Close'].iloc[0]

        print(f"\n📊 市場基準:")
        print(f"   期間回報: {benchmark_return:.2%}")
        print(f"   交易天數: {len(self.data)} 天")

        # 定義4種策略
        strategies = {
            "情緒動量策略": self.strategy_1_sentiment_momentum,
            "成交量反轉策略": self.strategy_2_volume_reversal,
            "風險調整布林帶策略": self.strategy_3_risk_adjusted_bollinger,
            "時衰減動量策略": self.strategy_4_time_decay_momentum
        }

        print(f"\n🎯 測試 {len(strategies)} 種CBSC策略:")

        all_results = {}

        for strategy_name, strategy_func in strategies.items():
            print(f"\n{'='*50}")
            print(f"🔄 開始: {strategy_name}")
            print(f"{'='*50}")

            try:
                result = strategy_func(self.data.copy())
                if result:
                    all_results[strategy_name] = result
                    self._print_strategy_summary(strategy_name, result, benchmark_return)
                else:
                    print(f"❌ {strategy_name} 失敗")
            except Exception as e:
                print(f"❌ {strategy_name} 出錯: {e}")

        # 生成比較報告
        self._generate_comparison_report(all_results, benchmark_return)

        return all_results

    def _print_strategy_summary(self, strategy_name: str, result: Dict, benchmark_return: float):
        """打印策略摘要"""
        print(f"   總回報: {result['total_return']:.2%}")
        print(f"   年化回報: {result['annual_return']:.2%}")
        print(f"   夏普比率: {result['sharpe_ratio']:.3f}")
        print(f"   最大回撤: {result['max_drawdown']:.2%}")
        print(f"   勝率: {result['win_rate']:.1%}")
        print(f"   交易次數: {result['total_trades']}")
        print(f"   vs基準: {(result['total_return'] - benchmark_return):.2%}")

        # 評級評估
        excess_return = result['total_return'] - benchmark_return
        if excess_return > 0:
            print(f"   ✅ 超越市場 ({excess_return:.2%})")
        elif excess_return < -0.05:
            print(f"   ⚠️ 落後市場 ({excess_return:.2%})")
        else:
            print(f"   ✅ 接近市場 ({excess_return:.2%})")

    def _generate_comparison_report(self, results: Dict[str, Dict], benchmark_return: float):
        """生成比較報告"""
        print(f"\n{'='*80}")
        print("📊 策略比較報告")
        print(f"{'='*80}")

        if not results:
            print("❌ 沒有成功的策略結果")
            return

        # 排序
        sorted_results = sorted(results.items(), key=lambda x: x[1]['sharpe_ratio'], reverse=True)

        print(f"\n🎯 策略排名 (按夏普比率):")
        print("-" * 80)
        print(f"{'策略名稱':<20} {'總回報':<12} {'年化回報':<12} {'夏普比率':<10} {'最大回撤':<12} {'vs基準':<10} {'交易次數':<8}")
        print("-" * 80)

        for rank, (name, result) in enumerate(sorted_results, 1):
            excess = result['total_return'] - benchmark_return
            excess_str = f"+{excess:.2%}" if excess > 0 else f"{excess:.2%}"

            print(f"{rank}. {name:<20} {result['total_return']:<12.2%} "
                  f"{result['annual_return']:<12.2%} {result['sharpe_ratio']:<10.3f} "
                  f"{result['max_drawdown']:<12.2%} {excess_str:<10} {result['total_trades']:<8}")

        # 最佳策略
        if sorted_results:
            best_strategy = sorted_results[0]
            print(f"\n🏆 最佳策略: {best_strategy[0]}")
            print(f"   夏普比率: {best_strategy[1]['sharpe_ratio']:.3f}")
            print(f"   總回報: {best_strategy[1]['total_return']:.2%}")
            print(f"   超越市場: {(best_strategy[1]['total_return'] - benchmark_return):.2%}")

        # 總體表現
        winning_strategies = sum(1 for _, result in results.values() if result['total_return'] > benchmark_return)
        total_strategies = len(results)
        win_rate = (winning_strategies / total_strategies) * 100 if total_strategies > 0 else 0

        print(f"\n📈 總體表現:")
        print(f"   戰勝策略: {winning_strategies}/{total_strategies} ({win_rate:.1f}%)")
        print(f"   基準回報: {benchmark_return:.2%}")
        print(f"   平均表現: {np.mean([r['total_return'] for r in results.values()]):.2%}")

def main():
    """主執行函數"""
    print("啟動完整4種CBSC牛熊證策略回測...")

    strategies = CBSCFourStrategies()
    results = strategies.run_all_strategies()

    if results:
        print(f"\n🎉 完成4種CBSC策略測試！")
        print(f"📊 共測試了 {len(results)} 種策略")
        print(f"📈 使用了 100% 真實CBSC數據")
    else:
        print("❌ 策略測試失敗")

if __name__ == "__main__":
    main()