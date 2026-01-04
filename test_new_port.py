#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新的富途API端口配置
"""

import sys
import os
import socket

# 添加富途SDK路徑
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# 新配置
API_PORT = 1130
HOST = '127.0.0.1'

def test_port_1130():
    """測試API端口1130"""
    print("測試API端口1130...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((HOST, API_PORT))
        sock.close()

        if result == 0:
            print("端口1130連接成功")
            return True
        else:
            print(f"端口1130連接失敗，錯誤代碼: {result}")
            return False
    except Exception as e:
        print(f"端口測試失敗: {e}")
        return False

def test_futu_api_1130():
    """測試富途API端口1130連接"""
    print("開始測試富途API端口1130...")

    try:
        import futu as ft
        print(f"富途API版本: {ft.__version__}")

        # 使用端口1130創建連接
        print("創建連接到端口1130...")
        quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)

        # 測試連接
        print("測試連接狀態...")
        ret, data = quote_ctx.get_global_state()

        quote_ctx.close()

        if ret == ft.RET_OK:
            print("連接成功！富途API端口1130工作正常")
            print(f"全局狀態: {data}")
            return True
        else:
            print(f"連接失敗: {data}")
            return False

    except ImportError:
        print("富途SDK導入失敗")
        return False
    except Exception as e:
        print(f"API測試異常: {e}")
        return False

def main():
    """主測試流程"""
    print("富途新端口測試工具")
    print(f"API端口: {API_PORT}")
    print("=" * 40)

    # 1. 測試端口連通性
    port_ok = test_port_1130()

    # 2. 測試API連接
    if port_ok:
        api_ok = test_futu_api_1130()
    else:
        api_ok = False

    # 3. 結果總結
    print("\n測試結果:")
    print(f"端口連通: {'OK' if port_ok else 'FAIL'}")
    print(f"API連接: {'OK' if api_ok else 'FAIL'}")

    if port_ok and api_ok:
        print("\n成功！端口1130配置正確")
        print("可以開始使用新端口進行開發")
    else:
        print("\n需要檢查端口配置")
        print("請確認富途客戶端設置")

if __name__ == "__main__":
    main()