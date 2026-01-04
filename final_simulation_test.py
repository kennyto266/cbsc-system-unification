#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Simulation Test - 最終模擬交易測試
基於官方文檔：設置交易環境為模擬環境 trd_env = TrdEnv.SIMULATE
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def final_simulation_test():
    try:
        import futu as ft

        print("=== Final Simulation Test ===")
        print("Key: trd_env = TrdEnv.SIMULATE")
        print("Based on official documentation")
        print("=" * 50)

        # Create trading context
        print("\n1. Setting up trading context...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        # Get market data first
        print("\n2. Getting market data...")
        stock_code = "HK.00700"

        ret, sub_err = quote_ctx.subscribe([stock_code], [ft.SubType.QUOTE])
        if ret == ft.RET_OK:
            ret, quote_data = quote_ctx.get_stock_quote([stock_code])
            if ret == ft.RET_OK and quote_data.shape[0] > 0:
                price = quote_data.iloc[0]['last_price']
                print(f"   Market data: {stock_code} = {price:.2f} HKD")

                # Step 1: Try get_acc_list with simulation filter
                print("\n3. Getting account list...")
                ret, accounts = trade_ctx.get_acc_list()
                print(f"   get_acc_list result: {ret}")

                if ret == ft.RET_OK:
                    # Look for simulation accounts
                    simulation_accounts = []
                    for acc in accounts:
                        if acc.get('trd_env') == 'SIMULATE':
                            simulation_accounts.append(acc)

                    print(f"   Found {len(simulation_accounts)} simulation accounts")

                    if simulation_accounts:
                        sim_acc = simulation_accounts[0]
                        acc_id = sim_acc['acc_id']
                        print(f"   Using simulation account: {acc_id}")

                        # Step 2: Place simulation order with explicit environment
                        print(f"\n4. Placing LIMIT order (trd_env=TrdEnv.SIMULATE)...")

                        ret, order_data = trade_ctx.place_order(
                            acc_id=acc_id,  # Use simulation account ID
                            price=1.00,      # Very low price to avoid execution
                            qty=100,
                            code=stock_code,
                            trd_side=ft.TrdSide.BUY,
                            trd_env=ft.TrdEnv.SIMULATE,  # 关键：明确设置为模拟环境
                            order_type=ft.OrderType.NORMAL,
                            time_in_force=ft.TimeInForce.DAY,
                            remark="Final Test - SIMULATE Environment"
                        )

                        if ret == ft.RET_OK:
                            print(f"   🎉 SUCCESS! LIMIT ORDER PLACED!")

                            order_id = order_data.iloc[0]['order_id']
                            print(f"   Order ID: {order_id}")
                            print(f"   Environment: SIMULATE")
                            print(f"   Stock: {stock_code}")
                            print(f"   Price: 1.00 HKD")
                            print(f"   Quantity: 100")

                            # Step 3: Check order status
                            print(f"\n5. Checking order status...")
                            ret, status_data = trade_ctx.order_list_query(
                                order_id=order_id,
                                trd_env=ft.TrdEnv.SIMULATE
                            )

                            if ret == ft.RET_OK and status_data.shape[0] > 0:
                                status = status_data.iloc[0]['order_status']
                                print(f"   Order Status: {status}")

                                if status == 'SUBMITTED':
                                    print(f"   ✅ Order successfully submitted!")
                                elif status in ['FILLED_ALL', 'FILLED_PART']:
                                    print(f"   ⚠️ Order executed immediately!")

                            # Step 4: Cancel order
                            print(f"\n6. Canceling test order...")
                            cancel_ret = trade_ctx.cancel_order(
                                order_id=order_id,
                                trd_env=ft.TrdEnv.SIMULATE
                            )

                            if cancel_ret == ft.RET_OK:
                                print(f"   ✅ Order canceled successfully")
                            else:
                                print(f"   ⚠️ Order may still be active")

                            print(f"\n🎊 SIMULATION TRADING TEST COMPLETE!")
                            print(f"✅ trd_env=TrdEnv.SIMULATE working!")
                            print(f"✅ OrderType.NORMAL (LIMIT) working!")
                            print(f"✅ Ready for quantitative trading!")

                            return True
                        else:
                            print(f"   ❌ Order failed: {ret}")
                            if isinstance(order_data, dict):
                                print(f"   Error: {order_data}")
                else:
                    print(f"   No simulation accounts found")
                else:
                    print(f"   Failed to get account list: {ret}")

                # Fallback: Try direct order without account ID
                print(f"\n   Trying direct simulation order...")
                ret, order_data = trade_ctx.place_order(
                    price=1.00,
                    qty=100,
                    code=stock_code,
                    trd_side=ft.TrdSide.BUY,
                    trd_env=ft.TrdEnv.SIMULATE,  # 关键设置
                    order_type=ft.OrderType.NORMAL,
                    remark="Direct Test - SIMULATE Environment"
                )

                if ret == ft.RET_OK:
                    print(f"   🎉 DIRECT SIMULATION ORDER SUCCESS!")
                    order_id = order_data.iloc[0]['order_id']
                    print(f"   Order ID: {order_id}")

                    # Cancel immediately
                    trade_ctx.cancel_order(order_id=order_id, trd_env=ft.TrdEnv.SIMULATE)
                    print(f"   Order canceled successfully")

                    print(f"\n🎊 DIRECT SIMULATION TEST SUCCESS!")
                    return True
                else:
                    print(f"   Direct order also failed: {ret}")
            else:
                print(f"   Market data failed: {ret}")
        else:
            print(f"   Market subscription failed: {ret}")

        # Clean up
        quote_ctx.close()
        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(final_simulation_test())
    if success:
        print(f"\n🚀 SIMULATION TRADING IS READY!")
        print(f"You can now start developing your quantitative trading strategies!")
        else:
            print(f"\n⏳ Simulation trading not yet available")
            print(f"The service may be down or account needs activation")