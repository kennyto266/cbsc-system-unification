#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Order Test - 直接下單測試 (跳過解鎖)
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def direct_order_test():
    try:
        import futu as ft

        print("=== Direct Order Test (Skip Unlock) ===")
        print("=" * 50)

        # Setup connections
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        print("\n1. Checking market status...")
        ret, state = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print(f"   Market HK: {state.get('market_hk', 'Unknown')}")
            print(f"   Market US: {state.get('market_us', 'Unknown')}")
            print(f"   Quote Login: {state.get('qot_logined', False)}")
            print(f"   Trade Login: {state.get('trd_logined', False)}")

        # Get market data first
        print(f"\n2. Getting market data...")
        stock_code = "HK.00700"

        # Subscribe and get quote
        ret, sub_err = quote_ctx.subscribe([stock_code], [ft.SubType.QUOTE])
        if ret == ft.RET_OK:
            ret, quote_data = quote_ctx.get_stock_quote([stock_code])
            if ret == ft.RET_OK and quote_data.shape[0] > 0:
                price = quote_data.iloc[0]['last_price']
                print(f"   Current price: {price:.2f} HKD")

                # Try direct order placement
                print(f"\n3. Direct LIMIT order placement...")
                print(f"   Market is closed, but simulation trading should still work")

                # Use very safe order parameters
                test_price = 1.00  # Much lower than current price
                quantity = 100

                ret, order_data = trade_ctx.place_order(
                    price=test_price,
                    qty=quantity,
                    code=stock_code,
                    trd_side=ft.TrdSide.BUY,
                    trd_env=ft.TrdEnv.SIMULATE,
                    order_type=ft.OrderType.NORMAL,
                    time_in_force=ft.TimeInForce.DAY,
                    remark="Direct Test Order"
                )

                print(f"   Order placement result: {ret}")

                if ret == ft.RET_OK:
                    print(f"\n   🎉 SUCCESS! LIMIT ORDER PLACED!")

                    order_id = order_data.iloc[0]['order_id']
                    order_status = order_data.iloc[0]['order_status']

                    print(f"   Order ID: {order_id}")
                    print(f"   Status: {order_status}")
                    print(f"   Stock: {order_data.iloc[0]['code']}")
                    print(f"   Price: {test_price:.2f} HKD")
                    print(f"   Quantity: {quantity}")

                    # Check order status immediately
                    ret, status_data = trade_ctx.order_list_query(
                        order_id=order_id,
                        trd_env=ft.TrdEnv.SIMULATE
                    )

                    if ret == ft.RET_OK and status_data.shape[0] > 0:
                        current_status = status_data.iloc[0]['order_status']
                        print(f"   Current Status: {current_status}")

                        if current_status in ['SUBMITTED', 'SUBMITTING']:
                            print(f"   ✅ Order successfully submitted!")
                        elif current_status in ['FILLED_ALL', 'FILLED_PART']:
                            print(f"   ⚠️ Order executed immediately!")

                    # Cancel the order
                    cancel_ret = trade_ctx.cancel_order(
                        order_id=order_id,
                        trd_env=ft.TrdEnv.SIMULATE
                    )

                    if cancel_ret == ft.RET_OK:
                        print(f"   ✅ Order canceled successfully")
                    else:
                        print(f"   Order may still be active")

                    print(f"\n🎊 LIMIT ORDER TEST SUCCESS!")
                    print(f"✅ OrderType.NORMAL (LIMIT) is working!")
                    print(f"✅ Simulation trading is functional!")
                    print(f"✅ You can now start developing trading strategies!")

                    return True

                else:
                    print(f"   ❌ Order failed: {ret}")
                    if isinstance(order_data, dict):
                        print(f"   Error details: {order_data}")

                    print(f"\n   Troubleshooting:")
                    print(f"   1. Simulation account may not be properly activated in app")
                    print(f"   2. API permissions may need to be reconfigured")
                    print(f"   3. Try reactivating simulation trading in FutuNN app")

            else:
                print(f"   Market data failed: {ret}")
        else:
            print(f"   Market subscription failed: {ret}")

        quote_ctx.close()
        trade_ctx.close()

        return False

    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(direct_order_test())
    if success:
        print(f"\n🎉 Ready for Quantitative Trading!")
    else:
        print(f"\n📋 Next steps:")
        print(f"   1. Check simulation trading activation in FutuNN app")
        print(f"   2. Verify API permissions in app settings")
        print(f"   3. Restart FutuOpenD and try again")