#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Limit Order - 测试定價單（限價單）
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

async def test_limit_order():
    """Test placing a limit order"""
    print("=== Test Limit Order (定價單) ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        import futu as ft

        # Test connection
        print("\n1. Setting up trading connection...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("   SUCCESS: Trading connection established")

        # Try to get account info with different approach
        print("\n2. Checking account access...")

        # Try without specifying environment first
        ret, data = trade_ctx.accinfo_query()
        print(f"   Default account query - Return Code: {ret}")

        if ret == ft.RET_OK and data.shape[0] > 0:
            print(f"   SUCCESS: Found {data.shape[0]} account(s)")

            # Show available accounts
            for idx, row in data.iterrows():
                acc_id = row.get('acc_id', 'N/A')
                trd_env = row.get('trd_env', 'N/A')
                currency = row.get('currency', 'N/A')
                cash = row.get('cash', 0)
                print(f"   Account {idx+1}: ID={acc_id}, Env={trd_env}, Currency={currency}, Cash={cash:,.2f}")
        else:
            print("   No accounts found in default query")

            # Try simulation specifically
            print("\n   Trying simulation environment...")
            ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
            print(f"   Simulation query - Return Code: {ret}")

        # Get market data for limit order pricing
        print("\n3. Getting market data for pricing...")
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        # Use a popular stock
        stock_code = "HK.00700"  # Tencent

        try:
            # Get order book for better pricing
            ret, order_book = quote_ctx.get_order_book([stock_code])
            if ret == ft.RET_OK and len(order_book) > 0:
                book = order_book[stock_code]
                if 'Bid' in book and len(book['Bid']) > 0 and 'Ask' in book and len(book['Ask']) > 0:
                    best_bid = book['Bid'][0][0]  # Best bid price
                    best_ask = book['Ask'][0][0]  # Best ask price
                    print(f"   Market data for {stock_code}:")
                    print(f"   Best Bid: {best_bid:.2f} HKD")
                    print(f"   Best Ask: {best_ask:.2f} HKD")
                    print(f"   Spread: {best_ask - best_bid:.2f} HKD")
                else:
                    print("   No order book data available")
            else:
                print(f"   Failed to get order book: {ret}")

            # Get snapshot as fallback
            ret, snapshot = quote_ctx.get_market_snapshot([stock_code])
            if ret == ft.RET_OK and snapshot.shape[0] > 0:
                current_price = snapshot.iloc[0]['last_price']
                print(f"   Current price: {current_price:.2f} HKD")

        except Exception as e:
            print(f"   Error getting market data: {e}")

        # Test limit order placement
        print("\n4. Testing LIMIT order placement...")

        # Use very conservative pricing to avoid accidental execution
        test_price = 1.00  # Very low price
        test_quantity = 100
        order_side = ft.TrdSide.BUY
        order_type = ft.OrderType.NORMAL  # Limit order
        time_in_force = ft.TimeInForce.DAY  # Day order

        print(f"   Limit order parameters:")
        print(f"   - Stock: {stock_code}")
        print(f"   - Side: {'BUY' if order_side == ft.TrdSide.BUY else 'SELL'}")
        print(f"   - Type: LIMIT (OrderType.NORMAL)")
        print(f"   - Price: {test_price:.2f} HKD")
        print(f"   - Quantity: {test_quantity} shares")
        print(f"   - Time in Force: DAY")
        print(f"   - Estimated value: {test_price * test_quantity:.2f} HKD")

        try:
            # Place the limit order
            ret, order_data = trade_ctx.place_order(
                price=test_price,
                qty=test_quantity,
                code=stock_code,
                trd_side=order_side,
                trd_env=ft.TrdEnv.SIMULATE,
                order_type=order_type,
                time_in_force=time_in_force,
                remark="API Test Limit Order"
            )

            if ret == ft.RET_OK:
                order_id = order_data.iloc[0]['order_id']
                order_status = order_data.iloc[0]['order_status']
                order_time = order_data.iloc[0]['create_time']

                print(f"\n   SUCCESS: Limit order placed!")
                print(f"   Order ID: {order_id}")
                print(f"   Status: {order_status}")
                print(f"   Time: {order_time}")
                print(f"   Stock: {order_data.iloc[0]['code']}")
                print(f"   Price: {order_data.iloc[0]['price']:.2f}")
                print(f"   Quantity: {order_data.iloc[0]['qty']}")
                print(f"   Side: {order_data.iloc[0]['trd_side']}")

                # Check order status immediately
                print(f"\n5. Checking order status...")
                ret, status_data = trade_ctx.order_list_query(
                    order_id=order_id,
                    trd_env=ft.TrdEnv.SIMULATE
                )

                if ret == ft.RET_OK and status_data.shape[0] > 0:
                    status = status_data.iloc[0]['order_status']
                    qty_dealt = status_data.iloc[0].get('qty_dealt', 0)
                    deal_avg_price = status_data.iloc[0].get('deal_avg_price', 0)

                    print(f"   Current Status: {status}")
                    print(f"   Dealt Quantity: {qty_dealt}")
                    print(f"   Average Deal Price: {deal_avg_price:.2f}" if deal_avg_price > 0 else "   Average Deal Price: N/A")

                # Modify the limit order (test modification)
                print(f"\n6. Testing order modification...")
                new_price = test_price + 0.01  # Increase price slightly
                ret, modify_data = trade_ctx.modify_order(
                    order_id=order_id,
                    price=new_price,
                    qty=test_quantity,
                    trd_env=ft.TrdEnv.SIMULATE
                )

                if ret == ft.RET_OK:
                    print(f"   SUCCESS: Order modified!")
                    print(f"   New Price: {new_price:.2f} HKD")
                else:
                    print(f"   Modification failed: {ret}")

                # Cancel the order
                print(f"\n7. Canceling limit order...")
                ret, cancel_data = trade_ctx.cancel_order(
                    order_id=order_id,
                    trd_env=ft.TrdEnv.SIMULATE
                )

                if ret == ft.RET_OK:
                    print(f"   SUCCESS: Order canceled")
                else:
                    print(f"   Cancellation failed: {ret}")

            else:
                print(f"   FAILED: Could not place limit order")
                print(f"   Error Code: {ret}")
                if isinstance(order_data, str):
                    try:
                        print(f"   Error: {order_data[:100]}...")
                    except:
                        pass

        except Exception as e:
            print(f"   Exception during order placement: {e}")
            import traceback
            traceback.print_exc()

        quote_ctx.close()
        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Limit Order Test Complete ===")
    print("Key features tested:")
    print("- Market data retrieval")
    print("- Limit order placement")
    print("- Order status checking")
    print("- Order modification")
    print("- Order cancellation")

async def main():
    """Main function"""
    await test_limit_order()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test execution failed: {e}")