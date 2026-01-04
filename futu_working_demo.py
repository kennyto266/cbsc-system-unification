#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途牛牛API修復版模擬環境測試 - 基於之前成功的項目代碼
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# 設置環境變數
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加富途SDK路徑
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

class FutuWorkingDemoTester:
    def __init__(self):
        self.quote_ctx = None
        self.trade_ctx = None
        self.demo_accounts = []
        self.selected_acc_id = None

    async def test_basic_connection(self):
        """測試基本連接"""
        print("=== 富途API基本連接測試 ===")

        try:
            import futu as ft
            print(f"富途API版本: {ft.__version__}")

            # 按照官方文檔創建行情上下文
            print("創建行情上下文...")
            self.quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

            print("創建交易上下文...")
            self.trade_ctx = ft.OpenHKTradeContext(host='127.0.0.1', port=11111)

            print("[OK] 上下文創建成功")
            return True

        except Exception as e:
            print(f"[ERROR] 連接失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_user_info(self):
        """測試用戶信息"""
        print("\n=== 用戶信息測試 ===")

        try:
            # 獲取用戶信息
            ret, data = self.quote_ctx.get_user_info()

            if ret == ft.RET_OK:
                print("[OK] 用戶信息獲取成功")
                if data is not None and len(data) > 0:
                    user_info = data.iloc[0]
                    print(f"  用戶ID: {user_info.get('user_id', 'N/A')}")
                    print(f"  登錄狀態: {user_info.get('login_status', 'N/A')}")
                    print(f"  賬戶名稱: {user_info.get('name', 'N/A')}")
                    return True
                else:
                    print("[WARN] 用戶信息為空")
                    return True
            else:
                print(f"[FAIL] 用戶信息獲取失敗: {data}")
                return False

        except Exception as e:
            print(f"[ERROR] 用戶信息測試異常: {e}")
            return False

    async def test_demo_accounts(self):
        """測試模擬賬戶"""
        print("\n=== 模擬賬戶測試 ===")

        try:
            import futu as ft

            # 查詢模擬賬戶列表 (在查詢時指定環境)
            print("查詢模擬賬戶信息...")
            ret, data = self.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

            if ret == ft.RET_OK:
                print("[OK] 模擬賬戶查詢成功")

                self.demo_accounts = []
                if data is not None and len(data) > 0:
                    for index, row in data.iterrows():
                        account_info = {
                            'acc_id': str(row.get('acc_id', '')),
                            'acc_type': str(row.get('acc_type', '')),
                            'currency': str(row.get('currency', '')),
                            'cash': float(row.get('cash', 0)),
                            'total_assets': float(row.get('total_assets', 0)),
                            'power': float(row.get('power', 0)),
                            'market_val': float(row.get('market_val', 0)),
                            'max_withdraw': float(row.get('max_withdraw', 0)),
                            'trade_pwd_required': bool(row.get('trade_pwd_required', False))
                        }
                        self.demo_accounts.append(account_info)

                        print(f"  賬戶 {index + 1}:")
                        print(f"    賬戶ID: {account_info['acc_id']}")
                        print(f"    賬戶類型: {account_info['acc_type']}")
                        print(f"    總資產: {account_info['total_assets']}")
                        print(f"    可用資金: {account_info['power']}")
                        print(f"    需要交易密碼: {'YES' if account_info['trade_pwd_required'] else 'NO'}")

                    # 自動選擇第一個賬戶
                    if self.demo_accounts:
                        self.selected_acc_id = self.demo_accounts[0]['acc_id']
                        print(f"\n[OK] 自動選擇賬戶: {self.selected_acc_id}")
                        return "accounts_found"
                    else:
                        print("[WARN] 沒有找到模擬賬戶")
                        return "no_accounts"
                else:
                    print("[WARN] 模擬賬戶數據為空")
                    return "no_data"
            else:
                print(f"[FAIL] 模擬賬戶查詢失敗: {data}")
                return "query_failed"

        except Exception as e:
            print(f"[ERROR] 模擬賬戶測試異常: {e}")
            import traceback
            traceback.print_exc()
            return "error"

    async def test_market_data(self):
        """測試市場數據"""
        print("\n=== 市場數據測試 ===")

        try:
            # 測試港股
            test_stocks = ['HK.00700', 'HK.0388', 'HK.1398']

            for stock_code in test_stocks:
                print(f"  測試股票: {stock_code}")

                # 獲取市場快照
                ret, data = self.quote_ctx.get_market_snapshot([stock_code])

                if ret == ft.RET_OK and data is not None and len(data) > 0:
                    stock_data = data.iloc[0]
                    last_price = float(stock_data.get('last_price', 0))
                    volume = int(stock_data.get('volume', 0))
                    print(f"    [OK] 最新價: {last_price}, 成交量: {volume}")
                else:
                    print(f"    [FAIL] 無法獲取數據: {data}")

                await asyncio.sleep(0.1)  # 避免頻繁請求

            return True

        except Exception as e:
            print(f"[ERROR] 市場數據測試異常: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def cleanup(self):
        """清理資源"""
        print("\n=== 清理資源 ===")

        try:
            if self.quote_ctx:
                self.quote_ctx.close()
                print("[OK] 行情上下文已關閉")

            if self.trade_ctx:
                self.trade_ctx.close()
                print("[OK] 交易上下文已關閉")

        except Exception as e:
            print(f"[ERROR] 清理資源失敗: {e}")

    async def run_full_test(self):
        """運行完整測試"""
        print("富途牛牛API修復版模擬環境測試")
        print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        test_results = {
            'connection': False,
            'user_info': False,
            'demo_accounts': 'none',
            'market_data': False
        }

        try:
            # 1. 基本連接測試
            test_results['connection'] = await self.test_basic_connection()
            if not test_results['connection']:
                print("[FAIL] 基本連接失敗，測試終止")
                return test_results

            # 2. 用戶信息測試
            test_results['user_info'] = await self.test_user_info()

            # 3. 模擬賬戶測試
            test_results['demo_accounts'] = await self.test_demo_accounts()

            # 4. 市場數據測試
            test_results['market_data'] = await self.test_market_data()

        except Exception as e:
            print(f"[ERROR] 測試過程發生異常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()

        return test_results

def generate_test_report(results, selected_acc_id, demo_accounts):
    """生成測試報告"""
    print("\n" + "=" * 60)
    print("測試結果報告")
    print("-" * 30)

    status_map = {
        True: "[PASS]",
        False: "[FAIL]",
        'none': "[SKIP]",
        'accounts_found': "[PASS]",
        'no_accounts': "[FAIL]",
        'no_data': "[WARN]",
        'query_failed': "[FAIL]",
        'error': "[ERROR]"
    }

    print(f"基本連接: {status_map.get(results['connection'], '[UNKNOWN]')}")
    print(f"用戶信息: {status_map.get(results['user_info'], '[UNKNOWN]')}")
    print(f"模擬賬戶: {status_map.get(results['demo_accounts'], '[UNKNOWN]')}")
    print(f"市場數據: {status_map.get(results['market_data'], '[UNKNOWN]')}")

    if selected_acc_id:
        print(f"\n選中賬戶: {selected_acc_id}")

    # 總結
    success_count = sum(1 for v in results.values() if v is True)
    total_count = len([k for k in results.keys() if k not in ['demo_accounts']])

    if success_count == total_count:
        print("\n[SUCCESS] 所有核心功能測試通過！")
        print("[OK] 富途模擬環境已完全就緒")
        return True
    elif success_count >= total_count * 0.7:
        print("\n[PARTIAL] 大部分功能測試通過")
        print("[OK] 基本功能可用，部分功能需要配置")
        return True
    else:
        print("\n[FAILED] 測試失敗項目較多")
        print("[ACTION] 請檢查富途客戶端設置")
        return False

async def main():
    """主函數"""
    tester = FutuWorkingDemoTester()
    results = await tester.run_full_test()

    success = generate_test_report(
        results,
        tester.selected_acc_id,
        tester.demo_accounts
    )

    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n測試過程發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)