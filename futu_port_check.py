#!/usr/bin/env python3
"""
富途 OpenD 端口衝突檢測和解決工具
"""

import socket
import subprocess
import sys
import time
import os
from typing import List, Optional, Tuple

class FutuPortManager:
    def __init__(self, default_port=11111, alternative_ports=[11011, 11211, 11311]):
        self.default_port = default_port
        self.alternative_ports = alternative_ports
        self.occupied_processes = []

    def check_port_availability(self, port: int) -> Tuple[bool, Optional[int]]:
        """檢查端口是否可用，返回 (是否可用, 占用進程ID)"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', port))
                if result == 0:
                    return False, None  # 端口被占用，但無法獲取進程ID
            return True, None
        except Exception:
            return True, None

    def find_occupying_process(self, port: int) -> Optional[dict]:
        """查找占用指定端口的進程信息"""
        try:
            if sys.platform == "win32":
                # Windows 系統
                cmd = f'netstat -ano | findstr ":{port}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if f":{port}" in line and 'LISTENING' in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                pid = int(parts[-1])
                                return self._get_process_info_windows(pid)
            else:
                # Linux/Mac 系統
                cmd = f'lsof -i :{port}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')[1:]  # 跳過標題行
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = int(parts[1])
                            return self._get_process_info_unix(pid)
        except Exception as e:
            print(f"查找進程時發生錯誤: {e}")

        return None

    def _get_process_info_windows(self, pid: int) -> dict:
        """獲取 Windows 進程信息"""
        try:
            cmd = f'tasklist /fi "PID eq {pid}" /fo csv'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    info = lines[1].strip('"').split('","')
                    if len(info) >= 2:
                        return {
                            'pid': pid,
                            'name': info[0],
                            'memory': info[4] if len(info) > 4 else 'N/A',
                            'status': info[1] if len(info) > 1 else 'N/A'
                        }
        except Exception:
            pass

        return {'pid': pid, 'name': 'Unknown', 'memory': 'N/A', 'status': 'N/A'}

    def _get_process_info_unix(self, pid: int) -> dict:
        """獲取 Linux/Mac 進程信息"""
        try:
            cmd = f'ps -p {pid} -o pid,comm,stat,rss'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        memory_kb = int(parts[3]) if parts[3].isdigit() else 0
                        return {
                            'pid': pid,
                            'name': parts[1],
                            'memory': f"{memory_kb}KB",
                            'status': parts[2]
                        }
        except Exception:
            pass

        return {'pid': pid, 'name': 'Unknown', 'memory': 'N/A', 'status': 'N/A'}

    def kill_process(self, pid: int) -> bool:
        """終止指定進程"""
        try:
            if sys.platform == "win32":
                subprocess.run(f'taskkill /F /PID {pid}', shell=True, check=True)
            else:
                subprocess.run(f'kill -9 {pid}', shell=True, check=True)
            return True
        except Exception as e:
            print(f"終止進程失敗: {e}")
            return False

    def find_available_port(self) -> Optional[int]:
        """查找可用端口"""
        print(f"檢查富途端口可用性...")

        # 檢查默認端口
        available, _ = self.check_port_availability(self.default_port)
        if available:
            print(f"✅ 默認端口 {self.default_port} 可用")
            return self.default_port

        print(f"⚠️ 默認端口 {self.default_port} 被占用")

        # 檢查占用進程
        process_info = self.find_occupying_process(self.default_port)
        if process_info:
            print(f"占用進程信息:")
            print(f"   PID: {process_info['pid']}")
            print(f"   名稱: {process_info['name']}")
            print(f"   狀態: {process_info['status']}")
            print(f"   內存: {process_info['memory']}")

        # 檢查備選端口
        for port in self.alternative_ports:
            available, _ = self.check_port_availability(port)
            if available:
                print(f"✅ 找到可用端口: {port}")
                return port
            else:
                print(f"❌ 備選端口 {port} 也被占用")

        print("❌ 所有端口都被占用，需要手動解決")
        return None

    def start_futu_with_port(self, port: int) -> bool:
        """使用指定端口啟動富途"""
        try:
            if sys.platform == "win32":
                futu_path = self._find_futu_executable_windows()
                if futu_path:
                    print(f"使用端口 {port} 啟動富途...")
                    # 這裡可以添加富途的啟動參數，如果支持的話
                    subprocess.Popen([futu_path], shell=False)
                    return True
            else:
                print("請手動啟動富途並配置端口")
                return False
        except Exception as e:
            print(f"啟動富途失敗: {e}")
            return False

    def _find_futu_executable_windows(self) -> Optional[str]:
        """查找富途可執行文件路徑"""
        possible_paths = [
            r"C:\Program Files\Futu\FutuOpenD\FutuOpenD.exe",
            r"C:\Program Files (x86)\Futu\FutuOpenD\FutuOpenD.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def check_futu_connection(self, port: int, timeout=10) -> bool:
        """檢查富途連接"""
        print(f"檢查富途連接 (端口 {port})...")

        for i in range(timeout):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    result = sock.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        print(f"✅ 富途連接成功 (端口 {port})")
                        return True
            except Exception:
                pass

            time.sleep(1)
            print(f"等待富途啟動... ({i+1}/{timeout})")

        print(f"❌ 富途連接超時 (端口 {port})")
        return False

def main():
    """主函數"""
    print("🔧 富途 OpenD 端口衝突解決工具")
    print("=" * 50)

    manager = FutuPortManager()

    # 檢查端口可用性
    available_port = manager.find_available_port()

    if available_port is None:
        print("\n❌ 沒有可用的端口，請手動解決衝突")
        print("\n解決建議:")
        print("1. 終束占用端口的進程")
        print("2. 重啟富途客戶端")
        print("3. 使用不同的電腦進行測試")
        return

    print(f"\n🎯 推薦使用端口: {available_port}")

    # 如果默認端口被占用，提供建議
    if available_port != manager.default_port:
        print(f"\n💡 修改建議:")
        print(f"1. 在富途客戶端中修改端口為 {available_port}")
        print(f"2. 在代碼中使用新端口連接")
        print(f"3. 更新防火牆規則允許新端口")

        # 檢查是否為富途進程占用
        process_info = manager.find_occupying_process(manager.default_port)
        if process_info and 'Futu' in process_info['name']:
            print(f"\n🔄 檢測到富途進程，建議操作:")
            choice = input("是否重新啟動富途客戶端? (y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                manager.kill_process(process_info['pid'])
                print("富途進程已終止，請重新啟動富途客戶端")

    # 檢查富途是否正在運行
    print(f"\n🔍 檢查富途運行狀態...")
    if manager.check_futu_connection(available_port):
        print("✅ 富途正在運行，可以進行後續操作")
        print(f"\n📝 下一步操作:")
        print(f"1. 更新 POC 代碼中的端口配置: port = {available_port}")
        print(f"2. 運行: python POC_QUICK_START.py")
        print(f"3. 開始富途 OpenD POC 開發")
    else:
        print("❌ 富途未運行")
        print(f"\n📝 下一步操作:")
        print("1. 啟動富途客戶端")
        print("2. 確保登錄成功")
        print("3. 重新運行此工具進行檢查")
        print("4. 運行 POC 測試")

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
    input()