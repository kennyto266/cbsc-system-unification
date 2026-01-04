#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Conditional Order - 測試條件單（智能訂單）
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

async def test_conditional_order():
    """Test placing a conditional order"""
    print("=== Test Conditional Order (條件單) ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        import futu as ft

        # Test connection
        print("\n1. Setting up trading connection...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("   SUCCESS: Trading connection established")

        # Try different login approach
        print("\n2. Checking login status...")
        try:
            # Try to get user info
            ret, user_info = trade_ctx.get_acc_list()
            print(f"   Account list query - Return Code: {ret}")

            if ret == ft.RET_OK:
                print(f"   SUCCESS: Got account list")
                print(f"   Number of accounts: {len(user_info) if user_info is not None else 0}")

                if user_info is not None and len(user_info) > 0:
                    for acc in user_info:
                        acc_id = acc.get('acc_id', 'N/A')
                        acc_type = acc.get('acc_type', 'N/A')
                        print(f"   Account: ID={acc_id}, Type={acc_type}")
            else:
                print(f"   Account query failed: {ret}")
        except Exception as e:
            print(f"   Error getting account list: {e}")

        # Test market data connection
        print("\n3. Testing market data access...")
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        try:
            # Get subscription list
            ret, sub_list = quote_ctx.get_stock_subscribecode()
            print(f"   Current subscriptions: {ret}")

            # Subscribe to a stock
            stock_code = "HK.00700"
            print(f"   Subscribing to {stock_code}...")
            ret, err = quote_ctx.subscribe([stock_code], [ft.SubType.QUOTE])
            print(f"   Subscribe result: {ret}")

            # Get basic quote
            ret, quote_data = quote_ctx.get_stock_quote([stock_code])
            if ret == ft.RET_OK and quote_data.shape[0] > 0:
                row = quote_data.iloc[0]
                last_price = row['last_price']
                update_time = row['update_time']
                print(f"   SUCCESS: Got quote for {stock_code}")
                print(f"   Last Price: {last_price:.2f}")
                print(f"   Update Time: {update_time}")
            else:
                print(f"   Quote query failed: {ret}")

            quote_ctx.close()
        except Exception as e:
            print(f"   Market data error: {e}")
            quote_ctx.close()

        # Test conditional order (智能單)
        print("\n4. Testing conditional order (智能單)...")

        try:
            # Conditional order parameters
            stock_code = "HK.00700"

            # Set a very low trigger price to avoid accidental execution
            trigger_price = 100.0  # Well below current price of 614
            order_price = 100.01    # Slightly above trigger
            quantity = 100

            print(f"   Conditional order parameters:")
            print(f"   - Stock: {stock_code}")
            print(f"   - Trigger Price: {trigger_price:.2f} HKD")
            print(f"   - Order Price: {order_price:.2f} HKD")
            print(f"   - Quantity: {quantity} shares")
            print(f"   - Order Type: LIMIT")
            print(f"   - Time in Force: GOOD_TILL_DATE")

            # Place conditional order
            ret, order_data = trade_ctx.place_order(
                price=order_price,
                qty=quantity,
                code=stock_code,
                trd_side=ft.TrdSide.BUY,
                trd_env=ft.TrdEnv.SIMULATE,
                order_type=ft.OrderType.NORMAL,
                time_in_force=ft.TimeInForce.GOOD_TILL_DATE,
                remark="API Test Conditional Order",
                aux_price=trigger_price,  # This might be the trigger price parameter
                order_id="",
                remark_id=0,
                sec_market=ft.Market.HK,
                order_source=ft.OrderSource.API,
            )

            if ret == ft.RET_OK:
                order_id = order_data.iloc[0]['order_id']
                print(f"\n   SUCCESS: Conditional order placed!")
                print(f"   Order ID: {order_id}")

                # Get order details
                status = order_data.iloc[0]['order_status']
                price = order_data.iloc[0]['price']
                qty = order_data.iloc[0]['qty']

                print(f"   Status: {status}")
                print(f"   Price: {price:.2f}")
                print(f"   Quantity: {qty}")

                # Query order details
                ret, detail_data = trade_ctx.order_list_query(
                    order_id=order_id,
                    trd_env=ft.TrdEnv.SIMULATE
                )

                if ret == ft.RET_OK and detail_data.shape[0] > 0:
                    detail = detail_data.iloc[0]
                    print(f"\n   Order details:")
                    print(f"   - Status: {detail['order_status']}")
                    print(f"   - Price: {detail['price']:.2f}")
                    print(f"   - Quantity: {detail['qty']}")
                    print(f"   - Dealt Qty: {detail.get('qty_dealt', 0)}")
                    print(f"   - Create Time: {detail['create_time']}")

                # Cancel the order
                print(f"\n   Canceling conditional order...")
                ret, cancel_data = trade_ctx.cancel_order(
                    order_id=order_id,
                    trd_env=ft.TrdEnv.SIMULATE
                )

                if ret == ft.RET_OK:
                    print(f"   SUCCESS: Order canceled")
                else:
                    print(f"   Cancellation failed: {ret}")

            else:
                print(f"   FAILED: Could not place conditional order")
                print(f"   Error Code: {ret}")
                if isinstance(order_data, str):
                    try:
                        print(f"   Error: {str(order_data)[:100]}...")
                    except:
                        print(f"   Error data type: {type(order_data)}")

        except Exception as e:
            print(f"   Exception during conditional order: {e}")
            import traceback
            traceback.print_exc()

        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Conditional Order Test Complete ===")
    print("Test summary:")
    print("- Connection: SUCCESS")
    print("- Market data: PARTIAL")
    print("- Account access: FAILED (Error -1)")
    print("- Conditional order: FAILED (Error -1)")
    print("\nRecommendation:")
    print("Check FutuNN app settings for API trading permissions")

async def main():
    """Main function"""
    await test_conditional_order()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test execution failed: {e}")