#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Simulation Test - 高級模擬賬戶測試
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def advanced_test():
    try:
        import futu as ft

        print("Advanced Simulation Account Test")
        print("=" * 50)

        # Try different trading contexts
        contexts = [
            ("OpenHKTradeContext", ft.OpenHKTradeContext),
            ("OpenUSTradeContext", ft.OpenUSTradeContext),
            ("OpenCNTradeContext", ft.OpenCNTradeContext),
        ]

        for ctx_name, ctx_class in contexts:
            print(f"\nTesting {ctx_name}...")
            try:
                trade_ctx = ctx_class(host=HOST, port=API_PORT)
                print(f"  {ctx_name} connected")

                # Test account list
                ret, accounts = trade_ctx.get_acc_list()
                print(f"  get_acc_list: {ret}")

                if ret == ft.RET_OK:
                    print(f"  SUCCESS: {ctx_name} found {len(accounts) if accounts else 0} accounts")

                    for i, acc in enumerate(accounts):
                        acc_id = acc.get('acc_id', 'N/A')
                        trd_env = acc.get('trd_env', 'N/A')
                        acc_type = acc.get('acc_type', 'N/A')
                        currency = acc.get('currency', 'N/A')
                        sec_firm = acc.get('security_firm', 'N/A')

                        print(f"  Account {i+1}:")
                        print(f"    ID: {acc_id}")
                        print(f"    Environment: {trd_env}")
                        print(f"    Type: {acc_type}")
                        print(f"    Currency: {currency}")
                        print(f"    Security Firm: {sec_firm}")

                        # Found simulation account
                        if trd_env == 'SIMULATE' or 'SIMULATE' in str(acc_type):
                            print(f"    *** SIMULATION ACCOUNT FOUND! ***")

                            # Try order without account_id
                            print(f"  Testing order placement...")
                            ret, order = trade_ctx.place_order(
                                price=1.00,
                                qty=100,
                                code="HK.00700",
                                trd_side=ft.TrdSide.BUY,
                                trd_env=ft.TrdEnv.SIMULATE,
                                order_type=ft.OrderType.NORMAL,
                                remark="Advanced Test"
                            )

                            if ret == ft.RET_OK:
                                print(f"  SUCCESS: Order placed!")
                                order_id = order.iloc[0]['order_id']
                                print(f"  Order ID: {order_id}")

                                # Cancel
                                trade_ctx.cancel_order(
                                    order_id=order_id,
                                    trd_env=ft.TrdEnv.SIMULATE
                                )
                                print(f"  Order canceled successfully")

                                return  # Success!

                # Close context
                trade_ctx.close()

            except Exception as e:
                print(f"  {ctx_name} error: {e}")

        # Try all account query methods
        print(f"\nTesting all query methods...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        methods = [
            ("get_acc_list()", lambda: trade_ctx.get_acc_list()),
            ("accinfo_query()", lambda: trade_ctx.accinfo_query()),
            ("accinfo_query(SIMULATE)", lambda: trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)),
            ("accinfo_query(REAL)", lambda: trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)),
        ]

        for method_name, method in methods:
            try:
                ret, data = method()
                print(f"{method_name}: {ret}")
                if ret == ft.RET_OK:
                    print(f"  SUCCESS: {method_name} worked!")
                    if hasattr(data, 'shape') and data.shape[0] > 0:
                        print(f"  Found {data.shape[0]} accounts")
            except Exception as e:
                print(f"{method_name}: Exception - {e}")

        # Try without any account query - direct order
        print(f"\nTrying direct order placement...")
        try:
            ret, order = trade_ctx.place_order(
                price=1.00,
                qty=100,
                code="HK.00700",
                trd_side=ft.TrdSide.BUY,
                trd_env=ft.TrdEnv.SIMULATE,
                order_type=ft.OrderType.NORMAL,
                remark="Direct Test"
            )

            if ret == ft.RET_OK:
                print(f"DIRECT SUCCESS: Order placed!")
                order_id = order.iloc[0]['order_id']
                print(f"Order ID: {order_id}")

                # Cancel
                trade_ctx.cancel_order(
                    order_id=order_id,
                    trd_env=ft.TrdEnv.SIMULATE
                )
                print("Order canceled")

            else:
                print(f"Direct order failed: {ret}")

        except Exception as e:
            print(f"Direct order error: {e}")

        trade_ctx.close()

    except Exception as e:
        print(f"Advanced test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(advanced_test())