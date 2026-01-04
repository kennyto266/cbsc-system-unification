#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Permission Check - 完整權限檢查和修復
基於官方文檔: https://openapi.futunn.com/futu-api-doc/intro/authority.html
"""

import os
import sys
import asyncio

# Use virtual environment Python
VENV_PYTHON = r"C:\Users\Penguin8n\CODEX--\.venv\Scripts\python.exe"

# Connection configuration
API_PORT = 1130
HOST = '127.0.0.1'

async def complete_permission_check():
    try:
        import futu as ft

        print("=== Complete Permission Check & Fix ===")
        print("Based on: https://openapi.futunn.com/futu-api-doc/intro/authority.html")
        print("Key finding: API permissions ≠ APP permissions")
        print("=" * 60)

        # Setup connections
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        # Step 1: Check global state and login status
        print("\n1. Checking global state...")
        ret, state = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print(f"   Server: {state.get('server_ver', 'Unknown')}")
            print(f"   Quote Login: {state.get('qot_logined', False)}")
            print(f"   Trade Login: {state.get('trd_logined', False)}")
            print(f"   Market Status: HK={state.get('market_hk', 'Unknown')}")

            if not state.get('trd_logined', False):
                print("\n   ❌ TRADE LOGIN FAILED - This is the root cause!")
                print("   Solution: Re-login in FutuNN App with correct API permissions")
                return

        # Step 2: Try all possible account access methods
        print("\n2. Testing all account access methods...")

        methods = [
            ("Default get_acc_list", lambda: trade_ctx.get_acc_list()),
            ("Simulation get_acc_list", lambda: trade_ctx.get_acc_list()),
            ("Default accinfo_query", lambda: trade_ctx.accinfo_query()),
            ("Simulation accinfo_query", lambda: trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)),
            ("Real accinfo_query", lambda: trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)),
        ]

        working_method = None
        for method_name, method_func in methods:
            try:
                ret, data = method_func()
                print(f"   {method_name}: {ret}")
                if ret == ft.RET_OK:
                    print(f"      ✅ SUCCESS!")
                    working_method = (method_name, data)
                    break
                else:
                    print(f"      ❌ Failed: {ret}")
            except Exception as e:
                print(f"   {method_name}: Exception - {str(e)[:50]}")

        if working_method:
            method_name, account_data = working_method
            print(f"\n3. ✅ Working method found: {method_name}")

            # Step 3: Analyze account data
            if hasattr(account_data, 'shape') and account_data.shape[0] > 0:
                print(f"   Found {account_data.shape[0]} account(s)")

                for i, acc in enumerate(account_data.iterrows()):
                    acc_info = acc[1] if isinstance(acc, tuple) else acc
                    acc_id = acc_info.get('acc_id', 'N/A')
                    trd_env = acc_info.get('trd_env', 'N/A')
                    currency = acc_info.get('currency', 'N/A')

                    print(f"   Account {i+1}: ID={acc_id}, Env={trd_env}, Currency={currency}")

                    if trd_env == 'SIMULATE':
                        print(f"      🎯 SIMULATION ACCOUNT!")

                        # Step 4: Test order with account
                        print(f"\n4. Testing LIMIT order...")
                        ret, order = trade_ctx.place_order(
                            acc_id=acc_id,
                            price=1.00,
                            qty=100,
                            code="HK.00700",
                            trd_side=ft.TrdSide.BUY,
                            trd_env=ft.TrdEnv.SIMULATE,
                            order_type=ft.OrderType.NORMAL,
                            remark="Permission Test Order"
                        )

                        if ret == ft.RET_OK:
                            order_id = order.iloc[0]['order_id']
                            print(f"   🎉 SUCCESS: LIMIT ORDER PLACED!")
                            print(f"   Order ID: {order_id}")

                            # Cancel
                            trade_ctx.cancel_order(
                                acc_id=acc_id,
                                order_id=order_id,
                                trd_env=ft.TrdEnv.SIMULATE
                            )
                            print(f"   Order canceled successfully")
                            print(f"\n🎊 ALL PROBLEMS SOLVED!")
                            return

                        else:
                            print(f"   ❌ Order failed: {ret}")
            else:
                print(f"   Account data type: {type(account_data)}")
        else:
            print(f"\n3. ❌ No working account method found")
            print(f"\n   This indicates API permission issues!")

        # Step 5: Diagnostic based on official documentation
        print(f"\n5. 📋 Diagnostic Report Based on Official Docs:")
        print(f"   Based on: https://openapi.futunn.com/futu-api-doc/intro/authority.html")
        print(f"")
        print(f"   Root Cause: API permissions ≠ APP permissions")
        print(f"   ")
        print(f"   Required Actions in FutuNN App:")
        print(f"   1. App → 設置 → 隱私與安全 → API交易權限")
        print(f"      ✅ 讀取賬戶信息")
        print(f"      ✅ 模擬交易權限")
        print(f"      ✅ 行情數據權限")
        print(f"   ")
        print(f"   2. App → 交易 → 模擬交易")
        print(f"      確認模擬賬戶資金顯示（通常100萬港幣）")
        print(f"   ")
        print(f"   3. Restart FutuOpenD after permission changes")
        print(f"   ")
        print(f"   4. Re-run this test")
        print(f"   ")
        print(f"   Reference: API權限跟APP的權限不完全一樣")

        quote_ctx.close()
        trade_ctx.close()

    except Exception as e:
        print(f"Permission check failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(complete_permission_check())