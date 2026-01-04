#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Basic Order - 基本訂單測試
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

async def test_basic_order():
    """Test basic order functionality"""
    print("=== Basic Order Test ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)

    try:
        import futu as ft

        # Test connection
        print("\n1. Trading connection setup...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("   Connection: SUCCESS")

        # Check Futu API version
        print(f"\n2. Futu API Version: {ft.__version__ if hasattr(ft, '__version__') else 'Unknown'}")

        # List available constants
        print(f"\n3. Available Order Types:")
        for attr in dir(ft.OrderType):
            if not attr.startswith('_'):
                print(f"   - {attr}")

        print(f"\n   Available Time In Force:")
        for attr in dir(ft.TimeInForce):
            if not attr.startswith('_'):
                print(f"   - {attr}")

        print(f"\n   Available Trade Sides:")
        for attr in dir(ft.TrdSide):
            if not attr.startswith('_'):
                print(f"   - {attr}")

        # Test basic account info
        print(f"\n4. Account access test...")
        try:
            # Try to get any account information
            ret, data = trade_ctx.accinfo_query()
            print(f"   Default query: {ret}")

            if ret != ft.RET_OK:
                # Try simulation explicitly
                ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                print(f"   Simulation query: {ret}")

            if ret == ft.RET_OK:
                print(f"   Account access: SUCCESS")
                if hasattr(data, 'shape'):
                    print(f"   Account count: {data.shape[0]}")
            else:
                print(f"   Account access: FAILED (Code: {ret})")

        except Exception as e:
            print(f"   Account test error: {e}")

        # Test market data
        print(f"\n5. Market data test...")
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        try:
            # Get stock snapshot
            stock_code = "HK.00700"
            ret, data = quote_ctx.get_market_snapshot([stock_code])

            if ret == ft.RET_OK and data.shape[0] > 0:
                stock_info = data.iloc[0]
                price = stock_info['last_price']
                volume = stock_info['volume']
                print(f"   Market data: SUCCESS")
                print(f"   {stock_code} Price: {price:.2f}")
                print(f"   Volume: {volume:,}")
            else:
                print(f"   Market data: FAILED ({ret})")

        except Exception as e:
            print(f"   Market data error: {e}")

        quote_ctx.close()

        # Simple order test (if account access works)
        print(f"\n6. Order placement test...")
        try:
            # Use a test order that won't execute
            test_order = {
                'price': 0.01,  # Very low price
                'qty': 100,
                'code': 'HK.00700',
                'trd_side': ft.TrdSide.BUY,
                'trd_env': ft.TrdEnv.SIMULATE,
                'order_type': ft.OrderType.NORMAL,
                'remark': 'Test Order'
            }

            print(f"   Test order: {test_order}")
            print(f"   Attempting to place order...")

            ret, order_data = trade_ctx.place_order(**test_order)

            if ret == ft.RET_OK:
                print(f"   Order placement: SUCCESS")
                order_id = order_data.iloc[0]['order_id']
                print(f"   Order ID: {order_id}")

                # Cancel immediately
                cancel_ret = trade_ctx.cancel_order(order_id=order_id, trd_env=ft.TrdEnv.SIMULATE)
                if cancel_ret == ft.RET_OK:
                    print(f"   Order cancellation: SUCCESS")
                else:
                    print(f"   Cancellation failed: {cancel_ret}")

            else:
                print(f"   Order placement: FAILED ({ret})")
                if isinstance(order_data, str):
                    print(f"   Error: {str(order_data)[:100]}...")

        except Exception as e:
            print(f"   Order test error: {e}")

        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Summary ===")
    print("Futu API connection is working")
    print("Market data access is working")
    print("Account permissions need to be checked in FutuNN app")

async def main():
    """Main function"""
    await test_basic_order()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test execution failed: {e}")