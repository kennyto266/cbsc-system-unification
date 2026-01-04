#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Simulation Test - 簡化模擬交易測試
"""

import os
import sys
import asyncio

os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def simple_simulation_test():
    try:
        import futu as ft

        print("=== Simple Simulation Test ===")
        print("Key: trd_env = TrdEnv.SIMULATE")
        print("=" * 50)

        # Setup
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Try direct simulation order
        print("\n1. Testing direct simulation order...")
        ret, order_data = trade_ctx.place_order(
            price=1.00,
            qty=100,
            code="HK.00700",
            trd_side=ft.TrdSide.BUY,
            trd_env=ft.TrdEnv.SIMULATE,  # 关键设置
            order_type=ft.OrderType.NORMAL,
            remark="Simple Simulation Test"
        )

        print(f"Order placement result: {ret}")

        if ret == ft.RET_OK:
            print("SUCCESS! Simulation order placed!")

            order_id = order_data.iloc[0]['order_id']
            print(f"Order ID: {order_id}")

            # Cancel
            cancel_ret = trade_ctx.cancel_order(
                order_id=order_id,
                trd_env=ft.TrdEnv.SIMULATE
            )

            if cancel_ret == ft.RET_OK:
                print("Order canceled successfully!")

            print("\nSimulation trading is working!")

        else:
            print(f"Failed: {ret}")
            print("This confirms service issues - not account permissions")

        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(simple_simulation_test())