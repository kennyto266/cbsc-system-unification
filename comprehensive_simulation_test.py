#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Simulation Test - 完整模擬交易測試
包含編碼修復和詳細診斷
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def comprehensive_simulation_test():
    try:
        import futu as ft

        print("=== Comprehensive Simulation Test ===")
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
                print("   ✅ Market data access working")
            else:
                print(f"   Market data failed: {ret}")
        else:
            print(f"   Market subscription failed: {ret}")

        # Test multiple approaches for simulation access
        print("\n4. Testing simulation account access...")
        
        # Method 1: Get acc_list
        print("   Method 1: get_acc_list")
        try:
            ret, accounts = trade_ctx.get_acc_list()
            print(f"   Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   ✅ SUCCESS! Found {len(accounts)} accounts")
                for i, acc in enumerate(accounts):
                    acc_id = acc.get('acc_id', 'N/A')
                    trd_env = acc.get('trd_env', 'N/A')
                    acc_type = acc.get('acc_type', 'N/A')
                    print(f"   Account {i+1}: ID={acc_id}, Env={trd_env}, Type={acc_type}")
                
                # Look for simulation accounts
                sim_accounts = [acc for acc in accounts if acc.get('trd_env') == 'SIMULATE']
                if sim_accounts:
                    print(f"   Found {len(sim_accounts)} simulation accounts")
                else:
                    print(f"   No simulation accounts found")
            else:
                print(f"   ❌ FAILED: Return code {ret}")
        except Exception as e:
            print(f"   Exception: {str(e)}")

        # Method 2: accinfo_query with SIMULATE
        print("\n   Method 2: accinfo_query with SIMULATE")
        try:
            ret, acc_info = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
            print(f"   Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   ✅ SUCCESS! Simulation account info retrieved")
                if acc_info.shape[0] > 0:
                    for i, acc in acc_info.iterrows():
                        acc_id = acc['acc_id']
                        acc_type = acc['acc_type']
                        print(f"   Account: {acc_id}, Type: {acc_type}")
            else:
                print(f"   ❌ FAILED: Return code {ret}")
        except Exception as e:
            print(f"   Exception: {str(e)}")

        # Method 3: accinfo_query with REAL
        print("\n   Method 3: accinfo_query with REAL")
        try:
            ret, acc_info = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)
            print(f"   Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   ✅ SUCCESS! Real account info retrieved")
                if acc_info.shape[0] > 0:
                    for i, acc in acc_info.iterrows():
                        acc_id = acc['acc_id']
                        acc_type = acc['acc_type']
                        print(f"   Account: {acc_id}, Type: {acc_type}")
            else:
                print(f"   ❌ FAILED: Return code {ret}")
        except Exception as e:
            print(f"   Exception: {str(e)}")

        # Method 4: Direct simulation order
        print("\n   Method 4: Direct simulation order")
        try:
            ret, order_data = trade_ctx.place_order(
                price=1.00,
                qty=100,
                code=stock_code,
                trd_side=ft.TrdSide.BUY,
                trd_env=ft.TrdEnv.SIMULATE,
                order_type=ft.OrderType.NORMAL,
                remark="Comprehensive Test"
            )
            print(f"   Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   ✅ SUCCESS! Simulation order placed")
                order_id = order_data.iloc[0]['order_id']
                print(f"   Order ID: {order_id}")
                
                # Cancel the test order
                cancel_ret = trade_ctx.cancel_order(
                    order_id=order_id,
                    trd_env=ft.TrdEnv.SIMULATE
                )
                if cancel_ret == ft.RET_OK:
                    print(f"   ✅ Order canceled successfully")
            else:
                print(f"   ❌ FAILED: Return code {ret}")
        except Exception as e:
            print(f"   Exception: {str(e)}")

        # Analysis and recommendations
        print("\n" + "=" * 60)
        print("ANALYSIS AND RECOMMENDATIONS:")
        print("=" * 60)
        
        if ret == ft.RET_OK:
            print("✅ SUCCESS: pdt_protection=0 fix worked!")
            print("✅ Simulation trading is now available")
            print("✅ Ready for quantitative trading development")
        else:
            print("❌ pdt_protection=0 fix may not have taken effect")
            print("❌ Simulation trading still not accessible")
            print("\nPOSSIBLE REASONS:")
            print("1. FutuOpenD needs more time to restart")
            print("2. pdt_protection parameter needs different setting")
            print("3. Service restart required in app interface")
            print("4. Account permissions need to be reactivated")
            
            print("\nNEXT STEPS:")
            print("1. Wait 2-3 minutes and retry")
            print("2. Check FutuOpenD process status")
            print("3. Try restarting via FutuNN app interface")
            print("4. Contact Futu support if issue persists")

        # Clean up
        quote_ctx.close()
        trade_ctx.close()

        return ret == ft.RET_OK

    except Exception as e:
        print(f"Comprehensive test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(comprehensive_simulation_test())
    if success:
        print(f"\n🎉 SIMULATION TRADING IS READY!")
        print(f"You can now start developing your quantitative trading strategies!")
    else:
        print(f"\n⏳ Further troubleshooting needed")
        print(f"Check the analysis above for next steps")