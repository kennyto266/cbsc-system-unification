#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Account Error - Capture exact error messages
"""

import os
import sys
import json
from datetime import datetime

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Add Futu SDK path
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# Connection configuration
API_PORT = 1130
HOST = '127.0.0.1'

def main():
    """Main function to debug account errors"""
    print("Futu Account Debug Tool")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)

    try:
        import futu as ft
        print(f"Futu API Version: {ft.__version__}")

        # Create trade context
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        # Test simulation account
        print("\nTesting Simulation Account...")
        ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

        print(f"Return Code: {ret}")
        print(f"Data Type: {type(data)}")

        # Save raw error data to file
        error_info = {
            'return_code': ret,
            'data_type': str(type(data)),
            'timestamp': datetime.now().isoformat()
        }

        if isinstance(data, str):
            error_info['error_message'] = data
            print(f"Error Message: {data}")
        elif hasattr(data, '__dict__'):
            error_info['data_attributes'] = list(data.__dict__.keys())
        else:
            try:
                error_info['data_repr'] = repr(data)
            except:
                error_info['data_repr'] = 'Cannot represent data'

        # Save to file
        with open('account_debug_info.json', 'w', encoding='utf-8') as f:
            json.dump(error_info, f, indent=2, ensure_ascii=False)

        print(f"\nDebug info saved to: account_debug_info.json")

        # Try different approach - check all environments
        print("\nTrying different query methods...")

        # Method 1: Try without environment
        try:
            print("Method 1: No environment specified")
            ret2, data2 = trade_ctx.accinfo_query()
            print(f"Method 1 Return Code: {ret2}")
            if ret2 == ft.RET_OK:
                print("[SUCCESS] Default query worked!")
                if hasattr(data2, 'shape'):
                    print(f"Found {data2.shape[0]} accounts")
        except Exception as e:
            print(f"Method 1 failed: {e}")

        # Method 2: Try getting global state to confirm connection
        try:
            print("\nMethod 2: Check global state")
            quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
            ret3, data3 = quote_ctx.get_global_state()
            print(f"Global State Return Code: {ret3}")
            if ret3 == ft.RET_OK:
                print("Connection is working")
                print(f"Trading Login: {data3.get('trd_logined', False)}")
                print(f"Quote Login: {data3.get('qot_logined', False)}")
            quote_ctx.close()
        except Exception as e:
            print(f"Global state check failed: {e}")

        # Method 3: Try checking if user has proper permissions
        try:
            print("\nMethod 3: Check user permissions")
            quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
            ret4, data4 = quote_ctx.get_user_info()
            print(f"User Info Return Code: {ret4}")
            if ret4 == ft.RET_OK:
                print("User permissions available")
                if isinstance(data4, dict):
                    print(f"User ID: {data4.get('user_id', 'N/A')}")
                    print(f"Account Type: {data4.get('account_type', 'N/A')}")
            quote_ctx.close()
        except Exception as e:
            print(f"User info check failed: {e}")

        trade_ctx.close()

        print("\n=== Diagnostic Summary ===")
        print("Possible issues:")
        print("1. Simulation account not properly activated in the app")
        print("2. API permissions issue")
        print("3. Need to restart FutuOpenD client")
        print("4. Account synchronization delay")

    except Exception as e:
        print(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Script failed: {e}")
        import traceback
        traceback.print_exc()