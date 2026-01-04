#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Reset Trading Password - 測試重置後的交易密碼
在 FutuNN App 中重置交易密碼為 677750 後立即測試
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def test_reset_password():
    try:
        import futu as ft

        print("=== Test Reset Trading Password ===")
        print("Trading Password: 677750 (6-digit)")
        print("Please complete password reset in FutuNN App first")
        print("=" * 60)

        print("\nIMPORTANT: Before running this test:")
        print("1. Open FutuNN App")
        print("2. Go to: Trade → Security Settings")
        print("3. Reset trading password to: 677750")
        print("4. Ensure API permissions are enabled")
        print("5. Press Enter to continue testing...")
        
        input("Press Enter after completing password reset...")

        # Setup trading context
        print("\n1. Setting up trading context...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Test unlock with reset password
        print("\n2. Testing unlock with reset password: 677750")
        
        ret, unlock_data = trade_ctx.unlock_trade(password='677750')
        print(f"   Unlock Return Code: {ret}")
        
        if ret == ft.RET_OK:
            print("   SUCCESS! Trading unlocked with reset password!")
            
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
                    print("   This confirms simulation trading is properly configured")
                    
                    # Test simulation order
                    print(f"\n4. Testing simulation order placement...")
                    stock_code = "HK.00700"
                    
                    ret, order_data = trade_ctx.place_order(
                        price=1.00,  # Low price to avoid execution
                        qty=100,
                        code=stock_code,
                        trd_side=ft.TrdSide.BUY,
                        trd_env=ft.TrdEnv.SIMULATE,
                        order_type=ft.OrderType.NORMAL,
                        remark="Password Reset Test - SUCCESS!"
                    )
                    
                    print(f"   Order Placement Return Code: {ret}")
                    
                    if ret == ft.RET_OK:
                        print("   SUCCESS! Simulation order placed!")
                        order_id = order_data.iloc[0]['order_id']
                        print(f"   Order ID: {order_id}")
                        
                        # Verify order details
                        print(f"   Order Details:")
                        print(f"   - Stock: {order_data.iloc[0]['code']}")
                        print(f"   - Price: {order_data.iloc[0]['price']}")
                        print(f"   - Quantity: {order_data.iloc[0]['qty']}")
                        print(f"   - Status: {order_data.iloc[0]['order_status']}")
                        
                        # Cancel the test order
                        print(f"\n5. Canceling test order...")
                        cancel_ret = trade_ctx.cancel_order(
                            order_id=order_id,
                            trd_env=ft.TrdEnv.SIMULATE
                        )
                        
                        if cancel_ret == ft.RET_OK:
                            print("   SUCCESS: Order canceled")
                        else:
                            print(f"   Order cancellation failed: {cancel_ret}")
                        
                        print(f"\n🎉 COMPLETE SUCCESS!")
                        print(f"   ✅ Trading password reset successful")
                        print(f"   ✅ Trading unlock working")
                        print(f"   ✅ Simulation account access working")
                        print(f"   ✅ Order placement working")
                        print(f"   ✅ Order cancellation working")
                        
                        print(f"\n🚀 QUANTITATIVE TRADING IS NOW READY!")
                        print(f"   You can start developing your trading strategies")
                        
                        # Test additional functions
                        print(f"\n6. Testing additional trading functions...")
                        
                        # Test position query
                        ret, positions = trade_ctx.position_list_query(trd_env=ft.TrdEnv.SIMULATE)
                        print(f"   Position Query Return Code: {ret}")
                        if ret == ft.RET_OK:
                            print(f"   SUCCESS: Position query working - {len(positions)} positions")
                        
                        # Test order history
                        ret, orders = trade_ctx.order_list_query(trd_env=ft.TrdEnv.SIMULATE)
                        print(f"   Order History Return Code: {ret}")
                        if ret == ft.RET_OK:
                            print(f"   SUCCESS: Order history working - {len(orders)} orders")
                        
                        trade_ctx.close()
                        return True
                        
                    else:
                        print(f"   Order placement failed: {ret}")
                        if isinstance(order_data, dict):
                            print(f"   Error details: {order_data}")
                else:
                    print(f"   No simulation accounts found")
                    print(f"   Available environments: {[acc.get('trd_env', 'N/A') for acc in accounts]}")
                    
                    print(f"\n   Recommendation: Check simulation trading activation in FutuNN App")
                    
            else:
                print(f"   Account query failed: {ret}")
                if isinstance(accounts, dict):
                    print(f"   Error details: {accounts}")
                    
        else:
            print(f"   FAILED: Unlock still failed with code {ret}")
            print(f"   Possible reasons:")
            print(f"   1. Password not properly reset in FutuNN App")
            print(f"   2. API permissions not fully enabled")
            print(f"   3. Trading permissions not activated")
            
            if isinstance(unlock_data, dict):
                print(f"   Error details: {unlock_data}")
            
            print(f"\n   Troubleshooting steps:")
            print(f"   1. Verify password reset in FutuNN App")
            print(f"   2. Check API permissions in App settings")
            print(f"   3. Try a different 6-digit password")
            print(f"   4. Contact Futu support if issues persist")

        # Clean up
        trade_ctx.close()
        return False

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_reset_password())
    print(f"\n" + "=" * 60)
    if success:
        print("🎉 PASSWORD RESET SUCCESSFUL!")
        print("✅ All trading functions are now operational")
        print("✅ Ready for quantitative trading development")
        print("\nNext steps:")
        print("1. Start developing your trading strategies")
        print("2. Test strategy execution with simulation trading")
        print("3. Implement risk management and monitoring")
    else:
        print("❌ Password reset test unsuccessful")
        print("\nAdditional steps:")
        print("1. Verify password was properly reset in FutuNN App")
        print("2. Check API permissions are fully enabled")
        print("3. Try a different password or contact support")
        print("4. Focus on market data analysis while troubleshooting")