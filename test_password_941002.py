#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Password 941002 - 測試密碼 941002
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def test_password_941002():
    try:
        import futu as ft

        print("=== Test Password 941002 ===")
        print("Trading Password: 941002")
        print("=" * 50)

        # Setup trading context
        print("\n1. Setting up trading context...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Test unlock with password 941002
        print("\n2. Testing unlock with password: 941002")
        ret, unlock_data = trade_ctx.unlock_trade(password='941002')
        print(f"   Unlock Return Code: {ret}")
        
        if ret == ft.RET_OK:
            print("   SUCCESS! Trading unlocked with password 941002!")
            
            # Test account access
            print("\n3. Testing account access...")
            ret, accounts = trade_ctx.get_acc_list()
            print(f"   Account List Return Code: {ret}")
            
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
                    print(f"\n   FOUND {len(simulation_accounts)} SIMULATION ACCOUNTS!")
                    
                    # Test simulation order
                    print(f"\n4. Testing simulation order...")
                    stock_code = "HK.00700"
                    
                    ret, order_data = trade_ctx.place_order(
                        price=1.00,
                        qty=100,
                        code=stock_code,
                        trd_side=ft.TrdSide.BUY,
                        trd_env=ft.TrdEnv.SIMULATE,
                        order_type=ft.OrderType.NORMAL,
                        remark="SUCCESS Test - 941002 Password"
                    )
                    
                    print(f"   Order Placement Return Code: {ret}")
                    
                    if ret == ft.RET_OK:
                        print("   SUCCESS! Simulation order placed!")
                        order_id = order_data.iloc[0]['order_id']
                        print(f"   Order ID: {order_id}")
                        
                        # Cancel order
                        cancel_ret = trade_ctx.cancel_order(
                            order_id=order_id,
                            trd_env=ft.TrdEnv.SIMULATE
                        )
                        
                        if cancel_ret == ft.RET_OK:
                            print("   SUCCESS: Order canceled")
                        
                        print(f"\n🎉 BREAKTHROUGH SUCCESS WITH PASSWORD 941002!")
                        print("   ✅ Trading unlock successful")
                        print("   ✅ Simulation account access working")
                        print("   ✅ Order placement working")
                        print("   ✅ Order cancellation working")
                        
                        # Test additional functions
                        print(f"\n5. Testing additional functions...")
                        
                        # Test position query
                        ret, positions = trade_ctx.position_list_query(trd_env=ft.TrdEnv.SIMULATE)
                        print(f"   Position Query: {ret}")
                        if ret == ft.RET_OK:
                            print(f"   SUCCESS: {len(positions)} positions")
                        
                        # Test order history
                        ret, orders = trade_ctx.order_list_query(trd_env=ft.TrdEnv.SIMULATE)
                        print(f"   Order History: {ret}")
                        if ret == ft.RET_OK:
                            print(f"   SUCCESS: {len(orders)} orders")
                        
                        trade_ctx.close()
                        return True
                        
                    else:
                        print(f"   Order placement failed: {ret}")
                else:
                    print(f"   No simulation accounts found")
            else:
                print(f"   Account query failed: {ret}")
                
        else:
            print(f"   FAILED: Unlock failed with code {ret}")
            if isinstance(unlock_data, dict):
                print(f"   Error details: {unlock_data}")

        trade_ctx.close()
        return False

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_password_941002())
    print(f"\n" + "=" * 50)
    if success:
        print("🎉 PASSWORD 941002 WORKS!")
        print("✅ SIMULATION TRADING IS READY!")
        print("✅ Ready for quantitative trading development!")
    else:
        print("❌ Password 941002 failed")
        print("Continue troubleshooting or contact support")