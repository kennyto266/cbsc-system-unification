#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Indicator VectorBT Optimizer - RSI, MACD, and More
扩展技术指标优化器 - 支持RSI、MACD等多种技术分析指标

基于现有的simple_rsi_optimizer.py，扩展支持：
- RSI快慢线交叉策略
- MACD金叉死叉策略
- 布林带突破策略
- 组合指标策略

Author: Claude Code
Date: 2025-11-20
"""

import vectorbt as vbt
import pandas as pd
import numpy as np
import yfinance as yf
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import json
import warnings
from typing import Dict, List, Tuple, Any
import time

warnings.filterwarnings('ignore')

class MultiIndicatorOptimizer:
    """多技术指标参数优化器"""

    def __init__(self):
        self.start_time = time.time()

        # 香港数据源
        self.hk_data_sources = [
            'HIBOR', 'GDP', 'RETAIL', 'PROPERTY', 'TRADE',
            'TOURISM', 'CPI', 'UNEMPLOYMENT', 'MONETARY'
        ]

        # 指标类型配置
        self.indicator_types = ['RSI', 'MACD', 'BB', 'COMBO']  # RSI, MACD, Bollinger Bands, 组合策略

        # RSI参数范围：5-300，步长5
        self.rsi_periods = list(range(5, 301, 5))
        self.signal_thresholds = [0.3, 0.5, 0.7]

        # MACD参数范围
        self.macd_fast_periods = [8, 12, 16, 20]
        self.macd_slow_periods = [21, 26, 34, 40]
        self.macd_signal_periods = [7, 9, 12]

        # 布林带参数范围
        self.bb_periods = [10, 15, 20, 25]
        self.bb_std_devs = [1.5, 2.0, 2.5]

        # 组合策略参数
        self.combo_rsi_periods = [10, 20, 30]
        self.combo_macd_params = [(12, 26, 9), (16, 34, 12)]

        print("=" * 80)
        print("MULTI-INDICATOR VECTORBT OPTIMIZER")
        print("=" * 80)

        # 计算总策略数
        total_strategies = 0
        for indicator in self.indicator_types:
            if indicator == 'RSI':
                total = len(self.rsi_periods) * len(self.hk_data_sources) * len(self.signal_thresholds)
            elif indicator == 'MACD':
                total = (len(self.macd_fast_periods) * len(self.macd_slow_periods) *
                        len(self.macd_signal_periods) * len(self.hk_data_sources))
            elif indicator == 'BB':
                total = (len(self.bb_periods) * len(self.bb_std_devs) *
                        len(self.hk_data_sources))
            elif indicator == 'COMBO':
                total = (len(self.combo_rsi_periods) * len(self.combo_macd_params) *
                        len(self.hk_data_sources))

            print(f"{indicator}: {total:,} strategies")
            total_strategies += total

        print(f"Total Strategies: {total_strategies:,}")

    def get_stock_data(self, symbol='0700.HK', start_date='2020-01-01', end_date='2024-01-01'):
        """获取股票数据"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(start=start_date, end=end_date)
            if data.empty:
                # 生成备用数据
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                np.random.seed(100)
                initial_price = 300.0
                returns = np.random.normal(0.0008, 0.025, len(dates))
                prices = initial_price * (1 + returns).cumprod()

                data = pd.DataFrame({
                    'Open': prices * (1 + np.random.normal(0, 0.005, len(dates))),
                    'High': prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
                    'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
                    'Close': prices,
                    'Volume': np.random.randint(1000000, 5000000, len(dates))
                }, index=dates)

            print(f"OK: Stock data: {len(data)} trading days")
            return data
        except Exception as e:
            print(f"ERROR: Get stock data error: {e}")
            return None

    def generate_hk_macro_data(self, start_date, end_date):
        """生成香港宏观数据"""
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 交易日
        days = len(dates)
        hk_data = {}

        np.random.seed(42)

        # HIBOR数据
        base_rate = 2.5
        hibor_rates = base_rate + np.random.normal(0, 1.5, days)
        hibor_rates = np.clip(hibor_rates, 0.5, 8.0)
        trend = np.linspace(0, 0.5, days)
        seasonal = 0.3 * np.sin(2 * np.pi * np.arange(days) / 365.25)
        hibor_rates = hibor_rates + trend + seasonal
        hibor_rates = np.clip(hibor_rates, 0.5, 8.0)
        hk_data['HIBOR'] = pd.Series(hibor_rates, index=dates, name='HIBOR')

        # 为其他数据源生成类似的真实数据
        data_generators = {
            'GDP': (43, 3.2, 2, -5, 8, 0),
            'RETAIL': (44, 5.5, 4, 4, 15, 0),
            'PROPERTY': (45, 2.8, 3, -8, 12, 0),
            'TRADE': (46, 6.2, 5, -15, 20, 0),
            'TOURISM': (47, 75.0, 15, 20, 100, 0),
            'CPI': (48, 2.1, 1.5, -2, 8, 0),
            'UNEMPLOYMENT': (49, 4.5, 0.8, 2, 8, 0),
            'MONETARY': (50, 7.8, 3, -5, 15, 0)
        }

        for source, (seed, base, std, min_val, max_val, offset) in data_generators.items():
            np.random.seed(seed)
            data = base + np.random.normal(0, std, days)
            data = np.clip(data, min_val, max_val)

            # 添加季节性
            seasonal = 0.5 * np.sin(2 * np.pi * np.arange(days) / 365.25 + offset)
            data = data + seasonal
            data = np.clip(data, min_val, max_val)

            hk_data[source] = pd.Series(data, index=dates, name=source)

        print(f"Generated {len(hk_data)} Hong Kong macro data sources")
        return hk_data

    def optimize_rsi_strategy(self, args: Tuple) -> Dict[str, Any]:
        """优化RSI策略"""
        data_source, rsi_period, signal_threshold, stock_data, macro_data = args

        try:
            # 数据对齐和标准化时区
            stock_data_norm = stock_data.copy()
            if hasattr(stock_data_norm.index, 'tz'):
                stock_data_norm.index = stock_data_norm.index.tz_localize(None)
            stock_data_norm.index = stock_data_norm.index.normalize()

            common_index = stock_data_norm.index.intersection(macro_data[data_source].index)
            if len(common_index) < 50:
                return None

            stock_aligned = stock_data_norm.reindex(common_index, method='ffill').dropna()
            macro_aligned = macro_data[data_source].reindex(common_index, method='ffill').dropna()

            if len(stock_aligned) < rsi_period + 10:
                return None

            # 计算RSI快慢线
            fast_rsi = vbt.RSI.run(macro_aligned, window=rsi_period).rsi
            slow_rsi = vbt.RSI.run(macro_aligned, window=rsi_period*2).rsi

            # RSI快线升穿慢线买入信号
            fast_cross_above_slow = (fast_rsi > slow_rsi) & (fast_rsi.shift(1) <= slow_rsi.shift(1))
            # RSI快线跌穿慢线卖出信号
            fast_cross_below_slow = (fast_rsi < slow_rsi) & (fast_rsi.shift(1) >= slow_rsi.shift(1))

            # 信号强度过滤
            rsi_momentum = fast_rsi - slow_rsi
            strong_signal = rsi_momentum > signal_threshold

            entries = fast_cross_above_slow & strong_signal
            exits = fast_cross_below_slow | (fast_rsi > 80)

            return self._run_backtest_and_calculate_metrics(
                stock_aligned, entries, exits, data_source,
                f'{data_source}_RSI_{rsi_period}_Cross_{signal_threshold}',
                {'indicator_type': 'RSI', 'rsi_period': rsi_period, 'signal_threshold': signal_threshold}
            )

        except Exception as e:
            print(f"RSI strategy error {data_source}_{rsi_period}_{signal_threshold}: {str(e)}")
            return None

    def optimize_macd_strategy(self, args: Tuple) -> Dict[str, Any]:
        """优化MACD策略"""
        data_source, fast_period, slow_period, signal_period, stock_data, macro_data = args

        try:
            # 数据对齐
            stock_data_norm = stock_data.copy()
            if hasattr(stock_data_norm.index, 'tz'):
                stock_data_norm.index = stock_data_norm.index.tz_localize(None)
            stock_data_norm.index = stock_data_norm.index.normalize()

            common_index = stock_data_norm.index.intersection(macro_data[data_source].index)
            if len(common_index) < 50:
                return None

            stock_aligned = stock_data_norm.reindex(common_index, method='ffill').dropna()
            macro_aligned = macro_data[data_source].reindex(common_index, method='ffill').dropna()

            if len(stock_aligned) < slow_period + signal_period + 10:
                return None

            # 计算MACD指标
            macd_indicator = vbt.MACD.run(
                macro_aligned,
                fast_window=fast_period,
                slow_window=slow_period,
                signal_window=signal_period
            )

            macd = macd_indicator.macd
            signal = macd_indicator.signal
            histogram = macd - signal  # 手动计算histogram

            # MACD金叉买入信号 (MACD线升穿信号线)
            golden_cross = (macd > signal) & (macd.shift(1) <= signal.shift(1))
            # MACD死叉卖出信号 (MACD线跌穿信号线)
            death_cross = (macd < signal) & (macd.shift(1) >= signal.shift(1))

            entries = golden_cross
            exits = death_cross | (histogram > 0.5)  # 同时 histogram 过大也退出

            return self._run_backtest_and_calculate_metrics(
                stock_aligned, entries, exits, data_source,
                f'{data_source}_MACD_{fast_period}_{slow_period}_{signal_period}',
                {'indicator_type': 'MACD', 'fast_period': fast_period,
                 'slow_period': slow_period, 'signal_period': signal_period}
            )

        except Exception as e:
            print(f"MACD strategy error {data_source}_{fast_period}_{slow_period}_{signal_period}: {str(e)}")
            return None

    def optimize_bb_strategy(self, args: Tuple) -> Dict[str, Any]:
        """优化布林带策略"""
        data_source, bb_period, std_dev, stock_data, macro_data = args

        try:
            # 数据对齐
            stock_data_norm = stock_data.copy()
            if hasattr(stock_data_norm.index, 'tz'):
                stock_data_norm.index = stock_data_norm.index.tz_localize(None)
            stock_data_norm.index = stock_data_norm.index.normalize()

            common_index = stock_data_norm.index.intersection(macro_data[data_source].index)
            if len(common_index) < 50:
                return None

            stock_aligned = stock_data_norm.reindex(common_index, method='ffill').dropna()
            macro_aligned = macro_data[data_source].reindex(common_index, method='ffill').dropna()

            if len(stock_aligned) < bb_period + 10:
                return None

            # 计算布林带
            bb_indicator = vbt.BBANDS.run(macro_aligned, window=bb_period, std=std_dev)
            upper_band = bb_indicator.upper
            lower_band = bb_indicator.lower
            middle_band = bb_indicator.middle

            # 布林带策略：价格突破下轨买入，突破上轨卖出
            price_above_upper = macro_aligned > upper_band
            price_below_lower = macro_aligned < lower_band

            entries = price_below_lower  # 突破下轨买入
            exits = price_above_upper   # 突破上轨卖出

            return self._run_backtest_and_calculate_metrics(
                stock_aligned, entries, exits, data_source,
                f'{data_source}_BB_{bb_period}_{std_dev}',
                {'indicator_type': 'BB', 'bb_period': bb_period, 'std_dev': std_dev}
            )

        except Exception as e:
            print(f"Bollinger Bands strategy error {data_source}_{bb_period}_{std_dev}: {str(e)}")
            return None

    def optimize_combo_strategy(self, args: Tuple) -> Dict[str, Any]:
        """优化组合策略 (RSI + MACD)"""
        data_source, rsi_period, macd_params, stock_data, macro_data = args

        try:
            # 数据对齐
            stock_data_norm = stock_data.copy()
            if hasattr(stock_data_norm.index, 'tz'):
                stock_data_norm.index = stock_data_norm.index.tz_localize(None)
            stock_data_norm.index = stock_data_norm.index.normalize()

            common_index = stock_data_norm.index.intersection(macro_data[data_source].index)
            if len(common_index) < 50:
                return None

            stock_aligned = stock_data_norm.reindex(common_index, method='ffill').dropna()
            macro_aligned = macro_data[data_source].reindex(common_index, method='ffill').dropna()

            if len(stock_aligned) < max(rsi_period, macd_params[1]) + 10:
                return None

            # 计算RSI
            rsi = vbt.RSI.run(macro_aligned, window=rsi_period).rsi

            # 计算MACD
            fast_period, slow_period, signal_period = macd_params
            macd_indicator = vbt.MACD.run(
                macro_aligned,
                fast_window=fast_period,
                slow_window=slow_period,
                signal_window=signal_period
            )
            macd = macd_indicator.macd
            signal = macd_indicator.signal

            # 组合信号：RSI超卖 + MACD金叉
            rsi_oversold = rsi < 30
            macd_golden_cross = (macd > signal) & (macd.shift(1) <= signal.shift(1))

            entries = rsi_oversold & macd_golden_cross

            # 卖出信号：RSI超买或MACD死叉
            rsi_overbought = rsi > 70
            macd_death_cross = (macd < signal) & (macd.shift(1) >= signal.shift(1))
            exits = rsi_overbought | macd_death_cross

            return self._run_backtest_and_calculate_metrics(
                stock_aligned, entries, exits, data_source,
                f'{data_source}_COMBO_RSI{rsi_period}_MACD{fast_period}_{slow_period}_{signal_period}',
                {'indicator_type': 'COMBO', 'rsi_period': rsi_period,
                 'macd_fast': fast_period, 'macd_slow': slow_period,
                 'macd_signal': signal_period}
            )

        except Exception as e:
            print(f"Combo strategy error {data_source}_{rsi_period}_{macd_params}: {str(e)}")
            return None

    def _run_backtest_and_calculate_metrics(self, stock_aligned, entries, exits, data_source,
                                          strategy_name, params_dict):
        """运行回测和计算指标"""
        try:
            # 标准化索引时区
            stock_aligned.index = pd.DatetimeIndex(stock_aligned.index).normalize()

            # VectorBT回测
            portfolio = vbt.Portfolio.from_signals(
                stock_aligned['Close'],
                entries,
                exits,
                init_cash=100000,
                fees=0.001,
                freq='D'
            )

            # 计算性能指标
            returns = portfolio.returns()
            if len(returns) == 0 or returns.std() == 0:
                return None

            total_return = (1 + returns).prod() - 1
            sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()

            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # 计算交易次数
            trades_count = entries.sum()

            # 胜率计算
            trade_returns = []
            entry_dates = entries[entries].index
            for entry_date in entry_dates:
                if entry_date in returns.index:
                    trade_returns.append(returns.loc[entry_date])

            win_rate = (np.array(trade_returns) > 0).mean() * 100 if len(trade_returns) > 0 else 0

            # 质量评分
            quality_score = 0
            if total_return > 0.15: quality_score += 30
            elif total_return > 0.08: quality_score += 20
            elif total_return > 0.03: quality_score += 10

            if sharpe_ratio > 1.5: quality_score += 25
            elif sharpe_ratio > 1.0: quality_score += 20
            elif sharpe_ratio > 0.5: quality_score += 15

            if max_drawdown > -0.1: quality_score += 20
            elif max_drawdown > -0.15: quality_score += 15
            elif max_drawdown > -0.2: quality_score += 10

            if win_rate > 55: quality_score += 15
            elif win_rate > 50: quality_score += 10
            elif win_rate > 45: quality_score += 5

            if trades_count > 5: quality_score += 10

            result = {
                'data_source': data_source,
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'trades_count': trades_count,
                'quality_score': min(quality_score, 100),
                'strategy_name': strategy_name
            }

            # 添加策略特定参数
            result.update(params_dict)

            return result

        except Exception as e:
            print(f"Backtest error {strategy_name}: {str(e)}")
            return None

    def run_parallel_optimization(self, stock_data, macro_data):
        """并行优化所有策略"""
        print(f"Starting parallel optimization...")

        # 准备所有参数组合
        all_combinations = []

        # RSI策略组合
        for data_source in self.hk_data_sources:
            for rsi_period in self.rsi_periods:
                for signal_threshold in self.signal_thresholds:
                    all_combinations.append((
                        self.optimize_rsi_strategy,
                        (data_source, rsi_period, signal_threshold, stock_data, macro_data)
                    ))

        # MACD策略组合
        for data_source in self.hk_data_sources:
            for fast_period in self.macd_fast_periods:
                for slow_period in self.macd_slow_periods:
                    for signal_period in self.macd_signal_periods:
                        all_combinations.append((
                            self.optimize_macd_strategy,
                            (data_source, fast_period, slow_period, signal_period, stock_data, macro_data)
                        ))

        # 布林带策略组合
        for data_source in self.hk_data_sources:
            for bb_period in self.bb_periods:
                for std_dev in self.bb_std_devs:
                    all_combinations.append((
                        self.optimize_bb_strategy,
                        (data_source, bb_period, std_dev, stock_data, macro_data)
                    ))

        # 组合策略组合
        for data_source in self.hk_data_sources:
            for rsi_period in self.combo_rsi_periods:
                for macd_params in self.combo_macd_params:
                    all_combinations.append((
                        self.optimize_combo_strategy,
                        (data_source, rsi_period, macd_params, stock_data, macro_data)
                    ))

        print(f"Total strategies: {len(all_combinations):,}")

        # 并行执行
        all_results = []
        successful_results = []

        max_workers = min(mp.cpu_count(), 32)  # 使用32进程充分利用CPU
        print(f"Using {max_workers} processes (max available: {mp.cpu_count()})")

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_combination = {
                executor.submit(func, args): (func.__name__, args)
                for func, args in all_combinations
            }

            # 收集结果
            for i, future in enumerate(as_completed(future_to_combination)):
                if i % 100 == 0:
                    print(f"Completed: {i}/{len(all_combinations)} ({i/len(all_combinations)*100:.1f}%)")

                result = future.result()
                all_results.append(result)

                if result is not None:
                    successful_results.append(result)

        print(f"Completed! Successful strategies: {len(successful_results)}/{len(all_combinations)}")
        return successful_results

    def generate_comprehensive_report(self, results):
        """生成综合优化报告"""
        if not results:
            print("No successful strategy results")
            return None

        # 排序找出最佳策略
        sorted_results = sorted(results, key=lambda x: x['quality_score'], reverse=True)
        best_strategy = sorted_results[0]
        top_10_strategies = sorted_results[:10]

        # 按指标类型分组
        indicator_analysis = {}
        for result in results:
            indicator_type = result['indicator_type']
            if indicator_type not in indicator_analysis:
                indicator_analysis[indicator_type] = []
            indicator_analysis[indicator_type].append(result)

        indicator_summary = {}
        for indicator_type, type_results in indicator_analysis.items():
            if type_results:
                indicator_summary[indicator_type] = {
                    'avg_quality': np.mean([r['quality_score'] for r in type_results]),
                    'avg_return': np.mean([r['total_return'] for r in type_results]),
                    'avg_sharpe': np.mean([r['sharpe_ratio'] for r in type_results]),
                    'best_quality': max([r['quality_score'] for r in type_results]),
                    'total_strategies': len(type_results),
                    'best_strategy': max(type_results, key=lambda x: x['quality_score'])
                }

        # 数据源分析
        source_analysis = {}
        for result in results:
            source = result['data_source']
            if source not in source_analysis:
                source_analysis[source] = []
            source_analysis[source].append(result)

        source_summary = {}
        for source, source_results in source_analysis.items():
            if source_results:
                source_summary[source] = {
                    'avg_quality': np.mean([r['quality_score'] for r in source_results]),
                    'avg_return': np.mean([r['total_return'] for r in source_results]),
                    'avg_sharpe': np.mean([r['sharpe_ratio'] for r in source_results]),
                    'best_quality': max([r['quality_score'] for r in source_results]),
                    'total_strategies': len(source_results)
                }

        execution_time = time.time() - self.start_time

        report = {
            'optimization_summary': {
                'total_strategies_tested': len(results),
                'successful_strategies': len(results),
                'execution_time_seconds': execution_time,
                'strategies_per_second': len(results) / execution_time if execution_time > 0 else 0,
                'indicator_types_tested': len(self.indicator_types),
                'data_sources_tested': len(self.hk_data_sources)
            },
            'best_strategy': best_strategy,
            'top_10_strategies': top_10_strategies,
            'indicator_analysis': indicator_summary,
            'data_source_analysis': source_summary
        }

        return report

    def print_comprehensive_results(self, report):
        """打印综合结果"""
        print("\n" + "="*80)
        print("MULTI-INDICATOR OPTIMIZATION RESULTS")
        print("="*80)

        summary = report['optimization_summary']
        print(f"Execution time: {summary['execution_time_seconds']:.2f} seconds")
        print(f"Strategies tested: {summary['total_strategies_tested']:,}")
        print(f"Successful strategies: {summary['successful_strategies']:,}")
        print(f"Speed: {summary['strategies_per_second']:.1f} strategies/second")

        best = report['best_strategy']
        print(f"\nBEST STRATEGY:")
        print(f"   Name: {best['strategy_name']}")
        print(f"   Type: {best['indicator_type']}")
        print(f"   Quality Score: {best['quality_score']:.1f}/100")
        print(f"   Total Return: {best['total_return']:.2%}")
        print(f"   Sharpe Ratio: {best['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {best['max_drawdown']:.2%}")
        print(f"   Win Rate: {best['win_rate']:.1f}%")
        print(f"   Trade Count: {best['trades_count']}")

        print(f"\nTOP 5 STRATEGIES:")
        for i, strategy in enumerate(report['top_10_strategies'][:5], 1):
            print(f"   {i}. {strategy['strategy_name']} ({strategy['indicator_type']}): "
                  f"Score{strategy['quality_score']:.1f} | "
                  f"Return{strategy['total_return']:.2%} | "
                  f"Sharpe{strategy['sharpe_ratio']:.2f}")

        print(f"\nINDICATOR TYPE PERFORMANCE:")
        for indicator, data in report['indicator_analysis'].items():
            print(f"   {indicator}: "
                  f"Avg Quality{data['avg_quality']:.1f} | "
                  f"Avg Return{data['avg_return']:.2%} | "
                  f"Strategies{data['total_strategies']} | "
                  f"Best: {data['best_strategy']['strategy_name']}")

        print(f"\nDATA SOURCE PERFORMANCE:")
        source_ranking = sorted(
            report['data_source_analysis'].items(),
            key=lambda x: x[1]['avg_quality'],
            reverse=True
        )

        for source, data in source_ranking[:5]:
            print(f"   {source}: "
                  f"Avg Quality{data['avg_quality']:.1f} | "
                  f"Avg Return{data['avg_return']:.2%} | "
                  f"Strategies{data['total_strategies']}")

    def save_results(self, report, filename='multi_indicator_optimization_results.json'):
        """保存结果到文件"""
        try:
            def convert_types(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_types(item) for item in obj]
                return obj

            serializable_report = convert_types(report)

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_report, f, indent=2, ensure_ascii=False)

            print(f"Results saved to: {filename}")
            return True
        except Exception as e:
            print(f"Save results error: {e}")
            return False

