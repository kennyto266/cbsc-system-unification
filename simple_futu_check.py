#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版富途連接診斷工具
基於官方文檔的Telnet命令檢查方法
"""

import socket
import subprocess
import sys

def check_futu_process():
    """檢查富途進程"""
    print("檢查富途進程...")
    try:
        result = subprocess.run(['tasklist', '/fi', 'imagename eq FutuOpenD.exe'],
                               capture_output=True, text=True)
        if 'FutuOpenD.exe' in result.stdout:
            print("富途進程正在運行")
            return True
        else:
            print("富途進程未運行")
            return False
    except Exception as e:
        print(f"檢查進程失敗: {e}")
        return False

def check_telnet_connection():
    """檢查Telnet連接"""
    print("檢查Telnet連接 (端口4444)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', 4444))
        sock.close()

        if result == 0:
            print("Telnet端口4444可連接")
            return True
        else:
            print(f"Telnet端口4444連接失敗 (錯誤: {result})")
            return False
    except Exception as e:
        print(f"Telnet連接檢查失敗: {e}")
        return False

def check_api_connection():
    """檢查API連接"""
    print("檢查API連接 (端口11111)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', 11111))
        sock.close()

        if result == 0:
            print("API端口11111可連接")
            return True
        else:
            print(f"API端口11111連接失敗 (錯誤: {result})")
            return False
    except Exception as e:
        print(f"API連接檢查失敗: {e}")
        return False

def send_telnet_command(command):
    """發送Telnet命令"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('127.0.0.1', 4444))

        # 發送命令
        cmd = command + '\n'
        sock.send(cmd.encode('utf-8'))

        # 接收響應
        response = sock.recv(1024).decode('utf-8')
        sock.close()

        return response.strip()
    except Exception as e:
        return f"命令失敗: {e}"

def check_opend_status():
    """檢查OpenD狀態"""
    print("檢查OpenD狀態...")

    if not check_telnet_connection():
        print("Telnet未啟用，無法檢查OpenD狀態")
        return False

    # 測試基本命令
    commands = ['help', 'status']
    for cmd in commands:
        print(f"執行命令: {cmd}")
        response = send_telnet_command(cmd)
        if "命令失敗" in response:
            print(f"命令 {cmd} 失敗")
            return False
        else:
            print(f"命令 {cmd} 成功")

    print("OpenD狀態正常")
    return True

def main():
    """主診斷流程"""
    print("富途連接診斷工具")
    print("=" * 40)

    # 1. 檢查進程
    process_ok = check_futu_process()

    # 2. 檢查端口
    telnet_ok = check_telnet_connection()
    api_ok = check_api_connection()

    # 3. 檢查OpenD狀態
    opend_ok = False
    if telnet_ok:
        opend_ok = check_opend_status()

    # 4. 總結
    print("\n診斷結果:")
    print(f"進程狀態: {'OK' if process_ok else 'FAIL'}")
    print(f"Telnet連接: {'OK' if telnet_ok else 'FAIL'}")
    print(f"API連接: {'OK' if api_ok else 'FAIL'}")
    print(f"OpenD狀態: {'OK' if opend_ok else 'FAIL'}")

    # 5. 提供建議
    print("\n解決建議:")
    if not process_ok:
        print("1. 手動啟動富途OpenD客戶端")
    if not telnet_ok:
        print("2. 檢查客戶端Telnet設置 (默認端口4444)")
    if not api_ok:
        print("3. 檢查客戶端API設置 (默認端口11111)")
    if not opend_ok and telnet_ok:
        print("4. 檢查客戶端是否完成登錄")

    all_ok = process_ok and telnet_ok and api_ok and opend_ok
    if all_ok:
        print("\n所有檢查通過！可以嘗試API連接")
    else:
        print("\n請根據上述建議處理問題")

if __name__ == "__main__":
    main()