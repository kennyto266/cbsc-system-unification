#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correct Simulation Account Test - 基於官方文檔的正確模擬賬戶測試
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

async def test_simulation_correct():
    """Test simulation account using correct official API sequence"""
    print("=== Correct Simulation Account Test ===")
    print("Based on: https://openapi.futunn.com/futu-api-doc/trade/get-acc-list.html")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        import futu as ft

        # Setup connection - use HKTradeContext for account list
        print("\n1. Setting up trading connection...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
        print("   Connection: SUCCESS")

        # Step 1: Get account list (CORRECT METHOD)
        print("\n2. Getting trading account list (OFFICIAL METHOD)...")
        ret, account_list = trade_ctx.get_acc_list()
        print(f"   get_acc_list() return code: {ret}")

        if ret == ft.RET_OK:
            print("   SUCCESS: Account list retrieved!")
            print(f"   Number of accounts: {len(account_list) if account_list else 0}")

            if account_list and len(account_list) > 0:
                # Display all accounts
                print("\n   Available Accounts:")
                simulation_accounts = []

                for idx, acc in enumerate(account_list):
                    acc_id = acc.get('acc_id', 'N/A')
                    acc_type = acc.get('acc_type', 'N/A')
                    trd_env = acc.get('trd_env', 'N/A')
                    currency = acc.get('currency', 'N/A')
                    security_firm = acc.get('security_firm', 'N/A')

                    print(f"   Account {idx+1}:")
                    print(f"     ID: {acc_id}")
                    print(f"     Type: {acc_type}")
                    print(f"     Environment: {trd_env}")
                    print(f"     Currency: {currency}")
                    print(f"     Security Firm: {security_firm}")

                    # Look for simulation accounts
                    if trd_env == 'SIMULATE':
                        simulation_accounts.append(acc)
                        print(f"     >>> SIMULATION ACCOUNT FOUND! <<<")

                if simulation_accounts:
                    print(f"\n   Found {len(simulation_accounts)} simulation account(s)")

                    # Use first simulation account for testing
                    sim_acc = simulation_accounts[0]
                    sim_acc_id = sim_acc['acc_id']
                    print(f"   Using simulation account: {sim_acc_id}")

                    # Step 2: Get market data for order
                    print(f"\n3. Getting market data...")
                    stock_code = "HK.00700"

                    # Subscribe and get quote
                    ret, sub_err = quote_ctx.subscribe([stock_code], [ft.SubType.QUOTE])
                    if ret == ft.RET_OK:
                        ret, quote_data = quote_ctx.get_stock_quote([stock_code])
                        if ret == ft.RET_OK and quote_data.shape[0] > 0:
                            last_price = quote_data.iloc[0]['last_price']
                            print(f"   Market data: {stock_code} = {last_price:.2f} HKD")

                            # Step 3: Place limit order (NO UNLOCK NEEDED)
                            print(f"\n4. Placing LIMIT order (NO UNLOCK REQUIRED)...")
                            test_price = 1.00  # Very low price to avoid execution
                            quantity = 100

                            print(f"   Order parameters:")
                            print(f"     Stock: {stock_code}")
                            print(f"     Account ID: {sim_acc_id}")
                            print(f"     Environment: SIMULATE")
                            print(f"     Order Type: LIMIT (NORMAL)")
                            print(f"     Price: {test_price:.2f} HKD")
                            print(f"     Quantity: {quantity}")

                            # Place order using official parameters
                            ret, order_data = trade_ctx.place_order(
                                acc_id=sim_acc_id,  # Use account_id from get_acc_list
                                price=test_price,
                                qty=quantity,
                                code=stock_code,
                                trd_side=ft.TrdSide.BUY,
                                trd_env=ft.TrdEnv.SIMULATE,
                                order_type=ft.OrderType.NORMAL,
                                time_in_force=ft.TimeInForce.DAY,
                                remark="Official API Test - Limit Order"
                            )

                            if ret == ft.RET_OK:
                                print(f"\n   🎉 SUCCESS: LIMIT ORDER PLACED! 🎉")

                                order_id = order_data.iloc[0]['order_id']
                                order_status = order_data.iloc[0]['order_status']

                                print(f"   Order ID: {order_id}")
                                print(f"   Status: {order_status}")
                                print(f"   Stock: {order_data.iloc[0]['code']}")
                                print(f"   Price: {order_data.iloc[0]['price']:.2f}")
                                print(f"   Quantity: {order_data.iloc[0]['qty']}")

                                # Step 4: Check order status
                                print(f"\n5. Checking order status...")
                                ret, status_data = trade_ctx.order_list_query(
                                    acc_id=sim_acc_id,
                                    order_id=order_id,
                                    trd_env=ft.TrdEnv.SIMULATE
                                )

                                if ret == ft.RET_OK and status_data.shape[0] > 0:
                                    status = status_data.iloc[0]['order_status']
                                    print(f"   Order Status: {status}")

                                # Step 5: Cancel order (cleanup)
                                print(f"\n6. Canceling test order...")
                                cancel_ret = trade_ctx.cancel_order(
                                    acc_id=sim_acc_id,
                                    order_id=order_id,
                                    trd_env=ft.TrdEnv.SIMULATE
                                )

                                if cancel_ret == ft.RET_OK:
                                    print(f"   SUCCESS: Test order canceled")

                                print(f"\n=== LIMIT ORDER TEST COMPLETE SUCCESS ===")
                                print(f"✅ OrderType.NORMAL (LIMIT) is working!")
                                print(f"✅ Simulation account access confirmed!")
                                print(f"✅ You can now start quantitative trading!")

                            else:
                                print(f"   ❌ Order placement failed: {ret}")
                                if isinstance(order_data, str):
                                    print(f"   Error: {order_data}")

                        else:
                            print(f"   ❌ Market data failed: {ret}")
                    else:
                        print(f"   ❌ Market subscription failed: {ret}")
                else:
                    print(f"\n   ❌ NO SIMULATION ACCOUNTS FOUND!")
                    print(f"   You need to activate simulation trading in FutuNN App")
                    print(f"   Path: App → Trading → Simulation Trading → Activate")
            else:
                print(f"   ❌ No accounts found")
        else:
            print(f"   ❌ get_acc_list() failed: {ret}")
            if isinstance(account_list, str):
                print(f"   Error: {account_list[:100]}...")

        quote_ctx.close()
        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Complete ===")

async def main():
    """Main function"""
    await test_simulation_correct()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test execution failed: {e}")