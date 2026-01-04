#!/usr/bin/env python3
"""
富途 OpenD 登錄問題解決工具
針對登錄超時和端口衝突問題
"""

import os
import sys
import time
import subprocess
from typing import List, Tuple
import requests
import json

class FutuLoginFixer:
    def __init__(self):
        self.default_ports = [11111, 4444, 11011, 11211]
        self.working_port = None

    def check_futu_service_status(self) -> dict:
        """檢查富途服務狀態"""
        status = {
            'processes': [],
            'ports': {},
            'login_page': False,
            'overall': 'unknown'
        }

        # 檢查富途進程
        try:
            if sys.platform == "win32":
                # Windows 檢查
                result = subprocess.run(
                    'tasklist /fi "imagename eq FutuOpenD.exe" /fo csv',
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='gbk'
                )

                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # 跳過標題行
                        if line.strip():
                            parts = line.split('","')
                            if len(parts) >= 2:
                                status['processes'].append({
                                    'name': parts[0].strip('"'),
                                    'pid': parts[1].strip('"'),
                                    'status': parts[-1].strip('"') if len(parts) > 5 else 'Unknown'
                                })

        except Exception as e:
            print(f"檢查進程時發生錯誤: {e}")

        # 檢查端口
        for port in self.default_ports:
            available = self._check_port_available(port)
            status['ports'][port] = {
                'available': not available,
                'status': 'occupied' if not available else 'free'
            }

        # 檢查登錄頁面可訪問性
        for port in self.default_ports:
            try:
                # 檢查富途 API 連接
                import futu as ft
                quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=port)
                ret, data = quote_ctx.get_global_state()
                if ret == ft.RET_OK:
                    status['login_page'] = True
                    status['overall'] = 'running'
                    self.working_port = port
                    quote_ctx.close()
                    break
                quote_ctx.close()
            except Exception:
                continue

        return status

    def _check_port_available(self, port: int) -> bool:
        """檢查端口是否被占用"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', port))
                return result != 0
        except:
            return True

    def diagnose_login_timeout(self) -> List[str]:
        """診斷登錄超時問題"""
        issues = []

        print("🔍 診斷富途登錄超時問題...")
        print("-" * 50)

        # 檢查網絡連接
        print("1. 檢查網絡連接...")
        try:
            # 檢查到 Google (測試網絡)
            response = requests.get('https://www.google.com', timeout=5)
            if response.status_code == 200:
                print("✅ 網絡連接正常")
            else:
                print("❌ 網絡連接異常")
                issues.append("網絡連接問題")
        except Exception as e:
            print(f"❌ 網絡連接失敗: {e}")
            issues.append("網絡連接問題")

        # 檢查富途服務
        print("\n2. 檢查富途服務狀態...")
        status = self.check_futu_service_status()

        if not status['processes']:
            print("❌ 未檢測到富途進程")
            issues.append("富途進程未運行")
        else:
            print(f"✅ 檢測到 {len(status['processes'])} 個富途進程")

        if not status['login_page']:
            print("❌ 富途 API 連接失敗")
            issues.append("富途服務未啟動")
        else:
            print(f"✅ 富途服務運行正常 (端口: {self.working_port})")

        # 檢查端口配置
        print("\n3. 檢查端口配置...")
        for port, info in status['ports'].items():
            if info['available']:
                print(f"✅ 端口 {port} 可用")
            else:
                print(f"⚠️ 端口 {port} 被占用")
                if port not in [11111, 4444]:  # 排除富途標準端口
                    issues.append(f"非標準端口 {port} 被占用")

        # 檢查防火牆設置
        print("\n4. 檢查防火牆設置...")
        try:
            result = subprocess.run(
                'netsh advfirewall show allprofiles state',
                shell=True,
                capture_output=True,
                text=True
            )
            if 'State' in result.stdout:
                print("✅ Windows 防火牆已檢查")
            else:
                print("⚠️ 無法檢查防火牆狀態")
        except:
            print("⚠️ 無法檢查防火牆")

        return issues

    def generate_solutions(self, issues: List[str]) -> List[str]:
        """生成解決方案"""
        solutions = []

        for issue in issues:
            if "網絡" in issue:
                solutions.extend([
                    "檢查網絡連接和 DNS 設置",
                    "嘗試切換到其他網絡",
                    "聯繫網絡管理員檢查防火牆設置"
                ])

            elif "進程未運行" in issue:
                solutions.extend([
                    "手動啟動富途 OpenD 客戶端",
                    "檢查富途安裝路徑是否正確",
                    "以管理員身份運行富途"
                ])

            elif "服務未啟動" in issue:
                solutions.extend([
                    "重啟富途客戶端",
                    "檢查客戶端配置文件",
                    "清除富途緩存數據"
                ])

            elif "端口衝突" in issue:
                solutions.extend([
                    "終止占用端口的進程",
                    "在富途設置中更改端口為 11111",
                    "使用富途修復工具清理衝突"
                ])

        return solutions

    def auto_fix_port_conflict(self) -> bool:
        """自動修復端口衝突"""
        print("\n🔧 嘗試自動修復端口衝突...")

        # 查找富途進程
        for port in [4444, 11011, 11211]:
            if not self._check_port_available(port):
                print(f"發現富途使用端口 {port}")

                # 嘗試終止進程
                try:
                    if sys.platform == "win32":
                        result = subprocess.run(
                            f'tasklist /fi "imagename eq FutuOpenD.exe" /fo csv',
                            shell=True,
                            capture_output=True,
                            text=True,
                            encoding='gbk'
                        )

                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')
                            for line in lines[1:]:
                                if line.strip():
                                    parts = line.split('","')

                                    if len(parts) >= 2:
                                        pid = parts[1].strip('"')
                                        subprocess.run(
                                            f'taskkill /F /PID {pid}',
                                            shell=True
                                        )
                                        print(f"已終止富途進程 (PID: {pid})")
                except Exception as e:
                    print(f"終止進程失敗: {e}")

                # 等待進程終止
                time.sleep(3)

                # 檢查默認端口是否現在可用
                if self._check_port_available(11111):
                    print("✅ 默認端口 11111 現在可用")
                    return True

        return False

    def setup_default_configuration(self) -> dict:
        """設置默認配置"""
        print("\n⚙️ 設置富途默認配置...")

        # 創建配置文件
        config = {
            'futu_port': 11111,
            'websocket_port': 4444,
            'host': '127.0.0.1',
            'timezone': 'UTC+8',
            'env_vars': {
                'FUTU_HOST': '127.0.0.1',
                'FUTU_PORT': '11111'
            }
        }

        # 更新 POC 配置文件
        try:
            if os.path.exists('POC_QUICK_START.py'):
                with open('POC_QUICK_START.py', 'r', encoding='utf-8') as f:
                    content = f.read()

                # 檢查並更新端口配置
                if 'def __init__(self, host=\'127.0.0.1\', port=11111):' in content:
                    print("✅ POC 配置已正確設置")
                else:
                    print("⚠️ POC 配置需要更新")

            # 創建環境變量設置腳本
            with open('set_futu_env.bat', 'w', encoding='utf-8') as f:
                f.write('@echo off\n')
                f.write('echo 設置富途環境變量...\n')
                f.write(f'set FUTU_HOST={config["env_vars"]["FUTU_HOST"]}\n')
                f.write(f'set FUTU_PORT={config["env_vars"]["FUTU_PORT"]}\n')
                f.write('echo 環境變量已設置\n')
                f.write('echo 現在可以運行: python POC_QUICK_START.py\n')

            print("✅ 配置設置完成")
            print(f"   - 默認端口: {config['futu_port']}")
            print(f"   - WebSocket端口: {config['websocket_port']}")
            print(f"   - 連接地址: {config['host']}")

            return config

        except Exception as e:
            print(f"❌ 設置配置失敗: {e}")
            return {}

    def test_final_connection(self) -> bool:
        """測試最終連接"""
        print("\n🧪 測試富途最終連接...")

        try:
            import futu as ft
            quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)

            # 測試基本連接
            ret, data = quote_ctx.get_global_state()
            if ret == ft.RET_OK:
                print("✅ 富途連接成功！")

                # 測試行情數據
                ret, data = quote_ctx.get_market_snapshot(["HK.00700"])
                if ret == ft.RET_OK and data:
                    snapshot = data[0]
                    print(f"✅ 行情測試成功:")
                    print(f"   騁豐控股 (00700): {snapshot['last_price']}")
                    print(f"   漲跌: {snapshot['change_val']}")

                quote_ctx.close()
                return True
            else:
                print(f"❌ 富途連接失敗: {data}")
                quote_ctx.close()
                return False

        except Exception as e:
            print(f"❌ 連接測試失敗: {e}")
            return False

def main():
    """主函數"""
    print("🔧 富途 OpenD 登錄超時修復工具")
    print("=" * 60)

    fixer = FutuLoginFixer()

    # 診斷問題
    issues = fixer.diagnose_login_timeout()

    if not issues:
        print("\n✅ 富途連接正常，無需修復")
        return

    print(f"\n🔍 發現 {len(issues)} 個問題:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

    # 生成解決方案
    solutions = fixer.generate_solutions(issues)

    print(f"\n💡 解決方案:")
    for i, solution in enumerate(solutions, 1):
        print(f"  {i}. {solution}")

    # 自動修復
    print(f"\n🤖 嘗試自動修復...")

    if fixer.auto_fix_port_conflict():
        print("✅ 端口衝突已修復")
    else:
        print("⚠️ 自動修復失敗，請手動操作")

    # 設置配置
    config = fixer.setup_default_configuration()

    # 最終測試
    print("\n" + "=" * 60)
    print("🎯 最終測試")
    print("=" * 60)

    if fixer.test_final_connection():
        print("✅ 富途 OpenD 登錄問題已解決！")
        print("\n下一步操作:")
        print("1. 重新打開富途客戶端並登錄")
        print("2. 確認網絡連接穩定")
        print("3. 運行: python POC_QUICK_START.py")
    else:
        print("❌ 修復失敗，請手動操作")
        print("\n建議操作:")
        print("1. 完全卸載並重新安裝富途 OpenD")
        print("2. 檢查網絡防火牆設置")
        print("3. 聯繫富途技術支持")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作被用戶中斷")
    except Exception as e:
        print(f"\n發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    print("\n按任意鍵退出...")
    try:
        input()
    except:
        pass