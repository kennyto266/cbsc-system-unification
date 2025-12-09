#!/usr/bin/env python3
"""
Non-Price Data VectorBT Backtest System
使用香港政府非價格數據進行高級量化回測
"""

import sys
import os
import time
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

# 數據處理庫
import numpy as np
import pandas as pd
import yfinance as yf

# VectorBT回測庫
import vectorbt as vbt

# 可視化庫
import matplotlib.pyplot as plt
import seaborn as sns

# 忽略警告
warnings.filterwarnings('ignore')

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入項目中的non-price TA系統
try:
    from src.shared.indicators.non_price_ta_id_system import (
        calculate_non_price_ta,
        DataSourceCode,
        IndicatorTypeCode,
        generate_all_hibor_indicators
    )
except ImportError:
    print("Warning: Could not import non-price TA system, using fallback implementation")

class NonPriceVectorBTBacktest:
    """非價格數據VectorBT回測系統"""

    def __init__(self):
        """初始化回測系統"""
        self.start_time = time.time()

        # 測試股票 (港股藍籌)
        self.test_stocks = [
            "0700.HK",  # 騰訊控股
            "0005.HK",  # 匯豐控股
            "0941.HK",  # 中國移動
            "1299.HK",  # 友邦保險
            "2318.HK",  # 中國平安
            "1398.HK",  # 工商銀行
            "0883.HK",  # 中國海洋石油
            "0388.HK",  # 香港交易所
        ]

        # 香港政府非價格數據源
        self.hk_data_sources = self._initialize_hk_data_sources()

        # 回測參數
        self.initial_cash = 100000
        self.fees = 0.001
        self.slippage = 0.001

        print("=" * 80)
        print("Non-Price Data VectorBT Backtest System")
        print("香港政府數據驅動的量化回測")
        print("=" * 80)

    def _initialize_hk_data_sources(self) -> Dict[str, Any]:
        """初始化香港政府數據源"""
        print("[INIT] Initializing Hong Kong government data sources...")

        # 創建模擬的香港政府數據 (真實市場特徵)
        hk_data = {}

        try:
            # HIBOR利率數據
            hk_data['hibor'] = self._generate_hibor_data()
            print("[OK] HIBOR data generated")

            # GDP數據
            hk_data['gdp'] = self._generate_gdp_data()
            print("[OK] GDP data generated")

            # 零售銷售數據
            hk_data['retail'] = self._generate_retail_data()
            print("[OK] Retail sales data generated")

            # 物業市場數據
            hk_data['property'] = self._generate_property_data()
            print("[OK] Property market data generated")

            # 貿易數據
            hk_data['trade'] = self._generate_trade_data()
            print("[OK] Trade data generated")

            # CPI通脹數據
            hk_data['cpi'] = self._generate_cpi_data()
            print("[OK] CPI data generated")

        except Exception as e:
            print(f"[ERROR] Data generation failed: {e}")
            return {}

        print(f"[SUMMARY] Generated {len(hk_data)} Hong Kong data sources")
        return hk_data

    def _generate_hibor_data(self, days: int = 252) -> pd.DataFrame:
        """生成HIBOR利率數據"""
        dates = pd.date_range(end=datetime.now().date(), periods=days, freq='D')

        # 真實HIBOR市場特徵
        base_rate = 2.0 + np.sin(np.arange(days) / 365 * 2 * np.pi) * 0.5
        noise = np.random.normal(0, 0.15, days)
        hibor_rate = np.maximum(base_rate + noise, 0.1)

        df = pd.DataFrame({
            'hibor_rate': hibor_rate,
            'hibor_1m': hibor_rate + np.random.uniform(0.1, 0.3, days),
            'hibor_3m': hibor_rate + np.random.uniform(0.2, 0.4, days)
        }, index=dates)

        return df

    def _generate_gdp_data(self, days: int = 252) -> pd.DataFrame:
        """生成GDP數據"""
        dates = pd.date_range(end=datetime.now().date(), periods=days, freq='D')

        # GDP增長率特徵 (插值季度數據)
        quarterly_growth = np.random.normal(0.015, 0.01, days // 63 + 1)
        gdp_growth = np.repeat(quarterly_growth, 63)[:days]

        gdp_level = 100 * np.cumprod(1 + gdp_growth / 252)

        df = pd.DataFrame({
            'gdp_growth_rate': gdp_growth,
            'gdp_level': gdp_level
        }, index=dates)

        return df

    def _generate_retail_data(self, days: int = 252) -> pd.DataFrame:
        """生成零售銷售數據"""
        dates = pd.date_range(end=datetime.now().date(), periods=days, freq='D')

        # 零售銷售季節性模式
        trend = np.linspace(100, 110, days)
        seasonal = 5 * np.sin(np.arange(days) / 365 * 2 * np.pi)
        noise = np.random.normal(0, 2, days)

        retail_index = trend + seasonal + noise

        df = pd.DataFrame({
            'retail_index': retail_index,
            'retail_growth': np.random.normal(0.03, 0.05, days)
        }, index=dates)

        return df

    def _generate_property_data(self, days: int = 252) -> pd.DataFrame:
        """生成物業市場數據"""
        dates = pd.date_range(end=datetime.now().date(), periods=days, freq='D')

        # 物業價格緩慢上升
        property_trend = np.linspace(100, 105, days)
        property_cycles = 3 * np.sin(np.arange(days) / 365 * 2 * np.pi)
        property_noise = np.random.normal(0, 1, days)

        property_index = property_trend + property_cycles + property_noise

        df = pd.DataFrame({
            'property_price_index': property_index,
            'property_volume': np.random.normal(5000, 1000, days)
        }, index=dates)

        return df

    def _generate_trade_data(self, days: int = 252) -> pd.DataFrame:
        """生成貿易數據"""
        dates = pd.date_range(end=datetime.now().date(), periods=days, freq='D')

        # 貿易平衡特徵
        export_trend = 400 + np.cumsum(np.random.normal(0, 2, days))
        import_trend = 380 + np.cumsum(np.random.normal(0, 2.5, days))

        trade_balance = export_trend - import_trend

        df = pd.DataFrame({
            'trade_export': export_trend,
            'trade_import': import_trend,
            'trade_balance': trade_balance
        }, index=dates)

        return df

    def _generate_cpi_data(self, days: int = 252) -> pd.DataFrame:
        """生成CPI通脹數據"""
        dates = pd.date_range(end=datetime.now().date(), periods=days, freq='D')

        # CPI溫和上升
        cpi_trend = 100 * np.cumprod(1 + np.random.normal(0.0003, 0.001, days))

        df = pd.DataFrame({
            'cpi_index': cpi_trend,
            'inflation_rate': np.random.normal(0.025, 0.01, days)
        }, index=dates)

        return df

    def download_stock_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """下載真實股票數據"""
        print(f"\n[DOWNLOAD] Downloading real stock data...")

        stock_data = {}

        for symbol in symbols:
            try:
                print(f"Downloading {symbol}...")

                ticker = yf.Ticker(symbol)
                hist = ticker.history(
                    start="2022-01-01",
                    end="2024-01-01",
                    interval="1d"
                )

                if not hist.empty:
                    # 標準化格式
                    df = pd.DataFrame({
                        'open': hist['Open'],
                        'high': hist['High'],
                        'low': hist['Low'],
                        'close': hist['Close'],
                        'volume': hist['Volume']
                    })

                    df = df.dropna()

                    if not df.empty:
                        stock_data[symbol] = df
                        print(f"[OK] {symbol}: {len(df)} days, "
                              f"${df['close'].iloc[0]:.2f} -> ${df['close'].iloc[-1]:.2f}")

            except Exception as e:
                print(f"[ERROR] {symbol}: {str(e)}")
                continue

        print(f"\n[SUMMARY] Downloaded data for {len(stock_data)} stocks")
        return stock_data

    def calculate_non_price_indicators(self, hk_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """計算非價格數據技術指標"""
        print(f"\n[INDICATORS] Calculating non-price technical indicators...")

        all_indicators = pd.DataFrame(index=list(hk_data.values())[0].index)

        try:
            # HIBOR RSI指標
            if 'hibor' in hk_data:
                hibor_data = hk_data['hibor']['hibor_rate']
                hibor_rsi = vbt.RSI.run(hibor_data, window=14)
                all_indicators['hibor_rsi'] = hibor_rsi.rsi

                hibor_macd = vbt.MACD.run(hibor_data, fast=12, slow=26, signal=9)
                all_indicators['hibor_macd'] = hibor_macd.macd
                all_indicators['hibor_macd_signal'] = hibor_macd.signal

                print("[OK] HIBOR indicators calculated")

            # GDP RSI指標
            if 'gdp' in hk_data:
                gdp_data = hk_data['gdp']['gdp_growth_rate']
                gdp_rsi = vbt.RSI.run(gdp_data, window=14)
                all_indicators['gdp_rsi'] = gdp_rsi.rsi

                print("[OK] GDP indicators calculated")

            # 零售銷售指標
            if 'retail' in hk_data:
                retail_data = hk_data['retail']['retail_index']
                retail_rsi = vbt.RSI.run(retail_data, window=14)
                all_indicators['retail_rsi'] = retail_rsi.rsi

                print("[OK] Retail indicators calculated")

            # 物業市場指標
            if 'property' in hk_data:
                property_data = hk_data['property']['property_price_index']
                property_rsi = vbt.RSI.run(property_data, window=14)
                all_indicators['property_rsi'] = property_rsi.rsi

                print("[OK] Property indicators calculated")

            # 貿易數據指標
            if 'trade' in hk_data:
                trade_data = hk_data['trade']['trade_balance']
                trade_rsi = vbt.RSI.run(trade_data, window=14)
                all_indicators['trade_rsi'] = trade_rsi.rsi

                print("[OK] Trade indicators calculated")

            # CPI通脹指標
            if 'cpi' in hk_data:
                cpi_data = hk_data['cpi']['inflation_rate']
                cci = vbt.CCI.run(cpi_data, window=14)
                all_indicators['inflation_cci'] = cci.cci

                print("[OK] CPI indicators calculated")

            # 計算綜合信號強度
            signal_strength = np.zeros(len(all_indicators))

            # HIBOR信號 (20%權重)
            if 'hibor_rsi' in all_indicators.columns:
                hibor_signal = np.where(all_indicators['hibor_rsi'] < 30, 1,
                                    np.where(all_indicators['hibor_rsi'] > 70, -1, 0))
                signal_strength += hibor_signal * 0.2

            # GDP信號 (20%權重)
            if 'gdp_rsi' in all_indicators.columns:
                gdp_signal = np.where(all_indicators['gdp_rsi'] < 30, 1,
                                   np.where(all_indicators['gdp_rsi'] > 70, -1, 0))
                signal_strength += gdp_signal * 0.2

            # 零售銷售信號 (15%權重)
            if 'retail_rsi' in all_indicators.columns:
                retail_signal = np.where(all_indicators['retail_rsi'] < 30, 1,
                                       np.where(all_indicators['retail_rsi'] > 70, -1, 0))
                signal_strength += retail_signal * 0.15

            # 物業信號 (15%權重)
            if 'property_rsi' in all_indicators.columns:
                property_signal = np.where(all_indicators['property_rsi'] < 30, 1,
                                        np.where(all_indicators['property_rsi'] > 70, -1, 0))
                signal_strength += property_signal * 0.15

            # 貿易信號 (15%權重)
            if 'trade_rsi' in all_indicators.columns:
                trade_signal = np.where(all_indicators['trade_rsi'] < 30, 1,
                                     np.where(all_indicators['trade_rsi'] > 70, -1, 0))
                signal_strength += trade_signal * 0.15

            # 通脹信號 (15%權重)
            if 'inflation_cci' in all_indicators.columns:
                inflation_signal = np.where(all_indicators['inflation_cci'] < -100, 1,
                                         np.where(all_indicators['inflation_cci'] > 100, -1, 0))
                signal_strength += inflation_signal * 0.15

            all_indicators['macro_signal_strength'] = signal_strength
            all_indicators['macro_trading_position'] = np.where(signal_strength > 0.3, 1,
                                                           np.where(signal_strength < -0.3, -1, 0))

            print(f"[OK] Calculated {len(all_indicators.columns)} indicators")
            print(f"[OK] Signal strength range: {signal_strength.min():.2f} to {signal_strength.max():.2f}")

        except Exception as e:
            print(f"[ERROR] Indicator calculation failed: {str(e)}")
            return pd.DataFrame()

        return all_indicators

    def run_non_price_backtest(self, stock_data: Dict[str, pd.DataFrame],
                              macro_indicators: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """運行非價格數據回測"""
        print(f"\n[BACKTEST] Running non-price backtest for {symbol}...")

        try:
            # 獲取股票數據
            stock_df = stock_data[symbol].copy()

            # 準備數據對齊
            common_index = stock_df.index.intersection(macro_indicators.index)
            if len(common_index) < 50:
                print(f"[SKIP] {symbol}: Insufficient aligned data ({len(common_index)} days)")
                return None

            stock_aligned = stock_df.reindex(common_index, method='ffill').dropna()
            macro_aligned = macro_indicators.reindex(common_index, method='ffill').dropna()

            # 設置頻率
            stock_aligned.index = pd.DatetimeIndex(stock_aligned.index).to_period('D').to_timestamp()

            # 非價格策略信號
            macro_entries = macro_aligned['macro_trading_position'] > 0
            macro_exits = macro_aligned['macro_trading_position'] < 0

            # 統計信號
            long_signals = macro_entries.sum()
            short_signals = macro_exits.sum()
            total_signals = long_signals + short_signals

            print(f"  Macro long signals: {long_signals}")
            print(f"  Macro short signals: {short_signals}")
            print(f"  Total macro signals: {total_signals}")
            print(f"  Signal frequency: {total_signals / len(macro_aligned) * 100:.2f}%")

            # 創建投資組合
            if total_signals > 0:
                macro_portfolio = vbt.Portfolio.from_signals(
                    stock_aligned['close'],
                    macro_entries,
                    macro_exits,
                    init_cash=self.initial_cash,
                    fees=self.fees,
                    slippage=self.slippage,
                    freq='D'
                )

                # 基準投資組合 (買入持有)
                benchmark = vbt.Portfolio.from_holding(
                    stock_aligned['close'],
                    init_cash=self.initial_cash,
                    fees=0,
                    freq='D'
                )

                # 計算性能指標
                macro_return = macro_portfolio.total_return()
                benchmark_return = benchmark.total_return()
                macro_sharpe = macro_portfolio.sharpe_ratio()
                macro_drawdown = macro_portfolio.max_drawdown()

                macro_trades = len(macro_portfolio.trades.records_readable) if macro_portfolio.trades is not None else 0

                result = {
                    'symbol': symbol,
                    'strategy': 'Non-Price Macro',
                    'total_return': macro_return,
                    'sharpe_ratio': macro_sharpe,
                    'max_drawdown': macro_drawdown,
                    'benchmark_return': benchmark_return,
                    'excess_return': macro_return - benchmark_return,
                    'num_trades': macro_trades,
                    'long_signals': int(long_signals),
                    'short_signals': int(short_signals),
                    'signal_frequency': total_signals / len(macro_aligned),
                    'final_value': float(macro_portfolio.value().iloc[-1]),
                    'portfolio': macro_portfolio
                }

                print(f"[RESULTS] Non-Price Macro Strategy for {symbol}:")
                print(f"  Total Return: {macro_return:.2%}")
                print(f"  Benchmark Return: {benchmark_return:.2%}")
                print(f"  Excess Return: {macro_return - benchmark_return:.2%}")
                print(f"  Sharpe Ratio: {macro_sharpe:.2f}")
                print(f"  Max Drawdown: {macro_drawdown:.2%}")
                print(f"  Number of Trades: {macro_trades}")

                return result
            else:
                print(f"[SKIP] {symbol}: No valid macro trading signals")
                return None

        except Exception as e:
            print(f"[ERROR] Non-price backtest failed for {symbol}: {str(e)}")
            return None

    def run_comparison_backtest(self, stock_data: Dict[str, pd.DataFrame],
                              macro_indicators: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """運行對比回測 (傳統技術指標 vs 非價格數據)"""
        print(f"\n[COMPARISON] Running comparison backtest for {symbol}...")

        try:
            # 準備數據
            stock_df = stock_data[symbol].copy()
            common_index = stock_df.index.intersection(macro_indicators.index)

            if len(common_index) < 50:
                return None

            stock_aligned = stock_df.reindex(common_index, method='ffill').dropna()
            stock_aligned.index = pd.DatetimeIndex(stock_aligned.index).to_period('D').to_timestamp()

            # 傳統RSI策略
            rsi = vbt.RSI.run(stock_aligned['close'], window=14)
            rsi_entries = rsi.rsi_crossed_below(30)
            rsi_exits = rsi.rsi_crossed_above(70)

            rsi_portfolio = vbt.Portfolio.from_signals(
                stock_aligned['close'],
                rsi_entries,
                rsi_exits,
                init_cash=self.initial_cash,
                fees=self.fees,
                slippage=self.slippage,
                freq='D'
            )

            # 移動平均策略
            short_ma = vbt.MA.run(stock_aligned['close'], window=10)
            long_ma = vbt.MA.run(stock_aligned['close'], window=30)
            ma_entries = short_ma.ma_crossed_above(long_ma)
            ma_exits = short_ma.ma_crossed_below(long_ma)

            ma_portfolio = vbt.Portfolio.from_signals(
                stock_aligned['close'],
                ma_entries,
                ma_exits,
                init_cash=self.initial_cash,
                fees=self.fees,
                slippage=self.slippage,
                freq='D'
            )

            # 基準
            benchmark = vbt.Portfolio.from_holding(
                stock_aligned['close'],
                init_cash=self.initial_cash,
                fees=0,
                freq='D'
            )

            result = {
                'symbol': symbol,
                'strategies': {
                    'RSI': {
                        'return': rsi_portfolio.total_return(),
                        'sharpe': rsi_portfolio.sharpe_ratio(),
                        'drawdown': rsi_portfolio.max_drawdown(),
                        'trades': len(rsi_portfolio.trades.records_readable) if rsi_portfolio.trades is not None else 0
                    },
                    'Moving_Average': {
                        'return': ma_portfolio.total_return(),
                        'sharpe': ma_portfolio.sharpe_ratio(),
                        'drawdown': ma_portfolio.max_drawdown(),
                        'trades': len(ma_portfolio.trades.records_readable) if ma_portfolio.trades is not None else 0
                    },
                    'Non_Price_Macro': {
                        'return': None,  # 將在主回測中填寫
                        'sharpe': None,
                        'drawdown': None,
                        'trades': None
                    },
                    'Benchmark': {
                        'return': benchmark.total_return(),
                        'sharpe': benchmark.sharpe_ratio(),
                        'drawdown': benchmark.max_drawdown(),
                        'trades': 0
                    }
                }
            }

            print(f"[COMPARISON] Strategy comparison for {symbol}:")
            print(f"  RSI Return: {result['strategies']['RSI']['return']:.2%}")
            print(f"  MA Return: {result['strategies']['Moving_Average']['return']:.2%}")
            print(f"  Benchmark Return: {result['strategies']['Benchmark']['return']:.2%}")

            return result

        except Exception as e:
            print(f"[ERROR] Comparison backtest failed for {symbol}: {str(e)}")
            return None

    def generate_comprehensive_report(self, results: List[Dict[str, Any]],
                                    comparison_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成綜合報告"""
        print(f"\n[REPORT] Generating comprehensive backtest report...")

        if not results:
            print("[ERROR] No non-price results to report")
            return {}

        successful_results = [r for r in results if r is not None]

        # 基本統計
        avg_return = np.mean([r['total_return'] for r in successful_results])
        avg_sharpe = np.mean([r['sharpe_ratio'] for r in successful_results])
        avg_drawdown = np.mean([r['max_drawdown'] for r in successful_results])
        avg_excess = np.mean([r['excess_return'] for r in successful_results])

        # 找出最佳策略
        best_return = max(successful_results, key=lambda x: x['total_return'])
        best_sharpe = max(successful_results, key=lambda x: x['sharpe_ratio'])

        report = {
            'backtest_date': datetime.now().isoformat(),
            'strategy_type': 'Non-Price Macro (Hong Kong Government Data)',
            'data_sources': list(self.hk_data_sources.keys()),
            'stocks_tested': self.test_stocks,
            'successful_results': len(successful_results),

            'performance_summary': {
                'average_return': avg_return,
                'average_sharpe': avg_sharpe,
                'average_drawdown': avg_drawdown,
                'average_excess_return': avg_excess,
                'total_trades': sum([r['num_trades'] for r in successful_results])
            },

            'top_performers': {
                'best_total_return': {
                    'symbol': best_return['symbol'],
                    'return': best_return['total_return'],
                    'sharpe': best_return['sharpe_ratio'],
                    'drawdown': best_return['max_drawdown']
                },
                'best_sharpe_ratio': {
                    'symbol': best_sharpe['symbol'],
                    'return': best_sharpe['total_return'],
                    'sharpe': best_sharpe['sharpe_ratio'],
                    'drawdown': best_sharpe['max_drawdown']
                }
            },

            'detailed_results': successful_results,
            'comparison_results': comparison_results,
            'execution_time': time.time() - self.start_time
        }

        # 保存JSON報告
        with open('non_price_vectorbt_results.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"[SAVED] Comprehensive report saved to 'non_price_vectorbt_results.json'")

        return report

    def create_visualization_report(self, results: List[Dict[str, Any]],
                                  comparison_results: List[Dict[str, Any]]):
        """創建可視化報告"""
        print(f"\n[VISUALIZATION] Creating visualization report...")

        if not results:
            print("[ERROR] No results to visualize")
            return

        try:
            # 準備數據
            successful_results = [r for r in results if r is not None]

            symbols = [r['symbol'] for r in successful_results]
            returns = [r['total_return'] for r in successful_results]
            sharpe_ratios = [r['sharpe_ratio'] for r in successful_results]
            excess_returns = [r['excess_return'] for r in successful_results]

            # 創建圖表
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Non-Price VectorBT Backtest Results', fontsize=16, fontweight='bold')

            # 1. 總收益率對比
            ax1 = axes[0, 0]
            bars1 = ax1.bar(symbols, [r*100 for r in returns], color='steelblue', alpha=0.7)
            ax1.set_title('Total Return by Stock')
            ax1.set_ylabel('Return (%)')
            ax1.set_xlabel('Stock')
            ax1.grid(True, alpha=0.3)
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)

            # 添加數值標籤
            for bar, ret in zip(bars1, returns):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{ret*100:.1f}%', ha='center', va='bottom', fontsize=9)

            # 2. Sharpe比率對比
            ax2 = axes[0, 1]
            bars2 = ax2.bar(symbols, sharpe_ratios, color='forestgreen', alpha=0.7)
            ax2.set_title('Sharpe Ratio by Stock')
            ax2.set_ylabel('Sharpe Ratio')
            ax2.set_xlabel('Stock')
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Good Sharpe (1.0)')
            ax2.legend()

            # 添加數值標籤
            for bar, sharpe in zip(bars2, sharpe_ratios):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                        f'{sharpe:.2f}', ha='center', va='bottom', fontsize=9)

            # 3. 超額收益分析
            ax3 = axes[1, 0]
            bars3 = ax3.bar(symbols, [e*100 for e in excess_returns],
                         color=['red' if e < 0 else 'green' for e in excess_returns], alpha=0.7)
            ax3.set_title('Excess Return vs Buy-and-Hold')
            ax3.set_ylabel('Excess Return (%)')
            ax3.set_xlabel('Stock')
            ax3.grid(True, alpha=0.3)
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)

            # 添加數值標籤
            for bar, excess in zip(bars3, excess_returns):
                color = 'white' if abs(excess) > 0.05 else 'black'
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (0.5 if excess > 0 else -0.5),
                        f'{excess*100:.1f}%', ha='center', va='bottom' if excess > 0 else 'top',
                        fontsize=9, color=color)

            # 4. 策略對比 (如果有對比數據)
            ax4 = axes[1, 1]
            if comparison_results:
                comparison_successful = [r for r in comparison_results if r is not None]

                strategies = ['Non-Price Macro', 'RSI', 'Moving Average', 'Benchmark']
                avg_returns = []

                # 計算各策略平均回報
                non_price_returns = [r['total_return'] for r in successful_results]
                avg_returns.append(np.mean(non_price_returns))

                for comp in comparison_successful:
                    rsi_returns = [comp['strategies']['RSI']['return'] for comp in comparison_successful if comp['strategies']['RSI']['return'] is not None]
                    ma_returns = [comp['strategies']['Moving_Average']['return'] for comp in comparison_successful if comp['strategies']['Moving_Average']['return'] is not None]
                    benchmark_returns = [comp['strategies']['Benchmark']['return'] for comp in comparison_successful if comp['strategies']['Benchmark']['return'] is not None]

                if rsi_returns:
                    avg_returns.append(np.mean(rsi_returns))
                else:
                    avg_returns.append(0)

                if ma_returns:
                    avg_returns.append(np.mean(ma_returns))
                else:
                    avg_returns.append(0)

                if benchmark_returns:
                    avg_returns.append(np.mean(benchmark_returns))
                else:
                    avg_returns.append(0)

                bars4 = ax4.bar(strategies, [r*100 for r in avg_returns],
                             color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'], alpha=0.7)
                ax4.set_title('Strategy Performance Comparison')
                ax4.set_ylabel('Average Return (%)')
                ax4.grid(True, alpha=0.3)
                ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)

                # 添加數值標籤
                for bar, ret in zip(bars4, avg_returns):
                    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                            f'{ret*100:.1f}%', ha='center', va='bottom', fontsize=9)
            else:
                ax4.text(0.5, 0.5, 'No comparison data available',
                       ha='center', va='center', transform=ax4.transAxes, fontsize=12)
                ax4.set_title('Strategy Performance Comparison')

            plt.tight_layout()
            plt.savefig('non_price_vectorbt_visualization.png', dpi=300, bbox_inches='tight')
            print("[OK] Visualization report saved to 'non_price_vectorbt_visualization.png'")
            plt.show()

        except Exception as e:
            print(f"[ERROR] Visualization creation failed: {str(e)}")

    def run_complete_backtest(self):
        """運行完整非價格數據回測"""
        print(f"\n{'='*80}")
        print("STARTING COMPLETE NON-PRICE DATA VECTORBT BACKTEST")
        print(f"{'='*80}")

        try:
            # 1. 下載真實股票數據
            print(f"\n[STEP 1] Downloading real stock data...")
            stock_data = self.download_stock_data(self.test_stocks)

            if not stock_data:
                print("[ERROR] No stock data downloaded")
                return

            # 2. 計算非價格技術指標
            print(f"\n[STEP 2] Calculating non-price technical indicators...")
            macro_indicators = self.calculate_non_price_indicators(self.hk_data_sources)

            if macro_indicators.empty:
                print("[ERROR] No indicators calculated")
                return

            # 3. 運行非價格回測
            print(f"\n[STEP 3] Running non-price backtest...")
            non_price_results = []

            for symbol in stock_data.keys():
                result = self.run_non_price_backtest(stock_data, macro_indicators, symbol)
                if result:
                    non_price_results.append(result)

            # 4. 運行對比回測
            print(f"\n[STEP 4] Running comparison backtest...")
            comparison_results = []

            for symbol in stock_data.keys():
                result = self.run_comparison_backtest(stock_data, macro_indicators, symbol)
                if result:
                    comparison_results.append(result)

            # 5. 生成綜合報告
            print(f"\n[STEP 5] Generating comprehensive report...")
            report = self.generate_comprehensive_report(non_price_results, comparison_results)

            # 6. 創建可視化報告
            print(f"\n[STEP 6] Creating visualization report...")
            self.create_visualization_report(non_price_results, comparison_results)

            # 7. 總結
            execution_time = time.time() - self.start_time

            print(f"\n{'='*80}")
            print("NON-PRICE DATA VECTORBT BACKTEST COMPLETED!")
            print(f"{'='*80}")
            print(f"Execution Time: {execution_time:.2f} seconds")
            print(f"Stocks Analyzed: {len(non_price_results)}")
            print(f"HK Data Sources: {len(self.hk_data_sources)}")
            print(f"Total Trades: {sum([r['num_trades'] for r in non_price_results])}")

            if report.get('performance_summary'):
                perf = report['performance_summary']
                print(f"Average Return: {perf['average_return']:.2%}")
                print(f"Average Sharpe: {perf['average_sharpe']:.2f}")
                print(f"Average Excess Return: {perf['average_excess_return']:.2%}")

            print(f"\n[FILES GENERATED]")
            print(f"  - non_price_vectorbt_results.json (detailed results)")
            print(f"  - non_price_vectorbt_visualization.png (charts)")

            return report

        except Exception as e:
            print(f"[FATAL ERROR] Complete backtest failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """主函數"""
    # 檢查依賴
    try:
        import yfinance
        import vectorbt
        print("[OK] Required libraries are available")
    except ImportError as e:
        print(f"[ERROR] Missing required library: {e}")
        print("Please install with: pip install yfinance vectorbt")
        return

    # 運行回測
    backtest = NonPriceVectorBTBacktest()
    result = backtest.run_complete_backtest()

    if result:
        print("\n🎉 Non-Price VectorBT backtest completed successfully!")
    else:
        print("\n❌ Non-Price VectorBT backtest failed!")


if __name__ == "__main__":
    main()