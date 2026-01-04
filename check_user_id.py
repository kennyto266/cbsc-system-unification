#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check User ID - 檢查當前登錄的用戶 ID
"""

import os
import sys
import asyncio

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def check_user_id():
    try:
        import futu as ft

        print("=== Check Current User ID ===")
        print("=" * 50)

        # Setup quote context
        print("\n1. Setting up quote context...")
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        # Get global state
        print("\n2. Getting global state...")
        ret, state = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print(f"   Server Version: {state.get('server_ver', 'Unknown')}")
            print(f"   Quote Login: {state.get('qot_logined', False)}")
            print(f"   Trade Login: {state.get('trd_logined', False)}")
            
            # Try to get account info without unlock first
            print("\n3. Checking account info...")
            
            # Setup trade context
            trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
            
            # Try different approaches to get user ID
            print("   Testing different account query methods...")
            
            # Method 1: Try get_acc_list (might work)
            try:
                ret, accounts = trade_ctx.get_acc_list()
                print(f"   get_acc_list Return Code: {ret}")
                if ret == ft.RET_OK:
                    print(f"   SUCCESS! Found {len(accounts)} accounts")
                    for i, acc in enumerate(accounts):
                        acc_id = acc.get('acc_id', 'N/A')
                        trd_env = acc.get('trd_env', 'N/A')
                        print(f"   Account {i+1}: ID={acc_id}, Env={trd_env}")
                else:
                    print(f"   get_acc_list failed: {ret}")
            except Exception as e:
                print(f"   get_acc_list Exception: {str(e)}")
            
            # Method 2: Try accinfo_query with SIMULATE
            try:
                ret, acc_info = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                print(f"   accinfo_query(SIMULATE) Return Code: {ret}")
                if ret == ft.RET_OK and acc_info.shape[0] > 0:
                    print(f"   SUCCESS! Simulation account info:")
                    for i, acc in acc_info.iterrows():
                        acc_id = acc['acc_id']
                        acc_type = acc['acc_type']
                        print(f"   Account: {acc_id}, Type: {acc_type}")
                else:
                    print(f"   SIMULATE account info failed: {ret}")
            except Exception as e:
                print(f"   accinfo_query Exception: {str(e)}")
            
            # Method 3: Try accinfo_query with REAL
            try:
                ret, acc_info = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)
                print(f"   accinfo_query(REAL) Return Code: {ret}")
                if ret == ft.RET_OK and acc_info.shape[0] > 0:
                    print(f"   SUCCESS! Real account info:")
                    for i, acc in acc_info.iterrows():
                        acc_id = acc['acc_id']
                        acc_type = acc['acc_type']
                        print(f"   Account: {acc_id}, Type: {acc_type}")
                else:
                    print(f"   REAL account info failed: {ret}")
            except Exception as e:
                print(f"   accinfo_query Exception: {str(e)}")
            
            trade_ctx.close()
            
        else:
            print(f"   Global state failed: {ret}")
        
        # Check Futu OpenD config for user info
        print("\n4. Checking FutuOpenD configuration...")
        try:
            import json
            config_path = r"C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\vuex.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                user_id = config['state']['ftOpenDState'].get('userID', 'Unknown')
                nick_name = config['state']['ftOpenDState'].get('nickName', 'Unknown')
                login_status = config['state']['ftOpenDState'].get('loginStatus', 'Unknown')
                
                print(f"   User ID from config: {user_id}")
                print(f"   Nick Name: {nick_name}")
                print(f"   Login Status: {login_status}")
                print(f"   Sub Quota: {config['state']['ftOpenDState'].get('subQuota', 'Unknown')}")
                print(f"   Used Sub Quota: {config['state']['ftOpenDState'].get('usedSubQuota', 'Unknown')}")
            else:
                print(f"   Config file not found")
        except Exception as e:
            print(f"   Config check failed: {e}")
        
        quote_ctx.close()
        
        print(f"\n" + "=" * 50)
        print("USER ID ANALYSIS:")
        print("Please check:")
        print("1. The correct User ID from the outputs above")
        print("2. If there are multiple User IDs, which one is correct")
        print("3. Whether the FutuNN app login matches this User ID")
        
    except Exception as e:
        print(f"User ID check failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_user_id())