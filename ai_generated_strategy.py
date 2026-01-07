# Cell 1
# Cell 1: Imports and setup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
plt.style.use('fivethirtyeight')

# Cell 2
# Cell 2: Data fetching function
def fetch_data(symbol, start, end):
    """
    Fetch historical stock data using Yahoo Finance API
    """
    try:
        data = yf.download(symbol, start=start, end=end)
        if data.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# Cell 3
# Cell 3: Strategy parameters definition
def define_parameters():
    """
    Define parameters for the Bollinger Bands strategy
    """
    params = {
        'window': 20,  # Bollinger Bands window period
        'num_std': 2,  # Number of standard deviations for bands
        'risk_per_trade': 0.02,  # Risk per trade (2% of capital)
        'max_positions': 5,  # Maximum number of simultaneous positions
        'stop_loss': 0.03,  # Stop loss at 3%
        'take_profit': 0.06  # Take profit at 6%
    }
    return params

# Cell 4
# Cell 4: Signal generation logic
def calculate_bollinger_bands(data, window=20, num_std=2):
    """
    Calculate Bollinger Bands
    """
    data['MA'] = data['Adj Close'].rolling(window=window).mean()
    data['STD'] = data['Adj Close'].rolling(window=window).std()
    data['Upper Band'] = data['MA'] + (data['STD'] * num_std)
    data['Lower Band'] = data['MA'] - (data['STD'] * num_std)
    return data

def generate_signals(data):
    """
    Generate buy/sell signals based on Bollinger Bands
    """
    data['Signal'] = 0
    # Buy signal when price crosses below lower band
    data.loc[data['Adj Close'] < data['Lower Band'], 'Signal'] = 1
    # Sell signal when price crosses above upper band
    data.loc[data['Adj Close'] > data['Upper Band'], 'Signal'] = -1
    
    # Generate entry and exit points
    data['Position'] = data['Signal'].replace(0, method='ffill')
    return data

# Cell 5
# Cell 5: Simple backtesting
def backtest_strategy(data, params):
    """
    Backtest the Bollinger Bands strategy
    """
    # Initialize variables
    initial_capital = 100000
    capital = initial_capital
    positions = 0
    trades = []
    
    # Calculate position sizes based on risk management
    position_size = capital * params['risk_per_trade'] / params['stop_loss']
    
    for i in range(1, len(data)):
        current_price = data['Adj Close'].iloc[i]
        prev_signal = data['Signal'].iloc[i-1]
        current_signal = data['Signal'].iloc[i]
        
        # Check for entry signal (buy)
        if current_signal == 1 and positions < params['max_positions']:
            # Check if we have enough capital
            if capital >= position_size:
                positions += 1
                capital -= position_size
                trades.append({
                    'Date': data.index[i],
                    'Type': 'Buy',
                    'Price': current_price,
                    'Position': position_size
                })
                
                # Set stop loss and take profit levels
                stop_loss = current_price * (1 - params['stop_loss'])
                take_profit = current_price * (1 + params['take_profit'])
                
                trades[-1]['Stop Loss'] = stop_loss
                trades[-1]['Take Profit'] = take_profit
        
        # Check for exit signal (sell) or stop/take profit
        elif (current_signal == -1 or 
              (positions > 0 and 
               (current_price <= trades[-1]['Stop Loss'] or 
                current_price >= trades[-1]['Take Profit']))) and positions > 0:
            
            # Calculate profit/loss
            profit = (current_price - trades[-1]['Price']) / trades[-1]['Price'] * position_size
            capital += position_size + profit
            
            trades.append({
                'Date': data.index[i],
                'Type': 'Sell',
                'Price': current_price,
                'Position': position_size,
                'Profit': profit
            })
            
            positions -= 1
    
    # Calculate final portfolio value
    final_value = capital + positions * position_size
    
    # Create a DataFrame of trades
    trades_df = pd.DataFrame(trades)
    
    # Calculate performance metrics
    if len(trades_df) > 0:
        winning_trades = trades_df[trades_df['Profit'] > 0]
        losing_trades = trades_df[trades_df['Profit'] <= 0]
        
        win_rate = len(winning_trades) / (len(trades_df) / 2)  # Divide by 2 because each trade has buy and sell
        avg_win = winning_trades['Profit'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['Profit'].mean() if len(losing_trades) > 0 else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        performance = {
            'Initial Capital': initial_capital,
            'Final Value': final_value,
            'Total Return': (final_value - initial_capital) / initial_capital * 100,
            'Win Rate': win_rate * 100,
            'Average Win': avg_win,
            'Average Loss': avg_loss,
            'Profit Factor': profit_factor,
            'Total Trades': len(trades_df) / 2
        }
    else:
        performance = {
            'Initial Capital': initial_capital,
            'Final Value': initial_capital,
            'Total Return': 0,
            'Win Rate': 0,
            'Average Win': 0,
            'Average Loss': 0,
            'Profit Factor': 0,
            'Total Trades': 0
        }
    
    return trades_df, performance
