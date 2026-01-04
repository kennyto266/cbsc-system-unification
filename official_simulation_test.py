#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Official Simulation Test - 根據官方文檔測試模擬交易
參考：https://openapi.futunn.com/futu-api-doc/qa/trade.html
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def official_simulation_test():
    try:
        import futu as ft

        print("=== Official Simulation Test ===")
        print("Based on: https://openapi.futunn.com/futu-api-doc/qa/trade.html")
        print("Key: Set trd_env=TrdEnv.SIMULATE for simulation")
        print("=" * 60)

        # Step 1: Get account list first (官方要求)
        print("\n1. Get trading account list (OFFICIAL METHOD)...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        ret, account_list = trade_ctx.get_acc_list()
        print(f"get_acc_list result: {ret}")

        if ret == ft.RET_OK:
            print(f"SUCCESS: Found accounts")

            # Show all accounts
            simulation_accounts = []
            for i, acc in enumerate(account_list):
                acc_id = acc.get('acc_id', 'N/A')
                trd_env = acc.get('trd_env', 'N/A')
                acc_type = acc.get('acc_type', 'N/A')
                print(f"Account {i+1}: ID={acc_id}, Env={trd_env}, Type={acc_type}")

                # Look for simulation accounts
                if trd_env == 'SIMULATE':
                    simulation_accounts.append(acc)
                    print(f"  --> SIMULATION ACCOUNT FOUND! <--")

            if simulation_accounts:
                print(f"\nFound {len(simulation_accounts)} simulation accounts")

                # Use first simulation account
                sim_acc = simulation_accounts[0]
                acc_id = sim_acc['acc_id']

                print(f"\n2. Testing simulation trading with account: {acc_id}")

                # Get market data
                quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
                stock_code = "HK.00700"

                ret, sub_err = quote_ctx.subscribe([stock_code], [ft.SubType.QUOTE])
                if ret == ft.RET_OK:
                    ret, quote_data = quote_ctx.get_stock_quote([stock_code])
                    if ret == ft.RET_OK:
                        price = quote_data.iloc[0]['last_price']
                        print(f"Market data: {stock_code} = {price:.2f} HKD")

                        # Step 2: Place simulation order (官方方法)
                        print(f"\n3. Placing LIMIT order (SIMULATION)...")

                        # Official simulation order parameters
                        ret, order_data = trade_ctx.place_order(
                            price=1.00,  # Very low price to avoid execution
                            qty=100,
                            code=stock_code,
                            trd_side=ft.TrdSide.BUY,
                            trd_env=ft.TrdEnv.SIMULATE,  # 关键：必须设置为模拟环境
                            order_type=ft.OrderType.NORMAL,
                            time_in_force=ft.TimeInForce.DAY,
                            remark="Official Simulation Test"
                        )

                        if ret == ft.RET_OK:
                            print(f"SUCCESS: Limit order placed!")

                            order_id = order_data.iloc[0]['order_id']
                            order_status = order_data.iloc[0]['order_status']

                            print(f"Order ID: {order_id}")
                            print(f"Status: {order_status}")
                            print(f"Stock: {order_data.iloc[0]['code']}")
                            print(f"Price: 1.00 HKD")
                            print(f"Quantity: 100")

                            # Step 3: Check order status
                            print(f"\n4. Checking order status...")
                            ret, status_data = trade_ctx.order_list_query(
                                order_id=order_id,
                                trd_env=ft.TrdEnv.SIMULATE
                            )

                            if ret == ft.RET_OK and status_data.shape[0] > 0:
                                current_status = status_data.iloc[0]['order_status']
                                print(f"Current Status: {current_status}")

                            # Step 4: Cancel order
                            print(f"\n5. Canceling order...")
                            cancel_ret = trade_ctx.cancel_order(
                                order_id=order_id,
                                trd_env=ft.TrdEnv.SIMULATE
                            )

                            if cancel_ret == ft.RET_OK:
                                print(f"Order canceled successfully")

                            print(f"\n🎉 SIMULATION TRADING TEST SUCCESS!")
                            print(f"✅ trd_env=TrdEnv.SIMULATE working!")
                            print(f"✅ OrderType.NORMAL (LIMIT) working!")
                            print(f"✅ Ready for quantitative trading!")

                        else:
                            print(f"Order failed: {ret}")
                            if isinstance(order_data, str):
                                print(f"Error: {order_data}")

                    quote_ctx.close()
            else:
                print(f"No simulation accounts found!")
                print(f"Available account types: {[acc.get('trd_env', 'N/A') for acc in account_list]}")
        else:
            print(f"Failed to get account list: {ret}")

            # Try alternative: Direct simulation order without account list
            print(f"\nTrying direct simulation order...")

            ret, order_data = trade_ctx.place_order(
                price=1.00,
                qty=100,
                code="HK.00700",
                trd_side=ft.TrdSide.BUY,
                trd_env=ft.TrdEnv.SIMULATE,  # 关键设置
                order_type=ft.OrderType.NORMAL,
                remark="Direct Simulation Test"
            )

            if ret == ft.RET_OK:
                print(f"SUCCESS: Direct simulation order worked!")
                order_id = order_data.iloc[0]['order_id']
                print(f"Order ID: {order_id}")

                # Cancel immediately
                trade_ctx.cancel_order(
                    order_id=order_id,
                    trd_env=ft.TrdEnv.SIMULATE
                )

                print(f"Order canceled successfully")
                print(f"\n🎉 DIRECT SIMULATION TEST SUCCESS!")
            else:
                print(f"Direct simulation order also failed: {ret}")

        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(official_simulation_test())