#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Demo Account Check - English version to avoid encoding issues
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

async def check_demo_accounts():
    """Check demo accounts"""
    print("=== Futu Demo Account Check ===")

    try:
        import futu as ft
        print(f"Futu API Version: {ft.__version__}")

        # Create trade context
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Query demo accounts
        print("Querying demo accounts...")
        ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

        print(f"Return code: {ret}")
        print(f"Data type: {type(data)}")

        if ret == ft.RET_OK and data is not None:
            print(f"Data rows: {len(data)}")

            if len(data) > 0:
                print("\n=== Demo Account Information ===")

                for index, row in data.iterrows():
                    print(f"\nAccount {index + 1}:")
                    print(f"  Account ID: {row.get('acc_id', 'N/A')}")
                    print(f"  Account Type: {row.get('acc_type', 'N/A')}")
                    print(f"  Currency: {row.get('currency', 'N/A')}")
                    print(f"  Cash: {row.get('cash', 0):,.2f}")
                    print(f"  Total Assets: {row.get('total_assets', 0):,.2f}")
                    print(f"  Market Value: {row.get('market_val', 0):,.2f}")
                    print(f"  Buying Power: {row.get('power', 0):,.2f}")
                    print(f"  Max Withdraw: {row.get('max_withdraw', 0):,.2f}")
                    print(f"  Financing: {row.get('finance', 0):,.2f}")
                    print(f"  Interest: {row.get('interest', 0):,.2f}")
                    print(f"  Trade Password Required: {row.get('trade_pwd_required', False)}")
                    print(f"  Delay Trading: {row.get('aid_delay_trd', False)}")
                    print(f"  AID Account: {row.get('aid_acc_num', 'N/A')}")

                    # Save detailed account info
                    account_details = {
                        'acc_id': str(row.get('acc_id', '')),
                        'acc_type': str(row.get('acc_type', '')),
                        'currency': str(row.get('currency', '')),
                        'cash': float(row.get('cash', 0)),
                        'total_assets': float(row.get('total_assets', 0)),
                        'market_val': float(row.get('market_val', 0)),
                        'power': float(row.get('power', 0)),
                        'max_withdraw': float(row.get('max_withdraw', 0)),
                        'finance': float(row.get('finance', 0)),
                        'interest': float(row.get('interest', 0)),
                        'trade_pwd_required': bool(row.get('trade_pwd_required', False)),
                        'aid_delay_trd': bool(row.get('aid_delay_trd', False)),
                        'aid_acc_num': str(row.get('aid_acc_num', ''))
                    }

                    # Save to JSON
                    with open(f'demo_account_{index+1}_info.json', 'w', encoding='utf-8') as f:
                        json.dump(account_details, f, indent=2, ensure_ascii=False)

                    print(f"  [INFO] Account details saved to: demo_account_{index+1}_info.json")
            else:
                print("No demo accounts found")
        else:
            print(f"Query failed with return code: {ret}")
            if data:
                print(f"Error info: {data}")

        # Close connection
        trade_ctx.close()
        print("\nConnection closed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

async def check_positions():
    """Check positions"""
    print("\n=== Checking Positions ===")

    try:
        import futu as ft

        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Query positions (without specifying acc_id first)
        print("Querying positions...")
        ret, data = trade_ctx.position_list_query(trd_env=ft.TrdEnv.SIMULATE)

        print(f"Position query return code: {ret}")

        if ret == ft.RET_OK and data is not None and len(data) > 0:
            print(f"Found {len(data)} positions:")

            for index, row in data.iterrows():
                print(f"\nPosition {index + 1}:")
                print(f"  Stock Code: {row.get('code', 'N/A')}")
                print(f"  Stock Name: {row.get('security_name', 'N/A')}")
                print(f"  Quantity: {row.get('qty', 0):,.0f}")
                print(f"  Cost Price: {row.get('cost_price', 0):.4f}")
                print(f"  Market Value: {row.get('market_val', 0):,.2f}")
                print(f"  Unrealized P&L: {row.get('unrealized_pl', 0):,.2f}")
                print(f"  Unrealized P&L %: {row.get('unrealized_pl_ratio', 0)*100:.2f}%")
                print(f"  Realized P&L: {row.get('realized_pl', 0):,.2f}")
                print(f"  Position Side: {row.get('position_side', 'N/A')}")
        else:
            print("No positions found or query failed")

        trade_ctx.close()

    except Exception as e:
        print(f"Position check error: {e}")

async def main():
    """Main function"""
    print("Futu Demo Account Information Checker")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    await check_demo_accounts()
    await check_positions()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()