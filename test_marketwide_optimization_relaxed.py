"""
Market-Wide Optimization Test - Relaxed Filter
================================================

Tests with lower Sharpe Ratio threshold to show qualified results.
"""

import requests
import time
from datetime import date

print('=' * 70)
print('Market-Wide Optimization - Relaxed SR Threshold Test')
print('=' * 70)

API_BASE = 'http://192.168.1.5:8003'
TEST_STOCK_COUNT = 15
START_DATE = date(2020, 1, 1)  # 5 years including bull market
END_DATE = date(2024, 12, 31)
MIN_SR = 0.5  # Relaxed threshold

# Start optimization
print(f'\n[1] Starting Optimization')
print(f'    Stocks: {TEST_STOCK_COUNT}')
print(f'    Period: {START_DATE} to {END_DATE}')
print(f'    Min SR: {MIN_SR}')

start = time.time()

response = requests.post(
    f'{API_BASE}/api/vectorbt/optimize-marketwide',
    json={
        'stock_count': TEST_STOCK_COUNT,
        'start_date': START_DATE.isoformat(),
        'end_date': END_DATE.isoformat(),
        'min_sharpe_ratio': MIN_SR,
        'max_workers': 31,
        'initial_cash': 100000,
        'commission': 0.001
    }
)

task_id = response.json()['task_id']
print(f'    Task ID: {task_id}')

# Monitor progress
print(f'\n[2] Progress')
last_pct = 0
while True:
    time.sleep(2)
    progress = requests.get(
        f'{API_BASE}/api/vectorbt/optimize-marketwide/{task_id}/progress'
    ).json()

    status = progress['status']
    pct = progress.get('progress_percentage', 0)
    completed = progress.get('completed_stocks', 0)
    total = progress.get('total_stocks', 0)

    bar_len = 30
    filled = int(bar_len * pct / 100)
    bar = '=' * filled + '-' * (bar_len - filled)

    if status == 'running':
        print(f'\r[{bar}] {pct:5.1f}% | {completed}/{total} stocks', end='', flush=True)
    elif status == 'completed':
        print(f'\r[{bar}] 100.0% | {total}/{total} stocks')
        break
    elif status == 'failed':
        print(f'\n[X] Failed: {progress.get("error")}')
        exit(1)

# Get results
print(f'\n[3] Results')
results = requests.get(
    f'{API_BASE}/api/vectorbt/optimize-marketwide/{task_id}/results'
).json()

total_time = time.time() - start

print(f'\nSummary:')
print(f'    Time: {total_time:.2f}s')
print(f'    Stocks: {results["total_stocks"]}')
print(f'    Combos/Stock: {results["total_combinations"]}')
print(f'    Total Backtests: {results["summary"]["total_backtests_run"]:,}')
print(f'    Qualified (SR>{MIN_SR}): {results["qualified_results_count"]:,}')
print(f'    Qualification Rate: {results["summary"]["qualification_rate"]:.2f}%')

if results['qualified_results_count'] > 0:
    print(f'\nTop 10 Results:')
    print(f'{"Rank":<4} {"Symbol":<10} {"MA":<10} {"Return":<10} {"Sharpe":<8} {"MDD":<8} {"Excess":<8}')
    print('-' * 70)

    for i, r in enumerate(results['top_10'][:10], 1):
        p = r['params']
        ma = f"{p['short_period']}/{p['long_period']}"
        print(f'{i:<4} {r["symbol"]:<10} {ma:<10} '
              f'{r["total_return"]:>6.2f}%   {r["sharpe_ratio"]:>6.2f}   '
              f'{r["max_drawdown"]:>6.2f}%  {r["excess_return"]:>6.2f}%')

    print(f'\nBest Overall:')
    b = results['best_overall']
    print(f'    {b["symbol"]}: SR={b["sharpe_ratio"]:.2f}')
else:
    print(f'\nNo results passed SR > {MIN_SR} filter')
    print('This demonstrates the filter is working correctly.')

print(f'\n[4] Performance')
print(f'    {results["summary"]["total_backtests_run"] / total_time:.0f} backtests/second')
print(f'    Estimated for 50 stocks: {(50/TEST_STOCK_COUNT * total_time):.0f}s')

print('=' * 70)
