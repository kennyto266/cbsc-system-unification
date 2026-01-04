#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test All Account Types - Based on official documentation
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Add Futu SDK path
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# Connection configuration
API_PORT = 1130
HOST = '127.0.0.1'

async def test_all_account_environments():
    """Test all possible trading environments"""
    print("=== Testing All Trading Environments ===")

    try:
        import futu as ft
        print(f"Futu API Version: {ft.__version__}")
        print(f"Available environments: REAL, SIMULATE")

        # Create trade context
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Method 1: No environment specified (default)
        print("\n--- Method 1: Default Query ---")
        try:
            ret, data = trade_ctx.accinfo_query()
            print(f"Return code: {ret}")
            print(f"Data type: {type(data)}")

            if ret == ft.RET_OK and data is not None:
                if hasattr(data, 'shape'):
                    print(f"Data shape: {data.shape}")
                    if data.shape[0] > 0:
                        print("Account details:")
                        for col in data.columns[:10]:  # Show first 10 columns
                            print(f"  {col}: {data[col].iloc[0]}")
                elif isinstance(data, dict):
                    print("Account data (dict):")
                    for key, value in list(data.items())[:10]:
                        print(f"  {key}: {value}")
                else:
                    print(f"Account data: {data}")
            else:
                print(f"Default query failed: {data}")
        except Exception as e:
            print(f"Default query error: {e}")

        # Method 2: SIMULATE environment
        print("\n--- Method 2: SIMULATE Environment ---")
        try:
            ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
            print(f"Return code: {ret}")

            if ret == ft.RET_OK:
                print("[SUCCESS] SIMULATE accounts available!")
                if hasattr(data, 'shape') and data.shape[0] > 0:
                    print(f"Found {data.shape[0]} simulation accounts")
                    # Save simulation account info
                    sim_accounts = []
                    for i in range(data.shape[0]):
                        account_info = {}
                        for col in data.columns:
                            account_info[col] = data[col].iloc[i]
                        sim_accounts.append(account_info)

                    with open('simulation_accounts.json', 'w', encoding='utf-8') as f:
                        json.dump(sim_accounts, f, indent=2, ensure_ascii=False)
                    print(f"Simulation account details saved to: simulation_accounts.json")
            else:
                print(f"SIMULATE query failed: {data}")

                # Provide specific guidance based on error
                if isinstance(data, str):
                    if "模擬" in data or "模拟" in data:
                        print("[GUIDANCE] Error mentions simulation - may need to activate in app")
                    elif "權限" in data or "权限" in data:
                        print("[GUIDANCE] Permission issue - check account permissions")
                    else:
                        print(f"[GUIDANCE] Error message: {data[:100]}...")
        except Exception as e:
            print(f"SIMULATE query error: {e}")

        # Method 3: REAL environment (just to check)
        print("\n--- Method 3: REAL Environment ---")
        try:
            ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)
            print(f"Return code: {ret}")

            if ret == ft.RET_OK:
                print("[INFO] REAL accounts available")
                if hasattr(data, 'shape'):
                    print(f"Real account count: {data.shape[0]}")
            else:
                print(f"REAL query not available: {data}")
        except Exception as e:
            print(f"REAL query error: {e}")

        # Method 4: Try different markets
        print("\n--- Method 4: Market-specific Queries ---")
        markets_to_test = ['HK', 'US', 'CN', 'SG', 'JP']

        for market in markets_to_test:
            try:
                print(f"Testing {market} market...")
                # Try with stock-specific context
                if market == 'HK':
                    ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
                elif market == 'US':
                    ctx = ft.OpenUSTradeContext(host=HOST, port=API_PORT)
                elif market == 'CN':
                    ctx = ft.OpenCNTradeContext(host=HOST, port=API_PORT)
                elif market == 'SG':
                    ctx = ft.OpenSGTradeContext(host=HOST, port=API_PORT)
                elif market == 'JP':
                    ctx = ft.OpenJPTradeContext(host=HOST, port=API_PORT)

                ret, data = ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                print(f"  {market} SIMULATE return code: {ret}")

                if ret == ft.RET_OK:
                    print(f"  [SUCCESS] {market} simulation accounts available!")

                ctx.close()

            except Exception as e:
                print(f"  {market} market error: {str(e)[:50]}...")

            await asyncio.sleep(0.1)  # Small delay between requests

        trade_ctx.close()

        print("\n=== Recommendations ===")
        print("Based on the test results:")
        print("1. If SIMULATE still fails, you need to:")
        print("   - Open Futu NiuNiu app")
        print("   - Go to Trading > Simulation Trading")
        print("   - Click 'Generate Now' to create simulation accounts")
        print("2. Alternative approach:")
        print("   - Continue with market data analysis")
        print("   - Build strategy frameworks")
        print("   - Test with historical data")
        print("3. Once simulation is activated:")
        print("   - Re-run this test script")
        print("   - Verify account access")
        print("   - Start paper trading")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    print("Comprehensive Futu Account Type Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    await test_all_account_environments()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()