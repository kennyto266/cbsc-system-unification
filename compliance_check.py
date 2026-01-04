#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compliance Check for Futu API - 富途API合規檢查
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

async def check_compliance():
    """Check Futu API compliance status"""
    print("=== 富途API合規檢查 ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        import futu as ft

        # Test connection
        print("\n1. 測試連接狀態...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
        print("   連接成功")

        # Get global state
        print("\n2. 檢查登入和合規狀態...")
        ret, global_state = quote_ctx.get_global_state()

        if ret == ft.RET_OK:
            print(f"   伺服器版本: {global_state.get('server_ver', 'Unknown')}")
            print(f"   行情登入: {'✅' if global_state.get('qot_logined') else '❌'}")
            print(f"   交易登入: {'✅' if global_state.get('trd_logined') else '❌'}")
            print(f"   程序狀態: {global_state.get('program_status_desc', 'Unknown')}")

            # Check user info
            print(f"\n3. 檢查用戶權限...")
            try:
                # Get user info
                ret, user_info = trade_ctx.get_acc_list()
                if ret == ft.RET_OK:
                    print(f"   賬戶列表: ✅ 獲取成功")
                    if user_info and len(user_info) > 0:
                        for acc in user_info:
                            acc_id = acc.get('acc_id', 'N/A')
                            acc_type = acc.get('acc_type', 'N/A')
                            print(f"   賬戶 {acc_id}: 類型 {acc_type}")
                    else:
                        print("   ⚠️ 無可用賬戶")
                else:
                    print(f"   ❌ 賬戶列表獲取失敗: {ret}")

                    # Try specific environment
                    print(f"\n   嘗試模擬環境...")
                    ret, sim_acc = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                    if ret == ft.RET_OK:
                        print(f"   模擬賬戶: ✅ 可用")
                        if sim_acc.shape[0] > 0:
                            cash = sim_acc.iloc[0].get('cash', 0)
                            print(f"   模擬資金: {cash:,.2f}")
                    else:
                        print(f"   ❌ 模擬賬戶失敗: {ret}")

            except Exception as e:
                print(f"   用戶權限檢查錯誤: {e}")

            # Check market data permissions
            print(f"\n4. 檢查行情權限...")
            try:
                # Test subscription
                test_stock = "HK.00700"
                ret, sub_err = quote_ctx.subscribe([test_stock], [ft.SubType.QUOTE])
                if ret == ft.RET_OK:
                    print(f"   行情訂閱: ✅ {test_stock} 成功")

                    # Get quote
                    ret, quote_data = quote_ctx.get_stock_quote([test_stock])
                    if ret == ft.RET_OK and quote_data.shape[0] > 0:
                        price = quote_data.iloc[0]['last_price']
                        print(f"   實時報價: {price:.2f} HKD")
                    else:
                        print(f"   報價獲取失敗: {ret}")
                else:
                    print(f"   ❌ 行情訂閱失敗: {ret}")
            except Exception as e:
                print(f"   行情權限檢查錯誤: {e}")

        quote_ctx.close()
        trade_ctx.close()

        # Display compliance requirements
        print(f"\n5. 合規要求檢查清單:")
        print(f"   □ 已在富途牛牛App完成交易賬戶開通")
        print(f"   □ 已完成API問卷協議")
        print(f"   □ 已開通港股交易權限")
        print(f"   □ 已激活模擬交易功能")
        print(f"   □ 已在App中開啟API權限")

        print(f"\n📖 合規鏈接:")
        print(f"   API問卷協議: https://www.futunn.com/about/api-disclaimer?lang=en-US")
        print(f"   模擬交易: 富途牛牛App → 交易 → 模擬交易")

    except Exception as e:
        print(f"檢查失敗: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== 合規檢查完成 ===")

async def main():
    """Main function"""
    await check_compliance()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"檢查執行失敗: {e}")