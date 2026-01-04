#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Demo Account Information
"""

import os
import sys
import json
import asyncio
from datetime import datetime

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Add Futu SDK path
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# Connection configuration
API_PORT = 1130
HOST = '127.0.0.1'

class DemoAccountChecker:
    def __init__(self):
        self.trade_ctx = None
        self.api_port = API_PORT

    async def check_demo_accounts(self):
        """Check all demo accounts"""
        print("=== Checking Demo Account Information ===")

        try:
            import futu as ft
            print(f"Futu API Version: {ft.__version__}")

            # Create trade context
            self.trade_ctx = ft.OpenHKTradeContext(host=HOST, port=self.api_port)

            # Query demo accounts
            print("Querying demo accounts...")
            ret, data = self.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

            if ret == ft.RET_OK and data is not None and len(data) > 0:
                print(f"Found {len(data)} demo accounts:")
                print("-" * 60)

                accounts = []
                for index, row in data.iterrows():
                    account_info = {
                        'account_index': index + 1,
                        'acc_id': str(row.get('acc_id', '')),
                        'acc_type': str(row.get('acc_type', '')),
                        'currency': str(row.get('currency', '')),
                        'cash': float(row.get('cash', 0)),
                        'total_assets': float(row.get('total_assets', 0)),
                        'market_val': float(row.get('market_val', 0)),
                        'power': float(row.get('power', 0)),
                        'max_withdraw': float(row.get('max_withdraw', 0)),
                        'finance': float(row.get('finance', 0)),
                        'interest': float(row.get('interest', 0)),
                        'trade_pwd_required': bool(row.get('trade_pwd_required', False)),
                        'aid_delay_trd': bool(row.get('aid_delay_trd', False)),
                        'aid_acc_num': str(row.get('aid_acc_num', ''))
                    }
                    accounts.append(account_info)

                    print(f"Account {account_info['account_index']}:")
                    print(f"  Account ID: {account_info['acc_id']}")
                    print(f"  Account Type: {account_info['acc_type']}")
                    print(f"  Currency: {account_info['currency']}")
                    print(f"  Cash: {account_info['cash']:,.2f}")
                    print(f"  Total Assets: {account_info['total_assets']:,.2f}")
                    print(f"  Market Value: {account_info['market_val']:,.2f}")
                    print(f"  Buying Power: {account_info['power']:,.2f}")
                    print(f"  Max Withdraw: {account_info['max_withdraw']:,.2f}")
                    print(f"  Financing: {account_info['finance']:,.2f}")
                    print(f"  Interest: {account_info['interest']:,.2f}")
                    print(f"  Trade Password Required: {account_info['trade_pwd_required']}")
                    print(f"  Delay Trading: {account_info['aid_delay_trd']}")
                    print(f"  AID Account: {account_info['aid_acc_num']}")
                    print("-" * 60)

                return accounts

            else:
                print("No demo accounts found or query failed")
                print(f"Return code: {ret}")
                print(f"Error data: {data}")
                return []

        except Exception as e:
            print(f"Error checking demo accounts: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def check_positions(self, acc_id):
        """Check positions for specific account"""
        print(f"\n=== Checking Positions for Account {acc_id} ===")

        try:
            import futu as ft

            # Query positions
            ret, data = self.trade_ctx.position_list_query(
                trd_env=ft.TrdEnv.SIMULATE,
                acc_id=acc_id
            )

            if ret == ft.RET_OK and data is not None and len(data) > 0:
                print(f"Found {len(data)} positions:")
                print("-" * 40)

                positions = []
                for index, row in data.iterrows():
                    pos_info = {
                        'code': str(row.get('code', '')),
                        'qty': float(row.get('qty', 0)),
                        'can_sell_qty': float(row.get('can_sell_qty', 0)),
                        'cost_price': float(row.get('cost_price', 0)),
                        'cost_price_valid': bool(row.get('cost_price_valid', False)),
                        'market_val': float(row.get('market_val', 0)),
                        'unrealized_pl': float(row.get('unrealized_pl', 0)),
                        'unrealized_pl_ratio': float(row.get('unrealized_pl_ratio', 0)),
                        'realized_pl': float(row.get('realized_pl', 0)),
                        'position_side': str(row.get('position_side', '')),
                        'security_name': str(row.get('security_name', ''))
                    }
                    positions.append(pos_info)

                    print(f"Position {index + 1}:")
                    print(f"  Stock Code: {pos_info['code']}")
                    print(f"  Stock Name: {pos_info['security_name']}")
                    print(f"  Quantity: {pos_info['qty']:,.0f}")
                    print(f"  Sellable: {pos_info['can_sell_qty']:,.0f}")
                    print(f"  Cost Price: {pos_info['cost_price']:.4f}")
                    print(f"  Market Value: {pos_info['market_val']:,.2f}")
                    print(f"  Unrealized P&L: {pos_info['unrealized_pl']:,.2f}")
                    print(f"  Unrealized P&L %: {pos_info['unrealized_pl_ratio']*100:.2f}%")
                    print(f"  Realized P&L: {pos_info['realized_pl']:,.2f}")
                    print("-" * 40)

                return positions
            else:
                print("No positions found")
                return []

        except Exception as e:
            print(f"Error checking positions: {e}")
            return []

    async def check_funds(self, acc_id):
        """Check fund flow for account"""
        print(f"\n=== Checking Fund Flow for Account {acc_id} ===")

        try:
            import futu as ft

            # Query fund flow
            ret, data = self.trade_ctx.funds_flow(
                trd_env=ft.TrdEnv.SIMULATE,
                acc_id=acc_id
            )

            if ret == ft.RET_OK and data is not None and len(data) > 0:
                print(f"Found {len(data)} fund flow records:")
                print("-" * 40)

                for index, row in data.iterrows():
                    print(f"Record {index + 1}:")
                    print(f"  Time: {row.get('time', '')}")
                    print(f"  Business Type: {row.get('business_type', '')}")
                    print(f"  Business Name: {row.get('business_name', '')}")
                    print(f"  Amount: {float(row.get('amount', 0)):,.2f}")
                    print(f"  Balance: {float(row.get('balance', 0)):,.2f}")
                    print(f"  Currency: {row.get('currency', '')}")
                    print("-" * 40)

            else:
                print("No fund flow records found")

        except Exception as e:
            print(f"Error checking fund flow: {e}")

    def cleanup(self):
        """Clean up resources"""
        print("\n=== Cleaning Up ===")

        try:
            if self.trade_ctx:
                self.trade_ctx.close()
                print("Trade context closed")

        except Exception as e:
            print(f"Cleanup failed: {e}")

    async def run_complete_check(self):
        """Run complete account check"""
        print("Futu Demo Account Information Checker")
        print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        try:
            # Check all demo accounts
            accounts = await self.check_demo_accounts()

            if accounts:
                # For each account, get detailed info
                for account in accounts:
                    acc_id = account['acc_id']

                    # Check positions
                    await self.check_positions(acc_id)

                    # Check fund flow
                    await self.check_funds(acc_id)

                # Save account information
                account_summary = {
                    'check_time': datetime.now().isoformat(),
                    'accounts': accounts
                }

                with open('demo_accounts_info.json', 'w', encoding='utf-8') as f:
                    json.dump(account_summary, f, indent=2, ensure_ascii=False)

                print(f"\n[SUCCESS] Account information saved to: demo_accounts_info.json")
                print(f"[INFO] Total accounts found: {len(accounts)}")

            else:
                print("\n[INFO] No demo accounts available")

        except Exception as e:
            print(f"[ERROR] Account check failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

async def main():
    """Main function"""
    checker = DemoAccountChecker()
    await checker.run_complete_check()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCheck interrupted by user")
    except Exception as e:
        print(f"\nCheck failed: {e}")
        import traceback
        traceback.print_exc()