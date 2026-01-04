#!/usr/bin/env python3
"""
富途快速連接測試
"""

import sys
import os

# 添加富途SDK路徑
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

try:
    import futu as ft
    print("富途SDK導入成功")
except ImportError:
    print("富途SDK導入失敗")
    sys.exit(1)

def test_connection():
    """測試連接"""
    try:
        print("正在建立連接...")
        quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

        ret, data = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print("✅ 富途連接成功！")
            print(f"連接狀態: {data}")

            # 測試基本行情
            print("\n測試騰訊控股行情...")
            ret, market_data = quote_ctx.get_market_snapshot(["HK.00700"])
            if ret == ft.RET_OK and market_data:
                stock = market_data[0]
                print(f"股票代碼: {stock.get('code', 'N/A')}")
                print(f"最新價格: {stock.get('last_price', 'N/A')}")
                print(f"漲跌額: {stock.get('change_val', 'N/A')}")
            else:
                print("行情數據獲取失敗")
        else:
            print(f"❌ 連接失敗: {data}")

        quote_ctx.close()
        return ret == ft.RET_OK

    except Exception as e:
        print(f"❌ 連接異常: {e}")
        return False

if __name__ == "__main__":
    print("富途 OpenD 快速連接測試")
    print("-" * 40)

    if test_connection():
        print("\n🎉 測試完成！富途API工作正常")
    else:
        print("\n💥 測試失敗，請檢查富途客戶端")