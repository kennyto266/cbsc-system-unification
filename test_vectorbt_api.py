#!/usr/bin/env python
"""Test VectorBT API"""
import requests
import json
import time

# Test health endpoint
print("=== Testing VectorBT API ===")
print("\n1. Health Check:")
response = requests.get("http://localhost:8001/api/vectorbt/health")
print(json.dumps(response.json(), indent=2))

# Test strategies endpoint
print("\n2. List Strategies:")
response = requests.get("http://localhost:8001/api/vectorbt/strategies")
print(json.dumps(response.json(), indent=2))

# Test backtest endpoint
print("\n3. Start Backtest:")
backtest_request = {
    "symbols": ["0700.HK", "0941.HK"],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategy_type": "ma_crossover",
    "short_period": 10,
    "long_period": 30
}

response = requests.post(
    "http://localhost:8001/api/vectorbt/backtest",
    json=backtest_request
)
result = response.json()
print(json.dumps(result, indent=2))

# Get task status
if 'task_id' in result:
    task_id = result['task_id']
    print(f"\n4. Check Task Status (task_id: {task_id}):")

    # Wait a bit for the task to complete
    time.sleep(5)

    response = requests.get(f"http://localhost:8001/api/vectorbt/status/{task_id}")
    print(json.dumps(response.json(), indent=2))

    # Get results
    print(f"\n5. Get Results:")
    response = requests.get(f"http://localhost:8001/api/vectorbt/results/{task_id}")
    print(json.dumps(response.json(), indent=2))

print("\n=== Test Complete ===")
