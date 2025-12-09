#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途API調試測試
檢查數據結構並修復問題

Author: Claude Code Assistant
Date: 2025-11-21
"""

import sys

# 檢查富途API
try:
    import futu as ft
    print("富途API已安裝")
except ImportError:
    print("富途API未安裝")
    sys.exit(1)

def test_futu_api():
    """測試富途API"""
    try:
        print("正在測試富途API...")

        # 創建行情上下文
        quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

        # 測試不同股票代碼格式
        test_codes = [
            'HK.00700',  # 富途標準格式
            '00700.HK',  # 我們的格式
            '00700'      # 純數字
        ]

        for code in test_codes:
            print(f"\n測試代碼: {code}")

            try:
                ret, data = quote_ctx.get_market_snapshot([code])

                if ret == ft.RET_OK:
                    print(f"成功獲取數據，行數: {len(data)}")
                    if not data.empty:
                        print("數據列:")
                        for col in data.columns:
                            print(f"  {col}")

                        print(f"第一行數據:")
                        for col in data.columns:
                            value = data.iloc[0][col]
                            print(f"  {col}: {value}")

                        # 檢查是否有lastPrice
                        if 'lastPrice' in data.columns:
                            last_price = data.iloc[0]['lastPrice']
                            print(f"最新價格: {last_price}")
                        else:
                            print("沒有lastPrice列")
                    else:
                        print("數據為空")
                else:
                    print(f"獲取數據失敗: {data}")

            except Exception as e:
                print(f"測試{code}時出錯: {e}")

        # 測試查詢市場狀態
        print(f"\n測試市場狀態...")
        ret, data = quote_ctx.get_global_state()
        if ret == ft.RET_OK:
            print("市場狀態查詢成功")
        else:
            print(f"市場狀態查詢失敗: {data}")

        # 測試交易上下文
        print(f"\n測試交易上下文...")
        trade_ctx = ft.OpenHKTradeContext(host='127.0.0.1', port=11111)

        # 查詢賬戶信息
        ret, acc_data = trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
        if ret == ft.RET_OK and acc_data is not None:
            print("賬戶信息查詢成功")
            print(f"數據行數: {len(acc_data)}")
            if not acc_data.empty:
                print("賬戶數據列:")
                for col in acc_data.columns:
                    print(f"  {col}")
        else:
            print(f"賬戶信息查詢失敗: {acc_data}")

        # 清理
        quote_ctx.close()
        trade_ctx.close()
        print(f"\n測試完成")

    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_futu_api()