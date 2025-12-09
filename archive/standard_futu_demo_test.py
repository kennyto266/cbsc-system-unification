#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
標準富途API測試 - 基於官方文檔的demo戶口交易測試
使用您提供的標準代碼格式

Author: Claude Code Assistant
Date: 2025-11-21
"""

import sys
from datetime import datetime

try:
    from futu import *
except ImportError:
    print("富途API未安裝，請先安裝: pip install futu-api")
    sys.exit(1)

def standard_futu_test():
    """使用標準富途API格式測試demo戶口交易"""
    try:
        print("=== 標準富途API Demo交易測試 ===")
        print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("用戶ID: 2860386")
        print("目標: 港股模擬交易 - 買入1手騰訊(00700)")

        # 步驟1: 登陸OpenD並取得行情及交易權限
        print("\n--- 步驟1: 連接OpenD ---")
        trd_ctx = OpenHKTradeContext(host='127.0.0.1', port=11111)
        print("OpenD connection successful")

        # 步驟2: 查詢demo戶口資金
        print("\n--- 步驟2: 查詢賬戶資金 ---")
        ret_funds, funds_data = trd_ctx.accinfo_query(trd_env=TrdEnv.SIMULATE)
        if ret_funds == RET_OK:
            print("Funds query successful:")
            if not funds_data.empty:
                for _, row in funds_data.iterrows():
                    print(f"  Cash: {row.get('cash', 0):,.0f} HKD")
                    print(f"  Buying Power: {row.get('power', 0):,.0f} HKD")
                    print(f"  Total Assets: {row.get('total_assets', 0):,.0f} HKD")
        else:
            print(f"Funds query failed: {funds_data}")

        # 步驟3: 查詢持倉
        print("\n--- 步驟3: 查詢持倉 ---")
        ret_pos, pos_data = trd_ctx.position_list_query(trd_env=TrdEnv.SIMULATE)
        if ret_pos == RET_OK:
            print("Position query successful")
            if pos_data.empty:
                print("  No current positions")
            else:
                print(f"  Current positions: {len(pos_data)}")
        else:
            print(f"Position query failed: {pos_data}")

        # 步驟4: 下單測試 (港股模擬盤)
        print("\n--- 步驟4: 模擬下單測試 ---")
        print("Order parameters:")
        print("  Code: 00700 (Tencent)")
        print("  Price: 510.00 HKD")
        print("  Quantity: 1 lot (1000 shares)")
        print("  Side: BUY")
        print("  Market: HK")
        print("  Environment: SIMULATE")

        ret, data = trd_ctx.place_order(
            price=510.0,           # 價格
            qty=1000,              # 1手 = 1000股
            code='HK.00700',       # 正確的股票代碼格式
            trd_side=TrdSide.BUY, # 買入
            order_type=OrderType.NORMAL,  # 普通單
            trd_env=TrdEnv.SIMULATE,     # 模擬環境
            acc_id=0              # 使用默認賬戶
        )

        if ret == RET_OK:
            print("ORDER SUCCESSFUL!")
            if not data.empty:
                order_id = data.iloc[0]['order_id']
                order_status = data.iloc[0]['order_status']
                print(f"  Order ID: {order_id}")
                print(f"  Order Status: {order_status}")
                print(f"  Please check order details in Futu App!")

                # 保存成功結果
                result = {
                    'success': True,
                    'order_id': str(order_id),
                    'order_status': str(order_status),
                    'symbol': '00700',
                    'side': 'BUY',
                    'price': 510.0,
                    'quantity': 1000,
                    'timestamp': datetime.now().isoformat()
                }

                with open('standard_futu_demo_result.json', 'w', encoding='utf-8') as f:
                    import json
                    json.dump(result, f, indent=2, default=str)

                print(f"Result saved to: standard_futu_demo_result.json")
                return True
            else:
                print("Order successful but no return data")
        else:
            print(f"ORDER FAILED!")
            print(f"Return code: {ret}")
            print(f"Error details: {data}")

            # 分析常見錯誤
            error_str = str(data).lower()
            if "购买力" in error_str or "buying_power" in error_str or "insufficient" in error_str:
                print("\nBUYING POWER ISSUE SOLUTION:")
                print("1. Check if agreement confirmation is completed in Futu App")
                print("2. Confirm simulation trading permissions are enabled")
                print("3. Try manual order in App to test permissions")
            elif "协议" in error_str or "agreement" in error_str:
                print("\nAGREEMENT CONFIRMATION ISSUE:")
                print("1. Please complete disclaimer agreement in Futu App")
                print("2. Restart OpenD client after completion")
            elif "时间" in error_str or "time" in error_str:
                print("\nTRADING TIME ISSUE:")
                print("1. Confirm current time is within HK trading hours")
                print("2. Trading hours: 09:30-12:00, 13:00-16:00")

        return False

    except Exception as e:
        print(f"PROGRAM ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            if 'trd_ctx' in locals():
                trd_ctx.close()
                print("\nConnection closed")
        except:
            pass

if __name__ == "__main__":
    print("Starting Standard Futu API Demo Trading Test...")
    print("Please ensure:")
    print("1. Futu OpenD is running (port 11111)")
    print("2. Agreement confirmation completed in Futu App")
    print("3. Simulation trading permissions are enabled")
    print()

    success = standard_futu_test()

    if success:
        print("\n" + "="*60)
        print("DEMO TRADING TEST SUCCESSFUL!")
        print("Please check order status in Futu App")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("DEMO TRADING TEST FAILED")
        print("Please make settings according to error messages above")
        print("="*60)

    sys.exit(0 if success else 1)