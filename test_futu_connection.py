#!/usr/bin/env python3
"""
富途 OpenD 連接測試腳本
測試富途API連接和基本功能
"""

import sys
import time
from datetime import datetime

try:
    import futu as ft
    print("富途SDK已加載")
except ImportError:
    print("富途SDK未安裝，請運行: pip install futu-api")
    sys.exit(1)

def test_futu_connection():
    """測試富途連接"""
    print("開始測試富途連接...")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    try:
        # 建立連接
        quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)
        print("連接已建立...")

        # 測試基本連接
        ret, data = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print("富途連接成功！")
            print(f"全局狀態: {data}")

            # 測試市場數據
            print("\n測試市場數據...")
            ret, data = quote_ctx.get_market_snapshot(["HK.00700"])
            if ret == ft.RET_OK and data:
                snapshot = data[0]
                print(f"騰訊控股 (00700): {snapshot.get('last_price', 'N/A')}")
                print(f"漲跌: {snapshot.get('change_val', 'N/A')}")
            else:
                print("市場數據獲取失敗")
        else:
            print(f"富途連接失敗: {data}")
            return False

        # 關閉連接
        quote_ctx.close()
        print("\n連接已關閉")
        return True

    except Exception as e:
        print(f"連接測試異常: {e}")
        return False

def main():
    """主函數"""
    print("富途 OpenD 連接測試")
    print("=" * 50)

    # 測試連接
    if test_futu_connection():
        print("\n✅ 富途連接測試通過！")
        print("可以開始POC開發")
    else:
        print("\n❌ 富途連接測試失敗")
        print("請檢查富途客戶端是否正常運行")

if __name__ == "__main__":
    main()