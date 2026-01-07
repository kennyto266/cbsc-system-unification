# Cell 1
# Cell 1: Imports and setup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta

# Set display options
pd.set_option('display.max_columns', None)
plt.style.use('seaborn-v0_8-darkgrid')

# Cell 2
# Cell 2: Data fetching function
def fetch_data(symbol, start_date, end_date):
    """
    Fetch historical stock data from Yahoo Finance
    
    Parameters:
    symbol (str): Stock ticker symbol
    start_date (str): Start date in 'YYYY-MM-DD' format
    end_date (str): End date in 'YYYY-MM-DD' format
    
    Returns:
    pd.DataFrame: DataFrame with OHLCV data
    """
    try:
        data = yf.download(symbol, start=start_date, end=end_date)
        if data.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# Cell 3
# Cell 3: Strategy parameters definition
class StrategyParameters:
    def __init__(self):
        # Time parameters
        self.short_window = 50  # Short-term moving average period
        self.long_window = 200  # Long-term moving average period
        
        # Risk management parameters
        self.stop_loss_pct = 0.03  # 3% stop loss
        self.take_profit_pct = 0.06  # 6% take profit
        
        # Position sizing
        self.max_position_size = 0.10  # Max 10% of portfolio per trade
        
        # Additional parameters
        self.commission = 0.001  # 0.1% commission per trade

# Initialize strategy parameters
params = StrategyParameters()

# Cell 4
# Cell 4: Signal generation logic
def generate_signals(data, params):
    """
    Generate trading signals based on moving average crossover
    
    Parameters:
    data (pd.DataFrame): DataFrame with OHLCV data
    params (StrategyParameters): Strategy parameters
    
    Returns:
    pd.DataFrame: DataFrame with signals
    """
    # Create a copy of the data to avoid modifying the original
    df = data.copy()
    
    # Calculate moving averages
    df['short_ma'] = df['Close'].rolling(window=params.short_window, min_periods=1).mean()
    df['long_ma'] = df['Close'].rolling(window=params.long_window, min_periods=1).mean()
    
    # Generate signals
    # 1: Buy signal (short MA crosses above long MA)
    # -1: Sell signal (short MA crosses below long MA)
    # 0: Hold
    df['signal'] = 0
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
    df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1
    
    # Generate entry and exit points
    df['position'] = df['signal'].replace(0, method='ffill').shift(1)
    
    return df

# Cell 5
# Cell 5: Simple backtesting
def backtest_strategy(data, params):
    """
    Backtest the moving average crossover strategy
    
    Parameters:
    data (pd.DataFrame): DataFrame with OHLCV data
    params (StrategyParameters): Strategy parameters
    
    Returns:
    pd.DataFrame: DataFrame with backtest results
    """
    # Generate signals
    df = generate_signals(data, params)
    
    # Initialize portfolio variables
    df['position'] = 0
    df['cash'] = 100000  # Starting with $100,000
    df['holdings'] = 0
    df['total'] = df['cash']
    df['returns'] = 0
    df['trade_log'] = []
    
    # Backtest loop
    for i in range(1, len(df)):
        current_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # Skip if no signal
        if current_row['signal'] == 0:
            # Carry forward position
            df.at[df.index[i], 'position'] = prev_row['position']
            df.at[df.index[i], 'cash'] = prev_row['cash']
            df.at[df.index[i], 'holdings'] = prev_row['holdings']
            df.at[df.index[i], 'total'] = prev_row['total']
            continue
            
        # Buy signal
        if current_row['signal'] == 1 and prev_row['position'] != 1:
            # Calculate position size (max 10% of portfolio)
            position_value = min(prev_row['total'] * params.max_position_size, prev_row['total'])
            shares = position_value / current_row['Close']
            
            # Apply commission
            commission_cost = position_value * params.commission
            
            # Update portfolio
            df.at[df.index[i], 'position'] = 1
            df.at[df.index[i], 'cash'] = prev_row['cash'] - position_value - commission_cost
            df.at[df.index[i], 'holdings'] = shares
            df.at[df.index[i], 'trade_log'] = f"BUY: {shares:.2f} shares at ${current_row['Close']:.2f}"
            
        # Sell signal
        elif current_row['signal'] == -1 and prev_row['position'] != -1:
            # Sell all holdings
            shares = prev_row['holdings']
            sell_value = shares * current_row['Close']
            
            # Apply commission
            commission_cost = sell_value * params.commission
            
            # Update portfolio
            df.at[df.index[i], 'position'] = -1
            df.at[df.index[i], 'cash'] = prev_row['cash'] + sell_value - commission_cost
            df.at[df.index[i], 'holdings'] = 0
            df.at[df.index[i], 'trade_log'] = f"SELL: {shares:.2f} shares at ${current_row['Close']:.2f}"
            
        # Calculate total portfolio value
        df.at[df.index[i], 'total'] = df.at[df.index[i], 'cash'] + df.at[df.index[i], 'holdings'] * current_row['Close']
        
        # Calculate returns
        if i > 1:
            df.at[df.index[i], 'returns'] = (df.at[df.index[i], 'total'] - prev_row['total']) / prev_row['total']
    
    # Calculate benchmark returns (buy and hold)
    df['benchmark'] = 100000 * (df['Close'] / df['Close'].iloc[0])
    
    return df
