#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Unlock Test - 快速測試交易解鎖
使用密碼 677750 快速測試當前狀態
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def quick_unlock_test():
    try:
        import futu as ft

        print("=== Quick Unlock Test ===")
        print("Testing password: 677750")
        print("=" * 50)

        # Setup trading context
        print("\n1. Setting up trading context...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Quick unlock test
        print("\n2. Quick unlock test...")
        ret, unlock_data = trade_ctx.unlock_trade(password='677750')
        print(f"   Unlock Return Code: {ret}")
        
        if ret == ft.RET_OK:
            print("   SUCCESS! Trading unlocked!")
            
            # Quick simulation test
            print("\n3. Quick simulation test...")
            ret, order_data = trade_ctx.place_order(
                price=1.00,
                qty=100,
                code="HK.00700",
                trd_side=ft.TrdSide.BUY,
                trd_env=ft.TrdEnv.SIMULATE,
                order_type=ft.OrderType.NORMAL,
                remark="Quick Test"
            )
            
            print(f"   Order Return Code: {ret}")
            if ret == ft.RET_OK:
                print("   SUCCESS! Simulation order working!")
                order_id = order_data.iloc[0]['order_id']
                print(f"   Order ID: {order_id}")
                
                # Cancel order
                trade_ctx.cancel_order(order_id=order_id, trd_env=ft.TrdEnv.SIMULATE)
                print("   Order canceled")
                
                print(f"\n🎉 SIMULATION TRADING WORKS!")
                return True
            else:
                print(f"   Order failed: {ret}")
        else:
            print(f"   Unlock failed: {ret}")
            print(f"   Please reset password to 677750 in FutuNN App")
            print(f"   Then run the full test script")

        trade_ctx.close()
        return False

    except Exception as e:
        print(f"Quick test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_unlock_test())
    if success:
        print("\nSUCCESS! Trading is ready!")
    else:
        print("\nPlease reset password in FutuNN App first")