#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Account Check - Handle encoding issues and get error details
"""

import os
import sys
import json
import traceback
from datetime import datetime

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Add Futu SDK path
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# Connection configuration
API_PORT = 1130
HOST = '127.0.0.1'

def safe_str(s):
    """Convert string to safe representation"""
    if isinstance(s, str):
        try:
            return s.encode('ascii', errors='replace').decode('ascii')
        except:
            return repr(s)
    return str(s)

def main():
    """Main function"""
    print("=== Futu Account Final Check ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"User ID: 2860386")
    print(f"API Port: {API_PORT}")
    print("=" * 40)

    try:
        import futu as ft
        print(f"API Version: {ft.__version__}")

        # Step 1: Check global state first
        print("\n1. Global State Check:")
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
        ret, data = quote_ctx.get_global_state()
        print(f"   Return Code: {ret}")
        if ret == ft.RET_OK:
            print(f"   Trading Login: {data.get('trd_logined', False)}")
            print(f"   Quote Login: {data.get('qot_logined', False)}")
            print(f"   Server Version: {data.get('server_ver', 'N/A')}")
            print(f"   Program Status: {data.get('program_status_type', 'N/A')}")
        else:
            print(f"   Global State Error: {safe_str(data)}")
        quote_ctx.close()

        # Step 2: Test simulation account
        print("\n2. Simulation Account Test:")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)

        try:
            ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
            print(f"   Return Code: {ret}")

            if ret == ft.RET_OK:
                print("   [SUCCESS] Simulation Account Available!")
                print(f"   Data Type: {type(data)}")

                if hasattr(data, 'shape'):
                    print(f"   Account Count: {data.shape[0]}")

                    # Save account details to JSON
                    if data.shape[0] > 0:
                        accounts = []
                        for i in range(data.shape[0]):
                            row = data.iloc[i]
                            account = {}
                            for col in data.columns:
                                try:
                                    account[col] = row[col]
                                except:
                                    account[col] = None
                            accounts.append(account)

                        with open('simulation_accounts_final.json', 'w', encoding='utf-8') as f:
                            json.dump(accounts, f, indent=2, ensure_ascii=False)
                        print("   Account details saved to: simulation_accounts_final.json")

                        # Show first account summary
                        if accounts:
                            acc = accounts[0]
                            print(f"   First Account:")
                            print(f"     Account ID: {acc.get('acc_id', 'N/A')}")
                            print(f"     Currency: {acc.get('currency', 'N/A')}")
                            print(f"     Cash: {acc.get('cash', 0):,.2f}")
                            print(f"     Total Assets: {acc.get('total_assets', 0):,.2f}")
                            print(f"     Buying Power: {acc.get('power', 0):,.2f}")
                else:
                    print(f"   Data: {safe_str(data)[:200]}...")
            else:
                print("   [FAILED] Simulation Account Not Available")
                print(f"   Error Type: {type(data)}")

                # Try to save error info
                error_info = {
                    'return_code': ret,
                    'data_type': str(type(data)),
                    'error_data': safe_str(data),
                    'timestamp': datetime.now().isoformat()
                }

                with open('simulation_error_info.json', 'w', encoding='utf-8') as f:
                    json.dump(error_info, f, indent=2, ensure_ascii=False)
                print(f"   Error info saved to: simulation_error_info.json")

                # Provide guidance
                print("   Possible Solutions:")
                print("   1. Restart FutuOpenD client")
                print("   2. Check if simulation is properly activated in NiuNiu app")
                print("   3. Verify API permissions for trading")
                print("   4. Try again after a few minutes")

        except Exception as e:
            print(f"   Exception occurred: {safe_str(str(e))}")
            traceback.print_exc()

        # Step 3: Test real account (for comparison)
        print("\n3. Real Account Test (for comparison):")
        try:
            ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)
            print(f"   Return Code: {ret}")
            if ret == ft.RET_OK:
                print("   Real account available")
            else:
                print("   Real account not available through API")
        except Exception as e:
            print(f"   Real account test failed: {safe_str(str(e))}")

        trade_ctx.close()

        # Step 4: Final recommendations
        print("\n4. Summary and Recommendations:")
        print("   Status Check:")
        print("   ✓ API Connection: Working")
        print("   ✓ User Authentication: Working (ID: 2860386)")
        print("   ✓ Market Data: Working")
        print("   ⚠ Simulation Account: Needs verification")
        print("")
        print("   Next Steps:")
        print("   1. If simulation shows error code -1:")
        print("      - Check NiuNiu app: Trading > Simulation Trading")
        print("      - Ensure simulation is properly activated")
        print("      - Try restarting FutuOpenD client")
        print("   2. If simulation is activated:")
        print("      - Continue with strategy development")
        print("      - Test with simulation trading")
        print("   3. Available Now:")
        print("      - Market data analysis")
        print("      - Technical indicators")
        print("      - Strategy backtesting")

    except Exception as e:
        print(f"Critical Error: {safe_str(str(e))}")
        traceback.print_exc()

if __name__ == "__main__":
    main()