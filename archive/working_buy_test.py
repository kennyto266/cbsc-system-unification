#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Working Buy Test with get_acc_list method
Use the proper method to get account ID

Author: Claude Code Assistant
Date: 2025-11-21
"""

import asyncio
import json
import sys
from datetime import datetime

try:
    import futu as ft
except ImportError:
    print("Futu API not installed")
    sys.exit(1)

async def test_working_buy():
    """Test buy order with proper account ID"""
    try:
        print("=== WORKING BUY TEST ===")
        print("User ID: 2860386")
        print("Target: 1 hand of Tencent (HK.00700)")

        # Connect to API
        trade_ctx = ft.OpenHKTradeContext(host='127.0.0.1', port=11111)
        quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)
        print("Connected to Futu API")

        # Get account list properly
        print("Getting account list...")
        ret, acc_list = trade_ctx.get_acc_list()

        if ret == ft.RET_OK:
            print(f"Account list successful!")
            print(f"Number of accounts: {len(acc_list)}")

            if len(acc_list) > 0:
                # Get the first account
                acc_id = acc_list[0]
                print(f"Found account ID: {acc_id}")

                # Get account info to verify
                ret, acc_info = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                if ret == ft.RET_OK and not acc_info.empty:
                    cash = acc_info.iloc[0]['cash']
                    total_assets = acc_info.iloc[0]['total_assets']
                    print(f"Account cash: {cash:,.0f} HKD")
                    print(f"Account total assets: {total_assets:,.0f} HKD")
            else:
                print("No accounts found!")
                return False
        else:
            print(f"Failed to get account list: {acc_list}")
            return False

        # Get market data
        print("\nGetting Tencent market data...")
        ret, market_data = quote_ctx.get_market_snapshot(['HK.00700'])

        if ret == ft.RET_OK and not market_data.empty:
            row = market_data.iloc[0]
            last_price = float(row['last_price'])
            lot_size = int(row['lot_size'])
            print(f"Tencent current price: {last_price:.2f} HKD")
            print(f"Lot size: {lot_size} shares")

            # Try to unlock trade
            print("\nAttempting to unlock trade...")
            try:
                ret, unlock_data = trade_ctx.unlock_trade(password='123456', trd_env=ft.TrdEnv.SIMULATE)
                if ret == ft.RET_OK:
                    print("Trade unlocked successfully")
                else:
                    print(f"Trade unlock failed (continuing): {unlock_data}")
            except Exception as e:
                print(f"Trade unlock exception (continuing): {e}")

            # Place buy order with proper account ID
            print(f"\nPlacing BUY order with account ID: {acc_id}")

            buy_price = last_price + 0.1  # Slightly above current price
            quantity = 1  # 1 hand

            print(f"Order details:")
            print(f"  Account ID: {acc_id}")
            print(f"  Symbol: HK.00700")
            print(f"  Side: BUY")
            print(f"  Quantity: {quantity} hand")
            print(f"  Price: {buy_price:.2f} HKD")

            # Place the order
            ret, order_data = trade_ctx.place_order(
                price=float(buy_price),
                qty=quantity,
                code="HK.00700",
                trd_side=ft.TrdSide.BUY,
                order_type=ft.OrderType.NORMAL,
                trd_env=ft.TrdEnv.SIMULATE,
                acc_id=acc_id
            )

            if ret == ft.RET_OK:
                order_id = str(order_data.iloc[0]['orderID'])
                print(f"\n*** ORDER PLACED SUCCESSFULLY! ***")
                print(f"Order ID: {order_id}")
                print(f"PLEASE CHECK YOUR FUTU DEMO ACCOUNT NOW!")

                # Save result
                result = {
                    'success': True,
                    'order_id': order_id,
                    'account_id': acc_id,
                    'symbol': 'HK.00700',
                    'side': 'BUY',
                    'quantity': quantity,
                    'price': buy_price,
                    'timestamp': datetime.now().isoformat()
                }

                with open('working_buy_test_result.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, default=str)

                print(f"Result saved to: working_buy_test_result.json")
                print(f"\nCHECK YOUR FUTU DEMO ACCOUNT:")
                print(f"- Look for order ID: {order_id}")
                print(f"- Stock: HK.00700 (Tencent)")
                print(f"- Price: {buy_price:.2f} HKD")
                print(f"- Quantity: {quantity} hand ({lot_size * quantity} shares)")

                return True
            else:
                print(f"\n*** ORDER FAILED ***")
                print(f"Error: {order_data}")
                return False
        else:
            print(f"Failed to get market data: {market_data}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            if 'trade_ctx' in locals():
                trade_ctx.close()
            if 'quote_ctx' in locals():
                quote_ctx.close()
            print("\nDisconnected from Futu API")
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_working_buy())
    if success:
        print("\nBUY TEST COMPLETED SUCCESSFULLY!")
        print("CHECK YOUR FUTU DEMO ACCOUNT FOR THE ORDER!")
    else:
        print("\nBUY TEST FAILED!")

    sys.exit(0 if success else 1)