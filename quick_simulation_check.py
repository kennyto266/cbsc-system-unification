#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Simulation Check - 快速模擬賬戶檢查
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def quick_check():
    try:
        import futu as ft

        print("Quick Simulation Account Check")
        print("=" * 40)

        # Connect
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("Connection established")

        # Get account list (OFFICIAL METHOD)
        ret, accounts = trade_ctx.get_acc_list()
        print(f"get_acc_list return code: {ret}")

        if ret == ft.RET_OK:
            print(f"SUCCESS: Found {len(accounts) if accounts else 0} account(s)")

            for i, acc in enumerate(accounts):
                acc_id = acc.get('acc_id', 'N/A')
                trd_env = acc.get('trd_env', 'N/A')
                print(f"Account {i+1}: ID={acc_id}, Env={trd_env}")

                if trd_env == 'SIMULATE':
                    print(f"  --> SIMULATION ACCOUNT FOUND! <--")

                    # Test quick order
                    print(f"Testing limit order...")
                    ret, order = trade_ctx.place_order(
                        acc_id=acc_id,
                        price=1.00,
                        qty=100,
                        code="HK.00700",
                        trd_side=ft.TrdSide.BUY,
                        trd_env=ft.TrdEnv.SIMULATE,
                        order_type=ft.OrderType.NORMAL,
                        remark="Quick Test"
                    )

                    if ret == ft.RET_OK:
                        order_id = order.iloc[0]['order_id']
                        print(f"SUCCESS: Order placed! ID={order_id}")

                        # Cancel
                        trade_ctx.cancel_order(acc_id=acc_id, order_id=order_id, trd_env=ft.TrdEnv.SIMULATE)
                        print("Order canceled")

                    else:
                        print(f"Order failed: {ret}")

        else:
            print("FAILED: No simulation accounts available")

            # Try alternative methods
            print("\nTrying alternative checks...")

            # Try accinfo_query
            try:
                ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                print(f"accinfo_query(SIMULATE): {ret}")
            except Exception as e:
                print(f"accinfo_query error: {e}")

        trade_ctx.close()

    except Exception as e:
        print(f"Check failed: {e}")

if __name__ == "__main__":
    asyncio.run(quick_check())