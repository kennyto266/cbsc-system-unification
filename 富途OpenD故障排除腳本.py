#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途OpenD故障排除與連接檢查腳本
"""

import telnetlib
import socket
import subprocess
import time
import sys
from typing import Optional, Tuple


class OpenDDiagnostic:
    """OpenD診斷工具類"""

    def __init__(self, host='localhost', telnet_port=11111, api_port=33333):
        self.host = host
        self.telnet_port = telnet_port
        self.api_port = api_port

    def check_port_open(self, port: int, timeout: int = 5) -> bool:
        """檢查端口是否開放"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.host, port))
            sock.close()
            return result == 0
        except Exception as e:
            print(f"檢查端口 {port} 時發生錯誤: {e}")
            return False

    def check_opend_process(self) -> Tuple[bool, str]:
        """檢查OpenD進程是否運行"""
        try:
            # Windows系統
            if sys.platform == 'win32':
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq FutuOpenD.exe'],
                                      capture_output=True, text=True)
                if 'FutuOpenD.exe' in result.stdout:
                    return True, "OpenD進程正在運行"
                else:
                    return False, "未找到OpenD進程"
            else:
                # Linux/Mac系統
                result = subprocess.run(['pgrep', '-f', 'FutuOpenD'],
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    return True, f"OpenD進程PID: {result.stdout.strip()}"
                else:
                    return False, "未找到OpenD進程"
        except Exception as e:
            return False, f"檢查進程時發生錯誤: {e}"

    def telnet_command(self, command: str) -> Optional[str]:
        """通過Telnet發送命令"""
        try:
            tn = telnetlib.Telnet(self.host, self.telnet_port, timeout=10)
            tn.write(command.encode('utf-8') + b'\n')
            response = tn.read_until(b'\n', timeout=5).decode('utf-8', errors='ignore')
            tn.close()
            return response.strip()
        except Exception as e:
            print(f"Telnet命令執行失敗: {e}")
            return None

    def check_opend_status(self) -> dict:
        """檢查OpenD整體狀態"""
        status = {
            'process_running': False,
            'telnet_accessible': False,
            'api_accessible': False,
            'login_status': 'unknown',
            'error_message': None
        }

        # 檢查進程
        status['process_running'], msg = self.check_opend_process()
        if not status['process_running']:
            status['error_message'] = msg
            return status

        # 檢查Telnet端口
        if self.check_port_open(self.telnet_port):
            status['telnet_accessible'] = True
            # 獲取狀態信息
            response = self.telnet_command('help')
            if response and 'help' in response.lower():
                status['login_status'] = 'telnet_connected'
        else:
            status['error_message'] = f"Telnet端口 {self.telnet_port} 無法訪問"

        # 檢查API端口
        if self.check_port_open(self.api_port):
            status['api_accessible'] = True

        return status

    def test_connectivity(self) -> dict:
        """測試網絡連通性"""
        results = {}

        # 測試本地端口
        results['telnet_port'] = self.check_port_open(self.telnet_port)
        results['api_port'] = self.check_port_open(self.api_port)

        # 測試網絡連接（可選）
        test_hosts = [
            ('富途API服務器', 'open_quote.futunn.com', 443),
            ('Google DNS', '8.8.8.8', 53)
        ]

        results['network_connectivity'] = []
        for name, host, port in test_hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                results['network_connectivity'].append({
                    'name': name,
                    'host': host,
                    'port': port,
                    'success': result == 0
                })
            except Exception as e:
                results['network_connectivity'].append({
                    'name': name,
                    'host': host,
                    'port': port,
                    'success': False,
                    'error': str(e)
                })

        return results

    def request_quote_right(self) -> bool:
        """請求行情權限"""
        command = 'request_highest_quote_right'
        response = self.telnet_command(command)
        if response and 'success' in response.lower():
            return True
        return False

    def input_verify_code(self, code: str) -> bool:
        """輸入驗證碼"""
        command = f'input_phone_verify_code -code={code}'
        response = self.telnet_command(command)
        if response and 'success' in response.lower():
            return True
        return False


def print_diagnostic_report():
    """打印診斷報告"""
    print("=== 富途OpenD診斷報告 ===\n")

    # 可以根據實際情況修改端口
    diagnostic = OpenDDiagnostic(
        host='localhost',
        telnet_port=11111,  # 默認Telnet端口
        api_port=33333      # 默認API端口
    )

    # 1. 檢查OpenD狀態
    print("1. OpenD狀態檢查")
    print("-" * 40)
    status = diagnostic.check_opend_status()

    if status['process_running']:
        print("✓ OpenD進程正在運行")
    else:
        print(f"✗ {status.get('error_message', 'OpenD進程未運行')}")
        return

    if status['telnet_accessible']:
        print("✓ Telnet服務可訪問")
    else:
        print(f"✗ {status.get('error_message', 'Telnet服務不可訪問')}")

    if status['api_accessible']:
        print("✓ API端口可訪問")
    else:
        print("✗ API端口無法訪問")

    print(f"\n登錄狀態: {status['login_status']}")

    # 2. 網絡連通性測試
    print("\n2. 網絡連通性測試")
    print("-" * 40)
    connectivity = diagnostic.test_connectivity()

    print(f"Telnet端口 ({diagnostic.telnet_port}): {'✓ 開放' if connectivity['telnet_port'] else '✗ 關閉'}")
    print(f"API端口 ({diagnostic.api_port}): {'✓ 開放' if connectivity['api_port'] else '✗ 關閉'}")

    print("\n外部網絡連接:")
    for conn in connectivity['network_connectivity']:
        status_str = "✓ 成功" if conn['success'] else f"✗ 失败"
        if 'error' in conn:
            status_str += f" ({conn['error']})"
        print(f"  {conn['name']}: {status_str}")

    # 3. 故障排除建議
    print("\n3. 故障排除建議")
    print("-" * 40)

    if not status['process_running']:
        print("• 請確保OpenD程序已啟動")
        print("• 檢查OpenD配置文件 (FutuOpenD.xml)")

    if not status['telnet_accessible']:
        print("• 檢查Telnet端口配置")
        print("• 確認防火牆設置")
        print("• 驗證OpenD啟動參數")

    if not status['api_accessible']:
        print("• 檢查API端口配置")
        print("• 確認端口未被其他程序佔用")

    if not any(connectivity['network_connectivity']):
        print("• 檢查網絡連接")
        print("• 驗證代理設置")
        print("• 聯繫網絡管理員")


def main():
    """主函數"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        diagnostic = OpenDDiagnostic()

        if command == 'status':
            status = diagnostic.check_opend_status()
            print(f"OpenD Status: {status}")
        elif command == 'quote':
            if diagnostic.request_quote_right():
                print("✓ 成功請求行情權限")
            else:
                print("✗ 請求行情權限失敗")
        elif command == 'verify':
            if len(sys.argv) > 2:
                code = sys.argv[2]
                if diagnostic.input_verify_code(code):
                    print("✓ 驗證碼輸入成功")
                else:
                    print("✗ 驗證碼輸入失敗")
            else:
                print("請提供驗證碼: python opend_diagnostic.py verify <code>")
        else:
            print(f"未知命令: {command}")
            print("可用命令: status, quote, verify")
    else:
        # 默認運行完整診斷
        print_diagnostic_report()


if __name__ == "__main__":
    main()