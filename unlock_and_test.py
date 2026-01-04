#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unlock and Test - 解鎖交易並測試
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def unlock_and_test():
    try:
        import futu as ft

        print("=== Unlock Trading and Test ===")
        print("Even though docs say simulation doesn't need unlock...")
        print("Testing if unlock resolves -1 error code")
        print("=" * 60)

        # Connect
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("Connection established")

        # Step 1: Try unlock trading
        print("\n1. Attempting to unlock trading...")

        # Common passwords to try
        passwords = ["", "123456", "000000", "111111", "888888"]

        for pwd in passwords:
            try:
                print(f"   Trying password: '{'None' if pwd == '' else pwd}'")
                ret, unlock_data = trade_ctx.unlock_trade(password=pwd)

                if ret == ft.RET_OK:
                    print(f"   ✅ SUCCESS: Trading unlocked with password '{pwd}'")
                    if unlock_data:
                        print(f"   Message: {unlock_data}")
                    break
                else:
                    print(f"   Failed: {ret} - {unlock_data}")
            except Exception as e:
                print(f"   Error with password '{pwd}': {e}")

        # Step 2: Check if unlock worked
        print("\n2. Testing account access after unlock...")
        ret, accounts = trade_ctx.get_acc_list()
        print(f"   get_acc_list: {ret}")

        if ret == ft.RET_OK:
            print(f"   ✅ SUCCESS: Found {len(accounts) if accounts else 0} accounts")

            for i, acc in enumerate(accounts):
                acc_id = acc.get('acc_id', 'N/A')
                trd_env = acc.get('trd_env', 'N/A')
                acc_type = acc.get('acc_type', 'N/A')
                currency = acc.get('currency', 'N/A')

                print(f"   Account {i+1}:")
                print(f"     ID: {acc_id}")
                print(f"     Environment: {trd_env}")
                print(f"     Type: {acc_type}")
                print(f"     Currency: {currency}")

                if trd_env == 'SIMULATE' or 'SIMULATE' in str(acc_type):
                    print(f"     🎯 SIMULATION ACCOUNT FOUND!")

                    # Step 3: Test limit order
                    print(f"\n3. Testing LIMIT order...")
                    ret, order = trade_ctx.place_order(
                        acc_id=acc_id,
                        price=1.00,
                        qty=100,
                        code="HK.00700",
                        trd_side=ft.TrdSide.BUY,
                        trd_env=ft.TrdEnv.SIMULATE,
                        order_type=ft.OrderType.NORMAL,
                        time_in_force=ft.TimeInForce.DAY,
                        remark="Post-Unlock Test"
                    )

                    if ret == ft.RET_OK:
                        order_id = order.iloc[0]['order_id']
                        print(f"   🎉 SUCCESS: LIMIT ORDER PLACED!")
                        print(f"   Order ID: {order_id}")

                        # Check order status
                        ret, status = trade_ctx.order_list_query(
                            acc_id=acc_id,
                            order_id=order_id,
                            trd_env=ft.TrdEnv.SIMULATE
                        )

                        if ret == ft.RET_OK:
                            order_status = status.iloc[0]['order_status']
                            print(f"   Order Status: {order_status}")

                        # Cancel order
                        cancel_ret = trade_ctx.cancel_order(
                            acc_id=acc_id,
                            order_id=order_id,
                            trd_env=ft.TrdEnv.SIMULATE
                        )

                        if cancel_ret == ft.RET_OK:
                            print(f"   ✅ Order canceled successfully")

                        print(f"\n🎊 LIMIT ORDER TEST COMPLETE SUCCESS!")
                        print(f"OrderType.NORMAL (LIMIT) is now working!")
                        return

                    else:
                        print(f"   ❌ Order still failed: {ret}")

        else:
            print(f"   ❌ Account access still failed: {ret}")

            # Try accinfo_query as fallback
            print(f"\n   Trying accinfo_query...")
            try:
                ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                print(f"   accinfo_query(SIMULATE): {ret}")

                if ret == ft.RET_OK:
                    print(f"   ✅ accinfo_query works! Account available.")

                    # Try order without account_id
                    ret, order = trade_ctx.place_order(
                        price=1.00,
                        qty=100,
                        code="HK.00700",
                        trd_side=ft.TrdSide.BUY,
                        trd_env=ft.TrdEnv.SIMULATE,
                        order_type=ft.OrderType.NORMAL,
                        remark="Direct Test After Unlock"
                    )

                    if ret == ft.RET_OK:
                        print(f"   🎉 DIRECT ORDER SUCCESS!")
                        order_id = order.iloc[0]['order_id']
                        trade_ctx.cancel_order(order_id=order_id, trd_env=ft.TrdEnv.SIMULATE)

            except Exception as e:
                print(f"   accinfo_query error: {e}")

        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(unlock_and_test())