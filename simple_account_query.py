#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Account Query - Check available trading accounts
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

async def check_accounts():
    """Simple account check"""
    print("=== Account Information ===")

    try:
        import futu as ft

        # Create quote context first
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        # Get user info
        ret, data = quote_ctx.get_user_info()
        print(f"User info return code: {ret}")

        if ret == ft.RET_OK:
            if isinstance(data, dict):
                print("User data format: Dict")
                for key, value in data.items():
                    print(f"  {key}: {value}")
            elif hasattr(data, 'to_dict'):
                print("User data format: DataFrame")
                user_dict = data.to_dict()
                for key, value in user_dict.items():
                    print(f"  {key}: {value}")
            else:
                print(f"User data type: {type(data)}")
                print(f"User data: {data}")

        quote_ctx.close()

        # Create trade context
        print("\n=== Trading Accounts ===")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Try simulation environment
        print("Checking SIMULATE environment...")
        ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
        print(f"SIMULATE return code: {ret}")

        if ret == ft.RET_OK:
            print("SIMULATE accounts found:")
            if isinstance(data, dict):
                print(f"Account data: {data}")
            elif hasattr(data, 'shape'):
                print(f"Data shape: {data.shape}")
                if data.shape[0] > 0:
                    print("Account details:")
                    for col in data.columns:
                        print(f"  {col}: {data[col].iloc[0] if len(data) > 0 else 'N/A'}")
                else:
                    print("No account data")
            else:
                print(f"Data type: {type(data)}")
                print(f"Data: {data}")
        else:
            print(f"SIMULATE query failed. Error: {data if isinstance(data, str) else 'Unknown'}")

        # Try real environment (just to check)
        print("\nChecking REAL environment...")
        try:
            ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)
            print(f"REAL return code: {ret}")

            if ret == ft.RET_OK:
                print("REAL accounts available")
            else:
                print(f"REAL accounts not available: {data if isinstance(data, str) else 'Unknown'}")
        except Exception as e:
            print(f"REAL environment error: {e}")

        trade_ctx.close()

        print("\n=== Recommendations ===")
        print("Based on the results:")
        print("1. If SIMULATE failed, you may need to:")
        print("   - Enable paper trading in Futu OpenD client")
        print("   - Open a demo account through the client")
        print("2. For development, you can:")
        print("   - Use market data with quote context")
        print("   - Test order placement logic (without execution)")
        print("   - Implement risk management frameworks")

    except Exception as e:
        print(f"Account check failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    print("Simple Futu Account Query")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)

    await check_accounts()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()