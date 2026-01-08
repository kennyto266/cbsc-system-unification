#!/usr/bin/env python3
"""
Sample Data Importer - Generate and import test data

This script generates realistic sample data for development and testing.
"""

import os
import sys
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np
from clickhouse_driver import Client

# Import configuration
try:
    from etl_config import get_clickhouse_client
except ImportError:
    print("[ERROR] Failed to import from etl_config.py")
    print("Ensure clickhouse-driver is installed")
    sys.exit(1)


def generate_sample_backtests(n: int = 1000) -> List[Dict]:
    """Generate sample backtest results"""
    strategies = [
        'ma_crossover',
        'momentum',
        'mean_reversion',
        'breakout',
        'grid_trading'
    ]

    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMD', 'INTC', 'MRNA']

    data = []
    base_date = datetime.now() - timedelta(days=90)

    for i in range(n):
        strategy_id = f"{random.choice(strategies)}_v{random.randint(1, 5)}"
        symbol = random.choice(symbols)

        # Generate realistic metrics
        total_return = random.gauss(0.15, 0.30)  # 15% avg, 30% std
        sharpe_ratio = random.gauss(1.0, 0.5)
        max_drawdown = abs(random.gauss(-0.15, 0.10))
        win_rate = random.gauss(0.55, 0.15)
        profit_factor = random.gauss(1.5, 0.5)
        avg_trade = random.gauss(100, 200)

        # Generate parameters based on strategy
        if strategy_id.startswith('ma_crossover'):
            parameters = {
                'short_ma': random.choice([5, 10, 15, 20]),
                'long_ma': random.choice([30, 50, 100, 200])
            }
        elif strategy_id.startswith('momentum'):
            parameters = {
                'lookback_period': random.choice([10, 20, 30]),
                'threshold': random.uniform(0.01, 0.05)
            }
        elif strategy_id.startswith('mean_reversion'):
            parameters = {
                'lookback': random.choice([10, 20, 30]),
                'std_threshold': random.uniform(1.5, 3.0)
            }
        elif strategy_id.startswith('breakout'):
            parameters = {
                'period': random.choice([20, 40, 60]),
                'volume_threshold': random.uniform(1.2, 2.0)
            }
        else:  # grid_trading
            parameters = {
                'grid_spacing': random.uniform(0.005, 0.02),
                'grid_levels': random.randint(5, 15)
            }

        # Generate dates
        backtest_date = base_date + timedelta(days=random.randint(0, 90))
        start_date = backtest_date - timedelta(days=random.randint(30, 365))
        end_date = backtest_date - timedelta(days=random.randint(1, 30))

        data.append({
            'strategy_id': strategy_id,
            'backtest_date': backtest_date,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'total_return': max(min(total_return, 2.0), -0.5),
            'sharpe_ratio': max(min(sharpe_ratio, 3.0), -1.0),
            'max_drawdown': max(min(max_drawdown, 0.5), 0),
            'win_rate': max(min(win_rate, 1.0), 0),
            'profit_factor': max(profit_factor, 0.5),
            'avg_trade': avg_trade,
            'total_trades': random.randint(50, 500),
            'parameters': json.dumps(parameters),
            'created_at': backtest_date
        })

    return data


def generate_sample_performance(n: int = 500) -> List[Dict]:
    """Generate sample real-time performance data"""
    strategies = ['ma_crossover_v2', 'momentum_v1', 'mean_reversion_v3']
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

    data = []
    base_time = datetime.now() - timedelta(hours=24)

    for i in range(n):
        strategy_id = random.choice(strategies)
        symbol = random.choice(symbols)
        timestamp = base_time + timedelta(seconds=random.randint(0, 86400))

        data.append({
            'strategy_id': strategy_id,
            'timestamp': timestamp,
            'symbol': symbol,
            'current_pnl': random.gauss(500, 2000),
            'unrealized_pnl': random.gauss(200, 1000),
            'position_size': random.choice([-100, -50, 0, 50, 100]),
            'entry_price': random.uniform(100, 500),
            'current_price': random.uniform(100, 500),
            'last_signal': random.choice(['BUY', 'SELL', 'HOLD', 'CLOSE']),
            'last_signal_time': timestamp - timedelta(minutes=random.randint(1, 120))
        })

    return data