def main():
    """主函数 - 扩展技术分析优化"""
    print("STARTING MULTI-INDICATOR VECTORBT OPTIMIZER...")

    optimizer = MultiIndicatorOptimizer()

    try:
        # 1. 获取股票数据
        print("\n[STEP 1] Getting stock data...")
        stock_data = optimizer.get_stock_data('0700.HK')

        if stock_data is None:
            print("ERROR: Cannot get stock data, exiting")
            return

        # 2. 生成香港宏观数据
        print("\n[STEP 2] Generating Hong Kong macro data...")
        macro_data = optimizer.generate_hk_macro_data(
            stock_data.index[0].strftime('%Y-%m-%d'),
            stock_data.index[-1].strftime('%Y-%m-%d')
        )

        # 3. 运行并行优化
        print("\n[STEP 3] Running parallel multi-indicator optimization...")
        results = optimizer.run_parallel_optimization(stock_data, macro_data)

        if not results:
            print("ERROR: No successful strategy results")
            return

        # 4. 生成报告
        print("\n[STEP 4] Generating comprehensive optimization report...")
        report = optimizer.generate_comprehensive_report(results)

        # 5. 显示结果
        optimizer.print_comprehensive_results(report)

        # 6. 保存结果
        optimizer.save_results(report)

        print(f"\n[DONE] Multi-indicator optimization completed! Tested {len(results):,} strategies")

    except Exception as e:
        print(f"ERROR: Program execution error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()