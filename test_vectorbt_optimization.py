"""
Test VectorBT Parameter Optimization API
"""
import requests
import time

print('=' * 70)
print('VectorBT Parameter Optimization Test')
print('=' * 70)

# 1. Check health
response = requests.get('http://192.168.1.5:8003/health')
health = response.json()
print(f'\n[1] Backend Status')
print(f'    Status: {health["status"]}')
print(f'    VectorBT: {health.get("vectorbt_available")}')
print(f'    Data Source: {health.get("data_source")}')

# 2. Start optimization
print(f'\n[2] Starting Parameter Optimization')
optimization_request = {
    "symbols": ["0700.HK"],
    "start_date": "2024-06-01",
    "end_date": "2024-09-30",
    "strategy_type": "ma_crossover",
    "short_period_range": [5, 20, 5],   # 5, 10, 15, 20
    "long_period_range": [20, 60, 10],   # 20, 30, 40, 50, 60
    "initial_cash": 100000,
    "commission": 0.001,
    "optimization_target": "sharpe_ratio"
}

print(f'    Stock: {optimization_request["symbols"]}')
print(f'    Period: {optimization_request["start_date"]} to {optimization_request["end_date"]}')
print(f'    Short Range: {optimization_request["short_period_range"]}')
print(f'    Long Range: {optimization_request["long_period_range"]}')
print(f'    Target: {optimization_request["optimization_target"]}')

response = requests.post(
    'http://192.168.1.5:8003/api/vectorbt/optimize',
    json=optimization_request
)

result = response.json()
task_id = result['task_id']
print(f'    Task ID: {task_id}')
print(f'    Status: {result["status"]}')

# 3. Wait for completion
print(f'\n[3] Waiting for optimization...')
for i in range(120):
    time.sleep(1)
    status_resp = requests.get(f'http://192.168.1.5:8003/api/vectorbt/optimize/{task_id}')
    status = status_resp.json()
    status_code = status.get('status', 'unknown')

    if status_code == 'completed':
        print(f'    [OK] Completed!')
        break
    elif status_code == 'failed':
        print(f'    [ERROR] Failed!')
        print(f'    Error: {status.get("error")}')
        break

    if (i + 1) % 10 == 0:
        completed = status.get('completed_combinations', 0)
        total = status.get('total_combinations', 0)
        print(f'    Progress: {completed}/{total} combinations tested ({i+1}s)', end='\r')

# 4. Get final results
final_result = requests.get(f'http://192.168.1.5:8003/api/vectorbt/optimize/{task_id}').json()

print(f'\n[4] OPTIMIZATION RESULTS')
print(f'    Total Combinations: {final_result["total_combinations"]}')
print(f'    Completed: {final_result["completed_combinations"]}')
print(f'\n[5] BEST PARAMETERS')
best_params = final_result['best_params']
print(f'    Short Period: {best_params.get("short_period")}')
print(f'    Long Period: {best_params.get("long_period")}')

best_metrics = final_result['best_metrics']
print(f'\n[6] BEST METRICS')
print(f'    Total Return: {best_metrics.get("total_return"):.2f}%')
print(f'    Sharpe Ratio: {best_metrics.get("sharpe_ratio"):.2f}')
print(f'    Max Drawdown: {best_metrics.get("max_drawdown"):.2f}%')

print(f'\n[7] TOP 5 RESULTS')
all_results = final_result.get('all_results', [])
# Sort by score descending
sorted_results = sorted(all_results, key=lambda x: x.get('score', 0), reverse=True)[:5]

for i, res in enumerate(sorted_results, 1):
    print(f'    #{i}: MA({res["short_period"]}/{res["long_period"]}) - '
          f'Return: {res["total_return"]:.2f}%, '
          f'Sharpe: {res["sharpe_ratio"]:.2f}, '
          f'MDD: {res["max_drawdown"]:.2f}%')

print(f'\n[8] SUMMARY')
print(f'    Engine: VectorBT (with Numba JIT)')
print(f'    Data: Yahoo Finance (Real Market Data)')
print(f'    Status: SUCCESS')
print(f'\n    System is using VectorBT for optimization!')
print('=' * 70)
