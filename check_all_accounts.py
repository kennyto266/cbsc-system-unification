#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check All Account Types - 检查所有账户类型
"""

import os
import sys
import asyncio
from datetime import datetime

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Add Futu SDK path
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# Connection configuration
API_PORT = 1130
HOST = '127.0.0.1'

async def check_all_accounts():
    """Check all available account types"""
    print("=== Check All Account Types ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        import futu as ft

        # Test connection
        print("\n1. Setting up trading connection...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("   SUCCESS: Trading connection established")

        # Check all account types
        account_types = [
            (ft.TrdEnv.SIMULATE, "Simulation"),
            (ft.TrdEnv.REAL, "Real"),
        ]

        for env, env_name in account_types:
            print(f"\n2. Checking {env_name} account...")
            ret, data = trade_ctx.accinfo_query(trd_env=env)

            print(f"   Return Code: {ret}")

            if ret == ft.RET_OK and data.shape[0] > 0:
                print(f"   SUCCESS: {env_name} account available")
                print(f"   Found {data.shape[0]} {env_name.lower()} account(s)")

                # Display first account details
                first_row = data.iloc[0]
                try:
                    acc_id = first_row.get('acc_id', 'N/A')
                    currency = first_row.get('currency', 'N/A')
                    cash = first_row.get('cash', 0)
                    total_assets = first_row.get('total_assets', 0)

                    print(f"   First Account ID: {acc_id}")
                    print(f"   Currency: {currency}")
                    print(f"   Cash: {cash:,.2f}")
                    print(f"   Total Assets: {total_assets:,.2f}")

                except Exception as e:
                    print(f"   Error reading account details: {e}")

                # Try to get more detailed account info
                try:
                    print(f"   Account columns: {list(data.columns)}")
                    for idx, row in data.iterrows():
                        print(f"   Account {idx + 1}:")
                        for col in data.columns:
                            val = row[col]
                            if val is not None and str(val) != 'nan':
                                print(f"     {col}: {val}")
                        if idx >= 0:  # Show only first account details
                            break
                except Exception as e:
                    print(f"   Error showing details: {e}")

            else:
                print(f"   FAILED: {env_name} account not available")
                print(f"   Error Code: {ret}")
                if isinstance(data, str):
                    try:
                        print(f"   Error: {str(data)[:50]}...")
                    except:
                        print(f"   Error data (type: {type(data)})")

        # Try checking trade days
        print(f"\n3. Checking trade days...")
        try:
            ret, trade_days = trade_ctx.get_global_state()
            if ret == ft.RET_OK:
                print(f"   Market is open: {trade_days}")
            else:
                print(f"   Failed to get market state: {ret}")
        except Exception as e:
            print(f"   Error checking market state: {e}")

        # Try to unlock trading with different passwords
        print(f"\n4. Testing trade unlock...")
        passwords = ["", "123456", "000000", "111111"]

        for pwd in passwords:
            try:
                print(f"   Trying password: '{pwd}'")
                ret, unlock_data = trade_ctx.unlock_trade(password=pwd)
                if ret == ft.RET_OK:
                    print(f"   SUCCESS: Trading unlocked with password '{pwd}'")
                    break
                else:
                    print(f"   Failed: {unlock_data}")
            except Exception as e:
                print(f"   Error with password '{pwd}': {e}")

        trade_ctx.close()

    except Exception as e:
        print(f"Check failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Check Complete ===")

async def main():
    """Main function"""
    await check_all_accounts()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Check execution failed: {e}")