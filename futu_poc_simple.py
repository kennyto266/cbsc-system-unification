#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Futu POC Development - Simplified version for Windows compatibility
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Add Futu SDK path
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# Connection configuration
API_PORT = 1130
HOST = '127.0.0.1'
USER_ID = "2860386"

class FutuPOCTest:
    def __init__(self):
        self.quote_ctx = None
        self.trade_ctx = None
        self.api_port = API_PORT
        self.user_id = USER_ID

    async def test_connection(self):
        """Test basic connection"""
        print("=== Testing Futu API Connection ===")

        try:
            import futu as ft
            print(f"Futu API Version: {ft.__version__}")

            # Create quote context
            print(f"Connecting to API port {self.api_port}...")
            self.quote_ctx = ft.OpenQuoteContext(host=HOST, port=self.api_port)

            # Test connection
            ret, data = self.quote_ctx.get_global_state()

            if ret == ft.RET_OK:
                print("[SUCCESS] API connection successful!")
                print(f"Global state: {data}")
                return True
            else:
                print(f"[FAILED] API connection failed: {data}")
                return False

        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
            return False

    async def test_market_data(self):
        """Test market data retrieval"""
        print("\n=== Testing Market Data ===")

        try:
            import futu as ft

            # Test Hong Kong stocks
            test_stocks = ['HK.00700', 'HK.0388']
            market_data = []

            for stock_code in test_stocks:
                print(f"Getting {stock_code} data...")

                ret, data = self.quote_ctx.get_market_snapshot([stock_code])

                if ret == ft.RET_OK and data is not None and len(data) > 0:
                    stock_data = data.iloc[0]
                    stock_info = {
                        'code': stock_code,
                        'last_price': float(stock_data.get('last_price', 0)),
                        'volume': int(stock_data.get('volume', 0)),
                        'change_val': float(stock_data.get('change_val', 0)),
                        'change_rate': float(stock_data.get('change_rate', 0))
                    }
                    market_data.append(stock_info)

                    print(f"  {stock_code}: Price={stock_info['last_price']}, "
                          f"Volume={stock_info['volume']}, "
                          f"Change={stock_info['change_val']}")
                else:
                    print(f"  {stock_code}: Data retrieval failed")

                await asyncio.sleep(0.2)

            print(f"\nSuccessfully retrieved {len(market_data)} stocks data")
            return market_data

        except Exception as e:
            print(f"[ERROR] Market data test failed: {e}")
            return []

    async def test_demo_accounts(self):
        """Test demo accounts"""
        print("\n=== Testing Demo Accounts ===")

        try:
            import futu as ft

            # Create trade context
            self.trade_ctx = ft.OpenHKTradeContext(host=HOST, port=self.api_port)

            # Query demo accounts
            print("Querying demo accounts...")
            ret, data = self.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

            if ret == ft.RET_OK:
                if data is not None and len(data) > 0:
                    print(f"Found {len(data)} demo accounts:")

                    for index, row in data.iterrows():
                        acc_id = str(row.get('acc_id', ''))
                        total_assets = float(row.get('total_assets', 0))
                        cash = float(row.get('cash', 0))

                        print(f"  Account {index+1}:")
                        print(f"    ID: {acc_id}")
                        print(f"    Total Assets: {total_assets:.2f}")
                        print(f"    Cash: {cash:.2f}")

                    return True
                else:
                    print("No demo accounts found")
                    return False
            else:
                print(f"Demo account query failed: {data}")
                return False

        except Exception as e:
            print(f"[ERROR] Demo account test failed: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        print("\n=== Cleaning Up Resources ===")

        try:
            if self.quote_ctx:
                self.quote_ctx.close()
                print("Quote context closed")

            if self.trade_ctx:
                self.trade_ctx.close()
                print("Trade context closed")

        except Exception as e:
            print(f"Cleanup failed: {e}")

    async def run_complete_test(self):
        """Run complete POC test"""
        print("Futu POC Development Test")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        print(f"User ID: {self.user_id}")
        print(f"API Port: {self.api_port}")
        print("-" * 50)

        results = {
            'connection': False,
            'market_data': [],
            'demo_accounts': False
        }

        try:
            # 1. Test connection
            results['connection'] = await self.test_connection()

            if results['connection']:
                # 2. Test market data
                results['market_data'] = await self.test_market_data()

                # 3. Test demo accounts
                results['demo_accounts'] = await self.test_demo_accounts()
            else:
                print("[STOP] Connection failed, stopping further tests")

        except Exception as e:
            print(f"[ERROR] Test process failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        return results

def generate_test_report(results):
    """Generate test report"""
    print("\n" + "=" * 50)
    print("POC TEST RESULTS")
    print("-" * 30)

    status_map = {
        True: "PASS",
        False: "FAIL"
    }

    print(f"API Connection: {status_map.get(results['connection'])}")
    print(f"Market Data: {len(results['market_data'])} stocks retrieved")
    print(f"Demo Accounts: {status_map.get(results['demo_accounts'])}")

    # Save detailed results
    report_data = {
        'user_id': USER_ID,
        'api_port': API_PORT,
        'test_time': datetime.now().isoformat(),
        'results': results
    }

    try:
        with open('futu_poc_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed results saved to: futu_poc_test_results.json")
    except Exception as e:
        print(f"Failed to save results: {e}")

    # Summary
    success_count = sum([
        results['connection'],
        len(results['market_data']) > 0,
        results['demo_accounts']
    ])

    total_tests = 3
    success_rate = success_count / total_tests

    if success_rate == 1.0:
        print(f"\n[SUCCESS] All POC tests passed!")
        print("[READY] Futu API is fully ready")
        print("[NEXT] Can start real-time trading system development")
        print("\nRecommended next steps:")
        print("1. Real-time market monitoring")
        print("2. Trading strategy execution")
        print("3. Risk management system")
        print("4. Backtest engine integration")
        print("5. Web interface development")
    elif success_rate >= 0.7:
        print(f"\n[PARTIAL] Most POC functions available (Success rate: {success_rate:.1%})")
        print("[GOOD] Basic functions working, can start development")
    else:
        print(f"\n[WARNING] Some functions need checking (Success rate: {success_rate:.1%})")
        print("[FIX] Please check related configuration")

async def main():
    """Main function"""
    poc_test = FutuPOCTest()
    results = await poc_test.run_complete_test()
    generate_test_report(results)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()