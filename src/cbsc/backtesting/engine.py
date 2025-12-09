"""
CBSC VectorBT Native Backtesting Engine
CBSC VectorBT原生回測引擎

Main backtesting engine using VectorBT as the core for CBSC strategy analysis.
使用VectorBT作為核心進行CBSC策略分析的主要回測引擎。

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

from data_loader import CBSCDataLoader
from signal_generator import CBSCSignalGenerator

class CBSCBacktester:
    """CBSC回測器 - 基於VectorBT的高性能回測引擎"""

    def __init__(self, sentiment_path: str, config: Optional[Dict] = None):
        """
        初始化回測器

        Args:
            sentiment_path: CBSC情緒數據路徑
            config: 回測配置參數
        """
        self.config = config or self._default_config()

        # 初始化組件
        self.data_loader = CBSCDataLoader(sentiment_path)
        self.signal_generator = CBSCSignalGenerator(self.config.get('signal_config', {}))

        # 數據存儲
        self.features_df = None
        self.price_data = None
        self.portfolios = {}

        print("CBSC回測器初始化完成")

    def _default_config(self) -> Dict:
        """默認配置參數"""
        return {
            'initial_cash': 1000000,      # 初始資金
            'fees': 0.003,               # 交易費用 (0.3% for CBSC)
            'slippage': 0.001,           # 滑點
            'call_price_buffer': 0.05,   # 收回價緩衝區
            'max_position_size': 0.1,    # 最大持倉比例 (10% for leveraged products)
            'signal_config': {
                'sentiment_threshold': 0.3,
                'extreme_sentiment_boost': 1.5,
                'rsi_overbought': 70,
                'rsi_oversold': 30
            }
        }

    def prepare_data(self, symbol: str = "0700.HK") -> bool:
        """
        準備回測數據

        Args:
            symbol: 股票代碼

        Returns:
            是否成功準備數據
        """
        try:
            print(f"準備 {symbol} 回測數據...")

            # 加載數據
            sentiment_df = self.data_loader.load_sentiment_data()
            if sentiment_df.empty:
                print("情緒數據加載失敗")
                return False

            price_df = self.data_loader.load_price_data(symbol)
            if price_df.empty:
                print("價格數據加載失敗")
                return False

            # 對齊和創建特徵
            aligned_sentiment, aligned_price = self.data_loader.align_data()
            self.features_df = self.data_loader.create_cbsc_features(aligned_sentiment, aligned_price)
            self.price_data = aligned_price

            # 為VectorBT準備價格數據
            self.price_data['Date'] = pd.to_datetime(self.price_data['Date'])
            self.price_data = self.price_data.set_index('Date')

            print(f"數據準備完成: {len(self.features_df)} 條記錄")
            return True

        except Exception as e:
            print(f"數據準備失敗: {e}")
            return False

    def run_single_strategy(self, strategy_name: str, entries: pd.Series, exits: pd.Series) -> vbt.Portfolio:
        """
        運行單個策略回測

        Args:
            strategy_name: 策略名稱
            entries: 進入信號
            exits: 退出信號

        Returns:
            VectorBT投資組合對象
        """
        try:
            print(f"運行 {strategy_name} 策略回測...")

            # 創建VectorBT投資組合
            portfolio = vbt.Portfolio.from_signals(
                close=self.price_data['close'],
                entries=entries,
                exits=exits,
                init_cash=self.config['initial_cash'],
                fees=self.config['fees'],
                slippage=self.config['slippage'],
                freq='1D'
            )

            # 存儲結果
            self.portfolios[strategy_name] = portfolio

            print(f"{strategy_name} 策略回測完成")
            return portfolio

        except Exception as e:
            print(f"{strategy_name} 策略回測失敗: {e}")
            return None

    def run_multiple_strategies(self, symbol: str = "0700.HK") -> Dict[str, vbt.Portfolio]:
        """
        運行多種策略回測

        Args:
            symbol: 股票代碼

        Returns:
            策略名稱到投資組合的映射
        """
        if not self.prepare_data(symbol):
            return {}

        print("運行多策略回測...")

        # 生成多種策略信號
        strategies = self.signal_generator.generate_multiple_strategies(self.features_df)

        # 運行每種策略
        for strategy_name, (entries, exits) in strategies.items():
            portfolio = self.run_single_strategy(strategy_name, entries, exits)

        return self.portfolios

    def calculate_performance_metrics(self, portfolio: vbt.Portfolio) -> Dict[str, float]:
        """
        計算策略性能指標

        Args:
            portfolio: VectorBT投資組合

        Returns:
            性能指標字典
        """
        try:
            # 獲取回測結果
            stats = portfolio.stats()

            # 計算核心指標
            total_return = stats['Total Return [%]']
            annual_return = stats['Annual Return [%]']
            sharpe_ratio = stats['Sharpe Ratio']
            max_drawdown = stats['Max Drawdown [%]']
            calmar_ratio = stats['Calmar Ratio']
            win_rate = stats['Win Rate [%]']
            profit_factor = stats['Profit Factor']
            total_trades = stats['# Trades']

            # 計算風險調整指標
            returns = portfolio.returns()
            downside_returns = returns[returns < 0]
            downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
            sortino_ratio = returns.mean() / downside_std if downside_std > 0 else 0

            metrics = {
                'total_return': float(total_return),
                'annual_return': float(annual_return),
                'sharpe_ratio': float(sharpe_ratio),
                'sortino_ratio': float(sortino_ratio),
                'max_drawdown': float(max_drawdown),
                'calmar_ratio': float(calmar_ratio),
                'win_rate': float(win_rate),
                'profit_factor': float(profit_factor),
                'total_trades': int(total_trades),
                'avg_return': float(returns.mean() * 252 * 100),  # 年化
                'volatility': float(returns.std() * np.sqrt(252) * 100)  # 年化波動率
            }

            return metrics

        except Exception as e:
            print(f"計算性能指標失敗: {e}")
            return {}

    def compare_strategies(self) -> pd.DataFrame:
        """
        比較多種策略性能

        Returns:
            策略比較結果DataFrame
        """
        if not self.portfolios:
            print("沒有可用的策略結果進行比較")
            return pd.DataFrame()

        comparison_data = []

        for strategy_name, portfolio in self.portfolios.items():
            metrics = self.calculate_performance_metrics(portfolio)
            metrics['strategy'] = strategy_name
            comparison_data.append(metrics)

        comparison_df = pd.DataFrame(comparison_data)
        comparison_df = comparison_df.set_index('strategy')

        # 按Sharpe比率排序
        comparison_df = comparison_df.sort_values('sharpe_ratio', ascending=False)

        print("策略比較完成")
        return comparison_df

    def plot_strategy_results(self, strategy_names: Optional[List[str]] = None,
                            figsize: Tuple[int, int] = (15, 10)) -> None:
        """
        繪製策略結果

        Args:
            strategy_names: 要繪製的策略名稱列表
            figsize: 圖表大小
        """
        if not self.portfolios:
            print("沒有可用的策略結果進行繪製")
            return

        if strategy_names is None:
            strategy_names = list(self.portfolios.keys())

        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle('CBSC策略回測結果', fontsize=16)

        # 1. 淨值曲線
        ax1 = axes[0, 0]
        for strategy_name in strategy_names:
            if strategy_name in self.portfolios:
                portfolio = self.portfolios[strategy_name]
                equity_curve = portfolio.value()
                equity_curve.plot(ax=ax1, label=strategy_name, linewidth=2)

        ax1.set_title('淨值曲線')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('投資組合價值')
        ax1.legend()
        ax1.grid(True)

        # 2. 回撤曲線
        ax2 = axes[0, 1]
        for strategy_name in strategy_names:
            if strategy_name in self.portfolios:
                portfolio = self.portfolios[strategy_name]
                drawdown = portfolio.drawdown()
                drawdown.plot(ax=ax2, label=strategy_name, linewidth=2)

        ax2.set_title('回撤曲線')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('回撤 (%)')
        ax2.legend()
        ax2.grid(True)

        # 3. 策略比較柱狀圖
        ax3 = axes[1, 0]
        comparison_df = self.compare_strategies()
        if not comparison_df.empty:
            comparison_df[['sharpe_ratio', 'max_drawdown', 'win_rate']].plot(
                kind='bar', ax=ax3, secondary_y='max_drawdown'
            )
            ax3.set_title('策略風險收益比較')
            ax3.set_xlabel('策略')

        # 4. 月度收益熱力圖
        ax4 = axes[1, 1]
        if len(strategy_names) > 0 and strategy_names[0] in self.portfolios:
            portfolio = self.portfolios[strategy_names[0]]
            returns = portfolio.returns()
            monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)

            # 創建年度-月份矩陣
            monthly_df = monthly_returns.to_frame('returns')
            monthly_df['year'] = monthly_df.index.year
            monthly_df['month'] = monthly_df.index.month
            heatmap_data = monthly_df.pivot(index='year', columns='month', values='returns')

            sns.heatmap(heatmap_data, ax=ax4, cmap='RdYlGn', center=0,
                       annot=True, fmt='.2%', cbar_kws={'label': '月度收益率'})
            ax4.set_title('月度收益熱力圖')
            ax4.set_xlabel('月份')
            ax4.set_ylabel('年份')

        plt.tight_layout()
        plt.show()

    def generate_report(self, save_path: Optional[str] = None) -> str:
        """
        生成回測報告

        Args:
            save_path: 報告保存路徑

        Returns:
            報告文本
        """
        comparison_df = self.compare_strategies()

        report_lines = [
            "=" * 60,
            "CBSC量化策略回測報告",
            "=" * 60,
            f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"回測數據: {len(self.features_df) if self.features_df is not None else 0} 條記錄",
            f"測試策略: {len(self.portfolios)} 種",
            "",
            "策略性能比較:",
            "-" * 40
        ]

        if not comparison_df.empty:
            for strategy_name, row in comparison_df.iterrows():
                report_lines.extend([
                    f"\n{strategy_name}:",
                    f"  總收益率: {row['total_return']:.2f}%",
                    f"  年化收益率: {row['annual_return']:.2f}%",
                    f"  Sharpe比率: {row['sharpe_ratio']:.3f}",
                    f"  最大回撤: {row['max_drawdown']:.2f}%",
                    f"  勝率: {row['win_rate']:.2f}%",
                    f"  總交易次數: {row['total_trades']}",
                ])

        # 最佳策略推薦
        if not comparison_df.empty:
            best_strategy = comparison_df.index[0]
            best_metrics = comparison_df.iloc[0]

            report_lines.extend([
                "\n" + "=" * 40,
                "最佳策略推薦:",
                f"策略名稱: {best_strategy}",
                f"Sharpe比率: {best_metrics['sharpe_ratio']:.3f}",
                f"年化收益率: {best_metrics['annual_return']:.2f}%",
                f"最大回撤: {best_metrics['max_drawdown']:.2f}%",
                "",
                "風險提示:",
                "- CBSC產品具有槓桿效應，風險較高",
                "- 回測結果不代表未來表現",
                "- 建議結合多種策略進行風險分散",
                "=" * 60
            ])

        report = "\n".join(report_lines)

        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"報告已保存到: {save_path}")

        return report

def main():
    """測試CBSC回測器"""
    print("=== CBSC VectorBT 回測器測試 ===")

    # 初始化回測器
    sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
    backtester = CBSCBacktester(sentiment_path)

    # 運行多策略回測
    print("\n1. 運行策略回測...")
    portfolios = backtester.run_multiple_strategies("0700.HK")

    if portfolios:
        # 比較策略
        print("\n2. 比較策略性能...")
        comparison_df = backtester.compare_strategies()
        print(comparison_df.round(3))

        # 生成報告
        print("\n3. 生成回測報告...")
        report = backtester.generate_report("cbsc_backtest_report.txt")
        print(report)

        print("\n✅ CBSC回測器測試完成！")
    else:
        print("❌ 回測失敗，無法生成策略結果")

if __name__ == "__main__":
    main()