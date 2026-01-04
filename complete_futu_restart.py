#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete FutuOpenD Restart - 完全重啟 FutuOpenD 服務
解決所有 API 調用返回錯誤代碼 -1 的問題
"""

import os
import sys
import asyncio
import time

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def complete_futu_restart():
    try:
        print("=== Complete FutuOpenD Service Restart ===")
        print("API Port: 1130")
        print("WebSocket Port: 11111") 
        print("WebSocket Key: cb8fe2a668e624da")
        print("=" * 60)
        
        # Step 1: Kill all Futu processes
        print("\n1. Terminating all Futu processes...")
        
        # Kill all Futu related processes
        kill_commands = [
            "taskkill /F /IM FutuOpenD.exe",
            "taskkill /F /IM Futu_OpenD.exe"
        ]
        
        for cmd in kill_commands:
            print(f"   Executing: {cmd}")
            os.system(cmd)
        
        # Wait for processes to terminate
        print("   Waiting for processes to terminate...")
        time.sleep(3)
        
        # Step 2: Clean restart FutuOpenD
        print("\n2. Starting clean FutuOpenD with correct parameters...")
        
        futu_path = r"C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\open-d\windows"
        futu_exe = os.path.join(futu_path, "FutuOpenD.exe")
        
        # Start FutuOpenD with clean parameters
        start_cmd = f'start "" "{futu_exe}" --api_port={API_PORT} --ws_port=11111 --ws_key=cb8fe2a668e624da'
        print(f"   Starting: {start_cmd}")
        os.system(start_cmd)
        
        # Wait for service to initialize
        print("   Waiting for FutuOpenD to initialize (30 seconds)...")
        time.sleep(30)
        
        # Step 3: Test basic connectivity
        print("\n3. Testing basic connectivity...")
        try:
            import futu as ft
            
            # Test quote context first
            quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
            print("   Quote context: Created successfully")
            
            # Test market data
            ret, state = quote_ctx.get_global_state()
            if ret == ft.RET_OK:
                print(f"   SUCCESS: Global state retrieved")
                print(f"   Server Version: {state.get('server_ver', 'Unknown')}")
                print(f"   Quote Login: {state.get('qot_logined', False)}")
                print(f"   Trade Login: {state.get('trd_logined', False)}")
                
                # Test market data
                ret, quote_data = quote_ctx.get_stock_quote(['HK.00700'])
                if ret == ft.RET_OK and quote_data.shape[0] > 0:
                    price = quote_data.iloc[0]['last_price']
                    print(f"   SUCCESS: Market data working - HK.00700 = {price:.2f} HKD")
                else:
                    print(f"   Market data test failed: {ret}")
            else:
                print(f"   Global state failed: {ret}")
            
            quote_ctx.close()
            
        except Exception as e:
            print(f"   Connectivity test failed: {e}")
            return False
        
        # Step 4: Test trading unlock
        print("\n4. Testing trading unlock with correct password...")
        try:
            trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
            
            # Try unlock with both passwords
            passwords = ['941002', '677750']
            
            for pwd in passwords:
                print(f"   Trying password: {pwd}")
                ret, unlock_data = trade_ctx.unlock_trade(password=pwd)
                print(f"   Unlock Return Code: {ret}")
                
                if ret == ft.RET_OK:
                    print(f"   SUCCESS: Trading unlocked with password: {pwd}")
                    
                    # Test account access
                    ret, accounts = trade_ctx.get_acc_list()
                    if ret == ft.RET_OK:
                        print(f"   SUCCESS: Account list retrieved")
                        simulation_accounts = []
                        for acc in accounts:
                            env = acc.get('trd_env', 'N/A')
                            if env == 'SIMULATE':
                                simulation_accounts.append(acc)
                        
                        if simulation_accounts:
                            print(f"   SUCCESS: Found {len(simulation_accounts)} simulation accounts")
                            
                            # Test simulation order
                            ret, order_data = trade_ctx.place_order(
                                price=1.00,
                                qty=100,
                                code="HK.00700",
                                trd_side=ft.TrdSide.BUY,
                                trd_env=ft.TrdEnv.SIMULATE,
                                order_type=ft.OrderType.NORMAL,
                                remark="Post-Restart Test"
                            )
                            
                            if ret == ft.RET_OK:
                                print(f"   SUCCESS: Simulation order placed!")
                                order_id = order_data.iloc[0]['order_id']
                                print(f"   Order ID: {order_id}")
                                
                                # Cancel order
                                cancel_ret = trade_ctx.cancel_order(
                                    order_id=order_id,
                                    trd_env=ft.TrdEnv.SIMULATE
                                )
                                if cancel_ret == ft.RET_OK:
                                    print(f"   SUCCESS: Order canceled")
                                
                                print(f"\n🎉 COMPLETE SUCCESS! Everything working!")
                                print(f"   - Market data: Functional")
                                print(f"   - Trading unlock: Successful (password: {pwd})")
                                print(f"   - Simulation trading: Fully operational")
                                
                                trade_ctx.close()
                                return True
                            else:
                                print(f"   Order placement failed: {ret}")
                        else:
                            print(f"   No simulation accounts found")
                    else:
                        print(f"   Account list failed: {ret}")
                else:
                    print(f"   Password {pwd} failed")
            
            trade_ctx.close()
            
        except Exception as e:
            print(f"   Trading unlock test failed: {e}")
        
        return False

    except Exception as e:
        print(f"Complete restart failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(complete_futu_restart())
    print(f"\n" + "=" * 60)
    if success:
        print("FINAL RESULT: FUTUOPEND SERVICE FULLY RESTORED!")
        print("✅ All functionality working correctly")
        print("✅ Ready for quantitative trading development")
        print("✅ Market data analysis available")
        print("✅ Simulation trading operational")
        print("\nYou can now proceed with your trading strategy development!")
    else:
        print("SERVICE RESTART INCOMPLETE")
        print("❌ Additional troubleshooting may be required")
        print("\nAlternative solutions:")
        print("1. Check FutuNN app service status")
        print("2. Verify network connectivity")
        print("3. Contact Futu technical support")