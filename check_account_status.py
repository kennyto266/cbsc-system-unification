#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Account Status - 檢查賬戶狀態和權限
不進行交易解鎖，只檢查可用功能和權限
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def check_account_status():
    try:
        import futu as ft

        print("=== Account Status Check ===")
        print("Checking available functions and permissions")
        print("=" * 60)

        # Setup contexts
        print("\n1. Setting up contexts...")
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Check global state
        print("\n2. Checking global state...")
        ret, state = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print(f"   Server Version: {state.get('server_ver', 'Unknown')}")
            print(f"   Quote Login: {state.get('qot_logined', False)}")
            print(f"   Trade Login: {state.get('trd_logined', False)}")
            print(f"   Market HK: {state.get('market_hk', 'Unknown')}")
            print(f"   Market US: {state.get('market_us', 'Unknown')}")
            print(f"   Market Time: {state.get('local_time', 'Unknown')}")
        else:
            print(f"   Global state failed: {ret}")

        # Test what functions work without unlock
        print("\n3. Testing available functions without unlock...")
        
        # Test get_funds
        print("   Testing get_funds (may work without unlock)...")
        try:
            ret, funds = trade_ctx.get_funds(trd_env=ft.TrdEnv.SIMULATE)
            print(f"   get_funds Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   SUCCESS! Funds information available")
                if funds.shape[0] > 0:
                    for i, fund in funds.iterrows():
                        currency = fund['currency']
                        total = fund['total_assets']
                        print(f"   {currency}: Total Assets = {total}")
            else:
                print(f"   get_funds failed: {ret}")
        except Exception as e:
            print(f"   get_funds Exception: {str(e)}")

        # Test get_acc_list without unlock
        print("\n   Testing get_acc_list without unlock...")
        try:
            ret, accounts = trade_ctx.get_acc_list()
            print(f"   get_acc_list Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   SUCCESS! Account list available without unlock")
                print(f"   Found {len(accounts)} accounts:")
                for i, acc in enumerate(accounts):
                    acc_id = acc.get('acc_id', 'N/A')
                    trd_env = acc.get('trd_env', 'N/A')
                    acc_type = acc.get('acc_type', 'N/A')
                    print(f"   Account {i+1}: ID={acc_id}, Env={trd_env}, Type={acc_type}")
            else:
                print(f"   get_acc_list failed: {ret}")
        except Exception as e:
            print(f"   get_acc_list Exception: {str(e)}")

        # Test position_list_query without unlock
        print("\n   Testing position_list_query without unlock...")
        try:
            ret, positions = trade_ctx.position_list_query(trd_env=ft.TrdEnv.SIMULATE)
            print(f"   position_list_query Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   SUCCESS! Position list available")
                print(f"   Found {len(positions)} positions")
            else:
                print(f"   position_list_query failed: {ret}")
        except Exception as e:
            print(f"   position_list_query Exception: {str(e)}")

        # Test order_list_query without unlock
        print("\n   Testing order_list_query without unlock...")
        try:
            ret, orders = trade_ctx.order_list_query(trd_env=ft.TrdEnv.SIMULATE)
            print(f"   order_list_query Return Code: {ret}")
            if ret == ft.RET_OK:
                print(f"   SUCCESS! Order list available")
                print(f"   Found {len(orders)} orders")
            else:
                print(f"   order_list_query failed: {ret}")
        except Exception as e:
            print(f"   order_list_query Exception: {str(e)}")

        # Test different environments
        print("\n4. Testing different trading environments...")
        
        for env_name, env_value in [("SIMULATE", ft.TrdEnv.SIMULATE), 
                                       ("REAL", ft.TrdEnv.REAL)]:
            print(f"\n   Testing {env_name} environment...")
            
            # Test accinfo_query
            try:
                ret, acc_info = trade_ctx.accinfo_query(trd_env=env_value)
                print(f"   accinfo_query({env_name}) Return Code: {ret}")
                if ret == ft.RET_OK:
                    print(f"   SUCCESS! {env_name} account info available")
                    if acc_info.shape[0] > 0:
                        for i, acc in acc_info.iterrows():
                            acc_id = acc['acc_id']
                            acc_type = acc['acc_type']
                            print(f"   Account: {acc_id}, Type: {acc_type}")
                else:
                    print(f"   {env_name} account info failed: {ret}")
            except Exception as e:
                print(f"   accinfo_query({env_name}) Exception: {str(e)}")

        # Market data test (should work)
        print("\n5. Testing market data access...")
        stock_code = "HK.00700"
        try:
            ret, quote_data = quote_ctx.get_stock_quote([stock_code])
            if ret == ft.RET_OK and quote_data.shape[0] > 0:
                price = quote_data.iloc[0]['last_price']
                volume = quote_data.iloc[0]['volume']
                print(f"   Market Data: {stock_code} = {price:.2f} HKD, Volume: {volume:,}")
                print("   SUCCESS: Market data fully functional")
            else:
                print(f"   Market data failed: {ret}")
        except Exception as e:
            print(f"   Market data Exception: {str(e)}")

        # Clean up
        quote_ctx.close()
        trade_ctx.close()

        print("\n" + "=" * 60)
        print("ACCOUNT STATUS ANALYSIS:")
        print("=" * 60)
        print("Based on the test results above:")
        print("1. Market data access: Check if working")
        print("2. Trading login status: Check from global state")
        print("3. Available trading functions: Which ones work without unlock")
        print("4. Account environments: Which environments are accessible")
        print("\nNEXT STEPS:")
        print("- If market data works but trading doesn't, focus on unlock/password")
        print("- If some trading functions work without unlock, note which ones")
        print("- Check if simulation environment is properly configured")
        
        return True

    except Exception as e:
        print(f"Account status check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(check_account_status())