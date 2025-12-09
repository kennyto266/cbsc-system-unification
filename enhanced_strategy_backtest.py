#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 增强策略回测系统
集成StockBacktest的高级策略到完整量化交易系统
支持多策略、参数优化、Sharpe比率优化
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Tuple, Optional
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from itertools import product
import time

warnings.filterwarnings('ignore')

class EnhancedStrategyBacktest:
    """增强策略回测引擎"""
    
    def __init__(self, symbol: str, start_date: str = '2020-01-01', end_date: str = '2023-01-01'):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.results = []
        self.logger = logging.getLogger(__name__)
        
    def load_data(self) -> bool:
        """加载股票数据"""
        try:
            self.logger.info(f"正在加载 {self.symbol} 数据...")
            self.data = yf.download(self.symbol, start=self.start_date, end=self.end_date)
            if self.data is None or self.data.empty:
                self.logger.error(f"无法加载 {self.symbol} 数据")
                return False
            self.logger.info(f"数据加载完成: {len(self.data)} 个交易日")
            return True
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return False
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        # 移动平均线
        for period in [5, 10, 15, 20, 30, 50, 100, 200]:
            df[f'MA{period}'] = df['Close'].rolling(window=period).mean()
        
        # RSI指标
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 0.0001)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD指标
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        
        # 布林带
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
        
        # KD指标
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        df['K'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
        df['D'] = df['K'].rolling(window=3).mean()
        
        # 威廉指标
        df['WR'] = 100 * (high_max - df['Close']) / (high_max - low_min)
        
        # ADX指标
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # 成交量指标
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_ratio'] = df['Volume'] / df['Volume_MA']
        
        return df
    
    def run_ma_crossover_strategy(self, short_window: int, long_window: int) -> Dict:
        """移动平均交叉策略"""
        if short_window >= long_window:
            return None
            
        df = self.data.copy()
        df[f'MA{short_window}'] = df['Close'].rolling(window=short_window).mean()
        df[f'MA{long_window}'] = df['Close'].rolling(window=long_window).mean()
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 生成交易信号
        df['signal'] = np.where(df[f'MA{short_window}'] > df[f'MA{long_window}'], 1, 0)
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, f"MA交叉({short_window},{long_window})")
    
    def run_rsi_strategy(self, rsi_period: int, oversold: float, overbought: float) -> Dict:
        """RSI策略"""
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # RSI策略信号
        df['signal'] = 0
        df.loc[df['RSI'] < oversold, 'signal'] = 1  # 超卖买入
        df.loc[df['RSI'] > overbought, 'signal'] = 0  # 超买卖出
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, f"RSI({rsi_period},{oversold},{overbought})")
    
    def run_macd_strategy(self, fast: int, slow: int, signal: int) -> Dict:
        """MACD策略"""
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # MACD策略信号
        df['signal'] = np.where(df['MACD'] > df['MACD_signal'], 1, 0)
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, f"MACD({fast},{slow},{signal})")
    
    def run_bollinger_bands_strategy(self, period: int, std_dev: float) -> Dict:
        """布林带策略"""
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 布林带策略信号
        df['signal'] = 0
        df.loc[df['Close'] < df['BB_lower'], 'signal'] = 1  # 价格触及下轨买入
        df.loc[df['Close'] > df['BB_upper'], 'signal'] = 0  # 价格触及上轨卖出
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, f"布林带({period},{std_dev})")
    
    def run_combined_strategy(self, params: Dict) -> Dict:
        """组合策略"""
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 组合多个指标
        conditions = []
        
        # MA条件
        if 'ma_short' in params and 'ma_long' in params:
            ma_short = params['ma_short']
            ma_long = params['ma_long']
            df[f'MA{ma_short}'] = df['Close'].rolling(window=ma_short).mean()
            df[f'MA{ma_long}'] = df['Close'].rolling(window=ma_long).mean()
            conditions.append(df[f'MA{ma_short}'] > df[f'MA{ma_long}'])
        
        # RSI条件
        if 'rsi_oversold' in params and 'rsi_overbought' in params:
            rsi_oversold = params['rsi_oversold']
            rsi_overbought = params['rsi_overbought']
            conditions.append((df['RSI'] > rsi_oversold) & (df['RSI'] < rsi_overbought))
        
        # MACD条件
        if 'macd_enabled' in params and params['macd_enabled']:
            conditions.append(df['MACD'] > df['MACD_signal'])
        
        # 布林带条件
        if 'bb_enabled' in params and params['bb_enabled']:
            conditions.append(df['Close'] > df['BB_lower'])
        
        if not conditions:
            return None
        
        # 组合所有条件
        df['signal'] = 1
        for condition in conditions:
            df['signal'] = df['signal'] & condition
        df['signal'] = df['signal'].astype(int)
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, "组合策略")
    
    def _calculate_strategy_performance(self, df: pd.DataFrame, strategy_name: str) -> Dict:
        """计算策略绩效"""
        try:
            # 计算策略收益
            df['strategy_returns'] = df['position'].shift(1) * df['Close'].pct_change()
            df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
            
            # 计算绩效指标
            total_return = (df['cumulative_returns'].iloc[-1] - 1) * 100
            annual_return = ((df['cumulative_returns'].iloc[-1] ** (252 / len(df))) - 1) * 100
            volatility = df['strategy_returns'].std() * np.sqrt(252) * 100
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
            
            # 最大回撤
            cumulative = df['cumulative_returns']
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100
            
            # 胜率
            winning_trades = (df['strategy_returns'] > 0).sum()
            total_trades = (df['strategy_returns'] != 0).sum()
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # 交易次数
            trade_count = (df['position'] != 0).sum()
            
            return {
                'strategy_name': strategy_name,
                'total_return': round(total_return, 2),
                'annual_return': round(annual_return, 2),
                'volatility': round(volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 2),
                'trade_count': trade_count,
                'final_value': round(df['cumulative_returns'].iloc[-1] * 100000, 2)  # 假设初始资金10万
            }
        except Exception as e:
            self.logger.error(f"计算策略绩效失败: {e}")
            return None
    
    def optimize_parameters(self, strategy_type: str = 'all', max_workers: int = None) -> List[Dict]:
        """参数优化"""
        if max_workers is None:
            max_workers = min(mp.cpu_count(), 8)
        
        self.logger.info(f"开始参数优化，使用 {max_workers} 个线程")
        
        results = []
        
        if strategy_type in ['all', 'ma']:
            # MA交叉策略优化
            ma_results = self._optimize_ma_parameters(max_workers)
            results.extend(ma_results)
        
        if strategy_type in ['all', 'rsi']:
            # RSI策略优化
            rsi_results = self._optimize_rsi_parameters(max_workers)
            results.extend(rsi_results)
        
        if strategy_type in ['all', 'macd']:
            # MACD策略优化
            macd_results = self._optimize_macd_parameters(max_workers)
            results.extend(macd_results)
        
        if strategy_type in ['all', 'bb']:
            # 布林带策略优化
            bb_results = self._optimize_bb_parameters(max_workers)
            results.extend(bb_results)
        
        # 按Sharpe比率排序
        results = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)
        
        self.logger.info(f"参数优化完成，共测试 {len(results)} 个策略")
        return results
    
    def _optimize_ma_parameters(self, max_workers: int) -> List[Dict]:
        """优化MA参数"""
        results = []
        short_windows = range(5, 51, 5)
        long_windows = range(20, 201, 10)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for short, long in product(short_windows, long_windows):
                if short < long:
                    future = executor.submit(self.run_ma_crossover_strategy, short, long)
                    futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        return results
    
    def _optimize_rsi_parameters(self, max_workers: int) -> List[Dict]:
        """优化RSI参数"""
        results = []
        oversold_values = range(20, 41, 5)
        overbought_values = range(60, 81, 5)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for oversold, overbought in product(oversold_values, overbought_values):
                if oversold < overbought:
                    future = executor.submit(self.run_rsi_strategy, 14, oversold, overbought)
                    futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        return results
    
    def _optimize_macd_parameters(self, max_workers: int) -> List[Dict]:
        """优化MACD参数"""
        results = []
        fast_values = range(8, 17, 2)
        slow_values = range(20, 31, 2)
        signal_values = range(7, 12, 1)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for fast, slow, signal in product(fast_values, slow_values, signal_values):
                if fast < slow:
                    future = executor.submit(self.run_macd_strategy, fast, slow, signal)
                    futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        return results
    
    def _optimize_bb_parameters(self, max_workers: int) -> List[Dict]:
        """优化布林带参数"""
        results = []
        periods = range(15, 26, 2)
        std_devs = [1.5, 2.0, 2.5]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for period, std_dev in product(periods, std_devs):
                future = executor.submit(self.run_bollinger_bands_strategy, period, std_dev)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        return results
    
    def get_best_strategies(self, top_n: int = 10) -> List[Dict]:
        """获取最佳策略"""
        if not self.results:
            self.logger.warning("没有回测结果，请先运行参数优化")
            return []
        
        return self.results[:top_n]
    
    def generate_report(self, output_file: str = None) -> str:
        """生成回测报告"""
        if not self.results:
            return "没有回测结果"
        
        report = f"""
# {self.symbol} 策略回测报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
回测期间: {self.start_date} 至 {self.end_date}
测试策略数量: {len(self.results)}

## 最佳策略 (按Sharpe比率排序)

"""
        
        for i, strategy in enumerate(self.results[:10], 1):
            report += f"""
### {i}. {strategy['strategy_name']}
- 总收益率: {strategy['total_return']:.2f}%
- 年化收益率: {strategy['annual_return']:.2f}%
- 波动率: {strategy['volatility']:.2f}%
- Sharpe比率: {strategy['sharpe_ratio']:.3f}
- 最大回撤: {strategy['max_drawdown']:.2f}%
- 胜率: {strategy['win_rate']:.2f}%
- 交易次数: {strategy['trade_count']}
- 最终价值: ¥{strategy['final_value']:,.2f}

"""
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"报告已保存到: {output_file}")
        
        return report

def main():
    """主函数 - 示例用法"""
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 创建回测实例
    backtest = EnhancedStrategyBacktest('0700.HK', '2020-01-01', '2023-01-01')
    
    # 加载数据
    if not backtest.load_data():
        return
    
    # 运行参数优化
    print("开始参数优化...")
    backtest.optimize_parameters(strategy_type='all')
    
    # 获取最佳策略
    best_strategies = backtest.get_best_strategies(10)
    
    # 生成报告
    report = backtest.generate_report('strategy_backtest_report.txt')
    print(report)

if __name__ == "__main__":
    main()
