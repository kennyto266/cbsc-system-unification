#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test All Trading Environments - 測試所有交易環境
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

async def test_all_environments():
    """Test all trading environments"""
    print("=== Test All Trading Environments ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        import futu as ft

        # Setup connection
        print("\n1. Setting up trading connection...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("   Connection: SUCCESS")

        # Test all available environments
        environments = [
            (ft.TrdEnv.SIMULATE, "SIMULATION"),
            (ft.TrdEnv.REAL, "LIVE_TRADING"),
        ]

        print("\n2. Testing all trading environments...")

        for env, env_name in environments:
            print(f"\n   Testing {env_name} environment...")

            try:
                # Try account query
                ret, data = trade_ctx.accinfo_query(trd_env=env)
                print(f"   Account query: {ret}")

                if ret == ft.RET_OK and data.shape[0] > 0:
                    print(f"   SUCCESS: {env_name} account available!")

                    # Show account details
                    for idx, row in data.iterrows():
                        acc_id = row.get('acc_id', 'N/A')
                        currency = row.get('currency', 'N/A')
                        cash = row.get('cash', 0)
                        total_assets = row.get('total_assets', 0)

                        print(f"   Account {idx+1}:")
                        print(f"     ID: {acc_id}")
                        print(f"     Currency: {currency}")
                        print(f"     Cash: {cash:,.2f}")
                        print(f"     Total Assets: {total_assets:,.2f}")

                    # Test order placement with this environment
                    print(f"   Testing order placement in {env_name}...")
                    ret, order_data = trade_ctx.place_order(
                        price=1.00,
                        qty=100,
                        code="HK.00700",
                        trd_side=ft.TrdSide.BUY,
                        trd_env=env,
                        order_type=ft.OrderType.NORMAL,
                        time_in_force=ft.TimeInForce.DAY,
                        remark=f"Test Order - {env_name}"
                    )

                    if ret == ft.RET_OK:
                        order_id = order_data.iloc[0]['order_id']
                        print(f"   SUCCESS: Order placed in {env_name}!")
                        print(f"   Order ID: {order_id}")

                        # Cancel immediately
                        cancel_ret = trade_ctx.cancel_order(order_id=order_id, trd_env=env)
                        if cancel_ret == ft.RET_OK:
                            print(f"   Order canceled successfully")

                        break  # Found working environment

                    else:
                        print(f"   Order placement failed in {env_name}: {ret}")

                else:
                    print(f"   No accounts available in {env_name}")

            except Exception as e:
                print(f"   Error testing {env_name}: {e}")

        # Try without specifying environment
        print(f"\n   Testing default environment...")
        try:
            ret, data = trade_ctx.accinfo_query()
            print(f"   Default query: {ret}")

            if ret == ft.RET_OK and data.shape[0] > 0:
                print(f"   SUCCESS: Default environment works!")
                print(f"   Available accounts: {data.shape[0]}")

                # Try order with default environment
                ret, order_data = trade_ctx.place_order(
                    price=1.00,
                    qty=100,
                    code="HK.00700",
                    trd_side=ft.TrdSide.BUY,
                    order_type=ft.OrderType.NORMAL,
                    time_in_force=ft.TimeInForce.DAY,
                    remark="Test Order - Default"
                )

                if ret == ft.RET_OK:
                    print(f"   SUCCESS: Order placed in default environment!")

                    # Cancel
                    order_id = order_data.iloc[0]['order_id']
                    trade_ctx.cancel_order(order_id=order_id)

        except Exception as e:
            print(f"   Error with default environment: {e}")

        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Complete ===")

async def main():
    """Main function"""
    await test_all_environments()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test execution failed: {e}")