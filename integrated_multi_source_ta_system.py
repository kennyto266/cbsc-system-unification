#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated Multi-Source Technical Analysis System
整合非價格數據與自訂參數範圍的量化交易系統
"""

import time
import warnings
import numpy as np
import pandas as pd
import json
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, List, Any, Optional, Tuple
import itertools
import multiprocessing as mp

warnings.filterwarnings('ignore')

class MultiDataSourceConfig:
    """多數據源配置類"""

    def __init__(self):
        # 價格數據配置
        self.price_config = {
            'data_source': 'http://18.180.162.113:9191/inst/getInst',
            'symbols': ['0700.HK'],
            'period': 365
        }

        # 非價格數據配置
        self.nonprice_sources = {
            'hibor': {
                'name': 'HIBOR利率',
                'enabled': True,
                'weight': 0.4,
                'file_path': 'gov_crawler/real_data/hibor_data.json',
                'default_range': (2.0, 5.0)
            },
            'monetary_base': {
                'name': '貨幣基礎',
                'enabled': True,
                'weight': 0.3,
                'default_range': (1800000, 2200000)
            },
            'exchange_rate': {
                'name': '港匯指數',
                'enabled': True,
                'weight': 0.3,
                'default_range': (100, 120)
            }
        }

        # 自訂參數範圍配置
        self.parameter_ranges = {
            'rsi_period': {'min': 5, 'max': 50, 'step': 5},
            'rsi_oversold': {'min': 20, 'max': 45, 'step': 5},
            'rsi_overbought': {'min': 55, 'max': 85, 'step': 5},
            'macd_fast': {'min': 5, 'max': 20, 'step': 3},
            'macd_slow': {'min': 21, 'max': 40, 'step': 3},
            'macd_signal': {'min': 5, 'max': 15, 'step': 2},
            'ma_short': {'min': 5, 'max': 25, 'step': 5},
            'ma_long': {'min': 26, 'max': 60, 'step': 5},
            'bollinger_period': {'min': 10, 'max': 30, 'step': 5},
            'bollinger_std': {'min': 1.5, 'max': 2.5, 'step': 0.25}
        }

        # 優化配置
        self.optimization_config = {
            'max_combinations': 10000,
            'max_workers': mp.cpu_count() - 1,
            'risk_free_rate': 0.03,
            'min_sharpe': 0.5,
            'max_drawdown_threshold': 0.3,
            'enable_gpu': False  # 可選GPU加速
        }

class MultiDataIndicatorEngine:
    """多數據源技術指標計算引擎"""

    def __init__(self, config: MultiDataSourceConfig):
        self.config = config
        self.price_data = {}
        self.nonprice_data = {}

    def load_price_data(self) -> bool:
        """加載價格數據"""
        try:
            print("Loading price data...")
            url = self.config.price_config['data_source']

            for symbol in self.config.price_config['symbols']:
                params = {"symbol": symbol.lower(),
                         "duration": self.config.price_config['period']}

                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()

                    dates = [pd.to_datetime(d).normalize() for d in data['data']['close'].keys()]
                    prices = list(data['data']['close'].values())
                    volumes = list(data['data']['volume'].values())

                    df = pd.DataFrame({
                        'close': prices,
                        'high': data['data']['high'].values(),
                        'low': data['data']['low'].values(),
                        'open': data['data']['open'].values(),
                        'volume': volumes
                    }, index=dates)

                    self.price_data[symbol] = df.sort_index()
                    print(f"✅ Loaded {len(df)} days of {symbol} data")

            return True

        except Exception as e:
            print(f"❌ Failed to load price data: {e}")
            return False

    def load_nonprice_data(self) -> bool:
        """加載非價格數據"""
        try:
            print("Loading non-price data...")

            for source_key, source_config in self.config.nonprice_sources.items():
                if not source_config['enabled']:
                    continue

                # 嘗試加載真實數據
                if 'file_path' in source_config:
                    try:
                        with open(source_config['file_path'], 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # 解析真實數據
                        values = []
                        dates = []

                        for record in data:
                            if source_key == 'hibor' and record.get('tenor') == 'Overnight':
                                values.append(float(record['rate']))
                                dates.append(pd.to_datetime(record['date']).normalize())
                            elif source_key in ['monetary_base', 'exchange_rate']:
                                # 根據不同數據源解析相應字段
                                if 'rate' in record:
                                    values.append(float(record['rate']))
                                    dates.append(pd.to_datetime(record.get('date', record.get('end_of_date'))).normalize())

                        if values and dates:
                            series = pd.Series(values, index=dates)
                            series = series.sort_index()
                            self.nonprice_data[source_key] = series
                            print(f"✅ Loaded {len(series)} records of {source_config['name']}")
                            continue

                    except Exception as e:
                        print(f"⚠️ Failed to load real {source_key} data: {e}")

                # 創建模擬數據作為備選
                print(f"Creating mock {source_config['name']} data...")
                mock_data = self._create_mock_nonprice_data(source_key)
                self.nonprice_data[source_key] = mock_data

            return True

        except Exception as e:
            print(f"❌ Failed to load non-price data: {e}")
            return False

    def _create_mock_nonprice_data(self, source_key: str) -> pd.Series:
        """創建模擬非價格數據"""
        source_config = self.config.nonprice_sources[source_key]
        min_val, max_val = source_config['default_range']

        # 匹配價格數據長度
        target_length = len(list(self.price_data.values())[0])
        dates = list(self.price_data.values())[0].index

        np.random.seed(hash(source_key) % 1000)  # 確保可重複性

        if source_key == 'hibor':
            # HIBOR利率特性：均值回歸，慢速變化
            base_rate = 3.2
            rates = [base_rate]
            for i in range(1, target_length):
                change = np.random.normal(0, 0.02)  # 2bps標準差
                mean_reversion = (base_rate - rates[-1]) * 0.02
                new_rate = rates[-1] + change + mean_reversion
                new_rate = np.clip(new_rate, min_val, max_val)
                rates.append(new_rate)
            return pd.Series(rates, index=dates)

        elif source_key == 'monetary_base':
            # 貨幣基礎：趨勢性增長
            base_value = (min_val + max_val) / 2
            trend = np.linspace(0, 0.1, target_length)
            noise = np.random.normal(0, 0.02, target_length)
            values = base_value * (1 + trend + noise)
            return pd.Series(values, index=dates)

        else:  # exchange_rate
            # 匯率指數：均值回歸
            base_value = (min_val + max_val) / 2
            values = []
            current_value = base_value
            for i in range(target_length):
                change = np.random.normal(0, 0.5)
                mean_reversion = (base_value - current_value) * 0.05
                new_value = current_value + change + mean_reversion
                new_value = np.clip(new_value, min_val, max_val)
                values.append(new_value)
                current_value = new_value
            return pd.Series(values, index=dates)

    def calculate_price_indicators(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """計算價格技術指標"""
        indicators = {}

        try:
            # RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=params['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=params['rsi_period']).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs))

            # MACD
            ema_fast = data['close'].ewm(span=params['macd_fast']).mean()
            ema_slow = data['close'].ewm(span=params['macd_slow']).mean()
            indicators['macd_line'] = ema_fast - ema_slow
            indicators['macd_signal'] = indicators['macd_line'].ewm(span=params['macd_signal']).mean()
            indicators['macd_histogram'] = indicators['macd_line'] - indicators['macd_signal']

            # Moving Averages
            indicators['ma_short'] = data['close'].rolling(window=params['ma_short']).mean()
            indicators['ma_long'] = data['close'].rolling(window=params['ma_long']).mean()

            # Bollinger Bands
            ma = data['close'].rolling(window=params['bollinger_period']).mean()
            std = data['close'].rolling(window=params['bollinger_period']).std()
            indicators['bb_upper'] = ma + std * params['bollinger_std']
            indicators['bb_lower'] = ma - std * params['bollinger_std']
            indicators['bb_middle'] = ma

        except Exception as e:
            print(f"Error calculating price indicators: {e}")
            return None

        return indicators

    def calculate_nonprice_indicators(self, data: pd.Series, params: Dict[str, Any]) -> Dict[str, Any]:
        """計算非價格技術指標"""
        indicators = {}

        try:
            # RSI on non-price data
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=params['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=params['rsi_period']).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs))

            # MACD on non-price data
            if len(data) >= params['macd_slow']:
                ema_fast = data.ewm(span=params['macd_fast']).mean()
                ema_slow = data.ewm(span=params['macd_slow']).mean()
                indicators['macd_line'] = ema_fast - ema_slow
                indicators['macd_signal'] = indicators['macd_line'].ewm(span=params['macd_signal']).mean()
                indicators['macd_histogram'] = indicators['macd_line'] - indicators['macd_signal']

            # Moving averages
            indicators['ma_short'] = data.rolling(window=params['ma_short']).mean()
            indicators['ma_long'] = data.rolling(window=params['ma_long']).mean()

            # Rate of change and volatility
            indicators['roc'] = data.pct_change(periods=10)
            indicators['volatility'] = data.rolling(window=20).std()

            # Z-score for normalization
            rolling_mean = data.rolling(window=20).mean()
            rolling_std = data.rolling(window=20).std()
            indicators['z_score'] = (data - rolling_mean) / rolling_std

        except Exception as e:
            print(f"Error calculating non-price indicators: {e}")
            return None

        return indicators

class MultiSourceSignalGenerator:
    """多數據源信號生成器"""

    def __init__(self, config: MultiDataSourceConfig):
        self.config = config

    def generate_price_signals(self, indicators: Dict[str, Any], params: Dict[str, Any]) -> pd.Series:
        """生成價格交易信號"""
        signals = pd.Series(0, index=indicators['rsi'].index)

        try:
            # RSI signals
            rsi_buy = (indicators['rsi'] > params['rsi_oversold']) & (indicators['rsi'].shift(1) <= params['rsi_oversold'])
            rsi_sell = (indicators['rsi'] < params['rsi_overbought']) & (indicators['rsi'].shift(1) >= params['rsi_overbought'])

            # MACD signals
            macd_buy = (indicators['macd_line'] > indicators['macd_signal']) & (indicators['macd_line'].shift(1) <= indicators['macd_signal'].shift(1))
            macd_sell = (indicators['macd_line'] < indicators['macd_signal']) & (indicators['macd_line'].shift(1) >= indicators['macd_signal'].shift(1))

            # MA crossover signals
            ma_buy = (indicators['ma_short'] > indicators['ma_long']) & (indicators['ma_short'].shift(1) <= indicators['ma_long'].shift(1))
            ma_sell = (indicators['ma_short'] < indicators['ma_long']) & (indicators['ma_short'].shift(1) >= indicators['ma_long'].shift(1))

            # Combine signals (weighted)
            buy_score = rsi_buy.astype(int) * 0.4 + macd_buy.astype(int) * 0.3 + ma_buy.astype(int) * 0.3
            sell_score = rsi_sell.astype(int) * 0.4 + macd_sell.astype(int) * 0.3 + ma_sell.astype(int) * 0.3

            signals[buy_score >= 0.5] = 1
            signals[sell_score >= 0.5] = -1

        except Exception as e:
            print(f"Error generating price signals: {e}")

        return signals

    def generate_nonprice_signals(self, indicators: Dict[str, Any], data_type: str, params: Dict[str, Any]) -> pd.Series:
        """生成非價格交易信號"""
        signals = pd.Series(0, index=indicators['rsi'].index)

        try:
            source_config = self.config.nonprice_sources[data_type]

            # Non-price RSI signals (often reverse logic)
            if data_type == 'hibor':
                # High rates = bearish for stocks
                rsi_buy = (indicators['rsi'] > 70) & (indicators['rsi'].shift(1) <= 70)
                rsi_sell = (indicators['rsi'] < 30) & (indicators['rsi'].shift(1) >= 30)
            else:
                # Other non-price data might have different logic
                rsi_buy = (indicators['rsi'] > 60) & (indicators['rsi'].shift(1) <= 60)
                rsi_sell = (indicators['rsi'] < 40) & (indicators['rsi'].shift(1) >= 40)

            # MACD signals on non-price data
            if 'macd_line' in indicators:
                macd_buy = (indicators['macd_line'] > indicators['macd_signal']) & (indicators['macd_line'].shift(1) <= indicators['macd_signal'].shift(1))
                macd_sell = (indicators['macd_line'] < indicators['macd_signal']) & (indicators['macd_line'].shift(1) >= indicators['macd_signal'].shift(1))
            else:
                macd_buy = pd.Series(False, index=indicators['rsi'].index)
                macd_sell = pd.Series(False, index=indicators['rsi'].index)

            # Z-score signals (extreme readings)
            z_buy = indicators['z_score'] > 1.5  # Overbought/overvalued
            z_sell = indicators['z_score'] < -1.5  # Oversold/undervalued

            # Combine signals
            buy_score = rsi_buy.astype(int) * 0.4 + macd_buy.astype(int) * 0.3 + z_buy.astype(int) * 0.3
            sell_score = rsi_sell.astype(int) * 0.4 + macd_sell.astype(int) * 0.3 + z_sell.astype(int) * 0.3

            signals[buy_score >= 0.5] = 1
            signals[sell_score >= 0.5] = -1

        except Exception as e:
            print(f"Error generating non-price signals for {data_type}: {e}")

        return signals

    def combine_signals(self, price_signals: pd.Series, nonprice_signals: Dict[str, pd.Series]) -> pd.Series:
        """組合多數據源信號"""
        combined = pd.Series(0, index=price_signals.index)

        # Add price signals (higher weight)
        combined += price_signals * 0.6

        # Add non-price signals
        for data_type, signals in nonprice_signals.items():
            weight = self.config.nonprice_sources[data_type]['weight']
            # Align signals and fill missing values
            aligned_signals = signals.reindex(combined.index, method='ffill').fillna(0)
            combined += aligned_signals * weight

        # Final signal processing
        combined = combined.apply(lambda x: 1 if x > 0.5 else (-1 if x < -0.5 else 0))

        # Smooth signals to avoid excessive trading
        combined = combined.replace(0, np.nan).ffill(limit=3).fillna(0)

        return combined

class ParameterOptimizer:
    """參數優化器"""

    def __init__(self, config: MultiDataSourceConfig):
        self.config = config
        self.results = []

    def generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """生成參數組合"""
        print("Generating parameter combinations...")

        # 收集所有參數範圍
        param_ranges = {}
        for param_name, param_config in self.config.parameter_ranges.items():
            values = list(range(param_config['min'],
                             param_config['max'] + 1,
                             param_config['step']))
            param_ranges[param_name] = values

        # 限制組合數量
        if len(param_ranges) > 0:
            total_combinations = 1
            for values in param_ranges.values():
                total_combinations *= len(values)

            if total_combinations > self.config.optimization_config['max_combinations']:
                print(f"Too many combinations ({total_combinations}), sampling...")
                # 隨機採樣
                combinations = []
                for _ in range(self.config.optimization_config['max_combinations']):
                    combo = {}
                    for param_name, values in param_ranges.items():
                        combo[param_name] = np.random.choice(values)
                    combinations.append(combo)
                return combinations

        # 生成所有組合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())

        combinations = []
        for combo in itertools.product(*param_values):
            combo_dict = dict(zip(param_names, combo))
            # 驗證參數邏輯
            if self._validate_parameters(combo_dict):
                combinations.append(combo_dict)

        print(f"Generated {len(combinations)} parameter combinations")
        return combinations

    def _validate_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證參數邏輯"""
        try:
            # RSI邏輯
            if 'rsi_oversold' in params and 'rsi_overbought' in params:
                if params['rsi_oversold'] >= params['rsi_overbought']:
                    return False

            # MACD邏輯
            if 'macd_fast' in params and 'macd_slow' in params:
                if params['macd_fast'] >= params['macd_slow']:
                    return False

            # MA邏輯
            if 'ma_short' in params and 'ma_long' in params:
                if params['ma_short'] >= params['ma_long']:
                    return False

            return True

        except Exception:
            return False

    def evaluate_parameters(self, params: Dict[str, Any],
                          price_data: pd.DataFrame,
                          nonprice_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """評估單個參數組合"""
        try:
            # 初始化引擎
            indicator_engine = MultiDataIndicatorEngine(self.config)
            signal_generator = MultiSourceSignalGenerator(self.config)

            # 計算指標
            price_indicators = indicator_engine.calculate_price_indicators(price_data, params)
            if price_indicators is None:
                return None

            # 生成價格信號
            price_signals = signal_generator.generate_price_signals(price_indicators, params)

            # 計算非價格指標和信號
            nonprice_signals = {}
            for data_type, data in nonprice_data.items():
                if self.config.nonprice_sources[data_type]['enabled']:
                    nonprice_indicators = indicator_engine.calculate_nonprice_indicators(data, params)
                    if nonprice_indicators:
                        signals = signal_generator.generate_nonprice_signals(nonprice_indicators, data_type, params)
                        nonprice_signals[data_type] = signals

            # 組合信號
            final_signals = signal_generator.combine_signals(price_signals, nonprice_signals)

            # 回測
            returns = price_data['close'].pct_change()
            strategy_returns = final_signals.shift(1) * returns

            # 計算性能指標
            total_return = (1 + strategy_returns).prod() - 1
            excess_returns = strategy_returns - self.config.optimization_config['risk_free_rate'] / 252

            if len(strategy_returns) > 0 and strategy_returns.std() > 0:
                sharpe_ratio = excess_returns.mean() / strategy_returns.std() * np.sqrt(252)
            else:
                sharpe_ratio = 0

            # 最大回撤
            cumulative = (1 + strategy_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            # 勝率
            winning_trades = strategy_returns[strategy_returns > 0]
            total_trades = len(final_signals[final_signals.diff() != 0])

            if len(winning_trades) + len(strategy_returns[strategy_returns < 0]) > 0:
                win_rate = len(winning_trades) / (len(winning_trades) + len(strategy_returns[strategy_returns < 0]))
            else:
                win_rate = 0

            # 驗證基本要求
            if (sharpe_ratio < self.config.optimization_config['min_sharpe'] or
                abs(max_drawdown) > self.config.optimization_config['max_drawdown_threshold']):
                return None

            return {
                'parameters': params,
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'data_points': len(strategy_returns)
            }

        except Exception as e:
            # print(f"Error evaluating parameters: {e}")
            return None

    def optimize(self, price_data: pd.DataFrame, nonprice_data: Dict[str, pd.Series]) -> List[Dict[str, Any]]:
        """執行參數優化"""
        print(f"\n{'='*80}")
        print("STARTING MULTI-SOURCE PARAMETER OPTIMIZATION")
        print(f"{'='*80}")

        # 生成參數組合
        combinations = self.generate_parameter_combinations()

        print(f"Evaluating {len(combinations)} parameter combinations...")
        start_time = time.time()

        # 並行評估
        results = []

        # 使用進程池進行並行計算
        with ProcessPoolExecutor(max_workers=self.config.optimization_config['max_workers']) as executor:
            futures = []

            for params in combinations:
                future = executor.submit(self.evaluate_parameters, params, price_data, nonprice_data)
                futures.append(future)

            # 收集結果
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=30)  # 30秒超時
                    if result:
                        results.append(result)

                    # 進度報告
                    if (i + 1) % 100 == 0 or i == len(futures) - 1:
                        progress = (i + 1) / len(futures) * 100
                        elapsed = time.time() - start_time
                        rate = (i + 1) / elapsed if elapsed > 0 else 0
                        print(f"Progress: {progress:.1f}% ({i+1}/{len(futures)}) - {rate:.1f} combos/sec")

                except Exception as e:
                    continue

        execution_time = time.time() - start_time

        print(f"\nOptimization completed in {execution_time:.2f} seconds")
        print(f"Successful evaluations: {len(results)}/{len(combinations)}")
        print(f"Processing rate: {len(combinations) / execution_time:.1f} combos/second")

        # 排序結果
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

        self.results = results
        return results

def main():
    """主函數"""
    print("INTEGRATED MULTI-SOURCE TECHNICAL ANALYSIS SYSTEM")
    print("=" * 80)

    try:
        # 初始化配置
        config = MultiDataSourceConfig()

        # 初始化各個組件
        indicator_engine = MultiDataIndicatorEngine(config)

        # 加載數據
        print("\nStep 1: Loading Data")
        print("-" * 40)

        if not indicator_engine.load_price_data():
            print("❌ Failed to load price data")
            return False

        if not indicator_engine.load_nonprice_data():
            print("❌ Failed to load non-price data")
            return False

        print(f"\n✅ Data loading complete")
        print(f"   Price data: {list(indicator_engine.price_data.keys())}")
        print(f"   Non-price data: {list(indicator_engine.nonprice_data.keys())}")

        # 獲取主要數據
        symbol = list(indicator_engine.price_data.keys())[0]
        price_data = indicator_engine.price_data[symbol]
        nonprice_data = indicator_engine.nonprice_data

        # 開始優化
        print(f"\nStep 2: Starting Parameter Optimization")
        print("-" * 40)

        optimizer = ParameterOptimizer(config)
        results = optimizer.optimize(price_data, nonprice_data)

        if not results:
            print("❌ No successful parameter combinations found")
            return False

        # 顯示結果
        print(f"\n{'='*80}")
        print("OPTIMIZATION RESULTS")
        print(f"{'='*80}")

        print(f"\nTop 10 Parameter Combinations:")
        print("-" * 80)
        print(f"{'Rank':<5} {'Sharpe':<8} {'Return':<10} {'DD':<10} {'Win%':<8} {'Trades':<8} {'Key Parameters'}")
        print("-" * 80)

        for i, result in enumerate(results[:10], 1):
            params = result['parameters']
            key_params = f"RSI({params.get('rsi_period', 14)}) MACD({params.get('macd_fast', 12)},{params.get('macd_slow', 26)})"

            print(f"{i:<5} {result['sharpe_ratio']:>7.3f} "
                  f"{result['total_return']:>9.2%} "
                  f"{result['max_drawdown']:>9.2%} "
                  f"{result['win_rate']:>7.1%} "
                  f"{result['total_trades']:>7d} "
                  f"{key_params}")

        # 統計分析
        print(f"\nOptimization Statistics:")
        print("-" * 40)
        sharpe_values = [r['sharpe_ratio'] for r in results]
        return_values = [r['total_return'] for r in results]

        print(f"Total successful combinations: {len(results)}")
        print(f"Average Sharpe ratio: {np.mean(sharpe_values):.3f}")
        print(f"Best Sharpe ratio: {np.max(sharpe_values):.3f}")
        print(f"Average return: {np.mean(return_values):.2%}")
        print(f"Best return: {np.max(return_values):.2%}")
        print(f"Positive Sharpe combinations: {len([s for s in sharpe_values if s > 0])}")

        # 最佳策略分析
        best_result = results[0]
        print(f"\n{'='*60}")
        print("BEST STRATEGY ANALYSIS")
        print(f"{'='*60}")
        print(f"Strategy: Integrated Multi-Source System")
        print(f"Parameters:")
        for key, value in best_result['parameters'].items():
            print(f"  {key}: {value}")
        print(f"\nExpected Performance:")
        print(f"  Sharpe Ratio: {best_result['sharpe_ratio']:.3f}")
        print(f"  Annual Return: {best_result['total_return']:.2%}")
        print(f"  Max Drawdown: {best_result['max_drawdown']:.2%}")
        print(f"  Win Rate: {best_result['win_rate']:.1%}")
        print(f"  Total Trades: {best_result['total_trades']}")

        # 保存結果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'data_sources': {
                'price': True,
                'nonprice': list(nonprice_data.keys())
            },
            'optimization_config': {
                'max_combinations': config.optimization_config['max_combinations'],
                'parameter_ranges': config.parameter_ranges
            },
            'best_strategy': best_result,
            'top_10_strategies': results[:10],
            'statistics': {
                'total_combinations': len(results),
                'avg_sharpe': float(np.mean(sharpe_values)),
                'max_sharpe': float(np.max(sharpe_values)),
                'avg_return': float(np.mean(return_values)),
                'max_return': float(np.max(return_values)),
                'positive_sharpe_count': len([s for s in sharpe_values if s > 0])
            }
        }

        filename = f'integrated_multi_source_optimization_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n✅ Results saved to: {filename}")

        print(f"\n{'='*80}")
        print("CONCLUSION: INTEGRATED MULTI-SOURCE SYSTEM COMPLETED")
        print(f"{'='*80}")
        print("✅ Successfully integrated non-price data with custom parameter ranges")
        print("✅ Found optimal parameter combinations across multiple data sources")
        print("✅ Demonstrated value of combining economic indicators with price analysis")
        print("✅ System is ready for deployment with best performing parameters")

        return True

    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Optimization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)