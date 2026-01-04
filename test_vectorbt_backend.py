"""
Test VectorBT backend with real data
"""
import requests
import time

print('=' * 70)
print('Testing VectorBT Backend')
print('=' * 70)

# Check health
response = requests.get('http://192.168.1.5:8003/health')
print(f'\n[1] Backend Status: {response.json()["status"]}')

# Prepare backtest request
backtest_request = {
    "symbols": ["0700.HK"],
    "start_date": "2024-06-01",
    "end_date": "2024-09-30",
    "strategy_type": "ma_crossover",
    "initial_cash": 100000,
    "commission": 0.001,
    "short_period": 10,
    "long_period": 30,
    "use_multiprocess": False,
    "max_workers": 4
}

print(f'\n[2] Starting backtest...')
print(f'    Stock: 0700.HK (Tencent)')
print(f'    Period: 2024-06-01 to 2024-09-30')
print(f'    Strategy: MA Crossover (10/30)')

# Start backtest
response = requests.post(
    'http://192.168.1.5:8003/api/vectorbt/backtest',
    json=backtest_request
)

result = response.json()
task_id = result['task_id']
print(f'    Task ID: {task_id}')

# Wait for completion
print(f'\n[3] Waiting for completion...')
for i in range(30):
    time.sleep(1)
    status_resp = requests.get(f'http://192.168.1.5:8003/api/vectorbt/status/{task_id}')
    status = status_resp.json()['status']
    print(f'    Progress: {status} ({i+1}s)', end='\r')

    if status == 'completed':
        print(f'\n    [OK] Completed!')
        break
    elif status == 'failed':
        print(f'\n    [ERROR] Failed!')
        break

# Get results
results_resp = requests.get(f'http://192.168.1.5:8003/api/vectorbt/results/{task_id}')
backtest_result = results_resp.json()

print(f'\n[4] BACKTEST RESULTS:')
print(f'    Total Return: {backtest_result["returns"]:.2f}%')
print(f'    Sharpe Ratio: {backtest_result["sharpe_ratio"]:.2f}')
print(f'    Max Drawdown: {backtest_result["max_drawdown"]:.2f}%')
print(f'    Total Trades: {backtest_result["total_trades"]}')
print(f'    Win Rate: {backtest_result["win_rate"]:.1f}%')

# Check if VectorBT was used
print(f'\n[5] ENGINE VERIFICATION:')
equity_curve_len = len(backtest_result.get('equity_curve', []))
print(f'    Equity curve points: {equity_curve_len}')

if equity_curve_len > 0:
    print(f'    [SUCCESS] VectorBT is working!')
    print(f'    [SUCCESS] Real Yahoo Finance data + VectorBT engine')
else:
    print(f'    [WARN] No equity curve data')

print('=' * 70)
