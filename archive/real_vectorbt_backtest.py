#!/usr/bin/env python3
"""
Real VectorBT Backtest
真实股票数据回测演示
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import vectorbt as vbt
import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("REAL VECTORBT BACKTEST")
print("CODEX-- Quantitative Trading System")
print("=" * 60)

class RealVectorBTBacktest:
    """真实VectorBT回测类"""
    
    def __init__(self):
        # 香港热门股票代码
        self.hk_stocks = [
            "0700.HK",  # 腾讯控股
            "0005.HK",  # 汇丰控股
            "1398.HK",  # 工商银行
            "0941.HK",  # 中国移动
            "2318.HK",  # 中国平安
            "1299.HK",  # 友邦保险
            "0388.HK",  # 香港交易所
            "0883.HK",  # 中国海洋石油
            "1810.HK",  # 小米集团
            "0002.HK"   # 中电控股
        ]
        
        # 回测参数
        self.start_date = "2022-01-01"
        self.end_date = "2024-01-01"
        self.initial_cash = 100000  # 10万港币
        self.fees = 0.001  # 0.1% 手续费
        
    def download_real_data(self, symbols=None):
        """下载真实股票数据"""
        if symbols is None:
            symbols = self.hk_stocks[:5]  # 只下载前5只股票
        
        print(f"\n[DOWNLOAD] Downloading real stock data...")
        print(f"Stocks: {symbols}")
        print(f"Period: {self.start_date} to {self.end_date}")
        
        price_data = {}
        
        for symbol in symbols:
            try:
                print(f"Downloading {symbol}...")
                
                # 使用yfinance下载数据
                ticker = yf.Ticker(symbol)
                hist = ticker.history(
                    start=self.start_date,
                    end=self.end_date,
                    interval="1d"
                )
                
                if not hist.empty:
                    # 转换为VectorBT格式
                    df = pd.DataFrame({
                        'open': hist['Open'],
                        'high': hist['High'],
                        'low': hist['Low'],
                        'close': hist['Close'],
                        'volume': hist['Volume']
                    })
                    
                    # 移除空值
                    df = df.dropna()
                    
                    if not df.empty:
                        price_data[symbol] = df
                        print(f"[OK] {symbol}: {len(df)} days, "
                              f"${df['close'].iloc[0]:.2f} -> ${df['close'].iloc[-1]:.2f}")
                    else:
                        print(f"[SKIP] {symbol}: No valid data after cleaning")
                else:
                    print(f"[SKIP] {symbol}: No data available")
                    
            except Exception as e:
                print(f"[ERROR] {symbol}: {str(e)}")
                continue
        
        print(f"\n[SUMMARY] Downloaded data for {len(price_data)} stocks")
        return price_data
    
    def calculate_technical_indicators(self, price_data, symbol):
        """计算技术指标"""
        print(f"\n[INDICATORS] Calculating technical indicators for {symbol}...")
        
        try:
            df = price_data[symbol]
            
            # RSI
            rsi = vbt.RSI.run(df['close'], window=14)
            
            # MACD
            macd = vbt.MACD.run(df['close'], fast=12, slow=26, signal=9)
            
            # Bollinger Bands
            bbands = vbt.BBANDS.run(df['close'], window=20, std=2)
            
            # ATR
            atr = vbt.ATR.run(df['high'], df['low'], df['close'], window=14)
            
            # ADX (需要high, low, close)
            adx = vbt.ADX.run(df['high'], df['low'], df['close'], window=14)
            
            print(f"[OK] Calculated {len(rsi.rsi)} RSI values")
            print(f"[OK] Calculated {len(macd.macd)} MACD values")
            print(f"[OK] Calculated {len(bbands.upper)} Bollinger Bands values")
            
            return {
                'rsi': rsi.rsi,
                'macd': macd.macd,
                'macd_signal': macd.signal,
                'bb_upper': bbands.upper,
                'bb_lower': bbands.lower,
                'bb_middle': bbands.middle,
                'atr': atr.atr,
                'adx': adx.adx
            }
            
        except Exception as e:
            print(f"[ERROR] Indicator calculation failed: {str(e)}")
            return {}
    
    def create_trading_signals(self, price_data, indicators, symbol):
        """创建交易信号"""
        print(f"\n[SIGNALS] Creating trading signals for {symbol}...")
        
        try:
            df = price_data[symbol]
            signals = pd.DataFrame(index=df.index)
            
            if not indicators:
                # 使用简单的移动平均线策略
                ma_10 = df['close'].rolling(10).mean()
                ma_30 = df['close'].rolling(30).mean()
                signals['ma_cross'] = np.where(ma_10 > ma_30, 1, -1)
                print(f"[OK] Using simple MA crossover strategy")
            else:
                # 多信号融合策略
                signal_values = []
                
                # RSI信号
                if 'rsi' in indicators:
                    rsi_signal = np.where(indicators['rsi'] < 30, 1, np.where(indicators['rsi'] > 70, -1, 0))
                    signal_values.append(rsi_signal * 0.3)
                    print(f"[OK] RSI signals integrated")
                
                # MACD信号
                if 'macd' in indicators and 'macd_signal' in indicators:
                    macd_signal = np.where(
                        (indicators['macd'] > indicators['macd_signal']) & 
                        (indicators['macd'] > 0), 1,
                        np.where(
                            (indicators['macd'] < indicators['macd_signal']) & 
                            (indicators['macd'] < 0), -1, 0
                        )
                    )
                    signal_values.append(macd_signal * 0.4)
                    print(f"[OK] MACD signals integrated")
                
                # 布林带信号
                if 'bb_upper' in indicators and 'bb_lower' in indicators:
                    bb_signal = np.where(
                        df['close'] < indicators['bb_lower'], 1,
                        np.where(df['close'] > indicators['bb_upper'], -1, 0)
                    )
                    signal_values.append(bb_signal * 0.2)
                    print(f"[OK] Bollinger Bands signals integrated")
                
                # ATR止损信号
                if 'atr' in indicators:
                    atr_stop = indicators['atr'] * 2
                    returns = df['close'].pct_change()
                    atr_signal = np.where(returns < -atr_stop, -1, np.where(returns > atr_stop, 1, 0))
                    signal_values.append(atr_signal * 0.1)
                    print(f"[OK] ATR stop signals integrated")
                
                # 融合信号
                if signal_values:
                    signals['combined'] = np.sum(signal_values, axis=0)
                    signals['final'] = np.where(signals['combined'] > 0.5, 1, 
                                              np.where(signals['combined'] < -0.5, -1, 0))
                else:
                    signals['final'] = 0
            
            # 统计信号
            long_signals = (signals['final'] > 0).sum()
            short_signals = (signals['final'] < 0).sum()
            
            print(f"[OK] Signal statistics:")
            print(f"  Long signals: {long_signals}")
            print(f"  Short signals: {short_signals}")
            print(f"  Total signals: {long_signals + short_signals}")
            print(f"  Signal frequency: {(long_signals + short_signals) / len(signals) * 100:.2f}%")
            
            return signals
            
        except Exception as e:
            print(f"[ERROR] Signal creation failed: {str(e)}")
            return pd.DataFrame()
    
    def run_vectorbt_backtest(self, price_data, symbol, signals):
        """运行VectorBT回测"""
        print(f"\n[BACKTEST] Running VectorBT backtest for {symbol}...")
        
        try:
            df = price_data[symbol]
            
            # 创建投资组合
            portfolio = vbt.Portfolio.from_signals(
                df['close'],
                signals['final'] > 0,  # 买入信号
                signals['final'] < 0,  # 卖出信号
                init_cash=self.initial_cash,
                fees=self.fees,
                slippage=0.001
            )
            
            # 计算性能指标
            total_return = portfolio.total_return()
            sharpe_ratio = portfolio.sharpe_ratio()
            max_drawdown = portfolio.max_drawdown()
            
            # 交易统计
            trades = portfolio.trades
            num_trades = len(trades) if trades is not None else 0
            
            # 基准对比（买入持有策略）
            benchmark = vbt.Portfolio.from_holding(
                df['close'],
                init_cash=self.initial_cash,
                fees=0
            )
            
            benchmark_return = benchmark.total_return()
            
            # 超额收益
            excess_return = total_return - benchmark_return
            
            print(f"[RESULTS] Backtest Results for {symbol}:")
            print(f"  Initial Cash: ${self.initial_cash:,.0f}")
            print(f"  Final Value: ${portfolio.value().iloc[-1]:,.0f}")
            print(f"  Total Return: {total_return:.2%}")
            print(f"  Benchmark Return: {benchmark_return:.2%}")
            print(f"  Excess Return: {excess_return:.2%}")
            print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
            print(f"  Max Drawdown: {max_drawdown:.2%}")
            print(f"  Number of Trades: {num_trades}")
            print(f"  Win Rate: {portfolio.win_rate():.2f}" if hasattr(portfolio, 'win_rate') else "  Win Rate: N/A")
            
            # 权益曲线数据
            equity_curve = portfolio.value()
            
            return {
                'symbol': symbol,
                'portfolio': portfolio,
                'equity_curve': equity_curve,
                'returns': portfolio.returns(),
                'trades': trades,
                'metrics': {
                    'total_return': total_return,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'benchmark_return': benchmark_return,
                    'excess_return': excess_return,
                    'num_trades': num_trades,
                    'win_rate': portfolio.win_rate() if hasattr(portfolio, 'win_rate') else 0
                }
            }
            
        except Exception as e:
            print(f"[ERROR] Backtest failed for {symbol}: {str(e)}")
            return None
    
    def generate_backtest_report(self, results):
        """生成回测报告"""
        print(f"\n[REPORT] Generating comprehensive backtest report...")
        
        if not results:
            print("[ERROR] No results to report")
            return
        
        # 成功的回测
        successful_results = [r for r in results if r is not None]
        
        if not successful_results:
            print("[ERROR] No successful backtests")
            return
        
        print(f"[SUMMARY] Backtest Summary:")
        print("=" * 60)
        print(f"{'Stock':<10} {'Return':<10} {'Sharpe':<8} {'MaxDD':<10} {'Trades':<8} {'WinRate':<8}")
        print("-" * 60)
        
        total_sharpe = 0
        total_return = 0
        best_stock = None
        best_sharpe = -999
        
        for result in successful_results:
            symbol = result['symbol']
            metrics = result['metrics']
            
            print(f"{symbol:<10} {metrics['total_return']:<10.2%} {metrics['sharpe_ratio']:<8.2f} "
                  f"{metrics['max_drawdown']:<10.2%} {metrics['num_trades']:<8} {metrics['win_rate']:<8.2f}")
            
            total_sharpe += metrics['sharpe_ratio']
            total_return += metrics['total_return']
            
            if metrics['sharpe_ratio'] > best_sharpe:
                best_sharpe = metrics['sharpe_ratio']
                best_stock = symbol
        
        # 统计信息
        avg_sharpe = total_sharpe / len(successful_results)
        avg_return = total_return / len(successful_results)
        
        print(f"\n[STATISTICS]:")
        print(f"  Total Stocks Tested: {len(successful_results)}")
        print(f"  Average Return: {avg_return:.2%}")
        print(f"  Average Sharpe: {avg_sharpe:.2f}")
        print(f"  Best Stock: {best_stock} (Sharpe: {best_sharpe:.2f})")
        
        # 保存详细报告
        report_data = {
            'backtest_date': datetime.now().isoformat(),
            'period': f"{self.start_date} to {self.end_date}",
            'initial_cash': self.initial_cash,
            'fees': self.fees,
            'results': []
        }
        
        for result in successful_results:
            report_data['results'].append({
                'symbol': result['symbol'],
                'total_return': result['metrics']['total_return'],
                'sharpe_ratio': result['metrics']['sharpe_ratio'],
                'max_drawdown': result['metrics']['max_drawdown'],
                'benchmark_return': result['metrics']['benchmark_return'],
                'excess_return': result['metrics']['excess_return'],
                'num_trades': result['metrics']['num_trades'],
                'win_rate': result['metrics']['win_rate'],
                'final_value': float(result['portfolio'].value().iloc[-1])
            })
        
        # 保存报告
        with open('real_backtest_results.json', 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n[SAVED] Detailed report saved to 'real_backtest_results.json'")
        
        return report_data
    
    def run_complete_backtest(self):
        """运行完整回测"""
        start_time = datetime.now()
        
        try:
            # 1. 下载真实数据
            price_data = self.download_real_data()
            
            if not price_data:
                print("[ERROR] No stock data downloaded")
                return
            
            # 2. 对每只股票进行回测
            results = []
            
            for symbol in price_data.keys():
                print(f"\n{'='*20}")
                print(f"PROCESSING {symbol}")
                print(f"{'='*20}")
                
                # 计算技术指标
                indicators = self.calculate_technical_indicators(price_data, symbol)
                
                # 创建交易信号
                signals = self.create_trading_signals(price_data, indicators, symbol)
                
                if signals.empty:
                    print(f"[SKIP] {symbol}: No valid signals generated")
                    continue
                
                # 运行回测
                result = self.run_vectorbt_backtest(price_data, symbol, signals)
                
                if result:
                    results.append(result)
            
            # 3. 生成报告
            if results:
                report = self.generate_backtest_report(results)
                
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                print(f"\n{'='*60}")
                print(f"REAL VECTORBT BACKTEST COMPLETED")
                print(f"{'='*60}")
                print(f"Execution Time: {execution_time:.2f} seconds")
                print(f"Stocks Analyzed: {len(results)}")
                print(f"Average Performance: Sharpe {sum(r['metrics']['sharpe_ratio'] for r in results) / len(results):.2f}")
                print(f"Success Rate: {len(results) / len(price_data) * 100:.1f}%")
                
            else:
                print("[ERROR] No successful backtests completed")
                
        except Exception as e:
            print(f"[FATAL ERROR] Backtest failed: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    # 检查yfinance是否安装
    try:
        import yfinance
        print("[OK] yfinance is installed")
    except ImportError:
        print("[ERROR] yfinance not installed")
        print("Please install it with: pip install yfinance")
        return
    
    # 运行回测
    backtest = RealVectorBTBacktest()
    backtest.run_complete_backtest()


if __name__ == "__main__":
    main()