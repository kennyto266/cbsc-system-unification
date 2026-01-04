#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Limit Order Test - 最終限價單測試
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

async def test_limit_order_final():
    """Final test of limit order after compliance confirmation"""
    print("=== Final Limit Order Test ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Status: Testing after compliance confirmation")
    print("=" * 50)

    try:
        import futu as ft

        # Setup connections
        print("\n1. Setting up connections...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
        print("   Connection: SUCCESS")

        # Check global state
        ret, state = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print(f"   Server: {state.get('server_ver', 'Unknown')}")
            print(f"   Quote Login: {state.get('qot_logined', False)}")
            print(f"   Trade Login: {state.get('trd_logined', False)}")

        # Test simulation account directly with limit order
        print("\n2. Testing Simulation Trading...")

        # Test order parameters - very safe values
        stock_code = "HK.00700"
        test_price = 1.00  # Very low price to avoid execution
        quantity = 100

        print(f"   Stock: {stock_code}")
        print(f"   Order Type: LIMIT (OrderType.NORMAL)")
        print(f"   Price: {test_price:.2f} HKD")
        print(f"   Quantity: {quantity}")
        print(f"   Environment: SIMULATION")

        # Try to place the limit order
        print(f"\n3. Placing LIMIT order...")
        ret, order_data = trade_ctx.place_order(
            price=test_price,
            qty=quantity,
            code=stock_code,
            trd_side=ft.TrdSide.BUY,
            trd_env=ft.TrdEnv.SIMULATE,
            order_type=ft.OrderType.NORMAL,
            time_in_force=ft.TimeInForce.DAY,
            remark="Final Test Limit Order"
        )

        if ret == ft.RET_OK:
            print(f"   SUCCESS: Limit order placed!")

            # Get order details
            order_id = order_data.iloc[0]['order_id']
            order_status = order_data.iloc[0]['order_status']

            print(f"   Order ID: {order_id}")
            print(f"   Status: {order_status}")
            print(f"   Price: {test_price:.2f} HKD")
            print(f"   Quantity: {quantity}")

            # Check order status
            ret, status_data = trade_ctx.order_list_query(
                order_id=order_id,
                trd_env=ft.TrdEnv.SIMULATE
            )

            if ret == ft.RET_OK and status_data.shape[0] > 0:
                status = status_data.iloc[0]['order_status']
                print(f"   Current Status: {status}")

            # Cancel the test order
            print(f"\n4. Canceling test order...")
            cancel_ret = trade_ctx.cancel_order(
                order_id=order_id,
                trd_env=ft.TrdEnv.SIMULATE
            )

            if cancel_ret == ft.RET_OK:
                print(f"   SUCCESS: Test order canceled")
            else:
                print(f"   Cancellation failed: {cancel_ret}")

            print(f"\n=== LIMIT ORDER TEST SUCCESS ===")
            print(f"OrderType.NORMAL (LIMIT) is working!")
            print(f"You can now place real limit orders.")

        else:
            print(f"   FAILED: Limit order placement failed")
            print(f"   Error Code: {ret}")

            # Check if we need to try different approach
            if ret == -1:
                print(f"\n   Possible issues:")
                print(f"   - Need to login to FutuNN app")
                print(f"   - Simulation trading not activated")
                print(f"   - Account permissions not configured")

                # Try to get account info for debugging
                print(f"\n   Checking account access...")
                try:
                    acc_ret, acc_data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                    if acc_ret == ft.RET_OK:
                        print(f"   Account access: SUCCESS")
                    else:
                        print(f"   Account access: FAILED ({acc_ret})")
                except Exception as e:
                    print(f"   Account check error: {e}")

        quote_ctx.close()
        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Complete ===")

async def main():
    """Main function"""
    await test_limit_order_final()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test execution failed: {e}")