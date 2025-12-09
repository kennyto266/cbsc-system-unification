#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete CBSC Strategies Parameter Optimizer
Optimize all 4 CBSC strategies with comprehensive parameter testing
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import itertools
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class CompleteCBSCStrategiesOptimizer:
    def __init__(self):
        self.results = {}
        self.best_results = {}
        self.optimization_data = None
        self.risk_free_rate = 0.02  # 2% annual risk-free rate

    def load_optimization_data(self):
        """Load CBSC optimization data"""
        print("Loading CBSC optimization data...")

        try:
            # Load the latest parameter analysis results
            with open('complete_parameter_analysis_20251204_203609.json', 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)

            print("Successfully loaded CBSC parameter analysis:")
            print(f"  Data Period: {analysis_data['analysis_metadata']['data_period']}")
            print(f"  Trading Days: {analysis_data['analysis_metadata']['trading_days']}")
            print(f"  Strategies: {len(analysis_data['optimal_parameters'])}")

            # Load price data for backtesting
            data_files = [
                'acheng_sharpe_results.csv',
                'warrant_sentiment_merged.csv',
                'strategy_performance_demo.csv'
            ]

            data = None
            for file in data_files:
                try:
                    data = pd.read_csv(file)
                    if 'Date' in data.columns or 'date' in data.columns:
                        print(f"Successfully loaded price data: {file}")
                        break
                except:
                    continue

            # Process the loaded data
            if data is not None:
                if 'HSIF_close' in data.columns:
                    data = data.rename(columns={'HSIF_close': 'Close'})
                elif 'close' in data.columns:
                    data = data.rename(columns={'close': 'Close'})

                # Ensure Date column format
                if 'Date' in data.columns:
                    data['Date'] = pd.to_datetime(data['Date'])
                elif 'date' in data.columns:
                    data['Date'] = pd.to_datetime(data['date'])
                    data = data.drop('date', axis=1)

                data = data.sort_values('Date').reset_index(drop=True)

            else:
                # Generate simulated data
                print("Generating simulated data for testing...")
                dates = pd.date_range(start='2025-09-01', end='2025-10-17', freq='D')
                dates = dates[dates.weekday < 5]

                np.random.seed(42)
                n_days = len(dates)

                data = pd.DataFrame({
                    'Date': dates,
                    'Close': 100 + np.cumsum(np.random.normal(0, 0.02, n_days)),
                    'Volume': np.random.uniform(100000000, 500000000, n_days),
                    'Bull_Ratio': np.random.uniform(0.3, 0.7, n_days),
                    'Bear_Turnover_HKD': np.random.uniform(50000000, 300000000, n_days)
                })

            self.optimization_data = data
            self.parameter_analysis = analysis_data
            return True

        except Exception as e:
            print(f"Data loading failed: {e}")
            return False

    def generate_strategy_parameters(self, strategy_name: str) -> List[Dict]:
        """Generate comprehensive parameter combinations for each strategy"""

        if strategy_name == 'sentiment_momentum':
            return self.generate_sentiment_momentum_parameters()
        elif strategy_name == 'volume_reversal':
            return self.generate_volume_reversal_parameters()
        elif strategy_name == 'risk_adjusted_bollinger':
            return self.generate_risk_adjusted_bollinger_parameters()
        elif strategy_name == 'time_decay_momentum':
            return self.generate_time_decay_momentum_parameters()
        else:
            return []

    def generate_sentiment_momentum_parameters(self) -> List[Dict]:
        """Generate sentiment momentum strategy parameters"""
        print("Generating sentiment momentum parameters...")

        # Parameter ranges for comprehensive testing
        sentiment_short_windows = list(range(5, 21, 5))      # 5, 10, 15, 20
        sentiment_long_windows = list(range(10, 31, 5))       # 10, 15, 20, 25, 30
        momentum_thresholds = [0.01, 0.02, 0.03, 0.05, 0.08]  # 1%, 2%, 3%, 5%, 8%
        volume_multipliers = [1.1, 1.2, 1.3, 1.5, 2.0]        # 1.1x, 1.2x, 1.3x, 1.5x, 2.0x
        volume_ma_windows = list(range(5, 16, 5))            # 5, 10, 15
        min_volume_thresholds = [100000000, 200000000, 500000000]  # 100M, 200M, 500M
        position_sizes = [0.1, 0.2, 0.3, 0.4]                # 10%, 20%, 30%, 40%

        parameters = []
        total_combinations = 0

        for short_w in sentiment_short_windows:
            for long_w in sentiment_long_windows:
                if short_w >= long_w:
                    continue

                for momentum_th in momentum_thresholds:
                    for vol_mult in volume_multipliers:
                        for vol_ma in volume_ma_windows:
                            for min_vol in min_volume_thresholds:
                                for pos_size in position_sizes:
                                    params = {
                                        'sentiment_short_window': short_w,
                                        'sentiment_long_window': long_w,
                                        'momentum_threshold': momentum_th,
                                        'volume_multiplier': vol_mult,
                                        'volume_ma_window': vol_ma,
                                        'min_volume_threshold': min_vol,
                                        'position_size': pos_size
                                    }
                                    parameters.append(params)
                                    total_combinations += 1

        print(f"Generated {total_combinations:,} sentiment momentum parameter combinations")
        return parameters

    def generate_volume_reversal_parameters(self) -> List[Dict]:
        """Generate volume reversal strategy parameters"""
        print("Generating volume reversal parameters...")

        ratio_short_windows = list(range(2, 11, 2))        # 2, 4, 6, 8, 10
        ratio_long_windows = list(range(5, 21, 5))         # 5, 10, 15, 20
        volume_spike_multipliers = [1.05, 1.1, 1.2, 1.3, 1.5]  # 1.05x, 1.1x, 1.2x, 1.3x, 1.5x
        volume_spike_windows = list(range(3, 11, 2))       # 3, 5, 7, 9
        extreme_bull_thresholds = [0.50, 0.55, 0.60, 0.65] # 50%, 55%, 60%, 65%
        extreme_bear_thresholds = [0.35, 0.40, 0.45, 0.50] # 35%, 40%, 45%, 50%
        position_sizes = [0.2, 0.3, 0.4, 0.5]               # 20%, 30%, 40%, 50%

        parameters = []
        total_combinations = 0

        for short_w in ratio_short_windows:
            for long_w in ratio_long_windows:
                if short_w >= long_w:
                    continue

                for vol_mult in volume_spike_multipliers:
                    for vol_w in volume_spike_windows:
                        for bull_th in extreme_bull_thresholds:
                            for bear_th in extreme_bear_thresholds:
                                if bull_th <= bear_th:
                                    continue

                                for pos_size in position_sizes:
                                    params = {
                                        'ratio_short_window': short_w,
                                        'ratio_long_window': long_w,
                                        'volume_spike_multiplier': vol_mult,
                                        'volume_spike_window': vol_w,
                                        'extreme_bull_threshold': bull_th,
                                        'extreme_bear_threshold': bear_th,
                                        'position_size': pos_size
                                    }
                                    parameters.append(params)
                                    total_combinations += 1

        print(f"Generated {total_combinations:,} volume reversal parameter combinations")
        return parameters

    def generate_risk_adjusted_bollinger_parameters(self) -> List[Dict]:
        """Generate risk adjusted Bollinger strategy parameters"""
        print("Generating risk adjusted Bollinger parameters...")

        rsi_periods = list(range(5, 16, 5))             # 5, 10, 15
        rsi_overbought_levels = [60, 65, 70, 75]        # 60, 65, 70, 75
        rsi_oversold_levels = [25, 30, 35, 40]          # 25, 30, 35, 40
        bb_periods = list(range(5, 16, 5))              # 5, 10, 15
        bb_std_multipliers = [1.5, 1.8, 2.0, 2.2]      # 1.5, 1.8, 2.0, 2.2
        risk_threshold_bull = [0.6, 0.65, 0.7, 0.75]    # 60%, 65%, 70%, 75%
        risk_threshold_bear = [0.3, 0.35, 0.4, 0.45]    # 30%, 35%, 40%, 45%
        position_sizes = [0.2, 0.3, 0.4, 0.5]           # 20%, 30%, 40%, 50%

        parameters = []
        total_combinations = 0

        for rsi_p in rsi_periods:
            for rsi_ob in rsi_overbought_levels:
                for rsi_os in rsi_oversold_levels:
                    if rsi_ob <= rsi_os:
                        continue

                    for bb_p in bb_periods:
                        for bb_std in bb_std_multipliers:
                            for risk_bull in risk_threshold_bull:
                                for risk_bear in risk_threshold_bear:
                                    if risk_bull <= risk_bear:
                                        continue

                                    for pos_size in position_sizes:
                                        params = {
                                            'rsi_period': rsi_p,
                                            'rsi_overbought': rsi_ob,
                                            'rsi_oversold': rsi_os,
                                            'bb_period': bb_p,
                                            'bb_std_multiplier': bb_std,
                                            'risk_threshold_bull': risk_bull,
                                            'risk_threshold_bear': risk_bear,
                                            'position_size': pos_size
                                        }
                                        parameters.append(params)
                                        total_combinations += 1

        print(f"Generated {total_combinations:,} risk adjusted Bollinger parameter combinations")
        return parameters

    def generate_time_decay_momentum_parameters(self) -> List[Dict]:
        """Generate time decay momentum strategy parameters"""
        print("Generating time decay momentum parameters...")

        decay_half_lives = [10, 20, 30, 40, 50]           # 10, 20, 30, 40, 50 days
        momentum_strength_thresholds = [0.01, 0.02, 0.03, 0.05]  # 1%, 2%, 3%, 5%
        bull_thresholds = [0.50, 0.52, 0.55, 0.60]        # 50%, 52%, 55%, 60%
        bear_thresholds = [0.40, 0.45, 0.48, 0.50]        # 40%, 45%, 48%, 50%
        time_decay_thresholds = [0.3, 0.4, 0.5, 0.6]      # 30%, 40%, 50%, 60%
        min_turnover_thresholds = [300000, 500000, 1000000]  # 300K, 500K, 1M
        position_sizes = [0.15, 0.25, 0.35, 0.45]         # 15%, 25%, 35%, 45%

        parameters = []
        total_combinations = 0

        for decay_hl in decay_half_lives:
            for mom_th in momentum_strength_thresholds:
                for bull_th in bull_thresholds:
                    for bear_th in bear_thresholds:
                        if bull_th <= bear_th:
                            continue

                        for time_th in time_decay_thresholds:
                            for min_turn in min_turnover_thresholds:
                                for pos_size in position_sizes:
                                    params = {
                                        'decay_half_life': decay_hl,
                                        'momentum_strength_threshold': mom_th,
                                        'bull_threshold': bull_th,
                                        'bear_threshold': bear_th,
                                        'time_decay_threshold': time_th,
                                        'min_turnover_threshold': min_turn,
                                        'position_size': pos_size
                                    }
                                    parameters.append(params)
                                    total_combinations += 1

        print(f"Generated {total_combinations:,} time decay momentum parameter combinations")
        return parameters

    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        data = data.copy()

        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        data['BB_Middle'] = data['Close'].rolling(window=20).mean()
        bb_std = data['Close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
        data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)

        # Volume MA
        data['Volume_MA'] = data['Volume'].rolling(window=10).mean()

        # Bull/Bear Ratio MA (if available)
        if 'Bull_Ratio' in data.columns:
            data['Bull_Ratio_MA'] = data['Bull_Ratio'].rolling(window=10).mean()

        return data

    def simulate_sentiment_momentum_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """Simulate sentiment momentum strategy"""
        data = self.calculate_technical_indicators(data.copy())

        # Extract parameters
        short_w = params['sentiment_short_window']
        long_w = params['sentiment_long_window']
        momentum_th = params['momentum_threshold']
        vol_mult = params['volume_multiplier']
        vol_ma_w = params['volume_ma_window']
        min_vol = params['min_volume_threshold']
        pos_size = params['position_size']

        # Calculate strategy indicators
        if 'Bull_Ratio' in data.columns:
            data['Bull_Ratio_Short'] = data['Bull_Ratio'].rolling(window=short_w).mean()
            data['Bull_Ratio_Long'] = data['Bull_Ratio'].rolling(window=long_w).mean()
            data['Bull_Ratio_Momentum'] = (data['Bull_Ratio_Short'] - data['Bull_Ratio_Long']) / data['Bull_Ratio_Long']

        # Generate signals
        data['Signal'] = 'HOLD'
        if 'Bull_Ratio_Momentum' in data.columns:
            buy_condition = (
                (data['Bull_Ratio_Momentum'] > momentum_th) &
                (data['Volume'] > data['Volume_MA'] * vol_mult) &
                (data['Volume'] > min_vol) &
                (data['RSI'] < 70)  # Avoid overbought
            )

            sell_condition = (
                (data['Bull_Ratio_Momentum'] < -momentum_th) |
                (data['RSI'] > 80)  # Exit on extreme overbought
            )

            data.loc[buy_condition, 'Signal'] = 'BUY'
            data.loc[sell_condition, 'Signal'] = 'SELL'

        # Calculate performance
        return self.calculate_strategy_performance(data, params, 'sentiment_momentum')

    def simulate_volume_reversal_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """Simulate volume reversal strategy"""
        data = self.calculate_technical_indicators(data.copy())

        # Extract parameters
        short_w = params['ratio_short_window']
        long_w = params['ratio_long_window']
        vol_spike_mult = params['volume_spike_multiplier']
        vol_spike_w = params['volume_spike_window']
        bull_th = params['extreme_bull_threshold']
        bear_th = params['extreme_bear_threshold']
        pos_size = params['position_size']

        # Calculate strategy indicators
        if 'Bull_Ratio' in data.columns:
            data['Bull_Ratio_Short'] = data['Bull_Ratio'].rolling(window=short_w).mean()
            data['Bull_Ratio_Long'] = data['Bull_Ratio'].rolling(window=long_w).mean()
            data['Volume_Spike'] = data['Volume'] / data['Volume'].rolling(window=vol_spike_w).mean()

        # Generate reversal signals
        data['Signal'] = 'HOLD'
        if all(col in data.columns for col in ['Bull_Ratio_Short', 'Bull_Ratio_Long', 'Volume_Spike']):
            # Buy when extremely bearish with volume spike
            buy_condition = (
                (data['Bull_Ratio_Short'] < bear_th) &
                (data['Volume_Spike'] > vol_spike_mult) &
                (data['RSI'] < 30)
            )

            # Sell when extremely bullish or reversal confirmed
            sell_condition = (
                (data['Bull_Ratio_Short'] > bull_th) |
                (data['RSI'] > 75)
            )

            data.loc[buy_condition, 'Signal'] = 'BUY'
            data.loc[sell_condition, 'Signal'] = 'SELL'

        # Calculate performance
        return self.calculate_strategy_performance(data, params, 'volume_reversal')

    def simulate_risk_adjusted_bollinger_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """Simulate risk adjusted Bollinger strategy"""
        data = self.calculate_technical_indicators(data.copy())

        # Extract parameters
        rsi_p = params['rsi_period']
        rsi_ob = params['rsi_overbought']
        rsi_os = params['rsi_oversold']
        bb_p = params['bb_period']
        bb_std = params['bb_std_multiplier']
        risk_bull = params['risk_threshold_bull']
        risk_bear = params['risk_threshold_bear']
        pos_size = params['position_size']

        # Recalculate RSI and Bollinger with custom parameters
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_p).mean()
        rs = gain / loss
        data['RSI_Custom'] = 100 - (100 / (1 + rs))

        data['BB_Middle_Custom'] = data['Close'].rolling(window=bb_p).mean()
        bb_std_custom = data['Close'].rolling(window=bb_p).std()
        data['BB_Upper_Custom'] = data['BB_Middle_Custom'] + (bb_std_custom * bb_std)
        data['BB_Lower_Custom'] = data['BB_Middle_Custom'] - (bb_std_custom * bb_std)

        # Generate signals with risk adjustment
        data['Signal'] = 'HOLD'

        # Buy conditions
        buy_condition = (
            ((data['RSI_Custom'] < rsi_os) | (data['Close'] < data['BB_Lower_Custom'])) &
            (data['RSI_Custom'] > 20)  # Avoid extreme oversold
        )

        # Risk-adjusted buy conditions based on Bull_Ratio
        if 'Bull_Ratio' in data.columns:
            risk_adjusted_buy = buy_condition & (data['Bull_Ratio'] > risk_bear)
        else:
            risk_adjusted_buy = buy_condition

        # Sell conditions
        sell_condition = (
            ((data['RSI_Custom'] > rsi_ob) | (data['Close'] > data['BB_Upper_Custom'])) |
            (data['RSI_Custom'] > 85)  # Force exit on extreme overbought
        )

        # Risk-adjusted sell conditions
        if 'Bull_Ratio' in data.columns:
            risk_adjusted_sell = sell_condition | (data['Bull_Ratio'] < risk_bull)
        else:
            risk_adjusted_sell = sell_condition

        data.loc[risk_adjusted_buy, 'Signal'] = 'BUY'
        data.loc[risk_adjusted_sell, 'Signal'] = 'SELL'

        # Calculate performance
        return self.calculate_strategy_performance(data, params, 'risk_adjusted_bollinger')

    def simulate_time_decay_momentum_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """Simulate time decay momentum strategy"""
        data = self.calculate_technical_indicators(data.copy())

        # Extract parameters
        decay_hl = params['decay_half_life']
        mom_th = params['momentum_strength_threshold']
        bull_th = params['bull_threshold']
        bear_th = params['bear_threshold']
        time_th = params['time_decay_threshold']
        min_turn = params['min_turnover_threshold']
        pos_size = params['position_size']

        # Calculate time decay weighted momentum
        data['Price_Momentum'] = data['Close'].pct_change()

        # Apply exponential decay
        decay_factor = np.log(2) / decay_hl
        time_weights = np.exp(-decay_factor * np.arange(len(data)))
        data['Time_Decay_Momentum'] = data['Price_Momentum'].rolling(window=decay_hl).apply(
            lambda x: np.sum(x * time_weights[-len(x):]) / np.sum(time_weights[-len(x):]) if len(x) > 0 else 0
        )

        # Generate signals
        data['Signal'] = 'HOLD'

        # Buy conditions
        buy_condition = (
            (data['Time_Decay_Momentum'] > mom_th) &
            (data['Volume'] > min_turn)
        )

        # Sentiment-adjusted conditions
        if 'Bull_Ratio' in data.columns:
            sentiment_buy = buy_condition & (data['Bull_Ratio'] > bull_th)
            sentiment_sell = (data['Time_Decay_Momentum'] < -mom_th) | (data['Bull_Ratio'] < bear_th)
        else:
            sentiment_buy = buy_condition
            sentiment_sell = data['Time_Decay_Momentum'] < -mom_th

        data.loc[sentiment_buy, 'Signal'] = 'BUY'
        data.loc[sentiment_sell, 'Signal'] = 'SELL'

        # Calculate performance
        return self.calculate_strategy_performance(data, params, 'time_decay_momentum')

    def calculate_strategy_performance(self, data: pd.DataFrame, params: Dict, strategy_name: str) -> Dict:
        """Calculate strategy performance metrics"""

        # Extract position size
        pos_size = params.get('position_size', 0.3)

        # Calculate positions and returns
        cash = 100000  # Starting capital
        position = 0
        portfolio_values = [cash]
        trades = []

        for i in range(len(data)):
            if i == 0:
                continue

            current_price = data.loc[i, 'Close']
            signal = data.loc[i, 'Signal']

            if signal == 'BUY' and position == 0 and cash > current_price:
                # Buy
                shares = int(cash * pos_size / current_price)
                cash -= shares * current_price
                position = shares
                trades.append({
                    'type': 'BUY',
                    'date': data.loc[i, 'Date'],
                    'price': current_price,
                    'shares': shares
                })

            elif signal == 'SELL' and position > 0:
                # Sell
                cash += position * current_price
                trades.append({
                    'type': 'SELL',
                    'date': data.loc[i, 'Date'],
                    'price': current_price,
                    'shares': position
                })
                position = 0

            # Calculate portfolio value
            portfolio_value = cash + (position * current_price if position > 0 else 0)
            portfolio_values.append(portfolio_value)

        # Calculate performance metrics
        if len(portfolio_values) > 1:
            portfolio_series = pd.Series(portfolio_values)
            returns = portfolio_series.pct_change().dropna()

            total_return = (portfolio_values[-1] / portfolio_values[0] - 1)

            # Annualized metrics
            trading_days = len(data)
            annual_return = total_return * (252 / trading_days) if trading_days > 0 else 0
            volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.15

            # Risk-adjusted metrics
            sharpe_ratio = (annual_return - self.risk_free_rate) / volatility if volatility > 0 else 0

            # Maximum drawdown
            rolling_max = portfolio_series.expanding().max()
            drawdown = (portfolio_series - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # Calmar ratio
            calmar_ratio = abs(annual_return / max_drawdown) if max_drawdown != 0 else annual_return / 0.001

            # Trading statistics
            buy_trades = len([t for t in trades if t['type'] == 'BUY'])
            sell_trades = len([t for t in trades if t['type'] == 'SELL'])
            total_trades = min(buy_trades, sell_trades)

            # Win rate calculation
            profitable_trades = 0
            trade_pairs = []
            for i, trade in enumerate(trades):
                if trade['type'] == 'SELL' and i > 0 and trades[i-1]['type'] == 'BUY':
                    buy_price = trades[i-1]['price']
                    sell_price = trade['price']
                    if sell_price > buy_price:
                        profitable_trades += 1
                    trade_pairs.append({
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'profit_pct': (sell_price - buy_price) / buy_price
                    })

            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            avg_profit = np.mean([t['profit_pct'] for t in trade_pairs]) if trade_pairs else 0

        else:
            total_return = 0
            annual_return = 0
            sharpe_ratio = 0
            max_drawdown = 0
            calmar_ratio = 0
            win_rate = 0
            total_trades = 0
            avg_profit = 0
            volatility = 0.15

        # Return performance with parameters
        result = {
            'strategy_name': strategy_name,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'avg_profit': avg_profit,
            'volatility': volatility,
            'final_value': portfolio_values[-1] if portfolio_values else 100000,
            'parameters': params
        }

        return result

    def optimize_strategy(self, strategy_name: str):
        """Optimize a single strategy with all parameter combinations"""
        print(f"\n{'='*80}")
        print(f"Optimizing {strategy_name.replace('_', ' ').upper()} Strategy")
        print(f"{'='*80}")

        # Generate parameter combinations
        parameter_combinations = self.generate_strategy_parameters(strategy_name)

        if not parameter_combinations:
            print(f"No parameter combinations generated for {strategy_name}")
            return None

        print(f"\nTesting {len(parameter_combinations):,} parameter combinations...")

        # Strategy simulation function
        strategy_simulators = {
            'sentiment_momentum': self.simulate_sentiment_momentum_strategy,
            'volume_reversal': self.simulate_volume_reversal_strategy,
            'risk_adjusted_bollinger': self.simulate_risk_adjusted_bollinger_strategy,
            'time_decay_momentum': self.simulate_time_decay_momentum_strategy
        }

        simulator = strategy_simulators.get(strategy_name)
        if not simulator:
            print(f"No simulator found for {strategy_name}")
            return None

        # Run optimization
        results = []
        best_sharpe = -float('inf')
        best_return = -float('inf')
        best_calmar = -float('inf')
        most_trades = 0

        optimal_sharpe = None
        optimal_return = None
        optimal_calmar = None
        optimal_trades = None

        total_combinations = len(parameter_combinations)
        progress_interval = max(1, total_combinations // 10)

        for idx, params in enumerate(parameter_combinations):
            # Progress display
            if (idx + 1) % progress_interval == 0 or idx == 0:
                progress = (idx + 1) / total_combinations * 100
                print(f"Progress: {progress:.1f}% ({idx+1}/{total_combinations}) - Best Sharpe: {best_sharpe:.4f}")

            try:
                # Simulate strategy
                result = simulator(self.optimization_data.copy(), params)
                results.append(result)

                # Update best results
                if result['sharpe_ratio'] > best_sharpe and result['total_trades'] > 0:
                    best_sharpe = result['sharpe_ratio']
                    optimal_sharpe = result.copy()

                if result['total_return'] > best_return and result['total_trades'] > 0:
                    best_return = result['total_return']
                    optimal_return = result.copy()

                if result['calmar_ratio'] > best_calmar and result['total_trades'] > 0:
                    best_calmar = result['calmar_ratio']
                    optimal_calmar = result.copy()

                if result['total_trades'] > most_trades:
                    most_trades = result['total_trades']
                    optimal_trades = result.copy()

            except Exception as e:
                # Skip invalid parameter combinations
                continue

        # Filter results with trades
        trading_results = [r for r in results if r['total_trades'] > 0]

        print(f"\nOptimization complete for {strategy_name}!")
        print(f"Total combinations tested: {len(parameter_combinations):,}")
        print(f"Combinations with trades: {len(trading_results):,}")

        # Store results
        strategy_results = {
            'all_results': results,
            'trading_results': trading_results,
            'best_sharpe': optimal_sharpe,
            'best_return': optimal_return,
            'best_calmar': optimal_calmar,
            'most_trades': optimal_trades,
            'total_combinations_tested': total_combinations,
            'combinations_with_trades': len(trading_results)
        }

        return strategy_results

    def run_complete_optimization(self):
        """Run optimization for all 4 CBSC strategies"""
        print("Starting Complete CBSC Strategies Parameter Optimization")
        print("=" * 80)

        # Load data
        if not self.load_optimization_data():
            print("Data loading failed, cannot proceed with optimization")
            return None

        strategies = [
            'sentiment_momentum',
            'volume_reversal',
            'risk_adjusted_bollinger',
            'time_decay_momentum'
        ]

        all_results = {}

        for strategy in strategies:
            try:
                strategy_results = self.optimize_strategy(strategy)
                if strategy_results:
                    all_results[strategy] = strategy_results
                    print(f"Successfully optimized {strategy}")
                else:
                    print(f"Failed to optimize {strategy}")
            except Exception as e:
                print(f"Error optimizing {strategy}: {e}")
                continue

        self.results = all_results
        return all_results

    def analyze_all_results(self):
        """Analyze results for all strategies"""
        print("\n" + "=" * 80)
        print("COMPLETE CBSC STRATEGIES OPTIMIZATION ANALYSIS")
        print("=" * 80)

        if not self.results:
            print("No results to analyze")
            return

        # Strategy comparison table
        print(f"\n{'Strategy':<25} {'Total Tests':<12} {'With Trades':<12} {'Best Sharpe':<12} {'Best Return':<12} {'Best Calmar':<12}")
        print("-" * 85)

        strategy_summary = {}

        for strategy_name, strategy_results in self.results.items():
            total_tests = strategy_results['total_combinations_tested']
            with_trades = strategy_results['combinations_with_trades']

            best_sharpe = strategy_results['best_sharpe']['sharpe_ratio'] if strategy_results['best_sharpe'] else 0
            best_return = strategy_results['best_return']['total_return'] if strategy_results['best_return'] else 0
            best_calmar = strategy_results['best_calmar']['calmar_ratio'] if strategy_results['best_calmar'] else 0

            strategy_summary[strategy_name] = {
                'total_tests': total_tests,
                'with_trades': with_trades,
                'best_sharpe': best_sharpe,
                'best_return': best_return,
                'best_calmar': best_calmar
            }

            print(f"{strategy_name.replace('_', ' '):<25} {total_tests:<12,} {with_trades:<12,} {best_sharpe:<12.6f} {best_return:<12.6f} {best_calmar:<12.6f}")

        # Detailed analysis for each strategy
        print(f"\n" + "=" * 80)
        print("DETAILED STRATEGY ANALYSIS")
        print("=" * 80)

        for strategy_name, strategy_results in self.results.items():
            print(f"\n{strategy_name.replace('_', ' ').upper()} STRATEGY")
            print("-" * 50)

            if strategy_results['best_sharpe']:
                best = strategy_results['best_sharpe']
                print(f"Best Sharpe Configuration:")
                print(f"  Sharpe Ratio: {best['sharpe_ratio']:.6f}")
                print(f"  Total Return: {best['total_return']:.6f}")
                print(f"  Annual Return: {best['annual_return']:.6f}")
                print(f"  Max Drawdown: {best['max_drawdown']:.6f}")
                print(f"  Calmar Ratio: {best['calmar_ratio']:.6f}")
                print(f"  Win Rate: {best['win_rate']:.4f}")
                print(f"  Total Trades: {best['total_trades']}")
                print(f"  Volatility: {best['volatility']:.6f}")
                print(f"  Parameters: {best['parameters']}")

            # Show top 5 results by Sharpe
            trading_results = sorted(strategy_results['trading_results'], key=lambda x: x['sharpe_ratio'], reverse=True)
            if trading_results:
                print(f"\nTop 5 Configurations by Sharpe Ratio:")
                for i, result in enumerate(trading_results[:5], 1):
                    print(f"  {i}. Sharpe: {result['sharpe_ratio']:.6f} | Return: {result['total_return']:.6f} | "
                          f"Trades: {result['total_trades']:2d} | Win%: {result['win_rate']:.3f}")

        # Overall best strategies comparison
        print(f"\n" + "=" * 80)
        print("OVERALL BEST STRATEGIES COMPARISON")
        print("=" * 80)

        all_best_configs = []
        for strategy_name, strategy_results in self.results.items():
            if strategy_results['best_sharpe']:
                config = strategy_results['best_sharpe'].copy()
                config['strategy'] = strategy_name
                all_best_configs.append(config)

        if all_best_configs:
            # Sort by Sharpe ratio
            sorted_configs = sorted(all_best_configs, key=lambda x: x['sharpe_ratio'], reverse=True)

            print(f"\nAll Strategies Ranked by Sharpe Ratio:")
            print(f"{'Rank':<4} {'Strategy':<20} {'Sharpe':<10} {'Return':<10} {'Trades':<8} {'Win%':<8}")
            print("-" * 70)

            for i, config in enumerate(sorted_configs, 1):
                print(f"{i:<4} {config['strategy'].replace('_', ' '):<20} {config['sharpe_ratio']:<10.6f} "
                      f"{config['total_return']:<10.6f} {config['total_trades']:<8} {config['win_rate']:<8.3f}")

        return strategy_summary

    def save_comprehensive_results(self):
        """Save all optimization results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save complete results
        results_file = f"complete_cbsc_strategies_optimization_{timestamp}.json"

        try:
            # Prepare data for JSON serialization
            json_results = {}
            for strategy_name, strategy_results in self.results.items():
                json_results[strategy_name] = {
                    'metadata': {
                        'total_combinations_tested': strategy_results['total_combinations_tested'],
                        'combinations_with_trades': strategy_results['combinations_with_trades']
                    },
                    'best_results': {
                        'best_sharpe': strategy_results['best_sharpe'],
                        'best_return': strategy_results['best_return'],
                        'best_calmar': strategy_results['best_calmar'],
                        'most_trades': strategy_results['most_trades']
                    },
                    'top_10_results': sorted(
                        [r for r in strategy_results['trading_results'] if r['total_trades'] > 0],
                        key=lambda x: x['sharpe_ratio'],
                        reverse=True
                    )[:10] if strategy_results['trading_results'] else []
                }

            complete_data = {
                'optimization_metadata': {
                    'timestamp': timestamp,
                    'data_period': f"{self.optimization_data['Date'].min().strftime('%Y-%m-%d')} to {self.optimization_data['Date'].max().strftime('%Y-%m-%d')}",
                    'total_trading_days': len(self.optimization_data),
                    'strategies_tested': len(self.results)
                },
                'strategy_results': json_results
            }

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"\nComplete results saved to: {results_file}")

            # Save summary report
            report_file = f"complete_cbsc_strategies_report_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("Complete CBSC Strategies Parameter Optimization Report\n")
                f.write(f"Generated: {timestamp}\n")
                f.write("=" * 60 + "\n\n")

                f.write("Optimization Overview:\n")
                f.write(f"  Data Period: {complete_data['optimization_metadata']['data_period']}\n")
                f.write(f"  Trading Days: {complete_data['optimization_metadata']['total_trading_days']}\n")
                f.write(f"  Strategies Tested: {complete_data['optimization_metadata']['strategies_tested']}\n\n")

                f.write("Strategy Performance Summary:\n")
                f.write("-" * 40 + "\n")

                for strategy_name, strategy_data in json_results.items():
                    f.write(f"\n{strategy_name.replace('_', ' ').upper()}:\n")
                    f.write(f"  Total Combinations Tested: {strategy_data['metadata']['total_combinations_tested']:,}\n")
                    f.write(f"  Combinations with Trades: {strategy_data['metadata']['combinations_with_trades']:,}\n")

                    if strategy_data['best_results']['best_sharpe']:
                        best = strategy_data['best_results']['best_sharpe']
                        f.write(f"  Best Sharpe: {best['sharpe_ratio']:.6f}\n")
                        f.write(f"  Best Return: {best['total_return']:.6f}\n")
                        f.write(f"  Best Parameters: {best['parameters']}\n")

            print(f"Summary report saved to: {report_file}")

        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    """Main execution function"""
    print("Complete CBSC Strategies Parameter Optimizer")
    print("Optimizing all 4 CBSC strategies with comprehensive parameter testing")
    print("=" * 80)

    optimizer = CompleteCBSCStrategiesOptimizer()

    try:
        # Run complete optimization for all strategies
        results = optimizer.run_complete_optimization()

        if results:
            # Analyze all results
            strategy_summary = optimizer.analyze_all_results()

            # Save comprehensive results
            optimizer.save_comprehensive_results()

            print(f"\n" + "=" * 80)
            print("OPTIMIZATION COMPLETE!")
            print("=" * 80)
            print("All 4 CBSC strategies have been optimized with comprehensive parameter testing.")
            print("Detailed results and reports have been generated.")
        else:
            print("Optimization failed")

    except Exception as e:
        print(f"Execution error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()