#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Trading Test - 简单交易测试
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

async def simple_trade_test():
    """Simple test of placing a simulation order"""
    print("=== Simple Trading Order Test ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        import futu as ft

        # Test connection
        print("\n1. Setting up trading connection...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("   SUCCESS: Trading connection established")

        # Test simulation account
        print("\n2. Checking simulation account...")
        ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

        if ret == ft.RET_OK and data.shape[0] > 0:
            print("   SUCCESS: Simulation account available")

            # Get account info
            acc_id = data.iloc[0]['acc_id']
            cash = data.iloc[0]['cash']
            print(f"   Account ID: {acc_id}")
            print(f"   Available cash: {cash:,.2f} HKD")

            # Test unlocking trade (try with common password)
            print("\n3. Attempting to unlock trading...")
            ret, unlock_data = trade_ctx.unlock_trade(password="123456")
            if ret == ft.RET_OK:
                print("   SUCCESS: Trading unlocked")
            else:
                print(f"   INFO: Unlock returned: {unlock_data}")
                print("   Continuing test (simulation may not need unlock)")

            # Place a test order (small test)
            print("\n4. Placing test order...")

            # Test Tencent stock (HK.00700)
            stock_code = "HK.00700"

            # Get current price first
            print(f"   Getting current price for {stock_code}...")
            quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
            ret, price_data = quote_ctx.get_market_snapshot([stock_code])

            if ret == ft.RET_OK and price_data.shape[0] > 0:
                current_price = price_data.iloc[0]['last_price']
                print(f"   Current price: {current_price:.2f} HKD")

                # Calculate test order parameters
                test_price = 1.00  # Very low price to avoid accidental execution
                test_quantity = 100  # 100 shares

                print(f"   Test order parameters:")
                print(f"   - Stock code: {stock_code}")
                print(f"   - Price: {test_price:.2f} HKD (intentionally low)")
                print(f"   - Quantity: {test_quantity} shares")
                print(f"   - Estimated amount: {test_price * test_quantity:,.2f} HKD")

                # Place the order
                print(f"\n   Executing order...")
                ret, order_data = trade_ctx.place_order(
                    price=test_price,
                    qty=test_quantity,
                    code=stock_code,
                    trd_side=ft.TrdSide.BUY,
                    trd_env=ft.TrdEnv.SIMULATE,
                    order_type=ft.OrderType.NORMAL,
                    remark="API Test Order"
                )

                if ret == ft.RET_OK:
                    order_id = order_data.iloc[0]['order_id']
                    print(f"   SUCCESS: Order placed successfully!")
                    print(f"   Order ID: {order_id}")
                    print(f"   Status: {order_data.iloc[0]['order_status']}")
                    print(f"   Time: {order_data.iloc[0]['create_time']}")

                    # Check order status
                    print(f"\n5. Checking order status...")
                    ret, status_data = trade_ctx.order_list_query(
                        order_id=order_id,
                        trd_env=ft.TrdEnv.SIMULATE
                    )

                    if ret == ft.RET_OK and status_data.shape[0] > 0:
                        status = status_data.iloc[0]['order_status']
                        print(f"   Order status: {status}")

                        if status == 'SUBMITTED':
                            print("   SUCCESS: Order submitted")
                        elif status == 'FILLED_ALL':
                            print("   SUCCESS: Order fully executed")
                        elif status == 'FILLED_PART':
                            print("   INFO: Order partially executed")
                        else:
                            print(f"   Order status: {status}")

                    # Try to cancel the order to be safe
                    print(f"\n6. Canceling test order...")
                    ret, cancel_data = trade_ctx.cancel_order(
                        order_id=order_id,
                        trd_env=ft.TrdEnv.SIMULATE
                    )

                    if ret == ft.RET_OK:
                        print(f"   SUCCESS: Test order canceled")
                    else:
                        print(f"   INFO: Cancel returned: {ret}")

                else:
                    print(f"   FAILED: Order placement failed")
                    print(f"   Error code: {ret}")
                    print(f"   Error message: {order_data}")

                quote_ctx.close()
            else:
                print(f"   FAILED: Cannot get stock price")
                print(f"   Error: {ret}")
                quote_ctx.close()

        else:
            print("   FAILED: Simulation account not available")
            print(f"   Return code: {ret}")
            if isinstance(data, str):
                print(f"   Error: {data[:100]}...")

        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Complete ===")
    print("If you see SUCCESS messages, simulation trading is working!")

async def main():
    """Main function"""
    await simple_trade_test()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test execution failed: {e}")