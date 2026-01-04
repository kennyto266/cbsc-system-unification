#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Trading Order - 測試模擬交易下單功能
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

async def test_trading_order():
    """Test placing a simulation order"""
    print("=== 測試模擬交易下單 ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        import futu as ft

        # Test connection
        print("\n1. 建立交易連接...")
        trade_ctx = ft.OpenHKTradeContext(host=HOST, port=API_PORT)
        print("   ✅ 交易連接建立成功")

        # Test simulation account
        print("\n2. 檢查模擬賬戶...")
        ret, data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

        if ret == ft.RET_OK and data.shape[0] > 0:
            print("   ✅ 模擬賬戶可用")

            # Get account info
            acc_id = data.iloc[0]['acc_id']
            cash = data.iloc[0]['cash']
            print(f"   賬戶 ID: {acc_id}")
            print(f"   可用資金: {cash:,.2f} HKD")

            # Test unlocking trade
            print("\n3. 解鎖交易...")
            ret, data = trade_ctx.unlock_trade(password="123456")
            if ret == ft.RET_OK:
                print("   ✅ 交易解鎖成功")
            else:
                print(f"   ⚠️ 交易解鎖返回: {data}")
                print("   繼續測試 (模擬環境可能不需要解鎖)")

            # Place a test order (小額測試)
            print("\n4. 下測試單...")

            # Test Tencent stock (HK.00700)
            stock_code = "HK.00700"

            # Get current price first
            print(f"   獲取 {stock_code} 當前價格...")
            quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
            ret, price_data = quote_ctx.get_market_snapshot([stock_code])

            if ret == ft.RET_OK and price_data.shape[0] > 0:
                current_price = price_data.iloc[0]['last_price']
                print(f"   當前價格: {current_price:.2f} HKD")

                # Calculate test order price (slightly lower than market)
                test_price = current_price * 0.995  # 99.5% of current price
                test_quantity = 100  # 100 shares

                print(f"   測試單參數:")
                print(f"   - 股票代碼: {stock_code}")
                print(f"   - 價格: {test_price:.2f} HKD")
                print(f"   - 數量: {test_quantity} 股")
                print(f"   - 預計金額: {test_price * test_quantity:,.2f} HKD")

                # Place the order
                print(f"\n   執行下單...")
                ret, order_data = trade_ctx.place_order(
                    price=test_price,
                    qty=test_quantity,
                    code=stock_code,
                    trd_side=ft.TrdSide.BUY,
                    trd_env=ft.TrdEnv.SIMULATE,
                    order_type=ft.OrderType.NORMAL,
                    remark="API測試單"
                )

                if ret == ft.RET_OK:
                    order_id = order_data.iloc[0]['order_id']
                    print(f"   ✅ 下單成功！")
                    print(f"   訂單 ID: {order_id}")
                    print(f"   狀態: {order_data.iloc[0]['order_status']}")
                    print(f"   時間: {order_data.iloc[0]['create_time']}")

                    # Check order status
                    print(f"\n5. 查詢訂單狀態...")
                    ret, status_data = trade_ctx.order_list_query(
                        order_id=order_id,
                        trd_env=ft.TrdEnv.SIMULATE
                    )

                    if ret == ft.RET_OK and status_data.shape[0] > 0:
                        status = status_data.iloc[0]['order_status']
                        print(f"   訂單狀態: {status}")

                        if status == 'SUBMITTED':
                            print("   ✅ 訂單已提交")
                        elif status == 'FILLED_ALL':
                            print("   ✅ 訂單完全成交")
                        else:
                            print(f"   訂單狀態: {status}")

                else:
                    print(f"   ❌ 下單失敗")
                    print(f"   錯誤代碼: {ret}")
                    print(f"   錯誤信息: {data}")

                quote_ctx.close()
            else:
                print(f"   ❌ 無法獲取股價信息")
                quote_ctx.close()

        else:
            print("   ❌ 模擬賬戶不可用")

        trade_ctx.close()

    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== 測試完成 ===")
    print("如果看到 ✅ 標記，表示模擬交易功能正常")

async def main():
    """Main function"""
    await test_trading_order()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"測試執行失敗: {e}")