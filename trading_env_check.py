#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Environment Check - Check what trading environments are available
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

async def check_trading_environments():
    """Check available trading environments"""
    print("=== Trading Environment Check ===")

    try:
        import futu as ft
        print(f"Futu API Version: {ft.__version__}")
        print(f"Available trading environments:")
        print(f"  REAL: {ft.TrdEnv.REAL}")
        print(f"  SIMULATE: {ft.TrdEnv.SIMULATE}")
        print(f"  PAPER: {ft.TrdEnv.PAPER}")

        # Create trade context
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Try different environments
        environments = [
            ("REAL", ft.TrdEnv.REAL),
            ("SIMULATE", ft.TrdEnv.SIMULATE),
            ("PAPER", ft.TrdEnv.PAPER)
        ]

        for env_name, env_value in environments:
            print(f"\n--- Testing {env_name} Environment ---")
            try:
                ret, data = trade_ctx.accinfo_query(trd_env=env_value)
                print(f"Return code: {ret}")

                if ret == ft.RET_OK and data is not None and len(data) > 0:
                    print(f"[SUCCESS] {env_name} environment has {len(data)} account(s)")

                    for index, row in data.iterrows():
                        print(f"  Account {index + 1}: ID={row.get('acc_id', 'N/A')}, "
                              f"Type={row.get('acc_type', 'N/A')}, "
                              f"Assets={row.get('total_assets', 0):,.2f}")
                else:
                    print(f"[INFO] {env_name} environment not available or no accounts")
                    if isinstance(data, str):
                        print(f"  Error message: {data[:100]}...")

            except Exception as e:
                print(f"[ERROR] Failed to check {env_name}: {str(e)[:100]}...")

        trade_ctx.close()

    except Exception as e:
        print(f"Error: {e}")

async def check_user_info():
    """Check user information"""
    print("\n=== User Information Check ===")

    try:
        import futu as ft

        # Create quote context
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        # Get user info
        ret, data = quote_ctx.get_user_info()

        if ret == ft.RET_OK and data is not None and len(data) > 0:
            print("[SUCCESS] User information retrieved:")

            for index, row in data.iterrows():
                print(f"\nUser {index + 1}:")
                print(f"  User ID: {row.get('user_id', 'N/A')}")
                print(f"  Login Status: {row.get('login_status', 'N/A')}")
                print(f"  Name: {row.get('name', 'N/A')}")
                print(f"  Account Type: {row.get('account_type', 'N/A')}")
                print(f"  Nickname: {row.get('nickname', 'N/A')}")

                # Save user info
                user_info = {
                    'user_id': str(row.get('user_id', '')),
                    'login_status': str(row.get('login_status', '')),
                    'name': str(row.get('name', '')),
                    'account_type': str(row.get('account_type', '')),
                    'nickname': str(row.get('nickname', ''))
                }

                with open('user_info.json', 'w', encoding='utf-8') as f:
                    json.dump(user_info, f, indent=2, ensure_ascii=False)

                print(f"  [INFO] User info saved to: user_info.json")
        else:
            print(f"[FAILED] User info query failed: {ret}")

        quote_ctx.close()

    except Exception as e:
        print(f"User info check error: {e}")

async def check_global_state():
    """Check global state for more details"""
    print("\n=== Global State Check ===")

    try:
        import futu as ft

        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        ret, data = quote_ctx.get_global_state()

        if ret == ft.RET_OK:
            print("[SUCCESS] Global state retrieved:")
            print(f"  Server Version: {data.get('server_ver', 'N/A')}")
            print(f"  Trading Login: {data.get('trd_logined', False)}")
            print(f"  Quote Login: {data.get('qot_logined', False)}")
            print(f"  Program Status: {data.get('program_status_desc', 'N/A')}")
            print(f"  Market Status:")
            print(f"    Hong Kong: {data.get('market_hk', 'N/A')}")
            print(f"    US: {data.get('market_us', 'N/A')}")
            print(f"    China A: {data.get('market_sz', 'N/A')}")
            print(f"    Shanghai: {data.get('market_sh', 'N/A')}")

            # Save global state
            with open('global_state.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"  [INFO] Global state saved to: global_state.json")
        else:
            print(f"[FAILED] Global state query failed: {ret}")

        quote_ctx.close()

    except Exception as e:
        print(f"Global state check error: {e}")

async def main():
    """Main function"""
    print("Futu Trading Environment Checker")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    await check_user_info()
    await check_global_state()
    await check_trading_environments()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()