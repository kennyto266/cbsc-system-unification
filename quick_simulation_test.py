#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Simulation Test - Fast verification after pdt_protection fix
"""

import os
import sys
import asyncio
from datetime import datetime

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Add Futu SDK path
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# Connection configuration
API_PORT = 1130
HOST = '127.0.0.1'

async def quick_test():
    """Quick test of simulation account access"""
    print("=== Quick Simulation Access Test ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)

    try:
        import futu as ft

        # Test connection
        print("\n1. Testing API Connection...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("   Connection established")

        # Test simulation account
        print("\n2. Testing Simulation Account...")
        ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

        print(f"   Return Code: {ret}")

        if ret == ft.RET_OK:
            print("   [SUCCESS] Simulation Account Available!")

            if hasattr(data, 'shape') and data.shape[0] > 0:
                print(f"   Found {data.shape[0]} simulation account(s)")

                # Get first account info
                first_row = data.iloc[0]
                try:
                    acc_id = first_row.get('acc_id', 'N/A')
                    currency = first_row.get('currency', 'N/A')
                    cash = first_row.get('cash', 0)
                    total_assets = first_row.get('total_assets', 0)

                    print(f"   First Account ID: {acc_id}")
                    print(f"   Currency: {currency}")
                    print(f"   Cash: {cash:,.2f}")
                    print(f"   Total Assets: {total_assets:,.2f}")

                    print("\n   [EXCELLENT] pdt_protection fix was successful!")
                    print("   You can now use simulation trading features.")

                except Exception as e:
                    print(f"   Error reading account details: {e}")
            else:
                print("   [INFO] Simulation query returned but no accounts found")
        else:
            print("   [FAILED] Simulation Account Still Not Available")
            print(f"   Error Code: {ret}")
            if isinstance(data, str):
                print(f"   Error (first 50 chars): {data[:50]}...")

            print("\n   Troubleshooting:")
            print("   1. Ensure FutuOpenD was started with --pdt_protection=0")
            print("   2. Wait 30 seconds after startup")
            print("   3. Check if simulation is activated in NiuNiu app")
            print("   4. Try restarting with the provided batch file")

        trade_ctx.close()

    except Exception as e:
        print(f"Test failed: {e}")

    print("\n3. Next Steps:")
    print("   If SUCCESS: Start developing with simulation trading")
    print("   If FAILED: Apply the pdt_protection fix and retry")

async def main():
    """Main function"""
    await quick_test()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test execution failed: {e}")