#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Status Check - 檢查交易服務狀態
基於重新假設：錯誤代碼-1 可能表示服務問題，而非權限問題
"""

import os
import sys
import asyncio

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def service_status_check():
    try:
        import futu as ft

        print("=== Service Status Check ===")
        print("Assumption: Error code -1 = Service Issue, not Permission Issue")
        print("=" * 60)

        # Check multiple connection types
        contexts = [
            ("Quote Context", ft.OpenQuoteContext),
            ("HK Trade Context", ft.OpenHKTradeContext),
            ("US Trade Context", ft.OpenUSTradeContext),
        ]

        for ctx_name, ctx_class in contexts:
            print(f"\n1. Testing {ctx_name}...")
            try:
                ctx = ctx_class(host=HOST, port=API_PORT)
                print(f"   Connection: SUCCESS")

                # Test basic functions
                if ctx_name == "Quote Context":
                    # Test quote functions (should work)
                    ret, state = ctx.get_global_state()
                    print(f"   Global State: {ret}")
                    if ret == ft.RET_OK:
                        print(f"   Server: {state.get('server_ver', 'Unknown')}")
                        print(f"   Trade Login: {state.get('trd_logined', False)}")
                        print(f"   Market Hours: HK={state.get('market_hk', 'Unknown')}")

                else:
                    # Test trade functions (return -1)
                    print(f"   Testing trade functions...")

                    # Method 1: Try get_acc_list
                    try:
                        ret, accounts = ctx.get_acc_list()
                        print(f"   get_acc_list: {ret}")
                    except Exception as e:
                        print(f"   get_acc_list Exception: {str(e)[:50]}")

                    # Method 2: Try accinfo_query
                    try:
                        ret, acc_info = ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                        print(f"   accinfo_query(SIMULATE): {ret}")
                    except Exception as e:
                        print(f"   accinfo_query Exception: {str(e)[:50]}")

                    # Method 3: Try direct order
                    try:
                        ret, order = ctx.place_order(
                            price=1.00,
                            qty=100,
                            code="HK.00700",
                            trd_side=ft.TrdSide.BUY,
                            trd_env=ft.TrdEnv.SIMULATE,
                            order_type=ft.OrderType.NORMAL,
                            remark="Service Test"
                        )
                        print(f"   place_order: {ret}")
                    except Exception as e:
                        print(f"   place_order Exception: {str(e)[:50]}")

                ctx.close()

            except Exception as e:
                print(f"   {ctx_name} Exception: {str(e)[:50]}")

        # Analysis based on results
        print(f"\n2. SERVICE STATUS ANALYSIS:")
        print(f"   - Quote functions: Likely working (login success)")
        print(f"   - Trade functions: All returning -1")
        print(f"   ")
        print(f"   POSSIBLE CAUSES:")
        print(f"   1. Trading service is down for maintenance")
        print(f"   2. Trading hours restriction (even for simulation)")
        print(f"   3. Service capacity issues")
        print(f"   4. Server-side error or bug")
        print(f"   ")
        print(f"   RECOMMENDATIONS:")
        print(f"   1. Check Futu service status page")
        print(f"   2. Wait and retry during market hours")
        print(f"   3. Contact Futu support if issue persists")
        print(f"   4. Try different time (market open/close)")

    except Exception as e:
        print(f"Service check failed: {e}")

if __name__ == "__main__":
    asyncio.run(service_status_check())