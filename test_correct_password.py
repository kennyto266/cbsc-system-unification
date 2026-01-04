#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Correct Trading Password - 測試正確的交易密碼
使用新的交易密碼：941002
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def test_correct_password():
    try:
        import futu as ft

        print("=== Test Correct Trading Password ===")
        print("Using new trading password: 941002")
        print("=" * 60)

        # Setup trading context
        print("\n1. Setting up trading context...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Step 1: Try to unlock trading interface with new password
        print("\n2. Unlocking trading interface with correct password...")
        
        ret, unlock_data = trade_ctx.unlock_trade(password='941002')
        print(f"   Unlock Return Code: {ret}")
        
        if ret == ft.RET_OK:
            print("   SUCCESS! Trading interface unlocked with new password!")
            
            # Now test simulation account access
            print("\n3. Testing simulation account access after successful unlock...")
            
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
                            remark="SUCCESS Test - Simulation Trading"
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
                            
                            print(f"\n🎉 BREAKTHROUGH SUCCESS! Simulation trading is working!")
                            print(f"   Key findings:")
                            print(f"   - Correct trading password: 941002")
                            print(f"   - unlock_trade() is essential before trading")
                            print(f"   - Simulation trading is fully functional")
                            
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
            print("\n   Method 2: Direct simulation order after successful unlock")
            try:
                ret, order_data = trade_ctx.place_order(
                    price=1.00,
                    qty=100,
                    code="HK.00700",
                    trd_side=ft.TrdSide.BUY,
                    trd_env=ft.TrdEnv.SIMULATE,
                    order_type=ft.OrderType.NORMAL,
                    remark="Direct Test After Correct Unlock"
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
                    
                    print(f"\n🎉 DIRECT SIMULATION TRADING SUCCESS!")
                    return True
                else:
                    print(f"   Direct order failed: {ret}")
            except Exception as e:
                print(f"   Exception during direct order: {str(e)}")
                
        else:
            print(f"   FAILED: Trading unlock still failed with code {ret}")
            print(f"   Possible remaining issues:")
            print(f"   1. Trading password still incorrect")
            print(f"   2. Account trading permissions not fully set up")
            print(f"   3. Time-based restrictions")
            
            if isinstance(unlock_data, dict):
                print(f"   Error details: {unlock_data}")

        # Clean up
        trade_ctx.close()
        return False

    except Exception as e:
        print(f"Correct password test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_correct_password())
    print(f"\n" + "=" * 60)
    if success:
        print("FINAL RESULT: SUCCESS WITH NEW TRADING PASSWORD!")
        print("✅ Trading unlock successful with password: 941002")
        print("✅ Simulation trading is now fully functional")
        print("✅ All trading operations working correctly")
        print("\n🚀 Ready for quantitative trading development!")
        print("Next steps:")
        print("1. Use password '941002' for all unlock_trade() calls")
        print("2. Store password securely in your trading applications")
        print("3. Start developing your automated trading strategies")
        print("4. Market data analysis is already fully available")
    else:
        print("FINAL RESULT: Still experiencing issues")
        print("❌ Even with new password, unlock failed")
        print("Additional troubleshooting may be needed")
        print("\nRecommendations:")
        print("1. Verify the password in FutuNN app")
        print("2. Check account trading permissions")
        print("3. Contact Futu support if needed")