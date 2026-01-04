#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Account Issue - 調試賬戶問題
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

async def debug_account_issue():
    """Debug account access issues"""
    print("=== Debug Account Access Issue ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        import futu as ft

        # Setup connections
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        # Get global state for detailed info
        print("\n1. Getting system state...")
        ret, state = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print(f"   Server Version: {state.get('server_ver', 'Unknown')}")
            print(f"   Quote Login: {state.get('qot_logined', False)}")
            print(f"   Trade Login: {state.get('trd_logined', False)}")
            print(f"   Program Status: {state.get('program_status_desc', 'Unknown')}")
            print(f"   Market HK: {state.get('market_hk', 'Unknown')}")
            print(f"   Market US: {state.get('market_us', 'Unknown')}")

        # Try different account query methods
        print("\n2. Testing different account query methods...")

        methods = [
            ("accinfo_query()", lambda: trade_ctx.accinfo_query()),
            ("accinfo_query(SIMULATE)", lambda: trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)),
            ("accinfo_query(REAL)", lambda: trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)),
            ("get_acc_list()", lambda: trade_ctx.get_acc_list()),
        ]

        for method_name, method_func in methods:
            print(f"\n   Testing {method_name}...")
            try:
                ret, data = method_func()
                print(f"   Return Code: {ret}")

                if ret == ft.RET_OK:
                    print(f"   SUCCESS: {method_name} worked!")

                    if hasattr(data, 'shape'):
                        print(f"   Data shape: {data.shape}")
                        if data.shape[0] > 0:
                            print(f"   First row: {data.iloc[0].to_dict()}")
                    elif isinstance(data, list):
                        print(f"   List length: {len(data)}")
                        if len(data) > 0:
                            print(f"   First item: {data[0]}")
                    else:
                        print(f"   Data type: {type(data)}")
                        print(f"   Data: {data}")

                else:
                    print(f"   FAILED: {method_name} returned {ret}")
                    if isinstance(data, str):
                        print(f"   Error message: {data[:100]}...")

            except Exception as e:
                print(f"   Exception with {method_name}: {e}")

        # Try market subscription and trading test
        print("\n3. Testing direct market access...")
        try:
            # Subscribe to a stock
            ret, sub_err = quote_ctx.subscribe(["HK.00700"], [ft.SubType.QUOTE])
            print(f"   Subscribe result: {ret}")

            if ret == ft.RET_OK:
                # Get market data
                ret, quote_data = quote_ctx.get_stock_quote(["HK.00700"])
                if ret == ft.RET_OK and quote_data.shape[0] > 0:
                    price = quote_data.iloc[0]['last_price']
                    print(f"   Market data: SUCCESS (Price: {price:.2f})")

                    # Try simple order without account query
                    print("\n4. Testing direct order placement...")
                    ret, order_data = trade_ctx.place_order(
                        price=1.00,
                        qty=100,
                        code="HK.00700",
                        trd_side=ft.TrdSide.BUY,
                        trd_env=ft.TrdEnv.SIMULATE,
                        order_type=ft.OrderType.NORMAL,
                        remark="Direct Test Order"
                    )

                    if ret == ft.RET_OK:
                        print(f"   BREAKTHROUGH: Order placement succeeded!")
                        order_id = order_data.iloc[0]['order_id']
                        print(f"   Order ID: {order_id}")

                        # Cancel it
                        cancel_ret = trade_ctx.cancel_order(order_id=order_id, trd_env=ft.TrdEnv.SIMULATE)
                        if cancel_ret == ft.RET_OK:
                            print(f"   Order canceled successfully")

                    else:
                        print(f"   Order placement still failed: {ret}")

                else:
                    print(f"   Market data failed: {ret}")

        except Exception as e:
            print(f"   Market access error: {e}")

        quote_ctx.close()
        trade_ctx.close()

    except Exception as e:
        print(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Debug Complete ===")
    print("Recommendation:")
    print("1. Check if simulation trading is activated in FutuNN App")
    print("2. Ensure HK market trading account is opened")
    print("3. Verify API permissions are enabled in app settings")

async def main():
    """Main function"""
    await debug_account_issue()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Debug execution failed: {e}")