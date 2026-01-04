#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account Status Checker - English only to avoid encoding issues
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

def safe_print(data, prefix=""):
    """Safe print that handles encoding issues"""
    try:
        if isinstance(data, str):
            print(f"{prefix}{data}")
        elif isinstance(data, dict):
            for key, value in data.items():
                try:
                    print(f"{prefix}{key}: {value}")
                except:
                    print(f"{prefix}{key}: [Cannot display value]")
        else:
            print(f"{prefix}{str(data)[:100]}")
    except Exception as e:
        print(f"{prefix}[Display error: {e}]")

async def check_simulation_accounts():
    """Check simulation accounts with safe output"""
    print("=== Checking Simulation Accounts ===")

    try:
        import futu as ft
        print(f"Futu API Version: {ft.__version__}")

        # Create trade contexts for different markets
        contexts = []

        # HK market
        print("\n--- Hong Kong Market ---")
        try:
            hk_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
            ret, data = hk_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

            print(f"HK SIMULATE Return Code: {ret}")

            if ret == ft.RET_OK and data is not None:
                print("[SUCCESS] HK Simulation Account Found!")

                if hasattr(data, 'shape'):
                    print(f"Data shape: {data.shape}")
                    if data.shape[0] > 0:
                        print(f"Found {data.shape[0]} HK simulation accounts")

                        # Get first account details
                        first_row = data.iloc[0]
                        account_info = {}

                        safe_cols = ['acc_id', 'acc_type', 'currency', 'cash', 'total_assets',
                                   'market_val', 'power', 'max_withdraw']

                        for col in safe_cols:
                            if col in data.columns:
                                account_info[col] = first_row[col]
                                try:
                                    print(f"  {col}: {first_row[col]}")
                                except:
                                    print(f"  {col}: [Cannot display]")

                        # Save account info
                        with open('hk_simulation_account.json', 'w', encoding='utf-8') as f:
                            json.dump(account_info, f, indent=2, ensure_ascii=False)
                        print("  [INFO] Account details saved to hk_simulation_account.json")

                # Check positions for HK
                try:
                    ret_pos, pos_data = hk_ctx.position_list_query(trd_env=ft.TrdEnv.SIMULATE)
                    print(f"HK Positions Return Code: {ret_pos}")

                    if ret_pos == ft.RET_OK and pos_data is not None and len(pos_data) > 0:
                        print(f"  Found {len(pos_data)} positions")
                    else:
                        print("  No positions found")
                except Exception as e:
                    print(f"  Position check error: {str(e)[:50]}...")

                hk_ctx.close()
            else:
                print("[FAILED] HK Simulation Account Not Available")
                if isinstance(data, str):
                    print(f"Error message (first 50 chars): {data[:50]}...")
                else:
                    print(f"Error type: {type(data)}")

        except Exception as e:
            print(f"HK Market Error: {e}")

        await asyncio.sleep(0.5)

        # US market
        print("\n--- US Market ---")
        try:
            us_ctx = ft.OpenUSTradeContext(host=HOST, port=API_PORT)
            ret, data = us_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

            print(f"US SIMULATE Return Code: {ret}")

            if ret == ft.RET_OK and data is not None:
                print("[SUCCESS] US Simulation Account Found!")

                if hasattr(data, 'shape'):
                    print(f"Found {data.shape[0]} US simulation accounts")

                    if data.shape[0] > 0:
                        first_row = data.iloc[0]
                        try:
                            print(f"  Account ID: {first_row.get('acc_id', 'N/A')}")
                            print(f"  Currency: {first_row.get('currency', 'N/A')}")
                            print(f"  Cash: {first_row.get('cash', 0):,.2f}")
                            print(f"  Total Assets: {first_row.get('total_assets', 0):,.2f}")
                        except:
                            print("  [Cannot display account details]")

                us_ctx.close()
            else:
                print("[INFO] US Simulation Account Not Available")

        except Exception as e:
            print(f"US Market Error: {e}")

        await asyncio.sleep(0.5)

        # China market
        print("\n--- China Market ---")
        try:
            cn_ctx = ft.OpenCNTradeContext(host=HOST, port=API_PORT)
            ret, data = cn_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

            print(f"CN SIMULATE Return Code: {ret}")

            if ret == ft.RET_OK and data is not None:
                print("[SUCCESS] CN Simulation Account Found!")

                if hasattr(data, 'shape'):
                    print(f"Found {data.shape[0]} CN simulation accounts")

                cn_ctx.close()
            else:
                print("[INFO] CN Simulation Account Not Available")

        except Exception as e:
            print(f"CN Market Error: {e}")

    except Exception as e:
        print(f"Account check failed: {e}")
        import traceback
        traceback.print_exc()

async def check_account_funds():
    """Check account funds and buying power"""
    print("\n=== Checking Account Funds ===")

    try:
        import futu as ft

        # Try different market contexts to find available funds
        markets = [
            ("HK", ft.OpenHKTradeContext),
            ("US", ft.OpenUSTradeContext),
            ("CN", ft.OpenCNTradeContext)
        ]

        for market_name, context_class in markets:
            try:
                print(f"\n--- {market_name} Market Funds ---")
                ctx = context_class(host=HOST, port=API_PORT)

                ret, data = ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

                if ret == ft.RET_OK and data is not None and len(data) > 0:
                    for i in range(len(data)):
                        try:
                            row = data.iloc[i]
                            print(f"  Account {i+1}:")
                            print(f"    Cash: {row.get('cash', 0):,.2f}")
                            print(f"    Buying Power: {row.get('power', 0):,.2f}")
                            print(f"    Total Assets: {row.get('total_assets', 0):,.2f}")
                            print(f"    Market Value: {row.get('market_val', 0):,.2f}")
                            print(f"    Currency: {row.get('currency', 'N/A')}")
                        except:
                            print(f"    Account {i+1}: [Cannot display details]")
                else:
                    print(f"  No {market_name} simulation funds available")

                ctx.close()

            except Exception as e:
                print(f"  {market_name} funds check error: {e}")

            await asyncio.sleep(0.1)

    except Exception as e:
        print(f"Funds check failed: {e}")

async def check_recent_trades():
    """Check recent trades history"""
    print("\n=== Checking Recent Trades ===")

    try:
        import futu as ft

        ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Check recent orders
        ret, data = ctx.order_list_query(trd_env=ft.TrdEnv.SIMULATE)

        if ret == ft.RET_OK and data is not None and len(data) > 0:
            print(f"Found {len(data)} recent orders:")

            # Show up to 5 recent orders
            for i in range(min(5, len(data))):
                try:
                    row = data.iloc[i]
                    print(f"  Order {i+1}: {row.get('code', 'N/A')} "
                          f"{row.get('trd_side', 'N/A')} "
                          f"{row.get('order_type', 'N/A')} "
                          f"Qty: {row.get('qty', 0)}")
                except:
                    print(f"  Order {i+1}: [Cannot display details]")
        else:
            print("No recent orders found")

        ctx.close()

    except Exception as e:
        print(f"Trade history check error: {e}")

async def main():
    """Main function"""
    print("Futu Account Status Checker")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    await check_simulation_accounts()
    await check_account_funds()
    await check_recent_trades()

    print("\n=== Summary ===")
    print("Account status check completed.")
    print("Detailed account information has been saved to JSON files.")
    print("Please check the generated files for complete details.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()