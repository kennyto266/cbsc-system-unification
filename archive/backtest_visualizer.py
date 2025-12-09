#!/usr/bin/env python3
"""
Backtest Visualizer
真实回测可视化图表生成器
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

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class BacktestVisualizer:
    """回测可视化类"""

    def __init__(self, results_file='fixed_real_backtest_results.json'):
        """初始化可视化器"""
        self.results_file = results_file
        self.results_data = None
        self.load_results()

    def load_results(self):
        """加载回测结果"""
        try:
            with open(self.results_file, 'r') as f:
                self.results_data = json.load(f)
            print(f"[OK] 加载回测结果: {self.results_file}")
        except Exception as e:
            print(f"[ERROR] 无法加载回测结果: {e}")
            return

    def create_strategy_performance_chart(self):
        """创建策略表现对比图表"""
        if not self.results_data:
            return

        # 准备数据
        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Real VectorBT Backtest Performance Analysis', fontsize=16, fontweight='bold')

        # 1. 总收益率对比
        ax1 = axes[0, 0]
        returns_pivot = df.pivot(index='symbol', columns='strategy', values='total_return')
        returns_pivot.plot(kind='bar', ax=ax1, color=['#2E86AB', '#A23B72'])
        ax1.set_title('Total Return by Stock and Strategy')
        ax1.set_ylabel('Total Return')
        ax1.set_xlabel('Stock')
        ax1.legend(title='Strategy')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # 2. Sharpe比率对比
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

        # 3. 最大回撤对比
        ax3 = axes[1, 0]
        drawdown_pivot = df.pivot(index='symbol', columns='strategy', values='max_drawdown')
        drawdown_pivot.plot(kind='bar', ax=ax3, color=['#2E86AB', '#A23B72'])
        ax3.set_title('Maximum Drawdown by Stock and Strategy')
        ax3.set_ylabel('Max Drawdown')
        ax3.set_xlabel('Stock')
        ax3.legend(title='Strategy')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # 4. 策略平均表现对比
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

        # 添加数值标签
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
        print("[OK] 策略表现分析图表已保存: backtest_performance_analysis.png")
        plt.show()

    def create_risk_return_scatter(self):
        """创建风险-收益散点图"""
        if not self.results_data:
            return

        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        fig, ax = plt.subplots(figsize=(12, 8))

        # 按策略分组
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

            # 添加股票标签
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

        # 添加风险区域标注
        ax.fill_between([-40, 0], [0, 0], [30, 30], alpha=0.1, color='green', label='Low Risk Zone')
        ax.fill_between([-40, 0], [0, 0], [-20, -20], alpha=0.1, color='red', label='High Risk Zone')

        plt.tight_layout()
        plt.savefig('risk_return_analysis.png', dpi=300, bbox_inches='tight')
        print("[OK] 风险-收益分析图表已保存: risk_return_analysis.png")
        plt.show()

    def create_portfolio_heatmap(self):
        """创建投资组合表现热力图"""
        if not self.results_data:
            return

        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        # 创建指标矩阵
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown']
        stocks = df['symbol'].unique()
        strategies = df['strategy'].unique()

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        for i, metric in enumerate(metrics):
            # 创建数据透视表
            pivot_data = df.pivot(index='symbol', columns='strategy', values=metric)

            # 热力图
            im = axes[i].imshow(pivot_data.values, cmap='RdYlGn', aspect='auto')

            # 设置标签
            axes[i].set_xticks(np.arange(len(strategies)))
            axes[i].set_yticks(np.arange(len(stocks)))
            axes[i].set_xticklabels(strategies)
            axes[i].set_yticklabels(stocks)

            # 添加数值
            for row in range(len(stocks)):
                for col in range(len(strategies)):
                    value = pivot_data.iloc[row, col]
                    text_color = 'black' if abs(value) < 0.5 else 'white'
                    axes[i].text(col, row, f'{value:.2f}',
                                ha="center", va="center", color=text_color, fontsize=10)

            axes[i].set_title(f'{metric.replace("_", " ").title()}', fontweight='bold')

            # 添加颜色条
            cbar = plt.colorbar(im, ax=axes[i])
            cbar.set_label(metric.replace("_", " ").title(), rotation=270, labelpad=15)

        plt.tight_layout()
        plt.savefig('portfolio_performance_heatmap.png', dpi=300, bbox_inches='tight')
        print("[OK] 投资组合表现热力图已保存: portfolio_performance_heatmap.png")
        plt.show()

    def create_trading_frequency_chart(self):
        """创建交易频率分析图表"""
        if not self.results_data:
            return

        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 1. 交易次数对比
        trades_pivot = df.pivot(index='symbol', columns='strategy', values='num_trades')
        trades_pivot.plot(kind='bar', ax=ax1, color=['#2E86AB', '#A23B72'])
        ax1.set_title('Number of Trades by Stock and Strategy')
        ax1.set_ylabel('Number of Trades')
        ax1.set_xlabel('Stock')
        ax1.legend(title='Strategy')
        ax1.grid(True, alpha=0.3)

        # 2. 超额收益分析
        excess_returns_pivot = df.pivot(index='symbol', columns='strategy', values='excess_return')
        excess_returns_pivot.plot(kind='bar', ax=ax2, color=['#2E86AB', '#A23B72'])
        ax2.set_title('Excess Return vs Benchmark')
        ax2.set_ylabel('Excess Return')
        ax2.set_xlabel('Stock')
        ax2.legend(title='Strategy')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        plt.tight_layout()
        plt.savefig('trading_frequency_analysis.png', dpi=300, bbox_inches='tight')
        print("[OK] 交易频率分析图表已保存: trading_frequency_analysis.png")
        plt.show()

    def create_comprehensive_dashboard(self):
        """创建综合仪表板"""
        if not self.results_data:
            return

        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

        fig.suptitle('VectorBT Real Backtest Comprehensive Dashboard', fontsize=18, fontweight='bold')

        detailed_results = self.results_data['detailed_results']
        df = pd.DataFrame(detailed_results)

        # 1. 总收益率雷达图
        ax1 = fig.add_subplot(gs[0, 0])
        self._create_radar_chart(ax1, df, 'total_return', 'Total Return Radar')

        # 2. Sharpe比率雷达图
        ax2 = fig.add_subplot(gs[0, 1])
        self._create_radar_chart(ax2, df, 'sharpe_ratio', 'Sharpe Ratio Radar')

        # 3. 风险指标对比
        ax3 = fig.add_subplot(gs[0, 2:])
        strategies = df['strategy'].unique()
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown']

        x = np.arange(len(metrics))
        width = 0.35

        for i, strategy in enumerate(strategies):
            strategy_data = df[df['strategy'] == strategy]
            values = [strategy_data[metric].mean() for metric in metrics]
            ax3.bar(x + i * width, values, width, label=strategy, alpha=0.7)

        ax3.set_title('Average Strategy Metrics Comparison')
        ax3.set_ylabel('Values')
        ax3.set_xticks(x + width / 2)
        ax3.set_xticklabels([m.replace('_', ' ').title() for m in metrics])
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. 策略表现矩阵
        ax4 = fig.add_subplot(gs[1, :2])
        performance_matrix = df.pivot_table(index='symbol', columns='strategy', values='total_return', aggfunc='mean')
        sns.heatmap(performance_matrix, annot=True, fmt='.2%', cmap='RdYlGn', ax=ax4, cbar_kws={'label': 'Total Return'})
        ax4.set_title('Performance Heatmap')

        # 5. 回撤分析
        ax5 = fig.add_subplot(gs[1, 2:])
        drawdown_matrix = df.pivot_table(index='symbol', columns='strategy', values='max_drawdown', aggfunc='mean')
        sns.heatmap(drawdown_matrix, annot=True, fmt='.2%', cmap='RdYlGn_r', ax=ax5, cbar_kws={'label': 'Max Drawdown'})
        ax5.set_title('Drawdown Heatmap')

        # 6. 综合评分
        ax6 = fig.add_subplot(gs[2, :])
        self._create_performance_score_chart(ax6, df)

        plt.tight_layout()
        plt.savefig('comprehensive_dashboard.png', dpi=300, bbox_inches='tight')
        print("[OK] 综合仪表板已保存: comprehensive_dashboard.png")
        plt.show()

    def _create_radar_chart(self, ax, df, metric, title):
        """创建雷达图"""
        strategies = df['strategy'].unique()
        stocks = df['symbol'].unique()

        angles = np.linspace(0, 2 * np.pi, len(stocks), endpoint=False).tolist()
        angles += angles[:1]  # 闭合

        for strategy in strategies:
            strategy_data = df[df['strategy'] == strategy]
            values = strategy_data[metric].tolist()
            values += values[:1]  # 闭合

            ax.plot(angles, values, 'o-', linewidth=2, label=strategy)
            ax.fill(angles, values, alpha=0.25)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(stocks)
        ax.set_title(title, fontweight='bold')
        ax.legend()
        ax.grid(True)

    def _create_performance_score_chart(self, ax, df):
        """创建综合评分图表"""
        # 计算综合评分
        df['performance_score'] = (
            df['sharpe_ratio'] * 0.4 +
            df['total_return'] * 2 +
            (1 + df['max_drawdown']) * 0.3  # 回撤越小越好
        ) * 100

        pivot_scores = df.pivot_table(index='symbol', columns='strategy', values='performance_score', aggfunc='mean')

        pivot_scores.plot(kind='bar', ax=ax, color=['#2E86AB', '#A23B72'], width=0.8)
        ax.set_title('Overall Performance Score (Higher is Better)')
        ax.set_ylabel('Performance Score')
        ax.set_xlabel('Stock')
        ax.legend(title='Strategy')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=100, color='green', linestyle='--', alpha=0.5, label='Good Performance (100)')

        # 添加数值标签
        for p in ax.patches:
            ax.annotate(f'{p.get_height():.0f}',
                       (p.get_x() + p.get_width() / 2., p.get_height()),
                       ha='center', va='center',
                       xytext=(0, 5),
                       textcoords='offset points',
                       fontsize=8)

    def generate_all_charts(self):
        """生成所有图表"""
        print("\n" + "="*60)
        print("GENERATING BACKTEST VISUALIZATION CHARTS")
        print("="*60)

        try:
            print("\n[CHART 1] 策略表现分析图表...")
            self.create_strategy_performance_chart()

            print("\n[CHART 2] 风险-收益散点图...")
            self.create_risk_return_scatter()

            print("\n[CHART 3] 投资组合表现热力图...")
            self.create_portfolio_heatmap()

            print("\n[CHART 4] 交易频率分析图表...")
            self.create_trading_frequency_chart()

            print("\n[CHART 5] 综合仪表板...")
            self.create_comprehensive_dashboard()

            print(f"\n{'='*60}")
            print("ALL VISUALIZATION CHARTS GENERATED SUCCESSFULLY!")
            print("="*60)
            print("Generated files:")
            print("  - backtest_performance_analysis.png")
            print("  - risk_return_analysis.png")
            print("  - portfolio_performance_heatmap.png")
            print("  - trading_frequency_analysis.png")
            print("  - comprehensive_dashboard.png")

        except Exception as e:
            print(f"[ERROR] 图表生成失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    visualizer = BacktestVisualizer()
    visualizer.generate_all_charts()


if __name__ == "__main__":
    main()