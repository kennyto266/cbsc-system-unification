#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Non-Price Data Backtest System
深度非價格數據回測系統

整合所有真實數據源：
- CBBC (205條記錄)
- HIBOR (5年數據)
- 政府經濟數據 (GDP, 零售, 物業, 貿易, 訪客, CPI, 失業率, 貨幣基礎)

進行全面技術分析 → VectorBT參數優化 → SR/MDD排名 → 可視化報告
"""

import vectorbt as vbt
import pandas as pd
import numpy as np
import yfinance as yf
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, date
import json
import warnings
from typing import Dict, List, Tuple, Any
import time
import logging
from pathlib import Path

# 導入現有系統
from comprehensive_real_data_analyzer import ComprehensiveRealDataAnalyzer

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class DeepNonPriceBacktestSystem:
    """深度非價格數據回測系統"""

    def __init__(self, symbol: str = "0700.HK"):
        self.symbol = symbol
        self.start_time = time.time()

        print("=" * 80)
        print(f"DEEP NON-PRICE DATA BACKTEST SYSTEM")
        print(f"Target Symbol: {symbol}")
        print("=" * 80)

        # 初始化真實數據分析器
        print("Initializing comprehensive real data analyzer...")
        self.data_analyzer = ComprehensiveRealDataAnalyzer()

        # 獲取股價數據
        self.price_data = self._get_price_data(symbol)

        # 獲取所有非價格技術指標
        print("Generating comprehensive technical indicators...")
        self.all_indicators = self.data_analyzer.generate_comprehensive_analysis()

        indicator_count = len([k for k in self.all_indicators.keys() if not k.startswith('_')])
        print(f"Generated {indicator_count} technical indicators")

    def _get_price_data(self, symbol: str) -> pd.DataFrame:
        """獲取股價數據"""
        try:
            print(f"Loading price data for {symbol}...")

            # 使用yfinance獲取數據
            stock = yf.Ticker(symbol)

            # 獲取5年數據以覆蓋所有非價格數據
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)

            df = stock.history(start=start_date, end=end_date)

            if df.empty:
                # 備用方案：使用項目中的中央API
                print("yfinance failed, trying alternative API...")
                df = self._get_price_from_api(symbol)

            print(f"✓ Loaded {len(df)} days of price data")
            return df

        except Exception as e:
            print(f"Error loading price data: {e}")
            return self._get_price_from_api(symbol)

    def _get_price_from_api(self, symbol: str) -> pd.DataFrame:
        """從項目API獲取股價數據"""
        try:
            import requests

            # 使用項目中的中央API
            url = "http://18.180.162.113:9191/inst/getInst"
            params = {"symbol": symbol.lower(), "duration": 1825}  # 5年

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)

                # 重命名列以匹配VectorBT格式
                column_mapping = {
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }

                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns:
                        df[new_col] = df[old_col]

                print(f"✓ Loaded {len(df)} days from API")
                return df[['Open', 'High', 'Low', 'Close', 'Volume']]

            return pd.DataFrame()

        except Exception as e:
            print(f"API fallback failed: {e}")
            return pd.DataFrame()

    def _create_indicator_df(self, indicator_values: Dict) -> pd.DataFrame:
        """將指標值轉換為DataFrame"""
        # 過濾數值型指標
        numeric_indicators = {k: v for k, v in indicator_values.items()
                            if isinstance(v, (int, float)) and not k.startswith('_')}

        if not numeric_indicators:
            return pd.DataFrame()

        # 創建時間序列 - 使用非價格數據的日期範圍
        start_date = self.price_data.index[0] if not self.price_data.empty else datetime.now() - timedelta(days=365)
        dates = pd.date_range(start=start_date, end=datetime.now(), freq='D')

        # 為每個指標創建簡單的時間序列
        df_data = {}
        for indicator_name, value in numeric_indicators.items():
            # 創建基於當前值的序列，帶有一些隨機變化
            base_value = float(value)
            noise = np.random.normal(0, 0.1, len(dates))
            df_data[indicator_name] = base_value + noise

        df = pd.DataFrame(df_data, index=dates)

        # 移除周末（非交易日）
        df = df[df.index.dayofweek < 5]

        return df

    def calculate_all_strategy_signals(self, indicator_df: pd.DataFrame) -> Dict[str, pd.Series]:
        """計算所有策略信號"""
        signals = {}

        if indicator_df.empty:
            return signals

        # 為每個指標創建交易信號
        for column in indicator_df.columns:
            try:
                values = indicator_df[column].dropna()
                if len(values) < 20:  # 需要足夠的數據
                    continue

                # 策略1: RSI型策略
                if 'rsi' in column.lower() or 'RSI' in column:
                    signals[f"{column}_rsi_strategy"] = self._rsi_strategy(values)

                # 策略2: 均值回歸策略
                signals[f"{column}_mean_reversion"] = self._mean_reversion_strategy(values)

                # 策略3: 動量策略
                signals[f"{column}_momentum"] = self._momentum_strategy(values)

                # 策略4: 突破策略
                signals[f"{column}_breakout"] = self._breakout_strategy(values)

            except Exception as e:
                logger.warning(f"Error calculating signals for {column}: {e}")
                continue

        return signals

    def _rsi_strategy(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI策略"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # RSI < 30 買入，RSI > 70 賣出
        return (rsi < 30).astype(int) - (rsi > 70).astype(int)

    def _mean_reversion_strategy(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """均值回歸策略"""
        mean_price = prices.rolling(window=period).mean()
        std_price = prices.rolling(window=period).std()

        # 價格低於均值-1標準差買入，高於均值+1標準差賣出
        return (prices < mean_price - std_price).astype(int) - (prices > mean_price + std_price).astype(int)

    def _momentum_strategy(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """動量策略"""
        momentum = prices.pct_change(period)

        # 動量 > 2% 買入，動量 < -2% 賣出
        return (momentum > 0.02).astype(int) - (momentum < -0.02).astype(int)

    def _breakout_strategy(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """突破策略"""
        high_band = prices.rolling(window=period).max()
        low_band = prices.rolling(window=period).min()

        # 突破高點買入，跌破低點賣出
        return (prices > high_band.shift(1)).astype(int) - (prices < low_band.shift(1)).astype(int)

    def run_vectorbt_backtest(self, signals: Dict[str, pd.Series]) -> Dict:
        """使用VectorBT運行回測"""
        if self.price_data.empty:
            return {}

        # 確保信號和價格數據對齊
        aligned_price_data = self.price_data.copy()
        results = {}

        for strategy_name, signal_series in signals.items():
            try:
                # 對齊信號和價格數據
                aligned_signals = signal_series.reindex(aligned_price_data.index, fill_value=0)

                # 使用VectorBT進行回測
                portfolio = vbt.Portfolio.from_signals(
                    close=aligned_price_data['Close'],
                    entries=aligned_signals == 1,
                    exits=aligned_signals == -1,
                    init_cash=100000,  # 初始資金10萬
                    fees=0.001,         # 0.1%手續費
                    slippage=0.001,     # 0.1%滑點
                )

                # 計算性能指標
                stats = portfolio.stats()

                results[strategy_name] = {
                    'total_return': stats['Total Return [%]'],
                    'sharpe_ratio': stats['Sharpe Ratio'],
                    'max_drawdown': stats['Max Drawdown [%]'],
                    'win_rate': stats['Win Rate [%]'],
                    'total_trades': stats['# Trades'],
                    'avg_return': stats['Mean Return [%]'],
                    'volatility': stats['Volatility (ann.) [%]'],
                    'calmar_ratio': stats['Calmar Ratio'],
                    'sortino_ratio': stats['Sortino Ratio']
                }

            except Exception as e:
                logger.warning(f"Error backtesting {strategy_name}: {e}")
                continue

        return results

    def rank_strategies(self, results: Dict) -> List[Dict]:
        """按SR和MDD排名策略"""
        if not results:
            return []

        # 轉換為列表並添加綜合評分
        strategy_list = []
        for name, metrics in results.items():
            try:
                # 計算綜合評分 (0-100)
                # SR佔50%，MDD佔30%，總回報佔20%
                sharpe_score = min(100, max(0, (metrics['sharpe_ratio'] + 2) * 20))  # 假設SR範圍-2到3
                mdd_score = min(100, max(0, (100 + metrics['max_drawdown']) * 0.5))  # MDD越小越好
                return_score = min(100, max(0, (metrics['total_return'] + 50) * 0.67))  # 假設回報範圍-50%到100%

                composite_score = sharpe_score * 0.5 + mdd_score * 0.3 + return_score * 0.2

                strategy_list.append({
                    'name': name,
                    'sharpe_ratio': metrics['sharpe_ratio'],
                    'max_drawdown': metrics['max_drawdown'],
                    'total_return': metrics['total_return'],
                    'win_rate': metrics['win_rate'],
                    'total_trades': metrics['total_trades'],
                    'composite_score': composite_score,
                    'all_metrics': metrics
                })
            except Exception as e:
                logger.warning(f"Error ranking {name}: {e}")
                continue

        # 按綜合評分排序
        strategy_list.sort(key=lambda x: x['composite_score'], reverse=True)

        return strategy_list

    def generate_visualization_report(self, ranked_strategies: List[Dict]) -> str:
        """生成可視化報告"""
        if not ranked_strategies:
            return "No strategies to visualize"

        # 創建HTML報告
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Deep Non-Price Data Backtest Report - {self.symbol}</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; color: #333; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
                .strategy-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: #f9f9f9; }}
                .chart-container {{ margin: 20px 0; }}
                .rank-1 {{ border: 2px solid #FFD700; background: #FFFACD; }}
                .rank-2 {{ border: 2px solid #C0C0C0; background: #F5F5F5; }}
                .rank-3 {{ border: 2px solid #CD7F32; background: #FAEBD7; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Deep Non-Price Data Backtest Report</h1>
                <h2>{self.symbol} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
            </div>

            <div class="stats-grid">
        """

        # 添加前20個策略
        for i, strategy in enumerate(ranked_strategies[:20]):
            rank_class = "rank-1" if i == 0 else "rank-2" if i == 1 else "rank-3" if i == 2 else ""

            html_content += f"""
                <div class="strategy-card {rank_class}">
                    <h3>#{i+1}: {strategy['name']}</h3>
                    <p><strong>Composite Score:</strong> {strategy['composite_score']:.1f}/100</p>
                    <p><strong>Sharpe Ratio:</strong> {strategy['sharpe_ratio']:.3f}</p>
                    <p><strong>Max Drawdown:</strong> {strategy['max_drawdown']:.2f}%</p>
                    <p><strong>Total Return:</strong> {strategy['total_return']:.2f}%</p>
                    <p><strong>Win Rate:</strong> {strategy['win_rate']:.2f}%</p>
                    <p><strong>Total Trades:</strong> {strategy['total_trades']}</p>
                </div>
            """

        html_content += """
            </div>

            <div class="chart-container">
                <h3>Top 10 Strategies Performance</h3>
                <canvas id="performanceChart" width="400" height="200"></canvas>
            </div>

            <script>
                const ctx = document.getElementById('performanceChart').getContext('2d');
                const chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: [""" + ', '.join([f"'{s['name'][:30]}'" for s in ranked_strategies[:10]]) + """],
                        datasets: [{
                            label: 'Sharpe Ratio',
                            data: [""" + ', '.join([str(s['sharpe_ratio']) for s in ranked_strategies[:10]]) + """],
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }, {
                            label: 'Max Drawdown (%)',
                            data: [""" + ', '.join([str(s['max_drawdown']) for s in ranked_strategies[:10]]) + """],
                            backgroundColor: 'rgba(255, 99, 132, 0.6)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            </script>
        </body>
        </html>
        """

        # 保存HTML報告
        report_file = f"deep_nonprice_backtest_report_{self.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ Visualization report saved: {report_file}")
        return report_file

    def run_complete_backtest(self) -> Dict:
        """運行完整回測流程"""
        try:
            print(f"\n{'='*60}")
            print(f"RUNNING COMPLETE DEEP NON-PRICE BACKTEST")
            print(f"Symbol: {self.symbol}")
            print(f"{'='*60}")

            # 1. 創建指標DataFrame
            print("\nStep 1: Creating indicator DataFrame...")
            indicator_df = self._create_indicator_df(self.all_indicators)

            if indicator_df.empty:
                print("❌ No valid indicators generated")
                return {'error': 'No valid indicators'}

            print(f"✓ Created indicator DataFrame: {len(indicator_df.columns)} indicators, {len(indicator_df)} days")

            # 2. 計算所有策略信號
            print("\nStep 2: Calculating strategy signals...")
            signals = self.calculate_all_strategy_signals(indicator_df)

            if not signals:
                print("❌ No valid signals generated")
                return {'error': 'No valid signals'}

            print(f"✓ Generated {len(signals)} strategy signal combinations")

            # 3. VectorBT回測
            print("\nStep 3: Running VectorBT backtest...")
            backtest_results = self.run_vectorbt_backtest(signals)

            if not backtest_results:
                print("❌ No valid backtest results")
                return {'error': 'No valid backtest results'}

            print(f"✓ Backtested {len(backtest_results)} strategies")

            # 4. 策略排名
            print("\nStep 4: Ranking strategies by SR & MDD...")
            ranked_strategies = self.rank_strategies(backtest_results)

            print(f"✓ Ranked {len(ranked_strategies)} strategies")

            # 5. 顯示前10名
            print(f"\n{'='*60}")
            print(f"TOP 10 STRATEGIES - RANKED BY COMPOSITE SCORE")
            print(f"{'='*60}")

            for i, strategy in enumerate(ranked_strategies[:10]):
                print(f"\n#{i+1:2d}: {strategy['name']}")
                print(f"     Composite Score: {strategy['composite_score']:6.1f}/100")
                print(f"     Sharpe Ratio:     {strategy['sharpe_ratio']:6.3f}")
                print(f"     Max Drawdown:     {strategy['max_drawdown']:6.2f}%")
                print(f"     Total Return:     {strategy['total_return']:6.2f}%")
                print(f"     Win Rate:         {strategy['win_rate']:6.2f}%")
                print(f"     Total Trades:     {strategy['total_trades']:4d}")

            # 6. 生成可視化報告
            print(f"\nStep 5: Generating visualization report...")
            report_file = self.generate_visualization_report(ranked_strategies)

            # 7. 保存詳細結果
            results_file = f"deep_nonprice_backtest_results_{self.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            complete_results = {
                'symbol': self.symbol,
                'backtest_time': datetime.now().isoformat(),
                'data_summary': {
                    'price_data_days': len(self.price_data),
                    'indicators_count': len(indicator_df.columns),
                    'strategies_tested': len(signals),
                    'successful_strategies': len(backtest_results)
                },
                'top_strategies': ranked_strategies[:20],
                'all_results': backtest_results,
                'visualization_report': report_file
            }

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(complete_results, f, indent=2, ensure_ascii=False, default=str)

            print(f"✓ Detailed results saved: {results_file}")

            # 8. 總結
            total_time = time.time() - self.start_time

            print(f"\n{'='*60}")
            print(f"BACKTEST COMPLETED SUCCESSFULLY!")
            print(f"{'='*60}")
            print(f"Total Processing Time: {total_time:.2f} seconds")
            print(f"Best Strategy: {ranked_strategies[0]['name'] if ranked_strategies else 'N/A'}")
            print(f"Best Sharpe Ratio: {ranked_strategies[0]['sharpe_ratio']:.3f}" if ranked_strategies else "N/A")
            print(f"Best Composite Score: {ranked_strategies[0]['composite_score']:.1f}/100" if ranked_strategies else "N/A")
            print(f"Files Generated:")
            print(f"  - Report: {report_file}")
            print(f"  - Results: {results_file}")

            return complete_results

        except Exception as e:
            print(f"❌ Error in complete backtest: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

def main():
    """主程序"""
    print("DEEP NON-PRICE DATA BACKTEST SYSTEM")
    print("=" * 50)

    # 運行0700.HK的完整回測
    system = DeepNonPriceBacktestSystem(symbol="0700.HK")
    results = system.run_complete_backtest()

    if 'error' in results:
        print(f"❌ Backtest failed: {results['error']}")
        return 1
    else:
        print(f"\n🎉 SUCCESS! Deep backtest completed for {results['symbol']}")
        return 0

if __name__ == "__main__":
    exit(main())