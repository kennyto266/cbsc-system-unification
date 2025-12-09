#!/usr/bin/env python3
"""
ASCII Backtest Visualizer
Pure ASCII version for Windows compatibility
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Set font for better display
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ASCIIBacktestVisualizer:
    """ASCII Backtest Visualization Class"""

    def __init__(self, results_file='fixed_real_backtest_results.json'):
        """Initialize visualizer"""
        self.results_file = results_file
        self.results_data = None
        self.load_results()

    def load_results(self):
        """Load backtest results"""
        try:
            with open(self.results_file, 'r') as f:
                self.results_data = json.load(f)
            print(f"[OK] Loaded backtest results: {self.results_file}")
        except Exception as e:
            print(f"[ERROR] Cannot load backtest results: {e}")
            return

    def create_strategy_performance_chart(self):
        """Create strategy performance comparison chart"""
        if not self.results_data:
            return

        # Prepare data
        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        # Create chart
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Real VectorBT Backtest Performance Analysis', fontsize=16, fontweight='bold')

        # 1. Total Return Comparison
        ax1 = axes[0, 0]
        returns_pivot = df.pivot(index='symbol', columns='strategy', values='total_return')
        returns_pivot.plot(kind='bar', ax=ax1, color=['#2E86AB', '#A23B72'])
        ax1.set_title('Total Return by Stock and Strategy')
        ax1.set_ylabel('Total Return')
        ax1.set_xlabel('Stock')
        ax1.legend(title='Strategy')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # Format y-axis as percentage
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))

        # 2. Sharpe Ratio Comparison
        ax2 = axes[0, 1]
        sharpe_pivot = df.pivot(index='symbol', columns='strategy', values='sharpe_ratio')
        sharpe_pivot.plot(kind='bar', ax=ax2, color=['#2E86AB', '#A23B72'])
        ax2.set_title('Sharpe Ratio by Stock and Strategy')
        ax2.set_ylabel('Sharpe Ratio')
        ax2.set_xlabel('Stock')
        ax2.legend(title='Strategy')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.axhline(y=1.0, color='green', linestyle='--', alpha=0.5, label='Good Sharpe (1.0)')

        # 3. Maximum Drawdown Comparison
        ax3 = axes[1, 0]
        drawdown_pivot = df.pivot(index='symbol', columns='strategy', values='max_drawdown')
        drawdown_pivot.plot(kind='bar', ax=ax3, color=['#2E86AB', '#A23B72'])
        ax3.set_title('Maximum Drawdown by Stock and Strategy')
        ax3.set_ylabel('Max Drawdown')
        ax3.set_xlabel('Stock')
        ax3.legend(title='Strategy')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # Format y-axis as percentage
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))

        # 4. Strategy Average Performance
        ax4 = axes[1, 1]
        strategy_summary = self.results_data['strategy_performance_summary']
        strategies = list(strategy_summary.keys())
        avg_returns = [strategy_summary[s]['avg_return'] * 100 for s in strategies]
        avg_sharpes = [strategy_summary[s]['avg_sharpe'] for s in strategies]

        x = np.arange(len(strategies))
        width = 0.35

        bars1 = ax4.bar(x - width/2, avg_returns, width, label='Avg Return (%)', color='#2E86AB', alpha=0.7)
        bars2 = ax4.bar(x + width/2, np.array(avg_sharpes) * 100, width, label='Avg Sharpe (×100)', color='#A23B72', alpha=0.7)

        ax4.set_title('Strategy Performance Summary')
        ax4.set_ylabel('Values')
        ax4.set_xlabel('Strategy')
        ax4.set_xticks(x)
        ax4.set_xticklabels(strategies)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax4.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        plt.savefig('backtest_performance_analysis.png', dpi=300, bbox_inches='tight')
        print("[OK] Strategy performance analysis chart saved: backtest_performance_analysis.png")
        plt.show()

    def create_risk_return_scatter(self):
        """Create risk-return scatter plot"""
        if not self.results_data:
            return

        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        fig, ax = plt.subplots(figsize=(12, 8))

        # Group by strategy
        strategies = df['strategy'].unique()
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

        for i, strategy in enumerate(strategies):
            strategy_data = df[df['strategy'] == strategy]
            ax.scatter(strategy_data['max_drawdown'] * 100,
                      strategy_data['total_return'] * 100,
                      label=strategy,
                      s=100,
                      alpha=0.7,
                      color=colors[i % len(colors)],
                      edgecolors='black')

            # Add stock labels
            for _, row in strategy_data.iterrows():
                ax.annotate(row['symbol'],
                           (row['max_drawdown'] * 100, row['total_return'] * 100),
                           xytext=(5, 5),
                           textcoords='offset points',
                           fontsize=8,
                           alpha=0.8)

        ax.set_title('Risk-Return Profile Analysis', fontsize=14, fontweight='bold')
        ax.set_xlabel('Maximum Drawdown (%)', fontsize=12)
        ax.set_ylabel('Total Return (%)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        ax.legend(fontsize=10)

        # Add risk zone annotations
        ax.fill_between([-40, 0], [0, 0], [30, 30], alpha=0.1, color='green', label='Low Risk Zone')
        ax.fill_between([-40, 0], [0, 0], [-20, -20], alpha=0.1, color='red', label='High Risk Zone')

        plt.tight_layout()
        plt.savefig('risk_return_analysis.png', dpi=300, bbox_inches='tight')
        print("[OK] Risk-return analysis chart saved: risk_return_analysis.png")
        plt.show()

    def create_portfolio_heatmap(self):
        """Create portfolio performance heatmap"""
        if not self.results_data:
            return

        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        # Create metrics matrix
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown']
        stocks = df['symbol'].unique()
        strategies = df['strategy'].unique()

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        for i, metric in enumerate(metrics):
            # Create pivot table
            pivot_data = df.pivot(index='symbol', columns='strategy', values=metric)

            # Heatmap
            im = axes[i].imshow(pivot_data.values, cmap='RdYlGn', aspect='auto')

            # Set labels
            axes[i].set_xticks(np.arange(len(strategies)))
            axes[i].set_yticks(np.arange(len(stocks)))
            axes[i].set_xticklabels(strategies)
            axes[i].set_yticklabels(stocks)

            # Add values
            for row in range(len(stocks)):
                for col in range(len(strategies)):
                    value = pivot_data.iloc[row, col]
                    text_color = 'black' if abs(value) < 0.5 else 'white'
                    axes[i].text(col, row, f'{value:.2f}',
                                ha="center", va="center", color=text_color, fontsize=10)

            axes[i].set_title(f'{metric.replace("_", " ").title()}', fontweight='bold')

            # Add colorbar
            cbar = plt.colorbar(im, ax=axes[i])
            cbar.set_label(metric.replace("_", " ").title(), rotation=270, labelpad=15)

        plt.tight_layout()
        plt.savefig('portfolio_performance_heatmap.png', dpi=300, bbox_inches='tight')
        print("[OK] Portfolio performance heatmap saved: portfolio_performance_heatmap.png")
        plt.show()

    def create_trading_frequency_chart(self):
        """Create trading frequency analysis chart"""
        if not self.results_data:
            return

        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 1. Trading volume comparison
        trades_pivot = df.pivot(index='symbol', columns='strategy', values='num_trades')
        trades_pivot.plot(kind='bar', ax=ax1, color=['#2E86AB', '#A23B72'])
        ax1.set_title('Number of Trades by Stock and Strategy')
        ax1.set_ylabel('Number of Trades')
        ax1.set_xlabel('Stock')
        ax1.legend(title='Strategy')
        ax1.grid(True, alpha=0.3)

        # 2. Excess return analysis
        excess_returns_pivot = df.pivot(index='symbol', columns='strategy', values='excess_return')
        excess_returns_pivot.plot(kind='bar', ax=ax2, color=['#2E86AB', '#A23B72'])
        ax2.set_title('Excess Return vs Benchmark')
        ax2.set_ylabel('Excess Return')
        ax2.set_xlabel('Stock')
        ax2.legend(title='Strategy')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # Format y-axis as percentage
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))

        plt.tight_layout()
        plt.savefig('trading_frequency_analysis.png', dpi=300, bbox_inches='tight')
        print("[OK] Trading frequency analysis chart saved: trading_frequency_analysis.png")
        plt.show()

    def create_best_performers_chart(self):
        """Create best performers visualization"""
        if not self.results_data:
            return

        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Sort by total return
        df_sorted = df.sort_values('total_return', ascending=True)

        # 1. Top performers by return
        ax1.barh(range(len(df_sorted)), df_sorted['total_return'] * 100,
                color=['#2E86AB' if s == 'Moving Average' else '#A23B72' for s in df_sorted['strategy']])
        ax1.set_yticks(range(len(df_sorted)))
        ax1.set_yticklabels([f"{row['symbol']} ({row['strategy']})" for _, row in df_sorted.iterrows()])
        ax1.set_xlabel('Total Return (%)')
        ax1.set_title('Strategy Performance by Total Return')
        ax1.grid(True, alpha=0.3)
        ax1.axvline(x=0, color='black', linestyle='-', alpha=0.3)

        # 2. Top performers by Sharpe ratio
        df_sharpe_sorted = df.sort_values('sharpe_ratio', ascending=True)
        ax2.barh(range(len(df_sharpe_sorted)), df_sharpe_sorted['sharpe_ratio'],
                color=['#2E86AB' if s == 'Moving Average' else '#A23B72' for s in df_sharpe_sorted['strategy']])
        ax2.set_yticks(range(len(df_sharpe_sorted)))
        ax2.set_yticklabels([f"{row['symbol']} ({row['strategy']})" for _, row in df_sharpe_sorted.iterrows()])
        ax2.set_xlabel('Sharpe Ratio')
        ax2.set_title('Strategy Performance by Sharpe Ratio')
        ax2.grid(True, alpha=0.3)
        ax2.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        ax2.axvline(x=1.0, color='green', linestyle='--', alpha=0.5, label='Good Sharpe (1.0)')

        plt.tight_layout()
        plt.savefig('best_performers_analysis.png', dpi=300, bbox_inches='tight')
        print("[OK] Best performers analysis chart saved: best_performers_analysis.png")
        plt.show()

    def create_summary_dashboard(self):
        """Create summary dashboard"""
        if not self.results_data:
            return

        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)
        strategy_summary = self.results_data['strategy_performance_summary']

        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        fig.suptitle('VectorBT Real Backtest Summary Dashboard', fontsize=18, fontweight='bold')

        # 1. Performance summary table
        ax1 = fig.add_subplot(gs[0, :])
        ax1.axis('tight')
        ax1.axis('off')

        # Create table data
        table_data = []
        headers = ['Stock', 'Strategy', 'Return', 'Sharpe', 'Max DD', 'Trades', 'Excess']

        for _, row in df.iterrows():
            table_data.append([
                row['symbol'],
                row['strategy'],
                f"{row['total_return']:.2%}",
                f"{row['sharpe_ratio']:.2f}",
                f"{row['max_drawdown']:.2%}",
                str(row['num_trades']),
                f"{row['excess_return']:.2%}"
            ])

        table = ax1.table(cellText=table_data, colLabels=headers,
                         cellLoc='center', loc='center',
                         colColours=['#f3f3f3']*len(headers))
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.0, 1.5)
        ax1.set_title('Complete Backtest Results', fontweight='bold', pad=20)

        # 2. Strategy comparison radar
        ax2 = fig.add_subplot(gs[1, 0])
        strategies = df['strategy'].unique()
        metrics = ['total_return', 'sharpe_ratio']

        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]

        for strategy in strategies:
            strategy_data = df[df['strategy'] == strategy]
            values = [strategy_data[metric].mean() for metric in metrics]
            values += values[:1]
            ax2.plot(angles, values, 'o-', linewidth=2, label=strategy)
            ax2.fill(angles, values, alpha=0.25)

        ax2.set_xticks(angles[:-1])
        ax2.set_xticklabels([m.replace('_', ' ').title() for m in metrics])
        ax2.set_title('Strategy Performance Radar', fontweight='bold')
        ax2.legend()
        ax2.grid(True)

        # 3. Win rate chart
        ax3 = fig.add_subplot(gs[1, 1])
        win_rates = []
        strategy_names = []

        for strategy in strategies:
            strategy_data = df[df['strategy'] == strategy]
            win_rate = (strategy_data['excess_return'] > 0).mean()
            win_rates.append(win_rate * 100)
            strategy_names.append(strategy)

        bars = ax3.bar(strategy_names, win_rates, color=['#2E86AB', '#A23B72'])
        ax3.set_title('Win Rate vs Benchmark')
        ax3.set_ylabel('Win Rate (%)')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=50, color='black', linestyle='--', alpha=0.5, label='50% Benchmark')

        # Add value labels
        for bar, rate in zip(bars, win_rates):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{rate:.0f}%', ha='center', va='bottom')

        # 4. Risk-adjusted returns
        ax4 = fig.add_subplot(gs[1, 2])
        risk_adj_returns = []

        for strategy in strategies:
            strategy_data = df[df['strategy'] == strategy]
            risk_adj = strategy_data['total_return'].mean() / abs(strategy_data['max_drawdown'].mean())
            risk_adj_returns.append(risk_adj * 100)

        bars = ax4.bar(strategy_names, risk_adj_returns, color=['#2E86AB', '#A23B72'])
        ax4.set_title('Risk-Adjusted Returns')
        ax4.set_ylabel('Return/Max DD (%)')
        ax4.grid(True, alpha=0.3)

        # Add value labels
        for bar, adj_ret in zip(bars, risk_adj_returns):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{adj_ret:.1f}', ha='center', va='bottom')

        # 5. Summary statistics
        ax5 = fig.add_subplot(gs[2, :])
        ax5.axis('tight')
        ax5.axis('off')

        summary_text = f"""
        BACKTEST SUMMARY STATISTICS

        Period: {self.results_data['period']} | Initial Cash: ${self.results_data['initial_cash']:,} | Fees: {self.results_data['fees']:.1%}

        Best Overall Performance: {df.loc[df['total_return'].idxmax(), 'symbol']} ({df.loc[df['total_return'].idxmax(), 'strategy']})
        Return: {df['total_return'].max():.2%} | Sharpe: {df.loc[df['total_return'].idxmax(), 'sharpe_ratio']:.2f}

        Best Risk-Adjusted: {df.loc[df['sharpe_ratio'].idxmax(), 'symbol']} ({df.loc[df['sharpe_ratio'].idxmax(), 'strategy']})
        Sharpe: {df['sharpe_ratio'].max():.2f} | Return: {df.loc[df['sharpe_ratio'].idxmax(), 'total_return']:.2%}

        Most Stable: {df.loc[df['max_drawdown'].idxmin(), 'symbol']} ({df.loc[df['max_drawdown'].idxmin(), 'strategy']})
        Max Drawdown: {df['max_drawdown'].min():.2%} | Return: {df.loc[df['max_drawdown'].idxmin(), 'total_return']:.2%}
        """

        ax5.text(0.1, 0.5, summary_text, fontsize=11, verticalalignment='center',
                fontfamily='monospace', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))

        plt.tight_layout()
        plt.savefig('summary_dashboard.png', dpi=300, bbox_inches='tight')
        print("[OK] Summary dashboard saved: summary_dashboard.png")
        plt.show()

    def generate_all_charts(self):
        """Generate all visualization charts"""
        print("\n" + "="*60)
        print("GENERATING BACKTEST VISUALIZATION CHARTS")
        print("="*60)

        try:
            print("\n[CHART 1] Strategy Performance Analysis...")
            self.create_strategy_performance_chart()

            print("\n[CHART 2] Risk-Return Scatter Plot...")
            self.create_risk_return_scatter()

            print("\n[CHART 3] Portfolio Performance Heatmap...")
            self.create_portfolio_heatmap()

            print("\n[CHART 4] Trading Frequency Analysis...")
            self.create_trading_frequency_chart()

            print("\n[CHART 5] Best Performers Analysis...")
            self.create_best_performers_chart()

            print("\n[CHART 6] Summary Dashboard...")
            self.create_summary_dashboard()

            print(f"\n{'='*60}")
            print("ALL VISUALIZATION CHARTS GENERATED SUCCESSFULLY!")
            print("="*60)
            print("Generated files:")
            print("  - backtest_performance_analysis.png")
            print("  - risk_return_analysis.png")
            print("  - portfolio_performance_heatmap.png")
            print("  - trading_frequency_analysis.png")
            print("  - best_performers_analysis.png")
            print("  - summary_dashboard.png")

        except Exception as e:
            print(f"[ERROR] Chart generation failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function"""
    visualizer = ASCIIBacktestVisualizer()
    visualizer.generate_all_charts()


if __name__ == "__main__":
    main()