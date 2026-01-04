#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean Simulation Test - 無編碼問題的模擬交易測試
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def clean_simulation_test():
    try:
        import futu as ft

        print("=== Clean Simulation Test ===")
        print("Time: 2025-12-20 04:22:00")
        print("=" * 60)
        print("Testing pdt_protection=0 fix effectiveness")
        print("=" * 60)

        # Setup contexts
        print("\n1. Establishing connection...")
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Test global state first
        print("\n2. Checking global state...")
        ret, state = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print(f"   Server Version: {state.get('server_ver', 'Unknown')}")
            print(f"   Quote Login: {state.get('qot_logined', False)}")
            print(f"   Trade Login: {state.get('trd_logined', False)}")
            print(f"   Market HK: {state.get('market_hk', 'Unknown')}")
            print(f"   Market US: {state.get('market_us', 'Unknown')}")
        else:
            print(f"   Global state failed: {ret}")

        # Test market data (should work)
        print("\n3. Testing market data access...")
        stock_code = "HK.00700"
        ret, sub_err = quote_ctx.subscribe([stock_code], [ft.SubType.QUOTE])
        if ret == ft.RET_OK:
            ret, quote_data = quote_ctx.get_stock_quote([stock_code])
            if ret == ft.RET_OK and quote_data.shape[0] > 0:
                price = quote_data.iloc[0]['last_price']
                volume = quote_data.iloc[0]['volume']
                print(f"   Market Data: {stock_code} = {price:.2f} HKD, Volume: {volume:,}")
                print("   SUCCESS: Market data access working")
            else:
                print(f"   Market data failed: {ret}")
        else:
            print(f"   Market subscription failed: {ret}")

        # Test simulation access
        print("\n4. Testing simulation account access...")
        
        # Method 1: Get acc_list
        print("   Method 1: get_acc_list")
        try:
            ret, accounts = trade_ctx.get_acc_list()
            print(f"   Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   SUCCESS! Found {len(accounts)} accounts")
                simulation_accounts = []
                for i, acc in enumerate(accounts):
                    acc_id = acc.get('acc_id', 'N/A')
                    trd_env = acc.get('trd_env', 'N/A')
                    acc_type = acc.get('acc_type', 'N/A')
                    print(f"   Account {i+1}: ID={acc_id}, Env={trd_env}, Type={acc_type}")
                    
                    if trd_env == 'SIMULATE':
                        simulation_accounts.append(acc)
                
                if simulation_accounts:
                    print(f"   FOUND {len(simulation_accounts)} simulation accounts")
                    sim_acc = simulation_accounts[0]
                    acc_id = sim_acc['acc_id']
                    print(f"   Using simulation account: {acc_id}")
                    
                    # Test placing an order with this account
                    print(f"\n5. Testing simulation order...")
                    ret, order_data = trade_ctx.place_order(
                        price=1.00,
                        qty=100,
                        code=stock_code,
                        trd_side=ft.TrdSide.BUY,
                        trd_env=ft.TrdEnv.SIMULATE,
                        order_type=ft.OrderType.NORMAL,
                        remark="Clean Simulation Test"
                    )
                    
                    print(f"   Order Return Code: {ret}")
                    if ret == ft.RET_OK:
                        print(f"   SUCCESS! Simulation order placed!")
                        order_id = order_data.iloc[0]['order_id']
                        print(f"   Order ID: {order_id}")
                        
                        # Cancel order
                        cancel_ret = trade_ctx.cancel_order(
                            order_id=order_id,
                            trd_env=ft.TrdEnv.SIMULATE
                        )
                        if cancel_ret == ft.RET_OK:
                            print(f"   SUCCESS: Order canceled")
                        
                        return True
                    else:
                        print(f"   FAILED: Order placement failed with code {ret}")
                else:
                    print(f"   NO simulation accounts found")
                    print(f"   Available environments: {[acc.get('trd_env', 'N/A') for acc in accounts]}")
            else:
                print(f"   FAILED: Return code {ret}")
        except Exception as e:
            print(f"   Exception: {str(e)}")

        # Method 2: Direct simulation order without account list
        print("\n   Method 2: Direct simulation order")
        try:
            ret, order_data = trade_ctx.place_order(
                price=1.00,
                qty=100,
                code=stock_code,
                trd_side=ft.TrdSide.BUY,
                trd_env=ft.TrdEnv.SIMULATE,
                order_type=ft.OrderType.NORMAL,
                remark="Direct Test"
            )
            print(f"   Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   SUCCESS! Direct simulation order worked!")
                order_id = order_data.iloc[0]['order_id']
                print(f"   Order ID: {order_id}")
                
                # Cancel
                cancel_ret = trade_ctx.cancel_order(
                    order_id=order_id,
                    trd_env=ft.TrdEnv.SIMULATE
                )
                if cancel_ret == ft.RET_OK:
                    print(f"   SUCCESS: Order canceled")
                
                return True
            else:
                print(f"   FAILED: Direct order also failed with code {ret}")
        except Exception as e:
            print(f"   Exception: {str(e)}")

        # Clean up
        quote_ctx.close()
        trade_ctx.close()
        return False

    except Exception as e:
        print(f"Clean test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(clean_simulation_test())
    print(f"\n" + "=" * 60)
    if success:
        print("FINAL RESULT: SIMULATION TRADING IS READY!")
        print("You can now start developing your quantitative trading strategies!")
        print("The pdt_protection=0 fix was successful.")
    else:
        print("FINAL RESULT: Simulation trading still not accessible")
        print("The pdt_protection=0 fix may need more time or different approach.")
        print("\nPossible reasons:")
        print("1. FutuOpenD still restarting")
        print("2. Parameter needs to be set differently")
        print("3. Account needs activation in app")
        print("4. Service maintenance in progress")