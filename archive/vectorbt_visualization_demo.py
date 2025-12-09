#!/usr/bin/env python3
"""
VectorBT 高級數據可視化系統
展示VectorBT的強大圖表功能和數據分析能力

Reference: https://vectorbt.dev/getting-started/features/#extra
"""

import requests
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# VectorBT樣式設置
vbt.settings.set_theme('seaborn')
vbt.settings.plotting['layout']['template'] = 'plotly_white'

class VectorBTVisualizer:
    """VectorBT 高級可視化系統"""

    def __init__(self, symbol='0700.HK'):
        self.symbol = symbol
        self.data = self.get_stock_data(symbol)
        self.portfolio = None

    def get_stock_data(self, symbol, days=1095):
        """獲取股價數據"""
        try:
            url = "http://18.180.162.113:9191/inst/getInst"
            params = {"symbol": symbol.lower(), "duration": days}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            close_data = data['data']['close']
            dates = list(close_data.keys())
            closes = list(close_data.values())

            df = pd.DataFrame({
                'date': pd.to_datetime(dates),
                'close': [float(x) for x in closes]
            })
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

            # 添加OHLCV數據用於VectorBT可視化
            df['open'] = df['close'].shift(1).fillna(df['close'])
            df['high'] = df['close'] * 1.01
            df['low'] = df['close'] * 0.99
            df['volume'] = np.random.randint(1000000, 5000000, len(df))

            print(f"✅ 數據獲取成功: {len(df)}天, 價格範圍: {df['close'].min():.2f} - {df['close'].max():.2f}")
            return df

        except Exception as e:
            print(f"❌ 數據獲取失敗: {str(e)}")
            return None

    def generate_signals(self, rsi_period=14, overbought=70, oversold=30):
        """生成RSI交易信號"""
        # 計算RSI指標
        rsi = vbt.RSI.run(self.data['close'], window=rsi_period)

        # 生成交易信號
        entries = rsi.rsi_crossed_below(oversold)  # RSI跌破超賣線買入
        exits = rsi.rsi_crossed_above(overbought)   # RSI突破超買線賣出

        return entries, exits, rsi

    def create_portfolio(self, entries, exits, init_cash=100000, fees=0.001):
        """創建VectorBT投資組合"""
        self.portfolio = vbt.Portfolio.from_signals(
            close=self.data['close'],
            entries=entries,
            exits=exits,
            init_cash=init_cash,
            fees=fees,
            slippage=0.001,
            freq='D'
        )
        return self.portfolio

    def 針對核心可視化展示(self):
        """VectorBT核心可視化功能展示"""
        if self.data is None:
            print("❌ 數據未加載")
            return

        print("\n🎯 開始VectorBT核心可視化展示...")

        # 生成信號
        entries, exits, rsi = self.generate_signals()

        # 創建投資組合
        portfolio = self.create_portfolio(entries, exits)

        # === 1. 價格和信號圖表 ===
        print("\n📈 1. 價格與交易信號可視化")
        # 設置VectorBT主題
        vbt.settings.set_theme('seaborn')

        # K線圖 + 信號
        fig = go.Figure()

        # 添加K線圖
        fig.add_trace(go.Candlestick(
            x=self.data.index,
            open=self.data['open'],
            high=self.data['high'],
            low=self.data['low'],
            close=self.data['close'],
            name='K線'
        ))

        # 添加買入信號
        buy_signals = entries[entries == True]
        if len(buy_signals) > 0:
            buy_prices = self.data.loc[buy_signals.index, 'close']
            fig.add_trace(go.Scatter(
                x=buy_signals.index,
                y=buy_prices,
                mode='markers',
                marker=dict(symbol='triangle-up', size=12, color='green'),
                name='買入信號'
            ))

        # 添加賣出信號
        sell_signals = exits[exits == True]
        if len(sell_signals) > 0:
            sell_prices = self.data.loc[sell_signals.index, 'close']
            fig.add_trace(go.Scatter(
                x=sell_signals.index,
                y=sell_prices,
                mode='markers',
                marker=dict(symbol='triangle-down', size=12, color='red'),
                name='賣出信號'
            ))

        # 添加RSI圖
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(
            x=self.data.index,
            y=rsi.rsi,
            name='RSI',
            line=dict(color='blue')
        ))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", name="超買線")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", name="超賣線")

        # 保存圖表
        fig.write_html(f"vectorbt_price_signals_{self.symbol}.html")
        fig_rsi.write_html(f"vectorbt_rsi_{self.symbol}.html")

        print("   ✅ 價格信號圖已保存")

        # === 2. 投資組合表現可視化 ===
        print("\n💰 2. 投資組合表現分析")

        # 投資組合價值曲線
        fig_portfolio = portfolio.plot()
        fig_portfolio.write_html(f"vectorbt_portfolio_{self.symbol}.html")

        # 淨值曲線與基準對比
        equity_curve = portfolio.value()
        benchmark = (self.data['close'] / self.data['close'].iloc[0]) * 100000

        fig_comparison = go.Figure()
        fig_comparison.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve,
            name='策略淨值',
            line=dict(color='blue')
        ))
        fig_comparison.add_trace(go.Scatter(
            x=benchmark.index,
            y=benchmark,
            name='基準表現',
            line=dict(color='gray', dash='dash')
        ))

        fig_comparison.update_layout(
            title='策略 vs 基準表現對比',
            xaxis_title='日期',
            yaxis_title='淨值 (HKD)'
        )

        fig_comparison.write_html(f"vectorbt_benchmark_comparison_{self.symbol}.html")

        print("   ✅ 投資組合圖表已保存")

        # === 3. 交易分析可視化 ===
        print("\n📊 3. 交易分析統計")

        # 獲取交易記錄
        trades = portfolio.trades.records_readable
        if len(trades) > 0:
            # 交易分布圖
            fig_trades = px.histogram(
                trades,
                x='Return',
                title="交易收益分布",
                nbins=20
            )
            fig_trades.write_html(f"vectorbt_trades_distribution_{self.symbol}.html")

            # 月度收益統計
            monthly_returns = portfolio.resample('M').returns()
            fig_monthly = go.Figure(data=[
                go.Bar(x=monthly_returns.index.strftime('%Y-%m'), y=monthly_returns.values)
            ])
            fig_monthly.update_layout(
                title='月度收益統計',
                xaxis_title='月份',
                yaxis_title='收益率'
            )
            fig_monthly.write_html(f"vectorbt_monthly_returns_{self.symbol}.html")

            print(f"   ✅ 交易分析圖已保存 ({len(trades)}筆交易)")

        # === 4. 風險指標可視化 ===
        print("\n⚠️ 4. 風險指標分析")

        # 回撤分析
        drawdown = portfolio.drawdown()
        fig_drawdown = drawdown.plot()
        fig_drawdown.write_html(f"vectorbt_drawdown_{self.symbol}.html")

        # 滾動Sharpe比率
        rolling_sharpe = portfolio.rolling_sharpe()
        fig_rolling = rolling_sharpe.plot()
        fig_rolling.write_html(f"vectorbt_rolling_sharpe_{self.symbol}.html")

        # 統計指標熱力圖
        stats = portfolio.stats()

        # 創建統計指標表
        stats_data = {
            '指標': ['總回報', '年化回報', 'Sharpe比率', '最大回撤', 'Calmar比率', '勝率', '盈利因子'],
            '數值': [
                f"{stats['Total Return [%]']:.2f}%",
                f"{stats['Annual Return [%]']:.2f}%",
                f"{stats['Sharpe Ratio']:.4f}",
                f"{stats['Max Drawdown [%]']:.2f}%",
                f"{stats['Calmar Ratio']:.4f}",
                f"{stats['Win Rate [%]']:.2f}%",
                f"{stats['Profit Factor']:.2f}"
            ]
        }

        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=list(stats_data.keys()), fill_color='lightblue'),
            cells=dict(values=list(stats_data.values()), fill_color='lightyellow')
        )])

        fig_stats.update_layout(title='策略績效指標')
        fig_stats.write_html(f"vectorbt_performance_stats_{self.symbol}.html")

        print("   ✅ 風險指標圖已保存")

        # === 5. 多策略對比可視化 ===
        print("\n🔄 5. 多策略表現對比")

        strategies = {}
        strategy_params = [
            (14, 70, 30),  # 基礎RSI
            (10, 80, 20),  # 激進RSI
            (20, 60, 40),  # 保守RSI
        ]

        for i, (period, ob, os) in enumerate(strategy_params):
            entries_i, exits_i, rsi_i = self.generate_signals(period, ob, os)
            portfolio_i = vbt.Portfolio.from_signals(
                close=self.data['close'],
                entries=entries_i,
                exits=exits_i,
                init_cash=100000,
                fees=0.001
            )
            strategies[f'RSI_{period}_{ob}_{os}'] = portfolio_i.value()

        # 多策略對比圖
        fig_strategies = go.Figure()
        for strategy_name, equity in strategies.items():
            fig_strategies.add_trace(go.Scatter(
                x=equity.index,
                y=equity,
                name=strategy_name,
                mode='lines'
            ))

        fig_strategies.update_layout(
            title='多策略表現對比',
            xaxis_title='日期',
            yaxis_title='淨值 (HKD)'
        )

        fig_strategies.write_html(f"vectorbt_strategy_comparison_{self.symbol}.html")

        print("   ✅ 多策略對比圖已保存")

        # === 生成總結報告 ===
        self.generate_visualization_report()

    def generate_visualization_report(self):
        """生成可視化總結報告"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>VectorBT 高級可視化展示 - {self.symbol}</title>
            <style>
                body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 20px; background: #f5f5f5; }}
                .header {{ background: linear-gradient(45deg, #1f77b4, #ff7f0e); color: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
                .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                .chart-link {{ display: block; background: #007bff; color: white; padding: 10px; text-align: center; text-decoration: none; border-radius: 5px; margin: 5px 0; }}
                .chart-link:hover {{ background: #0056b3; }}
                .feature {{ background: #e8f4f8; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .metric {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 VectorBT 高級數據可視化系統</h1>
                <h2>{self.symbol} - 專業量化分析圖表</h2>
                <p>基於 https://vectorbt.dev/getting-started/features/#extra</p>
                <p>生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>📈 價格與信號分析</h3>
                    <div class="feature">
                        <div class="metric">K線圖 + 交易信號</div>
                        <p>互動式價格圖表與買賣點標記</p>
                    </div>
                    <a href="vectorbt_price_signals_{self.symbol}.html" class="chart-link" target="_blank">📊 價格信號圖</a>
                    <a href="vectorbt_rsi_{self.symbol}.html" class="chart-link" target="_blank">📈 RSI指標圖</a>
                </div>

                <div class="card">
                    <h3>💰 投資組合表現</h3>
                    <div class="feature">
                        <div class="metric">淨值曲線分析</div>
                        <p>策略表現與基準對比</p>
                    </div>
                    <a href="vectorbt_portfolio_{self.symbol}.html" class="chart-link" target="_blank">📈 投資組合圖</a>
                    <a href="vectorbt_benchmark_comparison_{self.symbol}.html" class="chart-link" target="_blank">⚖️ 基準對比圖</a>
                </div>

                <div class="card">
                    <h3>📊 交易統計分析</h3>
                    <div class="feature">
                        <div class="metric">交易收益分布</div>
                        <p>月度收益統計與分析</p>
                    </div>
                    <a href="vectorbt_trades_distribution_{self.symbol}.html" class="chart-link" target="_blank">📊 交易分布圖</a>
                    <a href="vectorbt_monthly_returns_{self.symbol}.html" class="chart-link" target="_blank">📅 月度收益圖</a>
                </div>

                <div class="card">
                    <h3>⚠️ 風險管理分析</h3>
                    <div class="feature">
                        <div class="metric">回撤與風險指標</div>
                        <p>滾動Sharpe比率分析</p>
                    </div>
                    <a href="vectorbt_drawdown_{self.symbol}.html" class="chart-link" target="_blank">📉 回撤分析圖</a>
                    <a href="vectorbt_rolling_sharpe_{self.symbol}.html" class="chart-link" target="_blank">🎯 滾動Sharpe圖</a>
                </div>

                <div class="card">
                    <h3>📋 績效指標表</h3>
                    <div class="feature">
                        <div class="metric">完整績效統計</div>
                        <p>關鍵指標一覽表</p>
                    </div>
                    <a href="vectorbt_performance_stats_{self.symbol}.html" class="chart-link" target="_blank">📈 績效指標表</a>
                </div>

                <div class="card">
                    <h3>🔄 多策略對比</h3>
                    <div class="feature">
                        <div class="metric">策略表現比較</div>
                        <p>參數敏感性分析</p>
                    </div>
                    <a href="vectorbt_strategy_comparison_{self.symbol}.html" class="chart-link" target="_blank">⚖️ 策略對比圖</a>
                </div>
            </div>

            <div class="card">
                <h3>🎯 VectorBT 核心功能特色</h3>
                <div class="grid">
                    <div class="feature">
                        <h4>🚀 高性能向量化計算</h4>
                        <p>比傳循環快1000倍的優化性能</p>
                    </div>
                    <div class="feature">
                        <h4>📊 內置豐富圖表</h4>
                        <p>專業金融可視化圖表庫</p>
                    </div>
                    <div class="feature">
                        <h4>📈 實時互動圖表</h4>
                        <p>基於Plotly的動態交互功能</p>
                    </div>
                    <div class="feature">
                        <h4>⚡ 靈活數據處理</h4>
                        <p>支持Pandas和NumPy無縫集成</p>
                    </div>
                    <div class="feature">
                        <h4>🎨 自定義樣式</h4>
                        <p>支持多種主題和個性化設置</p>
                    </div>
                    <div class="feature">
                        <h4>🔧 高級統計分析</h4>
                        <p>內置風險管理和績效評估</p>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>💡 使用說明</h3>
                <p>1. 點擊上方鏈接查看各類可視化圖表</p>
                <p>2. 所有圖表支持縮放、平移和數據懸停</p>
                <p>3. 可以導出圖表為PNG或PDF格式</p>
                <p>4. 支持實時數據更新和動態刷新</p>
            </div>
        </body>
        </html>
        """

        report_file = f"vectorbt_visualization_dashboard_{self.symbol}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n🎉 VectorBT可視化報告已生成: {report_file}")

def main():
    """主函數"""
    print("=" * 80)
    print("🚀 VectorBT 高級數據可視化系統")
    print("=" * 80)
    print("基於: https://vectorbt.dev/getting-started/features/#extra")
    print("=" * 80)

    # 創建可視化器
    visualizer = VectorBTVisualizer('0700.HK')

    if visualizer.data is None:
        print("❌ 無法獲取數據，退出程序")
        return

    # 執行完整可視化展示
    visualizer.針對核心可視化展示()

    print("\n" + "=" * 80)
    print("🎉 VectorBT可視化展示完成！")
    print("=" * 80)
    print("📊 所有圖表已保存為HTML格式")
    print("🔗 點擊 vectorbt_visualization_dashboard_0700.HK.html 查看總覽")
    print("⚡ 支持縮放、平移、數據懸停等交互功能")
    print("=" * 80)

if __name__ == "__main__":
    main()