#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Order with Password - 使用交易密碼測試下單
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Use virtual environment path
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

# Connection configuration
API_PORT = 1130
HOST = '127.0.0.1'
TRADE_PASSWORD = "677750"  # 您提供的交易密碼

async def test_order_with_password():
    try:
        import futu as ft

        print("=== Test Order with Password ===")
        print(f"Trade Password: {TRADE_PASSWORD}")
        print("=" * 50)

        # Setup connections
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        print("\n1. Checking connection status...")
        ret, state = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print(f"   Quote Login: {state.get('qot_logined', False)}")
            print(f"   Trade Login: {state.get('trd_logined', False)}")
            print(f"   Market HK: {state.get('market_hk', 'Unknown')}")

        # Step 1: Unlock trading with password
        print(f"\n2. Unlocking trading with password...")
        print(f"   Password: {TRADE_PASSWORD}")

        ret, unlock_data = trade_ctx.unlock_trade(password=TRADE_PASSWORD)
        print(f"   Unlock result: {ret}")

        if ret == ft.RET_OK:
            print(f"   ✅ Trading unlocked successfully!")
            if unlock_data:
                print(f"   Message: {unlock_data}")
        else:
            print(f"   ❌ Unlock failed: {unlock_data}")
            # Continue anyway - might not need unlock for simulation

        # Step 2: Try direct order placement
        print(f"\n3. Attempting to place LIMIT order...")

        # Order parameters
        stock_code = "HK.00700"  # Tencent
        order_price = 1.00         # Very low price to avoid execution
        order_quantity = 100       # 100 shares

        print(f"   Stock: {stock_code}")
        print(f"   Order Type: LIMIT (OrderType.NORMAL)")
        print(f"   Side: BUY")
        print(f"   Price: {order_price:.2f} HKD")
        print(f"   Quantity: {order_quantity}")
        print(f"   Environment: SIMULATION")

        # Place the order
        ret, order_data = trade_ctx.place_order(
            price=order_price,
            qty=order_quantity,
            code=stock_code,
            trd_side=ft.TrdSide.BUY,
            trd_env=ft.TrdEnv.SIMULATE,
            order_type=ft.OrderType.NORMAL,
            time_in_force=ft.TimeInForce.DAY,
            remark="Test Order with Password"
        )

        if ret == ft.RET_OK:
            print(f"\n   🎉 SUCCESS: LIMIT ORDER PLACED!")

            order_id = order_data.iloc[0]['order_id']
            order_status = order_data.iloc[0]['order_status']
            create_time = order_data.iloc[0]['create_time']

            print(f"   Order ID: {order_id}")
            print(f"   Status: {order_status}")
            print(f"   Time: {create_time}")
            print(f"   Price: {order_price:.2f} HKD")
            print(f"   Quantity: {order_quantity}")

            # Step 3: Check order status
            print(f"\n4. Checking order status...")
            ret, status_data = trade_ctx.order_list_query(
                order_id=order_id,
                trd_env=ft.TrdEnv.SIMULATE
            )

            if ret == ft.RET_OK and status_data.shape[0] > 0:
                status = status_data.iloc[0]['order_status']
                qty_dealt = status_data.iloc[0].get('qty_dealt', 0)
                print(f"   Current Status: {status}")
                print(f"   Dealt Quantity: {qty_dealt}")

            # Step 4: Cancel order (cleanup)
            print(f"\n5. Canceling test order...")
            cancel_ret = trade_ctx.cancel_order(
                order_id=order_id,
                trd_env=ft.TrdEnv.SIMULATE
            )

            if cancel_ret == ft.RET_OK:
                print(f"   ✅ Order canceled successfully")
            else:
                print(f"   ⚠️ Cancel failed: {cancel_ret}")
                print(f"   Order may still be active")

            print(f"\n🎊 LIMIT ORDER TEST COMPLETE!")
            print(f"OrderType.NORMAL (LIMIT) is working!")
            print(f"Simulation trading is functional!")

        else:
            print(f"   ❌ Order placement failed: {ret}")
            if isinstance(order_data, str):
                print(f"   Error message: {order_data}")

            # Check if it's a market hours issue
            print(f"\n   Possible reasons:")
            print(f"   - Market is closed (HK Market: {state.get('market_hk', 'Unknown')})")
            print(f"   - Trading password incorrect")
            print(f"   - Account permissions issue")
            print(f"   - Simulation account not properly activated")

        quote_ctx.close()
        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_order_with_password())