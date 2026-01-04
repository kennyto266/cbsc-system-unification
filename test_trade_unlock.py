#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Trade Unlock - 測試交易解鎖功能
基於官方文檔：所有交易功能都需要先解鎖交易接口
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def test_trade_unlock():
    try:
        import futu as ft

        print("=== Trade Unlock Test ===")
        print("Based on official documentation: All trading functions require unlocking first")
        print("=" * 60)

        # Setup trading context
        print("\n1. Setting up trading context...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Step 1: Try to unlock trading interface
        print("\n2. Unlocking trading interface...")
        print("   Using provided trading password: 677750")
        
        # Important: The unlock_trade function is required before any trading operations
        ret, unlock_data = trade_ctx.unlock_trade(password='677750')
        print(f"   Unlock Return Code: {ret}")
        
        if ret == ft.RET_OK:
            print("   SUCCESS: Trading interface unlocked!")
            
            # Now test simulation account access
            print("\n3. Testing simulation account access after unlock...")
            
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
                        print(f"   FOUND {len(simulation_accounts)} simulation accounts!")
                        
                        # Test placing a simulation order
                        print(f"\n4. Testing simulation order placement...")
                        stock_code = "HK.00700"
                        
                        ret, order_data = trade_ctx.place_order(
                            price=1.00,
                            qty=100,
                            code=stock_code,
                            trd_side=ft.TrdSide.BUY,
                            trd_env=ft.TrdEnv.SIMULATE,
                            order_type=ft.OrderType.NORMAL,
                            remark="Post-Unlock Simulation Test"
                        )
                        
                        print(f"   Order Placement Return Code: {ret}")
                        if ret == ft.RET_OK:
                            print(f"   SUCCESS! Simulation order placed!")
                            order_id = order_data.iloc[0]['order_id']
                            print(f"   Order ID: {order_id}")
                            
                            # Cancel the test order
                            cancel_ret = trade_ctx.cancel_order(
                                order_id=order_id,
                                trd_env=ft.TrdEnv.SIMULATE
                            )
                            if cancel_ret == ft.RET_OK:
                                print(f"   SUCCESS: Order canceled")
                            
                            print(f"\n🎉 BREAKTHROUGH! Simulation trading is now working!")
                            print(f"   The key was: unlock_trade(password) before trading operations")
                            
                            return True
                        else:
                            print(f"   Order placement failed: {ret}")
                    else:
                        print(f"   No simulation accounts found")
                        print(f"   Available environments: {[acc.get('trd_env', 'N/A') for acc in accounts]}")
                else:
                    print(f"   FAILED: Account list query failed with code {ret}")
            except Exception as e:
                print(f"   Exception during account query: {str(e)}")
                
            # Method 2: Try direct simulation order
            print("\n   Method 2: Direct simulation order after unlock")
            try:
                ret, order_data = trade_ctx.place_order(
                    price=1.00,
                    qty=100,
                    code="HK.00700",
                    trd_side=ft.TrdSide.BUY,
                    trd_env=ft.TrdEnv.SIMULATE,
                    order_type=ft.OrderType.NORMAL,
                    remark="Direct Test After Unlock"
                )
                print(f"   Direct Order Return Code: {ret}")
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
                    
                    print(f"\n🎉 BREAKTHROUGH! Direct simulation trading works!")
                    return True
                else:
                    print(f"   Direct order failed: {ret}")
            except Exception as e:
                print(f"   Exception during direct order: {str(e)}")
                
        else:
            print(f"   FAILED: Trading unlock failed with code {ret}")
            print(f"   Possible issues:")
            print(f"   1. Incorrect trading password")
            print(f"   2. Trading not enabled for this account")
            print(f"   3. Account type restrictions")
            
            if isinstance(unlock_data, dict):
                print(f"   Error details: {unlock_data}")

        # Clean up
        trade_ctx.close()
        return False

    except Exception as e:
        print(f"Trade unlock test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_trade_unlock())
    print(f"\n" + "=" * 60)
    if success:
        print("FINAL RESULT: TRADE UNLOCK SOLVED THE ISSUE!")
        print("✅ Simulation trading is now accessible")
        print("✅ The root cause was missing unlock_trade(password) call")
        print("✅ All trading operations now require unlock first")
        print("\nNext steps:")
        print("1. Always call unlock_trade(password) before any trading operations")
        print("2. Store password securely for automated trading")
        print("3. Start developing your quantitative trading strategies!")
    else:
        print("FINAL RESULT: Trade unlock failed")
        print("❌ The issue may be:")
        print("   - Incorrect trading password")
        print("   - Trading permissions not properly set up")
        print("   - Account requires additional activation")
        print("\nRecommendations:")
        print("1. Verify trading password in FutuNN app")
        print("2. Check account trading permissions")
        print("3. Contact Futu support if needed")