def generate_sample_market_data(n_days: int = 365) -> List[Dict]:
    """Generate sample market data"""
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

    data = []
    base_date = datetime.now() - timedelta(days=n_days)

    for symbol in symbols:
        current_price = random.uniform(100, 500)
        dates = [base_date + timedelta(days=d) for d in range(n_days)]

        for date in dates:
            # Generate daily price movement
            daily_return = random.gauss(0, 0.02)  # 2% daily volatility
            open_price = current_price * (1 + random.gauss(0, 0.005))
            close_price = current_price * (1 + daily_return)
            high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, 0.01)))
            volume = int(random.gauss(1000000, 500000))

            # Calculate VWAP
            vwap = (high_price + low_price + close_price) / 3

            data.append({
                'symbol': symbol,
                'timestamp': date,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': max(volume, 100000),
                'vwap': vwap
            })

            current_price = close_price

    return data


def generate_sample_trades(n: int = 2000) -> List[Dict]:
    """Generate sample trade records"""
    strategies = ['ma_crossover_v2', 'momentum_v1', 'mean_reversion_v3']
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

    data = []
    base_date = datetime.now() - timedelta(days=90)

    for i in range(n):
        trade_id = f"trade_{i:06d}"
        strategy_id = random.choice(strategies)
        symbol = random.choice(symbols)

        entry_time = base_date + timedelta(days=random.randint(0, 90))
        is_closed = random.random() > 0.3  # 70% of trades are closed

        entry_price = random.uniform(100, 500)
        quantity = random.choice([10, 25, 50, 100])

        if is_closed:
            exit_time = entry_time + timedelta(days=random.randint(1, 30))
            exit_price = entry_price * (1 + random.gauss(0, 0.05))
            pnl = (exit_price - entry_price) * quantity
            commission = abs(pnl) * 0.001  # 0.1% commission
        else:
            exit_time = None
            exit_price = None
            pnl = None
            commission = entry_price * quantity * 0.001

        side = random.choice(['long', 'short'])

        data.append({
            'trade_id': trade_id,
            'strategy_id': strategy_id,
            'symbol': symbol,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'side': side,
            'pnl': pnl,
            'commission': commission
        })

    return data


def import_to_clickhouse(client: Client, table: str, data: List[Dict]):
    """Import data to ClickHouse"""
    if not data:
        return

    # Get column names from first record
    columns = list(data[0].keys())

    # Prepare data for insertion - keep datetime as datetime
    insert_data = []
    for record in data:
        row = []
        for col in columns:
            value = record[col]
            if value is None:
                row.append(0)  # Replace None with 0
            else:
                row.append(value)
        insert_data.append(tuple(row))

    # Insert data (use analytics database prefix)
    query = f"INSERT INTO analytics.{table} ({', '.join(columns)}) VALUES"
    try:
        client.execute(query, insert_data)
        print(f"  [OK] Imported {len(insert_data)} records to {table}")
    except Exception as e:
        print(f"  [ERROR] Failed to import: {e}")
        raise


def main():
    """Main import flow"""
    print("="*60)
    print("Sample Data Importer")
    print("="*60)

    # Connect to ClickHouse
    print("\n[@] Connecting to ClickHouse...")
    try:
        client = get_clickhouse_client()
        client.execute('SELECT 1')
        print("[OK] Connected successfully")
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure ClickHouse is running")
        print("2. Run: python scripts/init_clickhouse.py")
        sys.exit(1)

    # Import data
    print("\n[*] Importing sample data...")

    try:
        # Import backtests
        print("\n1. Importing backtest results...")
        backtests = generate_sample_backtests(1000)
        import_to_clickhouse(client, 'strategy_backtests', backtests)

        # Import performance data
        print("\n2. Importing performance data...")
        performance = generate_sample_performance(500)
        import_to_clickhouse(client, 'strategy_performance', performance)

        # Import market data
        print("\n3. Importing market data...")
        market_data = generate_sample_market_data(365)
        import_to_clickhouse(client, 'market_data', market_data)

        # Import trades
        print("\n4. Importing trades...")
        trades = generate_sample_trades(2000)
        import_to_clickhouse(client, 'trades', trades)

        print("\n" + "="*60)
        print("[OK] Sample data import completed!")
        print("="*60)

        # Show summary
        print("\n[] Summary:")
        for table in ['strategy_backtests', 'strategy_performance', 'market_data', 'trades']:
            result = client.execute(f"SELECT COUNT(*) FROM analytics.{table}")
            print(f"  • {table}: {result[0][0]:,} rows")

    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
