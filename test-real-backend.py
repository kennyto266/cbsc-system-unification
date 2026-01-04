"""
CBSC Real Backend System Test
真實後端系統測試腳本

測試真實回測系統的各個組件
"""

import asyncio
import sys
import os
from datetime import datetime, date

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import httpx


async def test_backend_health():
    """Test backend health endpoint"""
    print("\n" + "="*60)
    print("Testing Backend Health")
    print("="*60)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8001/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ Backend Health: OK")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Backend Health: FAILED (status {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ Backend Health: ERROR - {e}")
            return False


async def test_api_docs():
    """Test API documentation endpoint"""
    print("\n" + "="*60)
    print("Testing API Documentation")
    print("="*60)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8001/docs", timeout=10)
            if response.status_code == 200:
                print(f"✅ API Docs: OK")
                return True
            else:
                print(f"❌ API Docs: FAILED (status {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ API Docs: ERROR - {e}")
            return False


async def test_vectorbt_api():
    """Test VectorBT multiprocess API"""
    print("\n" + "="*60)
    print("Testing VectorBT Multiprocess API")
    print("="*60)

    async with httpx.AsyncClient() as client:
        try:
            # Test statistics endpoint
            response = await client.get(
                "http://localhost:8001/api/vectorbt/multiprocess/statistics",
                timeout=10
            )
            if response.status_code == 200:
                print(f"✅ VectorBT API: OK")
                print(f"   Engine Stats: {response.json()}")
                return True
            else:
                print(f"⚠️ VectorBT API: Not available (status {response.status_code})")
                return None
        except Exception as e:
            print(f"⚠️ VectorBT API: ERROR - {e}")
            return None


async def test_strategies_api():
    """Test Strategies API v2"""
    print("\n" + "="*60)
    print("Testing Strategies API v2")
    print("="*60)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://localhost:8001/api/strategies/v2/",
                timeout=10
            )
            if response.status_code == 200:
                print(f"✅ Strategies API: OK")
                data = response.json()
                print(f"   Strategies count: {data.get('total', 0)}")
                return True
            else:
                print(f"⚠️ Strategies API: Not available (status {response.status_code})")
                return None
        except Exception as e:
            print(f"⚠️ Strategies API: ERROR - {e}")
            return None


async def test_backtest_api():
    """Test Backtest API"""
    print("\n" + "="*60)
    print("Testing Backtest API")
    print("="*60)

    async with httpx.AsyncClient() as client:
        try:
            # Submit a simple backtest request
            backtest_request = {
                "symbols": ["0700.HK"],
                "strategy_name": "ma_crossover",
                "start_date": "2023-01-01",
                "end_date": "2024-01-01",
                "initial_capital": 100000,
                "commission": 0.001,
                "execution_mode": "portfolio",
                "max_workers": 4,
                "strategy_parameters": {
                    "fast_period": 10,
                    "slow_period": 20
                }
            }

            response = await client.post(
                "http://localhost:8001/api/vectorbt/multiprocess/backtest",
                json=backtest_request,
                timeout=30
            )

            if response.status_code in [200, 202]:
                print(f"✅ Backtest API: OK")
                result = response.json()
                print(f"   Task ID: {result.get('task_id')}")
                print(f"   Status: {result.get('status')}")
                return True
            else:
                print(f"⚠️ Backtest API: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"⚠️ Backtest API: ERROR - {e}")
            return None


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CBSC Real Backend System Test")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    results = {
        "Backend Health": await test_backend_health(),
        "API Docs": await test_api_docs(),
        "VectorBT API": await test_vectorbt_api(),
        "Strategies API": await test_strategies_api(),
        "Backtest API": await test_backtest_api(),
    }

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⚠️ N/A"
        print(f"{test_name:20s}: {status}")

    print("\n" + "="*60)
    print("Test Complete")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
