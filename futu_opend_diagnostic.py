#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途OpenD診斷工具 - 基於官方命令行文檔
使用Telnet命令檢查OpenD狀態和解決連接問題
"""

import socket
import subprocess
import time
import sys
import os
from datetime import datetime

class FutuOpenDDiagnostic:
    def __init__(self, host='127.0.0.1', telnet_port=4444, api_port=11111):
        self.host = host
        self.telnet_port = telnet_port
        self.api_port = api_port
        self.websocket_key = "cb8fe2a668e624da"
        self.niuniu_number = "2860386"

    def check_process_status(self):
        """檢查富途進程狀態"""
        print("=== 富途進程狀態檢查 ===")

        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ['tasklist', '/fi', 'imagename eq FutuOpenD.exe', '/fo', 'csv'],
                    capture_output=True,
                    text=True,
                    encoding='gbk'
                )

                if result.returncode == 0 and "FutuOpenD.exe" in result.stdout:
                    lines = result.stdout.strip().split('\n')
                    print("✅ 富途OpenD進程正在運行:")
                    for line in lines[1:]:  # 跳過標題行
                        if line.strip():
                            parts = line.split('","')
                            if len(parts) >= 2:
                                print(f"  進程: {parts[0].strip('"')}, PID: {parts[1].strip('"')}, 狀態: {parts[-1].strip('"')}")
                    return True
                else:
                    print("❌ 富途OpenD進程未運行")
                    return False
            else:
                # Linux/Mac
                result = subprocess.run(['pgrep', '-f', 'FutuOpenD'], capture_output=True, text=True)
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    print("✅ 富途OpenD進程正在運行:")
                    for pid in pids:
                        print(f"  PID: {pid}")
                    return True
                else:
                    print("❌ 富途OpenD進程未運行")
                    return False

        except Exception as e:
            print(f"❌ 檢查進程時發生錯誤: {e}")
            return False

    def check_port_connectivity(self):
        """檢查端口連通性"""
        print(f"\n=== 端口連通性檢查 ===")
        print(f"主機: {self.host}")
        print(f"Telnet端口: {self.telnet_port}")
        print(f"API端口: {self.api_port}")

        ports_to_check = [
            (self.telnet_port, "Telnet"),
            (self.api_port, "API")
        ]

        all_ok = True
        for port, port_type in ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((self.host, port))
                sock.close()

                if result == 0:
                    print(f"✅ {port_type}端口 {port} 可連接")
                else:
                    print(f"❌ {port_type}端口 {port} 連接失敗 (錯誤代碼: {result})")
                    all_ok = False

            except Exception as e:
                print(f"❌ 檢查{port_type}端口 {port} 時發生錯誤: {e}")
                all_ok = False

        return all_ok

    def telnet_command(self, command, timeout=10):
        """通過Telnet執行OpenD命令"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.host, self.telnet_port))

            # 發送命令
            cmd_bytes = (command + '\n').encode('utf-8')
            sock.send(cmd_bytes)

            # 接收響應
            response = sock.recv(4096).decode('utf-8')

            sock.close()
            return response.strip()

        except Exception as e:
            return f"Telnet命令執行失敗: {e}"

    def check_opend_status(self):
        """檢查OpenD狀態"""
        print(f"\n=== OpenD狀態檢查 (Telnet: {self.host}:{self.telnet_port}) ===")

        # 檢查基本連接
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.telnet_port))
            sock.close()

            if result != 0:
                print("❌ 無法連接到Telnet端口，OpenD可能未啟用Telnet功能")
                print("💡 建議: 檢查OpenD配置文件，確認Telnet端口設置")
                return False
        except Exception as e:
            print(f"❌ Telnet連接檢查失敗: {e}")
            return False

        # 執行狀態檢查命令
        commands_to_check = [
            ("help", "檢查命令幫助"),
            ("status", "檢查系統狀態"),
            ("get_global_state", "檢查全局狀態")
        ]

        all_ok = True
        for cmd, desc in commands_to_check:
            print(f"\n執行命令: {cmd} ({desc})")
            response = self.telnet_command(cmd, 5)

            if "Telnet命令執行失敗" not in response:
                print(f"✅ {cmd} 執行成功")
                if response:
                    print(f"  響應: {response[:200]}...")  # 只顯示前200字符
            else:
                print(f"❌ {cmd} 執行失敗: {response}")
                all_ok = False

        return all_ok

    def request_quote_permission(self):
        """請求行情權限"""
        print(f"\n=== 行情權限檢查 ===")

        print("嘗試請求最高行情權限...")
        response = self.telnet_command("request_highest_quote_right", 10)

        if "Telnet命令執行失敗" not in response:
            print("✅ 行情權限請求已發送")
            print(f"  響應: {response[:300]}...")
            return True
        else:
            print(f"❌ 行情權限請求失敗: {response}")
            return False

    def input_verify_code(self, verify_code):
        """輸入手機驗證碼"""
        print(f"\n=== 輸入驗證碼 ===")
        print(f"驗證碼: {verify_code}")

        command = f"input_phone_verify_code -code={verify_code}"
        response = self.telnet_command(command, 10)

        if "Telnet命令執行失敗" not in response:
            print("✅ 驗證碼已發送")
            print(f"  響應: {response[:300]}...")
            return True
        else:
            print(f"❌ 驗證碼輸入失敗: {response}")
            return False

    def test_api_connection(self):
        """測試API連接"""
        print(f"\n=== API連接測試 ===")

        try:
            # 添加富途SDK路徑
            sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')
            import futu as ft

            print(f"富途API版本: {ft.__version__}")

            # 創建連接
            quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.api_port)

            # 測試連接
            ret, data = quote_ctx.get_global_state()

            quote_ctx.close()

            if ret == ft.RET_OK:
                print("✅ API連接成功！")
                print(f"  全局狀態: {data}")
                return True
            else:
                print(f"❌ API連接失敗: {data}")
                return False

        except ImportError:
            print("❌ 富途SDK未安裝或無法導入")
            return False
        except Exception as e:
            print(f"❌ API連接測試異常: {e}")
            return False

    def run_comprehensive_diagnostic(self):
        """運行完整診斷"""
        print("富途OpenD完整診斷工具")
        print(f"基於官方文檔 - 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print(f"WebSocket密鑰: {self.websocket_key}")
        print(f"牛牛號: {self.niuniu_number}")
        print("-" * 60)

        results = {
            'process': False,
            'port_connectivity': False,
            'opend_status': False,
            'quote_permission': False,
            'api_connection': False
        }

        # 1. 檢查進程狀態
        results['process'] = self.check_process_status()

        # 2. 檢查端口連通性
        if results['process']:
            results['port_connectivity'] = self.check_port_connectivity()

        # 3. 檢查OpenD狀態
        if results['port_connectivity']:
            results['opend_status'] = self.check_opend_status()

        # 4. 檢查行情權限
        if results['opend_status']:
            results['quote_permission'] = self.request_quote_permission()

        # 5. 測試API連接
        if results['port_connectivity']:
            results['api_connection'] = self.test_api_connection()

        return results

    def generate_solutions(self, results):
        """根據診斷結果生成解決方案"""
        print(f"\n{'=' * 60}")
        print("診斷結果和解決方案")
        print("-" * 30)

        # 結果總結
        status_map = {
            True: "✅ 正常",
            False: "❌ 異常"
        }
        print(f"進程狀態: {status_map.get(results['process'])}")
        print(f"端口連通: {status_map.get(results['port_connectivity'])}")
        print(f"OpenD狀態: {status_map.get(results['opend_status'])}")
        print(f"行情權限: {status_map.get(results['quote_permission'])}")
        print(f"API連接: {status_map.get(results['api_connection'])}")

        print(f"\n📋 解決方案建議:")

        if not results['process']:
            print("1. ❌ 富途進程未運行")
            print("   → 手動啟動富途OpenD客戶端")
            print("   → 確認安裝路徑正確")

        if not results['port_connectivity']:
            print("2. ❌ 端口連接失敗")
            print("   → 檢查防火牆設置")
            print("   → 確認端口沒有被其他程序占用")
            print("   → 檢查OpenD配置中的端口設置")

        if not results['opend_status']:
            print("3. ❌ OpenD狀態異常")
            print("   → 檢查OpenD是否完成啟動")
            print("   → 確認Telnet功能已啟用")
            print("   → 檢查OpenD配置文件")

        if not results['quote_permission']:
            print("4. ❌ 行情權限問題")
            print("   → 在客戶端完成登錄認證")
            print("   → 輸入手機驗證碼（如果需要）")
            print("   → 申請必要的行情權限")

        if not results['api_connection']:
            print("5. ❌ API連接失敗")
            print("   → 確認客戶端已完成登錄")
            print("   → 檢查網絡連接")
            print("   → 重啟OpenD客戶端")

        # 整體建議
        success_count = sum(1 for v in results.values() if v is True)
        total_count = len(results)

        if success_count == total_count:
            print(f"\n🎉 所有檢查通過！富途OpenD完全就緒")
            print("✅ 可以開始API連接和POC開發")
        elif success_count >= total_count * 0.8:
            print(f"\n✅ 大部分功能正常")
            print("📊 基本連接可用，可以嘗試API開發")
        else:
            print(f"\n⚠️ 需要處理多個問題")
            print("🔧 請按照上述建議逐步解決")

def main():
    """主函數"""
    diagnostic = FutuOpenDDiagnostic()
    results = diagnostic.run_comprehensive_diagnostic()
    diagnostic.generate_solutions(results)

if __name__ == "__main__":
    main()